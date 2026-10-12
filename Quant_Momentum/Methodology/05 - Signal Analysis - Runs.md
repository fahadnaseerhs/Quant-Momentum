# 05 — Signal Analysis · Runs Log

Terse, timestamped log of every execution of `scripts/05_signal_analysis.py`.
For the full written analysis of a run, see §13 of [[05 - Signal Analysis]].

Related raw artefacts (overwritten on every run):
- `reports/tables/05_run_log.txt` — plain-text log of the latest run
- `reports/tables/05_ic_summary.csv` — the full 182-row grid
- `reports/tables/05_bucket_returns.csv` — quintile + tercile
- `reports/tables/05_block_ic.csv` — per asset-class block
- `reports/tables/05_rolling_ic.csv` — 252-day rolling, hero features
- `reports/tables/05_shift_test.csv` — leakage sanity check
- `reports/figures/05_g1..g7_*.png` (mirrored into [[Figures/05]])

---

## Run · 2026-10-04 19:06

**Input:** `data/features/features.parquet` — shape `(28780, 17)`, 20 tradeables + SPY, 2021-01-04 → 2026-09-25.

**Headline (whole universe, sorted by |NW t-stat|):**

| Feature         | Horizon    | Mean IC  | NW t | Hit rate | Q5 − Q1   | N days |
|---              |---         |---:      |---:  |---:      |---:       |---:    |
| vol_ratio_20d   | fwd_ret_3d | +0.02629 | **+2.38** | 53.14 % | +0.665 % | 1,417 |
| vol_ratio_20d   | fwd_ret_1d | +0.01278 | +1.66 | 50.46 % | +0.285 %  | 1,419 |
| mom_21d         | fwd_ret_1d | +0.01454 | +1.57 | 51.38 % | +0.335 %  | 1,417 |
| relret_21d      | fwd_ret_1d | +0.01443 | +1.56 | 51.38 % | +0.334 %  | 1,417 |
| mom_21d         | fwd_ret_3d | +0.02008 | +1.41 | 51.66 % | +0.881 %  | 1,415 |
| relret_21d      | fwd_ret_3d | +0.01999 | +1.40 | 51.59 % | +0.883 %  | 1,415 |
| vsmom_5d        | fwd_ret_3d | −0.00790 | −0.62 | 49.23 % | +0.192 %  | 1,371 |
| relret_63d      | fwd_ret_3d | +0.00976 | +0.60 | 49.75 % | +0.393 %  | 1,373 |
| mom_63d         | fwd_ret_3d | +0.00974 | +0.60 | 49.75 % | +0.404 %  | 1,373 |
| vsmom_10d       | fwd_ret_1d | −0.00506 | −0.58 | 49.02 % | +0.116 %  | 1,373 |

Of 182 (universe × feature × horizon) tests, **5 reach |t| > 1.5** and only **1 reaches |t| > 2**. Expected false-positive count at the 5% level ≈ 9, so the vol_ratio_20d → 3-day result is the single survivor worth watching; everything with |t| < 1.5 is noise.

**Block IC (hero features, 1-day target):**

| Universe     | n | mom_21d   | vsmom_21d  | relret_21d |
|---           |-: |---:       |---:        |---:        |
| whole        | 20 | +0.01454 | +0.00278   | +0.01443   |
| **crypto**   | 5  | **+0.01732** | +0.01602 | +0.01670 |
| tech         | 5  | −0.01059 | −0.01332   | −0.01059   |
| gold         | 2  | NaN      | NaN        | NaN        |
| oil          | 3  | −0.00423 | −0.00036   | −0.00423   |
| real_assets  | 3  | +0.00353 | +0.02231   | +0.00353   |
| bonds        | 2  | NaN      | NaN        | NaN        |

→ Crypto is the only block with internally-consistent positive momentum. Tech reverses.

**Leakage shift test (hero features):**

| Feature     | Horizon      | Baseline | Future leak (−1) | Past-only (+5) |
|---          |---           |---:      |---:              |---:            |
| mom_21d     | fwd_ret_1d   | +0.0145  | **+0.1736**      | −0.0005        |
| mom_21d     | fwd_ret_3d   | +0.0201  | +0.1171          | +0.0020        |
| vsmom_21d   | fwd_ret_1d   | +0.0028  | +0.1634          | +0.0045        |
| vsmom_21d   | fwd_ret_3d   | +0.0071  | +0.1025          | +0.0128        |
| relret_21d  | fwd_ret_1d   | +0.0144  | +0.1736          | −0.0005        |
| relret_21d  | fwd_ret_3d   | +0.0200  | +0.1170          | +0.0020        |

→ Future-leak IC jumps ~10× above baseline; past-only collapses to ~0. Baseline alignment is clean.

**Quintile returns (whole universe, 1-day horizon, in %):**

| Feature       | Q1     | Q2     | Q3     | Q4     | Q5     | Q5 − Q1 |
|---            |---:    |---:    |---:    |---:    |---:    |---:     |
| mom_21d       | +0.016 | +0.075 | +0.048 | +0.121 | +0.351 | +0.335  |
| vol_ratio_20d | +0.002 | +0.055 | +0.114 | +0.171 | +0.287 | +0.285  |
| vsmom_21d     | +0.046 | +0.062 | +0.058 | +0.091 | +0.277 | +0.231  |

**Decisions from this run:**
1. Carry **mom_21d → 1-day** and **vol_ratio_20d → 3-day** forward as the two Task-06 baselines.
2. Drop vol-scaled momentum from the default feature set (consistently weaker than raw mom in this sample).
3. Keep both horizons (1d and 3d) through Task 06 and let the backtest decide.
4. Flag the within-tech reversal — any model that applies momentum globally will fight it.

**Figures (click to open):**
- [[Figures/05/05_g1_scatter_mom21d_vs_fwd1d.png]]
- [[Figures/05/05_g2_ic_timeseries.png]]
- [[Figures/05/05_g3_cumulative_ic.png]]
- [[Figures/05/05_g4_bucket_bar.png]]
- [[Figures/05/05_g5_ic_heatmap.png]]
- [[Figures/05/05_g6_block_ic.png]]
- [[Figures/05/05_g7_rolling_ic_regime.png]]

---

**Related:** [[05 - Signal Analysis]] (methodology + full written interpretation), [[04 - Feature Engineering]], [[03 - Exploring Returns]].
