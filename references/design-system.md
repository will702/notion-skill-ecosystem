# Design system (all skills must follow it)

Aesthetic: minimalist, modern, editorial, premium, functional, information-dense without clutter. Every rule below is something a skill can check mechanically; if it can't be checked, it isn't a rule.

## Principles
1. Every page has one stated purpose, every database a reason to exist, every dashboard a clear hierarchy (summary first, queues second, archive last).
2. **One neutral accent color per dashboard.** Default `gray`; alternatives `blue` (slate) or `green` (muted). Callout and table colors use only that accent plus `default`. Status colors (red/yellow/green) appear only inside status or select options.
3. **Icons:** one style per workspace. Default: a restrained emoji set of at most 8 icons reused by meaning (for example 📌 pinned, 📥 inbox, 🗂 archive, ✅ done). Never use an emoji as the only status signal; pair it with text.
4. **Layout:** dividers between sections. Dashboards use 2 columns (3 at most): a narrow left column (`ratio="30"`) for navigation, quick links and counters, a wide right column (`ratio="70"`) for the core boards or queues. Anything needing more than 3 columns becomes a stacked section. Mobile collapses columns, so the page must read correctly in one column.
5. **Callouts:** at most 1 to 2 per major section, for status banners, rules or agendas. Never decorative.
6. **Toggles** hide dense logs, raw metadata and archives. Needs `markdown_version: "v2"` (see `enhanced-markdown.md`).
7. **Whitespace is intentional.** Vary blocks (callout, quote, table, toggle) only where content calls for it.
8. **Naming:** follow `naming.md`.
9. **Navigation:** a synced block for global headers and quick actions (original created with `<synced-block>`), breadcrumbs via parent hierarchy, a `<table-of-contents />` on long pages.
10. Optimize for desktop and mobile. Prefer useful interactive elements (filtered views, relations) over decorative widgets.

## Avoid
Excessive emojis, unnecessary callouts, nesting deeper than 3 levels of pages, decorative blocks without purpose, inconsistent headings, many near-duplicate databases, generic AI-looking dashboard layouts (identical card grids, gradient-like emoji rows, a callout on every heading).

## Data architecture
- **Master databases** store raw records and formulas. **Dashboards** contain only linked views (`v1/views` with `create_database`, or `view_id` widgets in a dashboard view) of master databases. Never copy rows into a dashboard.
- Relate entities with explicit relations and rollups. Do not duplicate free-text tags across related entities; use a relation to a Tags/Areas database instead.
- Use Formula 2.0 for badges, meters and relative-time flags (`formulas.md`).
- Status workflow uses a `status` or `select` property with plain-text option names.

## Page skeleton (default dashboard)
1. Title and one-line purpose.
2. Status banner callout (optional, one).
3. `<columns>`: left 30% (quick links, counters), right 70% (primary board or queue).
4. Divider, secondary views (calendar, table).
5. Divider, toggle heading `Archive` containing logs and old views.

## Design checks a skill must run before reporting
- Exactly one accent color used.
- At most 2 callouts per major section, no callout directly under a heading without content.
- Columns count 2 to 3, ratios sum to 100.
- No emoji-only status.
- Every database/dashboard page has an explicit parent and a title that follows `naming.md`.
- All dashboard views are linked to a master database (no pasted copies).
