id: MGR-P05
rule: If the tester or developer was on in this session, their rules still hold. The manager adds MGR-P01 on top.
why: A role switch never relaxes a rule.
applies-when: a session where another role was on.
not-when: none.
example: After the tester ran, TST-P01 still holds while the manager writes.
mode: all
trigger: at the start of the task
kind: user-policy
source: user decision, manager v1.2 plan, 2026-10-19
status: draft
review: user agreed the rules 2026-10-19 (plan decision 3); claude-sonnet-5-5 2026-10-19 CHANGE: wording matched to the plan; user approval ___
