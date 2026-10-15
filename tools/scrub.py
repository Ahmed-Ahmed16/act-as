import re
import subprocess
import sys
from pathlib import Path

# Each finding prints path, line and kind. The matched text is never printed.
PATTERNS = [
    ('private key', r'-----BEGIN [A-Z ]*PRIVATE KEY-----'),
    ('aws key', r'\b(?:AKIA|ASIA)[0-9A-Z]{16}\b'),
    ('github token', r'\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{22,})'),
    ('anthropic key', r'\bsk-ant-[A-Za-z0-9_-]{20,}'),
    ('openai key', r'\bsk-(?:proj-)?[A-Za-z0-9_-]{32,}'),
    ('google key', r'\bAIza[0-9A-Za-z_-]{35}\b'),
    ('slack token', r'\bxox[abposr]-[A-Za-z0-9-]{10,}'),
    ('jwt', r'\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}'),
    ('secret assignment', r'(?i)\b(?:api[_-]?key|secret|token|passw(?:or)?d)\b["\']?\s*[:=]\s*["\'][^"\'\s]{8,}["\']'),
    ('private path', r'(?i)\b[A-Z]:\\(?:Users|work-projects)\\|/(?:home|Users)/[a-z][\w.-]*/'),
    ('email', r'\b(?!noreply@)[A-Za-z0-9._%+-]+@(?!(?:users\.)?noreply\.|example\.)[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}\b'),
]
PATTERNS = [(kind, re.compile(pattern)) for kind, pattern in PATTERNS]
SKIP_DIRS = {'.git', '__pycache__', 'node_modules'}

def tree_files(root):
    for path in sorted(root.rglob('*')):
        relative = path.relative_to(root)
        if path.is_file() and not SKIP_DIRS.intersection(relative.parts):
            yield relative.as_posix(), path.read_bytes

def commit_files(root, commit):
    def git(*args):
        return subprocess.run(['git', '-C', str(root), *args], capture_output=True, check=True).stdout
    sha = git('rev-parse', '--verify', commit + '^{commit}').decode().strip()
    print(f'scrub.py: commit {sha}')
    for name in git('ls-tree', '-r', '-z', '--name-only', sha).decode('utf-8').split('\0'):
        if name:
            yield name, lambda name=name: git('show', f'{sha}:{name}')

def scan(files):
    findings = 0
    for name, read in files:
        data = read()
        if b'\0' in data[:8000]:
            continue
        for number, line in enumerate(data.decode('utf-8', 'replace').splitlines(), 1):
            for kind, pattern in PATTERNS:
                if pattern.search(line):
                    print(f'{name}:{number}: {kind}')
                    findings += 1
    print(f'total: {findings} findings')
    return 1 if findings else 0

def main(args):
    if len(args) not in (1, 3) or (len(args) == 3 and args[1] != '--commit'):
        raise ValueError('usage: scrub.py <folder> [--commit <ref>]')
    root = Path(args[0]).resolve()
    if not root.is_dir():
        raise ValueError('not a folder')
    return scan(commit_files(root, args[2]) if len(args) == 3 else tree_files(root))

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    try:
        sys.exit(main(sys.argv[1:]))
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print('scrub.py: ' + str(error).replace('\n', ' '), file=sys.stderr)
        sys.exit(2)
