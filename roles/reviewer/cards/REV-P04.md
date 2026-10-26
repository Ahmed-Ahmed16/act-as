id: REV-P04
rule: Count the changed lines. If the count exceeds 300, stop with a short packet. Continue only for that run if the user says "review it anyway".
why: Small changes are easier to review carefully, so the source recommends breaking large changes into smaller parts.
applies-when: When measuring the change size against the 300 line cap.
not-when: none
example: In invented PR 101 for owner/shop, the reviewer counts 301 changed lines and stops with a short packet unless the user says "review it anyway".
mode: all
trigger: When the changed line count exceeds 300
kind: source-advice
source: Small CLs | eng-practices, Why Write Small CLs?, https://google.github.io/eng-practices/review/developer/small-cls.html, read 2026-10-26
anchor: "Reviewed more thoroughly"
status: approved
review: drafted by gpt-6-luna effort max, 2026-10-26 (relay record); checked against the raw source by claude-sonnet-5-5, 2026-10-26, CHECK PASS: anchor verbatim under Why Write Small CLs; no line count in the source, 300 is a project choice; approved by Ahmed 2026-10-26, as drafted
extra: The source gives no hard line count; 300 and the words "review it anyway" are project choices.
