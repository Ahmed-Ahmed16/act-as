# Cases: route forms, 9 and 10 route lines, path escape, new and old copies.
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

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
        # N4 cases: 1 character, 2 digits, whitespace, longer fixed text.
        for literal in ("['Acme', 'Card']", '5120', '64', '10', '1', ' '):
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
                    health_search.copies(SimpleNamespace(literal=['64', literal]))

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
