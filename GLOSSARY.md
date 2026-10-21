# act-as

act-as puts a working role on a coding agent, the way you put on a hat. This
page names the words the skill uses, so every file means the same thing by them.

## Roles and modes

**Role**:
A named set of rules the agent follows until the user says `stop acting`, for
example tester, developer or manager. It adds rules and never removes one.
_Avoid_: persona, agent, profile

**Mode**:
1 kind of task inside a role, with its own list of steps, for example the
tester's code, site and explore modes.
_Avoid_: workflow, flow

**Step**:
1 numbered item in a mode's step list. The router says how a step is named
when cards load.

**Badge**:
The role name shown in every todo list header while a role is on, for example
`**Todo (tester)**`.
_Avoid_: tag, label

**Stop acting**:
The words that take the role off from the next task on.

## Cards

**Card**:
1 rule with its source, in 1 file.
_Avoid_: rule file, prompt

**Policy card**:
A card that holds a decision the user made, for example "the tester never
fixes". It loads at the start of every task in the role.
_Avoid_: user rule

**Source card**:
A card that holds advice taken from a book, a standard or a web page, with the
chapter and page or the date read.
_Avoid_: book card, advice card

**Card gate**:
The check that lets a card load only when its status is approved and its mode
line fits the step.
_Avoid_: loader, filter

## Where work goes

**Checkout**:
The user's own copy of the repo under test. A tester leaves it exactly as it
found it.
_Avoid_: source tree, working copy

**Throwaway copy**:
A copy of the checkout, made only to run tests or try a fix, and then thrown
away.
_Avoid_: scratch copy, sandbox

**Output folder**:
The folder outside the checkout where a tester writes its report, tests and
proposed patches.

**Handoff**:
The output folder, seen as the thing passed on to the user, to a developer role
session, or to a delegate.

**Overlay**:
The user's private files (`SETUP.md`, `USE-CASES.md`) that add local detail to
a role. They are never in the public repo.

## Proving a role works

**Behaviour test**:
A test of a role judged by what the agent did (tool calls, git state, database
rows), never by what it said. Each case has a known pass and a known fail.
_Avoid_: proof run

**Switch test**:
A behaviour test where the user moves from 1 role to another in the same
session, for example tester to developer.

**Planted bug**:
A bug put into a throwaway copy on purpose, so a behaviour test can check what
the role does when it finds it.
_Avoid_: seeded bug

## Where the skill runs

**Host**:
The coding agent program that runs the skill, for example Claude Code or Codex.
_Avoid_: platform, client

**Precedence level**:
1 of 4 places a rule can come from: the global agent file, the project
`CLAUDE.md`, the repo's other agent files such as `AGENTS.md`, and the role.
The order between them is set in the router, `SKILL.md`.
_Avoid_: tier
