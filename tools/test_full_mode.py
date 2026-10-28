import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
# Step 2 from c1aab50, saved before filling full mode for ticket 39.
EXPECTED_SPLIT_STEP = b"""2. **Split step.** Run `cards.py reviewer full 2` first. Run this step only
   when a full run's size line is `fail` and the user did not say
   "review it anyway". Stop the full review at size.

   a. Use this full run's own packet folder and saved counter run at
      `runs/size-count.json`. Never use a size run folder.
   b. List entry points that really load: routes, commands, scheduled jobs
      and screens. For example, `routes/garden.php` loads the seed screen.
      Cards: `REV-121`, `REV-123`, `REV-124`, `REV-125`, `REV-126`.
   c. Trace changed files to those entry points. Set shared files aside.
      For example, 2 routes may both use `SeedStore`.
      Cards: `REV-122`.
   d. Form groups by entry point. Name a cleanup group
      `no behaviour change: remove unused seed helpers`.
      Cards: `REV-127`, `REV-128`.
   e. Run `python tools/split_plan.py hunks --repo <checkout> --base <base> --head <head> --packet <packet folder>`.
      Place every piece. Cut a hunk into line ranges when it holds 2
      behaviours, including tests and generated copies. Link each test or
      generated piece to its changed source pieces, or to an unchanged
      file at the frozen head. Record the command used to check that file.
      A test with neither goes to `unplaced`. Give generated pieces a
      rebuild command. For example, `f1h1:L1-L8` goes with the seed screen.
      Cards: `REV-129`, `REV-130`, `REV-131`.
   f. Read language hunks with `hunks --show <hunk id>` and the same frozen
      arguments. Record each key's `shape`, `key`, `pieces`, `page` and
      `part`. Record each page with its source pieces. In `keys_check`,
      record `how` you read them and how many distinct keys you found as
      `keys_found`. For example, key `Plant` belongs to page `garden` and
      part `seed`. A text only unit needs a named existing screen. Record
      the command used to read it on the default branch. The packet says:
      `Translations by page: not checked: PR over the cap, split it first`
   g. Write `needs` and order the groups. Break any loop and record it in
      `loop_notes`. Put work no entry point reaches in `unplaced`, as a
      lead to follow. For example, move a shared type into the first group.
      Cards: `REV-132`, `REV-133`, `REV-134`, `REV-135`.
   h. Cut group 1 into parts of 300 counted lines or fewer. Mark pieces
      `money`, `access`, `deletion` or `unsure`. A part may stay over only
      for 1 new class or function. Record its declaration and closing
      lines. Search the base for its name and search the diff's deleted
      lines for it. For every other counted piece in that part, record
      a check that the symbol needs it. Move unrelated work out.
      Cards: `REV-136`, `REV-137`.
   i. Read the default branch, or the evidence that `main` exists, and
      record `main`. Read CI workflow files at the frozen head with GET
      calls. Record their `on:` text as read. If a file cannot be read,
      say `unreadable`. Do not guess what its filters do.
      Cards: `REV-138`, `REV-139`.
   j. Write `split-input.json`. Run `python tools/split_plan.py build <packet folder>`,
      then `python tools/short_packet.py <packet folder> --repo-name <owner/repo> --pr <number> --default <branch>@<40 hex> --date <YYYY-MM-DD>`.
      Run `python tools/packet_check.py <packet folder>` and quote its
      output. Never copy the `hunks` screen output into `runs/`. A pass
      proves shape and consistency. It does not prove recorded facts.
      Cards: `REV-140`.

"""


class FullModeTextTests(unittest.TestCase):
    def setUp(self):
        self.raw = (ROOT / 'roles/reviewer/modes/full.md').read_bytes()
        self.text = self.raw.decode('utf-8')

    def test_steps_are_exactly_1_to_10_in_order(self):
        steps = re.findall(r'^\d.*$', self.text, re.MULTILINE)
        self.assertEqual([line.split('. ', 1)[0] for line in steps],
                         [str(number) for number in range(1, 11)])
        for number, line in enumerate(steps, 1):
            with self.subTest(step=number):
                self.assertTrue(line.startswith(f'{number}. **'), line)

    def test_split_then_business_security_health_run_in_order(self):
        positions = [self.text.index('2. **Split step.**')]
        for number, name in [(4, 'Business'), (5, 'Security'), (6, 'Health')]:
            with self.subTest(step=number):
                match = re.search(rf'^{number}\. \*\*{name}\.\*\*', self.text, re.MULTILINE)
                self.assertIsNotNone(match)
                positions.append(match.start())
        self.assertEqual(positions, sorted(positions))

    def test_split_step_matches_c1aab50_bytes(self):
        match = re.search(rb'^2\. .*?(?=^\d+\. |^## |\Z)',
                          self.raw, re.MULTILINE | re.DOTALL)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(), EXPECTED_SPLIT_STEP)

    def test_full_run_names_required_tools_and_override_evidence(self):
        for token in ['override_parts.py', 'laravel_line.py', 'review it anyway',
                      'business-risk-notes', 'F-']:
            with self.subTest(token=token):
                self.assertIn(token, self.text)

    def test_finish_checklist_heading_exists(self):
        self.assertIn('## Finish checklist', self.text.splitlines())

    def test_merge_safety_phrase_is_only_used_with_never(self):
        for match in re.finditer('safe to merge', self.text):
            with self.subTest(line=self.text.count('\n', 0, match.start()) + 1):
                prefix = self.text[self.text.rfind('\n', 0, match.start()) + 1:match.start()]
                self.assertRegex(prefix, r'\b[Nn]ever\b')

    def test_full_mode_contains_no_ticket_placeholders(self):
        for placeholder in ['Filled by ticket 39', 'scaffold']:
            with self.subTest(placeholder=placeholder):
                self.assertNotIn(placeholder, self.text)


if __name__ == '__main__':
    unittest.main()
