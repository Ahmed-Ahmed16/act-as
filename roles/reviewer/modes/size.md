# Reviewer mode: size

Count the PR's changed lines against the 300 line cap. This mode counts and
writes a packet. It runs no business, security or health check.

This file covers a PR under the cap. Over the cap (301 or more counted
lines) is not written here yet: a later step adds the short packet, the
split plan and the draft message. Until then, on a count over 300, write the size
result, stop, and say "over the cap: split plan not written yet".

## Steps

Before each step, run `cards.py reviewer size <step number>`, for example
`cards.py reviewer size 1`. The step number is the digit, never the step name.

1. **Freeze.** Run the Laravel check from ROLE.md first. Then write down the
   full PR head commit, the full head commit of the PR's base branch, and
   the comparison base. Rule: `REV-P10`. One base serves every comparison;
   never pick another later. Open PR: the comparison base is the merge base
   of the base branch head and the PR head. Merged PR: the base is the one
   GitHub recorded for the PR (`gh pr view <n> --json baseRefOid`), used
   with the proved command in step 3. If that call fails or its answer
   cannot be checked, the base is not proved: write
   `not checked: PR already merged, base not proved` as the size line,
   stop, and make no count.
2. **Packet folder and first snapshot.** Make the packet folder outside the
   checkout (ROLE.md section 5). Save the checkout snapshot into its `runs/`
   folder: `python <snapshot tool> save <checkout> runs/snapshot-start.txt`.
   The checkout is never changed. If the PR head is not in the checkout,
   fetch it read only; do not check it out.
3. **Count.** Rule: `REV-P04`. Run the counter with the frozen values:
   `python tools/size_counter.py --repo <checkout> --base <comparison base> --head <PR head> --out <packet folder>`
   (add `--merged` for a merged PR). It writes `files.json` in the packet
   folder and prints the size line. Use its numbers as they are. Do not
   count by hand and do not round. Exit 1 means git failed: write
   `not checked: count failed, <the stderr line>`, never a pass. Exit 3
   means the base is not proved: use the step 1 words. Copy the counter's
   JSON output into `runs/size-count.json`.
4. **Decide.** 300 counted lines or fewer is `pass`. 301 or more is `fail`
   with no margin. The size line is
   `size: <pass or fail>, <n> counted lines, cap 300; left out: tests <n> (<k> files), lock files <n> (<k> files), generated <n> (<k> files), docs <n> (<k> files)`.
   Only the words "review it anyway" from the user lift the cap, and a size
   mode run has nothing to lift. A fail goes to the over the cap note at the
   top of this file.
5. **Write the packet.** File `packet.md` in the packet folder, in the
   packet format the packet check reads. Identity line with `mode=size`. The
   size line from step 4. The business, security and health lines each say
   `not asked: size run only`. The money line says
   `not checked: money not looked at, size run only`. Tests run says
   `not asked: size run only`. Split plan says
   `not needed: <n> counted lines, cap 300`. Every other field has real
   content: Behaviour changed (what the PR changes, in plain words, read
   from the diff), Files that matter most (path plus one line why), Not
   checked (a reason on every line, and at least the other three modes),
   Known risks and Pointers (`none` is allowed), Drafts, not sent (the
   message to the author, never sent). Write the 3 other saved inputs
   (`check-record.json`, `split-plan.json`, `rules-pages.json`) with empty
   lists, beside `packet.md`.
6. **Packet check.** Run `python tools/packet_check.py <packet folder>`
   after the last write to the packet. Exit 0 prints `packet_check: pass`.
   Anything else: repair and run again, or withhold the packet. Show a
   packet only after it passes (`REV-P08`).
7. **Show and compare.** Show the packet path and the verdict block. Save
   the snapshot again as `runs/snapshot-end.txt` and compare:
   `python <snapshot tool> compare runs/snapshot-start.txt runs/snapshot-end.txt`.
   Exit 0 means equal. Quote both snapshot paths and the result. Exit 1:
   say so plainly and do not call the checkout unchanged.

## Finish checklist

- [ ] Laravel check result quoted.
- [ ] Head, base branch head and comparison base written down in full.
- [ ] Counter command and its size line quoted.
- [ ] `files.json` saved and its total equals the size line.
- [ ] Packet check output quoted (`packet_check: pass`).
- [ ] Start and end snapshot compared, result quoted.
- [ ] Every `cards.py` command with its first output line.
- [ ] Nothing implied as "safe to merge".
