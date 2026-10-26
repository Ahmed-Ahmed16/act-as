import re


def parse(text, exit_code):
    # Counts: absent/0/positive; red: assertion/error; issues: skipped/incomplete.
    counts = {name.lower(): int(number) for name, number in re.findall(
        r'\b(Tests|Assertions|Failures|Errors|Skipped|Incomplete):\s*(\d+)', text)}
    green = re.search(r'^OK \((\d+) tests?, (\d+) assertions?\)', text, re.M)
    tests, assertions = ((int(green[1]), int(green[2])) if green else
                         (counts.get('tests', 0), counts.get('assertions', 0)))
    state, message = 'none', ''
    if (exit_code in (126, 127) or
            re.search(r'Could not open input file|No such file or directory|command not found', text) or
            ('not found' in text and not re.search(r'^PHPUnit\b', text, re.M))):
        state = 'unrunnable'
    elif re.search(r'ERRORS!|Fatal error|Parse error|syntax error', text, re.I) or counts.get('errors', 0):
        state = 'error'
    elif ('No tests executed' in text or counts.get('skipped', 0) or counts.get('incomplete', 0)):
        state = 'none'
    elif green and tests >= 1 and assertions >= 1 and exit_code == 0:
        state = 'ok'
    elif 'FAILURES!' in text and counts.get('failures', 0) > 0:
        state = 'assertion'
        first = re.search(r'^1\) (.*)(?:\n|$)', text, re.M)
        if first:
            message = first[1].rstrip('\r')
            block = re.split(r'^\d+\) ', text[first.end():], maxsplit=1, flags=re.M)[0]
            assertion = re.search(r'^Failed asserting[^\r\n]*', block, re.M)
            if assertion:
                message += '\n' + assertion[0]
    return dict(state=state, tests=tests, assertions=assertions, message=message)
