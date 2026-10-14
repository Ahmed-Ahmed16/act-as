# Applicability audit of the borrowed pstack items

Upstream: https://github.com/backnotprop/pstack at commit
`fce11a3442cfd59a21136de0b7010474c6a10ef5`, MIT, copyright 2026 Lauren Tan.
10 files copied byte for byte on 2026-10-13. Each was checked with
`git hash-object` against the upstream tree blob: 10 match, 0 mismatch. A
negative control (1 byte added to a copy) changed the hash, so the check can
fail. `SKILL.md` files are stored as `SKILL.upstream.md` so they do not register
as separate skills.

Every instruction was read against the tester rules TST-P01 to TST-P04 and the
user's approval gate. Where they clash, the override below wins.

| Item | Upstream line | Clash | Override for the tester |
| --- | --- | --- | --- |
| blast-radius | step 6, run it as an `arena`; "Write it through `unslop`"; `why` step 2 | `arena`, `unslop`, `why` are not installed | Skip those steps; say so in 1 line. |
| create-verification-skill | line 21, "fix that first (or report it precisely)" | fixing the checkout breaks TST-P01 | Report it precisely. Do not fix the checkout. |
| create-verification-skill | line 21, may create a missing asset as scaffolding | a write in the source checkout | Only inside a throwaway copy. |
| create-verification-skill | line 9 and 25, writes `<skills>/verify-<app>/` into the repo | a write in the source checkout | Write the generated skill to a separate folder outside the checkout, or ask the user first. |
| maintain-verification-skill | line 35, "keep it out of this PR" | the tester opens no PR | Record product gaps as bug reports only. |
| principle-build-the-lever | line 19, "Commit the lever" | commits need the user's yes | Save the lever as a file; commit only on the user's yes. |
| benchmark-checklist | none | none | none |
| principle-explain-the-number | none | none | none |
