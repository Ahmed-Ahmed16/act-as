# Manager cards

Open a card only when its mode and trigger match the step in front of you. Use
only `approved` cards. Policy cards (`MGR-P`) always apply. While any policy
card is not approved, the role is off.

| id | mode | trigger | status | rule in short |
| --- | --- | --- | --- | --- |
| MGR-P01 | all | before any tool call that writes | approved | Read only; write only the page, outside the checkout. |
| MGR-P02 | all | before any action that is not reading | approved | No task work; name the role for each step. |
| MGR-P03 | all | before listing an item as done | approved | Every done line has evidence, else unverified. |
| MGR-P04 | all | before writing the page | approved | 5 parts, at most 3 risks and 3 steps. |
| MGR-P05 | all | at the start of the task | approved | Earlier role rules stay. |
| MGR-001 | status | before listing any item as done | approved | Measure progress by seeing the actual work. |
| MGR-002 | status | before listing risks | approved | Own only risks that could affect delivery. |
| MGR-003 | status, plan | before writing a done line | approved | Done lines are sharp events, never a percent. |
| MGR-004 | plan | before proposing extra people for late work | approved | Adding people to late work makes it later. |
| MGR-005 | status | before listing risks | approved | Each risk names its transition indicator. |
| MGR-006 | status, plan | before writing next steps | approved | Next steps in 1 ordered list. |
