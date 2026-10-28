# Reviewer mode: full

Run size, business, security and health in that order, then the packet check. Only size can stop the run.

## Steps

Before each step, run `cards.py reviewer full <step number>`, for example
`cards.py reviewer full 1`. The step number is the digit, never the step name.

- Only size stops the run (story 18).
- One check record: `check-record.json` at the packet root. Where a mode
  says `runs/check-record.json`, use the root file, and pass that path to
  `check11_run.py --record` and `health_verdict.py --record`.
- Skip the mode steps that make the folder, write a mode packet, run the
  packet check or compare snapshots. Full mode does those once.

1. **Freeze, folder and size.** Run `cards.py reviewer full 1` first.
   a. Laravel check from ROLE.md. Stop as it says. No packet folder.
   b. Run size mode steps 1 to 4, each with its own
      `cards.py reviewer size <n>` line. A merged PR whose base is not
      proved: stop, make no packet, say so.
   c. Fetch the default branch fresh:
      `git -C <checkout> fetch origin <default branch>`.
      Write its name and `git rev-parse FETCH_HEAD` as the default commit.
      If the fetch fails, read the name and commit with
      `gh api repos/<owner>/<repo>/branches/<default branch>`
      (a read, no objects). Then business is
      `not checked: default branch not fetched`: skip business steps 3 to 7,
      call no `business_pages.py`, write a Not checked line.
      If both fail, make no packet and say so.
   d. Save `composer.json` and `composer.lock` at the frozen head to `runs/`
      with the raw `gh api` read from ROLE.md. Run
      `python tools/laravel_line.py runs/composer.lock runs/composer.json`.
      Its output is the packet's `Laravel:` line.
2. **Split step.** Run `cards.py reviewer full 2` first. Run this step only
   when a full run's size line is `fail` and the user did not say
   "review it anyway". Stop the full review at size.

   a. Use this full run's own packet folder and saved counter run at
      `runs/size-count.json`. Never use a size run folder.
   b. List entry points that really load: routes, commands, scheduled jobs
      and screens. For example, `routes/garden.php` loads the seed screen.
      Cards: `REV-121`, `REV-123`, `REV-124`, `REV-125`, `REV-126`.
   c. Trace changed files to those entry points. Set shared files aside.
      For example, 2 routes may both use `SeedStore`.
      Cards: `REV-122`.
   d. Form groups by entry point. Name a cleanup group
      `no behaviour change: remove unused seed helpers`.
      Cards: `REV-127`, `REV-128`.
   e. Run `python tools/split_plan.py hunks --repo <checkout> --base <base> --head <head> --packet <packet folder>`.
      Place every piece. Cut a hunk into line ranges when it holds 2
      behaviours, including tests and generated copies. Link each test or
      generated piece to its changed source pieces, or to an unchanged
      file at the frozen head. Record the command used to check that file.
      A test with neither goes to `unplaced`. Give generated pieces a
      rebuild command. For example, `f1h1:L1-L8` goes with the seed screen.
      Cards: `REV-129`, `REV-130`, `REV-131`.
   f. Read language hunks with `hunks --show <hunk id>` and the same frozen
      arguments. Record each key's `shape`, `key`, `pieces`, `page` and
      `part`. Record each page with its source pieces. In `keys_check`,
      record `how` you read them and how many distinct keys you found as
      `keys_found`. For example, key `Plant` belongs to page `garden` and
      part `seed`. A text only unit needs a named existing screen. Record
      the command used to read it on the default branch. The packet says:
      `Translations by page: not checked: PR over the cap, split it first`
   g. Write `needs` and order the groups. Break any loop and record it in
      `loop_notes`. Put work no entry point reaches in `unplaced`, as a
      lead to follow. For example, move a shared type into the first group.
      Cards: `REV-132`, `REV-133`, `REV-134`, `REV-135`.
   h. Cut group 1 into parts of 300 counted lines or fewer. Mark pieces
      `money`, `access`, `deletion` or `unsure`. A part may stay over only
      for 1 new class or function. Record its declaration and closing
      lines. Search the base for its name and search the diff's deleted
      lines for it. For every other counted piece in that part, record
      a check that the symbol needs it. Move unrelated work out.
      Cards: `REV-136`, `REV-137`.
   i. Read the default branch, or the evidence that `main` exists, and
      record `main`. Read CI workflow files at the frozen head with GET
      calls. Record their `on:` text as read. If a file cannot be read,
      say `unreadable`. Do not guess what its filters do.
      Cards: `REV-138`, `REV-139`.
   j. Write `split-input.json`. Run `python tools/split_plan.py build <packet folder>`,
      then `python tools/short_packet.py <packet folder> --repo-name <owner/repo> --pr <number> --default <branch>@<40 hex> --date <YYYY-MM-DD>`.
      Run `python tools/packet_check.py <packet folder>` and quote its
      output. Never copy the `hunks` screen output into `runs/`. A pass
      proves shape and consistency. It does not prove recorded facts.
      Cards: `REV-140`.

3. **Review it anyway.** Run `cards.py reviewer full 3` first.
   Only when size is `fail` and the user said "review it anyway" in this
   run. Never otherwise. Never for a later run (`REV-P04`).
   a. Do step 2 sub steps a to e and g to i. Do not do 2f's last sentence:
      never write `Translations by page: not checked: PR over the cap, split it first`.
      Translations come from health step 16. Write `split-input.json`.
      Run `python tools/split_plan.py build <packet folder>`.
      Do not run `short_packet.py`. Do not stop.
   b. Put the line `reviewed over the cap, on Ahmed's word` under
      `# Review packet`, above the identity line.
   c. The size line stays `fail` with counts. Every other line and field
      uses normal words. Never write `not checked: PR over the cap`
      anywhere, and never "It was not reviewed past size".
   d. In step 8, write the Split plan body as the single line
      `@@split-field@@`. End Drafts with the single line
      `@@split-draft@@`, after your findings for the author.
      Step 8 fills both.
4. **Business.** Run `cards.py reviewer full 4` first.
   Run business mode steps 3 to 7 with their own cards lines.
   Skip its steps 1, 2, 8, 9, 10. Keep grill briefs, Not checked lines,
   pointers and findings for step 8. Then write
   `runs/business-risk-notes.txt`: one line per changed file in a touched
   area whose rule concerns money, logins or access, or deleting data:
   `<path> | <area> | <money, access or deleting> | <rule id>`.
   No such file: write `none`.
5. **Security.** Run `cards.py reviewer full 5` first.
   Run security mode steps 2 to 7. Skip steps 1, 8, 9, 10.
   It fills the money line and the Opus brief (Q2 A).
6. **Health.** Run `cards.py reviewer full 6` first.
   Order: health step 2; then the guard block steps 1 to 5 (skills,
   targets, the 3 guards saved to `runs/`, `debate-review` through
   `guard_run.py debate`, team rule); then steps 3 to 19;
   step 21 only on a pointer. Skip steps 1 and 20.
   Risky areas for H6 and H11: run `risky_areas.py` as in step 8,
   add the files the money line names, add the files in
   `runs/business-risk-notes.txt`. A health entry whose finding touches
   access, money or private data starts its reason with `touches: access`,
   `touches: money` or `touches: private data`.
7. **Security fold in.** Run `cards.py reviewer full 7` first.
   For each health entry with a `touches:` reason and a word other than
   none, add a security entry with id `F-<health id>`, mode security,
   the same word, and the abuse and harm lines. Then rebuild the security
   line by the step 5 rule (fail first, then incomplete).
   If a fold turns the line to `fail`, add the entry to Known risks as a
   security entry. Do not rerun the tools.
8. **CI evidence and the packet.** Run `cards.py reviewer full 8` first.
   a. CI:
      `gh api --paginate --slurp 'repos/<owner>/<repo>/actions/runs?head_sha=<full head>&per_page=100'`,
      saved to `runs/ci-runs.json` (an array of pages).
      One Tests run line per run whose `head_sha` equals the PR head:
      `CI run <id> on <head>: <state>`. States: `pass` (completed, success);
      `fail` (failure, timed_out, startup_failure, action_required);
      `cancelled`; `mixed` (neutral, skipped or stale);
      `pending` (queued, in progress, waiting, requested).
      Every line that is not `pass` also gets a Not checked line.
      Only when all pages hold 0 runs:
      `not checked: no CI run on head <head>`.
      A local run never counts as CI proof.
   b. Write `packet.md`: the cap line (override only), identity (`mode=full`),
      the `Laravel:` line, size, business, security, health, money,
      then the 7 fields and Drafts. Known risks in order: must fix
      (security, business, health), findings with money, accounts or other
      users' data harm, other findings, leads. Behaviour changed holds
      Translations by page or `no translation files changed`.
      Not checked holds every `not checked` and every `___`, never empty.
      Drafts holds the message to the author (must fix first), grill briefs,
      rules page notes, and the Opus brief when money is yes.
      Never "safe to merge".
   c. Write the 4 JSON files at the root. Under the cap, `split-plan.json`
      is the empty form from size.md.
   d. Override only: `python tools/override_parts.py <packet folder>`.
9. **Packet check.** Run `cards.py reviewer full 9` first.
   `python tools/packet_check.py <packet folder>` after the last write,
   `override_parts.py` included. Not `packet_check: pass`:
   repair or withhold (`REV-P08`).
10. **Show and compare.** Run `cards.py reviewer full 10` first.
   Show the packet path and the verdict block. Save `runs/snapshot-end.txt`,
   compare with the start file, quote both and the result.
   Exit 1: say it plainly.

## Finish checklist

- [ ] Laravel check quoted.
- [ ] Head, base and default commit in full, and which fetch path ran.
- [ ] Laravel line.
- [ ] Size line and counter output.
- [ ] Key tool lines of each mode.
- [ ] 24 + H + T entries in the one record.
- [ ] Business risk notes file.
- [ ] Fold entries or "no touches".
- [ ] Money line and brief.
- [ ] CI read saved and every state line.
- [ ] Override: cap line, no cap stop words, `override_parts.py` output.
- [ ] Packet check output.
- [ ] Snapshots compared.
- [ ] Every `cards.py` line.
- [ ] Never imply "safe to merge".
