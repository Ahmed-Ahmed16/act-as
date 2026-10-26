# Reviewer cards

Open a card only when its mode and trigger match the step in front of you. Use
only `approved` cards. Policy cards (`REV-P`) always apply.

| id | mode | trigger | status | rule in short |
| --- | --- | --- | --- | --- |
| REV-P01 | all | Before touching checkout files or external systems | approved | Keep the checkout, running site and tracker read only. Write only the packet in a... |
| REV-P02 | all | Before a reviewer action is sent or committed | approved | Get the user's yes for the exact action before posting, commenting, reviewing,... |
| REV-P03 | all | When the reviewer is asked to fix code | approved | Never change code. If asked to fix something, name the developer role and direct... |
| REV-P04 | all | When the changed line count exceeds 300 | approved | Count the changed lines. If the count exceeds 300, stop with a short packet... |
| REV-P05 | all | When something was not checked | approved | Mark anything not inspected or not run as "not checked" and give the reason... |
| REV-P06 | all | When drafting the packet conclusion | approved | Do not write "safe to merge" in the packet. Do not add an overall line. |
| REV-P07 | all | When changed code handles money | approved | Flag money code for a separate Opus review. Do not perform that review, claim it... |
| REV-P08 | all | Before a packet is shown | approved | Show the packet only after the packet check passes. |
| REV-P09 | all | Before a reviewer mode starts | approved | For version 1, proceed only when composer.json is a valid JSON object and lists... |
| REV-P10 | all | Before the first comparison | approved | Record one comparison base at the start of the review. Use that same base for... |
| REV-P11 | all | When deciding whether a finding is must fix | approved | Mark a finding must fix only when code confirms the whole path to the harm. |

## Check map

Policy cards cover role rules. Every check listed below still needs a check card.

| check | card id or gap |
| --- | --- |
| `Q1` | `gap` |
| `Q2` | `gap` |
| `Q3` | `gap` |
| `Q4` | `gap` |
| `Q5` | `gap` |
| `Q6` | `gap` |
| `Q7` | `gap` |
| `Q8` | `gap` |
| `Q9` | `gap` |
| `Q10` | `gap` |
| `Q11` | `gap` |
| `Q12` | `gap` |
| `Q13` | `gap` |
| `Q14` | `gap` |
| `Q15` | `gap` |
| `Q16` | `gap` |
| `Q17` | `gap` |
| `Q18` | `gap` |
| `Q19` | `gap` |
| `Q20` | `gap` |
| `Q21` | `gap` |
| `Q22` | `gap` |
| `Q23` | `gap` |
| `Q24` | `gap` |
| `Q25` | `gap` |
| `Q26` | `gap` |
| `Q27` | `gap` |
| `Q28` | `gap` |
| `Q29` | `gap` |
| `Q30` | `gap` |
| `Q31` | `gap` |
| `Q32` | `gap` |
| `S1` | `gap` |
| `S2` | `gap` |
| `S3` | `gap` |
| `S4` | `gap` |
| `S5` | `gap` |
| `S6` | `gap` |
| `S7` | `gap` |
| `S8` | `gap` |
| `S9` | `gap` |
| `S10` | `gap` |
| `S11` | `gap` |
| `S12` | `gap` |
| `S13` | `gap` |
| `S14` | `gap` |
| `S15` | `gap` |
| `S16` | `gap` |
| `S17` | `gap` |
| `S18` | `gap` |
| `S19` | `gap` |
| `S20` | `gap` |
| `S21` | `gap` |
| `S22` | `gap` |
| `L1` | `gap` |
| `L5` | `gap` |
| `H1` | `gap` |
| `H2` | `gap` |
| `H3` | `gap` |
| `H4` | `gap` |
| `H5` | `gap` |
| `H6` | `gap` |
| `H7` | `gap` |
| `H8` | `gap` |
| `H9` | `gap` |
| `H10` | `gap` |
| `H11` | `gap` |
| `T1` | `gap` |
| `T2` | `gap` |
| `T3` | `gap` |
| `T4` | `gap` |
| `T5` | `gap` |
| `T6` | `gap` |
| `T7` | `gap` |
| `T8` | `gap` |

## Card gap list

- Q1
- Q2
- Q3
- Q4
- Q5
- Q6
- Q7
- Q8
- Q9
- Q10
- Q11
- Q12
- Q13
- Q14
- Q15
- Q16
- Q17
- Q18
- Q19
- Q20
- Q21
- Q22
- Q23
- Q24
- Q25
- Q26
- Q27
- Q28
- Q29
- Q30
- Q31
- Q32
- S1
- S2
- S3
- S4
- S5
- S6
- S7
- S8
- S9
- S10
- S11
- S12
- S13
- S14
- S15
- S16
- S17
- S18
- S19
- S20
- S21
- S22
- L1
- L5
- H1
- H2
- H3
- H4
- H5
- H6
- H7
- H8
- H9
- H10
- H11
- T1
- T2
- T3
- T4
- T5
- T6
- T7
- T8
