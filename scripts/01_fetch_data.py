"""Fetch daily adjusted-close prices for the locked universe and save as parquet.

Run from the project root:

    python scripts/01_fetch_data.py

Output:
    data/raw/prices_daily.parquet    (wide: rows=date, cols=ticker)
    data/raw/volume_daily.parquet    (wide: rows=date, cols=ticker)
    data/raw/fetch_log.txt           (one-line summary of what was pulled)
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import yfinance as yf

# Allow `python scripts/01_fetch_data.py` from project root without install.
sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.universe import ALL_TICKERS, START_DATE  # noqa: E402


RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"


def fetch() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Download OHLCV for every ticker; return (close, volume) wide frames."""
    print(f"Fetching {len(ALL_TICKERS)} tickers from {START_DATE} ...")
    raw = yf.download(
        tickers=ALL_TICKERS,
        start=START_DATE,
        auto_adjust=True,       # adjusts for splits/dividends; the "Close" is adjusted
        progress=True,
        group_by="ticker",
        threads=True,
    )

    # yfinance returns a multi-index (ticker, field) when group_by='ticker'.
    close = pd.concat(
        {t: raw[t]["Close"] for t in ALL_TICKERS if t in raw.columns.get_level_values(0)},
        axis=1,
    )
    volume = pd.concat(
        {t: raw[t]["Volume"] for t in ALL_TICKERS if t in raw.columns.get_level_values(0)},
        axis=1,
    )

    return close, volume


def sanity_check(close: pd.DataFrame) -> None:
    """Print a small report so we can eyeball data quality."""
    print("\n--- Sanity check ---")
    print(f"Shape:            {close.shape}   (rows=days, cols=tickers)")
    print(f"Date range:       {close.index.min().date()} -> {close.index.max().date()}")
    print(f"Tickers pulled:   {list(close.columns)}")

    missing = set(ALL_TICKERS) - set(close.columns)
    if missing:
        print(f"!! MISSING tickers (yfinance returned nothing): {sorted(missing)}")

    nan_pct = close.isna().mean().sort_values(ascending=False)
    print("\nNaN % per ticker (top 5):")
    print(nan_pct.head().to_string())


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    close, volume = fetch()

    close.to_parquet(RAW_DIR / "prices_daily.parquet")
    volume.to_parquet(RAW_DIR / "volume_daily.parquet")

    with (RAW_DIR / "fetch_log.txt").open("w", encoding="utf-8") as f:
        f.write(
            f"Fetched at {datetime.now().isoformat(timespec='seconds')}\n"
            f"Tickers  : {len(close.columns)} / {len(ALL_TICKERS)}\n"
            f"Rows     : {len(close)}\n"
            f"Range    : {close.index.min().date()} -> {close.index.max().date()}\n"
        )

    sanity_check(close)
    print(f"\nSaved: {RAW_DIR / 'prices_daily.parquet'}")
    print(f"Saved: {RAW_DIR / 'volume_daily.parquet'}")


if __name__ == "__main__":
    main()
