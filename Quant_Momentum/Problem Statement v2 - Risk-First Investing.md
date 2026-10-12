# Problem Statement v2 — Risk-First Investing

**Adopted:** 2026-10-12 · **Replaces:** the original goal "predict equity returns and trade them" in [[quant_equity_prediction_strategy_lab]] / [[00 - Project Introduction]]
**Why it changed:** six fair, pre-registered attempts to predict returns failed ([[Prediction Attempts Log]]), while risk forecasting and risk-based sizing passed every test.

## The problem
> **How can a normal investor decide how much to put in each asset so their losses stay within a limit they choose, and can we prove the risk numbers we show are honest?**

## Why this is the right problem
- **It can be solved:** risk (how much prices swing) is predictable; direction isn't.
- **It can be checked:** "a 1-in-20 bad month" either happens about 1 time in 20 or it doesn't. Banks test their risk models exactly this way.
- **It's useful:** it turns into a concrete plan of what to buy, how much, and when to trim (the PLAN tab of [[QM Terminal - Plan]]).

## What's already done
| Piece | Status | Where |
|---|---|---|
| Risk forecasts (EWMA / HAR) | ✅ tested | [[07b - Volatility Forecasting]], [[07c - Long-History Re-test]] |
| Risk per segment + buy list + bad-month cap + weekly trades | ✅ tested (Sharpe 1.23 vs SPY 0.69, worst drop −22% vs −55%) | [[QM Terminal - Phase 4 Plan (Allocation + Prediction)]] |
| Crisis types (bonds vs oil in 2008 / 2022) | ✅ history | [[QM Terminal - Plan]] |
| Honest record of failed predictions | ✅ | [[Prediction Attempts Log]] |
| Live terminal (product) | ✅ | `terminal/` |

## What's left
| Step | What | Status |
|---|---|---|
| **1** | **Risk report card:** formally test every risk number the terminal shows | ✅ done. Bad case, typical range (after fix 1b) and plan bad month **verified**; good case and expected shortfall hidden |
| 1c | Report card for the other horizons (1 week, 3 / 6 / 12 months) and the plan's typical range | next (until then only 1 month is shown) |
| 2 | Stress tests: each profile through 2008, Covid, 2022 | next |
| 3 | Forward paper-trading record: save the plan and warnings weekly, from now on | next |
| 4 | Final write-up (Task 12) | last |

---

## Step 1b — RESULT (2026-10-12)

**Code:** `scripts/18_risk_recalibration.py` · `reports/tables/18_*`. Frozen parameters (set on 2005–15): project k_typ = 1.00, k_es = 1.115; ETF k_typ = 1.04, k_es = 1.025.

| Holdout 2016–26 (project / ETF) | Before | After fix | Verdict |
|---|---|---|---|
| **Typical range (2 in 3)** | 62.9% / 59.5% inside | **64.9% / 65.5%** (p 0.07 / 0.16) | ✅ **PASS**, back on screen |
| **Bad case (1 in 20)** | 4.7% / 3.9% (too cautious) | **5.9% / 5.7%**, 100% / 83% of assets pass | ✅ **PASS**, now closer to 5% |
| Good case (1 in 20) | 8.1% / 12.0% | 5.6% ✅ / **7.4% ❌** (74% of ETFs pass) | ❌ stays hidden |
| Expected shortfall | 1.04 / 1.02 | **0.94 ❌** (over-corrected) / 0.98 ✅ | ❌ stays hidden |

**Terminal now** (`terminal/risk.py`: `VERIFIED = {bad ✓, typical ✓, good ✗, shortfall ✗}`, `K_TYP = 1.00`, `universe_drift`):
- **Calculator and Asset tabs:** per-asset numbers use the verified method (drift shift). They show the typical range plus the bad case, and no good case.
- **PLAN tab:** shows the plan's bad case (its own verified method). The plan-level typical range was never tested, so it isn't shown.
- **Only the 1-month horizon is offered.** That's the only horizon tested. 1 week, 3 months, 6 months and 1 year come back once they pass a report card.

![[18_g1_recalibration.png]]

## Step 1b — Fix for the failed numbers: PRE-REGISTRATION (frozen 2026-10-12, before running)

**Immediate action (done):** the terminal now shows **only verified numbers**, using the `risk.VERIFIED` switch. The good case and typical range are hidden everywhere until a fix passes.

**Fixes.** Each one is set using **only design data (≤ 2015)**, then frozen and tested on the **HOLDOUT (2016+)**:
| Fix | What changes | Parameter set on 2005–15 |
|---|---|---|
| **Drift** | Every bound is shifted by the **whole universe's typical monthly move** (the median of all assets' past standardised moves, using only data available at the time). It's the same for every asset, so a past winner such as BTC isn't credited with its own past growth | none (expanding, point in time) |
| **Typical-range width** | the 2-in-3 band is widened or narrowed around the drift-shifted centre by a factor k_typ | k_typ such that 2/3 of design months land inside |
| **Expected shortfall** | the predicted average breach loss × k_es | k_es = design-period average of real ÷ predicted breach losses |

**PASS on the HOLDOUT (same bars as step 1):**
- Good case: ≥ 80% of assets pass Kupiec and the pooled rate is 3–7%, both universes.
- Typical range: binomial p > 0.05, both universes.
- Expected shortfall: the 90% bootstrap interval includes 1, both universes. This is judged on the holdout, because k_es is set on the design period.
- **The bad case must still pass with the drift fix.** If it doesn't, the bad case keeps its current (verified) method.

Each number is judged separately. Anything that passes becomes `VERIFIED = True` and goes back on screen using the frozen parameters; anything that fails stays hidden.

## Step 1 — RESULT (2026-10-12)

**Code:** `scripts/17_risk_report_card.py` · tables `reports/tables/17_*.csv` · 4,348 + 6,117 asset-month forecasts, each made with only past data.

| Risk number | Verdict | Evidence (HOLDOUT 2016–26 unless noted) |
|---|---|---|
| **Asset bad case (1 in 20)** | ✅ **PASS** | real months worse than the warning: **4.7%** (project) / **3.9%** (ETF). 95% / 87% of assets pass Kupiec. **No clustering** on any asset (100% pass Christoffersen). The 4 "fails" (NVDA, QQQ, XLK, EEM, 1.6%) are on the **cautious** side |
| **Plan bad month** (Careful / Balanced / Bold) | ✅ **PASS** | breach rates 2.3–7.8%. Every profile passes Kupiec and conditional coverage, both universes, full period |
| Asset good case (1 in 20) | ❌ FAIL | months beat the good case **8–12%** of the time (target 5%): the upside is understated. Cause: past drift is deliberately removed, and 2016–26 was a strong bull market |
| Asset typical range (2 in 3) | ❌ FAIL | **60–64%** inside vs 67%. Close, but with over 4,000 checks even a small miss fails |
| Expected shortfall | ❌ FAIL (narrowly) | ETF passes (ratio 1.02, interval 0.99–1.05). Project assets: real breach losses are **7% worse** than predicted (1.07, interval 1.02–1.11) |

**What this means for the product:** the two numbers that protect you, the **bad case** and the **plan's bad month**, are honest and pass bank-style tests. The upside numbers (good case, typical range) and the expected shortfall need recalibrating, re-testing under a new pre-registration, or relabelling.

![[17_g1_risk_report_card.png]]

## Step 1 — Risk report card: PRE-REGISTRATION (frozen 2026-10-12, before running)

**Numbers tested** (exactly as the terminal computes them, but using **only data available at the time**):
1. **Asset "bad case (1 in 20)"** for the next month. Predicted 5% loss quantile = today's EWMA risk × the asset's own history of big moves (median-centred), estimated only from months already finished.
2. **Asset "good case (1 in 20)"**, the 95% quantile.
3. **Asset "typical range"**: 2-in-3 chance of landing inside (17%–83% quantiles).
4. **Plan "bad month"** for CAREFUL / BALANCED / BOLD (the bad-month cap the PLAN tab uses), from the weekly allocation backtest.
5. **Expected shortfall:** the average loss *when* the bad case is breached (new; the terminal will show it once it passes).

**Sampling:** one forecast per asset on the first trading day of each month, checked against that month's real move (no overlap). Universes: the project's 20 assets and the 23 hindsight-free ETFs. Periods: full, and HOLDOUT 2016+.

**Tests** (the standard bank risk-model tests):
- **Kupiec:** is the breach rate consistent with 5%?
- **Christoffersen independence:** do breaches clump together, for example all in 2008?
- **Conditional coverage:** both of the above together.
- **Typical range:** a binomial test that about 2/3 of months land inside.
- **Expected shortfall:** realised average breach loss ÷ predicted. The 90% bootstrap interval must include 1.

**PASS rules:**
- **Per number type:** at least **80% of assets** pass Kupiec (p > 0.05) on the HOLDOUT in each universe, **and** the pooled breach rate is between 3% and 7%.
- **Plan bad month:** Kupiec **and** conditional coverage p > 0.05 for every profile, both universes, full period.
- **Expected shortfall:** the bootstrap interval includes 1 in both universes.
- Anything that fails is either recalibrated (with a new pre-registration and a re-test) or labelled differently on the terminal.
