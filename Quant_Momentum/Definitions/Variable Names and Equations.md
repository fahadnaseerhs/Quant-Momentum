# Variable Names and Equations

Every column name, strategy name and metric in the project, with **what it means in plain words, the equation, and a tiny worked example**. The equations match the project code (`src/features.py`, `src/signals.py`, `src/baseline.py`).

**See also:** [[Glossary A-Z]] (words) · [[Graph and Table Labels]] (axes and CSV columns) · [[Task 04 - Graph Explanation]] · [[Task 05 - Graph Explanation]] · [[Task 06 - Graph Explanation]]

---

## 0. Notation (read this once)

| Symbol | Meaning |
|---|---|
| $i$ | an asset (BTC, AAPL, TLT, …) |
| $t$ | a trading day (the close of that day) |
| $P_{i,t}$ | adjusted closing price of asset $i$ on day $t$ |
| $V_{i,t}$ | trading volume of asset $i$ on day $t$ |
| $w$ | a lookback window, in **trading days**: 5, 10, 21, 63 |
| $\text{SPY}$ | the US stock market ETF, our benchmark (not traded as an asset) |
| $N$ | number of assets ranked each day (20) |

**Trading-day calendar:** 5 days ≈ 1 week · 10 ≈ 2 weeks · **21 ≈ 1 month** · **63 ≈ 3 months** · **252 ≈ 1 year**.

---

## 1. How the column names are built

| Piece | Stands for |
|---|---|
| `mom` | **mom**entum |
| `vsmom` | **v**olatility-**s**caled **mom**entum |
| `relret` | **rel**ative **ret**urn (to SPY) |
| `ewma_vol` | **EWMA** volatility |
| `roll_vol_63d` | **roll**ing **vol**atility, 63-day window |
| `vol_ratio_20d` | **vol**ume **ratio**, 20-day window |
| `fwd_ret_1d`, `fwd_ret_3d` | **f**or**w**ar**d** **ret**urn over the next 1 or 3 days |
| `_5d`, `_10d`, `_21d`, `_63d` | window length in trading days |
| `top5_` | strategy: hold the **top 5** by that feature |
| `ls_` | strategy: **l**ong–**s**hort |
| `eq_weight_universe` | hold all 20 assets at 5% each |
| `random_top5` | pick 5 assets at random each day |

Strategy names read as **`[what I hold]_[which feature]_[window]`**, e.g. `top5_vsmom_63d` = "hold the 5 assets with the highest vol-scaled 3-month momentum".

---

## 2. Returns

### Simple return (daily)
*The % change in price from yesterday to today. What an investor actually experiences.*

$$R_{i,t}=\frac{P_{i,t}}{P_{i,t-1}}-1$$

Example: 100 → 102 gives $R=+2\%$.

### Log return (daily)
*Same idea, but adds up over time.*

$$r_{i,t}=\ln\!\left(\frac{P_{i,t}}{P_{i,t-1}}\right)=\ln(1+R_{i,t})$$

Used for statistics (distributions, ACF). Portfolios and backtests use simple returns. See [[02 - Data Cleaning]] §7.

---

## 3. Momentum — `mom_5d`, `mom_10d`, `mom_21d`, `mom_63d`

*How much the price changed over the last $w$ trading days.*

$$\boxed{M_{i,t}^{(w)}=\frac{P_{i,t}}{P_{i,t-w}}-1}$$

**Example (`mom_63d`):** price was \$100 63 trading days ago and is \$130 today → $M=130/100-1=+0.30$ (**+30%**). If it is \$80 → $-0.20$.
Uses only prices up to day $t$, so no leakage.

---

## 4. Volatility

### 4a. Daily volatility, EWMA — `ewma_vol`
*How bumpy the asset has been recently, with a fading memory: recent days count more.* Recursive formula with $\lambda=0.94$:

$$\sigma_{i,t}^{2}=\lambda\,\sigma_{i,t-1}^{2}+(1-\lambda)\,R_{i,t}^{2},\qquad \lambda=0.94$$

Then $\sigma_{i,t}=\sqrt{\sigma^2_{i,t}}$. The first 63 days are set to missing (warm-up).
**The stored `ewma_vol` is lagged one day**, so the value in row $t$ is $\sigma_{i,t-1}$ (yesterday's estimate). This avoids any leakage.
A shock's influence halves about every $\ln 0.5/\ln 0.94\approx 11$ trading days.
Units: **per day** (0.02 = 2% a day).

### 4b. Daily volatility, rolling — `roll_vol_63d`
*Plain standard deviation of the last 63 daily returns, all weighted equally.*

$$\hat\sigma^{(63)}_{i,t}=\sqrt{\frac{1}{62}\sum_{s=t-62}^{t}\left(R_{i,s}-\bar R_{i}\right)^2}$$

### 4c. Annualised volatility
*Scale a daily volatility to a yearly number.*

$$\sigma_{annual}=\sigma_{daily}\times\sqrt{252}$$

Why $\sqrt{252}$ and not 252: see section 12.

---

## 5. Volatility-scaled momentum — `vsmom_5d … vsmom_63d`

*A momentum move measured in units of the asset's own normal daily wiggle: "is this move big **for this asset**?"*

$$\boxed{\text{vsmom}^{(w)}_{i,t}=\frac{M^{(w)}_{i,t}}{\sigma_{i,t-1}}}$$

**Example (`vsmom_63d`):**

| | $M^{(63)}$ | $\sigma_{t-1}$ (daily) | vsmom |
|---|---|---|---|
| Crypto token | +30% | 5% | $0.30/0.05=\mathbf{6}$ |
| Bond fund | +6% | 0.3% | $0.06/0.003=\mathbf{20}$ |

Raw momentum ranks the token first; vol-scaled momentum ranks the bond fund first because its move is far bigger relative to its normal.
Unit: "number of normal daily moves". It grows with the window (a $w$-day move is naturally about $\sqrt{w}$ times bigger).

---

## 6. Relative return — `relret_5d … relret_63d`

*How much the asset beat (or lagged) the market over the window.*

$$\boxed{\text{relret}^{(w)}_{i,t}=M^{(w)}_{i,t}-M^{(w)}_{\text{SPY},t}}$$

**Example:** asset +12% over 21 days, SPY +5% → $\text{relret}^{(21)}=+7\%$.

> **Key fact:** on a given day $M_{SPY,t}$ is the **same number subtracted from every asset**, so it **cannot change the ranking**. Hence `relret_w` ranks assets **identically** to `mom_w` (so they have the same IC, see [[Task 05 - Graph Explanation]]).

---

## 7. Volume ratio — `vol_ratio_20d`

*Is today's trading volume above or below the recent norm? (1 = normal, 2 = twice as busy.)*

$$\boxed{\text{VR}_{i,t}=\frac{V_{i,t}}{\frac{1}{20}\sum_{s=t-19}^{t}V_{i,s}}}$$

**Example:** today 150, 20-day average 100 → $\text{VR}=1.5$. Unit-free, so it can be compared across assets.

---

## 8. Targets (what we predict) — `fwd_ret_1d`, `fwd_ret_3d`

*The return that happens **after** day $t$. Labels only, never used as inputs.*

$$\boxed{R^{(h)}_{i,t\to t+h}=\frac{P_{i,t+h}}{P_{i,t}}-1},\qquad h\in\{1,3\}$$

`fwd_ret_1d` = tomorrow's return. `fwd_ret_3d` = the **total** return over the next three days. Consecutive 3-day targets share 2 days (the overlap trap).

---

## 9. Winsorising (capping extremes)

*Clip each feature column at its 1st and 99th percentile (pooled across all dates and assets).*

$$x^{wins}=\min\!\big(\max(x,\;q_{1\%}),\;q_{99\%}\big)$$

Explains the flat tops and bottoms in the Task 04 pictures. Targets are never winsorised.

---

## 10. Signal quality (Task 05)

### Information Coefficient (IC), one number per day
*How well the day's feature ranking agrees with the next return's ranking.*

$$\text{IC}_t=\rho_{Spearman}\big(\text{rank}_i(\text{feature}_{i,t}),\ \text{rank}_i(R_{i,t\to t+h})\big)$$

For $n$ assets and no ties, $\;\rho=1-\dfrac{6\sum_i d_i^2}{n(n^2-1)}$, where $d_i$ is the difference between asset $i$'s two ranks.
**Range:** +1 perfect, 0 random, −1 reversed.

### Mean IC, hit rate, IC std

$$\overline{\text{IC}}=\frac1T\sum_t\text{IC}_t\qquad
\text{hit rate}=\frac{\#\{t:\text{IC}_t>0\}}{T}\qquad
\text{IR}=\frac{\overline{\text{IC}}}{\text{std}(\text{IC}_t)}$$

### t-statistic (Newey–West)
*Is the mean IC different from zero, or is it luck?*

$$t=\frac{\overline{\text{IC}}}{\text{SE}_{NW}}$$

where $\text{SE}_{NW}$ is the standard error that accounts for neighbouring days being correlated (Bartlett weights, about 7 lags). **|t| ≳ 2 ≈ unlikely to be luck.** Plain-sample version: $\text{SE}=\sigma/\sqrt{T}$.

### Quintile spread
Each day sort assets by the feature into 5 groups; $Q_5$ = highest.

$$\text{spread}=\overline{R}_{Q5}-\overline{R}_{Q1}$$

(average next-period return of the top group minus the bottom group, before costs).

### Rolling and cumulative IC

$$\text{rollIC}_t=\frac{1}{252}\sum_{s=t-251}^{t}\text{IC}_s\qquad
\text{cumIC}_t=\sum_{s\le t}\text{IC}_s$$

The slope of $\text{cumIC}$ equals the average IC.

---

## 11. Strategies (Task 06)

### Rank and weights, top-5 long-only
Each day, rank the $N$ assets by the feature (rank 1 = highest value). Then

$$w_{i,t}=\begin{cases}\dfrac{1}{5}&\text{if rank}_{i,t}\le 5\\[2mm]0&\text{otherwise}\end{cases}$$

Weights sum to 1 (100% invested, equal 20% in each of 5 assets).

### Long–short (top 5 long, bottom 5 short)

$$w_{i,t}=\begin{cases}+\dfrac15&\text{if in the top 5}\\[1mm]-\dfrac15&\text{if in the bottom 5}\\[1mm]0&\text{otherwise}\end{cases}$$

Weights sum to 0 (market-neutral in dollars), gross exposure 2.

### Equal-weight universe and random

$$w_{i,t}=\frac1N\ (=5\%)\ \text{for all }i\qquad\text{random: 5 assets chosen at random each day, }\tfrac15\text{ each}$$

### Strategy daily return (no peeking)
*Today's chosen weights earn the **next** day's return.*

$$R^{strat}_{t}=\sum_i w_{i,t}\;R_{i,t\to t+1}$$

**Example (top-5):** the 5 held assets return +2%, +1%, −1%, +3%, 0% → $R^{strat}=\tfrac15(2+1-1+3+0)\%=+1\%$.

### Equity curve (Graph 1)
*What \$1 becomes.*

$$E_t=\prod_{s\le t}\left(1+R^{strat}_s\right),\qquad E_0=1$$

---

## 12. Performance metrics (Task 06 table and graphs)

| Metric | Equation | Plain meaning |
|---|---|---|
| **Cumulative return** | $E_T-1$ | Total gain (7.47 = +747%) |
| **Annual return** | $(1+\bar R)^{252}-1$ | Yearly growth rate from the average daily return $\bar R$ |
| **Annual volatility** | $\text{std}(R)\sqrt{252}$ | Yearly bumpiness |
| **Sharpe ratio (table)** | $\dfrac{\text{annual return}}{\text{annual volatility}}$ | Return per unit of bumpiness (no risk-free rate subtracted) |
| **Win rate** | $\dfrac{\#\{R_t>0\}}{T}$ | Share of positive days |
| **Turnover (daily, one-sided)** | $\tfrac12\sum_i\lvert w_{i,t}-w_{i,t-1}\rvert$ | Fraction of the portfolio replaced each day |

### Drawdown (Graph 2)
*How far below the best balance so far.*

$$\text{DD}_t=\frac{E_t}{\max_{s\le t}E_s}-1,\qquad \text{max drawdown}=\min_t \text{DD}_t$$

**Example:** balance \$1.80 at the peak, \$1.00 now → $\text{DD}=1.00/1.80-1=-44\%$.

### Rolling Sharpe (Graph 3)
*Sharpe over only the last 126 trading days (~6 months), recomputed daily.*

$$\text{Sharpe}^{roll}_t=\frac{\overline{R}_{t-125..t}}{\text{std}\big(R_{t-125..t}\big)}\times\sqrt{252}$$

(Simple average ÷ standard deviation, so it differs slightly from the table's compounded version.)

### Why $\sqrt{252}$? (scaling a daily Sharpe to a yearly one)
For independent days with mean $\mu$ and standard deviation $\sigma$, over $T$ days:

$$E[S_T]=T\mu,\qquad \mathrm{SD}(S_T)=\sigma\sqrt{T}\;\Rightarrow\;\frac{T\mu}{\sigma\sqrt{T}}=\sqrt{T}\,\frac{\mu}{\sigma}$$

With $T=252$: $\;\text{Sharpe}_{annual}=\sqrt{252}\,\mu/\sigma\approx 15.87\,\mu/\sigma$. Profit adds up linearly; randomness grows only like a square root because ups and downs partly cancel.

### Trading-cost drag (rough)
For a cost $c$ per unit traded (paid on buys and sells):

$$\text{yearly drag}\approx c\times 2\times\text{turnover}\times 252$$

Example: $c=0.1\%$, turnover $0.158$ → $0.001\times2\times0.158\times252\approx 8\%$ a year.

---

## 13. One-page cheat sheet

| Name | Equation in one line |
|---|---|
| `mom_wd` | $P_t/P_{t-w}-1$ |
| `ewma_vol` | $\sqrt{\sigma^2_{t-1}}$, with $\sigma_t^2=0.94\,\sigma_{t-1}^2+0.06\,R_t^2$ |
| `roll_vol_63d` | std of last 63 daily returns |
| `vsmom_wd` | `mom_wd` ÷ `ewma_vol` |
| `relret_wd` | `mom_wd` − SPY's `mom_wd` |
| `vol_ratio_20d` | $V_t$ ÷ average of last 20 days' volume |
| `fwd_ret_hd` | $P_{t+h}/P_t-1$ |
| IC | Spearman(rank of feature, rank of next return), per day |
| Sharpe | mean ÷ std (× √252 to annualise) |
| Drawdown | balance ÷ best balance so far − 1 |
| Turnover | ½ × sum of absolute weight changes |
