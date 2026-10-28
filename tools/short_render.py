if __package__:
    from .packet_check import CAP_STOP, parse_piece
else:
    from packet_check import CAP_STOP, parse_piece


def behaviour(plan):
    return '\n'.join([*(f"group summary: {g['name']} | {g['summary']}" for g in plan['groups']),
                      *(f"part: {p['name']} | {p['summary']}" for p in plan['first_group_parts']),
                      'Translations by page: ' + CAP_STOP])


def opens(row, unit):
    return ('opens against main after ' + unit + 's ' + ' and '.join(row['needs']) + ' are merged'
            if row['needs'] else 'opens against main; needs no other ' + unit)


def marks(row):
    return (['stands alone (' + ', '.join(row['marks']) + ')'] if row['marks'] else []) + (
        ['needs the separate Opus review (marked from entry points and file names, not read)']
        if set(row['marks']) & {'money', 'unsure'} else [])


def group_lines(group):
    return [f"group: {group['name']}, {group['counted']} counted lines",
            '  entry points: ' + ', '.join(group['entry_points']), '  ' + opens(group, 'group')]


def key_lines(keys):
    return [f"key {k['shape']}: {k['key']}, page {k['page']}, part {k.get('part') or 'none'}" for k in keys]


def group_details(group, head):
    lines = ['needs: ' + (', '.join(group['needs']) or 'none')]
    for page in group['pages']:
        lines.append(f"page: {page['name']}, " + (
            f"unchanged screen at {page['unchanged'].get('path', page['unchanged'].get('unchanged'))}; "
            'existence on the default branch not checked by the tool' if 'unchanged' in page else
            'source pieces ' + ', '.join(page.get('pieces', page.get('hunks', [])))))
    lines += key_lines(group['keys'])
    for link in group['links']:
        targets = [target['piece'] if 'piece' in target else
                   f"unchanged {target['unchanged']} at {head[:7]}" for target in link['for']]
        lines.append(f"test {link['piece']} for " + ', '.join(targets))
    return lines + (['rebuild: ' + group['rebuild']] if group['rebuild'] else []) + marks(group)


def stays_over(record, hunks):
    catalog = {h['id']: h for h in hunks['hunks']}
    key, start, end = parse_piece(record['piece'])
    hunk = catalog[key]
    end = hunk['counted'] if end is None else end
    related = '; '.join(f"{r['piece']} ({r['why']}; {r['needed_check']['command']}: "
                        f"{r['needed_check']['result']})" for r in record['related']) or 'none'
    return (f"stays over the cap: {record['symbol']} (new {record['kind']}) at {hunk['path']} lines "
            f"{hunk['new_start'] + start - 1} to {hunk['new_start'] + end - 1} "
            f"(file lines taken from the hunk start), {end - start + 1} counted lines alone; "
            f"also in this part, declared as needed by it: {related}. "
            "The reviewer's checks are recorded; the tool did not prove them. "
            'Your call: review it anyway or send it back.')


def part_lines(plan, files, hunks):
    catalog = {h['id']: row for row in files['files'] for h in row['hunks']}
    catalog.update({op['id']: op for op in hunks['ops']})
    lines = []
    for number, part in enumerate(plan['first_group_parts'], 1):
        rows = [catalog[parse_piece(piece)[0]] for piece in part['hunks']]
        lines += [f"part {number}: {part['summary']}", 'needs: ' + (', '.join(part['needs']) or 'none'),
                  opens(part, 'part'), f"counted: {part['counted']} (estimate)"]
        for label, paths in [('files', [r['path'] for r in rows]),
                             ('tests', [r['path'] for r in rows if r['kind'] == 'test']),
                             ('migrations', [r['path'] for r in rows if '/migrations/' in r['path']])]:
            lines.append(label + ': ' + (', '.join(dict.fromkeys(paths)) or 'none'))
        lines += marks(part) + (['rebuild: ' + part['rebuild']] if part['rebuild'] else [])
        if part.get('stays_over') is not None:
            lines.append(stays_over(part['stays_over'], hunks))
        lines.append("check: CI green on this PR's own head")
    return lines


def shared_files(plan, files):
    lines = []
    for row in files['files']:
        ids = {h['id'] for h in row['hunks']}
        places = [g['name'] + ': ' + ', '.join(p for p in g['hunks'] if parse_piece(p)[0] in ids)
                  for g in plan['groups'] if any(parse_piece(p)[0] in ids for p in g['hunks'])]
        if len(places) >= 2:
            lines.append('shared file: ' + row['path'] + '; ' + '; '.join(places))
    return '\n'.join(lines) or 'shared files: none'


def split_field(plan, files, hunks):
    lines = ['Counts are estimates: hunk lines from git, placed by reading entry points. '
             'A hunk may be cut into line ranges.']
    if plan['main']['state'] == 'not established':
        lines.append('not checked: main not established: ' + plan['main']['evidence'] + '.')
    ci = plan['ci']
    if ci['state'] == 'read':
        lines += [f"workflow {w['path']}, on block as read by the reviewer: " + '; '.join(w['on_text'].splitlines())
                  for w in ci['workflows']] or ['no workflow files found at the frozen head']
        lines.append('The tool does not interpret these filters. Read them to see whether a part opened against main gets CI.')
    else:
        lines.append('not checked: CI trigger not read (' + ci['reason'] + ').')
    for number, group in enumerate(plan['groups']):
        header = group_lines(group)
        details = group_details(group, plan['head'])
        advice = ('cut into the parts below' if number == 0 else
                  f"fits: {group['counted']} counted lines, open as 1 PR" if group['counted'] <= 300 else
                  'over the cap: split again when its turn comes')
        lines += header[:2] + ['  ' + details[0], header[2], '  ' + advice] + ['  ' + line for line in details[1:]]
        for op in hunks['ops']:
            if op['id'] in group['hunks']:
                action = f"renamed {op['old_path']} to {op['path']}" if op['old_path'] else op['status'] + ' ' + op['path']
                lines.append('  file operation: ' + action + ', 0 counted lines')
    counts = {h['id']: h['counted_lines'] for row in files['files'] for h in row['hunks']}
    total = sum((counts.get(key, 0) if end is None else end - start + 1) if counts.get(key, 0) else 0
                for key, start, end in map(parse_piece, plan['unplaced']))
    lines.append(f'unplaced (a lead, not a group): {total} counted lines')
    lines += key_lines(plan.get('unplaced_keys') or [])
    lines += marks(dict(marks=plan.get('unplaced_marks', [])))
    lines += ['tests with no source found (lead): ' + ', '.join(
        p for p in plan['unplaced'] if any(h['id'] == parse_piece(p)[0] for row in files['files']
                                          if row['kind'] == 'test' for h in row['hunks']))]
    lines += ['loop broken: ' + note for note in plan['loop_notes']]
    return '\n'.join(lines + part_lines(plan, files, hunks))


def draft(plan, files, hunks, opening):
    parts = plan['first_group_parts']
    plain = dict(plan, first_group_parts=[dict(p, marks=[], stays_over=None) for p in parts])
    lines = [opening, *(line for group in plan['groups'] for line in group_lines(group)),
             'group 1 cut into the parts below', *part_lines(plain, files, hunks), shared_files(plan, files)]
    lines += [p['name'] + ': ' + line for p in parts for line in marks(p)]
    lines += [stays_over(p['stays_over'], hunks) for p in parts if p.get('stays_over') is not None]
    return '\n'.join(lines + ['language keys travel with their page.',
                             'open part 1 first; each part gets its own review.'])
