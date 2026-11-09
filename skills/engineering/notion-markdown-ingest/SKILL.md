---
name: notion-markdown-ingest
description: Converts Markdown, including LaTeX-derived Markdown, into Notion v2 enhanced Markdown or block batches, handling 2,000-character splits, 100-block chunks, callouts, equations and image placeholders. Use when the user says "import this Markdown", "convert to Notion", "upload my notes", "paste LaTeX/Markdown into Notion" or "long document is too big".
---

# notion-markdown-ingest

## Purpose
Fill a gap: research found no reliable community Markdown-to-Notion converter, so this skill defines the mapping, the size-safe chunking and the image swap. It transforms text and writes it to an explicit parent; layout polish belongs to `notion-page-composer`.

## Activation triggers
- A `.md` file, pasted Markdown or LaTeX-derived Markdown (pandoc output, `\[ \]`, `tcolorbox`) must become a Notion page.
- Content exceeds 2,000 characters in one paragraph or 100 blocks.
- Images must appear in an imported page.

## Required tools
| Capability | Label | How |
|---|---|---|
| Create page from v2 Markdown | API-supported (Tested) | `ntn api v1/pages` with `markdown_version: "v2"` |
| Append batches | API-supported (Tested) | `PATCH v1/blocks/<id>/children`, at most 100 children |
| Read back | API-supported (Tested) | `ntn pages get <ID>` |
| Upload images (free plan) | API-supported (Tested, 5 MB) | `v1/file_uploads` then `.../send --file` |
| Swap placeholder for image block, delete placeholder | API-supported (Tested) | `PATCH` children with `after_block`, `DELETE v1/blocks/<id>` |
| Chunking | external (local Python) | `scripts/split_chunks.py`, stdlib only |
| Pandoc or LaTeX compile | external | optional, outside Notion |
| Import through the Notion UI (Import menu) | UI-only | fallback for formats this skill cannot handle |

CLI details: [notion-cli skill](../../../../.claude/skills/notion-cli/SKILL.md).

## Dependencies
- Mapping table (do not copy): [enhanced-markdown.md](../../../references/enhanced-markdown.md) section "Generic Markdown to Notion mapping". Limits: [api-limits.md](../../../references/api-limits.md).
- Layout and page creation conventions: `notion-page-composer` (it owns the final payload shape and design checks). Long reports: `notion-report-publisher` calls this skill.
- Approach that worked in practice: a converter script, an insert script and an attach script (callout conversion, anchor-based image insert, placeholder swap), reimplemented here as the workflow below.

## Operating principles
1. Convert to v2 Markdown first; use block JSON only for images and appends.
2. Split on structure: blank-line units; never split inside a fence, `<callout>`, `<toggle>` or `$$` block unless a single unit exceeds 2,000 characters.
3. Block JSON colors use `gray_background`; Markdown tags use `gray_bg`.
4. Tables inside callouts: put pipe tables unprefixed inside the `<callout>` body; blockquote prefixes (`> `) are stripped first.
5. Equations: `$$` alone on its line, expression, `$$` alone; expression at most 1,000 characters; inline `$..$`. Convert `\[ \]` and `equation` environments.
6. Images: standard Markdown image syntax with an external https URL is used for hosted images; uploaded files use a `{{IMG:name}}` placeholder paragraph.
7. Drop the leading `# Title` from the body only if it is also supplied as the page title; otherwise the first H1 becomes the title.

## Detailed workflow
Execution protocol:
1. **Analyze**: is the destination an operational dashboard, relational tracking database, or documentation wiki? Imports are almost always wiki or report pages.
2. **Retrieve context**: search for the parent and same-title pages (`ntn api v1/search`), note existing children to avoid duplicates, inventory images and their licenses.
3. **Plan**: show heading outline, counts (characters, units, batches, callouts, equations, images). Wait for approval if appending to an existing page.
4. **Generate payload**: convert per the mapping, then run `scripts/split_chunks.py`. Validate: balanced tags, `$$` pairs, no run over 2,000 characters.
5. **Execute**: small input (one unit list under the request limits of 1,000 blocks and 500 KB): single `POST v1/pages`. Larger: create the page with the first batch, then `PATCH` children per later batch, in order, one at a time. Upload images, attach by placeholder swap within about an hour.
6. **Verify**: `ntn pages get <ID>`; compare heading list, callout and equation counts, character total (within tolerance for escapes) and block count.
7. **Report**: page URL/ID, counts, batches sent, images attached, anything UI-only (page font, covers).

## Implementation instructions
Chunk locally (no network):
```bash
python3 -I skills/engineering/notion-markdown-ingest/scripts/split_chunks.py input.md > chunks.json
```
Output: `{"units": N, "batches": [[...<=100 units], ...]}`; options `--max-chars`, `--max-blocks`. Fences that must be split are closed and reopened with the same language.
Convert alerts: `> [!NOTE]` to `<callout icon="📘" color="gray_bg">`, `> [!TIP]` to icon 💡, `> [!WARNING]` to icon ⚠️, all in the one accent (`default` if the brief says none).
Append a batch (build JSON with `json.dumps` from the chunk list; Markdown append goes through the page-creation payload, block JSON through `children`):
```bash
ntn api v1/blocks/<PAGE_ID>/children -X PATCH -d @batch.json < /dev/null
```
(If `-d @file` is unsupported in your `ntn` version, use `-d "$(cat batch.json)"`.)
Swap an image: find the paragraph `{{IMG:name}}` (recurse into callouts via `has_children`), then:
```bash
ntn api v1/blocks/<PARENT_ID>/children -X PATCH -d '{"children":[{"type":"image","image":{"type":"file_upload","file_upload":{"id":"<FILE_UPLOAD_ID>"}}}],"position":{"type":"after_block","after_block":{"id":"<PLACEHOLDER_ID>"}}}' < /dev/null
ntn api v1/blocks/<PLACEHOLDER_ID> -X DELETE < /dev/null
```

## Examples
Input and output:
````markdown
> [!TIP]
> Cache the result.

\[ E = mc^2 \]
````
becomes
```markdown
<callout icon="💡" color="gray_bg">
Cache the result.
</callout>

$$
E = mc^2
$$
```
Create from converted Markdown (placeholder kept for later image swap):
```bash
ntn api v1/pages -d "$(python3 -I -c 'import json;print(json.dumps({"parent":{"type":"page_id","page_id":"<PARENT_PAGE_ID>"},"markdown":open("page.nfm.md",encoding="utf-8").read(),"markdown_version":"v2"}))')" < /dev/null
```

## Validation checklist
- [ ] `chunks.json` max unit length is 2,000 or fewer: `python3 -I -c "import json;d=json.load(open('chunks.json'));print(max(len(u) for b in d['batches'] for u in b))"`.
- [ ] Every batch has 100 or fewer units.
- [ ] `grep -c '<callout' ` equals `grep -c '</callout>'` in the converted file; `$$` lines are even in count.
- [ ] `ntn pages get <ID>` heading list equals the source heading list.
- [ ] No `{{IMG:` text remains on the page after attach.
- [ ] No `[!NOTE]`-style literal alerts remain.

## Failure handling
- 400 validation: rich text over 2,000 characters, equation over 1,000, bad color spelling, or unbalanced tag; re-split or fix and resend only that batch.
- 413 or payload error: reduce the batch size under 500 KB.
- 404: parent not shared with the integration.
- 429/529: honor `Retry-After`. 5xx on POST/PATCH: `ntn pages get <ID>` and compare the block count before resending a batch (duplicate-write risk).
- Upload expired (about 1 hour): re-upload, then attach in the same run.
- Free workspace with more than one member hits the 1,000 lifetime block limit: stop and report.

## Safety constraints
- Explicit parent ID always; never replace an existing page body without backup and approval.
- Only third-party images with a recorded source and license; captions follow [naming.md](../../../references/naming.md).
- Test only under the "Skill Sandbox" page. Never print or store tokens; run `ntn` with stdin closed.
- `split_chunks.py` is local and offline; run with `python3 -I`.
