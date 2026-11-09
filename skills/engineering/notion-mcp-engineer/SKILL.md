---
name: notion-mcp-engineer
description: Configures, diagnoses and optimizes the official remote Notion MCP server (https://mcp.notion.com/mcp) across Claude Code, Codex and Cursor, including OAuth, tool discovery, permissions and context cost. Use when the user says "set up Notion MCP", "Notion MCP needs authentication", "which Notion MCP tool", "MCP vs ntn" or "Notion MCP not showing tools".
---

# Notion MCP Engineer

## Purpose
Get exactly one working Notion MCP entry per client, authenticated through OAuth, then pick the right tools and keep context cost low. All MCP behavior below is intended usage and is **Not tested** until OAuth is completed (see [capability-matrix](../../../references/capability-matrix.md)).

## Activation triggers
- "add / install / configure Notion MCP", "Notion MCP needs authentication", "tools missing".
- "should I use MCP or ntn for this", "semantic search in Notion", "fetch this page through MCP".
- Duplicate or stale `notion` entries across projects or clients.

## Required tools
- Claude Code CLI: `claude mcp list|add|remove|get`, in-session `/mcp`. Label: MCP-supported (config is `external`).
- Codex CLI `codex mcp add|list` and Cursor `~/.cursor/mcp.json`: Not tested.
- `ntn` for fallback and for verification of whatever MCP wrote. Label: API-supported.
- Browser for the OAuth consent screen. Label: UI-only.

## Dependencies
- [capability-matrix](../../../references/capability-matrix.md) for labels; [api-limits](../../../references/api-limits.md) for the API limits behind `ntn`. MCP rate limits are unverified.
- Install state and the pending OAuth step: `../../../docs/install.md`; decision table: `../../../docs/research-report.md`.
- Owns MCP configuration and tool selection. `notion-api-engineer` owns raw REST, `notion-cli-engineer` owns terminal workflows, page layout belongs to `notion-page-composer`.

## Operating principles
1. Official remote server only: `https://mcp.notion.com/mcp`, HTTP transport, OAuth. No token or secret in any config file.
2. Exactly one Notion MCP entry per client. Duplicates (user vs project scope) cause ambiguous tools; remove the extra one.
3. Timestamped backup before touching a client config, for example `cp ~/.claude.json ~/.claude.json.bak-$(date +%Y%m%d-%H%M%S)`.
4. Inspect before change: run `claude mcp list` first.
5. Discover, do not assume: tool names come from the server after auth.
6. Self-hosted `makenotion/notion-mcp-server` is rejected (unmaintained, superseded).

Choose MCP vs `ntn` (from the research report):
| Task | Prefer |
|---|---|
| Conversational exploration, semantic search | MCP (Not tested) |
| Search by exact title, scripted | `ntn api v1/search` |
| Fetch page as Markdown | `ntn pages get` (tested); MCP fetch is Not tested |
| Create from enhanced Markdown | `ntn pages create` or `ntn api v1/pages` (tested) |
| Bulk, looped, resumable work | `ntn api` + `notion-api-engineer` |
| Buttons, automations | UI-only, neither |

## Detailed workflow
Execution protocol (workspace-touching tasks):
1. **Analyze**: classify the request (dashboard, relational database, wiki) and whether it needs conversation (MCP) or repeatability (`ntn`).
2. **Retrieve context**: `claude mcp list`; read `docs/install.md`; for pages, search first and collect parent IDs and schemas.
3. **Plan**: state client, scope, entry name, and the first read-only tool call; wait for approval before changing any config or existing content.
4. **Generate payload**: config command or tool arguments, with explicit parent IDs.
5. **Execute**: configure, authenticate, restart, run discovery, then tools.
6. **Verify**: `claude mcp list` shows `notion ... Connected`; re-fetch what a write produced (with the MCP fetch tool and `ntn pages get <ID>`) and compare.
7. **Report**: entry state per client, tool list found, what was written (URL/ID), UI-only steps left.

Setup sequence (Claude Code):
1. `claude mcp list` (check for existing `notion`).
2. Backup `~/.claude.json` with a timestamp.
3. `claude mcp add --scope user --transport http notion https://mcp.notion.com/mcp`
4. In a session run `/mcp`, choose `notion`, finish browser OAuth (UI-only).
5. Restart the session so tools load.
6. Tool discovery (below), then record the real list.

## Implementation instructions
- Codex (Not tested): `codex mcp add notion --url https://mcp.notion.com/mcp`, then `codex mcp list`. Backup `~/.codex/config.toml` first.
- Cursor (Not tested): in `~/.cursor/mcp.json` add under `mcpServers`: `"notion": {"url": "https://mcp.notion.com/mcp"}`. Backup first; keep other servers untouched; restart Cursor and authenticate in its MCP panel.
- Tool names reported by research (from the lox/notion-cli source, not from the server): `notion-search`, `notion-fetch`, `notion-create-pages`, `notion-update-page`, `notion-create-comment`, `notion-get-comments`, `notion-get-users`. The exact tool list is **Not tested** until authenticated.
- Discovery step after auth: list the tools the client exposes (Claude Code: `/mcp` then `notion`, or ask the agent to list its `mcp__notion__*` tools), copy names and one-line descriptions, and append them to `../../../docs/install.md` under section B as "Verified tool list (date)". This skill does not edit docs itself; hand the list to the lead.
- Selection: search -> fetch -> then create/update. Fetch before every update and update the narrowest scope (single page properties, not whole body).
- Context optimization: scope searches (title keywords, one data source), fetch single pages rather than whole trees, summarize large fetches before continuing, drop unused tool output, and use `ntn` for bulk operations that would flood context.
- Permissions: approve read tools freely; require explicit confirmation for create/update tools; the OAuth grant limits what the server can see (workspace sharing is UI-only).

## Examples
```bash
claude mcp list
cp ~/.claude.json ~/.claude.json.bak-$(date +%Y%m%d-%H%M%S)
claude mcp add --scope user --transport http notion https://mcp.notion.com/mcp
claude mcp get notion
claude mcp remove notion --scope project   # only to delete a duplicate, after backup
codex mcp add notion --url https://mcp.notion.com/mcp
```
Cursor entry (Not tested):
```json
{"mcpServers": {"notion": {"url": "https://mcp.notion.com/mcp"}}}
```
Intended first calls after auth (Not tested): `notion-search` with query "Skill Sandbox", then `notion-fetch` on the returned page.

## Validation checklist
- [ ] `claude mcp list | grep -c '^notion'` prints 1 (one entry); same check for other clients.
- [ ] A backup file with a timestamp exists and is newer than the change.
- [ ] `claude mcp list` shows `notion` as Connected, not `Needs authentication`.
- [ ] The discovered tool list is non-empty and was recorded (name plus description).
- [ ] No token, key or secret appears in any config.
- [ ] After a write, `ntn pages get <ID>` matches the intended content.

## Failure handling
- `Needs authentication`: run `/mcp`, choose `notion`, complete OAuth in the browser, restart. If it persists, `claude mcp remove notion` then re-add (after backup), re-authenticate.
- Tools absent after auth: restart the session; check `claude mcp get notion`; confirm the URL has no typo.
- Two `notion` entries: keep the user-scope one, remove the other after backup.
- Tool returns 404 or no results: page not shared with the OAuth grant (UI-only); share it, retry.
- Tool errors or rate limits: MCP limits are unverified; back off, then fall back to `ntn api` (see `notion-api-engineer` retry rules: 5xx on writes needs re-read first).
- Large fetch floods context: narrow the query, use `ntn pages get` and read only the section needed.
- Client not tested (Codex, Cursor): report the exact command used and its output; do not claim success.

## Safety constraints
- Test only on the "Skill Sandbox" page; give every write an explicit parent ID.
- Never delete or overwrite user content without explicit approval; prefer archive/trash.
- Never write tokens into configs or logs; OAuth only.
- Do not modify other MCP servers or other clients' configs unless asked; always back up first.
