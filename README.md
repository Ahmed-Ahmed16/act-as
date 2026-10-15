# act-as

A Claude Code skill that puts a working role on the agent. Type
`/act-as tester` and the agent works as a tester until you say `stop acting`.

Each role is a file of rules. The rules live on cards, 1 rule per card, each
with its source: a book page, a standard, or a web page with the date read.

## Roles

| Role | State |
| --- | --- |
| tester | v1 |
| developer | v1.1 draft |
| manager | planned |

## What the tester does

- Finds bugs and proves each one with a check that fails.
- Never changes the code it tests. It writes a report, its tests, and a
  proposed fix as a patch file into a separate output folder.
- Treats a running site as read only until you approve 1 exact write.
- Loads only the cards that fit the step, through `tools/cards.py`.

## Install

Clone this repo into your Claude Code skills folder:

```
git clone <repo url> ~/.claude/skills/act-as
```

Python 3.8 or newer is needed for `tools/cards.py`. Without it, the agent
opens the cards by hand.

## Layout

- `SKILL.md`: the router and the loading rules.
- `roles/<role>/ROLE.md`: the role. `modes/`: 1 file per mode.
- `roles/<role>/cards/`: the rules. `cards/INDEX.md` lists them.
- `tools/cards.py`: the card gate. `tools/test_cards.py`: its tests.
- `SOURCES.md`: every source behind the cards.
- `THIRD-PARTY-NOTICES.md`: licences for copied material.

## Tests

```
python -m unittest discover -s tools -p test_cards.py
```
