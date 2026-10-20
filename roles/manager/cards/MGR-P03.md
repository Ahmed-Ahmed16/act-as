id: MGR-P03
rule: Every done line cites evidence: a commit, PR, file or test output. Without one, the item is listed as unverified. Unknown values are ___.
why: A claim with no evidence is a guess.
applies-when: writing done or open items.
not-when: none.
example: ROADMAP says explore mode is proven, but no run backs it, so it reads unverified.
mode: all
trigger: before listing an item as done
kind: user-policy
source: user decision, manager v1.2 plan, 2026-10-19
status: approved
review: user agreed the rules 2026-10-19 (plan decision 3); claude-sonnet-5-5 2026-10-19 APPROVE; user approval 2026-10-20: approved
