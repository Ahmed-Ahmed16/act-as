import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path

if __package__:
    from .test_packet_check import good_inputs
else:
    from test_packet_check import good_inputs


class SplitPiecesTests(unittest.TestCase):
    def setUp(self):
        tree = tempfile.TemporaryDirectory(prefix='pieces-')
        self.addCleanup(tree.cleanup)
        script = Path(tree.name) / 'packet_check.py'
        shutil.copyfile(Path(__file__).with_name('packet_check.py'), script)
        spec = importlib.util.spec_from_file_location('standalone_packet', script)
        self.checker = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.checker)
        self.inputs = good_inputs()
        self.inputs['files.json']['files'][0].update(
            counted_lines=10, hunks=[dict(id='f1h1', counted_lines=10)])

    def failures(self, first, second, sizes=(4, 6)):
        self.inputs['split-plan.json']['groups'] = [
            dict(name='orchard', hunks=first), dict(name='grove', hunks=second)]
        body = f'group: orchard, {sizes[0]} counted lines\ngroup: grove, {sizes[1]} counted lines'
        lines = ('size: pass, 10 counted lines\n## Split plan\n' + body +
                 '\n## Drafts, not sent\n' + body).splitlines()
        return self.checker.split_failures(lines, self.inputs)

    def test_K1_adjacent_pieces_cover_hunk_and_count_each_group(self):
        self.assertEqual(self.failures(['f1h1:L1-L4'], ['f1h1:L5-L10']), [])
        self.assertTrue(callable(self.checker.parse_piece))

    def test_K2_missing_line_is_unplaced(self):
        failures = self.failures(['f1h1:L1-L4'], ['f1h1:L6-L10'], (4, 5))
        self.assertEqual([rule for rule, _ in failures], ['hunk-unplaced'])

    def test_K3_overlap_and_whole_with_piece_are_duplicates(self):
        for first, second, sizes in [(['f1h1:L1-L5'], ['f1h1:L5-L10'], (5, 6)),
                                     (['f1h1'], ['f1h1:L1-L4'], (10, 4))]:
            with self.subTest(first=first):
                self.assertIn('hunk-duplicate', dict(self.failures(first, second, sizes)))
        self.inputs['files.json']['files'][0]['hunks'][0]['counted_lines'] = 0
        self.assertIn('hunk-duplicate', dict(self.failures(['f1h1'], ['f1h1'], (0, 0))))

    def test_K4_bad_ranges_are_rejected(self):
        for piece in ['f1h1:L0-L3', 'f1h1:L5-L2', 'f1h1:L1-L11', 'f1h1:Lx-L3',
                      'f1op:L1-L2', 'f1h1:L1', 'f1h1:L1-L2:bad']:
            with self.subTest(piece=piece):
                self.assertIn('hunk-range', dict(self.failures([piece], [], (0, 0))))

    def test_K5_test_hunk_range_counts_zero(self):
        self.inputs['files.json']['files'].append(dict(
            kind='test', hunks=[dict(id='f2h1', counted_lines=0)]))
        self.assertEqual(self.failures(['f1h1', 'f2h1:L3-L99'], [], (10, 0)), [])
        self.assertIn('hunk-range', dict(self.failures(['f1h1', 'f2h1:L0-L3'], [], (10, 0))))

    def test_missing_hunk_id_returns_rule_instead_of_crashing(self):
        del self.inputs['files.json']['files'][0]['hunks'][0]['id']
        failures = self.failures([], [], (0, 0))
        self.assertIn('hunk-unplaced', dict(failures))


if __name__ == '__main__':
    unittest.main()
