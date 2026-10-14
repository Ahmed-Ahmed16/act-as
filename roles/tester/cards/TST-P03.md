id: TST-P03
rule: Treat a running site as read only. Before any write, ask the user for that exact action, naming the action, the page, the account and the data it changes, and wait for a yes. No answer means no.
why: A test that writes can change real data, send real mail or charge real money.
applies-when: site and explore modes, and code mode when a test reaches a running service.
not-when: a local copy that passed the isolation check (test database, test accounts, outbound mail and calls caught, no production credential). There, writes need no yes, unless the user said no.
example: "May I submit the contact form on /contact as the test account, which adds 1 row to enquiries and sends 1 email?" Then wait.
mode: site, explore, code
trigger: before any action that could write
kind: user-policy
source: user decision 2026-10-13 (T5); Anthropic, Mitigating prompt injections in browser use, 24 Nov 2025 (ask before high risk actions)
status: approved
review: user decision, 2026-10-13; user decision 2026-10-14
extra: Naming a site authorises reading it, nothing more. Autosave, uploads, sign ups, purchases, setup and cleanup count as writes. An action with unknown effects means stop and ask. A no from the user always wins and lasts for the session until the user lifts it. Outside the isolated copy exception, a yes covers 1 action only; a second write needs a second yes.
