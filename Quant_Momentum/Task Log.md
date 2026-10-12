# Task Log

A running status tracker for the project pipeline — **what has been done, what is in progress, and what is next.**

This complements the other folders rather than repeating them:
- [[_Methodology - README|Methodology]] explains the *why* and the math of each task (not a running log).
- [[_Graph Explanations - README|Graph Explanations]] explains each task's figures.
- This note is the *status* layer: one row per pipeline task, newest activity at the bottom of the changelog.

Full scope & task roadmap: [[quant_equity_prediction_strategy_lab]] (§16–§18 models, §38.2 notebook plan).

---

## Status overview

| # | Task | Status | Code | Methodology | Graphs |
|---|------|--------|------|-------------|--------|
| 01 | Data collection | ✅ Done | `src/universe.py` | [[01 - Data Collection]] | — |
| 02 | Data cleaning | ✅ Done | `src/cleaning.py` | [[02 - Data Cleaning]] | [[Task 02 - Graph Explanation]] |
| 03 | Exploring returns (EDA) | ✅ Done | `src/eda.py`, `notebooks/03_explore_returns.ipynb` | [[03 - Exploring Returns]] | [[Task 03 - Graph Explanation]] |
| 04 | Feature engineering | ✅ Done | `src/features.py` → `data/features/features.parquet` | [[04 - Feature Engineering]] | [[Task 04 - Graph Explanation]] |
| 05 | Signal / statistical testing | ✅ Done | `src/signals.py` → `reports/tables/05_*` | [[05 - Signal Analysis]] · [[05 - Signal Analysis - Runs]] | [[Task 05 - Graph Explanation]] |
| 06 | Baseline — Model 0 (rank-by-signal) | ✅ Done | `src/baseline.py` → `reports/tables/06_*` | — | [[Task 06 - Graph Explanation]] |
| 07 | **Model 1 — Time-series momentum** (pivoted from cross-sectional linear reg.) | ✅ Done (2021–26): no edge | `src/tsmom.py`, `scripts/07_tsmom.py` (old: `src/linear_model.py`) | [[07 - Time-Series Momentum]] | [[Task 07 - Graph Explanation]] |
| 07b | **Volatility forecasting** (HAR vs EWMA) | ✅ Done (2021–26): HAR better forecast, same Sharpe | `src/volforecast.py`, `scripts/07b_vol_forecast.py` | [[07b - Volatility Forecasting]] | [[Task 07b - Graph Explanation]] |
| 07c | **Long-history re-test** (2004–26) of 07 and 07b | ✅ Done: trend real but small; vol-sizing is the big win | `scripts/07c_fetch_long.py`, `--long` flag on 07/07b scripts | [[07c - Long-History Re-test]] | [[Task 07c - Graph Explanation]] |
| 08 | Model 2 — Gradient-boosted trees | ⬜ Not started, low priority (model ≈ rule; no non-linear signal seen) | — | — | — |
| 09 | Walk-forward backtest | ✅ Folded into 07–11 (every result is expanding walk-forward + embargo) | `src/tsmom.py`, `src/portfolio.py` | — | — |
| 10 | Transaction costs + combined book | ✅ Done: weekly rebalancing; 70/30 long+trend = same Sharpe, smaller DD (holdout) | `src/portfolio.py`, `scripts/10_costs_combined.py` | [[10 - Costs and Combined Book]] | [[Task 10 and 11 - Graph Explanation]] |
| 11 | Robustness (no-hindsight ETF universe) | ✅ Done: trend edge ≈ 0; risk-sized long book robust | `scripts/11_robust_etf.py` | [[11 - Robustness (No-Hindsight Universe)]] | [[Task 10 and 11 - Graph Explanation]] |
| 12 | Final results / dashboard → **QM Terminal** (live product) | ✅ Phases 1–3 built; AI briefing awaiting key | `terminal/` (run: `streamlit run terminal/app.py`) | [[QM Terminal - Plan]] | — |

Legend: ✅ done · 🟡 in progress / next · ⬜ not started.

> **Model-choice note:** the specific *advanced* model (Task 08: XGBoost vs LightGBM) is **not yet decided** — that call is the user's, after Model 1. Model 1 (linear regression) is the scoped next step and does not pre-empt that decision.

---

## Where the project stands (2026-10-11)

**Tasks 10 + 11 done.**
- **Task 10:** weekly rebalancing (chosen on 2005–15) cuts trend's cost drag from 2.3% to 1.0% a year; net Sharpe 0.39 → 0.53, and it held on the 2016–26 holdout (0.52 → 0.53). The 70% long + 30% trend book: holdout Sharpe 1.51 vs long 1.52, max DD −11% vs −17.5%. [[10 - Costs and Combined Book]]
- **Task 11:** on 23 broad ETFs with all settings frozen, **trend's edge ≈ 0** (IC 0.008, t 0.7; Sharpe 0.11). The **risk-sized long book is robust**: Sharpe 0.83 vs SPY 0.69 (t = 3.8), max DD −24% vs −55%. Combined: DD −15% but Sharpe 0.76. Trend consistently works on bonds and commodities and fails on US equities. [[11 - Robustness (No-Hindsight Universe)]]

**Project-level answer:** the robust edge is **diversification + volatility sizing**, not return prediction. Trend is an insurance sleeve whose cost depends on the universe.

**Possible next steps (awaiting the user):** (a) a pre-committed test of an **equal risk budget per asset class** for trend (the literature-standard fix for equity funds dominating); (b) **Task 12** final write-up / dashboard; (c) Task 08 trees, low priority.

---

## Task 07 history — Model 1, Time-Series Momentum

**Updated:** 2026-10-11 · **Status:** done; see 07c for the definitive numbers.

**What happened.**
1. The cross-sectional linear regression (15 features) got OOS IC ≈ 0 and lost to the baseline. Cause: ranking assets *across* crypto, equities, bonds and commodities is meaningless.
2. Pivoted to **time-series momentum**: each asset predicted from its own trend. 4 vol-normalised features (`rev_5`, skip-5 `mom_21/63/126`), label = vol-normalised 21-day forward return, pooled ridge with no intercept, expanding walk-forward with a 21-day embargo, 10 bps costs.
3. Result (OOS 2022-08 → 2026-09): model IC −0.026 (t −0.7), hit rate 49.9% vs 56.4% for always-long. Net Sharpe: model −0.10, plain trend rule −0.26, **inverse-vol long-only 1.50**, SPY 1.21. In-sample IC was 0.087, so the overfit gap persists even with 4 features.
4. Interpretation: in this window, holding the assets beat timing them. 4 OOS years is too short to confirm or reject trend (t ≈ SR·√T). Details: [[07 - Time-Series Momentum]].

**Decision (2026-10-11):** the user chose **Option 2 (volatility forecasting), then Option 1 (long history)**.

**07b result.** HAR beats EWMA at forecasting next-21-day vol: QLIKE −8.7%, Diebold–Mariano t = 2.76, better on 16/20 assets. This is the project's first significant OOS prediction. But the long-only book's Sharpe is unchanged (1.22 vs 1.22), because the weights are dominated by cross-asset vol differences that EWMA already gets right. Vol-sizing itself is the big win: Sharpe 1.05 → 1.22 and max DD −30% → −11% vs 1/N. Details: [[07b - Volatility Forecasting]].

**07c result (2004–26, about 21 OOS years).** Trend is **real but small**: IC 0.052 (in-sample 0.050, so no overfit gap), net Sharpe 0.41 (t ≈ 1.9; gross 0.73, t ≈ 3.3). The fitted model ≈ the simple rule. Costs eat about 45%. Trend helps in crashes and big moves (2008, 2020, 2022) and lags in calm bull markets (2023–24), so 2021–26 was a bad window. Exploratory: 25% trend + 75% long keeps Sharpe at 1.20 and cuts max DD from −20% to −15%. Vol: HAR beats EWMA on average but loses in crashes, so keep EWMA for sizing. Vol-sizing halves drawdowns vs 1/N (−20% vs −43%). Caveat: the hindsight-picked universe flatters long-only. Details: [[07c - Long-History Re-test]].

**Next (proposed then):** (1) cut trend turnover (Task 10); (2) a pre-committed combined book of long core + trend overlay; (3) robustness incl. a universe without hindsight winners (Task 11). All three were done on 2026-10-11; see "Where the project stands" above.

<details><summary>Original Task 07 scope (2026-10-08)</summary>

**Goal.** First *predictive* model: map features at day $t$ to the forward return, replacing the single-signal rank of Model 0 with a fitted linear combination of features, then feed predictions into the same equal-weighted top-N portfolio for comparison.

**Scope / requirements (from scope doc §17, §19, §23 and the 2026-09-27 daily-frequency amendment):**
- Walk-forward, expanding-window, out-of-sample prediction — **≥3-day embargo** between train and test because the 3-day target overlaps.
- Both targets: regression on $R_{t+1}$ (and $R_{t\to t+3}$), **and** the outperform-SPY classification (§19 Target B).
- Prediction-quality metrics: MAE, RMSE, prediction IC — *plus* portfolio metrics on the same basis as the baseline so the two are comparable.
- Re-run the leakage canary (the Task 05 shift test) against the model's own train/test split.

**Bar to beat.** The Model 0 baseline `top5_vsmom_21d` posts a **gross** daily-rebalanced Sharpe of 2.29 at zero cost ([[Task 06 - Graph Explanation]]). Model 1 must justify its added complexity on an **out-of-sample, cost-aware** basis — not in-sample.

**Planned outputs:** `src/linear_model.py`, `notebooks/07_linear_model.ipynb`, `reports/tables/07_*`, `reports/figures/07_*`, Methodology note `07 - Linear Regression`, and `Task 07 - Graph Explanation`.

</details>

---

## Changelog

- **2026-10-08** — Created this Task Log. Confirmed pipeline complete through Task 06 (baseline). Logged Task 07 (linear regression) as next.
- **2026-10-08** — Cross-sectional linear regression (gradient descent, 15 features) + walk-forward. OOS IC ≈ 0 (1d −0.003, 3d +0.006); portfolio Sharpe 1.36 vs baseline 2.03.
- **2026-10-11** — Diagnosed the universe/method mismatch (5 asset classes; cross-sectional ranking is meaningless). Pivoted Task 07 to **time-series momentum** (`src/tsmom.py`, `scripts/07_tsmom.py`). OOS: no edge (model net Sharpe −0.10, rule −0.26, long-only 1.50). Wrote [[07 - Time-Series Momentum]] and [[Task 07 - Graph Explanation]] (3 graphs). Decided against polynomial regression: more flexibility can't fix a missing signal.
- **2026-10-11** — 07b volatility forecasting (`src/volforecast.py`, `scripts/07b_vol_forecast.py`). HAR beats EWMA (QLIKE −8.7%, DM t = 2.76); portfolio Sharpe unchanged (1.22). Wrote [[07b - Volatility Forecasting]] and [[Task 07b - Graph Explanation]]. Started 07c (long history).
- **2026-10-11** — 07c: fetched 2004–26 into `data/long/` (originals untouched). Re-ran 07 and 07b with `--long`. Trend IC 0.052, net Sharpe 0.41; vol-sizing max DD −20% vs −43% for 1/N. Sizing now divides by the assets available each day (2021–26 numbers reproduced exactly). Fixed the asset-class legend colours in the G2 figures. Wrote [[07c - Long-History Re-test]] and [[Task 07c - Graph Explanation]].
- **2026-10-11** — Task 10: `src/portfolio.py` (realistic simulator: drift between rebalances, costs on actual trades) + `scripts/10_costs_combined.py`. Design/holdout split at 2016; chose weekly rebalancing and a 30% trend share on 2005–15. Holdout: combined Sharpe 1.51 vs long 1.52, DD −11% vs −17.5%. Wrote [[10 - Costs and Combined Book]].
- **2026-10-11** — Task 11: `scripts/11_robust_etf.py`, 23 broad ETFs (`data/etf/`), all settings frozen. Trend IC 0.008 (t 0.7), Sharpe 0.11; long risk-sized 0.83 vs SPY 0.69. Checked 2022 trend P&L by fund (no bug: US-equity shorts squeezed). Wrote [[11 - Robustness (No-Hindsight Universe)]] and [[Task 10 and 11 - Graph Explanation]]. Marked Task 09 as folded into 07–11.
- **2026-10-11** — Built the **QM Terminal** (Task 12 as a product): a live Streamlit app in `terminal/` with a terminal-style dark theme. Phase 1 market core, Phase 2 world view (4 gauges, globe, playbook), Phase 3 news (RSS live; AI briefing coded, needs `ANTHROPIC_API_KEY`). Fixed alert flicker (3-day confirm), weekend live quotes, and the SHY tail-range bug (median centring). Plan + build log: [[QM Terminal - Plan]].
- **2026-10-11** — **Phase 4A built: PLAN tab** (risk per segment, buy list based on risk, weekly trade list with a 20% band, holdings log) using `terminal/allocate.py`, tested in `scripts/13_allocation_backtest.py` on both universes. Always-fully-invested profiles lost about 50% in 2008 in the design period, so every profile now caps the 1-in-20 bad month (Careful −3%, Balanced −6%, Bold −10%). Balanced: Sharpe 1.23 (project) / 0.80 (ETF) vs SPY 0.69, max drop about −22% vs −55%. Details: [[QM Terminal - Phase 4 Plan (Allocation + Prediction)]]. Next: Part B prediction lab.
- **2026-10-11** — **Phase 4B prediction lab** (`scripts/14_prediction_lab.py`), pre-registered before the run. 5 families (macro trend, panic rebound, world regime, combined logistic, boosted trees = Task 08) predicted "up next month" vs the base rate, monthly walk-forward, both universes. **None passed.** All had negative holdout Brier skill (−0.002 to −0.058); the regime, combined and tree models were worse than pure noise; controls confirm the pipeline is fair. Terminal keeps risk-based guidance only. Task 08 is now effectively answered (trees = worst). Added a minimum-effect rule (Brier skill ≥ 0.005) for any future test.
- **2026-10-11** — **Path A1, stock selection** (pre-registered): point-in-time S&P 500 membership (`src/sp500.py`; Wikipedia page version from 10 Aug 2026 + patch), 642/849 tickers priced (coverage 62% → 99%), 103,930 stock-months (`scripts/15_sp500_data.py`, `16_stock_selection_lab.py`). **None of 9 candidates passed.** Near-miss: boosted trees (IC t 2.51 vs bar 2.6, +4.3%/yr top fifth), but its within-sector IC is 0.0006, so it was a sector bet. Logged in [[Prediction Attempts Log]] and [[Path A - Stock Selection Plan]]. Next: A2 fundamentals (SEC EDGAR), sector-neutral.
- **2026-10-12** — **New problem statement adopted:** [[Problem Statement v2 - Risk-First Investing]]. Return prediction has been tested 6 ways and failed, so the project now proves that risk-based sizing keeps losses within a chosen limit and that the risk numbers are honest. Path A2 is optional/parked. Remaining steps: (1) risk report card (bank-style VaR tests), (2) stress tests, (3) forward paper-trading record, (4) final write-up.
- **2026-10-12** — **Step 1 risk report card** (`scripts/17_risk_report_card.py`, pre-registered). **PASS:** asset bad case (holdout breach 4.7% / 3.9%, no clustering) and plan bad month (all profiles, both universes). **FAIL:** good case (upside understated, 8–12% breaches), typical range (60–64% vs 67%), expected shortfall on project assets (losses 7% worse than predicted). Next: recalibrate or relabel these, then step 2 stress tests.
- **2026-10-12** — **Step 1b** (pre-registered fix, `scripts/18_risk_recalibration.py`): a universe-wide drift shift plus a typical-range factor, both set on 2005–15. **Typical range now passes** (65% inside) and the **bad case still passes** (5.9% / 5.7%). The good case (ETF 7.4%) and expected shortfall (over-corrected) still fail and stay hidden. The terminal now shows **only verified numbers** (`risk.VERIFIED`), and only the 1-month horizon (the only one tested). Next: 1c (other horizons) and step 2 (stress tests).
