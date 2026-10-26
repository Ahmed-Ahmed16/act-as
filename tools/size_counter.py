import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

CAP = 300
EMPTY_BLOB = b'e69de29bb2d1d6434b8b29ae775ad8c2e48c5391'
GENERATED_PREFIXES = ('public/build/', 'vendor/', 'node_modules/', 'storage/',
                      'bootstrap/cache/', 'public/vendor/')
GENERATED_SUFFIXES = ('.min.js', '.min.css', '.map')
GENERATED_NAMES = {'_ide_helper.php', '_ide_helper_models.php', '.phpstorm.meta.php'}
LOCK_NAMES = {'composer.lock', 'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml'}
LEFT_OUT_NAMES = {'test': 'tests', 'lock': 'lock files', 'generated': 'generated', 'docs': 'docs'}
HUNK_HEADER = re.compile(rb'^@@ -\d+(?:,(\d+))? \+\d+(?:,(\d+))? @@', re.MULTILINE)


class GitError(RuntimeError):
    pass


class ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message)


def git_bytes(repo, *args):
    try:
        run = subprocess.run(['git', '-c', 'core.autocrlf=false', '-C', str(repo), *args],
                             capture_output=True)
    except OSError as error:
        raise GitError(f'git could not start: {error}') from error
    if run.returncode:
        reason = run.stderr.decode('utf-8', 'replace').strip()
        raise GitError(f'git failed (exit {run.returncode}): {reason}')
    return run.stdout


def changed_files(repo, comparison):
    raw = git_bytes(repo, 'diff', '--no-renames', '--raw', '-z', '--abbrev=40', comparison)
    numstat = git_bytes(repo, 'diff', '--no-renames', '--numstat', '-z', comparison)
    tokens = raw.split(b'\0')
    if tokens[-1] or len(tokens) % 2 != 1:
        raise GitError('git raw output has an unfinished file')
    files = {}
    for index in range(0, len(tokens) - 1, 2):
        metadata = tokens[index].split()
        if len(metadata) != 5:
            raise GitError('git raw output has bad file fields')
        path = tokens[index + 1]
        files[path] = {'path': path.decode('utf-8', 'surrogateescape'),
                       'status': metadata[4].decode('ascii'),
                       'old_blob': metadata[2], 'new_blob': metadata[3]}
    for record in numstat.split(b'\0'):
        if not record:
            continue
        fields = record.split(b'\t', 2)
        if len(fields) != 3 or fields[2] not in files:
            raise GitError('git numstat output does not match raw files')
        added, deleted, path = fields
        if any(count != b'-' and not count.isdigit() for count in (added, deleted)):
            raise GitError('git numstat output has bad line counts')
        files[path]['added'] = 0 if added == b'-' else int(added)
        files[path]['deleted'] = 0 if deleted == b'-' else int(deleted)
    if any('added' not in file for file in files.values()):
        raise GitError('git raw file is missing from numstat output')
    return list(files.values())


def non_public_blobs(repo, revision):
    blobs = set()
    for record in git_bytes(repo, 'ls-tree', '-r', '-z', revision).split(b'\0'):
        if not record:
            continue
        metadata, separator, path = record.partition(b'\t')
        fields = metadata.split()
        if not separator or len(fields) != 3:
            raise GitError('git tree output has bad file fields')
        if not path.startswith(b'public/') and fields[2] != EMPTY_BLOB:
            blobs.add(fields[2])
    return blobs


def is_generated_path(path):
    return (path.startswith(GENERATED_PREFIXES) or path.endswith(GENERATED_SUFFIXES)
            or path.rsplit('/', 1)[-1] in GENERATED_NAMES)


def file_kind(file, head_blobs, base_blobs):
    path = file['path']
    name = path.rsplit('/', 1)[-1]
    if is_generated_path(path):
        return 'generated'
    blob, blobs = ((file['old_blob'], base_blobs) if file['status'] == 'D'
                   else (file['new_blob'], head_blobs))
    if path.startswith('public/') and blob in blobs:
        return 'generated'
    if name in LOCK_NAMES or name.endswith('.lock'):
        return 'lock'
    if path.startswith('tests/') or '/tests/' in path or path.endswith('Test.php'):
        return 'test'
    if path.lower().endswith(('.md', '.markdown')):
        return 'docs'
    return 'counted'


def count_files(files, head_blobs, base_blobs):
    left_out = {name: {'lines': 0, 'files': 0} for name in LEFT_OUT_NAMES.values()}
    rows = []
    for file in files:
        kind = file_kind(file, head_blobs, base_blobs)
        lines = file['added'] + file['deleted']
        if kind != 'counted':
            left_out[LEFT_OUT_NAMES[kind]]['lines'] += lines
            left_out[LEFT_OUT_NAMES[kind]]['files'] += 1
        status = {'A': 'added', 'M': 'modified', 'D': 'deleted'}.get(
            file['status'], 'other:' + file['status'].lower())
        rows.append(dict(path=file['path'], old_path='', status=status, kind=kind,
                         counted_lines=lines if kind == 'counted' else 0, hunks=[]))
    added = sum(file['added'] for file in files)
    deleted = sum(file['deleted'] for file in files)
    counted = sum(row['counted_lines'] for row in rows)
    verdict = 'pass' if counted <= CAP else 'fail'
    exclusions = ', '.join(f'{name} {counts["lines"]} ({counts["files"]} files)'
                           for name, counts in left_out.items())
    report = dict(files=len(files), added=added, deleted=deleted, total_lines=added + deleted,
                  counted_total=counted, cap=CAP, verdict=verdict, left_out=left_out,
                  size_line=f'{verdict}, {counted} counted lines, cap {CAP}; left out: {exclusions}')
    return report, rows


def file_hunks(repo, comparison, row, file_index):
    # A literal path keeps names such as fruit [1].py from matching other files.
    patch = git_bytes(repo, 'diff', '--no-renames', '-U0', comparison,
                      '--', ':(literal)' + row['path'])
    hunks = []
    for number, header in enumerate(HUNK_HEADER.finditer(patch), 1):
        deleted, added = header.groups()
        lines = int(deleted) if deleted is not None else 1
        lines += int(added) if added is not None else 1
        hunks.append({'id': f'f{file_index}h{number}',
                      'counted_lines': lines if row['kind'] == 'counted' else 0})
    return hunks


def write_files(folder, rows):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'files.json').write_text(json.dumps({'files': rows}, indent=2) + '\n',
                                     encoding='utf-8')


def arguments(args):
    parser = ArgumentParser(allow_abbrev=False)
    parser.add_argument('--repo', required=True, type=Path)
    parser.add_argument('--base')
    parser.add_argument('--head', required=True)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--merged', action='store_true')
    options = parser.parse_args(args)
    if not options.base and not options.merged:
        raise ValueError('--base is required unless --merged is given')
    for revision in (options.base, options.head):
        if revision is not None and (not revision or revision.startswith('-')):
            raise ValueError('base and head must be git revisions')
    return options


def main(args):
    try:
        options = arguments(args)
        if options.merged and not options.base:
            print('not checked: PR already merged, base not proved')
            return 3
        if not options.repo.is_dir():
            raise ValueError('repo is missing or not a folder')
        comparison = options.base + '...' + options.head
        files = changed_files(options.repo, comparison)
        head_blobs = non_public_blobs(options.repo, options.head)
        base_blobs = non_public_blobs(options.repo, options.base)
        report, rows = count_files(files, head_blobs, base_blobs)
        report = dict(base=options.base, head=options.head, **report)
        if options.out is not None:
            for index, row in enumerate(rows, 1):
                row['hunks'] = file_hunks(options.repo, comparison, row, index)
                if sum(hunk['counted_lines'] for hunk in row['hunks']) != row['counted_lines']:
                    raise GitError('git hunk counts differ from numstat for ' + row['path'])
            write_files(options.out, rows)
        print(json.dumps(report))
        return 0
    except GitError as error:
        print('size_counter: ' + ' '.join(str(error).splitlines()), file=sys.stderr)
        return 1
    except (ValueError, OSError) as error:
        print('size_counter: ' + ' '.join(str(error).splitlines()), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    sys.exit(main(sys.argv[1:]))
