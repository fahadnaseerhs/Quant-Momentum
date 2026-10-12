---
name: feedback-methodology-writing-style
description: How to write every Methodology note in Obsidian — complete, clear, concise, intuition-first, undergrad-friendly.
metadata:
  type: feedback
---

**Rule:** Every note in `Quant_Momentum/Methodology/` must satisfy three properties simultaneously:

1. **Completeness** — cover every relevant concept, including the underlying finance methodology and finance-concept intuition, not just the mechanics of the task.
2. **Clarity** — accessible to an undergraduate student. If a concept is technical, **build the intuition first**, then the math. Use ordinary words.
3. **Conciseness** — say each thing once. If it must be said a second time (rare), frame it as an explicit reminder (e.g., "*Reminder from Task 01: …*").

**Why:** User asked for these three properties by name on 2026-09-27 when Methodology/02 was being planned. The Obsidian folder is their study resource — noise and repetition make it useless as a learning tool; missing intuition or missing finance concepts make it useless as a first-project reference.

**How to apply:**
- For any technical concept (log returns, LOCF, filtration, volatility scaling, walk-forward, Sharpe, etc.): open with an intuition or analogy in plain English, THEN present the mathematical formulation.
- Cover finance concepts explicitly — trading calendars, adjusted close, survivorship bias, lookahead bias, cross-sectional vs time-series — even when they feel "obvious." The user is learning quant for the first time.
- Do not repeat something already covered in a prior Methodology note. Link to it instead: `see [[01 - Data Collection]]`.
- If a repetition is genuinely useful (e.g., re-stating the leakage rule because it's about to be violated), mark it as a reminder: "**Reminder:** …".
- Tables save words. Prefer a small table to three paragraphs of prose when the content is comparative.
- Structure every note the same way: **Question → Prerequisites → Methodology (concept by concept) → Environment → Run guide → Expected outcome → What this task does NOT do → What comes next → Related notes.**
