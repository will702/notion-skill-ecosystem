---
name: notion-automation-engineer
description: Designs recurring tasks, status transitions, reminders, triggers and external API integrations for Notion, keeping native (UI-only) automations separate from scripted (external) ones. Use when the user says "recurring task", "automate this", "remind me", "when status changes", "cron", "webhook" or "sync with an external API".
---

## Purpose
Turn an automation request into a concrete, safe design. Native Notion database automations and buttons have no API, so this skill gives exact click steps for them. Anything scripted is `external` (cron/launchd calling `ntn api`, or `ntn workers`) and must be idempotent and rate-limit aware.

## Activation triggers
- "Create a weekly/monthly recurring task", "repeat this every Monday".
- "When Status becomes Done, set Completed On", "notify me when a task is overdue".
- "Sync rows from <service>", "push this to an external API", "run nightly".
- Auditing an existing automation for duplicate-write or rate-limit risk.

## Required tools
- `ntn api` (v1/search, v1/data_sources/<id>/query, v1/pages, v1/pages/<id> PATCH): `API-supported`, Tested per [capability matrix](../../../references/capability-matrix.md).
- `ntn workers` (`new`, `deploy`, `ls`, `exec`): `external`, Docs only / Not tested here; see [notion-cli](../../../../.claude/skills/notion-cli/SKILL.md).
- `cron` or `launchd` plus `python3` (stdlib) or POSIX `sh`: `external`.
- Notion UI for native automations: `UI-only`.
- Remote MCP: `MCP-supported`, Not tested (OAuth pending); read-only inspection only.

## Dependencies
- `notion-database-architect` owns schemas; this skill only adds the `Dedupe Key` (rich_text) and status properties it needs.
- `notion-page-composer` owns page layout for any report or log page an automation writes.
- `notion-project-manager` and `notion-meeting-intelligence` own the Tasks / Action Items semantics; this skill owns when and how rows get created.
- Limits and retry rules: [api-limits](../../../references/api-limits.md). Naming: [naming](../../../references/naming.md).

## Operating principles
1. Separate every automation into `native` (UI-only) or `external` in the plan; never mix steps.
2. Idempotent by construction: each generated row carries a deterministic `Dedupe Key` (for example `weekly-review-2026-W46`). Query first, create only if absent.
3. Never blind-retry POST or PATCH after a 5xx; re-read, compare, then decide. Retry GET/DELETE and 429/529 (honor `Retry-After`).
4. Respect about 3 requests/s on data source queries; sleep between rows, queue work, cap retries.
5. Run `ntn` with `< /dev/null`; log to a file, never print tokens.
6. Prefer native automations when they suffice; use scripts only for what the UI cannot do (external APIs, complex dedupe).

## Detailed workflow
Embedded 7-step execution protocol:
1. **Analyze**: classify as operational dashboard, relational tracking database, or documentation wiki; identify trigger, action, frequency and owner.
2. **Retrieve context**: `ntn api v1/search -d '{"query":"<db name>"}'`, then `GET v1/data_sources/<id>` for the schema; check the database already has `Dedupe Key`, `Status`, `Due Date`; check for existing automations in the UI (cannot be listed by API).
3. **Plan**: write a two-column table (Native / External). Show trigger, action, dedupe key formula, schedule, rate budget. Wait for approval before changing existing rows or schema.
4. **Generate payload**: build row JSON with a script (never hand-quoted); keys under 2,000 chars.
5. **Execute**: add missing properties via `PATCH v1/data_sources/<id>`; install the schedule; run once manually.
6. **Verify**: query by `Dedupe Key` and confirm exactly one row; run the script twice and confirm the second run prints `exists`.
7. **Report**: row/page IDs, schedule line, which parts are native (and the click steps the user must finish), which are external, known limits.

## Implementation instructions
**Native automations (`UI-only`, no endpoint):** open the database, click `...` (top right), Automations (or Properties, then Automations), `+ New automation`, choose trigger (`Page added`, or `Property edited` with a property and value), add action (`Edit property`, `Add page to`, `Send notification`, `Send webhook`), then `Create`. Recurring rows: use the `Every` trigger options where the plan offers them, or a database button `+` > Button.
**Status transition rules (native):** trigger `Status` is `Done` > action `Edit property` `Completed On` = `Now`. Reverse transition needs a second automation.
**External recurring rows (`external`, Tested for the API calls):** schedule [scripts/create_if_absent.py](scripts/create_if_absent.py) with cron, for example `0 7 * * 1 python3 /path/create_if_absent.py <DATA_SOURCE_ID> "Weekly Review" "weekly-review-$(date +\%G-W\%V)" "$(date +\%F)" >> ~/notion-auto.log 2>&1`. On macOS use a launchd plist with `StartCalendarInterval` (Docs only).
**Reminders:** native `Send notification` on a date-based trigger (`UI-only`); scripted alternative is a daily query for `Due Date` equal today and a `v1/comments` mention (`API-supported`, Docs only).
**Workers (`external`, Docs only / Not tested):** `ntn workers new <name>`, `ntn workers deploy`, `ntn workers exec <capability>`. Do not claim success until validated on the sandbox.
**Webhooks and third-party calls:** the external service calls your script, which writes through `ntn api`; Notion-side outbound webhooks are native `Send webhook` actions (`UI-only`, Not tested).

## Examples
Create-if-absent (query first, one POST, re-read on failure):
```sh
python3 -I scripts/create_if_absent.py <DATA_SOURCE_ID> "Weekly Review" "weekly-review-2026-W46" 2026-11-16
```
Manual dedupe check:
```sh
ntn api v1/data_sources/<DATA_SOURCE_ID>/query -d '{"filter":{"property":"Dedupe Key","rich_text":{"equals":"weekly-review-2026-W46"}}}' < /dev/null
```
Add the key property:
```sh
ntn api v1/data_sources/<DATA_SOURCE_ID> -X PATCH -d '{"properties":{"Dedupe Key":{"rich_text":{}}}}' < /dev/null
```
Cron (Mondays 07:00, log appended): see Implementation instructions.

## Validation checklist
- `python3 -I -m py_compile scripts/create_if_absent.py` exits 0.
- Running the script twice with the same key yields one row (query by key returns `results` length 1).
- Plan lists each step as `native` or `external`; every native step has click steps.
- Every external script runs `ntn` with `< /dev/null` (`grep -c "/dev/null\|DEVNULL"` is at least 1).
- Loop sleeps keep query rate at or below 3/s.
- No token or workspace ID appears in logs or committed files.

## Failure handling
- 400 validation: property name or type mismatch; re-fetch `GET v1/data_sources/<id>` and fix the payload.
- 404: page or database not shared with the integration; ask the user to add the connection.
- 429/529: wait `Retry-After`, then backoff with jitter, max 5 tries.
- 5xx on POST/PATCH: do not retry; query by `Dedupe Key`, create only if still absent.
- Rich text over 2,000 chars: truncate or split before sending.
- `ntn` hangs in a scheduler: stdin was not closed; add `< /dev/null`.
- Native automation missing after setup: it cannot be read by API; ask the user to confirm in the UI.

## Safety constraints
- Test only on the dedicated "Skill Sandbox" page and its databases.
- Never delete or overwrite rows without explicit approval; archive instead of deleting.
- Use an explicit parent or data source ID; start with read-only queries.
- Never print or store tokens; scripts rely on the existing `ntn` login.
- Do not install cron/launchd entries without showing the exact line and getting approval.
