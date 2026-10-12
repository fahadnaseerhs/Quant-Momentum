# Correlation and Diversification

**Prerequisites:** [[Volatility]], [[Return Distributions and Fat Tails]].

---

## 1. Intuition

You hold BTC and ETH. On the days BTC falls, does ETH usually fall too? If yes, owning both doesn't protect you much: they're close to being the same bet twice. If ETH tends to rise when BTC falls, the two cancel each other's swings and your total risk shrinks.

**Correlation measures how strongly two assets move together.** It determines whether holding more assets actually diversifies risk.

---

## 2. Covariance: the raw ingredient

$$\operatorname{Cov}(X, Y) = \frac{1}{T-1}\sum_{t=1}^{T}(x_t - \bar{x})(y_t - \bar{y})$$

**Intuition:** on each day, multiply "how far X was from its average" by "how far Y was from its average."
- Both above average, or both below → the product is **positive**.
- One above, one below → the product is **negative**.

Averaging over all days: positive covariance = they usually move together; negative = they usually move oppositely.

**Problem:** covariance's size depends on units and volatility. BTC–ETH covariance is large mostly because both are volatile, so the number isn't comparable across pairs.

---

## 3. Pearson correlation: covariance on a common scale

$$\rho_{XY} = \frac{\operatorname{Cov}(X,Y)}{s_X\, s_Y}$$

Dividing by both volatilities removes the scale. The result always lies between −1 and +1:

| $\rho$ | Meaning | Example you might expect |
|---|---|---|
| +1 | Move in perfect lockstep | An asset with itself |
| ≈ +0.8 | Strongly together | BTC and ETH |
| ≈ 0 | No linear relationship | Short Treasuries (SHY) and oil |
| < 0 | Tend to move oppositely | Long Treasuries (TLT) vs stocks, in *some* periods |
| −1 | Perfect mirror image | Rare in real assets |

**Three cautions:**
1. **Correlation ≠ causation.** BTC and MSTR are correlated because MSTR holds BTC, not because one "causes" the other on a given day.
2. **Pearson only sees straight-line relationships.** A strong curved relationship can show ρ ≈ 0.
3. **Pearson is sensitive to outliers** ([[Return Distributions and Fat Tails]] §7). One extreme day can shift ρ noticeably.

---

## 4. Spearman correlation: the robust alternative

**Intuition:** replace each value by its **rank** (smallest = 1, next = 2, …), then compute Pearson correlation on the ranks:

$$\rho^{S}_{XY} = \rho\big(\operatorname{rank}(x),\ \operatorname{rank}(y)\big)$$

- A +40% outlier becomes just "rank 1438", no more influential than any other top rank. That makes Spearman **robust to fat tails**.
- It captures any **monotonic** relationship (whenever X goes up, Y tends to go up), not only straight lines.

**Why it matters for this project:** in Task 05, the **Information Coefficient (IC)**, the main measure of a signal's quality, is exactly a Spearman correlation: on each day, between the assets' signal values and their subsequent returns.

---

## 5. The correlation matrix and heatmap

With 21 assets there are $21 \times 20 / 2 = 210$ distinct pairs. We arrange all pairwise correlations in a **21 × 21 correlation matrix**:
- **Symmetric**: $\rho_{ij} = \rho_{ji}$.
- **Diagonal = 1**: every asset is perfectly correlated with itself.

A **heatmap** colours each cell (e.g., red = strongly positive, white = zero, blue = negative), so 210 numbers can be read at a glance.

**Clustered ordering:** if assets are listed alphabetically, related assets end up scattered. **Hierarchical clustering** reorders rows and columns so that assets that move alike sit next to each other. Groups of related assets then show up as **bright blocks along the diagonal**, and each block is effectively one "theme" in the portfolio.

---

## 6. Diversification and the effective number of bets

**Intuition:** 20 assets that all move together are really one bet; 20 unrelated assets are 20 bets. Correlation decides where you sit between those extremes.

For an equally weighted portfolio of $N$ assets, each with volatility $\sigma$ and average pairwise correlation $\bar{\rho}$, the portfolio variance is:

$$\sigma_p^2 = \sigma^2\left(\frac{1-\bar{\rho}}{N} + \bar{\rho}\right)$$

- The first term, $\frac{1-\bar\rho}{N}$, is the part that **diversifies away** as $N$ grows.
- The second term, $\bar\rho$, **never disappears**. No matter how many assets you add, risk can't fall below $\bar\rho\,\sigma^2$.

**Effective number of independent bets.** $N$ fully independent assets would give variance $\sigma^2 / N$. Setting $\sigma^2/N_{eff}$ equal to the formula above and solving for $N_{eff}$:

$$N_{eff} = \frac{N}{1 + (N-1)\bar{\rho}}$$

| $N$ | $\bar\rho$ | $N_{eff}$ |
|---|---|---|
| 20 | 0.0 | 20 |
| 20 | 0.1 | 6.9 |
| 20 | 0.3 | **3.0** |
| 20 | 0.5 | 1.9 |

Even modest average correlation shrinks "20 assets" to a handful of true bets. (This is a simplification that assumes equal vol and equal correlations; the real matrix is lumpier, which is why the heatmap matters.)

---

## 7. Correlation changes over time

Like volatility ([[Volatility Clustering]]), correlations aren't constant.
- **Crisis effect:** in sell-offs, correlations across risky assets tend to **jump up** ("everything falls together"), just when diversification is needed most.
- **Regime shifts:** the stock–bond correlation was mostly negative for two decades, then turned **positive in 2022** when inflation hit both at once.

A **rolling correlation** (computed over the last 63 days, like rolling volatility) makes these shifts visible.

**Reminder from [[02 - Data Cleaning]] §6.3:** crypto's daily close is 8 pm New York, four hours after equities. News arriving in those four hours shows up in crypto "today" but in equities "tomorrow", which makes same-day crypto–equity correlations look **lower** than they really are.

---

## 8. Why this matters for cross-sectional momentum

Our method ranks all 20 assets on vol-scaled momentum and buys the top group. If assets form tight clusters (crypto, tech, energy, rates), then when crypto rallies, all five crypto tokens rise together, and "top 4" may simply mean "all crypto". The strategy then becomes an **asset-class timing bet** rather than a stock-picking one.

This isn't necessarily wrong, but we must know it. It determines whether later tasks should also test ranking **within** asset classes.

---

## 9. Summary

| Concept | Formula | Takeaway |
|---|---|---|
| Covariance | $\frac{1}{T-1}\sum(x-\bar x)(y-\bar y)$ | Do they move together? Scale-dependent |
| Pearson ρ | $\operatorname{Cov}/(s_X s_Y)$ | −1 to +1; linear; outlier-sensitive |
| Spearman ρ | Pearson on ranks | Robust to fat tails; basis of the IC |
| Correlation heatmap | 21 × 21 matrix, clustered | Blocks = hidden themes |
| Effective bets | $N/(1+(N-1)\bar\rho)$ | Correlation caps diversification |
| Rolling correlation | ρ over last 63 days | Correlations rise in crises |
