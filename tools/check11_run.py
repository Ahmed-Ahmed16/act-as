import hashlib
import json
import math
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from check11_parse import parse
from health_parse import ArgumentParser, outcome, run_cli

RESULT_WORDS = ('finding', 'clean', 'not checked', 'does not apply')


def command_args(command, copy, image, number=1):
    if not image or not image.strip():
        raise ValueError('--image is required')
    return ['docker', 'run', '--rm', '--network', 'none', '--name',
            f'actas-t36-{os.getpid()}-{number}', '-v', str(copy) + ':/work',
            '-w', '/work', image, 'sh', '-c', command]


class UnsafeTree(ValueError):
    pass


class StepTimeout(ValueError):
    pass


def git_output(repo, *args):
    completed = subprocess.run(['git', '-C', str(repo), *args], capture_output=True)
    if completed.returncode:
        raise ValueError('git failed: ' + completed.stderr.decode('utf-8', errors='replace').strip())
    return completed.stdout


def frozen_tree(repo, head, snapshot):
    # Git blobs include export ignored files and never read the working tree.
    snapshot.mkdir()
    links = []
    for entry in git_output(repo, 'ls-tree', '-rz', '--full-tree', head).split(b'\0'):
        if not entry:
            continue
        metadata, name = entry.split(b'\t', 1)
        mode, kind, object_id = metadata.decode('ascii').split()
        path = snapshot / os.fsdecode(name)
        if not path.resolve().is_relative_to(snapshot) or '.git' in path.relative_to(snapshot).parts:
            raise UnsafeTree('tracked path leaves the tree')
        if kind != 'blob':
            raise UnsafeTree('tracked entry is not a blob: ' + os.fsdecode(name))
        content = git_output(repo, 'cat-file', 'blob', object_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        if mode == '120000':
            links.append((path, os.fsdecode(content)))
        else:
            path.write_bytes(content)
            path.chmod(0o755 if mode == '100755' else 0o644)
    for path, destination in links:
        validate_link_target(path, destination, snapshot)
        try:
            path.symlink_to(destination)
        except OSError as error:
            raise UnsafeTree('symlink could not be preserved: ' + str(path.relative_to(snapshot))) from error
    validate_links(snapshot)


def validate_links(tree):
    for folder, dirs, files in os.walk(tree, followlinks=False):
        for name in dirs + files:
            path = Path(folder) / name
            if path.is_symlink():
                validate_link_target(path, os.readlink(path), tree)


def validate_link_target(path, destination, tree):
    try:
        inside = (path.parent / destination).resolve().is_relative_to(tree)
    except (OSError, RuntimeError, ValueError) as error:
        raise UnsafeTree('invalid symlink: ' + str(path.relative_to(tree))) from error
    if not inside:
        raise UnsafeTree('symlink leaves the tree: ' + str(path.relative_to(tree)))


def rebuild_copy(snapshot, copy):
    if copy.is_symlink():
        os.unlink(copy)
    elif copy.exists():
        shutil.rmtree(copy)
    shutil.copytree(snapshot, copy, symlinks=True)


def checkout_hashes(repo):
    hashes = {}
    for folder, dirs, files in os.walk(repo):
        dirs[:] = [name for name in dirs if name not in ('.git', 'vendor', 'node_modules', 'storage')]
        for name in files + [name for name in dirs if (Path(folder) / name).is_symlink()]:
            if name == '.git':
                continue
            path = Path(folder) / name
            if path.is_symlink():
                hashes[str(path.relative_to(repo))] = 'symlink:' + os.readlink(path)
                continue
            with path.open('rb') as source:
                hashes[str(path.relative_to(repo))] = hashlib.file_digest(source, 'sha256').hexdigest()
    return hashes


def validate_spec(spec):
    if not isinstance(spec, dict) or not isinstance(spec.get('command'), str) or '{test}' not in spec['command']:
        raise ValueError('spec command must contain {test}')
    if not isinstance(spec.get('tests'), list):
        raise ValueError('spec tests must be a list')
    if len(spec['tests']) > 3:
        raise ValueError('pick at most 3 tests')
    for picked in spec['tests']:
        if not isinstance(picked, dict) or any(not isinstance(picked.get(key), str) or
                                               not picked[key].strip() for key in ('name', 'probe')):
            raise ValueError('each test needs a name and a probe')
        fault = picked.get('fault')
        if not isinstance(fault, dict) or any(not isinstance(fault.get(key), str)
                                              for key in ('file', 'old', 'new')):
            raise ValueError('fault needs file, old and new strings')
        path = Path(fault['file'])
        if not fault['old'] or not fault['file'] or path.is_absolute() or path.drive or '..' in path.parts:
            raise ValueError('fault needs nonempty old text and a relative file inside the copy')


class Runner:
    def __init__(self, copy, image, timeout=600):
        self.copy, self.image, self.number, self.steps = copy, image, 0, []
        self.timeout = timeout

    def run(self, step, command):
        self.number += 1
        argv = command_args(command, self.copy, self.image, self.number)
        try:
            completed = subprocess.run(argv, cwd=self.copy, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, text=True, encoding='utf-8',
                                       errors='replace', timeout=self.timeout)
        except subprocess.TimeoutExpired:
            evidence = dict(step=step, command=command, argv=argv, cwd=str(self.copy), timed_out=True)
            self.steps.append(evidence)
            try:
                name = argv[argv.index('--name') + 1]
                stopped = subprocess.run(['docker', 'stop', '-t', '0', name],
                                         capture_output=True, text=True, timeout=10)
                evidence.update(stop_exit=stopped.returncode, stop_output=stopped.stdout + stopped.stderr)
            except (OSError, subprocess.TimeoutExpired) as error:
                evidence['stop_error'] = str(error)
            raise StepTimeout(f'{step} timed out') from None
        output = completed.stdout + completed.stderr
        evidence = dict(step=step, command=command, argv=argv, cwd=str(self.copy),
                        exit_code=completed.returncode, output='\n'.join(output.splitlines()[-40:]),
                        parsed=parse(output, completed.returncode))
        if step.startswith('probe_'):
            evidence['stdout'] = completed.stdout
        self.steps.append(evidence)
        return evidence


def fault_verdict(red, before, after):
    state = red['parsed']['state']
    if state == 'ok':
        if (before['stdout'], before['exit_code']) != (after['stdout'], after['exit_code']):
            return 'finding', 'test stayed green with a fault that contradicts it'
        return 'not checked', 'fault did not contradict the assertion'
    if state == 'error':
        return 'not checked', 'red was not an assertion failure'
    if state != 'assertion':
        return 'not checked', 'test did not run after the fault'
    return 'clean', red['parsed']['message']


def check_test(picked, command, runner, snapshot):
    runner.steps = []
    try:
        rebuild_copy(snapshot, runner.copy)
        return run_test(picked, command, runner, snapshot)
    except (StepTimeout, UnsafeTree) as error:
        return dict(test=picked['name'], tool_result='not checked', reason=str(error),
                    word='none', steps=runner.steps)


def run_test(picked, command, runner, snapshot):
    # Keep the ordered fault/reset sequence together so reset stays in its finally block.
    command = command.replace('{test}', shlex.quote(picked['name']))
    start = runner.run('start', command)['parsed']['state']
    tool_result, reason = 'not checked', 'fault could not be applied'
    if start != 'ok':
        reason = {'unrunnable': 'tests cannot run here', 'none': 'test did not run'}.get(
            start, 'test was not green at start')
    else:
        before = runner.run('probe_before', picked['probe'])
        fault = picked['fault']
        target = runner.copy / fault['file']
        if not target.resolve().is_relative_to(runner.copy):
            raise ValueError('fault file leaves the copy')
        try:
            original = target.read_bytes()
        except FileNotFoundError:
            original = b''
        applied = original.count(fault['old'].encode('utf-8')) == 1
        runner.steps.append(dict(step='fault', **fault, applied=applied))
        if applied:
            try:
                target.write_bytes(original.replace(fault['old'].encode('utf-8'), fault['new'].encode('utf-8')))
                after = runner.run('probe_after', picked['probe'])
                red = runner.run('fault_run', command)
                tool_result, reason = fault_verdict(red, before, after)
            finally:
                rebuild_copy(snapshot, runner.copy)
                if target.exists() or target.is_symlink():
                    os.unlink(target)
                shutil.copyfile(snapshot / fault['file'], target)
                equal = target.read_bytes() == (snapshot / fault['file']).read_bytes()
                runner.steps.append(dict(step='reset', byte_equal=equal))
                green = runner.run('green_again', command)['parsed']['state']
            if tool_result == 'clean' and (not equal or green != 'ok'):
                tool_result, reason = 'not checked', 'copy did not return to green after reset'
    return dict(test=picked['name'], tool_result=tool_result, reason=reason,
                word='must fix' if tool_result == 'finding' else 'none', steps=runner.steps)


def aggregate(tests):
    # Pick counts: 0/1/2/3. Findings win over unchecked tests, which win over clean.
    result_word = ('finding' if any(test['tool_result'] == 'finding' for test in tests) else
                   'not checked' if any(test['tool_result'] == 'not checked' for test in tests) else
                   'clean' if tests else 'does not apply')
    reason = '; '.join(f'{test["test"]}: {test["reason"]}' for test in tests
                       if test['tool_result'] == result_word)
    reason = (reason + f'; covers {len(tests)} picked tests') if tests else 'no test in a risky area'
    return outcome(result_word, reason + '; local evidence: independent-check.json',
                   tests=[dict(test=t['test'], tool_result=t['tool_result'], reason=t['reason']) for t in tests])


def read_record(path):
    record = json.loads(path.read_text(encoding='utf-8')) if path.exists() else dict(required_ids=[], entries=[])
    if (not isinstance(record, dict) or not isinstance(record.get('entries'), list) or
            any(not isinstance(entry, dict) for entry in record['entries']) or
            not isinstance(record.get('required_ids', []), list)):
        raise ValueError('record must contain entries and required_ids lists')
    return record


def write_record(path, record, summary, reading_result):
    entry = dict(id='H11', mode='health', area='', kind='check', tool_result=summary['result'],
                 reading_result=reading_result, word='must fix' if summary['result'] == 'finding' else 'none',
                 reason=summary['reason'], base_read='', head_read='')
    record['entries'] = [entry if old.get('id') == 'H11' else old for old in record['entries']]
    if not any(old.get('id') == 'H11' for old in record['entries']):
        record['entries'].append(entry)
    path.write_text(json.dumps(record, indent=2), encoding='utf-8')


def main():
    parser = ArgumentParser()
    for flag in ('repo', 'spec', 'out'):
        parser.add_argument('--' + flag, required=True, type=Path)
    parser.add_argument('--image', required=True)
    parser.add_argument('--head', required=True)
    parser.add_argument('--timeout', type=float, default=600)
    parser.add_argument('--record', type=Path)
    parser.add_argument('--reading-result', choices=RESULT_WORDS)
    args = parser.parse_args()
    if not args.image.strip():
        raise ValueError('--image is required')
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        raise ValueError('--timeout must be positive and finite')
    repo = args.repo.resolve()
    if not repo.is_dir():
        raise ValueError('repo must be a checkout folder')
    if args.record and not args.reading_result:
        raise ValueError('--reading-result is required with --record')
    if any(path.resolve().is_relative_to(repo) for path in [args.out] + ([args.record] if args.record else [])):
        raise ValueError('output and record must be outside the checkout')
    spec = json.loads(args.spec.read_text(encoding='utf-8'))
    validate_spec(spec)
    record = read_record(args.record) if args.record else None
    head = git_output(repo, 'rev-parse', '--verify', '--end-of-options', args.head + '^{commit}').decode().strip()
    before = checkout_hashes(repo)
    scratch = Path(tempfile.mkdtemp(prefix='actas-t36-'))
    tree_error = ''
    try:
        copy = scratch / 'checkout'
        snapshot = scratch / 'head'
        try:
            frozen_tree(repo, head, snapshot)
            runner = Runner(copy, args.image, args.timeout)
            tests = [check_test(picked, spec['command'], runner, snapshot) for picked in spec['tests']]
        except UnsafeTree as error:
            tree_error = str(error)
            tests = [dict(test=picked['name'], tool_result='not checked', reason=str(error),
                          word='none', steps=[]) for picked in spec['tests']]
    finally:
        shutil.rmtree(scratch)
        if checkout_hashes(repo) != before:
            raise ValueError('checkout changed')
    summary = aggregate(tests)
    if tree_error and not tests:
        summary = outcome('not checked', tree_error + '; local evidence: independent-check.json', tests=[])
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'independent-check.json').write_text(json.dumps(
        dict(command=spec['command'], image=args.image, head=head, tests=tests), indent=2), encoding='utf-8')
    if record is not None:
        write_record(args.record, record, summary, args.reading_result)
    return summary


if __name__ == '__main__':
    sys.exit(run_cli(main))
