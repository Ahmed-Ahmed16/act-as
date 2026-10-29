id: REV-P02
rule: Get the user's yes for the exact action before posting, commenting, reviewing, committing, pushing, merging or sending a draft message. When debate-review runs, use --dry-run only.
why: OWASP says a human should approve high impact actions before an agent takes them.
applies-when: Before any listed action or a debate-review run.
not-when: none
example: In invented PR 101 for owner/shop, the user approves a draft comment, but the reviewer waits for separate approval before posting it.
mode: all
trigger: Before a reviewer action is sent or committed
kind: source-advice
source: OWASP LLM06:2025 Excessive Agency, Prevention and Mitigation Strategies, Require user approval, https://genai.owasp.org/llmrisk/llm062025-excessive-agency/, read 2026-10-26
anchor: "require a human to approve high-impact actions before they are taken"
status: approved
review: drafted by gpt-6-luna effort max, 2026-10-26 (relay record); checked against the raw source by claude-sonnet-5-5, 2026-10-26, CHECK PASS: anchor verbatim in LLM06 item 6; supports human approval, the action list and dry run are project choices; approved by Ahmed 2026-10-26, as drafted
extra: OWASP supports human approval for high impact actions; the exact action list and --dry-run restriction are project choices. This checkout has no debate-review implementation, so support for that flag is not checked.
