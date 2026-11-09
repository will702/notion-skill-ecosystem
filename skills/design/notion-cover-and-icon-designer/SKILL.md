---
name: notion-cover-and-icon-designer
description: Chooses and applies page icons and covers, optimizes images locally, uploads them on the free plan and records source and license. Use when the user says "set a cover", "pick an icon", "optimize this image for Notion", "add a banner" or "make covers consistent".
---

# notion-cover-and-icon-designer

## Purpose
Select relevant, restrained icons and covers that match the art-direction brief, prepare image files locally, and set them on pages. Covers asset choice, optimization, upload and licensing; it does not decide the palette (`notion-art-director`).

## Activation triggers
- "Add a cover", "choose icons for these pages", "compress this image", "use this photo as banner".
- A page created by `notion-page-composer` or `notion-report-publisher` needs an icon or cover.
- `notion-visual-consistency` reports `D7` or `N5` findings.

## Required tools
| Capability | Label | How |
|---|---|---|
| Set page icon or cover (emoji, external URL) | API-supported (Docs only until validated; matrix: Not tested) | `ntn api v1/pages/<ID> -X PATCH -d '{"icon":...,"cover":...}'` |
| Set cover from an uploaded file | API-supported (Docs only; file_upload type for cover not yet exercised) | same PATCH with `{"type":"file_upload","file_upload":{"id":"<FILE_UPLOAD_ID>"}}` |
| Upload file, free plan | API-supported (Tested, up to 5 MB) | `v1/file_uploads` then `v1/file_uploads/<id>/send --file` |
| Image block in a page | API-supported (Tested) | see the placeholder swap in [enhanced-markdown.md](../../../references/enhanced-markdown.md) |
| Resize, crop, compress | external (local `magick`) | ImageMagick on the user's machine |
| Gallery covers, icon picker, "Add cover" button | UI-only | page hover menu; not exposed by the API |
| `ntn files create` | not usable | fails on the free plan |

CLI details: [notion-cli skill](../../../../.claude/skills/notion-cli/SKILL.md). Status of the PATCH rows is tracked in [capability-matrix.md](../../../references/capability-matrix.md).

## Dependencies
- Brief: `notion-art-director` (accent, icon set of 8 or fewer, cover style). Rules: [design-system.md](../../../references/design-system.md); filenames and captions: [naming.md](../../../references/naming.md); size limits: [api-limits.md](../../../references/api-limits.md).
- Owns: asset choice, optimization, upload, icon/cover PATCH. Does not own: page body (`notion-page-composer`), audits (`notion-visual-consistency`).

## Operating principles
1. Icons carry meaning from the brief's set; same meaning, same icon. Never the only status signal.
2. Prefer an external image URL you are licensed to use, or an uploaded file under 5 MB.
3. Covers: wide crop (about 3:1, for example 1500x500), muted, low contrast with the title, no text baked in.
4. Third-party images need a recorded source and license; caption text names both. Do not hotlink images you cannot license.
5. Relevance beats decoration: no cover is better than an unrelated one.
6. Optimize before upload: strip metadata, keep under 5 MB (target under 500 KB).

## Detailed workflow
Execution protocol:
1. **Analyze**: operational dashboard, relational tracking database, or documentation wiki? Dashboards usually get an icon only; wikis and reports may get a cover.
2. **Retrieve context**: fetch the page (`ntn api v1/pages/<ID>`), read current icon/cover, find the brief and the icon set; check for duplicate use of one icon across unrelated pages.
3. **Plan**: list page, icon, cover source, license, final filename. Wait for approval when replacing an existing icon or cover.
4. **Generate payload**: build the PATCH JSON with a script; optimize the image locally.
5. **Execute**: upload (if a file), then PATCH the page. Attach within about an hour of upload.
6. **Verify**: `GET v1/pages/<ID>` and compare `icon`/`cover` with the payload; for file uploads confirm the cover URL resolves in the response.
7. **Report**: page ID/URL, icon and cover applied, license and caption lines, and UI-only fallback (hover menu, Add cover) if the PATCH was rejected.

## Implementation instructions
Optimize with ImageMagick (external):
```bash
magick <INPUT> -resize 1500x500^ -gravity center -extent 1500x500 -strip -quality 82 <PAGE_SLUG>-01-<TOPIC>.jpg
```
Filename pattern: `<page-slug>-<nn>-<topic>.<ext>`. Check size: `stat -f%z <FILE>` (macOS) must be under 5242880.
Upload (free plan):
```bash
ntn api v1/file_uploads -d '{"mode":"single_part","filename":"<FILE>","content_type":"image/jpeg"}' < /dev/null
ntn api v1/file_uploads/<FILE_UPLOAD_ID>/send --file <FILE> < /dev/null
```
Set icon and external cover:
```bash
ntn api v1/pages/<PAGE_ID> -X PATCH -d '{"icon":{"type":"emoji","emoji":"📘"},"cover":{"type":"external","external":{"url":"<IMAGE_URL>"}}}' < /dev/null
```
Captions for in-page images: source name, author, license, link (rich text `link.url`, 2,000 characters max).

## Examples
Emoji icon only (no cover) for a dashboard:
```bash
ntn api v1/pages/<PAGE_ID> -X PATCH -d '{"icon":{"type":"emoji","emoji":"📌"}}' < /dev/null
```
Uploaded cover:
```bash
ntn api v1/pages/<PAGE_ID> -X PATCH -d '{"cover":{"type":"file_upload","file_upload":{"id":"<FILE_UPLOAD_ID>"}}}' < /dev/null
```
Caption record for a third-party image: `Source: Wikimedia Commons, <AUTHOR>, CC BY-SA 4.0` linked to the file page.

## Validation checklist
- [ ] `GET v1/pages/<ID>` shows the intended `icon` and `cover` types.
- [ ] Final file is 5,242,880 bytes or smaller (`stat`).
- [ ] Icon belongs to the brief's set; distinct icons across the scope are 8 or fewer.
- [ ] Every third-party image has source and license in its caption and in the report.
- [ ] Filename matches `<page-slug>-<nn>-<topic>.<ext>`.
- [ ] Upload was attached in the same run (no orphaned `file_upload` ids).

## Failure handling
- 400 on `cover` or `icon` shape: switch between `external` and `file_upload`; if still rejected, mark the capability not validated and give the UI steps (hover over the page title, Add cover, upload).
- 413 or size error: re-run `magick` with lower `-quality`, or smaller `-resize`.
- Upload expired (about 1 hour): upload again, do not reuse the id.
- 404: page not shared with the integration; ask the user to share it.
- 429/529: honor `Retry-After`. 5xx on PATCH: `GET` the page and compare before retrying.
- Unknown license: do not use the image; propose an own-made or solid-color cover.

## Safety constraints
- Never replace an existing icon or cover without approval; record the old value first.
- Use only images the user owns or that carry a compatible license.
- Test only under the "Skill Sandbox" page. Never print or store tokens; run `ntn` with stdin closed.
- Local `magick` writes to a new output file; never overwrite the original.
