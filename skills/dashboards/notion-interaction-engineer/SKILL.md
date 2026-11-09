---
name: notion-interaction-engineer
description: Adds interactivity to Notion workspaces (views, filters, sorts, grouping, relations, formulas, buttons, automations, synced blocks, templates, embeds), labeling each item API-supported, UI-only or external. Use when the user says "add a filter", "board grouped by", "add a button", "set up an automation", "synced block", or "make this interactive".
---

# Notion Interaction Engineer

## Purpose

Turn static pages and databases into interactive ones, and state honestly which parts the API can do and which the user must click. Owns views, filters, buttons, automations and synced blocks; schemas belong to `notion-database-architect`, dashboard assembly to `notion-dashboard-builder`, embeds to `notion-widget-integrator`.

## Activation triggers

"filter by", "sort by", "group by status", "calendar view", "button that creates a task", "automate when status changes", "sync this header across pages", "page template".

## Required tools

- `ntn api v1/views`, `v1/data_sources/<id>`, `v1/blocks/<id>/children`, `v1/pages`: see labels below.
- Official `notion-cli` skill for `ntn` syntax. MCP is intended usage only (Not tested, OAuth pending).

## Dependencies

- [capability-matrix.md](../../../references/capability-matrix.md) is authoritative for every label; [formulas.md](../../../references/formulas.md), [enhanced-markdown.md](../../../references/enhanced-markdown.md), [naming.md](../../../references/naming.md).
- Hands off schema changes to `notion-database-architect`, embeds to `notion-widget-integrator`.

## Operating principles

1. Label every item before proposing it; never promise a `UI-only` item as automated.
2. Prefer a view with a filter over a copied database.
3. Views use property IDs for grouping, names in docs for people.
4. Interactivity must serve a question; no decorative toggles or buttons.

## Detailed workflow

Execution protocol (all steps mandatory):
1. **Analyze**: is the target an operational dashboard, relational tracking database, or documentation wiki?
2. **Retrieve context**: fetch the data source (property IDs and types), existing views, existing buttons (visible only in UI).
3. **Plan**: table of item, label, evidence (matrix), who does it. Wait for approval before changing existing views.
4. **Generate payload**: JSON per view via script; click-step list for UI-only items.
5. **Execute**: API-supported items first, then hand the UI-only list to the user.
6. **Verify**: `GET v1/views/<id>` and compare; query the data source with the same filter and check row counts.
7. **Report**: URLs/IDs, what was created, active formulas, UI-only steps still pending.

## Implementation instructions

Capability labels:
| Item | Label | Evidence |
|---|---|---|
| Table, board (`group_by`), calendar views | `API-supported` | Tested |
| View filters and sorts (`filter`, `sorts` on create) | `API-supported` | Tested |
| Board grouping | `API-supported` | Tested: `configuration.group_by` with `property_id` and `sort` |
| Dashboard and widget views | `API-supported` | Tested |
| Formula 2.0 properties | `API-supported` | Tested |
| Relations and rollups | `API-supported` | Tested (property creation) |
| Synced block original | `API-supported` | Tested (v2 Markdown `<synced-block>`) |
| Synced block reference on another page | `API-supported` | Docs only (needs the original's block URL) |
| Data source template list | `API-supported` | Docs only |
| Creating or editing page templates | `UI-only` | no endpoint |
| Database buttons | `UI-only` | no endpoint |
| Database automations | `UI-only` | no endpoint |
| Scheduled or webhook-style automation | `external` | Docs only (`ntn workers` or cron) |
| Embeds | `external` | Not tested |

Button click steps (`UI-only`): 1. Open the page or database. 2. Type `/button` (or click `+` in the database header, then Button). 3. Name it with a verb (`Add Task`). 4. Add action `Add page to` and choose the database, set property defaults. 5. Optionally add `Edit property` or `Open page`. 6. Click Done and press the button once to test on the sandbox.
Automation click steps (`UI-only`): 1. Open the database. 2. Click the `...` menu, choose Automations (or Properties, then Automations). 3. Add a trigger (`Page added`, `Property edited`, or Recurring). 4. Add an action (`Edit property`, `Add page to`, `Send notification`). 5. Save, toggle on, edit one row to confirm.

## Examples

```bash
# Filtered, sorted table view

ntn api v1/views -d '{"database_id":"<DATABASE_ID>","data_source_id":"<DATA_SOURCE_ID>","name":"Open","type":"table","filter":{"property":"Status","select":{"does_not_equal":"Done"}},"sorts":[{"property":"Due Date","direction":"ascending"}]}' < /dev/null
# Calendar view

ntn api v1/views -d '{"database_id":"<DATABASE_ID>","data_source_id":"<DATA_SOURCE_ID>","name":"Calendar","type":"calendar"}' < /dev/null
```
Synced header on a page (v2 Markdown): `<synced-block>` newline content newline `</synced-block>`.
If `--spec` shows a different filter or sort shape, follow `ntn api v1/views --spec`; try property IDs if names are rejected.

## Validation checklist

- [ ] Every proposed item has exactly one label that matches the matrix.
- [ ] `GET v1/views/<id>` returns the planned type, filter and sorts.
- [ ] Board `group_by.property_id` equals the property ID from `GET v1/data_sources/<id>`.
- [ ] Query with the view's filter returns the same row count as the view shows.
- [ ] Report lists each UI-only item with its click steps.

## Failure handling

- 400: `group_by` missing `sort`, name instead of ID, color spelling; fix and resend once.
- 404: not shared with the integration; ask the user to share the page.
- 429/529: honor `Retry-After`. 5xx on POST: re-list views before retrying.
- Relation/rollup rejected: report the rejection, give UI steps instead.
- Button/automation requested via API: refuse, supply click steps.

## Safety constraints

- Sandbox only ("Skill Sandbox" page), explicit parent IDs.
- Do not delete or alter existing views, buttons or automations without approval.
- Automations can write to many rows; confirm trigger and action scope with the user before they enable it.
- Never print tokens; stdin closed.
