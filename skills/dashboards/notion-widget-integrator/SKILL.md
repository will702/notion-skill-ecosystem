---
name: notion-widget-integrator
description: Integrates external widgets into Notion pages (charts, timers, clocks, progress meters, diagrams, custom HTML embeds) and evaluates their security, responsiveness and embed compatibility. Use when the user says "add a clock", "embed a chart", "pomodoro timer widget", "embed this URL", or "custom HTML in Notion".
---

# Notion Widget Integrator

## Purpose

Choose, vet and embed hosted interactive widgets. Every widget is `external`: Notion cannot run arbitrary code, it only frames a URL. Prefer native alternatives (formula progress bars, linked views) first. Layout belongs to `notion-page-composer`, dashboards to `notion-dashboard-builder`.

## Activation triggers

"embed a widget", "clock/timer/pomodoro", "chart from a sheet", "diagram embed", "custom HTML", "does this embed work".

## Required tools

- `ntn api v1/pages` (v2 Markdown) or `v1/blocks/<id>/children` to insert the embed: `API-supported` for the block, Docs only for the `embed` syntax; the widget itself is `external`, Not tested.
- Any static host the user controls (for custom HTML): `external`.
- `ntn` syntax: the official `notion-cli` skill.

## Dependencies

- [enhanced-markdown.md](../../../references/enhanced-markdown.md), [design-system.md](../../../references/design-system.md) (prefer functional over decorative), [capability-matrix.md](../../../references/capability-matrix.md) (interactive widgets: `external`, Not tested), [api-limits.md](../../../references/api-limits.md) (URL max 2,000 chars).
- `notion-interaction-engineer` owns native interactivity; this skill only covers hosted embeds.

## Operating principles

1. Native first: a Formula 2.0 progress bar (see [formulas.md](../../../references/formulas.md)) beats an embedded one.
2. Treat the embed host as untrusted third-party code framed in the page.
3. No secrets, tokens or personal data in URLs or query strings.
4. HTTPS only; hosts must permit framing (no `X-Frame-Options: DENY`, no restrictive `frame-ancestors`).
5. A widget earns its place: one stated purpose, one per section.

## Detailed workflow

Execution protocol (all steps mandatory):
1. **Analyze**: is the page an operational dashboard, relational tracking database or documentation wiki? Widgets fit dashboards only.
2. **Retrieve context**: fetch the target page (`ntn pages get <PAGE_ID>`), list existing embeds, confirm the parent ID.
3. **Plan**: widget, host, purpose, native alternative considered, scorecard result. Wait for approval.
4. **Generate payload**: block JSON or v2 Markdown line with the `embed` tag.
5. **Execute**: append with `position` after a named block; never replace the body.
6. **Verify**: re-fetch; confirm the `embed` block and URL; ask the user to open the page and confirm it renders (rendering is not observable via API).
7. **Report**: page URL/ID, host, score, `external` label, fallback link, anything the user must check visually.

### Evaluation scorecard (score 0-2 each; embed only if total >= 8 and Security >= 2)

| Criterion | 0 | 1 | 2 |
|---|---|---|---|
| Security: HTTPS, known host, no secrets in URL, no required login cookies | any fail | unknown host | pass |
| Sandbox: host needs no popups, no top navigation, no storage | needs all | some | none |
| Framing allowed: opens inside another site | blocked | partial | tested in Notion |
| Responsiveness: usable at 360 px wide | broken | scrolls | fluid |
| Load time: first paint under 3 s, under 1 MB | over | borderline | under |
| Maintenance: stable URL, owner known | none | unclear | clear |

## Implementation instructions

1. Run the scorecard; record the score in the report.
2. Insert (Markdown v2; mark: Docs only, Not tested): `<embed source="https://example.com/widget">Pomodoro timer, hosted by example.com</embed>`. If the tag is rejected, use a block: `{"type":"embed","embed":{"url":"https://example.com/widget"}}` (Docs only).
3. Always add a caption naming host and purpose, and a plain link line below as fallback for clients that block frames.
4. Custom HTML: host it yourself on a static host (GitHub Pages or similar), keep it dependency-free, no inline secrets, no `postMessage` handlers that trust any origin, and fix a height in the page.
5. Never claim the widget works until the user confirmed rendering in Notion.

## Examples

```bash
ntn api v1/blocks/<PAGE_ID>/children -X PATCH -d '{"children":[{"type":"embed","embed":{"url":"https://example.com/clock"}}],"position":{"type":"after_block","after_block":{"id":"<BLOCK_ID>"}}}' < /dev/null
```
```markdown
<embed source="https://example.com/chart?id=public-demo">Weekly burndown, hosted by example.com</embed>
```
Placeholder hosts only; replace with the vetted URL.

## Validation checklist

- [ ] Scorecard total >= 8 and Security = 2, recorded in the report.
- [ ] URL starts with `https://`, is under 2,000 characters, and `grep -iE 'token|key|secret|password'` over it finds nothing.
- [ ] `ntn pages get <PAGE_ID>` shows the embed with its caption.
- [ ] Fallback link line present.
- [ ] Label `external` and evidence `Not tested` stated in the report.
- [ ] User confirmed visual rendering.

## Failure handling

- 400 validation: wrong block shape; retry once with the other form (tag vs block JSON).
- 404: page not shared with the integration; ask the user to share it.
- 429/529: honor `Retry-After`. 5xx on append: re-read children before retrying, to avoid a duplicate embed.
- Embed shows blank or "refused to connect": host blocks framing; pick another host or use a bookmark link.
- URL over 2,000 characters: shorten via the host's id parameter.

## Safety constraints

- Sandbox only for tests; explicit parent ID.
- Never embed a URL with credentials, session tokens or private data; never print tokens.
- Do not embed unvetted third-party code on pages shared publicly.
- Do not replace or delete existing blocks without approval.
