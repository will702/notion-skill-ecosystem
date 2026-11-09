---
name: notion-cli-engineer
description: Runs Notion terminal workflows with the official `ntn` CLI: search, read, create, update, import/export, batch scripts and validation, and decides between `ntn` and lox/notion-cli. Use when the user says "use ntn", "Notion CLI", "create a page from Markdown", "export a page", "upload a file to Notion", "batch update Notion" or "which Notion CLI".
---

# Notion CLI Engineer

## Purpose
Perform Notion operations from the terminal with the correct `ntn` command form, safe defaults and verification. Routes each operation to `ntn`, to the API, or elsewhere. Builds on the official skill `~/.claude/skills/notion-cli/SKILL.md` (reference it, do not duplicate it).

## Activation triggers
- "use ntn", "Notion CLI", "ntn pages create", "export this page to Markdown", "import Markdown".
- "upload a file", "ntn files create fails", "deploy a worker", "ntn doctor".
- "which CLI should I use", "should I install lox/notion-cli".

## Required tools
- `ntn` 0.23.28 (installed, primary). Label: API-supported. Self-describing: `ntn --help`, `ntn api ls`, `ntn api <path> --help|--docs|--spec`.
- `ntn workers` for deployable automations. Label: external (Docs only).
- Shell utilities (`jq` optional). Label: external.

## Dependencies
- [api-limits](../../../references/api-limits.md), [capability-matrix](../../../references/capability-matrix.md), [enhanced-markdown](../../../references/enhanced-markdown.md).
- Decisions: `../../../docs/research-report.md`. Owns terminal workflows. `notion-api-engineer` owns retries/pagination code, `notion-mcp-engineer` owns MCP, `notion-migration-engineer` owns schema and database moves, `notion-page-composer` owns layout.

## Operating principles
1. `ntn` is primary and installed. `lox/notion-cli` is borrow-ideas only (not installed: it overlaps `ntn` and the remote MCP and needs a Go toolchain). `vibe-notion` is rejected (extracts the desktop `token_v2` session cookie, account-wide credential risk). One CLI per job.
2. Scripts and background jobs run `ntn` with stdin closed: `< /dev/null`.
3. Read before write: `ntn whoami`, `ntn pages get`, search.
4. Look up syntax with `--help`/`--docs` rather than guessing.
5. `ntn pages edit <ID> --content` REPLACES the body and can delete subpages; back up first and get approval.

Routing per operation (research report):
| Operation | Command | Label |
|---|---|---|
| Search by title | `ntn api v1/search -d '{"query":"..."}'` | API-supported (tested) |
| Read page as Markdown | `ntn pages get <ID>` | API-supported (tested) |
| Create page from Markdown | `ntn pages create --parent page:<ID> --content` | API-supported (tested) |
| Create with toggles, TOC, synced block | `ntn api v1/pages` + `markdown_version:"v2"` | API-supported (tested) |
| Replace body | `ntn pages edit <ID> --content` | API-supported (tested) |
| Append/delete blocks | `ntn api v1/blocks/<ID>/children`, `/blocks/<ID>` | API-supported (tested) |
| Database, rows, query, formulas | `ntn api v1/databases`, `v1/pages`, `v1/data_sources/<ID>[/query]` | API-supported (tested) |
| File upload (free plan) | `v1/file_uploads` single_part | API-supported (tested) |
| Conversational/semantic exploration | remote MCP | MCP-supported (Not tested) |
| Buttons, automations | none | UI-only |

## Detailed workflow
Execution protocol:
1. **Analyze**: dashboard, relational database or wiki? Single operation or batch?
2. **Retrieve context**: `ntn whoami`; `ntn api v1/search`; `ntn pages get <PARENT_ID>`; `GET v1/data_sources/<ID>` for schemas; check duplicate titles.
3. **Plan**: list commands, parent IDs, expected counts. Wait for approval if existing content changes.
4. **Generate payload**: Markdown or JSON; validate with the checklist (block colors, 2,000-char runs).
5. **Execute**: create or append, then properties and formulas. Batch: loop with a pause (about 3 requests/s), log each ID.
6. **Verify**: `ntn pages get <NEW_ID>` and compare headings/blocks; count rows with a query.
7. **Report**: URL/ID, structure summary, schema, formulas, UI-only leftovers.

## Implementation instructions
- Markdown caveat: `ntn pages create` uses deprecated Markdown **v1**. Callouts, tables, equations, code, columns and dividers work; toggles, toggle headings, `<table-of-contents />` and `<synced-block>` do NOT. For those use `ntn api v1/pages` with `"markdown_version":"v2"`. The first H1 becomes the title. Pass `--content` through a shell variable or heredoc to avoid quoting damage.
- Export: `ntn pages get <ID> > page.md` (Markdown). Import: `ntn pages create --parent page:<ID> --content "$(cat page.md)"`. Images do not round-trip by upload ID; use a placeholder paragraph then an image block.
- Block read: `ntn api v1/blocks/<ID>/children page_size==100`, paginate with `start_cursor==<CURSOR>`; append `-X PATCH -d '{"children":[...]}'`.
- Data sources: `ntn datasources query` / `resolve` exist as CLI forms (check `ntn datasources --help`; Not exercised in the sandbox run). The tested path is `ntn api v1/data_sources/<ID>/query`.
- Files: `ntn files create` FAILS on the free plan (multipart). Use single_part: `ntn api v1/file_uploads -d '{"mode":"single_part","filename":"x.png","content_type":"image/png"}'`, then `ntn api v1/file_uploads/<UPLOAD_ID>/send --file x.png` (5 MB max), and attach to a block within about an hour.
- Health: `ntn doctor`, `ntn whoami`. Workers: `ntn workers new|deploy|ls|exec` (external; Not tested).
- Auth: use `NOTION_API_TOKEN` if set, else `ntn login` (browser, UI-only). Never echo the token.
- Batch scripts: for retries and pagination use `../notion-api-engineer/scripts/notion_request.py` instead of re-implementing them.

## Examples
```bash
ntn whoami < /dev/null
ntn api v1/search -d '{"query":"Skill Sandbox"}' < /dev/null
ntn pages get <PAGE_ID> < /dev/null > backup-<PAGE_ID>.md
ntn pages create --parent page:<PARENT_PAGE_ID> --content "# Release Notes

<callout icon=\"💡\" color=\"gray_bg\">
Body text
</callout>" < /dev/null
ntn api v1/pages -d '{"parent":{"type":"page_id","page_id":"<PARENT_PAGE_ID>"},"markdown":"# Toggle Demo\n\n<table-of-contents />","markdown_version":"v2"}' < /dev/null
ntn api v1/data_sources/<DATA_SOURCE_ID>/query -d '{"page_size":100}' < /dev/null
ntn api v1/file_uploads -d '{"mode":"single_part","filename":"x.png","content_type":"image/png"}' < /dev/null
ntn api v1/file_uploads/<UPLOAD_ID>/send --file x.png < /dev/null
```
Callout and other tag syntax: [enhanced-markdown](../../../references/enhanced-markdown.md). GitHub-style `> [!NOTE]` is not valid.

## Validation checklist
- [ ] `ntn whoami` succeeds before any write.
- [ ] Every scripted `ntn` call has `< /dev/null`.
- [ ] `ntn pages get <NEW_ID>` shows the expected title (first H1) and block kinds.
- [ ] v1-incompatible tags (toggle, `<table-of-contents />`, `<synced-block>`) were sent via v2, not `ntn pages create`.
- [ ] Before `pages edit`, a backup file exists and the page has no subpages (or approval covers them).
- [ ] Batch: created count equals planned count; IDs logged.
- [ ] Upload block attached within an hour of the upload.

## Failure handling
- 400 validation: print body; check color names (`gray_background` for blocks, `gray_bg` for Markdown), rich text under 2,000 chars, arrays at most 100.
- 404: page not shared with the integration (UI-only); share and retry.
- 429/529: back off and retry. 5xx on GET/DELETE: retry. 5xx on POST/PATCH: re-read and compare before resending (duplicate risk).
- `ntn files create` fails: switch to single_part recipe above.
- Hang in a script: stdin was not closed; add `< /dev/null`.
- Toggles missing after `pages create`: v1 dropped them; recreate via v2.
- Block limit on a free multi-member workspace: stop and report.

## Safety constraints
- Test only on the "Skill Sandbox" page; always pass an explicit parent ID.
- Never delete or overwrite user content without approval; prefer archive/trash; back up before `pages edit`.
- Never install `vibe-notion`; do not install `lox/notion-cli` without a new decision.
- Never print or store tokens; do not re-run the `curl | bash` installer on a machine that already has `ntn`.
