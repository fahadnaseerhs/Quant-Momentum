# 02 — Data Cleaning

**Phase in the pipeline:** Step 2 of `Data → Cleaning → Features → EDA → Statistics → Models → Portfolio → Backtest → Risk → Costs → Robustness`.

**Status:** ✅ Built, run, and verified (2026-09-27).

**Prerequisite:** [[01 - Data Collection]] produced `data/raw/prices_daily.parquet` (2096 calendar-day rows × 21 tickers).

**Scope change during this task:** the project moved from **monthly** to **daily** frequency. We now predict the **next 1-day** or **next 3-day** return (Section 6).

---

## 1. The question

> Raw prices for 21 assets live on **two different trading calendars** (equities: weekdays only; crypto: every day). How do we produce a **single, coherent, leakage-free daily dataset** that every later step can use without special cases?

---

## 2. Finance concept — the trading calendar

An exchange has opening hours. The NYSE trades Monday–Friday, minus about ten holidays, giving roughly **252 trading days per year**. On a Saturday, AAPL has no price: not zero, not Friday's price, simply **undefined**.

Crypto has no closing bell. BTC trades every day, about **365 days per year**.

Merged on calendar days, equities show NaN on weekends and holidays while crypto is always filled. That is truthful, but unusable for **cross-sectional** research, where every question has the form *"on day $t$, rank all 21 assets."* A ranking with half the assets missing means nothing.

**We force every asset onto one calendar: the days the NYSE was open.** You cannot trade an equity portfolio on a Sunday, so a Sunday ranking is useless.

**How we get the NYSE calendar exactly:** we take the dates on which SPY actually traded. Generic "business day" calendars get exchange-specific holidays wrong (Good Friday is an NYSE holiday but not a federal one; Veterans Day is the opposite). SPY's real trading dates cannot be wrong.

---

## 3. Alignment — keeping only trading days

**Intuition:** you track the weight of 21 people. Fifteen weigh in only on weekdays, six weigh in daily. To compare everyone fairly every weekday, you keep only the weekday readings.

Formally, for each trading day $t$ and asset $i$, we keep the most recent price at or before $t$:

$$P_{i,t}^{aligned} = P_{i,\tau}, \quad \tau = \max\{s \le t : P_{i,s} \text{ exists}\}$$

This is **Last-Observation-Carried-Forward (LOCF)**, the standard way to line up data that arrives on different schedules. Crypto has a price every day, so for our data $\tau = t$ always. The formula matters when a gap appears (Section 5).

**Order matters: align first, compute returns second.** Once weekend rows are dropped, Monday's crypto return is measured Friday → Monday, so it **still contains the weekend's price move**. Computing returns on the 7-day grid and then dropping weekends would throw away Saturday's and Sunday's returns entirely.

**Result:** 2096 calendar days → **1439 trading days**.

---

## 4. Finance concept — leakage, and why we never backfill

The scope document's most important rule:

> The model must never use information that was unavailable at the prediction time.

In probability theory, the information known up to time $t$ is called the **filtration** $\mathcal{F}_t$. Every feature must satisfy $X_t \in \mathcal{F}_t$.

**Backfilling** fills a missing price on day $t$ with a price from a later day $s > t$. For a strategy trading on day $t$, that hands it tomorrow's answer. This is **lookahead bias**, the main reason strategies look brilliant in backtests and fail with real money.

**Rule:** cleaning may forward-fill (use the past). It may never backfill.

---

## 5. Missing values that survive alignment

| Case | Example | Policy | Reasoning |
|---|---|---|---|
| **Pre-existence** | A token listed in 2022 has no 2021 prices | Leave NaN | Inventing pre-listing prices pretends the asset was investable when it wasn't (a form of survivorship bias). |
| **Short gap (≤ 2 trading days)** | One or two bad quotes | Forward-fill from the last real price | Value barely changes over one or two days; deleting the rows would distort volatility. |
| **Long gap (> 2 trading days)** | Trading halt, delisting, ticker change | Leave NaN and **list it in the log** | A long gap usually signals a real event. Filling it would hide the event. |

**Volume is never filled.** A missing volume day is not "the same volume as yesterday"; it is unknown.

**Our data:** zero fills and zero long gaps were needed. Every equity traded on every SPY date, and crypto trades daily. The rules exist so that the pipeline stays correct if the universe changes.

---

## 6. Frequency — why daily, and what it costs

### 6.1 The decision

We work at **daily** frequency and predict one of two targets. On day $t$, using only information up to the close of day $t$:

| Target | Formula | Meaning |
|---|---|---|
| 1-day | $R_{i,t\to t+1} = \dfrac{P_{i,t+1}}{P_{i,t}} - 1$ | Tomorrow's return |
| 3-day | $R_{i,t\to t+3} = \dfrac{P_{i,t+3}}{P_{i,t}} - 1$ | Total return over the next three days (not the third day alone) |

The targets are built in Task 03; cleaning only prepares the daily returns they come from.

### 6.2 Three costs of going daily

1. **More noise.** A single day's return is dominated by random news and order flow. Expect predictive correlations that are small (a few percent) but possibly meaningful across ~1400 days × 20 assets.
2. **More trading.** Rebalancing daily trades far more often than monthly. Transaction costs stop being a footnote and become the deciding test.
3. **Overlapping 3-day targets.** Monday's 3-day target (Tue+Wed+Thu) and Tuesday's (Wed+Thu+Fri) share two days. If training data ends on Monday and testing starts on Tuesday, the model has already seen part of the test answer. The fix, used in Task 09, is an **embargo**: a gap of at least 3 days between the training and testing periods.

### 6.3 A known imperfection: different closing times

yfinance's daily crypto bar ends at **midnight UTC (8 pm New York)**; equities close at **4 pm New York**. So a crypto "close" includes four extra hours of news. This barely matters for ranking assets on their own momentum. It matters more if one day we use crypto to predict equities, so it is documented here and revisited then.

---

## 7. Two definitions of return

We save both. They answer different questions.

### 7.1 Simple return

$$R_{i,t} = \frac{P_{i,t}}{P_{i,t-1}} - 1$$

**Intuition:** \$100 invested yesterday is worth \$100 × $(1 + R_{i,t})$ today. It is the number an investor actually experiences.

**Adds up across assets.** A portfolio's return is the weighted sum of its holdings' simple returns:

$$R_{p,t} = \sum_i w_i R_{i,t}$$

That is why every P&L and backtest uses simple returns.

**Does not add up across time.** +50% then −50% is not 0%: $(1.5)(0.5) - 1 = -25\%$. Over time, simple returns compound by multiplication.

### 7.2 Log return

**Intuition:** we want a return we can simply *add* over time. Logarithms turn products into sums:

$$\ln \prod_{t}(1 + R_t) = \sum_{t} \ln(1 + R_t)$$

So we define

$$r_{i,t} = \ln\left(\frac{P_{i,t}}{P_{i,t-1}}\right) = \ln(1 + R_{i,t})$$

A 3-day log return is just the sum of three daily log returns.

**Does not add up across assets.** A weighted sum of log returns is not the portfolio's log return.

**Why keep it:** log returns are closer to a normal (bell-curve) distribution, so regressions and statistical tests behave better on them.

### 7.3 Which to use

| Purpose | Use |
|---|---|
| Portfolio, backtest, P&L | Simple |
| Regression, t-tests, models assuming near-normality | Log |
| Rolling volatility (Task 03) | Log |

For daily moves the two are nearly identical (a +1% simple return is a +0.995% log return). They diverge on big days, which crypto has many of.

---

## 8. Finance lesson from this task — ticker symbols get reused

The first cleaning run showed `GOLD` (meant to be Barrick Gold) with **49.7% annual volatility** and ±19% single-day moves, too wild for a large gold miner.

**The cause:** Barrick changed its symbol to **`B`** in 2025. The symbol `GOLD` now belongs to **Gold.com, Inc.**, a precious-metals dealer, and yfinance returns *that* company's history under `GOLD`. We had been studying the wrong company for the whole sample.

**The fix:** switch to `B`, but first check that `B`'s history isn't spliced with its previous owner, Barnes Group (acquired in 2025). Checks passed: no price jump, 0.73 daily correlation with gold (GLD), 36% annual vol, normal for a miner.

**General rule:** when a data source looks up history by *today's* symbol, a reused symbol silently swaps in another company. This is a cousin of survivorship bias. **Sanity-check volatility and name/sector for every ticker.** The volatility table in the cleaning log is how this bug was caught.

---

## 9. The environment

### 9.1 Module vs script

| File | Type | Role |
|---|---|---|
| `src/cleaning.py` | **Module**: a library of functions | Defines the building blocks. Nothing happens when it is imported. |
| `scripts/02_clean_data.py` | **Script**: a program you run | Loads raw data, calls the module's functions in order, saves results. |

**Why split them:** later tasks reuse the same functions. Task 03 applies them to new columns; robustness tests re-run cleaning with different settings (e.g., a 5-day fill limit). Functions in a module can also be tested one at a time.

### 9.2 Functions in `src/cleaning.py`

| Function | Job | Section |
|---|---|---|
| `trading_calendar(prices, "SPY")` | Dates SPY traded = NYSE calendar | 2 |
| `align_to_calendar(df, calendar)` | Keep only trading-day rows | 3 |
| `nan_runs(series)` | Find each run of consecutive missing values | 5 |
| `fill_short_gaps(df, max_fill=2)` | Forward-fill short runs, report long ones | 5 |
| `to_returns(prices, "simple" or "log")` | Daily returns | 7 |
| `audit(...)` | Numbers for the cleaning log | 9.4 |

### 9.3 What the script does

```text
load raw prices + volume
  → build NYSE calendar from SPY
  → align prices and volume to it
  → forward-fill short price gaps (≤ 2 days)
  → compute simple and log returns
  → save 4 parquet files
  → write and print the audit log
```

### 9.4 Outputs (`data/processed/`)

| File | Contents | Shape |
|---|---|---|
| `prices_daily_clean.parquet` | Aligned, gap-handled adjusted closes | 1439 × 21 |
| `volume_daily_clean.parquet` | Aligned volume, never filled | 1439 × 21 |
| `returns_daily.parquet` | Simple returns | 1438 × 21 |
| `returns_daily_log.parquet` | Log returns | 1438 × 21 |
| `cleaning_log.txt` | Audit trail: fills, gaps, volatility and extremes per ticker | text |

Returns have one row fewer than prices because the first day has no previous price.

---

## 10. Guide to run it

From the project folder, with the environment activated:

```
.venv\Scripts\activate
python scripts/02_clean_data.py
```

Runs in about a second and prints the audit log.

**If the universe changes** (e.g., a ticker is swapped in `src/universe.py`), rerun `01_fetch_data.py` first, then this script.

---

## 11. Expected outcome (actual results)

| Check | Expected | Actual |
|---|---|---|
| Trading-day rows | ≈ 252 × 5.7 | **1439** (2021-01-04 → 2026-09-25) |
| Any infinite values | None | None |
| Any return ≤ −100% | None (impossible to lose more than everything) | None |
| Fills / long gaps | Few or none | 0 / 0 |

**Annual volatility by asset class** ($\sigma_{annual} = \sigma_{daily}\sqrt{252}$):

| Class | Assets | Annual vol |
|---|---|---|
| Short Treasuries | SHY | 1.9% |
| Long Treasuries, gold, REITs, commodities, market | TLT, GLD, VNQ, DBC, SPY | 15–19% |
| Oil, large tech, gold miner | XOM, CVX, USO, AAPL, MSFT, GOOGL, B | 25–37% |
| High-beta equity | META, NVDA | 43–51% |
| Crypto and crypto-proxy | BTC, ETH, MSTR, LINK, SOL, AVAX | 57–116% |

The spread from 1.9% to 116% is a **60× difference**. Ranking raw momentum across this universe would always put a crypto asset at the top or bottom. This table is the empirical case for **volatility-scaled momentum**, the method chosen in the universe decision.

---

## 12. What this task does *not* do

No features, no targets, no plots, no statistics, no models. Only: **raw calendar-day data → clean trading-day prices and returns.**

---

## 13. What comes next

**Task 03 — Exploring Returns** ([[03 - Exploring Returns]]): look at volatility, tails, correlation and autocorrelation before designing anything.

**Task 04 — Feature Engineering**, from the cleaned daily files:
- Momentum over windows measured in trading days (candidates: 5, 10, 21, 63)
- Rolling volatility, and **volatility-scaled momentum** $M_{i,t} / \sigma_{i,t}$
- Volume ratio, return relative to SPY
- The 1-day and 3-day forward-return targets, built so no feature on day $t$ touches any price after $t$

---

## 14. Related notes

- [[01 - Data Collection]] — raw data and adjusted-close mechanics
- [[_Methodology - README]] — folder conventions
- [[quant_equity_prediction_strategy_lab]] — original research scope (monthly framing now superseded by daily)
