"""
Task 11 — Robustness: re-run everything on a universe chosen WITHOUT hindsight.

The project universe (20 assets) was picked in 2026, so it contains known
winners (NVDA, MSTR, BTC, SOL).  Here: 23 broad ETFs that an investor could
have listed in 2005 — index, sector, bond, commodity and REIT funds, no single
stocks, no crypto.  Every setting is FROZEN from earlier tasks:
  * features / model / walk-forward: Task 07 (src/tsmom.py), h = 21
  * rebalance every k* days, trend share a*: Task 10 design period (10_choice.json)
Nothing is re-tuned on this data.

Outputs:
  data/etf/processed/prices_daily_clean.parquet  (+ cleaning_log.txt)
  reports/tables/11_etf_prediction.csv
  reports/tables/11_etf_final.csv
  reports/tables/11_etf_per_asset.csv
  reports/figures/11_g1_etf_equity.png  (copied to Quant_Momentum/Figures/11/)
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.baseline import equity_curve, performance_metrics
from src.cleaning import align_to_calendar, audit, fill_short_gaps, to_returns, trading_calendar
from src.portfolio import simulate, target_books

ETF_CLASS = {
    "SPY": "equity index", "QQQ": "equity index", "IWM": "equity index",
    "EFA": "equity index", "EEM": "equity index",
    "XLB": "sector", "XLE": "sector", "XLF": "sector", "XLI": "sector", "XLK": "sector",
    "XLP": "sector", "XLU": "sector", "XLV": "sector", "XLY": "sector",
    "SHY": "bond", "IEF": "bond", "TLT": "bond", "LQD": "bond", "TIP": "bond",
    "GLD": "commodity", "DBC": "commodity", "USO": "commodity",
    "VNQ": "real estate",
}
START, DESIGN_END, COST = "2004-01-01", "2015-12-31", 10
DATA_DIR = ROOT / "data" / "etf" / "processed"
FIG_DIR, TBL_DIR = ROOT / "reports" / "figures", ROOT / "reports" / "tables"
VAULT_FIG = ROOT / "Quant_Momentum" / "Figures" / "11"
for d in (DATA_DIR, FIG_DIR, TBL_DIR, VAULT_FIG):
    d.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------- #
# Data (same cleaning rules as Tasks 01–02)
# ---------------------------------------------------------------------- #
px_path = DATA_DIR / "prices_daily_clean.parquet"
if not px_path.exists():
    tickers = list(ETF_CLASS)
    raw = yf.download(tickers=tickers, start=START, auto_adjust=True, progress=False,
                      group_by="ticker", threads=True)
    close = pd.concat({t: raw[t]["Close"] for t in tickers if t in raw.columns.get_level_values(0)}, axis=1)
    prices = align_to_calendar(close, trading_calendar(close, "SPY"))
    prices, fill_report = fill_short_gaps(prices, max_fill=2)
    prices.to_parquet(px_path)
    rep = audit(close, prices, fill_report, to_returns(prices))
    (DATA_DIR / "cleaning_log.txt").write_text("\n".join(
        [f"Range: {rep['range'][0]} -> {rep['range'][1]}"] +
        [f"{t:<5} first {s['first_valid']}  filled {s['filled']}  long_gaps {s['long_gaps'] or '-'}"
         for t, s in rep["per_ticker"].items()]) + "\n", encoding="utf-8")
prices = pd.read_parquet(px_path)
prices.index = pd.to_datetime(prices.index)
print(f"ETF universe: {prices.shape[1]} funds, {prices.index[0].date()} -> {prices.index[-1].date()}")

choice = json.loads((TBL_DIR / "10_choice.json").read_text())
k, a = choice["k_star"], choice["a_star"]

# SPY is a tradeable here (benchmark=None); it is also the buy-and-hold yardstick.
books, fwd_1d, oos = target_books(prices, benchmark=None)
spy = (prices["SPY"].shift(-1) / prices["SPY"] - 1).reindex(fwd_1d.index)
design = fwd_1d.index <= DESIGN_END

# ---------------------------------------------------------------------- #
# Prediction quality
# ---------------------------------------------------------------------- #
ev = oos.dropna(subset=["y"])
ev_dates = ev.index.get_level_values("date").unique()
ev_no = ev.loc[ev.index.get_level_values("date").isin(ev_dates[::21])]
pred_rows = []
for sig in ("pred", "rule"):
    ic_no = np.corrcoef(ev_no[sig], ev_no["y"])[0, 1]
    pred_rows.append({"signal": "model" if sig == "pred" else "rule",
                      "ic_oos": np.corrcoef(ev[sig], ev["y"])[0, 1],
                      "ic_nonoverlap": ic_no,
                      "t_nonoverlap": ic_no * np.sqrt(len(ev_no) - 2) / np.sqrt(1 - ic_no ** 2),
                      "hit_rate": (np.sign(ev[sig]) == np.sign(ev["fwd_raw"])).mean(),
                      "always_long_hit": (ev["fwd_raw"] > 0).mean()})
pred_tbl = pd.DataFrame(pred_rows).set_index("signal")
pred_tbl.to_csv(TBL_DIR / "11_etf_prediction.csv", float_format="%.4f")

per_asset = pd.DataFrame({
    t: {"class": ETF_CLASS[t], "ic_model": np.corrcoef(g["pred"], g["y"])[0, 1]}
    for t, g in ev.groupby(level="ticker")}).T.sort_values("ic_model")
per_asset.to_csv(TBL_DIR / "11_etf_per_asset.csv", float_format="%.4f")

# ---------------------------------------------------------------------- #
# Books at the frozen settings
# ---------------------------------------------------------------------- #
final = {
    f"long (every {k}d)": simulate(books["long"], fwd_1d, k, COST)["net"],
    f"trend_model (every {k}d)": simulate(books["trend_model"], fwd_1d, k, COST)["net"],
    f"combined {1 - a:.0%} long + {a:.0%} trend":
        simulate((1 - a) * books["long"] + a * books["trend_model"], fwd_1d, k, COST)["net"],
    "SPY": spy,
}
rows = []
for name, r in final.items():
    for period, mask in [("design 2005-15", design), ("HOLDOUT 2016-26", ~design), ("full", np.ones_like(design))]:
        m = performance_metrics(r[mask])
        rows.append({"strategy": name, "period": period,
                     **{x: m[x] for x in ("sharpe", "ann_ret", "ann_vol", "max_dd")},
                     "t_sharpe": m["sharpe"] * np.sqrt(mask.sum() / 252)})
final_tbl = pd.DataFrame(rows).set_index(["strategy", "period"])
final_tbl.to_csv(TBL_DIR / "11_etf_final.csv", float_format="%.4f")

crisis = pd.DataFrame({name: {c: (1 + r.loc[s:e]).prod() - 1 for c, (s, e) in
                              {"2008-01..2009-03": ("2008-01-01", "2009-03-31"),
                               "2020 Feb-Mar": ("2020-02-15", "2020-03-31"),
                               "2022": ("2022-01-01", "2022-12-31")}.items()}
                       for name, r in final.items()})

pd.set_option("display.width", 170)
print(f"Frozen settings from Task 10: rebalance every {k} days, trend share {a:.0%}")
print("\n=== OOS prediction (h=21) ===")
print(pred_tbl.round(4).to_string())
print("\n=== Books, net of 10 bps ===")
print(final_tbl.unstack("period").round(3).to_string())
print("\n=== Crisis returns ===")
print(crisis.round(3).to_string())
print("\n=== Per-asset IC ===")
print(per_asset.to_string(float_format=lambda v: f"{v:.3f}"))

# ---------------------------------------------------------------------- #
# Figure
# ---------------------------------------------------------------------- #
COL = {"long": "#9D9D9D", "trend": "#4C78A8", "combined": "#E45756", "SPY": "#54A24B"}
plt.figure(figsize=(11, 6))
for name, r in final.items():
    key = next(c for c in COL if name.startswith(c))
    plt.plot(equity_curve(r), color=COL[key], lw=1.8 if key == "combined" else 1.2,
             label=f"{name}  (Sharpe {final_tbl.loc[(name, 'full'), 'sharpe']:.2f}, "
                   f"maxDD {final_tbl.loc[(name, 'full'), 'max_dd']:.0%})")
plt.axvline(pd.Timestamp("2016-01-01"), color="k", ls="--", lw=1)
plt.yscale("log")
plt.ylabel("equity (log, starts at 1)")
plt.title("Task 11 — G1: same strategy on 23 broad ETFs (no hindsight picks), frozen settings, net of 10 bps")
plt.legend(loc="upper left", fontsize=9)
plt.grid(True, which="both", ls=":", alpha=0.5)
plt.tight_layout()
plt.savefig(FIG_DIR / "11_g1_etf_equity.png", dpi=130)
plt.close()
shutil.copy2(FIG_DIR / "11_g1_etf_equity.png", VAULT_FIG / "11_g1_etf_equity.png")
print(f"\nSaved figure to {FIG_DIR} (copied to {VAULT_FIG})")
