# Graph Explanations — README

One note per task. Written for **understanding from zero**: every graph starts with the concept in plain words (with an everyday analogy), then walks you through reading the picture step by step, what it shows, why the project cares, and the common misreading. Every note embeds the actual picture.

**Tip:** Task 05 opens with six short concepts (IC, t-stat, quintiles, hit rate, multiple testing, the hero features). Read those first and the rest of the project's results make sense.

| Task | Note | Graphs | Source of pictures |
|---|---|---|---|
| 02 — Data Cleaning | [[Task 02 - Graph Explanation]] | 2 | `Figures/02/` (new; built by `scripts/02_cleaning_figures.py`) |
| 03 — Exploring Returns | [[Task 03 - Graph Explanation]] | 6 graph families, 16 pictures | `Figures/03/` |
| 04 — Feature Engineering | [[Task 04 - Graph Explanation]] | 8 graphs, 10 pictures | `Figures/04/` |
| 05 — Signal Analysis | [[Task 05 - Graph Explanation]] | 7 graphs | `Figures/05/` |
| 06 — Baseline Strategies | [[Task 06 - Graph Explanation]] | 3 graphs + scoreboard table + 4 extra checks | `Figures/06/` |
| 07 — Time-Series Momentum | [[Task 07 - Graph Explanation]] | 3 graphs | `Figures/07/` (copied automatically by `scripts/07_tsmom.py`) |
| 07b — Volatility Forecasting | [[Task 07b - Graph Explanation]] | 3 graphs | `Figures/07b/` (copied automatically) |
| 07c — Long-History Re-test | [[Task 07c - Graph Explanation]] | 3 graphs (of 6 generated) | `Figures/07c/` (copied automatically) |
| 10 & 11 — Costs, Combined Book, Robustness | [[Task 10 and 11 - Graph Explanation]] | 3 graphs | `Figures/10/`, `Figures/11/` (copied automatically) |

**Related:** [[Graph and Table Labels]] (dictionary of every axis, label and table column) · [[Glossary A-Z]] · [[_Methodology - README]] (the full write-up of each task)

---

## Suggested reading order

1. **Task 02** — why all data lives on one trading calendar, and why volatility differs 60× between assets.
2. **Task 03** — how returns behave: waves of volatility, fat tails, blocks of correlated assets, no own-return predictability.
3. **Task 04** — how those findings shaped the features (volatility scaling, winsorisation) and what the features look like.
4. **Task 05** — the first real test: does any feature rank tomorrow's winners? (The Information Coefficient is explained at the top of that note.)

---

## Notes about the pictures themselves

Things that are easy to misread, collected here so they're not lost:

| Where | What | Meaning |
|---|---|---|
| Task 04 pictures | Flat tops/bottoms and tall single bars at the extremes | **Winsorisation caps** (1st/99th percentile, pooled across all dates), not real data |
| Task 04, `04_g2` vs `04_g3` momentum files | Identical pictures | Older/newer export of the same chart |
| Task 04, `04_g3_vsmom_before_after.png` | Crypto and tech box colours swapped | Cosmetic palette-order bug; axis labels are correct |
| Task 05, G7 | Grey "bear" shading nearly invisible; the visible part (first half of 2021) is the 126-day moving average's warm-up, not a real bear market | Don't read regime conclusions from the shading |
| Task 05, G2/G3/G7 | Orange line hidden under blue | `relret_21d` ranks assets identically to `mom_21d` (subtracting SPY is a constant per day) |
| Task 03, 63-day windows | Sudden cliff ~3 months after a spike | The shock leaves the window ("ghost"), not a market event |

**Where figures live:** `reports/figures/` is the working folder written by the scripts. Obsidian can only embed images inside the vault, so copies are kept in `Quant_Momentum/Figures/02…05/`. After re-running a script, copy the new PNGs across.
