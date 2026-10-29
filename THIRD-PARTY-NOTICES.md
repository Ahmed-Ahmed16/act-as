# Third party notices

## What this file covers

This repo's own text and code are MIT (see `LICENSE`). Text we borrow keeps its
own licence, and the MIT licence of this repo does not cover it.

Reviewer cards say things in their own words. A card may hold a short quotation
(under 15 words) in its `anchor:` line or in another line. The page it comes
from is named in `source:` or in the line itself, and has an entry below with
its credit, its licence and a change note.

Some pages are never quoted. This is a choice of this project, not a claim that
the licence forbids it. Those pages are the Git documentation (GPL 2.0), the
Linux kernel documentation (GPL 2.0 only), the OWASP projects (CC BY SA 4.0),
laravel-translator (Prosperity Public License 3.0.0), the Unicode charts and
reports (Unicode Terms of Use) and the GNU coreutils manual (GNU FDL 1.3 or
later). Cards cite them by URL or in our own words.

Where we found no licence on a page, the entry says `___`. For a few of those
pages the maintainer chose to keep a short quotation, with credit, and the entry
says so. For the rest, cards cite the page only.

Open question, `___`: whether our own wording of a CC BY SA page is an
adaptation that must carry share alike. A passing licence check does not
answer it.

## pstack

Files under `roles/tester/borrowed/pstack/` are copied unchanged from
https://github.com/backnotprop/pstack at commit
`fce11a3442cfd59a21136de0b7010474c6a10ef5`. MIT License, copyright (c) 2026
Lauren Tan. The full licence text is in `roles/tester/borrowed/pstack/LICENSE`.
Only `SKILL.md` was renamed to `SKILL.upstream.md`; the content is unchanged.

Reviewer cards REV-417, REV-502, REV-505 and REV-510 cite the same project at
commit `f51fdeba3d803ef90e4eaa4a95ffb4e76008ab37`, MIT, same copyright line
(read 2026-10-28).

## Rules paraphrased from other projects

Cards that paraphrase rules from these projects cite the file they came from.
No text is copied from them.

- storytold/photocraft: MIT or Apache 2.0.
- tester-army/e2e: Apache 2.0.

## Sources cited by the reviewer cards

### Google engineering practices
Key: google
Credit: Google, https://google.github.io/eng-practices/
Licence: CC BY 3.0, https://creativecommons.org/licenses/by/3.0/
Evidence: https://raw.githubusercontent.com/google/eng-practices/3bb3ec25b3b0199f4940b1aa75f0ac5c5753301c/LICENSE read 2026-10-28, commit 3bb3ec25b3b0199f4940b1aa75f0ac5c5753301c; README.md lines 27 to 31 say the documents are licensed CC BY 3.0; no copyright line is shown
Changes: short phrases quoted as written where a card does; all other text is ours, paraphrased and shortened.
Use: short quotation under 15 words, with credit
Notice: This material is licensed under CC BY 3.0 (https://creativecommons.org/licenses/by/3.0/). We changed it: short phrases are quoted, the rest is in our own words. The licensor gives no warranty. Source: https://google.github.io/eng-practices/
Cards: REV-109, REV-110, REV-111, REV-112, REV-113, REV-127, REV-128, REV-129, REV-131, REV-132, REV-133, REV-136, REV-137, REV-140, REV-212, REV-214, REV-221, REV-303, REV-410, REV-414, REV-425, REV-442, REV-447, REV-501, REV-504, REV-507, REV-508, REV-509, REV-510, REV-515, REV-516, REV-519, REV-520, REV-521, REV-522, REV-523, REV-P03, REV-P04

### GitHub Docs
Key: github-docs
Credit: GitHub Inc., https://docs.github.com/ (documentation content; the site code is MIT and not used)
Licence: CC BY 4.0, https://creativecommons.org/licenses/by/4.0/
Evidence: https://raw.githubusercontent.com/github/docs/285a28f284a1ec002904a394349a688a27f40f8f/LICENSE read 2026-10-28, commit 285a28f284a1ec002904a394349a688a27f40f8f; README.md lines 35 to 38 give CC BY 4.0 for the content folders
Changes: short phrases quoted as written where a card does; all other text is ours, paraphrased and shortened.
Use: short quotation under 15 words, with credit
Notice: GitHub Inc. (c) 2026 (page footer of docs.github.com). This material is licensed under CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). We changed it: short phrases are quoted, the rest is in our own words. The licensor gives no warranty. Source: https://docs.github.com/
Cards: REV-102, REV-114, REV-115, REV-116, REV-117, REV-134, REV-138, REV-139, REV-204, REV-209, REV-411

### Laravel documentation
Key: laravel-docs
Credit: Taylor Otwell, https://laravel.com/docs/
Licence: MIT, https://opensource.org/license/mit
Evidence: https://raw.githubusercontent.com/laravel/docs/5b8c610735c8af96a3bda4e37a820b27dc40aee9/license.md read 2026-10-28, commit 5b8c610735c8af96a3bda4e37a820b27dc40aee9
Changes: short phrases quoted as written where a card does; all other text is ours, paraphrased and shortened.
Use: short quotation under 15 words, with credit
Notice: Copyright (c) Taylor Otwell. Licence text: MIT (the full text is under "Licence texts" below).
Cards: REV-121, REV-122, REV-123, REV-124, REV-125, REV-126, REV-132, REV-302, REV-304, REV-305, REV-306, REV-307, REV-308, REV-309, REV-310, REV-311, REV-313, REV-314, REV-315, REV-316, REV-320, REV-321, REV-322, REV-323, REV-328, REV-332, REV-333, REV-338, REV-356, REV-357, REV-407, REV-409, REV-431, REV-432, REV-433, REV-435, REV-436, REV-437, REV-438, REV-439, REV-440, REV-445, REV-601, REV-602, REV-603, REV-604, REV-607, REV-609, REV-610, REV-611, REV-612, REV-613

### Laravel framework source
Key: laravel-framework
Credit: Taylor Otwell, https://github.com/laravel/framework/
Licence: MIT, https://opensource.org/license/mit
Evidence: https://raw.githubusercontent.com/laravel/framework/e130a2e7f3e10e7d983ae5865389c628b4ea43bf/LICENSE.md read 2026-10-28, commit e130a2e7f3e10e7d983ae5865389c628b4ea43bf
Changes: short phrases quoted as written where a card does; all other text is ours, paraphrased and shortened.
Use: short quotation under 15 words, with credit
Notice: Copyright (c) Taylor Otwell. Licence text: MIT (the full text is under "Licence texts" below).
Cards: REV-601, REV-604

### OWASP Cheat Sheet Series
Key: owasp-cs
Credit: Cheat Sheets Series Team, https://cheatsheetseries.owasp.org/
Licence: CC BY SA 4.0, https://creativecommons.org/licenses/by-sa/4.0/
Evidence: https://raw.githubusercontent.com/OWASP/CheatSheetSeries/920293be317721982fa50324a6f26af3f29dc45e/LICENSE.md read 2026-10-28, commit 920293be317721982fa50324a6f26af3f29dc45e; page footer of https://cheatsheetseries.owasp.org/cheatsheets/Laravel_Cheat_Sheet.html (Last-Modified Wed, 28 Oct 2026 11:46:56 GMT) names Cheat Sheets Series Team and CC BY SA 4.0
Changes: nothing is quoted; every rule is in our own words, paraphrased and shortened.
Use: no quotes, own words
Notice: This material is licensed under CC BY SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/). We changed it: nothing is quoted, the rest is in our own words. The licensor gives no warranty. Source: https://cheatsheetseries.owasp.org/
Cards: REV-301, REV-304, REV-305, REV-306, REV-308, REV-309, REV-311, REV-312, REV-313, REV-314, REV-315, REV-316, REV-317, REV-319, REV-320, REV-323, REV-324, REV-325, REV-326, REV-327, REV-329, REV-330, REV-331, REV-334, REV-335, REV-336, REV-337, REV-338, REV-340, REV-341, REV-342, REV-343, REV-344, REV-345, REV-351, REV-352, REV-353, REV-354, REV-356, REV-357, REV-P01, REV-P05

### OWASP API Security Top 10
Key: owasp-api
Credit: OWASP API Security Project team, https://owasp.org/API-Security/
Licence: CC BY SA 4.0, https://creativecommons.org/licenses/by-sa/4.0/
Evidence: https://raw.githubusercontent.com/OWASP/API-Security/33cea37b2ffde3e2e62f6b5d79a029a22a846633/LICENSE read 2026-10-28, commit 33cea37b2ffde3e2e62f6b5d79a029a22a846633; page footer (Last-Modified Tue, 22 Sep 2026 14:25:40 GMT) shows a 2023 copyright line and no licence words
Changes: nothing is quoted; every rule is in our own words, paraphrased and shortened.
Use: no quotes, own words
Notice: Copyright 2023 OWASP API Security Project team. This material is licensed under CC BY SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/). We changed it: nothing is quoted, the rest is in our own words. The licensor gives no warranty. Source: https://owasp.org/API-Security/
Cards: REV-301, REV-303, REV-307, REV-337, REV-338, REV-339

### OWASP Top 10
Key: owasp-top10
Credit: OWASP Top 10 Team, https://owasp.org/Top10/
Licence: CC BY SA 4.0, https://creativecommons.org/licenses/by-sa/4.0/
Evidence: https://raw.githubusercontent.com/OWASP/Top10/3a31f35346c3f4e90f350395124382fa53af2afe/LICENSE read 2026-10-28, commit 3a31f35346c3f4e90f350395124382fa53af2afe; the 2021 page footer (Last-Modified Thu, 24 Sep 2026 14:12:52 GMT) says CC BY 3.0 while the repo says CC BY SA 4.0; which governs is ___; the stricter is used
Changes: nothing is quoted; every rule is in our own words, paraphrased and shortened.
Use: no quotes, own words
Notice: Copyright 2021 to 2025 OWASP Top 10 Team. The repo is licensed CC BY SA 4.0; the 2021 page footer says CC BY 3.0 (which governs is ___; the stricter is used). This material is licensed under CC BY SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/). We changed it: nothing is quoted, the rest is in our own words. The licensor gives no warranty. Source: https://owasp.org/Top10/
Cards: REV-346, REV-347, REV-349

### OWASP community pages
Key: owasp-community
Credit: OWASP Foundation, https://owasp.org/www-community/
Licence: CC BY SA 4.0, https://creativecommons.org/licenses/by-sa/4.0/
Evidence: https://owasp.org/www-community/attacks/CSV_Injection read 2026-10-28, Last-Modified Tue, 27 Oct 2026 16:31:20 GMT; the page says all content on the site is CC BY SA 4.0
Changes: nothing is quoted; every rule is in our own words, paraphrased and shortened.
Use: no quotes, own words
Notice: Copyright 2026 OWASP Foundation, Inc. This material is licensed under CC BY SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/). We changed it: nothing is quoted, the rest is in our own words. The licensor gives no warranty. Source: https://owasp.org/www-community/
Cards: REV-318

### OWASP GenAI Security Project
Key: owasp-genai
Credit: OWASP Foundation, https://genai.owasp.org/
Licence: CC BY SA 4.0, https://creativecommons.org/licenses/by-sa/4.0/
Evidence: https://genai.owasp.org/llmrisk/llm062025-excessive-agency/ read 2026-10-28, Last-Modified Wed, 28 Oct 2026 16:08:20 GMT; same footer sentence as the community pages; the repo licence file was not read again (___)
Changes: nothing is quoted; every rule is in our own words, paraphrased and shortened.
Use: no quotes, own words
Notice: Copyright 2025 OWASP Foundation, Inc. This material is licensed under CC BY SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/). We changed it: nothing is quoted, the rest is in our own words. The licensor gives no warranty. Source: https://genai.owasp.org/
Cards: REV-P02

### PHPUnit documentation
Key: phpunit
Credit: Sebastian Bergmann, https://docs.phpunit.de/
Licence: CC BY 3.0, https://creativecommons.org/licenses/by/3.0/
Evidence: https://docs.phpunit.de/en/12.5/copyright.html read 2026-10-28, Last-Modified Tue, 20 Oct 2026 14:53:12 GMT, ETag W/"308e0e7362c679badab2a4818ed01c0a"
Changes: short phrases quoted as written where a card does; all other text is ours, paraphrased and shortened.
Use: short quotation under 15 words, with credit
Notice: Copyright (c) 2025 Sebastian Bergmann. This material is licensed under CC BY 3.0 (https://creativecommons.org/licenses/by/3.0/). We changed it: short phrases are quoted, the rest is in our own words. The licensor gives no warranty. Source: https://docs.phpunit.de/
Cards: REV-411, REV-426

### PHP manual
Key: php-manual
Credit: PHP Documentation Group, https://www.php.net/manual/
Licence: CC BY 3.0 or later, https://creativecommons.org/licenses/by/3.0/
Evidence: https://www.php.net/manual/en/copyright.php read 2026-10-28, Last-Modified Wed, 28 Oct 2026 16:07:57 GMT
Changes: short phrases quoted as written where a card does; all other text is ours, paraphrased and shortened.
Use: short quotation under 15 words, with credit
Notice: Copyright 1997 to 2026 by the PHP Documentation Group. This material is licensed under CC BY 3.0 or later (https://creativecommons.org/licenses/by/3.0/). We changed it: short phrases are quoted, the rest is in our own words. The licensor gives no warranty. Source: https://www.php.net/manual/
Cards: REV-335, REV-445, REV-607, REV-608

### Composer documentation
Key: composer
Credit: Nils Adermann, Jordi Boggiano, https://getcomposer.org/doc/
Licence: MIT, https://opensource.org/license/mit
Evidence: https://raw.githubusercontent.com/composer/composer/aa438b3f3941006330d5dd3af4890a382383fe0f/LICENSE read 2026-10-28, commit aa438b3f3941006330d5dd3af4890a382383fe0f; the cited pages are that repo's doc/ files; that the licence covers them is assumed (___)
Changes: short phrases quoted as written where a card does; all other text is ours, paraphrased and shortened.
Use: short quotation under 15 words, with credit
Notice: Copyright (c) Nils Adermann, Jordi Boggiano. Licence text: MIT (the full text is under "Licence texts" below).
Cards: REV-346, REV-347, REV-348, REV-411, REV-P09

### Git documentation
Key: git-docs
Credit: Git project, https://git-scm.com/docs/
Licence: GPL 2.0, https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
Evidence: https://raw.githubusercontent.com/git/git/8d1b215c01512b9658d4525c54ff9b9245f9a7e8/COPYING read 2026-10-28, commit 8d1b215c01512b9658d4525c54ff9b9245f9a7e8; the git-scm.com doc pages show no licence text
Changes: nothing is quoted; cards cite the page by URL or say the point in our own words, paraphrased and shortened.
Use: URL only, nothing copied
Notice: nothing copied. Cited by URL or in our own words; this is the project's choice, not a claim that the licence forbids quoting.
Cards: REV-101, REV-102, REV-106, REV-114, REV-116, REV-117, REV-130, REV-206, REV-208, REV-413, REV-446, REV-P10

### Linux kernel documentation
Key: linux
Credit: Linux kernel contributors, https://www.kernel.org/doc/
Licence: GPL 2.0 only, https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
Evidence: https://raw.githubusercontent.com/torvalds/linux/65ba8f34ec886ec72b2c07ddc8cf3d815c32869d/COPYING read 2026-10-28, commit 65ba8f34ec886ec72b2c07ddc8cf3d815c32869d; COPYING opens SPDX GPL-2.0 WITH Linux-syscall-note; the doc pages show no licence statement
Changes: nothing is quoted; cards cite the page by URL or say the point in our own words, paraphrased and shortened.
Use: URL only, nothing copied
Notice: nothing copied. Cited by URL or in our own words; this is the project's choice, not a claim that the licence forbids quoting.
Cards: REV-133, REV-516

### pstack
Key: pstack
Credit: Lauren Tan, https://github.com/backnotprop/pstack
Licence: MIT, https://opensource.org/license/mit
Evidence: https://raw.githubusercontent.com/backnotprop/pstack/f51fdeba3d803ef90e4eaa4a95ffb4e76008ab37/LICENSE read 2026-10-28, commit f51fdeba3d803ef90e4eaa4a95ffb4e76008ab37
Changes: short phrases quoted as written where a card does; all other text is ours, paraphrased and shortened.
Use: short quotation under 15 words, with credit
Notice: Copyright (c) 2026 Lauren Tan. Licence text: MIT (the full text is under "Licence texts" below).
Cards: REV-417, REV-502, REV-505, REV-510

### jscpd
Key: jscpd
Credit: Andrey Kucherenko, https://github.com/kucherenko/jscpd
Licence: MIT, https://opensource.org/license/mit
Evidence: https://raw.githubusercontent.com/kucherenko/jscpd/db415b5d7cc34d72a324fe5eae2147646dc3558b/LICENSE read 2026-10-28, commit db415b5d7cc34d72a324fe5eae2147646dc3558b; that commit is tag v5.4.2, the tag the cards cite
Changes: short phrases quoted as written where a card does; all other text is ours, paraphrased and shortened.
Use: short quotation under 15 words, with credit
Notice: Copyright (c) 2013 to 2024 Andrey Kucherenko. Licence text: MIT (the full text is under "Licence texts" below).
Cards: REV-401, REV-402, REV-403

### Larastan
Key: larastan
Credit: Can Vural, Nuno Maduro, https://github.com/larastan/larastan
Licence: MIT, https://opensource.org/license/mit
Evidence: https://raw.githubusercontent.com/larastan/larastan/6ebed6b32e9f7c4b090bd397fbf68ece7da9287c/LICENSE.md read 2026-10-28, commit 6ebed6b32e9f7c4b090bd397fbf68ece7da9287c
Changes: short phrases quoted as written where a card does; all other text is ours, paraphrased and shortened.
Use: short quotation under 15 words, with credit
Notice: Copyright (c) Can Vural, Nuno Maduro (the email addresses in the source file are left out). Licence text: MIT (the full text is under "Licence texts" below).
Cards: REV-418

### PHPStan source
Key: phpstan-src
Credit: Ondřej Mirtes, PHPStan s.r.o., https://github.com/phpstan/phpstan-src
Licence: MIT, https://opensource.org/license/mit
Evidence: https://raw.githubusercontent.com/phpstan/phpstan-src/7c9daa4ca480f7407d3ce01754ea3a9a6d9b480c/LICENSE read 2026-10-28, commit 7c9daa4ca480f7407d3ce01754ea3a9a6d9b480c
Changes: short phrases quoted as written where a card does; all other text is ours, paraphrased and shortened.
Use: short quotation under 15 words, with credit
Notice: Copyright (c) 2016 Ondřej Mirtes. Copyright (c) 2025 PHPStan s.r.o. Licence text: MIT (the full text is under "Licence texts" below).
Cards: REV-416, REV-418

### PHPStan documentation
Key: phpstan-docs
Credit: PHPStan s.r.o., https://phpstan.org/
Licence: ___
Evidence: https://phpstan.org/user-guide/rule-levels read 2026-10-28, Last-Modified Wed, 28 Oct 2026 11:01:53 GMT; footer shows 2026 PHPStan s.r.o. and no licence words; the code licence does not settle the docs
Changes: short phrases quoted as written, under 15 words; all other text is ours, paraphrased and shortened.
Use: short quotation under 15 words, licence ___
Notice: licence ___ (none found). Only a short quotation is kept, with credit.
Cards: REV-216, REV-218, REV-416, REV-418, REV-421

### PHPMD
Key: phpmd
Credit: Manuel Pichler, https://phpmd.org/
Licence: BSD 3 Clause, https://opensource.org/license/bsd-3-clause
Evidence: https://raw.githubusercontent.com/phpmd/phpmd/bc69f061235285e5112f644d8e709b0f5cba5dcc/LICENSE read 2026-10-28, commit bc69f061235285e5112f644d8e709b0f5cba5dcc; https://phpmd.org/ (Last-Modified Sat, 17 Feb 2024 17:53:39 GMT) also says BSD 3 Clause
Changes: short phrases quoted as written where a card does; all other text is ours, paraphrased and shortened.
Use: short quotation under 15 words, with credit
Notice: Copyright (c) 2008, Manuel Pichler. Licence text: BSD 3 Clause (the full text is under "Licence texts" below).
Cards: REV-404, REV-405, REV-415

### Infection
Key: infection
Credit: Maks Rafalko, https://infection.github.io/
Licence: BSD 3 Clause, https://opensource.org/license/bsd-3-clause
Evidence: https://raw.githubusercontent.com/infection/infection/552535cba6fd93976ceeb601a0c0c67746bff071/LICENSE read 2026-10-28, commit 552535cba6fd93976ceeb601a0c0c67746bff071; https://infection.github.io/ (Last-Modified Wed, 14 Oct 2026 09:58:05 GMT) also says BSD 3 Clause
Changes: short phrases quoted as written where a card does; all other text is ours, paraphrased and shortened.
Use: short quotation under 15 words, with credit
Notice: Copyright (c) 2017, Maks Rafalko. Licence text: BSD 3 Clause (the full text is under "Licence texts" below).
Cards: REV-425, REV-521

### laravel-translator
Key: translator
Credit: Quentin Gabriele, https://github.com/ElegantEngineeringTech/laravel-translator
Licence: Prosperity Public License 3.0.0, https://prosperitylicense.com/versions/3.0.0
Evidence: https://raw.githubusercontent.com/ElegantEngineeringTech/laravel-translator/2b3a42abb26c03c605ac3510a4814af64e65ba4d/LICENSE.md read 2026-10-28, commit 2b3a42abb26c03c605ac3510a4814af64e65ba4d
Changes: nothing is quoted; cards cite the page by URL or say the point in our own words, paraphrased and shortened.
Use: URL only, nothing copied
Notice: nothing copied. Cited by URL or in our own words; this is the project's choice, not a claim that the licence forbids quoting.
Cards: REV-602, REV-606

### laravel-lang-monitor
Key: lang-monitor
Credit: Jonas Schen, https://github.com/jonasschen/laravel-lang-monitor
Licence: MIT, https://opensource.org/license/mit
Evidence: https://raw.githubusercontent.com/jonasschen/laravel-lang-monitor/89c148b06fbec2f1ae3806811f4441db6d90e257/LICENSE read 2026-10-28, commit 89c148b06fbec2f1ae3806811f4441db6d90e257
Changes: short phrases quoted as written where a card does; all other text is ours, paraphrased and shortened.
Use: short quotation under 15 words, with credit
Notice: Copyright (c) 2023 Jonas Schen. Licence text: MIT (the full text is under "Licence texts" below).
Cards: REV-606

### mattpocock/skills
Key: mattpocock
Credit: Matt Pocock, https://github.com/mattpocock/skills
Licence: MIT, https://opensource.org/license/mit
Evidence: https://raw.githubusercontent.com/mattpocock/skills/5beb35b040e3de97e54fa9e386d7e42d15c295c2/LICENSE read 2026-10-28, commit 5beb35b040e3de97e54fa9e386d7e42d15c295c2
Changes: short phrases quoted as written where a card does; all other text is ours, paraphrased and shortened.
Use: short quotation under 15 words, with credit
Notice: Copyright (c) 2026 Matt Pocock. Licence text: MIT (the full text is under "Licence texts" below).
Cards: REV-503

### Ousterhout, aposd vs clean code
Key: aposd
Credit: John Ousterhout, https://github.com/johnousterhout/aposd-vs-clean-code
Licence: ___
Evidence: https://github.com/johnousterhout/aposd-vs-clean-code read 2026-10-28, commit 2ce0742228fbf850e15101f83308de2cd72144b2; the GitHub licence API answers Not Found and the page shows no licence
Changes: short phrases quoted as written, under 15 words; all other text is ours, paraphrased and shortened.
Use: short quotation under 15 words, licence ___
Notice: licence ___ (none found). Only a short quotation is kept, with credit.
Cards: REV-503, REV-506

### AI Hero
Key: aihero
Credit: AI Hero, https://www.aihero.dev/
Licence: ___
Evidence: https://www.aihero.dev/skills-improve-codebase-architecture read 2026-10-28, ETag "f015030f3e67eb35a5d899da2c91fb2b"; no licence words found
Changes: short phrases quoted as written, under 15 words; all other text is ours, paraphrased and shortened.
Use: short quotation under 15 words, licence ___
Notice: licence ___ (none found). Only a short quotation is kept, with credit.
Cards: REV-503

### martinfowler.com
Key: fowler
Credit: Martin Fowler, https://martinfowler.com/
Licence: ___
Evidence: https://martinfowler.com/bliki/BeckDesignRules.html read 2026-10-28, Last-Modified Mon, 26 Oct 2026 23:42:43 GMT; footer shows Martin Fowler and Disclosures, no licence words
Changes: short phrases quoted as written, under 15 words; all other text is ours, paraphrased and shortened.
Use: short quotation under 15 words, licence ___
Notice: licence ___ (none found). Only a short quotation is kept, with credit.
Cards: REV-135, REV-202, REV-408, REV-443, REV-444, REV-445, REV-501, REV-502, REV-504, REV-513, REV-514, REV-517, REV-518, REV-522

### refactoring.com
Key: refactoring-com
Credit: refactoring.com, https://refactoring.com/
Licence: ___
Evidence: https://refactoring.com/catalog/replaceMagicLiteral.html read 2026-10-28, Last-Modified Mon, 12 Oct 2026 23:44:43 GMT; same footer as martinfowler.com, no licence words
Changes: nothing is quoted; cited only, paraphrased.
Use: cited only, nothing copied, licence ___
Notice: licence ___ (none found). Cited only, nothing copied.
Cards: REV-445

### Clean Coder blog
Key: cleancoder
Credit: Robert C. Martin, https://blog.cleancoder.com/
Licence: ___
Evidence: https://blog.cleancoder.com/uncle-bob/2014/05/08/SingleReponsibilityPrinciple.html read 2026-10-28, Last-Modified Thu, 19 Jan 2023 20:57:48 GMT; no licence words found
Changes: short phrases quoted as written, under 15 words; all other text is ours, paraphrased and shortened.
Use: short quotation under 15 words, licence ___
Notice: licence ___ (none found). Only a short quotation is kept, with credit.
Cards: REV-407, REV-408, REV-511, REV-512, REV-513

### Unicode data files
Key: unicode-data
Credit: Unicode, Inc., https://www.unicode.org/Public/
Licence: Unicode License v3, https://www.unicode.org/license.txt
Evidence: https://www.unicode.org/license.txt read 2026-10-28, Last-Modified Mon, 05 Jan 2026 15:17:23 GMT; the header of https://www.unicode.org/Public/18.0.0/ucd/Scripts.txt points to the terms of use, which list files under /Public/ as Data Files
Changes: short phrases quoted as written where a card does; all other text is ours, paraphrased and shortened.
Use: short quotation under 15 words, with credit
Notice: Copyright (c) 1991 to 2026 Unicode, Inc. Licence text: Unicode License v3 (the full text is under "Licence texts" below).
Cards: REV-608

### Unicode CLDR charts
Key: unicode-charts
Credit: Unicode, Inc., https://www.unicode.org/cldr/charts/
Licence: Unicode Terms of Use, https://www.unicode.org/copyright.html
Evidence: https://www.unicode.org/copyright.html read 2026-10-28, no revision shown; Terms of Use: copies of charts are allowed for personal or internal business purposes, not for public distribution; the CLDR chart page (Last-Modified Tue, 13 Oct 2026 16:01:18 GMT) shows no licence words
Changes: nothing is quoted; cards cite the page by URL or say the point in our own words, paraphrased and shortened.
Use: URL only, nothing copied
Notice: nothing copied. Cited by URL or in our own words; this is the project's choice, not a claim that the licence forbids quoting.
Cards: REV-603, REV-604

### Unicode technical reports
Key: unicode-reports
Credit: Unicode, Inc., https://www.unicode.org/reports/
Licence: Unicode Terms of Use, https://www.unicode.org/copyright.html
Evidence: https://unicode.org/reports/tr35/tr35-numbers.html read 2026-10-28, Last-Modified Wed, 21 Oct 2026 20:58:23 GMT; footer shows Copyright 2001 to 2026 Unicode, Inc. and says permission must be obtained from Unicode, Inc.
Changes: nothing is quoted; cards cite the page by URL or say the point in our own words, paraphrased and shortened.
Use: URL only, nothing copied
Notice: nothing copied. Cited by URL or in our own words; this is the project's choice, not a claim that the licence forbids quoting.
Cards: REV-604, REV-608

### Dijkstra EWD249
Key: ewd249
Credit: E. W. Dijkstra, https://www.cs.utexas.edu/~EWD/
Licence: ___
Evidence: https://www.cs.utexas.edu/~EWD/transcriptions/EWD02xx/EWD249/EWD249.html read 2026-10-28, Last-Modified Fri, 26 Aug 2022 13:58:37 GMT; no licence words found
Changes: short phrases quoted as written, under 15 words; all other text is ours, paraphrased and shortened.
Use: short quotation under 15 words, licence ___
Notice: licence ___ (none found). Only a short quotation is kept, with credit.
Cards: REV-P06

### PER Coding Style
Key: per
Credit: PHP Framework Interop Group, https://www.php-fig.org/per/
Licence: ___
Evidence: https://www.php-fig.org/per/coding-style/ read 2026-10-28, Last-Modified Wed, 28 Oct 2026 09:49:29 GMT; footer shows PHP Framework Interop Group, no licence name; the FIG licensing policy says non code items are CC BY 3.0 but does not mention PERs, so the PER licence stays ___
Changes: nothing is quoted; cited only, paraphrased.
Use: cited only, nothing copied, licence ___
Notice: licence ___ (none found). Cited only, nothing copied.
Cards: REV-520

### Cognitect, Documenting Architecture Decisions
Key: cognitect
Credit: Cognitect, https://www.cognitect.com/
Licence: copyright waived by the author, https://www.cognitect.com/blog/2011/11/15/documenting-architecture-decisions
Evidence: https://www.cognitect.com/blog/2011/11/15/documenting-architecture-decisions read 2026-10-28, ETag "e9740bf40773483ff241caa58721b908"
Changes: nothing is quoted; the card cites the post in an extra line and says the point in our own words, paraphrased and shortened.
Use: short quotation under 15 words, with credit; no card quotes it today (extra line only)
Notice: The page says the author has waived all copyright and related or neighboring rights to the post (read 2026-10-28). Credit: Cognitect.
Cards: REV-207

### GNU coreutils manual
Key: gnu-coreutils
Credit: Free Software Foundation, Inc., https://www.gnu.org/software/coreutils/
Licence: GNU FDL 1.3 or later, https://www.gnu.org/licenses/fdl-1.3.html
Evidence: https://www.gnu.org/software/coreutils/manual/html_node/index.html read 2026-10-28, no revision shown; manual for version 9.12; the site answers 403 to a script, plain curl works
Changes: nothing is quoted; cards cite the page by URL or say the point in our own words, paraphrased and shortened.
Use: URL only, nothing copied
Notice: Copyright (c) 1994 to 2026 Free Software Foundation, Inc. Permission is granted to copy, distribute and/or modify this document under the terms of the GNU Free Documentation License, Version 1.3 or any later version published by the Free Software Foundation; with no Invariant Sections, with no Front-Cover Texts, and with no Back-Cover Texts. A copy of the license is included in the section entitled "GNU Free Documentation License". Nothing is copied from the manual.
Cards: REV-229

### i18next documentation
Key: i18next
Credit: i18next, https://www.i18next.com/
Licence: ___
Evidence: https://www.i18next.com/principles/namespaces read 2026-10-28, ETag W/"9r5nk468x0afqa"; no licence words found
Changes: nothing is quoted; cited only, paraphrased.
Use: cited only, nothing copied, licence ___
Notice: licence ___ (none found). Cited only, nothing copied.
Cards: REV-612

## Licence texts

The full text of each licence that asks for it. Each text is copied from the
licence file of a source project that uses it, at the commit named in that
project's entry above: MIT from the Composer file, BSD 3 Clause from the PHPMD
file, Unicode License v3 from https://www.unicode.org/license.txt. The copyright
line of each source is in its own entry above.

### MIT

```text
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is furnished
to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
```

### BSD 3 Clause

```text
Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```

### Unicode License v3

```text
UNICODE LICENSE V3

COPYRIGHT AND PERMISSION NOTICE

Copyright © 1991-2026 Unicode, Inc.

NOTICE TO USER: Carefully read the following legal agreement. BY
DOWNLOADING, INSTALLING, COPYING OR OTHERWISE USING DATA FILES, AND/OR
SOFTWARE, YOU UNEQUIVOCALLY ACCEPT, AND AGREE TO BE BOUND BY, ALL OF THE
TERMS AND CONDITIONS OF THIS AGREEMENT. IF YOU DO NOT AGREE, DO NOT
DOWNLOAD, INSTALL, COPY, DISTRIBUTE OR USE THE DATA FILES OR SOFTWARE.

Permission is hereby granted, free of charge, to any person obtaining a
copy of data files and any associated documentation (the "Data Files") or
software and any associated documentation (the "Software") to deal in the
Data Files or Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, and/or sell
copies of the Data Files or Software, and to permit persons to whom the
Data Files or Software are furnished to do so, provided that either (a)
this copyright and permission notice appear with all copies of the Data
Files or Software, or (b) this copyright and permission notice appear in
associated Documentation.

THE DATA FILES AND SOFTWARE ARE PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT OF
THIRD PARTY RIGHTS.

IN NO EVENT SHALL THE COPYRIGHT HOLDER OR HOLDERS INCLUDED IN THIS NOTICE
BE LIABLE FOR ANY CLAIM, OR ANY SPECIAL INDIRECT OR CONSEQUENTIAL DAMAGES,
OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS,
WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION,
ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THE DATA
FILES OR SOFTWARE.

Except as contained in this notice, the name of a copyright holder shall
not be used in advertising or otherwise to promote the sale, use or other
dealings in these Data Files or Software without prior written
authorization of the copyright holder.
```
