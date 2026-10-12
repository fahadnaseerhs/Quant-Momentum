"""
Path A1 — download daily prices for every stock that was ever an S&P 500 member
since 2004 (point-in-time list from src/sp500.py), plus SPY.

Output (data/sp500/):
  membership.parquet     (ticker, start, end)
  prices.parquet         adjusted close, wide (date x ticker)
  volume.parquet
  coverage.csv           per month: members, members with a price, coverage %
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import sp500  # noqa: E402

OUT = ROOT / "data" / "sp500"
START = "2003-06-01"

iv = sp500.membership()
iv.attrs = {}
iv.to_parquet(OUT / "membership.parquet")
need = sorted(iv.loc[iv["end"].isna() | (iv["end"] >= "2004-06-01"), "ticker"].unique()) + ["SPY"]
print(f"{len(need)} tickers to download", flush=True)

closes, vols = [], []
for i in range(0, len(need), 80):
    chunk = need[i:i + 80]
    raw = yf.download(chunk, start=START, auto_adjust=True, progress=False, threads=True, group_by="column")
    closes.append(raw["Close"])
    vols.append(raw["Volume"])
    print(f"  {i + len(chunk)}/{len(need)}", flush=True)

px = pd.concat(closes, axis=1)
vol = pd.concat(vols, axis=1)
px.index = pd.to_datetime(px.index).tz_localize(None)
vol.index = px.index
px = px.loc[:, px.notna().sum() > 20]
vol = vol[px.columns]
cal = px.index[px["SPY"].notna()]
px, vol = px.reindex(cal), vol.reindex(cal)
px.to_parquet(OUT / "prices.parquet")
vol.to_parquet(OUT / "volume.parquet")

firsts = cal[[True] + [a.month != b.month for a, b in zip(cal[1:], cal[:-1])]]
rows = []
for d in firsts[firsts >= "2005-01-01"]:
    m = sp500.members_on(iv, d)
    have = [t for t in m if t in px.columns and pd.notna(px.at[d, t])]
    rows.append({"date": d, "members": len(m), "with_price": len(have), "coverage": len(have) / len(m)})
cov = pd.DataFrame(rows).set_index("date")
cov.to_csv(OUT / "coverage.csv", float_format="%.4f")
print(f"\nprices: {px.shape}, tickers with data {px.shape[1]}/{len(need)}")
print(cov["coverage"].resample("YE").mean().round(3).to_string())
