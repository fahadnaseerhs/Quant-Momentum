"""
Task 07 — Model 1: LEAKAGE-SAFE walk-forward evaluation.

Expanding-window, out-of-sample, purge+embargo = target horizon.
Monthly refit (step=21), daily predictions. Targets: fwd_ret_1d and fwd_ret_3d.

This is the real evaluation (contrast with 07_linear_model.py, the in-sample
learning run). The 1d predictions drive a top-5 equal-weight portfolio judged
on the SAME basis as the Model 0 baseline (gross Sharpe 2.29).

Outputs:
  reports/tables/07_wf_metrics.csv
  reports/tables/07_wf_ic_timeseries.csv
  reports/figures/07_g6_wf_split_diagram.png
  reports/figures/07_g7_wf_cost_curves.png
  reports/figures/07_g8_wf_ic_timeseries.png
  reports/figures/07_g9_wf_cumulative_ic.png
  reports/figures/07_g10_wf_pred_vs_actual.png
  reports/figures/07_g11_wf_equity_vs_baseline.png
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.linear_model import mae, rmse, walk_forward_predict
from src.baseline import (
    equity_curve,
    performance_metrics,
    portfolio_returns,
    rank_portfolio,
)

FEATURES_PATH = ROOT / "data" / "features" / "features.parquet"
RETURNS_PATH = ROOT / "data" / "processed" / "returns_daily.parquet"
FIG_DIR = ROOT / "reports" / "figures"
TBL_DIR = ROOT / "reports" / "tables"
FIG_DIR.mkdir(parents=True, exist_ok=True)
TBL_DIR.mkdir(parents=True, exist_ok=True)

FEATURE_COLS = [
    "mom_5d", "mom_10d", "mom_21d", "mom_63d",
    "ewma_vol", "roll_vol_63d",
    "vsmom_5d", "vsmom_10d", "vsmom_21d", "vsmom_63d",
    "vol_ratio_20d",
    "relret_5d", "relret_10d", "relret_21d", "relret_63d",
]
LR, N_EPOCHS, INITIAL_TRAIN, STEP, TOP_N = 0.2, 1500, 252, 21, 5


def daily_ic(pred: pd.Series, actual: pd.Series) -> pd.Series:
    """Daily cross-sectional Spearman rank IC between pred and realised."""
    df = pd.DataFrame({"p": pred, "a": actual}).dropna()
    out = {}
    for dt, g in df.groupby(level="date"):
        if g.shape[0] >= 3 and g["p"].std() > 0 and g["a"].std() > 0:
            out[dt] = spearmanr(g["p"], g["a"]).correlation
    return pd.Series(out).sort_index()


# ----------------------------------------------------------------------------- #
# Load
# ----------------------------------------------------------------------------- #
feats = pd.read_parquet(FEATURES_PATH)
rets = pd.read_parquet(RETURNS_PATH)
rets.index = pd.to_datetime(rets.index)

print("Running walk-forward (expanding, monthly refit)...")
results = {}
for target, horizon in [("fwd_ret_1d", 1), ("fwd_ret_3d", 3)]:
    data = feats[FEATURE_COLS + [target]].dropna().sort_index()
    preds, folds = walk_forward_predict(
        data, FEATURE_COLS, target,
        horizon=horizon, lr=LR, n_epochs=N_EPOCHS,
        initial_train=INITIAL_TRAIN, step=STEP,
    )
    actual = data.loc[preds.index, target]
    ic = daily_ic(preds, actual)
    results[target] = {
        "preds": preds, "actual": actual, "folds": folds, "ic": ic,
        "mae": mae(actual.to_numpy(), preds.to_numpy()),
        "rmse": rmse(actual.to_numpy(), preds.to_numpy()),
        "ic_mean": ic.mean(), "ic_std": ic.std(),
        "icir": ic.mean() / ic.std() * np.sqrt(252) if ic.std() > 0 else np.nan,
    }
    print(f"  {target}: {len(folds)} folds, {len(preds):,} OOS preds, "
          f"mean daily IC = {ic.mean():.4f}, ICIR(ann) = {results[target]['icir']:.2f}")


# ----------------------------------------------------------------------------- #
# Portfolio from 1d OOS predictions  (vs baseline + SPY)
# ----------------------------------------------------------------------------- #
pred1d = results["fwd_ret_1d"]["preds"]
tradeables = sorted(feats.index.get_level_values("ticker").unique())
fwd_1d_wide = feats["fwd_ret_1d"].unstack("ticker")[tradeables]

pred_df = pd.DataFrame({"pred": pred1d, "fwd_ret_1d": feats.loc[pred1d.index, "fwd_ret_1d"]})
w_model = rank_portfolio(pred_df, "pred", TOP_N)
ret_model = portfolio_returns(w_model, fwd_1d_wide)

w_base = rank_portfolio(feats, "vsmom_21d", TOP_N)
ret_base = portfolio_returns(w_base, fwd_1d_wide).reindex(ret_model.index)
spy = rets["SPY"].reindex(ret_model.index)

port = {
    "linear_oos_top5": ret_model,
    "baseline_vsmom21d_top5": ret_base,
    "SPY": spy,
}
rows = []
for name, r in port.items():
    m = performance_metrics(r)
    m["strategy"] = name
    rows.append(m)
port_metrics = pd.DataFrame(rows).set_index("strategy")

# ----------------------------------------------------------------------------- #
# Metrics tables
# ----------------------------------------------------------------------------- #
pred_metrics = pd.DataFrame({
    t: {"mae": results[t]["mae"], "rmse": results[t]["rmse"],
        "ic_mean": results[t]["ic_mean"], "ic_std": results[t]["ic_std"],
        "icir_ann": results[t]["icir"], "n_oos": len(results[t]["preds"]),
        "n_folds": len(results[t]["folds"])}
    for t in results
}).T
pred_metrics.to_csv(TBL_DIR / "07_wf_metrics.csv", float_format="%.6g")
port_metrics.to_csv(TBL_DIR / "07_wf_portfolio_metrics.csv", float_format="%.4f")
pd.DataFrame({t: results[t]["ic"] for t in results}).to_csv(
    TBL_DIR / "07_wf_ic_timeseries.csv", float_format="%.6g")

print("\n=== OOS prediction quality ===")
print(pred_metrics.round(4).to_string())
print("\n=== OOS portfolio (same rules as Model 0) ===")
print(port_metrics[["cum_ret", "ann_ret", "ann_vol", "sharpe", "max_dd", "win_rate", "n_days"]].round(3).to_string())


# ============================================================================= #
# FIGURES
# ============================================================================= #
folds1d = results["fwd_ret_1d"]["folds"]

# G6 — walk-forward split diagram (first 12 folds, for legibility)
plt.figure(figsize=(11, 6))
show = folds1d[:12]
for i, f in enumerate(show):
    y = len(show) - i
    plt.plot([f["train_start"], f["train_end"]], [y, y], lw=6, color="#4C78A8",
             solid_capstyle="butt")
    plt.plot([f["train_end"], f["test_start"]], [y, y], lw=6, color="#E45756",
             solid_capstyle="butt")  # purge+embargo gap
    plt.plot([f["test_start"], f["test_end"]], [y, y], lw=6, color="#54A24B",
             solid_capstyle="butt")
plt.yticks([len(show) - i for i in range(len(show))],
           [f"fold {i+1}" for i in range(len(show))], fontsize=8)
plt.xlabel("date")
plt.title("Task 07 — G6: expanding walk-forward splits  "
          "(blue=train · red=purge/embargo · green=test)")
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
plt.grid(True, axis="x", ls=":", alpha=0.5)
plt.tight_layout()
plt.savefig(FIG_DIR / "07_g6_wf_split_diagram.png", dpi=130)
plt.close()

# G7 — per-fold cost curves (training convergence over time)
plt.figure(figsize=(10, 6))
cmap = plt.cm.viridis
nf = len(folds1d)
for i, f in enumerate(folds1d):
    plt.plot(f["cost"], color=cmap(i / max(nf - 1, 1)), lw=0.8, alpha=0.8)
sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(0, nf - 1))
cbar = plt.colorbar(sm, ax=plt.gca())
cbar.set_label("fold (earliest → latest)")
plt.xlabel("epoch")
plt.ylabel(r"cost  $J=\frac{1}{2m}\sum(\hat{y}-y)^2$")
plt.title("Task 07 — G7: gradient-descent training, every walk-forward fold (1d)")
plt.grid(True, ls=":", alpha=0.5)
plt.tight_layout()
plt.savefig(FIG_DIR / "07_g7_wf_cost_curves.png", dpi=130)
plt.close()

# G8 — OOS daily IC time series
plt.figure(figsize=(11, 5.5))
for t, c in [("fwd_ret_1d", "#4C78A8"), ("fwd_ret_3d", "#F58518")]:
    ic = results[t]["ic"]
    plt.plot(ic.index, ic.rolling(21).mean(), color=c, lw=1.4,
             label=f"{t}  (21d-smoothed, mean={ic.mean():.3f})")
plt.axhline(0, color="k", lw=0.7, ls="--")
plt.ylabel("daily cross-sectional rank IC")
plt.title("Task 07 — G8: out-of-sample IC over time (21-day smoothed)")
plt.legend()
plt.grid(True, ls=":", alpha=0.5)
plt.tight_layout()
plt.savefig(FIG_DIR / "07_g8_wf_ic_timeseries.png", dpi=130)
plt.close()

# G9 — cumulative OOS IC
plt.figure(figsize=(11, 5.5))
for t, c in [("fwd_ret_1d", "#4C78A8"), ("fwd_ret_3d", "#F58518")]:
    plt.plot(results[t]["ic"].index, results[t]["ic"].cumsum(), color=c, lw=1.5, label=t)
plt.axhline(0, color="k", lw=0.7, ls="--")
plt.ylabel("cumulative daily IC")
plt.title("Task 07 — G9: cumulative out-of-sample IC (steady rise = persistent edge)")
plt.legend()
plt.grid(True, ls=":", alpha=0.5)
plt.tight_layout()
plt.savefig(FIG_DIR / "07_g9_wf_cumulative_ic.png", dpi=130)
plt.close()

# G10 — OOS predicted vs actual (1d)
p, a = results["fwd_ret_1d"]["preds"].to_numpy(), results["fwd_ret_1d"]["actual"].to_numpy()
plt.figure(figsize=(7.5, 7))
plt.scatter(p, a, s=6, alpha=0.15)
lim = np.percentile(np.abs(a), 99)
plt.plot([-lim, lim], [-lim, lim], "r--", lw=1, label="perfect prediction")
plt.xlim(-lim, lim); plt.ylim(-lim, lim)
plt.xlabel("predicted ŷ (out-of-sample)")
plt.ylabel("actual fwd_ret_1d")
plt.title(f"Task 07 — G10: OOS predicted vs actual (1d)\n"
          f"mean daily IC = {results['fwd_ret_1d']['ic_mean']:.3f}")
plt.legend()
plt.grid(True, ls=":", alpha=0.5)
plt.tight_layout()
plt.savefig(FIG_DIR / "07_g10_wf_pred_vs_actual.png", dpi=130)
plt.close()

# G11 — equity curve vs baseline
eq = pd.DataFrame({k: equity_curve(v) for k, v in port.items()})
plt.figure(figsize=(11, 6))
for col in eq.columns:
    plt.plot(eq.index, eq[col], lw=1.4, label=f"{col}  (Sharpe {port_metrics.loc[col,'sharpe']:.2f})")
plt.yscale("log")
plt.ylabel("equity (log, starts at 1)")
plt.title("Task 07 — G11: OOS linear model vs Model 0 baseline (gross, no costs)")
plt.legend(loc="upper left", fontsize=9)
plt.grid(True, which="both", ls=":", alpha=0.5)
plt.tight_layout()
plt.savefig(FIG_DIR / "07_g11_wf_equity_vs_baseline.png", dpi=130)
plt.close()

print(f"\nSaved figures to {FIG_DIR}")
print(f"Saved tables  to {TBL_DIR}")
