# Meeting Notes template

Purpose: a `Meetings` database plus an `Action Items` database (relation to each meeting) and a structured meeting page. Used by `notion-meeting-intelligence`.

Files: `schema.json` (properties keyed by database name, views and formulas carry a `database` field), `page.md` (v2 Markdown with `{{PLACEHOLDERS}}`).

## Instantiate
Tested end to end (sandbox, ntn 0.23.28).

```bash
python3 -I scripts/instantiate_template.py templates/meeting-notes --parent <PARENT_PAGE_ID> [--seed] [--set KEY=VALUE] [--manifest f.json] [--dry-run]
```
The script creates `Meetings` and `Action Items`, the `Action Items.Meeting` relation, the `Urgency` formula ([formulas](../../references/formulas.md)), and the `Meetings` page; this template defines no linked views. The relation `Meetings.Project` points outside the template (to `PROJECTS_DS_ID`) and is skipped with a NOTE unless you pass `--set PROJECTS_DS_ID=<data source id>`. Undo a run with `python3 -I scripts/instantiate_template.py --rollback f.json` (trashes with `in_trash:true`, Tested).

Relations are created by `PATCH v1/data_sources/<id>` (Tested); the auto-created reverse property is named "Related to <SourceDB> (<PropertyName>)" (for example "Related to Action Items (Meeting)"); rename it only if wanted. Writing relation values on rows stays Docs only.

## UI-only items
- Recurring meeting creation: database button or native automation (database `...` menu, Automations); scripted alternative is `external` (see `notion-automation-engineer`).
- Database buttons such as "New meeting from template".
