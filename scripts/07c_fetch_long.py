"""
Task 07c — Fetch + clean a LONG price history (2004 →) for the same universe.

Same tickers, same cleaning rules as Tasks 01–02 (SPY calendar, forward-fill
gaps <= 2 days, no backfill).  Assets enter when they list (crypto ~2014+).
Written to a SEPARATE folder so the 2021–26 data used by Tasks 02–07b is untouched.

Output:
  data/long/raw/prices_daily.parquet
  data/long/processed/prices_daily_clean.parquet
  data/long/processed/cleaning_log.txt
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.cleaning import align_to_calendar, audit, fill_short_gaps, to_returns, trading_calendar
from src.universe import ALL_TICKERS, BENCHMARK

START = "2004-01-01"
RAW_DIR = ROOT / "data" / "long" / "raw"
OUT_DIR = ROOT / "data" / "long" / "processed"
RAW_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)

raw = yf.download(tickers=ALL_TICKERS, start=START, auto_adjust=True,
                  progress=False, group_by="ticker", threads=True)
close = pd.concat({t: raw[t]["Close"] for t in ALL_TICKERS
                   if t in raw.columns.get_level_values(0)}, axis=1)
close.to_parquet(RAW_DIR / "prices_daily.parquet")

prices = align_to_calendar(close, trading_calendar(close, BENCHMARK))
prices, fill_report = fill_short_gaps(prices, max_fill=2)
returns = to_returns(prices, "simple")
prices.to_parquet(OUT_DIR / "prices_daily_clean.parquet")

rep = audit(close, prices, fill_report, returns)
lines = [f"Cleaned at : {datetime.now().isoformat(timespec='seconds')}",
         f"Range      : {rep['range'][0]} -> {rep['range'][1]}  ({rep['clean_rows']} trading days)",
         "", f"{'ticker':<10}{'first':>12}{'filled':>8}{'nan_left':>10}{'ann_vol':>9}{'worst':>9}{'best':>9}  long_gaps"]
for t, s in rep["per_ticker"].items():
    lines.append(f"{t:<10}{str(s['first_valid']):>12}{s['filled']:>8}{s['remaining_nan']:>10}"
                 f"{s['annual_vol']:>9.1%}{s['worst_day']:>9.1%}{s['best_day']:>9.1%}  {s['long_gaps'] or '-'}")
(OUT_DIR / "cleaning_log.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
