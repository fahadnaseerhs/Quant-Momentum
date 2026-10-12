# 04 — Feature Engineering

**Phase in the pipeline:** Step 4 of `Data → Cleaning → EDA → **Features** → Signal Analysis → Models → Portfolio → Backtest → Risk → Costs → Robustness`.

**Prerequisite:** [[03 - Exploring Returns]] is done. The cleaned dataset lives in `data/processed/`. All Task 03 findings (fat tails, vol clustering, N_eff ≈ 3.9, no own-return autocorrelation) inform the design choices below.

---

## 1. The question

> **"What measurable quantities, known at the end of day $t$, might help predict tomorrow's (or the next 3 days') return?"**

We are not asking "does momentum work?" yet — that is Task 05 (Signal Analysis). Here we only ask: *what features should we compute, and how do we compute them without leaking future information?*

---

## 2. Why feature engineering matters

A prediction model can only learn from the inputs it receives. If we hand it raw prices, it sees numbers that grow over time — useless for cross-sectional comparison. If we hand it well-constructed features (momentum, volatility, volume behaviour, relative performance), we give the model the *kind* of information that finance theory and our own EDA suggest might contain a signal.

But every feature introduces a risk: **lookahead bias**. If a feature at time $t$ accidentally uses price data from $t+1$, the model will appear to work in-sample but will fail in live trading. The central design constraint of this task is:

> **Every feature computed at the end of day $t$ uses only information available at the close of day $t$ or earlier.**

---

## 3. The features

### 3.1 Momentum (lookback returns)

Momentum measures how much an asset's price has moved over a trailing window. The idea: assets that have been going up tend to keep going up (momentum effect), or the opposite (mean reversion). Task 03 showed no autocorrelation in 1–10 day returns, but cross-sectional ranking (comparing assets to each other) is a different test — that's Task 05.

For each lookback window $w$ in trading days:

$$M_{i,t}^{(w)} = \frac{P_{i,t}}{P_{i,t-w}} - 1$$

**Lookback grid:** 5, 10, 21, 63 trading days (roughly 1 week, 2 weeks, 1 month, 3 months).

**Why these windows?** Task 03's decision log (`decisions/2026-09-27-task03-findings-and-env-repair.md`) sets the grid. The final window will be chosen by Task 05's cross-sectional test, not by the ACFs we already computed.

**Leakage check:** $P_{i,t}$ is the close price on day $t$, known at the end of day $t$. $P_{i,t-w}$ is older. ✅ No future data.

### 3.2 Volatility (EWMA, lagged one day)

Volatility measures how "jumpy" an asset is. Task 03 showed annual vol ranges from 1.9% (SHY) to 115% (AVAX), and vol clusters over time. We need vol for two reasons:

1. **Vol-scaling momentum** — so that a 5% move in AVAX (routine) isn't ranked the same as a 5% move in SHY (extraordinary).
2. **As a feature itself** — high-vol environments may predict different returns than low-vol environments.

The EWMA (Exponentially Weighted Moving Average) variance formula:

$$\sigma_t^2 = \lambda \cdot \sigma_{t-1}^2 + (1 - \lambda) \cdot r_t^2, \quad \lambda = 0.94$$

We use $\lambda = 0.94$ (the RiskMetrics standard). The first 63 days are set to NaN (warm-up period for the recursion to stabilise).

**Critical leakage rule:** When building features for day $t$, we use $\sigma_{t-1}$, **not** $\sigma_t$. Why? Because $\sigma_t$ depends on $r_t = P_t / P_{t-1} - 1$, which includes the close price of day $t$. If we used $\sigma_t$ and then predicted $R_{t+1}$, the vol estimate would contain $P_t$, which is fine. But the standard practice — and what avoids any subtle edge-case leakage in intraday contexts — is to lag by one day. This gives:

$$\text{vol\_scaled\_mom}_{i,t}^{(w)} = \frac{M_{i,t}^{(w)}}{\sigma_{i,t-1}}$$

**Robustness column:** We also compute a 63-day rolling standard deviation as an alternative vol measure, for later comparison.

### 3.3 Volume ratio

Volume can signal conviction. A price move on unusually high volume may be more meaningful than the same move on thin volume.

$$\text{VolumeRatio}_{i,t} = \frac{V_{i,t}}{\text{mean}(V_{i,t-19}, \ldots, V_{i,t})}$$

A value > 1 means today's volume is above its 20-day average.

**Leakage check:** Both numerator and denominator use data from day $t$ or earlier. ✅

### 3.4 Relative-to-market return

Is the asset outperforming the market, or just riding the tide?

$$\text{RelRet}_{i,t}^{(w)} = M_{i,t}^{(w)} - M_{\text{SPY},t}^{(w)}$$

We compute this for the same lookback grid (5, 10, 21, 63 days).

**Leakage check:** Same prices, same windows. ✅

### 3.5 Forward targets (NOT features — labels)

These are what we are trying to predict. They must **never** appear as model inputs.

$$R_{i,t+1}^{(1d)} = \frac{P_{i,t+1}}{P_{i,t}} - 1 \qquad \text{(1-day forward return)}$$

$$R_{i,t+1}^{(3d)} = \frac{P_{i,t+3}}{P_{i,t}} - 1 \qquad \text{(3-day forward return)}$$

These are computed here for convenience but stored in clearly labelled columns (`fwd_ret_1d`, `fwd_ret_3d`). The 3-day target overlaps — consecutive rows share 2 days of return — which matters for walk-forward splits later (≥3-day embargo needed).

---

## 4. Feature summary table

| Feature | Column pattern | Formula | Leakage-safe? |
|---|---|---|---|
| Momentum | `mom_5d`, `mom_10d`, `mom_21d`, `mom_63d` | $P_t / P_{t-w} - 1$ | ✅ |
| EWMA vol (lagged) | `ewma_vol` | $\sigma_{t-1}$, EWMA $\lambda=0.94$ | ✅ (lagged) |
| Rolling vol | `roll_vol_63d` | 63-day std of returns | ✅ |
| Vol-scaled momentum | `vsmom_5d`, …, `vsmom_63d` | $M_t^{(w)} / \sigma_{t-1}$ | ✅ |
| Volume ratio | `vol_ratio_20d` | $V_t / \text{mean}_{20}(V)$ | ✅ |
| Relative return | `relret_5d`, …, `relret_63d` | $M_t^{(w)} - M_{\text{SPY},t}^{(w)}$ | ✅ |
| **Forward targets** | `fwd_ret_1d`, `fwd_ret_3d` | $P_{t+h}/P_t - 1$ | ⚠️ Labels only |

---

## 5. Winsorisation

Task 03 showed fat tails in all 21 assets. Extreme outliers can dominate regression and ranking. We apply **winsorisation at the 1st and 99th percentile** to each feature column cross-sectionally (across all assets on a given day). This clips extreme values without removing rows.

Winsorisation is applied *after* feature construction and *before* any model or IC test.

---

## 6. The environment

### 6.1 What gets built

| Artefact | Path | Purpose |
|---|---|---|
| Feature library | `src/features.py` | Pure functions: `momentum()`, `ewma_vol_lagged()`, `volume_ratio()`, `relative_return()`, `forward_targets()`, `build_all_features()` |
| Feature script | `scripts/04_build_features.py` | Orchestrator: loads `data/processed/`, calls the library, saves the feature matrix |
| Feature matrix | `data/features/features.parquet` | Long-format: rows = (date, ticker), columns = features + targets |

### 6.2 Data flow

```
data/processed/prices_daily_clean.parquet
data/processed/returns_daily.parquet
data/processed/volume_daily_clean.parquet
        ↓
  src/features.py (pure functions)
        ↓
  scripts/04_build_features.py
        ↓
  data/features/features.parquet
```

---

## 7. Guide to run it

```
cd "C:\Users\USER\OneDrive\Desktop\Quant_ Momentum"
.venv\Scripts\activate
python scripts/04_build_features.py
```

Runtime: < 5 seconds (all computation is vectorised pandas, no network calls).

---

## 8. Expected outcome

### 8.1 Console output

```
Loading processed data ...
Building features for 21 tickers, 4 momentum windows ...
Feature matrix shape: (~1300, ~18) per ticker → (~27000, 18) total long-format
Saved: data/features/features.parquet
```

### 8.2 Checks

| Check | Expected |
|---|---|
| No NaN in forward targets (except the last 1 or 3 rows) | ✅ |
| `ewma_vol` starts after 63 warm-up days | ✅ |
| `vsmom_*` has no inf or extreme values after winsorisation | ✅ |
| Feature matrix is long-format with `date` + `ticker` as index | ✅ |

---

## 9. What this task does NOT do

- It does **not** test whether any feature predicts returns — that is [[05 - Signal Analysis]].
- It does **not** rank assets — ranking comes in Task 05 (Spearman IC).
- It does **not** train any model.
- It does **not** split data into train/test.

---

## 10. Where this leads

Once features are built:

- **05 — Signal Analysis** — rank assets cross-sectionally by each feature; compute Information Coefficient (Spearman IC) between feature ranks and forward-return ranks; test within asset-class blocks.
- **06 — Prediction Models** — use the feature matrix as inputs to Model 0 (rank baseline), Model 1 (linear regression), and later Model 2 (gradient-boosted trees).

---

## 11. Related notes

- [[03 - Exploring Returns]] — the EDA findings that informed these feature choices
- [[00 - Project Introduction]] — project overview
- [[quant_equity_prediction_strategy_lab]] — full research scope
