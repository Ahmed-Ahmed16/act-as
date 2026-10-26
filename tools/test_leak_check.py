import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


# Cases: no terms/files, 1 or many terms, short IDs, old lines, bad bytes, read errors.
class LeakCheckTests(unittest.TestCase):
    def setUp(self):
        self.tree = tempfile.TemporaryDirectory(prefix='actas-leak-')
        self.addCleanup(self.tree.cleanup)
        self.root = Path(self.tree.name)
        self.write('terms.txt', 'zorblax-corp\n')
        self.write('clean.txt', 'Ordinary public text.\n')

    def write(self, name, text):
        path = self.root / name
        path.write_text(text, encoding='utf-8')
        return path

    def run_check(self, *args):
        return subprocess.run(
            [sys.executable, '-E', '-B', str(Path(__file__).with_name('leak_check.py')), *args],
            cwd=self.root, capture_output=True, text=True, encoding='utf-8', timeout=30)

    def test_planted_term_from_each_of_7_invented_groups_is_found(self):
        terms = ['zorblax-corp', 'quuxpay', 'R99', 'flibber-team',
                 'nimbloo-project', 'wuglet-host', 'ploonix-client']
        self.write('terms.txt', '# invented groups\n\n' + '\n\n'.join(terms) + '\n')
        names = []
        expected = []
        for index, term in enumerate(terms, 1):
            name = f'group{index}.txt'
            names.append(name)
            self.write(name, f'Public heading\nContact {term} here.\n')
            expected.append(f'{name}:2: group-or-term-index {index}')
        run = self.run_check('terms.txt', *names)
        self.assertEqual(run.returncode, 1, run.stderr)
        self.assertEqual(run.stdout.splitlines(), expected + ['total: 7 hits'])
        self.assertEqual(run.stderr, '')
        for term in terms:
            self.assertNotIn(term, run.stdout + run.stderr)

    def test_old_unchanged_line_is_found_after_clean_append(self):
        path = self.write('notes.txt', 'Old zorblax-corp record\n')
        with path.open('a', encoding='utf-8') as stream:
            stream.write('New public line\n')
        run = self.run_check('terms.txt', 'notes.txt')
        self.assertEqual(run.returncode, 1, run.stderr)
        self.assertEqual(run.stdout, 'notes.txt:1: group-or-term-index 1\ntotal: 1 hits\n')

    def test_clean_set_exits_0(self):
        self.write('empty.txt', '')
        run = self.run_check('terms.txt', 'clean.txt', 'empty.txt')
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout, 'total: 0 hits\n')
        self.assertEqual(run.stderr, '')

    def test_invalid_inputs_exit_2_with_safe_reason(self):
        self.write('empty-terms.txt', '\n  \n# comment\n# another comment\n')
        (self.root / 'folder').mkdir()
        cases = [
            (('missing-terms.txt', 'clean.txt'), 'cannot read terms file'),
            (('empty-terms.txt', 'clean.txt'), 'no terms'),
            (('terms.txt',), 'usage:'),
            ((), 'usage:'),
            (('terms.txt', 'zorblax-corp-missing.txt'), 'cannot read candidate file'),
            (('terms.txt', 'folder'), 'cannot read candidate file'),
            (('folder', 'clean.txt'), 'cannot read terms file'),
        ]
        for args, reason in cases:
            with self.subTest(args=args):
                run = self.run_check(*args)
                self.assertEqual(run.returncode, 2, run.stdout + run.stderr)
                self.assertIn(reason, run.stderr)
                self.assertNotIn('zorblax-corp', run.stdout + run.stderr)

    def test_missing_candidate_after_hit_still_exits_2(self):
        self.write('hit.txt', 'zorblax-corp\n')
        run = self.run_check('terms.txt', 'hit.txt', 'missing.txt')
        self.assertEqual(run.returncode, 2, run.stdout + run.stderr)
        self.assertIn('cannot read candidate file', run.stderr)
        self.assertNotIn('zorblax-corp', run.stdout + run.stderr)

    def test_short_ids_require_word_boundaries(self):
        self.write('terms.txt', 'R99\nQ\nA123\n')
        self.write('ids.txt', 'R990 xR99 R99x _R99 R99_\n'
                   'Q2 xQ Qx _Q Q_\nA1234 xA123 A123x\n'
                   '(R99)\nQ!\n[A123]\n')
        run = self.run_check('terms.txt', 'ids.txt')
        self.assertEqual(run.returncode, 1, run.stderr)
        self.assertEqual(run.stdout.splitlines(), [
            'ids.txt:4: group-or-term-index 1',
            'ids.txt:5: group-or-term-index 2',
            'ids.txt:6: group-or-term-index 3', 'total: 3 hits'])

    def test_long_or_punctuated_terms_match_literal_substrings(self):
        self.write('terms.txt', 'quuxpay\nR99-\nz.q\nABCDE\n')
        self.write('text.txt', 'xquuxpayx\nxR99-x\nzXq\nxz.qx\nxABCDEx\n')
        run = self.run_check('terms.txt', 'text.txt')
        self.assertEqual(run.returncode, 1, run.stderr)
        self.assertEqual(run.stdout.splitlines(), [
            'text.txt:1: group-or-term-index 1',
            'text.txt:2: group-or-term-index 2',
            'text.txt:4: group-or-term-index 3',
            'text.txt:5: group-or-term-index 4', 'total: 4 hits'])

    def test_case_is_ignored(self):
        # A name in a lowercase URL or an uppercase heading is still a leak.
        self.write('text.txt', 'ZORBLAX-CORP\nsee zorblax-corp.example\n')
        run = self.run_check('terms.txt', 'text.txt')
        self.assertEqual(run.returncode, 1, run.stderr)
        self.assertEqual(run.stdout.splitlines(), [
            'text.txt:1: group-or-term-index 1',
            'text.txt:2: group-or-term-index 1',
            'total: 2 hits'])

    def test_invalid_utf8_is_replaced_and_whole_file_is_scanned(self):
        (self.root / 'bytes.txt').write_bytes(b'\xff\x00\nzorblax-corp\xff')
        run = self.run_check('terms.txt', 'bytes.txt')
        self.assertEqual(run.returncode, 1, run.stderr)
        self.assertEqual(run.stdout, 'bytes.txt:2: group-or-term-index 1\ntotal: 1 hits\n')

    def test_each_matching_term_on_each_line_is_reported(self):
        self.write('terms.txt', 'zorblax-corp\nquuxpay\n')
        self.write('text.txt', 'zorblax-corp zorblax-corp quuxpay\nquuxpay\n')
        run = self.run_check('terms.txt', 'text.txt')
        self.assertEqual(run.returncode, 1, run.stderr)
        self.assertEqual(run.stdout.splitlines(), [
            'text.txt:1: group-or-term-index 1',
            'text.txt:1: group-or-term-index 2',
            'text.txt:2: group-or-term-index 2', 'total: 3 hits'])


if __name__ == '__main__':
    unittest.main()
