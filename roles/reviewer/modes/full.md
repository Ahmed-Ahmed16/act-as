# Reviewer mode: full

Run size, business, security and health in that order, then the packet check. This file is a scaffold.

## Steps

Before each step, run `cards.py reviewer full <step number>`, for example
`cards.py reviewer full 1`. The step number is the digit, never the step name.

1. **Scaffold.** Filled by ticket 39. Until then this mode does nothing but
   open.
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

## Finish checklist

- [ ] Filled by ticket 39.
