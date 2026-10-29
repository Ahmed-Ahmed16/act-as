import hashlib
import re
from pathlib import PurePosixPath

if __package__:
    from .size_counter import changed_files, count_files, hunk_patch, non_public_blobs
else:
    from size_counter import changed_files, count_files, hunk_patch, non_public_blobs

HEADER = re.compile(rb'^@@ -\d+(?:,(\d+))? \+(\d+)(?:,(\d+))? @@[^\n]*\n', re.MULTILINE)


class HunkDifference(ValueError):
    pass


def patch_hunks(patch):
    headers = list(HEADER.finditer(patch))
    for index, header in enumerate(headers):
        end = headers[index + 1].start() if index + 1 < len(headers) else len(patch)
        changed = patch[header.end():end].split(b'\n')
        changed = [line + b'\n' for prefix in (b'-', b'+') for line in changed if line.startswith(prefix)]
        yield header, changed


def hunk_record(hunk_id, row, header, changed):
    return dict(id=hunk_id, **{key: row[key] for key in ('path', 'old_path', 'status', 'kind')},
                counted=len(changed) if row['kind'] == 'counted' else 0, lines=len(changed),
                deleted=int(header[1] or 1) if header else 0,
                new_start=int(header[2]) if header else 0, new_count=int(header[3] or 1) if header else 0,
                text_sha256=hashlib.sha256(b''.join(changed)).hexdigest(),
                language='lang' in PurePosixPath(row['path']).parts[:-1]
                and row['path'].endswith(('.json', '.php')))


def collect_hunks(repo, base, head, files):
    comparison = base + '...' + head
    _, rows = count_files(changed_files(repo, comparison), non_public_blobs(repo, head),
                         non_public_blobs(repo, base))
    records, ops, texts = [], [], {}
    for number, row in enumerate(rows, 1):
        for index, (header, changed) in enumerate(patch_hunks(hunk_patch(repo, comparison, row)), 1):
            hunk_id = f'f{number}h{index}'
            record = hunk_record(hunk_id, row, header, changed)
            row['hunks'].append(dict(id=hunk_id, counted_lines=record['counted']))
            records.append(record)
            texts[hunk_id] = changed
        if not row['hunks']:
            ops.append(hunk_record(f'f{number}op', row, None, []))
    if rows != files['files']:
        raise HunkDifference('hunk ids or counted lines differ from files.json')
    return records, ops, texts
