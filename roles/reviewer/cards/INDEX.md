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

## Business step cards

Drafted 2026-10-27 for ticket 45. All drafts: a different model checks them against the raw
source, then Ahmed approves. Business has no check id in the check map, so the
check id column says none. The step column says where each card belongs in the business mode
file (a number is a step of `## Steps`; `rerun` has no step number yet, see the report).

| id | mode | trigger | status | check id | step | rule in short |
| --- | --- | --- | --- | --- | --- | --- |
| REV-201 | business, full | When looking for the rules page of an area | approved | none | 3 | Pages come from docs/business-rules on the default branch commit. |
| REV-202 | business, full | When naming or judging a rules page | approved | none | 3 | A page name uses business words. |
| REV-203 | business, full | When reading the Covers line of a page | approved | none | 3 | The Covers line sits within the first 5 lines. |
| REV-204 | business, full | When a Covers entry holds a wildcard or pattern | approved | none | 3 | Covers entries are plain files and folders; a pattern is not read. |
| REV-205 | business, full | When a rules page has no Covers line | approved | none | 3 | A page with no Covers line is not applied; the area is incomplete. |
| REV-206 | business, full | When reading the code for a rule | approved | none | 5 | A status on the page is a hint, not an answer. |
| REV-207 | business, full | When a rule line has 2 statuses or none | approved | none | 3 | A rule with 2 statuses or none is not read; the area is incomplete. |
| REV-208 | business, full | When listing the changed files for the business step | approved | none | 3 | List changed files with rename detection on. |
| REV-209 | business, full | When mapping a renamed file to areas | approved | none | 3 | A renamed file is checked by its old path and its new path. |
| REV-210 | business, full | When a changed file is in the no area found list | approved | none | 4 | A changed file no page covers goes in the no area found list as a lead. |
| REV-211 | business, full | When a lead file changes behaviour | approved | none | 4 | A lead that changes behaviour is judged by its guessed area. |
| REV-212 | business, full | When reading the code behind a rule | approved | none | 5 | Read removed lines and callers, not only the files Covers names. |
| REV-213 | business, full | When a rule has no code at the comparison base | approved | none | 5 | No code at the base: write baseline none, new feature, and read the head. |
| REV-214 | business, full | When a match rule is broken by the PR | approved | none | 6 | A broken match rule is a must fix finding and the area fails. |
| REV-215 | business, full | When writing the rule line of a broken match rule | approved | none | 6 | Write the broken rule line in the page's own words, with the value. |
| REV-216 | business, full | When a gap rule is made worse by the PR | approved | none | 6 | A gap made worse is a must fix finding and the area fails. |
| REV-217 | business, full | When new code in an existing door does not follow a gap rule | approved | none | 6 | New code in an existing door that ignores a gap rule is a finding. |
| REV-218 | business, full | When the PR leaves a gap rule alone | approved | none | 6 | A gap left alone is a pointer. |
| REV-219 | business, full | When the PR fixes a gap rule | approved | none | 6 | A gap the PR fixes is 1 line in Behaviour changed, plus a draft note. |
| REV-220 | business, full | When the PR changes behaviour under an owner or open rule | approved | none | 6 | A changed owner or open rule makes the area incomplete. |
| REV-221 | business, full | When a rule and its code are changed in the same PR | approved | none | 6 | A rule and its code changed together: incomplete, merge only after the owner says yes. |
| REV-222 | business, full | When writing the approval line for a changed rule | approved | none | 6 | The reviewer never says the owner approved; print the old and new text. |
| REV-223 | business, full | When the PR changes a rules page | approved | none | 6 | A PR that changes a rule on the page shows the change on its own line. |
| REV-225 | business, full | When new behaviour has no rule on the page | approved | none | 6 | New behaviour with no rule is a pointer with a draft question. |
| REV-226 | business, full | When a touched area has no rules page | approved | none | 4 | An area with no page: not checked, incomplete, never a pass. |
| REV-227 | business, full | When writing the grill brief for a missing page | approved | none | 4 | A grill brief holds the area, the code facts, the PR change and draft questions. |
| REV-228 | business, full | When writing a draft rules page | approved | none | 4 | A grill draft page is written only to the drafts folder. |
| REV-229 | business, full | When a draft rules page is used | approved | none | 4 | A draft page that was used is named by its path and SHA 256, with a copy. |
| REV-230 | business, full | When an area has both a page and a draft | approved | none | 4 | The default branch page wins over a draft; add a pointer. |
| REV-231 | business, full | When building the business verdict | approved | none | 7 | Business fails if any area fails; else incomplete if any is open; else pass. |
| REV-232 | business, full | When writing a business entry | approved | none | 6 | Every business entry carries area: <name>. |
| REV-233 | business | When a business rerun starts | approved | none | rerun | A rerun refuses when the PR head has moved. |
| REV-234 | business | When a business rerun reads its commits and pages | approved | none | rerun | A rerun reads the commits named in the identity line. |
| REV-235 | business | When a business rerun writes the packet | approved | none | rerun | A rerun replaces only the named area's entries. |
| REV-236 | business | When a business rerun starts | approved | none | rerun | A business rerun runs no size, security or health step. |
| REV-237 | business | When a business rerun adds a page about who may do what | approved | none | rerun | A rerun that adds a page about who may do what changes the security line. |
| REV-238 | business | When a business rerun finishes | approved | none | rerun | A rerun adds the line business rerun for <area>, date, head. |
| REV-239 | business | When a business rerun checks draft pages | approved | none | rerun | A rerun rechecks the hash of every draft page and glossary. |

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
