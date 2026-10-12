# Autocorrelation: Momentum vs Reversal

**Prerequisites:** [[Correlation and Diversification]] (Pearson correlation), [[Volatility Clustering]], [[Return Distributions and Fat Tails]].

This note measures the project's central question in its simplest form: **does an asset's recent return tell us anything about its next return?**

---

## 1. Intuition

[[Correlation and Diversification|Correlation]] compares two *different* series on the same days. **Autocorrelation** ("self-correlation") compares a series with **its own past**: today's return against yesterday's, or against the return $k$ days earlier.

- If up days tend to be followed by up days, the series has **positive** autocorrelation: **momentum**.
- If up days tend to be followed by down days, it has **negative** autocorrelation: **reversal** (mean reversion).
- If yesterday says nothing about today, autocorrelation is **zero**: a **random walk**.

---

## 2. The formula

The **lag** $k$ is how many days back we look. The sample autocorrelation at lag $k$ is:

$$\hat{\rho}_k = \frac{\sum_{t=k+1}^{T}(r_t - \bar{r})(r_{t-k} - \bar{r})}{\sum_{t=1}^{T}(r_t - \bar{r})^2}$$

It's the Pearson correlation between the series and a copy of itself shifted $k$ days. It lies between −1 and +1, and $\hat\rho_0 = 1$.

---

## 3. The ACF plot

The **autocorrelation function (ACF)** plot shows $\hat{\rho}_k$ for $k = 1, 2, \dots, K$ as vertical bars, together with a shaded **significance band** around zero.

- A bar **inside** the band: indistinguishable from zero, i.e. from luck.
- A bar **outside** the band: statistically significant at the 5% level.

### 3.1 Where the band comes from

If the returns were pure noise (independent, identically distributed), each $\hat\rho_k$ would be approximately normal with mean 0 and standard deviation $1/\sqrt{T}$ (**Bartlett's result**). A 95% band is therefore:

$$\pm \frac{1.96}{\sqrt{T}}$$

With $T \approx 1438$ daily returns: $\pm 1.96/\sqrt{1438} \approx \pm 0.052$.

### 3.2 Two cautions when reading the band

1. **Volatility clustering makes the band too narrow.** Bartlett's band assumes constant variance. With [[Volatility Clustering]], the true uncertainty is larger, so some bars that poke slightly outside ±0.052 are still noise. The **robust (heteroskedasticity-adjusted)** standard error is

$$\operatorname{se}_{robust}(\hat\rho_k) = \frac{\sqrt{\sum_t x_t^2\, x_{t-k}^2}}{\sum_t x_t^2}, \qquad x_t = r_t - \bar r$$

   **Intuition:** a product $x_t x_{t-k}$ from a stormy period is huge and noisy, and this formula lets stormy days widen the band instead of pretending all days are equally reliable. Under constant variance it reduces to Bartlett's $1/\sqrt{T}$. In [[03 - Exploring Returns]], SPY's 3-day "reversal" passed Bartlett's band but failed the robust one.
2. **Multiple testing.** At a 5% level, **1 in 20 tests crosses the band by pure chance.** Checking 10 lags for 20 assets is 200 tests, so about **10 "significant" bars are expected even if nothing is there.** One isolated significant bar is not a discovery. A *consistent pattern* (the same sign at the same lag across many related assets) is far more convincing.

---

## 4. Testing all lags at once: Ljung–Box

Instead of judging bars one by one, the **Ljung–Box test** asks: *are the first $m$ autocorrelations jointly zero?*

$$Q(m) = T(T+2)\sum_{k=1}^{m}\frac{\hat{\rho}_k^2}{T-k}$$

- $H_0$: no autocorrelation at lags 1 to $m$.
- Under $H_0$, $Q(m)$ follows a $\chi^2_m$ distribution.
- Large $Q$ / small p-value → reject: there is *some* serial dependence in the first $m$ lags.

Because it squares each $\hat\rho_k$, it detects dependence of **either sign** but doesn't tell you which. The ACF plot shows the direction.

---

## 5. From autocorrelation to forecasting power

If the lag-1 autocorrelation is $\rho_1$, the best *linear* forecast of tomorrow's return from today's is:

$$\hat{r}_{t+1} = \bar{r} + \rho_1\,(r_t - \bar{r})$$

The share of tomorrow's variance this forecast explains is:

$$R^2 = \rho_1^2$$

| $\rho_1$ | $R^2$ | Meaning |
|---|---|---|
| 0.30 | 9% | Very strong for finance; would be suspicious |
| 0.10 | 1% | Strong for daily returns |
| **0.05** | **0.25%** | Typical size of a "real" daily effect |
| 0.00 | 0% | Unpredictable |

**Intuition for daily trading:** even an $R^2$ of 0.25% can be economically meaningful. It applies to 20 assets on every one of ~250 days a year, and small edges add up across many bets. It can also be wiped out entirely by transaction costs. This is why the project judges signals by after-cost portfolio results, not by $R^2$.

---

## 6. Autocorrelation and the √time rule

[[Volatility]] §3 annualised volatility with $\sqrt{252}$, assuming independence. The **variance ratio** measures how wrong that is when returns are autocorrelated:

$$VR(q) = \frac{\operatorname{Var}(q\text{-day return})}{q \cdot \operatorname{Var}(1\text{-day return})} = 1 + 2\sum_{k=1}^{q-1}\left(1 - \frac{k}{q}\right)\rho_k$$

| $VR(q)$ | Meaning |
|---|---|
| = 1 | Random walk; √time rule is exact |
| > 1 | Positive autocorrelation (momentum); multi-day risk is **larger** than √time suggests |
| < 1 | Negative autocorrelation (reversal); multi-day risk is **smaller** |

---

## 7. What causes momentum or reversal?

| Effect | Sign | Mechanism |
|---|---|---|
| **Under-reaction** | + | Information spreads slowly; prices adjust over several days |
| **Herding / trend-following** | + | Rising prices attract buyers, who push prices higher |
| **Over-reaction** | − | Prices overshoot on news, then correct |
| **Liquidity provision** | − | Heavy selling pushes price below fair value temporarily; buyers step in next day |
| **Bid–ask bounce** | − (lag 1) | Closing trades randomly hit the bid or the ask, creating fake alternation. Tiny for our liquid assets, but real. |

**What research typically finds at daily horizons:**
- **Individual equities:** slight **reversal** over 1 day to 1 month (the "short-term reversal" effect).
- **Crypto:** evidence of short-horizon **momentum** in time series, though it varies by period.
- **Equity indices, bonds, commodities:** close to zero at lag 1; momentum appears at horizons of months.

So our universe may contain **both** behaviours. That's exactly why we measure before designing features.

---

## 8. Important trap: overlapping returns

For the **3-day target** $R_{t\to t+3}$, computed every day, consecutive values share days:

- $R_{t \to t+3}$ uses days $t+1, t+2, t+3$
- $R_{t+1 \to t+4}$ uses days $t+2, t+3, t+4$ → **2 of 3 days in common**

Even if daily returns were **pure noise**, overlapping $h$-day returns have autocorrelation:

$$\rho_k = 1 - \frac{k}{h} \quad (k < h), \qquad \rho_k = 0 \quad (k \ge h)$$

For $h = 3$: $\rho_1 = 0.67$ and $\rho_2 = 0.33$, **created entirely by the overlap**.

**Consequences:**
- **Never** read an ACF of overlapping multi-day returns as evidence of momentum. Measure 3-day autocorrelation on **non-overlapping** blocks (days 1–3, 4–6, …), which leaves ~479 observations and a wider band of $\pm 1.96/\sqrt{479} \approx \pm 0.09$.
- In regressions on overlapping targets, errors are autocorrelated by construction, so later tasks need **Newey–West** standard errors and a **≥ 3-day embargo** between training and test sets (see the daily-frequency decision).

---

## 9. Time-series vs cross-sectional momentum

The ACF measures **time-series** predictability: each asset against its own past. Our strategy is **cross-sectional**: it ranks assets *against each other*. The two are related but not identical. Cross-sectional profits also depend on **lead–lag effects** (asset A's move today predicting asset B's move tomorrow, the **cross-autocorrelation**) and on differences in average returns between assets (Lo & MacKinlay, 1990).

So the ACF is essential **context**, but not the final verdict. The direct test of our strategy is the ranking and bucket analysis in Task 05.

---

## 10. Summary

| Concept | Formula | Takeaway |
|---|---|---|
| Autocorrelation | $\hat\rho_k$ = corr($r_t$, $r_{t-k}$) | + momentum, − reversal, 0 random walk |
| Significance band | $\pm 1.96/\sqrt{T}$ ≈ ±0.052 | Too narrow under clustering; beware 200 tests |
| Ljung–Box | $T(T+2)\sum \hat\rho_k^2/(T-k)$ | Joint test of the first $m$ lags |
| Forecast power | $R^2 = \rho_1^2$ | Daily effects are tiny; costs decide |
| Variance ratio | $1 + 2\sum(1-k/q)\rho_k$ | ≠ 1 → √time rule is off |
| Overlap trap | $\rho_k = 1 - k/h$ from overlap alone | Use non-overlapping blocks for 3-day returns |
