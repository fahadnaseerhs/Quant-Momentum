# Path A — Stock Selection (cross-sectional ranking)

**Status:** A1 tested (2026-10-11): **nothing passed** (near-miss = sector bet). A2 (fundamentals) is next and needs an SEC contact in `.env`. · **Why this path:** [[Prediction Attempts Log]] · **Terminal:** [[QM Terminal - Plan]]

## The question changes, the pass bar doesn't
Old question: "will these 20 assets go up next month?" That's about 20 bets a month, which is too few.
**New question: "which S&P 500 stocks will do better than the others next month?"** That's about 500 bets a month, or around 120,000 stock-months since 2005. Professional equity funds work this way: a small skill spread over many bets.

## ❌ A1 RESULT (2026-10-11): nothing passes. Closest near-miss = a sector bet

**Code:** `src/sp500.py` (membership as of each date) · `scripts/15_sp500_data.py` (prices) · `scripts/16_stock_selection_lab.py` (test) · tables `reports/tables/16_stock_lab*.csv`

**Data built:**
- Membership as of each date, rebuilt from Wikipedia's change history. The live page lost its change table in Aug 2026, so it comes from **page version 1368675864 (10 Aug 2026)**, with Aug–Oct patched from today's list.
- 849 tickers needed, **642 found on Yahoo**. **Coverage of members at each date:** 62% (2005) → 77% (2015) → 80% (2016) → 99% (2026). The missing ones are mostly stocks later acquired or bankrupt, which is survivorship bias, worst in the design period.
- Panel: **103,930 stock-months**, 261 months, 599 stocks. Known flaw: renamed tickers (e.g. FB → META) look like members before they joined.

**HOLDOUT 2016–2026:**

| Candidate | Rank IC | IC t | Top fifth vs avg stock (after costs) | Pass? |
|---|---|---|---|---|
| S1 momentum 12-1 | −0.006 | −0.3 | +0.4%/yr | ❌ |
| S2 short-term reversal | +0.007 | +0.4 | −0.7%/yr | ❌ |
| S3 low volatility | −0.012 | −0.5 | −3.8%/yr | ❌ |
| S4 low beta | −0.028 | −1.1 | −4.6%/yr | ❌ |
| S5 lottery (MAX) | −0.010 | −0.6 | −4.7%/yr | ❌ |
| S6 52-week high | −0.011 | −0.6 | −2.8%/yr | ❌ |
| C1 z-average | −0.012 | −0.5 | −4.4%/yr | ❌ |
| C2 ridge | +0.028 | +1.8 | +5.3%/yr (t 1.8) | ❌ (design IC < 0) |
| **C3 boosted trees** | **+0.031** | **+2.5** | **+4.3%/yr (t 2.1)** | ❌ **near-miss** (bar is 2.6) |
| controls (shuffled / random) | ≈ 0 | +0.4 / −1.6 | −1.5 / −3.0%/yr (costs) | — |

**Why the near-miss isn't real stock-picking (diagnostic, after the verdict):**
- C3's IC **within sectors is 0.0006 (t 0.06)**. Its whole edge is sector tilt: the top fifth held 25% IT vs 11% in the universe, and 4% financials vs 14%.
- "Buy tech" won 2016–26. On top of that, the sector labels are **today's** GICS sectors (hindsight).
- So nothing is carried forward to paper trading.

**Why the published signals failed here:** large-cap US stocks are the most crowded market in the world. Momentum crashed in 2009 and hasn't recovered in large caps. Low-vol and low-beta lost because 2016–26 was led by high-beta tech. This matches what other researchers report: these effects have decayed since publication.

**Lessons for A2 (to be fixed before the A2 run):**
1. Make every score **sector-neutral** (rank within sector), so a sector bet can't pass as skill.
2. Use **sector labels as they were at each date**, or none.
3. Keep the coverage report; flag months below 80%.

---

## Phases
| Phase | What | Data | Status |
|---|---|---|---|
| **A1** | Price-based signals with strong academic evidence, plus combinations and boosted trees | S&P 500 membership as it was at each date (rebuilt from Wikipedia's change history) + Yahoo prices | **building** |
| A2 | Company fundamentals: value, profitability, investment, accruals | SEC EDGAR company filings (free; needs a contact name/email in `.env` as the SEC requires) | after A1 |
| A3 | News sentiment scored by AI (Claude) | RSS / news, recorded **forward only** | after A2 |
| A4 | Anything that passes → paper-trading log for 3–6 months → terminal "STOCK PICKS" view | — | gated |

## A1 — PRE-REGISTRATION (frozen 2026-10-11, before any A1 data is downloaded)

**Universe.** Stocks that were S&P 500 members **at that date**, rebuilt by walking Wikipedia's addition/removal table back from today's list. Monthly, 2005-01 → 2026-09. Prices come from Yahoo. **Known weakness:** some delisted or acquired stocks have no Yahoo data. Coverage (the share of members with prices) is reported every month.

**Label.** The stock's return from the first trading day of the month to the first trading day of the next month. Scored **within the cross-section**: rank IC = Spearman correlation between the score and next month's return across all stocks, every month.

**Signals** (signs fixed by the literature, not fitted):
| ID | Signal | Expected sign | Source idea |
|---|---|---|---|
| S1 | momentum 12-1 (return months −12…−2) | + | Jegadeesh & Titman 1993 |
| S2 | short-term reversal (last month's return) | − | Jegadeesh 1990 |
| S3 | volatility, 3 months | − (low-vol) | Ang et al. 2006 |
| S4 | beta vs SPY, 1 year | − (betting against beta) | Frazzini & Pedersen 2014 |
| S5 | MAX: largest daily return last month | − (lottery) | Bali et al. 2011 |
| S6 | closeness to the 52-week high | + | George & Hwang 2004 |

**Combinations:**
| ID | Model | Fitting |
|---|---|---|
| C1 | average of the 6 signals' cross-sectional z-scores, signs as above | none |
| C2 | ridge regression on z-scored signals + sector | walk-forward, refit monthly, expanding |
| C3 | gradient-boosted trees on signals + sector | walk-forward, refit yearly, expanding |

Models are trained only on months whose labels ended before the prediction date.

**Portfolios** (monthly, equal weight, **10 bps per $ traded**):
- **Long-only top quintile vs the equal-weight universe**: what a normal investor can actually hold.
- Long top decile / short bottom decile, for information.

**Periods:** design = predictions ≤ 2015, **HOLDOUT = 2016 onwards.**

**PASS (on the HOLDOUT), all of these:**
1. Mean monthly rank IC **≥ 0.01** and its **t-stat ≥ 2.6**. This is a Bonferroni-style bar for 9 candidates: 0.05 / 9 one-sided.
2. Same sign in the design period (IC > 0 there too).
3. Long-only top quintile **beats the equal-weight universe after costs**, with an excess-return t-stat ≥ 2.
4. Survives the **controls**: shuffled-signal and random-score runs must show IC ≈ 0 through the same pipeline.

Anything that passes goes to paper trading, not straight to the terminal.

## What to expect (honestly)
Published versions of these signals often weakened after they became known. Momentum crashed in 2009, and low-vol is crowded. A pass would look like IC ≈ 0.02–0.04, with the top quintile beating the average stock by maybe 1–3% a year. It's a small edge that's only useful across many stocks.
