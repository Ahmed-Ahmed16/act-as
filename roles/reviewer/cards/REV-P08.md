id: REV-P08
rule: Show the packet only after the packet check passes.
why: The user policy makes a passing packet check the gate for showing a packet.
applies-when: Before displaying or sharing a packet.
not-when: none
example: In owner/shop, a packet that fails its check stays hidden until a later check passes.
mode: all
trigger: Before a packet is shown
kind: user-policy
source: user decision, reviewer v1 spec, approved 2026-10-25
status: approved
review: drafted by gpt-6-luna effort max, 2026-10-26 (relay record); checked against the raw source by claude-sonnet-5-5, 2026-10-26, CHECK PASS: matches the approved spec bullet; no external source; approved by Ahmed 2026-10-26, as user policy
extra: no external source found; searched protected branch status checks and OWASP Error Handling. Those cover merge gates and runtime errors, not packet display.
