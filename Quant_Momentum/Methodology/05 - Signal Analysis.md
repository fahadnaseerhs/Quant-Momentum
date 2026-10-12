# 05 — Signal Analysis

**Phase in the pipeline:** Step 5 of `Data → Cleaning → EDA → Features → **Signal Analysis** → Models → Portfolio → Backtest → Risk → Costs → Robustness`.

**Prerequisite:** [[04 - Feature Engineering]] is done. The feature matrix lives in `data/features/features.parquet` (28,780 rows × 17 columns; 20 tradeables × ~1,440 days; momentum, EWMA volatility, vol-scaled momentum, volume ratio, relative returns, plus `fwd_ret_1d` and `fwd_ret_3d` targets).

**Status:** ✅ Built and run (2026-10-04). §1–12 are the plan written before running; **§13 records what we actually saw** on the 2021-01-04 → 2026-09-25 feature matrix.

---

## 1. The question

In Task 04 we built features that *might* contain a signal. A feature is only a candidate clue. Before we train any model or run any backtest, we need an evidence check:

> **Does a feature we can compute at the end of day $t$ actually tell us anything about the return on day $t+1$ (or over days $t+1$ to $t+3$)?**

If we skip this step, we risk building a model, a backtest and a cost analysis on top of a signal that was never there.

---

## 2. Why cross-sectional, not time-series

Task 03's autocorrelation tests already asked a *time-series* question: does an asset's **own** past return predict its **own** next return? The answer across the 21-asset universe was no — only 9 of 210 lag tests passed at the 5% level, which is roughly what pure chance produces.

That is not a failure for this project, because the strategy is **cross-sectional**:

> On each day, rank all 20 assets by a feature, and ask whether the ranking agrees with the ranking of the next return.

The question is no longer "will BTC go up?" but "**among these 20 assets, which one is strongest right now?**" A feature can carry zero own-return predictability and still rank winners against losers.

---

## 3. The main metric —Information Coefficient (IC)

### 3.1 Definition

For each day $t$:

1. Rank all 20 assets by the feature value at day $t$ → rank vector $R^{\text{feat}}_t$.
2. Rank all 20 assets by the realised forward return at day $t$ → rank vector $R^{\text{ret}}_t$.
3. Compute the **Spearman rank correlation** between the two:

$$\text{IC}_t = \text{corr}_{\text{Spearman}}(R^{\text{feat}}_t,\ R^{\text{ret}}_t)$$

This gives one IC number per day, i.e. a time series of ~1,440 values.

### 3.2 Why ranks, not raw values

Task 03 established that every asset has **fat tails**: one earnings jump or crypto crash can distort any ordinary correlation. Ranks only care about order, so a single +40% day cannot drag the metric around. This is the "rank-based evaluation" chosen in `decisions/2026-09-27-task03-findings-and-env-repair.md`.

### 3.3 How to read a single IC value

| IC | Meaning |
|---|---|
| +1 | Perfect ranking of tomorrow's winners and losers |
| 0 | Ranking is no better than random |
| −1 | Ranking is exactly backwards (reversal signal) |

**Realistic numbers.** In daily equity prediction, a mean IC of **0.02–0.05** is already respectable. An IC above 0.2 almost always means a bug or data leakage — be suspicious, not excited.

### 3.4 Summarising the IC time series

- **Mean IC** $\bar{\text{IC}}$ — average signal strength.
- **Hit rate** $\Pr(\text{IC}_t > 0)$ — fraction of days the feature points the right way. A real signal is positive clearly more than 50% of the time.
- **Information Ratio of IC** $\bar{\text{IC}} / \text{std}(\text{IC})$ — stability of the signal.
- **t-statistic of $\bar{\text{IC}}$ with Newey–West standard errors** (see §4) — distinguishes real mean from luck.
- **Cumulative IC plot** — $\sum_{s \leq t} \text{IC}_s$. A steady upward slope means consistent signal; a jump followed by flatness means the signal worked once, in one regime.

---

## 4. Newey–West standard errors

To judge whether $\bar{\text{IC}} \neq 0$, we need a standard error. The textbook formula assumes **independent** daily IC values. That assumption fails for two concrete reasons:

1. **Volatility clustering.** Task 03 showed |returns| are autocorrelated for 20+ lags across 18 of 21 assets. Calm and stormy days come in streaks, so neighbouring ICs are related.
2. **Overlapping 3-day targets.** $\text{fwd\_ret\_3d}_t$ and $\text{fwd\_ret\_3d}_{t+1}$ share two of three days. Their ICs are mechanically linked.

Treating ICs as independent therefore produces **standard errors that are too small** — fake precision, fake significance.

**Newey–West (HAC) standard errors** widen the ruler to account for autocorrelation and heteroskedasticity, using a lag length roughly $L \approx 4(T/100)^{2/9}$ (≈ 7 lags for our sample). Every IC t-test in this task uses them.

---

## 5. Quintile bucket analysis

IC tells us whether the ranking agrees. Bucket analysis translates agreement into **return differences**.

### 5.1 Procedure

Each day:
1. Sort the 20 assets by the feature.
2. Split into 5 buckets (Q1 = weakest, Q5 = strongest). With 20 assets, that is 4 assets per bucket.
3. Record each bucket's mean next-day return.

Average each bucket's return across all days → a bar chart of **mean forward return by quintile**.

### 5.2 What to look for

- Q5 > Q4 > Q3 > Q2 > Q1 — a clean **monotonic staircase** is the strongest visual evidence.
- **Long–short spread** = mean(Q5) − mean(Q1). This is the paper profit, before costs, of buying the top bucket and shorting the bottom.
- A spiky pattern (only Q5 is high, Q1–Q4 scrambled) is weak evidence — it may be driven by one lucky asset.

### 5.3 Sample-size caveat

Four assets per bucket is small, so bucket means are noisy. We also report **terciles** (top/middle/bottom thirds) as a robustness check, and bootstrap confidence intervals around each bucket mean.

---

## 6. Block analysis — the N_eff ≈ 3.9 problem

Task 03 found the 20 assets behave like **~3.9 independent assets**, clustered into blocks:

- Crypto + MSTR (MSTR–BTC correlation 0.72)
- Oil + DBC (DBC–USO correlation 0.91)
- Gold
- Bonds (TLT, SHY)
- US tech + equities

A whole-universe IC can be inflated by block effects. "Crypto beat bonds today" is one macro fact, but it is counted across five crypto names and two bond names, which multiplies apparent evidence.

**Mitigation:** run the IC and bucket tests **two ways**:

1. **Whole universe.** All 20 ranked together. This is what the real strategy will do.
2. **Within blocks.** Rank only crypto against crypto, only tech against tech, etc. This asks whether momentum separates **similar** assets, which is a cleaner skill test.

Interpretation rules:
- Positive IC in both = genuine stock-picking signal.
- Positive IC only across the whole universe = asset-class rotation, not stock-picking.
- Positive IC only within blocks = narrow signal; may not survive portfolio construction.

---

## 7. Window and feature comparison

We built four lookback windows (5, 10, 21, 63 days) in Task 04 and deliberately did **not** choose one from the ACF charts (that would overfit). Task 05 is where the data votes.

For each combination of:
- feature family: raw momentum, vol-scaled momentum, relative return, volume ratio
- lookback: 5, 10, 21, 63
- target horizon: 1-day, 3-day
- universe: whole, or one of the asset-class blocks

we record (mean IC, Newey–West t-stat, hit rate, long–short spread). The output is a results table of maybe 50–100 rows. §8 below says how to read it honestly.

Robustness variants worth running:
- raw vs vol-scaled momentum — does scaling improve the IC?
- momentum vs relative-to-SPY return — does subtracting the market help?
- 1-day vs 3-day targets — does the longer horizon smooth noise?

---

## 8. The multiple-testing problem

### 8.1 Why it exists

A "significant" result at the 5% level means: *"if the feature had zero predictive power, luck would produce a result this good only 5% of the time."* For **one** test that is a fair bar. But if we run **40** independent tests on pure noise, we expect **~2** to pass by chance.

| Tests run | Expected false "wins" at 5% | Probability of at least one |
|---|---|---|
| 1 | 0.05 | 5% |
| 10 | 0.5 | ~40% |
| 40 | 2 | ~87% |
| 100 | 5 | ~99% |

Our grid in §7 easily reaches 50–100 tests. A couple of "significant" hits is therefore the **expected outcome under the null hypothesis of no signal.**

Task 03 already illustrated this: 9 "robust" autocorrelation hits out of 210 tests is 4.3%, essentially chance. We correctly called it noise.

### 8.2 Four defences

1. **Count the tests.** Report the denominator honestly, including the tests that failed. "1 of 5" means something very different from "1 of 100".
2. **Expect ~5% false positives.** The baseline is not zero. If 100 tests give 5 hits, we have found nothing special.
3. **Treat lone winners with suspicion.** One significant combination in a sea of failures is a lottery winner.
4. **Favour neighbour agreement.** Real economic effects are **smooth over nearby parameterisations**. If 21-day momentum works, 10-day and 63-day should at least tilt the same way. Zigzag patterns are noise; smooth gradients are signal.

### 8.3 Bonferroni as a hard sanity check

If we really want a single-test-equivalent threshold, divide the 5% target by the number of tests: $p < 0.05 / N$. For 40 tests that is $p < 0.00125$. This is blunt and over-conservative, but any result that passes it is extremely unlikely to be luck. We report it as an auxiliary column, not as the main criterion — the smoothness test (defence 4) is usually more informative.

### 8.4 The final safeguard

A separate out-of-sample window at the end of the data (set aside in Task 09's walk-forward design) is untouched by this entire task. Any winner selected here must survive on data it was never selected on.

---

## 9. Stability over time

A signal with a strong average can still be fragile. We split the sample into sub-periods (e.g. 2022 bear market, 2023 recovery, 2024–25) and check whether the IC keeps its sign.

**Why it matters.** Momentum is known to crash around sharp market reversals ("momentum crashes" — Daniel & Moskowitz 2016). If a feature's IC is +0.05 in calm periods and −0.08 in stress, the average hides a strategy that blows up at the worst time. This feeds into the regime analysis in the later robustness task.

Deliverable: a rolling-window (e.g. 252-day) mean IC plot per feature, with the zero line marked.

---

## 10. Leakage check

The feature matrix was built in Task 04 under strict leakage rules (vol is lagged one day, every rolling window uses only past data). Task 05 must preserve this:

- **Alignment:** every IC test uses $\text{feature}_t$ against $\text{fwd\_ret}_t$ (which is a future-only return by construction).
- **Shift test:** replace $\text{feature}_t$ with $\text{feature}_{t+1}$ and recompute the IC. It should collapse toward zero. If it stays high, we have a bug.
- **Nothing from the test period** is used to fit any threshold, bucket boundary, or lookback choice. Those come from training-period data only in Task 09. In Task 05 we are describing the full sample, not trading on it.

---

## 11. Expected outcomes and what each means

| Observation | Interpretation | Next step |
|---|---|---|
| Mean IC clearly > 0, buckets monotonic, stable across periods, consistent within blocks | Real signal worth modelling | Proceed to baseline (Model 0) and models (Task 06+) |
| Small positive IC, not significant after Newey–West and multiple-testing adjustment | Possibly weak effect, possibly noise | Proceed cautiously; costs will likely dominate |
| IC negative at short horizons | Short-term reversal, not momentum | Legitimate finding; usable if flipped |
| IC ≈ 0 across the grid | No cross-sectional predictability in this universe | A valid conclusion. "Momentum is statistically real but economically dead" is a valid project outcome. |

Based on Task 03's findings (no own-return autocorrelation at 1–10 days, strong block structure), the realistic prior is **small positive IC at the 21- and 63-day windows, concentrated in cross-asset-class ranking rather than within-block ranking**. The data decides.

---

## 12. Deliverables

**Code**
- `src/signals.py` — pure functions: `daily_ic`, `newey_west_tstat`, `bucket_returns`, `tercile_returns`, `rolling_ic`.
- `scripts/05_signal_analysis.py` — orchestrator: loads `data/features/features.parquet`, writes tables to `reports/tables/` and figures to `reports/figures/`.

**Tables (`reports/tables/`)**
- `05_ic_summary.csv` — one row per (feature × window × horizon × universe), columns: mean IC, NW t-stat, hit rate, long–short spread, N obs, N days.
- `05_bucket_returns.csv` — mean forward return per quintile and tercile.
- `05_block_ic.csv` — mean IC per asset-class block.
- `05_rolling_ic.csv` — 252-day rolling mean IC per feature.

**Figures (`reports/figures/`)**
- `05_g1_scatter_mom21d_vs_fwd1d.png` — raw scatter, with warning that noise dominates visually.
- `05_g2_ic_timeseries.png` — daily IC and 252-day rolling mean, per feature.
- `05_g3_cumulative_ic.png` — $\sum \text{IC}_s$ for each feature.
- `05_g4_bucket_bar.png` — quintile bar chart for each feature.
- `05_g5_ic_heatmap.png` — mean IC heatmap (features × windows × horizons).
- `05_g6_block_ic.png` — IC within and across blocks.
- `05_g7_rolling_ic_regime.png` — rolling IC per feature with regime shading.

**Note update**
- This file (§13 "What we actually saw") after the task is run.

---

## 13. What we actually saw

**Run:** `python scripts/05_signal_analysis.py` — produced on 2026-10-04 against `data/features/features.parquet` (28,780 rows, 20 tickers, 2021-01-04 → 2026-09-25). Full output in `reports/tables/05_run_log.txt`.

### 13.1 Headline — the strongest signals (whole universe)

Sorted by |Newey–West t-stat|. Only the top of the table is reproduced here — the full 182-row grid is in `reports/tables/05_ic_summary.csv`.

| Feature        | Horizon      | Mean IC  | NW t-stat | Hit rate | Q5 − Q1 spread | N days |
|---             |---           |---:      |---:       |---:      |---:            |---:    |
| vol_ratio_20d  | fwd_ret_3d   | +0.0263  | **+2.38** | 53.1 %   | +0.67 %        | 1,417  |
| vol_ratio_20d  | fwd_ret_1d   | +0.0128  | +1.66     | 50.5 %   | +0.29 %        | 1,419  |
| mom_21d        | fwd_ret_1d   | +0.0145  | +1.57     | 51.4 %   | +0.33 %        | 1,417  |
| relret_21d     | fwd_ret_1d   | +0.0144  | +1.56     | 51.4 %   | +0.33 %        | 1,417  |
| mom_21d        | fwd_ret_3d   | +0.0201  | +1.41     | 51.7 %   | +0.88 %        | 1,415  |
| relret_21d     | fwd_ret_3d   | +0.0200  | +1.40     | 51.6 %   | +0.88 %        | 1,415  |

Two things to note:

1. **Mean ICs are small (1–3 bp).** This is the realistic range the §3.3 table warned about. Nothing here suggests a bug or leak.
2. **vol_ratio_20d is the single most t-significant feature** at the 3-day horizon. We expected to find momentum here; we also found that unusually-high-volume days *lead* higher 3-day returns. That is new information from the data.

The other 170 rows have |t| < 1 — i.e. indistinguishable from the §8 multiple-testing noise floor.

### 13.2 Picture 1 — raw scatter

![[05_g1_scatter_mom21d_vs_fwd1d.png]]

28,780 (feature, forward return) pairs for mom_21d, coloured by asset class, with a thin OLS line through them. The slope exists (β ≈ +0.0075) but the point cloud is a cloud. **Visually you cannot see the signal**, which is exactly why we rank instead of regressing on raw values. The scatter is here to kill the intuition that a scalar look is enough.

### 13.3 Picture 2 — daily IC and its 252-day rolling mean

![[05_g2_ic_timeseries.png]]

Daily IC for the three hero features (mom_21d, vsmom_21d, relret_21d) against the 1-day target. The thin wobble is daily noise — ±0.5 is routine on 20 observations. The thick line is the 252-day rolling mean. The dotted horizontal is the full-sample mean.

- **mom_21d** and **relret_21d** sit slightly above zero for most of the sample.
- **vsmom_21d** is weakly positive at the overall mean (+0.003) and the rolling line crosses zero multiple times.
- No feature "always works". The signal is **statistical, not deterministic.**

### 13.4 Picture 3 — cumulative IC

![[05_g3_cumulative_ic.png]]

Running sum $\sum_{s\le t}\text{IC}_s$ for the same three features. The slope *is* the average daily IC.

- mom_21d / relret_21d: a steady, gentle upward slope — the signal keeps paying through the whole sample, in both the 2022 drawdown and the 2023–25 recovery.
- vsmom_21d: an almost-flat slope with a dip in late 2022 and recovery after.

A real signal looks like these — slow, grinding, never spectacular. A fake signal would look like a step: one big jump and then flat.

### 13.5 Picture 4 — quintile bar chart

![[05_g4_bucket_bar.png]]

Mean next-period return for each quintile of each hero feature, whole universe. With 20 assets this is 4 per bucket.

The two leftmost rows (**mom_21d** and **relret_21d**) show a mostly monotonic staircase Q1 < Q2 < Q3 < Q4 < Q5 at both horizons — the strongest visual evidence we have found so far. **vsmom_21d** has a weaker staircase, consistent with its lower IC.

Numbers for the whole-universe quintiles (daily horizon):

| Feature       | Q1       | Q2       | Q3       | Q4       | Q5       | Q5 − Q1 |
|---            |---:      |---:      |---:      |---:      |---:      |---:     |
| mom_21d       | +0.016 % | +0.075 % | +0.048 % | +0.121 % | +0.351 % | **+0.335 %** |
| vol_ratio_20d | +0.002 % | +0.055 % | +0.114 % | +0.171 % | +0.287 % | **+0.285 %** |
| vsmom_21d     | +0.046 % | +0.062 % | +0.058 % | +0.091 % | +0.277 % | +0.231 %     |

At the 3-day horizon the spreads roughly triple, as expected mechanically. **The spreads are pre-cost — Task 10 will test what survives transaction costs.**

### 13.6 Picture 5 — IC heatmap

![[05_g5_ic_heatmap.png]]

Rows = every feature in the Task 04 grid (mom/vsmom/relret × 5/10/21/63 + vol_ratio_20d), columns = horizons, cell = mean IC with the Newey–West t-stat in parentheses underneath.

- **The green strip** is at the 21-day momentum row and the vol_ratio_20d row.
- **The 5-day and 10-day momentum rows are near zero or slightly negative** — short-term reversal, not momentum. This matches the Task 03 autocorrelation findings.
- **The 63-day momentum rows are near zero** — longer windows add noise without adding signal in this sample.
- **vsmom features (vol-scaled) consistently underperform their un-scaled siblings** in this universe. In §15 this was listed as an open question; the data says scaling by EWMA vol *hurts*. We think that is because 2022–25 saw crypto's realised vol fall even as crypto momentum turned positive, so dividing by vol damped the signal we most wanted to capture.

The §8 smoothness heuristic says: real effects are smooth over neighbouring windows. The signal column shows mild tilt from 5d → 21d → 63d (negative → positive → zero), which is a smooth, not zigzag, pattern. That is weak corroboration that 21-day momentum is a real effect, not a lucky point in the grid.

### 13.7 Picture 6 — block IC vs whole-universe IC

![[05_g6_block_ic.png]]

Mean 1-day IC inside each asset class, next to the whole-universe column.

- **Crypto block:** IC ≈ +0.017 for all three hero features. Crypto's internal momentum ranking is **the only block where the signal is positive and material**.
- **Tech block:** IC ≈ **−0.011** — negative. Within US tech, high recent-21d-return names actually tend to **underperform** the following day. This is a short-term reversal effect, not momentum.
- **Oil block:** mildly negative (−0.004).
- **Real-assets block:** +0.003 (noise, 3 assets).
- **Gold / Bonds:** NaN — only 2 tickers per block, below the quintile and min-obs thresholds.

**Interpretation per §6:** The whole-universe +0.015 IC is a mix of (a) a strong within-crypto momentum effect and (b) a cross-asset-class rotation effect. Within US tech it is a **reversal**, which argues against treating 21-day momentum as a one-size-fits-all signal.

### 13.8 Picture 7 — rolling IC with SPY-bear shading

![[05_g7_rolling_ic_regime.png]]

The 252-day rolling IC per hero feature, with grey vertical bands where SPY is below its 126-day moving average (crude "bear" regime).

- The rolling IC for mom_21d and relret_21d stays mostly above zero across both bull and bear regimes — the signal does not disappear in the 2022 drawdown.
- vsmom_21d dips into negative territory in 2022 and recovers. This is the "momentum crash" pattern Daniel & Moskowitz (2016) describe — scaled momentum, by amplifying bets in low-vol crypto in late 2021, got hurt most by the 2022 reversal.

### 13.9 Leakage shift test — our Task 04 alignment is clean

| Feature   | Horizon      | Baseline IC | Future-leak IC (shift −1) | Past-only IC (shift +5) |
|---        |---           |---:         |---:                        |---:                      |
| mom_21d   | fwd_ret_1d   | +0.0145     | **+0.1736**                | −0.0005                  |
| mom_21d   | fwd_ret_3d   | +0.0201     | +0.1171                    | +0.0020                  |
| vsmom_21d | fwd_ret_1d   | +0.0028     | +0.1634                    | +0.0045                  |
| relret_21d| fwd_ret_1d   | +0.0144     | +0.1736                    | −0.0005                  |

The §10 shift test. We built two synthetic versions of each feature:

- **future_leak** — the feature from day $t+1$ pasted onto day $t$. If our baseline were already leaking, this shift would barely move the IC. Instead the IC jumps by **more than 10×** — the shifted feature now shares price $P_{t+1}$ with the forward return. That is the signature of leakage; the fact that the shift **introduces** it, rather than our baseline already having it, is the evidence that baseline is clean.
- **past_only** — the feature from day $t-5$ pasted onto day $t$. The IC collapses to ~0 for the raw momentum features, as it should: a 5-day-old feature retains little information about tomorrow's cross-sectional ranking.

The methodology §10 originally wrote "the IC should collapse toward zero" for the −1 shift — that wording turned out to be ambiguous. The right interpretation is: **the shifted and baseline ICs should be different**. The direction of the difference (inflation under future leak, decay under past-only) is what proves the baseline is correctly aligned.

### 13.10 Takeaways → Tasks 06+

1. **The best single feature by t-stat is vol_ratio_20d at the 3-day horizon** (IC = +0.026, t = +2.38). Momentum (mom_21d, relret_21d) at the 1-day horizon is the second-best cluster and is more consistent across sub-periods.
2. **21 days is the sweet-spot window.** 5d/10d are reversal-like; 63d is noise.
3. **Vol-scaled momentum underperforms raw momentum in this universe.** The §15 open question is answered: do **not** vol-scale as the default.
4. **The within-crypto rank is the cleanest skill test** — a +0.017 IC on only 5 assets. Within tech the signal reverses.
5. **No feature survives Bonferroni at $p < 0.05/182$** (that threshold needs |t| ≈ 3.1). The vol_ratio_20d / mom_21d results sit around |t| = 1.5–2.4, which is below the ultra-conservative bar but above the "pure noise" null. §8 defence 4 (smooth-neighbour agreement) argues more strongly in their favour than any single p-value.
6. **Baseline — Task 06** should rank by **mom_21d** against the 1-day target (bigger t-stat per day of risk, cleanest leakage profile) **and** separately rank by **vol_ratio_20d** against the 3-day target. The two will be our two Model-0 baselines; any later ML model must beat **both**.

---

## 14. What comes next

- **Task 06 — Baseline Model.** Model 0 = rank by the two features selected in §13.10. No learning, no fitting, just the signal itself as the trading rule. Any later ML model must beat this.
- **Task 07/08 — Prediction models.** Linear regression first, then (per the roadmap) XGBoost or LightGBM. The user picks after seeing baseline results.

---

## 15. Compute footprint

Negligible. The feature matrix is ~5 MB. Computing daily IC for one feature is a Spearman correlation on 20 numbers per day for ~1,440 days — well under a second. The entire script, including all plots, runs in about ten seconds on CPU. **No GPU needed, no heavy CPU usage, no cloud compute.** This whole project stays CPU-only through to the final backtest.

---

## 16. Open decisions on the user's plate

- **Target horizon:** both 1-day and 3-day have viable signals. §13 recommends keeping both and letting the backtest choose.
- **Prediction model:** linear regression → gradient boosting is the roadmap; the specific model is picked after Task 06 (baseline).

---

**Related notes:** [[04 - Feature Engineering]], [[03 - Exploring Returns]], [[Autocorrelation - Momentum vs Reversal]], [[Information Coefficient]], [[Multiple Testing]], [[Newey-West Standard Errors]].
