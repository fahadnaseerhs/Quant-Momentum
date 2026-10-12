# 07b — Volatility Forecasting (predict risk, not returns)

**Follows:** [[07 - Time-Series Momentum]]. Return direction turned out to be unpredictable, so this note tests the thing that *is* predictable.
**Code:** `src/volforecast.py` · `scripts/07b_vol_forecast.py` · **Graphs:** [[Task 07b - Graph Explanation]] · **Status:** [[Task Log]]
**Concept:** [[Volatility Clustering]]: calm periods stay calm, and wild periods stay wild.

---

## 1. The question

> **"Can we forecast each asset's volatility over the next 21 days better than our current EWMA estimate, and does a better forecast improve the inverse-vol long book?"**

## 2. Method

**Label:** realised vol over the next 21 days, in logs:
$$\text{lrv\_fut}_{i,t} = \log\sqrt{\tfrac{1}{21}\textstyle\sum_{k=1}^{21} r_{i,t+k}^2}$$

**Forecasters:**

| Name | What | Fitted? |
|---|---|---|
| **EWMA** | $\sigma_t$, λ = 0.94: the sizing input used so far | no |
| **HAR** (main) | $\text{lrv\_fut} = b_0 + b_1\,\text{lrv}_5 + b_2\,\text{lrv}_{22} + b_3\,\text{lrv}_{63}$, where $\text{lrv}_k$ = log realised vol over the past $k$ days (week, month, quarter) | pooled OLS |
| **HAR-L** | HAR + leverage term $\min(\text{5-day return}, 0)/\sigma$, because falls raise vol | pooled OLS |

The HAR forecast is converted to vol units with $\hat\sigma = e^{\hat y + s^2/2}$, where $s^2$ is the training residual variance (the log-normal mean correction).

**Leakage-safe:** the same walk-forward as Task 07. Expanding window, 252 days of first training, monthly refit, 21-day embargo. OOS runs **2022-05 → 2026-08**. The design was fixed before the run.

**Scoring:**
- **QLIKE**, the standard volatility-forecast loss. Lower is better, and it is robust to noise in realised vol.
- **Within-asset R²**. This gives no credit for knowing SOL is riskier than SHY; it only counts predicting the *ups and downs over time*.
- A **Diebold–Mariano t-test**. Losses are averaged across assets per date, and only every 21st date is used so the labels don't overlap. That leaves 52 dates.

**Portfolio:** the same long-only rule as Task 07, $w_i = \min(20\%/\hat\sigma_i^{ann}, 1)/N$, rebalanced daily with 10 bps costs. Only the vol input changes.

## 3. Results

### 3.1 Forecast accuracy (OOS)

| | QLIKE | vs EWMA | within-asset R² (log) | DM t-stat |
|---|---|---|---|---|
| EWMA | 0.263 | — | −0.001 | — |
| **HAR** | **0.240** | **−8.7% loss** | 0.041 | **2.76** |
| HAR-L | 0.241 | −8.5% | 0.044 | 2.86 |

**The first statistically significant out-of-sample prediction in the project.** HAR beats EWMA on 16 of 20 assets, most clearly on big tech (META +26%, GOOGL +21%, MSFT +18%), DBC and BTC. MSTR, USO, SHY and AVAX are slightly worse. The leverage term adds nothing.

HAR's weights put about 70% on the 63-day vol and about 10% each on the 5-day and 22-day vol. In practice HAR means "trust the longer history more than the last few days". EWMA (λ = 0.94) reacts mostly to the last 2–3 weeks.

### 3.2 Portfolio (OOS, net of 10 bps)

| book | Sharpe | ann. return | ann. vol | max DD |
|---|---|---|---|---|
| equal weight 1/N (no vol info) | 1.05 | 28.1% | 26.8% | −30.2% |
| sized by EWMA | 1.22 | 12.1% | 9.9% | −11.3% |
| **sized by HAR** | **1.22** | 12.2% | 10.0% | −11.5% |
| sized by HAR-L | 1.23 | 12.2% | 9.9% | −11.6% |
| SPY | 1.04 | 17.6% | 16.9% | −18.8% |

## 4. Verdict — honest

> **Update 2026-10-11 → see [[07c - Long-History Re-test]].** Over 21 years HAR still wins on average (−4.8% QLIKE), but it loses in crash years (2008, 2009, 2020). EWMA sizing is slightly better there (Sharpe 1.25 vs 1.22).


1. **Volatility is predictable, and HAR predicts it better** (t = 2.8). This is real out-of-sample prediction.
2. **The better forecast doesn't change the portfolio** (Sharpe 1.22 vs 1.22). The weights are driven mostly by the *huge* differences between assets (SOL around 100% vol vs SHY around 2%), and EWMA already captures those. HAR's gain is in the smaller up-and-down swings over time, which move weights only a little.
3. **The big win is vol-sizing itself, whichever forecast feeds it.** Compared with 1/N, Sharpe goes from 1.05 to 1.22 and max drawdown shrinks from −30% to −11%.
4. **Both forecasts react late to spikes** (see G3). Volatility jumps first and the forecasts catch up after it. That is a limit of using daily prices only.

**Possible follow-up, not run:** portfolio-level vol targeting, which scales the *whole book* up or down with forecast portfolio risk (Moreira & Muir, 2017). That is where better timing of volatility can affect Sharpe. It needs a covariance forecast and would be a new, separately pre-committed test.

**Next:** Option 1, re-testing trend and vol on ~20 years of history. See [[Task Log]].
