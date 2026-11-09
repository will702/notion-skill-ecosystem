# Productivity Dashboard

Decide what to do today and this week from one task list.

<callout icon="📌" color="gray_bg">
Source of truth: the Tasks database. This page holds linked views only; edit rows there.
</callout>

<columns>
<column ratio="30">
## Focus

{{VIEW:Due This Week}}
</column>
<column ratio="70">
## Board

{{VIEW:By Status}}
</column>
</columns>

---

## Calendar

{{VIEW:Calendar}}

---

<toggle heading="h2">
Archive

{{VIEW:All}}
</toggle>
