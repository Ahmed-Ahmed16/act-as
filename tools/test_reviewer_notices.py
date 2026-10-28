import datetime
import hashlib
import re
import shutil
import tempfile
import unittest
from collections import namedtuple
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
CARDS = ROOT / 'roles/reviewer/cards'
NOTICES = ROOT / 'THIRD-PARTY-NOTICES.md'
REFS = ROOT / 'tools/licence_refs'
REFERENCES = {
    'MIT': ('mit.txt', 'ea1e33f332d0c5837eac845603bf80d5ba0ee3f65436e4690e7bd6ea88cc8e2a'),
    'BSD 3 Clause': ('bsd-3-clause.txt', '7a77915f34caf18d47bc31750dae47dbd7f7895e95bbb8370f477c25009388f6'),
    'Unicode License v3': ('unicode-v3.txt', 'e7a93b009565cfce55919a381437ac4db883e9da2126fa28b91d12732bc53d96'),
}
MIT = 'https://opensource.org/license/mit'
BSD = 'https://opensource.org/license/bsd-3-clause'
CC3 = 'https://creativecommons.org/licenses/by/3.0/'
CC4 = 'https://creativecommons.org/licenses/by/4.0/'
SA4 = 'https://creativecommons.org/licenses/by-sa/4.0/'
GPL = 'https://www.gnu.org/licenses/old-licenses/gpl-2.0.html'
TERMS = 'https://www.unicode.org/copyright.html'
COGNITECT = 'https://www.cognitect.com/blog/2011/11/15/documenting-architecture-decisions'
GFDL = ('Permission is granted to copy, distribute and/or modify this document under the terms of the '
        'GNU Free Documentation License, Version 1.3 or any later version published by the Free Software Foundation')
Source = namedtuple('Source', 'key cls label link holder copyright routes evidence_hosts', defaults=[()])
RAW = ('raw.githubusercontent.com',)
C = 'Copyright (c) '
# Plan 3 and 3b supply these facts, independently of the notices being checked.
REG = [
    Source('google', 'attrib', 'CC BY 3.0', CC3, 'Google', (), (('google.github.io', '/eng-practices'),), RAW),
    Source('github-docs', 'attrib', 'CC BY 4.0', CC4, 'GitHub Inc.', ('GitHub Inc. (c) 2026',), (('docs.github.com', ''),), RAW),
    Source('laravel-docs', 'attrib', 'MIT', MIT, 'Taylor Otwell', (C + 'Taylor Otwell',), (('laravel.com', '/docs'),), RAW),
    Source('laravel-framework', 'attrib', 'MIT', MIT, 'Taylor Otwell', (C + 'Taylor Otwell',), (('github.com', '/laravel/framework'),)),
    Source('owasp-cs', 'nocopy', 'CC BY SA 4.0', SA4, 'Cheat Sheets Series Team', (), (('cheatsheetseries.owasp.org', ''),), RAW),
    Source('owasp-api', 'nocopy', 'CC BY SA 4.0', SA4, 'OWASP API Security Project team', ('Copyright 2023 OWASP API Security Project team',), (('owasp.org', '/API-Security'),), RAW),
    Source('owasp-top10', 'nocopy', 'CC BY SA 4.0', SA4, 'OWASP Top 10 Team', ('Copyright 2021 to 2025 OWASP Top 10 Team',), (('owasp.org', '/Top10'),), RAW),
    Source('owasp-community', 'nocopy', 'CC BY SA 4.0', SA4, 'OWASP Foundation', ('Copyright 2026 OWASP Foundation, Inc.',), (('owasp.org', '/www-community'),)),
    Source('owasp-genai', 'nocopy', 'CC BY SA 4.0', SA4, 'OWASP Foundation', ('Copyright 2025 OWASP Foundation, Inc.',), (('genai.owasp.org', ''),)),
    Source('phpunit', 'attrib', 'CC BY 3.0', CC3, 'Sebastian Bergmann', (C + '2025 Sebastian Bergmann',), (('docs.phpunit.de', ''),)),
    Source('php-manual', 'attrib', 'CC BY 3.0 or later', CC3, 'PHP Documentation Group', ('Copyright 1997 to 2026 by the PHP Documentation Group',), (('www.php.net', '/manual'),)),
    Source('composer', 'attrib', 'MIT', MIT, 'Nils Adermann, Jordi Boggiano', (C + 'Nils Adermann, Jordi Boggiano',), (('getcomposer.org', ''),), RAW),
    Source('git-docs', 'nocopy', 'GPL 2.0', GPL, 'Git project', (), (('git-scm.com', '/docs'),), RAW),
    Source('linux', 'nocopy', 'GPL 2.0 only', GPL, 'Linux kernel contributors', (), (('www.kernel.org', '/doc'),), RAW),
    Source('pstack', 'attrib', 'MIT', MIT, 'Lauren Tan', (C + '2026 Lauren Tan',), (('github.com', '/backnotprop/pstack'),)),
    Source('jscpd', 'attrib', 'MIT', MIT, 'Andrey Kucherenko', (C + '2013 to 2024 Andrey Kucherenko',), (('github.com', '/kucherenko/jscpd'),)),
    Source('larastan', 'attrib', 'MIT', MIT, 'Can Vural, Nuno Maduro', (C + 'Can Vural, Nuno Maduro',), (('github.com', '/larastan/larastan'),)),
    Source('phpstan-src', 'attrib', 'MIT', MIT, 'Ondřej Mirtes, PHPStan s.r.o.', (C + '2016 Ondřej Mirtes', C + '2025 PHPStan s.r.o.'), (('github.com', '/phpstan/phpstan-src'),)),
    Source('phpstan-docs', 'short', '___', '', 'PHPStan s.r.o.', (), (('phpstan.org', ''),)),
    Source('phpmd', 'attrib', 'BSD 3 Clause', BSD, 'Manuel Pichler', (C + '2008, Manuel Pichler',), (('phpmd.org', ''),), RAW),
    Source('infection', 'attrib', 'BSD 3 Clause', BSD, 'Maks Rafalko', (C + '2017, Maks Rafalko',), (('infection.github.io', ''),), RAW),
    Source('translator', 'nocopy', 'Prosperity Public License 3.0.0', 'https://prosperitylicense.com/versions/3.0.0', 'Quentin Gabriele', (), (('github.com', '/ElegantEngineeringTech/laravel-translator'),)),
    Source('lang-monitor', 'attrib', 'MIT', MIT, 'Jonas Schen', (C + '2023 Jonas Schen',), (('github.com', '/jonasschen/laravel-lang-monitor'),)),
    Source('mattpocock', 'attrib', 'MIT', MIT, 'Matt Pocock', (C + '2026 Matt Pocock',), (('github.com', '/mattpocock/skills'),)),
    Source('aposd', 'short', '___', '', 'John Ousterhout', (), (('github.com', '/johnousterhout/aposd-vs-clean-code'),)),
    Source('aihero', 'short', '___', '', 'AI Hero', (), (('www.aihero.dev', ''),)),
    Source('fowler', 'short', '___', '', 'Martin Fowler', (), (('martinfowler.com', ''),)),
    Source('refactoring-com', 'hold', '___', '', 'refactoring.com', (), (('refactoring.com', ''),)),
    Source('cleancoder', 'short', '___', '', 'Robert C. Martin', (), (('blog.cleancoder.com', ''),)),
    Source('unicode-data', 'attrib', 'Unicode License v3', 'https://www.unicode.org/license.txt', 'Unicode, Inc.', (C + '1991 to 2026 Unicode, Inc.',), (('www.unicode.org', '/Public'),)),
    Source('unicode-charts', 'nocopy', 'Unicode Terms of Use', TERMS, 'Unicode, Inc.', (), (('www.unicode.org', '/cldr/charts'),)),
    Source('unicode-reports', 'nocopy', 'Unicode Terms of Use', TERMS, 'Unicode, Inc.', (), (('www.unicode.org', '/reports'), ('unicode.org', '/reports'))),
    Source('ewd249', 'short', '___', '', 'E. W. Dijkstra', (), (('www.cs.utexas.edu', '/~EWD'),)),
    Source('per', 'hold', '___', '', 'PHP Framework Interop Group', (), (('www.php-fig.org', '/per'),)),
    Source('cognitect', 'attrib', 'copyright waived by the author', COGNITECT, 'Cognitect', (), (('www.cognitect.com', ''),)),
    Source('gnu-coreutils', 'nocopy', 'GNU FDL 1.3 or later', 'https://www.gnu.org/licenses/fdl-1.3.html', 'Free Software Foundation, Inc.', (C + '1994 to 2026 Free Software Foundation, Inc.',), (('www.gnu.org', '/software/coreutils'),)),
    Source('i18next', 'hold', '___', '', 'i18next', (), (('www.i18next.com', ''),)),
]
ROW = {source.key: source for source in REG}
OWN = {
    'not checked', 'not checked: PR already merged, base not proved', 'rules page: draft, not in the repo yet',
    "user A reads user B's record", 'also through relations', 'can any user of any role write that text',
    'live key or test key', "select * from orders where ref = '", '{{ $user->website }}',
    'Hello :name, order :order shipped', 'Arabic writes 0, 1 and 2 in words', 'not checked: no plural count for <language>',
    'passed through a variable', 'no trace', 'No trace', 'not checked: test database unavailable',
    '450 keys added to 1 file; a common file plus 1 file per page is an option',
}
ALLOW = {
    ('REV-114', 'Pull requests on GitHub show a three-dot diff.'): 'github-docs',
    ('REV-117', 'even if the ref has been deleted'): 'github-docs',
    ('REV-133', 'make sure the whole system keeps working after each CL is submitted'): 'google',
    ('REV-303', 'thinking about edge cases'): 'google',
    ('REV-304', "will not be called if the class doesn't contain a method"): 'laravel-docs',
    ('REV-307', 'Any IDs that are not in the given array will be removed'): 'laravel-docs',
    ('REV-308', 'you should be extremely careful to avoid creating SQL injection vulnerabilities'): 'laravel-docs',
    ('REV-309', 'never allow user input to dictate the column names'): 'laravel-docs',
    ('REV-311', 'considered unsafe, as the file name and extension may be tampered with'): 'laravel-docs',
    ('REV-313', 'does not allow SVG files due to the possibility of XSS'): 'laravel-docs',
    ('REV-314', 'intended for files that are going to be publicly accessible'): 'laravel-docs',
    ('REV-315', 'place these kinds of routes outside of the web middleware group'): 'laravel-docs',
    ('REV-316', 'Be very careful when echoing content that is supplied by users'): 'laravel-docs',
    ('REV-320', "should not be committed to your application's source control"): 'laravel-docs',
    ('REV-323', 'attached to routes or route groups using the throttle middleware'): 'laravel-docs',
    ('REV-335', 'Do not pass untrusted user input to unserialize()'): 'php-manual',
    ('REV-346', 'The command also detects abandoned packages and packages flagged as malware'): 'composer',
    ('REV-347', 'the custom repository has priority over packagist'): 'composer',
    ('REV-445', 'everything should be said “Once and only Once.”'): 'fowler',
    ('REV-516', 'that now really needs to be broken up into smaller methods'): 'google',
    ('REV-520', 'the author should maintain consistency with the existing code'): 'google',
    ('REV-602', 'the __ function will return the translation string key'): 'laravel-docs',
    ('REV-603', 'All placeholders are prefixed with a'): 'laravel-docs',
    ('REV-603', 'you may use'): 'laravel-docs',
    ('REV-608', '0620..063F ; Arabic # Lo'): 'unicode-data',
}
LONG_OK = {
    # Project example text shows the size report, including its omitted file counts.
    ('REV-108', 'example', 'size: pass, 212 counted lines, cap 300; left out: tests 140 (3 files), lock files 0 (0 files), generated 0 (0 files), docs 12 (1 file)'),
    # Project example text shows the refusal when a change exceeds the size cap.
    ('REV-140', 'example', 'This PR is 640 counted lines; the cap is 300. It was not reviewed past size.'),
    # Project example text compares the cancellation rule before and after the change.
    ('REV-215', 'example', 'R3 says an order can be cancelled within 24 hours; with this PR it can be cancelled within 12 hours'),
    # Project example text shows a pointer naming the jobs found in a large class.
    ('REV-405', 'example', '1200 line class: problem, 3 jobs (question 11; question 12 too once its card loads)'),
    # Project example text shows a suggested home for a large group of translation keys.
    ('REV-612', 'example', '450 keys added to 1 file; a common file plus 1 file per page is an option'),
}
FIELDS = ('Key', 'Credit', 'Licence', 'Evidence', 'Changes', 'Use', 'Notice', 'Cards')
SKIP = ('id', 'review')
LOCKED = ('nocopy', 'hold')
HTTP_EXAMPLES = ('http://evil.example', 'https://evil.example', 'http://169.254.169.254/')


def normal_url(url):
    if not plain_url(url):
        return None
    parsed = urlsplit(url)
    return parsed.hostname, parsed.path or '/'


def plain_url(url):
    # Boundaries: empty path, labels, literal scheme, fragments and dot segments.
    match = re.fullmatch(r'https://([a-z0-9.-]+)(/[A-Za-z0-9._~/-]*)?(?:#[A-Za-z0-9._~/-]*)?', url)
    if match is None or '.' not in match[1]:
        return False
    labels = match[1].split('.')
    return (all(re.fullmatch(r'[a-z0-9](?:[a-z0-9-]*[a-z0-9])?', label) and
                not label.isdigit() and not label.startswith('0x') for label in labels) and
            not any(segment in ('.', '..') for segment in (match[2] or '/').split('/')))


def source_key(url):
    normal = normal_url(url)
    if normal is None:
        return None
    host, path = normal
    matches = [(len(prefix), source.key) for source in REG for domain, prefix in source.routes
               if host == domain and (path == prefix or path.startswith(prefix + '/'))]
    return max(matches, default=(0, None))[1]


def urls(text):
    found = []
    for url in re.findall(r'https?://[^\s)\]}>"“”«»„]*', text, re.I):
        if url[-1] in ',;:' or (url.endswith('.') and url[-2] not in './'):
            url = url[:-1]
        found.append(url)
    return found


def card_sources(fields):
    keys, problems = set(), []
    for field, text in fields:
        if field in SKIP:
            continue
        for url in urls(text):
            if url in HTTP_EXAMPLES:
                continue
            if not plain_url(url):
                problems.append('url not plain: ' + url)
                continue
            key = source_key(url)
            keys.add(key) if key else problems.append('no licence class for URL ' + url)
    return keys, problems


def parse_card(path):
    pairs, problems, identities, names = [], [], [], set()
    lines = path.read_text(encoding='utf-8').splitlines()
    cid = next((m[1] for line in lines if (m := re.fullmatch(r'id: *(.*)', line))), path.stem)
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        match = re.fullmatch(r'([\w-]+): *(.*)', line)
        if not match:
            problems.append(f'{cid}: line {number}: expected key: value')
            continue
        field, text = match.groups()
        if field in names:
            problems.append(f'{cid}: line {number}: duplicate field {field}')
        names.add(field)
        pairs.append((field, text))
        if field == 'id':
            identities.append((number, text))
            if text != path.stem:
                problems.append(f'{cid}: line {number}: id differs from file name {path.stem}')
    if not identities:
        problems.append(f'{cid}: line 1: missing id')
    return cid, pairs, problems, identities


def read_cards(folder):
    approved, problems, seen = [], [], {}
    for path in sorted(Path(folder).glob('REV-*.md')):
        cid, pairs, errors, identities = parse_card(path)
        problems.extend(errors)
        for number, identity in identities:
            if identity in seen and seen[identity] != path.name:
                problems.append(f'{cid}: line {number}: same id in {seen[identity]} and {path.name}')
            seen[identity] = path.name
        fields = dict(pairs)
        names = [name for name, _ in pairs]
        if fields.get('status') == 'approved' and all(names.count(k) == 1 for k in ('status', 'mode')):
            approved.append((cid, pairs))
    return approved, problems


MARKS = '"“”«»„'
CLOSE = {'"': '"', '“': '”', '«': '»', '„': '”'}


def quotes(text):
    # Boundaries: 0, 1 or many pairs; unfinished, stray, nested and mixed marks; apostrophes are text.
    found, problems, opened, start = [], [], None, 0
    for index, mark in enumerate(text):
        if mark not in MARKS:
            continue
        before = text[index - 1] if index else ' '
        after = text[index + 1] if index + 1 < len(text) else ' '
        strong_open = before.isspace() and after.isalnum()
        strong_close = (before.isalnum() or before in '.,;:!?)') and not after.isalnum()
        if opened is None:
            if mark in '”»' or (mark == '"' and strong_close):
                problems.append('stray closing quote')
            else:
                opened, start = mark, index
        elif mark == CLOSE[opened] and not (mark == '"' and strong_open):
            found.append((text[start + 1:index], start, index + 1))
            opened = None
        elif mark == '"' and opened == '"':
            problems.append('nested quote marks')
        else:
            problems.append('mixed quote marks')
    if opened:
        problems.append('unfinished quote')
        found.append((text[start + 1:], start, len(text)))
    return found, list(dict.fromkeys(problems))


def field_quotes(field, text):
    # An anchor is one whole quote; marks inside it are the source's own words.
    if field != 'anchor':
        return [quote for quote, _, _ in quotes(text)[0]], quotes(text)[1]
    wrapped = len(text) > 2 and (text[0], text[-1]) in (('"', '"'), ('“', '”'), ('«', '»'))
    return [text[1:-1] if wrapped else text.strip(MARKS)], [] if wrapped else ['anchor is not in quote marks']


def card_problems(card, allow, long_ok):
    cid, fields = card
    keys, url_problems = card_sources(fields)
    problems = [f'{cid}: {problem}' for problem in url_problems]
    for field, text in fields:
        if field in SKIP:
            continue
        found, errors = field_quotes(field, text)
        problems.extend(f'{cid}: {error}' if error.startswith('anchor ') else f'{cid}: {error} in {field}' for error in errors)
        for quote in found:
            count = len(quote.split())
            if count < 2:
                continue
            if count >= 15 and (cid, field, quote) not in long_ok:
                problems.append(f'{cid}: quote of {count} words in {field}, limit 14')
            problems.extend(source_quote_problems((cid, field), quote, keys, allow))
    return problems


def source_quote_problems(location, quote, keys, allow):
    cid, field = location
    if quote in OWN or not any(ROW[key].cls in LOCKED for key in keys):
        return []
    source = allow.get((cid, quote))
    if source is None:
        return [f'{cid}: quote in {field} but the card cites a no copy source: {quote[:30]}']
    if source not in keys or ROW[source].cls in LOCKED:
        return [f'{cid}: allowed quote names source {source} that the card does not cite as a free source']
    return []


def revision_valid(evidence):
    if re.search(r'(?<![\w])(?:[0-9a-f]{40})(?![\w])|\bno revision shown\b', evidence):
        return True
    if re.search(r'\bETag\s+(?:W/)?"[^"\s]+"', evidence):
        return True
    for stamp in re.findall(r'\bLast-Modified\s+([A-Z][a-z]{2}, \d{2} [A-Z][a-z]{2} \d{4} \d{2}:\d{2}:\d{2} GMT)\b', evidence):
        try:
            if parsedate_to_datetime(stamp) is not None:
                return True
        except ValueError:
            pass
    return False


def evidence_problems(key, evidence):
    source, found = ROW[key], urls(evidence)
    hosts = {host for host, _ in source.routes} | set(source.evidence_hosts)
    if 'github.com' in hosts:
        hosts.update(RAW)
    problems = [f'{key}: Evidence url host not allowed: {url}' for url in found
                if plain_url(url) and urlsplit(url).hostname not in hosts]
    date_ok = False
    for stamp in re.findall(r'\bread\s+(\d{4}-\d{2}-\d{2})(?![\w-])', evidence):
        try:
            date_ok |= datetime.date.fromisoformat(stamp).year >= 2026
        except ValueError:
            pass
    requirements = [
        ('url', bool(found), 'an https URL with a public host'),
        ('date', date_ok, 'read and a real ISO date in 2026 or later'),
        ('revision', revision_valid(evidence), 'a commit, Last-Modified date, ETag value or no revision shown'),
    ]
    return problems + [f'{key}: Evidence {part} needs {need}' for part, valid, need in requirements if not valid]


def read_entries(text):
    section = text.partition('## Sources cited by the reviewer cards\n')[2].split('\n## ', 1)[0]
    entries, problems = {}, []
    for block in re.split(r'^### ', section, flags=re.M)[1:]:
        fields, errors = {}, []
        for line in block.splitlines()[1:]:
            if not line.strip():
                continue
            match = re.fullmatch(r'([A-Za-z]+): *(.*)', line)
            if not match:
                errors.append('unparsed line in entry')
                continue
            field, body = match.groups()
            if field in fields:
                errors.append('duplicate field ' + field)
            fields[field] = body
        key = fields.get('Key', '')
        problems.extend(f'{key}: {error}' for error in errors)
        if key in entries:
            problems.append(f'{key}: duplicate notice entry')
        entries[key] = fields
    return entries, problems


def credit_url(source):
    host, prefix = source.routes[0]
    return 'https://' + host + prefix + ('' if host == 'github.com' else '/')


def notice_contains(notice, part):
    return re.search(r'(?<!\w)' + re.escape(part) + r'(?!\w)', notice) is not None


def copyright_contains(notice, part):
    # Operational reading of exactly: allow the sentence and parenthetical forms in the real notices.
    suffix = r'(?:$|\s(?=[A-Z(]))' if part.endswith('.') else r'(?:$|\.(?=$|\s)| \()'
    return re.search(r'(?<![\w-])' + re.escape(part) + suffix, notice) is not None


def credit_prefix_matches(text, prefix):
    # Boundaries: exact text, slash extension, prose and a longer repository name.
    return (text.startswith(prefix) and (prefix.endswith('/') or
            re.match(r'(?:$|/|[^A-Za-z0-9._~/#-])', text[len(prefix):]) is not None))


def attribution_problems(source, entry):
    key, problems = source.key, []
    licence = source.label + (', ' + source.link if source.link else '')
    if entry['Licence'] != licence:
        problems.append(f'{key}: Licence must equal {licence}')
    credit = source.holder + ', ' + credit_url(source)
    credit_urls = urls(entry['Credit'])
    if (not credit_prefix_matches(entry['Credit'], credit) or not credit_urls or
            not credit_prefix_matches(credit_urls[0], credit_url(source))):
        problems.append(f'{key}: Credit must start with {credit}')
    if re.search(r'(?<!\w)paraphrased(?!\w)', entry['Changes']) is None:
        problems.append(f"{key}: Changes lacks 'paraphrased'")
    problems.extend(f"{key}: Notice lacks '{part}'" for part in source.copyright
                    if not copyright_contains(entry['Notice'], part))
    problems.extend(f"{key}: Notice lacks '{part}'" for part in notice_need(source)[len(source.copyright):]
                    if not notice_contains(entry['Notice'], part))
    return problems


def use_problems(source, use):
    needs = {'attrib': ['short quotation under 15 words'],
             'short': ['short quotation under 15 words', 'licence ___'], 'hold': ['cited only']}
    problems = []
    if ((source.cls == 'nocopy' and not any(notice_contains(use, part) for part in ('URL only', 'no quotes'))) or
            (source.cls in LOCKED and notice_contains(use, 'short quotation'))):
        problems.append(f'{source.key}: Use must say URL only or no quotes')
    return problems + [f"{source.key}: Use lacks '{part}'" for part in needs.get(source.cls, []) if not notice_contains(use, part)]


def entry_problems(entries, cited):
    problems = [f'{key}: url not plain: {url}' for key, entry in entries.items()
                for text in entry.values() for url in urls(text) if not plain_url(url)]
    for key, ids in cited.items():
        if key not in entries:
            problems.append(f'{key}: no notice entry')
            continue
        entry, source = entries[key], ROW[key]
        missing = [field for field in FIELDS if not entry.get(field, '').strip()]
        if missing:
            problems.append(f'{key}: empty or missing field {", ".join(missing)}')
            continue
        problems.extend(attribution_problems(source, entry))
        problems.extend(evidence_problems(key, entry['Evidence']))
        problems.extend(use_problems(source, entry['Use']))
        listed = [cid for cid in re.split(r'[,\s]+', entry['Cards']) if cid]
        if any(re.fullmatch(r'REV-[0-9A-Z]+', cid) is None for cid in listed) or set(listed) != ids:
            problems.append(f'{key}: Cards line differs from the cards that name it')
    return problems


def text_problems(text, used):
    section = text.partition('## Licence texts\n')[2].split('\n## ', 1)[0]
    blocks = re.findall(r'^### ([^\n]+)\n(.*?)(?=^### |\Z)', section, re.M | re.S)
    problems = []
    for label in sorted(used.intersection(REFERENCES)):
        filename = REFERENCES[label][0]
        bodies = [body for heading, body in blocks if heading == label]
        match = re.fullmatch(r'\s*```text[ \t]*\n(.*?)\n```\s*', bodies[0], re.S) if len(bodies) == 1 else None
        reference = (REFS / filename).read_text(encoding='utf-8')
        if match is None or match[1].split() != reference.split():
            problems.append(f'licence text {label} differs from tools/licence_refs/{filename}')
    return problems


def reference_problems(folder=REFS):
    return [f'licence reference {filename} hash differs' for filename, digest in REFERENCES.values()
            if hashlib.sha256((Path(folder) / filename).read_bytes().replace(b'\r\n', b'\n')).hexdigest() != digest]


def check(cards_dir=CARDS, notices=NOTICES, allow=ALLOW, long_ok=LONG_OK):
    approved, problems = read_cards(cards_dir)
    cited, seen_allow, seen_long = {}, set(), set()
    for cid, fields in approved:
        for key in card_sources(fields)[0]:
            cited.setdefault(key, set()).add(cid)
        problems.extend(card_problems((cid, fields), allow, long_ok))
        for field, text in fields:
            if field not in SKIP:
                for quote in field_quotes(field, text)[0]:
                    if len(quote.split()) >= 2:
                        seen_allow.add((cid, quote))
                    if len(quote.split()) >= 15:
                        seen_long.add((cid, field, quote))
    text = Path(notices).read_text(encoding='utf-8')
    entries, entry_errors = read_entries(text)
    problems.extend(entry_errors + entry_problems(entries, cited))
    problems.extend(text_problems(text, {ROW[key].label for key in cited}))
    problems.extend(f'ALLOW entry matches no quote: {entry}' for entry in sorted(set(allow) - seen_allow))
    problems.extend(f'LONG_OK entry matches no long quote: {entry}' for entry in sorted(set(long_ok) - seen_long))
    return problems


def notice_need(source):
    required = list(source.copyright)
    if source.label in REFERENCES:
        return required + ['Licence text: ' + source.label]
    if source.label.startswith('CC BY'):
        return required + ['licensed under ' + source.label, source.link, 'We changed it', 'no warranty']
    if source.label == 'GNU FDL 1.3 or later':
        return required + [GFDL]
    return required + [{ '___': 'licence ___', 'copyright waived by the author': 'has waived all copyright'
                       }.get(source.label, 'nothing copied')]


GOOGLE = 'https://google.github.io/eng-practices/review/'
GIT = 'https://git-scm.com/docs/git-diff'
GH = 'https://docs.github.com/en/pull-requests/reference/branches'
GH_QUOTE = 'Pull requests on GitHub show a three-dot diff.'
WORDS15 = ' '.join(['word'] * 15)


def entry_text(key, ids):
    source = ROW[key]
    use = {'attrib': 'short quotation under 15 words, with credit',
           'short': 'short quotation under 15 words, licence ___',
           'hold': 'cited only, nothing copied, licence ___', 'nocopy': 'URL only, nothing copied'}
    return dict(zip(FIELDS, [key, f'{source.holder}, {credit_url(source)}',
                source.label + (', ' + source.link if source.link else ''),
                credit_url(source) + ' read 2026-10-28, no revision shown',
                'short phrases quoted; the rest is ours, paraphrased.', use[source.cls],
                ' '.join(part if part.endswith(('.', '/')) else part + '.' for part in notice_need(source)), ', '.join(ids)]))


def fixture():
    specs = [
        ('google', GOOGLE, '"make sure the whole system keeps working"'),
        ('git-docs', GIT + ' ; ' + GH, None),
        ('owasp-cs', 'https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html', None),
        ('laravel-docs', 'https://laravel.com/docs/12.x/queries', None),
        ('phpmd', 'https://phpmd.org/rules/codesize.html', None),
        ('aihero', 'https://www.aihero.dev/skills-improve-codebase-architecture', '"would its complexity move behind a smaller interface"'),
        ('linux', 'https://www.kernel.org/doc/html/latest/process/submitting-patches.html', None),
        ('php-manual', 'https://www.php.net/manual/en/copyright.php', None),
        ('unicode-data', 'https://www.unicode.org/Public/18.0.0/ucd/Scripts.txt', None),
    ]
    cards, entries = {}, {}
    for number, (key, url, anchor) in enumerate(specs, 901):
        cid = f'REV-{number}'
        card = f'id: {cid}\nrule: r\nstatus: approved\nmode: all\nsource: {url}\n'
        cards[cid] = card + (f'anchor: {anchor}\n' if anchor else '')
        entries[key] = entry_text(key, [cid])
    cards['REV-902'] += f'extra: GitHub says "{GH_QUOTE}" Not copied.\n'
    cards['REV-904'] += 'extra: The page says "not checked" is ours.\n'
    entries['github-docs'] = entry_text('github-docs', ['REV-902'])
    return {'cards': cards, 'entries': entries,
            'texts': {label: (REFS / filename).read_text(encoding='utf-8')
                      for label, (filename, _) in REFERENCES.items()},
            'refs': {filename: (REFS / filename).read_bytes() for filename, _ in REFERENCES.values()},
            'allow': {('REV-902', GH_QUOTE): 'github-docs'}, 'long_ok': set()}


def build(tree):
    with tempfile.TemporaryDirectory(prefix='reviewer-notices-') as folder:
        root = Path(folder)
        for cid, body in tree['cards'].items():
            (root / f'{cid}.md').write_text(body, encoding='utf-8', newline='\n')
        entries = ''.join(f'### {key}\n' + ''.join(f'{name}: {body}\n' for name, body in fields.items())
                          for key, fields in tree['entries'].items())
        blocks = ''.join(f'### {label}\n\n```text\n{body}\n```\n' for label, body in tree['texts'].items())
        notices = root / 'notices.md'
        notices.write_text('## Sources cited by the reviewer cards\n' + entries + '\n## Licence texts\n' + blocks,
                           encoding='utf-8', newline='\n')
        refs = root / 'licence_refs'
        refs.mkdir()
        for filename, raw in tree['refs'].items():
            (refs / filename).write_bytes(raw)
        return check(root, notices, tree['allow'], tree['long_ok']) + reference_problems(refs)


def card_change(cid, field, body):
    def change(tree):
        text = tree['cards'][cid]
        line = f'{field}: {body}\n'
        tree['cards'][cid] = re.sub(r'^' + re.escape(field) + r':.*\n', lambda _: line, text, flags=re.M) \
            if re.search(r'^' + re.escape(field) + ':', text, re.M) else text + line
    return change


def entry_change(key, field, body):
    def change(tree):
        if body is None:
            del tree['entries'][key][field]
        else:
            tree['entries'][key][field] = body
    return change


class Controls(unittest.TestCase):
    def run_case(self, case, change, expected, tree=None):
        with self.subTest(case=case):
            tree = fixture() if tree is None else tree
            self.assertEqual(build(tree), [], 'starting fixture: ' + case)
            change(tree)
            self.assertEqual(sorted(build(tree)), sorted(expected))

    def test_starting_fixture_passes(self):
        self.assertEqual(build(fixture()), [])

    def test_code2_url_extraction_attacks(self):
        # Removing the plain check must expose each complete hostile run.
        def unicode_report(tree):
            card_change('REV-909', 'source', 'https://www.unicode.org/Public/;x/../../reports/tr35/')(tree)
            card_change('REV-909', 'anchor', '"Detect renames."')(tree)
            tree['entries']['unicode-reports'] = entry_text('unicode-reports', ['REV-909'])
        self.run_case('code2 Unicode semicolon traversal', unicode_report,
                      ['REV-909: url not plain: https://www.unicode.org/Public/;x/../../reports/tr35/'])
        for separator in [';', ',']:
            url = 'https://evil.example' + separator + '@git-scm.com/docs/git-diff'
            def spoof(tree):
                card_change('REV-901', 'source', url)(tree)
                card_change('REV-901', 'anchor', '"Detect renames."')(tree)
            self.run_case('code2 authority separator ' + separator, spoof, ['REV-901: url not plain: ' + url])

    def test_code2_credit_traversal(self):
        for key, cid, url, holder in [('google', 'REV-901', 'https://google.github.io/eng-practices/../other', 'Google'),
                                      ('pstack', 'REV-910', 'https://github.com/backnotprop/pstack/../pstack-other', 'Lauren Tan')]:
            tree = fixture()
            if key == 'pstack':
                tree['cards'][cid] = 'id: REV-910\nstatus: approved\nmode: all\nsource: https://github.com/backnotprop/pstack\n'
                tree['entries'][key] = entry_text(key, [cid])
            self.run_case('code2 credit traversal ' + key, entry_change(key, 'Credit', holder + ', ' + url),
                          [f'{key}: url not plain: {url}'], tree)

    def test_credit_prefix_allows_real_paths(self):
        # Exact equality would reject the real trailing slash and deeper path credits.
        for key, url, holder in [
            ('laravel-framework', 'https://github.com/laravel/framework/', 'Taylor Otwell'),
            ('composer', 'https://getcomposer.org/doc/', 'Nils Adermann, Jordi Boggiano'),
        ]:
            tree = fixture()
            tree['cards']['REV-910'] = f'id: REV-910\nstatus: approved\nmode: all\nsource: {url}\n'
            tree['entries'][key] = entry_text(key, ['REV-910'])
            self.run_case('credit real path ' + key, entry_change(key, 'Credit', holder + ', ' + url), [], tree)

    def test_credit_repository_boundary(self):
        url = 'https://github.com/backnotprop/pstack'
        for suffix, expected in [
            ('Other', ['pstack: Credit must start with Lauren Tan, ' + url]),
            ('.other', ['pstack: Credit must start with Lauren Tan, ' + url]),
            ('_other', ['pstack: Credit must start with Lauren Tan, ' + url]),
            ('~other', ['pstack: Credit must start with Lauren Tan, ' + url]),
            ('#other', ['pstack: Credit must start with Lauren Tan, ' + url]),
            ('/blob/main/LICENSE', []), (' with credit', []),
            ('?other', ['pstack: url not plain: ' + url + '?other']),
            (';other', ['pstack: url not plain: ' + url + ';other']),
            ('%2fother', ['pstack: url not plain: ' + url + '%2fother']),
        ]:
            tree = fixture()
            tree['cards']['REV-910'] = f'id: REV-910\nstatus: approved\nmode: all\nsource: {url}\n'
            tree['entries']['pstack'] = entry_text('pstack', ['REV-910'])
            self.run_case('credit repository boundary ' + suffix,
                          entry_change('pstack', 'Credit', 'Lauren Tan, ' + url + suffix), expected, tree)

    def test_code2_copyright_continuations(self):
        # Boundaries: surname suffix, hyphen, comma, space, slash and allowed parenthetical.
        for suffix in ['son', '-Smith', ' Smith', ', Smith', '/x']:
            self.run_case('code2 Otwell continuation ' + suffix, entry_change('laravel-docs', 'Notice',
                          'Copyright (c) Taylor Otwell' + suffix + '. Licence text: MIT'),
                          ["laravel-docs: Notice lacks 'Copyright (c) Taylor Otwell'"])
        self.run_case('code2 copyright parenthetical', entry_change('github-docs', 'Notice',
                      'GitHub Inc. (c) 2026 (page footer). licensed under CC BY 4.0 ' + CC4 + ' We changed it, no warranty'), [])
        for prefix in ['Other', 'Other-', 'Other_']:
            self.run_case('copyright preceding name ' + prefix, entry_change('laravel-docs', 'Notice',
                          prefix + 'Copyright (c) Taylor Otwell. Licence text: MIT'),
                          ["laravel-docs: Notice lacks 'Copyright (c) Taylor Otwell'"])
        for suffix, expected in [
            ('smith', ["unicode-data: Notice lacks 'Copyright (c) 1991 to 2026 Unicode, Inc.'"]),
            (' smith', ["unicode-data: Notice lacks 'Copyright (c) 1991 to 2026 Unicode, Inc.'"]),
            (' Next sentence.', []), (' (page footer)', []),
        ]:
            self.run_case('copyright final dot ' + suffix, entry_change('unicode-data', 'Notice',
                          'Licence text: Unicode License v3. Copyright (c) 1991 to 2026 Unicode, Inc.' + suffix), expected)

    def test_code2_host_escapes(self):
        for url in ['https://%6caravel.com/docs/12.x/queries', 'https://läravel.com/docs/12.x/queries']:
            self.run_case('code2 escaped or Unicode host ' + url, card_change('REV-904', 'source', url),
                          ['REV-904: url not plain: ' + url])
        url = 'https://xn--lravel-bua.com/docs/12.x/queries'
        self.run_case('code2 punycode host is plain but unmapped', card_change('REV-904', 'source', url),
                      ['REV-904: no licence class for URL ' + url])

    def test_use_whole_phrases(self):
        for key, use, expected in [
            ('git-docs', 'URL onlyness', ['git-docs: Use must say URL only or no quotes']),
            ('git-docs', 'no quotes2', ['git-docs: Use must say URL only or no quotes']),
            ('git-docs', '_URL only', ['git-docs: Use must say URL only or no quotes']),
            ('google', 'short quotation under 15 wordsExtra', ["google: Use lacks 'short quotation under 15 words'"]),
            ('aihero', 'short quotation under 15 words, licence ____', ["aihero: Use lacks 'licence ___'"]),
            ('git-docs', 'URL only, nothing copied', []), ('git-docs', 'no quotes, nothing copied', []),
        ]:
            self.run_case('whole Use ' + use, entry_change(key, 'Use', use), expected)
        tree = fixture()
        tree['cards']['REV-910'] = 'id: REV-910\nstatus: approved\nmode: all\nsource: https://refactoring.com/\n'
        tree['entries']['refactoring-com'] = entry_text('refactoring-com', ['REV-910'])
        self.run_case('whole Use hold', entry_change('refactoring-com', 'Use', 'cited onlyness'),
                      ["refactoring-com: Use lacks 'cited only'"], tree)

    def test_plain_url_boundaries(self):
        # Boundaries: scheme, labels, authority, every forbidden path character and fragment count.
        bad = ['http://laravel.com/docs', 'HTTPS://laravel.com/docs', 'https://LARAVEL.com/docs',
               'https://laravel.com:443/docs', 'https://user' + chr(64) + 'laravel.com/docs', 'https://laravel.com./docs',
               'https://laravel..com/docs', 'https://.laravel.com/docs', 'https://-laravel.com/docs',
               'https://laravel-.com/docs', 'https://laravel_com/docs', 'https://laravel/docs',
               'https://123.com/docs', 'https://0xabc.com/docs', 'https://laravel.com/docs/./x',
               'https://laravel.com/docs/../x', 'https://laravel.com/docs#one#two']
        bad += ['https://laravel.com/docs/a' + char + 'b' for char in ['%', ';', ',', '@', '?', '\\', ':', "'", '!', '=', '+', '&', '[', '<']]
        bad += ['https://laravel.com/docs#x' + char + 'y' for char in ['%', ';', '@', '?', '\\', ':', "'"]]
        for url in bad:
            self.run_case('plain refused ' + url, card_change('REV-904', 'extra', url), ['REV-904: url not plain: ' + url])
        self.run_case('plain empty path', card_change('REV-904', 'extra', 'https://laravel.com'),
                      ['REV-904: no licence class for URL https://laravel.com'])
        self.run_case('plain fragment and double slash', card_change('REV-904', 'source', 'https://laravel.com/docs//x#A_z-0.~//'), [])
        self.run_case('plain dot fragment', card_change('REV-904', 'extra', 'https://laravel.com/docs/x#..'), [])
        self.run_case('plain skipped review', card_change('REV-904', 'review', 'https://bad'), [])
        for field in ['rule', 'source', 'example', 'extra', 'why', 'trigger', 'applies-when', 'not-when', 'mode']:
            self.run_case('plain card field ' + field, card_change('REV-904', field, 'https://bad'), ['REV-904: url not plain: https://bad'])

    def test_exact_http_examples(self):
        for url in ['http://evil.example', 'https://evil.example', 'http://169.254.169.254/']:
            self.run_case('exact HTTP example ' + url, card_change('REV-904', 'example', 'Example ' + url + ','), [])
        for url in ['http://evil.example/x', 'http://169.254.169.254/x', 'http://laravel.com/docs']:
            self.run_case('HTTP outside exception ' + url, card_change('REV-904', 'example', url), ['REV-904: url not plain: ' + url])
        self.run_case('HTTPS example host is classified', card_change('REV-904', 'example', 'https://evil.example/x'),
                      ['REV-904: no licence class for URL https://evil.example/x'])

    def test_evidence_belongs_to_source(self):
        suffix = ' read 2026-10-28 no revision shown'
        for name, key, url, expected in [
            ('own host', 'google', 'https://google.github.io/eng-practices/', []),
            ('GitHub backed docs evidence', 'github-docs', 'https://raw.githubusercontent.com/github/docs/main/LICENSE', []),
            ('GitHub route raw evidence', 'pstack', 'https://raw.githubusercontent.com/backnotprop/pstack/main/LICENSE', []),
            ('GitHub backed raw evidence', 'google', 'https://raw.githubusercontent.com/google/eng-practices/main/LICENSE', []),
            ('no GitHub repo', 'aihero', 'https://raw.githubusercontent.com/google/eng-practices/main/LICENSE',
             ['aihero: Evidence url host not allowed: https://raw.githubusercontent.com/google/eng-practices/main/LICENSE']),
            ('another host', 'google', 'https://docs.github.com/', ['google: Evidence url host not allowed: https://docs.github.com/']),
        ]:
            tree = fixture()
            if key == 'pstack':
                tree['cards']['REV-910'] = 'id: REV-910\nstatus: approved\nmode: all\nsource: https://github.com/backnotprop/pstack\n'
                tree['entries'][key] = entry_text(key, ['REV-910'])
            self.run_case('evidence source ' + name, entry_change(key, 'Evidence', url + suffix), expected, tree)
        self.run_case('evidence every URL', entry_change('google', 'Evidence', 'https://google.github.io/ ' + 'https://bad' + suffix),
                      ['google: url not plain: https://bad'])

    def test_code2_numeric_evidence(self):
        for url in ['https://127.1/', 'https://0177.0.0.1/...', 'https://0x7f.0.0.1/...']:
            self.run_case('code2 numeric evidence ' + url, entry_change('google', 'Evidence', url + ' read 2026-10-28 no revision shown'),
                          ['google: url not plain: ' + url])

    def test_notice_urls_in_every_field(self):
        url = 'https://laravel.com/docs?bad'
        for field, other in [
            ('Key', []), ('Credit', []), ('Licence', ['google: Licence must equal CC BY 3.0, ' + CC3]),
            ('Evidence', []), ('Changes', []), ('Use', []), ('Notice', []),
            ('Cards', ['google: Cards line differs from the cards that name it']),
        ]:
            # Keep the lookup key stable when testing a malformed Key URL in an unused entry.
            tree = fixture()
            if field == 'Key':
                tree['entries']['unused'] = entry_text('google', ['REV-901'])
                tree['entries']['unused']['Key'] = 'unused'
                key = 'unused'
            else:
                key = 'google'
            body = tree['entries'][key][field] + ' ' + url
            location = body if field == 'Key' else key
            self.run_case('plain notice field ' + field, entry_change(key, field, body),
                          [location + ': url not plain: ' + url] + other, tree)

    def test_url_run_terminators_and_single_strip(self):
        # Boundaries: 1 trailing mark, repeated marks, slash dot, internal punctuation and run endings.
        for suffix, extracted, expected in [
            ('.', 'https://laravel.com/docs/x', []), (',', 'https://laravel.com/docs/x', []),
            (';', 'https://laravel.com/docs/x', []), (':', 'https://laravel.com/docs/x', []),
            ('..', 'https://laravel.com/docs/x..', []),
            (',;', 'https://laravel.com/docs/x,', ['REV-904: url not plain: https://laravel.com/docs/x,']),
            ('/.,', 'https://laravel.com/docs/x/.', ['REV-904: url not plain: https://laravel.com/docs/x/.']),
            ('/.', 'https://laravel.com/docs/x/.', ['REV-904: url not plain: https://laravel.com/docs/x/.']),
            (';inside', 'https://laravel.com/docs/x;inside', ['REV-904: url not plain: https://laravel.com/docs/x;inside']),
            (',inside', 'https://laravel.com/docs/x,inside', ['REV-904: url not plain: https://laravel.com/docs/x,inside']),
        ]:
            body = 'https://laravel.com/docs/x' + suffix
            with self.subTest(extraction=suffix):
                self.assertEqual(urls(body), [extracted])
            self.run_case('URL trailing strip ' + suffix, card_change('REV-904', 'extra', body), expected)
        for mark in [')', ']', '}', '>', '"', '“', '”', '«', '»', '„', ' ', '\t', '\n']:
            with self.subTest(terminator=mark):
                self.assertEqual(urls('https://laravel.com/docs/x' + mark + 'tail'), ['https://laravel.com/docs/x'])
            if mark in [')', ']', '}', '>']:
                self.run_case('URL closing bracket ' + mark, card_change('REV-904', 'extra', 'https://laravel.com/docs/x' + mark), [])
        self.run_case('URL quote cut', card_change('REV-904', 'extra', '"https://laravel.com/docs/x"'), [])

    def test_original_bad_controls(self):
        run = self.run_case
        locked = ' but the card cites a no copy source: '
        run('notice 1 missing entry', lambda t: t['entries'].pop('git-docs'), ['git-docs: no notice entry'])
        run('notice 2 wrong licence', entry_change('google', 'Licence', 'CC BY 4.0, ' + CC4), ['google: Licence must equal CC BY 3.0, ' + CC3])
        run('notice 3 empty credit', entry_change('google', 'Credit', ''), ['google: empty or missing field Credit'])
        run('notice 4 missing changes', entry_change('google', 'Changes', None), ['google: empty or missing field Changes'])
        run('notice 5 changes wording', entry_change('google', 'Changes', 'short phrases quoted'), ["google: Changes lacks 'paraphrased'"])
        run('notice 6 copyright', entry_change('laravel-docs', 'Notice', 'Licence text: MIT'), ["laravel-docs: Notice lacks 'Copyright (c) Taylor Otwell'"])
        run('text 7 swapped BSD', lambda t: t['texts'].update({'BSD 3 Clause': t['texts']['MIT']}), ['licence text BSD 3 Clause differs from tools/licence_refs/bsd-3-clause.txt'])
        run('notice 8 card list', entry_change('google', 'Cards', 'REV-999'), ['google: Cards line differs from the cards that name it'])
        run('evidence 9 no date', entry_change('google', 'Evidence', 'https://google.github.io/ no revision shown'), ['google: Evidence date needs read and a real ISO date in 2026 or later'])
        run('evidence 10 no revision', entry_change('google', 'Evidence', 'https://google.github.io/ read 2026-10-28'), ['google: Evidence revision needs a commit, Last-Modified date, ETag value or no revision shown'])
        run('notice 11 use short', entry_change('aihero', 'Use', 'cited only'), ["aihero: Use lacks 'short quotation under 15 words'", "aihero: Use lacks 'licence ___'"])
        run('notice 12 unknown licence', entry_change('aihero', 'Licence', 'MIT, ' + MIT), ['aihero: Licence must equal ___'])
        for number, field in ((13, 'anchor'), (14, 'extra'), (15, 'why')):
            body = f'GitHub says "{GH_QUOTE}" See "Detect renames."' if field == 'extra' else '"Detect renames."'
            run(f'quote {number} Git {field}', card_change('REV-902', field, body), [f'REV-902: quote in {field}' + locked + 'Detect renames.'])
        run('quote 16 source order', card_change('REV-902', 'source', GH + ' ; ' + GIT + ' "Detect renames."'), ['REV-902: quote in source' + locked + 'Detect renames.'])
        run('quote 17 long extra', card_change('REV-906', 'extra', '"' + ' '.join(['word'] * 16) + '"'), ['REV-906: quote of 16 words in extra, limit 14'])
        run('quote 18 OWASP anchor', card_change('REV-903', 'anchor', '"A valid signature proves who sent the payload"'), ['REV-903: quote in anchor' + locked + 'A valid signature proves who s'])
        run('quote 19 wrong allowed source', lambda t: t['allow'].update({('REV-902', GH_QUOTE): 'laravel-docs'}), ['REV-902: allowed quote names source laravel-docs that the card does not cite as a free source'])
        run('quote 20 unquoted anchor', card_change('REV-901', 'anchor', 'make sure'), ['REV-901: anchor is not in quote marks'])
        run('url 21 unknown URL', card_change('REV-901', 'extra', 'https://unknown.example/x'), ['REV-901: no licence class for URL https://unknown.example/x'])
        run('notice 22 extra only source', card_change('REV-901', 'extra', COGNITECT), ['cognitect: no notice entry'])
        run('notice 23 extra missing card', card_change('REV-904', 'extra', GOOGLE + 'x'), ['google: Cards line differs from the cards that name it'])
        run('notice 24 forbidden use', entry_change('git-docs', 'Use', 'short quotation under 15 words'), ['git-docs: Use must say URL only or no quotes'])
        run('quote 25 unfinished straight', card_change('REV-901', 'rule', 'say "ok'), ['REV-901: unfinished quote in rule'])
        run('stale 26 stale ALLOW', lambda t: t['allow'].update({('REV-902', 'no such quote'): 'github-docs'}), ["ALLOW entry matches no quote: ('REV-902', 'no such quote')"])

    def test_full_text_controls(self):
        for label, (filename, _) in REFERENCES.items():
            for name, edit in [('truncated', lambda s: s[:len(s) // 2]), ('word changed', lambda s: 'CHANGED ' + s.split(maxsplit=1)[1]),
                               ('extra paragraph', lambda s: s + '\nExtra paragraph.'), ('empty', lambda s: ''),
                               ('other licence', lambda s: (REFS / ('bsd-3-clause.txt' if label == 'MIT' else 'mit.txt')).read_text(encoding='utf-8'))]:
                self.run_case(f'text {label} {name}', lambda t: t['texts'].update({label: edit(t['texts'][label])}), [f'licence text {label} differs from tools/licence_refs/{filename}'])
            self.run_case(f'text {label} missing', lambda t: t['texts'].pop(label), [f'licence text {label} differs from tools/licence_refs/{filename}'])

    def test_evidence_controls(self):
        url = 'https://google.github.io/ '
        valid = url + 'read 2026-10-28, '
        cases = [('bad month', url + 'read 2026-99-99, no revision shown', 'date'),
                 ('bad day', url + 'read 2026-02-30, no revision shown', 'date'),
                 ('old year', url + 'read 2025-10-28, no revision shown', 'date'),
                 ('no read', url + '2026-10-28 no revision shown', 'date'),
                 ('bare ETag', valid + 'ETag', 'revision'), ('bare Last-Modified', valid + 'Last-Modified', 'revision'),
                 ('39 hex', valid + 'a' * 39, 'revision'), ('41 hex', valid + 'a' * 41, 'revision'),
                 ('no URL', 'read 2026-10-28 no revision shown', 'url')]
        errors = {'url': 'needs an https URL with a public host', 'date': 'needs read and a real ISO date in 2026 or later',
                  'revision': 'needs a commit, Last-Modified date, ETag value or no revision shown'}
        for name, evidence, part in cases:
            self.run_case('evidence ' + name, entry_change('google', 'Evidence', evidence), [f'google: Evidence {part} {errors[part]}'])
        self.run_case('evidence invalid host', entry_change('google', 'Evidence',
                      'https://example.invalid read 2026-10-28 no revision shown'),
                      ['google: Evidence url host not allowed: https://example.invalid'])
        self.run_case('evidence all bad parts', entry_change('google', 'Evidence', 'https://example.invalid 2026-99-99 ETag'),
                      ['google: Evidence url host not allowed: https://example.invalid'] +
                      [f'google: Evidence {part} {errors[part]}' for part in ('date', 'revision')])

    def test_exact_label_and_credit_controls(self):
        for key, body in [('aihero', 'MIT ___'), ('linux', 'GPL 2.0 or later, ' + GPL),
                          ('google', 'CC BY 4.0, ' + CC4 + ' (was CC BY 3.0)'),
                          ('php-manual', 'CC BY 3.0, ' + CC3), ('google', 'CC BY 3.0')]:
            source = ROW[key]
            expected = source.label + (', ' + source.link if source.link else '')
            self.run_case('notice label ' + body, entry_change(key, 'Licence', body), [f'{key}: Licence must equal {expected}'])
        for body in ['Wrong holder, ' + GOOGLE, 'Google']:
            self.run_case('notice credit ' + body, entry_change('google', 'Credit', body), ['google: Credit must start with Google, https://google.github.io/eng-practices/'])

    def test_quote_controls(self):
        self.run_case('quote unfinished curly Git', card_change('REV-902', 'why', '“Detect renames.'), ['REV-902: unfinished quote in why', 'REV-902: quote in why but the card cites a no copy source: Detect renames.'])
        self.run_case('quote stray closing', card_change('REV-901', 'why', 'stray ”'), ['REV-901: stray closing quote in why'])
        for body in ['“bad "mark”', '"bad “mark"']:
            self.run_case('quote mixed marks ' + body, card_change('REV-901', 'why', body), ['REV-901: mixed quote marks in why'])
        for field in ['rule', 'example', 'applies-when', 'not-when', 'trigger', 'why', 'extra', 'anchor']:
            self.run_case('quote 15 words ' + field, card_change('REV-906', field, '"' + WORDS15 + '"'), [f'REV-906: quote of 15 words in {field}, limit 14'])
        self.run_case('quote stale LONG_OK', lambda t: t['long_ok'].add(('REV-901', 'rule', 'no such quote')), ["LONG_OK entry matches no long quote: ('REV-901', 'rule', 'no such quote')"])

    def test_parser_controls(self):
        def append(cid, text):
            return lambda t: t['cards'].update({cid: t['cards'][cid] + text})
        self.run_case('parser duplicate why', append('REV-902', 'why: "Detect renames."\nwhy: ours\n'), ['REV-902: line 8: duplicate field why', 'REV-902: quote in why but the card cites a no copy source: Detect renames.'])
        for body in ['  "Detect renames."', 'bare sentence', '---']:
            self.run_case('parser unparsed ' + body, append('REV-902', body + '\n'), ['REV-902: line 7: expected key: value'])
        self.run_case('parser same id', lambda t: t['cards'].update({'REV-910': 'id: REV-902\nstatus: draft\nmode: all\n'}), ['REV-902: line 1: id differs from file name REV-910', 'REV-902: line 1: same id in REV-902.md and REV-910.md'])
        self.run_case('parser wrong id', card_change('REV-909', 'id', 'REV-999'), ['REV-999: line 1: id differs from file name REV-909', 'unicode-data: Cards line differs from the cards that name it'])
        for field in ['status', 'mode']:
            self.run_case('parser duplicate ' + field, append('REV-909', field + ': approved\n'), [f'REV-909: line 6: duplicate field {field}'])

    def test_url_controls(self):
        self.run_case('url query refused', card_change('REV-901', 'extra', 'https://unknown.example/?x=evil.example'),
                      ['REV-901: url not plain: https://unknown.example/?x=evil.example'])
        bad = ['https://github.com/backnotprop/pstack-other',
               'https://github.com.evil.example/backnotprop/pstack', 'https://evil.example.com/x', 'https://laravel.com/docsx/queries']
        for url in bad:
            self.run_case('url ' + url, card_change('REV-901', 'extra', url), ['REV-901: no licence class for URL ' + url])

    def test_known_good_variants_pass(self):
        variants = [
            ('draft unknown source', lambda t: t['cards'].update({'REV-910': 'id: REV-910\nstatus: draft\nmode: all\nsource: https://unknown.example/x\n'})),
            ('exact example only', lambda t: t['cards'].update({'REV-910': 'id: REV-910\nstatus: approved\nmode: all\nsource: http://evil.example\n'})),
            ('own locked', card_change('REV-903', 'extra', 'ours: "not checked"')),
            ('short free', card_change('REV-901', 'extra', '"a twelve word quote is fine here for a free source ok"')),
            ('curly anchor', card_change('REV-901', 'anchor', '“make sure the whole system keeps working”')),
            ('14 words', card_change('REV-906', 'rule', '"' + ' '.join(['word'] * 14) + '"')),
            ('base path URL', card_change('REV-904', 'source', 'https://laravel.com/docs')),
            ('whitespace licence', lambda t: t['texts'].update({label: '\r\n\t'.join(body.split()) for label, body in t['texts'].items()})),
        ]
        for name, change in variants:
            self.run_case('good ' + name, change, [])
        self.run_case('query URL now refused', card_change('REV-904', 'source', 'https://laravel.com/docs/12.x/queries?x=1#a'),
                      ['REV-904: url not plain: https://laravel.com/docs/12.x/queries?x=1#a'])
        for revision in ['a' * 40, 'Last-Modified Wed, 28 Oct 2026 11:46:56 GMT', 'ETag "abc"', 'ETag W/"abc"']:
            self.run_case('good revision ' + revision, entry_change('google', 'Evidence', 'https://google.github.io/ read 2026-10-28 ' + revision), [])

    def test_extra_bad_inputs(self):
        revision_error = ['google: Evidence revision needs a commit, Last-Modified date, ETag value or no revision shown']
        prefix = 'https://google.github.io/ read 2026-10-28 '
        self.run_case('extra 1 empty ETag', entry_change('google', 'Evidence', prefix + 'ETag ""'), revision_error)
        self.run_case('extra 2 impossible HTTP date', entry_change('google', 'Evidence', prefix + 'Last-Modified Wed, 30 Feb 2026 11:46:56 GMT'), revision_error)
        self.run_case('extra 3 text outside fence', lambda t: t['texts'].update({'MIT': t['texts']['MIT'] + '\n```\nExtra paragraph.\n```text'}), ['licence text MIT differs from tools/licence_refs/mit.txt'])
        url = 'https://evil.example' + chr(64) + 'github.com/backnotprop/pstack-other'
        self.run_case('extra 4 userinfo spoof', card_change('REV-901', 'extra', url), ['REV-901: url not plain: ' + url])
        self.run_case('extra 5 duplicate notice key', lambda t: t['entries'].update({'duplicate-google': dict(t['entries']['google'])}), ['google: duplicate notice entry'])

    def test_review_controls(self):
        locked = 'REV-902: quote in why but the card cites a no copy source: '
        self.run_case('review 1 straight quote nested in straight quote', card_change('REV-902', 'why', '"x "Detect renames." y"'),
                      ['REV-902: nested quote marks in why', 'REV-902: stray closing quote in why', locked + 'x "Detect renames.'])
        self.run_case('review 2 uppercase scheme and host', card_change('REV-901', 'extra', 'HTTPS://UNKNOWN.EXAMPLE/x'),
                      ['REV-901: url not plain: HTTPS://UNKNOWN.EXAMPLE/x'])
        self.run_case('review 3 guillemets', card_change('REV-902', 'why', '«Detect renames.»'), [locked + 'Detect renames.'])
        self.run_case('review 4 nested anchor on a no copy card', card_change('REV-903', 'anchor', '"A “signed” payload proves who sent it"'),
                      ['REV-903: quote in anchor but the card cites a no copy source: A “signed” payload proves who '])
        for name, anchor in (('curly inside straight', '"Eager loading alleviates the “N + 1” query problem"'),
                             ('straight inside straight', '"using the "default" translation of the string as the key"')):
            self.run_case('good nested anchor ' + name, card_change('REV-901', 'anchor', anchor), [])
        self.run_case('uppercase URL now refused', card_change('REV-904', 'source', 'HTTPS://LARAVEL.COM/docs/12.x/queries'),
                      ['REV-904: url not plain: HTTPS://LARAVEL.COM/docs/12.x/queries'])

    def test_changed_references_are_rejected(self):
        for label, (filename, _) in REFERENCES.items():
            self.run_case('reference reference ' + label, lambda t: t['refs'].update({filename: b'changed\n'}), [f'licence reference {filename} hash differs'])

    def test_review_path_normalisation(self):
        # Boundaries: encoded or plain dots, root escape, separators and equivalent hosts.
        def report(url):
            def change(tree):
                card_change('REV-909', 'source', url)(tree)
                card_change('REV-909', 'anchor', '"Detect renames."')(tree)
                tree['entries']['unicode-reports'] = entry_text('unicode-reports', ['REV-909'])
            return change
        for path in ['/Public/%2e%2e/reports/tr35/', '/Public/../reports/tr35/']:
            url = 'https://www.unicode.org' + path
            self.run_case('review Unicode ' + path, report(url),
                          ['REV-909: url not plain: ' + url])
            self.assertIsNone(source_key(url))
        for path in ['/Public/../../reports/tr35/', '/Public/%2f/reports', '/Public/%5c/reports']:
            url = 'https://www.unicode.org' + path
            self.run_case('review unmapped ' + path, card_change('REV-909', 'source', url),
                          ['REV-909: url not plain: ' + url])
        for url in ['https://laravel.com/%64ocs/12.x/queries', 'https://laravel.com.:443/docs/12.x/queries']:
            self.run_case('review Laravel ' + url, card_change('REV-904', 'source', url), ['REV-904: url not plain: ' + url])
            self.assertIsNone(source_key(url))
        self.run_case('review normalised test host', card_change('REV-901', 'extra', 'https://evil.example.:443/a/../x'),
                      ['REV-901: url not plain: https://evil.example.:443/a/../x'])
        url = 'https://evil.example/../../x'
        self.run_case('review test host root escape', card_change('REV-901', 'extra', url),
                      ['REV-901: url not plain: ' + url])
        for key, url in [
            ('unicode-reports', 'https://www.unicode.org/reports/tr35/'),
            ('unicode-reports', 'https://unicode.org/reports/tr35/'),
            ('laravel-docs', 'https://laravel.com/docs/12.x/queries#x'),
            ('laravel-docs', 'https://laravel.com/docs//12.x/queries'),
        ]:
            with self.subTest(plain_mapping=url):
                self.assertEqual(source_key(url), key)
            if key == 'unicode-reports':
                self.run_case('review plain Unicode ' + url, report(url),
                              ['REV-909: quote in anchor but the card cites a no copy source: Detect renames.'])

    def test_review_notice_parser(self):
        self.run_case('review duplicate Licence', entry_change('google', 'Licence',
                      'MIT, https://opensource.org/license/mit\nLicence: CC BY 3.0, https://creativecommons.org/licenses/by/3.0/'),
                      ['google: duplicate field Licence'])
        for line in ['  continuation', 'stray text']:
            self.run_case('review unparsed ' + line, entry_change('google', 'Changes', 'paraphrased\n' + line),
                          ['google: unparsed line in entry'])

    def test_review_exact_notice_and_credit(self):
        self.run_case('review Otwellson', entry_change('laravel-docs', 'Notice',
                      'Copyright (c) Taylor Otwellson. Licence text: MIT'),
                      ["laravel-docs: Notice lacks 'Copyright (c) Taylor Otwell'"])
        tree = fixture()
        tree['cards']['REV-910'] = 'id: REV-910\nstatus: approved\nmode: all\nsource: https://github.com/backnotprop/pstack\n'
        tree['entries']['pstack'] = entry_text('pstack', ['REV-910'])
        tree['entries']['pstack']['Credit'] = 'Lauren Tan, https://github.com/backnotprop/pstack'
        self.run_case('review pstack-other', entry_change('pstack', 'Credit',
                      'Lauren Tan, https://github.com/backnotprop/pstack-other'),
                      ['pstack: Credit must start with Lauren Tan, https://github.com/backnotprop/pstack'], tree)
        for body in ['Copyright (c) Taylor Otwell. Licence text: MIT',
                     'Other item, Copyright (c) Taylor Otwell. Licence text: MIT']:
            self.run_case('review complete copyright ' + body, entry_change('laravel-docs', 'Notice', body), [])
        self.run_case('review credit suffix', entry_change('google', 'Credit',
                      'Google, https://google.github.io/eng-practices/; documentation'), [])
        self.run_case('review phrase prefix', entry_change('google', 'Changes', 'unparaphrased'),
                      ["google: Changes lacks 'paraphrased'"])
        self.run_case('review Notice phrase suffix', entry_change('google', 'Notice',
                      entry_text('google', ['REV-901'])['Notice'].replace('no warranty', 'no warrantyes')),
                      ["google: Notice lacks 'no warranty'"])

    def test_review_public_evidence_hosts(self):
        # Boundaries: DNS labels, IP versions, local suffixes and a public DNS name.
        for host in ['127.0.0.1', '.', '8.8.8.8', 'localhost', 'x..org', '-x.org', 'x_.org']:
            self.run_case('review evidence ' + host, entry_change('google', 'Evidence',
                          f'https://{host}/ read 2026-10-28 no revision shown'),
                          [f'google: url not plain: https://{host}/'])
        self.run_case('review evidence [::1]', entry_change('google', 'Evidence',
                      'https://[::1]/ read 2026-10-28 no revision shown'), ['google: url not plain: https://[::1'])
        for host in ['x.invalid', 'x.example', 'x.test', 'x.localhost', 'x.local', 'x.internal']:
            self.run_case('review evidence ' + host, entry_change('google', 'Evidence',
                          f'https://{host}/ read 2026-10-28 no revision shown'),
                          [f'google: Evidence url host not allowed: https://{host}/'])
        self.run_case('review public DNS evidence', entry_change('google', 'Evidence',
                      'https://google.github.io/ read 2026-10-28 no revision shown'), [])

    def test_review_complete_card_ids(self):
        tree = fixture()
        tree['cards']['REV-109'] = tree['cards'].pop('REV-901').replace('REV-901', 'REV-109')
        tree['entries']['google']['Cards'] = 'REV-109'
        self.run_case('review REV-109x', entry_change('google', 'Cards', 'REV-109x'),
                      ['google: Cards line differs from the cards that name it'], tree)
        for body in ['REV-901x', 'REV-901 junk', 'REV-901/']:
            self.run_case('review Cards ' + body, entry_change('google', 'Cards', body),
                          ['google: Cards line differs from the cards that name it'])
        self.run_case('review Cards whitespace', entry_change('git-docs', 'Cards', ' \tREV-902, '), [])

    def test_review_extra_url_inputs(self):
        cases = [
            ('uppercase dot escape', 'https://www.unicode.org/Public/%2E%2E/reports/tr35/', None, ['REV-904: url not plain: https://www.unicode.org/Public/%2E%2E/reports/tr35/']),
            ('double slash', 'https://laravel.com/docs//12.x/queries', 'laravel-docs', []),
            ('raw backslash', 'https://laravel.com/docs/\\../reports', None, ['REV-904: url not plain: https://laravel.com/docs/\\../reports']),
            ('uppercase slash escape', 'https://laravel.com/docs/%2F../reports', None, ['REV-904: url not plain: https://laravel.com/docs/%2F../reports']),
            ('query before path', 'https://laravel.com/?next=?/docs/12.x/queries', None, ['REV-904: url not plain: https://laravel.com/?next=?/docs/12.x/queries']),
        ]
        for name, url, key, expected in cases:
            self.run_case('review extra ' + name, card_change('REV-904', 'extra', url), expected)
            with self.subTest(mapping=name):
                self.assertEqual(source_key(url), key)

    def test_round3_fooling_inputs(self):
        cases = [
            ('zero width space', 'https://laravel.com/docs/\u200bx',
             ['REV-904: url not plain: https://laravel.com/docs/\u200bx']),
            ('closing bracket glued URL', 'https://laravel.com/docs/x]https://unknown.example/y',
             ['REV-904: no licence class for URL https://unknown.example/y']),
            ('tab separated URL', 'https://laravel.com/docs/x\thttps://other.example',
             ['REV-904: no licence class for URL https://other.example']),
            ('fragment before path', 'https://laravel.com#/docs/x',
             ['REV-904: no licence class for URL https://laravel.com#/docs/x']),
            ('bare scheme', 'https://', ['REV-904: url not plain: https://']),
        ]
        for name, body, expected in cases:
            self.run_case('round3 fooling ' + name, card_change('REV-904', 'extra', body), expected)


class RealTree(unittest.TestCase):
    def test_real_tree_is_clean(self):
        self.maxDiff = None
        self.assertEqual(check(), [])

    def test_real_exception_lists_have_no_stale_entries(self):
        self.assertEqual([problem for problem in check() if problem.startswith(('ALLOW ', 'LONG_OK '))], [])

    def test_approved_ids_match_card_gate(self):
        from tools import cards as gate
        approved, problems = read_cards(CARDS)
        self.assertEqual(problems, [])
        expected = {path.stem for path in CARDS.glob('REV-*.md')
                    if any(not gate.card_body(CARDS.parent, mode.stem, path.stem)[1]
                           for mode in (CARDS.parent / 'modes').glob('*.md'))}
        actual = {cid for cid, fields in approved}
        self.assertTrue(actual)
        self.assertEqual(actual, expected)
        paths = list(CARDS.glob('REV-*.md'))
        self.assertEqual(len(actual), sum('status: approved' in p.read_text(encoding='utf-8').splitlines() for p in paths))

    def test_draft_copy_is_ignored(self):
        self.assertEqual(check(), [])
        approved, problems = read_cards(CARDS)
        self.assertEqual(problems, [])
        with tempfile.TemporaryDirectory(prefix='reviewer-draft-') as folder:
            copy = Path(folder) / 'cards'
            shutil.copytree(CARDS, copy)
            (copy / 'REV-999.md').write_text('id: REV-999\nrule: Draft only.\nstatus: draft\nmode: all\nsource: https://unknown.example/x\n', encoding='utf-8', newline='\n')
            self.assertEqual(check(copy, NOTICES, ALLOW, LONG_OK), [])
            copied, problems = read_cards(copy)
            self.assertEqual(problems, [])
            self.assertEqual({cid for cid, _ in copied}, {cid for cid, _ in approved})
            self.assertEqual(len(copied), len(approved))

    def test_reference_hashes_are_pinned(self):
        self.assertEqual(reference_problems(), [])
        for label, (filename, digest) in REFERENCES.items():
            with self.subTest(label=label):
                raw = (REFS / filename).read_bytes().replace(b'\r\n', b'\n')
                self.assertEqual(hashlib.sha256(raw).hexdigest(), digest)

    def test_registry_is_complete(self):
        self.assertEqual(len(REG), 37)
        self.assertEqual(len(ROW), len(REG))
        for source in REG:
            with self.subTest(key=source.key):
                self.assertTrue(source.holder)
                self.assertTrue(source.label)
                self.assertTrue(source.link or source.label in ('___', 'copyright waived by the author'))

    def test_every_source_url_maps_to_its_row(self):
        samples = [
            ('google', GOOGLE), ('github-docs', GH), ('laravel-docs', 'https://laravel.com/docs'),
            ('laravel-framework', 'https://github.com/laravel/framework/blob/main/LICENSE.md'),
            ('owasp-cs', 'https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html'),
            ('owasp-api', 'https://owasp.org/API-Security/editions/2023/'), ('owasp-top10', 'https://owasp.org/Top10/2021/'),
            ('owasp-community', 'https://owasp.org/www-community/attacks/CSV_Injection'), ('owasp-genai', 'https://genai.owasp.org/llmrisk/'),
            ('phpunit', 'https://docs.phpunit.de/en/12.5/'), ('php-manual', 'https://www.php.net/manual/en/'),
            ('composer', 'https://getcomposer.org/doc/'), ('git-docs', GIT), ('linux', 'https://www.kernel.org/doc/html/latest/'),
            ('pstack', 'https://github.com/backnotprop/pstack/blob/f51fdeb/README.md'), ('jscpd', 'https://github.com/kucherenko/jscpd'),
            ('larastan', 'https://github.com/larastan/larastan'), ('phpstan-src', 'https://github.com/phpstan/phpstan-src'),
            ('phpstan-docs', 'https://phpstan.org/user-guide/rule-levels'), ('phpmd', 'https://phpmd.org/'), ('infection', 'https://infection.github.io/'),
            ('translator', 'https://github.com/ElegantEngineeringTech/laravel-translator'), ('lang-monitor', 'https://github.com/jonasschen/laravel-lang-monitor'),
            ('mattpocock', 'https://github.com/mattpocock/skills'), ('aposd', 'https://github.com/johnousterhout/aposd-vs-clean-code'),
            ('aihero', 'https://www.aihero.dev/'), ('fowler', 'https://martinfowler.com/'), ('refactoring-com', 'https://refactoring.com/'),
            ('cleancoder', 'https://blog.cleancoder.com/'), ('unicode-data', 'https://www.unicode.org/Public/18.0.0/'),
            ('unicode-charts', 'https://www.unicode.org/cldr/charts/'), ('unicode-reports', 'https://unicode.org/reports/tr35/'),
            ('ewd249', 'https://www.cs.utexas.edu/~EWD/transcriptions/'), ('per', 'https://www.php-fig.org/per/coding-style/'),
            ('cognitect', COGNITECT), ('gnu-coreutils', 'https://www.gnu.org/software/coreutils/manual/'), ('i18next', 'https://www.i18next.com/principles/namespaces'),
        ]
        self.assertCountEqual([key for key, _ in samples], ROW)
        for key, url in samples:
            with self.subTest(case='url mapping ' + key):
                self.assertEqual(source_key(url), key)


if __name__ == '__main__':
    unittest.main()
