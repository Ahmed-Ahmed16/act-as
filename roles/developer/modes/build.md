# Developer mode: build

A new feature, or a change to existing behaviour.

## Steps

Before each step, run `cards.py developer build <step>`.

1. **Read the ground.** The repo's agent files and the architecture doc
   (`DEV-P04`). Done when the files the change will touch are named.
2. **Plan.** Split the work into patches of 300 changed lines or fewer, tests
   not counted (`DEV-P01`). Say which patches go to a delegate, if any.
3. **Test first.** For each patch, write a test for the new behaviour and see
   it fail (`DEV-P02`).
4. **Build.** Write the patch, or check the delegate's diff against the plan.
5. **Prove.** The new tests pass; the existing suite still passes.
6. **Hand back.** Report per the finish checklist. Commit only on the user's
   yes (`DEV-P06`).

## Finish checklist

- [ ] Files touched named, and the architecture doc path or the flag.
- [ ] Patch list with the changed lines of each.
- [ ] Every new test: failing run, then passing run, quoted.
- [ ] Full suite result: passed, failed, not run.
