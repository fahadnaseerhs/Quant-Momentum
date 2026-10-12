"""
Task 06 — Baseline model.

Rule-based (Model 0) strategies: rank the universe by a single signal each day,
hold equal-weighted top-N (optionally short bottom-N), rebalance daily.

Leakage: signal at day t decides positions held on day t+1; the realised return
earned is `fwd_ret_1d` at row t (= (P_{t+1}/P_t) - 1).  No parameters are fit.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


# ----------------------------------------------------------------------------- #
# Portfolio construction
# ----------------------------------------------------------------------------- #

def rank_portfolio(
    features: pd.DataFrame,
    signal_col: str,
    top_n: int = 5,
    long_short: bool = False,
) -> pd.DataFrame:
    """
    For each date, rank assets by `signal_col`. Equal-weight the top-N
    (and short-weight the bottom-N if long_short=True).

    Returns a (date x ticker) weight matrix. Weights sum to 1 for long-only,
    0 for long-short (gross exposure 2).
    """
    sig = features[signal_col].unstack("ticker")  # date x ticker
    n_assets = sig.shape[1]
    if top_n > n_assets // 2 and long_short:
        raise ValueError("top_n too large for long-short with this universe")

    # Rank per day; higher rank = stronger signal.
    ranks = sig.rank(axis=1, method="first", ascending=False)

    long_mask = ranks <= top_n
    weights = long_mask.astype(float).div(long_mask.sum(axis=1), axis=0)

    if long_short:
        short_mask = ranks > (n_assets - top_n)
        short_w = short_mask.astype(float).div(short_mask.sum(axis=1), axis=0)
        weights = weights - short_w

    # Days with no valid signal → NaN row → zero exposure
    weights = weights.where(sig.notna().any(axis=1).reindex(weights.index), 0.0)
    return weights


def portfolio_returns(
    weights: pd.DataFrame,
    fwd_returns: pd.DataFrame,
) -> pd.Series:
    """
    Weight today * forward_return_today  (= realised return earned by holding
    today's chosen portfolio over the next day).

    weights and fwd_returns: date x ticker. Rows aligned.
    """
    aligned_w, aligned_r = weights.align(fwd_returns, join="inner")
    return (aligned_w * aligned_r).sum(axis=1, min_count=1)


def turnover(weights: pd.DataFrame) -> pd.Series:
    """One-sided turnover per day: 0.5 * sum(|w_t - w_{t-1}|)."""
    return 0.5 * weights.diff().abs().sum(axis=1)


# ----------------------------------------------------------------------------- #
# Performance metrics
# ----------------------------------------------------------------------------- #

def equity_curve(ret: pd.Series) -> pd.Series:
    return (1.0 + ret.fillna(0.0)).cumprod()


def performance_metrics(ret: pd.Series, periods_per_year: int = 252) -> dict:
    """Standard summary of a daily return series."""
    r = ret.dropna()
    if r.empty:
        return {k: np.nan for k in
                ["cum_ret", "ann_ret", "ann_vol", "sharpe",
                 "max_dd", "win_rate", "n_days"]}
    eq = (1 + r).cumprod()
    cum_ret = eq.iloc[-1] - 1
    ann_ret = (1 + r.mean()) ** periods_per_year - 1
    ann_vol = r.std() * np.sqrt(periods_per_year)
    sharpe = ann_ret / ann_vol if ann_vol > 0 else np.nan
    dd = eq / eq.cummax() - 1
    max_dd = dd.min()
    win_rate = (r > 0).mean()
    return {
        "cum_ret": float(cum_ret),
        "ann_ret": float(ann_ret),
        "ann_vol": float(ann_vol),
        "sharpe": float(sharpe),
        "max_dd": float(max_dd),
        "win_rate": float(win_rate),
        "n_days": int(r.shape[0]),
    }


# ----------------------------------------------------------------------------- #
# Sanity benchmarks
# ----------------------------------------------------------------------------- #

def equal_weight_universe(fwd_returns: pd.DataFrame) -> pd.Series:
    """Hold every asset at 1/N every day."""
    n = fwd_returns.shape[1]
    w = pd.DataFrame(1.0 / n, index=fwd_returns.index, columns=fwd_returns.columns)
    return portfolio_returns(w, fwd_returns)


def random_portfolio(
    fwd_returns: pd.DataFrame,
    top_n: int = 5,
    seed: int = 42,
) -> pd.Series:
    """Each day, pick top_n assets at random. Equal-weighted. Reproducible."""
    rng = np.random.default_rng(seed)
    n = fwd_returns.shape[1]
    w = pd.DataFrame(0.0, index=fwd_returns.index, columns=fwd_returns.columns)
    for d in fwd_returns.index:
        pick = rng.choice(n, size=top_n, replace=False)
        w.iloc[w.index.get_loc(d), pick] = 1.0 / top_n
    return portfolio_returns(w, fwd_returns)
