# Glossary A–Z

Short definitions of every term used in the project so far. Each entry gives the meaning in one or two sentences, the formula where there is one, and a link (→) to the note that explains it in depth.

**Notation:** $P_t$ = price on day $t$, $R_t$ = simple return, $r_t$ = log return, $T$ = number of days, $W_t$ = value of \$1 invested at the start.

---

## A

### Adjusted close
The closing price corrected for stock splits and dividends, so that price changes show what an investor actually earned. All our prices are adjusted. → [[01 - Data Collection]]

### Alignment
Putting every asset onto the same list of dates (the NYSE trading days) so that they can be compared day by day. → [[02 - Data Cleaning]]

### Annualise
Converting a daily figure into a per-year figure. Mean: × 252. Volatility: × √252 (see [[#Square-root-of-time rule]]).

### Asset class
A group of similar investments. Ours: crypto, tech, gold, oil, real assets, bonds (`src/universe.py`). A label is not proof of behaviour: MSTR behaves like crypto, and DBC like oil.

### Autocorrelation (ACF)
The correlation between a series and its own past $k$ days. Positive = [[#Momentum]], negative = [[#Reversal (mean reversion)]], zero = [[#Random walk]].
$\hat\rho_k = \operatorname{corr}(r_t, r_{t-k})$ → [[Autocorrelation - Momentum vs Reversal]]

### Average pairwise correlation ($\bar\rho$)
The mean of the correlations between every pair of *different* assets. Ours: 0.21.

---

## B

### Backfill
Filling a missing value with a value from a **later** date. **Forbidden**, because it leaks future information (see [[#Lookahead bias]]).

### Bartlett band
The range $\pm 1.96/\sqrt{T}$ (±0.052 for our data). An ACF bar inside it can't be told apart from pure luck. It is too narrow when volatility clusters; see [[#Robust band]].

### Benchmark
The reference asset results are compared against. Ours is **SPY** (the S&P 500 ETF). It is not traded.

### Bessel's correction
Dividing by $T-1$ instead of $T$ when computing a sample variance, to remove a small downward bias.

### Bid–ask bounce
Closing prices randomly land on the buy price (bid) or the sell price (ask), creating a fake up-down pattern and a slightly negative lag-1 autocorrelation.

### Block (correlation block)
A group of assets that move together strongly (a bright square in the clustered heatmap). Ours: crypto + MSTR, oil + DBC, gold, bonds, US equities.

---

## C

### CAGR (Compound Annual Growth Rate)
The **constant** yearly growth rate that would turn \$1 into the actual final value over the same period.
$\text{CAGR} = W_T^{\,252/T} - 1$
Example: SOL's \$1 → \$49 over 5.7 years is a CAGR of about 98% per year. It hides the path; SOL also fell 96% along the way (see [[#Drawdown]]).

### Calendar day / trading day
A calendar day is any day of the year (365). A trading day is a day the exchange is open (~252 per year).

### Central Limit Theorem
Sums or averages of many independent random effects tend toward a normal distribution. It's why the normal curve is the default assumption, and why fat tails slow it down.

### Clustered heatmap
A coloured correlation table whose rows and columns are reordered (by **hierarchical clustering**) so that similar assets sit next to each other. The tree drawn on the edge is the **dendrogram**: the lower two branches join, the more alike the assets are.

### Correlation (Pearson)
How strongly two series move together, on a scale from −1 to +1.
$\rho_{XY} = \operatorname{Cov}(X,Y) / (s_X s_Y)$ → [[Correlation and Diversification]]

### Covariance
The average of (X's distance from its mean) × (Y's distance from its mean). Positive = they move together. Its size depends on units, which is why correlation is used instead.

### Cross-sectional
Comparing **many assets on the same day** (e.g., ranking all 20 by momentum today). Our strategy is cross-sectional. Opposite: [[#Time-series]].

### Cumulative return / total return
The total gain over the whole period: $W_T - 1$. A final value of \$2.63 = a 163% total return.

---

## D

### Daily return
The return from one trading day's close to the next. See [[#Simple return]] and [[#Log return]].

### Distribution
How often returns of each size occur. It's pictured with a [[#Histogram]]. → [[Return Distributions and Fat Tails]]

### Diversification
Reducing risk by holding assets that don't move together. It's limited by correlation (see [[#Effective number of bets]]).

### Drawdown / maximum drawdown
**Drawdown** is how far the value is below its highest point so far: $DD_t = W_t / \max_{s \le t} W_s - 1$. **Maximum drawdown** is the worst drawdown in the period (e.g., SOL −96%, TLT −44%).

---

## E

### Effective number of bets (N_eff)
How many truly independent bets a portfolio contains.
$N_{eff} = N / (1 + (N-1)\bar\rho)$. Ours: 20 assets → **≈ 3.9 bets**. → [[Correlation and Diversification]]

### Embargo
A gap of days left between training data and test data, so that overlapping targets can't leak the test answer into training. We need ≥ 3 days for 3-day targets.

### EWMA volatility
Exponentially weighted volatility: recent days count more, and old days fade out gradually.
$\hat\sigma_t^2 = \lambda \hat\sigma_{t-1}^2 + (1-\lambda) r_t^2$, with $\lambda = 0.94$ → [[Volatility]]

### Excess kurtosis
Kurtosis minus 3, so the normal distribution scores 0. Positive = fat tails. Ours ranges from 0.6 (TLT) to 23 (META).

---

## F

### Fat tails
Extreme days happen far more often than the normal curve predicts. Found in all 21 of our assets. → [[Return Distributions and Fat Tails]]

### Feature
An input a model uses to make a prediction (e.g., 21-day momentum). Built in Task 04.

### Filtration ($\mathcal{F}_t$)
The set of all information available up to day $t$. Every feature must belong to it (no future data).

### Final value (\$)
What \$1 invested at the start is worth at the end: $W_T$.

### Forward-fill
Filling a missing value with the **last known earlier** value. Allowed, for gaps of up to 2 days.

### Frequency
How often the data is observed: daily (our choice), weekly, monthly.

---

## G

### GARCH(1,1)
A model in which today's variance = a floor + a reaction to yesterday's shock + memory of yesterday's variance. EWMA is a special case. → [[Volatility Clustering]]

### Ghost effect (rolling window)
A shock keeps full weight in a rolling window for exactly $n$ days, then disappears all at once, so the rolling line drops off a cliff $n$ days after the event.

### Growth of \$1
See [[#Wealth index]].

---

## H

### Half-life
The number of days until a shock's weight in EWMA halves: $\ln 0.5 / \ln\lambda$ ≈ 11 days for λ = 0.94.

### Heteroskedasticity
Variance that changes over time. [[#Volatility clustering]] is one form of it. It makes standard statistical tests too optimistic.

### Histogram
A bar chart counting how many days fall into each return range.

### Horizon
How far ahead a target looks: **1-day** or **3-day** in this project.

### Hypothesis / null hypothesis ($H_0$)
A hypothesis is a claim to test. The null hypothesis is the "nothing is there" claim (e.g., "no autocorrelation"). A test either rejects it or fails to reject it.

---

## I

### i.i.d.
"Independent and identically distributed": each day is a fresh, unrelated draw from the same distribution. Pure noise.

### Information Coefficient (IC)
On one day, the [[#Spearman correlation]] between a signal's values across assets and those assets' next returns. The main signal-quality measure in Task 05.

---

## J

### Jarque–Bera test
A test of normality that combines skewness and kurtosis: $JB = \frac{T}{6}(S^2 + (K-3)^2/4)$. Above 5.99 → not normal.

---

## K

### Kurtosis
The fourth moment. It measures how much extreme values dominate: $K = \frac1T\sum z_t^4$ (normal = 3). See [[#Excess kurtosis]].

---

## L

### Lag ($k$)
How many days back a comparison looks. Lag 1 = yesterday.

### Leverage effect
In stocks, volatility rises more after falls than after equal-sized rises.

### Ljung–Box test
Tests whether the first $m$ autocorrelations are **jointly** zero: $Q(m) = T(T+2)\sum_{k=1}^m \hat\rho_k^2/(T-k)$.

### LOCF (Last Observation Carried Forward)
Using the most recent available value for a date. The basis of calendar alignment and forward-fill.

### Log return
$r_t = \ln(P_t/P_{t-1})$. It adds up across time, and is used for statistics. → [[02 - Data Cleaning]] §7

### Log scale
An axis on which equal distances mean equal **percentage** changes (1→2 looks the same as 10→20).

### Lookahead bias / leakage
Using information that wasn't available at the time of the decision. It makes backtests look far better than reality.

### Lookback window
How many past days a feature uses (e.g., 21-day momentum looks back 21 trading days).

---

## M

### Mean (sample mean)
The average: $\bar r = \frac1T \sum r_t$.

### Moments
Summary numbers of a distribution: 1st = mean, 2nd = variance, 3rd = skewness, 4th = kurtosis.

### Momentum
The tendency of assets that rose recently to keep rising. Measured as $M_{i,t} = P_{i,t}/P_{i,t-L} - 1$ over a lookback of $L$ days.

### Multiple testing
Running many tests at once. At a 5% level, about 1 in 20 looks "significant" by luck alone (≈ 10 of our 210 ACF bars).

---

## N

### NaN
"Not a Number": a missing value in the data.

### Newey–West standard errors
Standard errors that stay valid when data is autocorrelated or its variance changes. Needed with overlapping targets and volatility clustering.

### Non-overlapping returns
Multi-day returns computed on separate blocks (days 1–3, 4–6, …), so that no day is counted twice.

### Normal distribution
The bell curve, fully described by its mean and σ; 68–95–99.7% of values lie within 1, 2 and 3σ. Our benchmark shape.

### NYSE calendar
The days the New York Stock Exchange is open. We take it from the dates SPY traded.

---

## O

### Overfitting
Choosing settings because they happened to work best on past data. They then fail on new data.

### Overlapping returns
Multi-day returns computed every day, so that consecutive values share days. This creates fake autocorrelation of $1 - k/h$ (0.67 and 0.33 for 3-day returns).

---

## P

### p-value
The probability of seeing a result at least this extreme if the null hypothesis were true. Below 0.05 → "statistically significant at 5%".

### Parquet
A compressed, fast file format for tables. It keeps dates and numbers exactly.

### Portfolio
A collection of holdings with weights $w_i$. Its return is $\sum_i w_i R_i$ (simple returns).

---

## Q

### QQ plot
Sorted actual values plotted against the values a normal distribution would give. A straight line = normal; an S-shape = fat tails.

### Quantile / percentile
The value below which a given share of the data lies (the 1st percentile = the value below which 1% lies).

---

## R

### R² (R-squared)
The share of variation a forecast explains. For a lag-1 forecast, $R^2 = \rho_1^2$ (our maximum: 0.34%).

### Random walk
A price path whose changes are unpredictable from the past: all autocorrelations are zero.

### Rank
An asset's position when sorted (1 = smallest). Rank-based measures ignore how extreme the values are.

### Rebalancing
Adjusting holdings back to the target weights (daily, in this project).

### Regime
A period with distinct behaviour (calm, crash, high-inflation). Ours include 2022, April 2025, and January 2026 for gold.

### Relative volatility
One asset's volatility divided by SPY's ("× SPY's volatility"). BTC ranged from 1.2× to 9.7×.

### Return
See [[#Simple return]] and [[#Log return]].

### Reversal (mean reversion)
The tendency of moves to partly undo themselves: negative autocorrelation.

### Robust band / robust standard error
A significance band that allows for changing volatility, so it's wider than Bartlett's in stormy data: $\sqrt{\sum x_t^2 x_{t-k}^2}/\sum x_t^2$.

### Rolling (rolling window)
A statistic recomputed every day from only the **most recent $n$ days**. The window "rolls" forward one day at a time (e.g., 63-day rolling volatility, 63-day rolling correlation). Has a [[#Ghost effect (rolling window)]].

---

## S

### Sharpe ratio
Excess return per unit of volatility: $(R_p - R_f)/\sigma_p$. Used from the backtest onward.

### Significance (statistical)
A result is significant when it's unlikely to be luck (conventionally a p-value < 0.05, or a bar outside the 95% band).

### Simple return
$R_t = P_t/P_{t-1} - 1$. What an investor actually earns, and it adds up across assets in a portfolio. → [[02 - Data Cleaning]] §7

### Skewness
The third moment, which measures lopsidedness: $S = \frac1T\sum z_t^3$. Negative = crash-prone left tail.

### Spearman correlation
Pearson correlation computed on **ranks**. Robust to outliers; the basis of the IC.

### Spurious regression
A meaningless "relationship" found between trending (non-stationary) series such as prices.

### Square-root-of-time rule
If daily returns are independent, risk over $q$ days = daily risk × $\sqrt{q}$. Hence $\sigma_{annual} = \sigma_{daily}\sqrt{252}$.

### Standard deviation
The square root of the variance, in the same units as the data. For returns, it's called [[#Volatility]].

### Standardised return (z-score)
A return measured in standard deviations: $z_t = (r_t - \bar r)/s$.

### Stationarity
Statistical properties (mean, variance, autocorrelation) that don't change over time. Returns are approximately stationary; prices are not. → [[Prices, Returns and Stationarity]]

### Stylised facts
Patterns found in almost all asset returns: fat tails, volatility clustering, near-zero autocorrelation, and correlations that rise in crises.

### Survivorship bias
Studying only assets that still exist or succeeded today, which makes past performance look better than it was.

---

## T

### Target
The quantity a model predicts. Ours: the 1-day return $P_{t+1}/P_t - 1$ or the 3-day return $P_{t+3}/P_t - 1$.

### Ticker
An asset's trading symbol (e.g., SPY). Symbols can be **reused** by a different company (GOLD → Gold.com; Barrick is now B).

### Time-series
Looking at **one asset over time** (e.g., does BTC's own past predict BTC's future?). Opposite: [[#Cross-sectional]].

### Trading calendar
The list of days an exchange is open.

### Transaction costs
Brokerage fees, the bid–ask spread and slippage paid on each trade. Critical for daily strategies.

### Turnover
How much of the portfolio changes at each rebalance: $\frac12\sum_i |w_{i,t} - w_{i,t-1}|$.

---

## U

### Universe
The full list of assets the strategy can choose from: 20 tradeables + SPY. → `src/universe.py`

---

## V

### Variance
The average squared distance from the mean: $s^2 = \frac{1}{T-1}\sum (r_t - \bar r)^2$.

### Variance ratio VR(q)
The $q$-day variance divided by $q$ × the 1-day variance. = 1 for a random walk; > 1 = momentum; < 1 = reversal.

### Volatility
The standard deviation of returns: the typical size of a move. It's usually quoted per year. → [[Volatility]]

### Volatility clustering
Big moves follow big moves and calm follows calm; the *size* of returns is predictable, their *direction* is not. → [[Volatility Clustering]]

### Volatility scaling (vol-scaled)
Dividing a return or signal by its recent volatility so that assets are comparable: $M_{i,t}/\hat\sigma_{i,t}$ or $r_t/\hat\sigma_{t-1}$.

### Volume
The number of shares (or coins, or dollars for crypto) traded in a day.

---

## W

### Walk-forward backtest
Testing a strategy by repeatedly training on the past and testing on the next unseen period, stepping forward through time.

### Wealth index
The value of \$1 invested at the start: $W_t = \prod_{s \le t}(1 + R_s)$. → [[Prices, Returns and Stationarity]]

### White noise
A series with zero mean, constant variance and no autocorrelation. Pure unpredictability.

### Wide format
A table with one row per date and one column per ticker.

### Winsorise
Capping extreme values at a chosen percentile (e.g., 1st and 99th) to limit the influence of outliers.

---

## Z

### z-score
See [[#Standardised return (z-score)]].
