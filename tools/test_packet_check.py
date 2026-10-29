import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

if __package__:
    from .packet_check import bad_verdicts
else:
    from packet_check import bad_verdicts


FAILED_SHAPE = 1
HEADINGS = ['Behaviour changed', 'Files that matter most', 'Tests run',
            'Not checked', 'Known risks', 'Pointers', 'Split plan', 'Drafts, not sent']
MONEY_NO = 'no money code found by reading; not proof'
MONEY_YES = ('yes, files cart.py. Needs the separate Opus review before merge. '
             'Not done by this review.')
CAP_LINE = "reviewed over the cap, on Ahmed's word"
STOP = 'not checked: PR over the cap, split it first'
HEAD = 'a' * 40


def good_packet():
    bodies = ['The cart shows ___ (tax) after a country change.',
              'cart.py reads the country.', f'CI run 12 on {HEAD}: pass',
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


def replace_line(packet, field, body):
    line = next(line for line in packet.splitlines() if line.startswith(field + ':'))
    return packet.replace(line, field + ': ' + body)


def single_packet(mode='business'):
    packet = good_packet().replace('mode=full', 'mode=' + mode)
    for field in ['size', 'business', 'security', 'health']:
        if field != mode:
            packet = replace_line(packet, field, f'not asked: {mode} run only')
    if mode != 'security':
        packet = replace_line(packet, 'money', f'not checked: money not looked at, {mode} run only')
    return packet


def good_inputs():
    entries = [dict(id=entry_id, mode='security', area='', kind='check',
                    tool_result='Ran the orchard check.', reading_result='Read orchard.py.',
                    word='pass', reason='', base_read='', head_read='')
               for entry_id in [*(f'S{number}' for number in range(1, 23)), 'L1', 'L5', 'RA', 'RB']]
    for entry in entries[-2:]:
        entry.update(mode='business', area='orchard', kind='rule',
                     base_read='baseline: none, new feature', head_read='Read orchard.py.')
    return {
        'check-record.json': {'required_ids': ['RA', 'RB'], 'entries': entries},
        'files.json': {'files': [dict(path='orchard.py', old_path='', status='added',
                                    kind='counted', counted_lines=120,
                                    hunks=[{'id': 'h1', 'counted_lines': 70},
                                           {'id': 'h2', 'counted_lines': 50}])]},
        'split-plan.json': {'groups': [], 'first_group_parts': [], 'unplaced': []},
        'rules-pages.json': {'areas': [dict(area='orchard', page='orchard.md',
                                          commit='d' * 40,
                                          rules=[{'id': 'RA', 'status': 'active'},
                                                 {'id': 'RB', 'status': 'active'}])]}}


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
        self.inputs = good_inputs()
        self.write_inputs()

    def write_inputs(self):
        for filename, contents in self.inputs.items():
            (self.packet / filename).write_text(json.dumps(contents), encoding='utf-8')

    def split_packet(self):
        self.inputs['split-plan.json']['groups'] = [
            dict(name='orchard', entry_points=['orchard.py'], estimate=70, hunks=['h1']),
            dict(name='grove', entry_points=['grove.py'], estimate=50, hunks=['h2'])]
        self.write_inputs()
        groups = 'group: orchard, 70 counted lines\ngroup: grove, 50 counted lines'
        packet = replace_body(single_packet(), 'Split plan', groups)
        return replace_body(packet, 'Drafts, not sent', groups)

    def short_packet(self):
        packet = self.split_packet().replace('mode=business', 'mode=full')
        packet = replace_line(packet, 'size', 'fail, 120 counted lines')
        for field in ['business', 'security', 'health', 'money']:
            packet = replace_line(packet, field, STOP)
        for heading in HEADINGS[1:6]:
            packet = replace_body(packet, heading, STOP)
        return replace_body(packet, 'Behaviour changed', 'orchard changes.\ngrove changes.')

    def override_packet(self):
        return CAP_LINE + '\n' + replace_line(good_packet(), 'size', 'fail, 120 counted lines')

    def rerun_packet(self):
        packet = replace_line(good_packet(), 'business', 'pass, orchard rebuilt')
        packet = packet.replace('date=2026-10-26', 'date=2026-10-26; rerun=yes')
        return f'business rerun for orchard, 2026-10-26, head {HEAD}\n' + packet

    def assert_rules(self, packet, *rules):
        run = self.check_text(packet)
        self.assertEqual(run.returncode, FAILED_SHAPE, run.stderr + run.stdout)
        self.assertEqual(run.stderr, '')
        lines = run.stdout.splitlines()
        self.assertTrue(all(line.startswith('RULE ') and ': ' in line for line in lines), lines)
        self.assertCountEqual([line.split(':', 1)[0][5:] for line in lines], rules)

    # Cases: each packet type, absent counts, wrong head, empty fields,
    # wrong mode words, misplaced cap, missing areas, and rerun security words.
    # Removing a named exception must fail the corresponding CLI test.
    def test_short_packet_passes(self):
        self.assert_pass(self.short_packet())

    def test_single_mode_packet_passes(self):
        self.inputs['check-record.json']['entries'] = self.inputs['check-record.json']['entries'][-2:]
        self.write_inputs()
        self.assert_pass(single_packet())

    def test_single_size_over_cap_not_asked_passes(self):
        packet = replace_line(single_packet('size'), 'size', 'fail, 120 counted lines')
        self.assert_pass(replace_body(packet, 'Split plan', 'not asked: size run only'))

    def test_g14_size_mode_saved_examples_pass_packet_check(self):
        mode = Path(__file__).resolve().parents[1] / 'roles/reviewer/modes/size.md'
        instructions = mode.read_text(encoding='utf-8')
        common, over_cap = instructions.split('**Over the cap (', 1)
        pattern = r'`([\w-]+\.json)`(?:\s*:|\s+stays)\s*`([^`]+)`'
        examples = dict(re.findall(pattern, common))
        # G14: execute the saved examples at both sides of the cap.
        for total, verdict in [(301, 'fail'), (300, 'pass')]:
            with self.subTest(total=total):
                saved = dict(examples)
                if verdict == 'fail':
                    overrides = dict(re.findall(pattern, over_cap))
                    saved['split-plan.json'] = overrides.get('split-plan.json', '[]')
                # The old instruction says empty lists when no object is shown.
                for filename in ['check-record.json', 'split-plan.json', 'rules-pages.json']:
                    self.inputs[filename] = json.loads(saved.get(filename, '[]'))
                file = self.inputs['files.json']['files'][0]
                file.update(counted_lines=total, hunks=[{'id': 'h1', 'counted_lines': total}])
                self.write_inputs()
                packet = replace_line(single_packet('size'), 'size',
                                      f'{verdict}, {total} counted lines, cap 300')
                packet = replace_body(packet, 'Tests run', 'not asked: size run only')
                plan = ('not asked: size run only' if verdict == 'fail'
                        else f'not needed: {total} counted lines, cap 300')
                packet = replace_body(packet, 'Split plan', plan)
                if verdict == 'fail':
                    packet = replace_body(packet, 'Drafts, not sent', 'not asked: size run only')
                self.assert_pass(packet)

    def test_single_size_over_cap_not_checked_passes(self):
        packet = replace_line(single_packet('size'), 'size', 'fail, 120 counted lines')
        for field in ['business', 'security', 'health']:
            packet = replace_line(packet, field, STOP)
        self.assert_pass(replace_body(packet, 'Split plan', 'not asked: size run only'))

    # Cases: exact stop text, other plan text, groups in either body,
    # absent or repeated placements, empty drafts, and other packet modes.
    def test_single_size_over_cap_pass_verdicts_fail_single_mode_line(self):
        packet = replace_line(single_packet('size'), 'size', 'fail, 120 counted lines')
        packet = replace_body(packet, 'Split plan', 'not asked: size run only')
        for field in ['business', 'security', 'health']:
            packet = replace_line(packet, field, 'pass')
        self.assert_rules(packet, 'single-mode-line')

    def test_single_size_over_cap_groups_in_plan_fail_both_size_rules(self):
        split = self.split_packet()
        packet = replace_line(single_packet('size'), 'size', 'fail, 120 counted lines')
        groups = split.split('## Split plan\n', 1)[1].split('\n## ', 1)[0].strip()
        packet = replace_body(packet, 'Split plan', groups)
        for draft, extra_rules in [(groups, []), ('Draft: Ask about orchard.', ['split-message'])]:
            with self.subTest(draft=draft):
                self.assert_rules(replace_body(packet, 'Drafts, not sent', draft),
                                  'size-split-plan', 'size-no-draft', *extra_rules)

    def test_single_size_over_cap_groups_in_drafts_fail_size_no_draft(self):
        packet = replace_line(single_packet('size'), 'size', 'fail, 120 counted lines')
        packet = replace_body(packet, 'Split plan', 'not asked: size run only')
        for prefix in ['', '  ', '- ', '* ']:
            with self.subTest(prefix=prefix):
                self.assert_rules(replace_body(packet, 'Drafts, not sent',
                                              prefix + 'group: orchard, 70 counted lines'),
                                  'split-message', 'size-no-draft')

    def test_single_size_over_cap_other_plan_text_fails_size_split_plan(self):
        self.inputs['split-plan.json']['unplaced'] = ['h1', 'h2']
        self.write_inputs()
        packet = replace_line(single_packet('size'), 'size', 'fail, 120 counted lines')
        for body in ['not needed: x', 'Separate cart changes.',
                     'not asked: business run only', 'not asked: size run only\nExtra text.']:
            with self.subTest(body=body):
                self.assert_rules(replace_body(packet, 'Split plan', body), 'size-split-plan')

    def test_single_size_over_cap_skips_duplicate_and_unplaced_hunks(self):
        self.inputs['split-plan.json']['unplaced'] = ['h1', 'h1']
        self.write_inputs()
        packet = replace_line(single_packet('size'), 'size', 'fail, 120 counted lines')
        self.assert_pass(replace_body(packet, 'Split plan', 'not asked: size run only'))

    def test_other_packets_not_asked_plan_still_checks_hunks(self):
        for mode in ['size', 'business']:
            with self.subTest(mode=mode):
                packet = replace_body(single_packet(mode), 'Split plan', 'not asked: size run only')
                self.assert_rules(packet, 'hunk-unplaced')

    def test_single_size_over_cap_drafts_still_need_content(self):
        packet = replace_line(single_packet('size'), 'size', 'fail, 120 counted lines')
        packet = replace_body(packet, 'Split plan', 'not asked: size run only')
        self.assert_rules(replace_body(packet, 'Drafts, not sent', ''), 'missing-part')

    def test_rerun_packet_passes(self):
        self.assert_pass(self.rerun_packet())

    def test_generated_all_pass_verdict_passes_rerun_packet_check(self):
        # G10/G15: the generated verdict must name every saved area.
        self.inputs['rules-pages.json']['areas'].append(
            dict(area='grove', page='grove.md', commit='e' * 40, rules=[]))
        self.write_inputs()
        areas = self.root / 'business-areas.json'
        script = Path(__file__).with_name('business_verdict.py')
        # N3: a draft notice must survive the verdict and the rerun packet check.
        for reason, suffix in [('rules kept', ''),
                               ('rules page: draft, not in the repo yet',
                                ', rules page: draft, not in the repo yet')]:
            with self.subTest(reason=reason):
                areas.write_text(json.dumps({'areas': [
                    dict(area='orchard', state='pass', reason=reason),
                    dict(area='grove', state='pass', reason='rules kept')]}), encoding='utf-8')
                run = subprocess.run([sys.executable, '-B', str(script), 'verdict', '--areas', str(areas)],
                                     capture_output=True, text=True, encoding='utf-8', timeout=10)
                self.assertEqual(run.returncode, 0, run.stderr)
                self.assertEqual(run.stdout, 'business: pass, area orchard: every rule kept'
                                 + suffix + '; area grove: every rule kept\n')
                packet = replace_line(self.rerun_packet(), 'business',
                                      run.stdout.strip().removeprefix('business: '))
                self.assert_pass(packet)

    def test_rr6_identity_instruction_produces_valid_rerun_packet(self):
        # G13/G16: apply RR6's identity setting before the packet check.
        mode = Path(__file__).resolve().parents[1] / 'roles/reviewer/modes/business.md'
        rr6 = mode.read_text(encoding='utf-8').split('RR6.', 1)[1].split('\n## ', 1)[0]
        settings = re.findall(r'`(rerun=[^`]+)`', rr6)
        packet = self.rerun_packet().replace('; rerun=yes', '')
        if settings:
            packet = packet.replace('date=2026-10-26', 'date=2026-10-26; ' + settings[0])
        self.assert_pass(packet)

    def test_full_size_counts_missing(self):
        self.assert_rules(replace_line(good_packet(), 'size', 'pass'), 'full-size-counts')

    def test_full_line_forbids_not_asked_and_security_health_not_checked(self):
        for field, word in [('size', 'not asked'), ('business', 'not asked'),
                            ('security', 'not checked'), ('health', 'not checked')]:
            with self.subTest(field=field, word=word):
                self.assert_rules(replace_line(good_packet(), field, word), 'full-line')

    def test_full_business_not_checked_passes(self):
        self.assert_pass(replace_line(good_packet(), 'business', 'not checked: rules page unavailable'))

    def test_full_tests_run_other_commit(self):
        for body in [f'CI run 12 on {"b" * 40}: pass',
                     f'CI run 12 on {HEAD}: pass\nCI run 13 on {"b" * 40}: fail']:
            with self.subTest(body=body):
                self.assert_rules(replace_body(good_packet(), 'Tests run', body), 'full-tests-run')

    # Boundaries: exact CI syntax, 1 or many lines, blank lines, hex case,
    # wrong head, absent body, and each direction of the rerun field link.
    def test_full_tests_run_bad_ci_form(self):
        for body in [f'CI run 12, commit {HEAD}, result pass.', 'CI run 12, result pass.',
                     f'CI run 12.3 on {HEAD}: pass', f'CI run 12 on {HEAD}: passed',
                     f'CI run 12 on {HEAD}: pass.', f'CI run 12 on {HEAD}: pass\nExtra text.']:
            with self.subTest(body=body):
                self.assert_rules(replace_body(good_packet(), 'Tests run', body), 'tests-ci-form')

    def test_full_tests_run_ci_pass_result_passes(self):
        self.assert_pass(replace_body(good_packet(), 'Tests run', f'CI run acme_12-A on {HEAD}: pass'))

    def test_full_tests_run_ci_fail_result_passes(self):
        self.assert_pass(replace_body(good_packet(), 'Tests run', f'CI run 12 on {HEAD}: fail'))

    def test_full_tests_run_multiple_ci_lines_pass(self):
        body = f'CI run 12 on {HEAD}: pass\n\n \t\nCI run orchard_13-A on {HEAD.upper()}: fail'
        self.assert_pass(replace_body(good_packet(), 'Tests run', body))

    def test_full_tests_run_missing(self):
        self.assert_rules(replace_body(good_packet(), 'Tests run', ''), 'missing-part')

    def test_full_tests_run_no_ci_other_head(self):
        packet = replace_body(good_packet(), 'Tests run', 'not checked: no CI run on head ' + 'b' * 40)
        self.assert_rules(packet, 'full-tests-run')

    def test_full_no_ci_on_head_passes(self):
        self.assert_pass(replace_body(good_packet(), 'Tests run', 'not checked: no CI run on head ' + HEAD))

    def test_full_money_invalid(self):
        self.assert_rules(replace_line(good_packet(), 'money', 'no'), 'money-line', 'full-money')

    def test_full_split_plan_not_not_needed(self):
        packet = self.split_packet()
        packet = replace_line(packet, 'money', MONEY_NO).replace('mode=business', 'mode=full')
        for field in ['size', 'security', 'health']:
            original = next(line for line in good_packet().splitlines() if line.startswith(field + ':'))
            packet = replace_line(packet, field, original.split(': ', 1)[1])
        self.assert_rules(packet, 'full-split-plan')

    def test_override_cap_line_missing_cross_size_fail(self):
        self.assert_rules(self.override_packet().replace(CAP_LINE + '\n', ''), 'cross-size-fail')

    def test_override_size_not_fail(self):
        self.assert_rules(CAP_LINE + '\n' + good_packet(), 'override-size-fail')

    def test_override_size_counts_missing(self):
        self.assert_rules(replace_line(self.override_packet(), 'size', 'fail'), 'full-size-counts')

    def test_override_cap_line_after_identity(self):
        self.assert_rules(replace_line(good_packet(), 'size', 'fail, 120 counted lines') + CAP_LINE + '\n',
                          'override-cap-line', 'cross-size-fail')

    def test_override_not_checked_over_cap(self):
        self.assert_rules(replace_line(self.override_packet(), 'business', STOP), 'override-not-checked')

    def test_short_line_money_not_checked_missing(self):
        self.assert_rules(replace_line(self.short_packet(), 'money', MONEY_NO), 'short-line')

    def test_short_line_tests_run_not_checked_missing(self):
        self.assert_rules(replace_body(self.short_packet(), 'Tests run', 'CI run 12'), 'short-line')

    def test_short_line_known_risks_not_checked_missing(self):
        self.assert_rules(replace_body(self.short_packet(), 'Known risks', 'none'), 'short-line')

    def test_short_behaviour_fewer_lines_than_groups(self):
        self.assert_rules(replace_body(self.short_packet(), 'Behaviour changed', 'orchard changes.'),
                          'short-behaviour')

    def test_short_size_counts_missing(self):
        self.assert_rules(replace_line(self.short_packet(), 'size', 'fail'), 'short-size-counts')

    def test_short_split_plan_missing(self):
        self.assert_rules(replace_body(self.short_packet(), 'Split plan', ''),
                          'missing-part', 'split-field', 'short-split-plan')

    def test_short_draft_missing(self):
        self.assert_rules(replace_body(self.short_packet(), 'Drafts, not sent', ''),
                          'missing-part', 'split-message', 'short-draft')

    def test_single_mode_line_asked_word_outside_table(self):
        self.assert_rules(replace_line(single_packet('health'), 'health', 'not checked'),
                          'single-mode-line')

    def test_single_mode_line_other_mode_not_not_asked(self):
        self.assert_rules(replace_line(single_packet(), 'health', 'pass'), 'single-mode-line')

    def test_single_size_non_size_has_counts(self):
        self.assert_rules(replace_line(single_packet(), 'size', 'pass, 120 counted lines'), 'single-size')

    def test_single_size_asked_counts_missing(self):
        packet = replace_line(single_packet('size'), 'size', 'fail')
        self.assert_rules(replace_body(packet, 'Split plan', 'not asked: size run only'), 'single-size')

    def test_single_money_breaks_q2a(self):
        self.assert_rules(replace_line(single_packet(), 'money', MONEY_NO), 'single-money')

    def test_single_tests_run_outside_forms(self):
        self.assert_rules(replace_body(single_packet(), 'Tests run', 'not asked: health run only'),
                          'single-tests-run', 'tests-ci-form')

    def test_single_tests_run_bad_ci_form(self):
        packet = replace_body(single_packet(), 'Tests run', f'CI run 12, commit {HEAD}, result pass.')
        self.assert_rules(packet, 'tests-ci-form')

    def test_single_tests_run_other_commit(self):
        packet = replace_body(single_packet(), 'Tests run', f'CI run 12 on {"b" * 40}: pass')
        self.assert_rules(packet, 'single-tests-run')

    def test_single_tests_run_empty_body(self):
        self.assert_rules(replace_body(single_packet(), 'Tests run', ''), 'missing-part')

    def test_single_tests_run_normal_o17_passes(self):
        self.assert_pass(single_packet())

    def test_single_tests_run_not_asked_o17_passes(self):
        self.assert_pass(replace_body(single_packet(), 'Tests run', 'not asked: business run only'))

    def test_single_tests_run_no_ci_on_head_passes(self):
        self.assert_pass(replace_body(single_packet(), 'Tests run', 'not checked: no CI run on head ' + HEAD))

    def test_single_security_money_forms_pass(self):
        for money in [MONEY_NO, MONEY_YES, 'not checked: files unavailable']:
            with self.subTest(money=money):
                self.assert_pass(replace_line(single_packet('security'), 'money', money))

    def test_single_health_and_size_without_security_record_pass(self):
        self.inputs['check-record.json']['entries'] = self.inputs['check-record.json']['entries'][-2:]
        self.write_inputs()
        for mode in ['health', 'size']:
            with self.subTest(mode=mode):
                self.assert_pass(single_packet(mode))

    def test_cross_size_fail_other_lines_checked(self):
        self.assert_rules(replace_line(good_packet(), 'size', 'fail, 120 counted lines'), 'cross-size-fail')

    def test_rerun_line_missing_with_business_rerun_claim(self):
        packet = replace_line(good_packet(), 'business', 'pass, business rerun rebuilt orchard')
        self.assert_rules(packet, 'rerun-line')

    def test_rerun_yes_without_line_fails_rerun_field(self):
        packet = good_packet().replace('date=2026-10-26', 'date=2026-10-26; rerun=yes')
        self.assert_rules(packet, 'rerun-field')

    def test_rerun_line_without_field_fails_rerun_field(self):
        self.assert_rules(self.rerun_packet().replace('; rerun=yes', ''), 'rerun-field')

    def test_rerun_no_fails_rerun_field(self):
        for packet in [good_packet(), self.rerun_packet().replace('; rerun=yes', '')]:
            with self.subTest(packet=packet):
                packet = packet.replace('date=2026-10-26', 'date=2026-10-26; rerun=no')
                self.assert_rules(packet, 'rerun-field')

    def test_rerun_other_values_fail_rerun_field(self):
        for setting in ['', 'YES', 'true']:
            with self.subTest(setting=setting):
                packet = self.rerun_packet().replace('rerun=yes', 'rerun=' + setting)
                self.assert_rules(packet, 'rerun-field')

    def test_rerun_line_bad_shape_date_head_or_area(self):
        packet = self.rerun_packet()
        line = packet.splitlines()[0]
        for bad in [line + ' extra', line.replace('2026-10-26', '2026-02-30'),
                    line.replace(HEAD, 'b' * 40), line.replace('orchard', 'grove')]:
            with self.subTest(line=bad):
                self.assert_rules(packet.replace(line, bad), 'rerun-line')

    def test_rerun_business_missing_touched_area(self):
        packet = self.rerun_packet()
        self.inputs['rules-pages.json']['areas'].append(dict(area='grove', page='grove.md',
                                                           commit='e' * 40, rules=[]))
        self.write_inputs()
        self.assert_rules(packet, 'rerun-business')

    def test_rerun_business_area_case_matters(self):
        self.assert_rules(replace_line(self.rerun_packet(), 'business', 'pass, Orchard rebuilt'),
                          'rerun-business')

    def test_rerun_security_pass_with_incomplete_record(self):
        self.inputs['check-record.json']['entries'][0]['word'] = 'incomplete'
        self.write_inputs()
        self.assert_rules(self.rerun_packet(), 'rerun-security')

    def test_rerun_security_fail_turned_incomplete(self):
        self.inputs['check-record.json']['entries'][0]['word'] = 'must fix'
        self.write_inputs()
        self.assert_rules(replace_line(self.rerun_packet(), 'security', 'incomplete'),
                          'security-line', 'rerun-security')

    def test_rerun_security_not_asked_or_not_checked_stays(self):
        self.inputs['check-record.json']['entries'][0]['word'] = 'incomplete'
        self.write_inputs()
        packet = single_packet().replace('business: incomplete', 'business: incomplete, orchard')
        packet = packet.replace('date=2026-10-26', 'date=2026-10-26; rerun=yes')
        self.assert_pass(f'business rerun for orchard, 2026-10-26, head {HEAD}\n' + packet)
        packet = replace_line(self.short_packet(), 'business', STOP + ', orchard')
        packet = packet.replace('date=2026-10-26', 'date=2026-10-26; rerun=yes')
        self.assert_pass(f'business rerun for orchard, 2026-10-26, head {HEAD}\n' + packet)

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

    def assert_rule(self, packet, rule, message, *extra_lines):
        run = self.check_text(packet)
        self.assertEqual(run.returncode, FAILED_SHAPE, run.stderr + run.stdout)
        self.assertEqual(run.stdout.splitlines(), [f'RULE {rule}: {message}', *extra_lines])
        self.assertEqual(run.stderr, '')

    def test_full_packet_passes(self):
        self.assert_pass(good_packet())

    def test_override_packet_passes(self):
        self.assert_pass(self.override_packet())

    def test_headings_missing_duplicate_or_out_of_order(self):
        packet = good_packet()
        swapped = packet.replace('## Tests run', '## PLACEHOLDER').replace(
            '## Files that matter most', '## Tests run').replace(
            '## PLACEHOLDER', '## Files that matter most')
        swapped = replace_body(swapped, 'Tests run', f'CI run 12 on {HEAD}: pass')
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
                        packet = good_packet().replace(line, field + ': ' + word + ending)
                        self.assertEqual(bad_verdicts(packet.splitlines()), [])

    def test_money_line_rejects_bad_or_missing_forms(self):
        for money in ['', 'does not apply', 'not checked:',
                      MONEY_YES.replace('cart.py', ''), MONEY_YES.replace('Not done', 'Done')]:
            with self.subTest(money=money):
                bad = good_packet().replace('money: ' + MONEY_NO,
                                             'money: ' + money if money else '')
                self.assert_rule(bad, 'money-line', 'missing or invalid money line',
                                 'RULE full-money: missing or invalid money line')

    def test_money_forms_pass(self):
        for money in [MONEY_NO, MONEY_YES, 'not checked: The cart files were unavailable.']:
            with self.subTest(money=money):
                self.assert_pass(good_packet().replace(MONEY_NO, money))

    def test_missing_part_names_fields_with_no_content(self):
        self.inputs['split-plan.json']['unplaced'] = ['h1', 'h2']
        self.write_inputs()
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
        self.inputs['split-plan.json']['unplaced'] = ['h1', 'h2']
        self.write_inputs()
        self.assert_pass(replace_body(single_packet(), 'Split plan', 'Separate cart and account changes.'))

    def test_split_plan_not_needed_requires_a_reason_g6(self):
        # Boundaries: empty, spaces, tabs, newlines, and a real reason.
        for body in ['not needed:', 'not needed:   ', 'not needed:\t',
                     'not needed:\n \t']:
            with self.subTest(body=body):
                self.assert_rule(replace_body(good_packet(), 'Split plan', body),
                                 'missing-part', 'missing content: Split plan')
        self.assert_pass(replace_body(good_packet(), 'Split plan',
                                     'not needed: The change fits together.'))

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

    def test_unknown_placeholder_reasons_are_unmatched_g7(self):
        # Boundaries: empty answers, case, padding, and bare or labelled markers.
        for reason, labels in [('unknown', 'tax'), ('not checked', 'tax'),
                               ('not checked:', 'tax'), ('none', 'tax'),
                               (' UNKNOWN \t', 'tax'), ('___', 'bare ___, tax'),
                               ('___ (reason)', 'tax')]:
            with self.subTest(reason=reason):
                packet = replace_body(good_packet(), 'Not checked', '___ (tax): ' + reason)
                self.assert_rule(packet, 'unknown-unmatched', 'unmatched unknowns: ' + labels)
        self.assert_pass(replace_body(good_packet(), 'Not checked',
                                     '___ (tax): The owner has not supplied the tax rule.'))

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
        self.assert_rule(self.override_packet() + 'It was not reviewed past size\n',
                         'cap-contradiction', 'cap review contradicts size stop')
        self.assert_pass(good_packet() + 'It was not reviewed past size\n')

    def test_multiple_rules_each_print_once_in_rule_order(self):
        packet = good_packet() + 'safe to merge\nsafe to merge\nOverall: pass\n'
        run = self.check_text(packet)
        self.assertEqual(run.returncode, FAILED_SHAPE)
        self.assertEqual(run.stdout.splitlines(), ['RULE safe-to-merge: contains safe to merge',
                                                  'RULE overall-line: line starts with overall or ready'])
        self.assertEqual(run.stderr, '')

    # Boundaries: absent, blank, wrong types, 1 or many ids, repeat placements,
    # optional split, exact group order, ignored kinds, and unknown hunk ids.
    def test_bad_packet_check_record_id(self):
        for mode in ['full', 'security']:
            with self.subTest(mode=mode):
                self.inputs['check-record.json']['entries'] = [
                    entry for entry in good_inputs()['check-record.json']['entries']
                    if entry['id'] not in ['S1', 'S22', 'L5']]
                self.write_inputs()
                packet = good_packet() if mode == 'full' else single_packet(mode)
                self.assert_rule(packet,
                                 'check-record-id', 'missing ids: S1, S22, L5')

    def test_bad_packet_check_record_tool(self):
        for bad in [None, '', ' \t', 7]:
            with self.subTest(tool_result=bad):
                self.inputs['check-record.json']['entries'][0]['tool_result'] = bad
                self.write_inputs()
                self.assert_rule(good_packet(), 'check-record-tool', 'missing tool_result: S1')

    def test_bad_packet_check_record_reading(self):
        del self.inputs['check-record.json']['entries'][0]['reading_result']
        self.write_inputs()
        self.assert_rule(good_packet(), 'check-record-reading', 'missing reading_result: S1')

    def test_bad_packet_check_record_area(self):
        self.inputs['check-record.json']['entries'][-1]['area'] = ' '
        self.write_inputs()
        self.assert_rule(good_packet(), 'check-record-area', 'missing area: RB')

    def test_bad_packet_rule_base_read(self):
        del self.inputs['check-record.json']['entries'][-1]['base_read']
        self.write_inputs()
        self.assert_rule(good_packet(), 'rule-base-read', 'missing base_read: RB')

    def test_bad_packet_rule_head_read(self):
        self.inputs['check-record.json']['entries'][-1]['head_read'] = ''
        self.write_inputs()
        self.assert_rule(good_packet(), 'rule-head-read', 'missing head_read: RB')

    def test_bad_packet_rule_entry_missing(self):
        self.inputs['rules-pages.json']['areas'].append(
            dict(area='grove', page='grove.md', commit='e' * 40,
                 rules=[{'id': 'R3', 'status': 'active'}, {'id': 'R4', 'status': 'retired'}]))
        self.write_inputs()
        self.assert_rule(good_packet(), 'rule-entry-missing', 'missing rule entries: R3, R4')

    def test_bad_packet_security_line(self):
        self.inputs['check-record.json']['entries'][0]['word'] = 'must fix'
        self.write_inputs()
        self.assert_rule(good_packet(), 'security-line', 'security must fix requires fail')

    def test_bad_packet_hunk_unplaced(self):
        packet = self.split_packet()
        self.inputs['files.json']['files'][0]['hunks'].append({'id': 'h3', 'counted_lines': 0})
        self.write_inputs()
        self.assert_rule(packet, 'hunk-unplaced', 'unplaced hunks: h3')

    def test_bad_packet_hunk_duplicate(self):
        packet = self.split_packet()
        for unplaced in [['h1'], ['h1', 'h1']]:
            with self.subTest(unplaced=unplaced):
                self.inputs['split-plan.json']['unplaced'] = unplaced
                self.write_inputs()
                self.assert_rule(packet, 'hunk-duplicate', 'duplicate hunks: h1')

    def test_bad_packet_hunk_counts(self):
        self.assert_rule(good_packet().replace('120 counted lines', '121 counted lines'),
                         'hunk-counts', 'counted lines differ: packet 121, hunks 120')

    def test_bad_packet_split_field(self):
        packet = self.split_packet()
        for body in ['group: orchard, 71 counted lines\ngroup: grove, 50 counted lines',
                     'group: grove, 50 counted lines\ngroup: orchard, 70 counted lines',
                     'No groups listed.']:
            with self.subTest(body=body):
                self.assert_rule(replace_body(packet, 'Split plan', body),
                                 'split-field', 'group lines differ from split-plan.json')

    def test_bad_packet_split_message(self):
        packet = self.split_packet()
        self.assert_rule(replace_body(packet, 'Drafts, not sent', 'Draft: Ask about orchard.'),
                         'split-message', 'group lines differ from split-plan.json')

    def test_security_fail_with_must_fix_passes(self):
        self.inputs['check-record.json']['entries'][0]['word'] = 'must fix'
        self.write_inputs()
        self.assert_pass(good_packet().replace('security: pass', 'security: fail, 1 must fix'))

    def test_required_ids_apply_without_built_in_security_ids(self):
        self.inputs['check-record.json']['entries'] = self.inputs['check-record.json']['entries'][-2:]
        self.write_inputs()
        packet = single_packet()
        self.assert_pass(packet)
        self.inputs['check-record.json']['required_ids'].append('C1')
        self.write_inputs()
        self.assert_rule(packet, 'check-record-id', 'missing ids: C1')

    def test_split_groups_bullets_and_unknown_hunks_pass(self):
        packet = self.split_packet()
        self.inputs['split-plan.json']['groups'][0]['hunks'].append('absent')
        self.write_inputs()
        self.assert_pass(packet.replace('group: orchard', '- group: orchard').replace(
            'group: grove', '* group: grove'))

    def test_unplaced_hunks_and_ignored_file_kinds_pass(self):
        packet = self.split_packet()
        self.inputs['split-plan.json']['groups'][1]['hunks'] = []
        self.inputs['split-plan.json']['unplaced'] = ['h2']
        for kind in ['test', 'lock', 'generated', 'docs']:
            self.inputs['files.json']['files'].append(
                dict(path=kind + '.py', old_path='', status='added', kind=kind,
                     counted_lines=900, hunks=[{'id': kind, 'counted_lines': 900}]))
        self.write_inputs()
        self.assert_pass(packet.replace('group: grove, 50', 'group: grove, 0'))

    def test_hunk_counts_skips_size_without_count(self):
        self.assert_pass(single_packet())

    def test_json_input_errors_precede_packet_rules(self):
        for filename in self.inputs:
            for contents in [None, b'', b' \t\r\n', b'{', b'[]', b'null', b'\xff']:
                with self.subTest(filename=filename, contents=contents):
                    self.write_inputs()
                    target = self.packet / filename
                    if contents is None:
                        target.unlink()
                    else:
                        target.write_bytes(contents)
                    self.path.write_text(good_packet() + 'safe to merge\n', encoding='utf-8')
                    run = self.run_check(self.packet)
                    self.assertEqual(run.returncode, 2, run.stdout + run.stderr)
                    self.assertEqual(run.stdout, '')
                    self.assertEqual(len(run.stderr.splitlines()), 1, run.stderr)
                    self.assertTrue(run.stderr.startswith('packet_check: '), run.stderr)
                    self.assertIn(filename, run.stderr)

    def test_json_input_paths_must_be_files(self):
        for filename in self.inputs:
            with self.subTest(filename=filename):
                target = self.packet / filename
                target.unlink()
                target.mkdir()
                self.assert_bad_input(self.packet)
                target.rmdir()
                self.write_inputs()

    def test_json_lists_and_object_entries_require_shapes(self):
        cases = [('check-record.json', 'required_ids'), ('check-record.json', 'entries'),
                 ('files.json', 'files'), ('split-plan.json', 'groups'),
                 ('split-plan.json', 'first_group_parts'), ('split-plan.json', 'unplaced'),
                 ('rules-pages.json', 'areas')]
        for filename, key in cases:
            for bad in [None, {}]:
                with self.subTest(filename=filename, key=key, bad=bad):
                    self.inputs = good_inputs()
                    self.inputs[filename][key] = bad
                    self.write_inputs()
                    self.assert_bad_input(self.packet)
        for filename, key in [('check-record.json', 'entries'), ('files.json', 'files'),
                              ('split-plan.json', 'groups'), ('rules-pages.json', 'areas')]:
            with self.subTest(filename=filename, key=key):
                self.inputs = good_inputs()
                self.inputs[filename][key] = ['bad']
                self.write_inputs()
                self.assert_bad_input(self.packet)

    # G8 boundaries: numeric text, float, bool, null, list, object;
    # file and hunk counts, hunk ids, grouped ids, and unplaced ids.
    def test_saved_counts_require_integers(self):
        for location in ['files[0]', 'files[0].hunks[0]']:
            for bad in ['70', 70.0, True, None, [], {}]:
                with self.subTest(location=location, bad=bad):
                    self.inputs = good_inputs()
                    file = self.inputs['files.json']['files'][0]
                    target = file if location == 'files[0]' else file['hunks'][0]
                    target['counted_lines'] = bad
                    self.write_inputs()
                    run = self.run_check(self.packet)
                    self.assertEqual(run.returncode, 2, run.stdout + run.stderr)
                    self.assertEqual(run.stdout, '')
                    self.assertEqual(run.stderr.splitlines(), [
                        f'packet_check: files.json.{location}.counted_lines must be int'])

    def test_saved_hunk_ids_require_strings(self):
        cases = [('files.json', 'files[0].hunks[0].id'),
                 ('split-plan.json', 'groups[0].hunks[0]'),
                 ('split-plan.json', 'unplaced[0]')]
        for filename, location in cases:
            for bad in [{}, [], None, 7, True]:
                with self.subTest(filename=filename, location=location, bad=bad):
                    self.inputs = good_inputs()
                    packet = self.split_packet()
                    if filename == 'files.json':
                        self.inputs[filename]['files'][0]['hunks'][0]['id'] = bad
                    elif location.startswith('groups'):
                        self.inputs[filename]['groups'][0]['hunks'] = [bad]
                    else:
                        self.inputs[filename]['unplaced'] = [bad]
                    self.write_inputs()
                    run = self.check_text(packet)
                    self.assertEqual(run.returncode, 2, run.stdout + run.stderr)
                    self.assertEqual(run.stdout, '')
                    self.assertEqual(run.stderr.splitlines(), [
                        f'packet_check: {filename}.{location} must be str'])

    def test_nested_json_lists_and_object_entries_require_shapes(self):
        for key in ['hunks', 'rules', 'entry_points']:
            for bad in [None, {}, [None]]:
                if key == 'entry_points' and bad == [None]:
                    continue
                with self.subTest(key=key, bad=bad):
                    self.inputs = good_inputs()
                    self.split_packet()
                    if key == 'hunks':
                        self.inputs['files.json']['files'][0][key] = bad
                    elif key == 'rules':
                        self.inputs['rules-pages.json']['areas'][0][key] = bad
                    else:
                        self.inputs['split-plan.json']['groups'][0][key] = bad
                    self.write_inputs()
                    self.assert_bad_input(self.packet)

    def test_missing_entry_fields_are_rule_failures(self):
        for filename, key, field in [('check-record.json', 'entries', 'reason'),
                                     ('files.json', 'files', 'path'),
                                     ('rules-pages.json', 'areas', 'page')]:
            with self.subTest(filename=filename, field=field):
                self.inputs = good_inputs()
                del self.inputs[filename][key][0][field]
                self.write_inputs()
                self.assert_rule(good_packet(), 'input-fields',
                                 f'missing fields: {filename}.{key}[0].{field}')

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
