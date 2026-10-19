# Tester mode: site

Scripted checks of a running site in a browser: smoke, canary and regression.
Reads only, unless the user approves 1 exact write (`TST-P03`). A local server
that passed the isolation check counts as a copy, not a running site.

## Steps

Before each step, run `cards.py tester site <step>`.

1. **Name the target.** Live site, staging, or a local server. For a live site,
   the user named it in this session; that allows reading only. Done when the
   URL and its kind are written down.
2. **Learn the screen** before writing steps: routes, labels, roles, button
   text (`TST-007`).
3. **Choose what to check.** Keep browser checks few, since each is costly
   (`TST-207`); push business rules down to API checks where possible
   (`TST-206`, `TST-205`). Regression coverage for behaviour a change touches:
   `TST-208`. Access to records by id: map the inputs first (`TST-028`).
4. **Write the checks.** Wait for the page with conditions, never sleeps
   (`TST-008`); narrow locators that match twice (`TST-009`); keep secrets
   in the runner's credential store (`TST-005`).
5. **Run.** Before any step that could write, stop for `TST-P03`. A step that
   fails every run in the same place is a product bug or a changed screen, not
   a flake (`TST-010`). CI exit codes: `TST-006`.
6. **Around a release** (reads only; deploys, rollbacks, flag flips and
   traffic changes belong to others):
   - Before it: a rollback is ready (`TST-407`); pick the few metrics that
     show user harm (`TST-403`).
   - Right after it reaches the site: read only checks (`TST-401`); monitoring
     shows the running version (`TST-406`).
   - During a canary: compare canary with control (`TST-402`), over a window
     no longer than the canary (`TST-404`); a marginal score is reported as
     marginal (`TST-405`); compare versions in the same time window, not
     before and after (`TST-413`).
   - Shadow copies and dark launches: users see only the current version
     (`TST-411`); storage is read only or separate (`TST-412`).
7. **Report** each bug per `TST-P01`, `TST-P02`, `TST-215`, with screenshots.

## Finish checklist

- [ ] Target URL and kind (live, staging, local) quoted.
- [ ] Every check: its name and its pass or fail output.
- [ ] Every write: the user's approval quoted (action, page, account, data);
      isolation evidence under `TST-P03`; or the line "no writes made".
- [ ] Every bug: the 5 proof fields from `TST-P02`, plus a screenshot path.
- [ ] Results counted: passed, failed, suspected, not run.
