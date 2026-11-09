---
name: notion-report-publisher
description: Publishes long structured documents (research or equity-research reports) as polished Notion pages with a summary callout, key-figures table, table of contents, toggled appendices and a sources section. Use when the user says "publish this report", "put this research in Notion", "equity research page" or "make a report page".
---

# notion-report-publisher

## Purpose
Take a finished long-form document and produce a navigable, design-compliant report page. Owns report structure and citations; delegates Markdown conversion to `notion-markdown-ingest` and page assembly to `notion-page-composer`.

## Activation triggers
- "Publish this report/research note/equity research to Notion."
- A document with a summary, figures, appendices and references must become one page.
- Re-publishing a revised report (new page version, old one archived with approval).

## Required tools
| Capability | Label | How |
|---|---|---|
| Create page with v2 Markdown | API-supported (Tested) | `ntn api v1/pages`, `markdown_version: "v2"` |
| TOC, toggles for appendices | API-supported (Tested, v2 only) | `<table-of-contents />`, `<toggle heading="h2">` |
| Pipe tables, callouts, equations | API-supported (Tested) | enhanced Markdown |
| Append large bodies, images | API-supported (Tested) | via `notion-markdown-ingest` |
| Read back | API-supported (Tested) | `ntn pages get <ID>` |
| Charts and live data | external | embed block with a hosted URL; Not tested |
| Page font Serif, full width | UI-only | page `...` menu |
| MCP publishing | MCP-supported (Not tested) | intended usage only |

CLI details: [notion-cli skill](../../../../.claude/skills/notion-cli/SKILL.md).

## Dependencies
- Skeleton: [templates/report/page.md](../../../templates/report/page.md) and its [README](../../../templates/report/README.md).
- Conversion, chunking, images: [notion-markdown-ingest](../notion-markdown-ingest/SKILL.md). Layout, creation: [notion-page-composer](../../design/notion-page-composer/SKILL.md). Look: `notion-art-director`; icon/cover: `notion-cover-and-icon-designer`; audit: `notion-visual-consistency`.
- Rules: [design-system.md](../../../references/design-system.md) (one accent, callout limits), [naming.md](../../../references/naming.md), [enhanced-markdown.md](../../../references/enhanced-markdown.md), [api-limits.md](../../../references/api-limits.md).

## Operating principles
1. Report layout order: title, one-line purpose, summary callout (one), key-figures table, `<table-of-contents />`, numbered sections, toggled appendices, `Sources`.
2. One accent for the whole report (default `gray`); the summary callout is the only callout in the front matter; at most 2 callouts per major section afterward.
3. Key figures are a pipe table with columns `Metric`, `Value`, `As Of`, `Source`; every number traces to a source entry.
4. Appendices (raw data, methodology, long tables) go in `<toggle heading="h2">`; the main text stays readable without opening them.
5. Citations: numbered `[1]` in text, a `Sources` section listing author, title, date, URL; images carry source and license captions.
6. No investment recommendation text is generated; reproduce the author's content only.
7. Title is Title Case without emoji (for example `Acme Corp Equity Research 2026-11`).

## Detailed workflow
Execution protocol:
1. **Analyze**: this is a documentation wiki or report page; confirm no database is needed (if figures need a master table, hand off to `notion-database-architect`).
2. **Retrieve context**: search for the parent and an existing report with the same title; read the source document; list sections, tables, equations, images, sources.
3. **Plan**: show section outline, key-figures rows, which parts go in toggles, accent, expected batch count. Wait for approval if a prior version exists.
4. **Generate payload**: fill `{{PLACEHOLDERS}}` of the template, run through `notion-markdown-ingest`; validate callout count and that every `[n]` has a Sources entry.
5. **Execute**: create via `notion-page-composer` (v2 `POST v1/pages`), append remaining batches, attach images, then set icon/cover if the brief asks.
6. **Verify**: `ntn pages get <ID>`; compare headings, table row count, toggle and TOC presence, source count against the plan.
7. **Report**: page URL/ID, layout summary, section list, number of sources, UI-only steps (Serif font, full width).

## Implementation instructions
- Instantiate the template per its README; replace every `{{...}}`; leftover placeholders are a failure.
- Summary: 3 to 5 lines, the findings first, then the date range.
- Key figures: 5 to 12 rows; right-align nothing (pipe tables ignore alignment in Notion); use `<br />` only if needed.
- Long sections: convert with `scripts/split_chunks.py` in [notion-markdown-ingest](../notion-markdown-ingest/SKILL.md), create the page with the first batch, append the rest in order.
- Equations: `$$` blocks for models (for example a DCF identity); inline `$..$` elsewhere.
- Check count:
```bash
ntn pages get <PAGE_ID> < /dev/null | grep -c '<callout'
```

## Examples
Front matter of a published report:
```markdown
# Acme Corp Equity Research 2026-11

Coverage note on Acme Corp valuation and risks, as of 2026-11-09.

<callout icon="📌" color="gray_bg">
**Summary.** Revenue growth slowed to 6%; margin held at 21% [1].
</callout>

| Metric | Value | As Of | Source |
|---|---|---|---|
| Revenue growth | 6% | 2026-09-30 | [1] |
| Operating margin | 21% | 2026-09-30 | [1] |

<table-of-contents />
```
Create it:
```bash
ntn api v1/pages -d "$(cat payload.json)" < /dev/null
```

## Validation checklist
- [ ] Exactly one summary callout before the TOC; at most 2 callouts per later section.
- [ ] One accent color across all `color="..."` values (`grep -o 'color="[a-z_]*"' | sort -u`).
- [ ] `grep -c '{{' page.md` is 0.
- [ ] Every `[n]` marker has a matching entry in `Sources` (count equal).
- [ ] `ntn pages get <ID>` shows the TOC and each appendix as a toggle, not literal tags.
- [ ] Key-figures row count equals the plan.
- [ ] Section headings equal the source outline.

## Failure handling
- Literal `<toggle>` or `<table-of-contents />` text: v1 dialect used; recreate through `v1/pages` v2 (archive the bad page with approval).
- 400 for rich text over 2,000 characters or over 100 blocks: re-run chunking.
- Missing source for a number: stop, ask the user; never invent a citation.
- 404: parent not shared with the integration. 429/529: honor `Retry-After`. 5xx on POST/PATCH: `ntn pages get` and compare before retrying.
- Image license unknown: omit the image or use a placeholder note.

## Safety constraints
- Explicit parent ID; new version as a new page, old version archived only with approval; no `--content` replace on pages with subpages.
- Do not alter figures or conclusions of the source document; flag suspected errors to the user instead.
- Test only under the "Skill Sandbox" page. Never print or store tokens; run `ntn` with stdin closed.
