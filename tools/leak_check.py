import re
import sys
from pathlib import Path


def read_text(name, kind):
    try:
        return Path(name).read_text(encoding='utf-8', errors='replace')
    except (OSError, ValueError):
        # OS error messages can contain paths with private terms.
        raise ValueError(f'cannot read {kind}') from None


def term_patterns(name):
    terms = [line.strip() for line in read_text(name, 'terms file').splitlines()]
    terms = [term for term in terms if term and not term.startswith('#')]
    if not terms:
        raise ValueError('no terms after dropping blanks and comments')
    patterns = []
    for term in terms:
        pattern = re.escape(term)
        if len(term) <= 4 and term.isalnum():
            pattern = r'\b' + pattern + r'\b'
        patterns.append(re.compile(pattern, re.IGNORECASE))
    return patterns


def scan(names, patterns):
    hits = 0
    for name in names:
        text = read_text(name, 'candidate file')
        for number, line in enumerate(text.splitlines(), 1):
            for index, pattern in enumerate(patterns, 1):
                if pattern.search(line):
                    print(f'{name}:{number}: group-or-term-index {index}')
                    hits += 1
    print(f'total: {hits} hits')
    return 1 if hits else 0


def main(args):
    if len(args) < 2:
        raise ValueError('usage: python tools/leak_check.py TERMS_FILE FILE [FILE ...]')
    return scan(args[1:], term_patterns(args[0]))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    try:
        sys.exit(main(sys.argv[1:]))
    except ValueError as error:
        print(f'leak_check.py: {error}', file=sys.stderr)
        sys.exit(2)
