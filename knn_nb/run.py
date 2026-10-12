"""Honest out-of-sample test of from-scratch K-NN and Naive Bayes on the tech stocks.

Train on 2004 -> end of 2025, then predict each day of 2026 (retrained monthly, never sees the future).
K is chosen on 2025 only (training stops end-2024 for that choice).
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
K_GRID = [5, 10, 20, 50, 100, 200, 400]
FEATS = ["ret1", "ret5", "ret21", "ret63", "vol21"]

px = pd.read_parquet(ROOT / "data/long/processed/prices_daily_clean.parquet")[TICKERS]


def build(t: str) -> pd.DataFrame:
    p = px[t].dropna()
    r = p.pct_change()
    f = pd.DataFrame({
        "ret1": r, "ret5": p.pct_change(5), "ret21": p.pct_change(21), "ret63": p.pct_change(63),
        "vol21": r.rolling(21).std(),
    })
    f["target"] = r.shift(-1)                       # next-day return (the thing to predict)
    f["tdate"] = pd.Series(p.index, index=p.index).shift(-1)   # date the target is realised
    f = f.dropna()
    f["up"] = (f["target"] > 0).astype(int)
    return f


def pval_above(acc: float, base: float, n: int) -> float:
    """One-sided z-test: is accuracy above the baseline accuracy?"""
    z = (acc - base) / sqrt(base * (1 - base) / n)
    return 0.5 * (1 - erf(z / sqrt(2)))


def walk(d: pd.DataFrame, start: str, end: str | None, k: int) -> pd.DataFrame:
    """Predict each day in [start, end); retrain at the start of every month on data realised before it."""
    te = d[(d.index >= start) & ((d.index < end) if end else True)]
    rows = []
    for _, chunk in te.groupby(te.index.to_period("M")):
        cut = chunk.index[0]
        tr = d[d["tdate"] < cut]                    # only rows whose outcome was known before the month began
        knn = KNN(k).fit(tr[FEATS].values, tr["target"].values)
        nb = GaussianNB().fit(tr[FEATS].values, tr["up"].values)
        for dt, row in chunk.iterrows():
            x = row[FEATS].values.astype(float)
            m, s, pu = knn.predict(x)
            rows.append((dt, row["target"], m, s, pu, nb.prob_up(x)))
    return pd.DataFrame(rows, columns=["date", "actual", "knn_mean", "knn_sd", "knn_pup", "nb_pup"]).set_index("date")


data = {t: build(t) for t in TICKERS}

# ---- choose K on 2025 (training only sees data realised before each 2025 month) ----
val = {}
for k in K_GRID:
    errs = []
    for t in TICKERS:
        r = walk(data[t], "2025-01-01", "2026-01-01", k)
        errs.append(((r.actual - r.knn_mean) ** 2).mean())
    val[k] = float(np.mean(errs))
best_k = min(val, key=val.get)
print("validation MSE by K (2025):", {k: f"{v:.3e}" for k, v in val.items()}, "-> K =", best_k)

# ---- final test on 2026 ----
res, rows = {}, []
for t in TICKERS:
    r = walk(data[t], TEST_START, None, best_k)
    res[t] = r
    n = len(r)
    up = r.actual > 0
    base = max(up.mean(), 1 - up.mean())             # best constant guess, in hindsight (generous baseline)
    acc_knn = ((r.knn_mean > 0) == up).mean()
    acc_nb = ((r.nb_pup > 0.5) == up).mean()
    rows.append({
        "ticker": t, "days": n,
        "KNN MAE %": (r.actual - r.knn_mean).abs().mean() * 100,
        "zero-forecast MAE %": r.actual.abs().mean() * 100,
        "band coverage": ((r.actual - r.knn_mean).abs() <= r.knn_sd).mean(),
        "KNN acc": acc_knn, "NB acc": acc_nb, "best-constant acc": base,
        "p(KNN>const)": pval_above(acc_knn, base, n),
        "p(NB>const)": pval_above(acc_nb, base, n),
        "hold %": ((1 + r.actual).prod() - 1) * 100,
        "KNN signal %": ((1 + r.actual * np.sign(r.knn_mean)).prod() - 1) * 100,
        "NB signal %": ((1 + r.actual * np.where(r.nb_pup > 0.5, 1, -1)).prod() - 1) * 100,
    })
tab = pd.DataFrame(rows).set_index("ticker")
pd.set_option("display.width", 250)
print(tab.round(3).T)
tab.to_csv(Path(__file__).parent / "results.csv")

# ---- figures ----
fig, ax = plt.subplots(len(TICKERS), 1, figsize=(11, 13), sharex=True)
for a, t in zip(ax, TICKERS):
    r = res[t]
    a.fill_between(r.index, (r.knn_mean - r.knn_sd) * 100, (r.knn_mean + r.knn_sd) * 100, alpha=.3,
                   label="K-NN predicted ±1 sd (shadow)")
    a.plot(r.index, r.knn_mean * 100, lw=1, label="K-NN predicted mean")
    a.plot(r.index, r.actual * 100, color="k", lw=.7, label="actual")
    a.set_ylabel(f"{t} next-day %")
ax[0].legend(loc="upper left", ncol=3, fontsize=8)
ax[0].set_title(f"K-NN (K={best_k}) predicted shadow vs actual next-day return, 2026")
fig.tight_layout(); fig.savefig(OUT / "g1_knn_shadow_vs_actual.png", dpi=130); plt.close(fig)

fig, ax = plt.subplots(len(TICKERS), 1, figsize=(11, 11), sharex=True)
for a, t in zip(ax, TICKERS):
    r = res[t]
    a.fill_between(r.index, 0.5, r.nb_pup, alpha=.4, label="Naive Bayes P(up) vs 50%")
    a.scatter(r.index, np.where(r.actual > 0, 1.0, 0.0), s=6, color="k", label="actual (1=up, 0=down)")
    a.set_ylim(-.05, 1.05); a.set_ylabel(t)
ax[0].legend(loc="upper left", ncol=2, fontsize=8)
ax[0].set_title("Naive Bayes probability of an up day vs what actually happened, 2026")
fig.tight_layout(); fig.savefig(OUT / "g2_nb_prob_vs_actual.png", dpi=130); plt.close(fig)

fig, ax = plt.subplots(len(TICKERS), 1, figsize=(11, 12), sharex=True)
for a, t in zip(ax, TICKERS):
    r = res[t]
    a.plot(r.index, (1 + r.actual).cumprod(), color="k", label="buy & hold")
    a.plot(r.index, (1 + r.actual * np.sign(r.knn_mean)).cumprod(), label="follow K-NN (long/short)")
    a.plot(r.index, (1 + r.actual * np.where(r.nb_pup > .5, 1, -1)).cumprod(), label="follow Naive Bayes (long/short)")
    a.set_ylabel(t)
ax[0].legend(loc="upper left", ncol=3, fontsize=8)
ax[0].set_title("Growth of $1 in 2026: hold vs following each model (no costs)")
fig.tight_layout(); fig.savefig(OUT / "g3_follow_vs_hold.png", dpi=130); plt.close(fig)
print("figures saved to", OUT)
