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

## Review question cards

Drafted 2026-10-27. All are `draft`: none loads and none is approved. Their
check ids stay `gap` in the check map below until Ahmed approves them; the
orchestrator moves them then. Question 12 is NOT in the default set: it is
Ahmed's choice, and the spec leaves the count after it joins open.
Questions 14 and 19 have no card (open point O4). Questions 24 to 29 belong
to size and the packet, and question 30 to security.

| id | mode | trigger | status | check id | rule in short |
| --- | --- | --- | --- | --- | --- |
| REV-501 | health, full | When answering review question 1 | approved | Q1 | No layer, interface, flag or setting that no caller needs today. |
| REV-502 | health, full | When answering review question 2 | approved | Q2 | Prefer the smallest change; ask if deleting or reusing gives the same result. |
| REV-503 | health, full | When answering review question 3 | approved | Q3 | Imagine a helper or wrapper deleted; if nothing moves to the callers it hides nothing. |
| REV-504 | health, full | When answering review question 4 | approved | Q4 | Solve the problem known now, not one that might come. |
| REV-505 | health, full | When question 5 is asked after a pointer | approved | Q5 | A new one off special case in an existing flow is a design problem. |
| REV-506 | health, full | When question 6 is asked after a pointer | approved | Q6 | Splitting into small methods can go too far. |
| REV-507 | health, full | When answering review question 7 | approved | Q7 | A name says in full what the thing is or does, and is not too long. |
| REV-508 | health, full | When answering review question 8 | approved | Q8 | If you cannot follow the code, ask the author to clarify it first. |
| REV-509 | health, full | When question 9 is asked after a pointer | approved | Q9 | A comment explains why, not what. |
| REV-510 | health, full | When answering review question 10 | approved | Q10 | Count layers and hidden state; judge in the context of the whole system. |
| REV-511 | health, full | When answering review question 11 | approved | Q11 | Things that change together sit together; carries the G1 line. |
| REV-512 | health, full | When answering review question 12 | approved | Q12 | A class answers to one narrow business function. NOT in the default set. |
| REV-513 | health, full | When answering review question 13 | approved | Q13 | Business rules stay apart from web, database and framework; carries the G3 line. |
| REV-514 | health, full | When answering review question 15 | approved | Q15 | Could a unit test aim at the changed part alone? Partly backed. |
| REV-515 | health, full | When answering review question 16 | approved | Q16 | A change must not leave the touched code worse. |
| REV-516 | health, full | When answering review question 17 | approved | Q17 | Lines added to a long method may mean a second job. |
| REV-517 | health, full | When answering review question 18 | approved | Q18 | No second copy of existing logic; carries the G1 line. |
| REV-518 | health, full | When answering review question 20 | approved | Q20 | Quick fix or design step: say which. User policy, no source. |
| REV-519 | health, full | When question 21 is asked after a pointer | approved | Q21 | A refactoring goes in a separate PR from a feature or fix. |
| REV-520 | health, full | When answering review question 22 | approved | Q22 | Follow the style of the code around it when no other rule applies. |
| REV-521 | health, full | When answering review question 23 | approved | Q23 | Would the tests fail if the code broke? |
| REV-522 | health, full | When the PR is a refactor or cleanup, for review question 31 | approved | Q31 | A refactor needs a record of old behaviour and proof it holds. |
| REV-523 | health, full | When the docs-guard trigger fires or the PR adds behaviour no document mentions, for review question 32 | approved | Q32 | Docs change with behaviour or setup. |

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
