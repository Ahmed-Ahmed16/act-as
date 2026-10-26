import io
import json
import os
import re
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path, PurePosixPath

if __package__:
    from .size_counter import ArgumentParser, GitError, git_bytes
else:
    from size_counter import ArgumentParser, GitError, git_bytes

PATTERNS = {
    'S1': ("->find(", "findOrFail(", "where('id'", "_id')"),
    'S3': ('$request->all()', '->fill(', 'forceFill(', 'updateOrCreate(', '->sync(', '->attach(', 'createMany('),
    'S4': ('whereRaw', 'selectRaw', 'havingRaw', 'orderByRaw', 'DB::raw', 'DB::select(', 'DB::statement(', 'orderBy($'),
    'S5': ('unique:', 'Rule::unique', '->ignore('),
    'S6': ('->store(', '->storeAs(', '->move(', 'getClientOriginalName', 'public_path('),
    'S7': ('VerifyCsrfToken', '$except', 'csrf'), 'S8': ('{!!', 'fputcsv'),
    'S9': ('redirect($request', 'redirect()->to(', '->away(', "request('next')"),
    'S11': ('signedRoute', 'temporarySignedRoute', 'signed'),
    'S12': ('throttle', 'regenerate(', 'invalidate(', "Route::post('/login", "Route::post('login", 'password/reset', 'two-factor'),
    'S13': ('APP_DEBUG', 'trustProxies', 'config([', "'secure' =>", "'http_only' =>", "'same_site' =>"),
    'S14': ('Process::run(', 'shell_exec(', 'proc_open(', 'exec(', 'passthru(', 'system('),
    'S15': ('unserialize(', 'eval(', 'extract('), 'S16': ('->download(', 'response()->file', 'file_get_contents(', 'Storage::'),
    'S17': ('Http::get(', 'Http::post(', 'file_get_contents(', 'curl_'), 'S18': ('->json(', '$hidden'),
    'S19': ('Log::', 'logger(', 'report(')}
REMOVED = ('authorize', 'can:', 'middleware', 'signed', 'throttle', 'validate', 'lockForUpdate', "where('user_id'")
RULE_GROUPS = {
    'S3': ('php.laravel.security', 'laravel-dangerous-model-construction'),
    'S4': ('php.laravel.security', 'laravel-sql-injection laravel-api-route-sql-injection'),
    'S5': ('php.laravel.security', 'laravel-unsafe-validator'),
    'S7': ('php.laravel.security', 'laravel-blade-form-missing-csrf'),
    'S13': ('php.laravel.security', 'laravel-active-debug-code laravel-cookie-http-only laravel-cookie-long-timeout laravel-cookie-null-domain laravel-cookie-same-site laravel-cookie-secure-set'),
    'S14': ('php.lang.security', 'exec-use backticks-use'),
    'S15': ('php.lang.security', 'unserialize-use eval-use'), 'S17': ('php.lang.security', 'php-ssrf')}
RULES = {f'{prefix}.{name}.{name}': check for check, (prefix, names) in RULE_GROUPS.items() for name in names.split()}
RULES['php.lang.security.injection.tainted-exec.tainted-exec'] = 'S14'
SECRET_SHAPES = tuple(map(re.compile, (r'AKIA[0-9A-Z]{16}', r'ghp_[A-Za-z0-9]{20,}', r'sk_live_[A-Za-z0-9]{10,}', r'-----BEGIN [A-Z ]*PRIVATE KEY-----')))
SECRET = re.compile('|'.join(regex.pattern for regex in SECRET_SHAPES))
ENV = re.compile(r"(env\('[A-Z_]+',\s*)'([^']+)'")
FETCH = ("import pathlib,sys,urllib.request; "
         "[(pathlib.Path('/rules')/(r+'.yaml')).write_bytes(urllib.request.urlopen('https://semgrep.dev/c/r/'+r).read()) for r in sys.argv[1:]]")


def redact(text):
    return SECRET.sub('[redacted]', ENV.sub(r"\1'[redacted]'", text))


def save_json(path, report):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(redact(json.dumps(report, indent=2)) + '\n', encoding='utf-8')


def paths(filename):
    document = json.loads(filename.read_text(encoding='utf-8'))
    if not isinstance(document, dict) or not isinstance(document.get('files'), list):
        raise ValueError('files.json must contain a files list')
    selected = set()
    for row in document['files']:
        if not isinstance(row, dict) or not isinstance(row.get('path'), str) or not isinstance(row.get('status'), str):
            raise ValueError('files.json has an invalid file')
        path = row['path']
        if not path or path.startswith('/') or '..' in PurePosixPath(path).parts or any(c in path for c in '\n\r\0\\:'):
            raise ValueError('files.json has an unsafe path')
        if row['status'] != 'deleted':
            selected.add(path)
    return sorted(selected)


def pathcheck(expected, scanned):
    actual = set(scanned.read_text(encoding='utf-8').splitlines())
    extra, missing = sorted(actual - set(expected)), sorted(set(expected) - actual)
    return 'pathcheck: pass' if not extra and not missing else (
        f'pathcheck: fail, extra: {", ".join(extra)}, missing: {", ".join(missing)}')


def matches(path, side, text):
    table = dict(PATTERNS) if side == 'added' else {'S11': PATTERNS['S11'], 'S22': REMOVED, 'S7': ('@csrf',)}
    if side == 'added':
        if path.startswith('routes/'):
            table['S2'] = ('Route::post', 'Route::put', 'Route::patch', 'Route::delete')
        if path.startswith(('Resources/', 'app/Http/Resources/')) or '/Resources/' in path:
            table['S18'] += ('toArray(',)
        if path == 'composer.json':
            table['S21'] = ('"repositories"', '"scripts"')
    found = [(check, pattern) for check, patterns in table.items() for pattern in patterns if pattern in text]
    if side == 'added':
        found += [('S10', regex.pattern) for regex in (ENV, *SECRET_SHAPES) if regex.search(text)]
    return found


def patch_hits(path, patch):
    hits, old, new = [], 0, 0
    for line in patch.split('\n'):
        header = re.match(r'@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@', line)
        if header:
            old, new = map(int, header.groups())
        elif (old or new) and line.startswith(('+', '-')):
            side, number = ('added', new) if line[0] == '+' else ('removed', old)
            for check, pattern in matches(path, side, line[1:]):
                hits.append(dict(check=check, pattern=pattern, side=side, path=path, line=number, text=redact(line[1:])[:160]))
            old += side == 'removed'
            new += side == 'added'
    return hits


def finders(options):
    comparison = options.base + '...' + options.head
    diff = ('diff', '--no-renames', '--no-ext-diff', '--no-textconv')
    files = git_bytes(options.repo, *diff, '--name-only', '-z', comparison).decode('utf-8', 'surrogateescape').split('\0')[:-1]
    hits = []
    for path in files:
        patch = git_bytes(options.repo, *diff, '-U0', comparison, '--', ':(literal)' + path).decode('utf-8', 'replace')
        side = 'removed' if '\n+++ /dev/null\n' in patch else 'added'
        for check, pattern, applies in [('S20', 'path:webhook_or_callback', re.search('webhook|callback', path, re.I)),
            ('S21', 'path:dependency_manifest', path in ('composer.json', 'composer.lock', 'package.json', 'package-lock.json'))]:
            if applies:
                hits.append(dict(check=check, pattern=pattern, side=side, path=path, line=0, text=''))
        if path.endswith(('.php', '.env.example', '.json', '.js', '.yml', '.yaml')) or path == 'composer.lock':
            hits.extend(patch_hits(path, patch))
    return dict(files=files, hits=hits)


def run(argv, runner):
    try:
        return runner(argv, capture_output=True)
    except OSError:
        return subprocess.CompletedProcess(argv, None, b'', b'')


def unchecked(tool, reason, exit_code=None):
    return dict(status='not checked', line=f'not checked: {tool} did not run, {reason}', exit=exit_code, findings=[])


def container(tool, mounts):
    return ['docker', 'run', '--rm', '--name', f'actas-t33-{tool}-{os.getpid()}',
            *[arg for mount in mounts for arg in ('-v', mount)]]


def raw_output(out, tool, completed):
    stdout = completed.stdout.decode('utf-8', 'replace')
    stderr = completed.stderr.decode('utf-8', 'replace')
    safe = '\n'.join(line for line in (stdout + '\n' + stderr).splitlines() if not line.lstrip().startswith('Secret:'))
    (out / f'{tool}-raw.txt').write_text(redact(safe)[-16000:], encoding='utf-8')
    return stdout


def semgrep_finding(hit):
    rule, path, line = hit['check_id'], hit['path'], hit['start']['line']
    if not isinstance(rule, str) or not isinstance(path, str) or type(line) is not int or line < 1:
        raise ValueError('invalid finding')
    check = next(check for full, check in RULES.items() if rule == full or rule.endswith('.' + full))
    return dict(rule=rule, check=check, path=path, line=line)


def semgrep(options, mounts, selected, runner):
    with tempfile.TemporaryDirectory(prefix='actas-rules-') as folder:
        rules = Path(folder)
        fetch = run(container('rules', [f'{rules}:/rules:rw']) +
                    ['--network', 'bridge', options.image, 'python3', '-c', FETCH, *RULES], runner)
        raw_output(options.out, 'semgrep', fetch)
        if fetch.returncode != 0 or any(not (rules / (rule + '.yaml')).is_file() or (rules / (rule + '.yaml')).stat().st_size == 0 for rule in RULES):
            return unchecked('semgrep', 'rules fetch failed', fetch.returncode)
        completed = run(container('semgrep', mounts + [f'{rules}:/rules:ro']) +
            ['--network', 'none', '-e', 'SEMGREP_ENABLE_VERSION_CHECK=0', '-w', '/src', options.image,
             'semgrep', 'scan', '--metrics=off', '--disable-version-check', '--config', '/rules', '--json', '--error', '--', *selected], runner)
        stdout = raw_output(options.out, 'semgrep', completed)
        (options.out / 'semgrep-raw.json').write_text(redact(stdout), encoding='utf-8')
        if completed.returncode not in (0, 1):
            return unchecked('semgrep', f'exit {completed.returncode}', completed.returncode)
        try:
            report = json.loads(stdout)
            if not isinstance(report['results'], list) or report.get('errors'):
                raise ValueError('invalid results')
            findings = [semgrep_finding(hit) for hit in report['results']]
        except (ValueError, KeyError, TypeError, StopIteration):
            return unchecked('semgrep', 'invalid JSON', completed.returncode)
        return dict(status='ran', line=f'ran: semgrep, {len(findings)} findings', exit=completed.returncode, findings=findings)


def composer_audit(options, mounts, root, runner):
    audit = unchecked('composer audit', 'no composer.lock in the head')
    if (root / 'composer.lock').is_file():
        completed = run(container('composer', mounts) + ['--network', 'bridge', '-e', 'COMPOSER_ALLOW_SUPERUSER=1',
            '-e', 'COMPOSER_HOME=/tmp/c', '-w', '/src', options.image, 'composer', 'audit', '--locked', '--no-interaction', '--no-cache', '--no-plugins'], runner)
        stdout = raw_output(options.out, 'composer', completed)
        audit = unchecked('composer audit', f'exit {completed.returncode}', completed.returncode)
        if completed.returncode in (0, 1):
            count = sum(line.startswith('Package:') for line in stdout.splitlines()) if completed.returncode else 0
            audit = dict(status='ran', line=f'ran: composer audit, {count} advisories', exit=completed.returncode, advisories=count)
    return audit


def gitleaks(options, mounts, runner):
    completed = run(container('gitleaks', mounts) + ['--network', 'none', options.image,
                    'gitleaks', 'dir', '--no-banner', '--redact', '-v', '/src'], runner)
    raw_output(options.out, 'gitleaks', completed)
    leaks = unchecked('gitleaks', f'exit {completed.returncode}', completed.returncode)
    if completed.returncode in (0, 1):
        findings, rule = [], ''
        for line in (completed.stdout + b'\n' + completed.stderr).decode('utf-8', 'replace').splitlines():
            if line.strip().startswith('RuleID:'):
                rule = line.strip().partition(':')[2].strip()
            elif line.strip().startswith('File:') and rule and completed.returncode == 1:
                findings.append(dict(rule=rule, path=line.strip().partition(':')[2].strip()))
        leaks = dict(status='ran', line=f'ran: gitleaks, {len(findings)} findings', exit=completed.returncode, findings=findings)
        if completed.returncode == 1 and not findings:
            leaks = unchecked('gitleaks', 'invalid output', 1)
    return leaks


def tools(options, runner):
    selected = paths(options.files)
    options.out.mkdir(parents=True, exist_ok=True)
    path_file = options.out / 'semgrep-paths.txt'
    path_file.write_text(''.join(path + '\n' for path in selected), encoding='utf-8')
    docker = run(['docker', 'version', '--format', '{{.Server.Version}}'], runner)
    if docker.returncode != 0:
        lines = docker.stderr.decode('utf-8', 'replace').strip().splitlines()
        reason = 'Docker is off' + (f' ({redact(lines[0])[:80]})' if lines else '')
        statuses = {key: unchecked(label, reason) for key, label in
                    [('semgrep', 'semgrep'), ('composer_audit', 'composer audit'), ('gitleaks', 'gitleaks')]}
        statuses['semgrep']['paths'] = selected
        return dict(image=options.image, tools=statuses)
    archive = git_bytes(options.repo, 'archive', options.head)
    with tempfile.TemporaryDirectory(prefix='actas-head-') as folder:
        root = Path(folder)
        with tarfile.open(fileobj=io.BytesIO(archive)) as tree:
            tree.extractall(root, filter='data')
        mounts = [f'{root}:/src:ro']
        scan = unchecked('semgrep', 'no changed files to scan')
        if pathcheck(selected, path_file) != 'pathcheck: pass':
            scan = unchecked('semgrep', 'path list differs from files.json')
        elif selected:
            scan = semgrep(options, mounts, selected, runner)
        if pathcheck(paths(options.files), path_file) != 'pathcheck: pass':
            scan = unchecked('semgrep', 'path list differs from files.json')
        scan['paths'] = selected
        return dict(image=options.image, tools=dict(semgrep=scan,
                    composer_audit=composer_audit(options, mounts, root, runner), gitleaks=gitleaks(options, mounts, runner)))


def arguments(args):
    parser = ArgumentParser(allow_abbrev=False)
    commands = parser.add_subparsers(dest='command', required=True, parser_class=ArgumentParser)
    for name, flags in [('paths', ('files',)), ('pathcheck', ('files', 'scanned')),
                        ('finders', ('repo', 'base', 'head', 'out')), ('tools', ('repo', 'head', 'files', 'out'))]:
        command = commands.add_parser(name, allow_abbrev=False)
        for flag in flags:
            command.add_argument('--' + flag, required=True, type=str if flag in ('base', 'head') else Path)
        if name == 'tools':
            command.add_argument('--image', default='actas-reviewer:2026-10-26')
    options = parser.parse_args(args)
    for revision in (getattr(options, 'base', None), getattr(options, 'head', None)):
        if revision is not None and (not revision or revision.startswith('-')):
            raise ValueError('base and head must be git revisions')
    if hasattr(options, 'repo') and not options.repo.is_dir():
        raise ValueError('repo is missing or not a folder')
    if hasattr(options, 'image') and (not options.image or options.image.startswith('-')):
        raise ValueError('image must be a Docker image name')
    return options


def main(args, runner=subprocess.run):
    try:
        options = arguments(args)
        if options.command == 'paths':
            print(''.join(path + '\n' for path in paths(options.files)), end='')
        elif options.command == 'pathcheck':
            verdict = pathcheck(paths(options.files), options.scanned)
            print(verdict)
            return int(verdict != 'pathcheck: pass')
        else:
            report = finders(options) if options.command == 'finders' else tools(options, runner)
            target = options.out / ('security-' + options.command + '.json')
            save_json(target, report)
            print(target)
        return 0
    except GitError as error:
        print('security_scan: ' + redact(' '.join(str(error).splitlines())), file=sys.stderr)
        return 1
    except (ValueError, OSError, tarfile.TarError) as error:
        print('security_scan: ' + redact(' '.join(str(error).splitlines())), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    sys.exit(main(sys.argv[1:]))
