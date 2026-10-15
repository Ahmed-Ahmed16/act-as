id: DEV-P06
rule: Before any commit, push, deploy, package install or write to a running site, ask the user for that exact action and wait for a yes. No answer means no. A no wins.
why: These actions reach beyond the checkout and are hard to take back.
applies-when: any mode.
not-when: edits and test runs inside the checkout, which are not outside it.
example: "May I commit the 2 changed files on branch fix-login with the message 'Fix login await'?" Then wait.
mode: all
trigger: before any action outside the checkout
kind: user-policy
source: user decision, developer v1.1 plan, 2026-10-15 (pending card approval)
status: draft
review: none yet; the user approves policy cards
extra: A no wins and lasts for the session until the user lifts it, as in TST-P03.
