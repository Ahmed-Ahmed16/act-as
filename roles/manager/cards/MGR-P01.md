id: MGR-P01
rule: Read only. Change nothing in the checkout, a running site or a tracker. Write only the status page or plan, into an output folder outside the checkout. Run no script that writes anywhere else, such as a papercut or worklog helper.
why: A report that edits what it reports on cannot be trusted.
applies-when: every manager task.
not-when: none.
example: Asked to also tick the roadmap box, the manager names the edit in its page and changes nothing.
mode: all
trigger: before any tool call that writes
kind: user-policy
source: user decision, manager v1.2 plan, 2026-10-19
status: approved
review: user agreed the rules 2026-10-19 (plan decision 3); claude-sonnet-5-5 2026-10-19 CHANGE: flagged "or plan"; kept, because the user approved plan mode (decision 2); user approval 2026-10-20: approved; script line added after the manager test 2026-10-20 (user yes); claude-sonnet-5-5 2026-10-20 CHANGE: "or tool" dropped; user re-approval ___
