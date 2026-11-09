---
name: notion-research-assistant
description: Builds Notion research workspaces for literature reviews, sources, citations, notes, hypotheses, experiment logs and research dashboards. Use when the user says "literature review", "track sources", "add citation", "log an experiment", "hypothesis tracker" or "research dashboard".
---

## Purpose
Maintain linked Sources, Notes, Hypotheses and Experiments databases where every claim traces to a source row, with citation properties and a research dashboard of linked views. Citations are never invented.

## Activation triggers
- "Start a literature review", "add this paper/source", "cite this".
- "Record a hypothesis / experiment / result".
- "Which claims lack a source?", "build a research dashboard".

## Required tools
- `ntn api v1/databases`, `v1/data_sources/<id>` PATCH, `v1/pages`, `v1/data_sources/<id>/query`, `v1/search`: `API-supported`, Tested.
- Relations and rollups: `API-supported`, Tested (property creation; writing relation values stays Docs only).
- Views table/board/calendar, linked database blocks: `API-supported`, Tested.
- v2 Markdown pages (toggles for logs): `API-supported`, Tested.
- Fetching source metadata from the web or a DOI: `external`, not performed by this skill; user supplies or confirms metadata.
- MCP: `MCP-supported`, Not tested.

## Dependencies
- `notion-database-architect` owns schema mechanics; schema here: [templates/research](../../../templates/research/README.md).
- `notion-page-composer` owns layout; dashboard views follow [design-system](../../../references/design-system.md).
- `notion-meeting-intelligence` can feed discussion notes in as Notes rows.
- `notion-automation-engineer` owns scheduled reminders (for example a weekly unverified-claims check).
- Naming: [naming](../../../references/naming.md); limits: [api-limits](../../../references/api-limits.md).

## Operating principles
1. Every claim row links to at least one `Source` row; a claim without a source is flagged, not hidden.
2. Never fabricate citations. If title, authors, year or DOI are not provided or visible in the supplied material, leave them empty and set `Verification` to `Unverified`.
3. Distinguish `Verified` (user or document confirmed), `Unverified`, `Disputed`.
4. Quotes are verbatim with page/section reference.
5. Experiments are logged append-only; long logs go in toggles.
6. One neutral accent, at most 1-2 callouts per section.

## Detailed workflow
Embedded 7-step execution protocol:
1. **Analyze**: relational tracking database (Sources, Notes, Hypotheses, Experiments) plus a dashboard.
2. **Retrieve context**: `v1/search` for the four databases and the dashboard; fetch schemas and parent IDs; check duplicates by `DOI` or `URL` before adding a source.
3. **Plan**: show schema, relations, views and dashboard skeleton; wait for approval if existing content changes.
4. **Generate payload**: [schema.json](../../../templates/research/schema.json) properties, [page.md](../../../templates/research/page.md) body; validate with a script.
5. **Execute**: create Sources first, then Notes, Hypotheses, Experiments, add relations, then views and dashboard page.
6. **Verify**: re-fetch schemas and diff; query Notes where `Source` is empty and report the count.
7. **Report**: page URL/ID, layout, schema, formulas, UI-only items (database buttons, templates), and the count of Unverified rows.

## Implementation instructions
**Schema (`API-supported`):** `Sources`: Name (title), Authors (rich_text), Year (number), DOI (rich_text), URL (url), Type (select: Paper, Book, Web, Dataset), Verification (select: Verified, Unverified, Disputed), Citation (rich_text, formatted string), `Notes` (reverse relation). `Notes`: Name, Claim (rich_text), Source (relation to Sources), Quote (rich_text), Location (rich_text), Hypothesis (relation). `Hypotheses`: Name, Statement, Status (select: Proposed, Testing, Supported, Refuted), Notes, Experiments. `Experiments`: Name, Hypothesis (relation), Date, Method, Result, Status.
**Citation property:** `Citation` is composed only from filled fields (Authors, Year, Name, DOI/URL); if any is empty, append `[incomplete]` and set `Verification` to `Unverified`.
**Order:** create Sources first so Notes have relation targets; add relation properties by `PATCH v1/data_sources/<id>` after both exist.
**Hypothesis flow:** `Proposed` > `Testing` when an Experiment links; `Supported` or `Refuted` only with a linked Experiment `Result`.
**Claim rule:** a script or user flow that creates a Notes row must receive a `Source` ID; otherwise refuse and ask.
**Dashboard:** linked views (`create_database`) of Notes filtered `Source` is empty ("Unsourced Claims"), Hypotheses board by `Status` (needs property ID and `sort`), Experiments calendar, Sources table by `Verification`.
**Page layout:** H1, purpose line, one callout stating the citation rule, columns 30/70 for links and the board, divider, toggle `Experiment Log`.

## Examples
Add a source with unverified metadata:
```sh
ntn api v1/pages -d '{"parent":{"type":"data_source_id","data_source_id":"<SOURCES_DATA_SOURCE_ID>"},"properties":{"Name":{"title":[{"text":{"content":"<TITLE_AS_GIVEN>"}}]},"URL":{"url":"<URL>"},"Verification":{"select":{"name":"Unverified"}}}}' < /dev/null
```
Add a linked claim:
```sh
ntn api v1/pages -d '{"parent":{"type":"data_source_id","data_source_id":"<NOTES_DATA_SOURCE_ID>"},"properties":{"Name":{"title":[{"text":{"content":"<SHORT_CLAIM>"}}]},"Source":{"relation":[{"id":"<SOURCE_PAGE_ID>"}]}}}' < /dev/null
```
Find unsourced claims:
```sh
ntn api v1/data_sources/<NOTES_DATA_SOURCE_ID>/query -d '{"filter":{"property":"Source","relation":{"is_empty":true}}}' < /dev/null
```

## Validation checklist
- The unsourced-claims query returns 0 rows after the run (or the count is reported).
- Every Sources row without DOI/URL has `Verification` = `Unverified`.
- Schemas match [schema.json](../../../templates/research/schema.json) (diff names and types).
- Source duplicates check: query by `DOI` returns at most one row.
- Dashboard views are all linked views; one accent; at most 2 callouts per section.

## Failure handling
- 400: relation target not in the same workspace or property type mismatch; re-fetch schema.
- 404: database not shared with the integration.
- 429: honor `Retry-After`; throttle queries to about 3 req/s.
- 5xx on POST: query by `DOI`/`Name` before retrying; avoid duplicate sources.
- Rich text over 2,000 chars: split long quotes; cite location instead.
- Missing metadata: do not search-and-guess; ask the user or leave empty and mark Unverified.
- Relation rejected: report it and store the source name as text, flagged.

## Safety constraints
- Test only under "Skill Sandbox".
- Never fabricate or "complete" citations, DOIs, authors or quotes.
- Do not overwrite or delete existing notes without approval; archive instead.
- Explicit IDs only; never print or store tokens.
