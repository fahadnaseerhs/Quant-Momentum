"""Task 07b — Volatility forecasting (predict risk instead of returns).

Returns are close to unpredictable (Task 07), but volatility clusters
(Task 03), so tomorrow's risk IS forecastable.  A better risk forecast gives
better position sizes for the inverse-vol long book.

Target (label), per asset:
    lrv_fut = log sqrt( mean( r_{t+1}^2 ... r_{t+h}^2 ) )      realised vol over the next h days
Features (known at close t) — the HAR model (Corsi, 2009) with daily data:
    lrv_k   = log sqrt( mean( r_{t-k+1}^2 ... r_t^2 ) )        for k = 5, 22, 63
    neg_ret_5 = min(P_t / P_{t-5} - 1, 0) / (rv_22 * sqrt 5)   leverage effect (HAR-L only)
Model: pooled OLS with intercept on the logs.  Forecast in vol units:
    sigma_hat = exp(log-forecast + s^2 / 2)      (s^2 = training residual variance;
                                                  log-normal mean correction)
Benchmark: EWMA (lambda = 0.94), the sizing input used so far.

Methodology: Quant_Momentum/Methodology/07b - Volatility Forecasting.md
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.tsmom import ewma_vol

HAR = ["lrv_5", "lrv_22", "lrv_63"]
HAR_L = HAR + ["neg_ret_5"]


def realized_vol(returns: pd.DataFrame, window: int) -> pd.DataFrame:
    """Trailing realised vol through day t: sqrt of the mean squared return."""
    return np.sqrt(returns.pow(2).rolling(window).mean())


def build_vol_panel(prices: pd.DataFrame, horizon: int = 21, benchmark: str = "SPY") -> pd.DataFrame:
    """Long (date, ticker) panel: HAR features, leverage term, EWMA vol, label.

    Rows with a missing label (the last `horizon` days) are kept for prediction.
    """
    px = prices[[c for c in prices.columns if c != benchmark]]
    r = px.pct_change()

    wide = {f"lrv_{k}": np.log(realized_vol(r, k)) for k in (5, 22, 63)}
    wide["neg_ret_5"] = np.minimum(px / px.shift(5) - 1, 0) / (realized_vol(r, 22) * np.sqrt(5))
    wide["ewma"] = ewma_vol(r)
    # rolling(h) at t covers t-h+1..t; shifting by -h moves it to t+1..t+h
    wide["lrv_fut"] = np.log(np.sqrt(r.pow(2).rolling(horizon).mean().shift(-horizon)))

    panel = pd.concat({k: v.stack() for k, v in wide.items()}, axis=1)
    panel.index.names = ["date", "ticker"]
    panel = panel.replace([np.inf, -np.inf], np.nan)
    return panel.dropna(subset=HAR_L + ["ewma"]).sort_index()


def walk_forward_vol(
    panel: pd.DataFrame,
    features: list[str],
    *,
    horizon: int,
    initial_train: int = 252,
    step: int = 21,
):
    """Expanding-window walk-forward, purge/embargo = horizon (as in src/tsmom.py).

    Returns
    -------
    sigma : pd.Series — out-of-sample daily-vol forecasts (index like panel).
    folds : list of dicts — test start, coefficients, residual variance.
    """
    dates = panel.index.get_level_values("date")
    udates = dates.unique()
    pos = udates.get_indexer(dates)

    X = np.column_stack([np.ones(len(panel)), panel[features].to_numpy()])
    y = panel["lrv_fut"].to_numpy()
    has_y = ~np.isnan(y)

    sigma = np.full(len(panel), np.nan)
    folds = []
    for test_pos in range(initial_train + horizon, len(udates), step):
        tr = (pos < test_pos - horizon) & has_y
        te = (pos >= test_pos) & (pos < test_pos + step)
        b, *_ = np.linalg.lstsq(X[tr], y[tr], rcond=None)
        s2 = float(np.var(y[tr] - X[tr] @ b))
        sigma[te] = np.exp(X[te] @ b + s2 / 2)
        folds.append({"test_start": udates[test_pos], "s2": s2,
                      **dict(zip(["intercept"] + features, b))})

    return pd.Series(sigma, index=panel.index, name="sigma").dropna(), folds


def qlike(realized_var: np.ndarray, forecast_var: np.ndarray) -> np.ndarray:
    """QLIKE loss (Patton 2011): robust to noise in the realised proxy; lower = better."""
    ratio = realized_var / forecast_var
    return ratio - np.log(ratio) - 1
