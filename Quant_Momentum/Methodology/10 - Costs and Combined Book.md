# 10 — Trading Costs and the Combined Book

**Follows:** [[07c - Long-History Re-test]], where costs ate about 45% of trend's return and a 25% trend mix looked useful (exploratory).
**Code:** `src/portfolio.py` (`target_books`, `simulate`) · `scripts/10_costs_combined.py`
**Graphs:** [[Task 10 and 11 - Graph Explanation]] · **Status:** [[Task Log]] · **Robustness:** [[11 - Robustness (No-Hindsight Universe)]]

---

## 1. The questions

1. **How much of the trend edge can we keep by trading less often?**
2. **What is the right mix of the risk-sized long book and trend, chosen fairly?**

## 2. Method

### 2.1 Realistic simulation (new)

Earlier tasks assumed the book is reset to its target weights every day. Now:
- On a **rebalance day**, trade from the current weights to the target. Cost = 10 bps × Σ|trade|.
- **Between rebalances, positions drift with prices** and nothing is traded:
$$w_{i,t+1} = \frac{w_{i,t}(1+r_{i,t})}{1 + \sum_j w_{j,t} r_{j,t}}$$

### 2.2 Fair split: design vs holdout (fixed before running)

| Period | Dates | Used for |
|---|---|---|
| **design** | 2005-08 → 2015-12 | making every choice |
| **holdout** | 2016-01 → 2026-10 | reporting only; the choices never saw it |

**Choices, made on the design period only:**
- Rebalance every **k ∈ {1, 5, 21}** days → pick the best trend-model net Sharpe at 10 bps. **Result: k\* = 5 (weekly).**
- Trend share **a ∈ {0, 10, …, 50%}** of the combined book → pick the best net Sharpe. **Result: a\* = 30%.**

The combined book nets the two sleeves' targets, $W = (1-a)\,W_\text{long} + a\,W_\text{trend}$, and is simulated as one book, so opposite trades cancel.

## 3. Results

### 3.1 Trading less often (trend model, full 2005–26)

| rebalance | trades per year (× book) | cost per year @10 bps | net Sharpe @5 / 10 / 20 bps | design → holdout Sharpe @10 bps |
|---|---|---|---|---|
| daily | 22.9 | 2.3% | 0.56 / 0.39 / 0.07 | 0.19 → 0.61 |
| **weekly** | 10.4 | 1.0% | 0.60 / **0.53** / 0.37 | **0.52 → 0.53** |
| monthly | 4.6 | 0.5% | 0.59 / 0.56 / 0.49 | 0.30 → 0.84 |

- **Weekly is the stable choice.** It's nearly identical in both halves (0.52 → 0.53). Monthly is cheapest but swings a lot between periods, because results depend on *which day* of the month you trade.
- Weekly trading **cuts the cost drag from 2.3% to 1.0% a year**, and net Sharpe goes from 0.39 to 0.53.
- The long book trades very little (1–4× a year), so costs barely matter for it.

### 3.2 Final books (net of 10 bps, weekly)

| book | Sharpe design | **Sharpe holdout** | ann. return (holdout) | ann. vol (holdout) | **max DD (holdout)** |
|---|---|---|---|---|---|
| long (risk-sized) | 0.94 | **1.52** | 14.4% | 9.5% | −17.5% |
| trend model | 0.52 | 0.53 | 3.6% | 6.9% | −13.5% |
| trend rule | 0.38 | 0.66 | 4.5% | 6.9% | −13.5% |
| **combined 70/30** | 1.00 | **1.51** | 11.1% | 7.4% | **−11.1%** |
| SPY | 0.45 | 0.97 | 17.1% | 17.7% | −33.7% |

**Holdout verdict:** the combined book has the **same Sharpe as long-only (1.51 vs 1.52)** with a **37% smaller worst drawdown (−11.1% vs −17.5%)**. It gives up some raw return (11.1% vs 14.4%) because it carries less risk. Scaled up to the same volatility (×1.28), its worst drawdown would still be about −14% vs −17.5%.

## 4. Verdict

1. **Trade weekly.** It keeps most of the trend edge, halves the costs, and is stable across both halves.
2. **On this universe, a 30% trend sleeve is a drawdown reducer, not a Sharpe booster**, and the holdout confirmed it.
3. **This universe was picked with hindsight**, so these numbers need the robustness check → [[11 - Robustness (No-Hindsight Universe)]].
