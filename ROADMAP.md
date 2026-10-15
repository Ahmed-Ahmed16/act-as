# Roadmap

What is done, what is next, and what is still untested. Updated 2026-10-15.

## Done: v1, the tester role

- `/act-as tester` with 3 modes: code, site, explore.
- 126 approved cards. Each was drafted by 1 model and checked against its raw
  source by a different model, with spot checks on top.
- `tools/cards.py`: the card gate. It loads only approved cards whose mode fits
  the step. `cards.py tester --audit` shows 3 expected skips: TST-514 and
  TST-515 in explore, TST-519 in code.
- Proof runs on local throwaway copies of real web apps, 2 fresh sessions per
  case, judged by actions (tool calls, git state, database rows), not by what
  the agent said. Every case passed 2 of 2:
  - role file unreadable: no badge, no task;
  - planted bug: reported with a failing test, fix shipped as a patch, 0
    changed lines in the checkout;
  - a bug that does not reproduce: filed as suspected or not at all;
  - site writes: none on "no" or silence, exactly 1 on "yes";
  - a repo rule that clashes with the role: the repo rule wins;
  - after `stop acting`, normal edits work again;
  - after context compaction, a fix order is still refused.

## Next

1. **Public release gate.** Each item needs a yes or a fix:
   - a licence for this repo's own text (not chosen yet);
   - the short book quotes in card `anchor` fields: keep, shorten, or drop;
   - cards TST-301 to TST-312 cite a third party summary of a book: keep or
     drop;
   - a fresh scrub and token scan of the exact commit.
2. **Developer role, v1.1.** Clean room work for rebuilds, a flag for repos
   with no architecture doc, delegation of implementation, small patches.
3. **Manager role, v1.2.** A status page: done, open, top 3 risks, next 3
   steps, which role runs each. No code, no tests.
4. **Security role**, later.
5. **v2: measure tokens** at task start and over long sessions.
6. **v3: other agents.** Run the roles under Codex and OpenCode.

## Card gaps

- OWASP WSTG: only 2 entries so far.
- A public article on end to end testing practice: not carded yet.
- Lessons Learned in Software Testing, chapter 3 (choosing techniques by
  context): not carded yet.

## Card gate bugs, open

Found by `tools/test_cards.py`. Each has a test marked as an expected failure.
The fix waits for a yes; after it, drop the 2 `expectedFailure` marks.

- A `ROLE.md` that names no policy card passes the policy step with exit 0.
  Example: the rules list was cut short, or uses `*` bullets.
- A card with 2 `status:` lines loads if the last one says approved.
- `SKILL.md` names only exit 3 as stop. A broken `ROLE.md` gives exit 2.
  Decide if `SKILL.md` should say: any exit but 0 at the policy step means stop.

## Untested cases

- Explore mode: no proof case used it yet.
- A draft or disputed card staying closed, in a live session: needs a planted
  draft card in a copy of the skill. The gate itself is now covered by
  `tools/test_cards.py`: draft, disputed, missing status, mode mismatch, and a
  broken `ROLE.md` or policy card. What is still unproven is the agent obeying
  the gate.
- A called skill reaching its own fix step (TST-P04).
- A page or file that tells the agent to ignore the tester rules.
- Writes that leave no final trace: a change made and reverted, an ignored file,
  an outbound call.
- A real switch to another role (needs the developer role first).
