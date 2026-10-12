"""Signal analysis functions for Task 05.

Methodology: Quant_Momentum/Methodology/05 - Signal Analysis.md

Everything here is leakage-safe by construction: features at time t are
tested against forward returns that start at t+1 (built in Task 04).
"""

from __future__ import annotations

import numpy as np
import pandas as pd


# ───────────────────────── Information Coefficient ─────────────────────────

def daily_ic(
    feature: pd.Series,
    target: pd.Series,
    method: str = "spearman",
    min_obs: int = 3,
) -> pd.Series:
    """Cross-sectional rank correlation per day.

    Both inputs are long-format Series indexed by (date, ticker).
    For each date, correlate feature values across tickers against the
    realised forward returns across the same tickers.

    Returns a Series of daily IC values indexed by date.
    Fully vectorised — no per-day Python apply.
    """
    df = pd.concat([feature, target], axis=1).dropna()
    df.columns = ["f", "y"]
    if df.empty:
        return pd.Series(dtype=float, name="ic")

    by_date = df.groupby(level="date")
    if method == "spearman":
        f = by_date["f"].rank()
        y = by_date["y"].rank()
    else:
        f = df["f"]
        y = df["y"]

    tmp = pd.DataFrame({"f": f, "y": y})
    bd = tmp.groupby(level="date")
    f_dev = tmp["f"] - bd["f"].transform("mean")
    y_dev = tmp["y"] - bd["y"].transform("mean")

    cov = (f_dev * y_dev).groupby(level="date").sum()
    f_var = (f_dev * f_dev).groupby(level="date").sum()
    y_var = (y_dev * y_dev).groupby(level="date").sum()

    denom = np.sqrt(f_var * y_var)
    ic = cov / denom.where(denom > 0)

    counts = by_date.size()
    ic[counts < min_obs] = np.nan
    ic.name = "ic"
    return ic


def newey_west_tstat(x: pd.Series, lags: int | None = None) -> dict:
    """Newey–West HAC-adjusted t-stat for the mean of a time series.

    Bartlett kernel; lag length default L = floor(4 * (T/100)**(2/9)).

    Returns {mean, se, tstat, lags, n}.
    """
    x = pd.Series(x).dropna()
    n = len(x)
    if n < 10:
        return {"mean": np.nan, "se": np.nan, "tstat": np.nan, "lags": 0, "n": n}

    if lags is None:
        lags = max(1, int(np.floor(4 * (n / 100) ** (2 / 9))))

    arr = x.to_numpy(dtype=float)
    mean = float(arr.mean())
    e = arr - mean
    gamma0 = float(np.mean(e * e))
    s = gamma0
    for L in range(1, lags + 1):
        w = 1.0 - L / (lags + 1)
        gL = float(np.mean(e[L:] * e[:-L]))
        s += 2.0 * w * gL

    var = max(s / n, 0.0)
    se = float(np.sqrt(var))
    tstat = mean / se if se > 0 else np.nan
    return {"mean": mean, "se": se, "tstat": tstat, "lags": lags, "n": n}


def ic_summary(
    feature: pd.Series,
    target: pd.Series,
    nw_lags: int | None = None,
) -> dict:
    """Compact summary for one (feature, target) pair across a universe."""
    ic = daily_ic(feature, target)
    nw = newey_west_tstat(ic, lags=nw_lags)
    ic_std = float(ic.std()) if nw["n"] > 0 else np.nan
    hit = float((ic.dropna() > 0).mean()) if nw["n"] > 0 else np.nan
    return {
        "mean_ic": nw["mean"],
        "ic_std": ic_std,
        "ir": (nw["mean"] / ic_std) if ic_std and not np.isnan(ic_std) and ic_std > 0 else np.nan,
        "nw_se": nw["se"],
        "nw_tstat": nw["tstat"],
        "nw_lags": nw["lags"],
        "hit_rate": hit,
        "n_days": nw["n"],
    }


# ───────────────────────── Bucket / tercile returns ─────────────────────────

def _bucket_daily(
    feature: pd.Series,
    target: pd.Series,
    n_buckets: int,
) -> pd.DataFrame:
    """Per-day table: columns = bucket id (1..n), values = mean target
    inside the bucket on that day.  Days with fewer than n_buckets
    observations are dropped.

    Vectorised — no per-day apply.
    """
    df = pd.concat([feature, target], axis=1).dropna()
    df.columns = ["f", "y"]
    if df.empty:
        return pd.DataFrame()

    by_date = df.groupby(level="date")
    df["rank"] = by_date["f"].rank(method="first")
    counts = by_date.size()
    df["n"] = df.index.get_level_values("date").map(counts)
    df = df[df["n"] >= n_buckets]
    if df.empty:
        return pd.DataFrame()

    # Even bucket assignment from rank: bucket = ceil(rank / n * n_buckets)
    df["bucket"] = np.ceil(df["rank"] / df["n"] * n_buckets).astype(int)
    df["bucket"] = df["bucket"].clip(1, n_buckets)

    daily = (df.reset_index()
               .groupby(["date", "bucket"])["y"]
               .mean()
               .unstack("bucket"))
    daily.columns = [int(c) for c in daily.columns]
    return daily


def bucket_returns(
    feature: pd.Series,
    target: pd.Series,
    n_buckets: int = 5,
) -> pd.DataFrame:
    """Average forward return per bucket across all days.

    Returns DataFrame: bucket, mean_fwd_ret, se_fwd_ret, n_days.
    Bucket 1 = lowest feature value, bucket n = highest.
    """
    daily = _bucket_daily(feature, target, n_buckets)
    if daily.empty:
        return pd.DataFrame(columns=["bucket", "mean_fwd_ret", "se_fwd_ret", "n_days"])
    means = daily.mean()
    ses = daily.std() / np.sqrt(daily.count())
    counts = daily.count()
    out = pd.DataFrame({
        "bucket": means.index,
        "mean_fwd_ret": means.values,
        "se_fwd_ret": ses.values,
        "n_days": counts.values,
    })
    return out


def long_short_spread(bucket_df: pd.DataFrame) -> float:
    """mean(top bucket) − mean(bottom bucket).  NaN if the table is empty."""
    if bucket_df.empty:
        return np.nan
    return float(bucket_df["mean_fwd_ret"].iloc[-1]
                 - bucket_df["mean_fwd_ret"].iloc[0])


# ───────────────────────── Rolling / cumulative IC ─────────────────────────

def rolling_ic(ic: pd.Series, window: int = 252, min_periods: int | None = None) -> pd.Series:
    """Rolling mean of the daily IC series."""
    if min_periods is None:
        min_periods = window // 2
    return ic.rolling(window, min_periods=min_periods).mean()


def cumulative_ic(ic: pd.Series) -> pd.Series:
    """Running sum of the daily IC series — slope = average signal strength."""
    return ic.cumsum()


# ───────────────────────── Leakage shift test ─────────────────────────

def shift_feature_in_ticker(feature: pd.Series, periods: int = -1) -> pd.Series:
    """Shift the feature along the date axis within each ticker group.

    periods = -1 moves tomorrow's value into today's slot.  If our
    original alignment was correct, the IC of the shifted feature
    against the same forward return should collapse toward zero.
    """
    return feature.groupby(level="ticker").shift(periods)
