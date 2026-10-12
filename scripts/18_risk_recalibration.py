"""
Step 1b — fix the risk numbers that failed the report card (pre-registered in
Quant_Momentum/Problem Statement v2 - Risk-First Investing.md).

Fixes, each set on DESIGN (<=2015) only, then frozen and tested on HOLDOUT (2016+):
  drift      : shift every bound by the universe-wide median standardised move (point in time)
  k_typ      : widen/narrow the 2-in-3 band around the shifted centre (design coverage = 2/3)
  k_es       : scale expected shortfall by the design ratio realised / predicted

Outputs: reports/tables/18_recalibration.csv, 18_params.json,
         reports/figures/18_g1_recalibration.png (copied to Figures/18/)
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import binomtest, chi2

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.tsmom import ewma_vol  # noqa: E402
from src.universe import UNIVERSE  # noqa: E402

DESIGN_END, HOLDOUT = pd.Timestamp("2015-12-31"), pd.Timestamp("2016-01-01")
FIG, TBL = ROOT / "reports" / "figures", ROOT / "reports" / "tables"
VAULT = ROOT / "Quant_Momentum" / "Figures" / "18"
VAULT.mkdir(parents=True, exist_ok=True)
ETF = {"equity index": ["SPY", "QQQ", "IWM", "EFA", "EEM"],
       "sector": ["XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY"],
       "bond": ["SHY", "IEF", "TLT", "LQD", "TIP"], "commodity": ["GLD", "DBC", "USO"], "real estate": ["VNQ"]}
UNIVERSES = {"PROJECT 20": (ROOT / "data/long/processed/prices_daily_clean.parquet", UNIVERSE),
             "ETF 23": (ROOT / "data/etf/processed/prices_daily_clean.parquet", ETF)}
Q = [0.05, 1 / 6, 0.5, 5 / 6, 0.95]


def _ll(x, n, p):
    return (n - x) * np.log(1 - p) + x * np.log(p) if 0 < p < 1 else 0.0


def kupiec(h, p=0.05):
    n, x = len(h), int(np.sum(h))
    return float(chi2.sf(-2 * (_ll(x, n, p) - _ll(x, n, x / n)), 1)) if n else np.nan


def forecasts(prices: pd.DataFrame, tickers: list[str]) -> pd.DataFrame:
    idx = prices.index
    firsts = np.where(np.r_[True, idx.month[1:] != idx.month[:-1]])[0]
    lp = np.log(prices[tickers].to_numpy(float))
    sig = ewma_vol(prices[tickers].pct_change(fill_method=None)).to_numpy()
    Z = (np.r_[lp[21:], np.full((21, len(tickers)), np.nan)] - lp) / (sig * np.sqrt(21))   # known 21 days later
    rows = []
    for a, b in zip(firsts[:-1], firsts[1:]):
        past = Z[:max(a - 21, 0)]
        pooled = past[np.isfinite(past)]
        drift = np.median(pooled) if len(pooled) >= 250 else 0.0          # universe-wide, point in time
        for k, t in enumerate(tickers):
            if not (np.isfinite(lp[a, k]) and np.isfinite(lp[b, k]) and np.isfinite(sig[a, k]) and sig[a, k] > 0):
                continue
            h = past[:, k]
            h = h[np.isfinite(h)]
            if len(h) >= 250:
                zc = h - np.median(h)
                q = np.quantile(zc, Q)
                es = zc[zc <= q[0]].mean()
            else:
                q, es = np.array([-1.645, -0.967, 0.0, 0.967, 1.645]), -2.063
            rows.append({"asset": t, "date": idx[a], "R": lp[b, k] - lp[a, k], "scale": sig[a, k] * np.sqrt(b - a),
                         "q05": q[0], "q17": q[1], "q83": q[3], "q95": q[4], "es": es, "drift": drift})
    return pd.DataFrame(rows)


def evaluate(df: pd.DataFrame, k_typ: float, k_es: float, use_drift: bool) -> dict:
    d = df["drift"] if use_drift else 0.0
    s = df["scale"]
    bad, good = (df["q05"] + d) * s, (df["q95"] + d) * s
    lo, hi = (d + k_typ * df["q17"]) * s, (d + k_typ * df["q83"]) * s
    es = (df["es"] + d) * s * k_es
    b_hit, g_hit = df["R"] < bad, df["R"] > good
    inside = (df["R"] >= lo) & (df["R"] <= hi)
    per_asset = pd.DataFrame({"asset": df["asset"], "b": b_hit, "g": g_hit}).groupby("asset")
    kb = per_asset["b"].apply(lambda x: kupiec(x.to_numpy()))
    kg = per_asset["g"].apply(lambda x: kupiec(x.to_numpy()))
    ratio = (df["R"][b_hit] / es[b_hit]).to_numpy()
    rng = np.random.default_rng(0)
    boots = [rng.choice(ratio, len(ratio)).mean() for _ in range(2000)] if len(ratio) > 10 else [np.nan]
    return {"bad_rate": b_hit.mean(), "bad_assets_pass": (kb > 0.05).mean(),
            "good_rate": g_hit.mean(), "good_assets_pass": (kg > 0.05).mean(),
            "typical_inside": inside.mean(), "typical_p": binomtest(int(inside.sum()), len(df), 2 / 3).pvalue,
            "es_ratio": ratio.mean() if len(ratio) else np.nan,
            "es_lo90": np.quantile(boots, 0.05), "es_hi90": np.quantile(boots, 0.95), "n": len(df)}


def calibrate(design: pd.DataFrame) -> tuple[float, float]:
    s, d = design["scale"], design["drift"]
    ks = np.round(np.arange(0.80, 1.601, 0.01), 2)
    cov = [((design["R"] >= (d + k * design["q17"]) * s) & (design["R"] <= (d + k * design["q83"]) * s)).mean()
           for k in ks]
    k_typ = float(ks[int(np.argmin(np.abs(np.array(cov) - 2 / 3)))])
    bad = (design["q05"] + d) * s
    hit = design["R"] < bad
    k_es = float((design["R"][hit] / ((design["es"] + d) * s)[hit]).mean())
    return k_typ, k_es


rows, params = [], {}
for uname, (path, universe) in UNIVERSES.items():
    px = pd.read_parquet(path)
    px.index = pd.to_datetime(px.index)
    tickers = [t for v in universe.values() for t in v]
    df = forecasts(px, tickers)
    design, ho = df[df["date"] <= DESIGN_END], df[df["date"] >= HOLDOUT]
    k_typ, k_es = calibrate(design)
    params[uname] = {"k_typ": k_typ, "k_es": k_es, "drift_now": float(df["drift"].iloc[-1])}
    print(f"{uname}: k_typ={k_typ:.2f}  k_es={k_es:.3f}  drift now={df['drift'].iloc[-1]:+.3f} sigma", flush=True)
    for label, kt, ke, dr in (("BEFORE (step 1 method)", 1.0, 1.0, False), ("AFTER (fixed, frozen)", k_typ, k_es, True)):
        rows.append({"universe": uname, "version": label, **evaluate(ho, kt, ke, dr)})

R = pd.DataFrame(rows).set_index(["universe", "version"])
after = R.xs("AFTER (fixed, frozen)", level="version")
verdict = {
    "bad case (with drift)": bool(((after["bad_assets_pass"] >= 0.8) & after["bad_rate"].between(0.03, 0.07)).all()),
    "good case": bool(((after["good_assets_pass"] >= 0.8) & after["good_rate"].between(0.03, 0.07)).all()),
    "typical range": bool((after["typical_p"] > 0.05).all()),
    "expected shortfall": bool(((after["es_lo90"] <= 1) & (after["es_hi90"] >= 1)).all()),
}
R.to_csv(TBL / "18_recalibration.csv", float_format="%.4f")
(TBL / "18_params.json").write_text(json.dumps({"params": params, "verdict": verdict}, indent=2))
pd.set_option("display.width", 220)
print("\nHOLDOUT 2016-26\n" + R.round(4).to_string())
print("\n=== VERDICT (pre-registered) ===")
for k, v in verdict.items():
    print(f"  {'PASS' if v else 'FAIL'}  {k}")

fig, ax = plt.subplots(1, 4, figsize=(16, 4.2))
specs = [("bad_rate", "Bad case: % months worse", 5, 100), ("good_rate", "Good case: % months better", 5, 100),
         ("typical_inside", "Typical range: % months inside", 66.7, 100), ("es_ratio", "Shortfall: real ÷ predicted", 1, 1)]
for a_, (col, title, target, mult) in zip(ax, specs):
    labels, vals, colors = [], [], []
    for (u, v), r in R.iterrows():
        labels.append(f"{u}\n{'before' if v.startswith('BEFORE') else 'after'}")
        vals.append(r[col] * mult)
        colors.append("#9D9D9D" if v.startswith("BEFORE") else "#4C78A8")
    a_.bar(labels, vals, color=colors)
    a_.axhline(target, color="#E45756", ls="--", lw=1)
    a_.set_title(title, fontsize=10)
    a_.tick_params(axis="x", labelsize=7)
    a_.grid(True, axis="y", ls=":", alpha=0.5)
fig.suptitle("Step 1b — risk numbers before vs after the pre-registered fix (holdout 2016-26; red = target)")
fig.tight_layout()
fig.savefig(FIG / "18_g1_recalibration.png", dpi=130)
shutil.copy2(FIG / "18_g1_recalibration.png", VAULT / "18_g1_recalibration.png")
print("saved figure")
