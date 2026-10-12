# Task 07 — Graph Explanation (Time-Series Momentum)

**Previous:** [[Task 06 - Graph Explanation]] · **Index:** [[_Graph Explanations - README]] · **Method & full results:** [[07 - Time-Series Momentum]]
**Code:** `scripts/07_tsmom.py` · **Pictures:** `Figures/07/` · all three graphs use the primary horizon h = 21 days, out of sample (2022-08 → 2026-09).

Only 3 graphs. Each one answers a single question.

---

## G1 — Does it make money? (equity curves, net of costs)

![[07_ts_g1_equity.png]]

- 🧠 **Idea.** $1 invested in each strategy, after trading costs. Every line uses the same dates and the same risk sizing, so they are directly comparable.
- 👀 **How to read.** The y-axis is a log scale, so equal vertical distances mean equal % moves. The Sharpe ratio is in the legend.
- 🔎 **What it shows.** The **model (blue)** and the **trend rule (orange)** drift sideways and slightly down: net Sharpe −0.10 and −0.26. **Long-only (grey)**, which simply holds everything with inverse-vol sizing, climbs steadily (Sharpe 1.50). SPY grows the most in dollars but with bigger drops (Sharpe 1.21).
- 💡 **So what.** Predicting the direction added nothing. All the return came from being long assets that rose from 2022 to 2026.
- ⚠️ **Trap.** Don't read "long_only beats SPY" as skill. Long-only is diversified beta: spreading risk evenly across 20 assets lowers volatility.
- ✅ **Takeaway.** In this window, simply holding the assets beat trying to time them.

## G2 — Where does it predict? (per-asset OOS IC)

![[07_ts_g2_per_asset_ic.png]]

- 🧠 **Idea.** For each asset, the correlation between what the model predicted and what actually happened next month. Bar colour = asset class.
- 👀 **How to read.** Bars to the right are good (the predictions pointed the right way). Bars to the left mean the asset did the opposite of its trend.
- 🔎 **What it shows.** Most bars point left. The strongest negatives are energy and big tech (CVX, AAPL, XOM at −0.2 to −0.3): these names **mean-reverted** instead of trending. Only SHY, SOL, GLD, MSTR and NVDA are slightly positive.
- 💡 **So what.** No asset class is a clean pocket of trend. Even the "best" bars are small.
- ⚠️ **Trap.** Each asset has only about 48 independent 21-day periods, so one bar's noise band is roughly ±0.28. Almost every bar is inside that band. Don't hand-pick the positive assets: that would be fitting the test set.
- ✅ **Takeaway.** The failure is broad-based, not caused by one bad asset class.

## G3 — Did the training pattern survive? (in-sample vs OOS IC per refit)

![[07_ts_g3_ic_by_fold.png]]

- 🧠 **Idea.** At each monthly refit, the **black line** shows how well the model fit its training data. The **bars** show how well it predicted the next 21 days it had never seen.
- 👀 **How to read.** If the model had real skill, the bars would sit mostly above zero, near the black line.
- 🔎 **What it shows.** The black line is always positive (0.05–0.18), so in training "trend continues" always looked true. The bars swing randomly between −0.5 and +0.45, more red than blue, and average **−0.05**. There is a run of positive blocks in mid-2025 to early 2026, followed by negative ones.
- 💡 **So what.** This is overfitting in its purest form: a consistent in-sample relationship with no out-of-sample follow-through. It happened even with only 4 features.
- ⚠️ **Trap.** One block contains only about 20 independent labels (20 assets × 1 overlapping month), so a single ±0.4 bar is noise. Look at the average and the overall balance, not at individual bars.
- ✅ **Takeaway.** The training-set IC can't be trusted. Only the OOS bars count, and they average out to about zero.

---

**Bottom line:** see [[07 - Time-Series Momentum#6. Verdict — honest]]. There is no predictive edge in 2022–26, and the sample is too short to settle the question. Recommended next step: a longer history.
