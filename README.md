# Notion AI Skill Ecosystem

Composable skills, references and templates that let Claude Code (and other agents) build and operate Notion workspaces with the `ntn` CLI and Notion API. Everything here was validated against a dedicated "Skill Sandbox" page on `ntn` 0.23.28 (2026-11-09); see [docs/validation-report.md](docs/validation-report.md) for evidence and what is Not tested.

## Layout
- `skills/<category>/<skill>/SKILL.md`: 22 skills in design, dashboards, knowledge, automation and engineering. Each has the same 11 sections and a 7-step execution protocol.
- `references/`: shared source of truth ([design system](references/design-system.md), [naming](references/naming.md), [enhanced Markdown](references/enhanced-markdown.md), [formulas](references/formulas.md), [capability matrix](references/capability-matrix.md), [API limits](references/api-limits.md)). Skills link to these instead of copying.
- `templates/`: dashboards, knowledge-base, meeting-notes, project, report, research. Each has `schema.json`, `page.md` and a README.
- `scripts/`: `lint_skills.py` (structure checks) and `instantiate_template.py` (templates into a workspace).
- `docs/`: research report, install notes, decisions, limitations, validation report.

## Install
Skills are symlinked into `~/embedded/.agents/skills/` and `~/embedded/.claude/skills/` (the same layout as the official `notion-cli` skill):
```bash
cd ~/embedded
for d in notion-skill-ecosystem/skills/*/*/; do n=$(basename $d); c=$(basename $(dirname $d))
  ln -s ../../notion-skill-ecosystem/skills/$c/$n .agents/skills/$n
  ln -s ../../.agents/skills/$n .claude/skills/$n; done
```
Prerequisites: `ntn` logged in (`ntn api v1/users/me`) and the target page shared with the integration. The remote Notion MCP is configured but needs a one-time OAuth: run `/mcp`, select `notion`, finish the browser flow, restart the session.

## Use a template
```bash
python3 -I scripts/instantiate_template.py templates/project --parent <PAGE_ID> --dry-run
python3 -I scripts/instantiate_template.py templates/project --parent <PAGE_ID> --manifest manifest.json
python3 -I scripts/instantiate_template.py --rollback manifest.json   # trashes only what the manifest lists
```
Creates databases, relations, rollups, formulas, the page (Markdown v2) and moves linked views to their `{{VIEW:...}}` markers. Relations to databases outside the template are skipped unless you pass `--set <NAME>_DS_ID=<id>`.

## Skills
| Skill | Category | What it does |
|---|---|---|
| [notion-automation-engineer](skills/automation/notion-automation-engineer/SKILL.md) | automation | Designs recurring tasks, status transitions, reminders, triggers and external API integrations for Notion, keeping native (UI-only) automations separate from scripted (external) ones. |
| [notion-meeting-intelligence](skills/automation/notion-meeting-intelligence/SKILL.md) | automation | Builds meeting templates, agendas, notes, decisions, summaries and follow-ups in Notion, and extracts action items into a related Action Items database after user confirmation. |
| [notion-project-manager](skills/automation/notion-project-manager/SKILL.md) | automation | Builds Notion project dashboards, milestones, dependencies, progress, assignments, risks and weekly status reports on a Projects/Tasks/Milestones/Risks schema. |
| [notion-research-assistant](skills/automation/notion-research-assistant/SKILL.md) | automation | Builds Notion research workspaces for literature reviews, sources, citations, notes, hypotheses, experiment logs and research dashboards. |
| [notion-dashboard-builder](skills/dashboards/notion-dashboard-builder/SKILL.md) | dashboards | Builds Notion dashboards (productivity, project, academic, business, research, finance, team, knowledge) from linked views of master databases using the Views API. |
| [notion-database-architect](skills/dashboards/notion-database-architect/SKILL.md) | dashboards | Designs normalized Notion database schemas (properties, relations, rollups, formulas, status workflows, templates, integrity, duplicate detection) and defines the `schema.json` template format. |
| [notion-interaction-engineer](skills/dashboards/notion-interaction-engineer/SKILL.md) | dashboards | Adds interactivity to Notion workspaces (views, filters, sorts, grouping, relations, formulas, buttons, automations, synced blocks, templates, embeds), labeling each item API-supported, UI-only or external. |
| [notion-widget-integrator](skills/dashboards/notion-widget-integrator/SKILL.md) | dashboards | Integrates external widgets into Notion pages (charts, timers, clocks, progress meters, diagrams, custom HTML embeds) and evaluates their security, responsiveness and embed compatibility. |
| [notion-art-director](skills/design/notion-art-director/SKILL.md) | design | Defines the visual identity of a Notion workspace or page set (accent color, icon set, density, cover style, type hierarchy) and writes a short art-direction brief that other skills consume. |
| [notion-cover-and-icon-designer](skills/design/notion-cover-and-icon-designer/SKILL.md) | design | Chooses and applies page icons and covers, optimizes images locally, uploads them on the free plan and records source and license. |
| [notion-page-composer](skills/design/notion-page-composer/SKILL.md) | design | Composes Notion pages from a brief using headings, callouts, columns, dividers, tables, toggles, synced blocks and a table of contents, then creates them with v2 enhanced Markdown through `ntn api v1/pages`. |
| [notion-visual-consistency](skills/design/notion-visual-consistency/SKILL.md) | design | Audits Notion pages and databases for naming, typography, icon, cover and color consistency and returns a violations report; read-only by default. |
| [notion-api-engineer](skills/engineering/notion-api-engineer/SKILL.md) | engineering | Designs and debugs direct Notion REST API usage through `ntn api`: auth, Notion-Version pinning, pagination, rate limits, block and database operations, data-source endpoints, error handling and safe retries. |
| [notion-cli-engineer](skills/engineering/notion-cli-engineer/SKILL.md) | engineering | Runs Notion terminal workflows with the official `ntn` CLI: search, read, create, update, import/export, batch scripts and validation, and decides between `ntn` and lox/notion-cli. |
| [notion-markdown-ingest](skills/engineering/notion-markdown-ingest/SKILL.md) | engineering | Converts Markdown, including LaTeX-derived Markdown, into Notion v2 enhanced Markdown or block batches, handling 2,000-character splits, 100-block chunks, callouts, equations and image placeholders. |
| [notion-mcp-engineer](skills/engineering/notion-mcp-engineer/SKILL.md) | engineering | Configures, diagnoses and optimizes the official remote Notion MCP server (https://mcp.notion.com/mcp) across Claude Code, Codex and Cursor, including OAuth, tool discovery, permissions and context cost. |
| [notion-migration-engineer](skills/engineering/notion-migration-engineer/SKILL.md) | engineering | Plans and executes Notion schema changes and page or database migrations with a manifest, old-to-new ID mapping, relation reconstruction, schema diff, validation and rollback. |
| [notion-report-publisher](skills/engineering/notion-report-publisher/SKILL.md) | engineering | Publishes long structured documents (research or equity-research reports) as polished Notion pages with a summary callout, key-figures table, table of contents, toggled appendices and a sources section. |
| [notion-content-organizer](skills/knowledge/notion-content-organizer/SKILL.md) | knowledge | Categorizes, tags, adds metadata, migrates and cleans up Notion content while preserving the original, using a plan-then-approve workflow with a change manifest and rollback manifest. |
| [notion-knowledge-architect](skills/knowledge/notion-knowledge-architect/SKILL.md) | knowledge | Designs second-brain and knowledge-base structure in Notion (PARA, Zettelkasten only where they help), with master databases, relations, cross-linking, retrieval paths and a maintenance routine. |
| [notion-search-and-retrieval](skills/knowledge/notion-search-and-retrieval/SKILL.md) | knowledge | Builds Notion queries across pages and databases, traverses relations to find related pages and cites sources with page URLs. |
| [notion-workspace-auditor](skills/knowledge/notion-workspace-auditor/SKILL.md) | knowledge | READ-ONLY audit of a Notion workspace or subtree for duplicates, broken relations, deep nesting, naming violations, empty or stale pages and weak dashboards, producing a severity-ranked report. |

## Rules every skill follows
Read-only first; explicit parent ID on every write; never delete or overwrite without approval and a backup; trash instead of delete; never print or store tokens; retry 429/529 always but 5xx only on GET/DELETE; every capability labeled API-supported, MCP-supported, UI-only or external. UI-only items (database buttons, automations, sharing) are listed with click steps in [docs/limitations.md](docs/limitations.md).

Check structure with `python3 -I scripts/lint_skills.py`.
