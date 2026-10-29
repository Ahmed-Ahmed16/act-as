import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CardGateTests(unittest.TestCase):
    def setUp(self):
        self.tree = tempfile.TemporaryDirectory(prefix='actas-cards-')
        self.addCleanup(self.tree.cleanup)
        self.root = Path(self.tree.name)
        (self.root / 'tools').mkdir()
        shutil.copyfile(Path(__file__).with_name('cards.py'), self.root / 'tools/cards.py')
        self.role = self.root / 'roles/tester'
        (self.role / 'modes').mkdir(parents=True)
        (self.role / 'cards').mkdir()
        (self.role / 'ROLE.md').write_text(
            '# Tester\n## 3. Rules\n- `TST-P01` First\n- `TST-P02` Second\n- `TST-888` Other rule\n'
            'Cards for every mode:\n- `TST-501`, `TST-505`\n## 4. Skills\n- `TST-999`\n', encoding='utf-8')
        (self.role / 'modes/code.md').write_text(
            '# Code\n## Steps\n1. Empty.\n2. Checks `TST-001`, `TST-002`, `TST-003`, `TST-004`.\n'
            '3. Doubles `TST-105` to `TST-108`, again `TST-106`.\n'
            '4. AI: TST-018` to `TST-024`.\n5. Release.\n'
            '   - Nested `TST-401`.\n   - Nested `TST-402`.\n'
            '## Finish checklist\n- `TST-999`\n', encoding='utf-8')

    def card(self, card_id, status='approved', mode='all'):
        (self.role / f'cards/{card_id}.md').write_text(
            f'id: {card_id}\nrule: Café checks.\nstatus: {status}\nmode: {mode}\ntrigger: before a check\n', encoding='utf-8')

    def run_gate(self, *args):
        return subprocess.run([sys.executable, '-E', '-P', '-X', 'utf8', '-B',
                               str(self.root / 'tools/cards.py'), *args],
                              capture_output=True, text=True, encoding='utf-8', timeout=10)

    def test_approved_match_prints_full_body_and_trigger(self):
        self.card('TST-001', mode='site, code explore')
        run = self.run_gate('tester', 'code', '2')
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout.splitlines()[0], 'cards.py tester code 2: 1 printed, 3 skipped')
        self.assertIn('== TST-001 | trigger: before a check\n', run.stdout)
        self.assertIn((self.role / 'cards/TST-001.md').read_text(encoding='utf-8'), run.stdout)

    def test_ineligible_cards_skip_with_distinct_reasons(self):
        self.card('TST-001')
        self.card('TST-002', status='draft')
        self.card('TST-003', mode='site, explore')
        run = self.run_gate('tester', 'code', '2')
        self.assertEqual(run.returncode, 0, run.stderr)
        for card_id, reason in [('TST-002', 'status draft'), ('TST-003', 'mode site, explore'), ('TST-004', 'missing')]:
            with self.subTest(reason=reason):
                self.assertIn(f'SKIPPED {card_id}: {reason}\n', run.stdout)
                self.assertNotIn(f'id: {card_id}\n', run.stdout)

    def test_both_range_shapes_include_middle_ids_in_order_once(self):
        for step, start, end in [('3', 105, 108), ('4', 18, 24)]:
            with self.subTest(step=step):
                ids = [f'TST-{number:03d}' for number in range(start, end + 1)]
                for card_id in ids:
                    self.card(card_id)
                run = self.run_gate('tester', 'code', step)
                self.assertEqual(run.returncode, 0, run.stderr)
                self.assertEqual([line.split(' | ')[0][3:] for line in run.stdout.splitlines() if line.startswith('== ')], ids)

    def test_nested_last_step_stops_at_finish_heading(self):
        for card_id in ['TST-401', 'TST-402', 'TST-999']:
            self.card(card_id)
        run = self.run_gate('tester', 'code', '5')
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn('2 printed, 0 skipped', run.stdout)
        self.assertIn('id: TST-401\n', run.stdout)
        self.assertIn('id: TST-402\n', run.stdout)
        self.assertNotIn('TST-999', run.stdout)

    def test_common_uses_every_mode_list_only(self):
        for card_id in ['TST-501', 'TST-505', 'TST-999', 'TST-P01']:
            self.card(card_id)
        run = self.run_gate('tester', 'code', 'common')
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn('2 printed, 0 skipped', run.stdout)
        self.assertIn('id: TST-501\n', run.stdout)
        self.assertIn('id: TST-505\n', run.stdout)
        self.assertNotIn('TST-P01', run.stdout)
        self.assertNotIn('TST-999', run.stdout)

    def test_policy_rejects_each_invalid_required_card(self):
        self.card('TST-P01')
        path = self.role / 'cards/TST-P02.md'
        for reason in ['status draft', 'mode site', 'missing', 'unreadable']:
            with self.subTest(reason=reason):
                self.card('TST-P02', status='draft' if reason == 'status draft' else 'approved',
                          mode='site' if reason == 'mode site' else 'all')
                if reason == 'missing':
                    path.unlink()
                elif reason == 'unreadable':
                    path.write_bytes(b'\xff')
                run = self.run_gate('tester', 'code', 'policy')
                self.assertEqual(run.returncode, 3, run.stderr)
                self.assertIn(f'BLOCKED TST-P02: {reason}\n', run.stdout)
                self.assertIn('id: TST-P01\n', run.stdout)

    def test_policy_all_approved_prints_each_required_card(self):
        for card_id in ['TST-P01', 'TST-P02']:
            self.card(card_id)
        run = self.run_gate('tester', 'code', 'policy')
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn('2 printed, 0 skipped', run.stdout)
        self.assertIn('id: TST-P01\n', run.stdout)
        self.assertIn('id: TST-P02\n', run.stdout)
        self.assertNotIn('TST-888', run.stdout)

    def test_empty_step_is_valid(self):
        run = self.run_gate('tester', 'code', '1')
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout, 'cards.py tester code 1: 0 printed, 0 skipped\n')

    def test_unknown_step_exits_2_without_traceback(self):
        run = self.run_gate('tester', 'code', '99')
        self.assertEqual(run.returncode, 2)
        self.assertEqual(len(run.stderr.splitlines()), 1)
        self.assertIn('step 99', run.stderr)

    def test_audit_reports_mismatch_across_modes_and_common(self):
        (self.role / 'modes/site.md').write_text('## Steps\n1. `TST-001`.\n', encoding='utf-8')
        self.card('TST-001', mode='code')
        self.card('TST-501')
        self.card('TST-505', mode='code')
        run = self.run_gate('tester', '--audit')
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn('site 1 SKIPPED TST-001: mode code\n', run.stdout)
        self.assertIn('site common SKIPPED TST-505: mode code\n', run.stdout)
        self.assertEqual(run.stdout.splitlines()[-1], 'total: 18 skipped')
        self.assertNotIn('id:', run.stdout)

    def test_bad_arguments_exit_2_with_1_stderr_line(self):
        for args in [(), ('tester',), ('../tester', '--audit'), ('absent', '--audit'), ('tester', 'code', 'zero'),
                     ('tester', 'absent', '1'), ('tester', 'code', '1', 'extra')]:
            with self.subTest(args=args):
                run = self.run_gate(*args)
                self.assertEqual(run.returncode, 2)
                self.assertEqual(len(run.stderr.splitlines()), 1)
                self.assertEqual(run.stdout, '')

    def test_only_exact_approved_status_opens_a_step_card(self):
        # Known pass: status approved. Known fail: every other status, a near miss, or no status line.
        for status, reason in [('approved', ''), ('draft', 'status draft'), ('disputed', 'status disputed'),
                               ('Approved', 'status Approved'), ('approved yes', 'status approved yes'),
                               (None, 'status missing')]:
            with self.subTest(status=status):
                if status is None:
                    (self.role / 'cards/TST-001.md').write_text('id: TST-001\nmode: all\n', encoding='utf-8')
                else:
                    self.card('TST-001', status=status)
                run = self.run_gate('tester', 'code', '2')
                self.assertEqual(run.returncode, 0, run.stderr)
                if reason:
                    self.assertIn(f'SKIPPED TST-001: {reason}\n', run.stdout)
                    self.assertNotIn('id: TST-001\n', run.stdout)
                else:
                    self.assertIn('id: TST-001\n', run.stdout)
                    self.assertNotIn('SKIPPED TST-001', run.stdout)

    def test_policy_card_not_approved_blocks_the_role(self):
        # Known pass: both policy cards approved, exit 0. Known fail: P02 draft, disputed or unlabelled, exit 3.
        self.card('TST-P01')
        for status in ['approved', 'draft', 'disputed', None]:
            with self.subTest(status=status):
                if status is None:
                    (self.role / 'cards/TST-P02.md').write_text('id: TST-P02\nmode: all\n', encoding='utf-8')
                else:
                    self.card('TST-P02', status=status)
                run = self.run_gate('tester', 'code', 'policy')
                if status == 'approved':
                    self.assertEqual(run.returncode, 0, run.stderr)
                    self.assertIn('id: TST-P02\n', run.stdout)
                else:
                    self.assertEqual(run.returncode, 3, run.stderr)
                    self.assertIn(f"BLOCKED TST-P02: status {status or 'missing'}\n", run.stdout)
                    self.assertNotIn('id: TST-P02\n', run.stdout)

    def test_mode_line_must_name_the_mode_or_all(self):
        # Known pass: all, code, code in a list. Known fail: other modes, a longer word, empty, no mode line.
        for mode, fits in [('all', True), ('code', True), ('site, code', True), ('explore code', True),
                           ('site', False), ('site, explore', False), ('codes', False), ('', False), (None, False)]:
            for step, verdict in [('2', 'SKIPPED'), ('policy', 'BLOCKED')]:
                card_id = 'TST-001' if step == '2' else 'TST-P01'
                with self.subTest(mode=mode, step=step):
                    self.card('TST-P02')
                    if mode is None:
                        (self.role / f'cards/{card_id}.md').write_text(
                            f'id: {card_id}\nstatus: approved\n', encoding='utf-8')
                    else:
                        self.card(card_id, mode=mode)
                    run = self.run_gate('tester', 'code', step)
                    if fits:
                        self.assertNotIn(f'{verdict} {card_id}', run.stdout)
                        self.assertIn(f'id: {card_id}\n', run.stdout)
                        if step == 'policy':
                            self.assertEqual(run.returncode, 0, run.stderr)
                    else:
                        self.assertIn(f"{verdict} {card_id}: mode {'missing' if mode is None else mode}\n", run.stdout)
                        self.assertNotIn(f'id: {card_id}\n', run.stdout)
                        self.assertEqual(run.returncode, 3 if step == 'policy' else 0, run.stderr)

    def test_policy_card_that_is_a_folder_blocks_the_role(self):
        self.card('TST-P01')
        (self.role / 'cards/TST-P02.md').mkdir()
        run = self.run_gate('tester', 'code', 'policy')
        self.assertEqual(run.returncode, 3, run.stderr)
        self.assertIn('BLOCKED TST-P02: unreadable\n', run.stdout)

    def test_unreadable_role_file_turns_the_role_off(self):
        # Known pass: the fixture ROLE.md. Known fail: each broken ROLE.md exits non zero and prints no card.
        for card_id in ['TST-P01', 'TST-P02', 'TST-001', 'TST-501']:
            self.card(card_id)
        role_file = self.role / 'ROLE.md'
        good = role_file.read_text(encoding='utf-8')
        breaks = {
            'missing': lambda: role_file.unlink(),
            'folder': lambda: (role_file.unlink(), role_file.mkdir()),
            'bad bytes': lambda: role_file.write_bytes(b'\xff## 3. Rules\n- `TST-P01`\n'),
            'empty': lambda: role_file.write_text('', encoding='utf-8'),
            'no rules heading': lambda: role_file.write_text('# Tester\n- `TST-P01`\n', encoding='utf-8'),
        }
        for step in ['policy', 'common', '2']:
            with self.subTest(case='intact', step=step):
                self.assertEqual(self.run_gate('tester', 'code', step).returncode, 0)
            for case, damage in breaks.items():
                with self.subTest(case=case, step=step):
                    damage()
                    try:
                        run = self.run_gate('tester', 'code', step)
                    finally:
                        if role_file.is_dir():
                            role_file.rmdir()
                        role_file.write_text(good, encoding='utf-8')
                    self.assertNotEqual(run.returncode, 0)
                    self.assertEqual(run.stdout, '')
                    self.assertEqual(len(run.stderr.splitlines()), 1)

    def test_policy_step_with_no_policy_cards_blocks_the_role(self):
        # A ROLE.md that names no policy card must not pass the policy step.
        # Known pass is test_policy_all_approved_prints_each_required_card.
        for rules in ['- `TST-888` Other rule\n', '* `TST-P01` Star bullet\n* `TST-P02` Star bullet\n']:
            with self.subTest(rules=rules):
                (self.role / 'ROLE.md').write_text(
                    f'# Tester\n## 3. Rules\n{rules}Cards for every mode:\n- `TST-501`\n', encoding='utf-8')
                run = self.run_gate('tester', 'code', 'policy')
                self.assertEqual(run.returncode, 3, run.stdout)
                self.assertIn('BLOCKED ROLE.md: names no policy card\n', run.stdout)

    def test_repeated_status_or_mode_line_keeps_a_card_closed(self):
        # A second status or mode line must not open a card, whatever it says.
        # Known pass is test_only_exact_approved_status_opens_a_step_card.
        for body, reason in [('status: draft\nmode: all\nstatus: approved\n', 'status repeated'),
                             ('status: approved\nmode: site\nmode: code\n', 'mode repeated')]:
            with self.subTest(reason=reason):
                (self.role / 'cards/TST-001.md').write_text(f'id: TST-001\n{body}', encoding='utf-8')
                run = self.run_gate('tester', 'code', '2')
                self.assertEqual(run.returncode, 0, run.stderr)
                self.assertIn(f'SKIPPED TST-001: {reason}\n', run.stdout)
                self.assertNotIn('id: TST-001\n', run.stdout)


class RealTesterRoleTests(unittest.TestCase):
    # Reads the real cards in this checkout. Changes nothing.
    def run_gate(self, *args):
        return subprocess.run([sys.executable, '-E', '-P', '-X', 'utf8', '-B',
                               str(Path(__file__).with_name('cards.py')), *args],
                              capture_output=True, text=True, encoding='utf-8', timeout=30)

    def test_every_mode_opens_all_4_policy_cards(self):
        for mode in ['code', 'site', 'explore']:
            with self.subTest(mode=mode):
                run = self.run_gate('tester', mode, 'policy')
                self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
                self.assertEqual(run.stdout.splitlines()[0], f'cards.py tester {mode} policy: 4 printed, 0 skipped')

    def test_audit_shows_only_the_3_expected_skips(self):
        run = self.run_gate('tester', '--audit')
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout, 'code common SKIPPED TST-519: mode site, explore\n'
                                     'explore common SKIPPED TST-514: mode code, site\n'
                                     'explore common SKIPPED TST-515: mode code, site\n'
                                     'total: 3 skipped\n')


class RealReviewerRoleTests(unittest.TestCase):
    # Reads the real role. Only the unreadable role check writes, in a temp tree.
    modes = {'size': 29, 'business': 32, 'security': 33, 'health': 34, 'full': 39}
    policy_ids = [f'REV-P{number:02d}' for number in range(1, 12)]

    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]
        self.role = self.root / 'roles/reviewer'

    def run_gate(self, *args, root=None):
        if root is None:
            root = self.root
        return subprocess.run([sys.executable, '-E', '-P', '-X', 'utf8', '-B',
                               str(root / 'tools/cards.py'), *args],
                              capture_output=True, text=True, encoding='utf-8', timeout=30)

    def test_every_mode_reads_the_role_and_names_11_policy_cards(self):
        role_file = self.role / 'ROLE.md'
        self.assertTrue(role_file.is_file(), str(role_file))
        bullets = '\n'.join(line for line in role_file.read_text(encoding='utf-8')
                            .split('Cards for every mode:', 1)[0].splitlines()
                            if line.startswith('- '))
        self.assertEqual(re.findall(r'REV-P\d\d', bullets), self.policy_ids)
        approved = sum('status: approved' in path.read_text(encoding='utf-8').splitlines()
                       for card_id in self.policy_ids
                       for path in [self.role / f'cards/{card_id}.md'] if path.is_file())
        for mode in self.modes:
            with self.subTest(mode=mode):
                run = self.run_gate('reviewer', mode, 'policy')
                self.assertEqual(run.returncode, 0 if approved == 11 else 3, run.stdout + run.stderr)
                self.assertEqual(run.stdout.splitlines()[0],
                                 f'cards.py reviewer {mode} policy: {approved} printed, {11 - approved} skipped')

    def test_every_policy_card_file_exists_and_is_draft_or_approved(self):
        for card_id in self.policy_ids:
            with self.subTest(card_id=card_id):
                path = self.role / f'cards/{card_id}.md'
                self.assertTrue(path.is_file(), str(path))
                lines = path.read_text(encoding='utf-8').splitlines()
                statuses = [line.partition(':')[2].strip() for line in lines if line.startswith('status:')]
                self.assertEqual(len(statuses), 1, str(path))
                self.assertIn(statuses[0], ['draft', 'approved'], str(path))
                self.assertEqual([line for line in lines if line.startswith('id:')], [f'id: {path.stem}'])

    def test_audit_on_the_scaffolds_is_exact(self):
        run = self.run_gate('reviewer', '--audit')
        self.assertEqual(run.returncode, 0, run.stderr)
        # Change this string when step or common cards are routed into the modes.
        self.assertEqual(run.stdout, 'total: 0 skipped\n')

    def test_each_mode_scaffold_has_a_steps_heading_and_its_filled_by_line(self):
        for mode, ticket in self.modes.items():
            with self.subTest(mode=mode):
                path = self.role / f'modes/{mode}.md'
                self.assertTrue(path.is_file(), str(path))
                text = path.read_text(encoding='utf-8')
                self.assertIn('## Steps', text.splitlines())
                self.assertRegex(text.lower(), rf'(?m)^1\. [^\n]*filled by ticket {ticket}\b')

    def test_unreadable_reviewer_role_file_turns_the_role_off(self):
        self.assertTrue(self.role.is_dir(), str(self.role))
        with tempfile.TemporaryDirectory(prefix='actas-reviewer-') as tree:
            root = Path(tree)
            (root / 'tools').mkdir()
            shutil.copyfile(self.root / 'tools/cards.py', root / 'tools/cards.py')
            role = root / 'roles/reviewer'
            shutil.copytree(self.role, role)
            role_file = role / 'ROLE.md'
            role_file.unlink()
            role_file.mkdir()
            run = self.run_gate('reviewer', 'size', 'policy', root=root)
            self.assertEqual(run.returncode, 2, run.stdout + run.stderr)
            self.assertEqual(run.stdout, '')
            self.assertEqual(len(run.stderr.splitlines()), 1)
            self.assertNotIn('Traceback', run.stderr)


if __name__ == '__main__':
    unittest.main()
