# Project Introduction — Leakage Aware Quantitative Equity Prediction and Strategy Lab

## What this project is

This is my first quant project. It is a research pipeline that starts with a simple momentum idea and grows into a full quantitative equity prediction and backtesting lab. The full scope lives in [[quant_equity_prediction_strategy_lab]].

## The core question

> Can historical market information predict the next 1-day or 3-day returns well enough to build a profitable, risk-adjusted trading strategy — out of sample and after realistic transaction costs?

*(Amended 2026-09-27: the project moved from monthly to daily frequency. See [[02 - Data Cleaning]] §6.)*

> **⚠️ Updated 2026-10-12: the core question has changed.** Six fair, pre-registered tests showed that returns could **not** be predicted out of sample ([[Prediction Attempts Log]]), while risk could. The project now answers: *"How can a normal investor decide how much to put in each asset so their losses stay within a limit they choose, and can we prove the risk numbers are honest?"* See **[[Problem Statement v2 - Risk-First Investing]]**. The original question below is kept for the record.

For asset $i$ on trading day $t$, the two candidate targets are:

$$R_{i,t\to t+1} = \frac{P_{i,t+1}}{P_{i,t}} - 1, \qquad R_{i,t\to t+3} = \frac{P_{i,t+3}}{P_{i,t}} - 1$$

The prediction problem is $X_{i,t} \rightarrow \hat{R}_{i,t\to t+h}$, where $X_{i,t}$ only contains information available at the close of day $t$. No future data ever leaks in.

## What I am going to do

Walk through the full research pipeline end to end:

1. **Data** — daily data since 2021 on 20 mixed assets (crypto, tech, gold, oil, real assets, bonds) plus SPY as benchmark. The same framework can later be replicated on PSX.
2. **Feature engineering** — start small and interpretable: momentum over windows in trading days, rolling volatility, volatility-scaled momentum, volume ratio, relative-to-market return.
3. **Exploratory + statistical testing** — return distributions, momentum buckets, regression of forward returns on momentum, t-stats, p-values.
4. **Prediction models** — layered from simple to complex:
   - Model 0: rank-by-momentum baseline
   - Model 1: linear regression
   - Model 2: gradient-boosted trees (XGBoost / LightGBM)
   - The specific prediction model to use has **not been decided yet** — that call comes after the baseline and exploratory work.
5. **Portfolio construction** — equal-weighted top-N by predicted return.
6. **Walk-forward backtest** — strict expanding window, no lookahead.
7. **Risk & profitability** — cumulative return, Sharpe, max drawdown, win rate, turnover.
8. **Transaction costs** — test at 0%, 0.10%, 0.25%, 0.50%, 1.00%.
9. **Robustness** — vary momentum windows, portfolio size, cost assumptions, and market regimes.
10. **Market events** — annotate performance against major events; news sentiment is a Version 2 extension.

## What counts as success

The project is **not** successful just because the model makes money in-sample. A convincing result needs:

- A signal that is statistically observable
- Performance beyond the naive baseline
- Survival out of sample
- Survival after realistic costs
- Robustness across parameters and regimes
- No leakage / survivorship / overfitting artifacts

A perfectly valid conclusion is: *"the momentum signal is statistically observable, but its economic value disappears after transaction costs."* That is still a real quant research result.

## Design principle

**Leakage-aware from day one.** Every feature at time $t$ uses only information known at time $t$. Every backtest is walk-forward. Survivorship bias is documented, not ignored.

## Related notes

- [[quant_equity_prediction_strategy_lab]] — full scope document (the source of truth)
- [[Task Log]] — running status of every pipeline task (done / in progress / next)
