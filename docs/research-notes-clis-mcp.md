# Notion CLI and MCP research notes

Date of research: 2026-11-09. Read-only. Nothing was installed or executed from the cloned repos.
Clones (depth 1) live under `<scratch-dir>`.

## Scored table (1 = poor, 5 = excellent)

Scores are scout judgments from file inspection and GitHub metadata. "Security" is higher when the risk is lower.

| Criterion | lox/notion-cli | vibe-notion (devxoul) | makenotion/notion-mcp-server (self-hosted) | ntn (official CLI) |
|---|---|---|---|---|
| Maintenance / recent commits | 4 (pushed 2026-11-01, 1 open issue) | 4 (pushed 2026-10-26, 0 open issues) | 2 (README says no longer maintained; 212 open issues) | 4 (v0.23.28, beta; release cadence unverified) |
| Example quality | 4 (README quick start, skill file) | 4 (README, templates/*.sh, references/*.md) | 2 (OpenAPI-derived; docs point elsewhere) | 3 (`--help` has examples; not deeply inspected) |
| Documentation | 4 | 4 | 3 (README is detailed but for a deprecated repo) | 3 (help text only) |
| Codex + Claude Code compatibility | 4 (Go binary plus SKILL.md; Codex use unverified) | 4 (SKILL.md plus plugin manifest; Codex use unverified) | 2 (MCP only, needs local token config) | 3 (shell CLI, works from any agent that can run Bash) |
| MCP compatibility | 4 (client for remote MCP, OAuth) | 1 (does not use MCP; uses private web API) | 5 (is an MCP server) | 1 (no MCP surface seen) |
| Security (higher = lower risk) | 3 (OAuth tokens in 0600 file; no telemetry found) | 1 (extracts token_v2 session cookie from the desktop app) | 3 (token in env/config; self-hosted, MIT) | 4 (keychain or env token; no non-Notion hosts seen; unverified in depth) |
| Install requirements | 3 (Go toolchain, or build from source; go >= 1.26 per go.mod) | 2 (Node/Bun, better-sqlite3 native module, sqlite cookie DB access) | 3 (Node, an integration token, JSON config) | 4 (single binary at ~/.local/bin/ntn) |
| Real capabilities | 3 (search, view, create, upload, archive, comments, users via remote MCP) | 4 (broad CRUD incl. private-API features; fragile) | 3 (22 tools, data-source aware; keyword search only) | 4 (pages get/create/edit/trash, files, workers, raw public API) |
| Redundancy with ntn + official MCP | 2 (overlaps remote MCP and ntn) | 1 (overlaps ntn; adds unofficial access) | 1 (superseded by remote MCP) | n/a (baseline) |

## Per-candidate notes

### 1. lox/notion-cli
- Repo: https://github.com/lox/notion-cli. License MIT. Stars 37. Open issues 1. Archived: no.
- Version inspected: commit `f237f53ead3475716757caf726e6068d73bc4060` (committed 2026-11-01). go.mod `go 1.26.0`. No tagged version checked.
- What it is: Go CLI that calls the remote Notion MCP at `https://mcp.notion.com/mcp` (internal/mcp/client.go:21). Also has an "official API fallback" using `https://api.notion.com/v1` with an internal integration token (internal/config/config.go:20, internal/cli/official_api.go). Commands include `page list|view|create|upload|archive`, `search`, `comment`, `auth login|refresh|status|logout`, `auth api setup|verify`.
- MCP tool names it calls (grep): notion-search, notion-fetch, notion-create-pages, notion-update-page, notion-create-comment, notion-get-comments, notion-get-users. These are the remote MCP tool names; verified from lox source, not from Notion's published tool list (unverified against official docs).
- Skill: `skills/notion/SKILL.md` with `allowed-tools: Bash(notion-cli:*)`.
- Install: `go install github.com/lox/notion-cli@latest`, then `notion-cli auth login` (browser OAuth).

Security notes:
- Hosts contacted: mcp.notion.com, api.notion.com, notion.so (profile/integrations link text). Localhost callback for OAuth (internal/mcp/oauth.go:69). No non-Notion hosts found in non-test code.
- Token storage: MCP tokens in a file under a 0700 directory, file mode 0600 (internal/mcp/token_store.go:74-198; internal/config/config.go:279-318). Not keychain-backed.
- Shell exec: `os/exec` appears only in a test file and oauth.go (grep hit in oauth.go not inspected in depth; likely browser open). Unverified.
- Telemetry: none found by grep for "telemetry" or "analytics".
- No postinstall hooks (Go module, no package scripts).

### 2. 4ier/notion-cli
- NOT FOUND. `gh api repos/4ier/notion-cli` returned 404, `gh api users/4ier` returned 404, and `gh search repos "4ier notion"` returned nothing. The slug may be wrong or the repo may be private. Score not assigned. Unverified.

### 3. vibe-notion (devxoul/vibe-notion)
- Repo: https://github.com/devxoul/vibe-notion. npm package `vibe-notion` v1.11.5. License MIT in package.json; the GitHub API reported no license field, so treat the license as unverified at the repo level. Stars 64. Open issues 0. Archived: no.
- Version inspected: commit `282a3cf0c3f5d1db57e3062cdb099fa27ca9f341` (2026-10-26).
- What it is: an "unofficial private API" CLI. Its README says it reads the `token_v2` session cookie from the Notion desktop app so the agent acts as the logged-in user. It calls `https://www.notion.so/api/v3/<endpoint>` (src/platforms/notion/client.ts:41), not the public API. Also includes `vibe-notionbot`, which uses the official Integration API.
- Skill: `skills/vibe-notion/SKILL.md` (metadata says "unofficial private API"). Includes templates and reference docs.
- Install: npm (`vibe-notion`) with Bun or Node. Requires better-sqlite3 (native module) and on Node also a sqlite driver.

Security notes:
- Token extraction: runs `security find-generic-password -s "Notion Safe Storage" -w` to get the macOS keychain item that decrypts the Electron cookie store (src/platforms/notion/token-extractor.ts:244-248). Reads the Notion desktop cookies SQLite DB under ~/Library/Application Support/Notion or Containers paths (token-extractor.ts:304-306). Selects `token_v2`, `notion_user_id`, `notion_users` (token-extractor.ts:345).
- This means the CLI decrypts the desktop app's session cookie. It is a high-privilege credential (full account access, no scope limit). Notion's terms and the official API model are not followed. Treat as a policy and account-risk decision, not just a technical one.
- Hosts: www.notion.so only (api/v3 endpoints, file uploads via file-uploads path). No telemetry found by grep. Did not find child_process use outside the token extractor (grep was limited).
- Lifecycle scripts: package.json has `postbuild`, `prepublishOnly`, `postpublish` (dev/publish only, not install hooks). No `postinstall`. `trustedDependencies` is empty.
- Dependencies are `"latest"` for @notionhq/client, better-sqlite3, commander (no pinned versions). Supply-chain risk.
- Did not run it. Did not verify that the bun.lock pins these.

### 4. Official Notion MCP
Two different products share the name:

(a) Remote Notion MCP at `https://mcp.notion.com/mcp`. The docs page at developers.notion.com/docs/mcp was fetched with curl (saved as `.../scratchpad/research/remote-mcp-docs.html`). The fetched HTML is a client-rendered doc; the tool list did not come through. Tool names seen in lox's source (see above) suggest: notion-search, notion-fetch, notion-create-pages, notion-update-page, notion-create-comment, notion-get-comments, notion-get-users. The docs page links to "Rate limits" (/guides/mcp/rate-limits) and "Use Notion Skills with MCP" (/guides/mcp/notion-skills). The exact rate limit numbers are unverified.
- Auth: OAuth (per the self-hosted repo's note and the lox implementation). Respects each user's Notion permissions.

(b) Self-hosted `makenotion/notion-mcp-server` (npm `@notionhq/notion-mcp-server`, v2.6.1). Repo: MIT, 4703 stars, 212 open issues, pushed 2026-10-29, commit `cf16e5c20bfbfb98ecec1227f210ef0ae3abebe5`. The README says it is no longer actively maintained and points to the remote MCP. Tool count is 22 after v2.0.0. Tools documented in the README include query-data-source, retrieve-a-data-source, update-a-data-source, create-a-data-source, list-data-source-templates, move-page, retrieve-a-database, retrieve-page-markdown, update-page-markdown, plus OpenAPI-derived names such as API-search, API-create-a-comment, API-appendBlockChildren (names from test fixtures in src/openapi-mcp-server/mcp/__tests__/proxy.test.ts). Auth: integration token (`OPENAPI_MCP_HEADERS` / env). Limits: keyword search only; integration sees only pages shared with it.
- Not chosen: do not install. Use only if the remote MCP is unavailable and a bot identity is wanted.

Security notes for (b): token is passed through env/config headers. Source is MIT and public. No postinstall hooks found in package.json (only `"bin"` and build scripts; full scripts list not verified).

### 5. ntn (official Notion CLI)
- Binary: `<LOCAL_PATH>`, version `0.23.28` (from `ntn --version`). Marked "Beta" in help.
- Top-level commands (from `ntn --help`): api, auth, datasources, files (beta), pages, notion-as-code (beta), login, logout, whoami, doctor, update, workers (beta), help.
- `ntn pages` subcommands: trash, get (Markdown), create (from Markdown), edit (Markdown).
- `ntn files` subcommands: create (stdin or external URL), get, list.
- `ntn workers` subcommands include availability, capabilities, create, databases, delete, deploy, download, new, env, exec.
- `ntn api ls` lists 63 public API endpoints (for example POST /v1/pages, GET/PATCH /v1/blocks/{id}, POST /v1/comments, POST /v1/data_sources/{id}/query, POST /v1/databases, POST /v1/file_uploads, PATCH /v1/databases/{id}). Output was truncated in the 40-line window; I used the full count of 63.
- Env: NOTION_API_TOKEN overrides keychain; NOTION_KEYRING=0 uses ~/.config/notion/auth.json (file-based).
- Not run: `ntn login`, `ntn whoami`, `ntn doctor`, any write command. Per the read-only rule.

Security notes: auth via OS keychain by default, file fallback at ~/.config/notion/auth.json. Could not verify the file mode or the hosts it calls (unverified; no source available).

## Comparison: ntn vs lox/notion-cli vs official MCP, per operation

Legend: Y = supported per inspected surface; P = partial or indirect; ? = unverified.

| Operation | ntn | lox/notion-cli | Official remote MCP |
|---|---|---|---|
| Search | ? (no `ntn search`; use `ntn api` on the search endpoint, not inspected) | Y (`notion-cli search`) | Y (notion-search; semantic search per the self-hosted README comparison) |
| Fetch page (read) | Y (`ntn pages get`, Markdown) | Y (`page view`, with comments inline) | Y (notion-fetch) |
| Create page from Markdown | Y (`ntn pages create`) | Y (`page create --content`, `page upload <file.md>`) | Y (notion-create-pages) |
| Update page | Y (`ntn pages edit`, Markdown) | P (`notion-update-page` is wired in client; no CLI command confirmed) | Y (notion-update-page) |
| Database create | Y via `ntn api` POST /v1/databases, or `ntn datasources` | ? (no command found) | ? (remote tool list not verified) |
| Database query | Y via `ntn api` POST /v1/data_sources/{id}/query; `ntn datasources` present | ? | ? |
| Comments (list/create) | Y via `ntn api` /v1/comments | Y (`comment`, notion-get-comments, notion-create-comment) | Y (notion-get-comments, notion-create-comment) |
| File upload | Y (`ntn files create`) | ? (`page upload` is Markdown, not file blobs) | ? |
| Archive / delete | Y (`ntn pages trash`; DELETE /v1/blocks, /v1/comments via api) | Y (`page archive`, official API) | ? (remote tool list not verified) |
| Bulk scripting | Y (`ntn api` with JSON stdin, workers) | P (single-page commands; no batch found) | N (MCP tool calls, not scripted) |

## Recommendation summary
- ntn: install (already present). Use as the default for scripted and bulk Notion work via `ntn pages` and `ntn api`.
- lox/notion-cli: borrow ideas (skill layout, OAuth token store) or install only if a MCP-backed CLI is wanted for agents. Overlaps ntn.
- vibe-notion: skip for this project. Its design reads the desktop app session cookie, which is a high-risk, policy-sensitive credential path.
- Official remote MCP: use for agent-side search and fetch when connected. Prefer it over the self-hosted repo.
- Self-hosted notion-mcp-server: skip. Superseded by remote MCP.
- 4ier/notion-cli: not found. Confirm the slug before any evaluation.

## Unverified claims
- Remote MCP full tool list and rate-limit numbers (docs page did not render as text).
- lox/notion-cli database and file-upload coverage (no command found by grep, not exhaustively checked).
- ntn search and database-query behavior (only endpoint listing seen).
- vibe-notion license at repo level (GitHub API returned none; package.json says MIT).
- Codex compatibility for all candidates (not tested).
- ntn file permission and network hosts (no source).
