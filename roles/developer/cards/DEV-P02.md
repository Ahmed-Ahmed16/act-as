id: DEV-P02
rule: Prove first. A bug fix starts from a test that fails for the right reason and ends with that same test passing. A feature ends with tests that show it working. Quote the runs.
why: A fix with no failing test first may fix nothing.
applies-when: any bug fix or feature.
not-when: none.
example: The handoff test tests/login.spec fails with "expected 200, got 500". The patch is applied. The same test passes. Both runs are quoted.
mode: all
trigger: before writing a fix or feature, and before reporting it done
kind: user-policy
source: user decision, developer v1.1 plan, 2026-10-15 (pending card approval)
status: draft
review: second model check against PLAN.md, 2026-10-15: added exceptions removed; the user approves policy cards
