id: DEV-P04
rule: Before the first change, look for an architecture doc, for example ARCHITECTURE.md, docs/architecture*, or a layout section in the agent files. If there is none, say so in 1 line and name the files the change will touch. Do not write one unasked.
why: With no map of the code, a change can break a part nobody named.
applies-when: the first change to a repo in this session.
not-when: none.
example: "No architecture doc found (checked ARCHITECTURE.md, docs/architecture*, and the agent files for a layout section). This change touches src/cart.ts and src/api/orders.ts."
mode: all
trigger: before the first change to a repo
kind: user-policy
source: user decision, developer v1.1 plan, 2026-10-15
status: approved
review: second model check against PLAN.md, 2026-10-15: added exceptions removed; user decision 2026-10-19: approved
