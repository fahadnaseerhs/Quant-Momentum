"""Build the feature matrix from cleaned data, save as parquet, and show graphs.

Run from the project root:

    python scripts/04_build_features.py

Input:
    data/processed/prices_daily_clean.parquet
    data/processed/returns_daily.parquet
    data/processed/volume_daily_clean.parquet

Output:
    data/features/features.parquet   (long-format: index = date × ticker)
    data/features/build_log.txt
    reports/figures/04_*.png          (8 diagnostic graphs)
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# Allow running from project root without install.
sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.features import build_all_features  # noqa: E402
from src.universe import BENCHMARK, UNIVERSE  # noqa: E402


PROCESSED_DIR = Path(__file__).resolve().parents[1] / "data" / "processed"
FEATURES_DIR  = Path(__file__).resolve().parents[1] / "data" / "features"
FIGURES_DIR   = Path(__file__).resolve().parents[1] / "reports" / "figures"

# ── Asset-class colour palette (consistent across all graphs) ────────
CLASS_COLORS = {
    "crypto":      "#f7931a",   # bitcoin orange
    "tech":        "#00b4d8",   # electric blue
    "gold":        "#ffd700",   # gold
    "oil":         "#6b4226",   # crude brown
    "real_assets": "#8338ec",   # purple
    "bonds":       "#2dc653",   # green
}

TICKER_CLASS = {
    ticker: cls for cls, tickers in UNIVERSE.items() for ticker in tickers
}


def _savefig(fig: plt.Figure, name: str) -> None:
    """Save a figure to the reports/figures directory."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES_DIR / name, dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    print(f"  Saved figure: {FIGURES_DIR / name}")


# ═══════════════════════════════════════════════════════════════════════
#  GRAPH 1 — Feature Correlation Heatmap
#  "Which features carry the same information?"
# ═══════════════════════════════════════════════════════════════════════
def plot_correlation_heatmap(features: pd.DataFrame) -> plt.Figure:
    """Pearson correlation of all 17 columns (features + targets)."""
    corr = features.corr()
    fig, ax = plt.subplots(figsize=(12, 10))
    fig.patch.set_facecolor("#0e1117")
    ax.set_facecolor("#0e1117")

    mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
    cmap = sns.diverging_palette(250, 15, s=85, l=40, n=256, as_cmap=True)
    sns.heatmap(corr, mask=mask, cmap=cmap, center=0, vmin=-1, vmax=1,
                annot=True, fmt=".2f", linewidths=0.5,
                annot_kws={"size": 7, "color": "white"},
                cbar_kws={"shrink": 0.8, "label": "Pearson r"},
                square=True, ax=ax)

    ax.set_title("Feature Correlation Matrix\n"
                 "Which features carry the same information?",
                 fontsize=14, fontweight="bold", color="white", pad=15)
    ax.tick_params(colors="white", labelsize=8)
    cbar = ax.collections[0].colorbar
    cbar.ax.yaxis.label.set_color("white")
    cbar.ax.tick_params(colors="white")

    fig.tight_layout()
    return fig


# ═══════════════════════════════════════════════════════════════════════
#  GRAPH 2 — 21-Day Momentum Time Series by Asset Class
#  "What does momentum actually look like for each group?"
# ═══════════════════════════════════════════════════════════════════════
def plot_momentum_timeseries(features: pd.DataFrame) -> plt.Figure:
    """21-day momentum over time, one subplot per asset class."""
    classes = list(UNIVERSE.keys())
    fig, axes = plt.subplots(len(classes), 1, figsize=(16, 3.5 * len(classes)),
                             sharex=True)
    fig.patch.set_facecolor("#0e1117")
    fig.suptitle("21-Day Momentum Over Time — by Asset Class",
                 fontsize=18, fontweight="bold", color="white", y=1.005)

    for idx, cls in enumerate(classes):
        ax = axes[idx]
        ax.set_facecolor("#1a1d23")
        tickers = UNIVERSE[cls]
        color = CLASS_COLORS[cls]

        for ticker in tickers:
            try:
                series = features.xs(ticker, level="ticker")["mom_21d"].dropna()
                ax.plot(series.index, series.values, lw=0.9, alpha=0.85,
                        color=color, label=ticker)
            except KeyError:
                continue

        ax.axhline(0, color="#555", ls="-", lw=0.6)
        ax.set_ylabel("mom_21d", fontsize=9, color="white")
        ax.set_title(f"{cls.replace('_', ' ').title()}", fontsize=12,
                     fontweight="bold", color=color, loc="left")
        ax.legend(fontsize=7, ncol=len(tickers), loc="upper right",
                  facecolor="#1a1d23", labelcolor="white", framealpha=0.7)
        ax.tick_params(colors="white", labelsize=8)
        for spine in ax.spines.values():
            spine.set_color("#333")

    fig.tight_layout()
    return fig


# ═══════════════════════════════════════════════════════════════════════
#  GRAPH 3 — Vol-Scaled Momentum: Why Dividing by Volatility Matters
#  Before: crypto swamps everything.  After: fair comparison.
# ═══════════════════════════════════════════════════════════════════════
def plot_vsmom_comparison(features: pd.DataFrame) -> plt.Figure:
    """Side-by-side: raw momentum vs vol-scaled momentum by asset class."""
    df = features[["mom_21d", "vsmom_21d"]].copy().reset_index()
    df["class"] = df["ticker"].map(TICKER_CLASS)
    df = df.dropna(subset=["mom_21d", "vsmom_21d", "class"])

    order = list(CLASS_COLORS.keys())
    palette = [CLASS_COLORS[c] for c in order]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 7))
    fig.patch.set_facecolor("#0e1117")
    fig.suptitle("Why Vol-Scaling Matters\n"
                 "Left: raw momentum (crypto dominates)   →   "
                 "Right: vol-scaled (fair comparison)",
                 fontsize=14, fontweight="bold", color="white", y=1.02)

    # Left panel — raw momentum
    ax1.set_facecolor("#1a1d23")
    sns.boxplot(data=df, x="class", y="mom_21d", hue="class", order=order,
                palette=palette, fliersize=1.5, linewidth=0.8,
                boxprops=dict(alpha=0.8), legend=False, ax=ax1)
    ax1.axhline(0, color="#555", ls="--", lw=0.8)
    ax1.set_title("Raw 21d Momentum", fontsize=13, fontweight="bold",
                  color="#ff6b6b", pad=10)
    ax1.set_xlabel("Asset Class", fontsize=10, color="white")
    ax1.set_ylabel("mom_21d", fontsize=10, color="white")
    ax1.tick_params(colors="white")
    for spine in ax1.spines.values():
        spine.set_color("#333")

    # Right panel — vol-scaled momentum
    ax2.set_facecolor("#1a1d23")
    sns.boxplot(data=df, x="class", y="vsmom_21d", hue="class", order=order,
                palette=palette, fliersize=1.5, linewidth=0.8,
                boxprops=dict(alpha=0.8), legend=False, ax=ax2)
    ax2.axhline(0, color="#555", ls="--", lw=0.8)
    ax2.set_title("Vol-Scaled 21d Momentum  (mom ÷ vol)", fontsize=13,
                  fontweight="bold", color="#2dc653", pad=10)
    ax2.set_xlabel("Asset Class", fontsize=10, color="white")
    ax2.set_ylabel("vsmom_21d", fontsize=10, color="white")
    ax2.tick_params(colors="white")
    for spine in ax2.spines.values():
        spine.set_color("#333")

    fig.tight_layout()
    return fig


# ═══════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════

def main() -> None:
    FEATURES_DIR.mkdir(parents=True, exist_ok=True)

    # ── Load ─────────────────────────────────────────────────────────
    print("Loading processed data ...")
    prices = pd.read_parquet(PROCESSED_DIR / "prices_daily_clean.parquet")
    returns = pd.read_parquet(PROCESSED_DIR / "returns_daily.parquet")
    volume = pd.read_parquet(PROCESSED_DIR / "volume_daily_clean.parquet")

    print(f"  Prices shape : {prices.shape}")
    print(f"  Returns shape: {returns.shape}")
    print(f"  Volume shape : {volume.shape}")

    # ── Build ────────────────────────────────────────────────────────
    mom_windows = [5, 10, 21, 63]
    target_horizons = [1, 3]

    print(f"\nBuilding features for {len(prices.columns)} tickers, "
          f"{len(mom_windows)} momentum windows ...")

    features = build_all_features(
        prices=prices,
        returns=returns,
        volume=volume,
        benchmark=BENCHMARK,
        mom_windows=mom_windows,
        target_horizons=target_horizons,
    )

    # ── Save ─────────────────────────────────────────────────────────
    features.to_parquet(FEATURES_DIR / "features.parquet")

    # ── Sanity check ─────────────────────────────────────────────────
    print(f"\n--- Sanity check ---")
    print(f"Feature matrix shape: {features.shape}   "
          f"(rows = date x ticker, cols = features + targets)")
    print(f"Columns: {list(features.columns)}")
    print(f"Date range: {features.index.get_level_values('date').min().date()} "
          f"-> {features.index.get_level_values('date').max().date()}")

    n_tickers = features.index.get_level_values("ticker").nunique()
    print(f"Unique tickers: {n_tickers}")

    # NaN report
    nan_pct = features.isna().mean().sort_values(ascending=False)
    print(f"\nNaN % per column:")
    for col, pct in nan_pct.items():
        flag = "  <-- check" if pct > 0.15 else ""
        print(f"  {col:25s} {pct:6.2%}{flag}")

    # Inf check
    has_inf = np.isinf(features.select_dtypes(include="number").to_numpy()).any()
    print(f"\nContains inf: {has_inf}")
    if has_inf:
        print("  !! WARNING: infinite values found. Check vol-scaled features.")

    # ── Log ──────────────────────────────────────────────────────────
    with (FEATURES_DIR / "build_log.txt").open("w", encoding="utf-8") as f:
        f.write(
            f"Built at {datetime.now().isoformat(timespec='seconds')}\n"
            f"Shape   : {features.shape}\n"
            f"Columns : {list(features.columns)}\n"
            f"Tickers : {n_tickers}\n"
            f"Date    : {features.index.get_level_values('date').min().date()} "
            f"-> {features.index.get_level_values('date').max().date()}\n"
            f"Mom windows     : {mom_windows}\n"
            f"Target horizons : {target_horizons}\n"
        )

    print(f"\nSaved: {FEATURES_DIR / 'features.parquet'}")
    print(f"Saved: {FEATURES_DIR / 'build_log.txt'}")

    # ── Graphs (each in its own window) ──────────────────────────────
    print("\n--- Generating graphs (3 separate windows) ---")

    fig1 = plot_correlation_heatmap(features)
    _savefig(fig1, "04_g1_feature_correlation.png")

    fig2 = plot_momentum_timeseries(features)
    _savefig(fig2, "04_g2_momentum_21d_timeseries.png")

    fig3 = plot_vsmom_comparison(features)
    _savefig(fig3, "04_g3_vsmom_before_after.png")

    print("\nAll 3 graphs generated. Opening windows ...")
    plt.show()


if __name__ == "__main__":
    main()
