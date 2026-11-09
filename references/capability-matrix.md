# Capability matrix

Labels: `API-supported` (works through `ntn api` / REST), `MCP-supported` (official remote MCP), `UI-only` (user must do it by hand), `external` (needs an embed or integration).
Evidence column: **Tested** = executed on the sandbox with `ntn` 0.23.28 on 2026-11-09; **Docs only** = endpoint or syntax exists in current docs but was not exercised; **Not tested** = no evidence. MCP rows stay **Not tested** until the OAuth step is completed.

| Capability | Label | Evidence | How |
|---|---|---|---|
| Search by title | API-supported | Tested | `ntn api v1/search` |
| Read page as Markdown | API-supported | Tested | `ntn pages get <id>` |
| Create page from Markdown under explicit parent | API-supported | Tested | `ntn pages create` (v1) or `ntn api v1/pages` with `markdown_version: "v2"` |
| Replace page body | API-supported | Tested | `ntn pages edit <id> --content` |
| Callouts, quotes, dividers, to-dos, code, equations, pipe tables | API-supported | Tested | enhanced Markdown |
| Columns with ratio | API-supported | Tested | `<columns><column ratio=..>` |
| Toggles, toggle headings, table of contents | API-supported | Tested (v2 only) | `markdown_version: "v2"` |
| Synced block, original | API-supported | Tested (v2) | `<synced-block>`; reference to an existing one needs its URL (Docs only) |
| Block append / delete | API-supported | Tested | `v1/blocks/<id>/children` PATCH, `v1/blocks/<id>` DELETE |
| Database create with schema | API-supported | Tested | `v1/databases` with `initial_data_source` |
| Add / change properties | API-supported | Tested | `v1/data_sources/<id>` PATCH |
| Formula 2.0 properties | API-supported | Tested | reference formulas accepted and evaluated |
| Rows with properties, filtered query, sorts | API-supported | Tested | `v1/pages` (data_source parent), `v1/data_sources/<id>/query` |
| Views: table, board with `group_by`, calendar | API-supported | Tested | `v1/views` (`group_by` needs `sort`; property ids, not names) |
| View filters and sorts | API-supported | Tested | `filter`, `sorts` on create |
| Dashboard view and widget views | API-supported | Tested | `type: "dashboard"`, then `view_id` + widget body |
| Linked database block on a page | API-supported | Tested | `v1/views` with `create_database` |
| Relations and rollups | API-supported | Tested | `v1/data_sources/<id>` PATCH, tested across 4 linked databases (project, research, knowledge-base, meeting-notes templates). A relation needs `data_source_id` plus `single_property:{}` or `dual_property:{}` (the script sets the type key). The auto-created reverse property on the target is named "Related to <SourceDB> (<PropertyName>)" (e.g. "Related to Tasks (Milestone)"); rename only if wanted. Rollups (Projects.Completed, Projects.Total) work. Still Docs only: writing relation values on rows, relation `is_empty` filters, rollup `Open Blockers`, rollup of formulas |
| Linked view placement at a position on the page | API-supported | Tested | `v1/views` `create_database` appends the block at the page end; move it with `PATCH v1/pages/<id>/markdown` `update_content`; see enhanced-markdown.md. Works inside columns; automated by `scripts/instantiate_template.py` |
| Page markdown update_content | API-supported | Tested | `PATCH v1/pages/<id>/markdown` |
| Trash / restore page or database | API-supported | Tested (trash) | `in_trash:true` via `v1/pages/<id>` and `v1/databases/<id>` PATCH; used by `instantiate_template.py --rollback` |
| File upload and image blocks | API-supported | Tested | `mode=single_part` on the free plan, up to 5 MB |
| Page icon and cover | API-supported | Not tested (tested in the cover-and-icon skill validation) | `v1/pages/<id>` PATCH |
| Comments | API-supported | Docs only | `v1/comments` |
| Move page | API-supported | Docs only | `v1/pages/<id>/move` |
| Data source templates (list) | API-supported | Docs only | `v1/data_sources/<id>/templates` |
| Search, fetch, create, update through MCP | MCP-supported | Not tested (OAuth pending) | remote MCP `https://mcp.notion.com/mcp` |
| Database buttons | UI-only | no endpoint among the 63 listed by `ntn api ls` | User: open the database, click `+` in the header or a page, choose Button, set trigger and actions |
| Database automations (triggers/recurring) | UI-only | no endpoint among the 63 listed | User: database `...` menu, Automations (or Properties, then Automations), add trigger and action |
| Scheduled or external automations | external | Docs only | `ntn workers` or an external cron calling the API |
| Interactive widgets (clock, timer, charts) | external | Not tested | embed block with a hosted URL; check the host allows iframes |
| Synced block reference on another page | API-supported | Docs only | `<synced-block-reference url="...">` using the original's URL; a page URL is never valid |
| Page-level permissions / sharing | UI-only | not in the endpoint list | Share menu |
| Workspace settings, members, billing | UI-only | not in the endpoint list | Settings |

Re-run `ntn api ls` after every `ntn update`; this table is only valid for the version tested.
