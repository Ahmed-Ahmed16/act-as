import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


class GitError(RuntimeError):
    pass


def git_bytes(repo, *args):
    try:
        run = subprocess.run(['git', '-C', str(repo), *args], capture_output=True)
    except OSError as error:
        raise GitError(str(error)) from error
    if run.returncode:
        raise GitError(run.stderr.decode('utf-8', 'replace').splitlines()[0]
                       if run.stderr else f'git exited {run.returncode}')
    return run.stdout


def changed_files(options):
    tokens = iter(git_bytes(options.repo, 'diff', '-M', '--name-status', '-z',
                           options.base, options.head).decode('utf-8', 'surrogateescape').split('\0')[:-1])
    files = []
    for status in tokens:
        path = next(tokens)
        old_path = path if status[0] in 'RC' else None
        if old_path is not None:
            path = next(tokens)
        files.append(dict(path=path, old_path=old_path, status=status, areas=[]))
    return sorted(files, key=lambda row: row['path'])


def parse_page(contents):
    lines = contents.decode('utf-8').replace('\r', '').split('\n')
    cover_line = next((line for line in lines[:5] if line.startswith('Covers:')), '')
    covers_ok = cover_line.startswith('Covers:')
    covers = [entry.strip(' `\t') for entry in cover_line[7:].split(',')
              if entry.strip(' `\t')] if covers_ok else []
    covers_patterns = sorted(entry for entry in covers if any(char in entry for char in '*?[]{}'))
    covers = [entry for entry in covers if entry not in covers_patterns]
    not_checked = ['Covers entry is a pattern'] if covers_patterns else []
    checked_at = next((line.partition(':')[2].strip() for line in lines
                       if line.startswith('Checked at:')), None)
    rules = []
    for line in lines:
        rule = re.match(r'^R(\d+)\.', line)
        if rule:
            statuses = re.findall(r'\*\*(match|gap|owner|open)\*\*', line, re.I)
            status = statuses[0].lower() if len(statuses) == 1 else ('multiple' if statuses else 'none')
            rules.append(dict(id='R' + rule[1], status=status))
            if len(statuses) != 1:
                reason = f'{len(statuses)} statuses' if statuses else 'no status'
                not_checked.append(f'rule R{rule[1]} has {reason}')
    return dict(checked_at=checked_at, covers=sorted(covers), covers_ok=covers_ok, rules=rules,
                covers_patterns=covers_patterns, not_checked=not_checked,
                area_incomplete=bool(not_checked) or not covers_ok)


def load_pages(options, commit):
    paths = git_bytes(options.repo, 'ls-tree', '--name-only', '-z', commit,
                      'docs/business-rules/').decode('utf-8', 'surrogateescape').split('\0')
    drafts = {path.stem: path for path in options.drafts.glob('*.md') if path.is_file()} if options.drafts else {}
    defaults = {Path(path).stem: path for path in paths if path.endswith('.md')}
    pages = []
    for area in sorted(defaults.keys() | drafts.keys()):
        if area in defaults:
            path = defaults[area]
            contents = git_bytes(options.repo, 'show', commit + ':' + path)
            source, page_commit = 'default', commit
        else:
            path = str(drafts[area])
            contents = drafts[area].read_bytes()
            source, page_commit = 'draft', 'sha256:' + hashlib.sha256(contents).hexdigest()
        page = dict(area=area, source=source, page=path, commit=page_commit,
                    draft_also_exists=area in drafts and area in defaults,
                    **parse_page(contents), files=[])
        pages.append((page, contents))
    return pages


def covers_path(entry, path):
    return path is not None and (path == entry or path.startswith(entry if entry.endswith('/') else entry + '/'))


def mapped_pages(files, pages):
    touched = []
    for page, contents in pages:
        paths = [row['path'] for row in files if page['covers_ok'] and any(
            covers_path(entry, path) for entry in page['covers']
            for path in (row['path'], row['old_path']))]
        if paths:
            touched.append((dict(page, files=paths), contents))
    return touched


def mapped_files(files, pages):
    return [dict(row, areas=[page['area'] for page, _ in pages if row['path'] in page['files']])
            for row in files]


def save_pages(out, pages):
    # Boundaries: first run, empty update, existing areas, malformed saved entries.
    manifest_path = out / 'rules-pages.json'
    manifest = (json.loads(manifest_path.read_text(encoding='utf-8'))
                if manifest_path.exists() else {'areas': []})
    if not isinstance(manifest, dict) or not isinstance(manifest.get('areas'), list):
        raise ValueError('saved rules pages must be an object with an areas list')
    by_area = {}
    for page in manifest['areas']:
        if not isinstance(page, dict) or not isinstance(page.get('area'), str) or not page['area']:
            raise ValueError('saved rules page must have an area name')
        if page['area'] in by_area:
            raise ValueError('duplicate saved rules page area: ' + page['area'])
        by_area[page['area']] = page
    for page, _ in pages:
        by_area[page['area']] = {key: page[key] for key in ('area', 'page', 'commit', 'rules')}
    manifest['areas'] = list(by_area.values())
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    for page, contents in pages:
        (out / 'runs' / f'rules-page-{page["area"]}.md').write_bytes(contents)


def write_packet(options, commit, files, pages):
    touched = mapped_pages(files, pages)
    selected = touched
    if options.area is not None:
        if set(options.area) - {page['area'] for page, _ in touched}:
            raise ValueError('requested area is not touched by this diff')
        selected = [(page, contents) for page, contents in touched if page['area'] in options.area]
    files = mapped_files(files, touched)
    unmapped = [dict(path=row['path'], old_path=row['old_path']) for row in files if not row['areas']]
    report = dict(base=options.base, head=options.head, default_ref=options.default_ref,
                  default_commit=commit, files=files, no_area_found=unmapped,
                  areas=[page for page, _ in touched],
                  pages_with_patterns=[page for page, _ in pages if page['covers_patterns']],
                  pages_without_covers=[page['area'] for page, _ in pages if not page['covers_ok']])
    runs = options.out / 'runs'
    runs.mkdir(parents=True, exist_ok=True)
    (runs / 'business-map.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    save_pages(options.out, selected)
    print(f'business_pages: {len(touched)} touched areas, {len(unmapped)} files with no area found')


def main(args):
    parser = argparse.ArgumentParser(allow_abbrev=False)
    for flag in ('repo', 'base', 'head', 'default-ref', 'out'):
        parser.add_argument('--' + flag, required=True, type=Path if flag in ('repo', 'out') else str)
    parser.add_argument('--drafts', type=Path)
    parser.add_argument('--area', action='append', help='update only this area; may be repeated')
    options = parser.parse_args(args)
    if any(not ref or ref.startswith('-') for ref in (options.base, options.head, options.default_ref)):
        parser.error('base, head and default-ref must be git revisions')
    if options.drafts is not None and not options.drafts.is_dir():
        parser.error('drafts is missing or not a folder')
    try:
        commit = git_bytes(options.repo, 'rev-parse', '--verify', '--end-of-options',
                           options.default_ref + '^{commit}').decode('ascii').strip()
        files = changed_files(options)
        pages = load_pages(options, commit)
        write_packet(options, commit, files, pages)
        return 0
    except GitError as error:
        print('business_pages: error: ' + str(error).splitlines()[0], file=sys.stderr)
        return 1
    except (OSError, ValueError) as error:
        print('business_pages: error: ' + str(error).splitlines()[0], file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    sys.exit(main(sys.argv[1:]))
