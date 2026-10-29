"""Check packet.md text with Python 3.12 and the standard library.

Usage: python tools/packet_check.py <packet folder>
Exit 0 prints packet_check: pass. Exit 1 prints 1 RULE line per failed
rule. Exit 2 prints 1 packet_check: error line on stderr only.

A packet contains a line '# Review packet'. Before the identity it may
contain: reviewed over the cap, on Ahmed's word
The identity line has semicolon separated keys, for example:
identity: repo=acme/shop; pr=101; mode=full; head=<40 hex>; base=<40 hex>;
default=main@<40 hex>; date=2026-10-26
Write the identity on 1 line. Modes: full, size, business, security, health.
Verdict lines start size:, business:, security:, health:. Size allows pass,
fail, not asked. The others also allow incomplete and not checked.
Money uses 1 of these exact forms (replace placeholders with real text):
money: yes, files <files>. Needs the separate Opus review before merge. Not done by this review.
money: no money code found by reading; not proof
money: not checked: <reason>

Then include these '## ' headings exactly once, in this order:
Behaviour changed, Files that matter most, Tests run, Not checked,
Known risks, Pointers, Split plan, Drafts, not sent.
Each body ends at the next '## ' heading. Every body needs content.
Known risks and Pointers allow none. Other bodies need more than none or
an unknown without a reason. Split plan needs a plan or not needed: text.
Write unknowns as ___ (label). Each label outside Not checked needs a
Not checked line containing ___ (label): <reason>. Bare ___ is invalid.
The phrases safe to merge and lines starting overall or ready are invalid.
The cap line conflicts with the exact text It was not reviewed past size.
The packet folder also needs 4 JSON objects, validated before rules run:
check-record.json: required_ids, entries. Each entry has id, mode, area,
kind, tool_result, reading_result, word, reason, base_read, head_read.
files.json: files. Each file has path, old_path, status, kind,
counted_lines, hunks. Each hunk has id, counted_lines.
split-plan.json: groups, first_group_parts, unplaced. Each group has
name, entry_points, estimate, hunks (hunk ids).
rules-pages.json: areas. Each area has area, page, commit, rules.
Each rule has id, status. All collection fields are lists.
Counted lines must be integers. Hunk ids must be strings.
Bad file contents or list/object shapes exit 2 and name the file.
Missing entry fields exit 1, using input-fields if no other rule fails.
Full and security identity modes require S1 through S22, L1, L5 plus required_ids.
Record checks precede hunk checks and exact ordered group line comparisons.
Only counted file hunks contribute lines. Unknown hunk ids contribute 0.
Pieces use f1h1:L1-L4, with both ends included. Counted hunk pieces must
cover every changed line once. Operations such as f1op allow no range.
Hunk placement checks skip not needed and size mode fail with not asked.

Packet types add rules to these common checks. Full packets need size
counts, Tests run tied to the head, a money form above, and not needed
in Split plan. Security and health cannot say not checked in full packets.
An override needs the exact cap line above the identity, size fail with
counts, and no verdict saying not checked because of the cap.
Short packets have size fail with counts and the cap stop text in the
other verdicts, money, and fields except Behaviour changed, Split plan,
and Drafts, not sent. Behaviour changed needs ordered group summary lines and the exact cap stop Translations line.
The split plan and draft must contain group lines.
Single mode packets mark other modes not asked: <mode> run only.
Only an asked size line has counts. A size fail also allows the cap stop
text in the other verdicts. Money outside security says
not checked: money not looked at, <mode> run only. Tests run also allows
not asked: <mode> run only. Size fail without cap stop verdicts requires
the cap line unless mode is size.
In size mode, fail needs Split plan exactly not asked: size run only.
That case forbids group lines in Split plan and Drafts, not sent.
In full and single mode packets, tests-ci-form requires each non blank
Tests run line to say CI run <id> on <40 hex>: <pass|fail>. The id uses
letters A to Z or a to z, digits, underscores, or hyphens. Hex may use
either case. The exact not checked: no CI run on head <sha> form is also
allowed, as is not asked: <mode> run only in single mode packets.
Missing content stays with missing-part. Short packets skip tests-ci-form.
The existing full-tests-run and single-tests-run rules reject any 40 hex
commit other than the head and require the no CI run form to name that head.
The rerun-field rule requires identity rerun=yes exactly when a line
starting business rerun exists. Other rerun values are invalid.
A business rerun line needs a known area, an ISO date, and the head.
A business line claiming business rerun also requires that line.
Rerun business verdicts name every rules page area. Security must fix
still requires fail; an incomplete security entry cannot leave pass.
"""

import json
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

FAILED_SHAPE = 1
HEADINGS = ['Behaviour changed', 'Files that matter most', 'Tests run',
            'Not checked', 'Known risks', 'Pointers', 'Split plan', 'Drafts, not sent']
HEX = r'[0-9a-fA-F]{40}'
IDENTITY = {'repo': r'[^/\s;]+/[^/\s;]+', 'pr': r'[0-9]+',
            'mode': r'(?:full|size|business|security|health)',
            'head': HEX, 'base': HEX, 'default': r'[^\s;@]+@' + HEX,
            'date': r'[0-9]{4}-[0-9]{2}-[0-9]{2}'}
CAP_LINE = "reviewed over the cap, on Ahmed's word"
CAP_STOP = 'not checked: PR over the cap, split it first'
GROUP_LINE = r'^[ \t]*(?:[-*] )?group: (.+), ([0-9]+) counted lines[ \t]*$'
UNKNOWN = re.compile(r'___[ \t]*\(([^()\n]+)\)')
NO_REASON = {'___', 'unknown', 'not checked', 'not checked:'}
MONEY_END = '. Needs the separate Opus review before merge. Not done by this review.'
INPUT_SHAPES = {
    'check-record.json': {'required_ids': [], 'entries': dict.fromkeys(
        'id mode area kind tool_result reading_result word reason base_read head_read'.split())},
    'files.json': {'files': {**dict.fromkeys('path old_path status kind'.split()),
                             'counted_lines': int, 'hunks': {'id': str, 'counted_lines': int}}},
    'split-plan.json': {'groups': {**dict.fromkeys(['name', 'estimate']),
                                  'entry_points': [], 'hunks': [str]},
                        'first_group_parts': [], 'unplaced': [str]},
    'rules-pages.json': {'areas': {**dict.fromkeys(['area', 'page', 'commit']),
                                  'rules': dict.fromkeys(['id', 'status'])}}}


def input_type(contents, schema, location):
    if isinstance(schema, type):
        if type(contents) is not schema:
            raise ValueError(location + ' must be ' + schema.__name__)
    elif not isinstance(contents, list):
        raise ValueError(location + ' must be a list')
    elif isinstance(schema, list) and schema:
        for index, entry in enumerate(contents):
            input_type(entry, schema[0], f'{location}[{index}]')


def input_fields(document, schema, location):
    if not isinstance(document, dict):
        raise ValueError(location + ' must be an object')
    missing = [location + '.' + field for field in schema if field not in document]
    if missing and location.endswith('.json'):
        raise ValueError(location + ' has missing lists')
    for field, children in schema.items():
        if children is None or field not in document:
            continue
        input_type(document[field], children, location + '.' + field)
        if isinstance(children, dict):
            for index, entry in enumerate(document[field]):
                missing.extend(input_fields(entry, children, f'{location}.{field}[{index}]'))
    return missing


def read_inputs(folder):
    inputs, missing = {}, []
    for filename, schema in INPUT_SHAPES.items():
        path = folder / filename
        if not path.is_file():
            raise ValueError(filename + ' is missing or not a file')
        try:
            document = json.loads(path.read_text(encoding='utf-8'))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise ValueError(filename + ' is empty, unreadable, or invalid JSON') from error
        missing.extend(input_fields(document, schema, filename))
        inputs[filename] = document
    return inputs, missing


def record_failures(lines, inputs):
    record = inputs['check-record.json']
    entries = record['entries']
    ids = [entry.get('id') for entry in entries]
    required = list(record['required_ids'])
    if any(re.search(r'(?:^|;)\s*mode=(?:full|security)\s*(?:;|$)', identity)
           for identity in line_values(lines, 'identity')):
        # The 24 security checks: S1 to S22, plus L1 and L5.
        required += [f'S{number}' for number in range(1, 23)] + ['L1', 'L5']
    checks = [('check-record-id', 'missing ids', [key for key in required if key not in ids])]
    business = [entry for entry in entries if entry.get('mode') == 'business']
    rules = [entry for entry in entries if entry.get('kind') == 'rule']
    for rule, field, selected in [('check-record-tool', 'tool_result', entries),
                                  ('check-record-reading', 'reading_result', entries),
                                  ('check-record-area', 'area', business),
                                  ('rule-base-read', 'base_read', rules),
                                  ('rule-head-read', 'head_read', rules)]:
        checks.append((rule, 'missing ' + field, [entry.get('id', '<missing>') for entry in selected
                       if not isinstance(entry.get(field), str) or not entry[field].strip()]))
    page_ids = [rule.get('id', '<missing>') for area in inputs['rules-pages.json']['areas']
                for rule in area.get('rules', [])]
    checks.append(('rule-entry-missing', 'missing rule entries', [key for key in page_ids if key not in ids]))
    failures = [(rule, message + ': ' + ', '.join(dict.fromkeys(map(str, keys))))
                for rule, message, keys in checks if keys]
    security = line_values(lines, 'security')
    if any(entry.get('mode') == 'security' and entry.get('word') == 'must fix' for entry in entries):
        if not security or any(not re.match(r'fail\b', verdict) for verdict in security):
            failures.append(('security-line', 'security must fix requires fail'))
    return failures


def parse_piece(piece):
    # Cases: whole, range, zero, reversed, malformed, operation with range.
    if ':' not in piece:
        return piece, 1, None
    match = re.fullmatch(r'(f[0-9]+h[0-9]+):L([0-9]+)-L([0-9]+)', piece)
    if not match or not 1 <= int(match[2]) <= int(match[3]):
        raise ValueError('bad hunk range: ' + piece)
    return match[1], int(match[2]), int(match[3])


def piece_coverage(counts, placements):
    sizes, spans, failures = {}, {key: [] for key in counts}, []
    duplicates = [key for key, count in Counter(placements).items()
                  if count > 1 and ':' not in key]
    for piece in placements:
        try:
            key, start, end = parse_piece(piece)
            if key in counts and end is not None and end > counts[key]:
                raise ValueError('hunk range exceeds its lines: ' + piece)
        except ValueError as error:
            failures.append(('hunk-range', str(error)))
            sizes[piece] = 0
            continue
        sizes[piece] = (counts[key] if end is None else end - start + 1) if key in counts else 0
        if key in spans:
            spans[key].append((start, counts[key] if end is None else end))
    missing = []
    for key, ranges in spans.items():
        cursor, gap = 1, not ranges
        for start, end in sorted(ranges):
            gap |= start > cursor
            if start < cursor:
                duplicates.append(key)
            cursor = max(cursor, end + 1)
        if gap or cursor <= counts[key]:
            missing.append(key)
    for rule, label, keys in [('hunk-unplaced', 'unplaced', missing),
                               ('hunk-duplicate', 'duplicate', duplicates)]:
        if keys:
            failures.append((rule, label + ' hunks: ' + ', '.join(map(str, dict.fromkeys(keys)))))
    return sizes, failures


def split_failures(lines, inputs):
    plan = inputs['split-plan.json']
    hunks = [hunk for file in inputs['files.json']['files'] if file.get('kind') == 'counted'
             for hunk in file.get('hunks', [])]
    counts = {hunk.get('id'): hunk.get('counted_lines', 0) for hunk in hunks}
    groups = plan['groups']
    placements = [hunk for group in groups for hunk in group.get('hunks', [])] + plan['unplaced']
    sizes, coverage_failures = piece_coverage(counts, placements)
    bodies = field_bodies(lines)
    failures = []
    size_over_cap = (any(re.search(r'(?:^|;)\s*mode=size\s*(?:;|$)', identity)
                         for identity in line_values(lines, 'identity')[:1]) and
                     any(verdict_word(verdict) == 'fail' for verdict in line_values(lines, 'size')[:1]))
    split_body = bodies.get('Split plan', '')
    if not (split_body.startswith('not needed') or
            (size_over_cap and split_body.startswith('not asked'))):
        failures.extend(coverage_failures)
    size = re.search(r'\b([0-9]+)\s+counted lines\b', ' '.join(line_values(lines, 'size')[:1]))
    total = sum(hunk.get('counted_lines', 0) for hunk in hunks)
    if size and int(size[1]) != total:
        failures.append(('hunk-counts', f'counted lines differ: packet {int(size[1])}, hunks {total}'))
    expected = [(group.get('name'), sum(sizes[key] for key in group.get('hunks', [])))
                for group in groups]
    for rule, heading in [('split-field', 'Split plan'), ('split-message', 'Drafts, not sent')]:
        actual = [(match[1], int(match[2])) for match in re.finditer(
            GROUP_LINE, bodies.get(heading, ''), re.MULTILINE)]
        if actual != expected:
            failures.append((rule, 'group lines differ from split-plan.json'))
    return failures


def line_values(lines, field):
    return [line[len(field) + 1:].strip() for line in lines if line.startswith(field + ':')]


def field_bodies(lines):
    bodies = {}
    heading = None
    for line in lines:
        if line.startswith('## '):
            heading = line[3:]
            bodies.setdefault(heading, [])
        elif heading is not None:
            bodies[heading].append(line)
    return {name: '\n'.join(body).strip() for name, body in bodies.items()}


def bad_identity_keys(lines):
    identities = line_values(lines, 'identity')
    pairs = identities[0].split(';') if identities else []
    fields = dict(pair.strip().split('=', 1) for pair in pairs if '=' in pair)
    return [key for key, pattern in IDENTITY.items()
            if not re.fullmatch(pattern, fields.get(key, '').strip())]


def bad_verdicts(lines):
    bad = []
    for field in ['size', 'business', 'security', 'health']:
        words = ['pass', 'fail', 'not asked']
        if field != 'size':
            words += ['incomplete', 'not checked']
        pattern = '(?:' + '|'.join(sorted(words, key=len, reverse=True)) + r')(?=$|[,:;. ])'
        verdicts = line_values(lines, field)
        if not verdicts or any(not re.match(pattern, verdict) for verdict in verdicts):
            bad.append(field)
    return bad


def valid_money(money):
    if money == 'no money code found by reading; not proof':
        return True
    if money.startswith('not checked:'):
        return bool(money[len('not checked:'):].strip())
    if money.startswith('yes, files ') and money.endswith(MONEY_END):
        return bool(money[len('yes, files '):-len(MONEY_END)].strip())
    return False


def missing_parts(bodies):
    missing = []
    for heading in HEADINGS:
        if heading not in bodies:
            continue
        body = bodies[heading]
        if heading == 'Not checked' and not body:
            continue
        only_placeholders = all(line.strip().lower() in {'none', *NO_REASON}
                                for line in body.splitlines() if line.strip())
        empty_split_reason = (heading == 'Split plan' and body.startswith('not needed:')
                              and not body[len('not needed:'):].strip())
        if not body or empty_split_reason or (heading not in HEADINGS[4:6] and only_placeholders):
            missing.append(heading)
    return missing


def unmatched_unknowns(lines):
    # Cases: bare, labelled, repeated, matching label, absent, blank or placeholder reason.
    explained = set()
    outside = []
    bare = False
    heading = None
    for line in lines:
        if line.startswith('## '):
            heading = line[3:]
        for marker in re.finditer('___', line):
            labelled = UNKNOWN.match(line, marker.start())
            if not labelled:
                bare = True
            elif heading != 'Not checked':
                outside.append(labelled[1])
            else:
                explanation = re.match(r'[ \t]*:[ \t]*(\S.*)', line[labelled.end():])
                if explanation:
                    reason = explanation[1].strip()
                    if reason.lower() not in {'none', *NO_REASON} and not UNKNOWN.fullmatch(reason):
                        explained.add(labelled[1])
    return (['bare ___'] if bare else []) + list(dict.fromkeys(
        label for label in outside if label not in explained))


def header_failures(lines):
    failures = []
    actual = [line[3:] for line in lines if line.startswith('## ')]
    if lines.count('# Review packet') != 1 or actual != HEADINGS:
        failures.append(('headings', 'missing, duplicated, or out of order'))
    keys = bad_identity_keys(lines)
    if keys:
        failures.append(('identity', 'bad or missing keys: ' + ', '.join(keys)))
    verdicts = bad_verdicts(lines)
    if verdicts:
        failures.append(('verdict-words', 'bad or missing verdicts: ' + ', '.join(verdicts)))
    money = line_values(lines, 'money')
    if not money or any(not valid_money(verdict) for verdict in money):
        failures.append(('money-line', 'missing or invalid money line'))
    return failures


def rule_failures(text):
    lines = text.splitlines()
    bodies = field_bodies(lines)
    failures = header_failures(lines)
    missing = missing_parts(bodies)
    if missing:
        failures.append(('missing-part', 'missing content: ' + ', '.join(missing)))
    if not bodies.get('Not checked', ''):
        failures.append(('not-checked-empty', 'Not checked has no content'))
    unknowns = unmatched_unknowns(lines)
    if unknowns:
        failures.append(('unknown-unmatched', 'unmatched unknowns: ' + ', '.join(unknowns)))
    if 'safe to merge' in text.lower():
        failures.append(('safe-to-merge', 'contains safe to merge'))
    if any(line.lstrip(' \t-*#_').lower().startswith(('overall', 'ready')) for line in lines):
        failures.append(('overall-line', 'line starts with overall or ready'))
    if CAP_LINE in lines and 'It was not reviewed past size' in text:
        failures.append(('cap-contradiction', 'cap review contradicts size stop'))
    return failures


def verdict_word(verdict):
    match = re.match(r'(not asked|not checked|pass|fail|incomplete)(?=$|[,:;. ])', verdict)
    return match[1] if match else ''


def has_size_counts(verdict):
    return bool(re.search(r'\b[0-9]+\s+counted lines\b', verdict))


def tests_on_head(body, head):
    if body.startswith('not checked:'):
        match = re.fullmatch(r'not checked: no CI run on head (' + HEX + ')', body)
        return bool(match and match[1].lower() == head.lower())
    if body.startswith('not asked'):
        return False
    return all(commit.lower() == head.lower() for commit in re.findall(r'\b' + HEX + r'\b', body))


def tests_ci_failures(bodies, not_asked=''):
    tests = bodies.get('Tests run', '')
    if not tests or 'Tests run' in missing_parts(bodies):
        return []
    if tests == not_asked or re.fullmatch(r'not checked: no CI run on head ' + HEX, tests):
        return []
    if any(not re.fullmatch(r'CI run [A-Za-z0-9_-]+ on ' + HEX + r': (?:pass|fail)', line)
           for line in tests.splitlines() if line.strip()):
        return [('tests-ci-form', 'Tests run needs CI run <id> on <40 hex>: <pass|fail>')]
    return []


def full_failures(verdicts, bodies, head):
    failures = []
    forbidden = [field for field in ['size', 'business', 'security', 'health']
                 if verdict_word(verdicts[field]) == 'not asked' or
                 (field in ['security', 'health'] and verdict_word(verdicts[field]) == 'not checked')]
    if forbidden:
        failures.append(('full-line', 'words not allowed in full packets: ' + ', '.join(forbidden)))
    if verdict_word(verdicts['size']) in ['pass', 'fail'] and not has_size_counts(verdicts['size']):
        failures.append(('full-size-counts', 'size needs counted lines'))
    missing = missing_parts(bodies)
    tests = bodies.get('Tests run', '')
    if tests and 'Tests run' not in missing and not tests_on_head(tests, head):
        failures.append(('full-tests-run', 'Tests run must name the PR head'))
    if not valid_money(verdicts['money']):
        failures.append(('full-money', 'missing or invalid money line'))
    plan = bodies.get('Split plan', '')
    if plan and 'Split plan' not in missing and not re.match(r'not needed(?=$|:)', plan):
        failures.append(('full-split-plan', 'Split plan must say not needed'))
    return failures + tests_ci_failures(bodies)


def short_failures(verdicts, bodies, plan):
    failures = []
    if not has_size_counts(verdicts['size']):
        failures.append(('short-size-counts', 'size needs counted lines'))
    stopped = [verdicts['money'], *(bodies.get(heading, '') for heading in HEADINGS[1:6])]
    if any(body != CAP_STOP for body in stopped):
        failures.append(('short-line', 'short packet fields must say ' + CAP_STOP))
    behaviour = [line for line in bodies.get('Behaviour changed', '').splitlines() if line.strip()]
    summaries = [line[len('group summary: '):].split(' | ', 1)[0] for line in behaviour
                 if line.startswith('group summary: ')]
    if summaries != [group['name'] for group in plan['groups']]:
        failures.append(('short-behaviour', 'group summaries must match split groups once in order'))
    if 'Translations by page: ' + CAP_STOP not in behaviour:
        failures.append(('short-translations', 'Translations by page must say ' + CAP_STOP))
    for rule, heading in [('short-split-plan', 'Split plan'), ('short-draft', 'Drafts, not sent')]:
        if not plan['groups'] or not re.search(r'^(?:[-*] )?group: ', bodies.get(heading, ''), re.MULTILINE):
            failures.append((rule, heading + ' needs split groups'))
    return failures


def single_failures(verdicts, bodies, identity):
    failures = []
    mode, head = identity['mode'], identity['head']
    not_asked = f'not asked: {mode} run only'
    size = verdicts['size']
    over_cap = mode == 'size' and verdict_word(size) == 'fail'
    if over_cap:
        if bodies.get('Split plan', '') != not_asked:
            failures.append(('size-split-plan', 'Split plan must say ' + not_asked))
        if any(re.search(GROUP_LINE, bodies.get(heading, ''), re.MULTILINE)
               for heading in ['Split plan', 'Drafts, not sent']):
            failures.append(('size-no-draft', 'size run only forbids split group lines'))
    allowed = ['pass', 'fail', 'incomplete'] + (['not checked'] if mode == 'business' else [])
    bad = [field for field in ['business', 'security', 'health']
           if (field == mode and verdict_word(verdicts[field]) not in allowed) or
           (field != mode and verdicts[field] != not_asked and
            not (over_cap and verdicts[field] == CAP_STOP))]
    if bad:
        failures.append(('single-mode-line', 'wrong mode words: ' + ', '.join(bad)))
    if ((mode == 'size' and (verdict_word(size) not in ['pass', 'fail'] or not has_size_counts(size))) or
            (mode != 'size' and size != not_asked)):
        failures.append(('single-size', 'size needs counts when asked, otherwise ' + not_asked))
    money = verdicts['money']
    if ((mode == 'security' and not valid_money(money)) or
            (mode != 'security' and money != f'not checked: money not looked at, {mode} run only')):
        failures.append(('single-money', 'money must follow the ' + mode + ' run form'))
    tests = bodies.get('Tests run', '')
    if (tests and 'Tests run' not in missing_parts(bodies) and
            tests != not_asked and not tests_on_head(tests, head)):
        failures.append(('single-tests-run', 'Tests run needs the head or ' + not_asked))
    return failures + tests_ci_failures(bodies, not_asked)


def rerun_field_failures(lines, identity):
    rerun = identity.get('rerun')
    has_line = any(line.lstrip().startswith('business rerun') for line in lines)
    if (('rerun' in identity and rerun != 'yes') or (rerun == 'yes') != has_line):
        return [('rerun-field', 'identity rerun=yes and a business rerun line must occur together')]
    return []


def rerun_failures(lines, inputs, identity):
    reruns = [line for line in lines if line.lstrip().startswith('business rerun')]
    business = ' '.join(line_values(lines, 'business'))
    if not reruns:
        return [('rerun-line', 'business rerun claim needs a rerun line')] if 'business rerun' in business else []
    areas = [area.get('area') for area in inputs['rules-pages.json']['areas']]
    bad_line = False
    for line in reruns:
        match = re.fullmatch(r'business rerun for (.+), ([0-9]{4}-[0-9]{2}-[0-9]{2}), head (' + HEX + ')', line)
        if not match or match[1] not in areas or match[3].lower() != identity['head'].lower():
            bad_line = True
            continue
        try:
            date.fromisoformat(match[2])
        except ValueError:
            bad_line = True
    failures = [('rerun-line', 'rerun needs a known area, ISO date, and PR head')] if bad_line else []
    if any(isinstance(area, str) and area not in business for area in areas):
        failures.append(('rerun-business', 'business must name every touched area'))
    words = {entry.get('word') for entry in inputs['check-record.json']['entries']
             if entry.get('mode') == 'security' and isinstance(entry.get('word'), str)}
    security = [verdict_word(verdict) for verdict in line_values(lines, 'security')]
    if (('must fix' in words and any(word != 'fail' for word in security)) or
            ('incomplete' in words and 'pass' in security)):
        failures.append(('rerun-security', 'security must preserve must fix and incomplete entries'))
    return failures


def packet_type_failures(lines, inputs):
    # Common checks own malformed identity keys and plain bad verdict words.
    if bad_identity_keys(lines) or bad_verdicts(lines):
        return []
    identity = dict(pair.strip().split('=', 1) for pair in line_values(lines, 'identity')[0].split(';')
                    if '=' in pair)
    identity = {key: text.strip() for key, text in identity.items()}
    verdicts = {field: next(iter(line_values(lines, field)), '')
                for field in ['size', 'business', 'security', 'health', 'money']}
    bodies = field_bodies(lines)
    failures = rerun_failures(lines, inputs, identity) + rerun_field_failures(lines, identity)
    if identity['mode'] != 'full':
        return failures + single_failures(verdicts, bodies, identity)
    identity_index = next(index for index, line in enumerate(lines) if line.startswith('identity:'))
    cap = CAP_LINE in lines[:identity_index]
    if any(line.startswith('reviewed over the cap') for line in lines) and not cap:
        failures.append(('override-cap-line', 'the exact cap line must appear above identity'))
    size_fail = verdict_word(verdicts['size']) == 'fail'
    stopped = all(verdicts[field].startswith(CAP_STOP) for field in ['business', 'security', 'health'])
    if size_fail and not cap and stopped:
        return failures + short_failures(verdicts, bodies, inputs['split-plan.json'])
    if size_fail and not cap:
        failures.append(('cross-size-fail', 'size fail with other lines not not checked needs the reviewed over the cap line, or a size mode packet'))
    if cap:
        if not size_fail:
            failures.append(('override-size-fail', 'reviewed over the cap requires size fail'))
        if any(verdicts[field].startswith('not checked: PR over the cap')
               for field in ['business', 'security', 'health']):
            failures.append(('override-not-checked', 'override verdicts must not stop at the cap'))
    return failures + full_failures(verdicts, bodies, identity['head'])


def main(args):
    if len(args) != 1:
        raise ValueError('usage: packet_check.py <packet folder>')
    folder = Path(args[0])
    if not folder.is_dir():
        raise ValueError('packet folder is missing or not a folder')
    packet = folder / 'packet.md'
    if not packet.is_file():
        raise ValueError('packet.md is missing or not a file')
    try:
        text = packet.read_text(encoding='utf-8')
    except (OSError, UnicodeError) as error:
        raise ValueError('packet.md is unreadable or not valid UTF-8') from error
    if not text.strip():
        raise ValueError('packet.md is empty')
    inputs, missing = read_inputs(folder)
    lines = text.splitlines()
    failures = (rule_failures(text) + record_failures(lines, inputs) + split_failures(lines, inputs)
                + packet_type_failures(lines, inputs))
    if missing and not failures:
        failures.append(('input-fields', 'missing fields: ' + ', '.join(missing)))
    for rule, message in failures:
        print(f'RULE {rule}: {message}')
    if failures:
        return FAILED_SHAPE
    print('packet_check: pass')
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    try:
        sys.exit(main(sys.argv[1:]))
    except (ValueError, OSError) as error:
        print('packet_check: ' + str(error).replace('\n', ' ').replace('\r', ' '), file=sys.stderr)
        sys.exit(2)
