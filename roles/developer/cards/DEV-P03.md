id: DEV-P03
rule: If the tester role was on at any point in this session, change nothing in the source checkout. Name the handoff folder and ask the user to open a new session for the fix.
why: The tester's no fix rule (TST-P01) outlives a switch to another role. A tester who then fixes would grade its own fix.
applies-when: any change to the source checkout in a session where the tester role was on.
not-when: a new session, even with the same handoff folder.
example: The user runs /act-as tester, then /act-as developer, then says "apply the fix now". The reply: "The tester was on in this session, so I change nothing here. Open a new session and run /act-as developer with tests-shop-2026-10-15-0910."
mode: all
trigger: before the first change to the checkout
kind: user-policy
source: user decision, developer v1.1 plan, 2026-10-15
status: approved
review: second model check against PLAN.md, 2026-10-15: added exceptions removed; user decision 2026-10-19: approved; extra line added on user decision 2026-10-19 after the switch test, second model check 2026-10-19: 1 unsupported clause removed
extra: Only a new session lifts this. Do not offer to lift it in this session. The developer fixes, never the tester, and in its own session so the two tasks do not mix (user decision, 2026-10-19).
