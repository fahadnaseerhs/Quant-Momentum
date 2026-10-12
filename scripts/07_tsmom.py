"""
Task 07 (revised) — Time-series momentum prediction, leakage-safe walk-forward.

Pooled ridge (no intercept) on 4 vol-normalised trend/reversal features ->
vol-normalised forward return of the SAME asset.  Expanding window, monthly
refit, purge/embargo = horizon.  Primary horizon h = 21 (pre-committed);
h = 5 is reported as a robustness check only.

Benchmarks on the same OOS dates and the same position sizing:
  * rule   — sign of the average of the 3 trend features (no fitting)
  * long   — always long, same inverse-vol sizing (pure beta)
  * SPY
Net returns charge 10 bps per unit of weight traded.

Outputs:
  reports/tables/07_ts_prediction.csv
  reports/tables/07_ts_portfolio.csv
  reports/tables/07_ts_per_asset.csv
  reports/tables/07_ts_coefs.csv
  reports/figures/07_ts_g1_equity.png
  reports/figures/07_ts_g2_per_asset_ic.png
  reports/figures/07_ts_g3_ic_by_fold.png
  (figures copied to Quant_Momentum/Figures/07/)
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.baseline import equity_curve, performance_metrics
from src.tsmom import (
    ASSET_CLASS, FEATURES, build_panel, net_returns, tsmom_weights, walk_forward,
)

# `--long` re-runs everything on the 2004+ history (Task 07c, scripts/07c_fetch_long.py)
LONG = "--long" in sys.argv
TASK, TAG = ("07c", "07c_ts") if LONG else ("07", "07_ts")
PRICES_PATH = ROOT / "data" / ("long" if LONG else "") / "processed" / "prices_daily_clean.parquet"
FIG_DIR = ROOT / "reports" / "figures"
TBL_DIR = ROOT / "reports" / "tables"
VAULT_FIG = ROOT / "Quant_Momentum" / "Figures" / TASK
for d in (FIG_DIR, TBL_DIR, VAULT_FIG):
    d.mkdir(parents=True, exist_ok=True)

HORIZONS = (21, 5)       # 21 = primary (pre-committed), 5 = robustness
COST_BPS = 10
TREND = [f for f in FEATURES if f.startswith("mom_")]
CLASS_COLOR = {"crypto": "#E45756", "equity": "#4C78A8", "commodity": "#F58518",
               "bond": "#54A24B", "real estate": "#B279A2"}

prices = pd.read_parquet(PRICES_PATH)
prices.index = pd.to_datetime(prices.index)
assets = [c for c in prices.columns if c != "SPY"]
fwd_1d = (prices[assets].shift(-1) / prices[assets] - 1)
spy_1d = prices["SPY"].shift(-1) / prices["SPY"] - 1


def t_stat(ic: float, n: int) -> float:
    return ic * np.sqrt(n - 2) / np.sqrt(1 - ic ** 2)


pred_rows, port_rows, store = [], [], {}
for h in HORIZONS:
    panel = build_panel(prices, horizon=h)
    pred, folds = walk_forward(panel, horizon=h)
    oos = panel.loc[pred.index].assign(pred=pred)
    oos["rule"] = oos[TREND].mean(axis=1)
    ev = oos.dropna(subset=["y"])

    # non-overlapping sample: every h-th OOS date -> independent labels in time
    ev_dates = ev.index.get_level_values("date").unique()
    ev_no = ev.loc[ev.index.get_level_values("date").isin(ev_dates[::h])]

    for name in ("pred", "rule"):
        ic_no = np.corrcoef(ev_no[name], ev_no["y"])[0, 1]
        pred_rows.append({
            "horizon": h, "signal": "model" if name == "pred" else "rule",
            "ic_in_sample": np.mean([f["ic_in"] for f in folds]) if name == "pred" else np.nan,
            "ic_oos": np.corrcoef(ev[name], ev["y"])[0, 1],
            "rank_ic_oos": spearmanr(ev[name], ev["y"]).statistic,
            "ic_nonoverlap": ic_no,
            "t_nonoverlap": t_stat(ic_no, len(ev_no)),
            "n_nonoverlap": len(ev_no),
            "hit_rate": (np.sign(ev[name]) == np.sign(ev["fwd_raw"])).mean(),
            "always_long_hit": (ev["fwd_raw"] > 0).mean(),
            "n_oos_rows": len(ev),
        })

    # ---- portfolios on the OOS dates (last date has no next-day return) ----
    vol_w = oos["vol"].unstack("ticker")[assets]
    sigs = {
        "model": oos["pred"].unstack("ticker")[assets],
        "rule": oos["rule"].unstack("ticker")[assets],
        "long_only": vol_w.notna().astype(float),
    }
    dates = vol_w.index[spy_1d.loc[vol_w.index].notna()]   # drop the final day (no t+1)
    rets = {}
    for name, s in sigs.items():
        w = tsmom_weights(s.loc[dates], vol_w.loc[dates])
        r = net_returns(w, fwd_1d.loc[dates], COST_BPS)
        rets[name] = r["net"]
        port_rows.append({"horizon": h, "strategy": name,
                          "sharpe_gross": performance_metrics(r["gross"])["sharpe"],
                          **performance_metrics(r["net"]),
                          "avg_daily_turnover": r["turnover"].iloc[1:].mean()})
    rets["SPY"] = spy_1d.loc[dates]
    port_rows.append({"horizon": h, "strategy": "SPY",
                      "sharpe_gross": performance_metrics(rets["SPY"])["sharpe"],
                      **performance_metrics(rets["SPY"]), "avg_daily_turnover": 0.0})
    store[h] = {"ev": ev, "folds": folds, "rets": rets}

pred_tbl = pd.DataFrame(pred_rows).set_index(["horizon", "signal"])
port_tbl = pd.DataFrame(port_rows).set_index(["horizon", "strategy"])
pred_tbl.to_csv(TBL_DIR / f"{TAG}_prediction.csv", float_format="%.4f")
port_tbl.to_csv(TBL_DIR / f"{TAG}_portfolio.csv", float_format="%.4f")

# ---- per-asset and coefficients (primary horizon) ----
H = HORIZONS[0]
ev, folds, rets = store[H]["ev"], store[H]["folds"], store[H]["rets"]
per_asset = pd.DataFrame({
    t: {"class": ASSET_CLASS.get(t, "?"),
        "ic_model": np.corrcoef(g["pred"], g["y"])[0, 1],
        "ic_rule": np.corrcoef(g["rule"], g["y"])[0, 1],
        "hit_model": (np.sign(g["pred"]) == np.sign(g["fwd_raw"])).mean(),
        "always_long_hit": (g["fwd_raw"] > 0).mean()}
    for t, g in ev.groupby(level="ticker")
}).T.sort_values("ic_model")
per_asset.to_csv(TBL_DIR / f"{TAG}_per_asset.csv", float_format="%.4f")

coefs = pd.DataFrame([{"test_start": f["test_start"], **f["coef"]} for f in folds]).set_index("test_start")
coefs.to_csv(TBL_DIR / f"{TAG}_coefs.csv", float_format="%.4f")

# ---- by calendar year: when does trend work? ----
yr = ev.index.get_level_values("date").year
by_year = pd.DataFrame({
    "ic_model": ev.groupby(yr).apply(lambda g: np.corrcoef(g["pred"], g["y"])[0, 1]),
    "ic_rule": ev.groupby(yr).apply(lambda g: np.corrcoef(g["rule"], g["y"])[0, 1]),
    "n_assets": ev.groupby(yr).apply(lambda g: g.index.get_level_values("ticker").nunique()),
})
for name in ("model", "rule", "long_only", "SPY"):
    by_year[f"ret_{name}"] = (1 + rets[name]).groupby(rets[name].index.year).prod() - 1
by_year.to_csv(TBL_DIR / f"{TAG}_by_year.csv", float_format="%.4f")

pd.set_option("display.width", 160)
print("=== OOS prediction quality ===")
print(pred_tbl.round(4).to_string())
print(f"\n=== OOS portfolios (net of {COST_BPS} bps) ===")
print(port_tbl[["sharpe_gross", "sharpe", "ann_ret", "ann_vol", "max_dd", "avg_daily_turnover", "n_days"]]
      .round(3).to_string())
print(f"\n=== Per-asset OOS (h={H}) ===")
print(per_asset.to_string(float_format=lambda v: f"{v:.3f}"))
print(f"\n=== By year (h={H}) ===")
print(by_year.to_string(float_format=lambda v: f"{v:.3f}"))
print(f"\n=== Coefficients: first / last fold (h={H}) ===")
print(coefs.iloc[[0, -1]].round(3).to_string())


# ============================================================================= #
# FIGURES (primary horizon only)
# ============================================================================= #
sh = port_tbl.loc[H, "sharpe"]

# G1 — equity curves, net of costs
plt.figure(figsize=(11, 6))
for name, c in [("model", "#4C78A8"), ("rule", "#F58518"), ("long_only", "#9D9D9D"), ("SPY", "#54A24B")]:
    plt.plot(equity_curve(rets[name]), color=c, lw=1.6 if name == "model" else 1.2,
             label=f"{name}  (Sharpe {sh[name]:.2f})")
plt.yscale("log")
plt.ylabel("equity (log, starts at 1)")
plt.title(f"Task {TASK} — G1: time-series momentum, out-of-sample, net of {COST_BPS} bps (h={H})")
plt.legend(loc="upper left")
plt.grid(True, which="both", ls=":", alpha=0.5)
plt.tight_layout()
plt.savefig(FIG_DIR / f"{TAG}_g1_equity.png", dpi=130)
plt.close()

# G2 — per-asset OOS IC, coloured by asset class
plt.figure(figsize=(9, 7))
plt.barh(per_asset.index, per_asset["ic_model"].astype(float),
         color=[CLASS_COLOR[c] for c in per_asset["class"]])
plt.axvline(0, color="k", lw=0.8)
plt.xlabel(f"out-of-sample IC  (prediction vs realised {H}-day vol-normalised return)")
plt.title(f"Task {TASK} — G2: where the trend model predicts (h={H})")
plt.legend(handles=[Patch(color=c, label=k) for k, c in CLASS_COLOR.items()],
           loc="lower right", fontsize=8)
plt.grid(True, axis="x", ls=":", alpha=0.5)
plt.tight_layout()
plt.savefig(FIG_DIR / f"{TAG}_g2_per_asset_ic.png", dpi=130)
plt.close()

# G3 — in-sample vs out-of-sample IC per refit
fd = pd.DataFrame(folds).set_index("test_start")
plt.figure(figsize=(11, 5.5))
plt.bar(fd.index, fd["ic_oos"], width=18, color=np.where(fd["ic_oos"] > 0, "#4C78A8", "#E45756"),
        label="out-of-sample IC (each 21-day test block)")
plt.plot(fd.index, fd["ic_in"], color="k", lw=1.5, label="in-sample IC (training window)")
plt.axhline(fd["ic_oos"].mean(), color="#4C78A8", ls="--", lw=1,
            label=f"mean OOS IC = {fd['ic_oos'].mean():.3f}")
plt.axhline(0, color="k", lw=0.6)
plt.ylabel("IC")
plt.title(f"Task {TASK} — G3: in-sample vs out-of-sample IC at every refit (h={H})")
plt.legend(fontsize=8)
plt.grid(True, ls=":", alpha=0.5)
plt.tight_layout()
plt.savefig(FIG_DIR / f"{TAG}_g3_ic_by_fold.png", dpi=130)
plt.close()

for f in FIG_DIR.glob(f"{TAG}_g*.png"):
    shutil.copy2(f, VAULT_FIG / f.name)
print(f"\nSaved figures to {FIG_DIR} (copied to {VAULT_FIG})")
