id: REV-P09
rule: For version 1, proceed only when composer.json is a valid JSON object and lists laravel/framework under require. If it is under require-dev, appears elsewhere, is absent, unreadable or invalid, stop.
why: Composer defines require for packages needed by the package and require-dev for development or test packages.
applies-when: Before any reviewer mode in version 1.
not-when: none
example: In owner/shop, composer.json lists laravel/framework only under require-dev, so the reviewer stops.
mode: all
trigger: Before a reviewer mode starts
kind: source-advice
source: The composer.json schema, require and require-dev, https://getcomposer.org/doc/04-schema.md, read 2026-10-26
anchor: "Map of packages required for developing this package"
status: approved
review: drafted by gpt-6-luna effort max, 2026-10-26 (relay record); checked against the raw source by claude-sonnet-5-5, 2026-10-26, CHECK PASS: anchor verbatim in the Composer schema (require dev entry); the require entry says the package is not installed unless requirements are met; Laravel scope is a project choice; approved by Ahmed 2026-10-26, as drafted
extra: Composer defines the dependency sections. Laravel only scope, the valid object check and the laravel/framework gate are this project's choices.
