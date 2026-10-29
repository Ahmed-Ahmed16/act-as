import re
import sys
from bisect import bisect_right
from itertools import accumulate
from pathlib import Path


def read_text(name, kind):
    try:
        raw = Path(name).read_bytes()
        if raw.startswith((b'\xff\xfe', b'\xfe\xff')):
            return raw.decode('utf-16')
        if raw.startswith(b'\xef\xbb\xbf'):
            return raw.decode('utf-8-sig', errors='replace')
    except (OSError, ValueError):
        # OS error messages can contain paths with private terms.
        raise ValueError(f'cannot read {kind}') from None
    if b'\x00' in raw:
        raise ValueError(f'cannot read {kind}: not text')
    return raw.decode('utf-8', errors='replace')


def term_patterns(name):
    terms = [line.strip() for line in read_text(name, 'terms file').splitlines()]
    terms = [term for term in terms if term and not term.startswith('#')]
    if not terms:
        raise ValueError('no terms after dropping blanks and comments')
    patterns = []
    for term in terms:
        pattern = r'\s+'.join(re.escape(part) for part in term.split())
        if len(term) <= 4 and term.isalnum():
            pattern = r'(?<![^\W_])' + pattern + r'(?![^\W_])'
        patterns.append(re.compile(pattern, re.IGNORECASE))
    return patterns


def scan(names, patterns):
    hits = 0
    for name in names:
        text = read_text(name, 'candidate file')
        line_ends = list(accumulate(map(len, text.splitlines(keepends=True))))
        locations = {(bisect_right(line_ends, match.start()) + 1, index)
                     for index, pattern in enumerate(patterns, 1)
                     for match in pattern.finditer(text)}
        for number, index in sorted(locations):
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
