# {{RESEARCH_TOPIC}} Research Dashboard

One purpose: track sources, claims, hypotheses and experiments for {{RESEARCH_TOPIC}}.

<callout icon="📌" color="gray_bg">
**Citation rule.** Every claim links to a source row. Unverified metadata stays marked Unverified; nothing is guessed.
</callout>

<columns>
<column ratio="30">

### Quick Links

- [Sources]({{SOURCES_URL}})
- [Notes]({{NOTES_URL}})
- [Hypotheses]({{HYPOTHESES_URL}})
- [Experiments]({{EXPERIMENTS_URL}})

**Unsourced claims:** {{UNSOURCED_COUNT}}

</column>
<column ratio="70">

### Hypotheses by Status

{{VIEW:Hypotheses/By Status}}

</column>
</columns>

---

## Unsourced Claims

{{VIEW:Notes/Unsourced Claims}}

## Sources by Verification

{{VIEW:Sources/By Verification}}

---

<toggle heading="h2">
Experiment Log

{{EXPERIMENT_LOG}}

</toggle>
