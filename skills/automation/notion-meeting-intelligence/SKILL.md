---
name: notion-meeting-intelligence
description: Builds meeting templates, agendas, notes, decisions, summaries and follow-ups in Notion, and extracts action items into a related Action Items database after user confirmation. Use when the user says "meeting notes", "agenda", "action items", "decisions log", "summarize this meeting" or "follow-ups".
---

## Purpose
Keep meetings in a `Meetings` master database with a consistent page layout, and turn notes into tracked `Action Items` rows (owner, due date, status) only after the user confirms the extracted list.

## Activation triggers
- "Create a meeting page / agenda for <topic>", "set up meeting notes".
- "Extract action items from these notes", "what did we decide", "summarize and follow up".
- "Set up a meetings database", "link meetings to a project".

## Required tools
- `ntn api v1/databases`, `v1/data_sources/<id>` PATCH, `v1/pages`, `v1/data_sources/<id>/query`, `v1/search`: `API-supported`, Tested.
- Relations between Meetings, Action Items and Projects: `API-supported`, Tested (property creation; writing relation values stays Docs only).
- v2 Markdown page creation (`markdown_version: "v2"`): `API-supported`, Tested.
- `ntn pages get <id>`: `API-supported`, Tested (read notes back).
- Views (table, board, calendar): `API-supported`, Tested via `v1/views`.
- Recurring meeting pages and reminders: `UI-only` natively, or `external` via `notion-automation-engineer`.
- MCP search/fetch/create: `MCP-supported`, Not tested.

## Dependencies
- `notion-database-architect` owns schema creation rules; this skill supplies the schema in [templates/meeting-notes](../../../templates/meeting-notes/README.md).
- `notion-page-composer` owns layout primitives; this skill defines the meeting page order.
- `notion-project-manager` owns the Projects database that `Project` relates to.
- `notion-automation-engineer` owns recurring meeting creation and dedupe keys.
- Formats and colors: [enhanced-markdown](../../../references/enhanced-markdown.md), [design-system](../../../references/design-system.md), [naming](../../../references/naming.md).

## Operating principles
1. Meetings are a relational tracking database; pages are `YYYY-MM-DD Topic` per naming rules.
2. Action items are rows, never only checkboxes in prose, so they can be filtered by owner and due date.
3. Extraction proposes; the user confirms; only then rows are created.
4. Never invent owners or dates: leave `Owner` empty and mark `Due Date` as `TBD` in the proposal when the notes do not state them.
5. One neutral accent, at most 1-2 callouts per section, toggles for raw transcript or logs.
6. Decisions are quoted verbatim from notes, with attribution if given.

## Detailed workflow
Embedded 7-step execution protocol:
1. **Analyze**: relational tracking database (Meetings, Action Items) with a documentation-style page per meeting.
2. **Retrieve context**: `v1/search` for `Meetings`, `Action Items`, `Projects`; fetch schemas; check duplicate names and an existing page with the same `YYYY-MM-DD Topic` title; resolve attendee names to people options.
3. **Plan**: show the schema (or the page outline) and, for extraction, the proposed action-item table. Wait for approval before touching existing content or creating rows.
4. **Generate payload**: build the v2 Markdown from [page.md](../../../templates/meeting-notes/page.md) with placeholders filled; build row JSON with a script.
5. **Execute**: create databases and relation properties, then the meeting page (row in `Meetings`), then approved Action Items rows linked to the meeting.
6. **Verify**: `ntn pages get <id>` and diff headings against the template; query `Action Items` by `Meeting` relation and compare the count to the approved list.
7. **Report**: page URL/ID, layout summary, schema, active formulas, UI-only items (recurring creation, templates button).

## Implementation instructions
**Schema (`API-supported`):** `Meetings`: `Name` (title), `Date` (date), `Attendees` (people), `Status` (select: Planned, Held, Cancelled), `Project` (relation to Projects), `Summary` (rich_text). `Action Items`: `Name` (title), `Meeting` (relation to Meetings, reverse `Action Items`), `Owner` (people), `Due Date` (date), `Status` (status or select: Todo, In Progress, Done), `Dedupe Key` (rich_text). Full property JSON: [schema.json](../../../templates/meeting-notes/schema.json).
**Page layout (v2 Markdown):** H1 title; one-line purpose; agenda callout (one); Attendees and Date line; Notes; Decisions (quotes); Action Items (linked database view or table); Follow-ups; toggle `Raw Notes` for pasted transcript.
**Extraction rules:**
- Candidate line: imperative sentence, `I will`, `@Name to`, `TODO`, `action:`, or a to-do checkbox.
- Owner: explicit name or mention only; else empty.
- Due date: explicit date or relative term resolved against the meeting date (state the resolution); else `TBD`.
- Status: `Todo` by default.
- Dedupe: `Dedupe Key` = `<meeting-date>-<slug of text>`; query before create.
**Confirmation step:** present a table `# | Action | Owner | Due | Status` and ask "Create these N rows?"; create nothing until yes. Honor edits and removals.
**Linked view on the page:** `v1/views` with `create_database` and a filter on the `Meeting` relation (`API-supported`, Tested for linked blocks; relation filter Docs only).

## Examples
Create the meeting page (v2):
```sh
ntn api v1/pages -d '{"parent":{"type":"data_source_id","data_source_id":"<MEETINGS_DATA_SOURCE_ID>"},"properties":{"Name":{"title":[{"text":{"content":"2026-11-09 Weekly Sync"}}]},"Date":{"date":{"start":"2026-11-09"}},"Status":{"select":{"name":"Held"}}},"markdown":"## Agenda\n\n- Review risks\n\n## Notes\n\n## Decisions\n\n## Action Items\n","markdown_version":"v2"}' < /dev/null
```
Create an approved action item:
```sh
ntn api v1/pages -d '{"parent":{"type":"data_source_id","data_source_id":"<ACTION_ITEMS_DATA_SOURCE_ID>"},"properties":{"Name":{"title":[{"text":{"content":"Send revised plan"}}]},"Meeting":{"relation":[{"id":"<MEETING_PAGE_ID>"}]},"Due Date":{"date":{"start":"2026-11-13"}},"Status":{"select":{"name":"Todo"}}}}' < /dev/null
```
Read notes back: `ntn pages get <MEETING_PAGE_ID> < /dev/null`.

## Validation checklist
- Page headings match the template order (`ntn pages get` then grep the 6 headings).
- Row count in `Action Items` for the meeting equals the number the user approved.
- Every created action item has `Meeting` set; Owner empty or a real person.
- No more than 2 callouts per section; one accent color.
- Page title matches `YYYY-MM-DD Topic`.

## Failure handling
- 400 validation: property type mismatch (for example `Status` as status vs select); re-fetch schema and rebuild.
- 404: database not shared with the integration; ask the user to share it.
- 429: honor `Retry-After`; query is about 3 req/s, so sleep between rows.
- 5xx on a row POST: query by `Dedupe Key` before retrying; never blind-retry.
- Rich text over 2,000 chars (long notes): split into paragraphs; over 100 blocks, append in chunks.
- Relation property fails: report the failure, fall back to a text `Project` note, report it.

## Safety constraints
- Test only under the "Skill Sandbox" page.
- Create no rows before explicit confirmation; never overwrite existing meeting notes (`ntn pages edit --content` replaces the body; back up first).
- Do not fabricate attendees, decisions or due dates.
- Explicit parent/data source IDs only; never print or store tokens.
