import re
import sys
from pathlib import Path

ID = r'[A-Z]{3}-(?:P\d{2}|\d{3})'
RANGE = re.compile(r'(' + ID + r')`? +to +`?(' + ID + r')')

def card_ids(text):
    # Cases: empty, single, repeated; numeric and policy ranges; different prefixes.
    def expand(match):
        first, last = match.groups()
        prefix, start = first.rsplit('-', 1)
        last_prefix, end = last.rsplit('-', 1)
        policy = start.startswith('P')
        if prefix != last_prefix or policy != end.startswith('P'):
            return match.group(0)
        low, high = int(start.lstrip('P')), int(end.lstrip('P'))
        return ' '.join(f'{prefix}-' + ('P%02d' % n if policy else '%03d' % n) for n in range(low, high + 1))
    return list(dict.fromkeys(re.findall(ID, RANGE.sub(expand, text))))

def section(text, heading):
    return text.split(heading, 1)[1].split('\n## ', 1)[0]

def steps(role_dir, mode):
    text = section((role_dir / f'modes/{mode}.md').read_text(encoding='utf-8'), '## Steps\n')
    return dict(re.findall(r'(?ms)^(\d+)\. (.*?)(?=^\d+\. |\Z)', text))

def selected_ids(role_dir, mode, step):
    rules = section((role_dir / 'ROLE.md').read_text(encoding='utf-8'), '## 3. Rules\n')
    if step == 'policy':
        bullets = '\n'.join(line for line in rules.split('Cards for every mode:', 1)[0].splitlines() if line.startswith('- '))
        return [card_id for card_id in card_ids(bullets) if re.fullmatch(r'[A-Z]{3}-P\d{2}', card_id)]
    if step == 'common':
        return card_ids(rules.split('Cards for every mode:', 1)[1])
    mode_steps = steps(role_dir, mode)
    if step not in mode_steps:
        raise ValueError(f'unknown step {step}')
    return card_ids(mode_steps[step])

def card_body(role_dir, mode, card_id):
    try:
        body = (role_dir / f'cards/{card_id}.md').read_text(encoding='utf-8')
    except FileNotFoundError:
        return '', 'missing'
    except (OSError, UnicodeError):
        return '', 'unreadable'
    fields = dict(re.findall(r'^([\w-]+): *(.*)$', body, re.M))
    status, modes = fields.get('status', 'missing'), fields.get('mode', 'missing')
    if status != 'approved':
        return '', f'status {status}'
    if not {'all', mode}.intersection(re.split(r'[,\s]+', modes)):
        return '', f'mode {modes}'
    return f"== {card_id} | trigger: {fields.get('trigger', '')}\n{body}", ''

def show_cards(role_dir, mode, step):
    cards = [(card_id, *card_body(role_dir, mode, card_id)) for card_id in selected_ids(role_dir, mode, step)]
    skipped = sum(bool(reason) for _, _, reason in cards)
    print(f'cards.py {role_dir.name} {mode} {step}: {len(cards) - skipped} printed, {skipped} skipped')
    for card_id, body, reason in cards:
        if reason:
            print(f"{'BLOCKED' if step == 'policy' else 'SKIPPED'} {card_id}: {reason}")
        else:
            print(body, end='' if body.endswith('\n') else '\n')
    return 3 if step == 'policy' and skipped else 0

def audit(role_dir):
    skipped = 0
    for mode_file in sorted((role_dir / 'modes').glob('*.md')):
        for step in [*steps(role_dir, mode_file.stem), 'common']:
            for card_id in selected_ids(role_dir, mode_file.stem, step):
                _, reason = card_body(role_dir, mode_file.stem, card_id)
                if reason:
                    print(f'{mode_file.stem} {step} SKIPPED {card_id}: {reason}')
                    skipped += 1
    print(f'total: {skipped} skipped')

def main(args):
    if len(args) not in (2, 3) or not re.fullmatch(r'[a-z][a-z0-9_-]*', args[0]):
        raise ValueError('usage: cards.py <role> <mode> <step> or <role> --audit')
    role_dir = Path(__file__).resolve().parents[1] / 'roles' / args[0]
    if not (role_dir / 'ROLE.md').is_file():
        raise ValueError('unknown role')
    if len(args) == 2:
        if args[1] != '--audit':
            raise ValueError('invalid audit arguments')
        audit(role_dir)
        return 0
    _, mode, step = args
    if not re.fullmatch(r'[a-z][a-z0-9_-]*', mode) or not (role_dir / f'modes/{mode}.md').is_file():
        raise ValueError('unknown mode')
    if step not in ('common', 'policy') and not re.fullmatch(r'[1-9]\d*', step):
        raise ValueError('invalid step')
    return show_cards(role_dir, mode, step)

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    try:
        sys.exit(main(sys.argv[1:]))
    except (ValueError, IndexError, OSError, UnicodeError) as error:
        print('cards.py: ' + str(error).replace('\n', ' '), file=sys.stderr)
        sys.exit(2)
