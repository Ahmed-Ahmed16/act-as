import argparse
import json
import re
import sys
from pathlib import Path


class ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message)


def outcome(result_word, reason, **fields):
    return dict(result=result_word, reason=reason, **fields)


def run_cli(main):
    try:
        print(json.dumps(main(), ensure_ascii=True))
    except (OSError, UnicodeError, ValueError) as error:
        print(' '.join(str(error).splitlines()), file=sys.stderr)
        return 2
    return 0


def phpstan_errors(text):
    errors, stale = [], 0
    for line in text.splitlines():
        match = re.match(r'^(.+?):(\d+|\?):(.*)$', line)
        if not match:
            continue
        path, number, message = match.groups()
        if re.search(r'Ignored error pattern .* was not matched in reported errors', message):
            stale += 1
        else:
            errors.append(dict(path=path, line=None if number == '?' else int(number),
                               message=message))
    return errors, stale


def phpstan(args, text):
    for marker in ('Application bootstrap failed', 'Laravel framework bootstrap failed',
                   'No files found to analyse'):
        if marker in text:
            return outcome('not checked', marker)
    if re.search(r'syntax error|parse error', text, re.I):
        return outcome('not checked', 'PHPStan syntax error')
    if args.exit not in (0, 1):
        return outcome('not checked', f'PHPStan exit {args.exit}')
    errors, stale = phpstan_errors(text)
    if errors:
        return outcome('finding', 'PHPStan reported errors', errors=errors, stale_baseline=stale)
    if stale:
        return outcome('clean', f'{stale} stale baseline entries only', stale_baseline=stale)
    if args.exit == 0 and not text.strip():
        return outcome('clean', 'PHPStan reported 0 errors')
    return outcome('not checked', f'exit {args.exit} with output that could not be read')


def phpmd(args, text):
    if args.files == 0:
        return outcome('not checked', 'PHPMD was given 0 PHP files')
    lines = [line for line in text.splitlines() if line.strip() and not line.startswith('Deprecated:')]
    if args.exit == 0:
        return outcome('clean', 'PHPMD reported 0 violations')
    violations = [line for line in lines if re.match(r'^\S.*?:\d+(?:\D|$)', line)]
    if args.exit == 2 and violations:
        return outcome('finding', 'PHPMD reported violations', violations=violations)
    return outcome('not checked', f'PHPMD exit {args.exit}: ' +
                   (lines[0] if lines else '0 output lines'))


def jscpd(args, text):
    reason = text.splitlines()[0] if text.splitlines() else 'jscpd report missing or invalid'
    try:
        document = json.loads(Path(args.report).read_text(encoding='utf-8'))
    except (FileNotFoundError, UnicodeError, ValueError):
        return outcome('not checked', reason)
    total = document.get('statistics', {}) if isinstance(document, dict) else {}
    total = total.get('total', {}) if isinstance(total, dict) else {}
    if not isinstance(total, dict) or any(type(total.get(key)) is not int or total[key] < 0
                                         for key in ('sources', 'clones')):
        return outcome('not checked', reason)
    sources, clones = total['sources'], total['clones']
    if sources == 0:
        return outcome('not checked', 'jscpd scanned 0 PHP files')
    if args.exit == 2:
        return outcome('not checked', f'jscpd exit {args.exit}')
    if args.exit == 1 or clones > 0:
        return outcome('finding', 'jscpd reported clones', sources=sources, clones=clones)
    if args.exit != 0:
        return outcome('not checked', f'jscpd exit {args.exit}')
    return outcome('clean', 'jscpd reported 0 clones', sources=sources)


def main():
    parser = ArgumentParser()
    commands = parser.add_subparsers(dest='tool', required=True, parser_class=ArgumentParser)
    for tool in ('phpstan', 'phpmd', 'jscpd'):
        command = commands.add_parser(tool)
        command.add_argument('--output', required=True)
        command.add_argument('--exit', required=True, type=int)
        if tool == 'phpmd':
            command.add_argument('--files', required=True, type=int)
        if tool == 'jscpd':
            command.add_argument('--report', required=True)
    args = parser.parse_args()
    if args.tool == 'phpmd' and args.files < 0:
        raise ValueError('files must be at least 0')
    text = Path(args.output).read_text(encoding='utf-8')
    return {'phpstan': phpstan, 'phpmd': phpmd, 'jscpd': jscpd}[args.tool](args, text)


if __name__ == '__main__':
    sys.exit(run_cli(main))
