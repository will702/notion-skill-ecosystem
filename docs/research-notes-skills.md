# Research notes: Notion skill repositories

Source: read-only scout pass on 2026-11-09 (shallow clones, nothing executed). Scores 1-5, higher is better (Install: 5 = easy; Redundancy: 5 = low overlap). Items marked **unverified** were not confirmed. Commit hashes are the ones inspected, for provenance.

| Candidate | Commit | License | Stars | Maint | Examples | Docs | Codex+CC | MCP | Security | Install | Caps | Redund | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| makenotion/notion-cookbook | 1d52d1f (2026-11-06) | MIT | 223 | 5 | 5 | 4 | 4 | 5 | 4 | 3 | 5 | 3 | Borrow ideas; install only the mcp-clients skills after review |
| makenotion/skills (notion-cli, notion-apps) | 10e976a (2026-09-22) | MIT | 183 | 4 | 3 | 4 | 4 | 2 | 3 | 2 | 4 | 2 | `notion-cli` kept (already installed); `notion-apps` is alpha-gated, left as is |
| mattppal/formatting-notion-pages | 9c272d1 (2026-01-12) | MIT | 9 | 2 | 3 | 4 | 4 | 3 | 5 | 5 | 3 | 2 | Borrow ideas (API limits, block reference); stale, skip install |
| markus41/Claude-m (notion plugin) | 703f383 (2026-09-18) | plugin.json says MIT, no LICENSE file, GitHub shows null | 18 | 3 | 4 | 5 | 2 | 3 | 3 | 4 | 5 | 2 | Borrow ideas (design patterns); skip plugin install |
| TrevorS/notion-formatter | repo 404 | n/a | n/a | 1 | 2 | 2 | 4 | 1 | 4 | 5 | 2 | 2 | Skip (only a third-party registry snapshot exists) |
| aneym Notion skill | not found | n/a | n/a | - | - | - | - | - | - | - | - | - | Unverified, skip |
| harlanljones/notion | 404 | n/a | n/a | - | - | - | - | - | - | - | - | - | Unverified, skip |
| vladchatware/notion-skill (extra) | cb5e4b9 | MIT | 0 | 3 | 3 | 3 | 4 | 2 | 3 | 2 | 3 | 2 | Borrow ideas (`references/block-types.md`) |
| tellang/notion-cli, Python (extra) | 91cdd15 (2026-04-08) | MIT | 2 | 2 | 2 | 3 | 3 | 1 | 4 | 2 | 3 | 3 | Skip; borrow the field-filter idea |
| ArgentAIOS/agent-skills notion (extra) | 9cdab2b (2026-03-31) | MIT | 5 | - | - | - | - | - | - | - | - | - | Unverified, content not read |

Also seen, not candidates: Samin12/skills and idanbeck/claude-skills (no license), SethBurkart123/notion-formatter (a desktop app, not a skill).

## Security notes
- **makenotion/skills:** no scripts. Both SKILL.md files tell the user to run `curl -fsSL https://ntn.dev | bash` (pipe-to-shell from a non-Notion host). Already satisfied on this machine, so never re-run it blindly. `notion-apps` requires confirming alpha access first.
- **notion-cookbook:** no curl|bash or eval. `scripts/run-projects.mjs:68` spawns `npm`. Example code references non-Notion hosts (example.com, stripe, pagerduty, sentry) as demo templates only. Repo `AGENTS.md` is a contributor guide, not injection.
- **mattppal:** Markdown only, no scripts or network calls.
- **Claude-m:** no scripts; token read from `process.env.NOTION_TOKEN`. Frontmatter allows Bash and Notion MCP tools. README and marketplace are Microsoft-365 branded (`claude-m-microsoft-marketplace`): provenance mismatch, hence borrow-only.
- **TrevorS snapshot:** Markdown only, but its toggle and blockquote syntax conflicts with the official spec. Treat as unreliable.
- **tellang/notion-cli:** token from env; no subprocess or non-Notion URLs in the Python source. Not installed, so untested.
- **vladchatware:** README.md:36 and SKILL.md:33 contain the same curl|bash.

## Patterns worth borrowing (paths relative to clone roots)
- `Claude-m/notion/skills/notion-mastery/references/notion-markdown-spec.md`: tab indentation and block colors (L10-11), toggle headings (L71-104), `<details>` toggle (L145-152), callout (L168-182), `<columns>` (L184-200), `<table>` (L201+). **Caution:** its callout and toggle syntax (`::: callout`, `{toggle="true"}`) differs from the official Notion-flavored Markdown (`<callout>`, `<toggle>`), which was validated live on the API in this project. References in this repo follow the official spec.
- `Claude-m/.../formula-language.md`: formula reference with examples (if/ifs/format/date). `.../api-reference.md:474-495`: rate-limit backoff. `.../page-design-patterns.md` and `examples/design-showcase.md`: layout guidance.
- `mattppal/formatting-notion-pages/.../SKILL.md:298-304`: API limits (100 blocks per request, 2 nesting levels, 100 rich_text elements, 2000 chars per rich_text). **Unverified against official docs**; checked during Phase 3 (`references/api-limits.md`). `blocks-reference.md`: column_list (L199), equation (L371), synced_block (L383), template_button (L409).
- `notion-cookbook/examples/query-large-data-sources/index.ts` (pagination), `examples/intro-to-notion-api/intermediate/3-query-database.ts`, `4-sort-database.ts`, `6-create-page-with-template.ts`, `skills/mcp-clients/*/SKILL.md` (knowledge-capture, meeting-prep, weekly-project-digest), `workers/agents/skills/sync-guide/api-pagination-patterns.md`.
- `vladchatware/notion/references/block-types.md`: block JSON examples.
- `tellang/notion-cli/notion_cli/lib/fields.py`: keep only selected fields to cut token use.

## Unverified / not done
- A local Codex plugin exists at `~/.codex/.tmp/plugins/plugins/notion` (skills: notion-knowledge-capture, notion-meeting-intelligence, notion-research-documentation, notion-spec-to-implementation). Not inspected; overlaps the cookbook mcp-clients skills.
- Claude-m licensing is ambiguous (see table).
- ArgentAIOS, tellang, vladchatware: metadata and grep only.
- The scout reported it could not find local notion-cli/notion-apps installs; they are in `~/embedded/.claude/skills` and `.agents/skills` (verified separately).
