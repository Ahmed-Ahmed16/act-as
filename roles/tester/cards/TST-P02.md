id: TST-P02
rule: File a bug only with all 5 proof fields: the expected behaviour and where that expectation comes from, the target version, the setup, the observed failure, and evidence that reproduces it. Otherwise file it as suspected.
why: A failing check can come from bad credentials, missing fixtures or a wrong expectation, not a bug.
applies-when: before filing any bug.
not-when: a crash or data loss seen once; file it at once as suspected, high severity, and keep trying to reproduce it.
example: "Checkout total wrong" with no source for the right total stays suspected until the price rule is found in the spec or the code.
mode: all
trigger: before filing a bug
kind: user-policy
source: user decision 2026-10-13 (T4); photocraft AGENTS.md (regression test that failed before the fix); tester-army/e2e AGENTS.md (passing tests are not done); pstack skills/tdd and principle-prove-it-works
status: approved
review: user decision, 2026-10-13; the repo sources are to be rechecked when their own cards are written
extra: An intermittent failure is recorded as "intermittent, N of M runs". A fix is accepted only when the same check that failed now passes.
