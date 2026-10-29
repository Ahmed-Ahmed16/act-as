import re


def parse_collision(text, exit_code):
    summary = re.search(r'^[ \t]*Tests:[ \t]+(.+?)\s+\((\d+) assertions?\)', text, re.M)
    if not summary:
        return None
    counts = {name: int(number) for number, name in re.findall(
        r'(\d+)\s+(passed|failed|skipped|pending|incomplete|risky|todo)\b', summary[1])}
    tests, assertions = sum(counts.values()), int(summary[2])
    state, message = 'none', ''
    if counts.get('failed', 0):
        assertion = re.search(r'^[ \t]*(Failed asserting[^\r\n]*)', text, re.M)
        state = 'assertion' if assertion else 'error'
        message = assertion[1] if assertion else ''
    elif (counts.get('passed', 0) >= 1 and tests == counts['passed'] and
          assertions >= 1 and exit_code == 0):
        state = 'ok'
    return dict(state=state, tests=tests, assertions=assertions, message=message)


def parse(text, exit_code):
    # Counts: absent/0/positive; red: assertion/error; issues: skipped/incomplete.
    text = re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]', '', text)
    collision = parse_collision(text, exit_code)
    if collision is not None:
        return collision
    counts = {name.lower(): int(number) for name, number in re.findall(
        r'\b(Tests|Assertions|Failures|Errors|Skipped|Incomplete):\s*(\d+)', text)}
    green = re.search(r'^OK \((\d+) tests?, (\d+) assertions?\)', text, re.M)
    issues = re.search(r'^OK, but there were issues!\r?$', text, re.M)
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
    elif ((green or (issues and not {'failures', 'errors'}.intersection(counts))) and
          tests >= 1 and assertions >= 1 and exit_code == 0):
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
