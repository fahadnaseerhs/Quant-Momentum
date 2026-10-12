# 07 — Time-Series Momentum (Model 1, revised)

**Phase in the pipeline:** Step 7 of `Data → Cleaning → EDA → Features → Signal Analysis → Baseline → **Model 1** → …`
**Prerequisite:** [[04 - Feature Engineering]], [[05 - Signal Analysis]], baseline in [[Task 06 - Graph Explanation]].
**Code:** `src/tsmom.py` (features, model, sizing) · `scripts/07_tsmom.py` (walk-forward run, tables, 3 figures)
**Graphs:** [[Task 07 - Graph Explanation]] · **Status:** [[Task Log]]

---

## 1. The question

> **"Using only an asset's own price history, can we predict the direction of its next month's return well enough to trade it out of sample?"**

## 2. Why Task 07 pivoted from cross-sectional regression

The first Model 1 was a linear regression on the 15 Task 04 features, ranking assets against each other. Its walk-forward result (`07_wf_metrics.csv`) was **OOS IC ≈ 0** (1-day −0.003, 3-day +0.006), and its portfolio Sharpe (1.36) lost to the baseline (2.03). In-sample IC was 0.061, so it fit the training data and failed to generalise.

The root cause was a **method/universe mismatch**, not the model. The universe has 20 assets from five classes: 9 equities, 5 crypto, 2 bonds, 3 commodities and 1 REIT. Cross-sectional momentum asks "is SOL's trend stronger than SHY's?" That question only means something inside one homogeneous asset class. For a mixed basket, the standard tool is **time-series momentum**: each asset is compared only with its own past (Moskowitz, Ooi & Pedersen, 2012).

## 3. Method

### 3.1 Features (known at close of day $t$)

$\sigma_t$ is the EWMA ($\lambda = 0.94$) daily volatility of the asset's own returns through day $t$.

| Feature | Formula | Idea |
|---|---|---|
| `rev_5` | $\dfrac{P_t/P_{t-5}-1}{\sigma_t\sqrt5}$ | last week's move (short-term reversal?) |
| `mom_21`, `mom_63`, `mom_126` | $\dfrac{P_{t-5}/P_{t-L}-1}{\sigma_t\sqrt{L-5}}$ | trend over $L$ days, **skipping the last 5 days** |

Two fixes compared with Task 04:
- **Skip-5.** The old `mom_w` included the most recent days, where short-term reversal can cancel the trend. Now the trend and the recent week are separate inputs, and the model learns the sign of each.
- **Vol-normalised (a z-score of the move).** Dividing by $\sigma_t\sqrt{\text{days}}$ puts BTC (~57% vol) and SHY (~2% vol) on the same scale, so one pooled model can be fit across all 20 assets.

Collinearity dropped from 15 near-duplicate columns (condition number ~760) to **4** distinct ones.

### 3.2 Label

$$y_{i,t} = \frac{P_{i,t+h}/P_{i,t}-1}{\sigma_{i,t}\sqrt h}, \qquad h = 21 \text{ (primary, chosen before the run)}, \; h = 5 \text{ (robustness check)}$$

Features and the fitting label are clipped at ±4. This is a fixed bound, not a percentile estimated from the data, so the clip cannot leak future information.

### 3.3 Model

Pooled **ridge regression with no intercept**:

$$\hat y = \mathbf w^\top \mathbf x, \qquad \mathbf w = \left(\tfrac1m X^\top X + \alpha I\right)^{-1} \tfrac1m X^\top y, \quad \alpha = 0.05$$

- **No intercept, on purpose.** An intercept would learn 2021–26's average drift (the crypto and tech boom) and make the model permanently long. That would be beta dressed up as skill.
- **α is fixed, not tuned.** With 4 standardised features and more than 5,000 training rows, shrinkage barely matters. Tuning α on the test period would be data snooping.

### 3.4 Leakage-safe walk-forward

- Expanding window, **252 trading days** of first training data, **refit every 21 days**.
- **Purge/embargo = h.** A training row dated $d$ needs $d < t_\text{test} - h$, so every training label is fully realised before the first test date.
- The OOS period is **2022-08-04 → 2026-09-25** (about 4.1 years and 52 refits).

### 3.5 From prediction to positions

$$w_{i,t} = \operatorname{sign}(\hat y_{i,t}) \cdot \frac{\min(20\% / \sigma^{ann}_{i,t},\; 1)}{N}$$

The prediction sets the direction. Size is inverse-vol, capped at $1/N$ (no leverage), and the book rebalances daily. Net returns charge **10 bps per unit of weight traded**.

**Benchmarks**, all on the same dates with the same sizing:
- **rule**: the sign of the average of the 3 trend features, with no fitting. This is classic TSMOM.
- **long_only**: always long. This is pure beta and the honest yardstick.
- **SPY**.

## 4. How to run

```bash
.venv/Scripts/python.exe scripts/07_tsmom.py
```
This writes `reports/tables/07_ts_*.csv` and `reports/figures/07_ts_g*.png`, and copies the figures to `Figures/07/`. Runtime is a few seconds.

## 5. Results (OOS, 2022-08 → 2026-09)

### 5.1 Prediction quality

| h | signal | IC in-sample | IC OOS | IC non-overlap (t) | hit rate | always-long hit |
|---|---|---|---|---|---|---|
| 21 | model | 0.087 | **−0.026** | −0.022 (t = −0.70) | 49.9% | 56.4% |
| 21 | rule | — | 0.013 | 0.003 (t = 0.09) | 51.1% | 56.4% |
| 5 | model | 0.050 | −0.019 | −0.023 (t = −1.49) | 49.9% | 53.7% |
| 5 | rule | — | 0.007 | 0.000 (t = 0.00) | 50.6% | 53.7% |

*Non-overlap* keeps only every h-th date, so the labels don't share days. The t-stat is computed on those 980 (h=21) or 4,220 (h=5) rows. Assets are correlated with each other, so even these t-stats are generous.

### 5.2 Portfolios (net of 10 bps)

| h=21 | Sharpe gross | **Sharpe net** | ann. return | ann. vol | max DD |
|---|---|---|---|---|---|
| model | 0.38 | **−0.10** | −0.7% | 6.9% | −15.0% |
| rule | 0.13 | −0.26 | −1.7% | 6.8% | −14.5% |
| long_only | 1.54 | **1.50** | 14.5% | 9.7% | −10.1% |
| SPY | 1.21 | 1.21 | 19.4% | 16.1% | −18.8% |

h=5 tells the same story: the model's net Sharpe is −0.58, the rule's −0.35, and long-only's 1.58.

### 5.3 What the model learned

| fold | rev_5 | mom_21 | mom_63 | mom_126 |
|---|---|---|---|---|
| first (2022-08) | +0.107 | +0.043 | −0.030 | +0.088 |
| last (2026-09) | +0.039 | +0.043 | +0.004 | +0.059 |

The weights are stable and positive, so in training "trend continues" looked true. `rev_5` came out **positive**, meaning last week's move also continued rather than reversed. Then the pattern did not persist out of sample.

## 6. Verdict — honest

> **Update 2026-10-11 → see [[07c - Long-History Re-test]].** On 21 years of OOS data, the same model has IC 0.052 with no overfit gap and a net Sharpe of 0.41. The 2022–26 result below was a weak period for trend, not a dead signal.


1. **Neither the model nor the plain rule predicts out of sample.** OOS IC is ≈ 0 and not significant. The model's hit rate (49.9%) is below the 56% you'd get by always guessing "up".
2. **The overfit gap is still there with only 4 features.** In-sample IC was 0.087 and OOS was −0.026. Having too many features was not the problem. The in-sample relationship simply didn't carry into 2022–26.
3. **The only thing that earned money was being long.** The inverse-vol long-only book had a Sharpe of 1.50 with a −10% max drawdown, beating SPY on a risk-adjusted basis. That is **diversified beta in a bull market, not prediction**. It also tells us the Task 06 baseline's 2.29 Sharpe was largely beta.
4. **The sample is too short to test trend properly.** A genuine trend strategy has a Sharpe of roughly 0.5–1. Over $T$ years its t-stat is about $SR\sqrt T$, so with 4.1 OOS years even a true Sharpe of 0.7 gives t ≈ 1.4, which is undetectable. **No result here can confirm or kill trend-following.** What we can say is that in this window it added nothing over holding the assets.

## 7. What would change the answer

| Option | What | Why |
|---|---|---|
| **A. Longer history (recommended)** | Re-fetch equities/ETFs from ~2005. Crypto only exists from ~2015–18, so either drop it for the long test or use its shorter history. | Fixes the real constraint, which is statistical power. Trend evidence in the literature comes from decades of data and includes crisis years (2008, 2022) where trend pays. |
| B. Accept the null | Record "no predictive edge" and make the inverse-vol long book the reference strategy. | An honest, defensible result. **Don't move on to boosted trees (Task 08) on this data.** A more flexible model can't find a signal that isn't there; it only overfits harder. |

Related: [[Autocorrelation - Momentum vs Reversal]] · [[Volatility]] · [[Correlation and Diversification]]
