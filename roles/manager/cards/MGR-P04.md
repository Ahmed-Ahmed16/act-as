id: MGR-P04
rule: The status page has 5 parts: done, open, at most 3 risks, at most 3 next steps, and the role for each step. A role is tester, developer, manager, or user for steps only the user can do.
why: A short fixed shape is read; a long one is skipped.
applies-when: every status page; plan mode has no risks part.
not-when: none.
example: A fourth risk is dropped.
mode: all
trigger: before writing the page
kind: user-policy
source: user decision, manager v1.2 plan, 2026-10-19
status: approved
review: user agreed the rules 2026-10-19 (plan decision 3); claude-sonnet-5-5 2026-10-19 APPROVE, example trimmed to match the plan; user approval 2026-10-20: approved; role list added 2026-10-20 (user yes)
