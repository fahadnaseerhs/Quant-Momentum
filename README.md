# K-NN & Naive Bayes on 22 Years of Tech Stocks

### Branch `knn-naive-bayes`: what can two from-scratch classifiers honestly predict about AAPL, MSFT, NVDA, GOOGL and META?

> **The short version.** We built K-Nearest Neighbours and Gaussian Naive Bayes from scratch (NumPy, Pandas and Matplotlib only) and tested them with walk-forward retraining, a leakage gap, simple baselines and significance tests.
>
> - **Tomorrow's direction:** about 50%. Neither model beat "always guess up". Following their signals lost money.
> - **Size of tomorrow's move:** no edge in 2026 either.
> - **Next month's volatility regime (high vs low):** **66–68% accuracy vs 55%** for guessing, p < 0.001 over 2012–2026. Most of this comes from volatility *persisting*. The rule "next month = this month" gets 66% too. K-NN's real extra is a **17% more accurate volatility-level forecast**. Naive Bayes makes good calls but gives **over-confident probabilities**.
>
> The models cannot tell you *where* the price goes. They can tell you *how rough the ride will be*.

This branch is a CS471 Machine Learning assignment (Naive Bayes and K-NNs) built on the data of the main Quant-Momentum project. The original project README lives on `main`.

---

## 1. The two classifiers in one paragraph each

**K-NN.** K-NN stores every training day. To predict, it standardises the inputs with the training mean and standard deviation, measures the Euclidean distance to every stored day, takes the K closest, and averages what happened after them. That average is the prediction, and the spread of the neighbours' outcomes is the shaded band in the graphs. K is chosen on a validation period, never on the test period.

**Gaussian Naive Bayes.**
`P(class | x) ∝ P(class) · Π P(xⱼ | class)`
Each `P(xⱼ | class)` is a normal curve with a mean and variance learned per class. The model adds log-probabilities to avoid underflow, and a small variance floor avoids division by zero. "Naive" means the features are assumed independent within a class. Here that assumption is badly wrong, because 5-, 21-, 63- and 252-day volatility all measure the same thing. That is why its probabilities come out too extreme.

## 2. Data and pre-processing

| | |
|---|---|
| Source | Yahoo Finance (yfinance) daily adjusted closes, `data/long/processed/prices_daily_clean.parquet` |
| Stocks | AAPL, MSFT, NVDA, GOOGL (from Aug 2004), META (from May 2012) |
| Range | 2 Jan 2004 → 9 Oct 2026, 5,729 trading days |
| Cleaning | NYSE calendar, forward-fill gaps of ≤ 2 days, never back-fill |
| Features | past returns (1/5/21/63 d), size of today's move, volatility over 5/21/63/252 d (annualised %) |

**Leakage controls**
- Data is split by time and never shuffled.
- Scaling and the "normal" threshold are computed from training data only.
- A training row is used only once its outcome has finished, which gives a 21-day embargo for monthly targets.
- K is chosen on an earlier period.
- The test period is run once.

## 3. The three experiments

| | 1. Direction | 2. Next-day size | 3. Next-month regime |
|---|---|---|---|
| Target | up / down tomorrow | \|r(t+1)\| above median | next-21-day vol above median |
| Test | Jan–Oct 2026, daily | Jan–Oct 2026, daily | Jan 2012–Sep 2026, monthly |
| K (chosen on) | 200 (2025) | 400 (2025) | 100 (2008–2011) |
| Script | `knn_nb/run.py` | `knn_nb/run_vol.py` | `knn_nb/run_regime.py` |

Every model is retrained at the start of each month on all data available before that day (walk-forward). The baselines are:
- **Always-majority:** the most common class, chosen in hindsight, so it is a generous baseline.
- **Persistence:** "the future looks like the present".

## 4. Results

**Problem 1: direction (2026).**
- K-NN scored 42.5–49.2% and Naive Bayes 46.1–53.4%, against a 50.3–53.4% "always up" baseline. All p-values are ≥ 0.50.
- Following K-NN's signals lost money on every stock, from −5% to −61%. Buy-and-hold made +11% to +25%.

**Problem 2: next-day size (2026).** Pooled accuracy was 54.9% (K-NN) and 52.8% (Naive Bayes), against 54.6% for always-majority. There is no edge.

**Problem 3: next-month volatility regime (2012–2026, 843 stock-months)**

| | Majority | Persistence | K-NN | Naive Bayes |
|---|---|---|---|---|
| AAPL | 67.8% | 69.5% | 68.9% | 73.4% |
| MSFT | 50.8% | 58.2% | 61.0% | 63.3% |
| NVDA | 58.2% | 69.5% | 69.5% | 70.6% |
| GOOGL | 50.8% | 66.7% | 63.8% | 68.4% |
| META | 54.8% | 63.7% | 68.9% | 63.7% |
| **All pooled** | **54.7%** | **65.6%** | **66.3%** | **68.1%** |
| 2026 only | 64.4% | 60.0% | 66.7% | 55.6% |

- **Both models beat majority with p < 0.001.** Each stock is significant on its own except AAPL, where guessing "low" is already right 68% of the time.
- **Neither clearly beats persistence on accuracy** (p = 0.33 for K-NN, 0.06 for Naive Bayes).
- **K-NN beats persistence on the volatility level:** a mean absolute error of 9.2 vs 11.1 volatility points.
- **Naive Bayes is over-confident.** When it says "0–20% chance" of a high month, 31% were high. When it says "80–100%", 75% were.
- **2026 alone (45 predictions):** nothing is significant, because a calm year has too few regime changes to predict.

## 5. Why these percentages make sense in the real world

- **Direction is about 50%.** Any pattern in past prices that predicted tomorrow's direction would be traded away by other market participants. What moves the price tomorrow is new information that is not yet in the data. The "always up" baseline sits slightly above 50% only because tech stocks drifted upward.
- **Single-day size is noise.** One day is dominated by random news. In 2026, volatility moved only 2–4× between its calmest and wildest month, compared with 14–21× over 2005–2025. With so little variation there was nothing to forecast.
- **Monthly risk is predictable because of volatility clustering.** Turbulence lasts for months: the COVID crash in 2020 and the rate shock in 2022 are examples. Averaging over a month removes the day-to-day noise, and the correlation with the next month rises to about 0.5–0.6. The VIX, option prices, GARCH models and bank risk limits all rely on this fact.
- **Accuracy stops around 70% because shocks arrive without warning.** The first month of every crisis is missed, and borderline months near the threshold are close to coin flips.
- **The models tie with persistence** because their only useful input is "how volatile was it recently", and persistence already uses exactly that.

## 6. Graphs (`knn_nb/figures/`)

| File | Shows |
|---|---|
| `g1_knn_shadow_vs_actual.png` | Problem 1: K-NN predicted next-day return (shadow) vs actual. The prediction is flat and the reality is noise |
| `g2_nb_prob_vs_actual.png` | Problem 1: Naive Bayes P(up) hugs 50% and has no relation to actual up/down days |
| `g3_follow_vs_hold.png` | Problem 1: growth of $1 from following each model vs buy-and-hold |
| `g4`–`g6_vol_*.png` | Problem 2: next-day size. Accuracy is no better than the baselines |
| `g7_regime_process.png` | Problem 3: how each prediction is made (training block, 21-day embargo, predicted month) |
| `g8_regime_knn_shadow_vs_actual.png` | Problem 3: K-NN predicted monthly volatility (shadow) vs actual, 2012–2026, per stock |
| `g9_regime_nb_prob_vs_actual.png` | Problem 3: Naive Bayes P(high) vs actual high (red) / low (green) months |
| `g10_regime_scorecard.png` | Problem 3: accuracy vs both baselines, per stock, pooled, and 2026 alone |
| `g11_regime_trust_check.png` | Problem 3: calmest-to-stormiest staircase (K-NN) and probability calibration (Naive Bayes) |

## 7. Files and how to run

```
knn_nb/
├── knn.py               K-NN from scratch
├── naive_bayes.py       Gaussian Naive Bayes from scratch
├── run.py               Problem 1 – direction             → results.csv, g1–g3
├── run_vol.py           Problem 2 – next-day size         → results_vol.csv, g4–g6
├── run_regime.py        Problem 3 – next-month regime     → results_regime.csv, g7–g11
├── figures/             all graphs
└── report/
    ├── template.docx               course assignment template
    ├── build_report.py             fills the template (needs python-docx)
    └── KNN_NaiveBayes_Report.docx  the assignment report
```

Run the three experiments, then rebuild the report:

```bash
.venv/Scripts/python.exe knn_nb/run.py
```

```bash
.venv/Scripts/python.exe knn_nb/run_vol.py
```

```bash
.venv/Scripts/python.exe knn_nb/run_regime.py
```

```bash
python knn_nb/report/build_report.py
```

The report still needs two things added by hand: the scanned K-NN worked on paper (Section 9), and the student name and registration number on the cover.
