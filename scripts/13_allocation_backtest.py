"""
Phase 4A test — the terminal's allocation routine, run through history.

Exactly the live engine (terminal/allocate.py): equal risk inside each
segment, risk budget across segments (correlation-aware), profile sets the
safe part / growth tilt, weekly check on the first trading day of each week,
trade only assets >20% off target, 10 bps per $ traded. Positions drift between
trades; any untraded remainder sits in cash at 0%.

Universes: the project's 20 assets (data/long) and the 23 no-hindsight ETFs
(data/etf). Design 2005-2015 / holdout 2016-2026 as in Tasks 10-11. The
CAREFUL profile's bad-month multiplier (z_bad) is estimated on the DESIGN
period of the BALANCED run only, then checked on the holdout.

Outputs: reports/tables/13_allocation_metrics.csv, 13_bad_month_check.csv,
         reports/figures/13_g1_allocation_equity.png (copied to Figures/13/)
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.baseline import equity_curve, performance_metrics
from src.tsmom import ewma_vol
from src.universe import UNIVERSE
from terminal.allocate import BAND, MONTH, SAFE, allocation

DESIGN_END, COST = "2015-12-31", 10
FIG, TBL = ROOT / "reports" / "figures", ROOT / "reports" / "tables"
VAULT = ROOT / "Quant_Momentum" / "Figures" / "13"
for d in (FIG, TBL, VAULT):
    d.mkdir(parents=True, exist_ok=True)

ETF = {"equity index": ["SPY", "QQQ", "IWM", "EFA", "EEM"],
       "sector": ["XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY"],
       "bond": ["SHY", "IEF", "TLT", "LQD", "TIP"], "commodity": ["GLD", "DBC", "USO"],
       "real estate": ["VNQ"]}
ETF_GROWTH = {"equity index", "sector", "real estate"}


def load(path):
    p = pd.read_parquet(path)
    p.index = pd.to_datetime(p.index)
    return p


def run(prices: pd.DataFrame, universe: dict, profile: str, custom=None, z_bad=None, start=260):
    assets = [t for v in universe.values() for t in v]
    rets = prices[assets].pct_change(fill_method=None)
    sig = ewma_vol(rets)
    dates = prices.index
    week_start = np.r_[True, dates.weekday[1:] < dates.weekday[:-1]]
    w = np.zeros(len(assets))
    R = rets.to_numpy()
    net, rows, preds = [], [], []
    trades = turnover = 0.0
    for i in range(start, len(dates) - 1):
        traded = 0.0
        if week_start[i]:
            T, info = allocation(rets.iloc[i - 251:i + 1], sig.iloc[i], universe, profile, custom, z_bad)
            T = T.reindex(assets).fillna(0).to_numpy()
            move = ((T > 0) & ((w == 0) | (np.abs(w - T) > BAND * T))) | ((T == 0) & (w > 0))
            traded = np.abs(T - w)[move].sum()
            trades += move.sum()
            w = np.where(move, T, w)
            preds.append((dates[i], info["mix_swing"] / np.sqrt(MONTH), info["invest"]))
        r = np.nan_to_num(R[i + 1])
        gross = w @ r
        net.append(gross - COST * 1e-4 * traded)
        turnover += traded
        w = w * (1 + r) / (1 + gross)
    s = pd.Series(net, index=dates[start + 1:len(dates)])
    yrs = len(s) / 252
    p = pd.DataFrame(preds, columns=["date", "daily_sigma", "invest"]).set_index("date")
    return s, {"trades_per_year": trades / yrs, "turnover_per_year": turnover / yrs,
               "cost_per_year": COST * 1e-4 * turnover / yrs}, p


def monthly_z(s: pd.Series, preds: pd.DataFrame) -> pd.Series:
    """Realised next-21-day return / predicted monthly sigma, at each weekly check."""
    eq = (1 + s).cumprod()
    out = {}
    for d, row in preds.iterrows():
        i = eq.index.searchsorted(d)
        if i + MONTH < len(eq) and i > 0:
            r21 = eq.iloc[i + MONTH] / eq.iloc[i] - 1
            out[d] = r21 / (row["daily_sigma"] * np.sqrt(MONTH))
    return pd.Series(out)


def periods(s):
    d = s.index <= DESIGN_END
    return {"design": s[d], "HOLDOUT": s[~d], "full": s}


if __name__ == "__main__":   # importable: scripts/17_risk_report_card.py reuses run()/monthly_z()
    rows, curves, checks = [], {}, []
    for uname, path, universe, growth in [
            ("PROJECT 20", ROOT / "data/long/processed/prices_daily_clean.parquet", UNIVERSE, None),
            ("ETF 23 (no hindsight)", ROOT / "data/etf/processed/prices_daily_clean.parquet", ETF, ETF_GROWTH)]:
        px = load(path)
        print(f"\n=== {uname}: {px.index[0].date()} -> {px.index[-1].date()} ===")
        bold_budget = ({k: (2.0 if k in growth else 1.0) for k in universe} if growth else None)

        full = run(px, universe, "FULL")
        z = monthly_z(full[0], full[2])
        z_bad = float(-z[z.index <= DESIGN_END].quantile(0.05))
        print(f"z_bad (design-period 1-in-20 bad month, in monthly sigmas) = {z_bad:.2f}", flush=True)

        books = {"CAREFUL": run(px, universe, "CAREFUL", z_bad=z_bad),
                 "BALANCED": run(px, universe, "BALANCED", z_bad=z_bad),
                 "BOLD": run(px, universe, "BOLD", custom=bold_budget, z_bad=z_bad),
                 "FULL (always invested, v1)": full}
        per_asset = {t: [t] for v in universe.values() for t in v if t != SAFE}
        books["equal risk per ASSET (old split)"] = run(px, per_asset, "BALANCED")
        idx = full[0].index
        spy = (px["SPY"].shift(-1) / px["SPY"] - 1).reindex(idx).shift(1).fillna(0)
        books["SPY buy & hold"] = (spy, {"trades_per_year": 0, "turnover_per_year": 0, "cost_per_year": 0}, None)

        for name, (s, st, pred) in books.items():
            for per, x in periods(s).items():
                m = performance_metrics(x)
                m21 = (1 + x).rolling(MONTH).apply(np.prod, raw=True) - 1
                rows.append({"universe": uname, "book": name, "period": per,
                             "sharpe": m["sharpe"], "ann_ret": m["ann_ret"], "ann_vol": m["ann_vol"],
                             "max_dd": m["max_dd"], "worst_month": m21.min(), **st})
            if pred is not None:
                zz = monthly_z(s, pred)
                ho = zz[zz.index > DESIGN_END]
                checks.append({"universe": uname, "book": name,
                               "holdout share of months worse than predicted 1-in-20": (ho < -z_bad).mean(),
                               "n months checked": len(ho), "avg invested": pred["invest"].mean()})
            curves[(uname, name)] = s

    tbl = pd.DataFrame(rows).set_index(["universe", "book", "period"])
    tbl.to_csv(TBL / "13_allocation_metrics.csv", float_format="%.4f")
    chk = pd.DataFrame(checks).set_index(["universe", "book"])
    chk.to_csv(TBL / "13_bad_month_check.csv", float_format="%.4f")
    pd.set_option("display.width", 200)
    show = tbl.reset_index()
    show = show
    print(show.pivot_table(index=["universe", "book"], columns="period",
                           values=["sharpe", "ann_ret", "max_dd", "worst_month"]).round(3).to_string())
    print(tbl.xs("full", level="period")[["trades_per_year", "turnover_per_year", "cost_per_year"]].round(3).to_string())
    print("\nBad-month check (target about 5%):")
    print(chk.round(3).to_string())

    fig, axes = plt.subplots(1, 2, figsize=(15, 5.8))
    colors = {"CAREFUL": "#54A24B", "BALANCED": "#4C78A8", "BOLD": "#E45756", "FULL (always invested, v1)": "#B279A2",
              "equal risk per ASSET (old split)": "#9D9D9D", "SPY buy & hold": "#F58518"}
    for ax, uname in zip(axes, ["PROJECT 20", "ETF 23 (no hindsight)"]):
        for name, c in colors.items():
            s = curves[(uname, name)]
            full = tbl.loc[(uname, name, "full")]
            ax.plot(equity_curve(s), color=c, lw=1.6 if name in ("BALANCED", "CAREFUL", "BOLD") else 1.0,
                    label=f"{name}  (Sharpe {full['sharpe']:.2f}, maxDD {full['max_dd']:.0%})")
        ax.axvline(pd.Timestamp("2016-01-01"), color="k", ls="--", lw=0.8)
        ax.set_yscale("log")
        ax.set_title(uname)
        ax.grid(True, which="both", ls=":", alpha=0.5)
        ax.legend(fontsize=8, loc="upper left")
    fig.suptitle("Phase 4A — the terminal's allocation routine through history (weekly check, 20% band, 10 bps)")
    fig.tight_layout()
    fig.savefig(FIG / "13_g1_allocation_equity.png", dpi=130)
    shutil.copy2(FIG / "13_g1_allocation_equity.png", VAULT / "13_g1_allocation_equity.png")
    print("\nsaved figure")
