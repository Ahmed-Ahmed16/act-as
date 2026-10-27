import json
import io
import os
import shlex
import stat
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

import check11_run
from check11_run import checkout_hashes, command_args
from health_parse import run_cli
from test_packet_check import good_inputs, good_packet, single_packet


TOOLS = Path(__file__).resolve().parent
PYTHON = shlex.quote(sys.executable.replace('\\', '/'))
FAKE = '''import json
import sys
from pathlib import Path

source = Path('cart.php').read_text()
name = sys.argv[1]
if name == 'probe':
    print(source)
    sys.exit(0)
if name == 'probe_exit':
    print('cart')
    sys.exit(int(source == 'FAULT'))
if name == 'probe_stderr':
    print('cart')
    print(source, file=sys.stderr)
    sys.exit(0)
if name == 'probe_long':
    print(source)
    print('cart\\n' * 50)
    sys.exit(0)
if name == 'harmless':
    print('cart')
    sys.exit(0)
with Path('runs.jsonl').open('a') as log:
    log.write(json.dumps(dict(cwd=str(Path.cwd()), source=source, name=name)) + '\\n')
if name == 'noisy':
    print('cart\\n' * 50)
print('PHPUnit 11.0')
if source == 'FAULT':
    if name in ('fatal', 'parse'):
        print('Fatal error: broken cart' if name == 'fatal' else 'Parse error: broken cart')
        sys.exit(255)
    if name == 'none':
        print('No tests executed!')
        sys.exit(0)
    if name == 'missing':
        sys.exit(127)
    if name != 'fake':
        print('1) Cart::test_total')
        print('Failed asserting that FAULT matches expected GREEN.')
        print('FAILURES!\\nTests: 1, Assertions: 1, Failures: 1.')
        sys.exit(1)
if name == 'start_red':
    print('FAILURES!\\nTests: 1, Assertions: 1, Failures: 1.')
    sys.exit(1)
if name == 'start_none':
    print('OK (1 test, 0 assertions)')
    sys.exit(0)
print('OK (1 test, 1 assertion)')
'''


class RunTests(unittest.TestCase):
    # Boundaries: 0/1/3/4 tests, bad shapes/paths, all red states, reset, records.
    def setUp(self):
        self.tree = tempfile.TemporaryDirectory(prefix='cart-check11-')
        self.addCleanup(self.tree.cleanup)
        self.root = Path(self.tree.name)
        self.repo = self.root / 'checkout'
        self.repo.mkdir()
        self.source = self.repo / 'cart.php'
        self.source.write_bytes(b'GREEN')
        (self.repo / 'fakeunit.py').write_text(FAKE, encoding='utf-8')
        self.out = self.root / 'evidence'
        self.record = self.root / 'check-record.json'
        self.spec = dict(command=f'{PYTHON} fakeunit.py {{test}}', tests=[self.pick()])
        self.real_run = subprocess.run
        self.docker_calls = []
        self.git('init', '-q')
        self.freeze()

    def git(self, *args, **kwargs):
        completed = self.real_run(['git', '-C', str(self.repo), *args],
                                  capture_output=True, **kwargs)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return completed.stdout.decode().strip()

    def freeze(self):
        self.git('add', '.')
        tree = self.git('write-tree')
        self.head = self.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                             'commit-tree', tree, input=b'Fixture\n')

    def fake_docker(self, argv, **kwargs):
        if argv[0] != 'docker':
            return self.real_run(argv, **kwargs)
        self.docker_calls.append(argv)
        if argv[1] == 'stop':
            return subprocess.CompletedProcess(argv, 0, '', '')
        command = shlex.split(argv[-1])
        # This fixture transport runs only the trusted fake, never a shell or PR code.
        if command[:2] != [sys.executable.replace('\\', '/'), 'fakeunit.py']:
            return subprocess.CompletedProcess(argv, 127, '', 'command not found')
        return self.real_run([sys.executable, '-B', 'fakeunit.py', *command[2:]], **kwargs)

    def pick(self, name='good', probe='probe'):
        return dict(name=name, fault=dict(file='cart.php', old='GREEN', new='FAULT'),
                    probe=f'{PYTHON} fakeunit.py {probe}')

    def cli(self, *extra):
        spec_path = self.root / 'spec.json'
        spec_path.write_text(json.dumps(self.spec), encoding='utf-8')
        return self.script('check11_run.py', '--repo', str(self.repo), '--spec', str(spec_path),
                           '--out', str(self.out), '--image', 'fixture:image', '--head', self.head, *extra)

    def script(self, name, *args):
        if name == 'check11_run.py':
            stdout, stderr = io.StringIO(), io.StringIO()
            with (patch.object(sys, 'argv', [name, *args]),
                  patch.object(check11_run.subprocess, 'run', side_effect=self.fake_docker),
                  redirect_stdout(stdout), redirect_stderr(stderr)):
                code = run_cli(check11_run.main)
            return subprocess.CompletedProcess(args, code, stdout.getvalue(), stderr.getvalue())
        return subprocess.run([sys.executable, '-B', str(TOOLS / name), *args],
                              capture_output=True, text=True,
                              env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})

    def checked(self, *extra):
        run = self.cli(*extra)
        self.assertEqual(run.returncode, 0, run.stderr + run.stdout)
        self.assertEqual(run.stderr, '')
        self.assertEqual(len(run.stdout.splitlines()), 1, run.stdout)
        report = json.loads((self.out / 'independent-check.json').read_text(encoding='utf-8'))
        return json.loads(run.stdout), report

    def assert_bad(self, run, message=None):
        self.assertEqual(run.returncode, 2, run.stderr + run.stdout)
        self.assertEqual(run.stdout, '')
        self.assertEqual(len(run.stderr.splitlines()), 1, run.stderr)
        if message:
            self.assertIn(message, run.stderr)

    def test_real_assertion_resets_to_green_and_checkout_stays_untouched(self):
        before = checkout_hashes(self.repo)
        summary, report = self.checked()
        self.assertEqual(summary['result'], 'clean')
        self.assertIn('covers 1 picked tests', summary['reason'])
        self.assertTrue(summary['reason'].endswith('; local evidence: independent-check.json'))
        checked = report['tests'][0]
        self.assertEqual(checked['tool_result'], 'clean')
        self.assertEqual(checked['reason'],
                         'Cart::test_total\nFailed asserting that FAULT matches expected GREEN.')
        self.assertEqual(checked['word'], 'none')
        steps = checked['steps']
        self.assertEqual([step['step'] for step in steps],
                         ['start', 'probe_before', 'fault', 'probe_after', 'fault_run',
                          'reset', 'green_again'])
        self.assertEqual([steps[i]['parsed']['state'] for i in [0, 4, 6]],
                         ['ok', 'assertion', 'ok'])
        self.assertEqual(steps[2]['old'], 'GREEN')
        self.assertEqual(steps[2]['new'], 'FAULT')
        self.assertTrue(steps[5]['byte_equal'])
        self.assertIn('GREEN', steps[1]['stdout'])
        self.assertIn('FAULT', steps[3]['stdout'])
        self.assertEqual(steps[0]['exit_code'], 0)
        self.assertEqual(steps[4]['exit_code'], 1)
        self.assertIn('Failed asserting', steps[4]['output'])
        argv = steps[0]['argv']
        self.assertEqual(argv[:2], ['docker', 'run'])
        self.assertEqual(argv[-1], self.spec['command'].replace('{test}', 'good'))
        copy = Path(steps[0]['cwd'])
        self.assertNotEqual(copy, self.repo)
        self.assertFalse(copy.exists(), 'throwaway copy must be removed')
        self.assertEqual(before, checkout_hashes(self.repo))
        self.assertEqual(report['image'], 'fixture:image')
        self.assertEqual(report['command'], self.spec['command'])

    def test_green_test_with_contradicting_probe_is_finding(self):
        self.spec['tests'] = [self.pick('fake')]
        summary, report = self.checked()
        self.assertEqual(summary['result'], 'finding')
        checked = report['tests'][0]
        self.assertEqual(checked['word'], 'must fix')
        self.assertEqual(checked['reason'], 'test stayed green with a fault that contradicts it')
        self.assertTrue(next(s for s in checked['steps'] if s['step'] == 'reset')['byte_equal'])

    def test_unchanged_probe_is_not_checked(self):
        self.spec['tests'] = [self.pick('fake', 'harmless')]
        summary, report = self.checked()
        self.assertEqual(summary['result'], 'not checked')
        self.assertEqual(report['tests'][0]['reason'], 'fault did not contradict the assertion')
        self.assertIn('fake: fault did not contradict the assertion', summary['reason'])

    def test_probe_exit_code_difference_also_proves_contradiction(self):
        self.spec['tests'] = [self.pick('fake', 'probe_exit')]
        summary, _ = self.checked()
        self.assertEqual(summary['result'], 'finding')

    def test_probe_stderr_difference_is_not_a_contradiction(self):
        self.spec['tests'] = [self.pick('fake', 'probe_stderr')]
        _, report = self.checked()
        self.assertEqual(report['tests'][0]['reason'], 'fault did not contradict the assertion')

    def test_probe_difference_before_last_40_lines_is_still_a_finding(self):
        self.spec['tests'] = [self.pick('fake', 'probe_long')]
        summary, report = self.checked()
        self.assertEqual(summary['result'], 'finding')
        steps = report['tests'][0]['steps']
        self.assertEqual(steps[1]['output'], steps[3]['output'])
        self.assertNotEqual(steps[1]['stdout'], steps[3]['stdout'])

    def test_test_output_keeps_last_40_lines(self):
        self.spec['tests'] = [self.pick('noisy')]
        summary, report = self.checked()
        self.assertEqual(summary['result'], 'clean')
        start = report['tests'][0]['steps'][0]
        self.assertEqual(len(start['output'].splitlines()), 40)
        self.assertTrue(start['output'].endswith('OK (1 test, 1 assertion)'))

    def test_missing_runner_is_not_checked(self):
        self.spec['command'] = 'cart_runner_that_does_not_exist {test}'
        _, report = self.checked()
        self.assertEqual(report['tests'][0]['tool_result'], 'not checked')
        self.assertEqual(report['tests'][0]['reason'], 'tests cannot run here')

    def test_start_must_prove_a_green_test_ran(self):
        for name, reason in [('start_red', 'test was not green at start'),
                             ('start_none', 'test did not run')]:
            with self.subTest(name=name):
                self.spec['tests'] = [self.pick(name)]
                _, report = self.checked()
                self.assertEqual(report['tests'][0]['reason'], reason)
                self.assertEqual(len(report['tests'][0]['steps']), 1)

    def test_non_assertion_red_is_not_checked_and_still_resets(self):
        for name, reason in [('fatal', 'red was not an assertion failure'),
                             ('parse', 'red was not an assertion failure'),
                             ('none', 'test did not run after the fault'),
                             ('missing', 'test did not run after the fault')]:
            with self.subTest(name=name):
                self.spec['tests'] = [self.pick(name)]
                summary, report = self.checked()
                self.assertEqual(summary['result'], 'not checked')
                self.assertEqual(report['tests'][0]['reason'], reason)
                self.assertTrue(report['tests'][0]['steps'][-2]['byte_equal'])
                self.assertEqual(report['tests'][0]['steps'][-1]['parsed']['state'], 'ok')

    def test_reset_must_return_to_green(self):
        transport = self.fake_docker

        def fail_green_again(argv, **kwargs):
            if (argv[:2] == ['docker', 'run'] and
                    argv[argv.index('--name') + 1].endswith('-5')):
                return subprocess.CompletedProcess(argv, 2,
                    'ERRORS!\nTests: 1, Assertions: 0, Errors: 1.', '')
            return transport(argv, **kwargs)

        with patch.object(self, 'fake_docker', side_effect=fail_green_again):
            _, report = self.checked()
        self.assertEqual(report['tests'][0]['tool_result'], 'not checked')
        self.assertEqual(report['tests'][0]['reason'], 'copy did not return to green after reset')

    def test_review_N7_reset_preserves_fault_file_timestamp(self):
        transport = self.fake_docker
        timestamps = []

        def inspect_timestamp(argv, **kwargs):
            if argv[:2] == ['docker', 'run']:
                timestamps.append((Path(kwargs['cwd']) / 'cart.php').stat().st_mtime_ns)
            return transport(argv, **kwargs)

        with patch.object(self, 'fake_docker', side_effect=inspect_timestamp):
            summary, _ = self.checked()
        self.assertEqual(summary['result'], 'clean')
        self.assertEqual(timestamps[-1], timestamps[0])

    @unittest.skipIf(os.name == 'nt', 'Windows does not preserve POSIX executable mode bits')
    def test_review_N7_reset_preserves_executable_fault_file_mode(self):
        self.source.chmod(0o755)
        self.freeze()
        transport = self.fake_docker
        modes = []

        def inspect_mode(argv, **kwargs):
            if argv[:2] == ['docker', 'run']:
                modes.append(stat.S_IMODE((Path(kwargs['cwd']) / 'cart.php').stat().st_mode))
            return transport(argv, **kwargs)

        with patch.object(self, 'fake_docker', side_effect=inspect_mode):
            summary, _ = self.checked()
        self.assertEqual(summary['result'], 'clean')
        self.assertEqual(modes[0], 0o755)
        self.assertEqual(modes[-1], 0o755)

    def test_fault_must_match_exactly_once(self):
        for old in ['absent', 'E']:
            with self.subTest(old=old):
                self.spec['tests'][0]['fault']['old'] = old
                _, report = self.checked()
                self.assertEqual(report['tests'][0]['reason'], 'fault could not be applied')
                self.assertEqual(self.source.read_bytes(), b'GREEN')

    def test_test_count_limits_and_aggregation(self):
        self.spec['tests'] *= 4
        self.assert_bad(self.cli(), 'at most 3')
        self.spec['tests'] = []
        summary, report = self.checked()
        self.assertEqual(summary['result'], 'does not apply')
        self.assertIn('no test in a risky area', summary['reason'])
        self.assertEqual(report['tests'], [])
        self.spec['tests'] = [self.pick(), self.pick('fake', 'harmless'), self.pick('fake')]
        summary, report = self.checked()
        self.assertEqual(summary['result'], 'finding')
        self.assertIn('covers 3 picked tests', summary['reason'])
        self.assertEqual([t['tool_result'] for t in report['tests']],
                         ['clean', 'not checked', 'finding'])

    def test_checkout_change_is_reported_as_exit_2(self):
        transport = self.fake_docker

        def write_checkout(argv, **kwargs):
            if argv[:2] == ['docker', 'run']:
                self.source.write_text('CHANGED')
            return transport(argv, **kwargs)

        with patch.object(self, 'fake_docker', side_effect=write_checkout):
            self.assert_bad(self.cli(), 'checkout changed')
        self.assertEqual(self.source.read_text(), 'CHANGED')

    def test_hash_guard_ignores_git_file_and_generated_folders(self):
        before = checkout_hashes(self.repo)
        git_file_tree = self.root / 'worktree'
        git_file_tree.mkdir()
        (git_file_tree / '.git').write_text('gitdir: cart-worktree')
        self.assertEqual(checkout_hashes(git_file_tree), {})
        for name in ['vendor', 'node_modules', 'storage']:
            (self.repo / name).mkdir()
            (self.repo / name / 'generated').write_text('cart cache')
        self.assertEqual(checkout_hashes(self.repo), before)
        self.source.write_bytes(b'CHANGED')
        self.assertNotEqual(checkout_hashes(self.repo), before)

    def test_test_name_is_shell_quoted(self):
        self.spec['tests'] = [self.pick('good; exit 127')]
        summary, _ = self.checked()
        self.assertEqual(summary['result'], 'clean')

    def test_bad_spec_shapes_paths_and_record_options_are_single_line_errors(self):
        valid = json.loads(json.dumps(self.spec))
        cases = [None, [], {}, dict(command=3, tests=[]), dict(command='echo ok', tests=[]),
                 dict(command=valid['command'], tests=None),
                 dict(command=valid['command'], tests=[None])]
        for field, bad in [('name', ''), ('probe', None), ('probe', ''), ('fault', []),
                           ('fault', dict(file='../cart.php', old='GREEN', new='FAULT')),
                           ('fault', dict(file=str(self.source), old='GREEN', new='FAULT')),
                           ('fault', dict(file='cart.php', old='', new='FAULT')),
                           ('fault', dict(file='cart.php', old='GREEN', new=3))]:
            picked = self.pick()
            picked[field] = bad
            cases.append(dict(command=valid['command'], tests=[picked]))
        for spec in cases:
            with self.subTest(spec=spec):
                self.spec = spec
                self.assert_bad(self.cli())
        self.spec = valid
        self.assert_bad(self.cli('--record', str(self.record)), 'reading-result')
        self.assert_bad(self.cli('--record', str(self.record), '--reading-result', 'pass'))
        self.record.write_text('{"entries": [null]}', encoding='utf-8')
        self.assert_bad(self.cli('--record', str(self.record), '--reading-result', 'clean'))
        self.assert_bad(self.cli('--out', str(self.repo / 'evidence')))

    def test_record_create_replace_preserve_and_health_verdict(self):
        self.spec['tests'] = [self.pick('fake')]
        self.checked('--record', str(self.record), '--reading-result', 'clean')
        saved = json.loads(self.record.read_text())
        real = saved['entries'][0]
        self.assertEqual(real, dict(id='H11', mode='health', area='', kind='check',
                                   tool_result='finding', reading_result='clean', word='must fix',
                                   reason=real['reason'], base_read='', head_read=''))
        verdict = self.script('health_verdict.py', '--record', str(self.record))
        self.assertEqual(verdict.returncode, 0, verdict.stderr)
        self.assertEqual(json.loads(verdict.stdout)['verdict'], 'fail')
        other = dict(id='S1', mode='security', note=['keep', 7])
        baseline = [dict(real, id=f'H{n}', tool_result='clean', word='none') for n in range(1, 11)]
        saved.update(required_ids=['H11'], extra=dict(keep=True), entries=[other, *baseline, real])
        self.record.write_text(json.dumps(saved))
        self.spec['tests'] = [self.pick('fake', 'harmless')]
        self.checked('--record', str(self.record), '--reading-result', 'not checked')
        updated = json.loads(self.record.read_text())
        self.assertEqual(updated['entries'][0], other)
        self.assertEqual(updated['extra'], saved['extra'])
        self.assertEqual(updated['required_ids'], ['H11'])
        self.assertEqual(len(updated['entries']), 12)
        self.assertEqual(updated['entries'][1:-1], baseline)
        self.assertEqual(updated['entries'][-1]['tool_result'], 'not checked')
        verdict = self.script('health_verdict.py', '--record', str(self.record))
        self.assertEqual(verdict.returncode, 0, verdict.stderr)
        self.assertEqual(json.loads(verdict.stdout)['verdict'], 'incomplete')
        self.assertEqual(json.loads(verdict.stdout)['missing'], [])

    def test_health_packet_accepts_real_h11_record(self):
        self.checked('--record', str(self.record), '--reading-result', 'clean')
        real = json.loads(self.record.read_text())['entries'][0]
        packet = self.root / 'packet'
        packet.mkdir()
        inputs = good_inputs()
        entries = [dict(real, id=f'H{n}') for n in range(1, 11)] + [real]
        inputs['check-record.json'] = dict(required_ids=[f'H{n}' for n in range(1, 12)],
                                           entries=entries)
        inputs['rules-pages.json']['areas'] = []
        for name, document in inputs.items():
            (packet / name).write_text(json.dumps(document), encoding='utf-8')
        health_line = next(line for line in good_packet().splitlines() if line.startswith('health:'))
        text = single_packet('health').replace(health_line, 'health: pass')
        (packet / 'packet.md').write_text(text, encoding='utf-8')
        run = self.script('packet_check.py', str(packet))
        self.assertEqual(run.returncode, 0, run.stderr + run.stdout)
        self.assertEqual(run.stdout.strip(), 'packet_check: pass')

    def test_docker_arguments_keep_windows_path_and_disable_network(self):
        copy = r'D:\Carts\checkout copy'
        argv = command_args('php fakeunit.php cart', copy, 'cart:php')
        self.assertEqual(argv[:5], ['docker', 'run', '--rm', '--network', 'none'])
        self.assertTrue(argv[argv.index('--name') + 1].startswith('actas-t36-'))
        self.assertEqual(argv[argv.index('-v') + 1], copy + ':/work')
        self.assertEqual(argv[argv.index('-w') + 1], '/work')
        self.assertEqual(argv[-4:], ['cart:php', 'sh', '-c', 'php fakeunit.php cart'])

    def test_review_G25_missing_image_is_a_single_line_refusal(self):
        self.spec['tests'] = []
        spec = self.root / 'spec.json'
        spec.write_text(json.dumps(self.spec))
        run = self.script('check11_run.py', '--repo', str(self.repo), '--spec', str(spec),
                          '--out', str(self.out))
        self.assert_bad(run, '--image')
        self.assertEqual(self.docker_calls, [])
        with self.assertRaisesRegex(ValueError, '--image'):
            command_args('unused', self.repo, None)

    def test_review_G26_external_tracked_link_is_not_checked(self):
        outside = self.root / 'private.txt'
        outside.write_text('PRIVATE FIXTURE')
        blob = self.git('hash-object', '-w', '--stdin', input=str(outside).encode())
        self.git('update-index', '--add', '--cacheinfo', f'120000,{blob},private-link')
        tree = self.git('write-tree')
        head = self.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                        'commit-tree', tree, input=b'Link fixture\n')
        summary, report = self.checked('--head', head)
        self.assertEqual(summary['result'], 'not checked')
        self.assertIn('symlink leaves the tree', report['tests'][0]['reason'])
        self.assertEqual(self.docker_calls, [])
        self.assertNotIn('PRIVATE FIXTURE', json.dumps(report))
        self.spec['tests'] = []
        summary, report = self.checked('--head', head)
        self.assertEqual(summary['result'], 'not checked')
        self.assertEqual(report['tests'], [])

    def test_review_G27_swapped_target_cannot_overwrite_outside_file(self):
        outside = self.root / 'outside.txt'
        outside.write_bytes(b'KEEP')
        transport = self.fake_docker

        def swap_target(argv, **kwargs):
            completed = transport(argv, **kwargs)
            if argv[:2] == ['docker', 'run'] and argv[argv.index('--name') + 1].endswith('-4'):
                target = Path(kwargs['cwd']) / 'cart.php'
                target.unlink()
                # Hard links exercise unlink safety without Windows symlink privileges.
                os.link(outside, target)
            return completed

        with patch.object(self, 'fake_docker', side_effect=swap_target):
            summary, _ = self.checked()
        self.assertEqual(outside.read_bytes(), b'KEEP')
        self.assertEqual(summary['result'], 'clean')

    def test_review_G28_frozen_commit_ignores_dirty_and_export_ignored_files(self):
        (self.repo / '.gitattributes').write_text('cart.php export-ignore\n')
        self.freeze()
        self.source.write_bytes(b'DIRTY')
        (self.repo / 'untracked.txt').write_text('UNTRACKED')
        transport = self.fake_docker
        copied_untracked = []

        def inspect_copy(argv, **kwargs):
            if argv[:2] == ['docker', 'run']:
                copied_untracked.append((Path(kwargs['cwd']) / 'untracked.txt').exists())
            return transport(argv, **kwargs)

        with patch.object(self, 'fake_docker', side_effect=inspect_copy):
            summary, report = self.checked('--head', self.head)
        self.assertEqual(summary['result'], 'clean')
        self.assertEqual(report['head'], self.head)
        steps = report['tests'][0]['steps']
        self.assertEqual(steps[1]['stdout'].strip(), 'GREEN')
        self.assertEqual(steps[-1]['parsed']['state'], 'ok')
        self.assertEqual(self.source.read_bytes(), b'DIRTY')
        self.assertEqual(copied_untracked, [False] * 5)

    def test_review_G29_rebuild_removes_caches_before_green_and_next_pick(self):
        self.spec['tests'] = [self.pick(), self.pick()]
        (self.repo / 'config.txt').write_text('FROZEN')
        self.freeze()
        transport = self.fake_docker

        def cache_fault(argv, **kwargs):
            if argv[:2] != ['docker', 'run']:
                return transport(argv, **kwargs)
            copy = Path(kwargs['cwd'])
            number = int(argv[argv.index('--name') + 1].rsplit('-', 1)[1])
            cache = copy / 'fault-cache'
            if number in (5, 6, 10) and (cache.exists() or (copy / 'config.txt').read_text() != 'FROZEN'):
                return subprocess.CompletedProcess(argv, 2, 'Fatal error: stale cache', '')
            completed = transport(argv, **kwargs)
            if number in (4, 9):
                cache.write_text('FAULT')
                (copy / 'config.txt').write_text('FAULT')
            if number == 5:
                cache.write_text('baseline cache')
            return completed

        with patch.object(self, 'fake_docker', side_effect=cache_fault):
            summary, report = self.checked()
        self.assertEqual(summary['result'], 'clean')
        self.assertEqual([test['steps'][0]['parsed']['state'] for test in report['tests']],
                         ['ok', 'ok'])
        self.assertEqual([test['steps'][-1]['parsed']['state'] for test in report['tests']],
                         ['ok', 'ok'])

    def test_review_G30_sleeping_runner_is_stopped_and_step_is_recorded(self):
        sleeper = self.root / 'sleeper.py'
        sleeper.write_text("import time\ntime.sleep(0.2)\nprint('OK (1 test, 1 assertion)')\n")
        stopped = []

        def sleepy_docker(argv, **kwargs):
            if argv[:2] == ['docker', 'stop']:
                stopped.append(argv[-1])
                return subprocess.CompletedProcess(argv, 0, '', '')
            if argv[:2] == ['docker', 'run']:
                return self.real_run([sys.executable, '-B', str(sleeper)], **kwargs)
            return self.real_run(argv, **kwargs)

        runner = check11_run.Runner(self.repo, 'fixture:image')
        runner.timeout = 0.03
        with patch.object(check11_run.subprocess, 'run', side_effect=sleepy_docker):
            with self.assertRaisesRegex(ValueError, 'probe_before timed out'):
                runner.run('probe_before', 'sleep fixture')
        self.assertEqual(stopped, [runner.steps[0]['argv'][runner.steps[0]['argv'].index('--name') + 1]])
        self.assertTrue(stopped[0].startswith('actas-t36-'))
        self.assertTrue(runner.steps[0]['timed_out'])

    def test_review_G30_each_timed_out_step_makes_the_pick_not_checked(self):
        sleeper = self.root / 'sleeper.py'
        sleeper.write_text('import time\ntime.sleep(0.2)\n')
        transport = self.fake_docker
        # Boundaries: green, both probes, fault run, final green; invalid limits below.
        for number, step in enumerate(['start', 'probe_before', 'probe_after',
                                       'fault_run', 'green_again'], 1):
            stopped = []

            def timed_docker(argv, **kwargs):
                if argv[:2] == ['docker', 'stop']:
                    stopped.append(argv[-1])
                    return subprocess.CompletedProcess(argv, 0, '', '')
                if argv[:2] == ['docker', 'run']:
                    if argv[argv.index('--name') + 1].endswith(f'-{number}'):
                        return self.real_run([sys.executable, '-B', str(sleeper)], **kwargs)
                    kwargs.pop('timeout', None)
                return transport(argv, **kwargs)

            with self.subTest(step=step), patch.object(self, 'fake_docker', side_effect=timed_docker):
                summary, report = self.checked('--timeout', '0.03')
                self.assertEqual(summary['result'], 'not checked')
                picked = report['tests'][0]
                self.assertEqual(picked['reason'], f'{step} timed out')
                failed = next(s for s in picked['steps'] if s.get('timed_out'))
                self.assertEqual(stopped, [failed['argv'][failed['argv'].index('--name') + 1]])
                self.assertTrue(stopped[0].startswith('actas-t36-'))
                self.assertFalse(Path(failed['cwd']).exists())

    def test_review_N8_missing_docker_saves_failed_call_and_h11_record(self):
        transport = self.fake_docker
        # Launch failures can happen at the start, either probe, fault run, or reset run.
        for number, step in enumerate(['start', 'probe_before', 'probe_after',
                                       'fault_run', 'green_again'], 1):
            failed_calls = []

            def missing_docker(argv, **kwargs):
                if (argv[:2] == ['docker', 'run'] and
                        argv[argv.index('--name') + 1].endswith(f'-{number}')):
                    failed_calls.append(argv)
                    raise FileNotFoundError('docker fixture missing')
                return transport(argv, **kwargs)

            with self.subTest(step=step), patch.object(self, 'fake_docker', side_effect=missing_docker):
                summary, report = self.checked('--record', str(self.record), '--reading-result', 'clean')
                self.assertEqual(summary['result'], 'not checked')
                picked = report['tests'][0]
                self.assertEqual(picked['tool_result'], 'not checked')
                failed = next(s for s in picked['steps'] if s['step'] == step)
                self.assertEqual(failed['argv'], failed_calls[0])
                self.assertEqual(failed['error'], 'docker fixture missing')
                self.assertEqual(picked['reason'], 'tool did not run, ' + shlex.join(failed_calls[0]))
                saved = json.loads(self.record.read_text(encoding='utf-8'))['entries'][0]
                self.assertEqual(saved['id'], 'H11')
                self.assertEqual(saved['tool_result'], 'not checked')
                self.assertEqual(saved['reason'], summary['reason'])

    def test_required_head_and_invalid_image_or_timeout_refuse_before_running(self):
        for args, message in [(('--head', 'missing-commit'), 'git failed'),
                              (('--image', ''), '--image'),
                              *[(('--timeout', limit), '--timeout')
                                for limit in ['0', '-1', 'nan', 'inf']]]:
            with self.subTest(args=args):
                self.assert_bad(self.cli(*args), message)
                self.assertEqual(self.docker_calls, [])


if __name__ == '__main__':
    unittest.main()
