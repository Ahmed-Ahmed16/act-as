"""Read language folders only, no network.

Inputs: required --lang folder, optional --changed-files JSON list of paths or
objects with path/filename fields, --report values, and --base-lang folder.
Default output is a JSON gap list, including unreadable files. --report values
prints an object with gaps, values (placeholders and plural form counts),
placeholder_gaps (ignoring :count), no_letters (ar/en script checks),
locales_not_checked_for_letters, and changed_old_values (shared string keys).
--base-lang requires --report values; without it changed_old_values is empty.
Nonstring values and PHP expressions have no text and skip value checks.
Exit 0 prints a report. Bad input exits 2 with 1 stderr line and no stdout.
"""

import argparse
import json
import os
import re
import sys
import unicodedata
from pathlib import Path


TOKEN = re.compile(r'''\s+|//[^\n]*|\#[^\n]*|/\*.*?\*/|<\?php\b|\?>|=>|'(?:\\.|[^'\\])*'|"(?:\\.|[^"\\])*"|[+-]?\d+|[\w\\]+|.''', re.S)
PLACEHOLDER = re.compile(r'(?<![\w:]):[A-Za-z_][A-Za-z0-9_]*')
LETTER_SCRIPTS = {'ar': 'ARABIC', 'en': 'LATIN'}


def php_tokens(text):
    tokens = []
    for match in TOKEN.finditer(text):
        token = match.group()
        if token.isspace() or token.startswith(('//', '#', '/*')):
            continue
        if token in ("'", '"') or text.startswith('/*', match.start()):
            raise ValueError('unfinished string or comment')
        tokens.append(token)
    return tokens


def php_key(token):
    if re.fullmatch(r'[+-]?\d+', token):
        return str(int(token))
    if not token.startswith(("'", '"')):
        raise ValueError('expected string or integer key')
    if token[0] == "'":
        return re.sub(r"\\([\\'])", r'\1', token[1:-1])
    escapes = {'n': '\n', 'r': '\r', 't': '\t', 'v': '\v', 'e': '\x1b', 'f': '\f',
               '\\': '\\', '"': '"', '$': '$'}
    def unescape(match):
        code = match.group()[1:]
        if code.startswith('x'):
            return chr(int(code[1:], 16))
        if code[0] in '01234567':
            return chr(int(code, 8) % 256)
        return escapes.get(code, match.group())
    return re.sub(r'\\(?:x[0-9a-fA-F]{1,2}|[0-7]{1,3}|.)', unescape, token[1:-1])


class PhpArray:
    def __init__(self, text):
        self.tokens = php_tokens(text)
        self.position = 0

    def peek(self):
        return self.tokens[self.position] if self.position < len(self.tokens) else ''

    def take(self):
        token = self.peek()
        if not token:
            raise ValueError('unexpected end of PHP')
        self.position += 1
        return token

    def expect(self, expected):
        if self.take() != expected:
            raise ValueError('expected ' + expected)

    def array_keys(self):
        return set(self.array_values())

    def array_values(self):
        # Cases: empty arrays, leaves, nested arrays, trailing commas, missing delimiters.
        opening = self.take()
        if opening.lower() == 'array':
            self.expect('(')
        elif opening != '[':
            raise ValueError('expected array')
        closing = ')' if opening.lower() == 'array' else ']'
        leaves = {}
        while self.peek() != closing:
            key = php_key(self.take())
            self.expect('=>')
            if self.peek() == '[' or self.peek().lower() == 'array':
                leaves.update((key + '.' + child, text) for child, text in self.array_values().items())
            else:
                start = self.position
                self.skip_expression(closing)
                token = self.tokens[start]
                leaves[key] = (php_key(token) if self.position == start + 1
                               and token.startswith(("'", '"')) else None)
            if self.peek() == closing:
                break
            self.expect(',')
        self.expect(closing)
        return leaves

    def skip_expression(self, closing):
        start = self.position
        previous = ''
        while self.peek() not in ('', ',', closing):
            token = self.take()
            if token in ('(', '[', '{'):
                self.skip_nested(token)
            elif token in (')', ']', '}', ';', '=>', '<?php', '?>'):
                raise ValueError('invalid value')
            elif token.startswith(("'", '"')) and previous.startswith(("'", '"')):
                raise ValueError('missing value operator')
            previous = token
        if start == self.position or previous in ('.', '+', '-', '*', '/', '%', '=', '&', '|', '?', ':'):
            raise ValueError('unfinished value')

    def skip_nested(self, opening):
        pairs = {'(': ')', '[': ']', '{': '}'}
        stack = [pairs[opening]]
        while stack:
            token = self.take()
            if token in pairs:
                stack.append(pairs[token])
            elif token in (')', ']', '}'):
                if stack.pop() != token:
                    raise ValueError('mismatched value delimiter')
            elif token in (';', '<?php', '?>'):
                raise ValueError('invalid value')


def php_keys(text):
    return set(php_values(text))


def php_values(text):
    parser = PhpArray(text)
    parser.expect('<?php')
    parser.expect('return')
    translations = parser.array_values()
    parser.expect(';')
    if parser.peek() == '?>':
        parser.take()
    if parser.peek():
        raise ValueError('unexpected text after array')
    return translations


def raise_walk_error(error):
    raise error


def translation_files(lang):
    locales, files = set(), []
    for path in sorted(lang.iterdir()):
        if path.is_dir():
            locales.add(path.name)
            for folder, _, names in os.walk(path, onerror=raise_walk_error):
                for name in sorted(names):
                    if name.endswith('.php'):
                        group = (Path(folder) / name).relative_to(path).as_posix()
                        files.append((Path(folder) / name, path.name, 'php', group))
        elif path.suffix == '.json':
            locales.add(path.stem)
            files.append((path, path.stem, 'json', '<locale>.json'))
    return locales, files


def invalid_json_constant(token):
    raise ValueError('invalid JSON constant ' + token)


def file_keys(path, shape):
    return set(file_values(path, shape))


def file_values(path, shape):
    text = path.read_text(encoding='utf-8-sig')
    if shape == 'php':
        return php_values(text)
    translations = json.loads(text, parse_constant=invalid_json_constant)
    if not isinstance(translations, dict):
        raise ValueError('JSON must be an object')
    return {key: text if isinstance(text, str) else None for key, text in translations.items()}


def changed_paths(path):
    if path is None:
        return []
    entries = json.loads(path.read_text(encoding='utf-8-sig'))
    if not isinstance(entries, list):
        raise ValueError('changed files must be a list')
    paths = []
    for entry in entries:
        if isinstance(entry, dict):
            entry = entry.get('path', entry.get('filename'))
        if not isinstance(entry, str):
            raise ValueError('changed files must contain paths')
        paths.append(entry.replace('\\', '/'))
    return paths


def touched_file(shape, filename, locales, changed):
    candidates = [locale + '.json' for locale in locales] if shape == 'json' else [filename]
    return 'yes' if any(path == suffix or path.endswith('/' + suffix)
                        for path in changed for suffix in candidates) else 'no'


def read_translations(lang):
    locales, files = translation_files(lang)
    groups, excluded, entries = {}, {}, []
    for path, locale, shape, filename in files:
        group = (shape, filename)
        try:
            translations = file_values(path, shape)
        except (OSError, UnicodeError, ValueError, RecursionError) as error:
            excluded.setdefault(group, set()).add(locale)
            reason = ' '.join(str(error).splitlines())[:120]
            entries.append(dict(file=path.relative_to(lang).as_posix(), shape=shape,
                                unreadable=True, reason=reason))
        else:
            groups.setdefault(group, {}).setdefault(locale, {}).update(translations)
    return locales, groups, excluded, entries


def key_gaps(lang, changed):
    return gaps_from_catalog(read_translations(lang), changed)


def gaps_from_catalog(catalog, changed):
    locales, groups, excluded, unreadable = catalog
    entries = list(unreadable)
    for (shape, filename), per_locale in sorted(groups.items()):
        eligible = locales - excluded.get((shape, filename), set())
        all_keys = set().union(*per_locale.values())
        for key in sorted(all_keys):
            present = {locale for locale, keys in per_locale.items() if key in keys}
            missing = eligible - present
            if missing:
                identity = key if shape == 'json' else filename[:-4] + '.' + key
                entries.append(dict(key=identity, shape=shape, file=filename,
                                    locales_with=sorted(present), locales_missing=sorted(missing),
                                    touched_by_pr=touched_file(shape, filename, locales, changed)))
    return sorted(entries, key=lambda entry: (entry['shape'], entry.get('key', ''), entry['file']))


def string_values(catalog):
    return {(shape, filename, key, locale): text
            for (shape, filename), per_locale in catalog[1].items()
            for locale, translations in per_locale.items()
            for key, text in translations.items() if text is not None}


def value_identity(identity):
    shape, filename, key, locale = identity
    return dict(key=key if shape == 'json' else filename[:-4] + '.' + key,
                shape=shape, file=filename, locale=locale)


def placeholder_gaps(values):
    groups, gaps = {}, []
    for entry in values:
        group = (entry['key'], entry['shape'], entry['file'])
        groups.setdefault(group, {})[entry['locale']] = {name for name in entry['placeholders']
                                                       if name.lower() != ':count'}
    for (key, shape, filename), per_locale in groups.items():
        normalized = {locale: {name.lower() for name in names} for locale, names in per_locale.items()}
        all_names = set().union(*normalized.values())
        missing = sorted(locale for locale, names in normalized.items() if all_names - names)
        if len(per_locale) >= 2 and missing:
            gaps.append(dict(key=key, shape=shape, file=filename,
                             placeholders_by_locale={locale: sorted(names) for locale, names in per_locale.items()},
                             locales_missing_any=missing))
    return gaps


def letter_script(locale):
    return LETTER_SCRIPTS.get(re.split(r'[_-]', locale, maxsplit=1)[0])


def lacks_language_letters(text, locale):
    # Cases: no letters, another script only, matching letters, mixed scripts.
    script = letter_script(locale)
    if script is None:
        return False
    letters = [ch for ch in PLACEHOLDER.sub('', text) if ch.isalpha()]
    return bool(letters) and not any(unicodedata.name(ch, '').startswith(script) for ch in letters)


def values_report(catalog, changed, base_lang):
    head = string_values(catalog)
    base = string_values(read_translations(base_lang)) if base_lang is not None else {}
    values, no_letters, changed_old = [], [], []
    for identity, text in sorted(head.items()):
        entry = value_identity(identity)
        # Range prefixes do not change the number of pipe parts, even empty ones.
        plural_forms = len(text.split('|')) if '|' in text else None
        values.append(dict(entry, placeholders=sorted(set(PLACEHOLDER.findall(text))), plural_forms=plural_forms))
        if lacks_language_letters(text, entry['locale']):
            no_letters.append(entry)
        if identity in base and base[identity] != text:
            changed_old.append(dict(entry, old=base[identity], new=text))
    return dict(gaps=gaps_from_catalog(catalog, changed), values=values,
                placeholder_gaps=placeholder_gaps(values), no_letters=no_letters,
                locales_not_checked_for_letters=sorted(locale for locale in catalog[0] if letter_script(locale) is None),
                changed_old_values=changed_old)


class Arguments(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, 'translation_keys.py: ' + ' '.join(message.splitlines()) + '\n')


def main(args):
    parser = Arguments(description='List gaps between translation key sets.', allow_abbrev=False)
    parser.add_argument('--lang', type=Path, required=True)
    parser.add_argument('--changed-files', type=Path)
    parser.add_argument('--report', choices=['values'])
    parser.add_argument('--base-lang', type=Path)
    options = parser.parse_args(args)
    if not options.lang.is_dir():
        parser.error('lang must be a readable directory')
    if options.base_lang is not None:
        if options.report != 'values':
            parser.error('base-lang requires --report values')
        if not options.base_lang.is_dir():
            parser.error('base-lang must be a readable directory')
    try:
        changed = changed_paths(options.changed_files)
        if options.report == 'values':
            entries = values_report(read_translations(options.lang), changed, options.base_lang)
        else:
            entries = key_gaps(options.lang, changed)
    except (OSError, UnicodeError, ValueError, RecursionError) as error:
        parser.error(str(error))
    print(json.dumps(entries, ensure_ascii=True))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
