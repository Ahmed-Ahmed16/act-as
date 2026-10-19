# Developer mode: fix

Apply a tester handoff folder, or fix a reported bug. First check `DEV-P03`:
if the tester role was on in this session, stop and ask for a new session.

## Steps

Before each step, run `cards.py developer fix <step>`.

1. **Read the input.** The handoff `REPORT.md` and its "For the fixer"
   section, or the bug report. Check the base commit matches the checkout.
   Done when each bug to fix is listed with its test.
2. **Set up.** Run the install and test commands from the handoff or the repo
   docs. Done when the bug's test runs and fails for the reported reason.
3. **Fix.** Apply the proposed patch in the order given, or write the fix.
   Keep it within `DEV-P01`.
4. **Prove.** Run the same test: it now passes. Run the rest of the suite.
5. **Hand back.** Report per the finish checklist. Commit only on the user's
   yes (`DEV-P06`).

## Finish checklist

- [ ] `DEV-P03` check: tester role not on in this session, quoted.
- [ ] Every bug: its test failing before and passing after, both runs quoted.
- [ ] Full suite result: passed, failed, not run.
- [ ] `git diff --stat` quoted and lines outside tests counted.
