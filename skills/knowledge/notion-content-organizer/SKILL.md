---
name: notion-content-organizer
description: Categorizes, tags, adds metadata, migrates and cleans up Notion content while preserving the original, using a plan-then-approve workflow with a change manifest and rollback manifest. Use when the user says "organize my pages", "tag these notes", "migrate into this database", "clean up", "move these pages" or "categorize".
---

## Purpose
Apply structure to existing content (properties, relations, moves) safely. Nothing is deleted; every change is planned, approved, executed from a manifest and reversible through a rollback manifest.

## Activation triggers
- "Categorize these notes", "add tags and areas", "move these pages under X", "migrate this page list into the Notes database", "clean up my workspace".
- After `notion-workspace-auditor` produced findings, or after `notion-knowledge-architect` defined the target structure.

## Required tools
| Capability | Label | Command |
|---|---|---|
| Find pages (title search) | API-supported (Tested) | `ntn api v1/search` |
| Read page and properties | API-supported (Tested) | `ntn pages get <ID>`, `GET v1/pages/<ID>` |
| Update properties | API-supported (Tested for data source rows via `v1/pages`; PATCH on existing pages Docs only) | `ntn api v1/pages/<ID> -X PATCH -d '{"properties":{...}}'` |
| Move a page | API-supported (Docs only) | `POST v1/pages/<ID>/move` (pages; confirm database support before use, otherwise UI-only) |
| Archive/trash | API-supported (Tested) | `PATCH v1/pages/<ID>` with `{"in_trash":true}`, approval only |
| Semantic bulk grouping through MCP | MCP-supported (Not tested) | intended usage only |
| Sharing, bulk UI "Move to" for databases | UI-only | give click steps |
CLI basics: [notion-cli](../../../../.claude/skills/notion-cli/SKILL.md). Limits: [api-limits](../../../references/api-limits.md). Matrix: [capability-matrix](../../../references/capability-matrix.md).

## Dependencies
- `notion-database-architect` owns target schemas and new properties; this skill only fills them.
- `notion-knowledge-architect` defines categories, Areas and relations; `notion-workspace-auditor` supplies findings; `notion-search-and-retrieval` helps locate candidates.
- Naming: [naming](../../../references/naming.md). Design rules for any page left behind: [design-system](../../../references/design-system.md).

## Operating principles
- Preserve first: never edit page bodies, never use `ntn pages edit --content` (it replaces the body and can delete subpages).
- Prefer property updates and relations over moves; prefer moves over copies.
- Plan, show, wait for approval, execute from the manifest, verify, report.
- NEVER delete. Archive or trash only for items the user explicitly named, and record them in the rollback manifest.
- Batches of at most 20 items per approval round; about 3 req/s.
- A 5xx on PATCH or POST means re-read before retrying (duplicate or half-applied write).

## Detailed workflow
1. Analyze: decide whether this is taxonomy work (properties), relational linking (relations) or wiki reshaping (moves).
2. Retrieve context: `v1/search` (paginated) and `ntn pages get` for candidates; `GET v1/data_sources/<id>` for target schema and property IDs; record each item's current parent, property values and `last_edited_time`; check duplicate names at the destination.
3. Plan: write the change manifest (below) and a human summary table; no execution. Wait for explicit approval of the manifest, naming any items that would be trashed.
4. Generate payload: from the approved manifest build one request per change; validate select options exist, relation targets exist, rich text under 2,000 characters, arrays of at most 100 relations.
5. Execute: write the rollback manifest first (current values and parents), then apply changes in order, throttled; stop on first unexpected error.
6. Verify: re-read each changed page and compare to the manifest `after` values; count applied versus planned.
7. Report: items changed, skipped, failed; manifests' file paths; page URLs/IDs; anything UI-only (for example moving a database, sharing).

Operation menu:
- Tag or categorize: `PATCH v1/pages/<ID>` with select, multi-select or relation values.
- Metadata: fill `Type`, `Source`, `Area`, dates; never overwrite a non-empty value unless the manifest says `overwrite: true`.
- Move: `POST v1/pages/<ID>/move` with the new parent. Databases and their rows: change the row's `Area` relation instead.
- Migrate: create new rows in the target data source (`POST v1/pages`, copy title and properties, put the original URL in a `Source` URL property), leave originals in place; offer trashing the originals only after the user reviews.

## Implementation instructions
Change manifest (JSON list, save under the scratchpad or a local file, never inside the workspace):
```
[{"id":"<PAGE_ID>","op":"set_property","property":"Area","before":[],"after":["<AREA_PAGE_ID>"],"reason":"matches Area Health by title"},
 {"id":"<PAGE_ID>","op":"move","before":{"page_id":"<OLD_PARENT_ID>"},"after":{"page_id":"<NEW_PARENT_ID>"},"reason":"misfiled"},
 {"id":"<PAGE_ID>","op":"trash","before":{"in_trash":false},"after":{"in_trash":true},"requires_approval":true,"reason":"duplicate of <OTHER_ID>"}]
```
Rollback manifest: the same list with `before` and `after` swapped for every executed item (trash reverses with `{"in_trash":false}`), written before execution and appended per item as it succeeds.
Move payload: `{"parent":{"type":"page_id","page_id":"<NEW_PARENT_ID>"}}`; confirm the exact body shape with `ntn api v1/pages/<ID>/move --help` or docs before the first call (Docs only).

## Examples
```
ntn api v1/pages/<PAGE_ID> -X PATCH -d '{"properties":{"Area":{"relation":[{"id":"<AREA_PAGE_ID>"}]},"Status":{"select":{"name":"Active"}}}}' < /dev/null
ntn api v1/pages/<PAGE_ID>/move -X POST -d '{"parent":{"type":"page_id","page_id":"<NEW_PARENT_ID>"}}' < /dev/null
ntn api v1/pages/<PAGE_ID> < /dev/null   # verify parent and properties after
```
Rollback of a property change: PATCH the `before` value from the rollback manifest.

## Validation checklist
- [ ] Approved manifest exists and its item count equals planned count.
- [ ] Rollback manifest was written before the first write and has one entry per executed change.
- [ ] After execution, re-read of every changed page matches `after` (count of mismatches is 0).
- [ ] No page body changed: block count via `GET v1/blocks/<ID>/children` before and after is equal for sampled pages.
- [ ] No `trash` op ran without `requires_approval` confirmed by the user.
- [ ] Select options and relation targets existed before the PATCH.

## Failure handling
- 400 validation: unknown select option or wrong property type; fix the manifest, do not auto-create options without approval.
- 404: page not shared with the integration; skip and list it.
- 429: sleep `Retry-After`. 5xx on PATCH/POST: re-read the page; if the change applied, mark done, else retry once.
- Rich text over 2,000 characters in a metadata field: split or shorten, ask the user.
- Block-limit or free-workspace 1,000 block limit on migration copies: stop and report.
- Partial run: apply the rollback manifest for the failed items only if the user asks; otherwise report state.

## Safety constraints
- NEVER delete content; archive or trash only with explicit approval per item and a rollback entry.
- Never overwrite non-empty properties or page bodies without approval; never run `ntn pages edit --content`.
- Test only on the dedicated "Skill Sandbox" page; always use explicit parent IDs.
- Never print or store tokens; keep manifests free of page body text.
