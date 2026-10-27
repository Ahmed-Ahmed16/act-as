# Reviewer mode: health

Ask one thing: will this change hurt to change later? Health has 10 checks
here (H1 to H10). Each check has a tool part and a reading part. A tool hit
alone is never a finding. This mode runs no size, business or security check.

Built, each in its own step:

- The 8 translation checks and the user visible text pointer are built: `tools/translation_health.py` and `tools/translation_health_scan.py`, step 16.
- `clean-code-guard`, `test-guard`, `docs-guard`, `debate-review`: see the block "Guard skills and debate-review (ticket 37)" below.

Their steps are marked below. When one cannot run, write
`not checked: <reason>`. Health is then `incomplete`, never `pass`.

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
   Whole file reading cards: `REV-447`, `REV-448`.
3. **H1 Copied logic.** Tool: jscpd with `--baseline-from-ref <comparison
   base>` and `--fail-on-new-clones=0`, the role's own settings, format php,
   report json with `-r json`. Classify with `health_parse.py jscpd`. Reading:
   short copies jscpd cannot see, such as the same 2 line "card is active"
   check typed in 3 controllers and again in an export (question 18). The
   clone count is a floor.
   Copied logic cards: `REV-401` to `REV-403`.
4. **H2 Long methods and files.** Tool: PHPMD `ExcessiveMethodLength` and
   `ExcessiveClassLength` (1 class, not a whole file) on the changed PHP
   files, and the line count of each changed file. PHPMD runs with its own
   default limits (method 100 lines, class 1000 lines in PHPMD 3.0.0,
   `rulesets/codesize.xml`; read in the image 2026-10-27). Do not pass other
   limits. Every number from this step is a pointer (see "Pointers").
   Reading: questions 6 and 17.
   Long method and class cards: `REV-404`, `REV-405`.
5. **H3 One class, many jobs.** Tool: `health_search.py routes` counts the
   route lines per touched controller. The count is a pointer and never a
   finding. 10 or more route lines on 1 controller make a pointer (the script
   sets `pointer`); 9 or fewer do not. The pointer
   sends you to questions 11 and 13 (until the question 12 card can load; then
   12 and 13). A `Route::resource` line counts as 1 line but is many routes;
   say so. Reading: questions 11, 12 and 13.
   Route count card: `REV-407`.
6. **H4 Logic or queries in controllers.** Tool: search the changed controllers
   for query calls (`DB::`, `::where(`, `->where(`, `::query(`, `->get(`,
   `->join(`). Each hit is only a candidate. Open it and read whether the
   query or business rule belongs there. A hit you did not read is not a
   finding.
   Controller query card: `REV-408`.
7. **H5 N+1.** No tool. Reading: a lazy loaded relation read inside a loop
   over many rows. Always a `lead`, never `finding` and never `must fix`.
   Lazy relation card: `REV-409`.
8. **H6 Risky areas with no tests.** Risky means money, logins, deleting data,
   plus the risky areas from the business step. In a health only run there is
   no business step: use money, logins and deleting data only, and write
   "risky areas: business step not run (O13)" in the record. Find tests by what
   they exercise, not by a class name search alone. Read changes to the test
   config, skips, excluded groups, the CI workflow files and the Composer test
   scripts. A name or route hit is a candidate: trace the call and read the
   assertion before you write "covered". When nothing covers a risky area, this
   check is its own finding: "no test found by name, route or caller".

   **Risky areas in a health only run (O13, used by H6 and the independent check).**
   With no business step, read the changed files for the 3 fixed kinds only:
   money, logins, deleting data. Run `python tools/risky_areas.py --repo
   <checkout> --files <changed files>`. Each area it lists is a candidate:
   open the file and read whether the line really touches that kind. Drop a
   hit you read and rejected, and say so. These areas feed H6 (find tests for
   each) and the picks in step 15. A plain change gives none: write "risky
   areas: none found in the changed files". Not checked always holds
   "business risky areas: not asked: health run only". Never write the tool's
   list as a finding by itself.
   Risky area test cards: `REV-410` to `REV-412`.
9. **H7 Old tests edited or deleted.** Tool: `git diff -M --name-status
   <comparison base> <head>`. Judge each deleted or changed test by lost
   protection: does it still fail when the code breaks? A reason in the PR text
   does not count. A lost protection, confirmed in the code, is `must fix`.
   Changed test cards: `REV-413`, `REV-414`.
10. **H8 Dead code.** Tool: PHPMD `UnusedPrivateMethod` and
    `UnusedLocalVariable`, and PHPStan at level 4 (unused private methods,
    unreachable code, dead branches; not unused public or protected methods).
    Reading: `clean-code-guard` imperative 21 (ticket 37; until then, read for
    code nobody calls).
    Dead code cards: `REV-415` to `REV-417`.
11. **H9 Bugs.** Tool: PHPStan with Larastan at level 5, classified by
    `health_parse.py phpstan`. A line saying an ignored pattern "was not
    matched" is a stale baseline entry, not a bug; report the count. A run
    whose only issues are stale baseline entries is `clean`, with that count.
    Reading:
    open every error and confirm it. A bug the PR adds, once confirmed, is
    `must fix` whichever tool found it. A bug already there is a `lead`.
    Bug reading cards: `REV-418` to `REV-421`.
12. **H10 Cost to add.** No tool. Propose 1 realistic small feature in the
    area the PR touches, in 1 line (from the rules page when there is one;
    the user may name another). Write the list of files that must change on
    the PR head: counted, 1 line why each, copies marked as copies, and tests,
    migrations, views, translations, config and docs counted. It is an
    estimate: state the feature and the assumptions and mark uncertain files.
    When the area existed before, count the same feature on the base and on
    the head. Next to it, ask question 11 for the riskiest rule the PR touches.
    Cost and design burden cards: `REV-422` to `REV-424`.
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
    Laravel reading cards: `REV-431` to `REV-441`.
    Edge case, old behaviour and copied rule cards: `REV-442` to `REV-444`.
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
    Fixed list and copy search cards: `REV-445`, `REV-446`.
15. **H11 and the independent check (tests that prove nothing).** Reading
    picks the tests; the tool breaks the code. Pick at most 3 tests that
    assert money, login or deleting data in changed code. Find them by what
    they call, not by a name search alone. None found: write `H11: does not
    apply: no test in a risky area`. This never hides check H6 (risky area with
    no test). Write the picks and the code line to break in a spec file, then
    run `python tools/check11_run.py --repo <checkout> --head <head commit> --spec <spec.json> --out <packet folder>/independent-check --image actas-reviewer:2026-10-26 --record runs/check-record.json --reading-result <word>`.
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
    Independent test check cards: `REV-425` to `REV-430`.
16. **Translation checks (T1 to T8, G4).** Run
    `python tools/translation_health.py --repo <copy of head> --lang <head lang folder: lang or resources/lang> --base-lang <lang folder at the comparison base> --changed-files <files.json>`
    and save its output in `runs/`. It reads files only. No changed language
    file: write "no translation files changed" and stop. Every item below
    is a finding or a pointer. None is ever `must fix`, and none fails health,
    even when a missing key is confirmed in the code.
    Findings (open the code and confirm each before you write it):
    - T1 key in one language, not another: `check1`. A gap the PR did not
      touch is still a finding; show `touched_by_pr` as data. An unreadable
      file is `not checked: <file> unreadable`, never clean.
    - T2 key used in code but missing from a language: `check2`. Also run
      `php artisan translator:missing` in the container (network off). Never
      run `translator:translate` or `translator:proofread`: they call an AI
      service. The tool is proved offline for PHP group files only; for JSON
      keys the script alone answers. If the 2 disagree, read the code.
    - T3 named placeholder missing in one language: `check3` (`:count` skipped).
    - T4 wrong number of plural forms, only for `trans_choice` keys: `check4`
      gives the count per language. Compare it with the translation card on
      Unicode CLDR plural rules. The script never judges a count. No card
      loaded: `not checked: no plural card`.
    Pointers (never a fail):
    - T5 changed old values: `check5`. List them first in "Translations by
      page", on their own, before any group.
    - T6 keys with no use found: `check6`, split into "passed through a
      variable" and "no trace". Also run `php artisan translator:dead` the same
      way. A call site in `dynamic_call_sites` is `not checked`.
    - T7 raw output `{!! __() !!}`: `check7`. Read each one; `args_escaped:
      false` means an inserted value is not escaped. Say which value.
    - T8 value with no letters of its language: `check8`. A locale in
      `locales_not_checked_for_letters` is `not checked`, never a pass.
    - G4 user visible text typed as a literal: `g4_literal_text`. Open each
      `path:line` and read it. Text in logs, comments and tests does not count.
    Packet: put "Translations by page" in Behaviour changed (changed old
    values first, then `by_page`: each page, then "shared", then "no use
    found"). Findings go to Known risks, pointers to Pointers. A key passed
    through a variable is "not checked". Check record ids: T1 to T8, G4.
    Translation check cards: `REV-601` to `REV-608`.
    English key fact cards: `REV-609` to `REV-611`.
    Layout and helper cards: `REV-612`, `REV-613`.
17. **Pointers.** Every number from a tool or a guard is a pointer, including
    the 20 lines and complexity 10 of `clean-code-guard`. Each pointer gets 1
    line of judgement and a review question number. Example: "72 line method:
    fine, a plain list of menu entries" or "55 line method: problem, it does
    3 jobs (question 17)". A guard finding that is not a number stays a
    finding. A pointer never passes or fails health. The pointer map:
    a long new method, question 6; a small change inside a method that is
    already long, question 17; a long class, questions 12 and 11 (11 alone
    until the question 12 card loads); many routes on 1 controller, questions
    11 and 13 until the question 12 card loads, then 12 and 13; a copy,
    question 18.
    Pointer judgement cards: `REV-449`, `REV-450`.
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

    Ask question 5 when the diff has heavy special cases, question 9 when
    comments say what instead of why, and question 21 when a refactor is
    mixed into a feature PR. Ask question 6 (methods so small the reader
    jumps around) only when a pointer points there. Ask question 31 (a refactor
    needs a record of old behaviour and proof) when the PR is a refactor or
    cleanup. Ask question 32 (docs updated when behaviour or setup changed)
    when the `docs-guard` trigger fires, and also when the PR adds behaviour
    that no document mentions. Question 12 (one actor per class)
    joins only when its card loads from `cards.py`; if it does not load, do not
    ask it. Questions 14 and 19 are not asked in v1 (open). Questions 24 to 29
    belong to size and the packet; question 30 belongs to security. A design
    opinion with no shown harm is a pointer, never a finding.
    Default question cards: `REV-501` to `REV-504`, `REV-507`, `REV-508`,
    `REV-510`, `REV-511`, `REV-513` to `REV-518`, `REV-520`, `REV-521`.
    Conditional question cards: `REV-505`, `REV-506`, `REV-509`, `REV-512`,
    `REV-519`, `REV-522`, `REV-523`.
19. **Cost to add and verdict.** Write `runs/check-record.json` with an entry
    for H1 to H11 and T1 to T8, using their tool and reading results.
    Run `python tools/health_verdict.py --record runs/check-record.json`.
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

## Guard skills and debate-review (ticket 37)

The helper is `python tools/guard_run.py`. It decides; you read the result.

1. Skills. `guard_run.py skills clean-code-guard test-guard docs-guard debate-review`.
   A missing one gives `not checked: <skill> not installed`. Work without it,
   and health is `incomplete`.
2. Which files. `guard_run.py targets <changed files>` sorts them. Changed PHP
   outside tests goes to `clean-code-guard`, and Blade files count as PHP here
   (G6). A PR that changes only Blade files still gets the code guard. Changed
   tests go to `test-guard`. Changed docs go to `docs-guard`. All 3 guards are
   report only: they never edit, fix or post. A `must fix` from a guard is only
   as sure as your own reading of the code.

   Read each guard's `SKILL.md` and follow its review steps:

   - Run `clean-code-guard` on its code files in report only mode. Save its
     output to `runs/clean-code-guard.txt`.
   - Run `test-guard` on its test files in report only mode. Save its output
     to `runs/test-guard.txt`.
   - Run `docs-guard` on its docs files in report only mode. Save its output
     to `runs/docs-guard.txt`.

   If a guard cannot run, write `not checked: <guard> <reason>` in the check
   record. Name the guard and say why it could not run.
3. `debate-review`. Full run only, never in a health only or size only run.
   Run `guard_run.py debate --pr <url> --author <PR author login> --out-dir <packet folder>/debate`.
   It always passes `--dry-run`. Never run `debate-review` by hand, and never
   use `--post-draft`, `--force` or any posting flag. It keeps no worktree: if
   one is left behind, the line says so.
4. The team rule. The PR author login must be on the team login list. The list
   is private: its path comes from the environment variable `ACT_AS_TEAM_LIST`
   (set in the private harness config), never from a public file. Never copy a
   login from it into the packet. Results: a listed login runs the debate; an
   unlisted login gives `not checked: debate-review skipped, PR from outside the
   team`; a missing or empty list gives `not checked: team list missing`. Neither
   is ever treated as inside the team.
5. Every `not checked` line from this block goes into the check record and makes
   health `incomplete`. A debate finding is a pointer until you confirm it in the code.

## Finish checklist

- [ ] Laravel check result quoted; head, base and comparison base in full.
- [ ] Every touched file read whole (the tool calls show it).
- [ ] Every check H1 to H10 has a tool result and a reading result, each one of the 4 words.
- [ ] Every tool classified by `health_parse.py`; jscpd file count quoted.
- [ ] Route counts and copy searches quoted with `path:line`.
- [ ] Every pointer has a judgement line and a question number.
- [ ] The 16 questions answered; questions 5, 9 and 21 where the diff shows the thing; the other extra ones only where a pointer points.
- [ ] H11, the translation checks and the guard skills each have a result; one that could not run says `not checked: <reason>`.
- [ ] `health_verdict.py` output quoted and the health line matches it.
- [ ] Packet check output quoted (`packet_check: pass`).
- [ ] Start and end snapshot compared, result quoted.
- [ ] Every `cards.py` command with its first output line.
- [ ] Nothing implied as "safe to merge".
