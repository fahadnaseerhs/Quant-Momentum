---
name: project-quant-momentum-lab
description: Scope of the Quant Momentum project — leakage-aware equity return prediction & backtest lab; prediction model not yet chosen.
metadata:
  type: project
---

**Project:** Leakage Aware Quantitative Equity Prediction and Strategy Lab.

**Core question:** Can information available at day $t$ predict the next 1-day or 3-day returns well enough to produce a profitable, risk-adjusted, out-of-sample strategy after transaction costs?

**Scope (from [[reference_scope_document]]; frequency amended 2026-09-27, monthly → daily):**
- Universe: 20 mixed-asset tradeables + SPY, 2021 onward, **daily** frequency. See [[project_universe_and_method]]. Can later be ported to PSX.
- Starting hypothesis: short-horizon momentum; windows in trading days, defined in Task 03.
- Features: momentum, rolling volatility, volume ratio, relative-to-market return; additional technical features added deliberately to avoid overfitting.
- Models, layered: Model 0 rank-by-momentum baseline → Model 1 linear regression → Model 2 gradient-boosted trees (XGBoost / LightGBM). **The specific prediction model has not been decided yet — user will pick after baseline + EDA.**
- Targets: 1-day and 3-day forward returns (regression), or outperform-SPY (classification).
- Portfolio: equal-weighted top-N by predicted return.
- Backtest: strict walk-forward, no look-ahead.
- Evaluation: cumulative return, annualized return, Sharpe, max drawdown, win rate, turnover.
- Transaction costs tested at 0 / 0.10 / 0.25 / 0.50 / 1.00 %.
- Robustness across momentum windows, portfolio sizes, cost levels, and market regimes.
- Version 2 extension: technical features + macro data + news sentiment.

**Success criteria are evidence-based**, not "did it make money in-sample." A valid conclusion may be that momentum is statistically real but economically dead after costs.

**Why:** User's first quant project (see [[user_first_quant_project]]), framed as a research lab — the goal is to learn to run the full pipeline correctly, with leakage prevention as a first-class concern, not just to build a profitable strategy.

**How to apply:** Respect the pipeline order (data → EDA → statistics → baseline → models → backtest → risk → costs → robustness). Never skip the baseline. Any feature at time $t$ must use only info available at $t$. Do not pick a specific ML model unprompted — wait for the user's decision, though it is reasonable to remind them the roadmap points to XGBoost/LightGBM after linear regression.
