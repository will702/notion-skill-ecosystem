# Research report

Date: 2026-11-09. Detail lives in `research-notes-clis-mcp.md` and `research-notes-skills.md`; this file is the decision summary. Scores are 1-5 (higher is better) on: maintenance, examples, docs, Codex+Claude Code compatibility, MCP compatibility, security, install effort, real capabilities, low redundancy.

## Decision matrix

| Candidate | Score summary | Decision | Reason |
|---|---|---|---|
| `ntn` official CLI 0.23.28 | maint 4, security 4, caps 4, install 4 | **Install (done), primary CLI** | Already installed; passed 17/17 sandbox operations including search, Markdown round trip, database and formula work |
| Official remote Notion MCP | MCP 5 | **Use (configured, OAuth pending)** | First-party; conversational search/fetch/edit. Tool list and rate limits did not render from docs, so they are **unverified** until authenticated |
| `lox/notion-cli` (MIT, f237f53) | maint 4, security 3, redundancy 2 | **Borrow ideas, do not install** | Overlaps `ntn` plus the remote MCP; needs a recent Go toolchain; CLI decision rule forbids two CLIs for the same job |
| `vibe-notion` (devxoul 1.11.5) | security 1, redundancy 1 | **Skip** | Extracts the desktop app's `token_v2` session cookie via the macOS keychain; unofficial private API, ToS and account-wide credential risk |
| `makenotion/notion-mcp-server` (self-hosted) | maint 2, redundancy 1 | **Skip** | README says unmaintained; superseded by the remote MCP |
| `4ier/notion-cli` | not found (404) | **Skip, unverified** | Repo or slug does not exist publicly |
| `makenotion/skills` notion-cli | 4/4/4 | **Keep (already installed)** | Official; custom skills reference it instead of copying. `notion-apps` is alpha-gated and left as is |
| `makenotion/notion-cookbook` (MIT, 1d52d1f) | maint 5, examples 5 | **Borrow ideas** | Pagination and query patterns, mcp-clients workflow skills |
| `mattppal/formatting-notion-pages` | maint 2, security 5 | **Borrow ideas** | Block reference and API limits (re-verify limits) |
| `markus41/Claude-m` Notion Mastery | docs 5, caps 5, license unclear | **Borrow ideas** | Strongest design guidance; its Markdown syntax differs from the official spec, so only design ideas are taken |
| TrevorS, aneym, harlanljones | not found | **Skip** | 404 or not found |
| vladchatware, tellang (extras) | caps 3 | **Borrow ideas** | `block-types.md` examples; field-filter idea for token savings |

## CLI vs MCP per operation (verified)
| Task | Prefer | Evidence |
|---|---|---|
| Search by title | `ntn api v1/search` | PASS in sandbox run |
| Fetch page as Markdown | `ntn pages get` | PASS |
| Create page from enhanced Markdown | `ntn pages create --parent page:<id> --content` | PASS (callout, table, equation, code round-tripped) |
| Replace page content | `ntn pages edit <id> --content` | PASS |
| Block append/delete | `ntn api v1/blocks/<id>/children`, `/blocks/<id>` | PASS |
| Database create, rows, filtered query, formulas | `ntn api v1/databases`, `v1/pages`, `v1/data_sources/<id>/query` and `PATCH` | PASS |
| File upload | `ntn api v1/file_uploads` with `mode=single_part` on the free plan | PASS (earlier session); `ntn files create` fails on free plan (multipart) |
| Conversational exploration, semantic search | Remote MCP | Not tested (OAuth pending) |
| Buttons, automations, some view settings | UI-only | See `limitations.md` |

## Supply-chain notes
Both official skills tell users to run `curl -fsSL https://ntn.dev | bash`. That is a pipe-to-shell from a non-Notion host; on this machine `ntn` is already installed, so the command is not re-run. No third-party repository was installed or executed in this project.
