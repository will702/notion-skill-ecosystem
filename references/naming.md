# Naming conventions

Consistent names make search, formulas and automation predictable. Skills must apply these when creating anything and report violations when auditing.

## Pages
- Title Case, no trailing punctuation, no emoji in the title text (icons are set via the icon field).
- Dashboards end with ` Dashboard` (`Project Dashboard`), wiki pages are nouns (`Release Process`), meeting notes are `YYYY-MM-DD Topic`, logs are `YYYY-MM Log`.
- Test and scratch pages start with `Test ` or live under a page named `Skill Sandbox`. Never leave test pages elsewhere.

## Databases (master)
- Plural noun in Title Case: `Projects`, `Tasks`, `Meetings`, `Sources`.
- Views inside a master database: `All`, `Open`, `By Status`, `Calendar`. Views on dashboards are named for the question they answer: `Due This Week`.

## Properties
- Title property is `Name` (or the entity name for typed databases).
- Singular, Title Case: `Status`, `Due Date`, `Owner`, `Priority`.
- Relations are named for the target in singular (`Project`) and the reverse in plural (`Tasks`).
- Rollups and formulas are prefixed by purpose: `Progress`, `Urgency`, `Open Task Count`. Do not rename them after formulas reference them.
- Booleans use `Is` or `Has` (`Is Archived`).
- Select options: short, Title Case, no emoji: `Todo`, `In Progress`, `Done`.

## Files and assets
- Uploaded image filenames: `<page-slug>-<nn>-<topic>.png`; set a caption that names the source and license for any third-party image.

## Audit severity
- Error: duplicate database names, two properties differing only by case, a formula referencing a renamed property.
- Warning: inconsistent casing, emoji in titles, dashboards without the suffix, orphaned test pages.
