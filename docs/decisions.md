# Decisions

Format: date, decision, reason. Newest at the bottom.

| Date | Decision | Reason |
|---|---|---|
| 2026-11-09 | Repo lives at `~/embedded/notion-skill-ecosystem/` with its own `git init` | User choice; keeps `~/embedded` itself untouched (it is not a git repo) |
| 2026-11-09 | Dedicated private "Skill Sandbox" page at workspace root for all test writes | Standing rule 5; existing Embedded Systems 2 pages stay untouched |
| 2026-11-09 | `ntn` is the primary CLI; no second CLI installed yet | Already installed (0.23.28) and passed 17/17 sandbox ops; CLI decision rule forbids overlapping CLIs. Revisit `lox/notion-cli` after research |
| 2026-11-09 | Notion MCP configured for Claude Code only, at user scope | User choice; replaced a project-scoped entry to avoid duplicates; backup `~/.claude.json.bak-20261109-231626` |
| 2026-11-09 | Treat the prompt's `ntn` v0.14.1 as stale | Installed version is 0.23.28 |
| 2026-11-09 | Official `notion-cli` and `notion-apps` skills (makenotion/skills) kept as-is; custom skills reference them instead of copying | Already tracked in `skills-lock.json`; avoids drift |
| 2026-11-09 | Skills are installed as symlinks: `.agents/skills/<name>` points into this repo, `.claude/skills/<name>` points to that | Matches the layout of the official `notion-cli` skill; edits in the repo take effect everywhere |
| 2026-11-09 | Use `ntn api v1/pages` with `markdown_version: "v2"` instead of `ntn pages create/edit` for rich pages | The latter send deprecated Markdown v1; toggles, TOC and synced blocks are not created (tested) |
| 2026-11-09 | Linked views are placed by moving the appended `<database>` tag with `PATCH v1/pages/<id>/markdown` `update_content` | `create_database` always appends at the page end; the move was tested inside columns and leaves the master database unchanged. This corrects a research subagent's claim that placement was UI-only |
| 2026-11-09 | Relations and rollups are created with `PATCH v1/data_sources/<id>` after all databases exist | Tested on 4 templates; the auto-named reverse property is "Related to X (Y)" |
| 2026-11-09 | Retry 5xx only on GET/DELETE; on POST/PATCH re-read before retrying | Official guidance: a 5xx write may have succeeded (duplicate risk) |
| 2026-11-09 | `instantiate_template.py` writes its manifest after every created object and rollback only trashes manifest entries | A failed run once left two orphan databases; they were trashed by hand (recoverable) |
| 2026-11-09 | Borrow-only (no install): `lox/notion-cli`, `makenotion/notion-cookbook`, `mattppal/formatting-notion-pages`, `markus41/Claude-m`; skip `vibe-notion` (unofficial private API) and the 404 repos | See `docs/research-report.md` for licenses, commit dates and the security read of each |
| 2026-11-09 | `timeline` view removed from the project template | Not tested; replaced by a Milestones table view |
