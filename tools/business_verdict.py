import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


class ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message)


def areas_document(path):
    document = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(document, dict) or not isinstance(document.get('areas'), list):
        raise ValueError('expected an object with an areas list')
    return document['areas']


def text_field(row, key):
    if not isinstance(row, dict) or not isinstance(row.get(key), str) or any(
            char in row[key] for char in '\r\n'):
        raise ValueError(f'{key} must be text on 1 line')
    return row[key]


def verdict(options):
    areas = areas_document(options.areas)
    if not areas:
        raise ValueError('areas must not be empty')
    for area in areas:
        for key in ('area', 'state', 'reason'):
            text_field(area, key)
        if area['state'] not in ('pass', 'fail', 'incomplete', 'not checked'):
            raise ValueError('unknown area state: ' + area['state'])
    pending = [area for area in areas if area['state'] != 'pass']
    pending.sort(key=lambda area: area['state'] != 'fail')
    if not pending:
        draft_notice = 'rules page: draft, not in the repo yet'
        print('business: pass, ' + '; '.join(
            f'area {area["area"]}: every rule kept'
            + (', ' + draft_notice if draft_notice in area['reason'] else '')
            for area in areas))
    else:
        state = 'fail' if pending[0]['state'] == 'fail' else 'incomplete'
        print(f'business: {state}, ' + '; '.join(
            f'area {area["area"]}: {area["reason"]}' for area in pending))
    return 0


def security_line(options):
    line, area = (text_field(vars(options), key) for key in ('line', 'area'))
    match = re.fullmatch(r'security: (pass|fail|incomplete|not asked|not checked)(?=$|[,;:\s])(.*)', line)
    if not match:
        raise ValueError('expected a security line with a known state')
    state, rest = match.groups()
    if state == 'pass':
        rest = rest.lstrip(', ')
        line = 'security: incomplete, ' + (rest + '; ' if rest else '')
        line += 'merge only after: rerun security for ' + area
    elif state in ('incomplete', 'fail'):
        phrase = ('also merge only after: ' if state == 'incomplete' else 'also: ') + 'rerun security for ' + area
        if not re.search(re.escape(phrase) + r'(?=$|[;,.])', line):
            line += '; ' + phrase
    print(line)
    return 0


def packet_identity(options):
    if not re.fullmatch(r'[0-9a-fA-F]{40}', options.head):
        raise ValueError('head must be a full commit SHA')
    lines = (options.packet / 'packet.md').read_text(encoding='utf-8').splitlines()
    fields = {}
    for label in ('identity', 'size', 'business'):
        matches = [line for line in lines if line.startswith(label + ':')]
        if len(matches) != 1:
            raise ValueError(f'expected 1 {label} line')
        fields[label] = matches[0]
    pairs = re.findall(r'(?:^|[;\s])(\w+)=([^;\s]+)', fields['identity'])
    identity = dict(pairs)
    if len(identity) != len(pairs) or not identity.get('default', '').rpartition('@')[0]:
        raise ValueError('identity needs unique keys and a default branch')
    commits = {key: identity.get(key, '') for key in ('head', 'base', 'default')}
    commits['default'] = commits['default'].rpartition('@')[2]
    if any(not re.fullmatch(r'[0-9a-fA-F]{40}', sha) for sha in commits.values()):
        raise ValueError('identity needs full head, base and default commits')
    return fields, commits


def draft_pages(path):
    drafts = []
    for row in areas_document(path):
        area, commit = text_field(row, 'area'), text_field(row, 'commit')
        if not area or area in ('.', '..') or any(char in area for char in '/\\:'):
            raise ValueError('area must be a file stem')
        if commit.startswith('sha256:'):
            if not re.fullmatch(r'sha256:[0-9a-fA-F]{64}', commit):
                raise ValueError('invalid draft hash')
            drafts.append((area, commit))
    return drafts


def rerun_check(options):
    fields, commits = packet_identity(options)
    if commits['head'].lower() != options.head.lower():
        print('refuse: PR head moved since the packet was written '
              f'(packet {commits["head"][:7]}, now {options.head[:7]}); ask for a new full run')
        return 1
    if re.match(r'size: fail(?=$|[,;:\s])', fields['size']) and fields['business'].startswith('business: not checked: PR over the cap'):
        print('refuse: rerun on a short packet is not decided (O19); ask the user')
        return 3
    drafts = draft_pages(options.packet / 'rules-pages.json')
    if drafts and options.drafts is None:
        print(f'refuse: drafts folder needed for draft page {drafts[0][0]}')
        return 1
    warnings = []
    for area, commit in drafts:
        try:
            digest = hashlib.sha256((options.drafts / (area + '.md')).read_bytes()).hexdigest()
        except FileNotFoundError:
            warnings.append(f'page changed since the first run: {area} (file missing)')
            continue
        if digest != commit[7:]:
            warnings.append(f'page changed since the first run: {area}')
    print(f'use base {commits["base"]}\nuse default {commits["default"]}')
    for warning in warnings:
        print(warning)
    print('rerun-check: ok')
    return 0


def main(args):
    try:
        parser = ArgumentParser(allow_abbrev=False)
        subparsers = parser.add_subparsers(dest='command', required=True)
        for command, required, optional, action in (
                ('verdict', ('areas',), (), verdict),
                ('security-line', ('line', 'area'), (), security_line),
                ('rerun-check', ('packet', 'head'), ('drafts',), rerun_check)):
            subparser = subparsers.add_parser(command, allow_abbrev=False)
            subparser.set_defaults(action=action)
            for flag in required + optional:
                subparser.add_argument('--' + flag, required=flag in required,
                                       type=Path if flag in ('areas', 'packet', 'drafts') else str)
        options = parser.parse_args(args)
        return options.action(options)
    except (ValueError, OSError) as error:
        print('business_verdict: error: ' + ' '.join(str(error).splitlines()), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    sys.exit(main(sys.argv[1:]))
