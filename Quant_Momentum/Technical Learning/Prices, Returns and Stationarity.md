# Prices, Returns and Stationarity

**Prerequisite:** the definitions of simple return $R_t$ and log return $r_t$ in [[02 - Data Cleaning]] §7.

---

## 1. Why we almost never analyse prices directly

**Intuition.** Suppose you're asked, "What is Bitcoin's typical price?" Over 2021–2026 the answer ranged from roughly \$16,000 to over \$100,000. An average of those numbers describes no actual period; it's a blend of different eras. The question "what is Bitcoin's typical *daily return*?" does have a sensible answer, because returns move around a fairly stable level (close to zero) in every era.

That difference has a name: **stationarity**.

## 2. Stationarity

A time series is **(weakly) stationary** if its basic statistical properties don't depend on *when* you look:

$$E[X_t] = \mu, \qquad \operatorname{Var}(X_t) = \sigma^2, \qquad \operatorname{Cov}(X_t, X_{t-k}) = \gamma_k \quad \text{for every } t$$

In words: the average, the spread, and the relationship between today and $k$ days ago are all constant over time.

| Series               | Stationary?       | Why                                                                                                                 |
| -------------------- | ----------------- | ------------------------------------------------------------------------------------------------------------------- |
| Prices $P_t$         | **No**            | They trend and wander. The 2021 average and the 2025 average are different.                                         |
| Returns $R_t$, $r_t$ | **Approximately** | They fluctuate around a stable mean. Their *variance* does change over time, though; see [[Volatility Clustering]]. |

**Why it matters.** Almost every statistical tool (averages, correlations, regressions, t-tests) assumes the data comes from one stable process. Applied to non-stationary prices, those tools give nonsense. A classic example is **spurious regression**: two unrelated assets that both trend upward will show a "strong" price correlation that means nothing. This is why every analysis in this project works on **returns**.

---

## 3. Growth of \$1 (the wealth index)

To *see* an asset's history without comparing raw prices (a \$400 ETF and a \$15 stock can't share an axis), we track what \$1 invested on day 0 would be worth:

$$W_t = \prod_{s=1}^{t} (1 + R_s), \qquad W_0 = 1$$

**Intuition:** each day, your money is multiplied by $(1 + \text{that day's return})$. $W_t = 2.5$ means \$1 became \$2.50, a +150% cumulative return.

Every asset starts at 1, so assets with very different prices become directly comparable.

---

## 4. Why the log scale

On an ordinary (linear) axis, a move from \$1 to \$2 looks tiny next to a move from \$10 to \$11, yet the first is +100% and the second only +10%. For investment returns, the **percentage** change is what matters.

On a **log-scale** axis, equal vertical distances mean equal **percentage** changes: 1→2, 2→4, and 10→20 all look the same height. Mathematically this follows from [[02 - Data Cleaning]] §7.2:

$$\ln W_t = \sum_{s=1}^{t} r_s$$

So on a log chart, the curve's height is the running *sum* of log returns, and its **slope is the growth rate**. A straight line means steady compound growth; a steeper line means faster growth.

**Rule:** always draw growth-of-\$1 charts on a log scale when the assets differ a lot in performance. With SOL and SHY on the same chart, anything else is unreadable.

---

## 5. Summary

| Concept | One-line takeaway |
|---|---|
| Stationarity | Statistics only make sense on series whose behaviour is stable over time → use returns, not prices. |
| Wealth index $W_t$ | Growth of \$1; puts every asset on the same starting line. |
| Log scale | Equal heights = equal percentage moves; slope = growth rate. |
