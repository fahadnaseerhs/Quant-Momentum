"""
Task 10 — Cut trading costs, then build the combined book (long core + trend).

Long history (data/long/, 2004–26).  Realistic simulation: positions drift
between rebalances, costs only on actual trades (src/portfolio.simulate).

HONEST SPLIT (fixed before running):
  design  = OOS dates up to 2015-12-31  -> ALL choices are made here
  holdout = 2016-01-01 onwards          -> reported, never used to choose
Choices made on the design period:
  1. rebalance every k in {1, 5, 21} days -> k* = best trend-model net Sharpe @ 10 bps
  2. trend share a in {0, .1, ..., .5} of the combined book -> a* = best net Sharpe (k*, 10 bps)

Outputs:
  reports/tables/10_rebalance_costs.csv   strategy x k x cost (full period)
  reports/tables/10_selection.csv         design-period grids for k and a
  reports/tables/10_final.csv             final books: design / holdout / full
  reports/tables/10_choice.json           k*, a* (re-used unchanged by Task 11)
  reports/figures/10_g1_combined_equity.png
  reports/figures/10_g2_cost_vs_rebalance.png
  (figures copied to Quant_Momentum/Figures/10/)
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.baseline import equity_curve, performance_metrics
from src.portfolio import simulate, target_books

PRICES_PATH = ROOT / "data" / "long" / "processed" / "prices_daily_clean.parquet"
FIG_DIR, TBL_DIR = ROOT / "reports" / "figures", ROOT / "reports" / "tables"
VAULT_FIG = ROOT / "Quant_Momentum" / "Figures" / "10"
for d in (FIG_DIR, TBL_DIR, VAULT_FIG):
    d.mkdir(parents=True, exist_ok=True)

DESIGN_END = "2015-12-31"
EVERY = (1, 5, 21)
COSTS = (5, 10, 20)
MIX = (0.0, 0.1, 0.2, 0.3, 0.4, 0.5)
BASE_COST = 10

prices = pd.read_parquet(PRICES_PATH)
prices.index = pd.to_datetime(prices.index)
books, fwd_1d, oos = target_books(prices)
spy = (prices["SPY"].shift(-1) / prices["SPY"] - 1).reindex(fwd_1d.index)
design = fwd_1d.index <= DESIGN_END
years = len(fwd_1d) / 252


def sharpe(r: pd.Series) -> float:
    return performance_metrics(r)["sharpe"]


# ---------------------------------------------------------------------- #
# 1. Rebalance frequency x cost level (full period, for the picture)
# ---------------------------------------------------------------------- #
rows, sims = [], {}
for name in books:
    for k in EVERY:
        base = simulate(books[name], fwd_1d, every=k, cost_bps=0)
        sims[(name, k)] = base
        for c in COSTS:
            net = base["net"] - c * 1e-4 * base["turnover"]
            m = performance_metrics(net)
            rows.append({"strategy": name, "rebalance_days": k, "cost_bps": c,
                         "sharpe": m["sharpe"], "ann_ret": m["ann_ret"], "max_dd": m["max_dd"],
                         "turnover_per_year": base["turnover"].sum() / years,
                         "cost_drag_per_year": c * 1e-4 * base["turnover"].sum() / years,
                         "design_sharpe": sharpe(net[design]),
                         "holdout_sharpe": sharpe(net[~design])})
grid = pd.DataFrame(rows).set_index(["strategy", "rebalance_days", "cost_bps"])
grid.to_csv(TBL_DIR / "10_rebalance_costs.csv", float_format="%.4f")

# ---------------------------------------------------------------------- #
# 2. Choices on the DESIGN period only
# ---------------------------------------------------------------------- #
k_star = int(grid.xs(("trend_model", BASE_COST), level=("strategy", "cost_bps"))["design_sharpe"].idxmax())

mix_rows, mix_sims = [], {}
for a in MIX:
    target = (1 - a) * books["long"] + a * books["trend_model"]
    sim = simulate(target, fwd_1d, every=k_star, cost_bps=BASE_COST)
    mix_sims[a] = sim
    mix_rows.append({"trend_share": a, "design_sharpe": sharpe(sim["net"][design]),
                     "design_max_dd": performance_metrics(sim["net"][design])["max_dd"]})
mix_tbl = pd.DataFrame(mix_rows).set_index("trend_share")
a_star = float(mix_tbl["design_sharpe"].idxmax())

sel = pd.concat({
    "k_grid (trend_model, 10bps)": grid.xs(("trend_model", BASE_COST), level=("strategy", "cost_bps"))[["design_sharpe"]]
                                       .rename_axis("value"),
    "a_grid (combined, k*)": mix_tbl[["design_sharpe"]].rename_axis("value"),
})
sel.to_csv(TBL_DIR / "10_selection.csv", float_format="%.4f")
(TBL_DIR / "10_choice.json").write_text(json.dumps({"k_star": k_star, "a_star": a_star}))

# ---------------------------------------------------------------------- #
# 3. Final books at the chosen settings
# ---------------------------------------------------------------------- #
final = {
    "long (daily, Task 07c)": simulate(books["long"], fwd_1d, 1, BASE_COST)["net"],
    f"long (every {k_star}d)": mix_sims[0.0]["net"],
    f"trend_model (every {k_star}d)": simulate(books["trend_model"], fwd_1d, k_star, BASE_COST)["net"],
    f"trend_rule (every {k_star}d)": simulate(books["trend_rule"], fwd_1d, k_star, BASE_COST)["net"],
    f"combined {1 - a_star:.0%} long + {a_star:.0%} trend": mix_sims[a_star]["net"],
    "SPY": spy,
}
frows = []
for name, r in final.items():
    for period, mask in [("design 2005-15", design), ("HOLDOUT 2016-26", ~design), ("full", np.ones_like(design))]:
        m = performance_metrics(r[mask])
        frows.append({"strategy": name, "period": period, **{k: m[k] for k in
                      ("sharpe", "ann_ret", "ann_vol", "max_dd")}})
final_tbl = pd.DataFrame(frows).set_index(["strategy", "period"])
final_tbl.to_csv(TBL_DIR / "10_final.csv", float_format="%.4f")

pd.set_option("display.width", 170)
print(f"OOS {fwd_1d.index[0].date()} -> {fwd_1d.index[-1].date()}; design ends {DESIGN_END}")
print("\n=== Rebalance x cost (full period) ===")
print(grid[["sharpe", "ann_ret", "turnover_per_year", "cost_drag_per_year", "design_sharpe", "holdout_sharpe"]]
      .round(3).to_string())
print(f"\n=== Design-period choices: k* = {k_star} days, a* = {a_star:.0%} trend ===")
print(mix_tbl.round(3).to_string())
print("\n=== Final books ===")
print(final_tbl.unstack("period").round(3).to_string())

# ============================================================================= #
# FIGURES
# ============================================================================= #
COL = {"long": "#9D9D9D", "trend": "#4C78A8", "combined": "#E45756", "SPY": "#54A24B"}
plt.figure(figsize=(11, 6))
for name, r in final.items():
    if "daily" in name or "rule" in name:
        continue
    key = next(k for k in COL if name.startswith(k))
    full_sh = final_tbl.loc[(name, "full"), "sharpe"]
    ho_sh = final_tbl.loc[(name, "HOLDOUT 2016-26"), "sharpe"]
    plt.plot(equity_curve(r), color=COL[key], lw=1.8 if key == "combined" else 1.2,
             label=f"{name}  (Sharpe full {full_sh:.2f} · holdout {ho_sh:.2f})")
plt.axvline(pd.Timestamp("2016-01-01"), color="k", ls="--", lw=1)
plt.text(pd.Timestamp("2016-03-01"), 0.03, "holdout →  (choices never saw this)", fontsize=9,
         transform=plt.gca().get_xaxis_transform())
plt.yscale("log")
plt.ylabel("equity (log, starts at 1)")
plt.title(f"Task 10 — G1: combined book, net of {BASE_COST} bps, positions drift between rebalances")
plt.legend(loc="upper left", fontsize=9)
plt.grid(True, which="both", ls=":", alpha=0.5)
plt.tight_layout()
plt.savefig(FIG_DIR / "10_g1_combined_equity.png", dpi=130)
plt.close()

g = grid.xs("trend_model", level="strategy")["sharpe"].unstack("cost_bps")
ax = g.plot.bar(figsize=(9, 5.5), color=["#54A24B", "#4C78A8", "#E45756"], rot=0)
ax.set_xticklabels([f"every {k} day{'s' if k > 1 else ''}" for k in g.index])
ax.set_xlabel("rebalance frequency")
ax.set_ylabel("net Sharpe (full 2005-26)")
ax.legend([f"{c} bps per trade" for c in g.columns], title="cost")
ax.axhline(0, color="k", lw=0.7)
ax.grid(True, axis="y", ls=":", alpha=0.5)
ax.set_title("Task 10 — G2: trend model, trading less often vs paying more per trade")
plt.tight_layout()
plt.savefig(FIG_DIR / "10_g2_cost_vs_rebalance.png", dpi=130)
plt.close()

for f in FIG_DIR.glob("10_g*.png"):
    shutil.copy2(f, VAULT_FIG / f.name)
print(f"\nSaved figures to {FIG_DIR} (copied to {VAULT_FIG})")
