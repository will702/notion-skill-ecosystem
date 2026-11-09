# Knowledge Base template

Purpose: a second-brain starter. One Notes master database related to Areas and Sources, plus a home page with linked views. Methods and design rationale live in `notion-knowledge-architect`; this folder is only the instantiable artifact.

Files: `schema.json` (Notes plus Areas and Sources definitions, format `{"title","properties","views","formulas","seed_rows"}`), `page.md` (v2 home page with `{{VIEW:<name>}}` placeholders).

## Instantiate
Tested end to end (sandbox, ntn 0.23.28). Use `Skill Sandbox` as the parent for tests.

```bash
python3 -I scripts/instantiate_template.py templates/knowledge-base --parent <PARENT_PAGE_ID> [--seed] [--set KEY=VALUE] [--manifest f.json] [--dry-run]
```
The script creates Areas, Sources, Notes, the relations, the `Freshness` formula, views and the home page, and places each `{{VIEW:<name>}}` marker. Undo a run with `python3 -I scripts/instantiate_template.py --rollback f.json` (trashes with `in_trash:true`, Tested).

Relations are created by `PATCH v1/data_sources/<id>` with `data_source_id` plus `single_property:{}` or `dual_property:{}` (Tested). The auto-created reverse property is named "Related to <SourceDB> (<PropertyName>)" (for example "Related to Notes (Area)"), not `Notes`; rename it only if wanted.

## What is UI-only
- Database buttons and database automations (no endpoint): for example a "New Note" button or auto-set Status. Click steps: database `...` menu, Automations (or `+` in a page, Button).
- Page sharing and permissions (Share menu).
- Relation grouping in views if the API rejects it (Not tested); set Group in the view menu.

Relation and rollup property creation is Tested in `references/capability-matrix.md`. Still Docs only: writing relation values on rows and relation `is_empty` filters.
