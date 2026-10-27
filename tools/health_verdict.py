import json
import sys
from pathlib import Path

from health_parse import ArgumentParser, outcome, run_cli

RESULT_WORDS = ('finding', 'clean', 'not checked', 'does not apply')


def validate_entry(entry):
    name = entry.get('id')
    if not isinstance(name, str) or not name:
        raise ValueError('health entry has invalid id')
    if entry.get('word') not in ('must fix', 'finding', 'lead', 'none'):
        raise ValueError(f'{name}: invalid word')
    for field in ('tool_result', 'reading_result'):
        if entry.get(field) not in RESULT_WORDS:
            raise ValueError(f'{name}: invalid {field}')
    if entry['word'] == 'must fix' and (entry.get('kind') == 'pointer' or
                                        name in ('T1', 'T2', 'T3', 'T4')):
        raise ValueError(f'{name}: pointer or translation check can never be must fix')


def health_entries(record):
    if not isinstance(record, dict) or not isinstance(record.get('entries'), list):
        raise ValueError('record must contain entries as a list')
    required = record.get('required_ids', [])
    if not isinstance(required, list) or any(not isinstance(name, str) for name in required):
        raise ValueError('required_ids must be a list of ids')
    entries = []
    for entry in record['entries']:
        if not isinstance(entry, dict):
            raise ValueError('entry must be an object with an id')
        if entry.get('mode') == 'health':
            validate_entry(entry)
            entries.append(entry)
    return required, entries


def verdict(record):
    required, entries = health_entries(record)
    seen, reasons, pointers, failed, unchecked = set(), [], 0, False, False
    for entry in entries:
        name = entry['id']
        seen.add(name)
        pointer = entry.get('kind') == 'pointer'
        if entry['word'] == 'must fix':
            failed = True
            reasons.append(f'{name}: must fix')
        if pointer:
            pointers += 1
            continue
        if 'not checked' in (entry['tool_result'], entry['reading_result']):
            unchecked = True
            reasons.append(f'{name}: not checked')
    missing = [name for name in dict.fromkeys([f'H{n}' for n in range(1, 12)] +
                                             [f'T{n}' for n in range(1, 9)] + required)
               if name not in seen]
    decision = 'fail' if failed else 'incomplete' if unchecked or missing else 'pass'
    return outcome({'pass': 'clean', 'fail': 'finding', 'incomplete': 'not checked'}[decision],
                   f'health verdict: {decision}', verdict=decision, reasons=reasons,
                   missing=missing, pointers=pointers)


def main():
    parser = ArgumentParser()
    parser.add_argument('--record', required=True)
    args = parser.parse_args()
    return verdict(json.loads(Path(args.record).read_text(encoding='utf-8')))


if __name__ == '__main__':
    sys.exit(run_cli(main))
