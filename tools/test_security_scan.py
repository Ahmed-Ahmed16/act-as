import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


EXEC_RULE = 'php.lang.security.injection.tainted-exec.tainted-exec'


class DockerRunner:
    # The only fake boundary is Docker. Git and packet files stay real.
    def __init__(self, **settings):
        self.settings = settings
        self.calls = []
        self.sources = {}
        self.rules_dir = None

    def __call__(self, argv, **kwargs):
        if argv[0] == 'git':
            return subprocess.run(argv, **kwargs)
        if argv[0] != 'docker':
            raise AssertionError('Unexpected host command: ' + repr(argv))
        self.calls.append(argv)
        for tool in ('semgrep', 'composer', 'gitleaks'):
            if tool in argv:
                source = next(argv[n + 1].rsplit(':/src:', 1)[0]
                              for n, arg in enumerate(argv)
                              if arg == '-v' and ':/src:' in argv[n + 1])
                root = Path(source)
                self.sources[tool] = {path.relative_to(root).as_posix(): path.read_bytes()
                                      for path in root.rglob('*') if path.is_file()}
        if argv[1] == 'version':
            failure = self.settings.get('docker', 0)
            if isinstance(failure, OSError):
                raise failure
            return subprocess.CompletedProcess(argv, failure, b'28.0\n',
                                               self.settings.get('stderr', b''))
        if 'python3' in argv:
            mount = argv[argv.index('-v') + 1]
            self.rules_dir = Path(mount.rsplit(':/rules', 1)[0])
            for rule in argv[argv.index('python3') + 3:]:
                (self.rules_dir / (rule + '.yaml')).write_text(
                    '' if self.settings.get('empty_rules') else 'rules: []', encoding='utf-8')
            return subprocess.CompletedProcess(argv, self.settings.get('fetch', 0), b'', b'')
        if 'semgrep' in argv:
            source = next(argv[n + 1].rsplit(':/src:', 1)[0]
                          for n, arg in enumerate(argv) if arg == '-v' and ':/src:' in argv[n + 1])
            self.snapshot = (Path(source) / 'app/Fern.php').read_text(encoding='utf-8')
            payload = self.settings.get('payload', json.dumps({'results': [{
                'check_id': EXEC_RULE, 'path': 'app/Fern.php', 'start': {'line': 3},
                'extra': {'lines': 'exec($fern);'}}],
                'paths': {'scanned': ['app/Fern.php']}}).encode())
            return subprocess.CompletedProcess(argv, self.settings.get('semgrep', 1), payload, b'')
        if 'composer' in argv:
            advisories = {'fern/leaf': [{'advisoryId': f'PKSA-fern-{n}'} for n in range(18)]}
            payload = json.dumps({'advisories': advisories if self.settings.get('composer') == 1 else [],
                                  'abandoned': {}}).encode()
            return subprocess.CompletedProcess(argv, self.settings.get('composer', 0),
                self.settings.get('composer_payload', payload), b'')
        if 'gitleaks' in argv:
            return subprocess.CompletedProcess(argv, self.settings.get('gitleaks', 1),
                self.settings.get('leak_output',
                    b'RuleID: fern-token\nSecret: planted-secret\nFile: /src/app/Fern.php\n'), b'')
        raise AssertionError('Unexpected Docker command: ' + repr(argv))


class SecurityScanTests(unittest.TestCase):
    # Cases: empty/all deleted/mixed paths; added/removed/multiple hunks;
    # clean/insecure lines; secret defaults/key shapes; Docker off/failed/clean;
    # bad JSON/empty rules/tool errors; unsafe paths/revisions/archive links.
    # Removing a filter, mask, exit branch, or container flag must fail a case.
    def setUp(self):
        self.script = Path(__file__).with_name('security_scan.py')
        self.assertTrue(self.script.is_file(), 'security_scan.py has not been built')
        spec = importlib.util.spec_from_file_location('security_scan', self.script)
        self.scan = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.scan)
        self.tree = tempfile.TemporaryDirectory(prefix='fern-scan-')
        self.addCleanup(self.tree.cleanup)
        self.root = Path(self.tree.name)
        self.repo = self.root / 'fern'
        self.repo.mkdir()
        self.out = self.root / 'packet'
        self.files = self.root / 'files.json'
        self.env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM='1',
                        PYTHONDONTWRITEBYTECODE='1')
        self.git('init', '-b', 'main')
        self.git('config', 'user.name', 'Fern')
        self.git('config', 'user.email', 'fern@leaf.invalid')
        self.base = self.commit()
        self.write('app/Fern.php', '<?php\n$fern = 1;\nexec($fern);\n')
        self.write('composer.lock', '{}\n')
        self.head = self.commit()
        self.file_rows([('app/Fern.php', 'added'), ('composer.lock', 'modified')])

    def git(self, *args):
        run = subprocess.run(['git', '-c', 'core.autocrlf=false',
                              '-c', 'commit.gpgsign=false', '-C', str(self.repo), *args],
                             capture_output=True, env=self.env)
        self.assertEqual(run.returncode, 0, run.stderr.decode('utf-8', 'replace'))
        return run.stdout.decode('utf-8', 'surrogateescape').strip()

    def write(self, path, text):
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding='utf-8')

    def commit(self):
        self.git('add', '-A')
        self.git('commit', '--allow-empty', '-m', 'Update fern')
        return self.git('rev-parse', 'HEAD')

    def file_rows(self, rows):
        self.files.write_text(json.dumps({'files': [dict(path=p, status=s) for p, s in rows]}),
                              encoding='utf-8')

    def cli(self, *args, runner=None):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = self.scan.main(list(map(str, args)), runner=runner or DockerRunner())
        return code, stdout.getvalue(), stderr.getvalue()

    def tools(self, runner=None, *extra):
        before = self.git('status', '--porcelain')
        code, stdout, stderr = self.cli('tools', '--repo', self.repo, '--head', self.head,
            '--files', self.files, '--out', self.out, *extra, runner=runner)
        self.assertEqual((code, stderr), (0, ''))
        self.assertEqual(stdout.strip(), str(self.out / 'security-tools.json'))
        self.assertEqual(self.git('status', '--porcelain'), before)
        return json.loads((self.out / 'security-tools.json').read_text(encoding='utf-8'))

    def finders(self):
        code, stdout, stderr = self.cli('finders', '--repo', self.repo, '--base', self.base,
                                       '--head', self.head, '--out', self.out)
        self.assertEqual((code, stderr), (0, ''))
        self.assertEqual(stdout.strip(), str(self.out / 'security-finders.json'))
        return json.loads((self.out / 'security-finders.json').read_text(encoding='utf-8'))

    def test_paths_and_pathcheck_compare_sets(self):
        self.file_rows([('z.php', 'modified'), ('a.php', 'added'), ('gone.php', 'deleted'),
                        ('odd.php', 'other:t')])
        self.assertEqual(self.cli('paths', '--files', self.files), (0, 'a.php\nodd.php\nz.php\n', ''))
        scanned = self.root / 'scanned.txt'
        for contents, code, expected in [
            ('z.php\na.php\nodd.php\na.php\n', 0, 'pathcheck: pass\n'),
            ('extra.php\na.php\n', 1, 'pathcheck: fail, extra: extra.php, missing: odd.php, z.php\n')]:
            with self.subTest(contents=contents):
                scanned.write_text(contents, encoding='utf-8')
                self.assertEqual(self.cli('pathcheck', '--files', self.files, '--scanned', scanned),
                                 (code, expected, ''))

    def test_finders_report_added_removed_and_file_hits_with_line_numbers(self):
        self.write('routes/fern.php', "Route::get('/fern')->middleware('auth');\n")
        self.base = self.commit()
        self.write('routes/fern.php', "Route::post('/fern');\n")
        self.write('app/Leaf.php', '<?php\nDB::raw($x);\nLog::info($request->password);\n'
                   'redirect($request->next);\n$leaf = 3;\n')
        self.write('composer.lock', '{"fern": 2}\n')
        self.write('app/FernWebhook.php', 'leaf\nleaf\n')
        self.head = self.commit()
        report = self.finders()
        hits = {(h['check'], h['pattern'], h['side'], h['path'], h['line']) for h in report['hits']}
        self.assertEqual(hits, {
            ('S4', 'DB::raw', 'added', 'app/Leaf.php', 2),
            ('S19', 'Log::', 'added', 'app/Leaf.php', 3),
            ('S9', 'redirect($request', 'added', 'app/Leaf.php', 4),
            ('S22', 'middleware', 'removed', 'routes/fern.php', 1),
            ('S2', 'Route::post', 'added', 'routes/fern.php', 1),
            ('S21', 'path:dependency_manifest', 'added', 'composer.lock', 0),
            ('S20', 'path:webhook_or_callback', 'added', 'app/FernWebhook.php', 0)})
        self.assertEqual(report['files'],
                         ['app/FernWebhook.php', 'app/Leaf.php', 'composer.lock', 'routes/fern.php'])
        self.assertEqual(len(hits), len(report['hits']))

    def test_bound_query_and_authorize_are_clean_for_s4(self):
        self.write('app/Leaf.php', "$this->authorize('read');\n$rows = query('id = ?', [$id]);\n")
        self.head = self.commit()
        self.assertEqual([h for h in self.finders()['hits'] if h['check'] == 'S4'], [])

    # Cases: path scalar/lists/nesting, free text, secret shapes in paths.
    def test_review_patch_paths_keep_repo_names_but_mask_secrets(self):
        paths = ['resources/views/home/partials/a.blade.php',
                 'app/home/Models/User.php', 'app/Users/admin/x.php']
        private = '/home/ahmed/secret'
        document = dict(files=paths, path=paths[0], paths=dict(scanned=paths),
                        results=[dict(path=paths[1], extra=dict(lines=private))],
                        text=private, extra=[private], lines=[private])
        masked = self.scan.redact_strings(document)
        self.assertEqual(masked['files'], paths)
        self.assertEqual(masked['path'], paths[0])
        self.assertEqual(masked['paths']['scanned'], paths)
        self.assertEqual(masked['results'][0]['path'], paths[1])
        self.assertEqual(masked['results'][0]['extra']['lines'], '[redacted]secret')
        self.assertEqual(masked['text'], '[redacted]secret')
        self.assertEqual(masked['extra'], ['[redacted]secret'])
        self.assertEqual(masked['lines'], ['[redacted]secret'])
        secret = 'ghp_' + 'k' * 24
        self.assertEqual(self.scan.redact_strings(dict(path='app/' + secret + '.php')),
                         dict(path='app/[redacted].php'))
        self.assertEqual(self.scan.redact_strings(dict(files=["env('KEY', 'private')"])),
                         dict(files=["env('KEY', '[redacted]')"]))

    def test_review_patch_paths_survive_saved_finder_report(self):
        path = 'resources/views/home/partials/a.blade.php'
        self.write(path, '{!! $x !!} /home/ahmed/secret\n')
        self.head = self.commit()
        report = self.finders()
        self.assertIn(path, report['files'])
        hit, = [hit for hit in report['hits'] if hit['check'] == 'S8']
        self.assertEqual(hit['path'], path)
        self.assertEqual(hit['text'].rstrip('\r'), '{!! $x !!} [redacted]secret')

    def test_review_patch_paths_survive_semgrep_reports(self):
        path = 'resources/views/home/partials/a.blade.php'
        self.write(path, '<?php exec($x);\n')
        self.head = self.commit()
        selected = ['app/Fern.php', path]
        self.file_rows([(name, 'added') for name in selected])
        payload = dict(results=[dict(check_id=EXEC_RULE, path=path, start=dict(line=1),
                                    extra=dict(lines='/home/ahmed/secret'))],
                       paths=dict(scanned=selected))
        scan = self.tools(DockerRunner(payload=json.dumps(payload).encode()))['tools']['semgrep']
        self.assertEqual(scan['status'], 'ran')
        self.assertEqual(scan['paths'], selected)
        self.assertEqual(scan['findings'][0]['path'], path)
        raw = json.loads((self.out / 'semgrep-raw.json').read_text(encoding='utf-8'))
        self.assertEqual(raw['results'][0]['path'], path)
        self.assertEqual(raw['paths']['scanned'], selected)
        self.assertEqual(raw['results'][0]['extra']['lines'], '[redacted]secret')

    # Cases: head suppressions, no config, unrelated config, malformed/nonobject JSON.
    def test_review_patch_config_head_suppressions_are_removed_from_scan(self):
        self.write('.gitleaks.toml', '[allowlist]\npaths = [".*"]\n')
        config_bytes = (self.repo / '.gitleaks.toml').read_bytes()
        self.write('.gitleaksignore', 'planted-fingerprint\n')
        composer = dict(name='fern/leaf', require={'fern/stem': '^1.0'},
                        config={'audit': {'ignore': {'PKSA-x': 'y'}}, 'sort-packages': True})
        self.write('composer.json', json.dumps(composer))
        self.head = self.commit()
        runner = DockerRunner()
        report = self.tools(runner)
        for tool in ('semgrep', 'composer_audit', 'gitleaks'):
            self.assertEqual(report['tools'][tool]['status'], 'ran')
        command = next(argv for argv in runner.calls if 'gitleaks' in argv)
        trusted = 'GITLEAKS_CONFIG_TOML=[extend]\nuseDefault = true'
        with self.subTest(setting='trusted gitleaks config'):
            self.assertIn(trusted, command)
            self.assertEqual(command[command.index(trusted) - 1], '-e')
            self.assertLess(command.index(trusted), command.index(report['image']))
        with self.subTest(setting='gitleaks comments'):
            self.assertIn('--ignore-gitleaks-allow', command)
        for tool in ('semgrep', 'composer', 'gitleaks'):
            with self.subTest(tool=tool, setting='fingerprints'):
                self.assertNotIn('.gitleaksignore', runner.sources[tool])
            with self.subTest(tool=tool, setting='composer config'):
                self.assertEqual(runner.sources[tool]['.gitleaks.toml'],
                                 config_bytes)
                exported = json.loads(runner.sources[tool]['composer.json'])
                self.assertEqual(exported, dict(name='fern/leaf', require={'fern/stem': '^1.0'},
                                               config={'sort-packages': True}))
        command = next(argv for argv in runner.calls if 'semgrep' in argv)
        self.assertIn('--disable-nosem', command)

    def test_review_patch_config_other_or_invalid_composer_is_kept(self):
        for contents in ('{"config":{"sort-packages":true},"name":"fern/leaf"}',
                         '{broken JSON\n', '[]', 'null', '{"config":[]}'):
            with self.subTest(contents=contents):
                self.write('composer.json', contents)
                original = (self.repo / 'composer.json').read_bytes()
                self.head = self.commit()
                runner = DockerRunner()
                report = self.tools(runner)
                self.assertEqual(report['tools']['composer_audit']['status'], 'ran')
                self.assertEqual(runner.sources['composer']['composer.json'], original)

    def test_all_finder_patterns_and_side_filters(self):
        fixtures = [
            ('S1', '->find('), ('S1', 'findOrFail('), ('S1', "where('id'"), ('S1', "_id')"),
            ('S3', '$request->all()'), ('S3', '->fill('), ('S3', 'forceFill('),
            ('S3', 'updateOrCreate('), ('S3', '->sync('), ('S3', '->attach('), ('S3', 'createMany('),
            ('S4', 'whereRaw'), ('S4', 'selectRaw'), ('S4', 'havingRaw'), ('S4', 'orderByRaw'),
            ('S4', 'DB::raw'), ('S4', 'DB::select('), ('S4', 'DB::statement('), ('S4', 'orderBy($'),
            ('S5', 'unique:'), ('S5', 'Rule::unique'), ('S5', '->ignore('),
            ('S6', '->store('), ('S6', '->storeAs('), ('S6', '->move('),
            ('S6', 'getClientOriginalName'), ('S6', 'public_path('),
            ('S7', 'VerifyCsrfToken'), ('S7', '$except'), ('S7', 'csrf'),
            ('S8', '{!!'), ('S8', 'fputcsv'), ('S9', 'redirect($request'),
            ('S9', 'redirect()->to('), ('S9', '->away('), ('S9', "request('next')"),
            ('S11', 'signedRoute'), ('S11', 'temporarySignedRoute'), ('S11', 'signed'),
            ('S12', 'throttle'), ('S12', 'regenerate('), ('S12', 'invalidate('),
            ('S12', "Route::post('/login"), ('S12', "Route::post('login"),
            ('S12', 'password/reset'), ('S12', 'two-factor'), ('S13', 'APP_DEBUG'),
            ('S13', 'trustProxies'), ('S13', 'config(['), ('S13', "'secure' =>"),
            ('S13', "'http_only' =>"), ('S13', "'same_site' =>"),
            ('S14', 'Process::run('), ('S14', 'shell_exec('), ('S14', 'proc_open('),
            ('S14', 'exec('), ('S14', 'passthru('), ('S14', 'system('),
            ('S15', 'unserialize('), ('S15', 'eval('), ('S15', 'extract('),
            ('S16', '->download('), ('S16', 'response()->file'),
            ('S16', 'file_get_contents('), ('S16', 'Storage::'), ('S17', 'Http::get('),
            ('S17', 'Http::post('), ('S17', 'file_get_contents('), ('S17', 'curl_'),
            ('S18', '->json('), ('S18', '$hidden'),
            ('S19', 'Log::'), ('S19', 'logger('), ('S19', 'report(')]
        self.write('Resources/Leaf.php', '\n'.join(pattern for _, pattern in fixtures) + '\ntoArray(\n')
        self.write('app/Leaf.txt', 'DB::raw($x);\n')
        self.write('routes/Leaf.php', "->authorize( can: permission:\n")
        self.head = self.commit()
        hits = self.finders()['hits']
        for line, (check, pattern) in enumerate(fixtures, 1):
            with self.subTest(check=check, pattern=pattern):
                self.assertIn((check, pattern, line), [(h['check'], h['pattern'], h['line']) for h in hits
                                                       if h['path'] == 'Resources/Leaf.php'])
        self.assertIn(('S18', 'toArray(', len(fixtures) + 1),
                      [(h['check'], h['pattern'], h['line']) for h in hits])
        self.assertFalse(any(h['path'] in ('app/Leaf.txt', 'routes/Leaf.php') for h in hits))

    def test_removed_csrf_signed_and_all_s22_patterns(self):
        patterns = ['authorize', 'can:', 'middleware', 'signed', 'throttle', 'validate',
                    'lockForUpdate', "where('user_id'", '@csrf', 'DB::raw']
        self.write('app/Leaf.php', '\n'.join(patterns) + '\n')
        self.base = self.commit()
        self.write('app/Leaf.php', 'leaf\n')
        self.head = self.commit()
        hits = self.finders()['hits']
        self.assertEqual({(h['check'], h['pattern'], h['side'], h['line']) for h in hits},
            {('S22', p, 'removed', n) for n, p in enumerate(patterns[:8], 1)} |
            {('S7', '@csrf', 'removed', 9), ('S11', 'signed', 'removed', 4)})

    def test_review_n6_php_templates_produce_sql_hits(self):
        for name in ['a.phtml', 'b.tpl']:
            self.write(name, '<?php DB::raw($x); ?>\n')
        self.head = self.commit()
        hits = self.finders()['hits']
        for name in ['a.phtml', 'b.tpl']:
            with self.subTest(path=name):
                self.assertIn(('S4', name, 1),
                              [(h['check'], h['path'], h['line']) for h in hits])

    def test_secrets_are_masked_even_when_another_check_matches(self):
        secrets = ['AKIA' + 'F' * 16, 'ghp_' + 'g' * 24, 'sk_live_' + 'h' * 12,
                   '-----BEGIN FERN PRIVATE KEY-----', 'fern-default']
        self.write('.env.example', '\n'.join('Log::info("' + s + '");' for s in secrets[:4])
                   + "\nenv('FERN_KEY', 'fern-default');\nenv('EMPTY', '');\n")
        self.head = self.commit()
        report = self.finders()
        self.assertEqual(len([h for h in report['hits'] if h['check'] == 'S10']), 5)
        saved = (self.out / 'security-finders.json').read_text(encoding='utf-8')
        for secret in secrets:
            self.assertNotIn(secret, saved)
        self.assertIn("'[redacted]'", saved)

    def test_multiple_secret_shapes_and_patch_prefixes_keep_all_hits(self):
        self.base = self.head
        key = 'AKIA' + 'J' * 16
        token = 'ghp_' + 'k' * 24
        self.write('app/Fern.php', '++DB::raw($x);\n--Log::info($x);\n' + key + ' ' + token + '\n')
        self.head = self.commit()
        report = self.finders()
        self.assertIn(('S4', 1), [(h['check'], h['line']) for h in report['hits']])
        self.assertEqual(len([h for h in report['hits'] if h['check'] == 'S10']), 2)
        self.assertNotIn(key, json.dumps(report))
        self.assertNotIn(token, json.dumps(report))

    def test_review_g21_scrub_shapes_are_masked_in_saved_hit_text(self):
        secrets = ['sk-ant-api03-' + 'a' * 40, 'ASIA' + 'B' * 16,
                   'github_pat_' + 'c' * 30, 'sk-proj-' + 'd' * 40,
                   'AIza' + 'E' * 35, 'xoxb-' + 'f' * 20,
                   'eyJ' + 'g' * 12 + '.eyJ' + 'h' * 12 + '.' + 'i' * 12,
                   'api_key = "' + 'j' * 16 + '"',
                   'D:' + '\\Users\\fern\\site', 'fern' + '@' + 'leaf.invalid']
        self.write('app/Leaf.php', '\n'.join('Log::info(' + s + ');' for s in secrets))
        self.head = self.commit()
        report = self.finders()
        texts = [hit['text'] for hit in report['hits'] if hit['path'] == 'app/Leaf.php']
        expected = ['Log::info([redacted]);'] * len(secrets)
        expected[8] = 'Log::info([redacted]fern\\site);'
        self.assertEqual([text.rstrip('\r') for text in texts], expected)
        saved = (self.out / 'security-finders.json').read_text(encoding='utf-8')
        for secret in secrets:
            self.assertNotIn(secret, saved)

    def test_review_g22_export_attributes_do_not_omit_or_rewrite_blobs(self):
        cases = [('export-ignore', '<?php\nexec($fern);\n'),
                 ('export-subst', '<?php\n// $Format:%H$\nexec($fern);\n')]
        for attribute, contents in cases:
            with self.subTest(attribute=attribute):
                self.write('.gitattributes', 'app/Fern.php ' + attribute + '\n')
                self.write('app/Fern.php', contents)
                self.head = self.commit()
                runner = DockerRunner()
                self.tools(runner)
                self.assertEqual(getattr(runner, 'snapshot', None), contents)

    def test_review_g23_skipped_php_is_not_checked(self):
        self.write('app/Leaf.php', '<?php\nexec($leaf);\n')
        self.head = self.commit()
        self.file_rows([('app/Fern.php', 'modified'), ('app/Leaf.php', 'added'),
                        ('composer.lock', 'modified')])
        payload = json.dumps({'results': [], 'paths': {'scanned': ['app/Fern.php']}}).encode()
        scan = self.tools(DockerRunner(semgrep=0, payload=payload))['tools']['semgrep']
        self.assertEqual(scan['status'], 'not checked')
        self.assertIn('missing: app/Leaf.php', scan['line'])

    def test_review_g23_reported_paths_distinguish_missing_invalid_and_complete(self):
        # PHP rules do not cover the lock file. Empty and absent paths differ.
        cases = [(None, 'not checked', 'not checked: semgrep did not report scanned paths'),
                 ({'scanned': []}, 'not checked', 'missing: app/Fern.php'),
                 ({'scanned': 'app/Fern.php'}, 'not checked', 'invalid JSON'),
                 ({'scanned': [7]}, 'not checked', 'invalid JSON'),
                 ({'scanned': ['app/Fern.php\napp/Fern.php']}, 'not checked', 'invalid JSON'),
                 ({'scanned': ['./app/Fern.php']}, 'ran', 'pathcheck: pass')]
        for reported, status, message in cases:
            with self.subTest(reported=reported):
                payload = {'results': []}
                if reported is not None:
                    payload['paths'] = reported
                scan = self.tools(DockerRunner(semgrep=0, payload=json.dumps(payload).encode()))['tools']['semgrep']
                self.assertEqual(scan['status'], status)
                self.assertIn(message, scan.get('pathcheck', scan['line']))

    def test_review_g23_php_templates_require_scan_coverage(self):
        for name in ['app/Leaf.blade.php', 'app/Leaf.phtml', 'app/Leaf.tpl']:
            self.write(name, '<?php exec($leaf);\n')
        self.head = self.commit()
        self.file_rows([(name, 'added') for name in
                        ['app/Fern.php', 'app/Leaf.blade.php', 'app/Leaf.phtml', 'app/Leaf.tpl', 'composer.lock']])
        scan = self.tools(DockerRunner())['tools']['semgrep']
        self.assertEqual(scan['status'], 'not checked')
        self.assertIn('missing: app/Leaf.blade.php, app/Leaf.phtml, app/Leaf.tpl', scan['pathcheck'])

    def test_review_g24_composer_counts_json_advisories_by_package(self):
        payload = json.dumps({'advisories': {
            'fern/leaf': [{'advisoryId': 'PKSA-fern-1'}, {'advisoryId': 'PKSA-fern-2'}],
            'fern/stem': [{'advisoryId': 'PKSA-fern-3'}]}, 'abandoned': {}}).encode()
        runner = DockerRunner(composer=1, composer_payload=payload)
        audit = self.tools(runner)['tools']['composer_audit']
        self.assertEqual((audit['status'], audit['advisories']), ('ran', 3))
        command = next(argv for argv in runner.calls if 'composer' in argv)
        self.assertIn('--format=json', command)

    def test_review_g24_invalid_audit_json_is_not_checked(self):
        for payload in [b'not json', b'{}', b'{"advisories": null}',
                        b'{"advisories": {"fern/leaf": {}}}']:
            with self.subTest(payload=payload):
                audit = self.tools(DockerRunner(composer_payload=payload))['tools']['composer_audit']
                self.assertEqual(audit['status'], 'not checked')
                self.assertIn('invalid JSON', audit['line'])

    def test_diffs_do_not_execute_checkout_textconverters(self):
        self.base = self.head
        self.write('.gitattributes', '*.php diff=fern\n')
        self.write('app/Fern.php', 'DB::raw($x);\n')
        self.head = self.commit()
        self.git('config', 'diff.fern.textconv', 'missing-fern-program')
        self.assertTrue(any(h['check'] == 'S4' for h in self.finders()['hits']))

    def test_docker_off_records_exact_reasons_and_finders_still_work(self):
        for failure, stderr, suffix in [(1, b'', ''),
            (1, b'fern daemon sleeping\nother line', ' (fern daemon sleeping)'),
            (FileNotFoundError('docker missing'), b'', '')]:
            with self.subTest(failure=failure):
                report = self.tools(DockerRunner(docker=failure, stderr=stderr))
                for key, label in [('semgrep', 'semgrep'), ('composer_audit', 'composer audit'),
                                   ('gitleaks', 'gitleaks')]:
                    self.assertEqual(report['tools'][key]['status'], 'not checked')
                    self.assertEqual(report['tools'][key]['line'],
                                     f'not checked: {label} did not run, Docker is off{suffix}')
        self.assertTrue(self.finders()['hits'])

    def test_tool_results_and_container_boundaries(self):
        runner = DockerRunner()
        report = self.tools(runner)
        self.assertEqual(report['image'], 'actas-reviewer:2026-10-26')
        semgrep = report['tools']['semgrep']
        self.assertEqual((semgrep['status'], semgrep['exit']), ('ran', 1))
        self.assertEqual(semgrep['findings'],
            [dict(rule=EXEC_RULE, check='S14', path='app/Fern.php', line=3)])
        self.assertEqual(semgrep['paths'], ['app/Fern.php', 'composer.lock'])
        self.assertEqual((self.out / 'semgrep-paths.txt').read_text(), 'app/Fern.php\n')
        self.assertEqual(json.loads((self.out / 'semgrep-raw.json').read_text())['results'][0]['check_id'],
                         EXEC_RULE)
        self.assertEqual(report['tools']['gitleaks']['findings'],
                         [dict(rule='fern-token', path='/src/app/Fern.php')])
        self.assertNotIn('planted-secret', (self.out / 'gitleaks-raw.txt').read_text())
        self.assertIsNotNone(runner.rules_dir)
        self.assertFalse(runner.rules_dir.exists())
        for argv in runner.calls[1:]:
            self.assertIn('--rm', argv)
            self.assertTrue(argv[argv.index('--name') + 1].startswith('actas-t33-'))
            self.assertNotIn('docker.sock', ' '.join(argv))
            mounts = [argv[n + 1] for n, arg in enumerate(argv) if arg == '-v']
            if 'python3' in argv:
                self.assertEqual(len(mounts), 1)
                self.assertTrue(mounts[0].endswith(':/rules:rw'))
                self.assertNotIn('/src', ' '.join(mounts))
            else:
                self.assertTrue(any(m.endswith(':/src:ro') for m in mounts))
                if 'semgrep' in argv or 'gitleaks' in argv:
                    self.assertEqual(argv[argv.index('--network') + 1], 'none')
                if 'semgrep' in argv:
                    self.assertIn('SEMGREP_ENABLE_VERSION_CHECK=0', argv)
                    self.assertEqual(argv[argv.index('--') + 1:], semgrep['paths'])
                    for flag in ['--metrics=off', '--disable-version-check', '--json', '--error']:
                        self.assertIn(flag, argv)
                if 'composer' in argv:
                    self.assertIn('--no-plugins', argv)
                    self.assertIn('COMPOSER_HOME=/tmp/c', argv)
        self.assertFalse(any(self.out.glob('*.yaml')))

    def test_tool_errors_are_data_and_rules_failures_are_distinct(self):
        cases = [({'fetch': 1}, 'semgrep', 'rules fetch failed'),
                 ({'empty_rules': True}, 'semgrep', 'rules fetch failed'),
                 ({'semgrep': 2}, 'semgrep', 'exit 2'),
                 ({'payload': b'not json'}, 'semgrep', 'invalid JSON'),
                 ({'payload': b'{"results": {}}'}, 'semgrep', 'invalid JSON'),
                 ({'composer': 100}, 'composer_audit', 'exit 100'),
                 ({'gitleaks': 2}, 'gitleaks', 'exit 2')]
        for settings, key, reason in cases:
            with self.subTest(settings=settings):
                runner = DockerRunner(**settings)
                tool = self.tools(runner)['tools'][key]
                label = 'composer audit' if key == 'composer_audit' else key
                self.assertEqual(tool['status'], 'not checked')
                self.assertEqual(tool['line'], f'not checked: {label} did not run, {reason}')
                if runner.rules_dir is not None:
                    self.assertFalse(runner.rules_dir.exists())

    def test_prefixed_rule_ids_keep_the_printed_id_and_map_to_check(self):
        rule = 'rules.' + EXEC_RULE
        report = self.tools(DockerRunner(payload=json.dumps({'results': [{
            'check_id': rule, 'path': 'app/Fern.php', 'start': {'line': 3}}]}).encode()))
        self.assertEqual(report['tools']['semgrep']['findings'],
                         [dict(rule=rule, check='S14', path='app/Fern.php', line=3)])

    def test_unlisted_scanned_path_is_not_checked(self):
        payload = json.dumps({'results': [], 'paths': {'scanned': ['unlisted.php']}}).encode()
        runner = DockerRunner(payload=payload)
        report = self.tools(runner)
        self.assertEqual(report['tools']['semgrep']['status'], 'not checked')
        self.assertEqual(report['tools']['semgrep']['pathcheck'],
                         'pathcheck: fail, extra: unlisted.php, missing: app/Fern.php')

    # Cases: nested dicts/lists, integer/normal keys, shared masks and reserved suffixes.
    def test_nested_secret_keys_are_redacted_in_output_and_saved_json(self):
        aws, github = 'AKIA' + 'J' * 16, 'ghp_' + 'k' * 24
        document = {'normal': [{aws: {github: 'kept'}}], 7: 'integer'}
        expected = {'normal': [{'[redacted]': {'[redacted]': 'kept'}}], '7': 'integer'}
        self.assertEqual(self.scan.redact_strings(document)[7], 'integer')
        target = self.out / 'keys.json'
        self.scan.save_json(target, document)
        for label, output in [('redact_output', self.scan.redact_output(json.dumps(document))),
                              ('save_json', target.read_text(encoding='utf-8'))]:
            with self.subTest(output=label):
                self.assertEqual(json.loads(output), expected)

    def test_redacted_key_collisions_preserve_entries_and_normal_keys(self):
        aws, github = 'AKIA' + 'J' * 16, 'ghp_' + 'k' * 24
        document = {aws: 'aws', github: 'github', '[redacted]#2': 'normal'}
        self.assertEqual(self.scan.redact_strings(document),
                         {'[redacted]': 'aws', '[redacted]#3': 'github', '[redacted]#2': 'normal'})

    def test_raw_tail_masks_the_whole_secret_before_cutting(self):
        token = 'ghp_' + 'T' * 24
        payload = json.dumps({'results': [], 'padding': token + '.' * 15985}).encode()
        self.tools(DockerRunner(semgrep=0, payload=payload))
        raw = (self.out / 'semgrep-raw.txt').read_text(encoding='utf-8')
        self.assertNotIn('T' * 10, raw)
        self.assertIn('[redacted]', raw)

    def test_review_n5_semgrep_json_masks_nested_strings_before_saving(self):
        # Cases: nested objects/lists, scalar values, successful/failed scans.
        source = '$password = "abcdefgh123456";'
        payload = {'results': [{'check_id': EXEC_RULE, 'path': 'app/Fern.php',
                    'start': {'line': 3}, 'extra': {'lines': source,
                    'metadata': [source, {'source': source}, 7, None, True]}}],
                   'paths': {'scanned': ['app/Fern.php']}}
        for exit_code in [0, 2]:
            with self.subTest(exit_code=exit_code):
                scan = self.tools(DockerRunner(semgrep=exit_code,
                    payload=json.dumps(payload).encode()))['tools']['semgrep']
                self.assertEqual(scan['status'], 'ran' if exit_code == 0 else 'not checked')
                for suffix in ['json', 'txt']:
                    with self.subTest(suffix=suffix):
                        saved = (self.out / ('semgrep-raw.' + suffix)).read_text(encoding='utf-8')
                        self.assertNotIn('abcdefgh123456', saved)
                        self.assertIn('[redacted]', saved)
                        extra = json.loads(saved)['results'][0]['extra']
                        self.assertEqual(extra['lines'], '$[redacted];')
                        self.assertEqual(extra['metadata'],
                                         ['$[redacted];', {'source': '$[redacted];'}, 7, None, True])

    def test_review_n5_invalid_semgrep_json_masks_quoted_assignments(self):
        # Cases: plain/escaped quotes, interior escaped quote, truncated value.
        sources = ['$value = ' + quote + 'abcdefgh123456' + quote + ';'
                   for quote in ['"', "'", '\\"', "\\'"]]
        sources += [json.dumps({'lines': '$value = "prefix\\"abcdefgh123456";'})[:-1],
                    r'{"lines":"$password = \"abcdefgh123456']
        for source in sources:
            with self.subTest(source=source):
                payload = ('broken JSON\n' + source + '\nscan diagnostic').encode()
                scan = self.tools(DockerRunner(payload=payload))['tools']['semgrep']
                self.assertEqual(scan['status'], 'not checked')
                self.assertIn('invalid JSON', scan['line'])
                for suffix in ['json', 'txt']:
                    with self.subTest(suffix=suffix):
                        saved = (self.out / ('semgrep-raw.' + suffix)).read_text(encoding='utf-8')
                        self.assertNotIn('abcdefgh123456', saved)
                        self.assertIn('[redacted]', saved)
                        self.assertIn('scan diagnostic', saved)

    def test_gitleaks_exit_1_without_complete_findings_is_not_checked(self):
        for output in [b'', b'RuleID: fern-token\n', b'File: /src/app/Fern.php\n']:
            with self.subTest(output=output):
                report = self.tools(DockerRunner(leak_output=output))
                self.assertEqual(report['tools']['gitleaks']['status'], 'not checked')
                self.assertEqual(report['tools']['gitleaks']['line'],
                                 'not checked: gitleaks did not run, invalid output')

    def test_export_uses_head_and_keeps_dirty_checkout_contents(self):
        self.write('app/Fern.php', 'uncommitted fern\n')
        runner = DockerRunner()
        self.tools(runner)
        self.assertEqual(runner.snapshot, '<?php\n$fern = 1;\nexec($fern);\n')
        self.assertEqual((self.repo / 'app/Fern.php').read_text(), 'uncommitted fern\n')

    def test_composer_advisories_clean_tools_and_missing_lock(self):
        report = self.tools(DockerRunner(composer=1))
        self.assertEqual(report['tools']['composer_audit']['advisories'], 18)
        self.assertEqual(report['tools']['composer_audit']['status'], 'ran')
        report = self.tools(DockerRunner(semgrep=0, payload=b'{"results": []}', gitleaks=0))
        self.assertEqual(report['tools']['semgrep']['findings'], [])
        self.assertEqual(report['tools']['gitleaks']['findings'], [])
        self.assertEqual(report['tools']['composer_audit']['advisories'], 0)
        (self.repo / 'composer.lock').unlink()
        self.head = self.commit()
        runner = DockerRunner()
        report = self.tools(runner)
        self.assertEqual(report['tools']['composer_audit']['line'],
                         'not checked: composer audit did not run, no composer.lock in the head')
        self.assertFalse(any('composer' in argv for argv in runner.calls))

    def test_empty_paths_skip_semgrep_and_custom_image_is_used(self):
        self.file_rows([('gone.php', 'deleted')])
        runner = DockerRunner()
        report = self.tools(runner, '--image', 'fern-scanner:1')
        self.assertEqual(report['tools']['semgrep']['line'],
                         'not checked: semgrep did not run, no changed files to scan')
        self.assertEqual(report['image'], 'fern-scanner:1')
        self.assertFalse(any('semgrep' in argv or 'python3' in argv for argv in runner.calls))

    def test_bad_arguments_and_bad_git_have_distinct_exit_codes(self):
        for args in [(), ('unknown',), ('paths',),
            ('finders', '--repo', self.repo, '--base=-oops', '--head', self.head, '--out', self.out),
            ('tools', '--repo', self.repo, '--head', self.head, '--files', self.files,
             '--out', self.out, '--image=--privileged'),
            ('tools', '--repo', self.root / 'absent', '--head', self.head,
             '--files', self.files, '--out', self.out)]:
            with self.subTest(args=args):
                code, stdout, stderr = self.cli(*args)
                self.assertEqual((code, stdout), (2, ''))
                self.assertTrue(stderr.startswith('security_scan: '))
                self.assertEqual(len(stderr.splitlines()), 1)
        for mode in ['tools', 'finders']:
            args = ['--files', self.files] if mode == 'tools' else ['--base', self.base]
            code, stdout, stderr = self.cli(mode, '--repo', self.repo, '--head', 'f' * 40,
                                            '--out', self.out, *args)
            self.assertEqual((code, stdout), (1, ''))
            self.assertTrue(stderr.startswith('security_scan: git'))

    def test_malformed_files_and_unsafe_paths_are_bad_arguments(self):
        for document in [{}, {'files': None}, {'files': [{}]},
                         {'files': [{'path': '../fern', 'status': 'added'}]},
                         {'files': [{'path': '/fern', 'status': 'added'}]},
                         {'files': [{'path': 'fern\nleaf', 'status': 'added'}]}]:
            with self.subTest(document=document):
                self.files.write_text(json.dumps(document), encoding='utf-8')
                code, stdout, stderr = self.cli('paths', '--files', self.files)
                self.assertEqual((code, stdout), (2, ''))
                self.assertTrue(stderr.startswith('security_scan: '))

    def test_forbidden_flag_is_absent(self):
        forbidden = 'ignore-' + 'unreachable'
        self.assertNotIn(forbidden, self.script.read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
