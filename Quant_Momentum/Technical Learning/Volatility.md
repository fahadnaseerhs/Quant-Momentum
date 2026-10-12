# Volatility

**Prerequisite:** [[Prices, Returns and Stationarity]].

---

## 1. Intuition

Two assets both average +0.05% per day. Asset A moves between −0.5% and +0.5% on almost every day. Asset B regularly jumps ±8%. They have the same average, but holding B is a completely different experience: bigger swings, bigger possible losses, harder to sleep.

**Volatility measures how widely returns spread around their average.** In finance it is the most common single number for "risk".

---

## 2. Building it up from basic statistics

**Sample mean** (the typical daily return):

$$\bar{r} = \frac{1}{T} \sum_{t=1}^{T} r_t$$

**Sample variance** (average squared distance from the mean):

$$s^2 = \frac{1}{T-1} \sum_{t=1}^{T} (r_t - \bar{r})^2$$

- **Why square the deviations?** Positive and negative deviations would otherwise cancel out, and squaring makes every deviation count as a positive amount. It also makes large deviations count much more than small ones: a 4% deviation contributes 16 times as much as a 1% deviation.
- **Why divide by $T-1$, not $T$?** We measure distances from $\bar{r}$, which was itself computed from the same data, so it sits slightly closer to the data than the true mean does. Dividing by $T-1$ corrects this small downward bias (called **Bessel's correction**). With $T \approx 1438$ the difference is negligible.

**Standard deviation = volatility:**

$$\sigma = \sqrt{s^2}$$

Taking the square root returns to the original units (percent per day), so $\sigma$ can be read directly: "a typical day moves about $\sigma$ away from the average."

**Example from our data** (cleaning log, [[02 - Data Cleaning]] §11): SPY's daily σ is 1.05%, and AVAX's is 7.28%.

---

## 3. Daily to annual: the square-root-of-time rule

Volatility is usually quoted **per year** so that different frequencies can be compared. The conversion is:

$$\sigma_{annual} = \sigma_{daily} \times \sqrt{252}$$

**Why √252 and not 252?** Suppose daily returns are independent, each with variance $\sigma_d^2$. A year's return is (approximately, using log returns) the **sum** of 252 daily returns. For a sum of independent variables, **variances add**:

$$\operatorname{Var}\left(\sum_{t=1}^{252} r_t\right) = 252\,\sigma_d^2 \quad\Longrightarrow\quad \sigma_{annual} = \sqrt{252}\,\sigma_d$$

**Intuition:** good and bad days partly cancel each other out, so risk grows with the *square root* of time, not proportionally. Over 252 days, risk grows about 16×, not 252×.

SPY: 1.05% × √252 ≈ 16.7% per year, matching the cleaning log.

**Caveat:** the rule assumes returns are **independent** (no autocorrelation). If up days tend to follow up days, risk compounds faster than √time; if moves tend to reverse, it compounds slower. [[Autocorrelation - Momentum vs Reversal]] §6 gives the exact correction.

---

## 4. Rolling volatility: volatility that changes over time

A single σ for 2021–2026 hides a lot: 2022 and April 2025 were far wilder than mid-2023. To see volatility **change**, we compute it over a moving window of the most recent $n$ days:

$$\hat{\sigma}_t^{(n)} = \sqrt{\frac{1}{n-1} \sum_{s=t-n+1}^{t} \left(r_s - \bar{r}_{t}^{(n)}\right)^2}$$

where $\bar{r}_t^{(n)}$ is the average over the same window. On day $t$ it uses only days $t-n+1, \dots, t$: **no future data**, so it's leakage-safe.

**Choosing the window $n$** is a trade-off:

| Window | Trading days | Reacts to change | Noise | Use |
|---|---|---|---|---|
| 1 month | 21 | Fast | High | Short-term risk |
| 1 quarter | 63 | Medium | Medium | **Our default for plots** |
| 1 year | 252 | Slow | Low | Long-run comparison |

**The "ghost" effect:** a shock keeps full weight for exactly $n$ days, then vanishes all at once, so rolling volatility shows a flat-topped block that drops off a cliff $n$ days after the event, even if markets calmed down long before. EWMA (§5) avoids this.

**Practical simplification:** for daily data, the mean $\bar{r}$ (≈ 0.05%) is tiny next to σ (≈ 1–7%), so practitioners often set it to zero: $\hat{\sigma}_t^2 \approx \frac{1}{n}\sum r_s^2$. This removes a noisy estimate and barely changes the result.

---

## 5. Exponentially weighted volatility (EWMA)

A rolling window treats a return from 62 days ago as equally important as yesterday's, then drops it completely on day 64. That's a crude rule. **EWMA** weights recent days more and fades old days out gradually:

$$\hat{\sigma}_t^2 = \lambda\,\hat{\sigma}_{t-1}^2 + (1-\lambda)\,r_t^2$$

**Intuition:** today's variance estimate = mostly yesterday's estimate ($\lambda$) + a little of today's squared return ($1-\lambda$). A big shock raises the estimate immediately, and the effect then decays day by day.

- $\lambda = 0.94$ is the classic **RiskMetrics** choice for daily data (J.P. Morgan, 1994).
- **Half-life** (days until a shock's weight halves): $\ln(0.5)/\ln(\lambda) \approx 11$ days for $\lambda = 0.94$.

EWMA is a candidate for the σ in our volatility-scaled momentum (Task 04), since it reacts faster than a 63-day window.

---

## 6. Why volatility matters for this project

1. **Comparing assets fairly.** Our universe's annual vol ranges from 1.9% (SHY) to 116% (AVAX). A +10% move is a normal day for AVAX and a once-in-a-decade event for SHY. Dividing by volatility converts returns to a common unit: **"how many standard deviations did it move?"**

$$\text{vol-scaled momentum}_{i,t} = \frac{M_{i,t}}{\hat{\sigma}_{i,t}}$$

   This is the ranking signal chosen in the universe decision. A result of 2 means "the asset rose two of its own standard deviations", which is comparable across BTC and TLT.

2. **Risk control.** Vol-scaling automatically shrinks the signal in turbulent periods and enlarges it in calm ones.

3. **Annualised volatility is the denominator of the Sharpe ratio** (Task 09+), the main risk-adjusted performance measure.

---

## 7. Summary

| Concept | Formula | Takeaway |
|---|---|---|
| Volatility | $\sigma = \sqrt{\frac{1}{T-1}\sum (r_t-\bar r)^2}$ | Typical size of a day's move |
| Annualising | $\sigma_{annual} = \sigma_{daily}\sqrt{252}$ | Risk grows with √time if returns are independent |
| Rolling vol | σ over the last $n$ days | Shows volatility changing; window = speed vs noise |
| EWMA vol | $\hat\sigma_t^2 = \lambda\hat\sigma_{t-1}^2 + (1-\lambda)r_t^2$ | Recent days weigh more; half-life ≈ 11 days at λ = 0.94 |
| Vol-scaling | $M/\hat\sigma$ | Puts all assets on one "standard deviations" scale |
