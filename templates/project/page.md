# {{PROJECT_NAME}} Dashboard

One purpose: show where {{PROJECT_NAME}} stands and what needs attention this week.

<callout icon="📌" color="gray_bg">
**Status:** {{STATUS}} | **Progress:** {{PROGRESS}} | **Due:** {{DUE_DATE}}
</callout>

<columns>
<column ratio="30">

### Quick Links

- [Tasks]({{TASKS_URL}})
- [Milestones]({{MILESTONES_URL}})
- [Risks]({{RISKS_URL}})

**Owner:** {{OWNER}}

</column>
<column ratio="70">

### Open Tasks

{{VIEW:Tasks/Open}}

</column>
</columns>

---

## Milestones

{{VIEW:Milestones/All}}

## Risks

{{VIEW:Risks/Open}}

---

## Weekly Report

### Summary

{{WEEKLY_SUMMARY}}

### Overdue

| Task | Assignee | Due |
| --- | --- | --- |
| {{OVERDUE_TASK}} | {{ASSIGNEE}} | {{DUE}} |

---

<toggle heading="h2">
Archive

{{ARCHIVE_LINKS}}

</toggle>
