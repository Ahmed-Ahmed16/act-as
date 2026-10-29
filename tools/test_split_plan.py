import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

if __package__:
    from .test_hunk_text import OrchardRepo
else:
    from test_hunk_text import OrchardRepo


class SplitPlanTests(OrchardRepo, unittest.TestCase):
    def prepare(self):
        self.write('lang/en.json', 'unique_orchard_marker\nfruit\n')
        self.head = self.commit()
        self.count(self.head)

    def run_hunks(self, *extra):
        return subprocess.run([sys.executable, str(Path(__file__).with_name('split_plan.py')),
                               'hunks', '--repo', str(self.repo), '--base', self.base,
                               '--head', self.head, '--packet', str(self.packet), *map(str, extra)],
                              capture_output=True, text=True, encoding='utf-8', env=self.env)

    def test_Y1_full_commits_write_bound_records_and_language_flag(self):
        self.prepare()
        run = self.run_hunks()
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stderr, '')
        saved = json.loads((self.packet / 'hunks.json').read_bytes())
        self.assertEqual(set(saved), {'base', 'head', 'files_sha256', 'hunks', 'ops'})
        self.assertEqual((saved['base'], saved['head']), (self.base, self.head))
        self.assertEqual(saved['files_sha256'], hashlib.sha256((self.packet / 'files.json').read_bytes()).hexdigest())
        self.assertEqual(set(saved['hunks'][0]), set('id path old_path status kind counted lines deleted new_start new_count text_sha256 language'.split()))
        self.assertIs(saved['hunks'][0]['language'], True)
        self.assertEqual(run.stdout.splitlines(), ['f1h1 lang/en.json +1,2 2 +unique_orchard_marker'])

    def test_Y2_different_commit_and_short_saved_sha_fail_binding(self):
        self.prepare()
        original = (self.packet / 'runs/size-count.json').read_bytes()
        self.write('lang/en.json', 'another_orchard_marker\nfruit\n')
        self.head = self.commit()
        run = self.run_hunks()
        self.assertEqual((run.returncode, run.stderr), (1, ''))
        self.assertTrue(run.stdout.startswith('RULE hunks-head:'), run.stdout)
        self.assertFalse((self.packet / 'hunks.json').exists())
        for field in ('base', 'head'):
            with self.subTest(field=field):
                saved = json.loads(original)
                self.head = saved['head']
                saved[field] = saved[field][:9]
                (self.packet / 'runs/size-count.json').write_text(json.dumps(saved), encoding='utf-8')
                run = self.run_hunks()
                self.assertEqual((run.returncode, run.stderr), (1, ''))
                self.assertTrue(run.stdout.startswith('RULE hunks-head:'), run.stdout)

    def test_Y3_source_text_stays_on_screen(self):
        self.prepare()
        run = self.run_hunks()
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn('unique_orchard_marker', run.stdout)
        self.assertNotIn(b'unique_orchard_marker', (self.packet / 'hunks.json').read_bytes())

    def test_Y4_show_prints_every_changed_line_with_number(self):
        self.prepare()
        run = self.run_hunks('--show', 'f1h1')
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual([line for line in run.stdout.splitlines() if line.startswith('L')],
                         ['L1 +unique_orchard_marker', 'L2 +fruit'])

    def test_Y5_bad_inputs_are_stderr_only_and_changed_counts_differ(self):
        self.prepare()
        original = (self.packet / 'files.json').read_bytes()
        invalid_row = json.loads(original)
        invalid_row['files'][0]['path'] = None
        for contents in [b'', b'{', b'[]', b'{}', b'{"files": [null]}', b'\xff',
                         json.dumps(invalid_row).encode()]:
            with self.subTest(contents=contents):
                (self.packet / 'files.json').write_bytes(contents)
                run = self.run_hunks()
                self.assertEqual(run.returncode, 2, run.stdout + run.stderr)
                self.assertEqual(run.stdout, '')
                self.assertEqual(len(run.stderr.splitlines()), 1, run.stderr)
        for target in ('file', 'hunk'):
            with self.subTest(target=target):
                saved = json.loads(original)
                row = saved['files'][0]
                (row if target == 'file' else row['hunks'][0])['counted_lines'] += 1
                (self.packet / 'files.json').write_text(json.dumps(saved), encoding='utf-8')
                run = self.run_hunks()
                self.assertEqual((run.returncode, run.stderr), (1, ''))
                self.assertTrue(run.stdout.startswith('RULE hunks-differ:'), run.stdout)
        (self.packet / 'files.json').write_bytes(original)
        for saved in [[], {}, {'base': [], 'head': {}}, {'base': self.base, 'head': None}]:
            with self.subTest(saved=saved):
                (self.packet / 'runs/size-count.json').write_text(json.dumps(saved), encoding='utf-8')
                run = self.run_hunks()
                self.assertEqual((run.returncode, run.stdout), (2, ''))
                self.assertEqual(len(run.stderr.splitlines()), 1)
        self.packet = self.root / 'missing'
        run = self.run_hunks()
        self.assertEqual((run.returncode, run.stdout), (2, ''))
        self.assertEqual(len(run.stderr.splitlines()), 1)


if __name__ == '__main__':
    unittest.main()
