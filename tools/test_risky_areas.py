# Cases: content/path hits, word boundaries, empty files, invalid paths and reads, CLI.
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import risky_areas


class RiskyAreasTests(unittest.TestCase):
    def setUp(self):
        self.tree = tempfile.TemporaryDirectory(prefix='Zindle')
        self.addCleanup(self.tree.cleanup)
        self.repo = Path(self.tree.name) / 'plim'
        self.repo.mkdir()
        self.script = Path(__file__).with_name('risky_areas.py')

    def write(self, filename, text):
        path = self.repo / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
        return path

    def scan(self, *files):
        document = risky_areas.scan(SimpleNamespace(repo=self.repo, files=files))
        self.assertEqual(document['not_checked'],
                         ['business risky areas: not asked: health run only'])
        self.assertTrue(document['reason'])
        return document

    def test_content_words_report_each_kind_with_line_evidence(self):
        cases = {
            'money': ('price amount total currency charge refund payment invoice '
                      'balance checkout tax discount wallet').split(),
            'logins': ('login logout password auth session token credential sign_in '
                       'signin permission role').split(),
            'delete': ['delete', 'destroy', 'forceDelete', 'drop table', 'truncate',
                       'unlink', 'rmtree', 'remove', 'purge'],
        }
        for kind, words in cases.items():
            for word in words:
                with self.subTest(kind=kind, word=word):
                    line = f'  // {word.upper()} changed  '
                    self.write('glorp.php', '\n' + line + '\n')
                    document = self.scan('glorp.php')
                    self.assertEqual(document['result'], 'lead')
                    self.assertEqual(document['kinds_found'], [kind])
                    self.assertEqual(document['areas'], [dict(
                        kind=kind, file='glorp.php', line=2, evidence=line.strip())])

    def test_plain_content_and_similar_words_are_clean(self):
        self.write('glorp.css', 'author: Zindle; color: plum; autotal: 3;\nhello\n')
        document = self.scan('glorp.css')
        self.assertEqual(document['result'], 'clean')
        self.assertEqual(document['areas'], [])
        self.assertEqual(document['kinds_found'], [])

    # Cases: name humps, path humps, lowercase runs, all caps runs, snake case.
    def test_camel_case_content_and_payment_path_keep_exact_lines(self):
        filename = 'app/Http/PaymentController.php'
        self.write(filename, '<?php\nfunction refundOrder(){}\nclass RefundService {}\n'
                   'function deleteAccount(){}\nchargeCard();\ngetTotalPrice();\n'
                   'Session::flush();\n$u->delete();\n')
        document = self.scan(filename)
        self.assertEqual(document['result'], 'lead')
        self.assertEqual([(area['kind'], area['line']) for area in document['areas']],
                         [('money', 1), ('money', 2), ('money', 3), ('delete', 4),
                          ('money', 5), ('money', 6), ('logins', 7), ('delete', 8)])
        self.assertTrue(all(area['file'] == filename for area in document['areas']))
        self.write('glorp.php', 'getprice author TOTALS\nget_total_price();\n$u->delete();\n')
        self.assertEqual([(area['kind'], area['line'])
                          for area in self.scan('glorp.php')['areas']],
                         [('money', 2), ('delete', 3)])

    # Cases: missing/bad bytes alone or together, readable clean, mixed hits below.
    def test_unreadable_without_hits_is_not_checked(self):
        (self.repo / 'glorp.txt').write_bytes(b'\xff')
        self.write('plain.txt', 'hello\n')
        for files, failed in [(('app/Gone.php',), 1), (('glorp.txt',), 1),
                              (('app/Gone.php', 'glorp.txt', 'plain.txt'), 2),
                              (('plain.txt',), 0)]:
            with self.subTest(files=files):
                run = subprocess.run([sys.executable, '-B', str(self.script), '--repo',
                                      str(self.repo), '--files', *files],
                                     capture_output=True, text=True, encoding='utf-8')
                self.assertEqual((run.returncode, run.stderr), (0, ''))
                document = json.loads(run.stdout)
                self.assertEqual(document['result'], 'not checked' if failed else 'clean')
                self.assertEqual(document['areas'], [])
                if failed:
                    self.assertEqual(document['reason'],
                                     f'could not read {failed} requested file(s); open them yourself')
                    self.assertEqual(len(document['not_checked']), failed + 1)
                    for filename in files[:failed]:
                        self.assertTrue(any(entry.startswith(f'cannot read file {filename}: ')
                                            for entry in document['not_checked']))

    def test_path_words_report_candidates_even_for_empty_files(self):
        for filename, kind in (('PRICE/glorp.txt', 'money'),
                               ('glorp_password.txt', 'logins'),
                               ('purge/glorp.txt', 'delete')):
            for text in ('hello\n', ''):
                with self.subTest(filename=filename, text=text):
                    self.write(filename, text)
                    document = self.scan(filename)
                    self.assertEqual(document['result'], 'lead')
                    self.assertEqual(document['kinds_found'], [kind])
                    self.assertEqual(document['areas'], [dict(
                        kind=kind, file=filename, line=1, evidence=text.strip())])

    def test_multiple_kinds_and_files_keep_their_locations(self):
        self.write('glorp.php', '$price = 3;\npassword(); destroy();\n')
        self.write('zindle.php', '// refund\n')
        document = self.scan('glorp.php', 'zindle.php')
        self.assertEqual(document['result'], 'lead')
        self.assertEqual(set(document['kinds_found']), {'money', 'logins', 'delete'})
        self.assertEqual(document['areas'], [
            dict(kind='money', file='glorp.php', line=1, evidence='$price = 3;'),
            dict(kind='logins', file='glorp.php', line=2, evidence='password(); destroy();'),
            dict(kind='delete', file='glorp.php', line=2, evidence='password(); destroy();'),
            dict(kind='money', file='zindle.php', line=1, evidence='// refund'),
        ])

    def test_evidence_is_stripped_then_limited_to_120_characters(self):
        line = 'refund ' + 'z' * 150
        self.write('glorp.txt', '   ' + line + '   \n')
        self.assertEqual(self.scan('glorp.txt')['areas'][0]['evidence'], line[:120])

    def test_only_requested_files_are_read(self):
        self.write('glorp.txt', '')
        self.write('zindle.txt', 'payment password delete')
        self.assertEqual(self.scan('glorp.txt')['areas'], [])

    def test_escaping_and_absolute_paths_raise_value_error(self):
        outside = self.repo.parent / 'zindle.txt'
        outside.write_text('price', encoding='utf-8')
        inside = self.write('glorp.txt', 'price')
        for filename in ('../zindle.txt', '../missing.txt', str(outside), str(inside)):
            with self.subTest(filename=filename), self.assertRaises(ValueError):
                self.scan(filename)

    def test_unreadable_files_are_reported_without_losing_readable_results(self):
        # G32: missing, directory, binary; readable files before and after each skip.
        (self.repo / 'glorp.txt').write_bytes(b'\xff')
        self.write('before.php', 'price')
        self.write('after.php', 'password')
        for filename in ('missing.txt', '.', 'glorp.txt'):
            with self.subTest(filename=filename):
                run = subprocess.run([sys.executable, '-B', str(self.script), '--repo',
                                      str(self.repo), '--files', 'before.php', filename,
                                      'after.php'], capture_output=True, text=True,
                                     encoding='utf-8')
                self.assertEqual(run.returncode, 0, run.stderr)
                self.assertEqual(run.stderr, '')
                document = json.loads(run.stdout)
                self.assertEqual(document['result'], 'lead')
                self.assertEqual(document['areas'], [
                    dict(kind='money', file='before.php', line=1, evidence='price'),
                    dict(kind='logins', file='after.php', line=1, evidence='password')])
                self.assertEqual(document['kinds_found'], ['money', 'logins'])
                self.assertEqual(len(document['not_checked']), 2)
                self.assertTrue(document['not_checked'][1].startswith(
                    f'cannot read file {filename}: '))

    def test_permission_denied_file_is_reported_as_not_checked(self):
        self.write('glorp.txt', 'price')
        with patch.object(Path, 'read_text', side_effect=PermissionError('Zindle denied')):
            document = risky_areas.scan(SimpleNamespace(repo=self.repo, files=['glorp.txt']))
        self.assertEqual(document['areas'], [])
        self.assertEqual(document['not_checked'], [
            'business risky areas: not asked: health run only',
            'cannot read file glorp.txt: Zindle denied'])

    def test_cli_returns_json_and_exit_0(self):
        self.write('glorp.php', '$price = 3;\n')
        run = subprocess.run([sys.executable, '-B', str(self.script), '--repo',
                              str(self.repo), '--files', 'glorp.php'],
                             capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stderr, '')
        document = json.loads(run.stdout)
        self.assertEqual(document['result'], 'lead')
        self.assertEqual(document['kinds_found'], ['money'])
        self.assertEqual(document['not_checked'],
                         ['business risky areas: not asked: health run only'])

    def test_cli_bad_input_returns_exit_2_without_json(self):
        for args in ([], ['--repo', str(self.repo / 'missing'), '--files', 'glorp.txt'],
                     ['--repo', str(self.repo), '--files', '../outside.txt']):
            with self.subTest(args=args):
                run = subprocess.run([sys.executable, '-B', str(self.script), *args],
                                     capture_output=True, text=True, encoding='utf-8')
                self.assertEqual(run.returncode, 2)
                self.assertEqual(run.stdout, '')
                self.assertTrue(run.stderr.strip())


if __name__ == '__main__':
    unittest.main()
