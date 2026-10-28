import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class SplitBuildTests(unittest.TestCase):
    def setUp(self):
        scratch = Path(__file__).parent.parent / '.scratch'
        scratch.mkdir(exist_ok=True)
        self.tree = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.tree.cleanup)
        self.packet = Path(self.tree.name)
        (self.packet / 'runs').mkdir()
        self.files = dict(files=[])
        self.hunks = dict(base='a' * 40, head='b' * 40, hunks=[], ops=[])
        for n, path in enumerate(['app/Seed.py', 'lang/en.json', 'lang/en/buttons.php', 'app/Water.py'], 1):
            key = f'f{n}h1'
            self.files['files'].append(dict(path=path, old_path=path, status='A', kind='counted',
                                           counted_lines=2, hunks=[dict(id=key, counted_lines=2)]))
            self.hunks['hunks'].append(dict(id=key, path=path, old_path=path, status='A', kind='counted',
                                           counted=2, lines=2, deleted=0, new_start=1, new_count=2,
                                           text_sha256='0' * 64, language=n in (2, 3)))
        self.group = dict(name='seed', summary='Plant seeds.', entry_points=['app/Seed.py'], needs=[],
                          hunks=[f'f{n}h1' for n in range(1, 5)], links=[], rebuild='',
                          pages=[dict(name='plant', pieces=['f1h1']), dict(name='water', pieces=['f4h1'])],
                          keys=[dict(shape='json', key='Save', page='plant', part='part 1', pieces=['f2h1']),
                                dict(shape='php', key='buttons.save', page='water', part='part 2', pieces=['f3h1'])],
                          keys_check=dict(how='Read every changed language line.', keys_found=2))
        self.plan = dict(groups=[self.group], parts=[
            dict(name='part 1', summary='Plant.', needs=[], hunks=['f1h1', 'f2h1'], rebuild='', stays_over=None),
            dict(name='part 2', summary='Water.', needs=['part 1'], hunks=['f3h1', 'f4h1'], rebuild='', stays_over=None)],
            unplaced=[], unplaced_keys=[], unplaced_keys_check=None, marks=[], loop_notes=['Read the pages.'],
            main=dict(state='established', evidence='The saved default branch is main.'),
            ci=dict(state='read', reason='', workflows=[dict(path='.github/workflows/check.yml', on_text='push:')]))

    def save(self):
        raw_files = json.dumps(self.files).encode()
        self.hunks.setdefault('files_sha256', hashlib.sha256(raw_files).hexdigest())
        documents = {'files.json': self.files, 'hunks.json': self.hunks,
                     'runs/size-count.json': dict(base='a' * 40, head='b' * 40), 'split-input.json': self.plan}
        for name, document in documents.items():
            (self.packet / name).write_bytes(json.dumps(document).encode())

    def run_build(self):
        return subprocess.run([sys.executable, str(Path(__file__).with_name('split_plan.py')), 'build',
                               str(self.packet)], capture_output=True, text=True, encoding='utf-8')

    def built(self):
        self.save()
        run = self.run_build()
        self.assertEqual((run.returncode, run.stderr), (0, ''), run.stdout + run.stderr)
        return json.loads((self.packet / 'split-plan.json').read_bytes())

    def rule(self, expected):
        self.save()
        run = self.run_build()
        self.assertEqual((run.returncode, run.stderr), (1, ''), run.stdout + run.stderr)
        self.assertTrue(all(line.startswith('RULE ') for line in run.stdout.splitlines()), run.stdout)
        self.assertIn('RULE ' + expected + ':', run.stdout)
        self.assertFalse((self.packet / 'split-plan.json').exists())

    def test_M1_money_follows_part_2_only(self):
        self.plan['marks'] = [dict(mark='money', pieces=['f3h1'], note='Read it.')]
        saved = self.built()
        self.assertEqual(saved['groups'][0]['marks'], ['money'])
        self.assertEqual([part['marks'] for part in saved['first_group_parts']], [[], ['money']])

    def test_M2_overlapping_marks_both_survive(self):
        self.plan['marks'] = [dict(mark=mark, pieces=['f2h1:L1-L1'], note='') for mark in ['money', 'access']]
        saved = self.built()
        self.assertEqual(saved['first_group_parts'][0]['marks'], ['money', 'access'])

    def test_M3_all_mark_names_survive(self):
        names = ['money', 'access', 'deletion', 'unsure']
        self.plan['marks'] = [dict(mark=mark, pieces=[f'f{n}h1'], note='') for n, mark in enumerate(names, 1)]
        self.assertEqual(self.built()['groups'][0]['marks'], names)

    def test_M4_marks_need_known_names_and_placed_pieces(self):
        for mark, piece, rule in [('other', 'f1h1', 'split-mark-name'),
                                  ('money', 'f9h1', 'split-mark-place'),
                                  ('money', 'f4h1', 'split-mark-place')]:
            with self.subTest(mark=mark, piece=piece):
                self.plan['marks'] = [dict(mark=mark, pieces=[piece], note='')]
                if piece == 'f4h1':
                    self.group['hunks'].remove(piece)
                    self.plan['parts'][1]['hunks'].remove(piece)
                self.rule(rule)

    def test_M5_language_places_need_a_complete_key_check(self):
        for check in [dict(how='Read.', keys_found=3), None, dict(how=' ', keys_found=2)]:
            with self.subTest(check=check):
                self.group['keys_check'] = check
                self.rule('split-key-missing')
        self.group['hunks'].remove('f2h1')
        self.plan['parts'][0]['hunks'].remove('f2h1')
        self.plan['unplaced'] = ['f2h1']
        self.group['keys'] = self.group['keys'][1:]
        self.group['keys_check'] = dict(how='Read.', keys_found=1)
        self.rule('split-key-missing')
        self.plan['unplaced_keys'] = [dict(shape='json', key='Save', page='shared', part=None, pieces=['f2h1'])]
        self.plan['unplaced_keys_check'] = dict(how='Read every unplaced language line.', keys_found=1)
        self.assertEqual(self.built()['unplaced_keys'], self.plan['unplaced_keys'])

    def test_M6_key_identity_is_unique_across_places(self):
        duplicate = copy.deepcopy(self.group['keys'][0])
        self.group['keys'].append(duplicate)
        self.rule('split-key-twice')
        self.group['keys'].pop()
        self.plan['groups'].append(dict(name='pond', hunks=[], needs=[], keys=[duplicate]))
        self.rule('split-key-twice')

    def test_M7_overlapping_keys_cannot_claim_different_places(self):
        duplicate = dict(self.group['keys'][0], key='Cancel', pieces=['f2h1:L2-L2'], part='part 2')
        self.group['keys'].append(duplicate)
        self.rule('split-key-conflict')
        duplicate['part'] = 'part 1'
        self.group['keys'].pop()
        self.plan['groups'].append(dict(name='pond', hunks=[], needs=[], keys=[duplicate]))
        self.rule('split-key-conflict')

    def test_M8_compact_json_keys_count_the_placed_piece_once(self):
        self.hunks['hunks'][1].update(counted=1, lines=1, new_count=1)
        self.files['files'][1].update(counted_lines=1, hunks=[dict(id='f2h1', counted_lines=1)])
        self.group['keys'].append(dict(self.group['keys'][0], key='Cancel'))
        self.group['keys_check']['keys_found'] = 3
        saved = self.built()
        self.assertEqual(saved['groups'][0]['estimate'], 7)
        self.assertEqual(saved['first_group_parts'][0]['counted'], 3)

    def test_M9_compact_php_keys_share_a_line(self):
        self.hunks['hunks'][2].update(counted=1, lines=1, new_count=1)
        self.files['files'][2].update(counted_lines=1, hunks=[dict(id='f3h1', counted_lines=1)])
        self.group['keys'].append(dict(self.group['keys'][1], key='buttons.cancel', pieces=['f3h1:L1-L1']))
        self.group['keys_check']['keys_found'] = 3
        self.assertEqual(self.built()['groups'][0]['estimate'], 7)

    def test_M10_keys_need_language_pieces_in_the_declaring_group(self):
        self.group['keys'][0]['pieces'] = ['f1h1']
        self.rule('split-key-misplaced')
        self.group['keys'][0]['pieces'] = ['f2h1']
        self.group['keys'][0]['part'] = 'part 2'
        self.rule('split-key-misplaced')
        self.group['keys'][0]['part'] = 'part 1'
        self.group['hunks'].remove('f2h1')
        self.plan['parts'][0]['hunks'].remove('f2h1')
        self.plan['groups'].append(dict(name='pond', hunks=['f2h1'], needs=[], keys=[]))
        self.rule('split-key-misplaced')

    def test_M11_page_left_behind_fails_even_when_key_part_is_correct(self):
        self.plan['parts'][0]['hunks'].remove('f2h1')
        self.plan['parts'][1]['hunks'].append('f2h1')
        self.group['keys'][0]['part'] = 'part 2'
        self.rule('split-key-page-place')

    def test_M12_key_and_page_can_move_together(self):
        self.plan['parts'][0]['hunks'] = []
        self.plan['parts'][1]['hunks'] += ['f1h1', 'f2h1']
        self.group['keys'][0]['part'] = 'part 2'
        self.assertEqual(self.built()['first_group_parts'][1]['counted'], 8)

    def test_M13_php_identity_drops_locale_folder(self):
        self.hunks['hunks'][1]['path'] = 'lang/ar/reports/weekly.php'
        self.hunks['hunks'][2]['path'] = 'lang/en/reports/weekly.php'
        self.plan['parts'][0]['hunks'] = []
        self.plan['parts'][1]['hunks'] = self.group['hunks'].copy()
        self.group['keys'] = [dict(shape='php', key='reports/weekly.title', page='water', part='part 2',
                                   pieces=['f2h1', 'f3h1'])]
        self.group['keys_check']['keys_found'] = 1
        self.assertEqual(self.built()['groups'][0]['keys'], self.group['keys'])

    def test_M14_pages_must_belong_to_group_or_be_shared(self):
        self.group['keys'][0]['page'] = 'absent'
        self.rule('split-page-missing')
        self.group['keys'][0]['page'] = 'shared'
        self.assertEqual(self.built()['groups'][0]['keys'][0]['page'], 'shared')

    def test_M15_text_only_part_can_use_an_unchanged_page(self):
        self.plan['parts'][0]['hunks'].remove('f1h1')
        self.plan['parts'][1]['hunks'].append('f1h1')
        page = dict(name='plant', unchanged=dict(path='app/Old.py', at=self.hunks['head'], check='Read it.'))
        self.group['pages'][0] = page
        self.plan['parts'][0]['pages'] = [page]
        self.plan['parts'][0]['keys'] = [self.group['keys'][0]]
        self.assertEqual(self.built()['first_group_parts'][0]['counted'], 2)
        self.plan['parts'][0]['hunks'].append('f1h1')
        self.plan['parts'][1]['hunks'].remove('f1h1')
        self.plan['parts'][0]['pages'] = []
        self.plan['parts'][0]['keys'] = []
        (self.packet / 'split-plan.json').unlink()
        self.rule('split-text-only')

    def test_M16_stale_hunks_fail_commit_and_file_binding(self):
        for field, changed in [('head', 'c' * 40), ('base', 'd' * 40), ('files_sha256', 'f' * 64)]:
            with self.subTest(field=field):
                original = self.hunks.get(field)
                self.hunks[field] = changed
                self.rule('hunks-stale')
                if original is None:
                    self.hunks.pop(field)
                else:
                    self.hunks[field] = original

    def test_M17_ci_and_main_need_valid_states_and_evidence(self):
        for ci in [dict(state='guess'), dict(state='read', workflows=[dict(on_text='push:')]),
                   dict(state='read', workflows=[dict(path='ci.yml', on_text=' ')])]:
            with self.subTest(ci=ci):
                self.plan['ci'] = ci
                self.rule('split-ci-input')
        self.plan['ci'] = dict(state='read', workflows=[])
        for main in [dict(state='guess', evidence='Read.'), dict(state='established', evidence=' ')]:
            with self.subTest(main=main):
                self.plan['main'] = main
                self.rule('split-main-input')
        self.plan['main'] = dict(state='not established', evidence='No default branch record.')
        self.assertEqual(self.built()['ci']['workflows'], [])
        self.plan['ci'] = dict(state='unreadable', reason='The packet has no workflow text.')
        self.assertEqual(self.built()['ci']['state'], 'unreadable')

    def test_M18_build_saves_complete_plan_and_exact_byte_hashes(self):
        self.save()
        before = {name: (self.packet / name).read_bytes() for name in ['files.json', 'hunks.json', 'split-input.json']}
        run = self.run_build()
        self.assertEqual((run.returncode, run.stderr), (0, ''), run.stdout + run.stderr)
        saved = json.loads((self.packet / 'split-plan.json').read_bytes())
        self.assertEqual(set(saved), set('groups first_group_parts unplaced unplaced_keys unplaced_keys_check loop_notes main ci base head input_sha256 hunks_sha256 files_sha256'.split()))
        self.assertEqual(set(saved['groups'][0]), set('name entry_points estimate hunks summary needs links rebuild pages keys keys_check marks counted'.split()))
        self.assertEqual(set(saved['first_group_parts'][0]), set('name summary needs hunks counted marks rebuild stays_over'.split()))
        for field in ['unplaced', 'unplaced_keys', 'unplaced_keys_check', 'loop_notes', 'main', 'ci']:
            self.assertEqual(saved[field], self.plan[field])
        self.assertEqual((saved['base'], saved['head']), (self.hunks['base'], self.hunks['head']))
        for name, field in [('split-input.json', 'input_sha256'), ('hunks.json', 'hunks_sha256'), ('files.json', 'files_sha256')]:
            self.assertEqual(saved[field], hashlib.sha256(before[name]).hexdigest())
            self.assertEqual((self.packet / name).read_bytes(), before[name])
        self.assertEqual(saved['groups'][0]['estimate'], 8)

    def test_M19_bad_files_are_stderr_only(self):
        self.built()
        for name in ['files.json', 'hunks.json', 'runs/size-count.json', 'split-input.json']:
            for contents in [None, b'', b'{', b'[]', b'{}', b'\xff']:
                with self.subTest(name=name, contents=contents):
                    self.save()
                    path = self.packet / name
                    path.unlink() if contents is None else path.write_bytes(contents)
                    run = self.run_build()
                    self.assertEqual((run.returncode, run.stdout), (2, ''), run.stdout + run.stderr)
                    self.assertEqual(len(run.stderr.splitlines()), 1, run.stderr)
        for path, contents in [(['groups', 0, 'pages', 0, 'pieces'], None),
                               (['groups', 0, 'keys', 0, 'pieces'], 'f2h1'),
                               (['parts', 0, 'hunks'], None), (['ci', 'workflows'], None),
                               (['groups', 0, 'keys_check'], []), (['marks'], None),
                               (['unplaced_keys'], None), (['groups', 0, 'keys', 0, 'part'], []),
                               (['parts', 0, 'stays_over'], dict(related=None)),
                               (['parts', 0, 'keys'], [dict(page=[])]),
                               (['parts', 0, 'pages'], [dict(name=[], unchanged=dict(path='old.py'))]),
                               (['extra'], dict(pieces=None))]:
            with self.subTest(path=path):
                self.save()
                document = json.loads((self.packet / 'split-input.json').read_bytes())
                parent = document
                for component in path[:-1]:
                    parent = parent[component]
                parent[path[-1]] = contents
                (self.packet / 'split-input.json').write_bytes(json.dumps(document).encode())
                run = self.run_build()
                self.assertEqual((run.returncode, run.stdout), (2, ''), run.stdout + run.stderr)
                self.assertEqual(len(run.stderr.splitlines()), 1, run.stderr)


if __name__ == '__main__':
    unittest.main()
