"""Clean raw daily data: align to the NYSE calendar, fill short gaps, compute daily returns.

Run from the project root:

    python scripts/02_clean_data.py

Input:
    data/raw/prices_daily.parquet, data/raw/volume_daily.parquet
Output (data/processed/):
    prices_daily_clean.parquet   aligned + short gaps filled
    volume_daily_clean.parquet   aligned only (missing volume is not "unchanged", so never filled)
    returns_daily.parquet        simple returns
    returns_daily_log.parquet    log returns
    cleaning_log.txt             audit trail
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from src.cleaning import (  # noqa: E402
    align_to_calendar,
    audit,
    fill_short_gaps,
    to_returns,
    trading_calendar,
)
from src.universe import BENCHMARK  # noqa: E402

RAW_DIR = ROOT / "data" / "raw"
OUT_DIR = ROOT / "data" / "processed"
MAX_FILL_DAYS = 2


def write_log(report: dict, path: Path) -> None:
    lines = [
        f"Cleaned at     : {datetime.now().isoformat(timespec='seconds')}",
        f"Calendar source: {BENCHMARK} trading days",
        f"Raw rows       : {report['raw_rows']} (calendar days)",
        f"Clean rows     : {report['clean_rows']} (trading days)",
        f"Range          : {report['range'][0]} -> {report['range'][1]}",
        f"Max ffill      : {MAX_FILL_DAYS} trading days",
        f"Any inf        : {report['has_inf']}",
        f"Any return<=-1 : {report['below_minus_100']}",
        "",
        f"{'ticker':<10}{'first':>12}{'lead_nan':>10}{'filled':>8}{'nan_left':>10}"
        f"{'daily_sd':>10}{'ann_vol':>9}{'worst':>9}{'best':>9}  long_gaps",
    ]
    for t, s in report["per_ticker"].items():
        lines.append(
            f"{t:<10}{str(s['first_valid']):>12}{s['leading_nan']:>10}{s['filled']:>8}"
            f"{s['remaining_nan']:>10}{s['daily_std']:>10.2%}{s['annual_vol']:>9.1%}"
            f"{s['worst_day']:>9.1%}{s['best_day']:>9.1%}  {s['long_gaps'] or '-'}"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    raw_prices = pd.read_parquet(RAW_DIR / "prices_daily.parquet")
    raw_volume = pd.read_parquet(RAW_DIR / "volume_daily.parquet")

    calendar = trading_calendar(raw_prices, BENCHMARK)
    prices = align_to_calendar(raw_prices, calendar)
    volume = align_to_calendar(raw_volume, calendar)

    prices, fill_report = fill_short_gaps(prices, max_fill=MAX_FILL_DAYS)

    returns_simple = to_returns(prices, "simple")
    returns_log = to_returns(prices, "log")

    prices.to_parquet(OUT_DIR / "prices_daily_clean.parquet")
    volume.to_parquet(OUT_DIR / "volume_daily_clean.parquet")
    returns_simple.to_parquet(OUT_DIR / "returns_daily.parquet")
    returns_log.to_parquet(OUT_DIR / "returns_daily_log.parquet")

    report = audit(raw_prices, prices, fill_report, returns_simple)
    write_log(report, OUT_DIR / "cleaning_log.txt")

    print((OUT_DIR / "cleaning_log.txt").read_text(encoding="utf-8"))
    print(f"Saved 4 parquet files + cleaning_log.txt to {OUT_DIR}")


if __name__ == "__main__":
    main()
