import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

if __package__:
    from . import packet_check as checks
    from .short_render import behaviour, draft, split_field
    from .size_counter import ArgumentParser
else:
    import packet_check as checks
    from short_render import behaviour, draft, split_field
    from size_counter import ArgumentParser


def arguments(args):
    parser = ArgumentParser(allow_abbrev=False)
    parser.add_argument('packet', type=Path)
    for flag in ('repo-name', 'pr', 'default', 'date'):
        parser.add_argument('--' + flag, required=True)
    options = parser.parse_args(args)
    for field, text in dict(repo=options.repo_name, pr=options.pr, default=options.default, date=options.date).items():
        if not re.fullmatch(checks.IDENTITY[field], text):
            raise ValueError('invalid ' + field)
    date.fromisoformat(options.date)
    return options


def load_inputs(folder):
    names = ('split-plan.json', 'files.json', 'runs/size-count.json', 'hunks.json')
    raw = {name: (folder / name).read_bytes() for name in names}
    plan, files, saved, hunks = [json.loads(raw[name]) for name in names]
    for name, document, schema in [('files.json', files, checks.INPUT_SHAPES['files.json']),
                                 ('size-count', saved, dict(base=str, head=str, verdict=str, size_line=str, counted_total=int)),
                                 ('hunks', hunks, dict(base=str, head=str, hunks={}, ops={}))]:
        if checks.input_fields(document, schema, name):
            raise ValueError(name + ' has missing fields')
    row = dict(name=str, summary=str, hunks=[str], counted=int, needs=[str], marks=[str], rebuild=str)
    for document, schema in [(plan, dict(groups=dict(row, entry_points=[str], pages={}, keys={}, links={}),
                                        first_group_parts=row, unplaced=[str])), (plan['main'], dict(state=str, evidence=str)),
                             (plan['ci'], dict(state=str, **({'reason': str} if plan['ci'].get('state') == 'unreadable'
                                                             else {'workflows': {}})))]:
        if checks.input_fields(document, schema, 'plan'):
            raise ValueError('plan has missing fields')
    for name, field in [('files.json', 'files_sha256'), ('hunks.json', 'hunks_sha256'),
                        ('split-input.json', 'input_sha256')]:
        if name == 'split-input.json' and not (folder / name).exists():
            continue
        contents = raw[name] if name in raw else (folder / name).read_bytes()
        if hashlib.sha256(contents).hexdigest() != plan[field]:
            raise ValueError('plan is stale, run build again')
    if any(not re.fullmatch(checks.IDENTITY[field], plan[field]) or plan[field] != saved[field]
           or plan[field] != hunks[field] for field in ('base', 'head')):
        raise ValueError('plan is stale, run build again')
    if (saved['verdict'] != 'fail' or saved['counted_total'] <= 300
            or not saved['size_line'].startswith(f"fail, {saved['counted_total']} counted lines, ")):
        raise ValueError('size verdict must be fail over 300')
    return plan, files, saved, hunks


def main(args):
    try:
        options = arguments(args)
        plan, files, saved, hunks = load_inputs(options.packet)
        identity = (f'identity: repo={options.repo_name}; pr={options.pr}; mode=full; head={plan["head"]}; '
                    f'base={plan["base"]}; default={options.default}; date={options.date}')
        opening = f"This PR is {saved['counted_total']} counted lines; the cap is 300. It was not reviewed past size."
        bodies = [behaviour(plan), *([checks.CAP_STOP] * 5), split_field(plan, files, hunks), draft(plan, files, hunks, opening)]
        packet = '\n'.join(['# Review packet', identity, 'size: ' + saved['size_line'],
                            *(field + ': ' + checks.CAP_STOP for field in ('business', 'security', 'health', 'money')),
                            '', *(f'## {heading}\n{body}\n' for heading, body in zip(checks.HEADINGS, bodies))])
        entries = [dict(id=key, mode='security', kind='check', area='', tool_result='not checked',
                        reading_result='not checked', word='none', reason=checks.CAP_STOP, base_read='', head_read='')
                   for key in [*(f'S{n}' for n in range(1, 23)), 'L1', 'L5']]
        outputs = {'packet.md': packet, 'check-record.json': json.dumps(dict(required_ids=[], entries=entries), indent=2),
                   'rules-pages.json': json.dumps(dict(areas=[]))}
        inputs = {'check-record.json': dict(required_ids=[], entries=entries), 'files.json': files,
                  'split-plan.json': plan, 'rules-pages.json': dict(areas=[])}
        failures = checks.rule_failures(packet) + checks.split_failures(packet.splitlines(), inputs)
        failures += checks.packet_type_failures(packet.splitlines(), inputs)
        if failures:
            raise ValueError('packet shape is invalid: ' + failures[0][0])
        if any((options.packet / name).exists() for name in outputs):
            raise ValueError('packet output already exists')
        for name, contents in outputs.items():
            with (options.packet / name).open('x', encoding='utf-8', newline='\n') as output:
                output.write(contents + '\n')
        return 0
    except (ValueError, OSError, UnicodeError, KeyError, TypeError, AttributeError) as error:
        print('short_packet: ' + ' '.join(str(error).splitlines()), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    sys.exit(main(sys.argv[1:]))
