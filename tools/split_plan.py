import hashlib
import json
import re
import sys
from pathlib import Path

if __package__:
    from .hunk_text import HunkDifference, collect_hunks
    from .packet_check import INPUT_SHAPES, input_fields
    from .size_counter import ArgumentParser, GitError, git_bytes
else:
    from hunk_text import HunkDifference, collect_hunks
    from packet_check import INPUT_SHAPES, input_fields
    from size_counter import ArgumentParser, GitError, git_bytes


def arguments(args):
    parser = ArgumentParser(allow_abbrev=False)
    parser.add_argument('command', choices=['hunks'])
    parser.add_argument('--repo', required=True, type=Path)
    parser.add_argument('--base', required=True)
    parser.add_argument('--head', required=True)
    parser.add_argument('--packet', required=True, type=Path)
    parser.add_argument('--show')
    options = parser.parse_args(args)
    if any(not revision or revision.startswith('-') for revision in (options.base, options.head)):
        raise ValueError('base and head must be git revisions')
    return options


def main(args):
    try:
        options = arguments(args)
        raw_files = (options.packet / 'files.json').read_bytes()
        files = json.loads(raw_files)
        schema = {'files': dict(INPUT_SHAPES['files.json']['files'],
                               **dict.fromkeys(('path', 'old_path', 'status', 'kind'), str))}
        if input_fields(files, schema, 'files.json'):
            raise ValueError('files.json has missing fields')
        saved = json.loads((options.packet / 'runs/size-count.json').read_bytes())
        if not isinstance(saved, dict) or any(not isinstance(saved.get(key), str) for key in ('base', 'head')):
            raise ValueError('size-count.json needs base and head strings')
        commits = [git_bytes(options.repo, 'rev-parse', '--verify', revision + '^{commit}').decode().strip()
                   for revision in (options.base, options.head)]
        if any(not re.fullmatch(r'[0-9a-fA-F]{40}', saved[key])
               or saved[key].lower() != commit for key, commit in zip(('base', 'head'), commits)):
            print('RULE hunks-head: base and head must match the saved full commits')
            return 1
        hunks, ops, texts = collect_hunks(options.repo, *commits, files)
        if options.show is not None and options.show not in texts:
            raise ValueError('--show must name a hunk in this packet')
        document = dict(base=commits[0], head=commits[1], files_sha256=hashlib.sha256(raw_files).hexdigest(),
                        hunks=hunks, ops=ops)
        (options.packet / 'hunks.json').write_text(json.dumps(document, indent=2) + '\n', encoding='utf-8')
        for hunk in hunks:
            preview = texts[hunk['id']][0].decode('utf-8', 'replace').rstrip('\r\n')[:60]
            print(f"{hunk['id']} {hunk['path']} +{hunk['new_start']},{hunk['new_count']} {hunk['counted']} {preview}")
        if options.show is not None:
            for number, line in enumerate(texts[options.show], 1):
                print(f'L{number} ' + line.decode('utf-8', 'replace').rstrip('\r\n'))
        return 0
    except HunkDifference as error:
        print('RULE hunks-differ: ' + str(error))
        return 1
    except (ValueError, OSError, GitError) as error:
        print('split_plan: ' + ' '.join(str(error).splitlines()), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    sys.exit(main(sys.argv[1:]))
