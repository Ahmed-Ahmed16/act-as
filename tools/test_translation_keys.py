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


if __name__ == '__main__':
    unittest.main()
