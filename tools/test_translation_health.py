"""CLI checks use invented fixtures and real translation reports."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from translation_health_scan import scan_file


class TranslationHealthTests(unittest.TestCase):
    def setUp(self):
        self.tree = tempfile.TemporaryDirectory(prefix='luma-health-')
        self.addCleanup(self.tree.cleanup)
        self.root = Path(self.tree.name)
        self.script = Path(__file__).with_name('translation_health.py').resolve()
        self.orders = {'en': {'title': 'Orders', 'hello': 'Hello :name', 'count': ':count'},
                       'ar': {'title': 'الطلبات', 'hello': 'مرحبا :name', 'count': ':count'}}
        self.save_orders()
        self.write('lang/en.json', json.dumps({'Save': 'Save'}))
        self.write('lang/ar.json', json.dumps({'Save': 'حفظ'}))
        self.write('app/Parcel.php', "<?php __('orders.title');\n")
        self.write('resources/views/cart.blade.php', "{{ __('Save') }}\n")

    def write(self, relative, text):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
        return path

    def save_orders(self):
        for locale, entries in self.orders.items():
            body = ', '.join("'" + key + "' => '" + text + "'" for key, text in entries.items())
            self.write(f'lang/{locale}/orders.php', '<?php return [' + body + '];')

    def run_cli(self, *args):
        return subprocess.run([sys.executable, '-B', str(self.script), '--repo', str(self.root),
                               *map(str, args)], capture_output=True, text=True,
                              encoding='utf-8', timeout=15)

    def report(self, *args):
        run = self.run_cli(*args)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stderr, '')
        self.assertTrue(run.stdout.isascii())
        self.assertEqual(len(run.stdout.splitlines()), 1)
        return json.loads(run.stdout)

    def changed(self, paths):
        return self.write('changed.json', json.dumps(paths))

    def base(self):
        path = self.root / 'before'
        shutil.copytree(self.root / 'lang', path)
        return path

    def test_default_lang_path_finds_both_layouts(self):
        # G36: lang only, resources/lang only; changed paths use the chosen folder.
        del self.orders['ar']['title']
        self.save_orders()
        for folder in ('lang', 'resources/lang'):
            with self.subTest(folder=folder):
                if folder != 'lang':
                    shutil.move(str(self.root / 'lang'), str(self.root / folder))
                changed = self.changed([f'{folder}/en/orders.php'])
                report = self.report('--changed-files', changed)
                self.assertEqual(report['check1'], [
                    dict(key='orders.title', shape='php', file='orders.php', locales_with=['en'],
                         locales_missing=['ar'], touched_by_pr='yes', page='app/Parcel.php')])
                self.assertFalse(report['no_translation_files_changed'])

    def test_default_lang_path_prefers_lang_and_explicit_path_wins(self):
        fallback = self.root / 'resources/lang'
        self.write('resources/lang/en.json', '{"Fallback": "Fallback"}')
        self.assertEqual(self.report()['check2'], [])
        report = self.report('--lang', fallback)
        self.assertEqual(report['check2'], [
            dict(key='Save', locales_missing=['en'], used_at=['resources/views/cart.blade.php:1']),
            dict(key='orders.title', locales_missing=['en'], used_at=['app/Parcel.php:1'])])

    def test_gaps_preserve_report_fields_and_add_page(self):
        self.assertEqual(self.report()['check1'], [])
        del self.orders['ar']['title']
        self.save_orders()
        changed = self.changed([{'filename': 'lang/en/orders.php'}])
        self.assertEqual(self.report('--changed-files', changed)['check1'], [
            dict(key='orders.title', shape='php', file='orders.php', locales_with=['en'],
                 locales_missing=['ar'], touched_by_pr='yes', page='app/Parcel.php')])

    def test_used_keys_report_missing_locales_and_unknown_keys(self):
        self.assertEqual(self.report()['check2'], [])
        del self.orders['ar']['title']
        self.save_orders()
        self.write('app/Parcel.php', "<?php __('orders.title');\ntrans('absent.key');\n__('orders.title');")
        self.assertEqual(self.report()['check2'], [
            dict(key='absent.key', locales_missing=['ar', 'en'], used_at=['app/Parcel.php:2']),
            dict(key='orders.title', locales_missing=['ar'],
                 used_at=['app/Parcel.php:1', 'app/Parcel.php:3'])])

    def test_blade_attribute_calls_report_missing_keys_and_used_keys(self):
        # N9: HTML quotes must not hide any of the 3 Blade forms.
        for expression in ("{{ __('KEY') }}", "{!! trans('KEY') !!}", "@lang('KEY')"):
            for quote in ('"', "'"):
                with self.subTest(expression=expression, quote=quote):
                    self.write('resources/views/cart.blade.php', '\n'.join([
                        '<input',
                        ' title=' + quote + expression.replace('KEY', 'orders.hello') + quote,
                        ' placeholder=' + quote + expression.replace('KEY', 'missing.attribute') + quote + '>',
                    ]))
                    report = self.report()
                    self.assertEqual(report['check2'], [dict(
                        key='missing.attribute', locales_missing=['ar', 'en'],
                        used_at=['resources/views/cart.blade.php:3'])])
                    self.assertEqual(report['check6'], dict(
                        variable=[], no_trace=['Save', 'orders.count'], dynamic_call_sites=[]))

    def test_blade_attribute_and_text_calls_are_each_found_once(self):
        for expression in ("{{ __('orders.hello') }}", "{!! __('orders.hello') !!}",
                           "{{ __('orders.hello', ['name' => '}}']) }}",
                           "{!! __('orders.hello', ['name' => '!!}']) !!}",
                           "@lang('orders.hello')",
                           '''@lang('orders.hello', ['name' => "@lang('fake.string')"])'''):
            with self.subTest(expression=expression):
                source = '\n'.join([
                    '{{-- <input title="' + expression + '"> --}}',
                    '<input title="' + expression + '">',
                    '<!-- <input title="' + expression + '"> -->',
                    '<p>' + expression + '</p>',
                ])
                path = self.write('resources/views/cart.blade.php', source)
                calls, _, _ = scan_file(path, 'resources/views/cart.blade.php')
                self.assertEqual(sorted((call['key'], call['line']) for call in calls),
                                 [('orders.hello', 2), ('orders.hello', 4)])

    def test_blade_escaped_echoes_have_no_calls_or_raw_pointers(self):
        for source in ("@{{ __('x.a') }}", "@{!! __('x.b') !!}",
                       "@{{\n__('x.a')\n}}", "@{!!\n__('x.b')\n!!}"):
            with self.subTest(source=source):
                path = self.write('resources/views/cart.blade.php', source)
                calls, raw, _ = scan_file(path, 'resources/views/cart.blade.php')
                self.assertEqual((calls, raw), ([], []))

    def test_blade_plain_calls_beside_escaped_echoes_keep_their_lines(self):
        source = '\n'.join([
            "@{{\n__('x.a')\n}} {{ __('x.c') }}",
            "@{!!\n__('x.b')\n!!} {!! __('x.d') !!}",
            "@lang('x.e')",
        ])
        path = self.write('resources/views/cart.blade.php', source)
        calls, raw, _ = scan_file(path, 'resources/views/cart.blade.php')
        self.assertEqual([(call['key'], call['line']) for call in calls],
                         [('x.c', 3), ('x.d', 6), ('x.e', 7)])
        self.assertEqual(raw, [dict(path='resources/views/cart.blade.php', line=6,
                                   key='x.d', args_escaped=True)])

    def test_placeholders_come_from_report_and_count_is_ignored(self):
        self.assertEqual(self.report()['check3'], [])
        self.orders['ar']['hello'] = 'مرحبا'
        self.orders['ar']['count'] = 'عدد'
        self.save_orders()
        self.assertEqual(self.report()['check3'], [
            dict(key='orders.hello', shape='php', file='orders.php',
                 placeholders_by_locale={'ar': [], 'en': [':name']}, locales_missing_any=['ar'])])

    def test_plural_forms_only_include_trans_choice_literals(self):
        for locale in self.orders:
            self.orders[locale].update(title='A|B', parcels='A|B|C')
        self.save_orders()
        self.write('app/Parcel.php', "<?php __('orders.title'); trans_choice('orders.parcels', $n);")
        self.assertEqual(self.report()['check4'], [
            dict(key='orders.parcels', forms_by_locale={'ar': 3, 'en': 3})])
        self.write('app/Parcel.php', "<?php trans_choice('orders.title', $n);")
        self.assertEqual(self.report()['check4'], [
            dict(key='orders.title', forms_by_locale={'ar': 2, 'en': 2})])

    def test_base_changes_are_separate_from_new_key_groups(self):
        base = self.base()
        self.assertEqual(self.report('--base-lang', base)['check5'], [])
        self.orders['en']['title'] = 'Parcel orders'
        self.orders['en']['fresh'] = 'Fresh'
        self.save_orders()
        self.write('app/Parcel.php', "<?php __('orders.title'); __('orders.fresh');")
        report = self.report('--base-lang', base)
        self.assertEqual(report['check5'], [dict(key='orders.title', shape='php', file='orders.php',
                                               locale='en', old='Orders', new='Parcel orders')])
        self.assertEqual(report['by_page'], dict(scope='new keys', groups={'app/Parcel.php': ['orders.fresh']}))

    def test_unused_and_dynamic_prefix_keys_have_separate_lists(self):
        for expression in ["__('orders.' . $key)", 'trans("orders.$key")', "trans('orders.' . $key)"]:
            with self.subTest(expression=expression):
                self.write('app/Parcel.php', "<?php __('orders.title');\n" + expression + ';\n__($key);')
                self.assertEqual(self.report()['check6'], dict(
                    variable=['orders.count', 'orders.hello'], no_trace=[],
                    dynamic_call_sites=['app/Parcel.php:2', 'app/Parcel.php:3']))
        self.write('app/Parcel.php', "<?php __('orders.title');")
        self.assertEqual(self.report()['check6'], dict(variable=[], no_trace=['orders.count', 'orders.hello'],
                                                      dynamic_call_sites=[]))

    def test_raw_output_checks_every_replacement_and_ignores_escaped_output(self):
        cases = [("{!! __('Save', ['n' => e($x)]) !!}", True, 'Save'),
                 ("{!! __('Save', ['n' => htmlspecialchars($x), 'm' => e($y)]) !!}", True, 'Save'),
                 ("{!! __('Save', ['n' => $x]) !!}", False, 'Save'),
                 ("{!! trans_choice('Save', $n, ['n' => $x]) !!}", False, 'Save'),
                 ("{!! Lang::get('Save', ['n' => $x]) !!}", False, 'Save'),
                 ("{!! Lang::get('Save', ['n' => e($x)]) !!}", True, 'Save'),
                 ("{!! Lang::choice('Save', $n) !!}", True, 'Save'),
                 ("{!! Lang::choice('Save', $n, ['n' => $x]) !!}", False, 'Save'),
                 ("{!! Lang::choice('Save', $n, ['n' => e($x)]) !!}", True, 'Save'),
                 ("{!! trans($key) !!}", True, None),
                 ("{!! @lang('Save') !!}", True, 'Save'),
                 ("{!! __('Save') !!}", True, 'Save')]
        for source, escaped, key in cases:
            with self.subTest(source=source):
                self.write('resources/views/cart.blade.php', source)
                self.assertEqual(self.report()['check7'], [dict(path='resources/views/cart.blade.php',
                                                              line=1, key=key, args_escaped=escaped)])
        for call in ("__('Save')", "Lang::get('Save')", "Lang::choice('Save', $n)"):
            with self.subTest(escaped_output=call):
                self.write('resources/views/cart.blade.php', '{{ ' + call + ' }}')
                self.assertEqual(self.report()['check7'], [])

    def test_letter_checks_reuse_report_and_list_unknown_locale(self):
        self.assertEqual(self.report()['check8'], dict(no_letters=[], locales_not_checked_for_letters=[]))
        self.orders['ar']['title'] = 'Save'
        self.save_orders()
        self.write('lang/fr.json', '{"Save": "Enregistrer"}')
        self.assertEqual(self.report()['check8'], dict(
            no_letters=[dict(key='orders.title', shape='php', file='orders.php', locale='ar')],
            locales_not_checked_for_letters=['fr']))

    def test_php_visible_literals_include_only_requested_sinks(self):
        sources = ["$mail->subject('Your order shipped');", "Mail::raw('Your order shipped', $cb);",
                   "$flash->message('Your order shipped');", "$flash->with('message', 'Your order shipped');",
                   "$flash->with('error', 'Your order failed');", "$flash->with('success', 'Your order shipped');",
                   "response()->json(['message' => 'Your order shipped']);", "abort(403, 'Your order failed');",
                   "ValidationException::withMessages(['email' => 'Your address failed']);",
                   "ValidationException::withMessages('Your address failed');",
                   "ValidationException::withMessages(['email' => ['Your address failed']]);",
                   "$flash->error('Your order failed');"]
        for source in sources:
            with self.subTest(source=source):
                self.write('app/Parcel.php', '<?php\n' + source)
                self.assertEqual(self.report()['g4_literal_text'], ['app/Parcel.php:2'])
        self.write('app/Parcel.php', """<?php
$mail->subject(__('orders.title'));
Log::info('Order shipped for user');
logger('Order shipped for user');
$logger->error('Order shipped for user');
Log::channel('parcel')->error('Order shipped for user');
Log::stack(['single'])->error('Order shipped for user');
logger()->channel('parcel')->error('Order shipped for user');
// $mail->subject('Your order shipped');
# $mail->subject('Your order shipped');
/* $mail->subject('Your order shipped'); */
$mail->subject('OneWord');
$mail->with('other', 'Your order shipped');
""")
        self.assertEqual(self.report()['g4_literal_text'], [])

    def test_blade_text_excludes_markup_code_comments_and_scripts(self):
        self.write('resources/views/cart.blade.php', """<p>Your order shipped</p>
<p>{{ __('Save') }}</p>
<p>{!! __('Save') !!}</p>
{{-- Hidden words --}}
<!-- Hidden words -->
<script>const text = 'Hidden words';</script>
<style>.text { color: red; }</style>
@if($label === 'Hidden words')
<input title="Hidden words">
@endif
<?php $text = 'Hidden words'; ?>
""")
        self.assertEqual(self.report()['g4_literal_text'], ['resources/views/cart.blade.php:1'])

    def test_changed_files_scope_only_limits_literal_text(self):
        self.write('app/Parcel.php', "<?php $mail->subject('Your order shipped'); __('missing');")
        changed = self.changed(['resources/views/cart.blade.php'])
        report = self.report('--changed-files', changed)
        self.assertEqual(report['g4_literal_text'], [])
        self.assertEqual(report['check2'][0]['key'], 'missing')
        self.assertTrue(report['no_translation_files_changed'])
        changed = self.changed([{'path': 'lang/en/orders.php'}])
        self.assertFalse(self.report('--changed-files', changed)['no_translation_files_changed'])
        self.assertFalse(self.report()['no_translation_files_changed'])

    def test_page_groups_use_distinct_source_files(self):
        self.write('resources/views/cart.blade.php', "{{ __('Save') }} {{ __('orders.title') }}")
        report = self.report()
        self.assertEqual(report['by_page'], dict(scope='all keys', groups={
            'shared': ['orders.title'], 'resources/views/cart.blade.php': ['Save'],
            'no use found': ['orders.count', 'orders.hello']}))
        del self.orders['ar']['title']
        self.save_orders()
        self.assertEqual(self.report()['check1'][0]['page'], 'shared')

    def test_controller_and_its_view_form_1_page(self):
        # Ticket 64: counting source files split 1 rendered page into 2 groups.
        self.write('app/Parcel.php', '')
        self.write('resources/views/cart.blade.php', '')
        controller = 'app/Http/Controllers/CartController.php'
        view = 'resources/views/cart/index.blade.php'
        self.write(view, "{{ __('Save') }} {{ __('orders.title') }}")
        # G40: a response view must join the same page as the other literal renders.
        for render in ["view('cart.index')", 'View::make("cart.index", [])',
                       "response()->view('cart.index')"]:
            with self.subTest(render=render):
                self.write(controller, "<?php __('orders.hello'); __('orders.title'); return " + render + ';')
                self.assertEqual(self.report()['by_page']['groups'], {
                    view: ['Save', 'orders.hello', 'orders.title'],
                    'no use found': ['orders.count']})

    def test_response_view_among_2_renders_keeps_controller_separate(self):
        # G40: mixed render forms in either order, or 2 response views.
        self.write('app/Parcel.php', '')
        controller = 'app/Http/Controllers/CartController.php'
        self.write('resources/views/orders/index.blade.php', "{{ __('orders.hello') }}")
        renders = ["view('cart'); return response()->view('orders.index');",
                   "response()->view('orders.index'); return view('cart');",
                   "response()->view('cart'); return response()->view('orders.index');"]
        for render in renders:
            with self.subTest(render=render):
                self.write(controller, "<?php __('orders.title'); " + render)
                self.assertEqual(self.report()['by_page']['groups'], {
                    controller: ['orders.title'],
                    'resources/views/cart.blade.php': ['Save'],
                    'resources/views/orders/index.blade.php': ['orders.hello'],
                    'no use found': ['orders.count']})

    def test_unrelated_controller_and_view_stay_2_pages(self):
        controller = 'app/Http/Controllers/CartController.php'
        self.write('app/Parcel.php', '')
        renders = ["return response('OK');", 'return view($page);',
                   "return view('cart.' . $page);", "return view('cart.missing');",
                   "view('cart'); return view('orders.index');",
                   "// return view('cart');\nreturn response('OK');",
                   '''$example = "view('cart')"; return response('OK');''']
        for render in renders:
            with self.subTest(render=render):
                self.write(controller, "<?php __('orders.title'); " + render)
                self.assertEqual(self.report()['by_page']['groups'], {
                    controller: ['orders.title'],
                    'resources/views/cart.blade.php': ['Save'],
                    'no use found': ['orders.count', 'orders.hello']})

    def test_unreadable_translation_is_preserved_and_marked_not_checked(self):
        self.write('lang/ar/orders.php', '<?php return [')
        report = self.report()
        error, = report['check1']
        self.assertTrue(error['unreadable'])
        self.assertTrue(error['reason'])
        self.assertEqual(error['file'], 'ar/orders.php')
        self.assertEqual(error['page'], 'no use found')
        self.assertEqual(report['not_checked'], ['ar/orders.php unreadable'])

    def test_calls_skip_comments_strings_interpolation_and_excluded_folders(self):
        self.write('app/Parcel.php', """<?php
Lang::get('orders.title'); Lang::choice('orders.hello', 2);
__('Save'); trans('orders.count');
// __('fake.line');
/* trans('fake.block'); */
$example = "__('fake.string')";
__('orders.title' . $suffix);
__("orders.$suffix");
""")
        for path in ['app/tests/Skip.php', 'app/vendor/Skip.php', 'resources/lang/Skip.php',
                     'routes/node_modules/Skip.php', 'database/tests/Skip.php']:
            self.write(path, "<?php __('fake.folder'); $mail->subject('Hidden words');")
        report = self.report()
        self.assertEqual(report['check2'], [])
        self.assertEqual(report['check4'], [])
        self.assertEqual(report['check6']['no_trace'], [])
        self.assertEqual(report['check6']['dynamic_call_sites'], ['app/Parcel.php:7', 'app/Parcel.php:8'])

    def test_json_whole_keys_and_nested_php_groups_are_literal_identities(self):
        for locale in ['en', 'ar']:
            self.write(f'lang/{locale}/sector/parcel.php', "<?php return ['nested' => ['label' => 'Label']];")
            self.write(f'lang/{locale}.json', '{"Save": "Label", "whole.key": "Label"}')
        self.write('app/Parcel.php', "<?php __('sector/parcel.nested.label'); __('whole.key');")
        report = self.report()
        self.assertEqual(report['check2'], [])
        self.assertEqual(report['by_page']['groups']['app/Parcel.php'], ['sector/parcel.nested.label', 'whole.key'])

    def test_custom_lang_path_uses_its_actual_repo_prefix(self):
        shutil.move(str(self.root / 'lang'), str(self.root / 'resources' / 'lang'))
        changed = self.changed(['resources\\lang\\en\\orders.php'])
        self.assertFalse(self.report('--lang', self.root / 'resources/lang', '--changed-files', changed)
                         ['no_translation_files_changed'])
        changed = self.changed(['resources/language/other.php'])
        self.assertTrue(self.report('--lang', self.root / 'resources/lang', '--changed-files', changed)
                        ['no_translation_files_changed'])

    def test_nested_translation_arguments_do_not_become_literal_text(self):
        self.write('app/Parcel.php', "<?php __('Save', ['n' => $mail->subject('Hidden words')]);")
        self.assertEqual(self.report()['g4_literal_text'], [])
        self.write('app/Parcel.php', "<?php $mail->subject('Visible words');")
        self.assertEqual(self.report()['g4_literal_text'], ['app/Parcel.php:1'])

    def test_choice_dynamic_calls_do_not_explain_unused_keys(self):
        self.write('app/Parcel.php', "<?php trans_choice('orders.' . $key, 2); Lang::get('orders.' . $key);")
        self.assertEqual(self.report()['check6'], dict(variable=[],
            no_trace=['orders.count', 'orders.hello', 'orders.title'], dynamic_call_sites=['app/Parcel.php:1']))

    def test_replacement_arrays_must_escape_the_whole_expression(self):
        cases = [("[]", True), ("array('n' => e($x))", True),
                 ("['n' => e($x) . $y]", False), ("$replacements", False),
                 ("['n' => e($x)] + $unsafe", False), ("array('n' => e($x)) + $unsafe", False)]
        for replacement, escaped in cases:
            with self.subTest(replacement=replacement):
                self.write('resources/views/cart.blade.php', "{!! __('Save', " + replacement + ') !!}')
                self.assertEqual(self.report()['check7'][0]['args_escaped'], escaped)

    def test_escaped_dollar_is_literal_and_interpolation_is_dynamic(self):
        self.write('lang/en.json', json.dumps({'price.$unit': 'Price'}))
        self.write('lang/ar.json', json.dumps({'price.$unit': 'السعر'}))
        self.write('resources/views/cart.blade.php', '')
        self.write('app/Parcel.php', '<?php __("price.\\$unit");\n__("price.$unit");')
        report = self.report()
        self.assertEqual(report['check2'], [])
        self.assertEqual(report['check6']['dynamic_call_sites'], ['app/Parcel.php:2'])
        self.assertEqual(report['by_page']['groups']['app/Parcel.php'], ['price.$unit'])

    def test_blade_attributes_and_inline_script_comments_are_not_text_nodes(self):
        self.write('resources/views/cart.blade.php', '''<input title="a > b">
<style>.color { color: #abc; }</style>
<script>// Hidden words</script>
<p>Visible words</p>
''')
        self.assertEqual(self.report()['g4_literal_text'], ['resources/views/cart.blade.php:4'])

    def test_logger_receivers_are_separate_from_outer_conditions(self):
        for call in ["Log::channel('parcel')->error('Hidden words')",
                     "Log::stack(['single'])->error('Hidden words')",
                     "logger()->channel($channel)->error('Hidden words')"]:
            with self.subTest(call=call):
                self.write('app/Parcel.php', '<?php ' + call + ';')
                self.assertEqual(self.report()['g4_literal_text'], [])
        self.write('app/Parcel.php', "<?php if ($logger->isHandling('info')) { $mail->subject('Visible words'); }")
        self.assertEqual(self.report()['g4_literal_text'], ['app/Parcel.php:1'])

    def test_bad_arguments_and_child_errors_have_one_stderr_line(self):
        bad = self.write('bad.json', '{}')
        cases = [('--repo', self.root / 'missing'), ('--repo', self.root / 'bad.json'),
                 ('--unknown', 'x'), ('--lang', self.root / 'missing'),
                 ('--changed-files', bad), ('--base-lang', self.root / 'missing')]
        for args in cases:
            with self.subTest(args=args):
                run = self.run_cli(*args)
                self.assertEqual(run.returncode, 2)
                self.assertEqual(run.stdout, '')
                self.assertEqual(len(run.stderr.splitlines()), 1)
        run = self.run_cli('--changed-files', bad)
        self.assertEqual(run.stderr, 'translation_keys.py: changed files must be a list\n')


if __name__ == '__main__':
    unittest.main()
