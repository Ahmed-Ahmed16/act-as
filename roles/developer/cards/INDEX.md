# Developer cards

Open a card only when its mode and trigger match the step in front of you. Use
only `approved` cards. Policy cards (`DEV-P`) always apply. While any policy
card is not approved, the role is off.

| id | mode | trigger | status | rule in short |
| --- | --- | --- | --- | --- |
| DEV-P01 | all | before writing code, and before handing back a diff | approved | A code change over 300 changed lines, tests not counted, stops and gets split. |
| DEV-P02 | all | before writing a fix or feature, and before reporting it done | approved | A failing test before a fix, passing tests after, runs quoted. |
| DEV-P03 | all | before the first change to the checkout | approved | If the tester role was on in this session, change nothing in the checkout. |
| DEV-P04 | all | before the first change to a repo | approved | No architecture doc: say so and name the files the change touches. |
| DEV-P05 | all | before reading any input for a rebuild | approved | Never open the original's source; log every input. |
| DEV-P06 | all | before any action outside the checkout | approved | Ask for the exact action and wait for a yes before commit, push, deploy, install or site write. |

No mode cards yet. Card gaps are listed in `ROADMAP.md`.
