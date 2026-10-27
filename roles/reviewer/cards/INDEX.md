# Reviewer cards

Open a card only when its mode and trigger match the step in front of you. Use
only `approved` cards. Policy cards (`REV-P`) always apply.

| id | mode | trigger | status | rule in short |
| --- | --- | --- | --- | --- |
| REV-P01 | all | Before touching checkout files or external systems | approved | Keep the checkout, running site and tracker read only. Write only the packet in a... |
| REV-P02 | all | Before a reviewer action is sent or committed | approved | Get the user's yes for the exact action before posting, commenting, reviewing,... |
| REV-P03 | all | When the reviewer is asked to fix code | approved | Never change code. If asked to fix something, name the developer role and direct... |
| REV-P04 | all | When the changed line count exceeds 300 | approved | Count the changed lines. If the count exceeds 300, stop with a short packet... |
| REV-P05 | all | When something was not checked | approved | Mark anything not inspected or not run as "not checked" and give the reason... |
| REV-P06 | all | When drafting the packet conclusion | approved | Do not write "safe to merge" in the packet. Do not add an overall line. |
| REV-P07 | all | When changed code handles money | approved | Flag money code for a separate Opus review. Do not perform that review, claim it... |
| REV-P08 | all | Before a packet is shown | approved | Show the packet only after the packet check passes. |
| REV-P09 | all | Before a reviewer mode starts | approved | For version 1, proceed only when composer.json is a valid JSON object and lists... |
| REV-P10 | all | Before the first comparison | approved | Record one comparison base at the start of the review. Use that same base for... |
| REV-P11 | all | When deciding whether a finding is must fix | approved | Mark a finding must fix only when code confirms the whole path to the harm. |

## Size and comparison base cards

Approved by Ahmed on 2026-10-27. Cards with a check id are mapped in the
check map below; the others are rules of the size step.

| id | mode | trigger | status | check id | rule in short |
| --- | --- | --- | --- | --- | --- |
| REV-101 | size, full | When counting changed lines | approved | none | Count added plus deleted lines per file, read from git. |
| REV-102 | size, full | When a changed file is binary | approved | none | A binary file counts 0; read git's dashes as 0. |
| REV-103 | size, full | When a changed file was renamed | approved | none | A renamed or moved file counts like GitHub counts it: a pure move 0, a move with edits only its changed lines. |
| REV-104 | size, full | When sorting changed files for the count | approved | none | Tests, lock files, generated files and docs are left out; the rest counts. |
| REV-105 | size, full | When a changed file is deleted | approved | none | Lines in a deleted file stay counted. |
| REV-106 | size, full | When a changed file sits under public/ | approved | none | A public/ file is generated only if its blob id equals a source file's. |
| REV-107 | size, full | When a git call in the counter fails | approved | none | A failed git call gives "not checked", never a number. |
| REV-108 | size, full | When writing the size line | approved | none | The size line shows verdict, counted lines, cap and what was left out by kind. |
| REV-109 | size, full | When a PR is over the 300 line cap | approved | Q26 | An over the cap PR goes back with a request to split it. |
| REV-110 | size, full | When choosing the reading order of a PR | approved | Q25 | Tests may be read first; no fixed order. |
| REV-111 | size, full | When reading the list of changed files | approved | Q27 | Name a file unrelated to the stated task as a lead; it only sets the reading order. |
| REV-112 | size, full | When proposing or judging a split into parts | approved | Q28 | Each part of a split builds and passes its own tests. |
| REV-113 | size, full | When reading the PR description | approved | Q29 | Check the description says what was checked, skipped, and the risks. |
| REV-114 | all | When freezing the comparison base of an open PR | approved | none | Base is the merge base of the PR head and the base branch head. |
| REV-115 | all | When choosing what to compare the PR head with | approved | none | Never compare with the moving base tip or a local or fresh default branch. |
| REV-116 | all | When the PR is a stacked part | approved | none | If the base branch head is an ancestor of the PR head, it is the base. |
| REV-117 | all | When the PR is already merged | approved | none | Use GitHub's recorded base with a three dot diff; if not proved, "not checked", no count. |
| REV-118 | all | When freezing the PR head at the start | approved | none | Freeze the PR head as a full commit id once. |
| REV-119 | all | When a step needs the default branch | approved | none | Read the default branch name from GitHub at the start. |
| REV-120 | all | When writing the identity line | approved | none | The identity line names the commits used and the date. |

Q24 (proof shown by the author) stays on the gap list: the research found no
primary source, only community posts.

## Health check cards

Drafted 2026-10-27 by claude-sonnet-5-5 (ticket 47), fixed 2026-10-27 after the claude-opus-5-5 check. Every card is a draft: recheck pending, not approved. The check map below still says `gap` for these checks; it changes after the cards are approved. Check id: H1 to H11 are the health checks; "(part)" marks a further card of the same check; HL is a named Laravel reading prompt; L2 to L4 are the named reading steps; G1, G2 and G5 are the spec's gap items; "none" is a rule shared by several checks.

406 merged into 449 (the line count of a changed file is a pointer, like every tool number). REV-406 does not exist.

| id | mode | trigger | status | check id | rule in short |
| --- | --- | --- | --- | --- | --- |
| REV-401 | health, full | When running the copied logic tool (H1) | approved | H1 | The tool part of the copied logic check reports only clones that are new com... |
| REV-402 | health, full | When choosing the jscpd settings (H1) | approved | H1 (part) | Run jscpd with the role's own reviewed settings file, given with --config. N... |
| REV-403 | health, full | When reading the result of the jscpd scan (H1) | approved | H1 (part) | Read how many files jscpd scanned. A scan of 0 files is "not checked", never... |
| REV-404 | health, full | When PHPMD flags a long method (H2) | approved | H2 | A method that PHPMD's ExcessiveMethodLength flags is a pointer with 1 line o... |
| REV-405 | health, full | When PHPMD flags a long class (H2) | approved | H2 (part) | A class that PHPMD's ExcessiveClassLength flags is a pointer with 1 line of... |
| REV-407 | health, full | When counting routes per touched controller (H3) | approved | H3 | Count the route lines for each controller the PR touches. 10 or more route l... |
| REV-408 | health, full | When searching changed controllers for query calls (H4) | approved | H4 | Treat each query call found in a changed controller as a candidate only. Ope... |
| REV-409 | health, full | When reading for N+1 queries (H5) | approved | H5 | A relationship loaded lazily inside a loop over many rows is always a lead,... |
| REV-410 | health, full | When a test is found for a risky area (H6) | approved | H6 | A test found by name or route is only a candidate. Trace the call and read i... |
| REV-411 | health, full | When checking whether tests still run (H6) | approved | H6 (part) | Read changes to the test config, skipped tests, excluded groups, CI workflow... |
| REV-412 | health, full | When no test covers a risky area (H6) | approved | H6 (part) | When no test covers a risky area, report that as a finding of its own: "no t... |
| REV-413 | health, full | When listing old tests that were edited or deleted (H7) | approved | H7 | List edited and deleted tests with git diff -M --name-status from the compar... |
| REV-414 | health, full | When judging a deleted or changed test (H7) | approved | H7 (part) | Judge each deleted or changed test by lost protection: would it still fail i... |
| REV-415 | health, full | When running PHPMD for dead code (H8) | approved | H8 | Run PHPMD UnusedPrivateMethod and UnusedLocalVariable on the changed PHP fil... |
| REV-416 | health, full | When running PHPStan for dead code (H8) | approved | H8 (part) | Run PHPStan at level 4 for dead code: unused private methods, always false i... |
| REV-417 | health, full | When reading changed code for dead code (H8) | approved | H8 (part) | When reading changed code, look for code that no caller uses and for wrapper... |
| REV-418 | health, full | When running the bug finding tool (H9) | approved | H9 | Run PHPStan with Larastan at level 5 on the changed code. |
| REV-419 | health, full | When PHPStan reports an error (H9) | approved | H9 (part) | Open every PHPStan error and confirm it by reading the code. An error you di... |
| REV-420 | health, full | When deciding the weight of a confirmed bug (H9) | approved | H9 (part) | A bug that the PR adds, once confirmed, is must fix, whichever tool found it... |
| REV-421 | health, full | When a PHPStan run reports stale baseline entries (H9) | approved | H9 (part) | A PHPStan run whose only issues are stale baseline entries ("ignored pattern... |
| REV-422 | health, full | When writing the cost to add (H10) | approved | H10 | Propose 1 realistic small feature in the area the PR touches, in 1 line. Lis... |
| REV-423 | health, full | When the touched area existed before the PR (H10) | approved | H10 (part) | When the area existed before the PR, count the same feature on the base and... |
| REV-424 | health, full | When a design regression might be must fix | approved | none | A design regression is must fix only when the PR shows a burden (it made the... |
| REV-425 | health, full | When running the independent check on a picked test (H11) | approved | H11 | Break the code that a picked test claims to guard, then run that test unchan... |
| REV-426 | health, full | When the picked test goes red under the fault (H11) | approved | H11 (part) | The picked test must go red on an assertion failure. A red from a fatal erro... |
| REV-427 | health, full | When picking tests for the independent check (H11) | approved | H11 (part) | Pick at most 3 tests that assert money, login or deleting data in the change... |
| REV-428 | health, full | When writing the fault for a picked test (H11) | approved | H11 (part) | The fault must contradict what the test asserts. Never use a syntax error. A... |
| REV-429 | health, full | When writing the result of the independent check (H11) | approved | H11 (part) | Say what the independent check covered: "covers N picked tests". Never write... |
| REV-430 | health, full | When the picked tests cannot run in the container (H11) | approved | H11 (part) | If the picked tests cannot run here (no runner, no vendor folder, no network... |
| REV-431 | health, full | When reading a changed migration that modifies a column | approved | HL migrations | When a migration changes a column, check that it repeats every modifier the... |
| REV-432 | health, full | When reading the file name of a new migration | approved | HL migrations | Check the timestamp in the file name of a new migration. Migrations run in f... |
| REV-433 | health, full | When reading the down method of a new migration | approved | HL migrations | Read the down() method of each new migration: it should reverse what up() do... |
| REV-434 | health, full | When reading what a migration does to existing rows | approved | HL migrations | Read what a new or changed migration does to the rows already in the table,... |
| REV-435 | health, full | When env() is used in changed code outside config files | approved | HL config | Call env() only inside config files. In any other code read the value with c... |
| REV-436 | health, full | When a changed job is dispatched inside a transaction | approved | HL queues | When a job is dispatched inside a database transaction, check whether the jo... |
| REV-437 | health, full | When a changed event or listener may run before the commit | approved | HL events | When an event or a queued listener needs data written in a transaction, chec... |
| REV-438 | health, full | When a changed job can be retried | approved | HL queues | For a changed job, read how many attempts it gets, what each retry repeats,... |
| REV-439 | health, full | When a PR changes a job or a listener class | approved | HL queues | When a PR changes a job or listener, check that queue workers are restarted... |
| REV-440 | health, full | When a Blade view changed | approved | HL blade | When a Blade view changed, read the code that renders it as well. A view can... |
| REV-441 | health, full | When changed JavaScript carries the same rule as PHP | approved | HL javascript | When changed JavaScript carries the same rule as PHP (a limit, a check, a pr... |
| REV-442 | health, full | When reading changed code for a case it misses (L2) | approved | L2 | While reading the changed code, think of edge cases and check whether the co... |
| REV-443 | health, full | When reading changed code for behaviour that worked before (L3) | approved | L3 | Read for behaviour that worked before the PR and no longer does. |
| REV-444 | health, full | When a rule in the PR may be copied in 2 places (L4) | approved | L4 | When the PR changes a rule, search for a second copy of it and check that bo... |
| REV-445 | health, full | When a fixed list or limit is typed in 2 or more places (G1) | approved | G1 | A fixed list, or a single limit such as a size or a count, typed in 2 or mor... |
| REV-446 | health, full | When searching for the other copies of a list or limit (G2) | approved | G2 | To find other copies, search the repo for the same literal text with a fixed... |
| REV-447 | health, full | When reading the files a PR touched | approved | G5 | Read every touched file whole, not only the changed lines, when answering re... |
| REV-448 | health, full | When writing a finding found by reading a whole file | approved | G5 (part) | Report only what the PR added or what it left behind in an area it touched.... |
| REV-449 | health, full | When a tool or a guard gives a number | approved | pointers | Every number from a tool or a guard is a pointer. Give each pointer 1 line o... |
| REV-450 | health, full | When turning a pointer into a review question | approved | pointers | Use this map from pointer to question. A long new method: question 6. A smal... |

## Check map

Policy cards cover role rules. A check mapped to `gap` still needs a check card.

| check | card id or gap |
| --- | --- |
| `Q1` | `gap` |
| `Q2` | `gap` |
| `Q3` | `gap` |
| `Q4` | `gap` |
| `Q5` | `gap` |
| `Q6` | `gap` |
| `Q7` | `gap` |
| `Q8` | `gap` |
| `Q9` | `gap` |
| `Q10` | `gap` |
| `Q11` | `gap` |
| `Q12` | `gap` |
| `Q13` | `gap` |
| `Q14` | `gap` |
| `Q15` | `gap` |
| `Q16` | `gap` |
| `Q17` | `gap` |
| `Q18` | `gap` |
| `Q19` | `gap` |
| `Q20` | `gap` |
| `Q21` | `gap` |
| `Q22` | `gap` |
| `Q23` | `gap` |
| `Q24` | `gap` |
| `Q25` | `REV-110` |
| `Q26` | `REV-109` |
| `Q27` | `REV-111` |
| `Q28` | `REV-112` |
| `Q29` | `REV-113` |
| `Q30` | `gap` |
| `Q31` | `gap` |
| `Q32` | `gap` |
| `S1` | `gap` |
| `S2` | `gap` |
| `S3` | `gap` |
| `S4` | `gap` |
| `S5` | `gap` |
| `S6` | `gap` |
| `S7` | `gap` |
| `S8` | `gap` |
| `S9` | `gap` |
| `S10` | `gap` |
| `S11` | `gap` |
| `S12` | `gap` |
| `S13` | `gap` |
| `S14` | `gap` |
| `S15` | `gap` |
| `S16` | `gap` |
| `S17` | `gap` |
| `S18` | `gap` |
| `S19` | `gap` |
| `S20` | `gap` |
| `S21` | `gap` |
| `S22` | `gap` |
| `L1` | `gap` |
| `L5` | `gap` |
| `H1` | `gap` |
| `H2` | `gap` |
| `H3` | `gap` |
| `H4` | `gap` |
| `H5` | `gap` |
| `H6` | `gap` |
| `H7` | `gap` |
| `H8` | `gap` |
| `H9` | `gap` |
| `H10` | `gap` |
| `H11` | `gap` |
| `T1` | `gap` |
| `T2` | `gap` |
| `T3` | `gap` |
| `T4` | `gap` |
| `T5` | `gap` |
| `T6` | `gap` |
| `T7` | `gap` |
| `T8` | `gap` |

## Card gap list

- Q1
- Q2
- Q3
- Q4
- Q5
- Q6
- Q7
- Q8
- Q9
- Q10
- Q11
- Q12
- Q13
- Q14
- Q15
- Q16
- Q17
- Q18
- Q19
- Q20
- Q21
- Q22
- Q23
- Q24
- Q30
- Q31
- Q32
- S1
- S2
- S3
- S4
- S5
- S6
- S7
- S8
- S9
- S10
- S11
- S12
- S13
- S14
- S15
- S16
- S17
- S18
- S19
- S20
- S21
- S22
- L1
- L5
- H1
- H2
- H3
- H4
- H5
- H6
- H7
- H8
- H9
- H10
- H11
- T1
- T2
- T3
- T4
- T5
- T6
- T7
- T8
