# Reviewer mode: security

Ask 1 question: can someone abuse this change now? A tool finds the spot.
Reading decides. The tools and searches below are examples, not the limit of
the review. Also read the removed lines and the callers of changed code.

This mode runs 24 checks: S1 to S22, L1 and L5. It also fills the money
line. It never fixes anything and never says "safe to merge".

## Steps

Before each step, run `cards.py reviewer security <step number>`, for example
`cards.py reviewer security 1`. The step number is the digit, never the step name.

1. **Freeze and folder.** Run the Laravel check from ROLE.md first. Write down
   the full PR head, the full head of the base branch, and the comparison base.
   Rule: `REV-P10`. One base serves every comparison. Make the packet folder
   outside the checkout (ROLE.md section 5) and save the start snapshot to
   `runs/snapshot-start.txt`. The checkout is never changed. In a security
   only run, get `files.json` first:
   `python tools/size_counter.py --repo <checkout> --base <comparison base> --head <PR head> --out <packet folder>`
   (add `--merged` for a merged PR; exit 3 means the base is not proved: write
   `not checked: PR already merged, base not proved` as the security line and
   stop). Do not use its size verdict. Security runs on a PR over the cap only
   when the user said "review it anyway".
2. **Run the tools.** Rule: `REV-P05`. Command:
   `python tools/security_scan.py tools --repo <checkout> --head <PR head> --files <packet folder>/files.json --out <packet folder>/runs`
   It runs 3 tools in the 1 reviewer image (its name is in the output; write
   it in the packet):
   - Semgrep on the added and changed files only, never the whole project.
   - `composer audit` on the head lock file.
   - gitleaks on the head files.

   The scan folder holds the exact Git blobs. Export attributes cannot
   omit or rewrite them. Composer advisories are counted from its JSON output.
   Container rules, all of them:
   - Every container is named `actas-t33-<tool>-<pid>` and run with `--rm`.
   - The head files are mounted read only. Never mount the checkout, the home
     folder or the Docker socket.
   - Only the fetch step has a network: Semgrep rules by full id, and
     `composer audit` (it asks Packagist). The fetch step runs no PR code.
   - Scans, and anything that runs PR code, have `--network none`.
   - Semgrep rule files stay in a throwaway folder and are deleted. They are
     never copied into the packet or the repo.
   - Never use `composer audit --ignore-unreachable`. It turns a dead network
     into a false pass.
   - Never prune Docker. Never touch a container or image you did not make.

   If Docker is off, or a tool fails, that tool gives exactly
   `not checked: <tool> did not run, <reason>` (tool is `semgrep`,
   `composer audit` or `gitleaks`). Never a pass. The reading part of every
   check still runs, and a reading finding stays a finding. A Semgrep
   check that did not run, or that missed a PHP file from `files.json`, is
   "not checked", not clean. The PHP rules cover `.php`, `.phtml` and `.tpl`.
   `semgrep-paths.txt` holds the paths from Semgrep's JSON `paths.scanned`.
   If that field is missing, the line is
   `not checked: semgrep did not report scanned paths`. Copy the tool's output
   into `runs/`.
3. **Find the spots.** Command:
   `python tools/security_scan.py finders --repo <checkout> --base <comparison base> --head <PR head> --out <packet folder>/runs`
   It writes `runs/security-finders.json`: search hits for each check, on
   added lines, and on removed lines for S22. A hit is only a place to read.
   No hit does not clear a check: still read the changed code. Hits that
   look like keys are redacted. Never print or copy a secret into any file.
4. **Read the 24 checks.** Read in this order: L5 first, then S1 to S22, then
   L1. For each check, write 1 entry in `check-record.json`. It holds the id,
   `mode: security`, the tool part (hits or tool result, or "no tool"), the
   reading part (what you read and the answer), and a word:
   `must fix`, `finding`, `lead`, `pass`, or `incomplete`. A check that does not
   apply says `pass` with `does not apply: <why>` in the reason. A tool part
   that did not run gives `incomplete` with its "not checked" line as the
   reason, unless the reading found a finding or must fix, which wins. The
   questions to answer, with the tools named in the spec:
   - **L5, a file the task does not need.** Each changed file has a reason in
     the task. A file with no reason is a lead, read first. It only sets the
     reading order.
     Unrelated file card: `REV-111`.
   - **S1, login but no owner check.** Is there an owner or permission check for
     this action on this record? A job or command must not use system rights
     for a user's request. "User A asks for user B's record" is a flaw only
     when A has no permission and a test asserts the rejection.
   - **S2, a write with no policy.** Who may do it? A policy `before` method is
     not called when the class has no method for that ability.
   - **S3, mass assignment, also through relations.** Which fields and related
     rows can a user set? (Semgrep `laravel-dangerous-model-construction`.)
   - **S4, raw SQL.** Does user input reach it unbound? A bound `?` is safe.
   - **S5, `ignore()` in a unique rule.** Where does the id come from?
   - **S6, upload.** Disk, file name, size limit, allowed types (SVG carries
     script).
   - **S7, CSRF.** Each exempt route must be a real callback with a signature
     check (S20).
   - **S8, output to a browser or a sheet.** Can any role write that text? A
     link needs an allowed scheme. A sheet cell must not start with `=`, `+`,
     `-`, `@`.
   - **S9, redirect.** Is there a list of allowed places?
   - **S10, secrets.** Live key or test key? A fallback secret inside
     `env('X', '...')` counts.
   - **S11, signed link.** Write the intended access rule first. The link's
     purpose decides if it needs an expiry.
   - **S12, login and account flows.** A rate limit; a reset that checks a
     token; a new session id after login; logout ends the session; no way
     around 2 factor.
   - **S13, unsafe settings.** Runs on every PR. Production values, trusted
     proxies, the default of each `env()` call. A `.env.example` change is
     read by hand.
   - **S14, shell command.** Does user input reach it? The Semgrep rule is
     `php.lang.security.injection.tainted-exec.tainted-exec`. Its sources are
     PHP superglobals only (such as `$_GET`), so for Laravel input this check rests on the
     search hits and your reading.
   - **S15, `unserialize`, `eval`, `extract`.** Does user input reach it?
   - **S16, a file path from user input.** `basename` only, inside 1 allowed
     folder.
   - **S17, the server fetches a user URL.** A list of allowed hosts; does the
     client follow redirects?
   - **S18, private fields leave the app.** Only the fields the screen needs;
     never tokens, codes or other users' data.
   - **S19, personal data or secrets in logs.** What is logged, who reads the
     log, how long it is kept.
   - **S20, webhook and callback.** The signature covers the fields that pick
     the order; order id, amount and currency are compared; a replay is
     refused. This is money code (step 6). Read it only. Do not rebuild it.
   - **S21, dependency changes.** `composer audit` result, plus the manifest
     and lock diff: a new package, a new `repositories` entry, a new `scripts`
     entry, a downgrade. Lock files leave the size count but never this check.
   - **S22, a removed safeguard.** Read each removed `authorize`, `can:`,
     `middleware`, `signed`, `throttle`, `validate`, `lockForUpdate`,
     `where('user_id'`. Was a reason given? Does something else now guard it?
   - **L1, steps in the wrong order.** No tool. A repeat request, 2 parallel
     requests, an unknown payment result. A database transaction does not
     make an outside charge all or nothing.
   L2, L3 and L4 live in health. When one touches access, money or private
   data, report it here as a security finding too.
   Access cards: `REV-301` to `REV-307`.
   Input and output cards: `REV-308` to `REV-319`.
   Secrets and login cards: `REV-320` to `REV-327`.
   Settings and unsafe call cards: `REV-328` to `REV-342`, `REV-356`, `REV-357`.
   Callback and dependency cards: `REV-343` to `REV-350`.
   Removed safeguard and request order cards: `REV-351` to `REV-354`.
5. **Write each finding.** Words: `must fix`, `finding`, `lead`. No scale, no
   CVSS. Every entry in Known risks carries: the word, file and line, the
   abuse line ("who does what, step by step, to get what"), and the harm
   line. Example abuse line: "A signed in user changes the id in the URL from
   17 to 18 and downloads another customer's invoice." Rule: `REV-P11`.
   A finding is `must fix` only when the whole path from the user's input to
   the harm is read and confirmed in the code, and the abuse line needs
   nothing you cannot see. If 1 link hangs on something unseen (web server
   config, a setting, another service), it is a `finding` and it says
   `depends on: <x>`. A tool hit alone is a `lead`. A second model's comment
   is a lead until the code confirms it.
6. **Money line.** Rule: `REV-P07`. Decide by reading, not by words. Money
   words are only search hints: `$amountOfItems` in paging is not money; a
   bare `capture($id)` is. Money code is code that changes amounts, currency,
   charges, refunds, balances, payment status, or access a payment grants.
   If it is found, the line is exactly
   `money: yes, files <x, y>. Needs the separate Opus review before merge. Not done by this review.`
   and Drafts, not sent gets the Opus brief (below). If none is found by
   reading: `money: no money code found by reading; not proof`. If you could
   not look: `money: not checked: <reason>`. This run never does the money
   review, never says it is done, and never starts it. Run all 24 checks on the
   money files too. The flag adds to the review. It does not replace it.

   The Opus brief, under Drafts, not sent, holds 3 things:
   - the money files, one per line, with a line saying why each is money code;
   - the changed behaviour, in plain words: what the PR changes for amounts,
     charges, refunds, balances, payment status or access (read from the diff);
   - the standing money rule: build and review in separate Opus 5.5 sessions
     (`claude-opus-5-5`, effort medium); check which model actually ran; then
     a blind review by a different model; every fix gets reviewed again; if
     Opus is not available, say so and ask the user.
   The brief is a draft. It is never sent and never started.
7. **Verdict.** The security line is `security: <word> <reason>`.
   - `fail`: 1 or more `must fix` entries. The run goes on after a fail.
   - `incomplete`: no `must fix`, and 1 of these is true. A check, or the tool
     part of a check, is "not checked". Or a finding says `depends on: <x>`
     and its harm is money, accounts or other users' data. Write
     `merge only after: <x>`.
   - `pass`: every check that applies ran, no `must fix`. Ordinary findings
     allow a pass.
   Fail comes before incomplete. A locked Laravel major that is past its
   security fix date gets 1 finding line in Known risks ("framework version
   out of security support since <date>", releases page URL, date read). It
   never changes the verdict line by itself.
8. **Write the packet.** `packet.md` in the packet folder, in the packet
   format the packet check reads, plus the 4 saved inputs. In a security only
   run the identity line says `mode=security`. The size, business and health
   lines each say `not asked: security run only`. Tests run says
   `not asked: security run only`. Split plan says
   `not needed: security run only`. The security line is step 7, the money
   line is step 6. These fields all have real content: Behaviour changed;
   Files that matter most; Not checked (every tool that did not run, with its
   reason, and at least the other 3 modes); Known risks (the security
   entries); Pointers; Drafts, not sent (the message to the author, never
   sent; the Opus brief when the money line says yes). In a full run the
   full mode file calls this mode and merges these entries into the 1 packet.
9. **Packet check.** `python tools/packet_check.py <packet folder>` after the
   last write. Exit 0 prints `packet_check: pass`. Anything else: repair and run
   again, or withhold the packet. Show a packet only after it passes (`REV-P08`).
10. **Show and compare.** Show the packet path and the verdict block. Save
    `runs/snapshot-end.txt` and compare it with the start snapshot. Exit 0
    means equal. Quote both paths and the result. Exit 1: say so plainly.

## Rerun security for an area

The user says "rerun security for <area>" and names the exact packet path.
Default rules (O10, not yet confirmed): the same as "rerun business".

1. Read the identity line. If the PR head moved since the packet was written,
   refuse and ask for a new full run. Read the base and default branch commits
   named in the identity line, never a newer default branch head.
2. One writer at a time. Write into the same packet folder and the same
   `packet.md`. Never make a second packet.
3. Recompute the hash of every draft rules page you use. If one differs, write
   "page changed since the first run".
4. Replace only that area's security entries (check record, Known risks,
   Pointers, Not checked, Drafts). Do not run size, business or health again.
   Do not rerun the tools unless the user asks.
5. Security line rule: a first run `fail` stays `fail`, with
   `also: rerun security for <area>` added when that rerun is still open. An
   `incomplete` stays `incomplete`. A `pass` becomes `incomplete` with
   `merge only after: rerun security for <area>`.
6. Whether a new rules page "says who may do what" is not decided. Do not
   decide it. Quote the page lines about who may do what, next to the S1 and
   S2 entries, and say "page lines quoted, not judged". A rerun may keep or
   worsen the security line. It never improves it on your judgement of a page.
7. Add the line `security rerun for <area>, <date>, head <sha>` under the
   verdicts. Run the packet check again before showing the packet.

## Finish checklist

- [ ] Laravel check result quoted.
- [ ] Head, base branch head and comparison base written down in full.
- [ ] The image name, and the output line of each of the 3 tools (or its
      exact "not checked" line).
- [ ] The paths Semgrep reports match the changed PHP files in `files.json`
      (the `pathcheck` line).
- [ ] Finders file saved. No secret in any saved file.
- [ ] 24 entries in `check-record.json`: S1 to S22, L1, L5.
- [ ] Every finding has an abuse line and a harm line. Every `must fix` has a
      confirmed path. Every `depends on` names the unseen thing.
- [ ] Money line written. If it says yes, the Opus brief sits under Drafts.
- [ ] Packet check output quoted (`packet_check: pass`).
- [ ] Start and end snapshot compared, result quoted.
- [ ] Every `cards.py` command with its first output line.
- [ ] Nothing implied as "safe to merge".
