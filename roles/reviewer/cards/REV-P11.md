id: REV-P11
rule: Mark a finding must fix only when code confirms the whole path to the harm.
why: The user policy sets full path confirmation as the must fix threshold.
applies-when: When assigning must fix status to a finding.
not-when: none
example: In invented PR 101 for owner/shop, the claimed harm has no confirmed code path, so the reviewer does not mark it must fix.
mode: all
trigger: When deciding whether a finding is must fix
kind: user-policy
source: user decision, reviewer v1 spec, approved 2026-10-25
status: approved
review: drafted by gpt-6-luna effort max, 2026-10-26 (relay record); checked against the raw source by claude-sonnet-5-5, 2026-10-26, CHECK PASS: matches the approved spec bullet; no external source; approved by Ahmed 2026-10-26, as user policy
extra: no external source found for the full path threshold; searched OWASP Risk Rating Methodology and OWASP Code Review Guide. They cover likelihood, impact and review practice, but do not set this threshold.
