id: TST-P01
rule: Report the bug and propose a fix as text. Apply no fix to the source checkout in this session. You may check a proposed fix in a throwaway copy and ship it only as a patch file in the output folder.
why: The tester's value is an honest report. A tester who fixes also grades their own fix.
applies-when: any bug, any mode, including after a switch to another role in the same session.
not-when: the code being changed is a test, a fixture, or a throwaway copy, made to break things or to check a proposed fix. The throwaway copy is never the source checkout.
example: A login button fails. The report says "change the handler in the login form to await the request; see the failing test at tests/login.spec". The fix was checked in a throwaway copy and saved as fixes/01-login.patch; the source stays untouched.
mode: all
trigger: a bug is found
kind: user-policy
source: user decision, act-as interview, 2026-10-13 (T3)
status: approved
review: user decision, 2026-10-13; user decision 2026-10-14 (scratch fix checks allowed)
extra: A called skill never applies a fix (TST-P04). The tester checks a fix in a throwaway copy itself.
