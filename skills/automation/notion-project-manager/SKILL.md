---
name: notion-project-manager
description: Builds Notion project dashboards, milestones, dependencies, progress, assignments, risks and weekly status reports on a Projects/Tasks/Milestones/Risks schema. Use when the user says "project dashboard", "track milestones", "task dependencies", "weekly report", "risk register" or "project timeline".
---

## Purpose
Provide a relational project-management setup (Projects, Tasks, Milestones, Risks), progress and urgency formulas, linked-view dashboards and a weekly report page generated from a data source query.

## Activation triggers
- "Set up project tracking", "create a project dashboard".
- "Add milestones / dependencies / risks", "who owns what".
- "Generate the weekly report", "what is overdue", "show progress".
- "Timeline view" (see Implementation: not claimed as working).

## Required tools
- `ntn api v1/databases`, `v1/data_sources/<id>` PATCH, `v1/pages`, `v1/data_sources/<id>/query`: `API-supported`, Tested.
- Formula 2.0 properties: `API-supported`, Tested ([formulas](../../../references/formulas.md)).
- Relations and rollups: `API-supported`, Tested (property creation; rollup `Open Blockers` and writing relation values stay Docs only).
- `v1/views`: table, board, calendar, dashboard `API-supported`, Tested; `timeline` is Docs only / Not tested (do not claim it works).
- v2 Markdown report via `v1/pages` with `markdown_version: "v2"`: `API-supported`, Tested.
- Scheduled weekly generation: `external` (see `notion-automation-engineer`); native recurring: `UI-only`.
- MCP: `MCP-supported`, Not tested.

## Dependencies
- `notion-database-architect` owns schema mechanics; schema here: [templates/project](../../../templates/project/README.md).
- `notion-page-composer` owns layout; dashboards are built from linked views (`v1/views` with `create_database`).
- `notion-automation-engineer` owns schedules and dedupe for the weekly report.
- `notion-meeting-intelligence` writes Action Items; they can relate to Tasks.
- Rules: [design-system](../../../references/design-system.md), [naming](../../../references/naming.md), [api-limits](../../../references/api-limits.md), [capability-matrix](../../../references/capability-matrix.md).

## Operating principles
1. Master databases hold rows and formulas; dashboards hold only linked views, never copies.
2. Progress comes from relation rollups (`Completed`, `Total`), not manual numbers.
3. Status values are plain text: Not Started, In Progress, Blocked, Done.
4. One neutral accent per dashboard; at most 1-2 callouts per section; toggle for archive.
5. Do not claim timeline views; use table/board/calendar.
6. Weekly reports are append-only pages named `YYYY-MM-DD Weekly Report`; never overwrite last week.

## Detailed workflow
Embedded 7-step execution protocol:
1. **Analyze**: operational dashboard over a relational tracking database.
2. **Retrieve context**: `v1/search` for Projects/Tasks/Milestones/Risks; fetch schemas and parent IDs; check duplicate names.
3. **Plan**: show schema, formulas, views and dashboard skeleton; wait for approval if it changes existing content.
4. **Generate payload**: schema JSON from [schema.json](../../../templates/project/schema.json), page body from [page.md](../../../templates/project/page.md); validate JSON with a script.
5. **Execute**: create databases (Projects first), add relations then rollups then formulas, create views, then dashboard page.
6. **Verify**: re-fetch each data source and compare property names and types; query one row and read `Progress` and `Urgency`; list views via `GET v1/views`.
7. **Report**: page URL/ID, layout, schema, active formulas, UI-only items (database buttons, native automations, timeline view if wanted).

## Implementation instructions
**Schema (`API-supported`):** `Projects`: Name, Status, Owner (people), Start Date, Due Date, `Tasks` (reverse relation), `Total` (rollup count of Tasks), `Completed` (rollup of the `Is Done` checkbox, as in the template schema), `Progress` (formula), `Urgency` (formula). `Tasks`: Name, `Related to Projects (Tasks)` (auto-named reverse of `Projects.Tasks`; rename it to `Project` if wanted), Status, Assignee, Due Date, `Blocked By` (self-relation, dependencies), Milestone (relation). `Milestones`: Name, Project, Target Date, Status. `Risks`: Name, Project, Severity (select: Low, Medium, High), Likelihood, Mitigation, Status.
**Formulas:** use `Progress` and `Urgency` exactly as in [formulas.md](../../../references/formulas.md), with the divide-by-zero guard for `Total`. Property names are stable; do not rename.
**Dependencies:** `Blocked By` self-relation; a task is blocked when any related task `Status` is not Done (rollup `Open Blockers`, Docs only).
**Views:** `v1/views` type `table`, `board` (needs `configuration.group_by` with property ID and `sort`), `calendar`: Tested. `timeline`: Docs only / Not tested; offer a calendar view or a table sorted by `Start Date` instead.
**Weekly report generator (`API-supported` read + write, `external` if scheduled):** query Tasks with `filter` Status != Done and `Due Date` on_or_before next 7 days, read `Progress` per project, build v2 Markdown (summary, overdue table, risks toggle, next week), create via `v1/pages` under the Reports parent. Dedupe on the title date.

## Examples
Query overdue tasks:
```sh
ntn api v1/data_sources/<TASKS_DATA_SOURCE_ID>/query -d '{"filter":{"and":[{"property":"Status","select":{"does_not_equal":"Done"}},{"property":"Due Date","date":{"before":"2026-11-16"}}]},"page_size":100}' < /dev/null
```
Board view (property ID from `GET v1/data_sources/<id>`):
```sh
ntn api v1/views -d '{"database_id":"<DATABASE_ID>","data_source_id":"<TASKS_DATA_SOURCE_ID>","name":"By Status","type":"board","configuration":{"group_by":{"type":"select","property_id":"<STATUS_PROPERTY_ID>","sort":{"type":"manual"}}}}' < /dev/null
```
Weekly report:
```sh
ntn api v1/pages -d '{"parent":{"type":"page_id","page_id":"<REPORTS_PAGE_ID>"},"markdown":"# 2026-11-09 Weekly Report\n\n## Summary\n\n## Overdue\n\n<toggle>\nRisks\n\n</toggle>\n","markdown_version":"v2"}' < /dev/null
```

## Validation checklist
- Property names/types in each data source match [schema.json](../../../templates/project/schema.json) (re-fetch and diff).
- `Progress` renders like `████████░░ 75%` for Completed 3, Total 4.
- `Urgency` returns `Overdue` for a past due date with Status Todo.
- View count matches plan; no `timeline` view claimed as created.
- Dashboard contains only linked views; one accent; at most 2 callouts per section.
- Report page title matches `YYYY-MM-DD Weekly Report` and appears once.

## Failure handling
- 400 on view create: `group_by` missing `sort` or a name used instead of property ID; fix and resend.
- 400 on formula: expression mismatch; copy the validated expression and re-PATCH.
- 404: database not shared with the integration.
- 429/529: honor `Retry-After`; query about 3 req/s.
- 5xx on page create: query for the report title before retrying.
- Over 100 blocks or 2,000 chars: chunk appends; split paragraphs.
- Relation/rollup rejected: report it as not working, fall back to a number property and say so.

## Safety constraints
- Test only under "Skill Sandbox".
- No deleting or replacing existing project content without approval; archive rather than delete.
- Do not claim timeline views, database buttons or native automations as automated; give click steps.
- Explicit IDs only; never print or store tokens.
