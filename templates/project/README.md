# Project template

Purpose: `Projects`, `Tasks`, `Milestones` and `Risks` databases with `Progress` and `Urgency` formulas and a dashboard page. Used by `notion-project-manager`.

Files: `schema.json` (properties keyed by database; views and formulas carry a `database` field), `page.md` (v2 Markdown).

## Instantiate
Tested end to end (sandbox, ntn 0.23.28).

```bash
python3 -I scripts/instantiate_template.py templates/project --parent <PARENT_PAGE_ID> [--seed] [--set KEY=VALUE] [--manifest f.json] [--dry-run]
```
The script creates the four databases, the relations (`Projects.Tasks`, `Tasks.Milestone`, `Milestones.Project`, `Risks.Project`, `Tasks.Blocked By`), the rollups `Total` and `Completed` (Tested), the `Progress` and `Urgency` formulas ([formulas](../../references/formulas.md); the zero guard in `Progress` is a pattern), views, and the dashboard page. `{{VIEW:Database/Name}}` markers (formerly `{{LINKED_VIEW_*}}` placeholders) are replaced by linked views. Undo a run with `python3 -I scripts/instantiate_template.py --rollback f.json` (trashes with `in_trash:true`, Tested).

Relations: Tested. The auto-created reverse property is named "Related to <SourceDB> (<PropertyName>)" (for example "Related to Tasks (Milestone)"); rename it only if wanted. Still Docs only: writing relation values, relation `is_empty` filters, rollup `Open Blockers`, rollup of formulas.

The `timeline` view stays Docs only and was removed from `schema.json`; a `Milestones/All` table view was added instead.

## UI-only items
- Timeline view (not claimed via API), database buttons, native automations (for example Status to Done sets `Is Done`): database `...` menu, Automations.
- Page and database sharing.

Note: the script creates a linked view only for each `{{VIEW:Database/Name}}` marker in `page.md`. Schema views without a marker (for example `Projects/By Status`, `Tasks/Calendar`) are not created; add a marker where you want one.
