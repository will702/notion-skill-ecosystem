# Productivity Dashboard template

Purpose: Decide what to do today and this week from one task list. Urgency is a formula on the master Tasks database.

Files: `schema.json` (format defined in `notion-database-architect`), `page.md` (v2 enhanced Markdown with `{{VIEW:<name>}}` markers).

## Instantiate
Tested end to end (sandbox, ntn 0.23.28). Test only under the "Skill Sandbox" page.

```bash
python3 -I scripts/instantiate_template.py templates/dashboards/productivity-dashboard --parent <PARENT_PAGE_ID> [--seed] [--set KEY=VALUE] [--manifest f.json] [--dry-run]
```
The script creates the database, formulas, page and linked views, and replaces each `{{VIEW:<name>}}` marker with its linked view (placement is Tested, see [enhanced-markdown.md](../../../references/enhanced-markdown.md)). Undo a run with `python3 -I scripts/instantiate_template.py --rollback f.json` (trashes with `in_trash:true`, Tested). Skills involved: `notion-database-architect`, `notion-dashboard-builder`.

## UI-only
- Database buttons and automations (for example a button that adds a row): see `notion-interaction-engineer` for click steps.
- Page templates inside the database.
- Sharing the parent page with the integration.
