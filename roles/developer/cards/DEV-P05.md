id: DEV-P05
rule: In a clean room rebuild, never open or copy the original's source. Work from the spec, the docs and the observed behaviour. Log every input read in REBUILD-INPUTS.md.
why: Code written after reading the original can copy it without meaning to.
applies-when: rebuild mode.
not-when: none.
example: To rebuild a booking page, the developer reads the help pages and clicks through the live page (reads only), and logs both. It does not open the old repo.
mode: all
trigger: before reading any input for a rebuild
kind: user-policy
source: user decision, developer v1.1 plan, 2026-10-15
status: approved
review: second model check against PLAN.md, 2026-10-15: added exceptions removed; user decision 2026-10-19: approved
