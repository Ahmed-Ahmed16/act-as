# act-as: standing rules

These rules apply to every session that works on this repo.

## What act-as is
- A user typed skill: /act-as tester puts a working role on the agent until "stop acting". The role works like a hat: it adds rules, it never removes the user's own rules.
- Precedence, always: global CLAUDE.md, then project CLAUDE.md, then the repo's agent files, then the role.
- Layout: SKILL.md (router and loading rules), roles/<role>/ROLE.md, roles/<role>/modes/, roles/<role>/cards/ (1 rule per card) with cards/INDEX.md, tools/cards.py (the card gate) with tools/test_cards.py, SOURCES.md, THIRD-PARTY-NOTICES.md.

## Rules that never bend
- The tester never fixes the code it tests. It writes REPORT.md, its tests, and a proposed fix as a patch file into an output folder outside the checkout. It may check a fix in a throwaway copy. The checkout ends exactly as it started.
- A running site is read only until the user approves 1 exact write. A no always wins.
- If ROLE.md or a policy card cannot be read, the role is off: no badge, no task.
- Cards load only through tools/cards.py. A card loads only if its status is approved and its mode line fits.
- Every card cites a real source: a book with chapter and page, or a URL with the date read. Never write a rule from memory. Rules are in my own words; the only quote is a short anchor. If sources disagree, show both and I decide.
- A new card is drafted by 1 model and checked against the raw source by a different model before it can be approved. Never mark a card approved yourself.
- Patches stay small: a code change over 300 changed lines, tests not counted, stops and gets split.
- Role separation: the tester never fixes; the developer fixes, only in a separate session. DEV-P03 is never liftable.

## How to work with me
- Before you change a role or a card, say what changes and why, and wait for my yes.
- Judge a change by what an agent would do, not by what it would say. For any behaviour change, propose a test case with a known pass and a known fail.
- Say plainly what is verified and what is assumed. Unknown values are ___. Never invent a number, a page, or a source.
- CI (GitHub Actions tests) must be green before a merge.
- Commits use the GitHub noreply address only. My personal Gmail must never appear anywhere public.
- When you ask me to decide, explain each question in plain words: what goes wrong and the fix.
- ROADMAP.md holds done, next, card gaps, untested cases. Keep it current.

## How to write
- Everyday words, short sentences, one idea per sentence. A concrete example for each abstract idea.
- No em dashes, no en dashes, no hyphens joining words in prose. Numbers as digits.
- Lead with the answer. End a task with: what changed, what is still open, the next action.
