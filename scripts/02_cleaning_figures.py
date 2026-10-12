"""Task 02 — figures that illustrate what the cleaning step did.

Run from the project root:

    python scripts/02_cleaning_figures.py

Inputs:
    data/raw/prices_daily.parquet          (calendar-day grid, before cleaning)
    data/processed/prices_daily_clean.parquet
    data/processed/returns_daily.parquet

Outputs:
    reports/figures/02_g1_calendar_alignment.png
    reports/figures/02_g2_annual_vol_by_ticker.png
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.universe import UNIVERSE  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "prices_daily.parquet"
CLEAN = ROOT / "data" / "processed" / "prices_daily_clean.parquet"
RETURNS = ROOT / "data" / "processed" / "returns_daily.parquet"
FIGURES_DIR = ROOT / "reports" / "figures"

CLASS_COLORS = {
    "crypto":      "#f7931a",
    "tech":        "#00b4d8",
    "gold":        "#d4a900",
    "oil":         "#6b4226",
    "real_assets": "#8338ec",
    "bonds":       "#2dc653",
}
TICKER_CLASS = {t: c for c, ts in UNIVERSE.items() for t in ts}
TICKER_CLASS["SPY"] = "benchmark"
CLASS_COLORS["benchmark"] = "#888888"


def plot_calendar_alignment(raw: pd.DataFrame, clean: pd.DataFrame) -> plt.Figure:
    """Four weeks around US Thanksgiving: which days exist before and after alignment."""
    start, end = pd.Timestamp("2024-11-18"), pd.Timestamp("2024-12-08")
    days = pd.date_range(start, end, freq="D")
    raw_w = raw.reindex(days)
    kept = set(clean.index)

    fig, ax = plt.subplots(figsize=(13, 3.8))
    rows = [("BTC-USD  (raw)", raw_w["BTC-USD"].notna().values, "#f7931a"),
            ("SPY  (raw)", raw_w["SPY"].notna().values, "#4c78a8"),
            ("BTC-USD  (after alignment)",
             np.array([d in kept for d in days]) & raw_w["BTC-USD"].notna().values, "#f7931a")]

    for y, (label, present, color) in enumerate(reversed(rows)):
        xs = np.arange(len(days))
        ax.scatter(xs[present], np.full(present.sum(), y), s=170, color=color, zorder=3)
        ax.scatter(xs[~present], np.full((~present).sum(), y), s=170,
                   facecolor="none", edgecolor="#bbbbbb", zorder=2)

    weekend = [i for i, d in enumerate(days) if d.dayofweek >= 5]
    for i in weekend:
        ax.axvspan(i - 0.5, i + 0.5, color="#000000", alpha=0.06, lw=0)
    thanks = list(days).index(pd.Timestamp("2024-11-28"))
    ax.axvspan(thanks - 0.5, thanks + 0.5, color="#d62728", alpha=0.12, lw=0)
    ax.text(thanks, 2.55, "US Thanksgiving\n(NYSE closed)", ha="center", fontsize=8, color="#d62728")

    ax.set_yticks(range(3))
    ax.set_yticklabels([r[0] for r in reversed(rows)])
    ax.set_xticks(range(len(days)))
    ax.set_xticklabels([d.strftime("%a\n%d %b") for d in days], fontsize=7)
    ax.set_ylim(-0.6, 3.0)
    ax.set_title("Task 02 — one common calendar: crypto trades every day, SPY only on NYSE days\n"
                 "Filled dot = price exists, hollow = no price. Grey bands = weekends.", fontsize=11)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    return fig


def plot_annual_vol(returns: pd.DataFrame) -> plt.Figure:
    vol = (returns.std() * np.sqrt(252)).sort_values()
    colors = [CLASS_COLORS[TICKER_CLASS[t]] for t in vol.index]

    fig, ax = plt.subplots(figsize=(10, 7))
    ax.barh(vol.index, vol.values * 100, color=colors)
    ax.set_xscale("log")
    for y, v in enumerate(vol.values):
        ax.text(v * 100 * 1.04, y, f"{v:.1%}", va="center", fontsize=8)
    ax.set_xlabel("annualised volatility, % per year (log scale)")
    ax.set_title("Task 02 — annual volatility per asset after cleaning\n"
                 f"{vol.iloc[-1] / vol.iloc[0]:.0f}× spread between the calmest and wildest asset")
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in CLASS_COLORS.values()]
    ax.legend(handles, [k.replace("_", " ") for k in CLASS_COLORS], loc="lower right", fontsize=8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    return fig


def main() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    raw = pd.read_parquet(RAW)
    clean = pd.read_parquet(CLEAN)
    returns = pd.read_parquet(RETURNS)

    for fig, name in [(plot_calendar_alignment(raw, clean), "02_g1_calendar_alignment.png"),
                      (plot_annual_vol(returns), "02_g2_annual_vol_by_ticker.png")]:
        fig.savefig(FIGURES_DIR / name, dpi=150, bbox_inches="tight", facecolor="white")
        print(f"  Saved figure: {FIGURES_DIR / name}")


if __name__ == "__main__":
    main()
