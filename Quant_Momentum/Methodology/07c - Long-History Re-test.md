# 07c — Long-History Re-test (2004 → 2026)

**Re-tests:** [[07 - Time-Series Momentum]] and [[07b - Volatility Forecasting]] with the same code and the same pre-committed settings, on about 4× more data.
**Code:** `scripts/07c_fetch_long.py` (download + clean) · `scripts/07_tsmom.py --long` · `scripts/07b_vol_forecast.py --long`
**Graphs:** [[Task 07c - Graph Explanation]] · **Status:** [[Task Log]]

---

## 1. Why

On 2021–26, neither trend model showed an edge, but that window gave only about 4 OOS years. A genuine trend strategy (Sharpe ~0.7) needs roughly 8–10 years to show up statistically (t ≈ SR·√T). Re-testing on 20+ years answers "no edge" vs "edge too small to see".

## 2. Data

- **Same 20 assets + SPY, same cleaning rules** (SPY calendar, forward-fill ≤ 2 days, no backfill). Saved to `data/long/`; the 2021–26 data is untouched.
- **2004-01-02 → 2026-10-09**, 5,729 trading days. Assets join when they list: 12 in 2005, 15 by 2012 (META), 16 from 2014 (BTC), 18 from 2017 (ETH, LINK), 20 from 2020 (SOL, AVAX).
- **OOS ≈ 2005-08 → 2026-10, about 21 years**, including 2008, 2020 and 2022.
- Code change: position size now divides by the number of assets *available that day*. Re-running 2021–26 reproduced every earlier number exactly.

> ⚠️ **Selection bias.** The universe was picked in 2026, with hindsight: NVDA, MSTR, BTC and SOL are known winners. That heavily flatters **long-only** and **1/N** (1/N turns $1 into ~$90). Trend IC is less affected, but crypto's big trending bull runs still help it.

## 3. Trend (time-series momentum) — results

### 3.1 Prediction

| h | signal | IC in-sample | **IC OOS** | IC non-overlap (t) | hit rate | always-long hit |
|---|---|---|---|---|---|---|
| 21 | model | 0.050 | **0.052** | 0.045 (2.90) | 52.9% | 57.5% |
| 21 | rule | — | 0.057 | 0.039 (2.49) | 52.8% | 57.5% |
| 5 | model | 0.038 | 0.028 | 0.026 (3.40) | 51.7% | 54.5% |
| 5 | rule | — | 0.034 | 0.030 (3.97) | 51.8% | 54.5% |

- **The OOS IC equals the in-sample IC (0.052 vs 0.050), so there's no overfit gap.** On 4 years the gap looked like overfitting. On 21 years it's clear that 2022–26 was just a weak period.
- **The t-stats above are too generous.** Assets move together on the same day, so the rows aren't fully independent. The cleaner test is the portfolio's own Sharpe over 21 years: gross 0.73 gives **t ≈ 3.3**, and net 0.41 gives **t ≈ 1.9**.
- **The fitted model ≈ the simple rule.** Fitting adds almost nothing.
- **The signal lives in big regimes, not month to month.** The per-month test IC averages about 0, while the pooled IC is +0.05 (see G3, which is in the figures folder but not in the graph note). The signal comes from long trends like 2008, 2014, 2017, 2020 and 2022.

### 3.2 Portfolio (net of 10 bps, h = 21)

| | Sharpe gross | **Sharpe net** | ann. return | ann. vol | max DD |
|---|---|---|---|---|---|
| model | 0.73 | **0.41** | 2.9% | 7.1% | −17.4% |
| rule | 0.71 | 0.32 | 2.3% | 7.2% | −20.3% |
| long-only (inverse vol) | 1.24 | 1.20 | 11.5% | 9.6% | −19.7% |
| SPY | 0.69 | 0.69 | 13.1% | 19.1% | −55.2% |

**Costs eat about 45%** of the trend return. Turnover is 0.087 per day, which costs about 2.2% a year at 10 bps.

### 3.3 When trend works (by year, IC and return)

| | 2008 | 2014 | 2017 | 2020 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|---|
| IC model | +0.07 | +0.19 | +0.19 | +0.17 | +0.08 | −0.08 | −0.11 |
| model return | −4.2% | +10.3% | +11.6% | +19.3% | +2.5% | +1.0% | −2.3% |
| long-only return | −13.0% | +3.1% | +18.5% | +16.3% | −12.9% | +26.4% | +19.5% |
| SPY return | −34.3% | +14.5% | +21.6% | +15.6% | −19.0% | +26.0% | +25.3% |

Trend helps in big directional years and in sell-offs, and lags in steady bull markets (2023–24). Task 07's window fell mostly in the bad part.

### 3.4 Where trend works (per asset, OOS IC)

- **Positive:** SHY (+0.23), SOL, BTC, ETH, NVDA, DBC, GLD, MSTR and USO (+0.06 to +0.16). These are mostly macro assets (bonds, commodities) and crypto.
- **Negative:** single big-tech and energy stocks (CVX −0.10, GOOGL, MSFT, AAPL, META) and VNQ.
- This matches the literature: trend is strongest in macro and futures-like assets, while single stocks mean-revert more.

### 3.5 Trend as a diversifier (exploratory, not pre-committed)

The correlation of daily trend returns with the long-only book is **0.19**.

| period | trend | long-only |
|---|---|---|
| 2008-01 → 2009-03 | −7.8% | −14.0% |
| 2020 Feb–Mar crash | −0.2% | −12.8% |
| 2022 | +2.5% | −12.9% |

| mix (long + trend) | Sharpe | max DD | ann. return |
|---|---|---|---|
| 100% long | 1.20 | −19.7% | 11.5% |
| **75 / 25** | **1.20** | **−15.4%** | 9.3% |
| 50 / 50 | 1.10 | −12.2% | 7.1% |

Trend is a **shock absorber**: the same Sharpe with about a quarter less drawdown. It is not a profit engine on its own.

## 4. Volatility forecasting — results

| | QLIKE | vs EWMA | within-asset R² (log) | DM t |
|---|---|---|---|---|
| EWMA | 0.333 | — | 0.360 | — |
| HAR | 0.317 | −4.8% | 0.387 | 2.14 |
| HAR-L | 0.315 | −5.3% | 0.391 | 2.85 |

- **Over 21 years volatility is very predictable** (R² ≈ 0.36–0.39, compared with ≈ 0 on 2021–26), because vol regimes swing much more in a long history.
- **HAR wins on average but loses in crises**: 2008 (−5.9%), 2009 (−8.2%) and 2020 (−13.1%). It is slower to react to sudden spikes, and leaving out the leverage term makes that worse.
- **Portfolio:** EWMA-sized Sharpe 1.25 vs HAR-sized 1.22. EWMA is slightly better because crises are exactly when sizing matters most.
- **Vol-sizing vs 1/N:** about the same Sharpe (1.23–1.25), but max drawdown is **−20% vs −43%**.

## 5. Verdict

1. **Trend is real but small.** IC ≈ 0.05, net Sharpe 0.41 (t ≈ 1.9; t ≈ 3.3 before costs). The 2021–26 "no edge" was a weak period, not a dead signal. **You need long history to see it.**
2. **Fitting a model adds little over the simple rule.** The edge is in the *idea* (follow trends, size by risk), not in the regression.
3. **Costs are the main thing holding trend back** (about 2.2% a year against about 5% gross). Lowering turnover is the cheapest improvement.
4. **The best use of trend is as a diversifier**: 25% trend gives the same Sharpe with −15% instead of −20% max drawdown.
5. **Volatility:** keep **EWMA** (or HAR-L) for sizing. HAR is more accurate on average but slower in crashes.
6. **The most valuable piece overall is vol-sizing**: it halves drawdowns compared with 1/N.

## 6. Recommended next steps

| # | Step | Why |
|---|---|---|
| 1 | **Cut trend turnover** (Task 10): rebalance weekly or monthly, or trade only when the signal changes enough | Recovers part of the ~2.2% a year in costs. Biggest lever on net Sharpe. |
| 2 | **Pre-commit a combined book**: inverse-vol long core + trend overlay | Turns the exploratory 75/25 result into a proper test. |
| 3 | Robustness (Task 11): cost sensitivity, sub-periods, universe **without hindsight winners** | Measures how much selection bias flatters the results. |
| 4 | Task 08 (boosted trees): optional | There is now a real signal, but model ≈ rule suggests little non-linear structure to find. |
