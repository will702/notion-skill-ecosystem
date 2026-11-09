# Report template

`page.md` is a v2 enhanced-Markdown report skeleton: purpose line, one summary callout, key-figures table, table of contents, three numbered sections, two toggled appendices, Sources. It contains toggles and a TOC, so it must be created with `markdown_version: "v2"` (see [enhanced-markdown.md](../../references/enhanced-markdown.md)). `ntn pages create` would render those tags as literal text.

## Placeholders
`{{TITLE}}` (Title Case, no emoji), `{{PURPOSE_LINE}}`, `{{ACCENT}}` (`gray`, `blue` or `green`; one accent for the whole page), `{{SUMMARY}}`, `{{KEY_FIGURES_ROWS}}` (lines like `| Revenue growth | 6% | 2026-09-30 | [1] |`), `{{SECTION_n_TITLE}}`, `{{SECTION_n_BODY}}`, `{{APPENDIX_x_TITLE}}`, `{{APPENDIX_x_BODY}}`, `{{SOURCES_NUMBERED_LIST}}`. Delete unused sections entirely instead of leaving empty headings.

## Instantiate
1. Fill the placeholders with a script and write `filled.md`; check none remain: `grep -c '{{' filled.md` must print 0.
2. Build the payload (never hand-quote JSON):
```bash
python3 -I -c 'import json;print(json.dumps({"parent":{"type":"page_id","page_id":"<PARENT_PAGE_ID>"},"markdown":open("filled.md",encoding="utf-8").read(),"markdown_version":"v2"}))' > payload.json
```
3. Create under an explicit parent (stdin closed):
```bash
ntn api v1/pages -d "$(cat payload.json)" < /dev/null
```
4. Verify: `ntn pages get <NEW_PAGE_ID> < /dev/null`; confirm the TOC and both appendices are blocks, not literal tags.

For bodies over 2,000 characters per paragraph or 100 blocks, chunk with [notion-markdown-ingest](../../skills/engineering/notion-markdown-ingest/SKILL.md); the full workflow is in [notion-report-publisher](../../skills/engineering/notion-report-publisher/SKILL.md). Test only under the "Skill Sandbox" page.
