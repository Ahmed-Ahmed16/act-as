# Manager mode: status

Write 1 status page into an output folder outside the checkout.

## Steps

Before each step, run `cards.py manager status <step number>`, for example
`cards.py manager status 1`. The step number is the digit, never the step name.

1. **Gather.** Read the plan files, git log, open PRs and handoff folders.
   Change nothing. Done when each source read is listed.
2. **Done and open.** List what is done, each with its evidence, and what is
   open. Cards: MGR-001, MGR-003.
3. **Risks.** At most 3, each with its sign and owner role. Cards: MGR-002,
   MGR-005.
4. **Next steps.** At most 3, in order, each with a role and a done line.
   Cards: MGR-003, MGR-006.
5. **Write.** Save `STATUS.md` in the output folder and show its path.

## Finish checklist

- [ ] Page path quoted; checkout unchanged.
- [ ] No more than 3 risks and 3 steps.
