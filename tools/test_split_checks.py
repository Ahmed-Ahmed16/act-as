import copy
import json
import tempfile
import unittest
from pathlib import Path


class SplitChecksTests(unittest.TestCase):
    def setUp(self):
        scratch = Path(__file__).parent.parent / '.scratch'
        scratch.mkdir(exist_ok=True)
        self.tree = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.tree.cleanup)
        self.base, self.head = 'a' * 40, 'b' * 40
        self.files = {'files': []}
        self.hunks = dict(base=self.base, head=self.head, hunks=[], ops=[])
        self.plan = dict(groups=[], unplaced=[], parts=[])
        self.add_hunk('f1h1', 10)
        self.group('orchard', ['f1h1:L1-L4'])
        self.group('grove', ['f1h1:L5-L10'], needs=['orchard'])
        self.parts(['f1h1:L1-L4'])

    def add_hunk(self, key, lines, kind='counted', **extra):
        path = extra.pop('path', key + '.py')
        counted = lines if kind == 'counted' else 0
        self.files['files'].append(dict(path=path, old_path=path, status='A', kind=kind,
                                       counted_lines=counted, hunks=[dict(id=key, counted_lines=counted)]))
        record = dict(id=key, path=path, kind=kind, counted=counted, lines=lines,
                      deleted=0, new_start=1, new_count=lines, language=False)
        record.update(extra)
        self.hunks['hunks'].append(record)

    def group(self, name, pieces, **extra):
        group = dict(name=name, hunks=pieces, needs=[], links=[], rebuild='', pages=[], keys=[])
        group.update(extra)
        self.plan['groups'].append(group)
        return group

    def parts(self, *pieces):
        self.plan['parts'] = [dict(name=f'part {n}', hunks=span, needs=[], rebuild='', stays_over=None)
                              for n, span in enumerate(pieces, 1)]

    def reference(self, path='app/Harvest.py'):
        return dict(unchanged=path, at=self.head, check='git cat-file -e ' + self.head + ':' + path)

    def link(self, group, piece, target):
        group['links'].append({'piece': piece, 'for': [target]})

    def failures(self):
        if __package__:
            from .split_checks import split_failures
        else:
            from split_checks import split_failures
        documents = dict(zip(('files.json', 'hunks.json', 'split-input.json'),
                             (self.files, self.hunks, self.plan)))
        root = Path(self.tree.name)
        for name, document in documents.items():
            (root / name).write_text(json.dumps(document), encoding='utf-8')
        loaded = [json.loads((root / name).read_bytes()) for name in documents]
        failures = split_failures(*loaded)
        self.assertTrue(all(isinstance(row, tuple) and len(row) == 2 and
                            all(isinstance(field, str) and field for field in row) for row in failures))
        self.assertEqual(loaded, [self.files, self.hunks, self.plan])
        return failures

    def assert_rule(self, rule):
        failures = self.failures()
        self.assertIn(rule, [key for key, _ in failures], failures)
        return failures

    def test_A1_adjacent_counted_ranges_pass(self):
        self.assertEqual(self.failures(), [])

    def test_A2_missing_counted_piece_names_hunk(self):
        self.plan['groups'][1]['hunks'] = []
        failures = self.assert_rule('split-hunk-unplaced')
        self.assertTrue(any('f1h1' in message for _, message in failures))

    def test_A3_exempt_ranges_link_to_their_own_groups(self):
        self.add_hunk('f2h1', 40, 'test')
        for group, piece, target in zip(self.plan['groups'],
                                       ['f2h1:L1-L25', 'f2h1:L26-L40'],
                                       ['f1h1:L1-L4', 'f1h1:L5-L10']):
            group['hunks'].append(piece)
            self.link(group, piece, {'piece': target})
        self.parts(self.plan['groups'][0]['hunks'])
        self.assertEqual(self.failures(), [])

    def test_A4_exempt_parts_detect_gap_and_overlap(self):
        self.plan['groups'] = [self.plan['groups'][0]]
        group = self.plan['groups'][0]
        group['hunks'] = ['f1h1', 'f2h1']
        self.add_hunk('f2h1', 40, 'test')
        for piece, target in [('f2h1:L1-L25', 'f1h1:L1-L4'),
                              ('f2h1:L26-L40', 'f1h1:L5-L10')]:
            self.link(group, piece, {'piece': target})
        self.parts(['f1h1:L1-L4', 'f2h1:L1-L25'], ['f1h1:L5-L10', 'f2h1:L26-L40'])
        self.assertEqual(self.failures(), [])
        for piece, rule in [('f2h1:L27-L40', 'split-hunk-unplaced'),
                            ('f2h1:L25-L40', 'split-hunk-twice')]:
            with self.subTest(piece=piece):
                self.plan['parts'][1]['hunks'][1] = piece
                self.assert_rule(rule)

    def test_A5_file_operations_need_exactly_1_place(self):
        self.hunks['ops'] = [dict(id='f2op', path='empty.py', kind='counted', counted=0, lines=0)]
        self.assert_rule('split-hunk-unplaced')
        self.plan['unplaced'] = ['f2op']
        self.assertEqual(self.failures(), [])
        self.plan['groups'][1]['hunks'].append('f2op')
        self.assert_rule('split-hunk-twice')

    def test_A6_unknown_ids_and_bad_ranges_fail(self):
        for piece, rule in [('f99h1', 'split-hunk-unknown'),
                            ('f1h1:Lx-L3', 'split-hunk-range'), ('f1h1:L0-L3', 'split-hunk-range'),
                            ('f1h1:L5-L2', 'split-hunk-range'), ('f1h1:L1-L11', 'split-hunk-range'),
                            ('f1op:L1-L2', 'split-hunk-range')]:
            with self.subTest(piece=piece):
                self.plan['unplaced'] = [piece]
                self.assert_rule(rule)
        self.plan['unplaced'] = ['f1h1:L1-L1']
        self.assert_rule('split-hunk-twice')

    def test_A7_needs_must_point_back_and_notes_do_not_hide_loops(self):
        for need in ['grove', 'orchard', 'missing']:
            with self.subTest(need=need):
                self.plan['groups'][0]['needs'] = [need]
                self.assert_rule('split-need-order')
        self.plan['loop_notes'] = ['Shared setup moved to orchard.']
        self.plan['groups'][0]['needs'] = []
        self.assertEqual(self.failures(), [])

    def test_A8_test_pieces_need_nonempty_links(self):
        self.add_hunk('f2h1', 4, 'test')
        group = self.plan['groups'][1]
        group['hunks'].append('f2h1')
        self.assert_rule('split-link-missing')
        group['links'] = [{'piece': 'f2h1', 'for': []}]
        self.assert_rule('split-link-missing')

    def test_A9_links_cannot_cross_group_or_part_lines(self):
        self.add_hunk('f2h1', 4, 'test')
        group = self.plan['groups'][1]
        group['hunks'].append('f2h1')
        self.link(group, 'f2h1', {'piece': 'f1h1:L1-L4'})
        self.assert_rule('split-link-place')
        self.plan['groups'] = [group]
        group.update(needs=[], hunks=['f1h1', 'f2h1'])
        self.parts(['f1h1:L1-L4'], ['f1h1:L5-L10', 'f2h1'])
        self.assert_rule('split-link-place')
        group['links'][0]['for'] = [{'piece': 'f2h1'}]
        self.assert_rule('split-link-place')

    def test_A10_tests_can_link_to_unchanged_code(self):
        self.files['files'] = []
        self.hunks['hunks'] = []
        self.add_hunk('f2h1', 4, 'test')
        self.plan['groups'] = []
        group = self.group('harvest checks', ['f2h1'])
        self.link(group, 'f2h1', self.reference())
        self.parts(['f2h1'])
        self.assertEqual(self.failures(), [])

    def test_A11_unchanged_refs_need_unchanged_path_head_and_check(self):
        self.add_hunk('f2h1', 4, 'test')
        group = self.plan['groups'][1]
        group['hunks'].append('f2h1')
        for patch in [dict(unchanged='f1h1.py'), dict(at=self.base), dict(check=' '),
                      dict(unchanged='old.py')]:
            with self.subTest(patch=patch):
                self.files['files'][0]['old_path'] = 'old.py'
                reference = self.reference()
                reference.update(patch)
                group['links'] = [{'piece': 'f2h1', 'for': [reference]}]
                self.assert_rule('split-link-ref')
        for reference in [{}, None, {'bogus': 1}, dict(unchanged='app/Harvest.py', at=self.head)]:
            with self.subTest(reference=reference):
                group['links'] = [{'piece': 'f2h1', 'for': [reference]}]
                self.assert_rule('split-link-ref')

    def test_A12_unplaced_tests_need_no_link(self):
        self.add_hunk('f2h1', 4, 'test')
        self.plan['unplaced'] = ['f2h1']
        self.assertEqual(self.failures(), [])

    def test_A13_test_cleanup_can_link_only_to_unchanged_code(self):
        self.files['files'] = []
        self.hunks['hunks'] = []
        self.add_hunk('f2h1', 8, 'test')
        self.plan['groups'] = []
        group = self.group('no behaviour change: test cleanup', ['f2h1'])
        self.link(group, 'f2h1', self.reference())
        self.parts(['f2h1'])
        self.assertEqual(self.failures(), [])

    def test_A14_generated_pieces_need_group_and_part_rebuilds(self):
        self.add_hunk('f2h1', 9, 'generated')
        group = self.plan['groups'][1]
        group['hunks'].append('f2h1')
        self.link(group, 'f2h1', {'piece': 'f1h1:L5-L10'})
        self.assert_rule('split-rebuild-missing')
        group['rebuild'] = 'python build.py'
        self.assertEqual(self.failures(), [])
        self.plan['groups'] = [group]
        group.update(needs=[], hunks=['f1h1', 'f2h1'])
        self.parts(['f1h1', 'f2h1'])
        self.assert_rule('split-rebuild-missing')
        self.plan['parts'][0]['rebuild'] = 'python build.py'
        self.assertEqual(self.failures(), [])

    def large_part(self, length=320):
        self.files['files'] = []
        self.hunks['hunks'] = []
        self.plan = dict(groups=[], unplaced=[], parts=[])
        self.add_hunk('f1h1', length)
        self.add_hunk('f2h1', 6, 'test')
        self.add_hunk('f3h1', 2)
        group = self.group('harvest report', ['f1h1', 'f2h1', 'f3h1'])
        self.link(group, 'f2h1', {'piece': 'f1h1'})
        self.parts(group['hunks'].copy())
        record = dict(piece='f1h1', symbol='HarvestReport', kind='class',
                      declaration='class HarvestReport:', closing='    pass',
                      new_check=dict(base=self.base, command='git grep -n -w HarvestReport ' + self.base,
                                     found_in_base=[], deleted_in_pr=[]),
                      related=[dict(piece='f3h1', why='Its only use.', needed_check=dict(
                          command='git grep -n -w HarvestReport ' + self.head, needed=True,
                          result='f3h1 holds the only use.'))])
        self.plan['parts'][0]['stays_over'] = record
        return record

    def test_A15_size_edge_is_300_and_records_are_only_for_larger_parts(self):
        self.large_part(298)
        part = self.plan['parts'][0]
        part['stays_over'] = None
        self.assertEqual(self.failures(), [])
        part['stays_over'] = {}
        self.assert_rule('split-part-size')
        part['stays_over'] = None
        self.hunks['hunks'][0].update(lines=299, counted=299)
        self.assert_rule('split-part-size')
        self.large_part(151)
        part = self.plan['parts'][0]
        part.update(hunks=['f1h1', 'f1h1'], stays_over=None)
        self.assert_rule('split-part-size')

    def test_A16_large_new_symbol_with_test_and_needed_use_passes(self):
        record = self.large_part()
        record['piece'] = 'f1h1:L1-L320'
        self.assertEqual(self.failures(), [])

    def test_A17_symbol_span_and_new_evidence_must_fit(self):
        self.large_part()
        self.hunks['hunks'][0]['deleted'] = 1
        self.assert_rule('split-stays-over')
        self.large_part(300)
        self.assert_rule('split-stays-over')
        for field in ['declaration', 'closing', 'symbol', 'kind']:
            with self.subTest(field=field):
                record = self.large_part()
                record[field] = ' '
                self.assert_rule('split-stays-over')
        for patch in [dict(command=''), dict(base=self.head), dict(found_in_base=None)]:
            with self.subTest(patch=patch):
                record = self.large_part()
                record['new_check'].update(patch)
                self.assert_rule('split-stays-over')

    def test_A18_moved_symbol_evidence_fails(self):
        for field in ['found_in_base', 'deleted_in_pr']:
            with self.subTest(field=field):
                record = self.large_part()
                record['new_check'][field] = ['app/OldHarvest.py:4']
                self.assert_rule('split-stays-over')

    def test_A19_undeclared_counted_lines_fail_in_any_file(self):
        for path in ['f1h1.py', 'app/Other.py']:
            with self.subTest(path=path):
                self.large_part()
                self.add_hunk('f4h1', 1, path=path)
                self.plan['groups'][0]['hunks'].append('f4h1')
                self.plan['parts'][0]['hunks'].append('f4h1')
                self.assert_rule('split-stays-over')
        record = self.large_part()
        record['piece'] = 'f1h1:L1-L319'
        self.assert_rule('split-stays-over')

    def test_A20_declared_unneeded_work_fails(self):
        for needed in [False, None, 1, 'true']:
            with self.subTest(needed=needed):
                record = self.large_part()
                record['related'][0]['needed_check']['needed'] = needed
                self.assert_rule('split-stays-over')

    def test_A21_related_work_needs_named_command_and_result(self):
        for patch in [dict(command='git grep Harvest'), dict(command=' '), dict(result=' ')]:
            with self.subTest(patch=patch):
                record = self.large_part()
                record['related'][0]['needed_check'].update(patch)
                self.assert_rule('split-stays-over')
        record = self.large_part()
        del record['related'][0]['needed_check']
        self.assert_rule('split-stays-over')

    def test_A22_reason_text_cannot_replace_evidence(self):
        self.large_part()
        for record in ['too hard to split', {}, None]:
            with self.subTest(record=record):
                self.plan['parts'][0]['stays_over'] = record
                self.assert_rule('split-part-size' if record is None else 'split-stays-over')

    def test_A23_language_only_work_needs_unchanged_pages(self):
        for hunk in self.hunks['hunks']:
            hunk['language'] = True
        self.assert_rule('split-text-only')
        page = dict(name='harvest', unchanged=dict(path='app/Harvest.py', at=self.head, check='exists'))
        for group in self.plan['groups']:
            group['pages'] = [copy.deepcopy(page)]
            group['keys'] = [dict(page='harvest', pieces=group['hunks'], part='part 1')]
        self.assertEqual(self.failures(), [])
        self.plan['groups'][0]['keys'][0]['page'] = 'missing'
        self.assert_rule('split-text-only')
        self.plan['groups'][0]['keys'][0]['page'] = 'harvest'
        self.hunks['hunks'][0]['language'] = False
        self.assert_rule('split-text-only')

    def test_A24_parts_cover_group_1_once_and_need_only_earlier_parts(self):
        self.plan['parts'][0]['hunks'] = []
        self.assert_rule('split-part-cover')
        self.parts(['f1h1:L1-L4'], ['f1h1:L1-L4'])
        self.assert_rule('split-part-cover')
        self.parts(['f1h1:L1-L2'], ['f1h1:L3-L4'])
        self.assertEqual(self.failures(), [])
        for need in ['part 2', 'part 1', 'absent']:
            with self.subTest(need=need):
                self.plan['parts'][0]['needs'] = [need]
                self.assert_rule('split-part-need')
        self.plan['parts'][0]['needs'] = []
        self.plan['parts'][1]['needs'] = ['part 1']
        self.assertEqual(self.failures(), [])

    def test_A25_groups_need_unique_plain_names(self):
        self.plan['groups'] = []
        self.assert_rule('split-no-groups')
        for name in ['orchard', '', ' ', 'fruit | harvest']:
            with self.subTest(name=name):
                self.plan['groups'] = []
                self.group('orchard', ['f1h1:L1-L4'])
                self.group(name, ['f1h1:L5-L10'])
                self.assert_rule('split-name')


if __name__ == '__main__':
    unittest.main()
