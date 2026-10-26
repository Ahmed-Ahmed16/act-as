id: REV-P10
rule: Record one comparison base at the start of the review. Use that same base for every comparison.
why: Git defines A...B from a common ancestor, called the merge base.
applies-when: For every comparison made during the review.
not-when: none
example: For invented PR 101 in owner/shop, the reviewer freezes commit a1b2c3d and uses it as the base for every diff.
mode: all
trigger: Before the first comparison
kind: source-advice
source: Git - git-diff Documentation, SPECIFYING THE REVISIONS, https://git-scm.com/docs/git-diff, read 2026-10-26 ; second source: Git - git-merge-base Documentation, DESCRIPTION, https://git-scm.com/docs/git-merge-base, read 2026-10-26
anchor: "starting at a common ancestor of both"
status: approved
review: drafted by gpt-6-luna effort max, 2026-10-26 (relay record); checked against the raw source by claude-sonnet-5-5, 2026-10-26, CHECK PASS: anchor verbatim in git diff docs; merge base confirmed in git merge base docs; freezing one commit is a project choice; approved by Ahmed 2026-10-26, as drafted
extra: Git defines merge base behavior, but freezing one commit for every comparison is this project's choice.
