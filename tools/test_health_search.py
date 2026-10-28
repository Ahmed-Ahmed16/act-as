# Cases: route forms, 9 and 10 route lines, path escape, new and old copies.
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import health_search


class HealthSearchTests(unittest.TestCase):
    def setUp(self):
        self.tree = tempfile.TemporaryDirectory(prefix='Acme')
        self.addCleanup(self.tree.cleanup)
        self.root = Path(self.tree.name)
        self.repo = self.root / 'shop'
        self.repo.mkdir()
        self.script = Path(__file__).with_name('health_search.py')
        self.env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull,
                        GIT_CONFIG_NOSYSTEM='1', PYTHONDONTWRITEBYTECODE='1')
        self.git('init', '-b', 'main')
        self.git('config', 'user.name', 'Acme')
        self.git('config', 'user.email', 'shop@acme.invalid')

    def git(self, *args):
        run = subprocess.run(['git', '-c', 'core.autocrlf=false',
                              '-c', 'commit.gpgsign=false', '-C', str(self.repo), *args],
                             capture_output=True, text=True, encoding='utf-8', env=self.env)
        self.assertEqual(run.returncode, 0, run.stderr)
        return run.stdout.strip()

    def write(self, path, text):
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding='utf-8')

    def commit(self):
        self.git('add', '-A')
        self.git('commit', '--allow-empty', '-m', 'Acme')
        return self.git('rev-parse', 'HEAD')

    def run_cli(self, *args):
        return subprocess.run([sys.executable, '-B', str(self.script), *map(str, args)],
                              capture_output=True, text=True, encoding='utf-8', env=self.env)

    def document(self, *args):
        run = self.run_cli(*args)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stderr, '')
        self.assertEqual(len(run.stdout.splitlines()), 1)
        document = json.loads(run.stdout)
        self.assertTrue(document['reason'])
        return document

    def copies(self, base, head, *literals):
        args = ['copies', '--repo', self.repo, '--base', base, '--head', head]
        for literal in literals:
            args.extend(['--literal', literal])
        return self.document(*args)

    def test_acme_routes_count_lines_resources_and_class_boundaries(self):
        self.write('app/Card.php', '<?php class Card {}')
        self.write('app/Acme.php', '<?php class Acme {}')
        lines = ["<?php", "Route::get('shop', [Card::class, 'shop']);",
                 "Route::resource('shop', Card::class);",
                 "Route::apiResource('shop', Card::class);",
                 "Route::match(['get'], 'shop', 'Card@shop');",
                 'Route::any("shop", "Card@shop");',
                 "Route::post('shop', [AcmeCard::class, 'shop']);",
                 '$shop = Card::class;', "Route::get('shop', Card::class); Route::post('shop', Card::class);"]
        self.write('routes/web.php', '\n'.join(lines))
        self.write('routes/api.php', "Route::get('shop', [Card::class, 'shop']);")
        self.write('routes/shop/Acme.php', 'Route::any(Card::class);')
        document = self.document('routes', '--repo', self.repo, '--files',
                                 'app/Card.php', 'app/Acme.php')
        self.assertEqual(document['result'], 'clean')
        self.assertEqual(document['reason'], 'counts only, a number is a pointer')
        card, acme = document['controllers']
        self.assertEqual((card['file'], card['class'], card['route_lines'],
                          card['resource_lines']), ('app/Card.php', 'Card', 7, 2))
        self.assertEqual(card['where'], ['routes/api.php:1'] +
                         [f'routes/web.php:{n}' for n in (2, 3, 4, 5, 6, 9)])
        self.assertIn('higher', card['note'])
        self.assertEqual((acme['route_lines'], acme['resource_lines'], acme['where']),
                         (0, 0, []))

    def test_route_pointer_starts_at_10_lines(self):
        self.write('app/GlorpController.php', '<?php class GlorpController {}')
        for count, expected in ((9, False), (10, True)):
            with self.subTest(route_lines=count):
                lines = [f"Route::get('zindle{n}', [GlorpController::class, 'floop']);"
                         for n in range(count - 1)]
                lines.append("Route::resource('plim', GlorpController::class);")
                self.write('routes/web.php', '\n'.join(lines))
                document = self.document('routes', '--repo', self.repo, '--files',
                                         'app/GlorpController.php')
                controller = document['controllers'][0]
                self.assertEqual(controller['route_lines'], count)
                self.assertIs(controller.get('pointer'), expected)
                self.assertEqual(document['pointer_threshold'], 10)
                self.assertEqual(document['result'], 'clean')
                self.assertEqual(controller['resource_lines'], 1)
                self.assertEqual(controller['note'],
                                 'resource lines count as 1; the real route count is higher')

    def test_acme_new_lists_and_limits_name_both_paths_with_lines(self):
        for literal in ("['Acme', 'Card']", '5120', 'foo'):
            with self.subTest(literal=literal):
                self.write('app/Card.php', '\n' + literal + '\n')
                self.write('config/shop.php', '')
                base = self.commit()
                self.write('config/shop.php', literal + '\n')
                head = self.commit()
                self.git('checkout', base)
                document = self.copies(base, head, literal)
                self.assertEqual(document['result'], 'finding')
                self.assertEqual(document['reading_needed'], 'both copies must express the same rule')
                self.assertEqual(document['summary'], [dict(literal=literal, copy_count=2,
                                 new_copies=1, old_copies=1, result='finding')])
                self.assertEqual(document['literals'][0]['copies'], [
                    dict(path='app/Card.php', line=2, at_base=True, in_config=False,
                         in_lang=False, in_test=False),
                    dict(path='config/shop.php', line=1, at_base=False, in_config=True,
                         in_lang=False, in_test=False)])
                self.git('checkout', 'main')

    def test_copy_cap_never_classifies_partial_base_or_head_counts(self):
        # Cases: base overflow, head overflow, both overflow, much larger output.
        for base_count, head_count in ((3, 2), (2, 3), (3, 3), (1000, 1000)):
            with self.subTest(base=base_count, head=head_count):
                self.write('app/Card.php', 'foo\n' * base_count)
                base = self.commit()
                self.write('app/Card.php', 'foo\n' * head_count)
                head = self.commit()
                args = SimpleNamespace(repo=self.repo, base=base, head=head,
                                       literal=['foo', 'absent'])
                with patch.object(health_search, 'MAX_ROWS', 2):
                    document = health_search.copies(args)
                summary = document['summary'][0]
                self.assertEqual(document['result'], 'not checked')
                self.assertTrue(summary['incomplete'])
                self.assertEqual(summary['result'], 'not checked')
                self.assertIn('cap', summary['reason'])
                self.assertIn('2', summary['reason'])
                self.assertEqual(document['literals'][0]['copies'], [])
                for key in ('copy_count', 'new_copies', 'old_copies', 'old_only'):
                    self.assertNotIn(key, summary)
                self.assertEqual(document['summary'][1]['result'], 'clean')
                self.assertLess(len(json.dumps(document)), 1000)

    def test_finding_on_1_literal_wins_over_a_capped_literal(self):
        self.write('app/Card.php', 'foo\n' * 3 + 'rule\n')
        base = self.commit()
        self.write('config/shop.php', 'rule\n')
        head = self.commit()
        args = SimpleNamespace(repo=self.repo, base=base, head=head, literal=['foo', 'rule'])
        with patch.object(health_search, 'MAX_ROWS', 2):
            document = health_search.copies(args)
        self.assertEqual(document['summary'][0]['result'], 'not checked')
        self.assertEqual(document['summary'][1]['result'], 'finding')
        self.assertEqual(document['result'], 'finding')

    def test_up_to_cap_keeps_complete_counts_and_test_rows(self):
        # Cases: below cap, exactly cap; test rows have their own space.
        for count in (1, 2):
            with self.subTest(count=count):
                self.write('tests/Card.php', 'foo\n' * 2)
                self.write('zapp/Card.php', 'foo\n' * count)
                head = self.commit()
                args = SimpleNamespace(repo=self.repo, base=head, head=head, literal=['foo'])
                with patch.object(health_search, 'MAX_ROWS', 2):
                    document = health_search.copies(args)
                self.assertEqual(document['result'], 'clean')
                self.assertEqual(document['summary'][0]['copy_count'], count)
                self.assertEqual(document['summary'][0]['old_copies'], count + 2)
                self.assertEqual(document['summary'][0]['new_copies'], 0)
                self.assertEqual(len(document['literals'][0]['copies']), count + 2)

    def test_grep_stops_reading_and_reaps_the_process_at_the_cap(self):
        # The process boundary is mocked to catch reading beyond the overflow row.
        for path in ('app/Card.php', 'tests/Card.php', 'app/Card\nName.php'):
            with self.subTest(path=path):
                def lines():
                    for number in range(1, 4):
                        yield from f'HEAD:{path}\0{number}\0foo\n'.encode('utf-8').splitlines(
                            keepends=True)
                    self.fail('grep output was read past the cap')

                process = MagicMock()
                process.__enter__.return_value = process
                process.stdout = lines()
                process.returncode = -9
                process.poll.return_value = -9
                with patch.object(health_search, 'MAX_ROWS', 2), patch.object(
                        health_search.subprocess, 'Popen', return_value=process):
                    rows, incomplete = health_search.occurrences(self.repo, 'HEAD', 'foo')
                self.assertEqual(rows, [(path, 1), (path, 2)])
                self.assertTrue(incomplete)
                process.kill.assert_called_once_with()
                process.wait.assert_called_once_with()

    def test_grep_failure_keeps_the_existing_error_style(self):
        self.write('app/Card.php', 'foo')
        self.commit()
        with self.assertRaisesRegex(ValueError, '^git failed:'):
            health_search.occurrences(self.repo, 'missing-ref', 'foo')

    def test_short_literals_use_the_existing_cli_error_shape(self):
        self.write('app/Card.php', 'foo')
        head = self.commit()
        for literal in (' ', '$a', '64', '10', '1', '  ab  '):
            with self.subTest(literal=literal):
                run = self.run_cli('copies', '--repo', self.repo, '--base', head,
                                   '--head', head, '--literal', literal)
                self.assertEqual(run.returncode, 2)
                self.assertEqual(run.stdout, '')
                self.assertEqual(run.stderr.strip(),
                                 'literal must be at least 3 characters after strip() and on 1 line')

    def test_acme_g18_existing_file_counts_only_extra_copies_as_new(self):
        # G18 cases: added copies, unchanged copies, fewer copies, no copies.
        cases = [(1, 2, 1, 1, [True, False], 'finding'),
                 (2, 4, 2, 2, [True, True, False, False], 'finding'),
                 (2, 2, 0, 2, [True, True], 'clean'),
                 (2, 1, 0, 1, [True], 'clean'),
                 (1, 0, 0, 0, [], 'clean')]
        for base_count, head_count, new, old, at_base, result in cases:
            with self.subTest(base=base_count, head=head_count):
                self.write('app/Card.php', '5120\n' * base_count)
                base = self.commit()
                self.write('app/Card.php', 'Acme\n' + '5120\n' * head_count)
                document = self.copies(base, self.commit(), '5120')
                summary = document['summary'][0]
                self.assertEqual(summary['new_copies'], new)
                self.assertEqual(summary['old_copies'], old)
                self.assertEqual(summary['copy_count'], head_count)
                self.assertEqual(summary['result'], result)
                self.assertEqual(document['result'], result)
                self.assertEqual(summary.get('old_only', False), head_count == 2 and new == 0)
                copies = document['literals'][0]['copies']
                self.assertEqual([row['at_base'] for row in copies], at_base)
                self.assertEqual([row['line'] for row in copies],
                                 list(range(2, head_count + 2)))

    def test_acme_touching_old_copy_is_clean_with_old_only(self):
        for path in ('app/Card.php', 'app/Acme.php'):
            self.write(path, '5120\n')
        base = self.commit()
        self.write('app/Card.php', 'Acme\n5120\n')
        document = self.copies(base, self.commit(), '5120')
        self.assertEqual(document['result'], 'clean')
        self.assertEqual(document['summary'], [dict(literal='5120', copy_count=2,
                         new_copies=0, old_copies=2, result='clean', old_only=True)])

    def test_acme_no_copy_and_different_lists_are_clean(self):
        self.write('app/Card.php', "['Acme', 'Card']\n")
        self.write('app/Acme.php', "['Acme', 'shop']\n")
        head = self.commit()
        document = self.copies(head, head, 'Card shop', "['Acme', 'Card']",
                               "['Acme', 'shop']")
        self.assertEqual(document['result'], 'clean')
        self.assertEqual([row['copy_count'] for row in document['summary']], [0, 1, 1])
        self.assertEqual([row['result'] for row in document['summary']], ['clean'] * 3)

    def test_acme_flags_skips_tests_and_fixed_string(self):
        self.write('app/Card.php', 'Acme.*\n')
        base = self.commit()
        for path in ('config/shop.php', 'lang/shop.php', 'resources/lang/shop.php',
                     'tests/Card.php', 'vendor/Card.php', 'node_modules/Card.php',
                     'storage/Card.php'):
            self.write(path, 'Acme.*\n')
        self.write('app/Acme.php', 'Acme other\n')
        head = self.commit()
        document = self.copies(base, head, 'Acme.*')
        copies = {row['path']: row for row in document['literals'][0]['copies']}
        self.assertEqual(set(copies), {'app/Card.php', 'config/shop.php', 'lang/shop.php',
                                     'resources/lang/shop.php', 'tests/Card.php'})
        self.assertTrue(copies['config/shop.php']['in_config'])
        self.assertTrue(copies['lang/shop.php']['in_lang'])
        self.assertTrue(copies['resources/lang/shop.php']['in_lang'])
        self.assertTrue(copies['tests/Card.php']['in_test'])
        self.assertEqual(document['summary'][0]['copy_count'], 4)
        self.assertEqual(document['summary'][0]['new_copies'], 3)
        document = self.copies(head, head, 'Acme.*')
        self.assertEqual(document['summary'][0]['old_copies'], 5)

    def test_acme_test_copy_alone_never_becomes_a_finding(self):
        self.write('app/Card.php', '5120\n')
        base = self.commit()
        self.write('tests/Card.php', '5120\n')
        document = self.copies(base, self.commit(), '5120')
        self.assertEqual(document['result'], 'clean')
        self.assertEqual(document['summary'][0]['copy_count'], 1)
        self.assertEqual(document['summary'][0]['new_copies'], 0)

    def test_acme_empty_multiline_and_nul_literals_are_rejected(self):
        # NUL cannot be passed through subprocess arguments.
        for literal in ('', '64\n10', '64\r10', '64\0'):
            with self.subTest(literal=literal):
                with self.assertRaises(ValueError):
                    health_search.copies(SimpleNamespace(literal=['foo', literal]))

    def test_acme_bad_paths_refs_literals_and_arguments_have_1_error_line(self):
        self.write('app/Card.php', 'Acme')
        head = self.commit()
        (self.root / 'Card.php').write_text('Acme', encoding='utf-8')
        for args in [(), ('routes', '--repo', self.repo, '--files', '../Card.php'),
                     ('routes', '--repo', self.repo, '--files', self.root / 'Card.php'),
                     ('routes', '--repo', self.repo, '--files', 'app/shop.php'),
                     ('copies', '--repo', self.repo, '--base', 'Acme', '--head', head,
                      '--literal', '5120'),
                     ('copies', '--repo', self.repo, '--base', head, '--head', 'Acme',
                      '--literal', '5120'),
                     ('copies', '--repo', self.repo, '--base', head, '--head', head,
                      '--literal', '')]:
            with self.subTest(args=args):
                run = self.run_cli(*args)
                self.assertEqual(run.returncode, 2, run.stderr)
                self.assertEqual(run.stdout, '')
                self.assertEqual(len(run.stderr.splitlines()), 1, run.stderr)


if __name__ == '__main__':
    unittest.main()
