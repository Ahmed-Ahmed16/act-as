import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# Fake secrets are built at run time so this file stays clean under its own scan.
FAKE_TOKEN = 'gh' + 'p_' + 'A1b2C3d4' * 5
FAKE_KEY = '-----BEGIN ' + 'RSA PRIVATE KEY-----'
FAKE_PATH = 'D:' + '\\work-projects\\site'
FAKE_MAIL = 'someone' + '@' + 'company.com'


class ScrubTests(unittest.TestCase):
    def setUp(self):
        self.tree = tempfile.TemporaryDirectory(prefix='actas-scrub-')
        self.addCleanup(self.tree.cleanup)
        self.root = Path(self.tree.name)
        self.write('README.md', 'Clean text.\nSee https://example.org/page and noreply@anthropic.com.\n')

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')

    def git(self, *args):
        subprocess.run(['git', '-C', str(self.root), '-c', 'user.name=t', '-c', 'user.email=t@example.com', *args],
                       capture_output=True, check=True)

    def run_scrub(self, *args):
        return subprocess.run([sys.executable, '-E', '-B', str(Path(__file__).with_name('scrub.py')), str(self.root), *args],
                              capture_output=True, text=True, encoding='utf-8', timeout=30)

    def test_known_pass_clean_tree_exits_0(self):
        run = self.run_scrub()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertEqual(run.stdout, 'total: 0 findings\n')

    def test_known_fail_each_kind_is_found_and_value_never_printed(self):
        cases = [('token.md', f'x = {FAKE_TOKEN}\n', 'github token'), ('key.pem', FAKE_KEY + '\n', 'private key'),
                 ('path.md', f'Clone at {FAKE_PATH}\n', 'private path'), ('mail.md', f'Ask {FAKE_MAIL}\n', 'email')]
        for name, text, kind in cases:
            self.write(name, text)
        run = self.run_scrub()
        self.assertEqual(run.returncode, 1, run.stderr)
        for name, _, kind in cases:
            with self.subTest(kind=kind):
                self.assertIn(f'{name}:1: {kind}\n', run.stdout)
        for value in (FAKE_TOKEN, FAKE_PATH, FAKE_MAIL):
            self.assertNotIn(value, run.stdout)
        self.assertEqual(run.stdout.splitlines()[-1], 'total: 4 findings')

    def test_git_folder_is_skipped(self):
        self.write('.git/config', f'token = {FAKE_TOKEN}\n')
        run = self.run_scrub()
        self.assertEqual(run.returncode, 0, run.stdout)

    def test_commit_scan_reads_the_commit_not_the_working_tree(self):
        self.git('init', '-q')
        self.write('notes.md', f'x = {FAKE_TOKEN}\n')
        self.git('add', '.')
        self.git('commit', '-q', '-m', 'one')
        self.write('notes.md', 'cleaned in the working tree only\n')
        run = self.run_scrub('--commit', 'HEAD')
        self.assertEqual(run.returncode, 1, run.stderr)
        self.assertIn('notes.md:1: github token\n', run.stdout)
        self.assertTrue(run.stdout.startswith('scrub.py: commit '))
        self.assertEqual(self.run_scrub().returncode, 0)

    def test_bad_arguments_exit_2(self):
        for args in [('--commit',), ('--commit', 'nope'), ('--other', 'HEAD')]:
            with self.subTest(args=args):
                run = self.run_scrub(*args)
                self.assertEqual(run.returncode, 2)
                self.assertEqual(len(run.stderr.splitlines()), 1)


if __name__ == '__main__':
    unittest.main()
