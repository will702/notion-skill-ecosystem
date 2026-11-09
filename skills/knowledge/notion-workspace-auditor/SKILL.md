---
name: notion-workspace-auditor
description: READ-ONLY audit of a Notion workspace or subtree for duplicates, broken relations, deep nesting, naming violations, empty or stale pages and weak dashboards, producing a severity-ranked report. Use when the user says "audit my workspace", "find duplicates", "what is stale", "check broken relations" or "workspace health".
---

## Purpose
Find structural and hygiene problems and report them with severity and a suggested fix, without changing anything. Fixes are handed to `notion-content-organizer` (content) or `notion-database-architect` (schema).

## Activation triggers
- "Audit", "health check", "find duplicate databases", "which pages are stale or empty", "are my relations broken", "is my dashboard any good".
- Before a restructure by `notion-knowledge-architect` or a migration by `notion-content-organizer`.

## Required tools
Read-only allowlist. Anything not listed here must not be run.
| Command | Label |
|---|---|
| `ntn api v1/search -d '{"query":"...","page_size":100,"start_cursor":"..."}' < /dev/null` (POST but non-mutating; title search only) | API-supported (Tested) |
| `ntn pages get <PAGE_ID> < /dev/null` | API-supported (Tested) |
| `ntn api v1/blocks/<ID>/children page_size==100 start_cursor==<CURSOR> < /dev/null` (GET) | API-supported (Tested) |
| `ntn api v1/data_sources/<ID> < /dev/null` (GET) | API-supported (Tested) |
| `ntn api v1/views database_id==<DATABASE_ID> < /dev/null` (GET, list) | API-supported (Docs only) |
| `ntn api v1/data_sources/<ID>/query -d '{"page_size":100}' < /dev/null` (POST but non-mutating, sampling) | API-supported (Tested) |
Forbidden verbs: PATCH, DELETE, `ntn pages edit`, `ntn pages create`, `v1/pages` POST, `v1/views` POST. Page sharing and permission audits are UI-only. CLI basics: [notion-cli](../../../../.claude/skills/notion-cli/SKILL.md).

## Dependencies
- Severity scale and naming rules: [naming](../../../references/naming.md) (Error/Warning). Layout checks: [design-system](../../../references/design-system.md). Limits: [api-limits](../../../references/api-limits.md).
- Fix owners: `notion-content-organizer`, `notion-database-architect`, `notion-page-composer`. This skill never fixes.
- `notion-search-and-retrieval` owns general lookups; this skill only enumerates.

## Operating principles
- Read-only means zero writes: no archive, no property edit, no comment, no test row.
- Rate cap about 3 requests/s (sleep about 0.35 s between calls, a queue not bursts); paginate every list with `start_cursor` until `has_more` is false.
- Scope first: audit a named root page or the whole search result, never "everything" silently; cap with a page budget parameter.
- Report counts and IDs, not page body text, to keep output small.
- Search covers titles only, so enumeration is incomplete by design; say so in the report.

## Detailed workflow
Parameters: `STALE_DAYS` (default 180), `MAX_DEPTH` (default 3), `EMPTY` = zero child blocks, `PAGE_BUDGET` (default 500).
1. Analyze: classify the target as dashboard workspace, relational databases or documentation wiki; choose which checks apply.
2. Retrieve context: search (paginated) for pages and data sources; record IDs, titles, parents, `last_edited_time`, `in_trash`. Detect duplicate titles.
3. Plan: print the scope, parameters, request estimate (searches + one GET per database/page sampled) and confirm. No approval is needed for changes because there are none.
4. Generate payload: build the request list from the allowlist only; no write payloads exist.
5. Execute: run the checks below in order, throttled.
6. Verify: spot-check 3 reported findings per category by re-reading the object (`ntn pages get` or `GET v1/data_sources/<id>`), confirm each finding still holds.
7. Report: use the template; list scope, counts, findings by severity, UI-only items (sharing) and who should fix each.

Checks:
- Duplicates: same normalized title (lowercase, trimmed) among databases (Error) or pages with the same parent (Warning).
- Broken relations: in `GET v1/data_sources/<id>` each `relation.data_source_id`; a 404 or 400 on that target means broken (Error). Also a relation with no reverse property when one is expected (Warning).
- Nesting: follow `parent` chains; depth greater than `MAX_DEPTH` is Warning.
- Naming: apply naming.md; two properties differing only by case or duplicate database names are Error; casing, emoji in titles, dashboards lacking ` Dashboard`, orphan `Test ` pages outside `Skill Sandbox` are Warning.
- Empty: `GET v1/blocks/<id>/children page_size==1` returns no results and the page is not a database row: Info (Warning if it has a parent that links to it).
- Stale: `last_edited_time` older than `STALE_DAYS`: Info; Warning if it is a dashboard or a master database row set.
- Weak dashboards: a dashboard page with no linked views, more than 3 columns, more than 2 callouts per section, or more than one accent color (Warning). Views listed with `GET v1/views?database_id=` show master databases with only the default view (Info).

## Implementation instructions
Throttled paginated search (shell; keep the loop tiny, stdlib only):
```
cursor=""; while :; do
  if [ -z "$cursor" ]; then body='{"query":"","page_size":100}'; else body="{\"query\":\"\",\"page_size\":100,\"start_cursor\":\"$cursor\"}"; fi
  ntn api v1/search -d "$body" < /dev/null > page.json
  cursor=$(python3 -I -c 'import json;d=json.load(open("page.json"));print(d["next_cursor"] if d["has_more"] else "")')
  [ -z "$cursor" ] && break; sleep 0.4
done
```
Write intermediate output only under the scratchpad or a temp directory, never into the workspace. On 429 wait `Retry-After`; on 5xx retry GETs only (these are all reads).

## Examples
```
ntn api v1/search -d '{"query":"Dashboard","page_size":100}' < /dev/null
ntn api v1/blocks/<PAGE_ID>/children page_size==1 < /dev/null
ntn api v1/data_sources/<DATA_SOURCE_ID> < /dev/null
ntn api v1/views database_id==<DATABASE_ID> < /dev/null
```
Report template:
```
# Workspace Audit YYYY-MM-DD
Scope: <ROOT_PAGE_ID or search>  Params: STALE_DAYS=180 MAX_DEPTH=3  Requests: <n>  Coverage: title search only
Summary: Error <n> | Warning <n> | Info <n>
| Severity | Category | Object (title, ID) | Evidence | Suggested fix | Owner skill |
Not audited (UI-only): sharing and permissions, members, billing.
```

## Validation checklist
- [ ] Command log contains only allowlisted verbs (grep the log for `PATCH`, `DELETE`, `pages edit`, `pages create`: zero hits).
- [ ] Every list call paginated until `has_more` is false.
- [ ] Observed request rate at most 3/s (log timestamps).
- [ ] Each finding carries an ID, evidence and severity from naming.md.
- [ ] 3 sampled findings per category reconfirmed by re-read.
- [ ] Report states title-only search coverage.

## Failure handling
- 404 on an object: not shared with the integration; list it as "inaccessible", do not infer broken.
- 400: wrong ID type (database ID versus data source ID); fetch the data source ID from the database and retry once.
- 429: sleep `Retry-After`, then resume from the saved cursor.
- 5xx: retry the GET up to 3 times with backoff; then mark the item "unverified".
- Page budget reached: stop, report partial coverage with the last cursor.
- Never "fix" a finding in response to an error.

## Safety constraints
- This skill must never mutate: no PATCH, DELETE, POST that writes, `ntn pages edit` or `create`, and no archiving.
- Do not write under the sandbox or elsewhere in the workspace; local temp files only.
- Do not print page bodies beyond the minimum evidence; never print or store tokens.
- Test runs only against the dedicated "Skill Sandbox" page.
