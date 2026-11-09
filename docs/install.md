# Install and verification log

All output below is from real commands run on 2026-11-09. No secrets are recorded: `ntn` stores its credential in the OS keychain and the Notion MCP entry has no token (OAuth).

## A. CLI: `ntn` (official, beta)

| Item | Result |
|---|---|
| Version | `ntn 0.23.28` (the master prompt cited 0.14.1; treat that as stale) |
| Auth | `ntn whoami`, `ntn doctor`, `ntn api v1/users/me` all succeed (bot user) |
| Install command (fresh machine) | `curl -fsSL https://ntn.dev \| bash`, then `ntn login` |

Sandbox test run (`scratch/cli_tests.py`, results in `scratch/cli_test_results.json`): **17 / 17 passed**.

| Operation | Command used | Result |
|---|---|---|
| Search by title | `ntn api v1/search -d '{"query":...}'` | PASS |
| Retrieve page as Markdown | `ntn pages get <id>` | PASS |
| Create page from Markdown under explicit parent | `ntn pages create --parent page:<id> --content ...` | PASS |
| Markdown round trip (callout, table, `$$` equation, code) | `ntn pages get` after create | PASS, all four block kinds preserved |
| Edit page content | `ntn pages edit <id> --content ...` | PASS (replaces body) |
| Block append / delete | `ntn api v1/blocks/<id>/children -X PATCH`, `... -X DELETE` | PASS |
| Database create with schema | `ntn api v1/databases -d {initial_data_source...}` | PASS |
| Row create in data source | `ntn api v1/pages` with `data_source_id` parent | PASS |
| Query with filter | `ntn api v1/data_sources/<id>/query` | PASS |
| Add Formula 2.0 properties | `ntn api v1/data_sources/<id> -X PATCH` | PASS (both reference formulas accepted) |
| File upload | `mode=single_part` only on the free plan (multipart rejected); see `limitations.md` | PASS in an earlier session |

Reference formulas verified in the sandbox: Progress bar returned `████████░░ 75%` for 3/4, and the urgency flag returned `Overdue` for a past due date.

Operational notes learned the hard way:
- Run `ntn` with stdin closed (`< /dev/null`) in scripts and background jobs, or it can hang waiting on input.
- Retry on 502/503/504/429 with backoff.
- Block-API color names are `blue_background`, not `blue_bg` (the `_bg` form is for enhanced Markdown).

## B. MCP: official Notion MCP

| Item | Result |
|---|---|
| Endpoint | `https://mcp.notion.com/mcp` (HTTP, OAuth) |
| Client configured | Claude Code, **user scope**, one entry |
| Config backup | `~/.claude.json.bak-20261109-231626` (taken before the change) |
| Change | Added user-scope `notion`; removed the older project-scoped `notion` entry (home-dir project) so there is exactly one |
| Other servers | Untouched (verified list unchanged) |
| Status | `claude mcp list`: `notion ... Needs authentication` |

**Pending user step:** open Claude Code, run `/mcp`, choose `notion`, complete the browser OAuth, then start a new session so the tools load. Until then search / read / create / update / query through MCP are **Not tested**.

Codex (`~/.codex/config.toml`) and Cursor (`~/.cursor/mcp.json`) were deliberately not changed (user chose Claude Code only). To add later:
- Codex: `codex mcp add notion --url https://mcp.notion.com/mcp`
- Cursor: add `"notion": {"url": "https://mcp.notion.com/mcp"}` under `mcpServers`.

## C. API

| Item | Result |
|---|---|
| Access path | `ntn api` (OAuth bot user); no raw token stored in the repo |
| Sandbox | Private page "Skill Sandbox" at workspace root; every test write is under it |
| `Notion-Version` | CLI sends its own pinned version by default; override with `NOTION_API_VERSION` or `--notion-version` when a skill needs a specific one |

## Skill installation (2026-11-09)
22 skills symlinked: `~/embedded/.agents/skills/<name>` -> `../../notion-skill-ecosystem/skills/<category>/<name>` and `~/embedded/.claude/skills/<name>` -> `../../.agents/skills/<name>`. Verified: every link resolves to a `SKILL.md`, and Claude Code lists all 22 plus the official `notion-cli` and `notion-apps` (left untouched, `skills-lock.json` unchanged).
Still pending for the user: Notion MCP OAuth (`/mcp`, select `notion`, finish the browser flow, restart).
