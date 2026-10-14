id: TST-P04
rule: Run a called skill only up to its report step, as listed in ROLE.md section 4; skip any step that applies a fix.
why: Some installed skills end by fixing. diagnosing-bugs Phase 5 step 3 says "Apply the fix".
applies-when: calling any skill or tool from the tester role.
not-when: the user ends the role and asks for the fix in a new session.
example: diagnosing-bugs runs to "failing test written, seen failing", then the tester writes the bug report.
mode: all
trigger: before calling a skill
kind: user-policy
source: user decision 2026-10-13 (T3b); GPT-6 Astra plan debate 2026-10-13, checked against .agents/skills/diagnosing-bugs/SKILL.md Phase 5
status: approved
review: user decision, 2026-10-13
