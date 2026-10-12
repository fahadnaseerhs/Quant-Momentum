"""
Task 06 — Baseline (Model 0): rank-by-signal strategies.

Runs the pipeline on `data/features/features.parquet` and `data/processed/returns_daily.parquet`:
  - top-5 by vsmom_63d   (project starting hypothesis: 3M vol-scaled momentum)
  - top-5 by vsmom_21d
  - top-5 by mom_63d     (raw momentum, no vol scaling — to isolate the vol-scaling effect)
  - top-5 long / bottom-5 short, by vsmom_63d
  - equal-weight universe (static benchmark)
  - random top-5 (sanity floor; any real signal must beat this)
  - SPY (market benchmark)

Outputs:
  reports/tables/06_baseline_metrics.csv
  reports/tables/06_baseline_equity.csv
  reports/figures/06_g1_equity_curves.png
  reports/figures/06_g2_drawdowns.png
  reports/figures/06_g3_rolling_sharpe.png
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.baseline import (
    equal_weight_universe,
    equity_curve,
    performance_metrics,
    portfolio_returns,
    random_portfolio,
    rank_portfolio,
    turnover,
)

FEATURES_PATH = ROOT / "data" / "features" / "features.parquet"
RETURNS_PATH = ROOT / "data" / "processed" / "returns_daily.parquet"
FIG_DIR = ROOT / "reports" / "figures"
TBL_DIR = ROOT / "reports" / "tables"
FIG_DIR.mkdir(parents=True, exist_ok=True)
TBL_DIR.mkdir(parents=True, exist_ok=True)

TOP_N = 5


# ----------------------------------------------------------------------------- #
# Load
# ----------------------------------------------------------------------------- #
feats = pd.read_parquet(FEATURES_PATH)
rets = pd.read_parquet(RETURNS_PATH)
rets.index = pd.to_datetime(rets.index)

tradeables = sorted(feats.index.get_level_values("ticker").unique())
fwd_1d = feats["fwd_ret_1d"].unstack("ticker")[tradeables]
spy = rets["SPY"].reindex(fwd_1d.index)

print(f"features: {feats.shape},  tradeables: {len(tradeables)},  "
      f"date range: {fwd_1d.index.min().date()} -> {fwd_1d.index.max().date()}")


# ----------------------------------------------------------------------------- #
# Build strategies
# ----------------------------------------------------------------------------- #
strategies: dict[str, pd.Series] = {}
turnovers: dict[str, float] = {}

def _add(name, weights):
    strategies[name] = portfolio_returns(weights, fwd_1d)
    turnovers[name] = turnover(weights).mean()

_add("top5_vsmom_63d", rank_portfolio(feats, "vsmom_63d", TOP_N))
_add("top5_vsmom_21d", rank_portfolio(feats, "vsmom_21d", TOP_N))
_add("top5_mom_63d",   rank_portfolio(feats, "mom_63d",   TOP_N))
_add("ls_vsmom_63d",   rank_portfolio(feats, "vsmom_63d", TOP_N, long_short=True))

# Benchmarks
strategies["eq_weight_universe"] = equal_weight_universe(fwd_1d)
turnovers["eq_weight_universe"] = 0.0
strategies["random_top5"] = random_portfolio(fwd_1d, TOP_N, seed=42)
turnovers["random_top5"] = np.nan  # not comparable
strategies["SPY"] = spy
turnovers["SPY"] = 0.0


# ----------------------------------------------------------------------------- #
# Metrics table
# ----------------------------------------------------------------------------- #
rows = []
for name, r in strategies.items():
    m = performance_metrics(r)
    m["strategy"] = name
    m["avg_turnover_daily"] = turnovers[name]
    rows.append(m)

metrics = pd.DataFrame(rows).set_index("strategy")[
    ["cum_ret", "ann_ret", "ann_vol", "sharpe",
     "max_dd", "win_rate", "avg_turnover_daily", "n_days"]
]
metrics.to_csv(TBL_DIR / "06_baseline_metrics.csv", float_format="%.4f")
print("\n=== Performance ===")
print(metrics.round(3).to_string())


# ----------------------------------------------------------------------------- #
# Equity curves
# ----------------------------------------------------------------------------- #
eq = pd.DataFrame({k: equity_curve(v) for k, v in strategies.items()})
eq.to_csv(TBL_DIR / "06_baseline_equity.csv", float_format="%.6f")

plt.figure(figsize=(11, 6))
for col in eq.columns:
    plt.plot(eq.index, eq[col], label=col, lw=1.3)
plt.yscale("log")
plt.ylabel("Equity (log, starts at 1)")
plt.title("Task 06 — Baseline strategies: cumulative equity (before costs)")
plt.legend(loc="upper left", fontsize=9)
plt.grid(True, which="both", ls=":", alpha=0.5)
plt.tight_layout()
plt.savefig(FIG_DIR / "06_g1_equity_curves.png", dpi=130)
plt.close()


# ----------------------------------------------------------------------------- #
# Drawdowns
# ----------------------------------------------------------------------------- #
plt.figure(figsize=(11, 5))
for col in eq.columns:
    dd = eq[col] / eq[col].cummax() - 1
    plt.plot(dd.index, dd, label=col, lw=1.0)
plt.ylabel("Drawdown")
plt.title("Task 06 — Drawdowns")
plt.legend(loc="lower left", fontsize=9)
plt.grid(True, ls=":", alpha=0.5)
plt.tight_layout()
plt.savefig(FIG_DIR / "06_g2_drawdowns.png", dpi=130)
plt.close()


# ----------------------------------------------------------------------------- #
# Rolling 126-day Sharpe
# ----------------------------------------------------------------------------- #
window = 126
plt.figure(figsize=(11, 5))
for name, r in strategies.items():
    rs = r.rolling(window).mean() / r.rolling(window).std() * np.sqrt(252)
    plt.plot(rs.index, rs, label=name, lw=1.0)
plt.axhline(0, color="k", lw=0.6, ls="--")
plt.ylabel(f"Rolling {window}-day Sharpe (annualised)")
plt.title("Task 06 — Rolling Sharpe over time")
plt.legend(loc="upper left", fontsize=8)
plt.grid(True, ls=":", alpha=0.5)
plt.tight_layout()
plt.savefig(FIG_DIR / "06_g3_rolling_sharpe.png", dpi=130)
plt.close()

print(f"\nSaved figures to {FIG_DIR}")
print(f"Saved tables  to {TBL_DIR}")
