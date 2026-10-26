id: REV-P07
rule: Flag money code for a separate Opus review. Do not perform that review, claim it is done or start it.
why: The reviewer v1 policy assigns money code to a separate Opus review.
applies-when: When changed code handles money or payment logic.
not-when: No money code appears.
example: In invented PR 101 for owner/shop, a payment change is flagged for the separate Opus review, and the reviewer does not start it.
mode: all
trigger: When changed code handles money
kind: user-policy
source: user decision, reviewer v1 spec, approved 2026-10-25
status: approved
review: drafted by gpt-6-luna effort max, 2026-10-26 (relay record); checked against the raw source by claude-sonnet-5-5, 2026-10-26, CHECK PASS: matches the approved spec bullet; ASVS 2.3.5 claim in extra confirmed; no external source; approved by Ahmed 2026-10-26, as user policy
extra: no external source found for a separate Opus code review; searched OWASP ASVS V2.3.5 and OWASP Top 10:2025 A06. ASVS requires multi user approval for high value business flows, but not a separate code review.
