"""Problem 2: predict the SIZE of tomorrow's move (volatility), not its direction.

Same honest set-up as run.py: train on 2004 -> end of 2025, predict each day of 2026,
retrain monthly on data realised before the month, K chosen on 2025 only.

K-NN  : predicts tomorrow's absolute return |r(t+1)| (mean of the K most similar past days).
Naive Bayes : P(tomorrow is a "big" day), big = |r(t+1)| above the training-period median.
Baselines   : (a) majority class, (b) persistence "big tomorrow if today was big",
              (c) for size: today's 21-day vol scaled to an expected |r|.
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

sys.path.insert(0, str(Path(__file__).parent))
from knn import KNN
from naive_bayes import GaussianNB

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).parent / "figures"
OUT.mkdir(exist_ok=True)
TICKERS = ["AAPL", "MSFT", "NVDA", "GOOGL", "META"]
TEST_START = "2026-01-01"
K_GRID = [10, 20, 50, 100, 200, 400]
FEATS = ["abs1", "vol5", "vol21", "vol63", "ret21"]
GAUSS_ABS = sqrt(2 / np.pi)                         # E|r| = sd * sqrt(2/pi) for a normal

px = pd.read_parquet(ROOT / "data/long/processed/prices_daily_clean.parquet")[TICKERS]


def build(t: str) -> pd.DataFrame:
    p = px[t].dropna()
    r = p.pct_change()
    f = pd.DataFrame({
        "abs1": r.abs(),                            # size of today's move
        "vol5": r.rolling(5).std(), "vol21": r.rolling(21).std(), "vol63": r.rolling(63).std(),
        "ret21": p.pct_change(21),                  # recent trend (falls tend to raise vol)
    })
    f["target"] = r.shift(-1).abs()                 # size of tomorrow's move
    f["tdate"] = pd.Series(p.index, index=p.index).shift(-1)
    return f.dropna()


def pval_above(acc: float, base: float, n: int) -> float:
    z = (acc - base) / sqrt(base * (1 - base) / n)
    return 0.5 * (1 - erf(z / sqrt(2)))


def walk(d: pd.DataFrame, start: str, end: str | None, k: int) -> pd.DataFrame:
    te = d[(d.index >= start) & ((d.index < end) if end else True)]
    rows = []
    for _, chunk in te.groupby(te.index.to_period("M")):
        tr = d[d["tdate"] < chunk.index[0]]         # only outcomes known before the month began
        thr = tr["target"].median()                 # "big day" threshold from training data only
        knn = KNN(k).fit(tr[FEATS].values, tr["target"].values)
        nb = GaussianNB().fit(tr[FEATS].values, (tr["target"] > thr).astype(int).values)
        for dt, row in chunk.iterrows():
            x = row[FEATS].values.astype(float)
            nbh = knn.neighbours(x)
            rows.append((dt, row["target"], thr, nbh.mean(), np.percentile(nbh, 25), np.percentile(nbh, 75),
                         nb.prob_up(x), row["abs1"], row["vol21"] * GAUSS_ABS, tr["target"].mean()))
    cols = ["date", "actual", "thr", "knn", "knn_lo", "knn_hi", "nb_pbig", "today_abs", "vol21_fc", "const_fc"]
    return pd.DataFrame(rows, columns=cols).set_index("date")


data = {t: build(t) for t in TICKERS}

# ---- choose K on 2025 ----
val = {k: float(np.mean([((lambda r: ((r.actual - r.knn) ** 2).mean())(walk(data[t], "2025-01-01", "2026-01-01", k)))
                         for t in TICKERS])) for k in K_GRID}
best_k = min(val, key=val.get)
print("validation MSE by K (2025):", {k: f"{v:.3e}" for k, v in val.items()}, "-> K =", best_k)

# ---- final test on 2026 ----
res, rows = {}, []
for t in TICKERS:
    r = walk(data[t], TEST_START, None, best_k)
    res[t] = r
    n = len(r)
    big = r.actual > r.thr
    majority = max(big.mean(), 1 - big.mean())      # best constant guess, in hindsight
    acc_persist = ((r.today_abs > r.thr) == big).mean()
    acc_knn = ((r.knn > r.thr) == big).mean()
    acc_nb = ((r.nb_pbig > 0.5) == big).mean()
    rows.append({
        "ticker": t, "days": n,
        "KNN MAE %": (r.actual - r.knn).abs().mean() * 100,
        "vol21 MAE %": (r.actual - r.vol21_fc).abs().mean() * 100,
        "constant MAE %": (r.actual - r.const_fc).abs().mean() * 100,
        "KNN corr(pred, actual)": r[["knn", "actual"]].corr(method="spearman").iloc[0, 1],
        "share big days": big.mean(),
        "KNN acc": acc_knn, "NB acc": acc_nb, "majority acc": majority, "persistence acc": acc_persist,
        "p(KNN>majority)": pval_above(acc_knn, majority, n),
        "p(NB>majority)": pval_above(acc_nb, majority, n),
    })
tab = pd.DataFrame(rows).set_index("ticker")
pooled = pd.concat(res.values())
pb = pooled.actual > pooled.thr
summary = {
    "pooled KNN acc": ((pooled.knn > pooled.thr) == pb).mean(),
    "pooled NB acc": ((pooled.nb_pbig > .5) == pb).mean(),
    "pooled majority acc": max(pb.mean(), 1 - pb.mean()),
    "pooled persistence acc": ((pooled.today_abs > pooled.thr) == pb).mean(),
    "p(pooled NB > majority)": pval_above(((pooled.nb_pbig > .5) == pb).mean(), max(pb.mean(), 1 - pb.mean()), len(pooled)),
    "p(pooled KNN > majority)": pval_above(((pooled.knn > pooled.thr) == pb).mean(), max(pb.mean(), 1 - pb.mean()), len(pooled)),
}
pd.set_option("display.width", 250)
print(tab.round(3).T)
print({k: round(v, 4) for k, v in summary.items()})
tab.to_csv(Path(__file__).parent / "results_vol.csv")

# ---- figures ----
# g4: predicted shadow vs actual size of move (5-day average so the eye can follow it)
fig, ax = plt.subplots(len(TICKERS), 1, figsize=(11, 13), sharex=True)
for a, t in zip(ax, TICKERS):
    r = res[t]
    a.fill_between(r.index, r.knn_lo * 100, r.knn_hi * 100, alpha=.3, label="K-NN predicted 25-75% range (shadow)")
    a.plot(r.index, r.knn * 100, lw=1.2, label="K-NN predicted size")
    a.plot(r.index, r.actual * 100, color="k", lw=.5, alpha=.5, label="actual |move|")
    a.plot(r.index, r.actual.rolling(5).mean() * 100, color="k", lw=1.3, label="actual, 5-day avg")
    a.set_ylabel(f"{t} |move| %")
ax[0].legend(loc="upper left", ncol=2, fontsize=8)
ax[0].set_title(f"K-NN (K={best_k}) predicted size of tomorrow's move vs actual, 2026")
fig.tight_layout(); fig.savefig(OUT / "g4_vol_knn_shadow_vs_actual.png", dpi=130); plt.close(fig)

# g5: do the model's "calm" days really turn out calmer? (pooled, quintiles of prediction)
pooled["q_knn"] = pd.qcut(pooled.knn.rank(method="first"), 5, labels=[1, 2, 3, 4, 5])
pooled["q_nb"] = pd.qcut(pooled.nb_pbig.rank(method="first"), 5, labels=[1, 2, 3, 4, 5])
fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
(pooled.groupby("q_knn", observed=True).actual.mean() * 100).plot.bar(ax=ax[0], color="C0")
ax[0].set(title="K-NN: actual avg |move| by predicted quintile", xlabel="predicted size (1 = calmest)", ylabel="actual avg |move| %")
(pooled.assign(big=pb).groupby("q_nb", observed=True).big.mean() * 100).plot.bar(ax=ax[1], color="C1")
ax[1].axhline(pb.mean() * 100, color="k", ls="--", lw=1, label="overall share")
ax[1].set(title="Naive Bayes: share of big days by P(big) quintile", xlabel="P(big) quintile (1 = lowest)", ylabel="% of days that were big")
ax[1].legend()
for a in ax: a.tick_params(axis="x", rotation=0)
fig.tight_layout(); fig.savefig(OUT / "g5_vol_quintiles.png", dpi=130); plt.close(fig)

# g6: accuracy vs baselines per stock
acc = tab[["majority acc", "persistence acc", "KNN acc", "NB acc"]] * 100
acc.plot.bar(figsize=(10, 4.2), color=["#bbbbbb", "#777777", "C0", "C1"])
plt.axhline(50, color="k", lw=.8, ls=":")
plt.ylabel("accuracy %"); plt.title("Big-vs-small day accuracy in 2026: models vs simple baselines")
plt.xticks(rotation=0); plt.ylim(30, 80); plt.legend(fontsize=8, ncol=4, loc="upper left")
plt.tight_layout(); plt.savefig(OUT / "g6_vol_accuracy_vs_baselines.png", dpi=130); plt.close()
print("figures saved to", OUT)
