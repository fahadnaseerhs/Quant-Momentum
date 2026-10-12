# Methodology Folder

This folder contains **conceptual and mathematical documentation** for every task in the project. It is not code, and it is not a running log of what happened. Each note explains:

1. **The question** the task was trying to answer
2. **The methodology** — the ideas and the math, in plain language
3. **The environment / what was built**
4. **A guide to run it**
5. **The expected outcome**

The goal: if I come back to this project in six months, or hand it to someone else, they can read this folder and understand *why* the pipeline looks the way it does — not just *what* the code does.

The actual code lives in `../../scripts/` and `../../src/`. The full research scope lives in `../../quant_equity_prediction_strategy_lab.md`. The assistant's internal memory lives in `../../.claude/`.

## Notes

- [[01 - Data Collection]]
- [[02 - Data Cleaning]]
- [[03 - Exploring Returns]]
- [[04 - Feature Engineering]]
- [[05 - Signal Analysis]]  ·  run log: [[05 - Signal Analysis - Runs]]
- [[07 - Time-Series Momentum]] (Model 1; replaces the cross-sectional linear regression)
- [[07b - Volatility Forecasting]] (predict risk instead of returns)
- [[07c - Long-History Re-test]] (07 + 07b on 2004–26)
- [[10 - Costs and Combined Book]] (weekly rebalancing; long + trend; design/holdout split)
- [[11 - Robustness (No-Hindsight Universe)]] (23 broad ETFs, frozen settings; the project-level answer)

Concepts (volatility, correlation, autocorrelation, …) are explained once in [[_Technical Learning - README|Technical Learning]]; task notes link there instead of repeating them.
