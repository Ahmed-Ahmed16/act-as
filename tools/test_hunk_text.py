import hashlib
import importlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class OrchardRepo:
    def setUp(self):
        self.tree = tempfile.TemporaryDirectory(prefix='orchard-')
        self.addCleanup(self.tree.cleanup)
        self.root = Path(self.tree.name)
        self.repo = self.root / 'grove'
        self.repo.mkdir()
        self.packet = self.root / 'packet'
        self.env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM='1',
                        PYTHONDONTWRITEBYTECODE='1')
        self.git('init', '-b', 'main')
        self.git('config', 'user.name', 'Orchard')
        self.git('config', 'user.email', 'orchard@example.invalid')
        self.base = self.commit()

    def git(self, *args):
        run = subprocess.run(['git', '-c', 'core.autocrlf=false', '-c', 'commit.gpgsign=false',
                              '-C', str(self.repo), *args], capture_output=True, env=self.env)
        self.assertEqual(run.returncode, 0, run.stderr)
        return run.stdout.decode().strip()

    def write(self, path, contents):
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(contents.encode() if isinstance(contents, str) else contents)

    def commit(self):
        self.git('add', '-A')
        self.git('commit', '--allow-empty', '-m', 'Grow orchard')
        return self.git('rev-parse', 'HEAD')

    def count(self, head):
        script = Path(__file__).with_name('size_counter.py')
        run = subprocess.run([sys.executable, str(script), '--repo', str(self.repo),
                              '--base', self.base, '--head', head, '--out', str(self.packet)],
                             capture_output=True, env=self.env)
        self.assertEqual(run.returncode, 0, run.stderr)
        (self.packet / 'runs').mkdir(exist_ok=True)
        (self.packet / 'runs/size-count.json').write_bytes(run.stdout)
        return json.loads((self.packet / 'files.json').read_bytes())

    def collect(self, head, files):
        name = (__package__ + '.' if __package__ else '') + 'hunk_text'
        self.assertIsNotNone(importlib.util.find_spec(name), 'hunk_text is missing')
        return importlib.import_module(name).collect_hunks(self.repo, self.base, head, files)


class HunkTextTests(OrchardRepo, unittest.TestCase):
    # Cases: additions, deletions, replacement, 2 hunks, ignored kinds,
    # missing final newline, same size with new text, renames and literal paths.
    def test_X1_changed_lines_match_diff_and_keep_real_test_lengths(self):
        self.write('fruit.py', ''.join(f'fruit {n}\n' for n in range(14)))
        self.base = self.commit()
        self.write('fruit.py', ''.join(f'pear {n}\n' if n in (1, 12) else f'fruit {n}\n'
                                     for n in range(14)))
        self.write('tests/grove.py', 'grow\npick')
        head = self.commit()
        files = self.count(head)
        hunks, ops, text = self.collect(head, files)
        self.assertEqual(ops, [])
        self.assertEqual([(h['id'], h['counted'], h['lines'], h['deleted'], h['new_start'],
                           h['new_count']) for h in hunks],
                         [('f1h1', 2, 2, 1, 2, 1), ('f1h2', 2, 2, 1, 13, 1),
                          ('f2h1', 0, 2, 0, 1, 2)])
        self.assertEqual(text['f1h1'], [b'-fruit 1\n', b'+pear 1\n'])
        self.assertEqual(hunks[0]['text_sha256'], hashlib.sha256(b'-fruit 1\n+pear 1\n').hexdigest())
        self.assertEqual([h['id'] for h in hunks],
                         [h['id'] for row in files['files'] for h in row['hunks']])

    def test_X2_same_counts_with_new_text_change_hash(self):
        self.write('fruit.py', 'apple\n')
        head_a = self.commit()
        files = self.count(head_a)
        first, _, _ = self.collect(head_a, files)
        self.write('fruit.py', 'pears\n')
        head_b = self.commit()
        second, _, _ = self.collect(head_b, files)
        self.assertNotEqual(first[0]['text_sha256'], second[0]['text_sha256'])

    def test_X3_moved_head_reports_count_difference(self):
        self.write('fruit.py', 'apple\n')
        files = self.count(self.commit())
        self.write('fruit.py', 'apple\npear\n')
        head = self.commit()
        name = (__package__ + '.' if __package__ else '') + 'hunk_text'
        self.assertIsNotNone(importlib.util.find_spec(name), 'hunk_text is missing')
        module = importlib.import_module(name)
        with self.assertRaisesRegex(module.HunkDifference, 'differ'):
            self.collect(head, files)

    def test_X4_rename_and_binary_get_operations_without_hunks(self):
        self.write('fruit.py', 'apple\n')
        self.base = self.commit()
        self.git('mv', 'fruit.py', 'grove.py')
        self.write('orchard.bin', b'\0fruit')
        head = self.commit()
        hunks, ops, text = self.collect(head, self.count(head))
        self.assertEqual(hunks, [])
        self.assertEqual(text, {})
        self.assertEqual([(op['id'], op['path'], op['counted']) for op in ops],
                         [('f1op', 'grove.py', 0), ('f2op', 'orchard.bin', 0)])
        self.assertEqual(set(ops[0]), set('id path old_path status kind counted lines deleted new_start new_count text_sha256 language'.split()))

    def test_X5_edited_rename_and_literal_path_keep_counter_ids(self):
        self.write('fruit.py', 'apple\n' * 20)
        self.base = self.commit()
        self.git('mv', 'fruit.py', 'grove.py')
        self.write('grove.py', 'pear\n' + 'apple\n' * 19)
        self.write('fruit [1].py', 'pick\n')
        self.write('fruit 1.py', 'grow\ngrow\n')
        head = self.commit()
        files = self.count(head)
        hunks, _, _ = self.collect(head, files)
        self.assertEqual([(h['id'], h['counted']) for h in hunks],
                         [(h['id'], h['counted_lines']) for row in files['files'] for h in row['hunks']])
        renamed = next(h for h in hunks if h['old_path'])
        self.assertEqual((renamed['path'], renamed['old_path'], renamed['counted']),
                         ('grove.py', 'fruit.py', 2))

    def test_carriage_return_inside_line_keeps_git_line_count(self):
        self.write('fruit.py', b'fruit\rpear\n')
        head = self.commit()
        hunks, _, texts = self.collect(head, self.count(head))
        self.assertEqual((hunks[0]['lines'], hunks[0]['counted']), (1, 1))
        self.assertEqual(texts['f1h1'], [b'+fruit\rpear\n'])


if __name__ == '__main__':
    unittest.main()
