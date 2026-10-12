"""Path A — point-in-time S&P 500 membership.

Rebuilt from Wikipedia's "List of S&P 500 companies": today's constituents
plus the table of additions/removals, walked BACKWARDS from today. Membership
at date d = the set after applying every change dated <= d.

Known limits: the change table is incomplete before ~2000 and a few tickers
were renamed (Yahoo keeps the newest symbol). Coverage is measured downstream.

Plan: Quant_Momentum/Product/Path A - Stock Selection Plan.md
"""
from __future__ import annotations

import io
from pathlib import Path

import pandas as pd
import requests

WIKI = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
DIR = Path(__file__).resolve().parents[1] / "data" / "sp500"
UA = {"User-Agent": "Mozilla/5.0 (QuantMomentumLab research)"}


def yahoo(sym: str) -> str:
    return str(sym).strip().replace(".", "-")


SNAPSHOT_REV = 1368675864        # 2026-08-10: newest page version that still had the change table


def _changes_table(tables: list[pd.DataFrame]) -> pd.DataFrame | None:
    for t in tables:
        if any("Added" in str(c) for c in t.columns):
            t = t.copy()
            t.columns = ["_".join(c for c in col if c and not str(c).startswith("Unnamed")).strip("_")
                         if isinstance(col, tuple) else col for col in t.columns]
            return t
    return None


def fetch_tables(refresh: bool = False) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Timestamp]:
    """(current constituents, change log, snapshot constituents, snapshot date).

    Wikipedia removed the change table from the live page in Aug 2026, so the
    change log comes from the last page version that had it (SNAPSHOT_REV).
    Both pages are cached in data/sp500/.
    """
    DIR.mkdir(parents=True, exist_ok=True)
    live, snap = DIR / "wikipedia_sp500.html", DIR / "wikipedia_sp500_snapshot.html"
    if refresh or not live.exists():
        r = requests.get(WIKI, timeout=60, headers=UA)
        r.raise_for_status()
        live.write_text(r.text, encoding="utf-8")
    if not snap.exists():
        r = requests.get("https://en.wikipedia.org/w/index.php", params={"oldid": SNAPSHOT_REV},
                         timeout=60, headers=UA)
        r.raise_for_status()
        snap.write_text(r.text, encoding="utf-8")
    cur_tables = pd.read_html(io.StringIO(live.read_text(encoding="utf-8")))
    snap_tables = pd.read_html(io.StringIO(snap.read_text(encoding="utf-8")))
    snap_date = pd.Timestamp("2026-08-10")
    return cur_tables[0], _changes_table(snap_tables), snap_tables[0], snap_date


def membership(refresh: bool = False) -> pd.DataFrame:
    """Long table of (ticker, start, end) membership intervals; end = NaT if still a member."""
    current, changes, snap_current, snap_date = fetch_tables(refresh)
    sym_col = [c for c in current.columns if "Symbol" in c][0]
    members = {yahoo(s) for s in current[sym_col]}

    date_col = [c for c in changes.columns if c.lower().startswith("date") or c.lower().startswith("effective")][0]
    add_col = [c for c in changes.columns if c.startswith("Added") and "Ticker" in c][0]
    rem_col = [c for c in changes.columns if c.startswith("Removed") and "Ticker" in c][0]
    ch = pd.DataFrame({"date": pd.to_datetime(changes[date_col], errors="coerce"),
                       "added": changes[add_col], "removed": changes[rem_col]}).dropna(subset=["date"])

    # Patch the gap since the snapshot: additions carry a "Date added"; removals are
    # snapshot members no longer listed, paired with the addition dates in order.
    snap_members = {yahoo(s) for s in snap_current[[c for c in snap_current.columns if "Symbol" in c][0]]}
    added_col = [c for c in current.columns if "Date added" in c][0]
    adds = current.assign(t=current[sym_col].map(yahoo), d=pd.to_datetime(current[added_col], errors="coerce"))
    adds = adds[~adds["t"].isin(snap_members)].sort_values("d")
    gone = sorted(snap_members - members)
    gap = [{"date": d if pd.notna(d) else pd.Timestamp.today().normalize(), "added": t,
            "removed": gone[i] if i < len(gone) else None} for i, (t, d) in enumerate(zip(adds["t"], adds["d"]))]
    gap += [{"date": snap_date + pd.Timedelta(days=1), "added": None, "removed": g} for g in gone[len(adds):]]
    ch = pd.concat([ch, pd.DataFrame(gap)], ignore_index=True).sort_values("date", ascending=False)

    intervals = []
    end_of: dict[str, pd.Timestamp] = {}
    for _, r in ch.iterrows():
        a = yahoo(r["added"]) if isinstance(r["added"], str) and r["added"].strip() else None
        rm = yahoo(r["removed"]) if isinstance(r["removed"], str) and r["removed"].strip() else None
        if a and a in members:                       # before this date, `a` was not a member
            members.discard(a)
            intervals.append((a, r["date"], end_of.pop(a, pd.NaT)))
        if rm:                                       # before this date, `rm` was a member
            members.add(rm)
            end_of[rm] = r["date"]
    earliest = ch["date"].min()
    for t in members:                                # members before the oldest recorded change
        intervals.append((t, earliest - pd.Timedelta(days=3650), end_of.get(t, pd.NaT)))
    df = pd.DataFrame(intervals, columns=["ticker", "start", "end"])
    df.attrs["earliest_change"] = earliest
    return df


def members_on(intervals: pd.DataFrame, d: pd.Timestamp) -> list[str]:
    m = (intervals["start"] <= d) & (intervals["end"].isna() | (intervals["end"] > d))
    return sorted(intervals.loc[m, "ticker"].unique())


def sectors(refresh: bool = False) -> dict[str, str]:
    """Current GICS sector per ticker (removed stocks: unknown)."""
    current, *_ = fetch_tables(refresh)
    sym = [c for c in current.columns if "Symbol" in c][0]
    sec = [c for c in current.columns if "Sector" in c][0]
    return {yahoo(s): v for s, v in zip(current[sym], current[sec])}
