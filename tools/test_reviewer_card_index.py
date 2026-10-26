import re
import tempfile
import unittest
from pathlib import Path


# Range ends stay inclusive: Q32, S22, H11 and T8. L1 and L5 stand alone.
EXPECTED_IDS = (
    [f'Q{number}' for number in range(1, 33)]
    + [f'S{number}' for number in range(1, 23)]
    + ['L1', 'L5']
    + [f'H{number}' for number in range(1, 12)]
    + [f'T{number}' for number in range(1, 9)]
)
CARD_DIR = Path(__file__).resolve().parents[1] / 'roles/reviewer/cards'
INDEX_PATH = CARD_DIR / 'INDEX.md'


def _section(text, heading):
    return text.partition(heading + '\n')[2].split('\n## ', 1)[0]


def _policy_ids(text):
    policy_table = text.split('\n## Check map', 1)[0]
    return re.findall(r'^\|\s*`?(REV-P\d{2})`?\s*\|', policy_table, re.MULTILINE)


def _card_problems(card_id, card_dir):
    card_path = Path(card_dir) / f'{card_id}.md'
    if not card_path.is_file():
        return [f'{card_id}: card file missing']
    try:
        card_text = card_path.read_text(encoding='utf-8')
    except (OSError, UnicodeError) as error:
        return [f'{card_id}: card file unreadable: {error}']
    if not re.search(r'^status: approved[ \t]*$', card_text, re.MULTILINE):
        return [f'{card_id}: card status is not approved']
    return []


def _target_problems(check_id, target, gaps, card_dir):
    if target == '`gap`':
        if check_id not in gaps:
            return [f'{check_id}: gap missing from gap list']
        return []
    if re.fullmatch(r'`REV-(?:P\d{2}|\d{3})`', target):
        return [f'{check_id}: {problem}' for problem in
                _card_problems(target.strip('`'), card_dir)]
    return [f'{check_id}: row must name an approved card or gap in backticks']


def check_index(text, expected_ids, card_dir):
    problems = []
    expected = set(expected_ids)
    check_map = _section(text, '## Check map')
    gap_list = _section(text, '## Card gap list')
    gaps = set(re.findall(r'^- (\S+)[ \t]*$', gap_list, re.MULTILINE))
    rows = re.findall(r'^\|\s*`([^`]+)`\s*\|([^\n]*)$', check_map, re.MULTILINE)
    mapped = {}
    for check_id, target_cell in rows:
        target = target_cell.strip().removesuffix('|').strip()
        if check_id in mapped:
            problems.append(f'{check_id}: duplicate check map row')
        mapped[check_id] = target
        if check_id not in expected:
            problems.append(f'{check_id}: unexpected check map id')
        problems.extend(_target_problems(check_id, target, gaps, card_dir))
    for check_id in sorted(expected - mapped.keys()):
        problems.append(f'{check_id}: missing from check map')
    for check_id in sorted(gaps):
        if mapped.get(check_id) != '`gap`':
            problems.append(f'{check_id}: gap list id is not marked gap in check map')
    for card_id in _policy_ids(text):
        problems.extend(_card_problems(card_id, card_dir))
    return problems


class ReviewerCardIndexTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(INDEX_PATH.is_file(), f'Missing index: {INDEX_PATH}')
        self.text = INDEX_PATH.read_text(encoding='utf-8')

    def assert_problem_names(self, problems, check_id):
        self.assertTrue(problems, f'{check_id}: expected a validation problem')
        self.assertIn(check_id, '\n'.join(problems))

    def test_real_index_passes(self):
        self.assertEqual(check_index(self.text, EXPECTED_IDS, CARD_DIR), [])

    def test_missing_or_empty_check_row_fails(self):
        cases = [
            ('S5', self.text.replace('| `S5` | `gap` |\n', '').replace('- S5\n', ''),
             EXPECTED_IDS),
            ('S99', self.text.replace('## Check map\n',
                                     '## Check map\n| `S99` | |\n'),
             EXPECTED_IDS + ['S99']),
        ]
        for check_id, text, expected in cases:
            with self.subTest(check_id=check_id):
                self.assert_problem_names(check_index(text, expected, CARD_DIR), check_id)

    def test_mapped_card_without_file_fails(self):
        text = self.text.replace('| `S5` | `gap` |', '| `S5` | `REV-P99` |')
        text = text.replace('- S5\n', '')
        with tempfile.TemporaryDirectory(prefix='reviewer-index-') as folder:
            problems = check_index(text, EXPECTED_IDS, Path(folder))
        self.assertIn('S5: REV-P99: card file missing', problems)

    def test_gap_missing_from_list_fails(self):
        text = self.text.replace('- S5\n', '')
        problems = check_index(text, EXPECTED_IDS, CARD_DIR)
        self.assertIn('S5: gap missing from gap list', problems)

    def test_mapped_draft_card_fails(self):
        text = '## Check map\n| `Q1` | `REV-P99` |\n\n## Card gap list\n'
        with tempfile.TemporaryDirectory(prefix='reviewer-index-') as folder:
            card_dir = Path(folder)
            card = card_dir / 'REV-P99.md'
            card.write_text('id: REV-P99\nstatus: approved\n', encoding='utf-8')
            self.assertEqual(check_index(text, ['Q1'], card_dir), [])
            card.write_text('id: REV-P99\nstatus: draft\n', encoding='utf-8')
            problems = check_index(text, ['Q1'], card_dir)
        self.assertEqual(problems, ['Q1: REV-P99: card status is not approved'])

    def test_numeric_card_id_is_accepted_and_still_must_be_approved(self):
        text = '## Check map\n| `Q1` | `REV-999` |\n\n## Card gap list\n'
        with tempfile.TemporaryDirectory(prefix='reviewer-index-') as folder:
            card_dir = Path(folder)
            card = card_dir / 'REV-999.md'
            card.write_text('id: REV-999\nstatus: approved\n', encoding='utf-8')
            self.assertEqual(check_index(text, ['Q1'], card_dir), [])
            card.write_text('id: REV-999\nstatus: draft\n', encoding='utf-8')
            problems = check_index(text, ['Q1'], card_dir)
        self.assertEqual(problems, ['Q1: REV-999: card status is not approved'])
        bad = text.replace('REV-999', 'REV-99')
        self.assertEqual(check_index(bad, ['Q1'], card_dir),
                         ['Q1: row must name an approved card or gap in backticks'])

    def test_real_policy_table_has_exactly_11_existing_cards(self):
        policy_ids = _policy_ids(self.text)
        self.assertCountEqual(policy_ids, [f'REV-P{number:02d}' for number in range(1, 12)])
        for card_id in policy_ids:
            with self.subTest(card_id=card_id):
                self.assertTrue((CARD_DIR / f'{card_id}.md').is_file())

    def test_unexpected_check_id_fails(self):
        text = self.text.replace('## Check map\n', '## Check map\n| `S99` | `gap` |\n')
        text += '- S99\n'
        problems = check_index(text, EXPECTED_IDS, CARD_DIR)
        self.assertEqual(problems, ['S99: unexpected check map id'])

    def test_gap_list_id_without_gap_row_fails(self):
        text = self.text.replace('| `S5` | `gap` |', '| `S5` | `REV-P01` |')
        problems = check_index(text, EXPECTED_IDS, CARD_DIR)
        self.assertEqual(problems, ['S5: gap list id is not marked gap in check map'])

    def test_invalid_policy_card_fails(self):
        text = ('| id | mode | trigger | status | rule in short |\n'
                '| REV-P99 | all | before review | approved | Read the code. |\n'
                '\n## Check map\n| `Q1` | `gap` |\n\n## Card gap list\n- Q1\n')
        with tempfile.TemporaryDirectory(prefix='reviewer-index-') as folder:
            card_dir = Path(folder)
            self.assertEqual(check_index(text, ['Q1'], card_dir),
                             ['REV-P99: card file missing'])
            card = card_dir / 'REV-P99.md'
            card.write_text('id: REV-P99\nstatus: draft\n', encoding='utf-8')
            self.assertEqual(check_index(text, ['Q1'], card_dir),
                             ['REV-P99: card status is not approved'])
            card.write_text('id: REV-P99\nstatus: approved\n', encoding='utf-8')
            self.assertEqual(check_index(text, ['Q1'], card_dir), [])

    def test_duplicate_check_row_fails(self):
        text = self.text.replace('## Check map\n', '## Check map\n| `S5` | `gap` |\n')
        problems = check_index(text, EXPECTED_IDS, CARD_DIR)
        self.assertEqual(problems, ['S5: duplicate check map row'])


if __name__ == '__main__':
    unittest.main()
