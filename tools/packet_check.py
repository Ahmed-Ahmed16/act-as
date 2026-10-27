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
Hunk placement checks apply unless Split plan starts with not needed.
"""

import json
import re
import sys
from collections import Counter
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


def split_failures(lines, inputs):
    plan = inputs['split-plan.json']
    hunks = [hunk for file in inputs['files.json']['files'] if file.get('kind') == 'counted'
             for hunk in file.get('hunks', [])]
    counts = {hunk.get('id'): hunk.get('counted_lines', 0) for hunk in hunks}
    groups = plan['groups']
    placements = Counter(hunk for group in groups for hunk in group.get('hunks', []))
    placements.update(plan['unplaced'])
    bodies = field_bodies(lines)
    failures = []
    if not bodies.get('Split plan', '').startswith('not needed'):
        missing = [str(key) for key in counts if key not in placements]
        duplicates = [str(key) for key, count in placements.items() if count > 1]
        if missing:
            failures.append(('hunk-unplaced', 'unplaced hunks: ' + ', '.join(missing)))
        if duplicates:
            failures.append(('hunk-duplicate', 'duplicate hunks: ' + ', '.join(duplicates)))
    size = re.search(r'\b([0-9]+)\s+counted lines\b', ' '.join(line_values(lines, 'size')[:1]))
    total = sum(hunk.get('counted_lines', 0) for hunk in hunks)
    if size and int(size[1]) != total:
        failures.append(('hunk-counts', f'counted lines differ: packet {int(size[1])}, hunks {total}'))
    expected = [(group.get('name'), sum(counts.get(key, 0) for key in group.get('hunks', [])))
                for group in groups]
    for rule, heading in [('split-field', 'Split plan'), ('split-message', 'Drafts, not sent')]:
        actual = [(match[1], int(match[2])) for match in re.finditer(
            r'^[ \t]*(?:[-*] )?group: (.+), ([0-9]+) counted lines[ \t]*$',
            bodies.get(heading, ''), re.MULTILINE)]
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
        if not body or (heading not in HEADINGS[4:6] and only_placeholders):
            missing.append(heading)
    return missing


def unmatched_unknowns(lines):
    # Cases: bare, labelled, repeated, matching label, absent or blank reason.
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
            elif re.match(r'[ \t]*:[ \t]*\S', line[labelled.end():]):
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
    failures = rule_failures(text) + record_failures(lines, inputs) + split_failures(lines, inputs)
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
