---
name: notion-dashboard-builder
description: Builds Notion dashboards (productivity, project, academic, business, research, finance, team, knowledge) from linked views of master databases using the Views API. Use when the user says "build a dashboard", "project dashboard", "linked database view", "add a board view to a page", or "dashboard from my database".
---

# Notion Dashboard Builder

## Purpose

Assemble a dashboard page that contains only linked views of master databases, with summary first, queues second, archive last. Owns the page plus view wiring; schemas belong to `notion-database-architect`, layout blocks to `notion-page-composer`, buttons/automations to `notion-interaction-engineer`.

## Activation triggers

"build a dashboard", "project/academic/finance/team dashboard", "linked view of Tasks", "board grouped by Status", "dashboard view with widgets", "instantiate a dashboard template".

## Required tools

- `ntn api v1/views` (POST), `v1/data_sources/<id>` (GET), `v1/pages` (POST, `markdown_version: "v2"`), `v1/blocks/<id>/children`: `API-supported`, Tested.
- Linked database block (`create_database`), `type: "dashboard"` view and widget views (`view_id`): `API-supported`, Tested.
- Buttons, database automations: `UI-only`. Charts and timers: `external` (see `notion-widget-integrator`).
- `ntn` usage: the official `notion-cli` skill.

## Dependencies

- [design-system.md](../../../references/design-system.md) (one accent, 2 columns 30/70, archive toggle), [naming.md](../../../references/naming.md), [enhanced-markdown.md](../../../references/enhanced-markdown.md), [capability-matrix.md](../../../references/capability-matrix.md).
- `notion-database-architect` owns master databases and `schema.json`; `notion-page-composer` owns page layout; `notion-interaction-engineer` owns filters/buttons; ready templates live in `templates/dashboards/`.

## Operating principles

1. Master database vs linked view: rows, formulas and relations live only in master databases; a dashboard never holds rows or pasted copies.
2. Each linked view answers one named question (`Due This Week`, `By Status`).
3. One neutral accent (`gray` default), 2 columns with ratios summing to 100, at most one status callout.
4. Pages needing toggles or TOC use `v1/pages` with `"markdown_version":"v2"`.
5. Property IDs, not names, in view configuration.

## Detailed workflow

Execution protocol (all steps mandatory):
1. **Analyze**: this is an operational dashboard over relational tracking databases. If no master database exists, hand off to `notion-database-architect` first.
2. **Retrieve context**: search parent page and master database; GET the data source and record each property `id`; check for an existing page titled `<X> Dashboard`.
3. **Plan**: list views (name, type, filter, group), layout (left 30 counters/links, right 70 board/queue), UI-only items. Wait for approval if existing pages change.
4. **Generate payload**: build page Markdown with standalone `{{VIEW:<name>}}` markers (templates do this), build one JSON body per view with a script; never hand-quote JSON.
5. **Execute**: create the page, then each view (below), then verify placement.
6. **Verify**: `ntn pages get <PAGE_ID>`; list children of the page; `GET v1/views/<id>` for each view; compare type, filter and group to plan.
7. **Report**: page URL/ID, layout, view list, formulas used, UI-only steps (buttons, automations).

## Implementation instructions

Exact call sequence (all `API-supported`, Tested):
1. `GET v1/data_sources/<DATA_SOURCE_ID>`: read `properties.<Status>.id` for `group_by`.
2. Create the page: `POST v1/pages` with `markdown` and `markdown_version: "v2"`.
3. Linked database block with a view, one request per view:
   `POST v1/views` body: `data_source_id`, `name`, `type` (`table`|`board`|`calendar`), `create_database: {"parent":{"type":"page_id","page_id":"<PAGE_ID>"},"show_data_source_title":false}`, optional `filter`, `sorts`, `configuration`. Exactly one of `database_id`, `view_id`, `create_database`.
4. Board: `configuration: {"group_by":{"type":"select","property_id":"<STATUS_PROP_ID>","sort":{"type":"manual"}}}`; `type` matches the property type; `sort` is required.
5. Dashboard view (widgets): `POST v1/views` with `database_id`, `data_source_id`, `name`, `type: "dashboard"`; then each widget `POST v1/views` with `view_id: <DASHBOARD_VIEW_ID>` instead of `database_id`.
6. Placement: `create_database` appends the block at the end of the page; moving it to the marker via `PATCH v1/pages/<id>/markdown` `update_content` is `API-supported`, Tested (also inside columns); see [enhanced-markdown.md](../../../references/enhanced-markdown.md). [scripts/instantiate_template.py](../../../scripts/instantiate_template.py) automates this.
7. The marker text is replaced by the view tag in step 6; if placing manually, remove a leftover `{{VIEW:...}}` paragraph only after its view exists.
Template instantiation is automated: `python3 -I scripts/instantiate_template.py templates/<name> --parent <PAGE_ID>` (see the script's `--dry-run`).
Dashboard kinds map to schemas: productivity (Tasks), project (Projects+Tasks), academic (Assignments), business (Deals/Accounts), research (Sources), finance (Transactions), team (Tasks+Meetings), knowledge (Pages index). Use `notion-database-architect` for each.

## Examples

```bash
ntn api v1/data_sources/<DATA_SOURCE_ID> < /dev/null
ntn api v1/views -d '{"data_source_id":"<DATA_SOURCE_ID>","name":"By Status","type":"board","create_database":{"parent":{"type":"page_id","page_id":"<PAGE_ID>"},"show_data_source_title":false},"configuration":{"group_by":{"type":"select","property_id":"<STATUS_PROP_ID>","sort":{"type":"manual"}}}}' < /dev/null
ntn api v1/views -d '{"database_id":"<DATABASE_ID>","data_source_id":"<DATA_SOURCE_ID>","name":"Overview","type":"dashboard"}' < /dev/null
ntn api v1/views -d '{"view_id":"<DASHBOARD_VIEW_ID>","data_source_id":"<DATA_SOURCE_ID>","name":"Open Tasks","type":"table"}' < /dev/null
```
Compare the output of `ntn api v1/views --spec` if a field is rejected.

## Validation checklist

- [ ] `ntn pages get <PAGE_ID>` shows title ending in ` Dashboard`, one purpose line, at most one callout.
- [ ] Children list contains one linked database block per planned view (count equals plan).
- [ ] Each board view has `group_by.property_id` equal to the ID from step 1.
- [ ] No database was created by this run other than approved masters (search count unchanged).
- [ ] `<columns>` ratios sum to 100; one accent color only.
- [ ] No `{{VIEW:` text remains in the page Markdown.

## Failure handling

- 400 on `group_by`: name used instead of ID, or `sort` missing; re-fetch the data source.
- 400 on colors: `_bg` vs `_background` mix-up.
- 404: page or data source not shared with the integration; ask the user to share it.
- 429/529: wait `Retry-After`. 5xx on POST: list page children and `v1/views` before retrying, to avoid duplicate linked blocks.
- Block limit (free multi-member workspace, 1,000 lifetime blocks) or 100-element array limit: chunk requests.
- View filter shape rejected: check `--spec`, try property IDs.

## Safety constraints

- Test only on the "Skill Sandbox" page; explicit parent ID always.
- Never delete or overwrite existing pages/blocks without approval; `ntn pages edit --content` replaces the body, back up first.
- Never copy rows into a dashboard; never print tokens; stdin closed (`< /dev/null`).
