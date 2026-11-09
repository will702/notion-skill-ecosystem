---
name: notion-art-director
description: Defines the visual identity of a Notion workspace or page set (accent color, icon set, density, cover style, type hierarchy) and writes a short art-direction brief that other skills consume. Use when the user says "art direct", "design direction", "make it look premium", "pick a style", "visual identity" or "avoid generic AI look".
---

# notion-art-director

## Purpose
Own the high-level look. Decide accent, icon set, density, cover style and heading hierarchy once, write them into a brief of at most 15 lines, and hand it to `notion-page-composer` (layout), `notion-cover-and-icon-designer` (assets) and `notion-visual-consistency` (audit). This skill produces decisions, not pages.

## Activation triggers
- "Give this workspace a visual identity", "art direction for my dashboard", "make it editorial / premium / minimal".
- A new project area starts and no brief exists (search for a page named `Art Direction Brief`).
- A user rejects output as "generic", "AI-looking" or "cluttered".
- Not for: building the page itself (use `notion-page-composer`), checking existing pages (use `notion-visual-consistency`).

## Required tools
| Capability | Label | How |
|---|---|---|
| Search for an existing brief or sample pages | API-supported (Tested) | `ntn api v1/search -d '{"query":"Art Direction Brief"}' < /dev/null` |
| Read a reference page as Markdown | API-supported (Tested) | `ntn pages get <PAGE_ID> < /dev/null` |
| Store the brief as a page | API-supported (Tested) | create via `notion-page-composer` |
| Apply fonts per block, custom CSS, themes | UI-only | Notion offers only page-level font choice (Default, Serif, Mono) and full width/small text toggles in the page `...` menu |
| Brand fonts or image generation | external | outside Notion; import results as files |

CLI usage details: [notion-cli skill](../../../../.claude/skills/notion-cli/SKILL.md).

## Dependencies
- Rules source: [design-system.md](../../../references/design-system.md) (one accent, at most 8 icons, 2 to 3 columns, callout limits), [naming.md](../../../references/naming.md).
- Consumers: `notion-page-composer` owns layout and payloads; `notion-cover-and-icon-designer` owns images; `notion-visual-consistency` verifies the brief is followed.
- This skill never writes block payloads and never edits existing pages.

## Operating principles
1. Restraint over decoration: one accent (`gray` default, `blue` slate or `green` muted), reused everywhere.
2. Hierarchy comes from structure: H1 title, H2 sections, H3 sub-sections, dividers between sections, no skipped levels.
3. Density is a choice: `compact` (tables, toggles, 2 columns) for operational pages, `airy` (prose, quotes, few callouts) for wikis and reports.
4. Type pairing is limited to Notion page fonts: Default (sans) for operational, Serif for reports and essays, Mono only for technical logs. State it as a per-page recommendation (`UI-only` to apply).
5. Anti-generic checklist: no identical card grids, no emoji rows, no callout on every heading, no more than 8 icons in the set, no gradient-like color stacking.
6. A brief is falsifiable: every line must be checkable by `notion-visual-consistency`.

## Detailed workflow
Execution protocol (read-only until step 5):
1. **Analyze**: classify the target as operational dashboard, relational tracking database, or documentation wiki; note audience and desktop/mobile use.
2. **Retrieve context**: search for an existing `Art Direction Brief`, sibling pages and the parent ID; read two or three existing pages with `ntn pages get` to extract current accent, icons and density. Check for duplicate brief names.
3. **Plan**: draft the brief (below) and show it. Wait for approval if it would change an existing workspace's established look.
4. **Generate payload**: render the brief as v2 Markdown (hand to `notion-page-composer`); at most one callout.
5. **Execute**: create the `Art Direction Brief` page under the explicit parent via `notion-page-composer`.
6. **Verify**: `ntn pages get <BRIEF_ID>` and confirm every field below is present with a concrete value.
7. **Report**: brief page URL/ID, chosen accent and icon set, and UI-only steps (font choice, full-width toggle) the user must apply.

## Implementation instructions
Brief fields (all required, one line each):
- `Purpose`: the single stated purpose of the area.
- `Accent`: `gray` | `blue` | `green` (callouts use `<accent>_bg` and `default` only).
- `Icons`: at most 8 emoji with meanings, for example 📌 pinned, 📥 inbox, 🗂 archive, ✅ done.
- `Density`: `compact` or `airy`; max columns (2 default, 3 at most; ratios 30/70).
- `Cover style`: `none`, `solid <accent>` or `photo, muted, 3:1 crop`; sourcing rule in `notion-cover-and-icon-designer`.
- `Heading scale`: H1 title once, H2 per section, H3 sparingly; dividers between H2 sections.
- `Page font`: Default, Serif or Mono (UI-only).
- `Avoid`: copy the relevant lines from the design-system "Avoid" list by link, not text.

## Examples
Brief rendered as v2 Markdown for `notion-page-composer`:
```markdown
# Art Direction Brief

<callout icon="📌" color="gray_bg">
Applies to the Research area. Revisit when the area adds a second audience.
</callout>

## Decisions
- Purpose: reading and citing research.
- Accent: gray. Callouts: gray_bg or default only.
- Icons: 📌 pinned, 📥 inbox, 🗂 archive, ✅ done, 📘 reference.
- Density: airy; 2 columns max (30/70).
- Cover style: solid gray, no photos.
- Page font: Serif (UI-only).
```
Lookup of an existing brief:
```bash
ntn api v1/search -d '{"query":"Art Direction Brief","filter":{"property":"object","value":"page"}}' < /dev/null
```

## Validation checklist
- [ ] Brief names exactly one accent from `gray`, `blue`, `green`.
- [ ] Icon list length is 8 or fewer and each icon has a meaning.
- [ ] Column maximum is 2 or 3 and ratios sum to 100.
- [ ] Page title follows [naming.md](../../../references/naming.md) (Title Case, no emoji, no trailing punctuation).
- [ ] `ntn pages get <BRIEF_ID>` returns every field above.
- [ ] No more than 1 callout in the brief page.

## Failure handling
- Search returns nothing: assume no brief; create one only after approval.
- 404 on a page: not shared with the integration; ask the user to share it, do not guess.
- 429/529: wait `Retry-After`, retry. 5xx on a create: re-search by title before retrying to avoid duplicates.
- Conflicting existing looks (two accents found): report both, ask which wins; do not merge silently.
- Request for custom fonts or CSS: state it is not possible in Notion (UI-only font choice, otherwise external).

## Safety constraints
- Read-only on existing content; the only write is one new brief page under an explicit parent.
- Test only under the "Skill Sandbox" page; scratch pages start with `Test `.
- Never print or store tokens; run `ntn` with stdin closed.
- Never restyle or delete existing user pages; propose, then wait for approval.
