"""By page groups distinct keys, joining controllers to 1 literal Blade view.
Dynamic or multiple view names stay unlinked. No PHP runs.
See translation_health_scan for G4 rules and source scan limits.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from translation_keys import changed_paths
from translation_health_scan import TOKEN, arguments, literal, scan


class Arguments(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, 'translation_health.py: ' + ' '.join(message.splitlines()) + '\n')


def keys_report(lang, extra=()):
    command = [sys.executable, '-B', str(Path(__file__).with_name('translation_keys.py')),
               '--lang', str(lang), '--report', 'values', *map(str, extra)]
    run = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
    if run.returncode:
        sys.stderr.write(' '.join(run.stderr.splitlines()) + '\n')
        raise SystemExit(2)
    report = json.loads(run.stdout)
    required = ('gaps', 'values', 'placeholder_gaps', 'no_letters',
                'locales_not_checked_for_letters', 'changed_old_values')
    if not isinstance(report, dict) or any(not isinstance(report.get(key), list) for key in required):
        raise ValueError('invalid translation report')
    return report


def identity(entry):
    return entry['shape'], entry['file'], entry['key']


def rendered_views(text):
    # Cases: no call, 1 literal, repeated literal, dynamic name, multiple views.
    tokens = [(match.group(), match.start()) for match in TOKEN.finditer(text)
              if not match.group().startswith(('//', '#', '/*'))]
    names = set()
    for index, (token, _) in enumerate(tokens):
        if token != '(':
            continue
        context = [part for part, _ in tokens[max(0, index - 3):index]]
        if context != ['View', '::', 'make'] and not (
                context[-1:] == ['view'] and context[-2:-1] not in (['::'], ['$'])):
            continue
        parts, _ = arguments(tokens, index)
        names.add(literal(parts[0]) if parts else None)
    return names


def controller_pages(repo, calls):
    pages = {}
    for path in sorted({call['path'] for call in calls if call['path'].startswith('app/Http/Controllers/')}):
        names = rendered_views((repo / path).read_text(encoding='utf-8-sig'))
        if len(names) != 1:
            continue
        name = next(iter(names))
        if name is None or not re.fullmatch(r'[\w-]+(?:[./][\w-]+)*', name):
            continue
        view = 'resources/views/' + name.replace('.', '/') + '.blade.php'
        if (repo / view).is_file():
            pages[path] = view
    return pages


def health(report, base, source, pages):
    calls, raw, visible = source
    used, locales_by_key, forms = {}, {}, {}
    for call in calls:
        if call['key'] is not None:
            used.setdefault(call['key'], set()).add(f"{call['path']}:{call['line']}")
    for entry in report['values']:
        locales_by_key.setdefault(entry['key'], set()).add(entry['locale'])
        forms.setdefault(entry['key'], {})[entry['locale']] = entry['plural_forms']
    locales = set().union(*locales_by_key.values())
    def page(key):
        paths = {pages.get(path, path) for location in used.get(key, [])
                 for path in [location.rsplit(':', 1)[0]]}
        return next(iter(paths)) if len(paths) == 1 else 'shared' if paths else 'no use found'
    base_ids = {identity(entry) for entry in base['values']} if base is not None else set()
    groups = {}
    for entry in report['values']:
        if identity(entry) not in base_ids:
            groups.setdefault(page(entry['key']), set()).add(entry['key'])
    unused = set(locales_by_key) - set(used)
    prefixes = [call['prefix'] for call in calls if call['key'] is None and call['prefix']
                and call['name'] in ('__', 'trans')]
    variable = {key for key in unused if any(key.startswith(prefix) for prefix in prefixes)}
    choice_keys = {call['key'] for call in calls if call['name'] == 'trans_choice' and call['key'] is not None}
    return dict(
        check1=[dict(entry, page=page(entry.get('key'))) for entry in report['gaps']],
        check2=[dict(key=key, locales_missing=sorted(locales - locales_by_key.get(key, set())), used_at=sorted(used[key]))
                for key in sorted(used) if key not in locales_by_key or locales - locales_by_key[key]],
        check3=report['placeholder_gaps'],
        check4=[dict(key=key, forms_by_locale=forms.get(key, {})) for key in sorted(choice_keys)],
        check5=report['changed_old_values'],
        check6=dict(variable=sorted(variable), no_trace=sorted(unused - variable),
                    dynamic_call_sites=sorted({f"{call['path']}:{call['line']}" for call in calls if call['key'] is None})),
        check7=raw, check8={key: report[key] for key in ('no_letters', 'locales_not_checked_for_letters')},
        g4_literal_text=visible,
        by_page=dict(scope='new keys' if base is not None else 'all keys',
                     groups={group: sorted(keys) for group, keys in sorted(groups.items())}),
        not_checked=[entry['file'] + ' unreadable' for entry in report['gaps'] if entry.get('unreadable')])


def main(args):
    parser = Arguments(description='List translation health pointers.', allow_abbrev=False)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--lang', type=Path)
    parser.add_argument('--base-lang', type=Path)
    parser.add_argument('--changed-files', type=Path)
    options = parser.parse_args(args)
    try:
        repo = options.repo.resolve()
        if not repo.is_dir():
            parser.error('repo must be a readable directory')
        next(repo.iterdir(), None)
        lang = (repo / options.lang).resolve() if options.lang is not None else repo / 'lang'
        if options.lang is None and not lang.is_dir():
            lang = repo / 'resources/lang'
        extra = [part for flag, path in (('--changed-files', options.changed_files), ('--base-lang', options.base_lang))
                 if path is not None for part in (flag, path)]
        report = keys_report(lang, extra)
        base = keys_report(options.base_lang) if options.base_lang is not None else None
        changed = changed_paths(options.changed_files) if options.changed_files is not None else None
        source = scan(repo, changed)
        output = health(report, base, source, controller_pages(repo, source[0]))
        prefix = lang.relative_to(repo).as_posix().rstrip('/') + '/' if lang.is_relative_to(repo) else None
        output['no_translation_files_changed'] = prefix is not None and changed is not None and not any(
            path.startswith(prefix) for path in changed)
    except (OSError, UnicodeError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(output, ensure_ascii=True))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
