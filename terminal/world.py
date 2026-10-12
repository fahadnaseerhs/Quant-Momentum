"""QM Terminal — world view (Phase 2): gauges, weather type, playbook, globe.

Every threshold marks roughly the most unusual ~10% of days since 2004
(calibrated once, see Product/QM Terminal - Plan). The playbook is pure
history: what each bucket did after past episodes, with counts.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.universe import UNIVERSE  # noqa: E402
from terminal.data import fred  # noqa: E402

SAFE = "SHY"   # the safe part of the PLAN tab; kept out of bucket history so BONDS = long bonds

STATUS = ["NORMAL", "RISING", "ALARM"]
WEATHER = {"fear": "PANIC SHOCK", "recession": "GROWTH SCARE / DEPRESSION RISK",
           "inflation": "INFLATION SHOCK", "war": "WAR / GEOPOLITICAL TENSION"}
GPR_ELEVATED, GPR_TOP5, GPR_ALARM = 150.0, 177.0, 207.0     # 90th / 95th / 97th pct since 1985

COUNTRY = {
    "ARG": "Argentina", "AUS": "Australia", "BEL": "Belgium", "BRA": "Brazil", "CAN": "Canada",
    "CHE": "Switzerland", "CHL": "Chile", "CHN": "China", "COL": "Colombia", "DEU": "Germany",
    "DNK": "Denmark", "EGY": "Egypt", "ESP": "Spain", "FIN": "Finland", "FRA": "France",
    "GBR": "United Kingdom", "HKG": "Hong Kong", "HUN": "Hungary", "IDN": "Indonesia",
    "IND": "India", "ISR": "Israel", "ITA": "Italy", "JPN": "Japan", "KOR": "South Korea",
    "MEX": "Mexico", "MYS": "Malaysia", "NLD": "Netherlands", "NOR": "Norway", "PER": "Peru",
    "PHL": "Philippines", "POL": "Poland", "PRT": "Portugal", "RUS": "Russia",
    "SAU": "Saudi Arabia", "SWE": "Sweden", "THA": "Thailand", "TUN": "Tunisia", "TUR": "Turkey",
    "TWN": "Taiwan", "UKR": "Ukraine", "USA": "United States", "VEN": "Venezuela",
    "VNM": "Vietnam", "ZAF": "South Africa",
}


def _pc(s: pd.Series, d: int) -> pd.Series:
    return s.pct_change(d, fill_method=None) * 100


def _component(label, series, flag, fmt):
    return {"label": label, "series": series, "flag": flag, "fmt": fmt}


def build_gauges(w: pd.DataFrame, gpr_daily: pd.DataFrame, fred_key: str = "") -> dict:
    """Four gauges. Each: components (series + boolean flag series), status series (0/1/2)."""
    idx = w.index
    ff = lambda s: s.reindex(idx.union(s.index)).ffill().reindex(idx)  # noqa: E731  (monthly/daily -> SPY calendar)

    vix = w["^VIX"]
    fear = {"components": [_component("VIX fear index", vix, vix >= 30, "{:.1f}")]}
    fear["status"] = pd.Series(np.select([vix >= 30, vix >= 20], [2, 1], 0), idx)

    curve = w["^TNX"] - w["^IRX"]
    credit = _pc(w["HYG"] / w["IEF"], 63)
    cugold = _pc(w["HG=F"] / w["GC=F"], 63)
    rec = [_component("Yield curve 10y-3m (pp)", curve, curve < 0, "{:+.2f}"),
           _component("Credit stress: junk vs safe bonds, 3m %", credit, credit <= -5, "{:+.1f}%"),
           _component("Copper vs gold, 3m %", cugold, cugold <= -15, "{:+.1f}%")]
    sahm, hy = fred("SAHMREALTIME", fred_key), fred("BAMLH0A0HYM2", fred_key)
    if len(sahm):
        rec.append(_component("Jobless trend (Sahm rule)", ff(sahm), ff(sahm) >= 0.5, "{:.2f}"))
    if len(hy):
        rec.append(_component("Junk-bond spread (%)", ff(hy), ff(hy) >= 6, "{:.2f}"))

    oil63 = _pc(w["CL=F"], 63)
    tipief = _pc(w["TIP"] / w["IEF"], 63)
    y10 = w["^TNX"].diff(63)
    inf = [_component("Oil, 3m %", oil63, oil63 >= 25, "{:+.1f}%"),
           _component("Inflation protection vs bonds (TIP/IEF), 3m %", tipief, tipief >= 2.5, "{:+.1f}%"),
           _component("10y yield change, 3m (pp)", y10, y10 >= 0.6, "{:+.2f}")]
    be = fred("T10YIE", fred_key)
    if len(be):
        be_chg = ff(be).diff(63)
        inf.append(_component("Breakeven inflation change, 3m (pp)", be_chg, be_chg >= 0.4, "{:+.2f}"))

    g = ff(gpr_daily["GPRD_MA7"]) if len(gpr_daily) else pd.Series(np.nan, idx)
    oil21 = _pc(w["CL=F"], 21)
    ita = _pc(w["ITA"] / w["SPY"], 21)
    war = {"components": [_component("Geopolitical Risk index (7-day avg)", g, g >= GPR_ELEVATED, "{:.0f}"),
                          _component("Oil, 1m %", oil21, oil21 >= 13, "{:+.1f}%"),
                          _component("Defence stocks vs market, 1m %", ita, ita >= 4, "{:+.1f}%")]}
    war["status"] = pd.Series(np.select([g >= GPR_ALARM, (g >= GPR_ELEVATED) | ((oil21 >= 13) & (ita >= 4))],
                                        [2, 1], 0), idx)

    out = {"fear": fear, "war": war}
    for name, comps in (("recession", rec), ("inflation", inf)):
        n = sum(c["flag"].astype(int) for c in comps)
        out[name] = {"components": comps, "status": pd.Series(np.select([n >= 2, n >= 1], [2, 1], 0), idx)}

    # episode triggers for the playbook (history only)
    out["fear"]["trigger"] = vix >= 30
    out["recession"]["trigger"] = out["recession"]["status"] == 2
    out["inflation"]["trigger"] = out["inflation"]["status"] == 2
    out["war"]["trigger"] = g >= GPR_TOP5
    out["fear"]["trigger_text"] = "VIX at 30 or above"
    out["recession"]["trigger_text"] = "2+ recession signals at once"
    out["inflation"]["trigger_text"] = "2+ inflation signals at once"
    out["war"]["trigger_text"] = f"war-tension index in its top 5% (7-day avg >= {GPR_TOP5:.0f})"
    return out


def weather(gauges: dict) -> list[tuple[str, int]]:
    """Active weather types, most severe first; ('CALM', 0) if none."""
    act = [(WEATHER[k], int(g["status"].iloc[-1])) for k, g in gauges.items() if g["status"].iloc[-1] > 0]
    return sorted(act, key=lambda x: -x[1]) or [("CALM", 0)]


# ---------------------------------------------------------------------- #
# Playbook: what each bucket did after past episodes
# ---------------------------------------------------------------------- #

def episodes(trigger: pd.Series, cooldown: int = 63) -> list[pd.Timestamp]:
    """Dates the trigger switched on after >= `cooldown` days off."""
    t = trigger.fillna(False).astype(bool).to_numpy()
    out, last_on = [], -10 ** 9
    for i, on in enumerate(t):
        if on:
            if i - last_on > cooldown:
                out.append(trigger.index[i])
            last_on = i
    return out


def playbook(trigger: pd.Series, prices: pd.DataFrame, horizons=(21, 63)) -> tuple[pd.DataFrame, list]:
    """Per bucket (+SPY): median % move and 'up in N of M' after each episode start."""
    starts = [d for d in episodes(trigger) if d in prices.index]
    pos = {d: prices.index.get_loc(d) for d in starts}
    rows = []
    groups = {**{b.upper().replace("_", " "): [t for t in ts if t != SAFE] for b, ts in UNIVERSE.items()},
              "S&P 500": ["SPY"]}
    for name, ts in groups.items():
        row = {"segment": name}
        for h in horizons:
            moves = []
            for d in starts:
                i = pos[d]
                if i + h >= len(prices):
                    continue
                r = (prices[ts].iloc[i + h] / prices[ts].iloc[i] - 1).dropna()
                if len(r):
                    moves.append(r.mean() * 100)
            lab = "1M" if h == 21 else "3M"
            row[f"median {lab}"] = np.median(moves) if moves else np.nan
            row[f"up {lab}"] = f"{sum(m > 0 for m in moves)}/{len(moves)}" if moves else "—"
        rows.append(row)
    return pd.DataFrame(rows).set_index("segment"), starts


FAMOUS = {
    "2008 financial crisis (depression scare)": ("2007-10-09", "2009-03-09"),
    "2020 Covid crash (sudden shock)": ("2020-02-19", "2020-03-23"),
    "2022 Russia invades Ukraine (first 5 weeks)": ("2022-02-23", "2022-03-31"),
    "2022 inflation + rate hikes (full year)": ("2021-12-31", "2022-12-30"),
}


def famous_crises(prices: pd.DataFrame) -> pd.DataFrame:
    """Average % move per bucket (+SPY) through well-known crises."""
    rows = {}
    for name, (a, b) in FAMOUS.items():
        seg = prices.loc[a:b]
        first = seg.iloc[0]
        r = seg.iloc[-1] / first - 1
        row = {k.upper().replace("_", " "): r[[t for t in ts if t != SAFE and np.isfinite(first.get(t, np.nan))]].mean() * 100
               for k, ts in UNIVERSE.items()}
        row["S&P 500"] = r["SPY"] * 100
        rows[name] = row
    return pd.DataFrame(rows).T


# ---------------------------------------------------------------------- #
# Globe + world alerts
# ---------------------------------------------------------------------- #

def country_tension(gpr_monthly: pd.DataFrame) -> pd.DataFrame:
    """Latest month per country: level and percentile vs that country's own history since 2000."""
    cols = [c for c in gpr_monthly.columns if c.startswith("GPRC_")]
    m = gpr_monthly.loc["2000":, cols].dropna(how="all")
    last = m.iloc[-1]
    rows = []
    for c in cols:
        code = c.replace("GPRC_", "")
        h = m[c].dropna()
        if len(h) and np.isfinite(last[c]):
            rows.append({"iso3": code, "country": COUNTRY.get(code, code), "level": last[c],
                         "pct": (h < last[c]).mean() * 100})
    df = pd.DataFrame(rows)
    df.attrs["month"] = m.index[-1]
    return df


def world_alerts(gauges: dict, lookback: int = 30) -> list[dict]:
    """Status changes and component flag flips in the last `lookback` days, plus live alarms."""
    from terminal.alerts import debounce                 # 3-day confirmation, as for prices
    out = []
    for key, g in gauges.items():
        st = debounce(g["status"].iloc[-lookback - 40:]).astype(int).iloc[-lookback - 1:]
        ch = st[st.diff().fillna(0) != 0]
        for d, v in ch.items():
            prev = st.shift(1).loc[d]
            out.append({"date": d, "level": int(v), "source": "WORLD",
                        "text": f"{key.upper()} gauge {STATUS[int(prev)]} → {STATUS[int(v)]}"})
        for c in g["components"]:
            f = debounce(c["flag"].fillna(False).astype(int).iloc[-lookback - 40:]).astype(int).iloc[-lookback - 1:]
            for d in f[f.diff().fillna(0) != 0].index:
                on = bool(f.loc[d])
                val = c["series"].loc[d]
                out.append({"date": d, "level": 1 if on else 0, "source": "WORLD",
                            "text": f"{c['label']}: {'signal ON' if on else 'back to normal'} "
                                    f"({c['fmt'].format(val) if np.isfinite(val) else 'n/a'})"})
    g = gauges["war"]["components"][0]["series"].dropna()
    if len(g) > 300:
        now = g.iloc[-1]
        higher = g.iloc[:-1][g.iloc[:-1] >= now]
        if len(higher) and (g.index[-1] - higher.index[-1]).days > 365:
            out.append({"date": g.index[-1], "level": 2, "source": "WORLD",
                        "text": f"War-tension index {now:.0f}: highest since {higher.index[-1]:%b %Y}"})
    return out
