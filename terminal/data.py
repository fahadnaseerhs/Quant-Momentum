"""QM Terminal — data layer: daily history (cached), live quotes, GPR index, FRED.

History is cached to terminal/cache/ and refreshed at most every 12 hours;
live quotes are 1-minute bars (crypto ~live, US stocks ~15 min delayed).
Prices follow the project's cleaning rules (SPY trading calendar, forward-fill
<= 2 days), so every number matches the research in Tasks 07-11.
"""
from __future__ import annotations

import io
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.cleaning import align_to_calendar, fill_short_gaps, trading_calendar  # noqa: E402
from src.universe import BENCHMARK, UNIVERSE  # noqa: E402

CACHE = ROOT / "terminal" / "cache"
CACHE.mkdir(parents=True, exist_ok=True)

BUCKET_NAMES = {"crypto": "CRYPTO", "tech": "TECH", "gold": "GOLD", "oil": "OIL",
                "real_assets": "REAL ASSETS", "bonds": "BONDS"}
SEGMENT_NAMES = BUCKET_NAMES          # UI wording: "segment"
ASSETS = [t for ts in UNIVERSE.values() for t in ts]
BUCKET_OF = {t: b for b, ts in UNIVERSE.items() for t in ts}

# Company / fund names shown in the UI instead of tickers.
NAMES = {
    "BTC-USD": "Bitcoin", "ETH-USD": "Ethereum", "SOL-USD": "Solana", "LINK-USD": "Chainlink",
    "AVAX-USD": "Avalanche", "AAPL": "Apple", "MSFT": "Microsoft", "NVDA": "Nvidia",
    "GOOGL": "Alphabet", "META": "Meta Platforms", "GLD": "SPDR Gold Trust", "B": "Barrick Mining",
    "USO": "United States Oil Fund", "XOM": "Exxon Mobil", "CVX": "Chevron",
    "VNQ": "Vanguard Real Estate", "DBC": "Invesco Commodity Index", "MSTR": "Strategy Inc",
    "TLT": "iShares 20+ Yr Treasury", "SHY": "iShares 1-3 Yr Treasury", "SPY": "S&P 500",
}


def name(ticker: str) -> str:
    """Company / fund display name for a ticker."""
    return NAMES.get(ticker, ticker)
WORLD = ["^VIX", "^TNX", "^IRX", "HYG", "IEF", "TIP", "ITA", "CL=F", "HG=F", "GC=F"]
START = "2004-01-01"
GPR_URLS = {
    "daily": "https://www.matteoiacoviello.com/gpr_files/data_gpr_daily_recent.xls",
    "monthly": "https://www.matteoiacoviello.com/gpr_files/data_gpr_export.xls",
}
UA = {"User-Agent": "Mozilla/5.0 (QM Terminal)"}


def _fresh(path: Path, max_age_h: float) -> bool:
    return path.exists() and (time.time() - path.stat().st_mtime) < max_age_h * 3600


def load_env() -> dict:
    """Read KEY=VALUE lines from the project's .env (keys stay on this computer)."""
    env = {}
    f = ROOT / ".env"
    if f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.split("#")[0].strip().strip('"').strip("'")
    for k in ("FRED_API_KEY", "ANTHROPIC_API_KEY"):
        env.setdefault(k, os.environ.get(k, ""))
    return env


# ---------------------------------------------------------------------- #
# Daily history
# ---------------------------------------------------------------------- #

def history(max_age_h: float = 12) -> pd.DataFrame:
    """Raw daily closes (adjusted) for assets + SPY + world tickers since 2004."""
    path = CACHE / "history.parquet"
    if not _fresh(path, max_age_h):
        tickers = ASSETS + [BENCHMARK] + WORLD
        raw = yf.download(tickers, start=START, auto_adjust=True, progress=False, threads=True)["Close"]
        raw.index = pd.to_datetime(raw.index).tz_localize(None)
        today = pd.Timestamp.now(tz="America/New_York").normalize().tz_localize(None)
        raw = raw[raw.index < today]          # completed sessions only; today comes from live quotes
        raw.to_parquet(path)
    return pd.read_parquet(path)


def asset_prices(raw: pd.DataFrame) -> pd.DataFrame:
    """Assets + SPY on the SPY trading calendar, short gaps filled (Task 02 rules)."""
    cols = ASSETS + [BENCHMARK]
    px = align_to_calendar(raw[cols], trading_calendar(raw[cols], BENCHMARK))
    return fill_short_gaps(px, max_fill=2)[0]


def world_prices(raw: pd.DataFrame) -> pd.DataFrame:
    """World-gauge series on the SPY calendar (futures/indices ffilled up to 3 days)."""
    cal = trading_calendar(raw, BENCHMARK)
    w = raw[WORLD + [BENCHMARK]].reindex(cal).ffill(limit=3)
    w["CL=F"] = w["CL=F"].where(w["CL=F"] > 0)     # Apr-2020 negative oil print
    return w


# ---------------------------------------------------------------------- #
# Live quotes
# ---------------------------------------------------------------------- #

def live_quotes(tickers: list[str]) -> tuple[pd.DataFrame, pd.Timestamp]:
    """Last 1-minute price and its time (New York) per ticker."""
    now = pd.Timestamp.now(tz="America/New_York")
    try:
        bars = yf.download(tickers, period="1d", interval="1m", progress=False, threads=True)["Close"]
    except Exception:
        return pd.DataFrame(columns=["price", "time"]), now
    if isinstance(bars, pd.Series):
        bars = bars.to_frame(tickers[0])
    if bars.index.tz is None:
        bars.index = bars.index.tz_localize("UTC")
    bars.index = bars.index.tz_convert("America/New_York")
    rows = {t: {"price": bars[t].dropna().iloc[-1], "time": bars[t].dropna().index[-1]}
            for t in bars.columns if bars[t].notna().any()}
    return pd.DataFrame(rows).T, now


def with_live(prices: pd.DataFrame, live: pd.DataFrame) -> pd.DataFrame:
    """Append a 'now' row: prices traded AFTER the last daily close, else the last close."""
    now_row = prices.iloc[-1].copy()
    last_close_day = prices.index[-1].date()
    for t, r in live.iterrows():
        if t in now_row.index and np.isfinite(r["price"]) and r["time"].date() > last_close_day:
            now_row[t] = r["price"]
    if (now_row.fillna(0) == prices.iloc[-1].fillna(0)).all():
        return prices                              # nothing new since the close
    now_row.name = prices.index[-1] + pd.Timedelta(days=1)
    return pd.concat([prices, now_row.to_frame().T])


# ---------------------------------------------------------------------- #
# Geopolitical Risk index (Caldara & Iacoviello) and FRED
# ---------------------------------------------------------------------- #

def gpr(kind: str, max_age_h: float = 24) -> pd.DataFrame:
    """'daily' (GPRD, GPRD_MA7, ... since 1985) or 'monthly' (GPR + 44 country GPRC_xxx)."""
    path = CACHE / f"gpr_{kind}.xls"
    if not _fresh(path, max_age_h):
        try:
            r = requests.get(GPR_URLS[kind], timeout=60, headers=UA)
            r.raise_for_status()
            path.write_bytes(r.content)
        except Exception:
            if not path.exists():
                return pd.DataFrame()
    df = pd.read_excel(io.BytesIO(path.read_bytes()))
    key = "date" if kind == "daily" else "month"
    df[key] = pd.to_datetime(df[key])
    return df.set_index(key).sort_index()


def fred(series_id: str, api_key: str, max_age_h: float = 12) -> pd.Series:
    """One FRED series since 2004 (empty Series if no key or the request fails)."""
    if not api_key:
        return pd.Series(dtype=float)
    path = CACHE / f"fred_{series_id}.parquet"
    if not _fresh(path, max_age_h):
        try:
            r = requests.get("https://api.stlouisfed.org/fred/series/observations",
                             params={"series_id": series_id, "api_key": api_key,
                                     "file_type": "json", "observation_start": START},
                             timeout=30)
            r.raise_for_status()
            obs = pd.DataFrame(r.json()["observations"])
            s = pd.to_numeric(obs["value"], errors="coerce")
            s.index = pd.to_datetime(obs["date"])
            s.dropna().to_frame("v").to_parquet(path)
        except Exception:
            if not path.exists():
                return pd.Series(dtype=float)
    return pd.read_parquet(path)["v"]
