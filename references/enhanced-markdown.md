# Enhanced Markdown (Notion-flavored Markdown) reference

Source of truth: https://developers.notion.com/guides/data-apis/notion-flavored-markdown.md . Every row below is marked **Tested** (round-tripped on the sandbox on 2026-11-09 with `ntn` 0.23.28) or **Docs only**.

## Which entry point to use
| Entry point | Markdown dialect | Use for |
|---|---|---|
| `ntn pages create --content` / `ntn pages edit --content` | **v1 (deprecated default)**. Callouts, tables, equations, code, columns, dividers, to-dos, quotes work. Toggles, toggle headings, `<table-of-contents />` and `<synced-block>` come out as literal paragraphs. | Quick prose pages |
| `ntn api v1/pages -d '{"parent":{...},"markdown":"...","markdown_version":"v2"}'` | **v2 (recommended)**. Everything in the table below. | Any layout with toggles, TOC, synced blocks |
| `ntn api v1/pages/{id}/markdown -X PATCH` | Page markdown update endpoint (Tested, `update_content`) | Targeted edits |

Rule: when a page needs toggles, a table of contents or synced blocks, create it through `v1/pages` with `"markdown_version":"v2"`. Send `\n` as real JSON newlines (build the JSON with a script, never by hand-quoting).

## Block syntax (v2)
| Block | Syntax | Status |
|---|---|---|
| Heading 1-3 | `#`, `##`, `###` (H4 via `####`) | Tested |
| Callout | `<callout icon="💡" color="gray_bg">` newline body newline `</callout>` | Tested |
| Quote | `> text` | Tested |
| Columns | `<columns><column ratio="30">...</column><column ratio="70">...</column></columns>` | Tested (2 columns) |
| Divider | `---` | Tested |
| Toggle (plain) | `<toggle>` title, blank line, body, `</toggle>` | Tested (v2 only) |
| Toggle heading | `<toggle heading="h2">` title, blank line, body, `</toggle>` | Tested (v2 only) |
| Table of contents | `<table-of-contents />` | Tested (v2 only) |
| Synced block (original) | `<synced-block>` content `</synced-block>` | Tested (v2 only); a reference to an existing original needs its URL, Docs only |
| To-do | `- [ ]` / `- [x]` | Tested |
| Pipe table | `\| a \| b \|` with separator row; cells inline-only, `<br />` for breaks | Tested |
| Styled table | `<table header-row="true">` with `<tr><td>` | Docs only |
| Inline equation | `$E=mc^2$` | Tested |
| Block equation | `$$` on its own line, expression, `$$` on its own line (never same-line `$$...$$` or `\[...\]`) | Tested |
| Code | fenced with a language | Tested |
| Image | `![caption](url)` for URLs; uploaded files cannot be referenced from Markdown, so use a placeholder paragraph and swap it for an image block (below) | Tested |
| Mentions, dates, colors | `<mention url=...>`, `<date start=...>`, `<span color=...>` | Docs only |

## Colors: two spellings
- In Markdown tags: `gray_bg`, `blue_bg`, `yellow_bg` ... (Tested).
- In the block JSON API (`v1/blocks/.../children`): `gray_background`, `blue_background`, `yellow_background` ... Using `_bg` there returns a 400 validation error (hit during testing).

## Uploaded images (free-plan safe recipe)
1. `ntn api v1/file_uploads -d '{"mode":"single_part","filename":"x.png","content_type":"image/png"}'` then `ntn api v1/file_uploads/<id>/send --file x.png` (files up to 5 MB; `ntn files create` uses multipart and fails on the free plan).
2. Create the page with a placeholder paragraph such as `{{IMG:name}}`.
3. Find the placeholder block (recurse into callouts), `PATCH v1/blocks/<parent>/children` with an `image` block of `type: file_upload` and `position: {"type":"after_block","after_block":{"id":"<placeholder>"}}`, then `DELETE` the placeholder.
4. Upload and attach in the same run: unattached uploads expire after about an hour.

## Generic Markdown to Notion mapping (for `notion-markdown-ingest`)
| Input | Output |
|---|---|
| `# / ## / ###` | heading_1 / heading_2 / heading_3 (page title from the first H1) |
| `- [ ]` | to_do |
| fenced code | code block, keep the language |
| `> [!NOTE]`, `> [!TIP]`, other GitHub alerts | `<callout>` with a matching icon |
| plain blockquote | quote |
| LaTeX `\[ \]`, `equation` env | `$$` block on its own lines |
| `\tcolorbox`-style boxes | `<callout>`; body lines unprefixed, nested tables and code stay inside |
| rich-text run over 2,000 characters | split into consecutive paragraphs |

## Placing a linked view at a marker

Tested (sandbox, ntn 0.23.28). `POST v1/views` with `create_database` appends the `<database ...></database>` block at the END of the page. To place it:
1. Create the page with a standalone marker paragraph, e.g. `{{VIEW:By Status}}`.
2. `POST v1/views` with `create_database`.
3. `GET v1/pages/<id>/markdown?markdown_version=v2` and find the trailing `<database .../>` tag.
4. `PATCH v1/pages/<id>/markdown`:
   `{"markdown_version":"v2","type":"update_content","update_content":{"content_updates":[{"old_str":"\n\n<tag>","new_str":""},{"old_str":"\\{\\{VIEW:By Status\\}\\}","new_str":"<tag>"}]}}`
The marker reads back with backslash-escaped braces, so match with tolerant escaping. Works inside columns; the master database is unchanged and the linked block is a distinct block. Automated by `scripts/instantiate_template.py` (markers are `{{VIEW:Name}}` or `{{VIEW:Database/Name}}`).

## Cautions
- Community specs (for example Claude-m's `::: callout` and `{toggle="true"}`) differ from the official syntax above. Follow this file.
- A `<page>` tag in an `update` that omits an existing subpage can delete it; never run content replacement on a page with subpages without `allow_deleting_content` being deliberate.
