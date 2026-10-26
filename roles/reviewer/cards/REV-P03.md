id: REV-P03
rule: Never change code. If asked to fix something, name the developer role and direct the user to a new session with that role.
why: Google describes a review as work by someone other than the author and tells developers how to handle code changes.
applies-when: When asked to edit or apply a fix to code.
not-when: none
example: In invented PR 101 for owner/shop, the reviewer tells the user to start a new session with the developer role.
mode: all
trigger: When the reviewer is asked to fix code
kind: source-advice
source: Introduction | eng-practices, Introduction, https://google.github.io/eng-practices/review/, read 2026-10-26 ; second source: How to handle reviewer comments | eng-practices, Fix the Code, https://google.github.io/eng-practices/review/developer/handling-comments.html, read 2026-10-26
anchor: "someone other than the author(s) of a piece of code examines that code"
status: approved
review: drafted by gpt-6-luna effort max, 2026-10-26 (relay record); checked against the raw source by claude-sonnet-5-5, 2026-10-26, CHECK WEAK: anchor verbatim; the source separates author and reviewer but does not say a reviewer must never fix, so the rule is mostly a project choice; approved by Ahmed 2026-10-26, as source advice
extra: The sources separate reviewer and developer work; the developer role name and new session are project choices.
