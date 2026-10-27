import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

from health_parse import ArgumentParser, outcome, run_cli


def routes(args):
    repo = Path(args.repo).resolve(strict=True)
    if not repo.is_dir():
        raise ValueError('repo must be a directory')
    controllers = []
    route_files = sorted((repo / 'routes').glob('*.php'))
    for filename in args.files:
        path = (repo / filename).resolve(strict=True)
        if Path(filename).is_absolute() or not path.is_relative_to(repo):
            raise ValueError(f'file is not under repo: {filename}')
        path.read_text(encoding='utf-8')
        class_name = path.stem
        mention = re.compile(r'(?<![\w])' + re.escape(class_name) + r'::class\b|[\x27"]' +
                             re.escape(class_name) + '@')
        where, resources = [], 0
        for route_file in route_files:
            for number, line in enumerate(route_file.read_text(encoding='utf-8').splitlines(), 1):
                if 'Route::' in line and mention.search(line):
                    where.append(f'{route_file.relative_to(repo).as_posix()}:{number}')
                    resources += bool(re.search(r'Route::(?:resource|apiResource)\s*\(', line))
        controllers.append(dict(file=filename, **{'class': class_name}, route_lines=len(where),
                                resource_lines=resources, where=where,
                                note='resource lines count as 1; the real route count is higher'
                                if resources else 'counts route lines'))
    return outcome('clean', 'counts only, a number is a pointer', controllers=controllers)


def git(repo, *args):
    completed = subprocess.run(['git', '-C', str(repo), *args], capture_output=True)
    allowed = (0, 1) if args[0] == 'grep' else (0,)
    if completed.returncode not in allowed:
        raise ValueError('git failed: ' + completed.stderr.decode('utf-8', 'replace').strip())
    return completed.stdout


def occurrences(repo, ref, literal):
    raw = git(repo, 'grep', '-F', '-n', '-z', '-I', '-e', literal, ref, '--', '.',
              ':(exclude)vendor/**', ':(exclude)node_modules/**', ':(exclude)storage/**')
    return [(match[1].decode('utf-8')[len(ref) + 1:], int(match[2]))
            for match in re.finditer(rb'([^\0]+)\0(\d+)\0[^\n]*(?:\n|$)', raw)]


def copies(args):
    if any(not literal or '\n' in literal or '\r' in literal or '\0' in literal
           for literal in args.literal):
        raise ValueError('literal must be nonempty and on 1 line')
    refs = [git(args.repo, 'rev-parse', '--verify', '--end-of-options', ref + '^{commit}')
            .decode('ascii').strip() for ref in (args.base, args.head)]
    literals, summaries = [], []
    for literal in args.literal:
        base_counts = Counter(path for path, _ in occurrences(args.repo, refs[0], literal))
        rows = []
        for path, line in occurrences(args.repo, refs[1], literal):
            at_base = base_counts[path] > 0
            if at_base:
                base_counts[path] -= 1
            rows.append(dict(path=path, line=line, at_base=at_base,
                             in_config=path.startswith('config/'),
                             in_lang=path.startswith(('lang/', 'resources/lang/')),
                             in_test=path.startswith('tests/')))
        count = sum(not row['in_test'] for row in rows)
        new = sum(not row['at_base'] and not row['in_test'] for row in rows)
        summary = dict(literal=literal, copy_count=count, new_copies=new,
                       old_copies=sum(row['at_base'] for row in rows),
                       result='finding' if new >= 1 and count >= 2 else 'clean')
        if count >= 2 and new == 0:
            summary['old_only'] = True
        summaries.append(summary)
        literals.append(dict(literal=literal, copies=rows))
    return outcome('finding' if any(row['result'] == 'finding' for row in summaries) else 'clean',
                   'copy counts need reading', literals=literals, summary=summaries,
                   reading_needed='both copies must express the same rule')


def main():
    parser = ArgumentParser()
    commands = parser.add_subparsers(dest='command', required=True, parser_class=ArgumentParser)
    route_command = commands.add_parser('routes')
    route_command.add_argument('--repo', required=True)
    route_command.add_argument('--files', required=True, nargs='+')
    copy_command = commands.add_parser('copies')
    for flag in ('--repo', '--base', '--head'):
        copy_command.add_argument(flag, required=True)
    copy_command.add_argument('--literal', required=True, action='append')
    args = parser.parse_args()
    return routes(args) if args.command == 'routes' else copies(args)


if __name__ == '__main__':
    sys.exit(run_cli(main))
