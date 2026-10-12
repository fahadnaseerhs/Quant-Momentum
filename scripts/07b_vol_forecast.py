"""
Task 07b — Volatility forecasting, leakage-safe walk-forward (Option 2).

Forecast each asset's realised vol over the next 21 days with HAR / HAR-L,
benchmark against EWMA, then use each forecast to size the inverse-vol
long-only book (src/tsmom.tsmom_weights) and compare portfolios.

Outputs:
  reports/tables/07b_forecast_accuracy.csv
  reports/tables/07b_portfolio.csv
  reports/tables/07b_per_asset.csv
  reports/tables/07b_coefs.csv
  reports/figures/07b_g1_equity.png
  reports/figures/07b_g2_per_asset_qlike.png
  reports/figures/07b_g3_forecast_vs_realized.png
  (figures copied to Quant_Momentum/Figures/07b/)
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.baseline import equity_curve, performance_metrics
from src.tsmom import ASSET_CLASS, net_returns, tsmom_weights
from src.volforecast import HAR, HAR_L, build_vol_panel, qlike, walk_forward_vol

# `--long` re-runs everything on the 2004+ history (Task 07c, scripts/07c_fetch_long.py)
LONG = "--long" in sys.argv
TASK, TAG = ("07c", "07c_vol") if LONG else ("07b", "07b")
PRICES_PATH = ROOT / "data" / ("long" if LONG else "") / "processed" / "prices_daily_clean.parquet"
FIG_DIR = ROOT / "reports" / "figures"
TBL_DIR = ROOT / "reports" / "tables"
VAULT_FIG = ROOT / "Quant_Momentum" / "Figures" / TASK
for d in (FIG_DIR, TBL_DIR, VAULT_FIG):
    d.mkdir(parents=True, exist_ok=True)

H = 21
COST_BPS = 10
CLASS_COLOR = {"crypto": "#E45756", "equity": "#4C78A8", "commodity": "#F58518",
               "bond": "#54A24B", "real estate": "#B279A2"}

prices = pd.read_parquet(PRICES_PATH)
prices.index = pd.to_datetime(prices.index)
assets = [c for c in prices.columns if c != "SPY"]
fwd_1d = prices[assets].shift(-1) / prices[assets] - 1
spy_1d = prices["SPY"].shift(-1) / prices["SPY"] - 1

panel = build_vol_panel(prices, horizon=H)
fc = {"EWMA": panel["ewma"]}
coef_tbls = {}
for name, cols in [("HAR", HAR), ("HAR-L", HAR_L)]:
    fc[name], folds = walk_forward_vol(panel, cols, horizon=H)
    coef_tbls[name] = pd.DataFrame(folds).set_index("test_start")

oos_idx = fc["HAR"].index
F = pd.DataFrame({k: v.reindex(oos_idx) for k, v in fc.items()})
F["lrv_fut"] = panel.loc[oos_idx, "lrv_fut"]
ev = F.dropna()
rv2 = np.exp(2 * ev["lrv_fut"].to_numpy())


# ---------------------------------------------------------------------- #
# Forecast accuracy
# ---------------------------------------------------------------------- #
def within_r2(log_fc: pd.Series, log_rv: pd.Series) -> float:
    """R^2 of log-vol after removing each asset's own mean (no credit for
    simply knowing SOL is riskier than SHY)."""
    df = pd.DataFrame({"f": log_fc, "y": log_rv})
    resid = ((df["f"] - df["y"]) ** 2).sum()
    tot = df.groupby(level="ticker")["y"].transform(lambda s: (s - s.mean()) ** 2).sum()
    return 1 - resid / tot


ev_dates = ev.index.get_level_values("date").unique()
nonoverlap = ev_dates[::H]
loss = {k: pd.Series(qlike(rv2, ev[k].to_numpy() ** 2), index=ev.index) for k in fc}
acc_rows = []
for k in fc:
    log_fc = np.log(ev[k])
    # Diebold-Mariano style: average the loss gap across assets per date,
    # keep every H-th date (non-overlapping labels), t-test the mean.
    d = (loss["EWMA"] - loss[k]).groupby(level="date").mean().loc[nonoverlap]
    acc_rows.append({
        "forecaster": k,
        "qlike": loss[k].mean(),
        "qlike_improvement_vs_ewma": 1 - loss[k].mean() / loss["EWMA"].mean(),
        "log_mse": ((log_fc - ev["lrv_fut"]) ** 2).mean(),
        "within_asset_r2_log": within_r2(log_fc, ev["lrv_fut"]),
        "bias_log": (log_fc - ev["lrv_fut"]).mean(),
        "dm_t_vs_ewma": d.mean() / (d.std() / np.sqrt(len(d))) if k != "EWMA" else np.nan,
        "n_nonoverlap_dates": len(nonoverlap),
    })
acc = pd.DataFrame(acc_rows).set_index("forecaster")
acc.to_csv(TBL_DIR / f"{TAG}_forecast_accuracy.csv", float_format="%.4f")

per_asset = pd.DataFrame({
    t: {"class": ASSET_CLASS.get(t, "?"),
        "qlike_ewma": loss["EWMA"].xs(t, level="ticker").mean(),
        "qlike_har": loss["HAR"].xs(t, level="ticker").mean(),
        "improvement_har": 1 - loss["HAR"].xs(t, level="ticker").mean()
                             / loss["EWMA"].xs(t, level="ticker").mean()}
    for t in assets
}).T.sort_values("improvement_har")
per_asset.to_csv(TBL_DIR / f"{TAG}_per_asset.csv", float_format="%.4f")
pd.concat(coef_tbls, names=["model"]).to_csv(TBL_DIR / f"{TAG}_coefs.csv", float_format="%.4f")


# ---------------------------------------------------------------------- #
# Portfolios: same long-only inverse-vol rule, different vol input
# ---------------------------------------------------------------------- #
sig_wide = {k: F[k].unstack("ticker")[assets] for k in fc}
dates = sig_wide["HAR"].index
dates = dates[spy_1d.loc[dates].notna()]            # drop the final day (no t+1)
avail = sig_wide["HAR"].loc[dates].notna()          # same asset set for every book
ones = avail.astype(float).where(avail)

rets, port_rows = {}, []
books = {"equal_weight_1/N": avail.astype(float).div(avail.sum(axis=1), axis=0)}
books.update({f"sized_{k}": tsmom_weights(ones, sig_wide[k].loc[dates]) for k in fc})
for name, w in books.items():
    r = net_returns(w, fwd_1d.loc[dates], COST_BPS)
    rets[name] = r["net"]
    roll_vol = r["net"].rolling(63).std() * np.sqrt(252)
    port_rows.append({"strategy": name, **performance_metrics(r["net"]),
                      "avg_gross_exposure": w.abs().sum(axis=1).mean(),
                      "avg_daily_turnover": r["turnover"].iloc[1:].mean(),
                      "vol_of_rolling_vol": roll_vol.std()})
rets["SPY"] = spy_1d.loc[dates]
port_rows.append({"strategy": "SPY", **performance_metrics(rets["SPY"]),
                  "avg_gross_exposure": 1.0, "avg_daily_turnover": 0.0,
                  "vol_of_rolling_vol": (rets["SPY"].rolling(63).std() * np.sqrt(252)).std()})
port = pd.DataFrame(port_rows).set_index("strategy")
port.to_csv(TBL_DIR / f"{TAG}_portfolio.csv", float_format="%.4f")

yr = ev.index.get_level_values("date").year
by_year = pd.DataFrame({"qlike_improvement_har": 1 - loss["HAR"].groupby(yr).mean()
                                                  / loss["EWMA"].groupby(yr).mean()})
for name in ("equal_weight_1/N", "sized_EWMA", "sized_HAR"):
    by_year[f"ret_{name}"] = (1 + rets[name]).groupby(rets[name].index.year).prod() - 1
by_year.to_csv(TBL_DIR / f"{TAG}_by_year.csv", float_format="%.4f")

pd.set_option("display.width", 160)
print(f"OOS: {ev_dates[0].date()} -> {ev_dates[-1].date()}  ({len(ev):,} asset-days)")
print("\n=== Forecast accuracy (OOS, lower qlike/log_mse = better) ===")
print(acc.round(4).to_string())
print(f"\n=== Long-only book, net of {COST_BPS} bps ===")
print(port[["sharpe", "ann_ret", "ann_vol", "max_dd", "avg_gross_exposure",
            "avg_daily_turnover", "vol_of_rolling_vol"]].round(3).to_string())
print("\n=== Per-asset QLIKE, HAR vs EWMA ===")
print(per_asset.to_string(float_format=lambda v: f"{v:.3f}"))
print("\n=== By year ===")
print(by_year.to_string(float_format=lambda v: f"{v:.3f}"))
print("\n=== HAR coefficients: first / last fold ===")
print(coef_tbls["HAR"].iloc[[0, -1]].round(3).to_string())


# ============================================================================= #
# FIGURES
# ============================================================================= #
sh, dd = port["sharpe"], port["max_dd"]

# G1 — equity curves of the long-only book under each vol input
plt.figure(figsize=(11, 6))
for name, c in [("equal_weight_1/N", "#9D9D9D"), ("sized_EWMA", "#F58518"),
                ("sized_HAR", "#4C78A8"), ("sized_HAR-L", "#B279A2"), ("SPY", "#54A24B")]:
    plt.plot(equity_curve(rets[name]), color=c, lw=1.6 if name == "sized_HAR" else 1.1,
             label=f"{name}  (Sharpe {sh[name]:.2f}, maxDD {dd[name]:.0%})")
plt.yscale("log")
plt.ylabel("equity (log, starts at 1)")
plt.title(f"Task {TASK} — G1: long-only book sized by each vol forecast, OOS, net of {COST_BPS} bps")
plt.legend(loc="upper left", fontsize=9)
plt.grid(True, which="both", ls=":", alpha=0.5)
plt.tight_layout()
plt.savefig(FIG_DIR / f"{TAG}_g1_equity.png", dpi=130)
plt.close()

# G2 — per-asset forecast improvement of HAR over EWMA
plt.figure(figsize=(9, 7))
plt.barh(per_asset.index, 100 * per_asset["improvement_har"].astype(float),
         color=[CLASS_COLOR[c] for c in per_asset["class"]])
plt.axvline(0, color="k", lw=0.8)
plt.xlabel("QLIKE loss reduction vs EWMA (%)   — right = HAR forecasts better")
plt.title(f"Task {TASK} — G2: where HAR beats EWMA (next-{H}-day vol, OOS)")
plt.legend(handles=[Patch(color=c, label=k) for k, c in CLASS_COLOR.items()],
           loc="lower right", fontsize=8)
plt.grid(True, axis="x", ls=":", alpha=0.5)
plt.tight_layout()
plt.savefig(FIG_DIR / f"{TAG}_g2_per_asset_qlike.png", dpi=130)
plt.close()

# G3 — what a forecast looks like: BTC and TLT
fig, axes = plt.subplots(2, 1, figsize=(11, 7.5), sharex=True)
for ax, t in zip(axes, ["BTC-USD", "TLT"]):
    g = ev.xs(t, level="ticker") * np.sqrt(252)
    ax.plot(np.exp(ev.xs(t, level="ticker")["lrv_fut"]) * np.sqrt(252),
            color="k", lw=1.2, label=f"realised next-{H}-day vol")
    ax.plot(g["EWMA"], color="#F58518", lw=1, label="EWMA forecast")
    ax.plot(g["HAR"], color="#4C78A8", lw=1, label="HAR forecast")
    ax.set_ylabel(f"{t}  annualised vol")
    ax.grid(True, ls=":", alpha=0.5)
    ax.legend(fontsize=8, loc="upper right")
axes[0].set_title(f"Task {TASK} — G3: forecast vs what actually happened")
plt.tight_layout()
plt.savefig(FIG_DIR / f"{TAG}_g3_forecast_vs_realized.png", dpi=130)
plt.close()

for f in FIG_DIR.glob(f"{TAG}_g*.png"):
    shutil.copy2(f, VAULT_FIG / f.name)
print(f"\nSaved figures to {FIG_DIR} (copied to {VAULT_FIG})")
