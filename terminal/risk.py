"""QM Terminal — risk engine (Phase 1).

Only uses what passed the project's tests:
  * risk  = EWMA volatility (lambda 0.94), the sizing input validated in Tasks 07b-11
  * ranges = today's risk x the asset's OWN historical fat tails, average drift removed
             (no direction is predicted)
  * split  = inverse-volatility (equal risk) weights, the robust result of Task 11
  * trend  = skip-5 trend z-scores from Task 07, reported as what HAS happened
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.tsmom import ewma_vol  # noqa: E402
from terminal.data import ASSETS, BUCKET_OF  # noqa: E402

MONTH = 21
BANDS = [(2.0, "VERY CALM"), (6.0, "CALM"), (12.0, "LIVELY"), (np.inf, "STORMY")]
LEVEL_COLOR = {"VERY CALM": "#2ECC71", "CALM": "#3A8DFF", "LIVELY": "#FF9F1C", "STORMY": "#FF3B30"}
# Only horizons that passed the risk report card are offered (1 month so far);
# 1 week / 3 months / 6 months / 1 year come back once they are tested.
ALL_PERIODS = {"1 week": 5, "1 month": 21, "3 months": 63, "6 months": 126, "1 year": 252}
PERIODS = {"1 month": 21}

# Which outcome numbers passed the risk report card (scripts/17_risk_report_card.py,
# 2026-10-12). The UI only shows verified ones (user rule: unverified = not on screen).
# Step 1b (scripts/18_risk_recalibration.py): with the universe-wide drift shift the
# per-asset bad case still passes and the typical range now passes; the good case and
# expected shortfall still fail, so they stay hidden. Typical-range width factor
# frozen from 2005-15 for the project universe: K_TYP = 1.00 (i.e. drift shift only).
VERIFIED = {"bad": True, "good": False, "typical": True, "shortfall": False}
K_TYP = 1.00
QUANTS = [0.05, 1 / 6, 0.5, 5 / 6, 0.95]        # bad 1-in-20, typical low, middle, typical high, good 1-in-20


def level(month_swing_pct: float) -> str:
    for edge, name in BANDS:
        if month_swing_pct < edge:
            return name
    return "STORMY"


def sigma_history(prices: pd.DataFrame) -> pd.DataFrame:
    """Daily EWMA vol series for every column (NaN until 63 days of history)."""
    return ewma_vol(prices.pct_change(fill_method=None))


def trend_scores(prices: pd.DataFrame, sigma: pd.DataFrame) -> pd.DataFrame:
    """Average of the skip-5 trend z-scores over 1, 3 and 6 months (Task 07 features)."""
    zs = [(prices.shift(5) / prices.shift(L) - 1) / (sigma * np.sqrt(L - 5)) for L in (21, 63, 126)]
    return sum(zs) / 3


def trend_arrow(z: float) -> str:
    if not np.isfinite(z):
        return "·"
    return "↑↑" if z > 1 else "↑" if z > 0.3 else "↓↓" if z < -1 else "↓" if z < -0.3 else "→"


def snapshot(prices: pd.DataFrame) -> pd.DataFrame:
    """One row per asset: price, today's move, risk, label, usual risk, trend."""
    sig = sigma_history(prices)
    tz = trend_scores(prices, sig)
    last, prev = prices.iloc[-1], prices.iloc[-2]
    rows = []
    for t in ASSETS:
        s_hist = sig[t].dropna()
        if s_hist.empty:
            continue
        s_now = s_hist.iloc[-1]
        swing = s_now * np.sqrt(MONTH) * 100
        p = prices[t].dropna()
        ret = lambda d: (p.iloc[-1] / p.iloc[-1 - d] - 1) * 100 if len(p) > d else np.nan  # noqa: E731
        rows.append({
            "ticker": t, "bucket": BUCKET_OF[t],
            "price": last[t], "day_pct": (last[t] / prev[t] - 1) * 100,
            "sigma": s_now, "swing": swing, "level": level(swing),
            "usual_swing": s_hist.median() * np.sqrt(MONTH) * 100,
            "risk_pct": (s_hist < s_now).mean() * 100,            # vs its own history
            "day_sigmas": ((last[t] / prev[t] - 1) / sig[t].iloc[-2]) if sig[t].iloc[-2] > 0 else np.nan,
            "trend_z": tz[t].iloc[-1], "trend": trend_arrow(tz[t].iloc[-1]),
            "ret_1m": ret(21), "ret_3m": ret(63), "ret_6m": ret(126),
        })
    return pd.DataFrame(rows).set_index("ticker")


def trend_words(row: pd.Series) -> str:
    """'up 12% over 3 months, up 30% over 6 months' — facts about the past."""
    parts = []
    for col, span in (("ret_1m", "1 month"), ("ret_3m", "3 months"), ("ret_6m", "6 months")):
        v = row[col]
        if np.isfinite(v):
            parts.append(f"{'up' if v >= 0 else 'down'} {abs(v):.0f}% over {span}")
    return ", ".join(parts)


# ---------------------------------------------------------------------- #
# Outcome ranges
# ---------------------------------------------------------------------- #

def z_quantiles(price: pd.Series, sigma: pd.Series, days: int, drift: float = 0.0,
                k_typ: float = 1.0) -> np.ndarray:
    """Quantiles of standardised d-day log returns, z = R / (sigma_t * sqrt(d)), demeaned.

    Using the asset's own history keeps its fat tails; centring on the median
    removes the asset's OWN past drift so a past winner is not shown as a future
    winner. (The median, not the mean: days when sigma was near zero — e.g. SHY
    before Feb 2020 — give extreme z values that would drag a mean far off.)
    `drift` then adds back the WHOLE universe's typical move (universe_drift) and
    `k_typ` scales the 2-in-3 band — the step-1b fix verified for per-asset numbers.
    """
    lp = np.log(price)
    z = ((lp.shift(-days) - lp) / (sigma * np.sqrt(days))).dropna()
    z = z[np.isfinite(z)]
    if len(z) < 250:                                   # too little history: normal quantiles
        q = np.array([-1.645, -0.967, 0.0, 0.967, 1.645])
    else:
        q = (z - z.median()).quantile(QUANTS).to_numpy().copy()
    q[1], q[3] = k_typ * q[1], k_typ * q[3]
    return q + drift


def universe_drift(prices: pd.DataFrame, sigma: pd.DataFrame, days: int = MONTH) -> float:
    """Median standardised `days`-day move pooled over ALL assets and all history
    (same for every asset, so no single past winner gets credit for its own run)."""
    lp = np.log(prices)
    z = ((lp.shift(-days) - lp) / (sigma * np.sqrt(days))).to_numpy().ravel()
    z = z[np.isfinite(z)]
    return float(np.median(z)) if len(z) >= 250 else 0.0


def outcome_range(amount: float, sigma_now: float, q: np.ndarray, days: int) -> np.ndarray:
    """$ outcomes at the QUANTS levels for `amount` held `days` trading days."""
    return amount * np.exp(q * sigma_now * np.sqrt(days))


def equal_risk_split(prices: pd.DataFrame, tickers: list[str], amount: float, days: int):
    """Inverse-vol weights (each asset carries the same risk) + the mix's outcome range.

    The mix is treated as one synthetic asset (fixed weights, daily rebalanced)
    over the dates where all chosen assets exist, so its range includes real
    correlations and fat tails.
    """
    sig = sigma_history(prices[tickers])
    s_now = sig.iloc[-1]
    w = (1 / s_now) / (1 / s_now).sum()
    rets = prices[tickers].pct_change(fill_method=None).dropna()
    mix = (1 + rets @ w.to_numpy()).cumprod()
    mix_sig = ewma_vol(mix.pct_change().to_frame("m"))["m"]
    q = z_quantiles(mix, mix_sig, days)
    rng = outcome_range(amount, mix_sig.iloc[-1], q, days)
    alloc = pd.DataFrame({"weight": w, "dollars": w * amount, "swing": s_now * np.sqrt(MONTH) * 100})
    return alloc, rng, mix_sig.iloc[-1] * np.sqrt(MONTH) * 100, len(rets)


def monthly_moves(price: pd.Series) -> pd.Series:
    """All past 21-day % moves (overlapping), for the histogram."""
    return ((price / price.shift(MONTH) - 1) * 100).dropna()
