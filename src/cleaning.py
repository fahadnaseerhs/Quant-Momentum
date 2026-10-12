"""Reusable cleaning functions: calendar alignment, gap handling, daily returns, audit.

Methodology: Quant_Momentum/Methodology/02 - Data Cleaning.md
Every function only ever looks backwards in time (no backfill, no lookahead).
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def trading_calendar(prices: pd.DataFrame, reference: str) -> pd.DatetimeIndex:
    """Trading days = the dates on which the reference asset (SPY) actually traded.

    Using real SPY dates gives the exact NYSE calendar, including exchange-only
    holidays like Good Friday that generic business-day calendars get wrong.
    """
    return prices.index[prices[reference].notna()]


def align_to_calendar(df: pd.DataFrame, calendar: pd.DatetimeIndex) -> pd.DataFrame:
    """Keep only rows on the trading calendar. Crypto weekend rows are dropped.

    Returns must be computed AFTER this step, so Monday's crypto return spans
    Friday -> Monday and still contains the weekend's price move.
    """
    return df.reindex(calendar)


def nan_runs(s: pd.Series) -> list[tuple[pd.Timestamp, pd.Timestamp, int]]:
    """Internal NaN runs (after the first valid value) as (start, end, length)."""
    first = s.first_valid_index()
    if first is None:
        return []
    is_nan = s.loc[first:].isna()
    run_id = (is_nan != is_nan.shift()).cumsum()
    return [
        (block.index[0], block.index[-1], len(block))
        for _, block in is_nan[is_nan].groupby(run_id[is_nan])
    ]


def fill_short_gaps(df: pd.DataFrame, max_fill: int = 2) -> tuple[pd.DataFrame, dict]:
    """Forward-fill internal gaps of length <= max_fill; leave longer gaps as NaN.

    Leading NaNs (asset not yet listed) are never filled.
    Returns the filled frame and a report {ticker: {"filled": n, "long_gaps": [...]}}.
    """
    out = df.copy()
    report = {}
    for col in df.columns:
        filled, long_gaps = 0, []
        for start, end, length in nan_runs(df[col]):
            if length <= max_fill:
                last_valid = df[col].loc[:start].dropna().iloc[-1]
                out.loc[start:end, col] = last_valid
                filled += length
            else:
                long_gaps.append((start.date(), end.date(), length))
        report[col] = {"filled": filled, "long_gaps": long_gaps}
    return out, report


def to_returns(prices: pd.DataFrame, method: str = "simple") -> pd.DataFrame:
    """Day-over-day returns. The first row (no prior price) is dropped."""
    ratio = prices / prices.shift(1)
    if method == "simple":
        returns = ratio - 1
    elif method == "log":
        returns = np.log(ratio)
    else:
        raise ValueError(f"method must be 'simple' or 'log', got {method!r}")
    return returns.iloc[1:]


def audit(raw: pd.DataFrame, clean: pd.DataFrame, fill_report: dict, returns: pd.DataFrame) -> dict:
    """Numbers for the cleaning log and sanity checks."""
    per_ticker = {}
    for col in clean.columns:
        first = clean[col].first_valid_index()
        r = returns[col]
        per_ticker[col] = {
            "first_valid": first.date() if first is not None else None,
            "leading_nan": int(clean[col].loc[:first].isna().sum()) if first is not None else len(clean),
            "filled": fill_report[col]["filled"],
            "long_gaps": fill_report[col]["long_gaps"],
            "remaining_nan": int(clean[col].isna().sum()),
            "daily_std": float(r.std()),
            "annual_vol": float(r.std() * np.sqrt(252)),
            "worst_day": float(r.min()),
            "best_day": float(r.max()),
        }
    return {
        "raw_rows": len(raw),
        "clean_rows": len(clean),
        "range": (clean.index[0].date(), clean.index[-1].date()),
        "has_inf": bool(np.isinf(returns.to_numpy(dtype=float)).any()),
        "below_minus_100": bool((returns <= -1).any().any()),
        "per_ticker": per_ticker,
    }
