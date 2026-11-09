# Known limitations and UI-only steps

Valid for `ntn` 0.23.28 and the Notion API as tested on 2026-11-09. Re-check with `ntn api ls` after any update.

## UI-only (the user must do these by hand)
| Feature | Why | Exact steps |
|---|---|---|
| Database buttons | No endpoint among the 63 listed by `ntn api ls` | Open the page or database, type `/button`, choose Button, name it, add a trigger action (for example "Add page to" or "Edit property"), save |
| Database automations (triggers, recurring) | No endpoint | Open the database, click `...` (top right), choose Automations, `New automation`, pick a trigger and an action |
| Page and database sharing, permissions | Not in the API surface listed | `Share` menu on the page |
| Workspace settings, members, billing | Not in the API surface listed | Settings in the sidebar |
| Authorizing the Notion MCP | Browser OAuth | In Claude Code run `/mcp`, select `notion`, complete the browser flow, restart the session |

## Plan and platform limits
- **Free plan:** file uploads must use `mode=single_part` (5 MB max); `ntn files create` uses multipart and fails. Free workspaces with more than one member are limited to 1,000 lifetime blocks.
- **`ntn pages create` / `ntn pages edit`** send Markdown v1 (deprecated): toggles, toggle headings, table of contents and synced blocks are not created. Use `ntn api v1/pages` with `"markdown_version":"v2"`.
- **Search** is title search (`v1/search`, "Search by title"); semantic search exists only through the remote MCP, which is Not tested until OAuth is done.
- **Uploaded images** cannot be referenced from Markdown; they need a placeholder swap (see `references/enhanced-markdown.md`).
- **Unattached uploads** expire after roughly an hour.
- **Non-idempotent retries:** a 5xx on POST or PATCH can mean the write succeeded; re-read before retrying.
- **Rate limits:** about 3 requests/s per connection on non-Business plans and about 3/s on data source queries.

## Not tested in this project
- Official remote MCP tools (OAuth pending).
- Codex and Cursor MCP configuration (user chose Claude Code only).
- Comments, page move, template listing, synced block references, styled `<table>`, `<mention>`/`<date>` tags (documented, not exercised).
- Relation values on rows, relation `is_empty` filters, `Open Blockers` rollup, simulated 429/5xx retries.
- `notion-apps` (alpha-gated; left as installed).
- Timeline views (only table, board, calendar and dashboard were tested).

## Future improvements
- Authenticate the MCP and record the real tool list in `docs/install.md`.
- Add Codex and Cursor MCP entries if wanted.
- Run an agent-driven cold-prompt test per skill and a copy-and-rollback migration of a populated database.
- Re-evaluate `lox/notion-cli` if the remote MCP search needs a terminal front end.
