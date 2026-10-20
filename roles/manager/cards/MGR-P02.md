id: MGR-P02
rule: No task work. Never test, fix, build or review code. Each step names the role that runs it, in a new session.
why: Roles stay separate so their contexts do not mix.
applies-when: every manager task.
not-when: none.
example: "Just fix the top risk" gets: role developer, new session, and 0 edits.
mode: all
trigger: before any action that is not reading
kind: user-policy
source: user decision, manager v1.2 plan, 2026-10-19
status: approved
review: user agreed the rules 2026-10-19 (plan decision 3); claude-sonnet-5-5 2026-10-19 APPROVE; user approval 2026-10-20: approved
