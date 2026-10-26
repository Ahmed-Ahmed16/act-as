import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


FAILED_SHAPE = 1
HEADINGS = ['Behaviour changed', 'Files that matter most', 'Tests run',
            'Not checked', 'Known risks', 'Pointers', 'Split plan', 'Drafts, not sent']
MONEY_NO = 'no money code found by reading; not proof'
MONEY_YES = ('yes, files cart.py. Needs the separate Opus review before merge. '
             'Not done by this review.')
CAP_LINE = "reviewed over the cap, on Ahmed's word"


def good_packet():
    bodies = ['The cart shows ___ (tax) after a country change.',
              'cart.py reads the country.', 'python -m unittest passed.',
              '___ (tax): The owner has not supplied the tax rule.',
              'none', 'none', 'not needed: The change fits together.',
              'Draft: Ask the owner for the tax rule.']
    return ('# Review packet\n'
            f'identity: repo=acme/shop; pr=101; mode=full; head={"a" * 40}; '
            f'base={"b" * 40}; default=main@{"c" * 40}; date=2026-10-26\n'
            'size: pass, 120 counted lines\n'
            'business: incomplete, no rules page; merge only after: owner answers\n'
            'security: pass\nhealth: fail, 1 must fix\n'
            f'money: {MONEY_NO}\n\n' + ''.join(
                f'## {heading}\n{body}\n\n' for heading, body in zip(HEADINGS, bodies)))


def replace_body(packet, heading, body):
    before, rest = packet.split(f'## {heading}\n', 1)
    _, separator, after = rest.partition('\n## ')
    return before + f'## {heading}\n{body}\n' + separator + after


class PacketCheckTests(unittest.TestCase):
    # Boundaries: missing/empty/duplicate/order, word suffixes, labels/reasons,
    # each money form, all identity keys, bad paths/bytes, and multiple failures.
    # Removing any rule must make its named bad packet test fail.
    def setUp(self):
        self.tree = tempfile.TemporaryDirectory(prefix='packet-check-')
        self.addCleanup(self.tree.cleanup)
        self.root = Path(self.tree.name)
        self.script = self.root / 'packet_check.py'
        source = Path(__file__).with_name('packet_check.py')
        if source.exists():
            shutil.copyfile(source, self.script)
        self.packet = self.root / 'packet'
        self.packet.mkdir()
        self.path = self.packet / 'packet.md'
        self.path.write_text(good_packet(), encoding='utf-8')

    def run_check(self, *args):
        return subprocess.run([sys.executable, '-E', '-P', '-X', 'utf8', '-B',
                               str(self.script), *map(str, args)],
                              capture_output=True, text=True, encoding='utf-8', timeout=10)

    def check_text(self, packet):
        self.path.write_text(packet, encoding='utf-8')
        return self.run_check(self.packet)

    def assert_pass(self, packet):
        run = self.check_text(packet)
        self.assertEqual(run.returncode, 0, run.stderr + run.stdout)
        self.assertEqual(run.stdout, 'packet_check: pass\n')
        self.assertEqual(run.stderr, '')

    def assert_rule(self, packet, rule, message):
        run = self.check_text(packet)
        self.assertEqual(run.returncode, FAILED_SHAPE, run.stderr + run.stdout)
        self.assertEqual(run.stdout.splitlines(), [f'RULE {rule}: {message}'])
        self.assertEqual(run.stderr, '')

    def test_good_packet_passes(self):
        self.assert_pass(good_packet())

    def test_good_packet_with_cap_line_passes(self):
        self.assert_pass(CAP_LINE + '\n' + good_packet())

    def test_headings_missing_duplicate_or_out_of_order(self):
        packet = good_packet()
        swapped = packet.replace('## Tests run', '## PLACEHOLDER').replace(
            '## Files that matter most', '## Tests run').replace(
            '## PLACEHOLDER', '## Files that matter most')
        for bad in [packet.replace('# Review packet\n', ''),
                    '# Review packet\n' + packet, swapped,
                    packet.replace('## Pointers\n', ''),
                    packet + '## Pointers\nnone\n']:
            with self.subTest(packet=bad):
                self.assert_rule(bad, 'headings', 'missing, duplicated, or out of order')

    def test_identity_lists_bad_or_missing_keys(self):
        packet = good_packet()
        identity = packet.splitlines()[1]
        pairs = identity.removeprefix('identity: ').split('; ')
        for pair in pairs:
            key = pair.split('=', 1)[0]
            for replacement in ['', key + '=bad']:
                with self.subTest(key=key, replacement=replacement):
                    bad = packet.replace(identity, 'identity: ' + '; '.join(
                        replacement if entry == pair else entry for entry in pairs))
                    self.assert_rule(bad, 'identity', 'bad or missing keys: ' + key)
        self.assert_rule(packet.replace(identity + '\n', ''), 'identity',
                         'bad or missing keys: repo, pr, mode, head, base, default, date')

    def test_verdict_words_rejects_missing_and_bad_words(self):
        for field in ['size', 'business', 'security', 'health']:
            line = next(line for line in good_packet().splitlines() if line.startswith(field + ':'))
            for replacement in ['', field + ': passed', field + ': does not apply']:
                with self.subTest(field=field, replacement=replacement):
                    self.assert_rule(good_packet().replace(line, replacement),
                                     'verdict-words', 'bad or missing verdicts: ' + field)

    def test_verdict_word_endings_and_long_words_pass(self):
        for field in ['size', 'business', 'security', 'health']:
            line = next(line for line in good_packet().splitlines() if line.startswith(field + ':'))
            words = ['pass', 'fail', 'not asked']
            if field != 'size':
                words += ['incomplete', 'not checked']
            for word in words:
                for ending in ['', ', reason', ': reason', '; reason', '. reason', ' reason']:
                    with self.subTest(field=field, word=word, ending=ending):
                        self.assert_pass(good_packet().replace(line, field + ': ' + word + ending))

    def test_money_line_rejects_bad_or_missing_forms(self):
        for money in ['', 'does not apply', 'not checked:',
                      MONEY_YES.replace('cart.py', ''), MONEY_YES.replace('Not done', 'Done')]:
            with self.subTest(money=money):
                bad = good_packet().replace('money: ' + MONEY_NO,
                                             'money: ' + money if money else '')
                self.assert_rule(bad, 'money-line', 'missing or invalid money line')

    def test_money_forms_pass(self):
        for money in [MONEY_NO, MONEY_YES, 'not checked: The cart files were unavailable.']:
            with self.subTest(money=money):
                self.assert_pass(good_packet().replace(MONEY_NO, money))

    def test_missing_part_names_fields_with_no_content(self):
        for heading in [*HEADINGS[:3], HEADINGS[3], HEADINGS[7]]:
            for body in ['none', 'unknown', 'not checked', 'not checked:',
                         'unknown\nnot checked:']:
                with self.subTest(heading=heading, body=body):
                    packet = good_packet().replace('___ (tax)', 'tax pending')
                    self.assert_rule(replace_body(packet, heading, body),
                                     'missing-part', 'missing content: ' + heading)
        for heading in [*HEADINGS[:3], *HEADINGS[4:]]:
            with self.subTest(heading=heading, body=''):
                packet = good_packet().replace('___ (tax)', 'tax pending')
                self.assert_rule(replace_body(packet, heading, ''),
                                 'missing-part', 'missing content: ' + heading)

    def test_missing_part_allows_none_in_risks_and_pointers(self):
        for heading in HEADINGS[4:6]:
            with self.subTest(heading=heading):
                self.assert_pass(replace_body(good_packet(), heading, 'none found after reading'))
        self.assert_pass(replace_body(good_packet(), 'Split plan', 'Separate cart and account changes.'))

    def test_not_checked_empty_reports_only_its_own_rule(self):
        for body in ['', ' \n\t']:
            with self.subTest(body=body):
                packet = good_packet().replace('___ (tax)', 'tax pending')
                self.assert_rule(replace_body(packet, 'Not checked', body),
                                 'not-checked-empty', 'Not checked has no content')

    def test_unknown_unmatched_requires_labels_and_reasons(self):
        packet = good_packet()
        cases = [(packet.replace('___ (tax)', '___', 1), 'bare ___'),
                 (packet.replace('___ (tax): The owner', 'tax: The owner'), 'tax'),
                 (replace_body(packet, 'Not checked', '___ (tax):'), 'tax'),
                 (replace_body(packet, 'Not checked', '___ (tax):   '), 'tax'),
                 (packet + 'Extra ___\n', 'bare ___')]
        for bad, labels in cases:
            with self.subTest(packet=bad):
                self.assert_rule(bad, 'unknown-unmatched', 'unmatched unknowns: ' + labels)

    def test_unknown_labels_match_exactly_and_list_all(self):
        packet = good_packet().replace('___ (tax): The owner', '___ (taxes): The owner')
        self.assert_rule(packet, 'unknown-unmatched', 'unmatched unknowns: tax')
        packet = good_packet().replace('after a country', 'and ___ (fee) after a country')
        self.assert_rule(packet, 'unknown-unmatched', 'unmatched unknowns: fee')
        self.assert_pass(replace_body(packet, 'Not checked',
                                     '___ (tax): Missing rule.\n___ (fee): Missing owner.'))

    def test_safe_to_merge_rejects_substrings_and_case(self):
        for phrase in ['safe to merge', 'SAFE TO MERGE', 'unsafe to merge']:
            with self.subTest(phrase=phrase):
                self.assert_rule(good_packet() + phrase + '\n', 'safe-to-merge',
                                 'contains safe to merge')

    def test_overall_line_rejects_decorated_starts(self):
        for line in ['overall: pass', 'READY now', '  - **Overall** pass', '__Overall__ pass',
                     '* ### **ready**', 'already handled\noverall verdict: pass']:
            with self.subTest(line=line):
                self.assert_rule(good_packet() + line + '\n', 'overall-line',
                                 'line starts with overall or ready')
        self.assert_pass(good_packet() + 'The cart is ready for another review.\n')

    def test_cap_contradiction_rejects_both_statements(self):
        self.assert_rule(CAP_LINE + '\n' + good_packet() + 'It was not reviewed past size\n',
                         'cap-contradiction', 'cap review contradicts size stop')
        self.assert_pass(good_packet() + 'It was not reviewed past size\n')

    def test_multiple_rules_each_print_once_in_rule_order(self):
        packet = good_packet() + 'safe to merge\nsafe to merge\nOverall: pass\n'
        run = self.check_text(packet)
        self.assertEqual(run.returncode, FAILED_SHAPE)
        self.assertEqual(run.stdout.splitlines(), ['RULE safe-to-merge: contains safe to merge',
                                                  'RULE overall-line: line starts with overall or ready'])
        self.assertEqual(run.stderr, '')

    def assert_bad_input(self, *args):
        run = self.run_check(*args)
        self.assertEqual(run.returncode, 2)
        self.assertEqual(run.stdout, '')
        self.assertEqual(len(run.stderr.splitlines()), 1, run.stderr)
        self.assertTrue(run.stderr.startswith('packet_check: '), run.stderr)

    def test_bad_arguments_and_folder_paths(self):
        for args in [(), (self.packet, 'extra'), (self.root / 'absent',), (self.path,)]:
            with self.subTest(args=args):
                self.assert_bad_input(*args)

    def test_missing_empty_whitespace_and_invalid_utf8_packet(self):
        self.path.unlink()
        self.assert_bad_input(self.packet)
        for contents in [b'', b' \t\r\n', b'\xff']:
            with self.subTest(contents=contents):
                self.path.write_bytes(contents)
                self.assert_bad_input(self.packet)

    def test_packet_path_is_not_a_file(self):
        self.path.unlink()
        self.path.mkdir()
        self.assert_bad_input(self.packet)


if __name__ == '__main__':
    unittest.main()
