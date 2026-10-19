id: MGR-P04
rule: The status page has 5 parts: done, open, at most 3 risks, at most 3 next steps, and the role for each step.
why: A short fixed shape is read; a long one is skipped.
applies-when: status mode.
not-when: none.
example: A fourth risk is dropped, or replaces a weaker one.
mode: all
trigger: before writing the page
kind: user-policy
source: user decision, manager v1.2 plan, 2026-10-19
status: draft
review: user agreed the rules 2026-10-19 (plan decision 3); second model check ___; user approval ___
