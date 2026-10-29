import argparse
import fnmatch
import json
import os
import subprocess
import tempfile
from pathlib import Path, PurePosixPath


TEAM_LIST_ENV = 'ACT_AS_TEAM_LIST'
SKILLS_DIR_ENV = 'ACT_AS_SKILLS_DIR'


def _skills_root(skills_dir, env=None):
    if skills_dir is not None:
        return Path(skills_dir).expanduser()
    environment = os.environ if env is None else env
    configured = environment.get(SKILLS_DIR_ENV)
    return Path(configured).expanduser() if configured else Path.home() / '.claude' / 'skills'


def skill_status(name, skills_dir=None):
    installed = (_skills_root(skills_dir) / name / 'SKILL.md').is_file()
    return 'installed' if installed else f'not checked: {name} not installed'


def guard_targets(changed_files):
    targets = {'code': [], 'tests': [], 'docs': []}
    patterns = ('*Test.php', '*.test.js', '*.test.ts', '*.spec.js', '*.spec.ts',
                'test_*.py', '*_test.go')
    for filename in changed_files:
        path = PurePosixPath(str(filename).replace('\\', '/'))
        is_test = any(part in ('tests', 'test') for part in path.parts[:-1]) or any(
            fnmatch.fnmatchcase(path.name, pattern) for pattern in patterns)
        if is_test:
            targets['tests'].append(filename)
        elif path.suffix == '.php':
            targets['code'].append(filename)
        if path.suffix in ('.md', '.rst') or 'docs' in path.parts[:-1]:
            targets['docs'].append(filename)
    return targets


def team_gate(author, list_path=None, env=None):
    environment = os.environ if env is None else env
    configured = list_path if list_path is not None else environment.get(TEAM_LIST_ENV)
    missing = (False, 'not checked: team list missing')
    if not configured:
        return missing
    try:
        lines = Path(configured).expanduser().read_text(encoding='utf-8').splitlines()
    except (OSError, UnicodeError):
        return missing
    logins = {line.strip().casefold() for line in lines
              if line.strip() and not line.lstrip().startswith('#')}
    if not logins:
        return missing
    if author is None or author.strip().casefold() not in logins:
        return False, 'not checked: debate-review skipped, PR from outside the team'
    return True, 'inside the team'


def build_debate_command(skill_dir, pr_url, out_dir, extra_args=None):
    forbidden = {'--post-draft', '--force', '--keep', '--local', '--check'}
    extras = [] if extra_args is None else extra_args
    if any(arg.split('=', 1)[0] in forbidden for arg in extras):
        raise ValueError('unsafe debate arguments')
    if extras:
        raise ValueError('extra debate arguments are not supported')
    return ['node', str(Path(skill_dir) / 'scripts' / 'review-pr.mjs'), str(pr_url),
            '--dry-run', '--out-dir', str(out_dir)]


def _worktree_entries(tmp_dir):
    return {entry.name for entry in Path(tmp_dir).iterdir()
            if entry.name.startswith('debate-review-')}


def run_debate(pr_url, author, out_dir, skills_dir=None, list_path=None, env=None,
               runner=subprocess.run, tmp_dir=None):
    skills_root = _skills_root(skills_dir, env)
    status = skill_status('debate-review', skills_root)
    outcome = dict(ran=False, line=status, command=None, worktree_removed=None)
    if status != 'installed':
        return outcome
    allowed, outcome['line'] = team_gate(author, list_path, env)
    if not allowed:
        return outcome
    command = build_debate_command(skills_root / 'debate-review', pr_url, out_dir)
    outcome['command'] = command
    scratch = tempfile.gettempdir() if tmp_dir is None else tmp_dir
    before = _worktree_entries(scratch)
    try:
        completed = runner(command, capture_output=True, text=True, encoding='utf-8', errors='replace')
    except OSError as error:
        outcome['line'] = f'not checked: debate-review could not start: {error}'
    else:
        output_folder = Path(out_dir)
        output_folder.mkdir(parents=True, exist_ok=True)
        outcome['exit_code'] = completed.returncode
        for stream in ('stdout', 'stderr'):
            path = output_folder / f'debate-{stream}.txt'
            contents = getattr(completed, stream)
            path.write_text(contents if isinstance(contents, str) else '', encoding='utf-8')
            outcome[f'{stream}_path'] = str(path)
        outcome['ran'] = True
        outcome['line'] = (f'not checked: debate-review failed, exit {completed.returncode}'
                           if completed.returncode else 'ran: debate-review --dry-run')
    outcome['worktree_removed'] = not (_worktree_entries(scratch) - before)
    if not outcome['worktree_removed']:
        outcome['line'] = 'not checked: debate-review worktree left behind'
    return outcome


def main():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest='command', required=True)
    skills = commands.add_parser('skills')
    skills.add_argument('names', nargs='+')
    targets = commands.add_parser('targets')
    targets.add_argument('files', nargs='+')
    gate = commands.add_parser('gate')
    gate.add_argument('--author', required=True)
    gate.add_argument('--list', dest='list_path')
    debate = commands.add_parser('debate')
    for flag in ('--pr', '--author', '--out-dir'):
        debate.add_argument(flag, required=True)
    args = parser.parse_args()
    try:
        if args.command == 'skills':
            for name in args.names:
                print(skill_status(name))
        elif args.command == 'targets':
            print(json.dumps(guard_targets(args.files)))
        elif args.command == 'gate':
            print(team_gate(args.author, args.list_path)[1])
        else:
            print(run_debate(args.pr, args.author, args.out_dir)['line'])
    except (OSError, UnicodeError, ValueError) as error:
        print(f'not checked: {error}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
