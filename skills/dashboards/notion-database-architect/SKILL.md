---
name: notion-database-architect
description: Designs normalized Notion database schemas (properties, relations, rollups, formulas, status workflows, templates, integrity, duplicate detection) and defines the `schema.json` template format. Use when the user says "design a database", "database schema", "add a relation", "rollup", "avoid duplicate databases", or "audit my databases".
---

# Notion Database Architect

## Purpose

Produce the smallest correct set of master databases for a use case: one reason to exist per database, explicit relations instead of repeated text, formulas that live next to the data. Owns schemas and the `schema.json` format; does not build dashboard pages (see `notion-dashboard-builder`).

## Activation triggers

"design a schema", "what properties do I need", "should this be a relation or a select", "add a rollup", "status workflow", "find duplicate databases", "database template", "create schema.json".

## Required tools

- `ntn api v1/search`, `ntn api v1/databases` (POST), `ntn api v1/data_sources/<id>` (GET, PATCH), `ntn api v1/data_sources/<id>/query` (POST): `API-supported`, Tested.
- Relation and rollup property types via `PATCH v1/data_sources/<id>`: `API-supported`, Tested (property creation; see [capability matrix](../../../references/capability-matrix.md)).
- Template list `v1/data_sources/<id>/templates`: `API-supported`, Docs only. Creating or editing database page templates: `UI-only` (no endpoint).
- CLI basics: the official `notion-cli` skill.

## Dependencies

- [naming.md](../../../references/naming.md) for every name, [formulas.md](../../../references/formulas.md) for validated formulas, [api-limits.md](../../../references/api-limits.md) for retry rules.
- `notion-dashboard-builder` consumes the schemas; `notion-interaction-engineer` owns views, buttons and automations on them. This skill owns property choice and integrity.

## Operating principles

1. One database per entity (Projects, Tasks, Meetings). A new database needs a sentence stating what it stores that no existing one does.
2. Relation over repeated text. A relation named for the target in singular (`Project`), reverse in plural (`Tasks`).
3. Derived values are formulas or rollups (`Progress`, `Urgency`, `Open Task Count`), never typed by hand.
4. Status workflow: `select` with plain-text options (`Todo`, `In Progress`, `Done`). Native `status` option sets cannot be reliably defined at creation through the API (Not tested), so templates use `select`.
5. Integrity: required fields are enforced by views (a `Needs Owner` filter), not by hope; booleans use `Is`/`Has`.
6. Never rename a property a formula references.

## Detailed workflow

Execution protocol (all steps mandatory):
1. **Analyze**: operational dashboard, relational tracking database, or documentation wiki? Only the second needs this skill's full output.
2. **Retrieve context**: `ntn api v1/search -d '{"query":"<entity>"}' < /dev/null`; GET each candidate data source; list existing names to detect duplicates and case-only twins.
3. **Plan**: print entities, properties (name, type, why), relations, formulas. Wait for approval if any existing database changes.
4. **Generate payload**: write `schema.json` (format below); validate that every formula references existing property names and every `group_by_property` exists.
5. **Execute**: create database, PATCH formulas and relations, then seed rows. After a 5xx on POST/PATCH re-read before retrying.
6. **Verify**: GET the data source, compare property names and types to `schema.json`; query one row and read each formula result.
7. **Report**: database URL/ID, data source ID, schema table, active formulas, UI-only leftovers (templates, buttons).

### Schema-design checklist

- [ ] Entity named as plural Title Case noun; title property `Name`.
- [ ] No free-text field duplicates another database (use relation).
- [ ] Each select has 3-6 options, Title Case, no emoji.
- [ ] Each date has a purpose (`Due Date` drives Urgency and calendars).
- [ ] Every formula needs only properties in this database or its rollups.
- [ ] Reverse relation named plural; rollups prefixed by purpose.
- [ ] At least one view per question the dashboard asks.
- [ ] Duplicate detection plan (below).

## Implementation instructions

### `schema.json` format (used by `templates/`)

```json
{
  "title": "Tasks",
  "properties": { "<Name>": { "<notion property type>": {} } },
  "views": [ { "name": "By Status", "type": "board", "filter": null, "sorts": [], "group_by_property": "Status" } ],
  "formulas": { "Urgency": "ifs(...)" },
  "seed_rows": [ { "Name": "Example", "Status": "Todo" } ]
}
```
- `title` (string): database title, plural Title Case.
- `properties` (object): key is the property name; value is the exact Notion API property schema (`{"title":{}}`, `{"select":{"options":[{"name":"Todo"}]}}`, `{"date":{}}`, `{"number":{"format":"number"}}`, `{"checkbox":{}}`, `{"relation":{...}}`). Exactly one `title` property. Formulas are NOT listed here.
- `formulas` (object): name to Formula 2.0 expression string. Applied after create with `PATCH v1/data_sources/<id>` as `{"properties":{"<Name>":{"formula":{"expression":"..."}}}}`.
- `views` (array): `name` (question-style or naming.md view name), `type` (`table`|`board`|`calendar`), `filter` (a filter object in data-source-query syntax with property names, or `null`), `sorts` (array, may be empty), `group_by_property` (property NAME, required for `board`, `null` otherwise; the instantiator resolves it to the property ID). Calendar views need a date property: add `"date_property"` (name) as an optional extra key. Filter shape accepted by `v1/views` should be confirmed with `ntn api v1/views --spec`; if IDs are required, swap names for IDs from GET data source.
- `seed_rows` (array): objects keyed by property name with plain values (string, number, boolean, ISO date string); convert to API property values per type. Optional, keep at most 5.

### Duplicate detection

Before create: search by title and by `Name` with case folding; abort if a database with the same normalized title exists under the same parent. For rows: query `filter: {"property":"Name","title":{"equals":"<value>"}}` before every insert; skip or ask. Use a formula `lower(trim(prop("Name")))` only if a dedupe view is requested.

## Examples

```bash
ntn api v1/databases -d '{"parent":{"type":"page_id","page_id":"<PARENT_PAGE_ID>"},"title":[{"type":"text","text":{"content":"Projects"}}],"initial_data_source":{"properties":{"Name":{"title":{}},"Status":{"select":{"options":[{"name":"Todo"},{"name":"In Progress"},{"name":"Done"}]}},"Due Date":{"date":{}}}}}' < /dev/null
ntn api v1/data_sources/<DATA_SOURCE_ID> -X PATCH -d '{"properties":{"Urgency":{"formula":{"expression":"ifs(empty(prop(\"Due Date\")), \"No date\", dateBetween(prop(\"Due Date\"), now(), \"days\") < 0 and prop(\"Status\") != \"Done\", \"Overdue\", \"On track\")"}}}}' < /dev/null
ntn api v1/data_sources/<DATA_SOURCE_ID>/query -d '{"filter":{"property":"Name","title":{"equals":"Alpha"}}}' < /dev/null
```
Relation (Tested; reverse property is named "Related to <SourceDB> (<PropertyName>)"): `{"properties":{"Project":{"relation":{"data_source_id":"<PROJECTS_DS_ID>","single_property":{}}}}}`.

## Validation checklist

- [ ] `GET v1/data_sources/<id>` property names and types equal `schema.json` `properties` plus `formulas` keys.
- [ ] Query one row: each formula returns a non-error string/number.
- [ ] Search shows exactly one database with the title under the parent.
- [ ] Row count equals `len(seed_rows)`.
- [ ] No two property names differ only by case.
- [ ] Every `group_by_property` and `date_property` exists in `properties`.

## Failure handling

- 400 validation: print the offending property; usual causes are `_bg` colors, status option sets, or an unknown relation target. Fix payload, do not loop.
- 404 object not found: the parent or data source is not shared with the integration; ask the user to share it (UI-only).
- 429/529: honor `Retry-After`, retry. 5xx on POST/PATCH: re-read, compare, then retry only if missing.
- Rich text over 2,000 chars in a seed row: split or trim.
- Relation or rollup rejected: report the rejection and leave the property for UI creation.

## Safety constraints

- Test only under the dedicated "Skill Sandbox" page; always pass an explicit parent ID.
- Never delete properties, rows or databases without explicit approval; archive instead.
- Never print or store tokens. Run `ntn` with stdin closed.
- Changing an existing schema requires an approved plan first.
