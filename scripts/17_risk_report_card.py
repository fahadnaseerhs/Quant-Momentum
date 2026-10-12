"""
Step 1 of Problem Statement v2 — the RISK REPORT CARD.

Tests every risk number the terminal shows, recomputed with ONLY the data
available at the time (pre-registered in
Quant_Momentum/Problem Statement v2 - Risk-First Investing.md):

  asset level  : 1-in-20 bad case, 1-in-20 good case, 2-in-3 typical range,
                 expected shortfall — one forecast per asset per month
  plan level   : the PLAN tab's bad-month cap (CAREFUL / BALANCED / BOLD),
                 from the weekly allocation backtest (scripts/13)

Bank-style tests: Kupiec (breach rate), Christoffersen (breaches clustering),
conditional coverage, binomial (typical range), bootstrap (expected shortfall).

Outputs: reports/tables/17_asset_tests.csv, 17_summary.csv, 17_plan_tests.csv
         reports/figures/17_g1_risk_report_card.png (copied to Figures/17/)
"""
from __future__ import annotations

import importlib.util
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

spec = importlib.util.spec_from_file_location("alloc_bt", ROOT / "scripts" / "13_allocation_backtest.py")
bt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bt)

P_BAD, HOLDOUT = 0.05, pd.Timestamp("2016-01-01")
QUANTS = [0.05, 1 / 6, 5 / 6, 0.95]
FIG, TBL = ROOT / "reports" / "figures", ROOT / "reports" / "tables"
VAULT = ROOT / "Quant_Momentum" / "Figures" / "17"
VAULT.mkdir(parents=True, exist_ok=True)
UNIVERSES = {
    "PROJECT 20": (ROOT / "data/long/processed/prices_daily_clean.parquet", UNIVERSE, None),
    "ETF 23": (ROOT / "data/etf/processed/prices_daily_clean.parquet", bt.ETF, bt.ETF_GROWTH),
}


# ---------------------------------------------------------------------- #
# Bank-style tests
# ---------------------------------------------------------------------- #

def _ll(x, n, p):
    return (n - x) * np.log(1 - p) + x * np.log(p) if 0 < p < 1 else 0.0


def kupiec(hits: np.ndarray, p: float = P_BAD) -> float:
    """p-value that the breach rate equals p."""
    n, x = len(hits), int(hits.sum())
    if n == 0:
        return np.nan
    lr = -2 * (_ll(x, n, p) - _ll(x, n, x / n))
    return float(chi2.sf(lr, 1))


def christoffersen(hits: np.ndarray) -> float:
    """p-value that breaches are independent (no clustering)."""
    h = hits.astype(int)
    a, b = h[:-1], h[1:]
    n00, n01 = int(((a == 0) & (b == 0)).sum()), int(((a == 0) & (b == 1)).sum())
    n10, n11 = int(((a == 1) & (b == 0)).sum()), int(((a == 1) & (b == 1)).sum())
    if n01 + n11 == 0 or n00 + n01 == 0 or n10 + n11 == 0:
        return 1.0
    pi = (n01 + n11) / (n00 + n01 + n10 + n11)
    p01, p11 = n01 / (n00 + n01), n11 / (n10 + n11)
    l0 = _ll(n01 + n11, n00 + n01 + n10 + n11, pi)
    l1 = _ll(n01, n00 + n01, p01) + _ll(n11, n10 + n11, p11)
    return float(chi2.sf(-2 * (l0 - l1), 1))


def cond_coverage(hits: np.ndarray, p: float = P_BAD) -> float:
    lr_pof = chi2.isf(kupiec(hits, p), 1) if kupiec(hits, p) > 0 else 50.0
    lr_ind = chi2.isf(christoffersen(hits), 1) if christoffersen(hits) > 0 else 50.0
    return float(chi2.sf(lr_pof + lr_ind, 2))


# ---------------------------------------------------------------------- #
# 1. Asset-level forecasts, point in time
# ---------------------------------------------------------------------- #

def asset_forecasts(prices: pd.DataFrame, tickers: list[str]) -> pd.DataFrame:
    idx = prices.index
    firsts = np.where(np.r_[True, idx.month[1:] != idx.month[:-1]])[0]
    rows = []
    for t in tickers:
        p = prices[t]
        lp = np.log(p.to_numpy(float))
        sig = ewma_vol(p.pct_change(fill_method=None).to_frame("x"))["x"].to_numpy()
        z21 = (np.r_[lp[21:], np.full(21, np.nan)] - lp) / (sig * np.sqrt(21))   # known 21 days later
        for a, b in zip(firsts[:-1], firsts[1:]):
            if not (np.isfinite(lp[a]) and np.isfinite(lp[b]) and np.isfinite(sig[a]) and sig[a] > 0):
                continue
            hist = z21[:max(a - 21, 0)]
            hist = hist[np.isfinite(hist)]
            if len(hist) >= 250:
                zc = hist - np.median(hist)
                q = np.quantile(zc, QUANTS)
                es = zc[zc <= q[0]].mean()
            else:
                q, es = np.array([-1.645, -0.967, 0.967, 1.645]), -2.063
            scale = sig[a] * np.sqrt(b - a)
            R = lp[b] - lp[a]
            rows.append({"asset": t, "date": idx[a], "R": R, "bad": q[0] * scale, "good": q[3] * scale,
                         "typ_lo": q[1] * scale, "typ_hi": q[2] * scale, "es": es * scale})
    df = pd.DataFrame(rows)
    df["breach_low"] = df["R"] < df["bad"]
    df["breach_high"] = df["R"] > df["good"]
    df["inside_typ"] = (df["R"] >= df["typ_lo"]) & (df["R"] <= df["typ_hi"])
    return df


def es_ratio_ci(df: pd.DataFrame, n_boot: int = 2000, seed: int = 0):
    b = df[df["breach_low"]]
    if len(b) < 10:
        return np.nan, np.nan, np.nan
    ratio = b["R"].to_numpy() / b["es"].to_numpy()
    rng = np.random.default_rng(seed)
    boots = [rng.choice(ratio, len(ratio)).mean() for _ in range(n_boot)]
    return ratio.mean(), *np.quantile(boots, [0.05, 0.95])


asset_rows, summary_rows, forecasts = [], [], {}
for uname, (path, universe, _) in UNIVERSES.items():
    px = bt.load(path)
    tickers = [t for v in universe.values() for t in v]
    fc = asset_forecasts(px, tickers)
    forecasts[uname] = fc
    for per, mask in (("full", fc["date"] >= fc["date"].min()), ("HOLDOUT", fc["date"] >= HOLDOUT)):
        f = fc[mask]
        for a, g in f.groupby("asset"):
            g = g.sort_values("date")
            asset_rows.append({"universe": uname, "period": per, "asset": a, "months": len(g),
                               "bad_rate": g["breach_low"].mean(), "kupiec_bad": kupiec(g["breach_low"].to_numpy()),
                               "indep_bad": christoffersen(g["breach_low"].to_numpy()),
                               "good_rate": g["breach_high"].mean(), "kupiec_good": kupiec(g["breach_high"].to_numpy()),
                               "typical_inside": g["inside_typ"].mean()})
        A = pd.DataFrame([r for r in asset_rows if r["universe"] == uname and r["period"] == per])
        er, lo, hi = es_ratio_ci(f)
        n_in = int(f["inside_typ"].sum())
        summary_rows.append({
            "universe": uname, "period": per, "asset_months": len(f),
            "bad_rate_pooled": f["breach_low"].mean(), "assets_pass_kupiec_bad": (A["kupiec_bad"] > 0.05).mean(),
            "assets_pass_indep_bad": (A["indep_bad"] > 0.05).mean(),
            "good_rate_pooled": f["breach_high"].mean(), "assets_pass_kupiec_good": (A["kupiec_good"] > 0.05).mean(),
            "typical_inside_pooled": f["inside_typ"].mean(),
            "typical_binom_p": binomtest(n_in, len(f), 2 / 3).pvalue,
            "es_ratio": er, "es_ratio_lo90": lo, "es_ratio_hi90": hi})
    print(f"{uname}: {len(fc):,} asset-month forecasts", flush=True)

assets = pd.DataFrame(asset_rows)
summary = pd.DataFrame(summary_rows).set_index(["universe", "period"])
assets.to_csv(TBL / "17_asset_tests.csv", index=False, float_format="%.4f")


# ---------------------------------------------------------------------- #
# 2. Plan-level bad month (the PLAN tab's cap), from the weekly backtest
# ---------------------------------------------------------------------- #

plan_rows, plan_hits = [], {}
for uname, (path, universe, growth) in UNIVERSES.items():
    px = bt.load(path)
    bold_budget = ({k: (2.0 if k in growth else 1.0) for k in universe} if growth else None)
    full = bt.run(px, universe, "FULL")
    z = bt.monthly_z(full[0], full[2])
    z_bad = float(-z[z.index <= bt.DESIGN_END].quantile(0.05))
    for prof, custom in (("CAREFUL", None), ("BALANCED", None), ("BOLD", bold_budget)):
        s, _, pred = bt.run(px, universe, prof, custom=custom, z_bad=z_bad)
        zz = bt.monthly_z(s, pred)
        monthly = zz.groupby([zz.index.year, zz.index.month]).head(1)        # one check per month
        hits = (monthly < -z_bad).to_numpy()
        plan_hits[(uname, prof)] = monthly
        for per, m in (("full", np.ones(len(monthly), bool)), ("HOLDOUT", monthly.index >= HOLDOUT)):
            h = hits[m]
            plan_rows.append({"universe": uname, "profile": prof, "period": per, "months": len(h),
                              "bad_rate": h.mean(), "kupiec_p": kupiec(h), "indep_p": christoffersen(h),
                              "cond_cov_p": cond_coverage(h), "z_bad": z_bad})
        print(f"  plan {uname} {prof} done", flush=True)
plan = pd.DataFrame(plan_rows).set_index(["universe", "profile", "period"])


# ---------------------------------------------------------------------- #
# 3. Verdicts (pre-registered rules)
# ---------------------------------------------------------------------- #

ho = summary.xs("HOLDOUT", level="period")
verdict = {
    "asset bad case (1 in 20)": bool(((ho["assets_pass_kupiec_bad"] >= 0.8)
                                      & ho["bad_rate_pooled"].between(0.03, 0.07)).all()),
    "asset good case (1 in 20)": bool(((ho["assets_pass_kupiec_good"] >= 0.8)
                                       & ho["good_rate_pooled"].between(0.03, 0.07)).all()),
    "asset typical range (2 in 3)": bool((ho["typical_binom_p"] > 0.05).all()),
    "expected shortfall": bool(((summary["es_ratio_lo90"] <= 1) & (summary["es_ratio_hi90"] >= 1))
                               .xs("full", level="period").all()),
    "plan bad month (all profiles)": bool(((plan.xs("full", level="period")["kupiec_p"] > 0.05)
                                           & (plan.xs("full", level="period")["cond_cov_p"] > 0.05)).all()),
}
summary.to_csv(TBL / "17_summary.csv", float_format="%.4f")
plan.to_csv(TBL / "17_plan_tests.csv", float_format="%.4f")
pd.Series(verdict).to_csv(TBL / "17_verdict.csv", header=["pass"])

pd.set_option("display.width", 220)
print("\n=== ASSET-LEVEL SUMMARY ===\n" + summary.round(3).to_string())
print("\n=== PLAN BAD MONTH ===\n" + plan.round(3).to_string())
print("\n=== REPORT CARD (pre-registered rules) ===")
for k, v in verdict.items():
    print(f"  {'PASS' if v else 'FAIL'}  {k}")
fails = assets[(assets["period"] == "HOLDOUT") & (assets["kupiec_bad"] <= 0.05)]
print("\nHoldout assets failing Kupiec on the bad case:\n" + fails[["universe", "asset", "months", "bad_rate", "kupiec_bad"]]
      .round(3).to_string(index=False))


# ---------------------------------------------------------------------- #
# 4. One figure
# ---------------------------------------------------------------------- #

fig, ax = plt.subplots(1, 2, figsize=(15, 6))
for k, (uname, c) in enumerate((("PROJECT 20", "#4C78A8"), ("ETF 23", "#F58518"))):
    a = assets[(assets["universe"] == uname) & (assets["period"] == "HOLDOUT")].sort_values("bad_rate")
    ok = a["kupiec_bad"] > 0.05
    y = np.arange(len(a)) + (0 if k == 0 else len(assets[(assets["universe"] == "PROJECT 20")
                                                          & (assets["period"] == "HOLDOUT")]) + 1)
    ax[0].scatter(a["bad_rate"] * 100, y, color=np.where(ok, c, "#E45756"), s=28, zorder=3)
    for yy, name in zip(y, a["asset"]):
        ax[0].text(-0.3, yy, name, ha="right", va="center", fontsize=6)
ax[0].axvline(5, color="k", lw=1, ls="--", label="target 5%")
ax[0].axvspan(1.6, 9.3, color="#cccccc", alpha=0.3, label="consistent with 5% (≈129 months)")
ax[0].set_yticks([])
ax[0].set_xlim(-6, 20)
ax[0].set_xlabel("% of months worse than the predicted 1-in-20 bad case (2016-26)")
ax[0].set_title("Each asset's bad-case warning: blue/orange = passes, red = fails Kupiec")
ax[0].legend(fontsize=8, loc="lower right")
labels, vals, errs, cols = [], [], [], []
for (uname, prof), m in plan_hits.items():
    zb = plan.loc[(uname, prof, "full"), "z_bad"]
    h = (m < -zb).to_numpy()
    r = h.mean()
    labels.append(f"{prof} · {uname}")
    vals.append(r * 100)
    errs.append(1.96 * np.sqrt(r * (1 - r) / len(h)) * 100)
    cols.append("#54A24B" if plan.loc[(uname, prof, "full"), "cond_cov_p"] > 0.05 else "#E45756")
ax[1].barh(labels, vals, xerr=errs, color=cols)
ax[1].axvline(5, color="k", ls="--", lw=1)
ax[1].set_xlabel("% of months worse than the plan's predicted bad month (2005-26)")
ax[1].set_title("Plan bad-month warning: green = passes Kupiec + clustering test")
for a_ in ax:
    a_.grid(True, axis="x", ls=":", alpha=0.5)
fig.suptitle("Step 1 — Risk report card: are the terminal's risk numbers honest?")
fig.tight_layout()
fig.savefig(FIG / "17_g1_risk_report_card.png", dpi=130)
shutil.copy2(FIG / "17_g1_risk_report_card.png", VAULT / "17_g1_risk_report_card.png")
print("saved figure")
