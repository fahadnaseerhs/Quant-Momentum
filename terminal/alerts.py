"""QM Terminal — alerts: plain statements about what CHANGED.

Price alerts are rebuilt from history every refresh (so the feed is full from
the first launch), plus today's live moves. They state facts — risk level
changes, unusually big moves, trend flips, multi-year risk highs — and never
say what to buy.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from terminal.data import ASSETS, BUCKET_OF, name
from terminal.risk import MONTH, level, sigma_history, trend_arrow, trend_scores

LEVEL_RANK = {"VERY CALM": 0, "CALM": 1, "LIVELY": 2, "STORMY": 3}
CONFIRM = 3          # a new state must hold this many days before it is announced


def debounce(s: pd.Series, n: int = CONFIRM) -> pd.Series:
    """State series that only switches after `n` consecutive days in the new state
    (stops alerts flickering when a value sits on a band edge)."""
    vals = s.to_numpy(dtype=object)
    out = vals.copy()
    cur, cand, run = vals[0], None, 0
    for i, v in enumerate(vals):
        if v == cur:
            cand, run = None, 0
        else:
            run = run + 1 if v == cand else 1
            cand = v
            if run >= n:
                cur, cand, run = v, None, 0
        out[i] = cur
    return pd.Series(out, index=s.index)


def price_alerts(prices: pd.DataFrame, lookback: int = 30) -> list[dict]:
    sig = sigma_history(prices)
    swing = sig * np.sqrt(MONTH) * 100
    tz = trend_scores(prices, sig)
    rets = prices.pct_change(fill_method=None)
    window = prices.index[-lookback - 40:]             # warm-up so the debounced state is settled
    recent = prices.index[-lookback - 1:]
    out = []
    for t in ASSETS:
        b = BUCKET_OF[t].upper().replace("_", " ")
        nm = name(t)
        lv = debounce(swing[t].loc[window].map(lambda v: level(v) if np.isfinite(v) else None)).loc[recent]
        for d, prev, cur in zip(recent[1:], lv.iloc[:-1], lv.iloc[1:]):
            if prev and cur and prev != cur:
                up = LEVEL_RANK[cur] > LEVEL_RANK[prev]
                out.append({"date": d, "level": 2 if cur == "STORMY" else 1 if up else 0, "source": b,
                            "text": f"{nm} turned {cur.lower()} (was {prev.lower()}): "
                                    f"a normal month now swings ±{swing[t].loc[d]:.1f}%"})
        k = rets[t] / sig[t].shift(1)
        for d in recent[1:]:
            if np.isfinite(k.loc[d]) and abs(k.loc[d]) >= 3:
                out.append({"date": d, "level": 2, "source": b,
                            "text": f"{nm} moved {rets[t].loc[d] * 100:+.1f}% in a day "
                                    f"({abs(k.loc[d]):.1f}x a normal day)"})
        ar = debounce(tz[t].loc[window].map(trend_arrow)).loc[recent]
        for d, prev, cur in zip(recent[1:], ar.iloc[:-1], ar.iloc[1:]):
            if prev in ("↑", "↑↑") and cur in ("↓", "↓↓") or prev in ("↓", "↓↓") and cur in ("↑", "↑↑") \
                    or (prev == "→" and cur in ("↑↑", "↓↓")):
                out.append({"date": d, "level": 1, "source": b,
                            "text": f"{nm} trend flipped {prev} → {cur}"})
        s = sig[t].dropna()
        if len(s) > 300:
            higher = s.iloc[:-1][s.iloc[:-1] >= s.iloc[-1]]
            if len(higher) and (s.index[-1] - higher.index[-1]).days > 365:
                out.append({"date": s.index[-1], "level": 2, "source": b,
                            "text": f"{nm} risk is the highest since {higher.index[-1]:%b %Y}"})
    return out


def merge(*feeds: list[dict], limit: int = 60) -> pd.DataFrame:
    rows = [a for f in feeds for a in f]
    if not rows:
        return pd.DataFrame(columns=["date", "level", "source", "text"])
    df = pd.DataFrame(rows).drop_duplicates(subset=["date", "text"])
    return df.sort_values(["date", "level"], ascending=[False, False]).head(limit).reset_index(drop=True)
