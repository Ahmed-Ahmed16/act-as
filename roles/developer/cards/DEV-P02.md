id: DEV-P02
rule: Prove first. A bug fix starts from a test that fails for the reported reason and ends with that same test passing. A feature ends with tests that show it working. Quote the runs.
why: A fix with no failing test first may fix nothing.
applies-when: any fix or feature, in any mode.
not-when: a change with no behaviour, such as a comment or a rename the tests already cover; say so in 1 line.
example: The handoff test tests/login.spec fails with "expected 200, got 500". The patch is applied. The same test passes. Both runs are quoted.
mode: all
trigger: before writing a fix or feature, and before reporting it done
kind: user-policy
source: user decision, developer v1.1 plan, 2026-10-15 (pending card approval)
status: draft
review: none yet; the user approves policy cards
