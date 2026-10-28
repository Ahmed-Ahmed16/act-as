import importlib
import unittest


STOP = 'not checked: PR over the cap, split it first'


def render_inputs():
    files = dict(files=[
        dict(path='app/Seed.py', old_path='', status='A', kind='counted', counted_lines=601,
             hunks=[dict(id='f1h1', counted_lines=601)]),
        dict(path='tests/Seed.py', old_path='', status='A', kind='test', counted_lines=0,
             hunks=[dict(id='f2h1', counted_lines=0)]),
        dict(path='db/migrations/plant.sql', old_path='', status='A', kind='counted', counted_lines=1,
             hunks=[dict(id='f3h1', counted_lines=1)])])
    group = dict(name='plant', summary='Plant seeds.', entry_points=['route seed'], estimate=3, counted=3,
                 hunks=['f1h1:L1-L2', 'f2h1', 'f3h1'], needs=[], marks=[], rebuild='', pages=[], keys=[],
                 links=[dict(piece='f2h1', **{'for': [dict(piece='f1h1:L1-L2')]})])
    part = dict(name='seed', summary='Show seeds.', needs=[], counted=3, hunks=group['hunks'].copy(),
                marks=[], rebuild='python generate.py', stays_over=None)
    plan = dict(groups=[group, dict(group, name='water', summary='Water seeds.', hunks=['f1h1:L3-L302'],
                                   counted=300, estimate=300, needs=['plant'], links=[])],
                first_group_parts=[part], unplaced=['f1h1:L303-L601'], unplaced_keys=[],
                loop_notes=['Move the shared type into plant.'], main=dict(state='established', evidence='Read main.'),
                ci=dict(state='read', workflows=[]), head='b' * 40)
    hunks = dict(hunks=[dict(id='f1h1', path='app/Seed.py', new_start=7, counted=601, lines=601),
                        dict(id='f2h1', path='tests/Seed.py', new_start=1, counted=0, lines=3),
                        dict(id='f3h1', path='db/migrations/plant.sql', new_start=1, counted=1, lines=1)], ops=[])
    return plan, files, hunks


class ShortRenderTests(unittest.TestCase):
    # Cases: 300/301, no/1/2 needs, no/overlapping marks, no/2 workflows,
    # whole/ranged pieces, unplaced tests, unchanged pages, new symbol span.
    def setUp(self):
        name = (__package__ + '.' if __package__ else '') + 'short_render'
        self.assertIsNotNone(importlib.util.find_spec(name), 'short_render is missing')
        self.render = importlib.import_module(name)
        self.plan, self.files, self.hunks = render_inputs()

    def field(self):
        return self.render.split_field(self.plan, self.files, self.hunks)

    def draft(self, opening='This PR is 602 counted lines; the cap is 300. It was not reviewed past size.'):
        return self.render.draft(self.plan, self.files, self.hunks, opening)

    def test_B10_later_groups_fit_at_300_and_split_at_301(self):
        self.assertIn('fits: 300 counted lines, open as 1 PR', self.field())
        self.plan['groups'][1]['counted'] = 301
        self.assertIn('over the cap: split again when its turn comes', self.field())
        self.assertNotIn('fits:', self.field())

    def test_B11_unplaced_tests_are_leads_without_group_advice(self):
        self.plan['unplaced'].append('f2h1')
        self.plan['unplaced_marks'] = ['unsure']
        text = self.field().split('unplaced (a lead, not a group):', 1)[1].split('loop broken:', 1)[0]
        self.assertIn('299 counted lines', text)
        self.assertIn('tests with no source found (lead): f2h1', text)
        self.assertNotIn('fits', text)
        self.assertNotIn('split again', text)
        self.assertIn('stands alone (unsure)', text)
        self.assertIn('needs the separate Opus review', text)

    def test_B12_ci_read_unreadable_and_no_workflow_keep_part_check(self):
        cases = [
            (dict(state='unreadable', reason='GET failed'), 'not checked: CI trigger not read (GET failed).'),
            (dict(state='read', workflows=[]), 'no workflow files found at the frozen head'),
            (dict(state='read', workflows=[dict(path='ci.yml', on_text='push:\n  branches: [main]'),
                                          dict(path='test.yml', on_text='pull_request:')]),
             'workflow ci.yml, on block as read by the reviewer: push:;   branches: [main]')]
        for ci, expected in cases:
            with self.subTest(ci=ci):
                self.plan['ci'] = ci
                text = self.field()
                self.assertIn(expected, text)
                self.assertEqual(text.count("check: CI green on this PR's own head"), 1)
                if ci['state'] == 'read':
                    self.assertIn('The tool does not interpret these filters.', text)
                if ci.get('workflows'):
                    self.assertIn('workflow test.yml, on block as read by the reviewer: pull_request:', text)

    def test_B13_part_needs_print_main_in_every_case(self):
        first = self.plan['first_group_parts'][0]
        self.plan['first_group_parts'] = [first, dict(first, name='soil', needs=['seed']),
                                           dict(first, name='rain', needs=['seed', 'soil'])]
        text = self.field()
        for sentence in ['opens against main; needs no other part',
                         'opens against main after parts seed are merged',
                         'opens against main after parts seed and soil are merged']:
            self.assertIn(sentence, text)
        self.assertEqual(text.count("check: CI green on this PR's own head"), 3)

    def test_B14_unproved_main_keeps_open_sentences(self):
        self.plan['main'] = dict(state='not established', evidence='default branch read as develop; main not read')
        text = self.field()
        self.assertIn('not checked: main not established: default branch read as develop; main not read.', text)
        self.assertIn('opens against main after groups plant are merged', text)
        self.assertIn('opens against main; needs no other part', text)

    def test_B15_marks_show_separate_review_only_for_money_or_unsure(self):
        part = self.plan['first_group_parts'][0]
        for marks in [[], ['money'], ['access'], ['deletion'], ['unsure'], ['access', 'money']]:
            with self.subTest(marks=marks):
                part['marks'] = marks
                text = self.field().split('part 1:', 1)[1]
                self.assertEqual('stands alone (' in text, bool(marks))
                if marks:
                    self.assertIn('stands alone (' + ', '.join(marks) + ')', text)
                self.assertEqual('needs the separate Opus review' in text, bool(set(marks) & {'money', 'unsure'}))

    def test_B16_large_symbol_span_and_related_checks_are_explicit(self):
        self.plan['first_group_parts'][0]['stays_over'] = dict(
            piece='f1h1:L3-L303', symbol='SeedBook', kind='class', declaration='class SeedBook:', closing='pass',
            related=[dict(piece='f3h1', why='Loads SeedBook.', needed_check=dict(
                command='git grep SeedBook', result='Only use.', needed=True))])
        for text in [self.field(), self.draft()]:
            self.assertIn('stays over the cap: SeedBook (new class) at app/Seed.py lines 9 to 309', text)
            self.assertIn('301 counted lines alone', text)
            self.assertIn('f3h1', text)
            self.assertIn('Loads SeedBook.', text)
            self.assertIn('git grep SeedBook', text)
            self.assertIn('Only use.', text)
            self.assertIn("The reviewer's checks are recorded; the tool did not prove them. Your call:", text)

    def test_B17_draft_order_details_and_shared_file_assignments(self):
        text = self.draft()
        self.assertTrue(text.startswith('This PR is 602 counted lines; the cap is 300. It was not reviewed past size.\n'))
        fragments = ['group: plant, 3 counted lines', 'group: water, 300 counted lines', 'part 1:',
                     'shared file: app/Seed.py', 'language keys travel with their page.',
                     'open part 1 first; each part gets its own review.']
        positions = [text.index(fragment) for fragment in fragments]
        self.assertEqual(positions, sorted(positions))
        for fragment in ['files:', 'tests: tests/Seed.py', 'migrations: db/migrations/plant.sql',
                         'rebuild: python generate.py', "check: CI green on this PR's own head",
                         'plant: f1h1:L1-L2', 'water: f1h1:L3-L302']:
            self.assertIn(fragment, text)
        self.assertTrue(text.endswith('open part 1 first; each part gets its own review.'))
        self.assertNotIn('looks good', text)
        self.assertNotIn('safe to merge', text)
        self.assertTrue(self.draft('Custom opening.').startswith('Custom opening.\n'))
        group_lines = lambda body: [line for line in body.splitlines() if line.startswith('group: ')]
        self.assertEqual(group_lines(text), group_lines(self.field()))

    def test_draft_marks_and_large_symbols_follow_shared_file_rule(self):
        part = self.plan['first_group_parts'][0]
        part['marks'] = ['money']
        part['stays_over'] = dict(piece='f1h1:L3-L303', symbol='SeedBook', kind='class', related=[])
        text = self.draft()
        fragments = ['check: CI green', 'shared file: app/Seed.py', 'seed: stands alone (money)',
                     'stays over the cap: SeedBook', 'open part 1 first; each part gets its own review.']
        for fragment in fragments:
            self.assertIn(fragment, text)
        positions = [text.index(fragment) for fragment in fragments]
        self.assertEqual(positions, sorted(positions))

    def test_B18_pages_keys_and_links_keep_their_owners(self):
        group = self.plan['groups'][0]
        group['pages'] = [dict(name='garden', pieces=['f1h1:L1-L2'])]
        group['keys'] = [dict(shape='json', key='Plant', page='garden', part='seed')]
        group['links'].append(dict(piece='f2h1', **{'for': [dict(unchanged='app/Old.py', at='b' * 40)]}))
        text = self.field()
        for line in ['page: garden, source pieces f1h1:L1-L2', 'key json: Plant, page garden, part seed',
                     'test f2h1 for f1h1:L1-L2', 'test f2h1 for unchanged app/Old.py at bbbbbbb']:
            self.assertIn(line, text)

    def test_B21_rendered_text_has_no_unknown_or_long_dash(self):
        text = self.field() + self.draft() + self.render.behaviour(self.plan)
        self.assertIn('Counts are estimates: hunk lines from git, placed by reading entry points.', text)
        for forbidden in ['\u2014', '\u2013', '___']:
            self.assertNotIn(forbidden, text)

    def test_B26_unchanged_screen_discloses_unchecked_default_branch(self):
        self.plan['groups'][0]['pages'] = [dict(name='garden', unchanged=dict(path='app/Old.py'))]
        self.assertIn('page: garden, unchanged screen at app/Old.py; existence on the default branch not checked by the tool',
                      self.field())


if __name__ == '__main__':
    unittest.main()
