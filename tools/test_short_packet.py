import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

if __package__:
    from .test_packet_check import replace_body
else:
    from test_packet_check import replace_body


ROOT = Path(__file__).resolve().parents[1]
STOP = 'not checked: PR over the cap, split it first'


class ShortPacketBase(unittest.TestCase):
    # Cases: 301, larger, stale bytes/commits, absent/invalid input,
    # existing outputs, rename, binary, and a dropped or reordered group.
    def setUp(self):
        scratch = ROOT / '.scratch'
        scratch.mkdir(exist_ok=True)
        tree = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(tree.cleanup)
        self.root = Path(tree.name)
        self.repo = self.root / 'garden'
        self.repo.mkdir()
        self.packet = self.root / 'packet'
        self.env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM='1',
                        PYTHONDONTWRITEBYTECODE='1', TEMP=str(scratch), TMP=str(scratch))
        self.git('init', '-b', 'main')
        self.git('config', 'user.name', 'Garden')
        self.git('config', 'user.email', 'garden@example.invalid')
        self.write('old.py', 'old seed\n')
        self.base = self.commit()

    def git(self, *args):
        run = subprocess.run(['git', '-c', 'core.autocrlf=false', '-c', 'commit.gpgsign=false',
                              '-C', str(self.repo), *args], capture_output=True, env=self.env)
        self.assertEqual(run.returncode, 0, run.stderr)
        return run.stdout.decode().strip()

    def write(self, path, text):
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(text.encode() if isinstance(text, str) else text)

    def commit(self):
        self.git('add', '-A')
        self.git('commit', '-m', 'Plant seeds')
        return self.git('rev-parse', 'HEAD')

    def run_tool(self, name, *args):
        return subprocess.run([sys.executable, str(ROOT / 'tools' / name), *map(str, args)],
                              capture_output=True, text=True, encoding='utf-8', env=self.env)

    def passed(self, run):
        self.assertEqual((run.returncode, run.stderr), (0, ''), run.stdout + run.stderr)
        return run

    def save(self, name, document):
        (self.packet / name).write_bytes((json.dumps(document) + '\n').encode())

    def read(self, name):
        return json.loads((self.packet / name).read_bytes())

    def prepare(self, total=321, operations=False):
        self.write('app/Seed.py', ''.join(f'seed_{n} = {n}\n' for n in range(total)))
        self.write('tests/Seed.py', 'check seed\n')
        self.write('package-lock.json', '{}\n')
        if operations:
            self.git('mv', 'old.py', 'renamed.py')
            self.write('seed.bin', b'\0seed')
        self.head = self.commit()
        count = self.passed(self.run_tool('size_counter.py', '--repo', self.repo, '--base', self.base,
                                          '--head', self.head, '--out', self.packet))
        (self.packet / 'runs').mkdir()
        self.save('runs/size-count.json', json.loads(count.stdout))
        self.passed(self.run_tool('split_plan.py', 'hunks', '--repo', self.repo, '--base', self.base,
                                  '--head', self.head, '--packet', self.packet))
        hunks = self.read('hunks.json')
        source = next(h['id'] for h in hunks['hunks'] if h['path'] == 'app/Seed.py')
        test = next(h['id'] for h in hunks['hunks'] if h['kind'] == 'test')
        lock = next(h['id'] for h in hunks['hunks'] if h['kind'] == 'lock')
        group1 = dict(name='plant', summary='Plant seeds.', entry_points=['route plant'], needs=[],
                      hunks=[source + ':L1-L160', test], links=[dict(piece=test, **{'for': [dict(piece=source + ':L1-L80')]})])
        group2 = dict(name='water', summary='Water seeds.', entry_points=['command water'], needs=['plant'],
                      hunks=[f'{source}:L161-L{total}'])
        parts = [dict(name='seed', summary='Show seeds.', needs=[], hunks=[source + ':L1-L80', test]),
                 dict(name='soil', summary='Add soil.', needs=['seed'], hunks=[source + ':L81-L160'])]
        for op in hunks['ops']:
            group1['hunks'].append(op['id'])
            parts[0]['hunks'].append(op['id'])
        plan = dict(groups=[group1, group2], parts=parts, unplaced=[lock], marks=[], loop_notes=[],
                    main=dict(state='established', evidence='Read main.'), ci=dict(state='read', workflows=[]))
        self.save('split-input.json', plan)
        self.passed(self.run_tool('split_plan.py', 'build', self.packet))

    def writer(self, *extra):
        return self.run_tool('short_packet.py', self.packet, '--repo-name', 'example/garden', '--pr', '17',
                             '--default', 'main@' + self.base, '--date', '2026-10-28', *extra)

    def packet_text(self):
        return (self.packet / 'packet.md').read_text(encoding='utf-8')

    def check(self, text=None):
        if text is not None:
            (self.packet / 'packet.md').write_bytes(text.encode())
        return self.run_tool('packet_check.py', self.packet)

    def assert_bad_writer(self):
        before = {p.relative_to(self.packet): p.read_bytes() for p in self.packet.rglob('*') if p.is_file()}
        run = self.writer()
        self.assertEqual((run.returncode, run.stdout), (2, ''), run.stdout + run.stderr)
        self.assertEqual(len(run.stderr.splitlines()), 1, run.stderr)
        after = {p.relative_to(self.packet): p.read_bytes() for p in self.packet.rglob('*') if p.is_file()}
        self.assertEqual(before, after)
        return run


class ShortPacketTests(ShortPacketBase):
    def test_B1_count_build_write_and_check_including_301(self):
        for total in [321, 301]:
            with self.subTest(total=total):
                self.packet = self.root / f'packet{total}'
                self.prepare(total)
                self.passed(self.writer())
                self.assertEqual(self.passed(self.check()).stdout, 'packet_check: pass\n')
                saved = self.read('runs/size-count.json')
                self.assertEqual(saved['counted_total'], total)
                self.assertEqual(saved['left_out']['tests']['files'], 1)
                self.assertEqual(saved['left_out']['lock files']['files'], 1)
                self.assertIn('size: ' + saved['size_line'], self.packet_text())
                self.assertIn('Translations by page: ' + STOP, self.packet_text())

    def test_B2_dropped_piece_is_rejected(self):
        self.prepare()
        self.passed(self.writer())
        plan = self.read('split-plan.json')
        plan['groups'][1]['hunks'].clear()
        self.save('split-plan.json', plan)
        run = self.check()
        self.assertEqual((run.returncode, run.stderr), (1, ''))
        self.assertIn('RULE hunk-unplaced:', run.stdout)

    def test_B3_B4_message_counts_and_group_order_are_checked(self):
        self.prepare()
        self.passed(self.writer())
        original = self.packet_text()
        for heading, rule in [('Drafts, not sent', 'split-message'), ('Split plan', 'split-field')]:
            for replacement in ['group: plant, 159 counted lines\ngroup: water, 161 counted lines',
                                'group: water, 161 counted lines\ngroup: plant, 160 counted lines']:
                with self.subTest(heading=heading, replacement=replacement):
                    run = self.check(replace_body(original, heading, replacement))
                    self.assertEqual((run.returncode, run.stderr), (1, ''))
                    self.assertIn('RULE ' + rule + ':', run.stdout)

    def test_B19_edited_input_refuses_without_writes(self):
        self.prepare()
        path = self.packet / 'split-input.json'
        path.write_bytes(path.read_bytes() + b' ')
        self.assertIn('plan is stale, run build again', self.assert_bad_writer().stderr)

    def test_B20_pass_missing_plan_and_existing_packet_refuse(self):
        self.prepare()
        saved = self.read('runs/size-count.json')
        self.save('runs/size-count.json', dict(saved, verdict='pass'))
        self.assert_bad_writer()
        self.save('runs/size-count.json', saved)
        path = self.packet / 'split-plan.json'
        raw = path.read_bytes()
        path.unlink()
        self.assert_bad_writer()
        path.write_bytes(raw)
        (self.packet / 'packet.md').write_bytes(b'Keep this packet.\n')
        self.assert_bad_writer()

    def test_B22_check_record_contains_24_explicit_unchecked_entries(self):
        self.prepare()
        self.passed(self.writer())
        record = self.read('check-record.json')
        self.assertEqual(record['required_ids'], [])
        self.assertEqual([e['id'] for e in record['entries']], [*(f'S{n}' for n in range(1, 23)), 'L1', 'L5'])
        for entry in record['entries']:
            self.assertEqual(entry, dict(id=entry['id'], mode='security', kind='check', area='',
                                         tool_result='not checked', reading_result='not checked', word='none',
                                         reason=STOP, base_read='', head_read=''))
        self.assertEqual(self.read('rules-pages.json'), dict(areas=[]))

    def test_B23_role_keeps_scaffold_and_lists_split_steps(self):
        text = (ROOT / 'roles/reviewer/modes/full.md').read_text(encoding='utf-8')
        self.assertIn('1. **Scaffold.** Filled by ticket 39. Until then this mode does nothing but\n   open.', text)
        self.assertIn('2. **Split step.**', text)
        for letter in 'abcdefghij':
            self.assertIn('   ' + letter + '. ', text)
        for token in ['cards.py reviewer full 2', 'hunks', 'build', 'short_packet.py', 'packet_check.py',
                      'Translations by page: ' + STOP]:
            self.assertIn(token, text)
        self.assertNotIn('safe to merge', text)

    def test_B25_rename_and_binary_operations_pass_the_checker(self):
        self.prepare(operations=True)
        self.passed(self.writer())
        self.assertIn('file operation: renamed old.py to renamed.py, 0 counted lines', self.packet_text())
        self.assertIn('file operation: added seed.bin, 0 counted lines', self.packet_text())
        self.passed(self.check())

    def test_changed_hashes_commits_and_bad_arguments_refuse(self):
        self.prepare()
        for name in ['files.json', 'hunks.json']:
            with self.subTest(name=name):
                path = self.packet / name
                original = path.read_bytes()
                path.write_bytes(original + b' ')
                self.assert_bad_writer()
                path.write_bytes(original)
        for field in ['base', 'head']:
            saved = self.read('runs/size-count.json')
            self.save('runs/size-count.json', dict(saved, **{field: 'f' * 40}))
            self.assert_bad_writer()
            self.save('runs/size-count.json', saved)
        for extra in [('--pr', '-1'), ('--date', '2026-02-30'), ('--default', 'main@abc'),
                      ('--repo-name', 'garden'), ('--unknown', 'bad')]:
            with self.subTest(extra=extra):
                run = self.writer(*extra)
                self.assertEqual((run.returncode, run.stdout), (2, ''), run.stdout + run.stderr)
                self.assertEqual(len(run.stderr.splitlines()), 1, run.stderr)

    def test_null_workflow_text_refuses_without_a_traceback(self):
        self.prepare()
        plan = self.read('split-plan.json')
        self.save('split-plan.json', dict(plan, ci=dict(state='read', workflows=[dict(path='ci.yml', on_text=None)])))
        self.assert_bad_writer()

    def test_bad_rendered_shape_and_inconsistent_counts_leave_no_outputs(self):
        self.prepare()
        plan = self.read('split-plan.json')
        counter = self.read('runs/size-count.json')
        for variant in ['heading', 'group count', 'size line', 'counter total']:
            with self.subTest(variant=variant):
                changed_plan = json.loads(json.dumps(plan))
                changed_counter = dict(counter)
                if variant == 'heading':
                    changed_plan['groups'][0]['summary'] = 'Plant seeds.\n## Known risks\nnone'
                elif variant == 'group count':
                    changed_plan['groups'][0]['counted'] = 159
                elif variant == 'size line':
                    changed_counter['size_line'] = counter['size_line'].replace('321 counted', '322 counted')
                else:
                    changed_counter['counted_total'] = 322
                self.save('split-plan.json', changed_plan)
                self.save('runs/size-count.json', changed_counter)
                try:
                    self.assert_bad_writer()
                finally:
                    for name in ['packet.md', 'check-record.json', 'rules-pages.json']:
                        (self.packet / name).unlink(missing_ok=True)


if __name__ == '__main__':
    unittest.main()
