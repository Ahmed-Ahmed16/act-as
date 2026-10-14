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


if __name__ == '__main__':
    unittest.main()
