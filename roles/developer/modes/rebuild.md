# Developer mode: rebuild

A clean room rebuild of an existing product. The original's source is never
opened (`DEV-P05`).

## Steps

Before each step, run `cards.py developer rebuild <step number>`, for example
`cards.py developer rebuild 1`. The step number is the digit, never the step name.

1. **Gather inputs.** The spec, the user docs, and the running product's
   behaviour. Log each input in `REBUILD-INPUTS.md`: what it is, where it came
   from, when it was read. Reading a running product is read only
   (`DEV-P06`).
2. **Write the spec.** Turn the inputs into behaviours, each with an example.
   Done when every behaviour points at a logged input.
3. **Test first.** Write tests from the spec and see them fail (`DEV-P02`).
4. **Build** in patches within `DEV-P01`.
5. **Prove.** Run the tests; compare with the running product where it is
   safe to read.
6. **Hand back.** Report per the finish checklist.

## Finish checklist

- [ ] `REBUILD-INPUTS.md` path; no input is the original's source.
- [ ] Every behaviour: its test, failing then passing.
- [ ] Patch list with the changed lines of each.
