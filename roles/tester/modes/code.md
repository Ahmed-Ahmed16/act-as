# Tester mode: code

Tests on a local copy of the code: unit, integration, regression, and review of
test code. Tests go in the output folder from `ROLE.md` section 5 and run in
a throwaway copy. The source checkout stays untouched.

## Steps

Before each step, run `cards.py tester code <step>`.

1. **Set up.** Read the repo's test docs and runner config. Confirm the copy is
   isolated (`TST-P03`: test database, test accounts, mail caught, no
   production credential). Rebuild anything the tests read (`TST-004`). Done
   when 1 existing test runs green, or the reason it cannot is written down.
2. **Plan.** Pick the layer for each check (`TST-201`, `TST-205`, `TST-206`).
   Plan speed, security and load checks from the start (`TST-204`), and for
   inputs that reach a query or interpreter (`TST-026`, `TST-029`), and access
   rules (`TST-027`). For AI features: `TST-018` to `TST-024`. Turn a story's
   examples into readable tests (`TST-202`). Automate or test by hand:
   `TST-210`, `TST-211`. Which checks go in which pipeline stage: `TST-414`,
   `TST-415`.
3. **Write tests.** 1 condition per test, 4 visible parts (`TST-101`,
   `TST-118`); self checking (`TST-102`); repeatable with cleanup (`TST-103`,
   `TST-104`); minimal setup (`TST-116`, `TST-117`); doubles around the code,
   never in it (`TST-105` to `TST-108`); no branches, no sleeps (`TST-109`,
   `TST-110`, `TST-008`); messages that point at the failure (`TST-112`);
   secrets kept out (`TST-005`). A new or changed command or handler: test
   bad inputs and fuzz it (`TST-002`, `TST-003`).
4. **Run.** Watch a new test fail for the right reason before trusting a pass.
   A failure that comes and goes: `TST-113`. A test that broke after an
   unrelated change: `TST-114`. A slow suite: `TST-115`, `TST-209`. CI exit
   codes: `TST-006`. Failed eval runs of an AI feature: read the transcripts
   (`TST-017`). A test task that is stuck: ask for help (`TST-217`).
5. **Review test code** written in the session or by an AI agent: `TST-109`,
   `TST-111`, `TST-030`, and the `test-guard` skill (report only).
6. **Review a fix from another session:** it must come with a regression test
   that failed before it (`TST-001`, `TST-P02`). **Review a release on a test
   copy:** rollback safety evidence (`TST-408`), both flag states tested
   (`TST-409`), old release toggles (`TST-410`).
7. **Report** each bug per `TST-P01`, `TST-P02`, `TST-215`; where it is
   recorded: `TST-216`.

## Finish checklist

- [ ] Isolation check result quoted (step 1).
- [ ] Every new test: its path, and the run output showing it fail first, then
      the final run output.
- [ ] Start and end checkout state match; comparison quoted. Tests and runs
      are in the output folder from `ROLE.md` section 5.
- [ ] Every bug: the 5 proof fields from `TST-P02`.
- [ ] Results counted: passed, failed, suspected, not run.
