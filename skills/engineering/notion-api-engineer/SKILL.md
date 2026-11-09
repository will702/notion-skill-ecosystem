---
name: notion-api-engineer
description: Designs and debugs direct Notion REST API usage through `ntn api`: auth, Notion-Version pinning, pagination, rate limits, block and database operations, data-source endpoints, error handling and safe retries. Use when the user says "call the Notion API", "paginate results", "429 rate limit", "retry Notion request", "data source vs database endpoint" or "pin Notion-Version".
---

# Notion API Engineer

## Purpose
Make raw Notion API calls correct, resumable and safe: right endpoint, right version, bounded request size, paginated reads, and retries that never duplicate a write. Calls go through `ntn api` (API-supported); the helper `scripts/notion_request.py` adds retry and pagination around it.

## Activation triggers
- "call the Notion API", "query a data source", "paginate", "next_cursor", "has_more".
- Errors: 400 validation_error, 404 object_not_found, 409 conflict, 429, 502/503/504, 529.
- "pin the Notion version", "which endpoint replaced databases query", "integration capabilities".
- Writing a script that loops over many pages or blocks.

## Required tools
- `ntn` (0.23.28 tested): `ntn api <path> [-X METHOD] [-d JSON] [key==value]`, `ntn api ls`, `ntn api <path> --help|--docs|--spec`. Label: API-supported.
- `python3` (stdlib only) for `scripts/notion_request.py`. Label: external.
- Official CLI skill for syntax reference: `/Users/gregoriuswillson/embedded/.claude/skills/notion-cli/SKILL.md` (do not duplicate it).

## Dependencies
- Limits and retry policy: [api-limits](../../../references/api-limits.md). This skill implements them; it never restates the numbers beyond what a rule needs.
- Block shapes and colors: [enhanced-markdown](../../../references/enhanced-markdown.md); label checks: [capability-matrix](../../../references/capability-matrix.md).
- Owns raw API mechanics. `notion-database-architect` owns schema design, `notion-cli-engineer` owns interactive terminal workflows, `notion-mcp-engineer` owns MCP, `notion-migration-engineer` owns bulk moves.

## Operating principles
1. Read-only first: `GET`, search and `--help` before any write.
2. Pin the version for reproducible scripts: `--notion-version <VERSION>` per call or `NOTION_API_VERSION=<VERSION>` in the environment. Without either, `ntn` sends its own pinned default. Take `<VERSION>` from `ntn api <path> --docs`, never from memory.
3. Data-source era: a database is a container; its tables are data sources. Create with `POST v1/databases` (`initial_data_source`), read and alter schema with `GET`/`PATCH v1/data_sources/<id>`, query with `POST v1/data_sources/<id>/query`, create rows with parent `{"type":"data_source_id",...}`. Do not use `databases/<id>/query` or database-level `properties`.
4. Retry rules (from api-limits): 429 and 529 always, 5xx only GET/DELETE; after a 5xx on POST/PATCH re-read and compare first.
5. Integration capabilities (read content, update content, insert content, comments, user info) are set in the integration settings, which is UI-only. A 403 `restricted_resource` means a missing capability; a 404 usually means the page is not shared with the integration (Share menu, UI-only).
6. Never print or store tokens. `ntn` uses the keychain or `NOTION_API_TOKEN`.

## Detailed workflow
Execution protocol (workspace-touching tasks):
1. **Analyze**: is the target an operational dashboard, a relational tracking database or a documentation wiki? This picks the endpoints.
2. **Retrieve context**: `v1/search` for parent IDs; `GET v1/data_sources/<id>` for the schema; check duplicate names.
3. **Plan**: print method, path, body skeleton and expected request count; wait for approval if existing content changes.
4. **Generate payload**: build JSON, split text under 2,000 chars, arrays at most 100, at most 2 nesting levels per append.
5. **Execute**: create or append, then properties and formulas. Use `scripts/notion_request.py` for loops.
6. **Verify**: re-fetch (`GET v1/pages/<id>`, `v1/blocks/<id>/children`) and compare counts and key fields.
7. **Report**: page URL or ID, schema, request count, retries seen, anything UI-only (capabilities, sharing).

Retry matrix:
| Status | GET/DELETE | POST/PATCH |
|---|---|---|
| 429, 529 | retry with backoff | retry with backoff |
| 500, 502, 503, 504 | retry with backoff | stop, re-read, compare, then decide |
| 400, 401, 403, 404, 409 | no retry, fix cause | no retry, fix cause |

## Implementation instructions
- Helper (`API-supported` via `ntn`, `external` for the Python):
  `python3 -I scripts/notion_request.py v1/users/me`
  `python3 -I scripts/notion_request.py v1/search -d '{"query":"Roadmap"}' --paginate`
  `--dry-run` prints the `ntn` command without running it.
- In Python: `from notion_request import request, paginate, NtnError`. `request()` runs `ntn` with `stdin=DEVNULL`, backs off with full jitter on 429/529 (Retry-After is not exposed through `ntn` stdout, so it cannot be honored; if you call REST directly, honor the header first), and raises `NtnError(retryable_after_verify=True)` for a 5xx on a write.
- `paginate()` follows `has_more`/`next_cursor`, `page_size` 100. POST endpoints take `start_cursor` in the body; GET endpoints take `start_cursor==<cursor>`.
- Blocks: read `ntn api v1/blocks/<ID>/children page_size==100`; append with `-X PATCH -d '{"children":[...]}'`; position with `"position":{"type":"after_block","after_block":{"id":"<ID>"}}`; delete with `-X DELETE v1/blocks/<ID>` (archives).
- Throttle query loops to about 3 requests/s (data source query limit); sleep 0.35 s between pages if not using the helper.
- The helper reads the HTTP status from the JSON error body when present, else from the first 4xx/5xx number in the output. Error output shape of `ntn` is Not tested for every status; the lead should confirm on the sandbox.

## Examples
```bash
ntn api v1/users/me < /dev/null
ntn api v1/search -d '{"query":"Skill Sandbox","filter":{"property":"object","value":"page"}}' < /dev/null
ntn api v1/data_sources/<DATA_SOURCE_ID> < /dev/null
ntn api v1/data_sources/<DATA_SOURCE_ID>/query -d '{"page_size":100,"filter":{"property":"Status","status":{"equals":"Done"}}}' < /dev/null
ntn api v1/pages -d '{"parent":{"type":"data_source_id","data_source_id":"<DATA_SOURCE_ID>"},"properties":{"Name":{"title":[{"text":{"content":"Row 1"}}]}}}' < /dev/null
ntn api v1/blocks/<PAGE_ID>/children -X PATCH -d '{"children":[{"type":"paragraph","paragraph":{"rich_text":[{"text":{"content":"Hello"}}]}}]}' < /dev/null
NOTION_API_VERSION=<VERSION> ntn api v1/users/me < /dev/null
ntn api v1/users/me --notion-version <VERSION> < /dev/null
python3 -I scripts/notion_request.py v1/data_sources/<DATA_SOURCE_ID>/query -X POST -d '{}' --paginate
```

## Validation checklist
- [ ] `python3 -I -m py_compile scripts/notion_request.py` exits 0; `--help` and `--dry-run` run without Notion access.
- [ ] Every script call has stdin closed (`< /dev/null` or `DEVNULL`).
- [ ] Paginated read: item count equals the UI or `GET` count, and the last page returned `has_more: false`.
- [ ] After each write, a re-fetch shows the expected block or property count.
- [ ] No POST/PATCH is retried after a 5xx without a recorded re-read.
- [ ] Text runs under 2,000 chars, arrays at most 100, payload under 500 KB.
- [ ] No token appears in output, files or shell history.

## Failure handling
- 400 validation_error: print the body, fix the field (block colors use `gray_background`, Markdown uses `gray_bg`; mixing gives 400), resend once.
- 404 object_not_found: ask the user to share the page with the integration (UI-only); confirm with `v1/users/me`.
- 403: capability missing in integration settings (UI-only); report which one.
- 429/529: back off and retry; stop after the cap and report. A 429 with `rate_limit_reason: public_api_request_blocked` is not retried.
- 5xx on POST/PATCH: stop, re-read the target, compare with intent, resend only the missing part.
- 502 on GET/DELETE: retry; repeated failure after the cap goes to the user with the request path.
- Rich text over 2,000 chars or more than 100 elements: split and append in chunks.
- Free multi-member workspace block cap (1,000 lifetime blocks): stop and report.

## Safety constraints
- Test only under the "Skill Sandbox" page; always pass an explicit parent ID.
- Never delete or overwrite user content without explicit approval; prefer archive/trash over permanent deletion.
- Do not loop writes without a dry run and a request-count estimate.
- Never print, log or commit tokens; do not set `NOTION_API_TOKEN` inline in commands.
