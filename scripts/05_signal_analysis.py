"""Task 05 — Signal Analysis: does any feature in Task 04 actually rank
tomorrow's winners against tomorrow's losers?

Run from the project root:

    python scripts/05_signal_analysis.py

Inputs:
    data/features/features.parquet
    data/processed/prices_daily_clean.parquet   (SPY for regime shading)

Outputs:
    reports/tables/05_ic_summary.csv
    reports/tables/05_bucket_returns.csv
    reports/tables/05_block_ic.csv
    reports/tables/05_rolling_ic.csv
    reports/tables/05_shift_test.csv
    reports/tables/05_run_log.txt
    reports/figures/05_g1..g7_*.png
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.signals import (  # noqa: E402
    bucket_returns,
    cumulative_ic,
    daily_ic,
    ic_summary,
    long_short_spread,
    rolling_ic,
    shift_feature_in_ticker,
)
from src.universe import BENCHMARK, UNIVERSE  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FEATURES_PATH = ROOT / "data" / "features" / "features.parquet"
PRICES_PATH = ROOT / "data" / "processed" / "prices_daily_clean.parquet"
TABLES_DIR = ROOT / "reports" / "tables"
FIGURES_DIR = ROOT / "reports" / "figures"

CLASS_COLORS = {
    "crypto":      "#f7931a",
    "tech":        "#00b4d8",
    "gold":        "#ffd700",
    "oil":         "#6b4226",
    "real_assets": "#8338ec",
    "bonds":       "#2dc653",
}
TICKER_CLASS = {t: cls for cls, tks in UNIVERSE.items() for t in tks}

DARK = "#0e1117"
PANEL = "#1a1d23"
GRID = "#2a2d33"

FEATURE_FAMILIES = {
    "mom":    ["mom_5d",    "mom_10d",    "mom_21d",    "mom_63d"],
    "vsmom":  ["vsmom_5d",  "vsmom_10d",  "vsmom_21d",  "vsmom_63d"],
    "relret": ["relret_5d", "relret_10d", "relret_21d", "relret_63d"],
}
FEATURES_ALL = (FEATURE_FAMILIES["mom"]
                + FEATURE_FAMILIES["vsmom"]
                + FEATURE_FAMILIES["relret"]
                + ["vol_ratio_20d"])
HORIZONS = ["fwd_ret_1d", "fwd_ret_3d"]

# Hero features for the "feature × time" visualisations
HERO_FEATURES = ["mom_21d", "vsmom_21d", "relret_21d"]
HERO_HORIZON = "fwd_ret_1d"


# ───────────────────────── helpers ─────────────────────────

def _style_dark(ax: plt.Axes) -> None:
    ax.set_facecolor(PANEL)
    ax.tick_params(colors="white", labelsize=8)
    for spine in ax.spines.values():
        spine.set_color("#333")
    ax.grid(True, color=GRID, lw=0.5, alpha=0.5)


def _savefig(fig: plt.Figure, name: str) -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    out = FIGURES_DIR / name
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    print(f"  Saved figure: {out}")


def _subset(features: pd.DataFrame, tickers: set[str] | None) -> pd.DataFrame:
    if tickers is None:
        return features
    mask = features.index.get_level_values("ticker").isin(tickers)
    return features[mask]


def _spy_regime(prices: pd.DataFrame, lookback: int = 126) -> pd.Series:
    """1 if SPY above its `lookback`-day moving average, else 0.
    Used only for optional regime shading in Figure 7."""
    if BENCHMARK not in prices.columns:
        return pd.Series(dtype=int)
    spy = prices[BENCHMARK].dropna()
    ma = spy.rolling(lookback).mean()
    return (spy > ma).astype(int)


# ═══════════════════════════════════════════════════════════════════════
#  TABLES
# ═══════════════════════════════════════════════════════════════════════

def build_ic_summary(features: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """One row per (universe, feature, horizon).  Caches daily IC series
    for the whole universe for later plotting."""
    universes: dict[str, set[str] | None] = {"whole": None}
    for cls, tks in UNIVERSE.items():
        universes[cls] = set(tks)

    rows: list[dict] = []
    ic_cache: dict[tuple[str, str, str], pd.Series] = {}

    for uname, tks in universes.items():
        sub = _subset(features, tks)
        n_tickers = sub.index.get_level_values("ticker").nunique()

        for feat in FEATURES_ALL:
            for horizon in HORIZONS:
                summary = ic_summary(sub[feat], sub[horizon])
                # Long-short spread is only meaningful when we can form
                # quintiles (needs ≥ 5 tickers).
                ls = np.nan
                if n_tickers >= 5:
                    bk = bucket_returns(sub[feat], sub[horizon], n_buckets=5)
                    ls = long_short_spread(bk)

                rows.append({
                    "universe": uname,
                    "n_tickers": n_tickers,
                    "feature": feat,
                    "horizon": horizon,
                    "ls_spread_q5_q1": ls,
                    **summary,
                })

                # Cache daily IC for all whole-universe pairs (plots)
                if uname == "whole":
                    ic_cache[(uname, feat, horizon)] = daily_ic(sub[feat], sub[horizon])

    df = pd.DataFrame(rows)
    return df, ic_cache


def build_bucket_table(features: pd.DataFrame) -> pd.DataFrame:
    """Quintile + tercile mean forward returns for every (feature × horizon).
    Whole-universe only (within-block buckets need too few assets)."""
    rows = []
    for feat in FEATURES_ALL:
        for horizon in HORIZONS:
            for n_buckets, tag in [(5, "quintile"), (3, "tercile")]:
                bk = bucket_returns(features[feat], features[horizon], n_buckets=n_buckets)
                if bk.empty:
                    continue
                for _, r in bk.iterrows():
                    rows.append({
                        "feature": feat,
                        "horizon": horizon,
                        "scheme": tag,
                        "bucket": int(r["bucket"]),
                        "mean_fwd_ret": r["mean_fwd_ret"],
                        "se_fwd_ret": r["se_fwd_ret"],
                        "n_days": int(r["n_days"]),
                    })
    return pd.DataFrame(rows)


def build_rolling_table(ic_cache: dict, window: int = 252) -> pd.DataFrame:
    """Long-format rolling IC table for the hero features."""
    frames = []
    for (uname, feat, horizon), ic in ic_cache.items():
        if feat not in HERO_FEATURES or horizon != HERO_HORIZON:
            continue
        rol = rolling_ic(ic, window=window)
        tmp = pd.DataFrame({
            "date": rol.index,
            "feature": feat,
            "horizon": horizon,
            "rolling_ic_252d": rol.values,
        })
        frames.append(tmp)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True).dropna()


def build_shift_test(features: pd.DataFrame) -> pd.DataFrame:
    """Diagnostic to prove the Task 04 alignment is not leaking future info.

    Three variants, same forward-return target:

        baseline    : feature_t     vs fwd_ret_t         (our actual setup)
        future_leak : feature_{t+1} vs fwd_ret_t         (adds future info)
        past_only   : feature_{t-5} vs fwd_ret_t         (older info only)

    Expected behaviour if the baseline is clean:
      - future_leak IC >> baseline IC   (mechanical overlap through P_{t+1})
      - past_only IC   ≈ or <  baseline (older info decays)
    """
    rows = []
    for feat in HERO_FEATURES:
        for horizon in HORIZONS:
            ic_base = daily_ic(features[feat], features[horizon])
            ic_leak = daily_ic(shift_feature_in_ticker(features[feat], -1),
                               features[horizon])
            ic_past = daily_ic(shift_feature_in_ticker(features[feat], +5),
                               features[horizon])
            rows.append({
                "feature": feat,
                "horizon": horizon,
                "mean_ic_baseline":   float(ic_base.mean()),
                "mean_ic_future_leak": float(ic_leak.mean()),
                "mean_ic_past_only":   float(ic_past.mean()),
            })
    return pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════════════════════
#  GRAPH 1 — Scatter mom_21d vs fwd_ret_1d
#  "Visually, can we see the signal?  No.  Noise dominates."
# ═══════════════════════════════════════════════════════════════════════
def plot_scatter(features: pd.DataFrame) -> plt.Figure:
    df = features[["mom_21d", "fwd_ret_1d"]].dropna().reset_index()
    df["class"] = df["ticker"].map(TICKER_CLASS)

    fig, ax = plt.subplots(figsize=(11, 7))
    fig.patch.set_facecolor(DARK)
    _style_dark(ax)

    for cls in CLASS_COLORS:
        d = df[df["class"] == cls]
        ax.scatter(d["mom_21d"], d["fwd_ret_1d"], s=4, alpha=0.35,
                   color=CLASS_COLORS[cls], label=cls)

    # OLS fit line across all points
    x = df["mom_21d"].values
    y = df["fwd_ret_1d"].values
    if len(x) > 2:
        b, a = np.polyfit(x, y, 1)
        xs = np.linspace(x.min(), x.max(), 100)
        ax.plot(xs, a + b * xs, color="white", lw=1.5,
                label=f"OLS fit  (β = {b:+.4f})")

    ax.axhline(0, color="#555", lw=0.6)
    ax.axvline(0, color="#555", lw=0.6)
    ax.set_xlabel("mom_21d (feature at close of day t)", color="white")
    ax.set_ylabel("fwd_ret_1d  (return from t to t+1)", color="white")
    ax.set_title(
        "G1 — Momentum vs next-day return\n"
        "28,780 points.  Any signal is drowned by day-to-day noise — "
        "that's why we rank, not regress.",
        color="white", fontsize=13, fontweight="bold", pad=12,
    )
    ax.legend(facecolor=PANEL, labelcolor="white", loc="upper left",
              fontsize=8, framealpha=0.7)
    fig.tight_layout()
    return fig


# ═══════════════════════════════════════════════════════════════════════
#  GRAPH 2 — Daily IC + 252d rolling, hero features
# ═══════════════════════════════════════════════════════════════════════
def plot_ic_timeseries(ic_cache: dict) -> plt.Figure:
    fig, axes = plt.subplots(len(HERO_FEATURES), 1, figsize=(14, 9), sharex=True)
    fig.patch.set_facecolor(DARK)
    fig.suptitle("G2 — Daily IC with 252-day rolling mean (whole universe, 1-day horizon)",
                 color="white", fontsize=14, fontweight="bold", y=1.00)

    colors = {"mom_21d": "#f7931a", "vsmom_21d": "#2dc653", "relret_21d": "#00b4d8"}

    for ax, feat in zip(axes, HERO_FEATURES):
        _style_dark(ax)
        ic = ic_cache[("whole", feat, HERO_HORIZON)].dropna()
        rol = rolling_ic(ic, window=252)
        ax.plot(ic.index, ic.values, lw=0.4, alpha=0.35,
                color=colors.get(feat, "white"), label="daily IC")
        ax.plot(rol.index, rol.values, lw=1.8,
                color=colors.get(feat, "white"), label="252-day rolling")
        ax.axhline(0, color="#aaa", ls="--", lw=0.7)
        ax.axhline(float(ic.mean()), color="white", ls=":", lw=0.8,
                   label=f"mean = {ic.mean():+.4f}")
        ax.set_ylabel(feat, color="white")
        ax.legend(loc="upper right", fontsize=8, facecolor=PANEL,
                  labelcolor="white", framealpha=0.7)

    axes[-1].set_xlabel("Date", color="white")
    fig.tight_layout()
    return fig


# ═══════════════════════════════════════════════════════════════════════
#  GRAPH 3 — Cumulative IC
#  Steady slope = consistent signal.  Flat stretches = regimes of nothing.
# ═══════════════════════════════════════════════════════════════════════
def plot_cumulative_ic(ic_cache: dict) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(12, 6.5))
    fig.patch.set_facecolor(DARK)
    _style_dark(ax)
    colors = {"mom_21d": "#f7931a", "vsmom_21d": "#2dc653", "relret_21d": "#00b4d8"}

    for feat in HERO_FEATURES:
        ic = ic_cache[("whole", feat, HERO_HORIZON)].dropna()
        ax.plot(ic.index, cumulative_ic(ic).values, lw=1.6,
                color=colors.get(feat, "white"),
                label=f"{feat}  (mean IC = {ic.mean():+.4f})")

    ax.axhline(0, color="#aaa", ls="--", lw=0.7)
    ax.set_xlabel("Date", color="white")
    ax.set_ylabel("Cumulative daily IC", color="white")
    ax.set_title("G3 — Cumulative information coefficient\n"
                 "Upward slope = the signal keeps paying.  Flat = it stopped working.",
                 color="white", fontsize=13, fontweight="bold", pad=12)
    ax.legend(loc="upper left", facecolor=PANEL, labelcolor="white",
              fontsize=9, framealpha=0.7)
    fig.tight_layout()
    return fig


# ═══════════════════════════════════════════════════════════════════════
#  GRAPH 4 — Quintile bar chart per hero feature × horizon
# ═══════════════════════════════════════════════════════════════════════
def plot_bucket_bars(features: pd.DataFrame) -> plt.Figure:
    fig, axes = plt.subplots(len(HERO_FEATURES), len(HORIZONS),
                             figsize=(13, 10), sharey="row")
    fig.patch.set_facecolor(DARK)
    fig.suptitle("G4 — Mean forward return by momentum quintile  (whole universe)\n"
                 "Monotonic Q1→Q5 staircase = clean signal.  Scramble = noise.",
                 color="white", fontsize=13, fontweight="bold", y=1.00)

    colors = plt.cm.RdYlGn(np.linspace(0.1, 0.9, 5))

    for i, feat in enumerate(HERO_FEATURES):
        for j, horizon in enumerate(HORIZONS):
            ax = axes[i, j]
            _style_dark(ax)
            bk = bucket_returns(features[feat], features[horizon], n_buckets=5)
            if bk.empty:
                ax.set_axis_off(); continue
            x = bk["bucket"].astype(int).values
            y = bk["mean_fwd_ret"].values * 100
            se = bk["se_fwd_ret"].values * 100
            ax.bar(x, y, yerr=se, capsize=3, color=colors,
                   edgecolor="white", lw=0.6)
            ax.axhline(0, color="#aaa", ls="--", lw=0.7)
            ls = (y[-1] - y[0])
            ax.set_title(f"{feat} → {horizon}   "
                         f"long–short = {ls:+.3f}%",
                         color="white", fontsize=10, fontweight="bold")
            ax.set_xlabel("quintile (1 = low, 5 = high)", color="white", fontsize=9)
            if j == 0:
                ax.set_ylabel("mean forward return (%)", color="white", fontsize=9)

    fig.tight_layout()
    return fig


# ═══════════════════════════════════════════════════════════════════════
#  GRAPH 5 — Mean IC heatmap  (features × horizons)
# ═══════════════════════════════════════════════════════════════════════
def plot_ic_heatmap(ic_df: pd.DataFrame) -> plt.Figure:
    sub = ic_df[ic_df["universe"] == "whole"].copy()
    pivot = sub.pivot(index="feature", columns="horizon", values="mean_ic")
    # Order rows: mom → vsmom → relret → vol_ratio
    order = (FEATURE_FAMILIES["mom"] + FEATURE_FAMILIES["vsmom"]
             + FEATURE_FAMILIES["relret"] + ["vol_ratio_20d"])
    pivot = pivot.reindex(order)

    # t-stat annotations overlaid
    tstats = sub.pivot(index="feature", columns="horizon", values="nw_tstat").reindex(order)

    annot = pivot.round(4).astype(str) + "\n(t=" + tstats.round(2).astype(str) + ")"

    fig, ax = plt.subplots(figsize=(7, 10))
    fig.patch.set_facecolor(DARK)
    ax.set_facecolor(PANEL)
    vmax = max(abs(pivot.min().min()), abs(pivot.max().max()))
    sns.heatmap(pivot, cmap="RdYlGn", center=0, vmin=-vmax, vmax=vmax,
                annot=annot, fmt="", linewidths=0.5,
                annot_kws={"size": 8, "color": "black"},
                cbar_kws={"shrink": 0.8, "label": "Mean IC"}, ax=ax)
    ax.set_title("G5 — Mean IC heatmap  (whole universe)\n"
                 "cell = mean IC (Newey–West t-stat below)",
                 color="white", fontsize=12, fontweight="bold", pad=12)
    ax.tick_params(colors="white", labelsize=9)
    cbar = ax.collections[0].colorbar
    cbar.ax.yaxis.label.set_color("white")
    cbar.ax.tick_params(colors="white")
    fig.tight_layout()
    return fig


# ═══════════════════════════════════════════════════════════════════════
#  GRAPH 6 — IC within each asset-class block vs whole universe
# ═══════════════════════════════════════════════════════════════════════
def plot_block_ic(ic_df: pd.DataFrame) -> plt.Figure:
    sub = ic_df[(ic_df["feature"].isin(HERO_FEATURES))
                & (ic_df["horizon"] == HERO_HORIZON)].copy()
    pivot = sub.pivot(index="universe", columns="feature", values="mean_ic")
    # Row order: whole first, then blocks
    row_order = ["whole"] + list(UNIVERSE.keys())
    pivot = pivot.reindex(row_order)

    fig, ax = plt.subplots(figsize=(9, 6))
    fig.patch.set_facecolor(DARK)
    _style_dark(ax)

    x = np.arange(len(pivot.index))
    width = 0.25
    colors = {"mom_21d": "#f7931a", "vsmom_21d": "#2dc653", "relret_21d": "#00b4d8"}
    for i, feat in enumerate(HERO_FEATURES):
        if feat not in pivot.columns:
            continue
        vals = pivot[feat].values
        ax.bar(x + (i - 1) * width, vals, width,
               color=colors.get(feat, "white"), label=feat,
               edgecolor="white", lw=0.5)

    ax.axhline(0, color="#aaa", ls="--", lw=0.7)
    ax.set_xticks(x)
    ax.set_xticklabels(pivot.index, color="white", rotation=20)
    ax.set_ylabel("mean IC  (1-day horizon)", color="white")
    ax.set_title("G6 — IC per asset-class block vs the whole universe\n"
                 "Within-block IC answers: does the feature pick winners "
                 "even among similar assets?",
                 color="white", fontsize=12, fontweight="bold", pad=12)
    ax.legend(facecolor=PANEL, labelcolor="white", fontsize=9, framealpha=0.7)
    fig.tight_layout()
    return fig


# ═══════════════════════════════════════════════════════════════════════
#  GRAPH 7 — Rolling IC with SPY regime shading
# ═══════════════════════════════════════════════════════════════════════
def plot_rolling_ic_regime(ic_cache: dict, prices: pd.DataFrame) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(13, 6.5))
    fig.patch.set_facecolor(DARK)
    _style_dark(ax)

    regime = _spy_regime(prices, lookback=126)
    if not regime.empty:
        # Shade bear-market days (SPY below its 126d MA)
        bear = regime[regime == 0]
        if len(bear) > 0:
            # Group consecutive bear days into bands
            dates = bear.index.to_numpy()
            # Find run starts/ends
            is_consecutive = np.r_[True, (dates[1:] - dates[:-1]).astype("timedelta64[D]").astype(int) <= 5]
            starts = dates[~is_consecutive]
            # Simpler: just shade each day
            for d in dates:
                ax.axvspan(d, d + np.timedelta64(1, "D"), color="#555", alpha=0.08, lw=0)

    colors = {"mom_21d": "#f7931a", "vsmom_21d": "#2dc653", "relret_21d": "#00b4d8"}
    for feat in HERO_FEATURES:
        ic = ic_cache[("whole", feat, HERO_HORIZON)].dropna()
        rol = rolling_ic(ic, window=252)
        ax.plot(rol.index, rol.values, lw=1.8,
                color=colors.get(feat, "white"),
                label=feat)

    ax.axhline(0, color="#aaa", ls="--", lw=0.7)
    ax.set_xlabel("Date", color="white")
    ax.set_ylabel("252-day rolling mean IC", color="white")
    ax.set_title("G7 — Rolling IC with SPY-bear shading\n"
                 "Grey = days SPY is below its 126-day moving average.  "
                 "Does the signal survive stress?",
                 color="white", fontsize=12, fontweight="bold", pad=12)
    ax.legend(facecolor=PANEL, labelcolor="white", fontsize=10, framealpha=0.7)
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    fig.tight_layout()
    return fig


# ═══════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════
def main() -> None:
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Loading features from {FEATURES_PATH} ...")
    features = pd.read_parquet(FEATURES_PATH)
    prices = pd.read_parquet(PRICES_PATH)
    print(f"  features shape = {features.shape}")
    date_min = features.index.get_level_values("date").min().date()
    date_max = features.index.get_level_values("date").max().date()
    n_tickers = features.index.get_level_values("ticker").nunique()
    print(f"  date range     = {date_min} -> {date_max}")
    print(f"  tickers        = {n_tickers}")

    # ── Tables ────────────────────────────────────────────────────
    print("\n--- Building IC summary (universe × feature × horizon) ---")
    ic_df, ic_cache = build_ic_summary(features)
    ic_df.to_csv(TABLES_DIR / "05_ic_summary.csv", index=False)
    print(f"  Saved: {TABLES_DIR / '05_ic_summary.csv'}  ({len(ic_df)} rows)")

    # Block-only slice for convenience
    block_df = ic_df[(ic_df["universe"] != "whole")].copy()
    block_df.to_csv(TABLES_DIR / "05_block_ic.csv", index=False)
    print(f"  Saved: {TABLES_DIR / '05_block_ic.csv'}  ({len(block_df)} rows)")

    print("\n--- Building quintile / tercile bucket table ---")
    buckets_df = build_bucket_table(features)
    buckets_df.to_csv(TABLES_DIR / "05_bucket_returns.csv", index=False)
    print(f"  Saved: {TABLES_DIR / '05_bucket_returns.csv'}  ({len(buckets_df)} rows)")

    print("\n--- Building rolling IC table (hero features, 252d) ---")
    rolling_df = build_rolling_table(ic_cache, window=252)
    rolling_df.to_csv(TABLES_DIR / "05_rolling_ic.csv", index=False)
    print(f"  Saved: {TABLES_DIR / '05_rolling_ic.csv'}  ({len(rolling_df)} rows)")

    print("\n--- Running leakage shift test ---")
    shift_df = build_shift_test(features)
    shift_df.to_csv(TABLES_DIR / "05_shift_test.csv", index=False)
    print(f"  Saved: {TABLES_DIR / '05_shift_test.csv'}")
    print(shift_df.to_string(index=False))

    # ── Headline results to console ───────────────────────────────
    print("\n--- Headline whole-universe results (sorted by |t-stat|) ---")
    whole = (ic_df[ic_df["universe"] == "whole"]
             .assign(abs_t=lambda d: d["nw_tstat"].abs())
             .sort_values("abs_t", ascending=False)
             .drop(columns="abs_t"))
    cols = ["feature", "horizon", "mean_ic", "nw_tstat", "hit_rate",
            "ls_spread_q5_q1", "n_days"]
    print(whole[cols].head(12).to_string(index=False))

    # ── Run log ───────────────────────────────────────────────────
    log_path = TABLES_DIR / "05_run_log.txt"
    with log_path.open("w", encoding="utf-8") as f:
        f.write(f"Task 05 — Signal Analysis\n")
        f.write(f"Run at   : {datetime.now().isoformat(timespec='seconds')}\n")
        f.write(f"Features : {FEATURES_PATH}\n")
        f.write(f"Shape    : {features.shape}\n")
        f.write(f"Date     : {date_min} -> {date_max}\n")
        f.write(f"Tickers  : {n_tickers}\n\n")
        f.write("Top whole-universe signals by |NW t-stat|:\n")
        f.write(whole[cols].head(15).to_string(index=False))
        f.write("\n\nLeakage shift test (feature shifted -1 day):\n")
        f.write(shift_df.to_string(index=False))
    print(f"\nSaved log: {log_path}")

    # ── Figures ───────────────────────────────────────────────────
    print("\n--- Generating 7 figures ---")
    _savefig(plot_scatter(features),         "05_g1_scatter_mom21d_vs_fwd1d.png")
    _savefig(plot_ic_timeseries(ic_cache),   "05_g2_ic_timeseries.png")
    _savefig(plot_cumulative_ic(ic_cache),   "05_g3_cumulative_ic.png")
    _savefig(plot_bucket_bars(features),     "05_g4_bucket_bar.png")
    _savefig(plot_ic_heatmap(ic_df),         "05_g5_ic_heatmap.png")
    _savefig(plot_block_ic(ic_df),           "05_g6_block_ic.png")
    _savefig(plot_rolling_ic_regime(ic_cache, prices),
             "05_g7_rolling_ic_regime.png")

    print("\nAll 7 graphs generated. Opening windows ...")
    plt.show()


if __name__ == "__main__":
    main()
