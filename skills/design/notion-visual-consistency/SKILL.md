---
name: notion-visual-consistency
description: Audits Notion pages and databases for naming, typography, icon, cover and color consistency and returns a violations report; read-only by default. Use when the user says "audit the design", "check consistency", "naming check", "design quality review" or "why does this workspace look messy".
---

# notion-visual-consistency

## Purpose
Run the mechanical design and naming checks over a page tree and report violations with severity and a proposed fix. It never changes content unless the user approves a specific fix, which `notion-page-composer` or `notion-cover-and-icon-designer` then applies.

## Activation triggers
- "Audit this workspace/page", "consistency check", "are my names consistent", "design review".
- Before `notion-report-publisher` or a dashboard skill reports a result (self-check hook).
- After an `Art Direction Brief` is adopted and the user wants compliance verified.

## Required tools
| Capability | Label | How |
|---|---|---|
| Find pages by title | API-supported (Tested) | `ntn api v1/search -d '{"query":"..."}' < /dev/null` |
| Read page body as Markdown | API-supported (Tested) | `ntn pages get <ID> < /dev/null` |
| Page properties, icon, cover | API-supported (Docs only for icon/cover fields) | `ntn api v1/pages/<ID>` |
| Walk block children | API-supported (Tested) | `ntn api v1/blocks/<ID>/children page_size==100` (paginate `start_cursor==`) |
| Database schema | API-supported (Tested) | `ntn api v1/data_sources/<ID>` |
| Fix violations | API-supported, needs approval | delegated to sibling skills |
| Detect actual rendered font or width | UI-only | not exposed by the API; ask the user to check the page menu |
| MCP search/fetch | MCP-supported (Not tested) | intended usage only |

CLI details: [notion-cli skill](../../../../.claude/skills/notion-cli/SKILL.md).

## Dependencies
- Rules (the checks themselves live here, not in this file): [design-system.md](../../../references/design-system.md) "Design checks a skill must run before reporting" and [naming.md](../../../references/naming.md) including "Audit severity".
- Brief to compare against: produced by `notion-art-director`.
- Fixes: layout by `notion-page-composer`, icons/covers by `notion-cover-and-icon-designer`, schema renames by `notion-database-architect` (renaming a property referenced by a formula is an Error-class risk, see [formulas.md](../../../references/formulas.md)).

## Operating principles
1. Read-only by default; the report is the deliverable.
2. Every finding cites a check ID, the page/database ID, the evidence (a quoted title or count) and a severity.
3. Severity follows naming.md: Error for duplicate database names, case-only property duplicates, formula references to renamed properties; Warning for casing, emoji in titles, missing ` Dashboard` suffix, orphaned test pages. Design-system check failures are Warning unless they break mobile readability.
4. Audit only what was scoped; cap a run at 50 pages and say so.
5. Pace requests under about 3 per second.

## Detailed workflow
Execution protocol:
1. **Analyze**: is the scope an operational dashboard, a relational tracking database, or a documentation wiki? Choose the check subset.
2. **Retrieve context**: search the scope root, fetch child pages (breadth first, depth at most 3), fetch schemas for databases, find the art-direction brief. Check for duplicate names across the set.
3. **Plan**: list the pages to audit and the checks to run. Nothing changes, so no approval is needed; ask only when scope exceeds 50 pages.
4. **Generate payload**: no write payload. Build the findings table in memory.
5. **Execute**: run the checks (below) on each page's Markdown, titles, icons and schemas.
6. **Verify**: re-run each failing check on a second fetch to rule out stale reads; confirm counts (callouts, columns) by recount.
7. **Report**: findings table sorted Error then Warning, summary counts, proposed fixes grouped by owning skill, and a UI-only list (font, width). To publish the report as a page, hand it to `notion-page-composer` with approval.

## Implementation instructions
Checks (IDs used in the report):
- `D1` one accent: collect all `color="<x>_bg"` in callouts and tables; more than one non-`default` color is a violation.
- `D2` callouts: count per H2 section; more than 2, or a callout directly under a heading with no other content.
- `D3` columns: count per `<columns>`; must be 2 to 3 with ratios summing to 100.
- `D4` emoji-only status: a status cell or line consisting only of an emoji.
- `D5` parent and title: page has explicit parent; title follows naming.md.
- `D6` dashboard views are linked databases, not pasted rows (database block present, no duplicate pipe tables of master rows).
- `D7` icons: distinct emoji across the scope is 8 or fewer.
- `N1` page title: Title Case, no trailing punctuation, no emoji; suffixes (` Dashboard`, `YYYY-MM-DD Topic`, `YYYY-MM Log`).
- `N2` databases: plural Title Case, no duplicates. `N3` properties: singular Title Case, `Is`/`Has` booleans, no case-only twins.
- `N4` test pages outside `Skill Sandbox`; `N5` image filenames/captions per naming.md "Files and assets".
Counting sketch:
```bash
ntn pages get <PAGE_ID> < /dev/null | grep -o '<callout[^>]*>' | sort | uniq -c
```

## Examples
Report format:
```markdown
# Design Audit 2026-11-09

| ID | Severity | Where | Evidence | Fix owner |
|---|---|---|---|---|
| D1 | Warning | Research Hub (<PAGE_ID>) | callouts use gray_bg and blue_bg | notion-page-composer |
| N1 | Warning | "Q3 plan!" (<PAGE_ID>) | trailing punctuation | notion-page-composer |
| N2 | Error | Databases "Task" and "Tasks" | duplicate-purpose names | notion-database-architect |
```
Check a database name set:
```bash
ntn api v1/search -d '{"query":"","filter":{"property":"object","value":"data_source"}}' < /dev/null
```

## Validation checklist
- [ ] Every finding has check ID, ID of the page/database, evidence and severity.
- [ ] Counts in the summary equal the row counts in the table.
- [ ] Each Error was reproduced on a second fetch.
- [ ] Number of pages audited is stated and 50 or fewer.
- [ ] No write call was issued (no POST, PATCH, DELETE in the command log).
- [ ] UI-only items are listed separately, not reported as failures.

## Failure handling
- 404 on a page: not shared with the integration; list it as "not audited" with the reason.
- 429/529: honor `Retry-After`, then retry. 5xx on GET: retry with backoff; reads are idempotent.
- 400 on a search filter: drop the filter, filter client-side.
- Truncated child listing: continue with `start_cursor` until `has_more` is false.
- No brief found: audit against design-system.md defaults and say so.

## Safety constraints
- Read-only unless the user approves a named fix; never delete or overwrite content.
- Test only under the "Skill Sandbox" page; never leave `Test ` pages elsewhere.
- Do not print page bodies that contain secrets; never print or store tokens.
- Run `ntn` with stdin closed.
