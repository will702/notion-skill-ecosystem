# Project Dashboard template

Purpose: Track every project from intake to done, with progress and urgency at a glance. Progress and Urgency are formulas on the master Projects database.

Files: `schema.json` (format defined in `notion-database-architect`), `page.md` (v2 enhanced Markdown with `{{VIEW:<name>}}` markers).

## Instantiate
Tested end to end (sandbox, ntn 0.23.28). Test only under the "Skill Sandbox" page.

```bash
python3 -I scripts/instantiate_template.py templates/dashboards/project-dashboard --parent <PARENT_PAGE_ID> [--seed] [--set KEY=VALUE] [--manifest f.json] [--dry-run]
```
The script creates the database, formulas, page and linked views, and replaces each `{{VIEW:<name>}}` marker with its linked view (placement is Tested, see [enhanced-markdown.md](../../../references/enhanced-markdown.md)). Undo a run with `python3 -I scripts/instantiate_template.py --rollback f.json` (trashes with `in_trash:true`, Tested). Skills involved: `notion-database-architect`, `notion-dashboard-builder`. The zero-total guard in `Progress` is a pattern; re-query one row to verify.

## UI-only
- Database buttons and automations (for example a button that adds a row): see `notion-interaction-engineer` for click steps.
- Page templates inside the database.
- Sharing the parent page with the integration.
