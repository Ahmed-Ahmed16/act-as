id: MGR-P05
rule: Rules an earlier role set in this session stay on. The manager adds its own on top.
why: Same as SKILL.md step 5: a switch never relaxes a rule.
applies-when: a session where another role was on.
not-when: none.
example: After the tester ran, TST-P01 still holds while the manager writes.
mode: all
trigger: at the start of the task
kind: user-policy
source: user decision, manager v1.2 plan, 2026-10-19
status: draft
review: user agreed the rules 2026-10-19 (plan decision 3); second model check ___; user approval ___
