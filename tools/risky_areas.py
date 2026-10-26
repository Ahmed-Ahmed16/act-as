import re
import sys
from pathlib import Path

from health_parse import ArgumentParser, outcome, run_cli


PATTERNS = {
    'money': r'price|amount|total|currency|charge|refund|payment|invoice|balance|'
             r'checkout|tax|discount|wallet',
    'logins': r'login|logout|password|auth|session|token|credential|sign_in|signin|'
              r'permission|role',
    'delete': r'delete|destroy|forceDelete|drop\s+table|truncate|unlink|rmtree|remove|purge',
}
PATTERNS = {kind: re.compile(r'(?<![a-z0-9])(?:' + words + r')(?![a-z0-9])', re.I)
            for kind, words in PATTERNS.items()}


def changed_text(repo, filename):
    if Path(filename).is_absolute():
        raise ValueError(f'file is not under repo: {filename}')
    try:
        path = (repo / filename).resolve()
        if not path.is_relative_to(repo):
            raise ValueError(f'file is not under repo: {filename}')
        return path.read_text(encoding='utf-8')
    except (OSError, UnicodeError) as error:
        raise ValueError(f'cannot read file {filename}: {error}') from error


def file_areas(filename, text):
    areas = []
    path_kinds = {kind for kind, pattern in PATTERNS.items() if pattern.search(filename)}
    for number, line in enumerate(text.splitlines() or [''], 1):
        for kind, pattern in PATTERNS.items():
            if pattern.search(line) or (number == 1 and kind in path_kinds):
                areas.append(dict(kind=kind, file=filename, line=number,
                                  evidence=line.strip()[:120]))
    return areas


def scan(args):
    try:
        repo = Path(args.repo).resolve(strict=True)
    except OSError as error:
        raise ValueError(f'cannot read repo: {error}') from error
    if not repo.is_dir():
        raise ValueError('repo must be a directory')
    areas = []
    for filename in args.files:
        areas.extend(file_areas(filename, changed_text(repo, filename)))
    found = {area['kind'] for area in areas}
    return outcome('lead' if areas else 'clean',
                   'candidates only; open the files to judge' if areas else
                   'no risky area words found in the requested files',
                   areas=areas, kinds_found=[kind for kind in PATTERNS if kind in found],
                   not_checked=['business risky areas: not asked: health run only'])


def main():
    parser = ArgumentParser()
    parser.add_argument('--repo', required=True)
    parser.add_argument('--files', required=True, nargs='+')
    return scan(parser.parse_args())


if __name__ == '__main__':
    sys.exit(run_cli(main))
