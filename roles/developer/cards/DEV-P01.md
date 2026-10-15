id: DEV-P01
rule: Keep each patch small. A code change over 300 changed lines, tests not counted, stops before more code is written and gets split into patches that each fit.
why: A small patch can be reviewed and reverted. A large one hides mistakes.
applies-when: planning or writing any code change, including a delegate's diff.
not-when: test files do not count toward the 300.
example: A feature plan shows 450 changed lines. It becomes patch 1, the data model (180 lines), and patch 2, the form (270 lines).
mode: all
trigger: before writing code, and before handing back a diff
kind: user-policy
source: user decision, developer v1.1 plan, 2026-10-15 (pending card approval)
status: draft
review: second model check against PLAN.md, 2026-10-15: added exceptions removed; the user approves policy cards
