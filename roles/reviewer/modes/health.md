# Reviewer mode: health

Ask one thing: will this change hurt to change later? Health has 10 checks
here (H1 to H10). Each check has a tool part and a reading part. A tool hit
alone is never a finding. This mode runs no size, business or security check.

Not written here yet, each in its own later step:

- The 8 translation checks and the user visible text pointer: ticket 38.
- `clean-code-guard`, `test-guard`, `docs-guard`, `debate-review`: ticket 37.

Their steps are marked below. Until they exist, say each one is
`not checked: <name> not built yet`. Health is then `incomplete`, never `pass`.

## The 4 result words

Every tool part and every reading part ends in exactly 1 of these:

- `finding`: confirmed by reading the code.
- `clean`: looked, nothing there.
- `not checked: <reason>`: the tool did not run, or could not tell.
- `does not apply: <reason>`: the check has nothing to look at.

A check with no tool part writes `does not apply: no tool` for its tool part.
A check record entry (`runs/check-record.json`) has `id`, `mode` health,
`tool_result`, `reading_result`, `word`, `reason`. The word is `must fix`,
`finding`, `lead` or `none`.

## How the tools run

Tools run only in a throwaway container, never on the host, with the network
off: `docker run --rm --network none --name <unique name> actas-reviewer:2026-10-26 ...`.
Mount a copy of the PR head, not the checkout. If the container cannot start,
every tool part is `not checked: tool did not run, <the failed call>`. Never
start Docker Desktop yourself. Name the image `actas-reviewer:2026-10-26` in
the packet.

Save each tool's raw output and exit code in `runs/`, then classify it with
`python tools/health_parse.py <tool> ...`. Do not classify by eye. The exit
code alone says nothing:

- PHPStan exits 1 for findings and for boot errors alike. The script reads the text.
- An empty jscpd scan exits 0 and looks clean. The script reads the scanned
  file count. 0 files is `not checked`, never `clean`.
- A PR's own `.jscpd.json` is read by jscpd on its own. Always pass the
  role's own settings with `--config`, and still read the file count.
- PHPMD gives exit 0 with no output on a folder with 0 PHP files. Count the
  files you pass.

## Steps

Before each step, run `cards.py reviewer health <step number>`, for example
`cards.py reviewer health 1`. The step number is the digit, never the step name.

1. **Freeze and set up.** Run the Laravel check from ROLE.md first. Write
   down the full PR head, the base branch head and the comparison base
   (`REV-P10`). One base serves every comparison. Make the packet folder
   outside the checkout (ROLE.md section 5) and save the start snapshot to
   `runs/snapshot-start.txt`. The checkout is never changed. If the PR head
   is not in the checkout, fetch it read only. Write the list of changed
   files from the comparison base. Note the Laravel line: the tools in the
   image hold Laravel 11.54.0. If PHPStan with Larastan fails to boot on this
   project, H9 is `not checked`, not a pass.
2. **Read whole files (G5).** Read every touched file whole, not only the
   changed lines, for questions 11, 16 and 18. Report only what the PR added,
   or what it left behind in an area it touched. A problem in an untouched
   part of the same file is not reported. The tool calls must show the whole
   file was read. For each finding write one of: "PR added it", "PR left it
   in a touched area". If neither is true, drop it.
3. **H1 Copied logic.** Tool: jscpd with `--baseline-from-ref <comparison
   base>` and `--fail-on-new-clones=0`, the role's own settings, format php,
   report json with `-r json`. Classify with `health_parse.py jscpd`. Reading:
   short copies jscpd cannot see, such as the same 2 line "card is active"
   check typed in 3 controllers and again in an export (question 18). The
   clone count is a floor.
4. **H2 Long methods and files.** Tool: PHPMD `ExcessiveMethodLength` and
   `ExcessiveClassLength` (1 class, not a whole file) on the changed PHP
   files, and the line count of each changed file. Thresholds: `___` (Ahmed's
   call, the spec does not give them). Until they are set, the PHPMD part is
   `not checked: thresholds not set`. Every number from this step is a
   pointer (see "Pointers"). Reading: questions 6 and 17.
5. **H3 One class, many jobs.** Tool: `health_search.py routes` counts the
   route lines per touched controller. The count is a pointer and never a
   finding. The count that makes a pointer: `___` (Ahmed's call). Until it is
   set, report the count and write `pointer threshold not set`. The pointer
   sends you to questions 11 and 13 (until the question 12 card can load; then
   12 and 13). A `Route::resource` line counts as 1 line but is many routes;
   say so. Reading: questions 11, 12 and 13.
6. **H4 Logic or queries in controllers.** Tool: search the changed controllers
   for query calls (`DB::`, `::where(`, `->where(`, `::query(`, `->get(`,
   `->join(`). Each hit is only a candidate. Open it and read whether the
   query or business rule belongs there. A hit you did not read is not a
   finding.
7. **H5 N+1.** No tool. Reading: a lazy loaded relation read inside a loop
   over many rows. Always a `lead`, never `finding` and never `must fix`.
8. **H6 Risky areas with no tests.** Risky means money, logins, deleting data,
   plus the risky areas from the business step. In a health only run there is
   no business step: use money, logins and deleting data only, and write
   "risky areas: business step not run (O13)" in the record. Find tests by what
   they exercise, not by a class name search alone. Read changes to the test
   config, skips, excluded groups, the CI workflow files and the Composer test
   scripts. A name or route hit is a candidate: trace the call and read the
   assertion before you write "covered". When nothing covers a risky area, this
   check is its own finding: "no test found by name, route or caller".
9. **H7 Old tests edited or deleted.** Tool: `git diff -M --name-status
   <comparison base> <head>`. Judge each deleted or changed test by lost
   protection: does it still fail when the code breaks? A reason in the PR text
   does not count. A lost protection, confirmed in the code, is `must fix`.
10. **H8 Dead code.** Tool: PHPMD `UnusedPrivateMethod` and
    `UnusedLocalVariable`, and PHPStan at level 4 (unused private methods,
    unreachable code, dead branches; not unused public or protected methods).
    Reading: `clean-code-guard` imperative 21 (ticket 37; until then, read for
    code nobody calls).
11. **H9 Bugs.** Tool: PHPStan with Larastan at level 5, classified by
    `health_parse.py phpstan`. A line saying an ignored pattern "was not
    matched" is a stale baseline entry, not a bug; report the count. Reading:
    open every error and confirm it. A bug the PR adds, once confirmed, is
    `must fix` whichever tool found it. A bug already there is a `lead`.
12. **H10 Cost to add.** No tool. Propose 1 realistic small feature in the
    area the PR touches, in 1 line (from the rules page when there is one;
    the user may name another). Write the list of files that must change on
    the PR head: counted, 1 line why each, copies marked as copies, and tests,
    migrations, views, translations, config and docs counted. It is an
    estimate: state the feature and the assumptions and mark uncertain files.
    When the area existed before, count the same feature on the base and on
    the head. Next to it, ask question 11 for the riskiest rule the PR touches.
13. **Laravel reading prompts.** Read, for the changed files that fit:
    migrations (existing rows, order, rollback, a column change that drops its
    modifiers); config and env (`env()` outside config files breaks under
    config caching); queues, jobs and events (retries, old payloads, a job
    that starts before the transaction commits); Blade views and the code that
    calls them; changed JavaScript that carries the same behaviour as PHP.
    Also three named steps: L2 (a case the code misses), L3 (behaviour that
    worked before and now does not), L4 (a rule copied in 2 places that drifts
    apart). A refactor PR needs a record of old behaviour: tests that pass
    unchanged on base and head, or the output of base and head on 1 case at
    least (question 31). Each prompt ends in a result word.
14. **Fixed lists and limits typed in 2 or more places (G1, G2).** This links
    to questions 11 and 18. Search step (G2): for each fixed list, each single
    limit (a size, a count), and each helper like logic in a changed hunk, run
    `python tools/health_search.py copies --repo <copy of head> --literal <text> --base <comparison base> --head <PR head>`.
    It also finds the config key or language key that holds the same text.
    Name every other copy as `path:line`. Then read: a copy counts only when
    both copies express the same rule (same knowledge, not just the same
    text). Two equal lists that mean different things count as neither.
    Result: a `finding` when the PR adds a new copy; a pointer when the copy
    was already there and the PR only touched its file. It is `must fix` only
    with a shown burden (the PR made the 2nd copy) and a small fix named in
    1 line (for example "move the list to `config/uploads.php`"). No copy: `clean`.
15. **H11 and the independent check (tests that prove nothing).** Reading
    picks the tests; the tool breaks the code. Pick at most 3 tests that
    assert money, login or deleting data in changed code. Find them by what
    they call, not by a name search alone. None found: write `H11: does not
    apply: no test in a risky area`. This never hides check H6 (risky area with
    no test). Write the picks and the code line to break in a spec file, then
    run `python tools/check11_run.py --repo <checkout> --spec <spec.json> --out <packet folder>/independent-check --image actas-reviewer:2026-10-26 --record runs/check-record.json --reading-result <word>`.
    The tool works only in a throwaway copy, with the network off. It never
    writes to the checkout (`REV-P01`, `REV-P03`); if the checkout changes, it
    stops. Per test, it does these in order: a green run first; proof that the
    test ran (at least 1 test and 1 assertion); the fault; the same test run
    unchanged; the red must be an assertion failure, and its message is kept;
    the copy is reset and compared with the checkout; the test runs green
    again. The fault must contradict what the test asserts. Never a syntax
    error. The spec holds a probe command that shows the asserted behaviour
    before and after the fault. How to read the result per test:
    - Green with the fault, and the probe shows the behaviour changed: the test
      proves nothing. This is a `must fix` finding. Name the test and link
      `independent-check.json` in Known risks.
    - Green with the fault, and the probe shows no change: the fault was
      harmless. Write `not checked: fault did not contradict the assertion`.
      Pick a better fault or leave it. This never condemns the test.
    - Red, but not from an assertion (a fatal error, a parse error): write
      `not checked: red was not an assertion failure`.
    - The tests cannot run here (no runner, no vendor folder, no network to
      fetch it): write `not checked: tests cannot run here`. Do not install
      anything to make them run.
    - Red on the assertion, reset, green again: `clean` for that test.
    The 2 `not checked` results make health `incomplete`. The result covers only
    the tests picked: say "covers N picked tests" and never "the tests are good".
    The command, the fault and the result stay in `independent-check.json`,
    apart from the CI evidence; Known risks names that file.
16. **Translation checks.** Not written here. Ticket 38 fills this step. Until
    it does, write `T1 to T8: not checked: translation checks not built yet`.
17. **Pointers.** Every number from a tool or a guard is a pointer, including
    the 20 lines and complexity 10 of `clean-code-guard`. Each pointer gets 1
    line of judgement and a review question number. Example: "72 line method:
    fine, a plain list of menu entries" or "55 line method: problem, it does
    3 jobs (question 17)". A guard finding that is not a number stays a
    finding. A pointer never passes or fails health. The pointer map:
    a long new method, question 6; a small change inside a method that is
    already long, question 17; a long class, questions 12 and 11 (11 and 13
    until the question 12 card loads); many routes on 1 controller, questions
    11 and 13 until the question 12 card loads, then 12 and 13; a copy,
    question 18.
18. **The review questions.** Ask these 16 on every run, and answer each with
    1 line and a file:line, or "nothing to say":
    1. Is there a layer, interface, flag or setting no caller needs?
    2. Could less code give the same result?
    3. Does a helper or wrapper hide anything? If you removed it, would the
       mess move to the callers?
    4. Does it solve today's problem, or a future one?
    7. Can a reader tell what it does? Are the names exact?
    8. Is the code obvious? If you cannot follow it, others will not.
    10. Is there hidden state, a call order, or a hidden dependency?
    11. If a rule changes, how many places change?
    13. Are business rules kept apart from the web, the database and the framework?
    15. Can a unit test run without loading most of the system?
    16. Did the PR clean up the code it touched, or bolt onto it?
    17. Did a long function gain a second job?
    18. Is this a second copy of logic that already exists?
    20. Is this a quick fix or a design step that keeps the code healthy?
    22. Does it follow the style of the code around it?
    23. Would the tests fail if the code broke?

    Ask these 4 only when a pointer points there: 5 (heavy special cases), 6
    (methods so small the reader jumps around), 9 (comments say why, not
    what), 21 (a refactor mixed into a feature PR). Ask question 31 (a refactor
    needs a record of old behaviour and proof) when the PR is a refactor or
    cleanup. Ask question 32 (docs updated when behaviour or setup changed)
    when the `docs-guard` trigger fires; whether it also fires for new
    behaviour no doc mentions yet: `___`. Question 12 (one actor per class)
    joins only when its card loads from `cards.py`; if it does not load, do not
    ask it. Questions 14 and 19 are not asked in v1 (open). Questions 24 to 29
    belong to size and the packet; question 30 belongs to security. A design
    opinion with no shown harm is a pointer, never a finding.
19. **Cost to add and verdict.** Write `runs/check-record.json` with an entry
    for H1 to H10 (and for H11 and T1 to T8 as `not checked` until their
    tickets exist). Run `python tools/health_verdict.py --record runs/check-record.json`.
    The rules it applies:
    - `fail` only on a `must fix` finding confirmed in the code (`REV-P11`): a
      deleted or changed test that lost protection; a test that stays green
      in the independent check; a business rule copied in 2 places that
      already disagree; `test-guard` rules 1, 2 or 8; a `clean-code-guard`
      critical finding; a bug the PR introduces, confirmed (translation
      checks 1 to 4 are never must fix).
    - A design regression is `must fix` only with a shown burden (the PR
      created the 2nd copy of a rule or payload, or cost to add rose from base
      to head) and a named small fix.
    - Pointers and leads never fail health.
    - `incomplete` when any part is `not checked`. Add "merge only after: <x>".
    - `pass` only when every part is `clean` or `does not apply` and nothing
      is `must fix`.
20. **Write the packet and finish.** Write `packet.md` and the 3 other saved
    inputs in the packet folder (packet format as in `size.md` step 5). The
    health line is the verdict word plus a reason. In a health only run, the
    identity says `mode=health`, the size, business and security lines each say
    `not asked: health run only`, and the money line says `not checked: money
    not looked at, health run only`. Put must fix findings first in Known
    risks, then the rest, then leads. Put pointers in Pointers, each with its
    judgement line and its question. Draft the message to the author in Drafts,
    not sent; never send it. Run `python tools/packet_check.py <packet folder>`
    after the last write and show the packet only after `packet_check: pass`
    (`REV-P08`). Save the end snapshot and compare it with the start one.

## Finish checklist

- [ ] Laravel check result quoted; head, base and comparison base in full.
- [ ] Every touched file read whole (the tool calls show it).
- [ ] Every check H1 to H10 has a tool result and a reading result, each one of the 4 words.
- [ ] Every tool classified by `health_parse.py`; jscpd file count quoted.
- [ ] Route counts and copy searches quoted with `path:line`.
- [ ] Every pointer has a judgement line and a question number.
- [ ] The 16 questions answered; the extra ones only where a pointer points.
- [ ] Marked places for H11, the translation checks and the guard skills left as `not checked`.
- [ ] `health_verdict.py` output quoted and the health line matches it.
- [ ] Packet check output quoted (`packet_check: pass`).
- [ ] Start and end snapshot compared, result quoted.
- [ ] Every `cards.py` command with its first output line.
- [ ] Nothing implied as "safe to merge".
