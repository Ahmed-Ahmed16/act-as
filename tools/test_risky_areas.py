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

    def test_missing_directory_and_invalid_utf8_raise_value_error(self):
        (self.repo / 'glorp.txt').write_bytes(b'\xff')
        for filename in ('missing.txt', '.', 'glorp.txt'):
            with self.subTest(filename=filename), self.assertRaises(ValueError):
                self.scan(filename)

    def test_unreadable_file_raises_value_error(self):
        self.write('glorp.txt', 'price')
        with patch.object(Path, 'read_text', side_effect=PermissionError('Zindle denied')):
            with self.assertRaises(ValueError):
                self.scan('glorp.txt')

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
        for args in ([], ['--repo', str(self.repo), '--files', 'missing.txt']):
            with self.subTest(args=args):
                run = subprocess.run([sys.executable, '-B', str(self.script), *args],
                                     capture_output=True, text=True, encoding='utf-8')
                self.assertEqual(run.returncode, 2)
                self.assertEqual(run.stdout, '')
                self.assertTrue(run.stderr.strip())


if __name__ == '__main__':
    unittest.main()
