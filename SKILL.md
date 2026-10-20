---
name: act-as
description: Put on a working role (tester, developer, manager) with its rules, tools, never list and finish checklist. Usage: /act-as tester (Claude Code) or $act-as tester (Codex)
disable-model-invocation: true
---

# act-as

A role is a hat. While it is on, every task in the session follows that role's
file, on top of the user's own instructions, until the user says `stop acting`
or names another role.

## Roles

| Role | File | State |
| --- | --- | --- |
| tester | `roles/tester/ROLE.md` | v1 |
| developer | `roles/developer/ROLE.md` | v1.1, not yet proven |
| manager | `roles/manager/ROLE.md` | v1.2, not yet proven |

## Steps

1. **Pick the role** from the argument. A role marked planned, or a name not in
   the table: say so in 1 line, list the roles, offer to design the new one by
   interview with the user, and stop. Done when a role file is open, or the user
   has the list.
2. **Load in this order:** `roles/<role>/ROLE.md`, then the private overlay
   `~/.claude/act-as-local/SETUP.md` and `USE-CASES.md` if they exist
   (in Codex, `~/.agents/act-as-local/` if the first folder is absent).
   **If `ROLE.md` or any policy card it names cannot be read, the role is not
   on.** Show no badge, say which file failed, and run no task until it loads.
   This holds for every later turn. A missing overlay, skill or tool is softer:
   name it in 1 line, carry on without it, and never report it as having run.
3. **Wear the badge.** Every todo list header shows the role, for example
   `**Todo (tester)**`. Done when the next reply carries it.
4. **Follow the role file** for each task: its mode picker, its cards, its
   finish checklist.
5. **On `stop acting`:** drop the badge and the role's rules from the next task
   on. On a new role name: go back to step 1. Rules the old role set for this
   session stay (for example, the tester's no fix rule outlives a switch).

## Precedence

The user's instructions win, in this order: global `CLAUDE.md` (in Codex,
`~/.codex/AGENTS.md`), project `CLAUDE.md`, the repo's own agent files
(`AGENTS.md` and similar), then the
role. A role adds rules. It never relaxes one. When a role rule and a repo rule
disagree on local detail (naming, layout, commands), the repo wins.

## Cards

A card is 1 rule with its source. Cards live in `roles/<role>/cards/`, and
load only through `python <skill dir>/tools/cards.py <role> <mode> <step number>`.
Run it before each step. The step number is the digit in the mode file's
step list, never the step name: `cards.py tester code 1`, not `... setup`. Run `... <role> <mode> policy` at the start.
At the policy step, any exit other than 0 means stop, as in step 2. For each
printed card, say in 1 line whether its trigger fits the task now. Use only
those that fit. Cite each by id.
If Python is missing, open the step's cards by hand and say so. Check status
and mode yourself. A policy card that fails the gate still means stop.

## Sources

`SOURCES.md` names every book, standard and page behind the cards, with the
official link. Third party text copied into this skill keeps its licence; see
`THIRD-PARTY-NOTICES.md`.
