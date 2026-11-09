---
name: notion-migration-engineer
description: Plans and executes Notion schema changes and page or database migrations with a manifest, old-to-new ID mapping, relation reconstruction, schema diff, validation and rollback. Use when the user says "migrate a database", "copy pages to a new database", "change a property type", "rebuild relations", "schema diff" or "rollback a migration".
---

# Notion Migration Engineer

## Purpose
Move or reshape Notion content without risking the original: plan first, drive everything from a manifest, copy rather than move, validate by schema diff, row counts and spot checks, and roll back by trashing only what the migration created. All operations are API-supported unless noted; relation and rollup property creation is Tested ([capability-matrix](../../../references/capability-matrix.md)); writing relation values on migrated rows is Docs only, so verify on the sandbox first.

## Activation triggers
- "migrate / copy / restructure this database", "split or merge databases".
- "change a property type", "rename options", "add a relation between databases".
- "diff two schemas", "validate migration", "roll back".

## Required tools
- `ntn api` (API-supported): `GET/PATCH v1/data_sources/<ID>`, `POST v1/data_sources/<ID>/query`, `POST v1/pages`, `POST v1/databases`, `PATCH v1/pages/<ID>` (trash). Always `< /dev/null`.
- `scripts/schema_diff.py` (stdlib Python, external) and `jq` optional.
- `../notion-api-engineer/scripts/notion_request.py` for retries and pagination.

## Dependencies
- [api-limits](../../../references/api-limits.md) (3 req/s query, 100-element arrays, retry rules), [naming](../../../references/naming.md), [capability-matrix](../../../references/capability-matrix.md).
- Owns migration planning and validation. `notion-database-architect` owns the target schema design; `notion-api-engineer` owns request mechanics; `notion-cli-engineer` owns page export/import by Markdown.

## Operating principles
1. Plan first, manifest-driven: nothing is written until the manifest and plan are approved.
2. Copy, not move, by default. The original stays untouched until validation passes and the user approves any retirement.
3. Maintain an ID mapping table `old_id -> new_id` for every page and row; relations are rebuilt from it.
4. Rollback trashes only objects listed in the manifest as created by this migration. Never touch originals.
5. Idempotence: before creating, check the manifest; after a 5xx on POST/PATCH re-read the target before resending (duplicate risk).
6. Rows are copied in batches of at most 100 objects, paced to about 3 requests/s.

Manifest (JSON file, kept outside Notion), fields: `source_data_source_id`, `target_parent_id`, `created` (list of `{kind, old_id, new_id, title}`), `skipped`, `errors`, `started_at`.

## Detailed workflow
Execution protocol:
1. **Analyze**: is the source an operational dashboard, relational tracking database or documentation wiki? Dashboards are rebuilt after data; relational databases need relation order; wikis need page tree order.
2. **Retrieve context**: `GET v1/data_sources/<SOURCE_DS_ID>` saved to `source-schema.json`; query row count; search the target parent for duplicate names; list relations and rollups.
3. **Plan**: show target schema, creation order, batch plan, request estimate, rollback list. Wait for approval (existing content is never altered, but the plan must still be approved).
4. **Generate payload**: build create-database body and row payloads; map property types; drop read-only types (formula results, rollups, created/last-edited time) and recreate formula/rollup definitions in the schema, not in rows.
5. **Execute** in this order: (a) create target database with plain properties (title, text, number, select/multi_select/status with options, date, checkbox, url); (b) copy rows without relation values, recording the ID mapping; (c) create relation properties, targets before sources: independent databases first, then those that relate to them, then reverse relations; (d) fill relation values by translating old IDs through the mapping; (e) add rollups, then formulas that depend on them; (f) create views with property IDs from a fresh `GET`.
6. **Verify**: `GET v1/data_sources/<NEW_DS_ID>` -> `new-schema.json`; run `python3 -I scripts/schema_diff.py source-schema.json new-schema.json`; compare row counts; spot-check at least 5 rows (or 5%), including one with relations.
7. **Report**: URLs/IDs of the new objects, schema diff output, counts, mapping file location, rollback command list, UI-only leftovers (button and automation recreation, sharing, page-level permissions).

## Implementation instructions
- Schema diff (external): `python3 -I scripts/schema_diff.py OLD.json NEW.json`. Compares property names, types and select/multi_select/status option names; exit 0 identical, 1 differences, 2 error. Expected differences are listed in the plan (for example renamed or retyped properties).
- Property changes on an existing database are PATCHes and change content in place: only on a copied database. `PATCH v1/data_sources/<ID>` with `{"properties":{"Old":{"name":"New"}}}` renames; setting `null` removes a property (destructive: needs approval and a prior copy).
- Select option changes: PATCH the property with the full option list; existing row values keep matching names only if names match.
- Relation reconstruction: property creation Tested; writing relation values Docs only. A relation property points at a target data source; create after both exist; write relation values as `{"relation":[{"id":"<NEW_PAGE_ID>"}]}` (at most 100 per request) using the mapping table. Dual (reverse) properties are created with the relation; check the schema afterward.
- Pages with bodies: `ntn pages get <OLD_ID>` then create under the new row with `ntn api v1/pages` (`markdown_version:"v2"` if toggles or TOC) per `notion-cli-engineer`. Block-level copy: read `v1/blocks/<ID>/children`, append in chunks of at most 100, nesting at most 2 levels per request.
- Not migratable through the API: view-level quirks beyond create parameters, buttons, database automations, page permissions (UI-only), comments history and page edit history (not copied; say so in the report).
- Files: uploaded files are workspace-hosted; re-upload or reuse the external URL, and attach within about an hour of upload.

## Examples
```bash
ntn api v1/data_sources/<SOURCE_DS_ID> < /dev/null > source-schema.json
ntn api v1/databases -d '{"parent":{"type":"page_id","page_id":"<TARGET_PARENT_ID>"},"title":[{"text":{"content":"Tasks"}}],"initial_data_source":{"properties":{"Name":{"title":{}},"Due Date":{"date":{}}}}}' < /dev/null
ntn api v1/data_sources/<SOURCE_DS_ID>/query -d '{"page_size":100}' < /dev/null
ntn api v1/pages -d '{"parent":{"type":"data_source_id","data_source_id":"<NEW_DS_ID>"},"properties":{"Name":{"title":[{"text":{"content":"Row 1"}}]}}}' < /dev/null
ntn api v1/data_sources/<NEW_DS_ID> -X PATCH -d '{"properties":{"Project":{"relation":{"data_source_id":"<TARGET_DS_ID>","single_property":{}}}}}' < /dev/null
ntn api v1/pages/<NEW_PAGE_ID> -X PATCH -d '{"properties":{"Project":{"relation":[{"id":"<NEW_PROJECT_PAGE_ID>"}]}}}' < /dev/null
python3 -I scripts/schema_diff.py examples/source-schema.json examples/target-schema.json
ntn api v1/pages/<NEW_PAGE_ID> -X PATCH -d '{"in_trash":true}' < /dev/null   # rollback, manifest objects only (trash flag: Tested)
```
`examples/source-schema.json` and `examples/target-schema.json` are hand-made samples; the diff reports a missing relation, a renamed date, a retyped select and a dropped status option.

## Validation checklist
- [ ] `schema_diff.py` exits 0, or every reported difference is listed in the approved plan.
- [ ] Row count of target equals row count of source (paginate queries to `has_more: false`).
- [ ] Mapping table has one entry per source row; no duplicate `new_id`.
- [ ] Spot check: at least 5 rows match on title, select, date and relation targets.
- [ ] Relation values resolve to new-database pages, none point to originals.
- [ ] Source database row count and schema unchanged (re-run `GET` and diff against the saved `source-schema.json`: exit 0).
- [ ] Manifest `created` list matches what exists under `<TARGET_PARENT_ID>`.

## Failure handling
- 400 validation (unknown property, wrong type): fix the payload; do not retry unchanged. Read-only types cannot be written.
- 404: target or related data source not shared with the integration; ask the user to share (UI-only).
- 409 conflict on schema PATCH: re-read the schema and resend once.
- 429/529: back off and retry. 5xx on GET: retry. 5xx on POST/PATCH: query the target for the row by title or manifest, create only if absent.
- Relation write fails: the related page is not in the mapping yet; defer it to a second pass.
- Rich text over 2,000 characters or arrays over 100: split.
- Partial run: resume from the manifest; never restart blindly.
- Validation fails: keep the original, run rollback of manifest objects, report.

## Safety constraints
- Test only on the "Skill Sandbox" page; give every create an explicit parent ID.
- Never modify, delete or overwrite originals; rollback trashes only manifest-listed created objects (trash, not permanent delete).
- Never remove a property or retire the source without explicit approval after validation.
- Do not print or store tokens.
