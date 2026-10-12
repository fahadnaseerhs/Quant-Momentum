# 01 — Data Collection

**Phase in the pipeline:** Step 1 of `Data → Cleaning → Features → EDA → Statistics → Models → Portfolio → Backtest → Risk → Costs → Robustness`.

**Status:** Environment set up, script written. Data not yet pulled — user must run one command locally.

---

## 1. The question

> **"How does the data come in?"**

Every quant project starts here. Before we can build features, run statistics, or fit any model, we need a **clean, structured, time-indexed table of prices** for every asset we care about. Concretely:

- Which assets are we studying?
- Over what time range?
- At what frequency (daily / weekly / monthly)?
- From which source, and how do we know we can trust it?
- What exact format do we save it in so every downstream step can read it the same way?

If any of these is left vague, we will spend the rest of the project debugging data instead of debugging our signal. So this task is worth doing properly, even though nothing "quanty" happens in it yet.

---

## 2. The universe — what we chose and why

We picked **20 tradeable assets + 1 benchmark**, deliberately diverse across asset classes:

| Bucket | Assets | Purpose |
|---|---|---|
| **Crypto tokens** | BTC-USD, ETH-USD, SOL-USD, LINK-USD, AVAX-USD | Test whether momentum survives outside traditional equities |
| **Tech stocks** | AAPL, MSFT, NVDA, GOOGL, META | The classic momentum playground |
| **Gold** | GLD (ETF), B (Barrick — a gold miner; originally `GOLD`, see [[02 - Data Cleaning]] §8) | Safe-haven / inflation hedge behaviour |
| **Oil** | USO (ETF), XOM, CVX | Commodity + oil-major stocks |
| **Real-asset diversifiers** | VNQ (REITs), DBC (commodity basket), MSTR (crypto-treasury bridge) | Broaden exposure to real assets |
| **Bonds** | TLT (long Treasuries), SHY (short Treasuries) | Deliberate contrast — bonds have very different volatility |
| **Benchmark** | SPY | Not traded; only used to compute "relative-to-market" features |

**Why this mix instead of "20 US tech stocks"?**
Because the interesting question is not *"does momentum work on tech stocks?"* — that has been studied to death. The interesting question is *"does the same signal survive across genuinely different asset classes?"* If momentum works on BTC **and** gold **and** tech **and** oil, that is real evidence. If it only works on tech, we've probably rediscovered survivorship bias in a shiny wrapper.

**Why not RWA tokens like ONDO, PAXG, XAUT?**
These are on-chain tokens that our chosen data source (`yfinance`) does not cover. Adding them would require a second API (CoinGecko), which means two date grids, two formats, and twice the debugging surface. For a first pipeline, we deliberately keep the data plumbing simple. RWA tokens are on the roadmap for Version 2.

**Date range:** 2021-01-01 → today (~5 years of daily data).

---

## 3. The methodology of "getting" price data

### 3.1 What is a "price" anyway?

A stock or ETF's raw daily close price is **not directly usable** for return calculations. Two things can create fake jumps in the raw series:

1. **Stock splits** — a $200 stock does a 2-for-1 split and becomes $100 overnight. A naïve daily-return calculation would show a −50% day that never happened economically.
2. **Dividends** — the stock price drops by the dividend amount on the ex-dividend date. That is not a real loss for the investor; they got the cash.

The fix is the **adjusted close price**, which back-adjusts historical prices so that the return series reflects total shareholder experience (price + dividends) as if no splits had ever happened.

Mathematically, for a stock with unadjusted close $P_t$ and cumulative adjustment factor $f_t$:

$$P_t^{adj} = P_t \times f_t$$

The daily return of the *adjusted* series,

$$R_t = \frac{P_t^{adj}}{P_{t-1}^{adj}} - 1$$

is the return an investor would actually have earned. This is what every downstream feature (momentum, volatility, etc.) will be built from.

**In practice:** we tell `yfinance` `auto_adjust=True` and it returns an already-adjusted close series. One flag, one bug avoided.

### 3.2 What are we saving, and in what shape?

For each ticker we save two aligned tables:

- **Prices** — a wide DataFrame indexed by trading date, one column per ticker.
- **Volumes** — same shape.

$$\text{prices} \in \mathbb{R}^{T \times N}, \quad T = \text{trading days}, \quad N = 21 \text{ tickers}$$

This "wide" layout means every downstream calculation is a single vectorized pandas operation. Momentum for every asset at every date becomes one line of code, not a loop.

### 3.3 Why parquet, not CSV?

- **Speed** — parquet loads ~10–50× faster than CSV.
- **Type safety** — dates stay dates, floats stay floats. CSV loses type information every save/load cycle.
- **Size** — column-compressed, so the file is smaller.

CSV is fine for hand-inspection; parquet is what code should read.

### 3.4 The trading-calendar problem

- **Equities and ETFs** trade only US weekdays (excluding market holidays).
- **Crypto** trades 24/7, including weekends and holidays.

When we merge them into one table, we get a wide frame where crypto has values on Saturdays and Sundays but equities show NaN. That is expected and correct at this stage. We will decide how to reconcile it in **02 — Data Cleaning** (probably: keep only US trading days, forward-fill any residual gaps within a business week). For now we save the raw truth.

---

## 4. The environment

### 4.1 Folder structure

```
Quant_ Momentum/
├── .claude/            ← assistant memory + decisions (already set up)
├── Quant_Momentum/     ← Obsidian vault (this folder)
│   └── Methodology/    ← this note lives here
├── data/
│   ├── raw/            ← where fetched data lands (empty for now)
│   └── processed/      ← cleaned data (empty)
├── notebooks/          ← for research notebooks later
├── scripts/
│   └── 01_fetch_data.py    ← the fetch script
├── src/
│   ├── __init__.py
│   └── universe.py     ← the 21 tickers, in code
├── requirements.txt    ← Python dependencies
├── .gitignore
└── quant_equity_prediction_strategy_lab.md   ← scope of truth
```

**Design principle:** one source of truth per fact. The universe lives in `src/universe.py` — nowhere else. If we change the universe, we change that file, and every script pulls the new list automatically. No hard-coded ticker lists scattered around.

### 4.2 Dependencies (`requirements.txt`)

| Package | Why it's here |
|---|---|
| `pandas`, `numpy` | Data manipulation. The everyday workhorses. |
| `matplotlib`, `seaborn` | Charts. Used from EDA onward. |
| `yfinance` | The data source. Free, no key required. |
| `pyarrow` | Parquet reader/writer (pandas needs this under the hood). |
| `jupyter`, `ipykernel` | Notebooks. |
| `scipy`, `statsmodels` | Statistical tests (t-stats, p-values, regression) used in step 5. |
| `scikit-learn` | Linear regression baseline + later gradient-boosted models. |

Nothing exotic. Everything installs from PyPI with no compilation.

### 4.3 The fetch script's job (`scripts/01_fetch_data.py`)

Plain-language description (the actual code is in the file):

1. **Import** the 21 tickers from `src/universe.py`.
2. **Call `yfinance.download(...)`** with `auto_adjust=True`. This is a single batched network call for all 21 symbols.
3. **Split** the returned multi-column response into a clean prices frame and a clean volumes frame.
4. **Write** both to `data/raw/*.parquet`.
5. **Write** a one-page log to `data/raw/fetch_log.txt` (when, how many rows, date range) so we can later see what was pulled and when.
6. **Print** a sanity report to the terminal — shape, date range, and the top-5 NaN percentages per column.

The script is idempotent: rerun it any time to refresh with newer prices, without breaking any downstream code.

---

## 5. Guide to run it

**Once, on this machine:**

```
cd "C:\Users\USER\OneDrive\Desktop\Quant_ Momentum"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

This creates a project-local Python environment (`.venv/`) and installs everything from `requirements.txt` into it. `.venv/` is ignored by git.

**Every time you want fresh data:**

```
.venv\Scripts\activate
python scripts/01_fetch_data.py
```

Total runtime: **~10–30 seconds** depending on connection.

---

## 6. Expected outcome

### 6.1 Files on disk

After a successful run, these appear:

```
data/raw/prices_daily.parquet    (~50-200 KB)
data/raw/volume_daily.parquet    (~50-200 KB)
data/raw/fetch_log.txt           (four lines of metadata)
```

### 6.2 Console output

Something close to:

```
Fetching 21 tickers from 2021-01-01 ...
[**********************100%***********************]  21 of 21 completed

--- Sanity check ---
Shape:            (1450, 21)   (rows=days, cols=tickers)
Date range:       2021-01-04 → 2026-09-26
Tickers pulled:   ['BTC-USD', 'ETH-USD', 'SOL-USD', ..., 'SPY']

NaN % per ticker (top 5):
BTC-USD    0.28
ETH-USD    0.28
SOL-USD    0.28
LINK-USD   0.28
AVAX-USD   0.28

Saved: .../data/raw/prices_daily.parquet
Saved: .../data/raw/volume_daily.parquet
```

### 6.3 What to check

| Check | Expected | If it fails |
|---|---|---|
| `data/raw/prices_daily.parquet` exists | ✅ | Rerun; check internet |
| 21 columns | ✅ | If fewer, one ticker was renamed or delisted — investigate |
| Date range ends near today | ✅ | If it ends months ago, yfinance may be rate-limited — wait and retry |
| Equity NaN % near 0 | ✅ | Anything > 5% means a ticker is broken |
| Crypto NaN % around 25–30 % | ✅ | This is weekends — expected, not a problem |
| No "MISSING tickers" line | ✅ | If present, that ticker didn't return data — check spelling / delisting |

**Interpretation of that ~28% NaN for crypto:** 5 out of 7 days of the week × trading day rows would give a ratio close to `2/7 ≈ 0.286` if crypto had *no* weekend rows. In our case yfinance does include crypto weekend rows for the crypto tickers, so the NaN pattern we see is more complex — the count reflects where the master index sits. The key point: **NaNs at this stage are structural (calendar mismatch), not data errors.** They vanish once we align to a common calendar in step 02.

---

## 7. What this task does *not* do

- It does not compute returns.
- It does not compute features.
- It does not align crypto to the equity calendar.
- It does not handle missing values.
- It does not train, predict, or trade anything.

All of that is deliberately postponed. **This task is only about establishing a trustworthy, reproducible raw dataset.** If the raw data is wrong, everything above it is wrong.

---

## 8. Where this leads

Once this step succeeds:

- **02 — Data Cleaning** — align calendars, handle NaNs, compute daily simple and log returns, save a "research-ready" processed dataset.
- **03 — Feature Engineering** — build momentum, volatility, volume ratio, and relative-to-market features on the cleaned dataset.
- **04 — Exploratory Analysis** — return distributions, momentum buckets, first scatter plot of $M_{3M,t}$ vs $R_{t+1}$.

---

## 9. Related notes

- [[00 - Project Introduction]] — what the project is
- [[quant_equity_prediction_strategy_lab]] — the full research scope
- [[_Methodology - README]] — how this folder works
