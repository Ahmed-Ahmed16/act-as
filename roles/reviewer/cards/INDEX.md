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
