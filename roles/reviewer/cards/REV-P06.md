id: REV-P06
rule: Do not write "safe to merge" in the packet. Do not add an overall line.
why: Dijkstra says tests can show that bugs exist, but cannot show that none remain.
applies-when: When writing the packet conclusion or summary.
not-when: none
example: In invented PR 101 for owner/shop, tests pass, but the packet gives no overall verdict.
mode: all
trigger: When drafting the packet conclusion
kind: source-advice
source: Notes on Structured Programming (EWD 249), On the reliability of mechanisms, https://www.cs.utexas.edu/~EWD/transcriptions/EWD02xx/EWD249/EWD249.html, read 2026-10-26
anchor: "never to show their absence!"
status: approved
review: drafted by gpt-6-luna effort max, 2026-10-26 (relay record); checked against the raw source by claude-sonnet-5-5, 2026-10-26, CHECK PASS: anchor verbatim in EWD249; supports that testing cannot show absence, the packet wording rule is a project choice; approved by Ahmed 2026-10-26, as drafted
extra: The source limits what testing can prove; the ban on "safe to merge" and on an overall line is this project's packet rule.
