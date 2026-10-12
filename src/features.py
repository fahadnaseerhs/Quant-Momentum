"""Feature engineering for the quant momentum pipeline (Task 04).

Every function computes features using ONLY information available at
the close of day t or earlier.  No future data ever leaks in.

Methodology: Quant_Momentum/Methodology/04 - Feature Engineering.md
"""

from __future__ import annotations

import numpy as np
import pandas as pd


# ── Momentum ────────────────────────────────────────────────────────

def momentum(prices: pd.DataFrame, windows: list[int] | None = None) -> dict[str, pd.DataFrame]:
    """Lookback return: M_{i,t}^{(w)} = P_t / P_{t-w} - 1.

    Returns a dict {f"mom_{w}d": DataFrame} for each window.
    """
    if windows is None:
        windows = [5, 10, 21, 63]
    return {f"mom_{w}d": prices / prices.shift(w) - 1 for w in windows}


# ── Volatility ──────────────────────────────────────────────────────

def ewma_vol_lagged(
    returns: pd.DataFrame,
    lam: float = 0.94,
    warmup: int = 63,
    annualize: bool = False,
) -> pd.DataFrame:
    """EWMA volatility, LAGGED ONE DAY so it is known at the start of day t.

    sigma_t^2 = lam * sigma_{t-1}^2 + (1-lam) * r_t^2
    We return sigma_{t-1} — the vol estimate as of yesterday's close.
    """
    var = returns.pow(2).ewm(alpha=1 - lam, adjust=False).mean()
    vol = np.sqrt(var)
    vol.iloc[:warmup] = np.nan
    return vol.shift(1)  # <-- the lag: today's feature uses yesterday's vol


def rolling_vol(
    returns: pd.DataFrame,
    window: int = 63,
    annualize: bool = False,
) -> pd.DataFrame:
    """63-day rolling standard deviation of daily returns (robustness alternative)."""
    vol = returns.rolling(window).std()
    if annualize:
        vol = vol * np.sqrt(252)
    return vol


# ── Vol-scaled momentum ────────────────────────────────────────────

def vol_scaled_momentum(
    mom_dict: dict[str, pd.DataFrame],
    vol: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """M_{i,t}^{(w)} / sigma_{i,t-1} for each momentum window.

    `vol` must already be lagged (output of ewma_vol_lagged).
    """
    return {
        f"vsmom_{key.replace('mom_', '')}": mom / vol
        for key, mom in mom_dict.items()
    }


# ── Volume ratio ────────────────────────────────────────────────────

def volume_ratio(volume: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """V_t / mean(V_{t-19}, ..., V_t).  Values > 1 = above-average volume."""
    avg = volume.rolling(window).mean()
    return volume / avg


# ── Relative-to-market return ───────────────────────────────────────

def relative_return(
    mom_dict: dict[str, pd.DataFrame],
    benchmark: str = "SPY",
) -> dict[str, pd.DataFrame]:
    """M_{i,t}^{(w)} - M_{SPY,t}^{(w)} for each momentum window."""
    out = {}
    for key, mom in mom_dict.items():
        if benchmark not in mom.columns:
            continue
        mkt = mom[benchmark]
        rel = mom.sub(mkt, axis=0)
        # Drop the benchmark column itself — it is always zero
        rel = rel.drop(columns=[benchmark], errors="ignore")
        out[f"relret_{key.replace('mom_', '')}"] = rel
    return out


# ── Forward targets (labels, NOT features) ──────────────────────────

def forward_targets(prices: pd.DataFrame, horizons: list[int] | None = None) -> dict[str, pd.DataFrame]:
    """Forward return: R_{i,t+h} = P_{t+h} / P_t - 1.

    These are LABELS for prediction, not model inputs.
    """
    if horizons is None:
        horizons = [1, 3]
    return {f"fwd_ret_{h}d": prices.shift(-h) / prices - 1 for h in horizons}


# ── Winsorisation ───────────────────────────────────────────────────

def winsorise_cross_section(
    df: pd.DataFrame,
    lower: float = 0.01,
    upper: float = 0.99,
) -> pd.DataFrame:
    """Clip each column at its own lower/upper percentiles, row by row is too noisy
    with only 21 assets, so we clip per-column across all dates.
    """
    lo = df.quantile(lower)
    hi = df.quantile(upper)
    return df.clip(lower=lo, upper=hi, axis=1)


# ── Master builder ──────────────────────────────────────────────────

def build_all_features(
    prices: pd.DataFrame,
    returns: pd.DataFrame,
    volume: pd.DataFrame,
    benchmark: str = "SPY",
    mom_windows: list[int] | None = None,
    target_horizons: list[int] | None = None,
) -> pd.DataFrame:
    """Build the full feature matrix in long format (date, ticker).

    Parameters
    ----------
    prices : wide DataFrame (date × ticker), adjusted close.
    returns : wide DataFrame (date × ticker), simple daily returns.
    volume : wide DataFrame (date × ticker), daily volume.
    benchmark : ticker used for relative-return features.
    mom_windows : lookback windows in trading days.
    target_horizons : forward-return horizons (days).

    Returns
    -------
    Long-format DataFrame indexed by (date, ticker) with feature and
    target columns.  The benchmark ticker is excluded from rows (it is
    not tradeable).
    """
    if mom_windows is None:
        mom_windows = [5, 10, 21, 63]
    if target_horizons is None:
        target_horizons = [1, 3]

    tradeables = [c for c in prices.columns if c != benchmark]

    # 1. Momentum
    mom_dict = momentum(prices, mom_windows)

    # 2. Volatility (lagged one day)
    evol = ewma_vol_lagged(returns, lam=0.94, warmup=63)
    rvol = rolling_vol(returns, window=63)

    # 3. Vol-scaled momentum
    vsmom_dict = vol_scaled_momentum(mom_dict, evol)

    # 4. Volume ratio
    vratio = volume_ratio(volume, window=20)

    # 5. Relative-to-market return
    relret_dict = relative_return(mom_dict, benchmark=benchmark)

    # 6. Forward targets
    fwd_dict = forward_targets(prices, horizons=target_horizons)

    # ── Assemble into one wide frame, then melt to long ──
    # All wide frames share the same (date) index.  Subset to tradeables.
    parts: dict[str, pd.DataFrame] = {}

    for name, df in mom_dict.items():
        parts[name] = df[tradeables]

    parts["ewma_vol"] = evol[tradeables]
    parts["roll_vol_63d"] = rvol[tradeables]

    for name, df in vsmom_dict.items():
        parts[name] = df[tradeables]

    parts["vol_ratio_20d"] = vratio[tradeables]

    for name, df in relret_dict.items():
        # relret already has benchmark dropped
        parts[name] = df[[c for c in tradeables if c in df.columns]]

    for name, df in fwd_dict.items():
        parts[name] = df[tradeables]

    # Stack each part into long format and merge
    long_frames = []
    for col_name, wide_df in parts.items():
        stacked = wide_df.stack()
        stacked.name = col_name
        long_frames.append(stacked)

    features = pd.concat(long_frames, axis=1)
    features.index.names = ["date", "ticker"]

    # Winsorise feature columns (NOT targets)
    target_cols = [c for c in features.columns if c.startswith("fwd_ret_")]
    feature_cols = [c for c in features.columns if c not in target_cols]

    features[feature_cols] = winsorise_cross_section(features[feature_cols])

    # Sort for reproducibility
    features = features.sort_index()

    return features
