# Release checklist

The public release gate. Every item needs a yes or a fix before the repo goes
public. Each decision is the owner's; nothing here is chosen yet.

## Decisions

- [x] **Licence** for this repo's own text and code: `MIT`, in `LICENSE`.
  The borrowed pstack files keep their MIT licence either way; see
  `THIRD-PARTY-NOTICES.md`.
- [x] **Short book quotes** in card `anchor` fields: keep, shorten, or drop.
  Decision: `keep`, 2026-10-15.
- [ ] **Cards TST-301 to TST-312** cite a third party summary of
  *More Agile Testing*, not the book (see `SOURCES.md`): keep or drop.
  Decision: `___`.

## Scan of the exact commit

Run this on the commit that will be published, not on a working tree:

```
python tools/scrub.py . --commit <sha>
```

- Exit 0 and `total: 0 findings`: clean.
- Exit 1: each finding shows path, line and kind. The value is never printed.
  Fix it, make a new commit, and scan that new commit.
- Exit 2: bad arguments or an unknown commit.

It checks for keys and tokens, private keys, secret assignments, private
machine paths (a Windows user folder, a work projects folder, or a Linux or
Mac home folder), and email addresses. `.git` is skipped in a folder scan; a
commit scan reads only the commit's own files.

It does not know the names of people, machines or companies. Read the
published files for those by hand.

- [ ] Names checked by hand. Result: `___`.

- [ ] Commit scanned: `___`. Result: `___`.
- [ ] `python -m unittest discover -s tools -p "test_*.py"` passes on that
  commit.
