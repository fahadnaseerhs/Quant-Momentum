# Technical Learning

This folder holds the **finance and statistics concepts** the project relies on. Each concept is explained **once**, here, with intuition first and formulas second. The task notes in [[_Methodology - README|Methodology]] link to these notes instead of re-explaining.

For quick one-line meanings of any term or graph label, see [[_Definitions - README|Definitions]].

**Difference between the two folders:**
- **Methodology** describes *what we do in a task and why* (the plan, the decisions, the outputs).
- **Technical Learning** describes *the concepts themselves* (what volatility is, what autocorrelation measures), independent of any task.

## Reading order

Read top to bottom. Each note assumes the ones above it.

| # | Note | One-line summary | First used in |
|---|---|---|---|
| 1 | [[Prices, Returns and Stationarity]] | Why we study returns, not prices; growth of \$1; log-scale charts | Task 03 |
| 2 | [[Volatility]] | Standard deviation of returns; daily vs annual; rolling and exponentially-weighted estimates | Task 03 |
| 3 | [[Volatility Clustering]] | Calm and wild periods come in streaks; how to detect it; GARCH intuition | Task 03 |
| 4 | [[Return Distributions and Fat Tails]] | Normal curve, skewness, kurtosis, histograms, QQ plots, Jarque–Bera test | Task 03 |
| 5 | [[Correlation and Diversification]] | Covariance, Pearson and Spearman correlation, heatmaps, effective number of bets | Task 03 |
| 6 | [[Autocorrelation - Momentum vs Reversal]] | Does today's return predict tomorrow's? ACF, significance bands, Ljung–Box, overlapping-return trap | Task 03 |

Already covered elsewhere (not repeated here):
- Simple vs log returns, trading calendar, leakage, filtration → [[02 - Data Cleaning]]
- Adjusted close prices → [[01 - Data Collection]]

## Notation used in every note

| Symbol | Meaning |
|---|---|
| $P_t$ | Adjusted close price on trading day $t$ |
| $R_t$ | Simple return on day $t$: $P_t/P_{t-1} - 1$ |
| $r_t$ | Log return on day $t$: $\ln(P_t/P_{t-1})$ |
| $T$ | Number of observations (≈ 1438 daily returns per asset in our data) |
| $\bar{x}$ | Sample average of $x$ |
| $i$ | Asset index (1 to 21) |
| $k$ | Lag, in trading days |
