import hashlib
import json
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


def command_args(command, copy, image=None, number=1):
    if image:
        return ['docker', 'run', '--rm', '--network', 'none', '--name',
                f'actas-t36-{os.getpid()}-{number}', '-v', str(copy) + ':/work',
                '-w', '/work', image, 'sh', '-c', command]
    return ['sh', '-c', command]


def checkout_hashes(repo):
    hashes = {}
    for folder, dirs, files in os.walk(repo):
        dirs[:] = [name for name in dirs if name not in ('.git', 'vendor', 'node_modules', 'storage')]
        for name in files:
            if name == '.git':
                continue
            path = Path(folder) / name
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
    def __init__(self, copy, image):
        self.copy, self.image, self.number, self.steps = copy, image, 0, []

    def run(self, step, command):
        self.number += 1
        argv = command_args(command, self.copy, self.image, self.number)
        completed = subprocess.run(argv, cwd=self.copy, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace')
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


def check_test(picked, command, runner, repo):
    # Keep the ordered fault/reset sequence together so reset stays in its finally block.
    runner.steps = []
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
                shutil.copyfile(repo / fault['file'], target)
                equal = target.read_bytes() == (repo / fault['file']).read_bytes()
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
    parser.add_argument('--image')
    parser.add_argument('--record', type=Path)
    parser.add_argument('--reading-result', choices=RESULT_WORDS)
    args = parser.parse_args()
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
    before = checkout_hashes(repo)
    scratch = Path(tempfile.mkdtemp(prefix='actas-t36-'))
    try:
        copy = scratch / 'checkout'
        shutil.copytree(repo, copy, ignore=shutil.ignore_patterns('.git'))
        runner = Runner(copy, args.image)
        tests = [check_test(picked, spec['command'], runner, repo) for picked in spec['tests']]
    finally:
        shutil.rmtree(scratch)
        if checkout_hashes(repo) != before:
            raise ValueError('checkout changed')
    summary = aggregate(tests)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'independent-check.json').write_text(json.dumps(
        dict(command=spec['command'], image=args.image, tests=tests), indent=2), encoding='utf-8')
    if record is not None:
        write_record(args.record, record, summary, args.reading_result)
    return summary


if __name__ == '__main__':
    sys.exit(run_cli(main))
