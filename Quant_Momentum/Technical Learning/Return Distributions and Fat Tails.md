# Return Distributions and Fat Tails

**Prerequisites:** [[Volatility]], [[Volatility Clustering]].

---

## 1. Intuition: what a distribution is

Take all ~1438 of SPY's daily returns and sort them into bins: how many days fell between 0% and +0.5%, how many between +0.5% and +1%, and so on. The shape you get, most days near zero and a few days far out, is the **distribution** of returns. It answers: *how often does a move of each size happen?*

For risk and for statistics, the tails of the distribution (the rare, extreme days) matter most, because that's where large losses happen.

---

## 2. The normal distribution: the benchmark

The **normal (Gaussian) distribution** is the familiar bell curve. It's fully described by two numbers, its mean $\mu$ and standard deviation $\sigma$:

$$f(x) = \frac{1}{\sigma\sqrt{2\pi}}\, \exp\!\left(-\frac{(x-\mu)^2}{2\sigma^2}\right)$$

Its best-known property is the **68–95–99.7 rule**:

| Range | Share of observations |
|---|---|
| $\mu \pm 1\sigma$ | 68.3% |
| $\mu \pm 2\sigma$ | 95.4% |
| $\mu \pm 3\sigma$ | 99.7% |

A move of **4σ** or more (in either direction) should happen about once every 60 years of trading days, and one of **5σ** or more about once every 7,000 years.

**Why it's the default assumption:** by the **Central Limit Theorem**, the sum of many small independent effects tends toward a normal shape. Many textbook formulas (t-tests, confidence intervals, classic risk models) assume normality.

**Why it's only a benchmark:** real returns break the assumption. We use the normal curve as a *reference* to measure how far reality departs from it. (Scope doc §11.1 says the same.)

---

## 3. Standardising: the z-score

To compare shapes across assets with very different volatility, we convert each return into "how many standard deviations from the mean":

$$z_t = \frac{r_t - \bar{r}}{s}$$

After standardising, every asset has mean 0 and σ = 1, so SPY's and AVAX's distributions can be overlaid directly.

**Example from our data:** SPY's worst day was −5.9%, and its daily σ is 1.05%, so $z \approx -5.6$. Under a normal distribution, a day that bad has a probability of about $10^{-8}$, roughly **once in 400,000 years** of trading. It happened on 4 April 2025. This is what "fat tails" means in practice.

---

## 4. Describing the shape: moments

The mean and variance are the first two **moments** of a distribution. The third and fourth describe its shape.

### 4.1 Skewness: is the distribution lopsided?

$$\hat{S} = \frac{1}{T}\sum_{t=1}^{T} z_t^3$$

**Intuition:** cubing keeps the sign (a −3 becomes −27, a +3 becomes +27) and exaggerates big values. If large negative days outweigh large positive ones, the sum is negative.

| Skewness | Shape | Finance meaning |
|---|---|---|
| $\approx 0$ | Symmetric | Big up-days and big down-days equally likely |
| $< 0$ | Long **left** tail | Many small gains, occasional crashes. Typical of equity indices ("up the stairs, down the elevator"). |
| $> 0$ | Long **right** tail | Many small losses, occasional huge gains. Common in lottery-like assets and some crypto periods. |

### 4.2 Kurtosis: how heavy are the tails?

$$\hat{K} = \frac{1}{T}\sum_{t=1}^{T} z_t^4$$

**Intuition:** raising to the 4th power makes extreme values dominate completely. A 1σ day contributes 1, a 3σ day 81, and a 5σ day 625. So kurtosis is essentially a measure of **how much the extremes matter**.

- A normal distribution has $K = 3$.
- **Excess kurtosis** $= K - 3$, so the normal distribution scores 0.

| Excess kurtosis | Name | Shape vs normal |
|---|---|---|
| 0 | Mesokurtic | Normal-like |
| **> 0** | **Leptokurtic ("fat-tailed")** | Taller, narrower peak **and** fatter tails, with fewer "medium" days. Typical for daily returns (often 3–20+). |
| < 0 | Platykurtic | Thin tails; rare in finance |

**Fat tails** means that extreme days happen far more often than the normal curve predicts. It isn't only that the tails are "a bit wider": the peak is also taller, because the variance gets "spent" on a few huge days while most days are quieter than normal.

---

## 5. Testing normality formally: Jarque–Bera

The **Jarque–Bera (JB) test** combines skewness and excess kurtosis into one number:

$$JB = \frac{T}{6}\left(\hat{S}^2 + \frac{(\hat{K}-3)^2}{4}\right)$$

- If returns really were normal, $JB$ would follow a **chi-squared distribution with 2 degrees of freedom**, $\chi^2_2$.
- The 5% critical value is **5.99**. $JB > 5.99$ → reject normality.
- **Null hypothesis** $H_0$: the data is normal. A tiny **p-value** (probability of a result this extreme if $H_0$ were true) means we reject $H_0$.

With $T \approx 1438$, even small departures are detected, so expect enormous JB values (hundreds or thousands) for almost every asset. The test mostly confirms what the plots show. The *size* of skew and kurtosis is more informative than the p-value.

---

## 6. Two ways to see the distribution

### 6.1 Histogram with a normal overlay

- Bars: the share of days in each return bin (of standardised returns $z_t$).
- Curve: the normal density with the same mean and σ.

**How to read it:**

| Region | Fat-tailed data looks like… |
|---|---|
| Centre (near 0) | Bars **taller** than the curve |
| "Shoulders" (±1 to ±2σ) | Bars **shorter** than the curve |
| Tails (beyond ±3σ) | Bars exist where the curve is essentially zero |

Weakness: the tails hold only a handful of days, so they are nearly invisible on a histogram. That's why we also use a QQ plot.

### 6.2 QQ plot (quantile–quantile plot)

**Intuition:** line up the data's sorted values against the values a normal distribution *would* produce at the same positions, and see if they match.

**Construction:**
1. Sort the standardised returns: $z_{(1)} \le z_{(2)} \le \dots \le z_{(T)}$.
2. For the $j$-th value, compute the matching normal quantile $q_j = \Phi^{-1}\!\left(\frac{j - 0.5}{T}\right)$, where $\Phi^{-1}$ is the inverse of the normal cumulative distribution (the value below which a given share of a normal distribution lies).
3. Plot the points $(q_j,\ z_{(j)})$ and draw the 45° line $y = x$.

**How to read it:**

| Pattern | Meaning |
|---|---|
| Points on the 45° line | Normal |
| **S-shape**: left end bends **below** the line, right end bends **above** | **Fat tails**: the worst days are worse, and the best days better, than normal predicts |
| Only the left end bends away | Negative skew (crash risk) |
| Only the right end bends away | Positive skew |

The QQ plot magnifies the tails, which is exactly where the histogram is weakest.

---

## 7. Why this matters for the project

1. **Outliers dominate averages and regressions.** A single ±30% crypto day can move a mean or a regression coefficient more than hundreds of normal days combined. Later tasks therefore favour **rank-based** measures (Spearman correlation, see [[Correlation and Diversification]]) and may **winsorise** (cap extreme values at, e.g., the 1st and 99th percentile) *features*. Targets are never capped when measuring P&L.
2. **Statistical tests need care.** With fat tails, the Central Limit Theorem needs more data before averages look normal, so p-values are less reliable at small samples.
3. **Risk is understated by normal-based numbers.** Any "worst expected loss" computed from σ alone underestimates crash risk.
4. **Link to clustering.** If returns divided by *lagged* rolling volatility ([[Volatility Clustering]] §5) show much lower kurtosis, then much of the fat-tailedness comes from switching between calm and stormy regimes, and vol-scaling handles a large part of the problem.

---

## 8. Summary

| Concept | Formula | Takeaway |
|---|---|---|
| Normal distribution | $f(x)$ above | The reference shape; 68–95–99.7 rule |
| z-score | $(r-\bar r)/s$ | Common "standard deviations" scale |
| Skewness | $\frac1T\sum z^3$ | < 0 = crash-prone left tail |
| Excess kurtosis | $\frac1T\sum z^4 - 3$ | > 0 = fat tails; extremes far more common than normal |
| Jarque–Bera | $\frac{T}{6}(S^2 + (K-3)^2/4)$ | > 5.99 → not normal |
| QQ plot | sorted data vs normal quantiles | S-shape = fat tails |
