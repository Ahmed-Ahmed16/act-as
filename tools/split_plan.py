import hashlib
import json
import re
import sys
from pathlib import Path

if __package__:
    from .hunk_text import HunkDifference, collect_hunks
    from .packet_check import INPUT_SHAPES, input_fields
    from .size_counter import ArgumentParser, GitError, git_bytes
    from .split_checks import checked_index, key_failures, mark_failures, metadata_failures, saved_plan, split_failures
else:
    from hunk_text import HunkDifference, collect_hunks
    from packet_check import INPUT_SHAPES, input_fields
    from size_counter import ArgumentParser, GitError, git_bytes
    from split_checks import checked_index, key_failures, mark_failures, metadata_failures, saved_plan, split_failures


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
        if args and args[0] == 'build':
            parser = ArgumentParser(allow_abbrev=False)
            parser.add_argument('packet', type=Path)
            return build(parser.parse_args(args[1:]).packet)
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
    except (ValueError, OSError, UnicodeError, GitError) as error:
        print('split_plan: ' + ' '.join(str(error).splitlines()), file=sys.stderr)
        return 2


def build_schema(document, schema, name):
    if input_fields(document, schema, name):
        raise ValueError(name + ' has missing fields')


def build_inputs(raw):
    files, hunks, saved, plan = [json.loads(contents) for contents in raw]
    build_shape(plan)
    file_row = dict(INPUT_SHAPES['files.json']['files'], **dict.fromkeys(('path', 'old_path', 'status', 'kind'), str))
    build_schema(files, dict(files=file_row), 'files.json')
    hunk = dict(id=str, path=str, kind=str, counted=int, lines=int, deleted=int, language=bool)
    build_schema(hunks, dict(base=str, head=str, files_sha256=str, hunks=hunk, ops=hunk), 'hunks.json')
    build_schema(saved, dict(base=str, head=str), 'size-count.json')
    row = dict(name=str, hunks=[str], needs=[str])
    build_schema(plan, dict(groups=row, parts=row, unplaced=[str]), 'split-input.json')
    key = dict(shape=str, key=str, page=str, pieces=[str])
    for group in plan['groups'] + plan['parts'] + [dict(keys=plan.get('unplaced_keys', []))]:
        build_schema(dict(keys=group.get('keys', [])), dict(keys=key), 'keys')
        for record in group.get('keys', []):
            if record['shape'] not in ('json', 'php') or not record['key'].strip():
                raise ValueError('split-input.json has an invalid key identity')
    build_schema(plan, dict(marks=dict(mark=str, pieces=[str]), loop_notes=[str]), 'split-input.json')
    for field in ('ci', 'main'):
        if not isinstance(plan.get(field), dict):
            raise ValueError('split-input.json needs a ' + field + ' object')
    build_schema(dict(workflows=plan['ci'].get('workflows', [])), dict(workflows={}), 'ci')
    for group in plan['groups'] + plan['parts']:
        build_schema(dict(links=group.get('links', []), pages=group.get('pages', [])),
                     dict(links=dict(piece=str, **{'for': {}}), pages=dict(name=str)), 'group')
    return files, hunks, saved, plan


def build_shape(document):
    collections = dict.fromkeys('groups parts keys unplaced_keys marks pages links workflows related'.split(), {})
    collections.update(dict.fromkeys('hunks pieces unplaced needs entry_points loop_notes'.split(), [str]))
    scalars = dict(piece=str, part=str, summary=str, rebuild=str, how=str, keys_found=int)
    nullable = ('part', 'keys_check', 'unplaced_keys_check', 'stays_over')
    if isinstance(document, dict):
        for field, child in document.items():
            if child is None and field in nullable:
                continue
            if field in collections:
                build_schema({field: child}, {field: collections[field]}, 'split-input')
            if field in scalars and type(child) is not scalars[field]:
                raise ValueError('split-input.json has an invalid ' + field)
            if field in nullable and field != 'part' and not isinstance(child, dict):
                raise ValueError('split-input.json needs an object for ' + field)
            build_shape(child)
    elif isinstance(document, list):
        for child in document:
            build_shape(child)


def build(packet):
    names = ('files.json', 'hunks.json', 'runs/size-count.json', 'split-input.json')
    raw = [(packet / name).read_bytes() for name in names]
    files, hunks, saved, plan = build_inputs(raw)
    hashes = dict(zip(('files_sha256', 'hunks_sha256', 'counter_sha256', 'input_sha256'),
                      (hashlib.sha256(contents).hexdigest() for contents in raw)))
    index = checked_index(hunks, plan)
    failures = (split_failures(files, hunks, plan) + mark_failures(plan, index) + key_failures(plan, index)
                + metadata_failures(hunks, saved, hashes['files_sha256'], plan))
    for rule, message in failures:
        print(f'RULE {rule}: {message}')
    if failures:
        return 1
    document = dict(saved_plan(plan, index), base=hunks['base'], head=hunks['head'],
                    **{field: hashes[field] for field in ('input_sha256', 'hunks_sha256', 'files_sha256')})
    (packet / 'split-plan.json').write_bytes((json.dumps(document, indent=2) + '\n').encode('utf-8'))
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    sys.exit(main(sys.argv[1:]))
