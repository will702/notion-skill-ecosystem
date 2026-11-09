# Validation report

Environment: `ntn` 0.23.28, Notion API as of 2026-11-09, free-plan workspace, all writes under the page "Skill Sandbox". Raw outputs live in the git-ignored `scratch/` folder.

Legend. **Installed**: symlinked and listed by Claude Code. **Functional**: the operations the skill's workflow depends on were executed against the sandbox and the result was re-read. This is not an end-to-end test of an agent following the SKILL.md; no skill was run by an agent from a cold prompt. **Not tested** always has a reason.

## Repo-level checks
| Check | Result |
|---|---|
| `scripts/lint_skills.py` | 22 skills, 0 errors (frontmatter, 11 sections in order, links, secret/UUID scan, capability labels) |
| `py_compile` on all 6 scripts | pass |
| Skill discovery | all 22 listed by Claude Code after symlink install |
| `schema.json` files | all parse as JSON |
| `instantiate_template.py` dry run | pass on 7 databased templates plus report |
| `instantiate_template.py` real run | 7 databased templates plus report created under the sandbox; databases, relations, rollups, formulas, linked views and zero unresolved markers re-read via the API (project: 4 databases, 2 rollups, 3 linked views placed) |
| `--rollback` | page trashed and `in_trash` re-read as true (report manifest) |
| Idempotency | `create_if_absent.py` called twice with the same key: created, then skipped, one row in the query |
| Error paths | 404 for unknown page (helper prints status and message); 400 for 101 children; 400 for 2,001-character text. All match what the skills document |
| Chunking | `split_chunks.py` on a 7 KB input: every unit at most 2,000 characters, content preserved apart from separators |
| `schema_diff.py` | identical copies report OK; different schemas list MISSING and EXTRA properties |

## Per skill
| Skill | Installed | Functional | Tested | Notes |
|---|---|---|---|---|
| notion-art-director | yes | partial | design-system rules applied in the earlier study-notes pages and template pages | produces a brief only; no artifact to execute |
| notion-page-composer | yes | yes | v2 pages with columns, callouts, toggles, TOC, tables, equations created and re-read | styled `<table>` and synced block references are Docs only |
| notion-visual-consistency | yes | not tested | read-only audit not run against a workspace subtree | needs a run on the sandbox |
| notion-cover-and-icon-designer | yes | yes | emoji icon, external cover and uploaded-file cover (`file_upload`) set via PATCH and re-read | image optimization step (local `magick`) used earlier |
| notion-dashboard-builder | yes | yes | 3 dashboard templates: linked views created and moved into position; dashboard view and widget tested earlier | timeline views Not tested |
| notion-database-architect | yes | yes | databases, relations (dual), rollups, formulas created on 4 templates | relation values on rows, `is_empty` relation filters Not tested; reverse property is auto-named "Related to X (Y)" |
| notion-interaction-engineer | yes | partial | views, filters, sorts, board grouping, calendar tested | buttons and automations are UI-only, no endpoint; embed Not tested |
| notion-widget-integrator | yes | not tested | `embed` tag not exercised | widgets are `external` |
| notion-knowledge-architect | yes | yes | knowledge-base template: Notes/Areas/Sources with relations, freshness formula, 4 linked views | |
| notion-workspace-auditor | yes | not tested | read-only audit not run | |
| notion-content-organizer | yes | partial | row creation and property writes tested; trash tested | page move (`/move`) Docs only |
| notion-search-and-retrieval | yes | partial | `v1/search` and data source queries with filters used | semantic search needs the MCP, Not tested |
| notion-automation-engineer | yes | partial | `create_if_absent.py` idempotency tested | native automations UI-only; `ntn workers` Not tested |
| notion-meeting-intelligence | yes | yes | meeting-notes template: Meetings and Action Items with relation and urgency formula; page created | `Meetings.Project` relation skipped unless a Projects data source id is passed |
| notion-project-manager | yes | yes | project template: Projects/Tasks/Milestones/Risks, rollups, progress and urgency formulas, linked views | timeline view and `Open Blockers` rollup Docs only |
| notion-research-assistant | yes | yes | research template: Sources/Notes/Hypotheses/Experiments with relations, citation formula, 3 linked views | |
| notion-api-engineer | yes | yes | `notion_request.py`: live call, 404 path, dry run | simulated 429 and 5xx retry paths Not tested |
| notion-mcp-engineer | yes | not tested | MCP entry configured at user scope, OAuth not completed | user step: `/mcp`, authenticate, restart |
| notion-cli-engineer | yes | yes | 17 of 17 sandbox `ntn` operations (earlier), v1 versus v2 Markdown behavior verified | `lox/notion-cli` not installed by decision |
| notion-migration-engineer | yes | partial | `schema_diff.py` tested; databases created from schema | full copy-and-rollback of a populated database not run; relation value reconstruction Not tested |
| notion-markdown-ingest | yes | yes | the LaTeX-derived study pages (equations, tables, callouts, images via placeholder swap) built and viewed in the browser; `split_chunks.py` tested | |
| notion-report-publisher | yes | yes | report template page created and rolled back | |

## Not tested (and why)
- Official Notion MCP tools: OAuth is a browser step only the user can complete.
- Codex and Cursor MCP configuration: the user chose Claude Code only.
- Comments, page move, template listing, synced block references, styled tables, mentions and dates.
- Timeline views, database buttons and automations (no endpoint), `ntn workers`.
- Simulated 429/5xx responses: the retry code paths in `notion_request.py` and `instantiate_template.py` are written to the official guidance but were never triggered on purpose.
- Skill activation from a cold agent prompt.
