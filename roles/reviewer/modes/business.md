# Reviewer mode: business

Check the PR against the business rules page of each area it touches. The
page says what the business wants. The question is whether the PR still does
that, not only what the code did before. A tool finds the spot, then reading
decides. A tool hit alone is never a finding.

This mode never writes or edits a rules page in the checkout. It never passes
an area that has no page.

This file covers a PR under the cap, and a business run alone on a PR over
the cap. A business rerun on a short packet is not decided (open question
O19): stop and ask the user.

## The rules page contract

- Where: `docs/business-rules/<area>.md` on a fresh `origin/<default branch>`.
  1 page per area, named in business words (for example
  `lending-and-returns.md`). Nowhere else: no guessing from a README or a wiki.
- A line `Covers:` sits within the first 5 lines of the page (a title line
  `# ...` and a blank line may sit above it). It lists the files or folders
  the page covers, comma separated. A folder ends in `/`. Plain files and
  folders only. An entry with a wildcard or other pattern is not read: write
  `not checked: Covers entry is a pattern` and make that area incomplete. The
  plain entries on the same line still count.
- A line `Checked at:` names the commit the statuses describe.
- Each rule is a line that starts `R<n>.` and carries exactly 1 status word in
  bold: `match`, `gap`, `owner` or `open`. A rule with 2 statuses is
  "multiple" and stays unread, and so is a rule with none (settled 2026-10-27,
  B15): write `not checked: rule <id> has <2 statuses
  or no status>` and make that area incomplete.
- A page with no `Covers:` line in its first 5 lines is not applied. Write
  `not checked: page has no Covers line` and make that area incomplete.
- A draft page lives outside the checkout (the drafts folder the private
  overlay names, else `rules-drafts-<owner>-<repo>` next to the checkout). A
  draft is used only for an area with no page on the default branch. If both
  exist, the default page is used and a pointer says "Draft also exists, not
  used" (reference: the draft path).

## Steps

Before each step, run `cards.py reviewer business <step number>`, for example
`cards.py reviewer business 1`. The step number is the digit, never the step name.

1. **Freeze.** Run the Laravel check from ROLE.md first. Then freeze the
   same values as size mode step 1: full PR head, head of the PR's base
   branch, the comparison base (rule `REV-P10`, merged PR handled as there).
   Also fetch the default branch read only and write down its full commit
   as the default commit. Do not check anything out. The rules pages come from
   the default branch commit, never from the PR head and never from the
   working tree. If the default branch cannot be fetched, write
   `business: not checked: default branch not fetched` and stop.
2. **Packet folder and first snapshot.** As size mode step 2. In a full run
   these already exist: reuse them.
3. **Map files to areas.** Run the page tool with the frozen values:
   `python tools/business_pages.py --repo <checkout> --base <comparison base> --head <PR head> --default-ref <default commit> [--drafts <drafts folder>] --out <packet folder>`.
   It reads changed files with rename detection on (a rename is checked by
   its old path and its new path against every Covers line), reads each page,
   and writes `runs/business-map.json`, `rules-pages.json` and a copy of
   every page used in `runs/`. Exit 1 means git failed: write
   `business: not checked: mapping failed, <the stderr line>`, never a pass.
   Copy its one line of output into the packet's check notes.
4. **Areas with no page, and the no area found list.** Read
   `business-map.json`.
   - A changed file in `no_area_found` gets a guess of its area, from the code
     you read, marked `lead`. Put each file and guess in Not checked as
     `lead: <file>, guessed area <name>, no page covers it`. A lead whose
     file changes behaviour is judged by its guessed area. If that area has no
     page: `not checked: no rules page for <area>, grill needed`.
   - An area with no page: write 1 Not checked line
     `not checked: no rules page for <area>, grill needed` and put the
     grill brief under Drafts (see "Grill needed" below). The area state is
     `incomplete`, reason `rules page for <area>`. Say in 1 line that you can
     start the grill in a separate session while the run goes on. If the user
     says "not now", the brief stays in the packet.
   - A page in `pages_without_covers` that belongs to a touched area: the Not
     checked line above, area incomplete.
5. **Read each rule at the base and at the head.** For each page that maps at
   least 1 file, read the code each rule is about with
   `git show <comparison base>:<path>` and `git show <PR head>:<path>`. Also
   read removed lines and the callers of changed code, not only the files the
   Covers line names. Where the base has no code for the rule yet, the entry
   says `baseline: none, new feature` and the head alone is read. For every
   rule checked (match rules too) write 1 entry in
   `runs/check-record.json`: `kind: rule`, `mode: business`, `area`, `id`
   (the rule id), both reads, `tool_result`, `reading_result`, `word`,
   `reason`. Rule ids repeat across pages, so the `area` field tells them apart.
6. **Judge.** Rule: `REV-P11` (a finding is must fix only when the whole path
   to the harm is confirmed in the code). Use this table. The first matching
   row wins; the gap made worse row comes before the others.

   | Rule status | Base to head | Result |
   | --- | --- | --- |
   | match | the PR breaks it, in old or new code | must fix finding, area fails. One rule line, in the page's own words, with the rule and the value: `R3 says a loan lasts 21 days; with this PR it lasts 14` |
   | gap | made worse (check removed or weakened, wider reach, or a new door copies the weakness) | must fix finding, area fails |
   | gap | new code in an existing door that does not follow it | finding |
   | gap | left alone | pointer |
   | gap | fixed | 1 line in Behaviour changed; draft note under Drafts to flip the page |
   | owner or open | behaviour changed | area incomplete, `depends on: owner answers <id>` |
   | any | rule and its code changed together (PR changes the page) | area incomplete, `merge only after: owner says yes to the <id> change`; Not checked line `approval: not checked by the reviewer, old: "<exact old text>", new: "<exact new text>"` |
   | none | new behaviour with no rule | pointer, with a draft question for the page |

   A rule changed in code only, page left alone, is a fail. If the PR changes
   a rules page, check the code against the page as it is on the default
   branch, and show the change on its own line:
   `PR changes rule <id> on the page; needs the owner's yes`. The reviewer
   does not check the owner's yes. Every business entry in every field
   carries `area: <name>`.
7. **Verdict.** Write each area's state (`pass`, `fail`, `incomplete`,
   `not checked`, with a reason) to `runs/business-areas.json`:
   `{"areas":[{"area":"...","state":"...","reason":"..."}]}`. Include every
   touched area, each area once. Then run
   `python tools/business_verdict.py verdict --areas runs/business-areas.json`
   and use its line as the business line, as it is. Fail if any area fails;
   else incomplete if any area is not checked or depends on something; else
   pass. A rerun's verdict is rebuilt the same way from every area.
8. **Write the packet.** `packet.md` in the packet format the packet check
   reads (ROLE.md and the size mode file give the shape). For a business run
   alone: identity `mode=business`; the size, security and health lines say
   `not asked: business run only`; money says
   `not checked: money not looked at, business run only`; Tests run says
   `not asked: business run only`. In a full run, the other lines are the
   other modes' own. Placements:
   - must fix findings and findings: Known risks, with file and line, the
     rule line, the area, and the page with its commit (or path and hash for
     a draft);
   - pointers (gap left alone, new behaviour with no rule, draft also exists):
     Pointers, each with its judgement line and the page path as reference;
   - `no rules page`, `no Covers line`, leads, `depends on` and `approval`
     lines: Not checked;
   - grill briefs, rule text notes and the message to the author: Drafts, not sent.
   A draft page that was used is named in the business line:
   `rules page: draft, not in the repo yet`, and its path and SHA 256 go in
   Known risks or Behaviour changed where it was used; the copy is in `runs/`.
   Rule: `REV-P05` (not looked at means not checked, never a pass). The packet
   never says "safe to merge".
9. **Packet check.** Run `python tools/packet_check.py <packet folder>` after
   the last write. Exit 0 prints `packet_check: pass`. Anything else: repair
   and run again, or withhold the packet. Show a packet only after it passes
   (`REV-P08`).
10. **Show and compare.** Show the packet path and the verdict block. Save
    the snapshot again and compare, as size mode step 7. Quote both snapshot
    paths and the result.

### Rerun: "rerun business for <area>"

The user names the exact packet path. A rerun writes into the same folder and
the same `packet.md`. Only 1 writer at a time. Run no size, security or
health step.

These steps have their own numbers, 20 to 25, so `cards.py` can load them.
Before each one, run `cards.py reviewer business <step number>`, for example
`cards.py reviewer business 20`. No business card is approved yet, so these
steps list none.

20. **RR1. Check.** Run
   `python tools/business_verdict.py rerun-check --packet <packet folder> --head <current PR head> [--drafts <drafts folder>]`.
   Exit 1 with `refuse: PR head moved`: stop and ask for a new full run. Exit 3
   (short packet, O19): stop and ask the user. Exit 0: it prints the base and
   default commits from the identity line (`use base`, `use default`) and any
   `page changed since the first run: <area>` lines. Copy those lines into
   Not checked.
21. **RR2. Read the same commits.** Use the base and default commits the tool
   printed, never a newer default branch head. Run step 3 with them, with the
   area's new page (a new draft in the drafts folder, or the page now on the
   default branch commit named in the identity line; a page merged after the
   first run is not on that commit, so use the draft).
22. **RR3. Replace the area.** Redo steps 4 to 6 for that area only. Replace that
   area's entries by their `area` field in every field of the packet, in
   `check-record.json` and in `rules-pages.json`. Rewrite the draft message.
   Remove the grill brief of that area when its page now exists.
23. **RR4. Rebuild the verdict.** Update `runs/business-areas.json` with every
   area the PR touches, the other areas as they were. Run the step 7 command.
   Fixing 1 area must not pass business while another area is still
   `grill needed`.
24. **RR5. Security line rule.** If the rerun added a page that says who may do
   what, run
   `python tools/business_verdict.py security-line --line "<current security line>" --area <area>`
   and use its output as the security line. A security `pass` becomes
   `incomplete` with `merge only after: rerun security for <area>`. An
   `incomplete` keeps its reason and gains that reason. A `fail` stays `fail`
   and gains `also: rerun security for <area>`. A line that says `not asked` or
   `not checked` stays as it is. Whether a page "says who may do what" is a
   reading call (open question O10): state your reason in 1 line.
25. **RR6. Add the rerun line.** Set `rerun=yes` in the identity line. Under the verdict lines add
   `business rerun for <area>, <YYYY-MM-DD>, head <full head sha>`. Run the
   packet check again (step 9) and show the packet after it passes. The size
   and health lines stay as they were.

## Grill needed

A page is missing for an area the PR touches. The brief goes under Drafts, not
sent, and holds:
- the area name, in business words;
- the code facts read (files, what they do, with file and line);
- what the PR changes there;
- first draft questions for the owner, 1 line each, in plain words (what goes
  wrong if the answer is unknown).

A grill draft page is written only to the drafts folder (the private overlay's
folder, else `rules-drafts-<owner>-<repo>` next to the checkout). Refuse a path
inside the checkout. The business line stays `incomplete, merge only after:
rules page for <area>, then rerun business for <area>` until the page exists
and business is rerun for that area. A missing page never passes.

## Finish checklist

- [ ] Laravel check result quoted.
- [ ] Head, default branch commit and comparison base written down in full.
- [ ] Page tool command and its output line quoted.
- [ ] Every touched area has a state and a reason in `business-areas.json`.
- [ ] Every rule checked has a check record entry with both reads, or `baseline: none, new feature`.
- [ ] Every business entry in every field carries `area:`.
- [ ] Verdict tool line used as the business line.
- [ ] Missing page: `grill needed` line and brief present; never a pass.
- [ ] Packet check output quoted (`packet_check: pass`).
- [ ] Start and end snapshot compared, result quoted.
- [ ] Rerun only: the head check, the commits used, the security line rule applied, the rerun line added.
- [ ] Every `cards.py` command with its first output line.
- [ ] Nothing implied as "safe to merge".
