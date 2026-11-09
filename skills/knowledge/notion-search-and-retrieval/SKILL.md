---
name: notion-search-and-retrieval
description: Builds Notion queries across pages and databases, traverses relations to find related pages and cites sources with page URLs. Use when the user says "find", "search my notes", "what do I have on X", "related pages", "where did this come from" or asks a question that must be answered from workspace content.
---

## Purpose
Answer questions from workspace content accurately and cheaply: pick the right retrieval method, narrow with filters, follow relations, and cite each claim with a page URL. Read-only.

## Activation triggers
- "Find notes about X", "what do we know about Y", "show related pages", "list notes in Area Z", "cite where this came from".
- Lookups needed by `notion-workspace-auditor`, `notion-content-organizer` or `notion-knowledge-architect`.

## Required tools
| Capability | Label | Command |
|---|---|---|
| Title search | API-supported (Tested) | `ntn api v1/search -d '{"query":"..."}' < /dev/null` (`ntn api ls` describes it as "Search by title") |
| Filtered data source query | API-supported (Tested) | `POST v1/data_sources/<ID>/query` |
| Read page as Markdown | API-supported (Tested) | `ntn pages get <ID> < /dev/null` |
| Block children | API-supported (Tested) | `v1/blocks/<ID>/children page_size==100` |
| Relation traversal | API-supported (Docs only) | read the relation property, fetch each related page |
| Semantic or full-text search through the remote MCP | MCP-supported (Not tested, OAuth pending) | intended usage only |
CLI basics: [notion-cli](../../../../.claude/skills/notion-cli/SKILL.md). Limits: [api-limits](../../../references/api-limits.md). Matrix: [capability-matrix](../../../references/capability-matrix.md).

## Dependencies
- `notion-database-architect` owns schemas; this skill reads property names and IDs only.
- `notion-knowledge-architect` defines the relations traversed here; `notion-workspace-auditor` owns enumeration for audits; `notion-content-organizer` owns changes.
- Naming conventions help predict titles: [naming](../../../references/naming.md).

## Operating principles
- `v1/search` matches titles only. Do not claim it finds text inside pages; for content questions query a database with filters or read candidate pages.
- Prefer structured queries (filters on `Area`, `Status`, `Type`) over fetching many pages.
- Token economy: request only needed properties (`filter_properties` query parameter, Docs only), page_size small, read page Markdown only for the final shortlist.
- Every answer carries sources: title plus page URL for each claim; say "not found" instead of guessing.
- Honor about 3 requests/s and paginate with `start_cursor` while `has_more` is true.
- Read-only: no writes of any kind.

## Detailed workflow
1. Analyze: is the question about a known entity (title search), a category (data source filter), a relationship (relation traversal) or free text (needs MCP or reading shortlisted pages)?
2. Retrieve context: search for the database by name, `GET v1/data_sources/<id>` for property names, types and select options so filters use real values.
3. Plan: state the query strategy and the expected number of requests; no approval needed (read-only).
4. Generate payload: build the search or query JSON with a script; validate property names and option values against the schema.
5. Execute: run narrow query, paginate, then traverse relations (batch related IDs, one `ntn pages get` or `GET v1/pages/<ID>` each, within rate cap).
6. Verify: confirm each cited page exists and its title or property supports the claim; cross-check counts when summarizing.
7. Report: the answer, sources list (title, URL, relevant property), the query used, coverage caveat (title-only search), and anything the user must do in the UI.

## Implementation instructions
Filter query (data source rows, only needed properties):
```
ntn api 'v1/data_sources/<DATA_SOURCE_ID>/query?filter_properties[]=<TITLE_PROP_ID>&filter_properties[]=<AREA_PROP_ID>' -d '{"filter":{"and":[{"property":"Status","select":{"equals":"Active"}},{"property":"Area","relation":{"contains":"<AREA_PAGE_ID>"}}]},"sorts":[{"timestamp":"last_edited_time","direction":"descending"}],"page_size":25}' < /dev/null
```
Relation traversal: read the relation property array from a row (`properties.Source.relation[].id`), then fetch each target. Reverse direction: query the other data source with `{"property":"Source","relation":{"contains":"<PAGE_ID>"}}`.
Related pages without a relation: search by the title keywords of the seed page, then compare shared `Area` or `Tags` values.
Citation format: `- <Title> (<page url>) - <property or section supporting the claim>`. The URL is the page's `url` field in the API response.
Cross-database search: loop over the data source IDs of Notes, Projects, Sources and merge results by `last_edited_time`; dedupe by page ID.
MCP (Not tested): an MCP `search` tool may provide semantic search across the workspace and connected apps; treat as intended usage until OAuth is completed and a tested result exists.

Query narrowing order: (1) filter by `Area` or `Status`, (2) add a title `contains`, (3) sort by `last_edited_time` descending, (4) cap `page_size` at 25 and paginate only if the user needs more.
Token reduction: list only titles and URLs first, ask or decide which 3 to 5 pages to read, then `ntn pages get` those.
Relation depth: follow at most 2 hops (Note to Source to its other Notes) unless the user asks for more.

## Examples
```
ntn api v1/search -d '{"query":"Release","filter":{"property":"object","value":"page"},"page_size":20}' < /dev/null
ntn api v1/data_sources/<DATA_SOURCE_ID>/query -d '{"filter":{"property":"Name","title":{"contains":"Release"}},"page_size":10}' < /dev/null
ntn pages get <PAGE_ID> < /dev/null
ntn api v1/blocks/<PAGE_ID>/children page_size==100 < /dev/null
```
Answer shape: "Two notes cover this. Sources: Release Process (<PAGE_URL>), 2026-10-12 Release Retro (<PAGE_URL>). Coverage: title and filtered property search only."

## Validation checklist
- [ ] Each cited URL came from an API response `url` field, not constructed.
- [ ] Query used property names and select values that exist in `GET v1/data_sources/<id>`.
- [ ] Pagination followed until `has_more` was false, or the cap was stated.
- [ ] Zero write requests in the command log.
- [ ] Final answer states "not found" for any claim without a source.
- [ ] Request rate at most about 3/s.

## Failure handling
- 400 invalid filter: the property name or type is wrong; re-read the schema, fix, retry once.
- 404: not shared with the integration; report as inaccessible, ask the user to share (UI-only).
- Empty results from search: the text is probably inside a page body; query the database or read shortlisted pages, and say title search cannot see body text.
- 429: wait `Retry-After`. 5xx on these GET/POST-read calls: retry with backoff, up to 3 times.
- Oversized page (more than 100 blocks): paginate children rather than printing everything.
- MCP unavailable: say so and fall back to API methods.

## Safety constraints
- Read-only; never mutate, archive or comment.
- Do not print tokens; quote only the minimum text needed from pages.
- Test only on the dedicated "Skill Sandbox" page; explicit IDs only.
- Do not present unverified MCP behavior as working.
