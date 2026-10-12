# Leakage Aware Quantitative Equity Prediction and Strategy Lab

> **Scope amendments (2026-09-27)** — these override the sections below where they conflict:
> - **Frequency is daily, not monthly.** Targets are the next 1-day return $P_{t+1}/P_t - 1$ and the next 3-day return $P_{t+3}/P_t - 1$. Momentum windows are in trading days. 3-day targets overlap, so walk-forward splits need a ≥3-day embargo. (`.claude/decisions/2026-09-27-daily-frequency-horizons.md`)
> - **Universe is 20 mixed assets + SPY**, not 20 stocks (`src/universe.py`). Momentum is ranked on volatility-scaled values $M_{i,t}/\sigma_{i,t}$. (`.claude/decisions/2026-09-27-universe-and-methodology.md`)

## 1. Project Overview

### Core Research Question

> Can historical market information predict next month stock returns well enough to construct a profitable, risk adjusted trading strategy out of sample and after realistic transaction costs?

The project starts with a simple momentum hypothesis and progressively develops it into a complete quantitative research pipeline:

```text
Real Market Data
       ↓
Data Cleaning
       ↓
Feature Engineering
       ↓
Exploratory Analysis
       ↓
Statistical Testing
       ↓
Prediction Models
       ↓
Predicted Returns
       ↓
Stock Ranking
       ↓
Portfolio Construction
       ↓
Walk Forward Backtest
       ↓
Risk and Profitability Analysis
       ↓
Transaction Costs
       ↓
Robustness Testing
       ↓
Real Market Events
       ↓
Final Research Conclusion
```

The goal is not to prove beforehand that momentum or machine learning works.

The goal is to determine whether the signal contains genuine, repeatable, economically useful information.

---

# 2. Main Research Question

For stock \(i\) at month \(t\), define the next month return as:

\[
R_{i,t+1} = \frac{P_{i,t+1}}{P_{i,t}} - 1
\]

The central prediction problem is:

\[
X_{i,t} \rightarrow \hat{R}_{i,t+1}
\]

where:

* \(X_{i,t}\) contains information available at the end of month \(t\)
* \(\hat{R}_{i,t+1}\) is the predicted return for month \(t+1\)

The fundamental constraint is:

> The model must never use information that was unavailable at the prediction time.

This makes leakage prevention a core part of the project.

---

# 3. Initial Hypothesis, Momentum

The first hypothesis is:

> Stocks that have performed strongly over the previous several months may have a higher expected return during the following month.

For a 3 month momentum signal:

\[
M_{i,t}^{3M}
=
\frac{P_{i,t}}{P_{i,t-3}} - 1
\]

Example:

If a stock was priced at 100 three months ago and is now priced at 120:

\[
M^{3M} = \frac{120}{100}-1 = 0.20 = 20\%
\]

The stock therefore has a 20% three month momentum value.

Momentum is a starting hypothesis, not a guaranteed source of profit.

---

# 4. Dataset

## Initial Scope

Use approximately:

* 3 to 4 years of historical data
* Around 20 liquid stocks
* Monthly research observations
* Daily data as the underlying source where available

The first implementation can use a liquid equity market with clean historical data. The same framework can later be replicated on PSX.

## Basic Market Variables

### Price

* Open
* High
* Low
* Close
* Adjusted close

### Volume

* Daily volume
* Rolling average volume
* Volume ratio
* Volume momentum

### Market Information

* Broad market return
* Market volatility
* Relative stock performance
* Market regime indicators

---

# 5. Data Frequency

Raw data may be daily, but the first research version will operate primarily at monthly frequency.

For each month end:

```text
Month t
   ↓
Information available at t
   ↓
Calculate features
   ↓
Predict t + 1
   ↓
Observe actual return during t + 1
```

Example:

```text
January → March
    ↓
3 month momentum measured at March end
    ↓
Predict April
    ↓
Observe actual April return
```

Then repeat:

```text
February → April
    ↓
Predict May

March → May
    ↓
Predict June

...
```

---

# 6. Feature Engineering

The model should initially use a small number of economically interpretable features.

## 6.1 Momentum

### 1 Month Momentum

\[
M_{1M} = \frac{P_t}{P_{t-1}} - 1
\]

### 3 Month Momentum

\[
M_{3M} = \frac{P_t}{P_{t-3}} - 1
\]

### 6 Month Momentum

\[
M_{6M} = \frac{P_t}{P_{t-6}} - 1
\]

### 12 Month Momentum

\[
M_{12M} = \frac{P_t}{P_{t-12}} - 1
\]

The initial hypothesis will focus on 3 month momentum, with other windows introduced during robustness testing.

---

# 7. Volatility

A basic rolling volatility measure can be calculated as:

\[
\sigma_t =
Std(R_{t-n}, ..., R_t)
\]

where \(R_t\) represents periodic returns.

For example, a 3 month rolling volatility:

\[
\sigma_{3M}
=
Std(R_{t-2},R_{t-1},R_t)
\]

Volatility can tell us whether momentum behaves differently in high and low volatility environments.

---

# 8. Volume Features

A simple volume ratio:

\[
VolumeRatio_t
=
\frac{Volume_t}
{AverageVolume_{20}}
\]

A value greater than 1 means current volume is above its recent average.

Possible interpretation:

```text
Strong momentum
      +
Unusually high volume
      ↓
Potentially stronger information signal
```

This is a hypothesis to test, not an assumption.

---

# 9. Relative Market Performance

We can compare stock returns with market returns.

\[
RelativeReturn_t
=
R_{stock,t}
-
R_{market,t}
\]

This helps distinguish:

> The stock went up because the entire market went up

from:

> The stock outperformed the market.

---

# 10. Additional Features

Later versions may include:

* Moving average distance
* RSI
* Maximum drawdown
* Rolling beta
* Market volatility
* Volume momentum
* Price distance from moving averages
* Cross sectional rank
* Sector relative performance

Features should be added deliberately.

Adding a large number of indicators increases the risk of overfitting.

---

# 11. Exploratory Analysis

Before machine learning, determine whether the data contains a visible relationship.

## 11.1 Return Distribution

Study the distribution of monthly returns.

Calculate:

\[
\mu = Mean(R)
\]

\[
\sigma = Std(R)
\]

Compare the empirical distribution with a normal distribution:

\[
X \sim N(\mu,\sigma^2)
\]

Important:

> Stock returns should not automatically be assumed to be normally distributed.

Financial returns can exhibit:

* Fat tails
* Skewness
* Volatility clustering
* Nonstationarity

The normal distribution is therefore an analytical reference, not a guaranteed description of reality.

---

# 12. Momentum Buckets

At the end of every month:

1. Calculate momentum for every stock.
2. Rank the stocks.
3. Divide them into groups.

Example:

```text
Lowest 20%
20% to 40%
40% to 60%
60% to 80%
Highest 20%
```

Then measure the next month return of every group.

The key question:

> Does the highest momentum group consistently outperform the lowest momentum group?

---

# 13. Momentum Portfolio

With 20 stocks:

```text
20 stocks
    ↓
Rank by 3M momentum
    ↓
Top 20% = approximately 4 stocks
Bottom 20% = approximately 4 stocks
```

Define:

\[
R_{Winner,t}
=
\frac{1}{N}
\sum_{i \in Winners} R_{i,t}
\]

and:

\[
R_{Loser,t}
=
\frac{1}{N}
\sum_{i \in Losers} R_{i,t}
\]

The momentum spread is:

\[
R_{Momentum,t}
=
R_{Winner,t}
-
R_{Loser,t}
\]

If the spread is consistently positive, there is evidence that high momentum stocks outperformed low momentum stocks during the sample.

This still does not automatically imply that the strategy is profitable after costs.

---

# 14. Scatter Plot and Regression

For every stock month observation:

\[
X = M_{3M,t}
\]

\[
Y = R_{t+1}
\]

The basic regression is:

\[
R_{i,t+1}
=
\alpha
+
\beta M_{i,t}
+
\epsilon_{i,t+1}
\]

The coefficient \(\beta\) measures the estimated relationship between previous momentum and subsequent return.

Interpretation:

### If

\[
\beta > 0
\]

higher momentum is associated with higher subsequent returns.

### If

\[
\beta \approx 0
\]

there is little linear relationship.

### If

\[
\beta < 0
\]

the relationship may indicate reversal rather than momentum.

The important question is whether the relationship is statistically distinguishable from noise.

---

# 15. Statistical Testing

Calculate:

* Correlation
* Regression coefficient
* Standard error
* t statistic
* p value
* Confidence interval

A generic hypothesis test is:

\[
H_0:\beta=0
\]

versus:

\[
H_1:\beta\neq0
\]

The goal is not simply to find a low p value.

We also need to determine whether the effect is economically large enough to matter.

---

# 16. Prediction Models

The project uses progressively more sophisticated models.

## Model 0, Simple Momentum Baseline

No machine learning.

Rule:

```text
Rank stocks by 3M momentum
        ↓
Buy highest ranked stocks
```

This establishes a baseline.

Any sophisticated model must beat this baseline to justify its additional complexity.

---

# 17. Model 1, Linear Regression

A multivariable prediction model:

\[
\hat{R}_{i,t+1}
=
\alpha
+
\beta_1M_{3M}
+
\beta_2M_{6M}
+
\beta_3Volatility
+
\beta_4VolumeRatio
+
\beta_5RelativeReturn
\]

The model predicts next month return using multiple observable features.

Advantages:

* Easy to interpret
* Coefficients show direction and magnitude
* Useful baseline
* Helps identify whether nonlinear models are actually adding value

---

# 18. Model 2, Gradient Boosted Trees

A model such as XGBoost or LightGBM can learn nonlinear relationships.

Conceptually:

```text
Momentum
    +
Volume
    +
Volatility
    +
Market conditions
    ↓
Nonlinear model
    ↓
Expected next month return
```

It can potentially discover interactions such as:

```text
High momentum
+
High volume
+
Low volatility
        ↓
Different expected return
```

without manually specifying the interaction equation.

The model must still be evaluated strictly out of sample.

---

# 19. Two Prediction Targets

## Target A, Regression

Predict the actual future return:

\[
Y_{i,t+1}=R_{i,t+1}
\]

Output:

\[
\hat{R}_{i,t+1}
\]

Example:

```text
Stock A → +3.2%
Stock B → +1.1%
Stock C → -0.8%
```

---

## Target B, Classification

Instead of predicting the exact percentage, predict whether the stock will outperform a benchmark.

\[
Y =
\begin{cases}
1, & R_{stock}>R_{market}\\
0, & R_{stock}\le R_{market}
\end{cases}
\]

This asks:

> Can the model identify relative winners?

This can be more useful for portfolio construction than pretending to know the exact future percentage return.

---

# 20. Prediction Is Not the Final Objective

The project does not end when the model achieves a good prediction metric.

A model could have modest statistical predictive power but still produce a useful trading strategy.

Conversely, a model could have an impressive statistical score but lose money after costs.

Therefore:

\[
Prediction
\neq
Profitability
\]

The actual chain is:

\[
Prediction
\rightarrow
Portfolio
\rightarrow
Trading
\rightarrow
Return
\rightarrow
Risk
\rightarrow
Net Profit
\]

---

# 21. Stock Ranking

Suppose the model predicts:

| Stock | Predicted Return |
|---|---:|
| A | 4.1% |
| B | 3.7% |
| C | 2.9% |
| D | 1.2% |
| E | -0.8% |

We rank the stocks by predicted return.

Then construct a portfolio from the highest ranked stocks.

For example:

```text
Top 20% predicted returns
        ↓
BUY

Bottom 20%
        ↓
SELL, or exclude depending on strategy
```

---

# 22. Portfolio Construction

A simple equal weighted portfolio:

\[
w_i = \frac{1}{N}
\]

where \(N\) is the number of selected stocks.

Portfolio return:

\[
R_{p,t}
=
\sum_{i=1}^{N} w_iR_{i,t}
\]

More advanced versions can later introduce volatility weighting, risk constraints, or optimization.

The first version should remain interpretable.

---

# 23. Walk Forward Backtesting

This is one of the most important parts of the project.

We cannot train on the entire historical dataset and then evaluate the same period.

Instead:

```text
Train: Jan 2022 → Dec 2022
Test:  Jan 2023

Train: Jan 2022 → Jan 2023
Test:  Feb 2023

Train: Jan 2022 → Feb 2023
Test:  Mar 2023

...
```

At every point:

\[
Information_{available\ at\ t}
\rightarrow
Prediction_{t+1}
\]

No future information is allowed into the model.

This prevents lookahead bias.

---

# 24. Profitability Analysis

The final question is:

> Did the strategy make money?

Calculate cumulative return:

\[
R_{cumulative}
=
\prod_{t=1}^{T}(1+R_t)-1
\]

Annualized return:

\[
R_{annualized}
=
(1+R_{cumulative})^{1/T}-1
\]

where \(T\) is measured in years.

---

# 25. Win Rate

\[
WinRate
=
\frac{Number\ of\ profitable\ periods}
{Total\ periods}
\]

A high win rate is not automatically good.

A strategy can have a high win rate but large occasional losses.

Therefore win rate must be considered alongside drawdown and return distribution.

---

# 26. Volatility

Portfolio volatility:

\[
\sigma_p
=
Std(R_p)
\]

This measures how variable the strategy's returns are.

---

# 27. Sharpe Ratio

A simplified Sharpe ratio:

\[
Sharpe
=
\frac{R_p-R_f}{\sigma_p}
\]

where:

* \(R_p\) = portfolio return
* \(R_f\) = risk free rate
* \(\sigma_p\) = portfolio volatility

This asks:

> How much excess return did we obtain per unit of volatility?

---

# 28. Maximum Drawdown

Maximum drawdown measures the largest peak to trough decline.

If:

\[
Peak_t = \max(V_1,\ldots,V_t)
\]

then:

\[
Drawdown_t
=
\frac{V_t-Peak_t}{Peak_t}
\]

and:

\[
MaxDrawdown
=
\min(Drawdown_t)
\]

This is essential because a profitable strategy can still experience severe losses.

---

# 29. Transaction Costs

Gross profitability is not enough.

We need to account for:

* Brokerage
* Bid ask spread
* Slippage
* Portfolio turnover

Net return:

\[
R_{net}
=
R_{gross}
-
TransactionCosts
\]

We should test several cost assumptions:

```text
0%
0.10%
0.25%
0.50%
1.00%
```

The objective is to determine whether the strategy remains viable under realistic assumptions.

---

# 30. Turnover

Portfolio turnover measures how much the portfolio changes.

A simplified measure:

\[
Turnover_t
=
\frac{1}{2}
\sum_i
|w_{i,t}-w_{i,t-1}|
\]

High turnover can destroy a seemingly profitable strategy through transaction costs.

---

# 31. Benchmark Comparison

The strategy should be compared against simple alternatives.

Possible benchmarks:

1. Buy and hold market index
2. Equal weighted portfolio
3. Simple momentum strategy
4. Linear regression strategy
5. Machine learning strategy

The important comparison is not:

> Is XGBoost profitable?

It is:

> Does XGBoost produce better risk adjusted out of sample results than simpler alternatives?

---

# 32. Robustness Testing

We deliberately try to break the strategy.

## Different Momentum Windows

```text
1 month
3 months
6 months
12 months
```

## Different Portfolio Sizes

```text
Top 10%
Top 20%
Top 30%
```

## Different Transaction Costs

```text
0%
0.10%
0.25%
0.50%
1.00%
```

## Different Market Conditions

```text
Bull market
Bear market
High volatility
Low volatility
```

If the strategy only works under one narrowly chosen parameter, that is evidence of possible overfitting.

---

# 33. Market Regime Analysis

The strategy should be evaluated under different conditions.

For example:

\[
MarketRegime_t
\in
\{Bull,Bear,HighVolatility,LowVolatility\}
\]

Then compare strategy performance across regimes.

Questions:

* Does momentum disappear during crashes?
* Does volatility affect the signal?
* Does the ML model behave differently during market stress?
* Does the model generalize across different periods?

---

# 34. Real Market News and Events

News should initially be used as context rather than automatically fed into the model.

Major market periods can be annotated against the strategy's performance.

For example:

```text
Market Data
     │
     ├──── Major economic event
     │
     ├──── Interest rate change
     │
     ├──── Earnings period
     │
     ├──── Geopolitical event
     │
     └──── Market shock
```

Then investigate:

> Did the strategy continue working during major market events?

A later project extension can incorporate news directly:

\[
PriceFeatures
+
VolumeFeatures
+
NewsSentiment
+
MacroData
\rightarrow
PredictedReturn
\]

---

# 35. Leakage and Bias Controls

This project is explicitly leakage aware.

## Lookahead Bias

Never use future information when creating features.

Correct:

\[
X_t \rightarrow Y_{t+1}
\]

Incorrect:

\[
X_{t+1} \rightarrow Y_{t+1}
\]

---

## Survivorship Bias

Using only today's successful companies for historical testing can exaggerate performance.

The first project can use a fixed liquid stock universe for simplicity, but the limitation must be documented.

A later version should use historical constituents where possible.

---

## Overfitting

Avoid selecting parameters because they produce the best historical result.

A strategy should survive reasonable changes in:

* Features
* Momentum windows
* Portfolio size
* Transaction costs
* Market periods

---

# 36. Model Evaluation

For return prediction, calculate:

### Mean Absolute Error

\[
MAE
=
\frac{1}{N}
\sum_{i=1}^{N}
|y_i-\hat y_i|
\]

### Root Mean Squared Error

\[
RMSE
=
\sqrt{
\frac{1}{N}
\sum_{i=1}^{N}
(y_i-\hat y_i)^2
}
\]

### Prediction correlation

Measure the relationship between:

\[
ActualReturn
\]

and:

\[
PredictedReturn
\]

But these are not the final financial metrics.

The final evaluation remains portfolio performance after costs and risk.

---

# 37. Final Research Dashboard

The final project should produce a dashboard containing:

## Prediction

* Actual vs predicted returns
* Prediction error
* Prediction correlation
* Regression statistics

## Portfolio

* Top predicted stocks
* Portfolio weights
* Monthly turnover

## Performance

* Cumulative return
* Annualized return
* Volatility
* Sharpe ratio
* Maximum drawdown
* Win rate

## Strategy Comparison

```text
Benchmark
Momentum
Linear Regression
XGBoost
XGBoost after costs
```

## Robustness

* Different momentum windows
* Different transaction costs
* Different portfolio sizes
* Different market regimes

---

# 38. Expected Final Deliverables

## 1. Research Dataset

A clean stock month panel containing:

```text
Date
Ticker
Price
Returns
Momentum
Volatility
Volume
Market features
Future return
```

---

## 2. Research Notebook

Suggested structure:

```text
01_data_collection.ipynb

02_data_cleaning.ipynb

03_feature_engineering.ipynb

04_exploratory_analysis.ipynb

05_statistical_testing.ipynb

06_baseline_momentum.ipynb

07_linear_model.ipynb

08_xgboost_model.ipynb

09_walk_forward_backtest.ipynb

10_transaction_costs.ipynb

11_robustness_analysis.ipynb

12_final_results.ipynb
```

---

## 3. Visualizations

At minimum:

* Price charts
* Return distribution
* Momentum distribution
* Momentum versus future return scatter plot
* Momentum bucket performance
* Cumulative portfolio return
* Drawdown curve
* Predicted versus actual return
* Feature importance
* Performance by market regime

---

## 4. Final Performance Table

The final report should contain something like:

| Strategy | Annual Return | Volatility | Sharpe | Max Drawdown | Win Rate | Turnover |
|---|---:|---:|---:|---:|---:|---:|
| Benchmark | X | X | X | X | X | X |
| Momentum | X | X | X | X | X | X |
| Linear Model | X | X | X | X | X | X |
| XGBoost | X | X | X | X | X | X |
| XGBoost after costs | X | X | X | X | X | X |

The actual values will come from the experiment.

No result should be predetermined.

---

# 39. The Ultimate Research Question

The project begins with:

> Does momentum exist?

But that is only Stage 1.

The real research question becomes:

\[
\boxed{
Can information available at time\ t
predict\ returns\ at\ t+1
well\ enough\ to\ generate
economically\ meaningful
out\ of\ sample\ profits?
}
\]

The complete chain is:

\[
Data
\rightarrow
Signal
\rightarrow
Hypothesis
\rightarrow
Statistics
\rightarrow
Prediction
\rightarrow
Portfolio
\rightarrow
Backtest
\rightarrow
Risk
\rightarrow
Costs
\rightarrow
Out\ of\ Sample\ Profitability
\]

---

# 40. What Counts as Success?

The project is **not successful simply because the model makes money in the historical sample**.

A convincing result would require evidence that:

1. The signal exists in the data.
2. The relationship is statistically meaningful.
3. The model predicts something beyond the simplest baseline.
4. The prediction survives out of sample testing.
5. The resulting portfolio generates attractive risk adjusted returns.
6. The result survives reasonable transaction costs.
7. The result is not dependent on one arbitrary parameter.
8. The result is not obviously caused by lookahead, survivorship, or other leakage.
9. The strategy's weaknesses are clearly identified.

The strongest possible conclusion is therefore not necessarily:

> "We found a profitable strategy."

It could instead be:

> "The simple momentum signal is statistically observable, but its economic value disappears after transaction costs."

That is still a successful quantitative research result because the objective is to discover what the evidence supports.

---

# 41. Version 2, Advanced Extension

Once the first version is working, extend the feature set:

\[
Price
+
Volume
+
Volatility
+
TechnicalFeatures
+
MacroData
+
NewsSentiment
\]

Then compare:

```text
Simple Momentum
        ↓
Statistical Factors
        ↓
Linear Regression
        ↓
Tree Based ML
        ↓
News + Market ML
```

This transforms the project from a momentum experiment into a broader **quantitative equity prediction laboratory**.

---

# 42. Final End Result

The finished project should answer four questions:

### Question 1
**Is there a measurable relationship between historical market information and future returns?**

### Question 2
**Can a statistical or machine learning model exploit that relationship out of sample?**

### Question 3
**Can those predictions be converted into a trading strategy?**

### Question 4
**Does that strategy remain profitable and risk controlled after realistic transaction costs and robustness tests?**

The final output is therefore:

\[
\boxed{
Raw\ Market\ Data
\rightarrow
Quant\ Research
\rightarrow
Prediction\ Model
\rightarrow
Portfolio
\rightarrow
Backtest
\rightarrow
Risk/Profitability
\rightarrow
Evidence\ Based\ Conclusion
}
\]

This is the complete scope of the project.
