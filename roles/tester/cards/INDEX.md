# Tester cards

Open a card only when its mode and trigger match the step in front of you. Use
only `approved` cards. Policy cards (`TST-P`) always apply.

| id | mode | trigger | status | rule in short |
| --- | --- | --- | --- | --- |
| TST-P01 | all | a bug is found | approved | Report the bug and propose a fix as text; apply no fix in this session. |
| TST-P02 | all | before filing a bug | approved | File a bug only with all 5 proof fields: the expected behaviour and where that expectat... |
| TST-P03 | site, explore, code | before any action that could write | approved | Treat a running site as read only. Before any write, ask the user for that exact action... |
| TST-P04 | all | before calling a skill | approved | Run a called skill only up to its report step, as listed in ROLE.md section 4; skip any... |
| TST-001 | code | after writing a crash fix, before reporting it done | approved | After fixing a crash, add a small regression test that panicked before the fix. |
| TST-002 | code | when adding a command, before marking it done | approved | A new command needs a test that gives it empty, out of range or wrong type params and e... |
| TST-003 | code | after changing a command, before the final gate | approved | When a command is added or changed, run the panic_hunt test, which fuzzes every command... |
| TST-004 | code | before running tests on a local copy | approved | Rebuild dist before running any test that reads it, because a stale build gives confusi... |
| TST-005 | code,site | when a test needs a password or key | approved | Keep secrets out of test code: declare accounts under credentials and other secrets und... |
| TST-006 | code,site | when a CI job exits with a non zero code | approved | Do not retry an exit 2, because it is deterministic; only an exit 3 is worth a job leve... |
| TST-007 | site | before writing steps for a page | approved | Learn the screen's routes, labels, roles and button text before writing the steps for it. |
| TST-008 | site,code | when a test needs to wait for the page | approved | Do not add a sleep to a test. |
| TST-009 | site | when a locator fails with more than one match | approved | When a locator matches two nodes, narrow it with filter, first, nth or a scope instead ... |
| TST-010 | site | when sorting a failed check into flake or bug | approved | When a deterministic step fails every run at the same place with the same code, treat i... |
| TST-011 | explore | after a bug bash run, before writing repro tests | approved | Sort every bug bash finding into a bucket before writing any test for it. |
| TST-012 | explore | when verifying a candidate bug from a bug bash | approved | Write a repro test from the report's steps, and check that it fails on the bug's assert... |
| TST-013 | explore | after running repro tests | approved | If a repro test passes, move it out of the bug folder, because a pass means the bug did... |
| TST-014 | explore | when preparing charters for a bug bash | approved | Give each charter its own account and session, so one charter's edits do not show up as... |
| TST-015 | explore | before sharing a bug bash video | approved | Check a charter's video for secrets before sharing it when the charter or its session s... |
| TST-016 | explore | before filing an explore finding as a bug | approved | Read the finding's actual value against its screenshot before filing it as a bug. |
| TST-017 | code | after an eval run reports failures | approved | Read the transcripts of failed eval runs to decide whether the agent or the grader is a... |
| TST-018 | code | when writing a grader for an agent task | approved | It is often better to grade what the agent produced than the path it took. |
| TST-019 | code | when choosing graders for an AI feature test | approved | Prefer deterministic graders where possible; use model graders where necessary or for e... |
| TST-020 | code | when choosing a pass measure for an AI test | approved | Use pass^k when every run must succeed, and pass@k when one success is enough. |
| TST-021 | code | when setting up an eval suite | approved | Keep regression evals near a 100% pass rate, and let capability evals start at a low pa... |
| TST-022 | code,explore | when starting error analysis on an AI feature | approved | Annotate at least 30 traces yourself before reviewing suggestions from an agent. |
| TST-023 | code,explore | when a test feeds retrieved or tool text to an AI feature | approved | Test retrieved content, tool output and memory as prompt injection inputs, not only typ... |
| TST-024 | code | when a test passes a schema check on AI output | approved | Do not treat a schema valid AI output as safe; test its content too. |
| TST-025 | explore | when checking an AI feature for data leaks | approved | Check tool call arguments, reasoning traces and retrieved chunks for leaks, not only th... |
| TST-026 | code | when a test covers a field that reaches a query or interpreter | approved | Fuzz every input that reaches an interpreter, using automated testing including fuzzing. |
| TST-027 | code | when adding or changing an endpoint or role check | approved | Put functional access control checks into unit and integration tests, not only into man... |
| TST-028 | site | before testing access to records by id | approved | Before testing access to records by id, map every place where user input directly refer... |
| TST-029 | code | before planning SQL injection testing | approved | Before testing for SQL injection, list every input field whose value could be used to b... |
| TST-030 | code | when reviewing AI written tests | approved | Review tests written by an AI agent for file I/O and nondeterministic logic before acce... |
| TST-101 | code | before writing a test, and when reviewing a test someone wrote | approved | Give each test a single condition, so one test checks one thing and a failure points at... |
| TST-102 | code | before writing a test, and when reviewing a test that prints values but has no assertion | approved | A test must decide pass or fail on its own, so a clean run needs no person to read output. |
| TST-103 | code | when writing a test that uses shared state, and when a test fails only on a second run | approved | A test must give the same result on every run without a manual reset, so clean up any s... |
| TST-104 | code | when writing a test that creates persistent data | approved | Clean up what a test creates with one generic cleanup mechanism, not with separate clea... |
| TST-105 | code | when a test needs something from the product code that the product does not expose, and when reviewing a change to product code made for tests | approved | Do not put test only hooks or branches into the product code; the test brings its own s... |
| TST-106 | code | before writing a test that needs a dependency to return a specific value or fail | approved | Use a stub to feed the code under test the input it would get from a dependency, includ... |
| TST-107 | code | before writing a test that must confirm a call to another service | approved | Use a spy or a mock when the test must check what the code under test sent out to a dep... |
| TST-108 | code | when reviewing a test that uses doubles for many objects | approved | Replace the dependencies around the code under test, never the code under test itself. |
| TST-109 | code | when reviewing a test someone wrote, and before adding a branch to a test | approved | Treat control structures (if, loops, switch) in a test method as a serious warning sign. |
| TST-110 | code | when writing a test that reads a value returned by the code under test, and when reviewing a test with if statements | approved | Replace an if guard in a test with an assertion that fails the test with a clear reason. |
| TST-111 | code | when reviewing a test someone wrote, and after a failure that took long digging to understand | approved | When a test is hard to understand at a glance, simplify it so its behaviour is clear. |
| TST-112 | code | when writing assertions in a test, and when a failure log does not show which check failed | approved | Include descriptive assertion messages when they help identify a failure; strongly cons... |
| TST-113 | code | when a test fails on one run and passes on the next, or fails only on a teammate's machine | approved | When a test passes on some runs and fails on others, find the cause first; do not delet... |
| TST-114 | code | after a test breaks following a code change, and before updating the test | approved | When a test breaks after a change that should not touch what it checks, find out why th... |
| TST-115 | code | when the test run is slow and someone proposes a shared fixture | approved | When tests are slow, swap the slow dependency for a fast fake before you share state be... |
| TST-116 | code | before writing setup code, and when reviewing a test with long setup | approved | Move setup that is not the point of the test into a named helper, and keep in the test ... |
| TST-117 | code | before writing a test's setup, and when reviewing a setup block that runs long | approved | Build only the objects and values a test needs to explain its result, and hide the rest... |
| TST-118 | code | before writing a test, and when reviewing a test where setup and checks are interleaved | approved | Write each test in four visible parts, in order: setup, exercise, check, and cleanup. |
| TST-201 | code | writing tests for new or changed code | approved | For Quadrant 1 coverage, use unit and component tests, usually automated in the languag... |
| TST-202 | code | turning a story's examples into tests before coding starts | approved | Turn the customer's examples into tests that the business experts can read. |
| TST-203 | explore | a story passes its examples and needs a real user check | approved | Run exploratory sessions against the working product to find the serious bugs that scri... |
| TST-204 | code, site | planning checks for a story that touches speed, security or load | approved | Plan checks for speed, security and load from the start of the work, not in the last da... |
| TST-205 | code, site | deciding which layer an automated check belongs in | approved | Put most automated checks at the unit and component layer, and keep fewer checks at eac... |
| TST-206 | code, site | writing an automated check for a business rule | approved | Test business rules through the API or the code below the page when you can, not throug... |
| TST-207 | site | adding a new browser check to the smoke or regression suite | approved | Keep browser driven checks few, and count each one as costly to maintain. |
| TST-208 | code, site | a change touches code that existing behavior depends on | approved | Automate regression checks for existing behavior, so every build reports when something... |
| TST-209 | code | a suite run is slow and delays feedback | approved | Keep the suite that runs on every code change short, and move the slow checks to a nigh... |
| TST-210 | code, explore | deciding whether a new check should be automated or run by hand | approved | Treat a one off check as a candidate for manual testing; decide later whether automatin... |
| TST-211 | explore, code | planning how much regression stays manual | approved | Automate enough business checks that repeated manual regression does not take over the ... |
| TST-212 | explore | planning an exploratory session | approved | Start each exploratory session with a charter that names the area to explore. |
| TST-213 | explore | starting an exploratory session or bug bash | approved | In session based testing, set a mission or charter and time box the session to keep focus. |
| TST-214 | explore | during an exploratory session | approved | Take notes during every exploratory session, so each problem can be reproduced. |
| TST-215 | code, site, explore | writing a bug report | approved | A bug report states the steps, what should have happened, and what actually happened. |
| TST-216 | code, explore | deciding where a bug is recorded | approved | Use a defect tracking system when the team is distributed, needs audit or release recor... |
| TST-217 | code, explore | a test task is stuck or blocks a story | approved | Treat quality as the whole team's job, and ask a teammate for help when a test task is ... |
| TST-401 | site | right after a deploy reaches the site | approved | Use read only checks to inspect live behaviour when live verification is needed. |
| TST-402 | site | while a canary serves part of the live traffic | approved | While a canary runs, put its signals next to the control signals and judge the differen... |
| TST-403 | site | before a canary is watched | approved | Before a canary is watched, pick the few metrics that most show user harm, such as fail... |
| TST-404 | site | while a canary runs and the tester reads its metrics | approved | Read each canary metric over a window no longer than the canary itself. |
| TST-405 | site | a canary analysis returns a marginal result | approved | When a canary score is marginal, the tester reports it as marginal, not as a pass, and ... |
| TST-406 | site | after a release, when reading alerts or logs | approved | Check that monitoring shows the running version, so a production alert can be linked to... |
| TST-407 | site | before a release reaches the live site | approved | Before a release reaches the live site, check that a rollback is ready, and report it a... |
| TST-408 | code | before a release is cleared, on a test copy | approved | Review the evidence that rollback safety was tested in a representative test environment. |
| TST-409 | code | when a release has a feature flag, on a test copy | approved | Review the test records showing the build was tested with the flag on and with it off. |
| TST-410 | code | during a flag review on a test copy, before a release is cleared | approved | Release toggles should generally be retired within about 1 or 2 weeks, but product focu... |
| TST-411 | site | while a shadow copy runs beside the live site | approved | When a new version runs as a shadow copy on copied traffic, check that users only ever ... |
| TST-412 | site | while a dark launch runs against a copy of the data | approved | Verify from read only evidence that a dark launch reads production storage only, or use... |
| TST-413 | site | when judging a release from metrics across two time windows | approved | Judge a release by comparing the new and old versions over the same time window, not th... |
| TST-414 | code | when deciding which checks go in the build stage | approved | Typically, mock dependency API calls in unit tests, and test interactions with live dep... |
| TST-415 | code | when deciding which checks belong to which pipeline stage | approved | Put fast checks in early pipeline stages, and slower, deeper checks in later stages. |
| TST-501 | explore, code, site | before planning the test effort | approved | Let your mission decide what you test first and how deep you go. |
| TST-502 | explore, site, code | before writing a test status or saying testing is done | approved | Avoid implying that all bugs were found. Define what kind of testing is complete, then ... |
| TST-503 | code, site, explore | when writing the expected result for a new check | approved | When the spec does not give the expected result, work it out from clues before you judg... |
| TST-504 | explore, code, site | when choosing what to cover for a feature | approved | Recognise that every test relies on a model of the product, and a flawed model produces... |
| TST-505 | explore, code, site | before running any new test | approved | Ask yourself what question should guide the test before you run it. |
| TST-506 | site, code, explore | before filing a bug | approved | Write bug reports to support repair, by making the full impact of the problem clear. |
| TST-507 | site, code, explore | when writing the impact section of a bug report | approved | Make the benefit of fixing the bug clear; relevant evidence can include user impact, da... |
| TST-508 | code, site, explore | when choosing input values for a test | approved | Use extreme values early when relevant, and do not dismiss an extreme failure only beca... |
| TST-509 | site, code, explore | before setting severity on a bug report | approved | Set severity from the consequences, and keep it separate from priority, which can chang... |
| TST-510 | code, site, explore | after a minor failure, before filing it | approved | Test further after a seemingly minor coding error, then stop when more tests are unlike... |
| TST-511 | code, site, explore | before filing a bug | approved | Keep bugs in separate reports when they need different tests to verify their fixes. |
| TST-512 | site, code, explore | when writing the title of a bug report | approved | Give the summary line enough detail for managers to decide whether to ask for more info... |
| TST-513 | site, code, explore | while writing the description of a bug report | approved | Use neutral language, and avoid blaming or talking down to the people involved. |
| TST-514 | code, site | before choosing an automation tool or setting the automation plan | approved | Base the automation strategy on the testing requirements, the product architecture and ... |
| TST-515 | code, site | before automating a test suite | approved | Clean up disorganized testing before you automate it. |
| TST-517 | explore, site, code | when asked whether testing is done | approved | Stop when the clients have enough evidence to make a good decision, using judgement rat... |
| TST-518 | explore, site, code | when writing a status report | approved | Do not use bug counts as the main measure of project progress. |
| TST-519 | site, explore | before signing off a release report | approved | For software sold for resale, include the 10 likely most serious criticisms in the rele... |
| TST-601 | site | When a regression test fails intermittently | approved | Consider ongoing infrastructure testing to guard against intermittent regression failur... |
| TST-602 | site, explore | During debugging or exploratory testing of a running site | approved | Consider monitoring and log files as aids during debugging and exploration. |
| TST-603 | explore | When planning tests for a feature that depends on infrastructure | approved | Ask where the infrastructure could break, for example what happens when the network goe... |
| TST-604 | site | When a team asks for infrastructure testing or a plan for it | approved | At the planning or infrastructure testing support level, prepare a risk based plan cove... |
| TST-605 | code | When reviewing CI job code, build scripts or deploy scripts | approved | Test code written for CI and build systems. The chapter does not recommend testing the ... |
| TST-606 | site, explore | When joining a team or starting work that depends on the CI pipeline | approved | Learn the build pipeline, and know which tests run in which environment. |
| TST-607 | site | When an automatic push could replace the build under test mid session | approved | Raise a pull system for the test environment, so the tester decides when a new build la... |
| TST-608 | explore | When planning exploratory testing alongside an automated build pipeline | approved | When test and staging environments are outside the automated build path, plan explorato... |
| TST-609 | site | When reviewing how the team tests its deploy scripts | approved | Ask whether the same deploy script runs on a test or staging system first, since that r... |
| TST-610 | site | When testing infrastructure for connectivity, failover or backup | approved | In infrastructure testing, often include checks for connectivity, reliability, failover... |
| TST-611 | site | When watching production logs or site performance | approved | When you watch production logs or site performance, ask for a second pair of eyes. |
| TST-612 | code | When reviewing the regression test suite with the team | approved | Consider reviewing suites with programmers to find duplicate or low value tests and rel... |
