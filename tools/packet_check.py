"""Check packet.md text with Python 3.12 and the standard library.

Usage: python tools/packet_check.py <packet folder>
Exit 0 prints packet_check: pass. Exit 1 prints 1 RULE line per failed
text rule. Exit 2 prints 1 packet_check: error line on stderr only.

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
Only packet.md is read; evidence files and counts are not checked.
"""

import re
import sys
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
    failures = rule_failures(text)
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
