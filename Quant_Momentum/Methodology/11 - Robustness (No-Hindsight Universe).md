# 11 — Robustness: a Universe Chosen Without Hindsight

**Follows:** [[10 - Costs and Combined Book]] · **Code:** `scripts/11_robust_etf.py` (download + run) · **Data:** `data/etf/`
**Graphs:** [[Task 10 and 11 - Graph Explanation]] · **Status:** [[Task Log]]

---

## 1. The question

> **"Do the results survive on assets we did *not* pick knowing how they turned out?"**

The project's 20 assets were chosen in 2026: NVDA, MSTR, BTC and SOL are known winners. That flatters everything that holds them.

## 2. Method

**Universe: 23 broad ETFs** that any investor could have listed in 2005. No single stocks, no crypto.

| class | funds |
|---|---|
| equity index | SPY, QQQ, IWM, EFA, EEM |
| US sectors | XLB, XLE, XLF, XLI, XLK, XLP, XLU, XLV, XLY |
| bonds | SHY, IEF, TLT, LQD, TIP |
| commodities | GLD, DBC, USO |
| real estate | VNQ |

**Everything is frozen** from earlier tasks: the same features and model (Task 07), the same walk-forward, **weekly rebalancing and a 30% trend share** (Task 10 design period), and 10 bps costs. **Nothing is re-tuned.** Data runs 2004-01 → 2026-10 with the same cleaning rules. All funds exist from 2004 except GLD (2004-11), VNQ (2004-09), DBC and USO (2006).

## 3. Results

### 3.1 Prediction (h = 21)

| | IC OOS | IC non-overlap (t) | hit rate | always-long hit |
|---|---|---|---|---|
| model | **0.008** | 0.010 (t = 0.73) | 54.2% | 60.5% |
| rule | 0.020 | −0.002 (t = −0.11) | 54.4% | 60.5% |

**The trend signal is gone on this universe.** Compare IC 0.052 (t = 2.9) on the hindsight universe.

**Per fund (OOS IC):**
- **Positive:** SHY +0.21, DBC +0.07, GLD, EEM, EFA, TIP, LQD, IEF, TLT (+0.03 to +0.04).
- **Negative:** **every US equity fund** except XLF: XLP −0.14, XLU −0.11, XLV −0.09, IWM, XLK, QQQ, SPY, and others.

This is the same pattern as [[07c - Long-History Re-test]]: trend works on bonds, commodities and non-US equity, and fails on US stocks. Here **12 of the 23 funds are US equity**, so they swamp the macro trends.

### 3.2 Books (net of 10 bps, weekly)

| book | Sharpe design | Sharpe holdout | **Sharpe full** | ann. return | **max DD** |
|---|---|---|---|---|---|
| **long (risk-sized)** | 0.69 | 0.97 | **0.83** (t = 3.8) | 8.0% | **−23.7%** |
| trend model | 0.25 | −0.06 | 0.11 (t = 0.5) | 0.8% | −24.6% |
| combined 70/30 | 0.71 | 0.81 | 0.76 | 5.8% | −15.4% |
| SPY | 0.45 | 0.97 | 0.69 | 13.1% | −55.2% |

### 3.3 Crashes

| | long | trend | combined | SPY |
|---|---|---|---|---|
| 2008-01 → 2009-03 | −17.1% | **+1.5%** | −11.5% | −42.3% |
| 2020 Feb–Mar | −14.3% | −8.7% | −12.6% | −26.5% |
| 2022 | −10.6% | −9.6% | −9.9% | −19.0% |

**Why trend lost in 2022, a classic trend year.** This was checked, not assumed. Short bonds made money (TLT +1.3%, IEF +0.5%) and long commodities made money (USO +1.0%, DBC +0.9%). But each fund holds at most 1/N of the book, so these winners were small. Meanwhile the 12 US equity funds together lost about 14.5% (XLE was their only winner), mostly in the July and Oct–Nov bear-market rallies, when the shorts got squeezed.

## 4. Verdict — the honest project-level answer

1. **What is robust:** the **risk-sized, diversified long book**. On both universes it beats SPY on a risk-adjusted basis: Sharpe 0.83 vs 0.69 here (t = 3.8), with a worst loss of −24% vs −55%. That is **diversification + volatility sizing**, not return prediction.
2. **What is fragile:** **trend as a return predictor.** On the hindsight universe it worked (helped by crypto, SHY and commodities). On a neutral universe it's about zero overall. Across both universes it consistently works on **bonds and commodities** and consistently fails on **US equities**.
3. **The combined book** still cuts drawdowns (−15% vs −24%), but here it costs Sharpe (0.76 vs 0.83). So trend is an insurance policy whose cost depends on the universe.
4. **Volatility forecasting and weekly rebalancing** carry over without problems.

## 5. Hypothesis for a future test (must be pre-committed, not tuned here)

Trend failed partly because of **how risk is split**: equal capital per fund lets 12 correlated US-equity funds dominate. The standard fix in the literature is an **equal risk budget per asset class**: equities, bonds, commodities and real estate each get 1/4 of the risk. That is a new test and should be judged on its own holdout. Choosing it because of what we saw here would be fitting to this result.
