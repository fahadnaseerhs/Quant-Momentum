# 03 — Exploring Returns

**Phase in the pipeline:** Step 3 of `Data → Cleaning → **Exploring Returns** → Features → Signal Analysis → Statistics → Models → Portfolio → Backtest → Risk → Costs → Robustness`.

**Status:** ✅ Built and run (2026-09-27). §2–7 are the plan written before running; **§8 records what we actually saw**, and **§8.3 lists what it means for Task 04.**

**Prerequisites:**
- Data: `data/processed/returns_daily.parquet` and `returns_daily_log.parquet` from [[02 - Data Cleaning]].
- Concepts: read the [[_Technical Learning - README|Technical Learning]] notes first. This note uses their formulas and doesn't re-explain them.

---

## 1. The question

> Before designing any momentum feature: **how do daily returns in our 21-asset universe actually behave?** How volatile are they, is that volatility stable, how extreme are the extremes, which assets move together, and does a recent return carry any information about the next one?

**Why this comes before features.** Every design choice in Task 04 depends on the answers:

| Answer from this task | Decision it drives in Task 04+ |
|---|---|
| Does volatility change over time? | Fixed σ vs rolling/EWMA σ for vol-scaled momentum |
| How fat are the tails? | Pearson vs Spearman, whether to winsorise features |
| Which assets cluster together? | Rank across the whole universe or within asset classes |
| Momentum or reversal at 1–10 days? | Which lookback windows to build, and in which direction |

**Look first, then design.**

---

## 2. Graph 1: Growth of \$1 (log scale)

**Concept:** [[Prices, Returns and Stationarity]] §3–4.

**Formula:** for each asset, $W_{i,t} = \prod_{s \le t}(1 + R_{i,s})$, starting at $W_{i,0} = 1$ on 2021-01-04. Log-scale y-axis.

**Layout:** six panels, one per asset class (crypto, tech, gold, oil, real assets, bonds), with SPY drawn in grey on every panel as a reference.

**What we're trying to see:**
1. **The market regimes** of 2021–2026: the 2021 crypto boom, the 2022 bear market in stocks, bonds and crypto together, the 2023–24 recovery, the April 2025 tariff shock, the gold boom and January 2026 gold crash.
2. **Which asset classes won and lost** over the whole period, and whether assets within a class move as a group.
3. **A final data sanity check:** a vertical cliff with no matching event would suggest a leftover data error (like the GOLD ticker bug).

| If we see… | It means… | Consequence |
|---|---|---|
| Distinct up and down phases shared across classes | Clear regimes exist | Task 11 tests the strategy separately in each regime |
| Assets in a class tracking each other closely | Class-level co-movement | Confirms the correlation analysis (Graph 5) |
| An unexplained vertical jump | Possible data error | Stop and investigate before continuing |

---

## 3. Graph 2: Rolling volatility over time

**Concepts:** [[Volatility]] §4–5, [[Volatility Clustering]].

**Formula:** 63-day rolling annualised volatility, $\hat\sigma^{(63)}_{i,t}\sqrt{252}$, plus EWMA volatility with λ = 0.94 overlaid for a few representative assets.

**Layout:** one panel per asset class; y-axis in % per year.

**What we're trying to see:**
1. **Is volatility constant or wave-like?** Clustering predicts waves: spikes that decay slowly.
2. **Do the spikes line up with known events** (Graph 1's regimes)?
3. **Does each asset's *relative* volatility stay stable?** Is crypto always ~4× equities, or does the ratio swing?
4. **Rolling vs EWMA:** how much faster does EWMA react after a shock?

| If we see… | It means… | Consequence |
|---|---|---|
| Waves and spikes, not a flat line | Volatility clustering is present | Vol-scaled momentum must use a **time-varying** σ |
| Relative vol between assets also changes over time | A single σ per asset would mis-rank assets | Reinforces time-varying σ |
| EWMA reacts much faster with only modestly more noise | EWMA tracks regime shifts better | Candidate default σ for Task 04 |
| Roughly flat volatility | No clustering (unlikely) | A simple full-sample σ would suffice |

---

## 4. Graph 3: Distributions and fat tails

**Concept:** [[Return Distributions and Fat Tails]].

### 4.1 Summary table (all 21 assets)

| Column | Formula |
|---|---|
| Annualised mean | $252 \times \bar{r}$ |
| Annualised volatility | $\sqrt{252}\, s$ |
| Skewness | $\frac{1}{T}\sum z_t^3$ |
| Excess kurtosis | $\frac{1}{T}\sum z_t^4 - 3$ |
| Jarque–Bera statistic and p-value | $\frac{T}{6}\left(S^2 + \frac{(K-3)^2}{4}\right)$ |
| Worst and best day, in σ units | $\min z_t,\ \max z_t$ |

### 4.2 Plots, for four representative assets

**SPY** (broad market), **NVDA** (high-beta stock), **BTC-USD** (crypto), **TLT** (bonds):
- Histogram of $z_t$ with the standard normal curve overlaid
- QQ plot against the normal distribution

### 4.3 Before vs after volatility scaling

Recompute skewness and kurtosis on returns divided by the **previous day's** EWMA volatility:

$$\tilde{z}_{i,t} = \frac{r_{i,t}}{\hat\sigma_{i,t-1}}$$

(Using $t-1$ keeps it leakage-free; see [[Volatility Clustering]] §5.)

**What we're trying to see:**
1. **How fat the tails are**, per asset and per class.
2. **The direction of skew:** crash-prone (negative) or lottery-like (positive)?
3. **How much of the fat-tailedness disappears** after dividing by recent volatility.

| If we see… | It means… | Consequence |
|---|---|---|
| Excess kurtosis ≫ 0 everywhere; S-shaped QQ plots | Fat tails, as expected | Prefer Spearman / rank-based measures; consider winsorising features |
| Strongly negative skew in equities | Crash risk | Long-only portfolios carry hidden tail risk; watch drawdowns |
| Kurtosis drops sharply after vol-scaling | Fat tails are largely regime-switching | Vol-scaling does double duty: fair ranking **and** better-behaved inputs |
| Kurtosis barely drops | Genuine jump risk (single-day shocks) | Rank-based methods become more important |

---

## 5. Graph 4: Correlation structure

**Concept:** [[Correlation and Diversification]].

**Plots and numbers:**
1. **Clustered heatmap** of the 21 × 21 Pearson correlation matrix of daily returns.
2. The same matrix using **Spearman**. Big Pearson–Spearman gaps flag pairs driven by outliers.
3. **Average pairwise correlation** $\bar\rho$ among the 20 tradeables, and the **effective number of bets** $N_{eff} = N/(1+(N-1)\bar\rho)$.
4. **Rolling 63-day average pairwise correlation** over time.

**What we're trying to see:**
1. **Hidden blocks**: expected crypto (+ MSTR), big tech, energy (XOM, CVX, USO), gold (GLD, B), rates (TLT, SHY).
2. **Diversifiers:** which assets have low or negative correlation with the rest?
3. **How many real bets** the universe contains.
4. **Crisis behaviour:** does average correlation spike in 2022 and April 2025?

| If we see… | It means… | Consequence |
|---|---|---|
| Tight blocks, $N_{eff}$ ≈ 3–6 | Universe is a few themes, not 20 bets | Test ranking **within** asset classes as well as across the whole universe |
| Weak or no blocks, $N_{eff}$ high | Genuinely diverse universe | Cross-universe ranking is fine |
| Average correlation spikes in crises | Diversification fails when needed | Regime analysis in Task 11 must include correlation regimes |
| Crypto–equity correlation lower than expected | Partly the 4-hour close mismatch ([[02 - Data Cleaning]] §6.3) | Don't over-interpret same-day crypto–equity numbers |

---

## 6. Graph 5: Autocorrelation of daily returns (the key graph)

**Concept:** [[Autocorrelation - Momentum vs Reversal]].

### 6.1 ACF of 1-day returns

**Formula:** $\hat\rho_{i,k}$ for $k = 1,\dots,10$, for each asset.

**Layout:** a 21-panel grid of small ACF plots (one per asset), with a band of $\pm 1.96/\sqrt{T} \approx \pm 0.052$.

### 6.2 Ljung–Box and variance-ratio table

| Column | Formula | Question |
|---|---|---|
| $\hat\rho_1$ | lag-1 autocorrelation | Direction at 1 day |
| $Q(5)$, $Q(10)$ + p-values | Ljung–Box | Any dependence at all in the first 5 / 10 lags? |
| $VR(3)$ | $1 + 2\sum_{k=1}^{2}(1-k/3)\rho_k$ | Does 3-day risk differ from √3 × 1-day risk? |
| # significant lags out of 10 | count outside ±0.052 | Compare to the ~0.5 expected by chance |

### 6.3 ACF of **non-overlapping** 3-day returns

**Formula:** sum log returns in consecutive, non-overlapping blocks of 3 days, then compute $\hat\rho_k$ for $k = 1,\dots,5$. Band: $\pm 1.96/\sqrt{479} \approx \pm 0.09$.

**Why non-overlapping:** overlapping 3-day returns show $\rho_1 = 0.67$ from the overlap alone, even for pure noise ([[Autocorrelation - Momentum vs Reversal]] §8).

**What we're trying to see:**
1. **The sign at short lags, by asset class.** Momentum (positive) or reversal (negative)?
2. **Consistency.** Do related assets share the same sign at the same lag? Consistency across a class matters more than any single significant bar, given ~200 tests.
3. **Size.** With $R^2 = \rho_1^2$, how much forecasting power could a 1-day signal possibly have?
4. **The 3-day horizon.** Is there more (or less) structure at 3 days than at 1 day?

| If we see… | It means… | Consequence for Task 04 |
|---|---|---|
| Consistent **positive** $\rho_1$–$\rho_3$ in a class (e.g., crypto) | Short-term momentum in that class | Build short lookbacks (e.g., 3–10 days) in the momentum direction |
| Consistent **negative** $\rho_1$ in a class (e.g., single stocks) | Short-term reversal | Short lookbacks should be used **reversed** or excluded; momentum may only appear at longer lookbacks (21–63 days) |
| Mixed signs across classes | Different classes behave differently | Rank within classes, or build class-specific features |
| Everything inside the band, Ljung–Box not rejected | No linear time-series predictability at short lags | Not fatal (cross-sectional effects can still exist, see Task 05), but set expectations low |
| $VR(3)$ clearly ≠ 1 | Multi-day risk scales differently from √time | Affects 3-day target volatility and position sizing |

---

## 7. Graph 6: Autocorrelation of squared returns

**Concept:** [[Volatility Clustering]] §3.

**Formula:** $\hat\rho_k$ of $r_{i,t}^2$, for $k = 1,\dots,20$, for each asset. Same layout and band as Graph 5.

**What we're trying to see:** the statistical confirmation of Graph 2. Clustering shows up as **positive, slowly decaying** bars, visibly different from Graph 5's near-zero bars.

| If we see… | It means… | Consequence |
|---|---|---|
| Positive bars that persist 10–20 lags | Strong, persistent clustering | Time-varying σ required; use Newey–West standard errors in all later tests |
| Only lag 1–2 positive | Short-lived clustering | Shorter vol windows (e.g., 21 days or EWMA) are enough |
| Graph 5 ≈ 0 but Graph 6 clearly > 0 | Direction unpredictable, size predictable | The classic stylised fact; confirms data realism |

---

## 8. Results

### 8.1 Hypotheses: verdicts

Research on asset returns (the **stylised facts**, after Cont, 2001) predicted the following. Rejections are informative, not failures.

| # | Hypothesis | Result | Evidence |
|---|---|---|---|
| H1 | Volatility clusters in every asset | ✅ (with $\lvert r\rvert$) | 18/21 assets have ≥ 10 of 20 significant lags using $\lvert r\rvert$; only 8/21 using $r^2$ (see lesson L1) |
| H2 | Every asset is fat-tailed | ✅ | 21/21: excess kurtosis 0.6 (TLT) to 23 (META); JB rejects everywhere |
| H3 | Tails shrink after vol-scaling | ➖ | Median −22%. Strong for SPY (8.2 → 2.2), GLD (7.8 → 2.0), AAPL, SOL, SHY; **worse** for NVDA, GOOGL, META (lesson L3) |
| H4 | Equities are negatively skewed | ❌ | Mixed: META −1.0, oil −0.3/−0.4, but AAPL, MSFT, NVDA, SPY slightly positive. Skew is driven by a few days (SPY's +9.5σ on 9 Apr 2025) |
| H5 | ~5 blocks, $N_{eff}$ ≪ 20 | ✅ | $\bar\rho$ = 0.21 → $N_{eff}$ ≈ **3.9**. Blocks: crypto + MSTR, oil (+ DBC), gold, bonds, US equities |
| H6 | Correlation rises in stress | ✅ | Rolling avg 0.31 (2022) and 0.32 (Apr–May 2025) vs median 0.19; peak ≈ 0.43 around FTX |
| H7 | Daily autocorrelations are tiny | ✅ | Max $\lvert\rho_1\rvert$ = 0.058 (DBC) → $R^2$ = 0.34% |
| H8 | Stocks reverse, crypto trends (1–10 days) | ❌ | No class-level pattern. 9 robust hits in 210 tests vs ≈ 10.5 expected by chance |
| H9 | Size predictable, direction not | ✅ | Median lag-1 ACF: 0.126 ($\lvert r\rvert$), 0.111 ($r^2$), 0.001 (raw $r$) |

### 8.2 What each graph showed

**Graph 1: growth of \$1.** Huge dispersion. SOL turned \$1 into ≈ \$49, but had a −96% drawdown along the way. NVDA ≈ \$17. LINK ended flat after −90%, and TLT lost 39%. Regimes are visible: 2022 (stocks, bonds and crypto fell together), April 2025, January 2026 (gold). No unexplained cliffs.

![[03_g1_growth_of_1.png]]

**Graph 2: volatility over time.** Clear waves: each asset's 63-day volatility spans 3–5× between its calmest and wildest quarter. Relative volatility also moves: BTC ranges 1.2×–9.7× SPY's, GLD 0.5×–3.6×. EWMA reacts within days. The 63-day window lags, then drops off a cliff 63 days later as the shock leaves the window.

![[03_g2_rolling_vol.png]]
![[03_g2_rolling_vs_ewma.png]]

**Graph 3: tails.** Fat tails everywhere (S-shaped QQ plots). Vol-scaling calms indices and ETFs, but not earnings-driven single stocks.

![[03_g3_hist_qq.png]]
![[03_g3_kurtosis_before_after.png]]

**Graph 4: correlation.** Five blocks. Surprises: **MSTR behaves like crypto** (0.72 with BTC), **DBC behaves like oil** (0.91 with USO), and the "real assets" label is not a real group (within-class 0.17). Oil vs bonds −0.13.

![[03_g4_corr_clustered.png]]
![[03_g4_rolling_avg_corr.png]]

**Graph 5: autocorrelation (key graph).** Nothing consistent. Bars crossing the band occur at the rate luck predicts. Slight leanings (not significant): bonds and SPY negative (VR(3) 0.89–0.95), oil positive. SPY's −0.11 three-day reversal passes Bartlett's band but fails the robust one, so it's an artefact of volatile periods. The overlap trap reproduced theory exactly (0.67 / 0.34).

![[03_g5_acf_daily.png]]
![[03_g5_overlap_trap.png]]

**Graph 6: squared and absolute returns.** Strong, persistent clustering: still significant at lag 20 for TLT, SHY, AVAX and GLD.

![[03_g6_size_vs_direction.png]]

All other figures are in `Quant_Momentum/Figures/03/`; all tables are in `reports/tables/03_*.csv`.

### 8.3 What this means for Task 04

| Finding | Decision for Task 04 |
|---|---|
| Volatility varies 3–5× over time, and relative vol swings too | Vol-scaled momentum uses a **time-varying σ**; **EWMA (λ = 0.94)** is the default, 63-day rolling as a robustness check |
| Vol-scaling calms regime-driven tails, not earnings jumps | Use **rank-based** comparisons (Spearman / IC); consider winsorising features at 1%/99% |
| $N_{eff}$ ≈ 3.9; MSTR = crypto, DBC = oil | Test ranking **across the universe** and **within blocks**; treat MSTR as crypto-block and DBC as oil-block in any class-level analysis |
| No own-return predictability at 1–10 days | Short lookbacks (1–10 days) are **not** expected to work as time-series signals. Build a grid of lookbacks (5, 10, 21, 63) and let Task 05's cross-sectional test decide; do **not** pick lookbacks from these ACFs (overfitting) |
| Daily edges are tiny ($R^2$ < 0.4%) | Expectations stay modest; transaction costs will decide viability |
| Clustering persists 20+ days | All later significance tests use **Newey–West** standard errors |

**Why this isn't bad news for the project:** the ACF only tests whether an asset's *own* last 1–10 days predict its *own* next day. Our strategy is **cross-sectional** (it ranks assets against each other) and will also test **longer lookbacks** (21–63 days), which lags 1–10 don't cover ([[Autocorrelation - Momentum vs Reversal]] §9). Task 05 is the real test.

### 8.4 Lessons learned

- **L1. With fat tails, detect clustering with $\lvert r\rvert$, not $r^2$.** Squaring lets a few giant days dominate: META showed 0 significant $r^2$ lags but 10 with $\lvert r\rvert$.
- **L2. Always compare Bartlett and robust bands.** Several "significant" autocorrelations (SPY's 3-day reversal) disappear once volatility clustering is accounted for.
- **L3. Two kinds of fat tails.** *Regime tails* (calm/storm switching) shrink when you divide by recent volatility. *Jump tails* (earnings, news) don't, and can look even worse because the jump arrives in a calm period.
- **L4. Rolling windows have ghosts.** A 63-day window keeps a shock at full weight for 63 days, then drops it all at once. EWMA fades it gradually.
- **L5. Asset labels ≠ behaviour.** Check correlation before trusting a class label (MSTR, DBC).

---

## 9. The environment

| File | Type | Role |
|---|---|---|
| `src/eda.py` | Module | Reusable functions: wealth index, rolling and EWMA volatility, vol-scaled returns, moments table, ACF with Bartlett **and robust** bands, Ljung–Box, variance ratio, non-overlapping returns, average correlation, effective bets, rolling average correlation |
| `notebooks/03_explore_returns.ipynb` | Notebook | The six graphs and tables, with a written reading under each |
| `reports/figures/03_*.png` | Images | 16 figures, also copied to `Quant_Momentum/Figures/03/` so Obsidian can embed them |
| `reports/tables/03_*.csv` | Tables | 10 tables: growth, volatility, moments, kurtosis before/after, class correlations, ACF (daily, 3-day, squared/absolute) |

**Addition to the plan:** a robust (heteroskedasticity-adjusted) ACF band, $\pm 1.96 \cdot \sqrt{\sum x_t^2 x_{t-k}^2}\,/\sum x_t^2$, drawn as dashed lines next to Bartlett's grey band, plus the ACF of $\lvert r\rvert$ in Graph 6. Both were added because the concept notes warned that clustering and fat tails distort the standard tools.

**Libraries** (already in `requirements.txt`): `statsmodels` for ACF and Ljung–Box, `scipy.stats` for Jarque–Bera, skewness, kurtosis and QQ plots, `seaborn` for the clustered heatmap, `matplotlib` for everything else.

**Leakage note:** this task is descriptive and uses the full sample, which is fine because nothing here is used to *trade*. Any number carried forward into a feature (e.g., a σ used for scaling) is recomputed in Task 04 using only past data.

---

## 10. Guide to run it (once built)

```
.venv\Scripts\activate
jupyter notebook notebooks/03_explore_returns.ipynb
```

Then **Run → Run All Cells**. It should take well under a minute; figures are written to `reports/figures/`.

---

## 11. What this task does *not* do

- No features, no targets, no signals. We only describe returns.
- No trading conclusions. A significant autocorrelation is a *hint* for feature design, not a strategy.
- No parameter tuning on these results. Choosing lookbacks purely to maximise an in-sample ACF would be **overfitting**; we use the results only for *direction* and *broad ranges*.

---

## 12. What comes next

- **Task 04, Feature Engineering:** momentum over lookbacks informed by Graph 5, time-varying σ informed by Graphs 2 and 6, vol-scaled momentum, volume ratio, relative-to-SPY return, and the 1-day / 3-day targets.
- **Task 05, Signal Analysis:** momentum vs next-day returns (scatter), quintile bucket returns, and the daily Information Coefficient (Spearman) over time.

---

## 13. Related notes

- [[02 - Data Cleaning]] — where the returns come from
- [[_Technical Learning - README]] — concept notes used here
- [[quant_equity_prediction_strategy_lab]] — scope doc §11 (exploratory analysis)
