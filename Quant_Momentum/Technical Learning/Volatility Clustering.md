# Volatility Clustering

**Prerequisites:** [[Volatility]]. The detection method in §3 uses autocorrelation, which is fully explained in [[Autocorrelation - Momentum vs Reversal]]; for this note, "autocorrelation" just means "how strongly a series is related to its own past".

---

## 1. Intuition

Think of the weather. A stormy day is usually followed by more stormy days, and calm weeks come in runs too. You can't say whether tomorrow's wind blows east or west, but you can say it will probably be **strong** if today was strong.

Markets behave the same way. The mathematician Benoît Mandelbrot noticed in the 1960s that large price changes tend to be followed by large changes, of **either sign**, and small changes by small changes. This is **volatility clustering**, one of the most reliable facts in all of finance.

**Key distinction:**
- The **direction** of tomorrow's return is very hard to predict.
- The **size** of tomorrow's return is quite predictable.

---

## 2. What it looks like

- **On a return chart:** quiet stretches of small bars, interrupted by bursts of tall bars (in our sample: mid-2022, April 2025, January 2026).
- **On a rolling-volatility chart** ([[Volatility]] §4): volatility doesn't hover around a fixed level. It rises in waves, stays high for weeks, and then decays slowly.

---

## 3. How to detect it statistically

If big moves follow big moves, then the **size** of today's return is correlated with the size of yesterday's, even if the sign isn't. So we measure size by squaring the return (or taking its absolute value), which throws away the sign:

$$\text{size}_t = r_t^2 \qquad \text{or} \qquad |r_t|$$

We then compute the autocorrelation of $r_t^2$ at lags $k = 1, 2, \dots, 20$:

| Pattern in the autocorrelation of $r_t^2$ | Meaning |
|---|---|
| All close to zero | No clustering: size is unpredictable (what a pure random walk would show) |
| **Positive and slowly decaying over many lags** | **Volatility clustering**: size today predicts size for days or weeks ahead |

What's typically found in real data: autocorrelation of $r_t$ close to 0, but autocorrelation of $r_t^2$ clearly positive (0.1–0.3) and still visible 20+ days out.

**Prefer $\lvert r_t\rvert$ when tails are fat.** Squaring lets one giant day dominate the whole calculation and can **hide** clustering. In [[03 - Exploring Returns]], META showed no clustering with $r_t^2$ but clear clustering with $\lvert r_t\rvert$; overall, 18 of 21 assets clustered by $\lvert r_t\rvert$ versus 8 of 21 by $r_t^2$.

**Why this is not a contradiction:** "unpredictable direction" and "predictable size" can both hold at once. A coin flip that decides the sign, multiplied by a slowly changing "storm level" that decides the size, produces exactly this pattern.

---

## 4. A model of it: GARCH (intuition only)

The standard model is **GARCH(1,1)** (Bollerslev, 1986). Today's variance depends on yesterday's shock and yesterday's variance:

$$\sigma_t^2 = \omega + \alpha\, r_{t-1}^2 + \beta\, \sigma_{t-1}^2$$

| Term | Meaning |
|---|---|
| $\omega$ | A small constant: the long-run "floor" level of variance |
| $\alpha\, r_{t-1}^2$ | **Reaction**: a big move yesterday raises today's variance |
| $\beta\, \sigma_{t-1}^2$ | **Memory**: high variance yesterday carries over into today |
| $\alpha + \beta$ | **Persistence**. Close to 1 (typically 0.95–0.99) means storms last a long time. |

**Connection:** the EWMA estimator from [[Volatility]] §5 is GARCH with $\omega = 0$, $\alpha = 1-\lambda$, $\beta = \lambda$. We won't fit GARCH models in this project; the point is to understand *why* a rolling or EWMA estimate is needed.

**Related effect, the leverage effect:** in equities, volatility tends to rise more after *falls* than after rises of the same size. Falling prices make companies riskier and scare investors. Crypto shows this less consistently.

---

## 5. Why it matters for this project

1. **One σ per asset is not enough.** If volatility changes over time, vol-scaled momentum must divide by a **recent** volatility estimate (rolling or EWMA), not by a single number for the whole sample.
2. **Vol-scaling partly "removes" the storms.** Dividing each return by the volatility estimated *up to the day before*,

$$z_t = \frac{r_t}{\hat{\sigma}_{t-1}}$$

   should produce a series that looks much calmer and closer to normal. If it does, much of the "fat tails" in raw returns ([[Return Distributions and Fat Tails]]) comes from mixing calm and stormy periods. Using $\hat\sigma_{t-1}$ rather than $\hat\sigma_t$ matters: $\hat\sigma_t$ already contains $r_t$, which would be leakage.
3. **Statistical tests need robust versions.** Standard t-tests and regression errors assume constant variance. With clustering, they understate uncertainty, so later tasks use robust (**Newey–West / HAC**) standard errors.
4. **Regimes.** Momentum strategies historically suffer sharp losses when volatility spikes after a crash ("momentum crashes"). Knowing where the high-vol periods are lets Task 11 test performance by regime.

---

## 6. Summary

| Concept | Takeaway |
|---|---|
| Volatility clustering | Size of moves is persistent; direction is not |
| Detection | Autocorrelation of $r_t^2$ or $\lvert r_t \rvert$: positive and slowly decaying |
| GARCH(1,1) | Variance = floor + reaction to yesterday's shock + memory of yesterday's variance |
| Consequence | Use time-varying σ; use robust standard errors; test performance by regime |
