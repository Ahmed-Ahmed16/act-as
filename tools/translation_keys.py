"""Compare application translation keys; package translations under vendor are out of scope."""

import argparse
import json
import os
import re
import sys
from pathlib import Path


TOKEN = re.compile(r'''\s+|//[^\n]*|\#[^\n]*|/\*.*?\*/|<\?php\b|\?>|=>|'(?:\\.|[^'\\])*'|"(?:\\.|[^"\\])*"|[+-]?\d+|[\w\\]+|.''', re.S)


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
        # Cases: empty arrays, lists, mixed keys, nesting, trailing commas, missing delimiters.
        opening = self.take()
        if opening.lower() == 'array':
            self.expect('(')
        elif opening != '[':
            raise ValueError('expected array')
        closing = ')' if opening.lower() == 'array' else ']'
        leaves = set()
        # PHP 8.3 also advances from a first negative integer key.
        next_index = None
        while self.peek() != closing:
            if self.position + 1 < len(self.tokens) and self.tokens[self.position + 1] == '=>':
                key = php_key(self.take())
                self.expect('=>')
                if re.fullmatch(r'0|-?[1-9]\d*', key) and (next_index is None or int(key) >= next_index):
                    next_index = int(key) + 1
            else:
                if next_index is None:
                    next_index = 0
                key = str(next_index)
                next_index += 1
            if self.peek() == '[' or self.peek().lower() == 'array':
                leaves.update(key + '.' + child for child in self.array_keys())
            else:
                self.skip_expression(closing)
                leaves.add(key)
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
    parser = PhpArray(text)
    parser.expect('<?php')
    parser.expect('return')
    keys = parser.array_keys()
    parser.expect(';')
    if parser.peek() == '?>':
        parser.take()
    if parser.peek():
        raise ValueError('unexpected text after array')
    return keys


def raise_walk_error(error):
    raise error


def translation_files(lang):
    locales, files = set(), []
    for path in sorted(lang.iterdir()):
        if path.is_dir() and path.name != 'vendor':
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
    text = path.read_text(encoding='utf-8-sig')
    if shape == 'php':
        return php_keys(text)
    translations = json.loads(text, parse_constant=invalid_json_constant)
    if not isinstance(translations, dict):
        raise ValueError('JSON must be an object')
    return set(translations)


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
    relative_paths = ([locale + '.json' for locale in locales] if shape == 'json'
                      else [locale + '/' + filename for locale in locales])
    candidates = set(relative_paths)
    if shape == 'php':
        candidates.add(filename)
    lang_paths = ['lang/' + path for path in relative_paths]
    return 'yes' if any(path in candidates or path == lang_path or path.endswith('/' + lang_path)
                        for path in changed for lang_path in lang_paths) else 'no'


def key_gaps(lang, changed):
    locales, files = translation_files(lang)
    groups, excluded, entries = {}, {}, []
    for path, locale, shape, filename in files:
        group = (shape, filename)
        try:
            keys = file_keys(path, shape)
        except (OSError, UnicodeError, ValueError, RecursionError) as error:
            excluded.setdefault(group, set()).add(locale)
            reason = ' '.join(str(error).splitlines())[:120]
            entries.append(dict(file=path.relative_to(lang).as_posix(), shape=shape,
                                unreadable=True, reason=reason))
        else:
            groups.setdefault(group, {}).setdefault(locale, set()).update(keys)
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


class Arguments(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, 'translation_keys.py: ' + ' '.join(message.splitlines()) + '\n')


def main(args):
    parser = Arguments(description='List gaps between translation key sets.', allow_abbrev=False)
    parser.add_argument('--lang', type=Path, required=True)
    parser.add_argument('--changed-files', type=Path)
    options = parser.parse_args(args)
    if not options.lang.is_dir():
        parser.error('lang must be a readable directory')
    try:
        entries = key_gaps(options.lang, changed_paths(options.changed_files))
    except (OSError, UnicodeError, ValueError, RecursionError) as error:
        parser.error(str(error))
    print(json.dumps(entries, ensure_ascii=True))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
