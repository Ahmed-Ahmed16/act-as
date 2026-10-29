id: REV-P01
rule: Keep the checkout, running site and tracker read only. Write only the packet in a folder outside the checkout.
why: Least privilege limits each person to the access needed for their task, and separation of duties divides one process across people.
applies-when: Any reviewer session that could touch files, a running site or a tracker.
not-when: none
example: In invented PR 101 for owner/shop, the reviewer writes the packet outside the checkout and leaves the site and tracker unchanged.
mode: all
trigger: Before touching checkout files or external systems
kind: source-advice
source: OWASP Secure Product Design Cheat Sheet, The principle of Least Privilege and Separation of Duties, https://cheatsheetseries.owasp.org/cheatsheets/Secure_Product_Design_Cheat_Sheet.html, read 2026-10-26 ; second source: OWASP Authorization Cheat Sheet, Enforce Least Privileges, https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html, read 2026-10-26
status: approved
review: drafted by gpt-6-luna effort max, 2026-10-26 (relay record); checked against the raw source by claude-sonnet-5-5, 2026-10-26, CHECK PASS: anchor verbatim in the OWASP Secure Product Design page; supports least privilege, the read only boundary is a project choice; approved by Ahmed 2026-10-26, as drafted; edited 2026-10-28 for licence (Ahmed's call 2), anchor removed
extra: The access and separation rules support a limited role; the checkout, site, tracker and packet folder are this project's boundaries.
