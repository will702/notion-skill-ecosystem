# Formula 2.0 reference (validated)

Both reference formulas from the master prompt were added to a sandbox database through `PATCH v1/data_sources/<id>` as `{"properties":{"<Name>":{"formula":{"expression":"..."}}}}` and evaluated on a real row (2026-11-09).

## Progress bar (validated)
```
let(pct, prop("Completed") / prop("Total"),
  repeat("█", round(pct * 10)) + repeat("░", 10 - round(pct * 10)) + " " + format(round(pct * 100)) + "%")
```
Result for Completed 3, Total 4: `████████░░ 75%` (3/4 = 7.5 blocks, rounded to 8).
Guard against division by zero when Total can be 0: `if(prop("Total") == 0, "No items", ...)` (pattern, not yet exercised).

## Urgency flag (validated)
```
ifs(
  empty(prop("Due Date")), "No date",
  dateBetween(prop("Due Date"), now(), "days") < 0 and prop("Status") != "Done", "Overdue",
  dateBetween(prop("Due Date"), now(), "days") == 0 and prop("Status") != "Done", "Due today",
  "On track")
```
Result for a past due date with Status `Todo`: `Overdue`.
Note: `dateBetween(a, b, "days")` returns `a - b`, so a due date in the past gives a negative number.

## Rules
- Plain-text labels are the accessible default. Colored-dot emoji (⚪🔴🟡🟢) only if the workspace icon convention allows them, never as the only signal.
- Formulas reference property names; renaming a property breaks them. Keep names in `naming.md` stable.
- Put formulas in the **master** database, not in dashboards.
- To change a formula, PATCH the data source again with the full expression; re-query one row to verify.
