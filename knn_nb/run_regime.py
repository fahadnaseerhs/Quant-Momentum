"""Problem 3: will the NEXT MONTH be a high-volatility or low-volatility month for this stock?

Set-up fixed before looking at results:
  * One prediction per stock at the first trading day of each month, for the next 21 trading days.
  * Target : realised volatility of the next 21 daily returns (annualised %).
             "High" = above that stock's median monthly volatility in the training data.
  * Train  : every past day whose 21-day outcome had fully finished before the prediction date
             (this is the 21-day embargo - no overlap with the future).
  * K      : chosen on 2008-2011 only. Test: 2012 -> latest month with a complete outcome.
  * Baselines: "always the majority class" and persistence ("next month = this month").
"""
from __future__ import annotations

import sys
from math import erf, sqrt
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle

sys.path.insert(0, str(Path(__file__).parent))
from knn import KNN
from naive_bayes import GaussianNB

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).parent / "figures"
OUT.mkdir(exist_ok=True)
TICKERS = ["AAPL", "MSFT", "NVDA", "GOOGL", "META"]
H = 21                                              # horizon: one trading month
ANN = sqrt(252) * 100                               # daily sd -> annualised %
K_GRID = [10, 20, 50, 100, 200, 400]
VAL = ("2008-01-01", "2012-01-01")
TEST_START = "2012-01-01"
FEATS = ["vol5", "vol21", "vol63", "vol252", "ret21"]
MIN_TRAIN = 500                                     # need ~2 years of history before predicting
COL = {"majority": "#c7c7c7", "persistence": "#7f7f7f", "K-NN": "#1f77b4", "Naive Bayes": "#ff7f0e"}

px = pd.read_parquet(ROOT / "data/long/processed/prices_daily_clean.parquet")[TICKERS]


def build(t: str) -> pd.DataFrame:
    p = px[t].dropna()
    r = p.pct_change()
    f = pd.DataFrame({
        "vol5": r.rolling(5).std() * ANN, "vol21": r.rolling(21).std() * ANN,
        "vol63": r.rolling(63).std() * ANN, "vol252": r.rolling(252).std() * ANN,
        "ret21": p.pct_change(21) * 100,
    })
    f["target"] = r.rolling(H).std().shift(-H) * ANN          # vol of days t+1 .. t+21
    f["tdate"] = pd.Series(p.index, index=p.index).shift(-H)  # day the outcome is complete
    return f.dropna(subset=FEATS)


def pval_above(acc: float, base: float, n: int) -> float:
    z = (acc - base) / sqrt(base * (1 - base) / n)
    return 0.5 * (1 - erf(z / sqrt(2)))


def walk(d: pd.DataFrame, start: str, end: str | None, k: int) -> pd.DataFrame:
    known = d.dropna(subset=["target"])
    te = known[(known.index >= start) & ((known.index < end) if end else True)]
    month_starts = te.groupby(te.index.to_period("M")).head(1)
    rows = []
    for dt, row in month_starts.iterrows():
        tr = known[known["tdate"] < dt]             # outcome finished before we predict = embargo
        if len(tr) < MIN_TRAIN:
            continue
        normal = tr["target"].median()              # the stock's "normal" monthly vol, train only
        X, y = tr[FEATS].values, tr["target"].values
        knn = KNN(k).fit(X, y)
        nb = GaussianNB().fit(X, (y > normal).astype(int))
        x = row[FEATS].values.astype(float)
        nbh = knn.neighbours(x)
        rows.append((dt, row["target"], normal, nbh.mean(), np.percentile(nbh, 25), np.percentile(nbh, 75),
                     nb.prob_up(x), row["vol21"]))
    cols = ["date", "actual", "normal", "knn", "knn_lo", "knn_hi", "nb_phigh", "vol21_now"]
    return pd.DataFrame(rows, columns=cols).set_index("date")


def score(r: pd.DataFrame) -> dict:
    high = r.actual > r.normal
    maj = max(high.mean(), 1 - high.mean())
    acc = {"majority": maj,
           "persistence": ((r.vol21_now > r.normal) == high).mean(),
           "K-NN": ((r.knn > r.normal) == high).mean(),
           "Naive Bayes": ((r.nb_phigh > .5) == high).mean()}
    return {**acc, "n": len(r),
            "p K-NN>maj": pval_above(acc["K-NN"], maj, len(r)),
            "p NB>maj": pval_above(acc["Naive Bayes"], maj, len(r)),
            "p K-NN>persist": pval_above(acc["K-NN"], acc["persistence"], len(r)),
            "p NB>persist": pval_above(acc["Naive Bayes"], acc["persistence"], len(r)),
            "K-NN MAE (vol pts)": (r.actual - r.knn).abs().mean(),
            "persistence MAE (vol pts)": (r.actual - r.vol21_now).abs().mean(),
            "band coverage": ((r.actual >= r.knn_lo) & (r.actual <= r.knn_hi)).mean()}


data = {t: build(t) for t in TICKERS}

# ---- choose K on 2008-2011 only ----
val = {k: float(np.mean([((w.actual - w.knn) ** 2).mean()
                         for t in TICKERS if len(w := walk(data[t], *VAL, k))])) for k in K_GRID}
best_k = min(val, key=val.get)
print("validation MSE by K (2008-2011):", {k: round(v, 2) for k, v in val.items()}, "-> K =", best_k)

# ---- test 2012 -> latest ----
res = {t: walk(data[t], TEST_START, None, best_k) for t in TICKERS}
pooled = pd.concat(res, names=["ticker", "date"])
tab = pd.DataFrame({t: score(r) for t, r in res.items()}).T
tab.loc["ALL (pooled)"] = score(pooled)
y26 = pooled[pooled.index.get_level_values("date") >= "2026-01-01"]
tab.loc["2026 only (pooled)"] = score(y26)
pd.set_option("display.width", 250)
print(tab.astype(float).round(3).T)
tab.to_csv(Path(__file__).parent / "results_regime.csv")
first, last = pooled.index.get_level_values("date").min(), pooled.index.get_level_values("date").max()

# =====================================================================================
# G7  PROCESS: how one prediction is made (no leakage)
# =====================================================================================
fig, ax = plt.subplots(figsize=(12, 4.6))
ax.set_xlim(0, 100); ax.set_ylim(0, 10); ax.axis("off")
ax.add_patch(Rectangle((2, 5.2), 58, 1.6, color="#1f77b4", alpha=.25))
ax.text(31, 6.0, "TRAINING DATA\nevery past day whose next-21-day outcome is already finished",
        ha="center", va="center", fontsize=10)
ax.add_patch(Rectangle((60, 5.2), 12, 1.6, color="#d62728", alpha=.2))
ax.text(66, 6.0, "21-day gap\n(embargo)", ha="center", va="center", fontsize=9)
ax.add_patch(Rectangle((72, 5.2), 22, 1.6, color="#2ca02c", alpha=.25))
ax.text(83, 6.0, "NEXT 21 TRADING DAYS\n(what we predict)", ha="center", va="center", fontsize=10)
ax.annotate("", xy=(72, 4.6), xytext=(72, 3.3), arrowprops=dict(arrowstyle="->", lw=1.5))
ax.text(72, 2.9, "Prediction date = first trading day of the month", ha="center", fontsize=10, weight="bold")
ax.text(50, 1.4,
        "Inputs on that day: volatility over the last 5 / 21 / 63 / 252 days and the last-month return.\n"
        "K-NN: find the K most similar past days, average their next-month volatility.   "
        "Naive Bayes: P(next month is HIGH-vol | inputs).\n"
        "\"High\" = above this stock's median monthly volatility in the training data.  "
        "Then move forward one month, retrain, repeat.",
        ha="center", va="center", fontsize=9.5)
ax.text(1, 9.3, "How every prediction is made (walk-forward, retrained monthly)", fontsize=13, weight="bold")
ax.text(1, 8.4, f"K chosen on 2008-2011 only (K = {best_k}).  Test: {first:%b %Y} to {last:%b %Y}, "
        "one prediction per stock per month.", fontsize=10, color="#444")
fig.tight_layout(); fig.savefig(OUT / "g7_regime_process.png", dpi=130); plt.close(fig)

# =====================================================================================
# G8  K-NN: predicted next-month volatility (shadow) vs what actually happened
# =====================================================================================
fig, ax = plt.subplots(len(TICKERS), 1, figsize=(12, 14), sharex=True)
for a, t in zip(ax, TICKERS):
    r = res[t]
    a.fill_between(r.index, r.knn_lo, r.knn_hi, step="post", color="#1f77b4", alpha=.25,
                   label="K-NN predicted range (middle 50% of neighbours)")
    a.step(r.index, r.knn, where="post", color="#1f77b4", lw=1.3, label="K-NN prediction")
    a.step(r.index, r.actual, where="post", color="k", lw=1, label="actual next-month volatility")
    a.step(r.index, r.normal, where="post", color="#d62728", ls="--", lw=1, label="'normal' level (high/low line)")
    s = score(r)
    a.set_title(f"{t}   |   high/low accuracy: K-NN {s['K-NN']:.0%}, persistence {s['persistence']:.0%}, "
                f"always-majority {s['majority']:.0%}   |   actual inside shadow {s['band coverage']:.0%} of months",
                fontsize=9.5, loc="left")
    a.set_ylabel("annualised vol %")
ax[0].legend(loc="upper right", ncol=2, fontsize=8)
fig.suptitle("K-NN forecast of next month's volatility vs what actually happened (each step = one month)",
             fontsize=13, weight="bold")
fig.tight_layout(); fig.savefig(OUT / "g8_regime_knn_shadow_vs_actual.png", dpi=130); plt.close(fig)

# =====================================================================================
# G9  Naive Bayes: probability of a HIGH-vol month vs actual high/low months
# =====================================================================================
fig, ax = plt.subplots(len(TICKERS), 1, figsize=(12, 12), sharex=True)
for a, t in zip(ax, TICKERS):
    r = res[t]
    high = r.actual > r.normal
    a.fill_between(r.index, 0, r.nb_phigh, step="post", color="#ff7f0e", alpha=.35,
                   label="Naive Bayes P(next month is HIGH-vol)")
    a.axhline(.5, color="k", lw=.8, ls=":")
    a.scatter(r.index[high], np.full(high.sum(), 1.04), marker="|", s=60, color="#d62728", label="actually HIGH month")
    a.scatter(r.index[~high], np.full((~high).sum(), -0.04), marker="|", s=60, color="#2ca02c", label="actually LOW month")
    s = score(r)
    a.set_title(f"{t}   |   Naive Bayes accuracy {s['Naive Bayes']:.0%}  (persistence {s['persistence']:.0%}, "
                f"always-majority {s['majority']:.0%})", fontsize=9.5, loc="left")
    a.set_ylim(-.1, 1.1); a.set_ylabel("P(high)")
ax[0].legend(loc="upper right", ncol=3, fontsize=8, bbox_to_anchor=(1, 1.45))
fig.suptitle("Naive Bayes: predicted chance of a high-volatility month (orange) vs actual high (red) / low (green) months\n"
             "Above the dotted 50% line = model says HIGH", fontsize=12, weight="bold")
fig.tight_layout(); fig.savefig(OUT / "g9_regime_nb_prob_vs_actual.png", dpi=130); plt.close(fig)

# =====================================================================================
# G10  SCORECARD: accuracy vs baselines, per stock, pooled, and 2026 alone
# =====================================================================================
models = ["majority", "persistence", "K-NN", "Naive Bayes"]
rows_ = list(tab.index)
fig, ax = plt.subplots(figsize=(13, 5))
w = .2
xs = np.arange(len(rows_))
for i, m in enumerate(models):
    vals = tab[m].astype(float).values * 100
    bars = ax.bar(xs + (i - 1.5) * w, vals, w, color=COL[m], label=m if m != "majority" else "always-majority (baseline)")
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + .8, f"{v:.0f}", ha="center", fontsize=7.5)
ax.axhline(50, color="k", lw=.8, ls=":")
ax.set_xticks(xs, [f"{r}\n(n={int(tab.loc[r, 'n'])} months)" for r in rows_], fontsize=9)
ax.axvline(len(rows_) - 2.5, color="#999", lw=.8)
ax.set_ylim(0, 105); ax.set_ylabel("accuracy % (high vs low month)")
ax.legend(ncol=4, fontsize=9, loc="upper left")
ax.set_title("Scorecard: how often each method called the next month's volatility regime correctly\n"
             "grey = simple baselines (a model must beat these to add value)", fontsize=12, weight="bold")
fig.tight_layout(); fig.savefig(OUT / "g10_regime_scorecard.png", dpi=130); plt.close(fig)

# =====================================================================================
# G11  TRUST CHECK: when the model says calm/stormy, is it really calm/stormy?
# =====================================================================================
pooled["actual_rel"] = pooled.actual / pooled.normal
pooled["pred_rel"] = pooled.knn / pooled.normal
pooled["q"] = pd.qcut(pooled.pred_rel.rank(method="first"), 5, labels=["1\ncalmest", "2", "3", "4", "5\nstormiest"])
bins = [0, .2, .4, .6, .8, 1.0]
pooled["pbin"] = pd.cut(pooled.nb_phigh, bins, include_lowest=True,
                        labels=["0-20%", "20-40%", "40-60%", "60-80%", "80-100%"])
fig, ax = plt.subplots(1, 2, figsize=(13, 4.8))
g = pooled.groupby("q", observed=True)
v = g.actual_rel.mean()
bars = ax[0].bar(v.index.astype(str), v.values, color="#1f77b4")
ax[0].axhline(1, color="#d62728", ls="--", lw=1, label="normal level")
for b, val_, n in zip(bars, v.values, g.size().values):
    ax[0].text(b.get_x() + b.get_width() / 2, val_ + .03, f"{val_:.2f}x\n(n={n})", ha="center", va="bottom", fontsize=8.5)
ax[0].set(title="K-NN: months sorted into 5 groups by predicted volatility",
          xlabel="predicted group", ylabel="actual next-month vol / normal level", ylim=(0, 1.8))
ax[0].legend(loc="upper left")
g2 = pooled.assign(high=pooled.actual > pooled.normal).groupby("pbin", observed=True)
v2 = g2.high.mean() * 100
bars = ax[1].bar(v2.index.astype(str), v2.values, color="#ff7f0e")
ax[1].plot([0, 4], [10, 90], color="k", ls=":", lw=1, label="perfectly honest probabilities")
for b, val_, n in zip(bars, v2.values, g2.size().values):
    ax[1].text(b.get_x() + b.get_width() / 2, val_ / 2, f"{val_:.0f}%\n(n={n})", ha="center", fontsize=8.5, color="white", weight="bold")
ax[1].set(title="Naive Bayes: when it says X% chance of HIGH, how often was it high?",
          xlabel="Naive Bayes P(high)", ylabel="% of months that were actually HIGH", ylim=(0, 110))
ax[1].legend(loc="upper left")
fig.suptitle("Trust check (all stocks pooled, 2012 onward): do the predictions line up with reality?",
             fontsize=12, weight="bold")
fig.tight_layout(); fig.savefig(OUT / "g11_regime_trust_check.png", dpi=130); plt.close(fig)
print("figures saved to", OUT)
