# Graph and Table Labels

What every column name, axis label and visual mark in the project's outputs means. For the underlying concepts, follow the links to [[Glossary A-Z]].

**Units rule for all CSV tables:** numbers are stored as **decimals**. `0.169` means **16.9%**, and `-0.961` means **−96.1%**. Counts (`n_...`) and test statistics (`Q(5)`, `jb_stat`) are plain numbers.

---

## Marks that appear on many graphs

| Mark | Meaning |
|---|---|
| Grey dashed line labelled **SPY** | The benchmark (US stock market), drawn for comparison |
| Dotted vertical lines | Market events: **2022 bear market** (3 Jan 2022), **FTX collapse** (9 Nov 2022), **Tariff shock** (3 Apr 2025), **Gold crash** (30 Jan 2026) |
| X-axis: year labels + small `Apr Jul Oct` | Each year label marks 1 January; the small labels mark the start of each quarter |
| **log scale** on the y-axis | Equal heights = equal percentage moves → [[Glossary A-Z#Log scale]] |
| **% per year** | Annualised figure → [[Glossary A-Z#Annualise]] |
| Panel titles (Crypto, Tech, …) | The asset class from `src/universe.py` |

---

## Task 02 — `data/processed/cleaning_log.txt`

| Label | Meaning |
|---|---|
| `first` | First date with a valid price |
| `lead_nan` | Missing values *before* the first valid price (asset not yet listed) |
| `filled` | Missing values that were forward-filled (gaps ≤ 2 days) |
| `nan_left` | Missing values remaining after cleaning |
| `daily_sd` | Standard deviation of daily simple returns (daily volatility) |
| `ann_vol` | `daily_sd` × √252 (annual volatility) |
| `worst` / `best` | Largest one-day fall / rise |
| `long_gaps` | Gaps longer than 2 days, listed as (start, end, length) |

---

## Graph 1 — Growth of \$1

**Axes:** y = `value of $1 (log scale)`, x = date.

**Table `03_g1_growth.csv`:**

| Column | Meaning | Formula |
|---|---|---|
| `final_value_$` | What \$1 invested on the first day is worth at the end | $W_T$ |
| `total_return` | Total gain or loss over the whole period | $W_T - 1$ |
| `CAGR` | Constant yearly growth rate giving the same final value | $W_T^{252/T} - 1$ → [[Glossary A-Z#CAGR (Compound Annual Growth Rate)]] |
| `max_drawdown` | Worst fall from a previous peak | $\min_t (W_t / \max_{s\le t} W_s - 1)$ → [[Glossary A-Z#Drawdown / maximum drawdown]] |

---

## Graph 2 — Volatility over time

| Label | Meaning |
|---|---|
| **63-day rolling annualised volatility** | Volatility recomputed each day from the latest 63 trading days (≈ one quarter), × √252 → [[Glossary A-Z#Rolling (rolling window)]] |
| **EWMA, λ = 0.94** | Exponentially weighted volatility (recent days count more) → [[Glossary A-Z#EWMA volatility]] |
| **× SPY's volatility** | The asset's volatility divided by SPY's; 2× = twice as volatile as the market |
| "median within each class" | For each day, the middle value of the class members' ratios |

**Table `03_g2_vol_summary.csv`:**

| Column | Meaning |
|---|---|
| `min_63d_vol` / `median_63d_vol` / `max_63d_vol` | Calmest, typical and wildest 63-day annualised volatility |
| `max_over_min` | `max_63d_vol` ÷ `min_63d_vol`: how much volatility varied over time |
| `ratio_to_spy_min` / `ratio_to_spy_max` | Lowest and highest "× SPY's volatility" |

---

## Graph 3 — Distributions and fat tails

| Label                                                            | Meaning                                                                                               |
| ---------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| **z (standard deviations)**                                      | Return measured in standard deviations from the mean → [[Glossary A-Z#Standardised return (z-score)]] |
| Histogram **log y-axis**                                         | Bar heights on a log scale, so the rare tail days are visible                                         |
| Red curve **normal**                                             | The bell curve the data would follow if returns were normal                                           |
| QQ plot: **normal quantile** (x) vs **actual z** (y)             | Points on the red line = normal; bending away at the ends = fat tails → [[Glossary A-Z#QQ plot]]      |
| **raw** vs **vol-scaled** / "divided by previous day's EWMA vol" | Returns before and after dividing each day by the volatility estimated the day before                 |

**Table `03_g3_moments.csv`** (daily log returns):

| Column | Meaning |
|---|---|
| `ann_mean` | Average daily return × 252 |
| `ann_vol` | Daily volatility × √252 |
| `skew` | Skewness; negative = crash-prone left tail |
| `excess_kurt` | Excess kurtosis; 0 = normal, larger = fatter tails |
| `jb_stat` / `jb_pvalue` | Jarque–Bera normality test; p < 0.05 → not normal |
| `worst_z` / `best_z` | Worst and best day, in standard deviations |

**Table `03_g3_kurtosis_before_after_scaling.csv`** (same dates for both):

| Column | Meaning |
|---|---|
| `kurt_raw` / `kurt_scaled` | Excess kurtosis before / after volatility scaling |
| `skew_raw` / `skew_scaled` | Skewness before / after |
| `worst_z_raw` / `worst_z_scaled` | Worst day in σ units, before / after |
| `kurt_reduction` | 1 − `kurt_scaled` / `kurt_raw`; 0.73 = tails 73% thinner after scaling; **negative = tails got fatter** |

---

## Graph 4 — Correlation

| Label | Meaning |
|---|---|
| Heatmap colours | Red = move together, white = unrelated, blue = move oppositely |
| Numbers in cells | Pearson correlation between the row and column assets |
| Tree on the edges (**dendrogram**) | Shows which assets were grouped; branches that join low down = very similar |
| **Pearson − Spearman** | Difference between the two correlations; large values = the pair is driven by a few extreme days |
| Class block matrix | Average correlation **within** a class (diagonal) and **between** classes (off-diagonal) |
| **63-day rolling average correlation** | Average of all pairwise correlations among the 20 tradeables, over the latest 63 days |
| **full-sample average** | The same average over the whole 2021–2026 period (0.21) |
| Printed: **effective number of bets** | $N/(1+(N-1)\bar\rho)$ → [[Glossary A-Z#Effective number of bets (N_eff)]] |

---

## Graph 5 — Autocorrelation of returns

| Label | Meaning |
|---|---|
| Green / red bars | Positive (momentum-like) / negative (reversal-like) autocorrelation at that lag |
| **Grey band** | Bartlett band ±1.96/√T; bars inside = indistinguishable from luck |
| **Dashed lines** | Robust band (allows for volatility clustering); usually a bit wider |
| **lag (days)** | How many days back: lag 1 = yesterday vs today |
| **lag (3-day blocks)** | Lag measured in non-overlapping 3-day blocks |

**Table `03_g5_acf_daily_table.csv`:**

| Column | Meaning |
|---|---|
| `rho1`, `rho2`, `rho3` | Autocorrelation at lags 1, 2, 3 days |
| `robust_t_rho1` | `rho1` ÷ its robust standard error; beyond ±1.96 = significant |
| `Q(5)`, `Q(10)` | Ljung–Box statistic over the first 5 / 10 lags |
| `p(5)`, `p(10)` | Their p-values; < 0.05 = some dependence (can be too optimistic under clustering) |
| `VR(3)` | Variance ratio over 3 days; 1 = random walk, < 1 = reversal, > 1 = momentum |
| `n_sig_bartlett` / `n_sig_robust` | How many of the 10 lags fall outside the Bartlett / robust band |

**Table `03_g5_acf_by_class.csv`:** `mean_rho1` (class average of `rho1`), `share_rho1_negative` (fraction of the class with `rho1` < 0), `mean_VR3`, and `sig_bartlett` / `sig_robust` (total significant bars in the class).

**Table `03_g5_acf_3day_table.csv`:** `rho1_3d`, `rho2_3d` (autocorrelation between consecutive / every-other 3-day blocks), `robust_t_rho1_3d`, and the significance counts (out of 5 lags).

**Overlap-trap chart:** blue = overlapping 3-day returns, grey = what pure noise gives purely from the overlap ($1 - k/3$), orange = non-overlapping blocks (the honest measure).

---

## Graph 6 — Autocorrelation of squared and absolute returns

| Label | Meaning |
|---|---|
| Purple bars | Autocorrelation of **squared** returns $r^2$ (move size) |
| **absolute returns \|r\|** | Size measured without squaring; less dominated by single huge days |
| **median ACF across 21 assets** | For each lag, the middle value across all assets |

**Table `03_g6_acf_squared_table.csv`:**

| Column | Meaning |
|---|---|
| `acf_sq_lag1` … `acf_sq_lag20` | Autocorrelation of $r^2$ at lags 1, 5, 10, 20 |
| `n_lags_sig_of_20` | How many of 20 lags of $r^2$ are significantly positive |
| `acf_abs_lag1`, `acf_abs_lag20` | Autocorrelation of $\lvert r\rvert$ at lags 1 and 20 |
| `n_abs_lags_sig_of_20` | How many of 20 lags of $\lvert r\rvert$ are significantly positive (≥ 10 = clear clustering) |
