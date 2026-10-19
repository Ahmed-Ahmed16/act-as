# Tester mode: explore

A bug bash: exploring a running product to find what scripts miss. Run it on a
test or staging copy first; on a live site only when the user names it, and
then reads only (`TST-P03`).

## Steps

Before each step, run `cards.py tester explore <step number>`, for example
`cards.py tester explore 1`. The step number is the digit, never the step name.

1. **Charter.** Write 1 charter per session: the area and what to look for
   (`TST-212`). Time box it when running session based testing (`TST-213`).
   Give each charter its own account and session (`TST-014`).
2. **Explore** the working product (`TST-203`). Take notes as you go, so each
   problem can be reproduced (`TST-214`). AI features: test retrieved content,
   tool output and memory as injection inputs (`TST-023`), and look for leaks
   in tool arguments and retrieved chunks (`TST-025`). Before any step that
   could write, stop for `TST-P03`.
3. **Sort findings.** Put every finding in a bucket before writing any test
   (`TST-011`). Check each finding's real value against its screenshot
   (`TST-016`).
4. **Prove.** Write a repro test from the steps and check it fails on the
   bug's assertion (`TST-012`). A repro that passes means no bug: move it out
   of the bug folder (`TST-013`).
5. **Share.** Check videos and screenshots for secrets first (`TST-015`).
   Report per `TST-P01`, `TST-P02`, `TST-215`.

## Finish checklist

- [ ] Charter text and time box (or "none") quoted.
- [ ] Session notes file path.
- [ ] Every finding: its bucket, and either a failing repro test path or the
      label suspected.
- [ ] Every write: the user's approval or isolation evidence under `TST-P03` quoted; or "no writes made".
- [ ] Media checked for secrets before sharing: yes, with file list.
- [ ] Results counted: bugs, suspected, not bugs.
