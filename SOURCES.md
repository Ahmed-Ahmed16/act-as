# Sources

Every card cites 1 of these. Books are named, never copied or linked to a
copy; cards paraphrase them with chapter and page numbers. Read dates are on
each card. Each book lists its ISBN and a link to its library catalogue record,
not to a copy, so you can find the same edition and check the cited page. The
catalogue links were added on 2026-10-21 without being opened.

## Tester

### Books

- *xUnit Test Patterns: Refactoring Test Code*, Gerard Meszaros, Addison
  Wesley, 2007. https://www.informit.com/store/xunit-test-patterns-refactoring-test-code-9780131495050
  ISBN 9780131495050. Library record: https://openlibrary.org/isbn/9780131495050
  Cards TST-101 to TST-118.
- *Agile Testing: A Practical Guide for Testers and Agile Teams*, Lisa Crispin
  and Janet Gregory, Addison Wesley, 2009.
  https://www.pearson.com/store/en-us/p/agile-testing-a-practical-guide-for-testers-and-agile-teams/P200000009376/9780321534460
  ISBN 9780321534460. Library record: https://openlibrary.org/isbn/9780321534460
  Cards TST-201 to TST-217.

- *Lessons Learned in Software Testing: A Context Driven Approach*, Cem
  Kaner, James Bach and Bret Pettichord, Wiley, 2002.
  https://www.wiley.com/en-us/Lessons+Learned+in+Software+Testing%3A+A+Context-Driven+Approach-p-9780471081128
  ISBN 9780471081128. Library record: https://openlibrary.org/isbn/9780471081128
  Cards TST-501 to TST-519 (TST-516 dropped as a duplicate).
- A Bookey summary of *More Agile Testing* (Janet Gregory and Lisa Crispin,
  Addison Wesley, 2015). This is a third party summary, not the book; cards
  cite it as such. The book:
  https://www.pearson.com/store/en-gb/p/more-agile-testing-learning-journeys-for-the-whole-team/P200000009372/9780321967053
  ISBN 9780321967053. Library record: https://openlibrary.org/isbn/9780321967053
  Cards TST-301 to TST-312 were dropped on 2026-10-19, because a summary is
  not a primary source. Git history keeps them.
- *More Agile Testing*, Janet Gregory and Lisa Crispin, Addison Wesley, 2015,
  chapter 23 "Testing and DevOps": the publisher's free sample chapter (the
  real book text, printed pages 361 to 376), read 2026-10-14.
  https://ptgmedia.pearsoncmg.com/images/9780321967053/samplepages/9780321967053_Ch23_TestingandDevOps.pdf
  Cards TST-601 to TST-612.

### Testing in production and delivery pipelines

Cards TST-401 to TST-415. Pages read 2026-10-13:

- Google SRE Workbook, "Canarying Releases". https://sre.google/workbook/canarying-releases/
- Google SRE Workbook, "Monitoring". https://sre.google/workbook/monitoring/
- Google SRE Book, "Testing for Reliability". https://sre.google/sre-book/testing-reliability/
- AWS Builders Library, "Automating safe, hands off deployments" and
  "Ensuring rollback safety during deployments" (dates `___`).
  https://aws.amazon.com/builders-library/automating-safe-hands-off-deployments ,
  https://aws.amazon.com/builders-library/ensuring-rollback-safety-during-deployments
- Google Cloud blog, "Introducing Kayenta". https://cloud.google.com/blog/products/gcp/introducing-kayenta-an-open-automated-canary-analysis-tool-from-google-and-netflix
- Martin Fowler, "DeploymentPipeline". https://martinfowler.com/bliki/DeploymentPipeline.html
- Pete Hodgson, "Feature Toggles" (martinfowler.com). https://www.martinfowler.com/articles/feature-toggles.html
- Microsoft Code With Engineering Playbook, "Shadow Testing". https://microsoft.github.io/code-with-engineering-playbook/automated-testing/shadow-testing/
- Datadog blog, "Dark launches". https://www.datadoghq.com/blog/dark-launches/

### Standards

- OWASP Top 10:2025. https://top10.owasp.org/2025 . Cards TST-026, TST-027.
- OWASP Top 10 for LLM Applications 2026, v1.0, 3 Aug 2026.
  https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/ . Cards
  TST-023 to TST-025.
- OWASP Web Security Testing Guide v4.2. https://wstg.owasp.org/v4.2/ . Cards
  TST-028, TST-029.

### Repositories

- tester-army/e2e, Apache 2.0, commit 4b4b29727dde17eb135b030c031c10607a2d6299.
  https://github.com/tester-army/e2e . Cards TST-004 to TST-016.
- storytold/photocraft, MIT or Apache 2.0, commit
  6f85054288a564f9fbbccb99268ffdb34e581584. https://github.com/storytold/photocraft .
  Cards TST-001 to TST-003.
- backnotprop/pstack, MIT, commit fce11a3442cfd59a21136de0b7010474c6a10ef5.
  https://github.com/backnotprop/pstack . Copied items under
  `roles/tester/borrowed/pstack/`.

### Articles and papers

- Anthropic, "Demystifying evals for AI agents", 9 Jan 2026.
  https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents .
  Cards TST-017 to TST-021.
- Hamel Husain and Shreya Shankar, "Why is error analysis so important in LLM
  evals". https://hamel.dev/blog/posts/evals-faq/why-is-error-analysis-so-important-in-llm-evals-and-how-is-it-performed.html .
  Card TST-022.
- "Beyond Test Presence", arXiv 2607.12068, 13 Jul 2026.
  https://arxiv.org/abs/2607.12068 . Card TST-030.
- Anthropic, "Mitigating prompt injections in browser use", 24 Nov 2025.
  https://www.anthropic.com/research/prompt-injection-defenses . Card TST-P03.

## Developer

Cards DEV-P01 to DEV-P06 are user decisions from the developer v1.1 plan,
2026-10-15, approved by the user on 2026-10-19. No developer card
cites a book or web page yet; the gaps are in `ROADMAP.md`.

## Manager

Cards MGR-P01 to MGR-P05 are user decisions from the manager v1.2 plan,
2026-10-19, approved by the user on 2026-10-20. Cards MGR-001 to MGR-006,
each checked against its raw source by a second model, approved by the user
on 2026-10-20:

- GOV.UK Service Manual, "Governance principles for agile service delivery",
  last updated 23 May 2016, read 2026-10-19.
  https://www.gov.uk/service-manual/governance/governance-principles .
  Cards MGR-001, MGR-002.
- Frederick P. Brooks, The Mythical Man-Month, Anniversary Edition,
  Addison-Wesley 1995. ISBN 9780201835953.
  Library record: https://openlibrary.org/isbn/9780201835953
  Cards MGR-003, MGR-004.
- Tom DeMarco and Timothy Lister, Waltzing with Bears, Dorset House 2003.
  ISBN 9780932633606. Library record: https://openlibrary.org/isbn/9780932633606
  Card MGR-005.
- Scott Berkun, Making Things Happen, O'Reilly 2008. ISBN 9780596517717.
  Library record: https://openlibrary.org/isbn/9780596517717
  Card MGR-006.

## Reviewer

### Split plan and entry point tracing (cards REV-121 to REV-140)

Drafted 2026-10-28, checked 2026-10-28 by a second model, approved by Ahmed 2026-10-28. All pages read 2026-10-28.
Cards quote at most a short anchor and say the rest in their own words.
Borrowed text keeps its own licence; see THIRD-PARTY-NOTICES.md.

- Laravel 12.x documentation (MIT), always cited with the version in the link.
  Routing: https://laravel.com/docs/12.x/routing . Controllers:
  https://laravel.com/docs/12.x/controllers . Artisan console:
  https://laravel.com/docs/12.x/artisan . Task scheduling:
  https://laravel.com/docs/12.x/scheduling . Blade templates:
  https://laravel.com/docs/12.x/blade . Migrations (related only):
  https://laravel.com/docs/12.x/migrations . The controllers page is not on
  the ticket 19 frozen page list; its sections used here were compared with 11.x.
  Cards REV-121 to REV-126, REV-132.
- Google engineering practices (CC BY 3.0): small CLs
  https://google.github.io/eng-practices/review/developer/small-cls.html ,
  reviewer speed https://google.github.io/eng-practices/review/reviewer/speed.html ,
  CL descriptions https://google.github.io/eng-practices/review/developer/cl-descriptions.html .
  Cards REV-127 to REV-131, REV-133, REV-136, REV-137, REV-140.
- Linux kernel documentation (GPL 2.0 only, cited by URL and never copied):
  Submitting patches https://www.kernel.org/doc/html/latest/process/submitting-patches.html ,
  Coding style https://www.kernel.org/doc/html/latest/process/coding-style.html .
  Cards REV-133, REV-516.
- Pete Hodgson, Feature Toggles (aka Feature Flags), on martinfowler.com.
  https://martinfowler.com/articles/feature-toggles.html .
  Card REV-135.
- GitHub Docs (CC BY 4.0): workflow syntax
  https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax ,
  about stacked pull requests
  https://docs.github.com/en/pull-requests/get-started/about-stacked-prs .
  Cards REV-134, REV-138, REV-139.
- Git documentation (GPL 2.0, cited by URL only, nothing copied; the quotes were
  removed 2026-10-28): git-diff https://git-scm.com/docs/git-diff ,
  git-merge-base https://git-scm.com/docs/git-merge-base ,
  git-grep https://git-scm.com/docs/git-grep ,
  git-hash-object https://git-scm.com/docs/git-hash-object ,
  gitattributes https://git-scm.com/docs/gitattributes ,
  gitrevisions https://git-scm.com/docs/gitrevisions .
  Cards REV-101, REV-102, REV-106, REV-114, REV-116, REV-117, REV-130, REV-206,
  REV-208, REV-413, REV-446, REV-P10.

### Other reviewer cards (REV-101 to REV-120, REV-201 to REV-239, REV-301 to REV-357, REV-401 to REV-450, REV-501 to REV-523, REV-601 to REV-613, REV-P01 to REV-P11)

- Laravel framework source (MIT): https://github.com/laravel/framework/blob/e130a2e7f3e10e7d983ae5865389c628b4ea43bf/src/Illuminate/Translation/FileLoader.php#L153 , https://github.com/laravel/framework/blob/e130a2e7f3e10e7d983ae5865389c628b4ea43bf/src/Illuminate/Translation/MessageSelector.php#L387 . Cards REV-601, REV-604.
- OWASP Cheat Sheet Series (CC BY SA 4.0, cited in our own words, no text copied): https://cheatsheetseries.owasp.org/cheatsheets/Business_Logic_Security_Cheat_Sheet.html#permissions-and-ownership , https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html#validate-the-permissions-on-every-request , https://cheatsheetseries.owasp.org/cheatsheets/Laravel_Cheat_Sheet.html#mass-assignment , https://cheatsheetseries.owasp.org/cheatsheets/Laravel_Cheat_Sheet.html#raw-query-sql-injection , https://cheatsheetseries.owasp.org/cheatsheets/Laravel_Cheat_Sheet.html#column-name-sql-injection , https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html#filename-safety , https://cheatsheetseries.owasp.org/cheatsheets/Laravel_Cheat_Sheet.html#always-validate-file-type-and-size , https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html#upload-and-download-limits , https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html#list-allowed-extensions , https://cheatsheetseries.owasp.org/cheatsheets/Webhook_Security_Cheat_Sheet.html#cross-site-request-forgery-csrf-considerations , https://cheatsheetseries.owasp.org/cheatsheets/Laravel_Cheat_Sheet.html#cross-site-scripting-xss , https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html#xss-prevention-rules-summary , https://cheatsheetseries.owasp.org/cheatsheets/Unvalidated_Redirects_and_Forwards_Cheat_Sheet.html#preventing-unvalidated-redirects-and-forwards , https://cheatsheetseries.owasp.org/cheatsheets/Laravel_Cheat_Sheet.html#open-redirection , https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html#1-introduction , https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html#login-throttling , https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html#forgot-password-request , https://cheatsheetseries.owasp.org/cheatsheets/Multifactor_Authentication_Cheat_Sheet.html#mfa-fatigue-push-notification-bombing , https://cheatsheetseries.owasp.org/cheatsheets/Webhook_Security_Cheat_Sheet.html#rate-limiting , https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html#general-security-practices , https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html#renew-the-session-id-after-any-privilege-level-change , https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html#manual-session-expiration , https://cheatsheetseries.owasp.org/cheatsheets/Multifactor_Authentication_Cheat_Sheet.html#resetting-mfa , https://cheatsheetseries.owasp.org/cheatsheets/Multifactor_Authentication_Cheat_Sheet.html#mfa-downgrade-attacks , https://cheatsheetseries.owasp.org/cheatsheets/Laravel_Cheat_Sheet.html#cookie-security-and-session-management , https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html#httponly-attribute , https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html#secure-attribute , https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html#samesite-attribute , https://cheatsheetseries.owasp.org/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.html#defense-option-1-avoid-calling-os-commands-directly , https://cheatsheetseries.owasp.org/cheatsheets/Laravel_Cheat_Sheet.html#command-injection , https://cheatsheetseries.owasp.org/cheatsheets/Laravel_Cheat_Sheet.html#other-injections , https://cheatsheetseries.owasp.org/cheatsheets/Laravel_Cheat_Sheet.html#do-not-rely-on-user-input-to-dictate-filenames-or-path , https://cheatsheetseries.owasp.org/cheatsheets/Laravel_Cheat_Sheet.html#path-traversal , https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html#application-layer , https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html#case-2-application-can-send-requests-to-any-external-ip-address-or-domain-name , https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html#data-to-exclude , https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html#confidentiality , https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html#disposal-of-logs , https://cheatsheetseries.owasp.org/cheatsheets/Webhook_Security_Cheat_Sheet.html#signature-verification , https://cheatsheetseries.owasp.org/cheatsheets/Webhook_Security_Cheat_Sheet.html#input-validation , https://cheatsheetseries.owasp.org/cheatsheets/Business_Logic_Security_Cheat_Sheet.html#prices-and-totals , https://cheatsheetseries.owasp.org/cheatsheets/Webhook_Security_Cheat_Sheet.html#replay-attack-protection , https://cheatsheetseries.owasp.org/cheatsheets/Business_Logic_Security_Cheat_Sheet.html#use-idempotency-keys-for-external-actions , https://cheatsheetseries.owasp.org/cheatsheets/Business_Logic_Security_Cheat_Sheet.html#use-database-transactions-and-locks , https://cheatsheetseries.owasp.org/cheatsheets/Business_Logic_Security_Cheat_Sheet.html#reject-replays-of-completed-steps , https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html#domain-and-path-attributes , https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html#session-expiration , https://cheatsheetseries.owasp.org/cheatsheets/Secure_Product_Design_Cheat_Sheet.html , https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html . Cards REV-301, REV-304, REV-305, REV-306, REV-308, REV-309, REV-311, REV-312, REV-313, REV-314, REV-315, REV-316, REV-317, REV-319, REV-320, REV-323, REV-324, REV-325, REV-326, REV-327, REV-329, REV-330, REV-331, REV-334, REV-335, REV-336, REV-337, REV-338, REV-340, REV-341, REV-342, REV-343, REV-344, REV-345, REV-351, REV-352, REV-353, REV-354, REV-356, REV-357, REV-P01, REV-P05.
- OWASP API Security Top 10 (CC BY SA 4.0, cited by URL only, nothing copied): https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/#how-to-prevent , https://owasp.org/API-Security/editions/2023/en/0xa3-broken-object-property-level-authorization/#how-to-prevent , https://owasp.org/API-Security/editions/2023/en/0xa7-server-side-request-forgery/#how-to-prevent . Cards REV-301, REV-303, REV-307, REV-337, REV-338, REV-339.
- OWASP Top 10 (CC BY SA 4.0 by the repo, CC BY 3.0 by the page footer; which governs is ___; treated as CC BY SA 4.0, no text copied): https://owasp.org/Top10/2021/A06_2021-Vulnerable_and_Outdated_Components/#how-to-prevent . Cards REV-346, REV-347, REV-349.
- OWASP community pages (CC BY SA 4.0, cited by URL only, nothing copied): https://owasp.org/www-community/attacks/CSV_Injection . Card REV-318.
- OWASP GenAI Security Project (CC BY SA 4.0, cited by URL only, nothing copied): https://genai.owasp.org/llmrisk/llm062025-excessive-agency/ . Card REV-P02.
- PHPUnit documentation (CC BY 3.0): https://docs.phpunit.de/en/12.5/textui.html#filtering-by-group , https://docs.phpunit.de/en/12.5/writing-tests-for-phpunit.html#skipping-tests , https://docs.phpunit.de/en/12.5/textui.html#progress . Cards REV-411, REV-426.
- PHP manual (CC BY 3.0 or later): https://www.php.net/manual/en/function.unserialize.php#refsect1-function.unserialize-description , https://www.php.net/manual/en/language.enumerations.overview.php , https://www.php.net/manual/en/function.htmlspecialchars.php , https://www.php.net/manual/en/regexp.reference.unicode.php . Cards REV-335, REV-445, REV-607, REV-608.
- Composer documentation (MIT): https://getcomposer.org/doc/03-cli.md#audit , https://getcomposer.org/doc/05-repositories.md#loading-a-package-from-a-vcs-repository , https://getcomposer.org/doc/articles/scripts.md#what-is-a-script , https://getcomposer.org/doc/articles/scripts.md#defining-scripts , https://getcomposer.org/doc/04-schema.md . Cards REV-346, REV-347, REV-348, REV-411, REV-P09.
- pstack (MIT): https://github.com/backnotprop/pstack/blob/f51fdeba3d803ef90e4eaa4a95ffb4e76008ab37/skills/poteto-mode/playbooks/refactoring.md#L10 , https://github.com/backnotprop/pstack/blob/f51fdeba3d803ef90e4eaa4a95ffb4e76008ab37/skills/poteto-mode/SKILL.md#L44 , https://github.com/backnotprop/pstack/blob/f51fdeba3d803ef90e4eaa4a95ffb4e76008ab37/skills/interrogate/references/code-quality-review.md#L25 , https://github.com/backnotprop/pstack/blob/f51fdeba3d803ef90e4eaa4a95ffb4e76008ab37/skills/poteto-mode/SKILL.md#L49 . Cards REV-417, REV-502, REV-505, REV-510.
- jscpd (MIT): https://github.com/kucherenko/jscpd/blob/v5.4.2/README.md#recommended-aggregator-settings , https://github.com/kucherenko/jscpd/blob/v5.4.2/docs/rust.md#baseline , https://github.com/kucherenko/jscpd/blob/v5.4.2/docs/rust.md#config-file , https://github.com/kucherenko/jscpd/blob/v5.4.2/docs/rust.md#exit-codes . Cards REV-401, REV-402, REV-403.
- Larastan (MIT): https://github.com/larastan/larastan . Card REV-418.
- PHPStan source (MIT): https://github.com/phpstan/phpstan-src/blob/7c9daa4ca480f7407d3ce01754ea3a9a6d9b480c/src/Rules/DeadCode/UnusedPrivateMethodRule.php#L24 , https://github.com/phpstan/phpstan-src/blob/7c9daa4ca480f7407d3ce01754ea3a9a6d9b480c/conf/config.level5.neon#L5 . Cards REV-416, REV-418.
- PHPStan documentation (licence ___, short quotation kept): https://phpstan.org/user-guide/baseline , https://phpstan.org/user-guide/rule-levels . Cards REV-216, REV-218, REV-416, REV-418, REV-421.
- PHPMD (BSD 3 Clause): https://phpmd.org/rules/codesize.html#excessivemethodlength , https://phpmd.org/rules/codesize.html#excessiveclasslength , https://phpmd.org/rules/unusedcode.html#unusedprivatemethod , https://phpmd.org/rules/unusedcode.html#unusedlocalvariable . Cards REV-404, REV-405, REV-415.
- Infection (BSD 3 Clause): https://infection.github.io/guide/#What-is-Mutation-Testing . Cards REV-425, REV-521.
- ElegantEngineeringTech/laravel-translator, https://github.com/ElegantEngineeringTech/laravel-translator , Prosperity Public License 3.0.0 (Contributor Quentin Gabriele), cited by URL only, nothing copied. Cards REV-602, REV-606. jonasschen/laravel-lang-monitor, https://github.com/jonasschen/laravel-lang-monitor , MIT, Copyright (c) 2023 Jonas Schen. Card REV-606.
- mattpocock/skills (MIT): https://github.com/mattpocock/skills/blob/5beb35b040e3de97e54fa9e386d7e42d15c295c2/skills/engineering/improve-codebase-architecture/SKILL.md#L35 . Card REV-503.
- Ousterhout, aposd vs clean code (licence ___, short quotation kept): https://github.com/johnousterhout/aposd-vs-clean-code . Cards REV-503, REV-506.
- AI Hero (licence ___, short quotation kept): https://www.aihero.dev/skills-improve-codebase-architecture . Card REV-503.
- martinfowler.com (licence ___, short quotation kept): https://martinfowler.com/articles/feature-toggles.html , https://martinfowler.com/bliki/UbiquitousLanguage.html , https://martinfowler.com/bliki/PresentationDomainSeparation.html , https://martinfowler.com/bliki/DefinitionOfRefactoring.html , https://martinfowler.com/bliki/BeckDesignRules.html , https://martinfowler.com/bliki/Yagni.html , https://martinfowler.com/bliki/UnitTest.html , https://martinfowler.com/bliki/TechnicalDebtQuadrant.html . Cards REV-135, REV-202, REV-408, REV-443, REV-444, REV-445, REV-501, REV-502, REV-504, REV-513, REV-514, REV-517, REV-518, REV-522.
- refactoring.com (licence ___, cited only): https://refactoring.com/catalog/replaceMagicLiteral.html . Card REV-445.
- Clean Coder blog (licence ___, short quotation kept): https://blog.cleancoder.com/uncle-bob/2014/05/08/SingleReponsibilityPrinciple.html . Cards REV-407, REV-408, REV-511, REV-512, REV-513.
- Unicode data files (Unicode License v3): https://www.unicode.org/Public/18.0.0/ucd/Scripts.txt . Card REV-608.
- Unicode CLDR charts (Unicode Terms of Use, cited by URL only, nothing copied): https://www.unicode.org/cldr/charts/49/supplemental/language_plural_rules.html#ar , https://www.unicode.org/cldr/charts/49/supplemental/language_plural_rules.html#en . Cards REV-603, REV-604.
- Unicode technical reports (Unicode Terms of Use, cited by URL only, nothing copied): https://unicode.org/reports/tr35/tr35-numbers.html#Language_Plural_Rules , https://www.unicode.org/reports/tr24/#Common . Cards REV-604, REV-608.
- Dijkstra EWD249 (licence ___, short quotation kept): https://www.cs.utexas.edu/~EWD/transcriptions/EWD02xx/EWD249/EWD249.html . Card REV-P06.
- PER Coding Style 3.1, https://www.php-fig.org/per/coding-style/ , read 2026-10-28, licence ___ (see THIRD-PARTY-NOTICES.md), cited only. Card REV-520.
- Cognitect, Documenting Architecture Decisions (copyright waived by the author): https://www.cognitect.com/blog/2011/11/15/documenting-architecture-decisions . Card REV-207.
- GNU coreutils manual (GNU FDL 1.3 or later, cited by URL only, nothing copied): https://www.gnu.org/software/coreutils/manual/html_node/sha2-utilities.html#sha2-utilities . Card REV-229.
- i18next documentation (licence ___, cited only): https://www.i18next.com/principles/namespaces . Card REV-612.
