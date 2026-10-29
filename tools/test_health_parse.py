# Cases: clean, findings, stale entries, failed scans, bad input, bad arguments.
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class HealthParseTests(unittest.TestCase):
    def setUp(self):
        self.tree = tempfile.TemporaryDirectory(prefix='Acme')
        self.addCleanup(self.tree.cleanup)
        self.root = Path(self.tree.name)
        self.output = self.root / 'shop.txt'
        self.report = self.root / 'shop.json'
        self.script = Path(__file__).with_name('health_parse.py')

    def run_cli(self, *args):
        return subprocess.run([sys.executable, '-B', str(self.script), *map(str, args)],
                              capture_output=True, text=True, encoding='utf-8')

    def parse(self, tool, text='', code=0, *extra):
        self.output.write_text(text, encoding='utf-8')
        run = self.run_cli(tool, '--output', self.output, '--exit', code, *extra)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stderr, '')
        self.assertEqual(len(run.stdout.splitlines()), 1)
        document = json.loads(run.stdout)
        self.assertTrue(document['reason'])
        return document

    def test_acme_phpstan_clean_and_unknown_output(self):
        self.assertEqual(self.parse('phpstan')['result'], 'clean')
        for code in (0, 1):
            with self.subTest(code=code):
                document = self.parse('phpstan', 'Acme could not start', code)
                self.assertEqual(document['result'], 'not checked')
                if code == 1:
                    self.assertEqual(document['reason'],
                                     'exit 1 with output that could not be read')

    def test_acme_phpstan_boot_syntax_and_bad_exits(self):
        for text, code, reason in [
                ('Application bootstrap failed', 1, 'Application bootstrap failed'),
                ('Laravel framework bootstrap failed', 1, 'Laravel framework bootstrap failed'),
                ('No files found to analyse', 1, 'No files found to analyse'),
                ('shop.php:3:Syntax error, unexpected EOF', 1, 'syntax'),
                ('shop.php:4:Parse error: unexpected token', 1, 'syntax'),
                ('shop.php:2:Acme error', 255, '255')]:
            with self.subTest(text=text, code=code):
                document = self.parse('phpstan', text, code)
                self.assertEqual(document['result'], 'not checked')
                self.assertIn(reason.lower(), document['reason'].lower())

    def test_acme_phpstan_real_errors_preserve_windows_path_and_unknown_line(self):
        document = self.parse('phpstan', 'C:/shop/Card.php:12:Acme: missing card\n'
                              'shop.php:?:Acme missing shop\n', 1)
        self.assertEqual(document['result'], 'finding')
        self.assertEqual(document['errors'], [
            {'path': 'C:/shop/Card.php', 'line': 12, 'message': 'Acme: missing card'},
            {'path': 'shop.php', 'line': None, 'message': 'Acme missing shop'}])

    def test_acme_phpstan_stale_only_and_mixed(self):
        stale = 'shop.php:?:Ignored error pattern #Acme# was not matched in reported errors.\n'
        document = self.parse('phpstan', stale * 2, 1)
        self.assertEqual((document['result'], document['stale_baseline']), ('clean', 2))
        self.assertIn('stale', document['reason'])
        document = self.parse('phpstan', stale + 'shop.php:7:Acme error', 1)
        self.assertEqual((document['result'], document['stale_baseline']), ('finding', 1))
        self.assertEqual(len(document['errors']), 1)

    def test_acme_phpmd_empty_scan_and_clean(self):
        document = self.parse('phpmd', '', 0, '--files', 0)
        self.assertEqual(document['result'], 'not checked')
        self.assertEqual(document['reason'], 'PHPMD was given 0 PHP files')
        self.assertEqual(self.parse('phpmd', '', 0, '--files', 2)['result'], 'clean')

    def test_acme_phpmd_raw_lines_and_deprecation(self):
        lines = ['C:/shop/Card.php:12 Acme rule: card', 'shop.php:4\tAcme\tshop']
        document = self.parse('phpmd', 'Deprecated: Acme\n' + '\n'.join(lines),
                              2, '--files', 2)
        self.assertEqual(document['result'], 'finding')
        self.assertEqual(document['violations'], lines)
        self.assertEqual(self.parse('phpmd', 'Acme failed', 2,
                                    '--files', 2)['result'], 'not checked')

    def test_acme_phpmd_failed_exits_name_first_useful_line(self):
        for code in (1, 3, 255, 4):
            with self.subTest(code=code):
                document = self.parse('phpmd', 'Deprecated: Acme\nAcme failed\nshop',
                                      code, '--files', 1)
                self.assertEqual(document['result'], 'not checked')
                self.assertIn(str(code), document['reason'])
                self.assertIn('Acme failed', document['reason'])

    def test_acme_jscpd_sources_clones_and_exit_precedence(self):
        for sources, clones, code, expected in [
                (0, 0, 0, 'not checked'), (0, 3, 1, 'not checked'),
                (2, 0, 0, 'clean'), (2, 1, 1, 'finding'),
                (2, 1, 0, 'finding'), (2, 0, 1, 'finding'),
                (2, 1, 2, 'not checked'), (2, 0, 3, 'not checked'),
                (2, 1, 3, 'finding')]:
            with self.subTest(sources=sources, clones=clones, code=code):
                self.report.write_text(json.dumps({'statistics': {'total': {
                    'sources': sources, 'clones': clones}}}), encoding='utf-8')
                document = self.parse('jscpd', '', code, '--report', self.report)
                self.assertEqual(document['result'], expected)
                if sources == 0:
                    self.assertEqual(document['reason'], 'jscpd scanned 0 PHP files')
                if expected in ('clean', 'finding'):
                    self.assertEqual(document['sources'], sources)
                if expected == 'finding':
                    self.assertEqual(document['clones'], clones)

    def test_acme_jscpd_missing_empty_invalid_and_bad_counts(self):
        for raw in (None, '', 'Acme', '{}', '[]',
                    '{"statistics":{"total":{"sources":true,"clones":0}}}',
                    '{"statistics":{"total":{"sources":2,"clones":-1}}}'):
            with self.subTest(raw=raw):
                if raw is not None:
                    self.report.write_text(raw, encoding='utf-8')
                document = self.parse('jscpd', "git ref 'Acme' not found\nshop", 1,
                                      '--report', self.report)
                self.assertEqual(document['result'], 'not checked')
                self.assertIn("git ref 'Acme' not found", document['reason'])

    def test_acme_bad_input_and_arguments_have_1_error_line(self):
        self.output.write_bytes(b'\xff')
        for args in [(), ('phpstan', '--output', self.root / 'Card', '--exit', 0),
                     ('phpstan', '--output', self.output, '--exit', 0),
                     ('phpmd', '--output', self.output, '--exit', 0),
                     ('phpmd', '--output', self.output, '--exit', 0, '--files', -1),
                     ('jscpd', '--output', self.output, '--exit', 0),
                     ('phpstan', '--exit', 'Acme')]:
            with self.subTest(args=args):
                run = self.run_cli(*args)
                self.assertEqual(run.returncode, 2)
                self.assertEqual(run.stdout, '')
                self.assertEqual(len(run.stderr.splitlines()), 1, run.stderr)


if __name__ == '__main__':
    unittest.main()
