---
name: notion-page-composer
description: Composes Notion pages from a brief using headings, callouts, columns, dividers, tables, toggles, synced blocks and a table of contents, then creates them with v2 enhanced Markdown through `ntn api v1/pages`. Use when the user says "build a page", "create a page with toggles", "lay out this page", "add a table of contents" or "turn this brief into a page".
---

# notion-page-composer

## Purpose
Turn an art-direction brief plus content into a valid v2 enhanced-Markdown payload and create (or append to) the page under an explicit parent. Owns layout, block syntax and the v1-vs-v2 decision. Does not decide the look (that is `notion-art-director`) and does not convert arbitrary Markdown files (that is `notion-markdown-ingest`).

## Activation triggers
- "Create a page", "lay out", "add toggles / columns / TOC / synced header", "make a template page".
- A brief from `notion-art-director` exists and needs materializing.
- A report or long document needs a page shell (called by `notion-report-publisher`).

## Required tools
| Capability | Label | How |
|---|---|---|
| Create page, v2 Markdown | API-supported (Tested) | `ntn api v1/pages` with `"markdown_version":"v2"` |
| Create page, v1 Markdown | API-supported (Tested) | `ntn pages create --parent page:<id> --content` |
| Read back as Markdown | API-supported (Tested) | `ntn pages get <ID>` |
| Append blocks / insert after a block | API-supported (Tested) | `PATCH v1/blocks/<id>/children` with `position` |
| Toggles, toggle headings, TOC, synced original | API-supported (Tested, v2 only) | tags in [enhanced-markdown.md](../../../references/enhanced-markdown.md) |
| Synced reference to an existing original | API-supported (Docs only) | `<synced-block-reference url="...">` with the original's URL |
| Styled `<table>` tags | API-supported (Docs only) | prefer pipe tables |
| Page width, page font | UI-only | page `...` menu; breadcrumbs follow parent hierarchy |
| MCP create/update | MCP-supported (Not tested) | intended usage only; OAuth pending |

CLI details: [notion-cli skill](../../../../.claude/skills/notion-cli/SKILL.md).

## Dependencies
- Syntax and colors: [enhanced-markdown.md](../../../references/enhanced-markdown.md). Rules: [design-system.md](../../../references/design-system.md). Names: [naming.md](../../../references/naming.md). Limits: [api-limits.md](../../../references/api-limits.md).
- Upstream: `notion-art-director` supplies the brief. Sibling: `notion-cover-and-icon-designer` sets icon/cover after creation. Large or file-derived content: `notion-markdown-ingest`.
- Owns: payload shape and page creation. Does not own: schemas (`notion-database-architect`), audits (`notion-visual-consistency`).

## Operating principles
1. **v1-vs-v2 decision rule**: if the page needs any of toggle, toggle heading, `<table-of-contents />`, `<synced-block>`, use `v1/pages` with `markdown_version: "v2"`. Otherwise either works; default to v2 so later edits do not change dialect. `ntn pages create` is v1 and renders those tags as literal text.
2. The first H1 becomes the page title; do not repeat it as a body heading.
3. Skeleton order: purpose line, optional one status callout, columns (30/70) or prose, divider, secondary content, divider, toggle `Archive`.
4. Design-system limits: one accent, at most 2 callouts per major section, none directly under an empty heading.
5. Build JSON with a script (`json.dumps`), never hand-quoted shell strings.
6. Colors in Markdown use `gray_bg`; block JSON uses `gray_background`. Mixing returns 400.

## Detailed workflow
Execution protocol:
1. **Analyze**: operational dashboard, relational tracking database page, or documentation wiki? Pick the matching skeleton.
2. **Retrieve context**: search for the parent and any page with the same title (`ntn api v1/search`); read the brief; record the parent ID.
3. **Plan**: show the heading outline, block types and column layout. Wait for approval when appending to or replacing existing content.
4. **Generate payload**: write the Markdown, then wrap with `json.dumps`. Check columns 2 to 3 with ratios summing to 100, callout count, one accent, content under every heading. Split rich text over 2,000 characters.
5. **Execute**: `POST v1/pages` (new) or `PATCH v1/blocks/<id>/children` (append, at most 100 blocks per call, 2 nesting levels per request). `ntn pages edit --content` REPLACES the body: only after backup (`ntn pages get`) and explicit approval, never if subpages exist.
6. **Verify**: `ntn pages get <NEW_ID>`; compare heading list, callout count, toggle and TOC presence against the payload.
7. **Report**: page URL/ID, layout summary, UI-only follow-ups (font, width; icon via `notion-cover-and-icon-designer`).

## Implementation instructions
Build and create (stdin closed):
```bash
python3 -I - <<'PY' > payload.json
import json
md = open("page.md", encoding="utf-8").read()
print(json.dumps({"parent": {"type": "page_id", "page_id": "<PARENT_PAGE_ID>"},
                  "markdown": md, "markdown_version": "v2"}))
PY
ntn api v1/pages -d "$(cat payload.json)" < /dev/null
```
Quick syntax map (statuses in the reference): callout `<callout icon="💡" color="gray_bg">`, columns `<columns><column ratio="30">`, toggle `<toggle>` title, blank line, body, `</toggle>`, toggle heading `<toggle heading="h2">`, divider `---`, block equation `$$` on its own lines, pipe tables with a separator row.
Synced header: create the original once with `<synced-block>`; reuse elsewhere only with its block URL (Docs only).
Append after a block:
```bash
ntn api v1/blocks/<PAGE_ID>/children -X PATCH -d '{"children":[...],"position":{"type":"after_block","after_block":{"id":"<BLOCK_ID>"}}}' < /dev/null
```

## Examples
Minimal wiki page (v2):
```markdown
# Release Process

One page that explains how a release ships.

<table-of-contents />

---

## Steps
1. Freeze the branch.
2. Tag and publish.

<toggle heading="h2">Archive

Older notes live here.
</toggle>
```
Create a small one under a parent:
```bash
ntn api v1/pages -d '{"parent":{"type":"page_id","page_id":"<PARENT_PAGE_ID>"},"markdown":"# Release Process\n\nOne page.\n\n<table-of-contents />\n\n---\n\n## Steps\n\n- Freeze\n","markdown_version":"v2"}' < /dev/null
```

## Validation checklist
- [ ] Payload has `"markdown_version":"v2"` whenever a toggle, TOC or synced block is present (`grep -c '<toggle\|<table-of-contents\|<synced-block' page.md`).
- [ ] `ntn pages get <ID>` shows the tags as blocks, not literal `<toggle>` text.
- [ ] Exactly one H1; title follows [naming.md](../../../references/naming.md).
- [ ] At most 2 callouts per H2 section, one accent color only.
- [ ] Column ratios sum to 100; 2 or 3 columns.
- [ ] Every rich-text run is 2,000 characters or fewer; every append call 100 blocks or fewer.
- [ ] Parent ID was explicit and recorded in the report.

## Failure handling
- 400 validation: check color spelling (`_bg` vs `_background`), malformed tags, or a `$$` not on its own line; fix and resend.
- 404: parent not shared with the integration; ask the user to share it.
- 429/529: honor `Retry-After`. 5xx on POST/PATCH: re-search by title or re-read children before retrying; never retry blind.
- Literal `<toggle>` text on the page: v1 dialect was used; recreate with v2 (archive the bad page, with approval).
- Rich text over 2,000 characters or over 100 blocks: split via [notion-markdown-ingest](../../engineering/notion-markdown-ingest/SKILL.md).

## Safety constraints
- Always pass an explicit parent ID; never create at workspace root by default.
- Back up before any `--content` replacement; get approval; prefer appending over replacing.
- Test only under the "Skill Sandbox" page; test pages start with `Test `.
- Never print or store tokens; run `ntn` with stdin closed.
