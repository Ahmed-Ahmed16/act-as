import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cards  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
REAL_ROLE = ROOT / 'roles/reviewer'
MODE_CARD = re.compile(r'REV-\d{3}\.md')
APPROVED = re.compile(r'^status: approved[ \t]*$', re.MULTILINE)
RERUN_STEPS = [str(number) for number in range(20, 26)]


def approved_mode_cards(role_dir):
    # Policy cards (REV-P01 and up) load through the policy step: not counted here.
    found = []
    for path in sorted((role_dir / 'cards').iterdir()):
        if MODE_CARD.fullmatch(path.name) and APPROVED.search(path.read_text(encoding='utf-8')):
            found.append(path.stem)
    return found


def loading_steps(role_dir, card_id):
    # Every (mode, step) where cards.py really prints the card: listed and mode line fits.
    places = []
    for mode_file in sorted((role_dir / 'modes').glob('*.md')):
        mode = mode_file.stem
        for step in cards.steps(role_dir, mode):
            if card_id in cards.selected_ids(role_dir, mode, step) \
                    and cards.card_body(role_dir, mode, card_id)[1] == '':
                places.append((mode, step))
    return places


def unwired_cards(role_dir):
    return [card_id for card_id in approved_mode_cards(role_dir)
            if not loading_steps(role_dir, card_id)]


def run_gate(*args):
    return subprocess.run([sys.executable, '-E', '-P', '-X', 'utf8', '-B',
                           str(ROOT / 'tools/cards.py'), *args],
                          capture_output=True, text=True, encoding='utf-8', timeout=30)


class UnwiredCardCheckTests(unittest.TestCase):
    # Known bad: planted cards in a temp role folder that the real files never touch.
    def setUp(self):
        tree = tempfile.TemporaryDirectory(prefix='reviewer-wiring-')
        self.addCleanup(tree.cleanup)
        self.role = Path(tree.name) / 'roles/reviewer'
        (self.role / 'modes').mkdir(parents=True)
        (self.role / 'cards').mkdir()
        (self.role / 'ROLE.md').write_text(
            '# Reviewer\n## 3. Rules\n- `REV-P01` Read only\nCards for every mode:\nNone yet.\n'
            '## 4. Skills\n', encoding='utf-8')
        (self.role / 'modes/size.md').write_text(
            '# Size\n## Steps\n1. Freeze. Card `REV-101`.\n2. Count.\n## Finish checklist\n- `REV-103`\n',
            encoding='utf-8')

    def card(self, card_id, status='approved', mode='size'):
        (self.role / f'cards/{card_id}.md').write_text(
            f'id: {card_id}\nstatus: {status}\nmode: {mode}\ntrigger: before a check\n', encoding='utf-8')

    def test_approved_card_in_no_step_is_found(self):
        self.card('REV-101')
        self.assertEqual(unwired_cards(self.role), [])
        self.card('REV-102')
        self.assertEqual(unwired_cards(self.role), ['REV-102'])

    def test_a_card_named_only_outside_the_steps_is_found(self):
        self.card('REV-103')
        self.assertEqual(unwired_cards(self.role), ['REV-103'])

    def test_draft_and_policy_cards_are_not_asked_to_be_wired(self):
        self.card('REV-104', status='draft')
        self.card('REV-P01', mode='all')
        self.assertEqual(unwired_cards(self.role), [])

    def test_card_listed_in_a_step_whose_mode_does_not_fit_is_found(self):
        self.card('REV-101', mode='security')
        self.assertEqual(unwired_cards(self.role), ['REV-101'])

    def test_card_with_mode_all_in_any_step_is_wired(self):
        self.card('REV-101', mode='all')
        self.assertEqual(unwired_cards(self.role), [])


class RealReviewerWiringTests(unittest.TestCase):
    # Known good: the real role files.
    def test_health_questions_5_9_21_apply_to_the_diff_without_a_pointer(self):
        # G41: the real gate must print the conditions agreed in B17.
        run = run_gate('reviewer', 'health', '18')
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        printed = dict(re.findall(r'^== (REV-\w+) \|[^\n]*\n(.*?)(?=^== |\Z)',
                                  run.stdout, re.MULTILINE | re.DOTALL))
        for card_id in ['REV-505', 'REV-509', 'REV-519']:
            self.assertIn(card_id, printed)
            fields = dict(re.findall(r'^([\w-]+): *(.*)$', printed[card_id], re.MULTILINE))
            for field in ['applies-when', 'extra']:
                with self.subTest(card_id=card_id, field=field):
                    if field == 'applies-when':
                        self.assertTrue(fields[field].startswith('The PR '), fields[field])
                    else:
                        self.assertIn('asked when the diff shows the relevant change.', fields[field])
                    self.assertNotIn('pointer', fields[field])

    def test_every_approved_reviewer_card_is_loaded_by_a_step(self):
        self.assertEqual(unwired_cards(REAL_ROLE), [])

    def test_the_20_size_and_base_cards_are_approved_and_counted(self):
        expected = [f'REV-{number}' for number in range(101, 121)]
        self.assertEqual([card for card in approved_mode_cards(REAL_ROLE) if card in expected], expected)

    def test_cards_py_prints_each_card_wired_in_size_mode(self):
        wired = {}
        for card_id in approved_mode_cards(REAL_ROLE):
            for mode, step in loading_steps(REAL_ROLE, card_id):
                if mode == 'size':
                    wired.setdefault(step, []).append(card_id)
        self.assertTrue(wired)
        for step, card_ids in wired.items():
            with self.subTest(step=step):
                run = run_gate('reviewer', 'size', step)
                self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
                printed = re.findall(r'^== (REV-\w+) \|', run.stdout, re.MULTILINE)
                for card_id in card_ids:
                    self.assertIn(card_id, printed)
                self.assertNotIn('SKIPPED', run.stdout)

    def test_every_size_card_is_wired_in_size_mode(self):
        for number in range(101, 121):
            card_id = f'REV-{number}'
            with self.subTest(card_id=card_id):
                self.assertIn('size', [mode for mode, _ in loading_steps(REAL_ROLE, card_id)])

    def test_business_rerun_steps_20_to_25_load_their_approved_cards(self):
        self.assertTrue(set(RERUN_STEPS) <= set(cards.steps(REAL_ROLE, 'business')))
        expected = {'20': ['REV-233', 'REV-236', 'REV-239'], '21': ['REV-234'],
                    '22': ['REV-235'], '23': [], '24': ['REV-237'], '25': ['REV-238']}
        for step in RERUN_STEPS:
            with self.subTest(step=step):
                run = run_gate('reviewer', 'business', step)
                self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
                self.assertEqual(run.stdout.splitlines()[0],
                                 f'cards.py reviewer business {step}: {len(expected[step])} printed, 0 skipped')
                self.assertEqual(re.findall(r'^== (REV-\w+) \|', run.stdout, re.MULTILINE), expected[step])

    def test_a_rerun_step_number_that_does_not_exist_is_refused(self):
        run = run_gate('reviewer', 'business', '26')
        self.assertEqual(run.returncode, 2, run.stdout + run.stderr)
        self.assertIn('unknown step 26', run.stderr)


if __name__ == '__main__':
    unittest.main()
