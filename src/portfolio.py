"""Tasks 10–11 — target books and a realistic book simulator.

`simulate` lets positions DRIFT with prices between rebalance dates and charges
costs only on the trades actually made (|target - drifted weight|), instead of
the daily-rebalanced approximation used in Tasks 06–07c.

Methodology: Quant_Momentum/Methodology/10 - Costs and Combined Book.md
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.tsmom import FEATURES, build_panel, tsmom_weights, walk_forward

TREND = [f for f in FEATURES if f.startswith("mom_")]


def target_books(prices: pd.DataFrame, benchmark: str | None = "SPY", horizon: int = 21):
    """Daily TARGET weights for the trend model, the trend rule and the
    inverse-vol long book, on the walk-forward OOS dates.

    Returns (books: dict[name -> date x ticker weights], fwd_1d, oos panel).
    """
    panel = build_panel(prices, horizon=horizon, benchmark=benchmark)
    pred, _ = walk_forward(panel, horizon=horizon)
    oos = panel.loc[pred.index].assign(pred=pred)
    oos["rule"] = oos[TREND].mean(axis=1)

    assets = [c for c in prices.columns if c != benchmark]
    fwd_1d = prices[assets].shift(-1) / prices[assets] - 1
    vol = oos["vol"].unstack("ticker").reindex(columns=assets)
    dates = vol.index[fwd_1d.loc[vol.index].notna().any(axis=1)]   # drops the final day
    vol = vol.loc[dates]

    def wide(col):
        return oos[col].unstack("ticker").reindex(index=dates, columns=assets)

    books = {
        "trend_model": tsmom_weights(wide("pred"), vol),
        "trend_rule": tsmom_weights(wide("rule"), vol),
        "long": tsmom_weights(vol.notna().astype(float).where(vol.notna()), vol),
    }
    return books, fwd_1d.loc[dates], oos


def simulate(target: pd.DataFrame, fwd_1d: pd.DataFrame, every: int = 1,
             cost_bps: float = 10.0) -> pd.DataFrame:
    """Rebalance to `target` every `every` days; in between, weights drift.

    Day t: (rebalance) trade from drifted w to target, pay cost_bps * sum|trade|;
    earn w @ r_{t->t+1}; then w drifts to w * (1 + r) / (1 + portfolio return).
    The rest of the book is cash at 0% (SHY in the universe is the cash proxy).
    """
    T = target.to_numpy()
    R = fwd_1d.reindex_like(target).fillna(0.0).to_numpy()
    w = np.zeros(T.shape[1])
    net, traded = np.empty(len(T)), np.zeros(len(T))
    for t in range(len(T)):
        if t % every == 0:
            traded[t] = np.abs(T[t] - w).sum()
            w = T[t].copy()
        gross = w @ R[t]
        net[t] = gross - cost_bps * 1e-4 * traded[t]
        w = w * (1 + R[t]) / (1 + gross)
    return pd.DataFrame({"net": net, "turnover": traded}, index=target.index)
