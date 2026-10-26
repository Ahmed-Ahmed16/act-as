"""By page has scope and groups of distinct keys. See translation_health_scan for G4 rules and source scan limits. No PHP runs."""
import argparse
import json
import subprocess
import sys
from pathlib import Path
from translation_keys import changed_paths
from translation_health_scan import scan


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


def health(report, base, source):
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
        paths = {location.rsplit(':', 1)[0] for location in used.get(key, [])}
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
        lang = options.lang.resolve() if options.lang is not None else repo / 'lang'
        extra = [part for flag, path in (('--changed-files', options.changed_files), ('--base-lang', options.base_lang))
                 if path is not None for part in (flag, path)]
        report = keys_report(lang, extra)
        base = keys_report(options.base_lang) if options.base_lang is not None else None
        changed = changed_paths(options.changed_files) if options.changed_files is not None else None
        output = health(report, base, scan(repo, changed))
        prefix = lang.relative_to(repo).as_posix().rstrip('/') + '/' if lang.is_relative_to(repo) else None
        output['no_translation_files_changed'] = changed is not None and not any(
            path.startswith(prefix) for path in changed if prefix is not None)
    except (OSError, UnicodeError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(output, ensure_ascii=True))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
