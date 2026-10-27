"""Test language folders only, no network.

Inputs: required --lang, optional --changed-files JSON path list, --report values,
and --base-lang comparison folder (requires --report values). Default output is
a JSON gap list. Values output has gaps, values, placeholder_gaps, no_letters,
locales_not_checked_for_letters, and changed_old_values. Exit 0 means a report
was printed. Bad inputs exit 2 with 1 stderr line and no stdout.
"""

import ast
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class TranslationKeyTests(unittest.TestCase):
    def setUp(self):
        self.tree = tempfile.TemporaryDirectory(prefix='actas-keys-')
        self.addCleanup(self.tree.cleanup)
        self.root = Path(self.tree.name)
        self.lang = self.root / 'lang'
        self.lang.mkdir()
        self.script = Path(__file__).with_name('translation_keys.py').resolve()

    def write(self, relative, text):
        path = self.lang / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
        return path

    def run_cli(self, *args):
        return subprocess.run([sys.executable, '-E', '-P', '-X', 'utf8', '-B', str(self.script), *map(str, args)],
                              capture_output=True, text=True, encoding='utf-8', timeout=10)

    def entries(self, *args):
        run = self.run_cli('--lang', self.lang, *args)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stderr, '')
        return json.loads(run.stdout)

    def test_planted_gap_lists_whole_json_key_and_all_fields(self):
        self.write('ava.json', '{"zora.message": "A", "luma": "B"}')
        self.write('bex.json', '{"luma": "C"}')
        self.assertEqual(self.entries(), [dict(key='zora.message', shape='json', file='<locale>.json',
                                             locales_with=['ava'], locales_missing=['bex'], touched_by_pr='no')])

    def test_json_and_php_are_separate_key_spaces(self):
        for locale in ['ava', 'bex']:
            self.write(f'{locale}.json', '{"zora.title": "A"}')
            self.write(f'{locale}/luma.php', "<?php return ['label' => 'B'];")
        self.assertEqual(self.entries(), [])
        self.write('bex.json', '{}')
        self.write('ava/luma.php', '<?php return [];')
        gaps = self.entries()
        self.assertEqual([(gap['shape'], gap['key'], gap['locales_missing']) for gap in gaps],
                         [('json', 'zora.title', ['bex']), ('php', 'luma.label', ['ava'])])

    def test_key_removed_from_1_of_3_locales_is_reported(self):
        for locale in ['cyv', 'bex', 'ava']:
            self.write(f'{locale}.json', '{"luma": "A"}' if locale != 'bex' else '{}')
        gap, = self.entries()
        self.assertEqual(gap['locales_with'], ['ava', 'cyv'])
        self.assertEqual(gap['locales_missing'], ['bex'])

    def test_invalid_json_is_excluded_instead_of_creating_false_gaps(self):
        self.write('ava.json', '{"luma": "A"}')
        self.write('bex.json', '{"luma": "B"}')
        for broken in ['{"zora":', '[]', 'null', '"zora"', '{"luma": NaN}', '{"luma": Infinity}']:
            with self.subTest(broken=broken):
                self.write('cyv.json', broken)
                error, = self.entries()
                self.assertEqual((error['file'], error['shape'], error['unreadable']), ('cyv.json', 'json', True))
                self.assertTrue(error['reason'])
                self.assertNotIn('key', error)

    def test_nested_php_leaves_and_group_folders_keep_their_paths(self):
        self.write('ava/zora.php', "<?php return ['outer' => ['inner' => ['leaf' => 'A']], 'empty' => []];")
        self.write('bex/zora.php', "<?php return ['outer' => ['inner' => []]];")
        self.write('ava/sector/ledger.php', "<?php return ['title' => 'A'];")
        self.write('bex/sector/ledger.php', '<?php return [];')
        gaps = self.entries()
        self.assertEqual([(gap['key'], gap['file']) for gap in gaps],
                         [('sector/ledger.title', 'sector/ledger.php'), ('zora.outer.inner.leaf', 'zora.php')])

    def test_php_lists_use_automatic_integer_keys(self):
        cases = [
            ("['days' => ['Monday', 'Tuesday']]", ['days.0', 'days.1']),
            ("array('days' => array('Monday', 'Tuesday',))", ['days.0', 'days.1']),
            ("['days' => ['Monday', 4 => 'Tuesday', 2 => 'Wednesday', 'Thursday']]",
             ['days.0', 'days.2', 'days.4', 'days.5']),
            ("['days' => ['4' => 'Monday', 'Tuesday', 'label' => 'Wednesday', 'Thursday']]",
             ['days.4', 'days.5', 'days.6', 'days.label']),
            ("['days' => ['04' => 'Monday', '+4' => 'Tuesday', 'Wednesday']]",
             ['days.+4', 'days.0', 'days.04']),
            ("['days' => [['Monday'], ['Tuesday']]]", ['days.0.0', 'days.1.0']),
            ("['days' => [-3 => 'Monday', 'Tuesday']]", ['days.-2', 'days.-3']),
        ]
        self.write('ar/messages.php', '<?php return [];')
        for source, keys in cases:
            with self.subTest(source=source):
                self.write('en/messages.php', '<?php return ' + source + ';')
                self.assertEqual(self.entries(), [
                    dict(key='messages.' + key, shape='php', file='messages.php',
                         locales_with=['en'], locales_missing=['ar'], touched_by_pr='no')
                    for key in keys
                ])

    def test_discovery_includes_json_and_folder_only_locales(self):
        self.write('ava.json', '{"luma": "A"}')
        self.write('bex.json', '{}')
        self.write('cyv/zora.php', "<?php return ['title' => 'B'];")
        gaps = self.entries()
        self.assertEqual([(gap['key'], gap['locales_with'], gap['locales_missing']) for gap in gaps],
                         [('luma', ['ava'], ['bex', 'cyv']), ('zora.title', ['cyv'], ['ava', 'bex'])])

    def test_vendor_package_translations_do_not_create_locale_or_gaps(self):
        self.write('en/messages.php', "<?php return ['title' => 'A'];")
        self.write('ar/messages.php', '<?php return [];')
        self.write('vendor/pkg/en/p.php', "<?php return ['package' => 'B'];")
        self.assertEqual(self.entries(), [dict(key='messages.title', shape='php', file='messages.php',
                                             locales_with=['en'], locales_missing=['ar'], touched_by_pr='no')])

    def test_changed_files_both_formats_mark_gaps_without_filtering(self):
        self.write('ava.json', '{"luma": "A"}')
        self.write('bex.json', '{}')
        self.write('ava/sector/ledger.php', "<?php return ['title' => 'A'];")
        self.write('bex/sector/ledger.php', '<?php return [];')
        changes = self.root / 'files.json'
        cases = [(['repo/lang/ava.json'], ['yes', 'no']),
                 (['lang/ava.json'], ['yes', 'no']),
                 (['ava.json'], ['yes', 'no']),
                 (['app/ava.json'], ['no', 'no']),
                 ([{'path': r'repo\lang\bex\sector\ledger.php'}], ['no', 'yes']),
                 ([{'filename': 'repo/lang/ava/sector/ledger.php'}], ['no', 'yes']),
                 (['sector/ledger.php'], ['no', 'yes']),
                 (['repo/lang/zava.json', 'repo/lang/ava/sector/ledger.php.bak'], ['no', 'no'])]
        for paths, expected in cases:
            with self.subTest(paths=paths):
                changes.write_text(json.dumps(paths), encoding='utf-8')
                gaps = self.entries('--changed-files', changes)
                self.assertEqual([gap['touched_by_pr'] for gap in gaps], expected)
                self.assertEqual([gap['key'] for gap in gaps], ['luma', 'sector/ledger.title'])

    def test_changed_translation_paths_do_not_touch_suffix_matches(self):
        for group in ['messages.php', 'admin/messages.php']:
            self.write('en/' + group, "<?php return ['title' => 'A'];")
            self.write('ar/' + group, '<?php return [];')
        changes = self.root / 'files.json'
        cases = [
            ('lang/en/admin/messages.php', ['yes', 'no']),
            ('app/messages.php', ['no', 'no']),
            ('lang/en/messages.php', ['no', 'yes']),
            ('en/messages.php', ['no', 'yes']),
            ('messages.php', ['no', 'yes']),
            ('en/admin/messages.php', ['yes', 'no']),
            ('admin/messages.php', ['yes', 'no']),
            ('repo/lang/ar/admin/messages.php', ['yes', 'no']),
            ('repo/lang/ar/messages.php', ['no', 'yes']),
            ('app/en/messages.php', ['no', 'no']),
            ('lang/other/messages.php', ['no', 'no']),
            ('lang/en/messages.php.bak', ['no', 'no']),
        ]
        for path, expected in cases:
            with self.subTest(path=path):
                changes.write_text(json.dumps([path]), encoding='utf-8')
                self.assertEqual([gap['touched_by_pr'] for gap in self.entries('--changed-files', changes)],
                                 expected)

    def test_php_tokenizer_counts_keys_without_evaluating_values(self):
        self.write('ava/zora.php', r'''<?php
            // 'fake' => 'ignored',
            return array(
                'outer' => array("say\"hi" => 'A', 'slash\\key' => "B",),
                # 'ghost' => 'ignored',
                /* 'phantom' => array('hidden' => 'ignored'), */
                'number' => -3.5, 'constant' => ZORA_FLAG,
                'joined' => 'A' . 'B', 'called' => __('C', ['x', 'y']),
                -7 => false, 12 => null,
                'empty' => array(),
            ); ?>''')
        self.write('bex/zora.php', '<?php return [];')
        self.assertEqual([gap['key'] for gap in self.entries()],
                         ['zora.-7', 'zora.12', 'zora.called', 'zora.constant', 'zora.joined',
                          'zora.number', 'zora.outer.say"hi', 'zora.outer.slash\\key'])

    def test_unreadable_php_group_does_not_hide_other_readable_gaps(self):
        self.write('ava/zora.php', "<?php return ['luma' => 'A'];")
        self.write('bex/zora.php', '<?php return [;')
        self.write('cyv/zora.php', '<?php return [];')
        entries = self.entries()
        errors = [entry for entry in entries if entry.get('unreadable')]
        gaps = [entry for entry in entries if 'key' in entry]
        self.assertEqual(len(errors), 1)
        self.assertEqual((errors[0]['file'], errors[0]['shape']), ('bex/zora.php', 'php'))
        self.assertTrue(errors[0]['reason'])
        self.assertEqual([(gap['key'], gap['locales_missing']) for gap in gaps], [('zora.luma', ['cyv'])])

    def test_bad_php_syntax_is_reported_instead_of_clean_output(self):
        cases = ["<?php return ['luma' => 'A';", "<?php return ['luma' => ];",
                 "<?php return ['luma' => call(];", "<?php return ['luma' => 'A' 'zora' => 'B'];",
                 "<?php return ['luma' => 'open];", '<?php /* open',
                 "<?php return ['luma' => [] + ['zora' => 'A'];",
                 "<?php echo 'A';", "<?php return []; unexpected",
                 "<?php return ['luma' => 'A' . ];", "<?php return ['luma' => 'A' 'B'];"]
        for source in cases:
            with self.subTest(source=source):
                self.write('ava/zora.php', source)
                error, = self.entries()
                self.assertEqual((error['file'], error['shape'], error['unreadable']), ('ava/zora.php', 'php', True))

    def test_undecodable_bytes_are_reported_for_both_shapes(self):
        for relative, shape in [('ava.json', 'json'), ('bex/zora.php', 'php')]:
            self.write(relative, '').write_bytes(b'\xff')
        errors = self.entries()
        self.assertEqual([(entry['file'], entry['shape'], entry['unreadable']) for entry in errors],
                         [('ava.json', 'json', True), ('bex/zora.php', 'php', True)])
        self.assertTrue(all(entry['reason'] for entry in errors))

    def test_empty_and_clean_inputs_give_empty_list(self):
        self.assertEqual(self.entries(), [])
        for locale in ['ava', 'bex']:
            self.write(f'{locale}.json', '{"luma": "A"}')
            self.write(f'{locale}/zora.php', "<?php return ['title' => 'B'];")
        self.assertEqual(self.entries(), [])

    def test_bad_arguments_exit_2_with_1_stderr_line(self):
        plain_file = self.write('plain', 'A')
        for args in [(), ('--unknown',), ('--lang', self.root / 'absent'), ('--lang', plain_file),
                     ('--lang', self.lang, '--unknown'), ('--lang',)]:
            with self.subTest(args=args):
                run = self.run_cli(*args)
                self.assertEqual(run.returncode, 2, run.stderr)
                self.assertEqual(len(run.stderr.splitlines()), 1, run.stderr)
                self.assertTrue(run.stderr.startswith('translation_keys.py: '), run.stderr)
                self.assertEqual(run.stdout, '')

    def test_invalid_changed_files_are_argument_errors(self):
        changes = self.root / 'files.json'
        for content in ['{', '{}', '[1]', '[{}]', '[{"path": 1}]']:
            with self.subTest(content=content):
                changes.write_text(content, encoding='utf-8')
                run = self.run_cli('--lang', self.lang, '--changed-files', changes)
                self.assertEqual(run.returncode, 2)
                self.assertEqual(len(run.stderr.splitlines()), 1)
                self.assertTrue(run.stderr.startswith('translation_keys.py: '), run.stderr)
                self.assertEqual(run.stdout, '')

    def test_socket_block_still_allows_real_gap_output(self):
        self.write('ava.json', '{"luma": "A"}')
        self.write('bex.json', '{}')
        wrapper = (
            'import runpy, socket, sys; from unittest.mock import patch; '
            'script = sys.argv.pop(1); '
            'block = patch.object(socket, "socket", side_effect=AssertionError("network forbidden")); '
            'block.start(); runpy.run_path(script, run_name="__main__")'
        )
        control = self.root / 'probe.py'
        control.write_text('import socket\nsocket.socket()\n', encoding='utf-8')
        blocked = subprocess.run([sys.executable, '-E', '-P', '-X', 'utf8', '-B', '-c', wrapper, str(control)],
                                 capture_output=True, text=True, encoding='utf-8', timeout=10)
        self.assertNotEqual(blocked.returncode, 0)
        self.assertIn('AssertionError: network forbidden', blocked.stderr)
        run = subprocess.run([sys.executable, '-E', '-P', '-X', 'utf8', '-B', '-c', wrapper,
                              str(self.script), '--lang', str(self.lang)],
                             capture_output=True, text=True, encoding='utf-8', timeout=10)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stderr, '')
        self.assertEqual([entry['key'] for entry in json.loads(run.stdout)], ['luma'])

    def test_named_placeholder_gap_ignores_count_and_keeps_all_locales(self):
        self.write('ava.json', json.dumps({'luma': 'Hi :name, :count items', 'zora': 'Hi :count'}))
        self.write('bex.json', json.dumps({'luma': 'Hi, :count items', 'zora': 'Hi'}))
        report = self.entries('--report', 'values')
        self.assertEqual(report['placeholder_gaps'], [
            dict(key='luma', shape='json', file='<locale>.json',
                 placeholders_by_locale={'ava': [':name'], 'bex': []}, locales_missing_any=['bex'])])
        self.assertEqual(report['values'][0],
                         dict(key='luma', shape='json', file='<locale>.json', locale='ava',
                              placeholders=[':count', ':name'], plural_forms=None))

    def test_placeholder_case_variants_and_count_give_no_gap(self):
        for en, ar in [(':Name', ':name'), (':NAME :Name :name', ':name'), (':COUNT', ''), (':Count', '')]:
            with self.subTest(en=en, ar=ar):
                self.write('en.json', json.dumps({'luma': 'Hi ' + en}))
                self.write('ar.json', json.dumps({'luma': 'Hi ' + ar}))
                self.assertEqual(self.entries('--report', 'values')['placeholder_gaps'], [])

    def test_missing_placeholder_reports_gap_with_original_spelling(self):
        for name in [':name', ':Name', ':NAME']:
            with self.subTest(name=name):
                self.write('en.json', json.dumps({'luma': 'Hi ' + name}))
                self.write('ar.json', json.dumps({'luma': 'Hi'}))
                self.assertEqual(self.entries('--report', 'values')['placeholder_gaps'], [
                    dict(key='luma', shape='json', file='<locale>.json',
                         placeholders_by_locale={'ar': [], 'en': [name]}, locales_missing_any=['ar'])])

    def test_placeholder_boundaries_and_union_find_each_missing_locale(self):
        self.write('ava.json', json.dumps({'luma': ':zora :_luma :zora :name7 word:fake ::fake é:fake'}))
        self.write('bex.json', json.dumps({'luma': ':other'}))
        self.write('cyv.json', json.dumps({'luma': ':zora :_luma :name7 :other'}))
        report = self.entries('--report', 'values')
        self.assertEqual(report['placeholder_gaps'], [
            dict(key='luma', shape='json', file='<locale>.json',
                 placeholders_by_locale={'ava': [':_luma', ':name7', ':zora'], 'bex': [':other'],
                                         'cyv': [':_luma', ':name7', ':other', ':zora']},
                 locales_missing_any=['ava', 'bex'])])

    def test_plural_counts_are_reported_without_judging_them(self):
        for locale, phrase in [('ava', 'one|many'), ('bex', 'a|b|c')]:
            self.write(f'{locale}.json', json.dumps({'luma': phrase, 'zora': 'plain',
                                                   'range': '{0} none|[1,19] some|[20,*] many',
                                                   'empty': '|'}))
            self.write(f'{locale}/niva.php', "<?php return ['luma' => '" + phrase + "'];")
        report = self.entries('--report', 'values')
        self.assertEqual([(entry['shape'], entry['key'], entry['locale'], entry['plural_forms'])
                          for entry in report['values']],
                         [('json', 'empty', 'ava', 2), ('json', 'empty', 'bex', 2),
                          ('json', 'luma', 'ava', 2), ('json', 'luma', 'bex', 3),
                          ('json', 'range', 'ava', 3), ('json', 'range', 'bex', 3),
                          ('json', 'zora', 'ava', None), ('json', 'zora', 'bex', None),
                          ('php', 'niva.luma', 'ava', 2), ('php', 'niva.luma', 'bex', 3)])
        self.assertEqual(report['gaps'], [])

    def test_changed_values_only_include_shared_string_leaves(self):
        base = self.root / 'base'
        base.mkdir()
        (base / 'ava.json').write_text(json.dumps({'luma': 'A', 'removed': 'R', 'same': 'S',
                                                  'number': 1, 'text': 'before', 'blank': ''}), encoding='utf-8')
        self.write('ava.json', json.dumps({'luma': 'B', 'added': 'N', 'same': 'S',
                                         'number': 'now text', 'text': False, 'blank': 'after'}))
        (base / 'ava').mkdir()
        (base / 'ava/niva.php').write_text("<?php return ['luma' => 'A', 'joined' => 'A' . 'B'];",
                                          encoding='utf-8')
        self.write('ava/niva.php', "<?php return ['luma' => 'B', 'joined' => 'C'];")
        self.assertEqual(self.entries('--report', 'values', '--base-lang', base)['changed_old_values'], [
            dict(key='blank', shape='json', file='<locale>.json', locale='ava', old='', new='after'),
            dict(key='luma', shape='json', file='<locale>.json', locale='ava', old='A', new='B'),
            dict(key='niva.luma', shape='php', file='niva.php', locale='ava', old='A', new='B')])
        self.assertEqual(self.entries('--report', 'values')['changed_old_values'], [])

    def test_letter_rules_skip_neutral_text_and_unknown_locales(self):
        phrases = {'wrong': 'Save', 'count': ':count', 'digits': '50%', 'symbols': '☀ % !',
                   'right': 'حفظ', 'mixed': 'Save حفظ', 'blank': '', 'nonstring': 7}
        for locale in ['ar', 'ar_EG', 'ar-EG']:
            self.write(f'{locale}.json', json.dumps(phrases))
        for locale in ['en', 'en_GB', 'en-GB']:
            self.write(f'{locale}.json', json.dumps({'wrong': 'حفظ', 'right': 'Save', 'count': ':name'}))
        for locale in ['fr', 'ava', 'enx']:
            self.write(f'{locale}.json', '{"wrong": "Save"}')
        report = self.entries('--report', 'values')
        self.assertEqual(report['no_letters'], [
            dict(key='wrong', shape='json', file='<locale>.json', locale=locale)
            for locale in ['ar', 'ar-EG', 'ar_EG', 'en', 'en-GB', 'en_GB']])
        self.assertEqual(report['locales_not_checked_for_letters'], ['ava', 'enx', 'fr'])

    def test_clean_and_empty_reports_have_all_output_fields(self):
        expected = dict(gaps=[], values=[], placeholder_gaps=[], no_letters=[],
                        locales_not_checked_for_letters=[], changed_old_values=[])
        self.assertEqual(self.entries('--report', 'values'), expected)
        self.write('ar.json', json.dumps({'luma': 'حفظ :name'}))
        self.write('en.json', json.dumps({'luma': 'Save :name'}))
        expected['values'] = [dict(key='luma', shape='json', file='<locale>.json', locale=locale,
                                   placeholders=[':name'], plural_forms=None) for locale in ['ar', 'en']]
        self.assertEqual(self.entries('--report', 'values'), expected)

    def test_php_values_use_only_literal_leaves_and_keep_key_functions(self):
        source = r'''<?php return ['outer' => array('luma' => "Hi\n:name|Hi :count"),
            'escaped' => 'It\'s :name', 'joined' => ':ghost' . ':other',
            'called' => niva(':ghost'), 'number' => 7];'''
        self.write('ava/sector/niva.php', source)
        self.write('bex/sector/niva.php', "<?php return ['outer' => ['luma' => 'Hi :count']];")
        report = self.entries('--report', 'values')
        self.assertEqual(report['values'], [
            dict(key='sector/niva.escaped', shape='php', file='sector/niva.php', locale='ava',
                 placeholders=[':name'], plural_forms=None),
            dict(key='sector/niva.outer.luma', shape='php', file='sector/niva.php', locale='ava',
                 placeholders=[':count', ':name'], plural_forms=2),
            dict(key='sector/niva.outer.luma', shape='php', file='sector/niva.php', locale='bex',
                 placeholders=[':count'], plural_forms=None)])
        self.assertEqual(report['placeholder_gaps'], [
            dict(key='sector/niva.outer.luma', shape='php', file='sector/niva.php',
                 placeholders_by_locale={'ava': [':name'], 'bex': []}, locales_missing_any=['bex'])])
        self.assertEqual(report['gaps'], self.entries())
        from translation_keys import file_keys, php_keys
        self.assertEqual(php_keys(source), {'outer.luma', 'escaped', 'joined', 'called', 'number'})
        self.assertEqual(file_keys(self.lang / 'ava/sector/niva.php', 'php'), php_keys(source))

    def test_unreadable_base_and_head_files_skip_value_checks(self):
        self.write('ava.json', '{"luma": "Hi :name", "number": 3}')
        self.write('bex.json', '{')
        self.write('ava/niva.php', "<?php return ['luma' => 'B'];")
        base = self.root / 'base'
        (base / 'ava').mkdir(parents=True)
        (base / 'ava.json').write_bytes(b'\xff')
        (base / 'ava/niva.php').write_text('<?php return [;', encoding='utf-8')
        changes = self.root / 'files.json'
        changes.write_text('["ava/niva.php"]', encoding='utf-8')
        report = self.entries('--report', 'values', '--base-lang', base, '--changed-files', changes)
        self.assertEqual(report['gaps'], self.entries('--changed-files', changes))
        self.assertEqual(len(report['values']), 2)
        self.assertEqual(report['changed_old_values'], [])
        self.assertEqual(report['placeholder_gaps'], [])
        self.assertEqual(report['locales_not_checked_for_letters'], ['ava', 'bex'])

    def test_values_bad_arguments_exit_2_with_1_stderr_line(self):
        plain = self.write('plain', 'A')
        for args in [('--report', 'values'), ('--lang', self.root / 'absent', '--report', 'values'),
                     ('--lang', plain, '--report', 'values'),
                     ('--lang', self.lang, '--base-lang', self.lang),
                     ('--lang', self.lang, '--report', 'gaps'),
                     ('--lang', self.lang, '--report', 'values', '--base-lang', self.root / 'absent'),
                     ('--lang', self.lang, '--report', 'values', '--base-lang', plain),
                     ('--lang', self.lang, '--report', 'values', '--changed-files', self.root / 'absent')]:
            with self.subTest(args=args):
                run = self.run_cli(*args)
                self.assertEqual(run.returncode, 2, run.stderr)
                self.assertEqual(len(run.stderr.splitlines()), 1, run.stderr)
                self.assertTrue(run.stderr.startswith('translation_keys.py: '), run.stderr)
                self.assertEqual(run.stdout, '')
        changes = self.root / 'files.json'
        for content in ['{', '{}', '[1]', '[{}]', '[{"path": 1}]']:
            with self.subTest(content=content):
                changes.write_text(content, encoding='utf-8')
                run = self.run_cli('--lang', self.lang, '--report', 'values', '--changed-files', changes)
                self.assertEqual(run.returncode, 2)
                self.assertEqual(len(run.stderr.splitlines()), 1)
                self.assertEqual(run.stdout, '')

    def test_source_imports_no_network_modules(self):
        def network_imports(source):
            modules = set()
            for node in ast.walk(ast.parse(source)):
                if isinstance(node, ast.Import):
                    modules.update(alias.name.split('.')[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    modules.add(node.module.split('.')[0])
            return modules & {'socket', 'urllib', 'http', 'requests'}

        self.assertEqual(network_imports('import socket, urllib.request\nfrom http import client\nimport requests'),
                         {'socket', 'urllib', 'http', 'requests'})
        self.assertEqual(network_imports('# import socket\nphrase = "import requests"'), set())
        self.assertEqual(network_imports(self.script.read_text(encoding='utf-8')), set())


if __name__ == '__main__':
    unittest.main()
