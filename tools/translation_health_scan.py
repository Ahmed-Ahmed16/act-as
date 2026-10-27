"""G4 checks plain strings at PHP message sinks and Blade text nodes.
Mask comments, tags, echoes, directives, PHP blocks, scripts and styles.
Do not resolve variables, includes, aliases, heredocs or logger types.
Exclude logger receivers named logger. Treat computed replacements as unsafe."""
import os
import re
from pathlib import Path
from translation_keys import php_key, raise_walk_error
TOKEN = re.compile(r'''\{\{--.*?--\}\}|<!--.*?-->|//[^\n]*|\#[^\n]*|/\*.*?\*/|'(?:\\.|[^'\\])*'|"(?:\\.|[^"\\])*"|\w+|=>|::|->|[^\s]''', re.S)
INTERPOLATION = re.compile(r'(?<!\\)(?:\\\\)*\$')
TRANSLATORS = {'__', 'trans', 'trans_choice', 'Lang::get', 'Lang::choice', '@lang'}


def blank(match):
    return ''.join('\n' if ch == '\n' else ' ' for ch in match.group())


def arguments(tokens, opening):
    # Cases: empty, nested, trailing comma, unfinished source.
    depth, parts = [], [[]]
    for index in range(opening, len(tokens)):
        token = tokens[index][0]
        if token in ('(', '[', '{'):
            depth.append({'(': ')', '[': ']', '{': '}'}[token])
        elif token in (')', ']', '}'):
            if not depth or token != depth.pop():
                break
            if not depth:
                return [part for part in parts if part], index
        if index == opening:
            continue
        if token == ',' and len(depth) == 1:
            parts.append([])
        else:
            parts[-1].append(token)
    return [], opening


def literal(parts):
    if len(parts) != 1 or not parts[0].startswith(("'", '"')):
        return None
    token = parts[0]
    return None if token[0] == '"' and INTERPOLATION.search(token) else php_key(token)


def dynamic_prefix(parts):
    if not parts or not parts[0].startswith(("'", '"')):
        return ''
    token = parts[0]
    interpolation = INTERPOLATION.search(token) if token[0] == '"' else None
    if interpolation:
        return php_key(token[:interpolation.start()].rstrip('{') + '"')
    return literal(parts[:1]) or '' if parts[1:2] == ['.'] else ''


def replacements_escaped(name, parts):
    offset = 2 if name in ('trans_choice', 'Lang::choice') else 1
    if len(parts) <= offset:
        return True
    replacement = parts[offset]
    opening = 0 if replacement[:1] == ['['] else 1
    if replacement[:1] != ['['] and replacement[:2] != ['array', '(']:
        return False
    entries, end = arguments([(token, 0) for token in replacement], opening)
    if end != len(replacement) - 1:
        return False
    for entry in entries:
        expression = entry[entry.index('=>') + 1:] if '=>' in entry else entry
        if expression[:2] not in (['e', '('], ['htmlspecialchars', '(']):
            return False
        _, end = arguments([(token, 0) for token in expression], 1)
        if end != len(expression) - 1:
            return False
    return True


def message_literals(expression):
    if literal(expression) is not None:
        return [expression]
    if not expression or expression[0] != '[':
        return []
    entries, _ = arguments([(token, 0) for token in expression], 0)
    return [candidate for entry in entries for candidate in message_literals(
        entry[entry.index('=>') + 1:] if '=>' in entry else entry)]


def php_text(parts, context):
    name = context[-1] if context else ''
    receiver = ''.join(context)
    if re.search(r'\bLog::|\blogger\b.*->', receiver, re.I):
        return []
    if re.search(r'(?:->(?:subject|message|error)|Mail::raw)$', receiver):
        return parts[:1]
    if context[-2:] == ['->', 'with'] and parts and literal(parts[0]) in ('message', 'error', 'success'):
        return parts[1:2]
    if name == 'abort' and parts and re.fullmatch(r'\d+', ''.join(parts[0])):
        return parts[1:2]
    return static_text(parts, receiver)


def static_text(parts, receiver):
    if parts and receiver.endswith('ValidationException::withMessages'):
        return message_literals(parts[0])
    if not parts or not receiver.endswith('response()->json'):
        return []
    candidates = []
    for index, token in enumerate(parts[0][:-1]):
        if token == '=>' and literal(parts[0][index - 1:index]) == 'message':
            rest = parts[0][index + 1:]
            if len(rest) >= 2 and rest[1] in (',', ']'):
                candidates.append(rest[:1])
    return candidates


def translator_name(context):
    for length in (3, 2, 1):
        name = ''.join(context[-length:])
        if name in TRANSLATORS:
            return name if length > 1 or context[-2:-1] not in (['->'], ['::'], ['$']) else ''
    return ''


def receiver_context(tokens, opening, openings):
    index = opening - 1
    while index >= 0:
        index = openings.get(index, index)
        if tokens[index][0] == '(':
            index -= 1
        if index < 1 or tokens[index - 1][0] not in ('->', '::'):
            break
        index -= 2
    return [token for token, _ in tokens[max(0, index):opening]]


def scan_file(path, relative):
    text = path.read_text(encoding='utf-8-sig')
    masked = TOKEN.sub(lambda match: blank(match) if match.group().startswith(('//', '#', '/*', '{{--', '<!--')) else match.group(), text)
    tokens = [(match.group(), match.start()) for match in TOKEN.finditer(masked)]
    calls, visible, directives, translation_end, openings = [], set(), [], -1, {}
    for index, (token, position) in enumerate(tokens):
        if token != '(':
            continue
        parts, end = arguments(tokens, index)
        openings[end] = index
        context = [token for token, _ in tokens[max(0, index - 3):index]]
        name = translator_name(context)
        line = text.count('\n', 0, tokens[max(0, index - 1)][1]) + 1
        if name in TRANSLATORS:
            translation_end = max(translation_end, end)
            first = parts[0] if parts else []
            calls.append(dict(name=name, key=literal(first), prefix=dynamic_prefix(first),
                              path=relative, line=line, position=position,
                              args_escaped=replacements_escaped(name, parts)))
        for candidate in php_text(parts if index > translation_end else [], receiver_context(tokens, index, openings)):
            phrase = literal(candidate)
            if phrase and ' ' in phrase and any(ch.isalpha() for ch in phrase):
                visible.add(f'{relative}:{line}')
        if context[-2:-1] == ['@']:
            directives.append((tokens[index - 2][1], tokens[end][1] + 1))
    raw, blade_visible = blade_pointers(text, calls, directives, relative) if path.name.endswith('.blade.php') else ([], set())
    return calls, raw, visible | blade_visible


def blade_pointers(masked, calls, directives, relative):
    raw = []
    for match in re.finditer(r'\{!!.*?!!\}', masked, re.S):
        raw.extend({key: call[key] for key in ('path', 'line', 'key', 'args_escaped')}
                   for call in calls if match.start() <= call['position'] < match.end()
                   and call['name'] in TRANSLATORS)
    for start, end in reversed(directives):
        masked = masked[:start] + re.sub(r'[^\n]', ' ', masked[start:end]) + masked[end:]
    hidden = r'''\{\{--.*?--\}\}|<!--.*?-->|<script\b.*?</script\s*>|<style\b.*?</style\s*>|<\?.*?\?>|@php\b.*?@endphp|\{\{.*?\}\}|\{!!.*?!!\}|@\w+|<(?:"[^"]*"|'[^']*'|[^'">])*>'''
    nodes = re.sub(hidden, blank, masked, flags=re.S | re.I)
    visible = {f'{relative}:{line}' for line, text_line in enumerate(nodes.splitlines(), 1)
               if any(ch.isalpha() for ch in text_line)}
    return raw, visible


def scan(repo, changed):
    calls, raw, visible = [], [], set()
    for root in ('app', 'resources', 'routes', 'config', 'database'):
        if not (repo / root).exists():
            continue
        for folder, dirs, names in os.walk(repo / root, onerror=raise_walk_error):
            dirs[:] = sorted(name for name in dirs if name not in ('vendor', 'node_modules', 'tests', 'lang'))
            for name in sorted(names):
                if not name.endswith('.php'):
                    continue
                path = Path(folder) / name
                relative = path.relative_to(repo).as_posix()
                file_calls, file_raw, file_visible = scan_file(path, relative)
                calls.extend(file_calls)
                raw.extend(file_raw)
                if changed is None or relative in changed:
                    visible.update(file_visible)
    return calls, raw, sorted(visible)
