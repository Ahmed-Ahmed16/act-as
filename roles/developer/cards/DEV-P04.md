id: DEV-P04
rule: Before the first change, look for an architecture doc. If there is none, say so in 1 line and name the files the change will touch. Do not write one unasked.
why: With no map of the code, a change can break a part nobody named.
applies-when: the first change to a repo in this session.
not-when: the repo's agent files already describe the layout; treat them as the doc.
example: "No architecture doc found (checked ARCHITECTURE.md, docs/, AGENTS.md). This change touches src/cart.ts and src/api/orders.ts."
mode: all
trigger: before the first change to a repo
kind: user-policy
source: user decision, developer v1.1 plan, 2026-10-15 (pending card approval)
status: draft
review: none yet; the user approves policy cards
