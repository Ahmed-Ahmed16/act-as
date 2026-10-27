import json
import os
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from check11_run import checkout_hashes, command_args
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
if name == 'reset_red' and Path('runs.jsonl').read_text().count('reset_red') == 3:
    print('ERRORS!\\nTests: 1, Assertions: 0, Errors: 1.')
    sys.exit(2)
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

    def pick(self, name='good', probe='probe'):
        return dict(name=name, fault=dict(file='cart.php', old='GREEN', new='FAULT'),
                    probe=f'{PYTHON} fakeunit.py {probe}')

    def cli(self, *extra):
        spec_path = self.root / 'spec.json'
        spec_path.write_text(json.dumps(self.spec), encoding='utf-8')
        return self.script('check11_run.py', '--repo', str(self.repo), '--spec', str(spec_path),
                           '--out', str(self.out), *extra)

    def script(self, name, *args):
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
        before = {p.name: p.read_bytes() for p in self.repo.iterdir()}
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
        self.assertEqual(argv[:2], ['sh', '-c'])
        self.assertEqual(argv[2], self.spec['command'].replace('{test}', 'good'))
        copy = Path(steps[0]['cwd'])
        self.assertNotEqual(copy, self.repo)
        self.assertFalse(copy.exists(), 'throwaway copy must be removed')
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.repo.iterdir()})
        self.assertEqual(report['image'], None)
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
        self.spec['tests'] = [self.pick('reset_red')]
        _, report = self.checked()
        self.assertEqual(report['tests'][0]['tool_result'], 'not checked')
        self.assertEqual(report['tests'][0]['reason'], 'copy did not return to green after reset')

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
        script = self.repo / 'write_checkout.py'
        script.write_text('from pathlib import Path\n'
                          f'Path({str(self.source)!r}).write_text("CHANGED")\n', encoding='utf-8')
        self.spec['command'] = f'{PYTHON} write_checkout.py; {self.spec["command"]}'
        self.assert_bad(self.cli(), 'checkout changed')
        self.assertEqual(self.source.read_text(), 'CHANGED')

    def test_hash_guard_ignores_git_file_and_generated_folders(self):
        before = checkout_hashes(self.repo)
        (self.repo / '.git').write_text('gitdir: cart-worktree')
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
        baseline = [dict(real, id=name, tool_result='clean', word='none')
                    for name in [f'H{n}' for n in range(1, 11)] + [f'T{n}' for n in range(1, 9)]]
        saved.update(required_ids=['H11'], extra=dict(keep=True), entries=[other, *baseline, real])
        self.record.write_text(json.dumps(saved))
        self.spec['tests'] = [self.pick('fake', 'harmless')]
        self.checked('--record', str(self.record), '--reading-result', 'not checked')
        updated = json.loads(self.record.read_text())
        self.assertEqual(updated['entries'][0], other)
        self.assertEqual(updated['extra'], saved['extra'])
        self.assertEqual(updated['required_ids'], ['H11'])
        self.assertEqual(len(updated['entries']), 20)
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


if __name__ == '__main__':
    unittest.main()
