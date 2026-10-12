"""Task 07 (revised) — Time-series momentum (TSMOM) prediction.

Each asset is predicted from its OWN past trend; assets are never ranked
against each other.  The universe mixes equities, crypto, bonds and
commodities, and a cross-sectional rank across those has no meaning (why the
cross-sectional linear model had OOS IC ~ 0).

Features (all known at the close of day t, unitless, vol-normalised):
    rev_5   = (P_t / P_{t-5} - 1)      / (sigma_t * sqrt(5))       short-term reversal
    mom_L   = (P_{t-5} / P_{t-L} - 1)  / (sigma_t * sqrt(L - 5))   trend, skipping the last 5 days
              for L in (21, 63, 126)
Label:
    y_h     = (P_{t+h} / P_t - 1)      / (sigma_t * sqrt(h))
sigma_t = EWMA (lambda = 0.94) daily vol of the asset's own returns through day t.

Dividing by sigma puts BTC and SHY on the same scale, so one pooled model can
be fit across all assets.  Features and the fitting label are clipped at a
FIXED bound (no statistics estimated from the data -> no look-ahead).

Methodology: Quant_Momentum/Methodology/07 - Time-Series Momentum.md
"""
from __future__ import annotations

import numpy as np
import pandas as pd

CLIP = 4.0          # fixed clip for z-scored features / label
SKIP = 5            # days skipped between the trend window and today
LOOKBACKS = (21, 63, 126)
FEATURES = [f"rev_{SKIP}"] + [f"mom_{L}" for L in LOOKBACKS]

ASSET_CLASS = {
    "BTC-USD": "crypto", "ETH-USD": "crypto", "SOL-USD": "crypto",
    "LINK-USD": "crypto", "AVAX-USD": "crypto",
    "AAPL": "equity", "MSFT": "equity", "NVDA": "equity", "GOOGL": "equity",
    "META": "equity", "MSTR": "equity", "B": "equity", "XOM": "equity", "CVX": "equity",
    "GLD": "commodity", "USO": "commodity", "DBC": "commodity",
    "TLT": "bond", "SHY": "bond",
    "VNQ": "real estate",
}


# ---------------------------------------------------------------------- #
# Panel construction
# ---------------------------------------------------------------------- #

def ewma_vol(returns: pd.DataFrame, lam: float = 0.94, min_periods: int = 63) -> pd.DataFrame:
    """Daily EWMA volatility through day t (uses r_t, which is known at close t)."""
    var = returns.pow(2).ewm(alpha=1 - lam, adjust=False, min_periods=min_periods).mean()
    return np.sqrt(var)


def build_panel(prices: pd.DataFrame, horizon: int, benchmark: str = "SPY") -> pd.DataFrame:
    """Long (date, ticker) panel with features, label and helper columns.

    Columns: FEATURES, y (vol-normalised h-day forward return, unclipped),
    fwd_raw (raw h-day forward return), vol (daily sigma_t).
    Rows with missing features are dropped; rows with a missing label (the last
    `horizon` days) are KEPT so they can still be predicted.
    """
    px = prices[[c for c in prices.columns if c != benchmark]]
    vol = ewma_vol(px.pct_change())

    wide = {f"rev_{SKIP}": (px / px.shift(SKIP) - 1) / (vol * np.sqrt(SKIP))}
    for L in LOOKBACKS:
        wide[f"mom_{L}"] = (px.shift(SKIP) / px.shift(L) - 1) / (vol * np.sqrt(L - SKIP))
    fwd = px.shift(-horizon) / px - 1
    wide["y"] = fwd / (vol * np.sqrt(horizon))
    wide["fwd_raw"] = fwd
    wide["vol"] = vol

    panel = pd.concat({k: v.stack() for k, v in wide.items()}, axis=1)
    panel.index.names = ["date", "ticker"]
    return panel.dropna(subset=FEATURES).sort_index()


# ---------------------------------------------------------------------- #
# Model: pooled ridge regression, no intercept
# ---------------------------------------------------------------------- #

def ridge_fit(X: np.ndarray, y: np.ndarray, alpha: float) -> np.ndarray:
    """Closed-form ridge, no intercept:  w = (X'X/m + alpha*I)^-1  X'y/m.

    No intercept on purpose: an intercept would learn the sample's average
    drift (the 2021-26 crypto/tech boom) and make the model long-biased —
    that's beta, not trend skill.
    """
    m, n = X.shape
    return np.linalg.solve(X.T @ X / m + alpha * np.eye(n), X.T @ y / m)


def walk_forward(
    panel: pd.DataFrame,
    *,
    horizon: int,
    alpha: float = 0.05,
    initial_train: int = 252,
    step: int = 21,
):
    """Expanding-window walk-forward with a purge/embargo of `horizon` days.

    A training row dated d has a label that ends at d + horizon, so only rows
    with d < test_start - horizon are used: every training label is fully
    realised before the first test date.

    Returns
    -------
    pred  : pd.Series of out-of-sample predictions (index like panel).
    folds : list of dicts — test window, n_train, coefficients, in-sample IC,
            out-of-sample IC of that block.
    """
    dates = panel.index.get_level_values("date")
    udates = dates.unique()
    pos = udates.get_indexer(dates)

    X = panel[FEATURES].to_numpy().clip(-CLIP, CLIP)
    y_fit = panel["y"].to_numpy().clip(-CLIP, CLIP)
    y_eval = panel["y"].to_numpy()
    has_y = ~np.isnan(y_fit)

    pred = np.full(len(panel), np.nan)
    folds = []
    for test_pos in range(initial_train + horizon, len(udates), step):
        tr = (pos < test_pos - horizon) & has_y
        te = (pos >= test_pos) & (pos < test_pos + step)
        w = ridge_fit(X[tr], y_fit[tr], alpha)
        pred[te] = X[te] @ w

        te_y = te & has_y
        folds.append({
            "test_start": udates[test_pos],
            "test_end": udates[min(test_pos + step, len(udates)) - 1],
            "n_train": int(tr.sum()),
            "coef": dict(zip(FEATURES, w)),
            "ic_in": _corr(X[tr] @ w, y_eval[tr]),
            "ic_oos": _corr(pred[te_y], y_eval[te_y]) if te_y.sum() > 2 else np.nan,
        })

    return pd.Series(pred, index=panel.index, name="pred").dropna(), folds


def _corr(a: np.ndarray, b: np.ndarray) -> float:
    if len(a) < 3 or np.std(a) == 0 or np.std(b) == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


# ---------------------------------------------------------------------- #
# Positions & costs
# ---------------------------------------------------------------------- #

def tsmom_weights(
    signal: pd.DataFrame,
    vol: pd.DataFrame,
    target_vol_ann: float = 0.20,
) -> pd.DataFrame:
    """Direction = sign(signal); size = inverse vol, capped at 1/N (no leverage).

    w_i = sign(s_i) * min(target_vol / sigma_i_ann, 1) / N_t
    High-vol assets (crypto) get small weights, low-vol ones (SHY) are capped.
    N_t = assets with both a signal and a vol on day t, so the book stays fully
    budgeted before late-listing assets (crypto, META) exist.
    """
    n = (signal.notna() & vol.notna()).sum(axis=1).replace(0, np.nan)
    scale = (target_vol_ann / (vol * np.sqrt(252))).clip(upper=1.0)
    return (np.sign(signal) * scale).div(n, axis=0).fillna(0.0)


def net_returns(weights: pd.DataFrame, fwd_1d: pd.DataFrame, cost_bps: float) -> pd.DataFrame:
    """Gross and net daily returns.  Cost = cost_bps * sum|w_t - w_{t-1}|."""
    w, r = weights.align(fwd_1d, join="inner")
    gross = (w * r.fillna(0.0)).sum(axis=1)     # unlisted assets carry zero weight
    traded = w.diff().abs().sum(axis=1)
    traded.iloc[0] = w.iloc[0].abs().sum()
    net = gross - cost_bps * 1e-4 * traded
    return pd.DataFrame({"gross": gross, "net": net, "turnover": traded})
