# Codex integration plan

Goal: the same act-as skill works in OpenAI Codex (CLI and IDE extension) as well as Claude Code. No fork of roles or cards.

Repo state read: main 86f3e89, `SKILL.md`.

## What Codex does today (sources read 2026-10-20)

1. Codex has native skills in the same `SKILL.md` format. It needs `name` and `description` in the frontmatter. Ours has both (`SKILL.md` lines 2 and 3).
   Source: https://learn.chatgpt.com/docs/build-skills.md (redirected from https://developers.openai.com/codex/skills), read 2026-10-20.
2. Codex finds skills in `$CWD/.agents/skills` (repo), `$HOME/.agents/skills` (user) and `/etc/codex/skills` (admin). Same source.
3. The user calls a skill with `$act-as` or the `/skills` picker. Same source.
4. To stop Codex picking the skill on its own, set `policy: allow_implicit_invocation: false` in `agents/openai.yaml` inside the skill folder. Explicit `$act-as` still works. Same source. This is the Codex twin of our `disable-model-invocation: true`.
5. Skills may ship scripts, so `tools/cards.py` can run as it does today. Same source.
6. Codex reads `AGENTS.md` (global in `~/.codex`, then project root down to the current folder; closer files win; 32 KiB default cap).
   Source: https://learn.chatgpt.com/docs/agent-configuration/agents-md.md (redirected from https://developers.openai.com/codex/guides/agents-md), read 2026-10-20.

Not verified: whether Codex ignores the unknown key `disable-model-invocation`. The page does not say. Test T3 below checks it.

## Smallest change

A. Add 1 new file `agents/openai.yaml`:
```yaml
policy:
  allow_implicit_invocation: false
```
Claude Code ignores this folder. Codex reads it.

B. Edit `SKILL.md` (router only, no role or card change), 3 small edits:
- Usage line: `/act-as tester` in Claude Code, `$act-as tester` in Codex.
- Precedence: global `CLAUDE.md` or `~/.codex/AGENTS.md`, then project `CLAUDE.md` or `AGENTS.md`, then the role. Same order, both tools named.
- Overlay: look in `~/.claude/act-as-local/`, and if absent `~/.agents/act-as-local/`.

C. README: an install line for Codex: clone into `~/.agents/skills/act-as` (Windows: `%USERPROFILE%\.agents\skills\act-as`).

Estimated size: about 20 changed lines. Well under 300.

Not changed: ROLE.md files, modes, cards, `tools/cards.py`. Roles mention Claude only where they cite `CLAUDE.md`; a later pass can check that list, but it needs your yes per role.

## Tests (each with a known pass and a known fail)

T1 Explicit load. In Codex, `$act-as tester` in a repo. Pass: the next todo header shows `(tester)` and `cards.py tester ... policy` ran with exit 0. Fail: no badge, or cards read by hand without saying Python is missing.
T2 No auto pick. In Codex, ask "test this function" without `$act-as`. Pass: no badge, no cards.py call. Fail: the skill loads anyway. Run once with `agents/openai.yaml` and once without it; the run without it is the known fail case if Codex then picks it.
T3 Unknown key. Codex lists act-as in `/skills` with the current frontmatter. Pass: listed. Fail: load error on `disable-model-invocation`.
T4 Role off on unreadable file. Rename `roles/tester/ROLE.md`, run `$act-as tester`. Pass: no badge, names the missing file, runs no task. Fail: any badge or task.
T5 No fix rule. As tester in Codex, find a seeded bug. Pass: `git status` clean after, patch file in the output folder. Fail: any change in the checkout.
T6 Claude Code regression. Same T1 and T4 in Claude Code after the change. Pass: same results as today.

T1 to T5 need Codex on your PC. Cloud threads cannot run Codex for you.

## Open for you
1. Yes or no to A, B and C as a draft PR.
2. Do you mean Codex CLI or IDE extension, or also Codex cloud tasks? Cloud tasks only see the repo, so they would need a repo skill copy in `.agents/skills`. Not planned unless you say so.
