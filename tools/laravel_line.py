import json
import re
import sys
from pathlib import Path


def json_object(path):
    # Missing or unreadable sources use the next source, as do bad JSON shapes.
    try:
        document = json.loads(path.read_text(encoding='utf-8'))
        return document if isinstance(document, dict) else {}
    except (OSError, UnicodeError, ValueError):
        return {}


def project_text(text):
    # Cases: non string, blank, comma runs, and whitespace runs.
    return re.sub(r'[,\s]+', ' ', text).strip() if isinstance(text, str) else ''


def laravel_line(lock, manifest):
    packages = json_object(lock).get('packages', [])
    for package in packages if isinstance(packages, list) else []:
        if isinstance(package, dict) and package.get('name') == 'laravel/framework':
            raw_version = package.get('version')
            if isinstance(raw_version, str) and raw_version:
                version = project_text(raw_version)
                if not version:
                    break
                return f"Laravel: project {re.sub(r'^v(?=[0-9])', '', version, count=1)}, card docs 12.x"
    require = json_object(manifest).get('require', {})
    constraint = project_text(require.get('laravel/framework')) if isinstance(require, dict) else ''
    if constraint:
        return f'Laravel: project {constraint}, card docs 12.x, from the constraint, not the lock'
    return 'Laravel: project ___ (laravel version), card docs 12.x'


def main(args):
    if len(args) != 2:
        print('laravel_line: expected composer.lock and composer.json', file=sys.stderr)
        return 2
    print(laravel_line(*map(Path, args)))
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    sys.exit(main(sys.argv[1:]))
