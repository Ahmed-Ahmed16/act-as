from collections import Counter
from dataclasses import dataclass

if __package__:
    from .packet_check import parse_piece
else:
    from packet_check import parse_piece


@dataclass
class PieceIndex:
    catalog: dict
    spans: dict


def piece_names(document):
    if isinstance(document, dict):
        for key, child in document.items():
            if key == 'piece':
                yield child
            elif key in ('hunks', 'pieces', 'unplaced'):
                yield from child
            elif isinstance(child, (dict, list)):
                yield from piece_names(child)
    elif isinstance(document, list):
        for child in document:
            yield from piece_names(child)


def piece_span(piece, catalog):
    # Cases: whole, adjacent, gap, overlap, zero, reversed, too long, operation.
    if not isinstance(piece, str):
        raise ValueError('piece must be text')
    key, start, end = parse_piece(piece)
    if key not in catalog:
        raise KeyError(key)
    hunk = catalog[key]
    length = hunk['counted'] if hunk['counted'] > 0 else hunk['lines']
    if end is not None and end > length:
        raise ValueError('range exceeds hunk: ' + piece)
    return {(key, line) for line in range(start, (length if end is None else end) + 1)} or {(key, 0)}


def coverage(pieces, spans):
    return Counter(line for piece in pieces if isinstance(piece, str) for line in spans.get(piece, ()))


def coverage_failures(actual, expected):
    failures = []
    for rule, tokens in [('split-hunk-unplaced', expected - actual),
                         ('split-hunk-twice', {line for line, count in actual.items() if count > 1})]:
        if tokens:
            failures.append((rule, ', '.join(sorted({key for key, _ in tokens}))))
    return failures


def need_failures(rows, rule):
    earlier, failures = set(), []
    for row in rows:
        if any(need not in earlier or need == row['name'] for need in row.get('needs', [])):
            failures.append((rule, row['name'] + ': needs must name an earlier place'))
        earlier.add(row['name'])
    return failures


def nonempty(text):
    return isinstance(text, str) and bool(text.strip())


def reference_failures(reference, changed, head):
    if not isinstance(reference, dict):
        return [('split-link-ref', 'reference must name an unchanged file at head and a check')]
    path = reference.get('unchanged', reference.get('path'))
    if not nonempty(path) or path in changed or reference.get('at') != head or not nonempty(reference.get('check')):
        return [('split-link-ref', str(path) + ': needs an unchanged file at head and a check')]
    return []


def link_failures(group, places, spans, catalog):
    failures, linked_lines = [], set()
    group_lines = set(coverage(group['hunks'], spans))
    for link in group.get('links', []):
        linked = set(coverage([link.get('piece')], spans))
        if not link.get('for'):
            continue
        linked_lines.update(linked)
        for target in link['for']:
            if not isinstance(target, dict) or not any(key in target for key in ('piece', 'unchanged')):
                failures.append(('split-link-ref', 'link target must name a piece or an unchanged file'))
                continue
            if 'piece' not in target:
                continue
            source = set(coverage([target['piece']], spans))
            counted = source and all(catalog[key]['counted'] > 0 for key, _ in source)
            same_place = any(linked <= place and source <= place for place in places)
            if not counted or not linked or not linked <= group_lines or not same_place:
                failures.append(('split-link-place', str(link.get('piece')) + ': source must share its place'))
    needs_link = {line for line in group_lines if catalog[line[0]]['kind'] in ('test', 'generated')}
    if needs_link - linked_lines:
        failures.append(('split-link-missing', group['name'] + ': tests and generated pieces need links'))
    return failures


def text_failures(row, group, lines, catalog):
    counted = {key for key, _ in lines if catalog[key]['counted'] > 0}
    text_only = bool(counted) and all(catalog[key]['language'] for key in counted)
    pages = row.get('pages', group.get('pages', []))
    unchanged = {page.get('name') for page in pages if 'unchanged' in page}
    keys = row.get('keys', [key for key in group.get('keys', []) if key.get('part') == row['name']])
    if (text_only and (not unchanged or any(key.get('page') not in unchanged for key in keys))
            or unchanged and not text_only):
        return [('split-text-only', row['name'] + ': unchanged pages must match text only work')]
    return []


def related_evidence(related, symbol):
    check = related.get('needed_check')
    return (nonempty(related.get('why')) and isinstance(check, dict) and check.get('needed') is True
            and nonempty(check.get('command')) and symbol in check['command'] and nonempty(check.get('result')))


def symbol_evidence(record, counted, index):
    catalog, spans = index.catalog, index.spans
    if not isinstance(record, dict) or not all(nonempty(record.get(key)) for key in
                                              ('symbol', 'kind', 'declaration', 'closing')):
        return False
    symbol_lines = set(coverage([record.get('piece')], spans))
    if (len(symbol_lines) <= 300 or not symbol_lines <= counted or
            len({key for key, _ in symbol_lines}) != 1):
        return False
    if any(catalog[key]['deleted'] != 0 for key, _ in symbol_lines):
        return False
    return True


def new_evidence(check, base):
    return (isinstance(check, dict) and check.get('base') == base and nonempty(check.get('command'))
            and check.get('found_in_base') == [] and check.get('deleted_in_pr') == [])


def stays_over_valid(record, counted, index, base):
    if not symbol_evidence(record, counted, index):
        return False
    spans = index.spans
    symbol_lines = set(coverage([record['piece']], spans))
    check = record.get('new_check')
    if not new_evidence(check, base):
        return False
    related = record.get('related')
    if not isinstance(related, list):
        return False
    declared = Counter()
    for entry in related:
        if not isinstance(entry, dict) or not related_evidence(entry, record['symbol']):
            return False
        lines = set(coverage([entry.get('piece')], spans))
        if not lines or not lines <= counted - symbol_lines:
            return False
        declared.update(lines)
    return declared == Counter(counted - symbol_lines)


def part_failures(parts, group, index, base):
    catalog, spans = index.catalog, index.spans
    failures = need_failures(parts, 'split-part-need')
    expected = coverage(group['hunks'], spans)
    actual = coverage([piece for part in parts for piece in part['hunks']], spans)
    if actual != expected:
        failures.append(('split-part-cover', 'parts must cover group 1 exactly once'))
        failures.extend(coverage_failures(actual, expected))
    for part in parts:
        lines = coverage(part['hunks'], spans)
        counted = {line for line in lines if catalog[line[0]]['counted'] > 0}
        size = sum(lines[line] for line in counted)
        record = part.get('stays_over')
        if (size > 300) != (record is not None):
            failures.append(('split-part-size', part['name'] + ': stays_over must match size over 300'))
        if record is not None and (size <= 300 or not stays_over_valid(record, counted, index, base)):
            failures.append(('split-stays-over', part['name'] + ': symbol evidence is missing or inconsistent'))
        failures.extend(text_failures(part, group, lines, catalog))
        if any(catalog[key]['kind'] == 'generated' for key, _ in lines) and not nonempty(part.get('rebuild')):
            failures.append(('split-rebuild-missing', part['name'] + ': generated pieces need a rebuild'))
    return failures


def split_failures(files, hunks, plan):
    """Check parsed packet objects. Inspect evidence without running commands."""
    catalog = {hunk['id']: hunk for hunk in hunks['hunks'] + hunks['ops']}
    failures, spans = [], {}
    for piece in piece_names(plan):
        try:
            spans[piece] = piece_span(piece, catalog)
        except KeyError:
            failures.append(('split-hunk-unknown', 'unknown piece: ' + str(piece)))
        except ValueError as error:
            failures.append(('split-hunk-range', str(error)))
    groups, parts = plan.get('groups', []), plan.get('parts', [])
    if not groups:
        failures.append(('split-no-groups', 'at least 1 group is needed'))
    names = [group['name'] for group in groups]
    if any(not nonempty(name) or ' | ' in name or names.count(name) > 1 for name in names):
        failures.append(('split-name', 'group names must be nonempty, unique and have no separator'))
    failures.extend(need_failures(groups, 'split-need-order'))
    placed = coverage([piece for group in groups for piece in group['hunks']] + plan.get('unplaced', []), spans)
    expected = Counter(line for key in catalog for line in piece_span(key, catalog))
    failures.extend(coverage_failures(placed, expected))
    changed = {path for row in files['files'] for path in (row['path'], row['old_path'])}
    for index, group in enumerate(groups):
        lines = set(coverage(group['hunks'], spans))
        places = [set(coverage(part['hunks'], spans)) for part in parts] if index == 0 else [lines]
        failures.extend(link_failures(group, places, spans, catalog))
        references = [target for link in group.get('links', []) for target in link.get('for', [])
                      if isinstance(target, dict) and 'unchanged' in target]
        references += [page['unchanged'] for page in group.get('pages', []) if 'unchanged' in page]
        for reference in references:
            failures.extend(reference_failures(reference, changed, hunks['head']))
        if index > 0 and any(catalog[key]['kind'] == 'generated' for key, _ in lines) and not nonempty(group.get('rebuild')):
            failures.append(('split-rebuild-missing', group['name'] + ': generated pieces need a rebuild'))
        failures.extend(text_failures(group, group, lines, catalog))
    if groups:
        failures.extend(part_failures(parts, groups[0], PieceIndex(catalog, spans), hunks['base']))
    return failures
