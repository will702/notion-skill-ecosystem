# Research template

Purpose: `Sources`, `Notes`, `Hypotheses` and `Experiments` databases where every claim row links to a source, plus a research dashboard. Used by `notion-research-assistant`.

Files: `schema.json` (properties keyed by database; views and formulas carry a `database` field), `page.md` (v2 Markdown).

## Instantiate
Tested end to end (sandbox, ntn 0.23.28). The `Unsourced Claims` relation `is_empty` filter was accepted by the API on view creation, but its query results were not checked.

```bash
python3 -I scripts/instantiate_template.py templates/research --parent <PARENT_PAGE_ID> [--seed] [--set KEY=VALUE] [--manifest f.json] [--dry-run]
```
The script creates the four databases, the relations (`Notes.Source`, `Notes.Hypothesis`, `Experiments.Hypothesis`), the `Citation Check` formula, views and the dashboard page, replacing each `{{VIEW:Database/Name}}` marker (formerly `{{LINKED_VIEW_*}}`) with a linked view. Undo a run with `python3 -I scripts/instantiate_template.py --rollback f.json` (trashes with `in_trash:true`, Tested).

Relations: Tested. The auto-created reverse property is named "Related to <SourceDB> (<PropertyName>)" (for example "Related to Notes (Source)"); rename it only if wanted. The `Unsourced Claims` relation `is_empty` filter and writing relation values stay Docs only.

After instantiation: add sources with `Verification` = `Unverified` unless the user confirms metadata; never invent citations. Verify by querying `Notes` with `Source` `is_empty`; the count should be 0.

## UI-only items
- Database buttons (for example "Add source"), native automations, page sharing.
- Fetching metadata from DOIs or the web is `external` and not part of this template.

Note: only views with a `{{VIEW:Database/Name}}` marker in `page.md` are created (the `Experiments/Calendar` view has none).
