id: REV-P05
rule: Mark anything not inspected or not run as "not checked" and give the reason. Never call it a pass.
why: OWASP recommends secure defaults and says to fail securely to well defined defaults.
applies-when: For every file, claim or check that was not inspected or run.
not-when: none
example: In invented PR 101 for owner/shop, a test did not run because the test database was unavailable, so the packet says "not checked: test database unavailable".
mode: all
trigger: When something was not checked
kind: source-advice
source: OWASP Secure Product Design Cheat Sheet, Methodology, https://cheatsheetseries.owasp.org/cheatsheets/Secure_Product_Design_Cheat_Sheet.html, read 2026-10-26
status: approved
review: drafted by gpt-6-luna effort max, 2026-10-26 (relay record); checked against the raw source by claude-sonnet-5-5, 2026-10-26, CHECK WEAK: anchor verbatim; the source is about secure defaults in product design, applied here by analogy, the not checked label is a project rule; approved by Ahmed 2026-10-26, as source advice; edited 2026-10-28 for licence (Ahmed's call 2), anchor removed
extra: OWASP's design guide supports conservative defaults, but neither it nor the Error Handling guide sets a review status. The "not checked" label is this project's reporting rule.
