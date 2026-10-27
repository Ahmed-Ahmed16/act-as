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

## Security check cards

Drafted by claude-sonnet-5-5 on 2026-10-27 for ticket 46, fixed the same day
after the claude-opus-5-5 check. Recheck pending, not approved. The check id column shows the check each card is
planned for. The check map below stays on `gap` for these checks until Ahmed
approves the cards. Spec checks that hold several rules are split: S3 into 3
cards, S4 into 2, S6 into 4, S8 into 3, S11 into 2, S12 into 5, S13 into 6,
S17 into 2, S19 into 3, S20 into 3, S21 into 5, L1 into 3. Review question 30
has 2 cards (permission rules, edge cases). Cards that cite a Laravel docs page
carry `docs_version`, `checked_same` and `differs_on`.

| id | mode | trigger | status | check id | rule in short |
| --- | --- | --- | --- | --- | --- |
| REV-301 | security, full | When a changed action loads a record by an id from the request | approved | S1 | Every action that takes a record id from the client must check that this user... |
| REV-302 | security, full | When a changed action is guarded only by a login check | approved | Q30 | Check that an action follows the project's own permission rules, including the... |
| REV-303 | security, full | When a PR changes who may do an action | approved | Q30 | For a changed permission rule, think through its edge cases and look for a test... |
| REV-304 | security, full | When a changed write action relies on a policy | approved | S2 | Every action that creates, changes or deletes data is covered by a permission... |
| REV-305 | security, full | When request data goes into a model create or update | approved | S3 | Pass a model only the request fields you picked or validated, never all the... |
| REV-306 | security, full | When a model is unguarded or force methods are used | approved | S3 | Do not set $guarded to an empty array, and do not use forceFill or forceCreate... |
| REV-307 | security, full | When request ids go into a relation call | approved | S3 | When request ids go into sync, attach or a similar relation call, check which... |
| REV-308 | security, full | When a changed query uses raw SQL | approved | S4 | User input reaches SQL only as a bound value, written as ? or a name. It is... |
| REV-309 | security, full | When request data is used as a column name | approved | S4 | User input never picks a column name in a query, including the order by column.... |
| REV-310 | security, full | When a changed unique rule uses ignore | approved | S5 | Never pass request input to ignore() in a unique rule. Pass the id of the model... |
| REV-311 | security, full | When a changed line stores an uploaded file | approved | S6 | Store an upload under a name the app makes. Never trust the file name or... |
| REV-312 | security, full | When a changed route accepts an uploaded file | approved | S6 | Every upload has a maximum file size, set in the validation. |
| REV-313 | security, full | When a changed validation decides which upload types are allowed | approved | S6 | Allow only the file types the feature needs, and treat SVG as a file that can... |
| REV-314 | security, full | When a changed line picks the disk for an upload | approved | S6 | Store an upload on a disk that fits who may read it. The public disk is for... |
| REV-315 | security, full | When a route is excluded from CSRF protection | approved | S7 | A route is left out of CSRF checks only if it is a server to server callback... |
| REV-316 | security, full | When a changed view prints data without escaping | approved | S8 | Print user text with escaped output. Raw output ({!! !!}) is allowed only when... |
| REV-317 | security, full | When a changed view puts user text in a link address | approved | S8 | A link or src address built from user text needs a check of its scheme, with a... |
| REV-318 | security, full | When a changed export writes user text into a spreadsheet cell | approved | S8 | A spreadsheet or CSV export must not let a cell start with =, +, - or @ from... |
| REV-319 | security, full | When a changed redirect uses a request value | approved | S9 | A redirect target that comes from the request is accepted only if it is on a... |
| REV-320 | security, full | When a change adds a key or token to a committed file | approved | S10 | Keep secrets in the environment, not in code or in committed files. A fallback... |
| REV-321 | security, full | When a changed route is reached by a signed link | approved | S11 | A route that depends on a signed link must run the signature check, with the... |
| REV-322 | security, full | When a changed signed link has or lacks an expiry | approved | S11 | Write down what the signed link is meant to allow, then decide if it needs an... |
| REV-323 | security, full | When a changed route is a login, reset, 2 factor, payment or callback route | approved | S12 | A login, password reset, 2 factor or callback route has a rate limit. |
| REV-324 | security, full | When a changed flow resets or recovers an account | approved | S12 | A password reset checks a token that is random, tied to a single user, and no... |
| REV-325 | security, full | When a changed flow signs a user in or changes their rights | approved | S12 | The session id is renewed when a user logs in and when their rights change. |
| REV-326 | security, full | When a changed flow logs a user out | approved | S12 | Logout ends the session on the server, not only in the browser. |
| REV-327 | security, full | When a changed login or recovery path touches 2 factor | approved | S12 | A recovery or fallback path for the second factor may exist, but it must not... |
| REV-328 | security, full | When a changed file sets the debug option | approved | S13 | Debug mode is off in production. A change must not turn APP_DEBUG on for... |
| REV-329 | security, full | When a changed file sets a session cookie flag | approved | S13 | Session cookies carry the HttpOnly flag, so scripts cannot read them. |
| REV-330 | security, full | When a changed file sets the secure cookie option | approved | S13 | On a site served only over HTTPS, session cookies carry the Secure flag. On a... |
| REV-331 | security, full | When a changed file sets the same site cookie option | approved | S13 | Session cookies set SameSite to lax or strict, not none and not left to the... |
| REV-332 | security, full | When a change sets which proxies the app trusts | approved | S13 | List the proxies your app trusts by address. Use * to trust all proxies only... |
| REV-333 | security, full | When a changed config file calls env with a default | approved | S13 | Read the default value of every env() call that a change adds or edits. The... |
| REV-334 | security, full | When a changed line runs a shell command | approved | S14 | User input never reaches a shell command string. Avoid the shell; if a process... |
| REV-335 | security, full | When a changed line calls unserialize, eval or extract | approved | S15 | User input never reaches unserialize, eval or extract. |
| REV-336 | security, full | When a changed line builds a file path from request data | approved | S16 | A file path built from request data is cut down to a plain file name with... |
| REV-337 | security, full | When a changed line fetches a URL from request data | approved | S17 | When the server fetches a URL given by a user, use a list of allowed hosts... |
| REV-338 | security, full | When a changed HTTP client call fetches a user URL | approved | S17 | The HTTP client that fetches a user URL does not follow redirects. |
| REV-339 | security, full | When a changed response or export returns a model | approved | S18 | A response or export carries only the fields the screen needs, picked by name.... |
| REV-340 | security, full | When a changed line writes data to a log | approved | S19 | Logs never hold passwords, tokens, session ids or personal data unless the... |
| REV-341 | security, full | When a change adds a log destination or a log reader | approved | S19 | Check who can read the log files and where they are sent. Logs hold personal... |
| REV-342 | security, full | When a change adds or changes how long logs are kept | approved | S19 | Logs are kept for the period the project needs and are not kept beyond it. |
| REV-343 | security, full | When a changed route is a webhook or payment callback | approved | S20 | Verify a callback's signature over the raw request body, before the framework... |
| REV-344 | security, full | When a callback handler uses order id, amount or currency | approved | S20 | After a valid signature, still compare the order id, amount and currency in the... |
| REV-345 | security, full | When a callback handler changes data | approved | S20 | A callback that was already processed is refused. Keep the ids of processed... |
| REV-346 | security, full | When a PR changes a dependency manifest or lock file | approved | S21 | Run composer audit on the head lock file and read the result. If the audit... |
| REV-347 | security, full | When a PR adds a Composer repository entry | approved | S21 | A new repositories entry in composer.json needs reading and a reason. A custom... |
| REV-348 | security, full | When a PR adds a Composer script | approved | S21 | A new scripts entry in composer.json runs a command on every machine that runs... |
| REV-349 | security, full | When a PR adds a package | approved | S21 | Read every new package: is it needed, does it come from the official source... |
| REV-350 | security, full | When a PR lowers a package version | approved | S21 | Read every version downgrade in the manifest or lock diff. Say why a package... |
| REV-351 | security, full | When the diff removes a check or guard line | approved | S22 | For a safeguard removed in the diff (authorize, can:, middleware, signed... |
| REV-352 | security, full | When a change makes an outside call that has an effect | approved | L1 | A database transaction does not make an outside charge safe. Use the provider's... |
| REV-353 | security, full | When a change checks a value and then updates it | approved | L1 | 2 requests at the same time must not both pass a check and then both update.... |
| REV-354 | security, full | When a change adds a step that should happen once | approved | L1 | A step that may run only once must fail when it is sent again. Mark the step... |

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
