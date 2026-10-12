"""Reusable functions for exploring returns (Task 03).

Methodology: Quant_Momentum/Methodology/03 - Exploring Returns.md
Concepts:    Quant_Momentum/Technical Learning/
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.stattools import acf

TRADING_DAYS = 252


def wealth_index(simple_returns: pd.DataFrame) -> pd.DataFrame:
    """Growth of $1: cumulative product of (1 + R)."""
    return (1 + simple_returns).cumprod()


def rolling_vol(returns: pd.DataFrame, window: int = 63, annualize: bool = True) -> pd.DataFrame:
    """Standard deviation over the last `window` days (uses only past and current data)."""
    vol = returns.rolling(window).std()
    return vol * np.sqrt(TRADING_DAYS) if annualize else vol


def ewma_vol(returns: pd.DataFrame, lam: float = 0.94, annualize: bool = True, warmup: int = 63) -> pd.DataFrame:
    """RiskMetrics EWMA volatility: var_t = lam * var_{t-1} + (1 - lam) * r_t^2.

    The first `warmup` days are set to NaN because the recursion needs time
    to forget its arbitrary starting value.
    """
    var = returns.pow(2).ewm(alpha=1 - lam, adjust=False).mean()
    vol = np.sqrt(var)
    vol.iloc[:warmup] = np.nan
    return vol * np.sqrt(TRADING_DAYS) if annualize else vol


def vol_scaled_returns(returns: pd.DataFrame, lam: float = 0.94) -> pd.DataFrame:
    """r_t / sigma_{t-1}: each return in units of the volatility known the day before."""
    prior_vol = ewma_vol(returns, lam=lam, annualize=False).shift(1)
    return (returns / prior_vol).dropna(how="all")


def moments_table(returns: pd.DataFrame) -> pd.DataFrame:
    """Annualised mean/vol, skewness, excess kurtosis, Jarque-Bera, extreme days in sigma units."""
    rows = {}
    for col in returns.columns:
        r = returns[col].dropna()
        z = (r - r.mean()) / r.std()
        jb = stats.jarque_bera(r)
        rows[col] = {
            "ann_mean": r.mean() * TRADING_DAYS,
            "ann_vol": r.std() * np.sqrt(TRADING_DAYS),
            "skew": stats.skew(r),
            "excess_kurt": stats.kurtosis(r, fisher=True),
            "jb_stat": jb.statistic,
            "jb_pvalue": jb.pvalue,
            "worst_z": z.min(),
            "best_z": z.max(),
        }
    return pd.DataFrame(rows).T


def acf_table(returns: pd.DataFrame, nlags: int = 10) -> pd.DataFrame:
    """Autocorrelation at lags 1..nlags for each column (rows = assets, cols = lags)."""
    out = {col: acf(returns[col].dropna(), nlags=nlags, fft=True)[1:] for col in returns.columns}
    return pd.DataFrame(out, index=range(1, nlags + 1)).T


def acf_band(n_obs: int) -> float:
    """95% band for an ACF bar under the white-noise null (Bartlett): 1.96 / sqrt(T)."""
    return 1.96 / np.sqrt(n_obs)


def robust_acf_se(returns: pd.DataFrame, nlags: int = 10) -> pd.DataFrame:
    """Heteroskedasticity-robust standard error of each ACF bar.

    se_k = sqrt(sum x_t^2 x_{t-k}^2) / sum x_t^2, with x = demeaned returns.
    Under volatility clustering this is wider than Bartlett's 1/sqrt(T).
    """
    out = {}
    for col in returns.columns:
        x = returns[col].dropna().to_numpy()
        x = x - x.mean()
        x2 = x**2
        denom = x2.sum()
        out[col] = [np.sqrt((x2[k:] * x2[:-k]).sum()) / denom for k in range(1, nlags + 1)]
    return pd.DataFrame(out, index=range(1, nlags + 1)).T


def ljung_box_table(returns: pd.DataFrame, lags: tuple[int, ...] = (5, 10)) -> pd.DataFrame:
    """Ljung-Box Q statistic and p-value per asset for each lag count m."""
    rows = {}
    for col in returns.columns:
        lb = acorr_ljungbox(returns[col].dropna(), lags=list(lags))
        row = {}
        for m in lags:
            row[f"Q({m})"] = lb.loc[m, "lb_stat"]
            row[f"p({m})"] = lb.loc[m, "lb_pvalue"]
        rows[col] = row
    return pd.DataFrame(rows).T


def variance_ratio(acf_row: pd.Series, q: int) -> float:
    """VR(q) = 1 + 2 * sum_{k=1}^{q-1} (1 - k/q) * rho_k."""
    return 1 + 2 * sum((1 - k / q) * acf_row[k] for k in range(1, q))


def non_overlapping_sum(log_returns: pd.DataFrame, h: int = 3) -> pd.DataFrame:
    """Sum log returns over consecutive, non-overlapping blocks of h days; drop an incomplete last block."""
    n_full = (len(log_returns) // h) * h
    trimmed = log_returns.iloc[:n_full]
    block = np.arange(n_full) // h
    summed = trimmed.groupby(block).sum(min_count=h)
    summed.index = trimmed.index[h - 1 :: h]
    return summed


def average_pairwise_corr(corr: pd.DataFrame) -> float:
    """Mean of the off-diagonal entries of a correlation matrix."""
    values = corr.to_numpy()
    mask = ~np.eye(len(values), dtype=bool)
    return float(values[mask].mean())


def effective_bets(n: int, avg_corr: float) -> float:
    """N_eff = N / (1 + (N - 1) * avg_corr)."""
    return n / (1 + (n - 1) * avg_corr)


def rolling_average_corr(returns: pd.DataFrame, window: int = 63) -> pd.Series:
    """Average pairwise correlation over a rolling window."""
    values = returns.to_numpy()
    out = np.full(len(returns), np.nan)
    for end in range(window, len(returns) + 1):
        c = np.corrcoef(values[end - window : end].T)
        out[end - 1] = c[~np.eye(len(c), dtype=bool)].mean()
    return pd.Series(out, index=returns.index, name=f"avg_corr_{window}d")
