---
name: notion-knowledge-architect
description: Designs second-brain and knowledge-base structure in Notion (PARA, Zettelkasten only where they help), with master databases, relations, cross-linking, retrieval paths and a maintenance routine. Use when the user says "build a second brain", "organize my knowledge", "PARA", "Zettelkasten", "knowledge base structure" or "how should I link my notes".
---

## Purpose
Turn a pile of notes into a retrievable system: decide which method fits, define master databases (Notes, Projects, Areas, Resources/Sources, Tags) with explicit relations, and set linking and maintenance rules. This skill designs and orchestrates; schemas are built by `notion-database-architect`, pages by `notion-page-composer`. Starter artifact: `../../../templates/knowledge-base/README.md`.

## Activation triggers
- "Set up a second brain", "knowledge base", "wiki structure", "PARA in Notion", "Zettelkasten", "my notes are a mess and I can't find things".
- Requests to add Areas, Sources or Tags relations to an existing notes database.
- Not for cleaning existing content (`notion-content-organizer`), read-only health checks (`notion-workspace-auditor`) or lookups (`notion-search-and-retrieval`).

## Required tools
| Capability | Label | Command |
|---|---|---|
| Search existing structure by title | API-supported (Tested) | `ntn api v1/search -d '{"query":"..."}' < /dev/null` |
| Read a page as Markdown | API-supported (Tested) | `ntn pages get <PAGE_ID> < /dev/null` |
| Create databases, add properties, rows | API-supported (Tested) | `v1/databases`, `PATCH v1/data_sources/<id>`, `POST v1/pages` |
| Relations and rollups | API-supported (Tested, property creation) | verify with `GET v1/data_sources/<id>` after PATCH |
| Views and linked views | API-supported (Tested) | `POST v1/views` |
| Semantic search through the remote MCP | MCP-supported (Not tested, OAuth pending) | intended usage only |
| Buttons, automations, sharing | UI-only | give click steps |
CLI basics: [notion-cli](../../../../.claude/skills/notion-cli/SKILL.md). Limits: [api-limits](../../../references/api-limits.md). Matrix: [capability-matrix](../../../references/capability-matrix.md).

## Dependencies
- `notion-database-architect` owns property types, formulas and view creation; this skill only decides which databases and relations exist.
- `notion-page-composer` owns the home page layout (use `../../../templates/knowledge-base/page.md`).
- `notion-workspace-auditor` runs before restructuring an existing workspace; `notion-content-organizer` migrates the old content.
- Naming: [naming](../../../references/naming.md). Layout and data rules: [design-system](../../../references/design-system.md). Formulas: [formulas](../../../references/formulas.md).

## Operating principles
- Least structure that works: start with Notes plus Areas and Sources; add Projects and Tags only when the user has a need that relations cannot already answer.
- One master database per entity; everything else is a linked view (design-system data architecture).
- Relations over free-text tags: a Tags database only if tags are curated; otherwise use Area relation and a select `Type`.
- Every note reaches the user by at least 2 paths: an Area view and a Source or Related Note link.
- Nesting stays within 3 page levels; depth comes from relations, not subpages.
- Never move, rewrite or delete existing notes here; propose, and hand migration to `notion-content-organizer`.

## Detailed workflow
Method decision guide (answer these with the user, then recommend):
| Situation | Use | Skip when |
|---|---|---|
| Work is project-driven with deadlines and ongoing responsibilities | PARA: Projects (finite, outcome), Areas (ongoing), Resources (reference), Archive (inactive) | Fewer than about 10 active items |
| Notes are ideas that should compound, many short atomic notes | Zettelkasten: one idea per note, `Related Note` self-relation, permanent notes distinct from inbox | Notes are mostly meeting logs or documents |
| Material comes from external readings or meetings | Sources database, each note relates to its Source | Everything is original writing |
| Few notes, one topic | Single Notes database with `Status` and `Type` | Never over-build |

Execution protocol:
1. Analyze: classify the request as documentation wiki (reference-heavy), relational tracking database (Projects/Tasks style) or operational dashboard (inbox-first). Most second brains are a wiki with an inbox queue.
2. Retrieve context: `v1/search` for `Notes`, `Projects`, `Areas`, `Sources`, `Tags` (paginate); record parent page ID, existing data source IDs and property names; flag duplicate database names.
3. Plan: show the proposed databases, relations (`Area`/`Notes`, `Source`/`Notes`, `Related Note`), views, and the maintenance routine. If anything touches existing databases, wait for approval.
4. Generate payload: build database and view JSON via a script; validate relation targets exist (create target databases first, order: Areas, Sources, Notes, then self-relation).
5. Execute: create databases, PATCH relations, formulas, views, home page (v2 Markdown), seed rows.
6. Verify: `GET v1/data_sources/<id>` for each, compare properties and relation targets against the plan; `ntn pages get` the home page.
7. Report: home page URL/ID, databases and relation map, active formulas, views, and UI-only steps (buttons, automations, sharing).

Cross-linking rules: `Source` relation for provenance, `Related Note` self-relation for ideas, `<mention url="...">` inline links in note bodies (Docs only) for narrative references. Maintenance cadence: weekly Inbox review, monthly stale review using the `Freshness` formula, quarterly Area review.

## Implementation instructions
Property map (names per naming.md): Notes (`Name`, `Status`, `Type`, `Area`, `Source`, `Related Note`, `Project` optional); Projects (`Name`, `Status`, `Area`, `Due Date`); Areas (`Name`, `Description`); Sources (`Name`, `URL`, `Kind`); Tags only if curated (`Name`). Reverse relation names are plural (`Notes`, `Projects`).
Add a relation: `PATCH v1/data_sources/<NOTES_DATA_SOURCE_ID>` with `{"properties":{"Area":{"relation":{"data_source_id":"<AREAS_DATA_SOURCE_ID>","dual_property":{}}}}}`.
Retrieval design: Inbox view (`Status = Inbox`), `By Area`, `By Status` board (`group_by` with the property ID), and a Stale view driven by the `Freshness` formula from the template.
Alias every proposal to the template when possible instead of inventing a new schema.

## Examples
Check for an existing structure:
```
ntn api v1/search -d '{"query":"Notes","filter":{"property":"object","value":"data_source"},"page_size":100}' < /dev/null
```
Add the Source relation:
```
ntn api v1/data_sources/<NOTES_DATA_SOURCE_ID> -X PATCH -d '{"properties":{"Source":{"relation":{"data_source_id":"<SOURCES_DATA_SOURCE_ID>","dual_property":{}}}}}' < /dev/null
```
Recommendation text pattern: "Method: PARA-lite (Areas and Sources, no Projects yet) because you have 40 notes and no deadlines. Databases: Notes, Areas, Sources. Review: weekly Inbox."

## Validation checklist
- [ ] Each relation re-read via `GET v1/data_sources/<id>` shows the right `data_source_id` and a reverse property.
- [ ] Count of master databases equals the plan; no duplicate names (`v1/search` query per name returns 1 database each).
- [ ] Property and database names pass naming.md (singular properties, plural databases, title property `Name`).
- [ ] Home page has at most 1 callout, 2 columns summing to 100, and a toggle heading `Archive`.
- [ ] No free-text `Tags` multi-select exists next to a Tags database.
- [ ] Every view is a linked view of a master database.

## Failure handling
- 400 validation on a relation: the target data source ID is wrong or not shared; re-read IDs from `data_sources[0].id` and retry.
- 404: integration lacks access to the parent or target; ask the user to share the page (UI-only), do not guess.
- 429: honor `Retry-After`. 5xx on POST/PATCH: re-read before retrying to avoid duplicate databases.
- Rich text over 2,000 characters in seed notes: split into paragraphs. Block-limit (100 children): append in chunks.
- Relation grouping rejected in a view: fall back to a table view and tell the user to group in the UI.
- OAuth not completed for MCP: skip MCP steps and say they are Not tested.

## Safety constraints
- Test only under the "Skill Sandbox" page; never leave test pages elsewhere (naming.md).
- Always pass an explicit parent ID; never create at workspace root.
- Do not edit, move or delete existing notes; approval is required for any change to existing databases.
- Never print or store tokens. Do not replace page bodies with `ntn pages edit --content`.
