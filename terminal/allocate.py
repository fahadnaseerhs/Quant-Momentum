"""QM Terminal — Phase 4A: risk per segment, risk-based buy list, weekly trade list.

One engine for the live terminal AND the historical test
(scripts/13_allocation_backtest.py), so what is shown is what was tested.

  1. Inside each segment, assets share the segment's money by equal risk.
  2. Each segment gets a share of the TOTAL risk (equal by default, growth
     segments doubled for BOLD), counting correlations between segments.
  3. The profile sets how much goes into the risky mix vs the safe part (SHY).
  4. Weekly check: trade only assets more than BAND away from their target.

Plan: Quant_Momentum/Product/QM Terminal - Phase 4 Plan (Allocation + Prediction).md
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

SAFE = "SHY"
MONTH = 21
BAND = 0.20            # trade only if an asset is >20% away from its target
MIN_TRADE = 5.0        # ... and the trade is at least $5
LAM = 0.94
GROWTH = {"crypto", "tech", "real_assets"}
# Every profile caps the 1-in-20 bad month. In calm markets that means fully
# invested; when markets turn stormy the invested share shrinks automatically
# (the tested "when to sell"). Fully-invested versions lost ~50% in 2008 on the
# design period (scripts/13_allocation_backtest.py), so FULL is kept only as a yardstick.
PROFILES = {
    "CAREFUL": {"bad_month": 0.03, "tilt": 1.0,
                "text": "a bad month (1 in 20) loses about 3% at most; the rest stays safe"},
    "BALANCED": {"bad_month": 0.06, "tilt": 1.0,
                 "text": "every segment carries the same risk; a bad month loses about 6% at most, "
                         "so in storms part of the money moves to the safe part"},
    "BOLD": {"bad_month": 0.10, "tilt": 2.0,
             "text": "growth segments (crypto, tech, real assets) carry double risk; a bad month loses about 10% at most"},
    "FULL": {"bad_month": None, "tilt": 1.0, "text": "always fully invested, equal risk per segment (yardstick only)"},
}
PORTFOLIO_FILE = Path(__file__).resolve().parent / "portfolio.json"


def segments(universe: dict) -> dict:
    """Risk segments = the buckets without the safe asset."""
    out = {k: [t for t in v if t != SAFE] for k, v in universe.items()}
    return {k: v for k, v in out.items() if v}


def _ewma_last(x: np.ndarray) -> np.ndarray:
    """EWMA variance at the end of a returns window (columns = series)."""
    var = np.nanmean(x[:63] ** 2, axis=0)
    for row in x[63:]:
        var = np.where(np.isfinite(row), LAM * var + (1 - LAM) * row ** 2, var)
    return np.sqrt(var)


def risk_budget(cov: np.ndarray, budget: np.ndarray, iters: int = 500) -> np.ndarray:
    """Weights whose risk contributions w_i (Cov w)_i are proportional to `budget`."""
    b = budget / budget.sum()
    w = b / np.sqrt(np.diag(cov))
    w /= w.sum()
    for _ in range(iters):
        rc = w * (cov @ w)
        rc = rc / rc.sum()
        if np.abs(rc - b).max() < 1e-7:
            break
        w = w * np.sqrt(b / np.maximum(rc, 1e-12))
        w /= w.sum()
    return w


def allocation(rets: pd.DataFrame, sig_now: pd.Series, universe: dict, profile: str = "BALANCED",
               custom_budget: dict | None = None, z_bad: float | None = None) -> tuple[pd.Series, dict]:
    """Target weights (sum to 1, SAFE included) from a trailing returns window ending today.

    rets    : daily returns, last ~252 rows, columns = tickers
    sig_now : today's EWMA daily vol per ticker
    z_bad   : 1-in-20 bad-month size in units of monthly sigma (empirical; default normal 1.645)
    """
    cols = list(rets.columns)
    pos = {t: j for j, t in enumerate(cols)}
    X = rets.to_numpy(dtype=float)
    sv = sig_now.reindex(cols).to_numpy(dtype=float)
    recent_ok = np.isfinite(X[-63:]).sum(axis=0) >= 60
    inner, seg_cols = {}, []
    for s, ts in segments(universe).items():
        idx = [pos[t] for t in ts if t in pos]
        idx = [j for j in idx if np.isfinite(sv[j]) and sv[j] > 0 and recent_ok[j]]
        if not idx:
            continue
        w = (1 / sv[idx]) / (1 / sv[idx]).sum()
        inner[s] = pd.Series(w, index=[cols[j] for j in idx])
        seg_cols.append(np.nan_to_num(X[:, idx]) @ w)
    names = list(inner)
    R = np.column_stack(seg_cols)
    vol = _ewma_last(R)
    corr = np.corrcoef(R[-252:].T) if len(names) > 1 else np.ones((1, 1))
    cov = np.outer(vol, vol) * np.nan_to_num(corr, nan=0.0)
    if custom_budget:
        budget = np.array([max(custom_budget.get(s, 1.0), 0.0) for s in names])
    else:
        tilt = PROFILES[profile]["tilt"]
        budget = np.array([tilt if s in GROWTH else 1.0 for s in names])
    sw = risk_budget(cov, budget)
    mix_vol = float(np.sqrt(sw @ cov @ sw))
    z = z_bad if z_bad is not None else 1.645
    bad_mix = z * mix_vol * np.sqrt(MONTH)
    target_bad = PROFILES.get(profile, {}).get("bad_month")
    invest = min(1.0, target_bad / bad_mix) if target_bad else 1.0

    weights = pd.Series(0.0, index=rets.columns)
    for s, wseg in zip(names, sw):
        weights[inner[s].index] += invest * wseg * inner[s]
    if SAFE in weights.index:
        weights[SAFE] += 1 - invest
    rc = sw * (cov @ sw)
    info = {"segments": names, "segment_weight": dict(zip(names, sw * invest)),
            "segment_risk_share": dict(zip(names, rc / rc.sum())),
            "segment_swing": dict(zip(names, vol * np.sqrt(MONTH))),
            "corr": pd.DataFrame(corr, index=names, columns=names),
            "mix_swing": mix_vol * np.sqrt(MONTH) * invest, "invest": invest,
            "bad_month": bad_mix * invest}
    return weights, info


# ---------------------------------------------------------------------- #
# Live helpers: segment risk table, plan outcome
# ---------------------------------------------------------------------- #

def _index_from(rets: pd.DataFrame, w: pd.Series) -> pd.Series:
    """Fixed-weight daily-rebalanced index over the dates where the weighted assets traded."""
    sub = rets[w.index]
    r = (sub.fillna(0.0) * w).sum(axis=1)[sub.notna().any(axis=1)]
    return (1 + r).cumprod()


def segment_table(prices: pd.DataFrame, universe: dict, info: dict, amount: float = 100.0,
                  days: int = MONTH) -> pd.DataFrame:
    """Per segment: assets, monthly swing, level, risk vs own history, $amount bad/good, plan shares."""
    from src.tsmom import ewma_vol
    from terminal.risk import level, outcome_range, z_quantiles

    rets = prices.pct_change(fill_method=None)
    sig_now = ewma_vol(rets).iloc[-1]
    rows = []
    for s in info["segments"]:
        ts = [t for t in segments(universe)[s] if np.isfinite(sig_now.get(t, np.nan))]
        w = (1 / sig_now[ts]) / (1 / sig_now[ts]).sum()
        idx = _index_from(rets, w)
        sh = ewma_vol(idx.pct_change().to_frame("x"))["x"].dropna()
        s_now = sh.iloc[-1]
        o = outcome_range(amount, s_now, z_quantiles(idx, sh, days), days)
        swing = s_now * np.sqrt(MONTH) * 100
        rows.append({"segment": s, "assets": ts, "swing": swing, "level": level(swing),
                     "vs_history_pct": (sh < s_now).mean() * 100, "bad": o[0], "good": o[4],
                     "money_share": info["segment_weight"][s], "risk_share": info["segment_risk_share"][s]})
    return pd.DataFrame(rows).set_index("segment")


def plan_outcome(prices: pd.DataFrame, weights: pd.Series, amount: float, days: int):
    """(outcomes at QUANTS, monthly swing %) for the whole plan held `days` days."""
    from src.tsmom import ewma_vol
    from terminal.risk import outcome_range, z_quantiles

    w = weights[weights > 0]
    rets = prices[w.index].pct_change(fill_method=None)
    idx = _index_from(rets, w)
    sh = ewma_vol(idx.pct_change().to_frame("x"))["x"].dropna()
    q = z_quantiles(idx, sh, days)
    return outcome_range(amount, sh.iloc[-1], q, days), sh.iloc[-1] * np.sqrt(MONTH) * 100, -q[0] if days == MONTH else None


def live_z_bad(prices: pd.DataFrame, universe: dict) -> float:
    """1-in-20 bad month of today's fully-invested mix, in monthly sigmas, from that mix's own history."""
    from src.tsmom import ewma_vol
    rets = prices.pct_change(fill_method=None)
    w, _ = allocation(rets.iloc[-252:], ewma_vol(rets).iloc[-1], universe, "FULL")
    _, _, z = plan_outcome(prices, w, 100.0, MONTH)
    return float(z)


# ---------------------------------------------------------------------- #
# Holdings + weekly trade list
# ---------------------------------------------------------------------- #

def load_portfolio() -> dict:
    if PORTFOLIO_FILE.exists():
        return json.loads(PORTFOLIO_FILE.read_text(encoding="utf-8"))
    return {"profile": "BALANCED", "cash": 0.0, "shares": {}, "last_rebalance": None, "swing_at_rebalance": {}}


def save_portfolio(p: dict) -> None:
    PORTFOLIO_FILE.write_text(json.dumps(p, indent=2), encoding="utf-8")


def next_check(last: str | None, today: pd.Timestamp) -> pd.Timestamp:
    """The weekly check is on Mondays."""
    d = today.normalize()
    return d + pd.Timedelta(days=(7 - d.weekday()) % 7)


def trade_list(shares: dict, cash: float, prices: pd.Series, target_w: pd.Series,
               swing_now: pd.Series, swing_then: dict, band: float = BAND, min_trade: float = MIN_TRADE) -> pd.DataFrame:
    """Buys/sells needed to bring holdings back to target (only where >band away)."""
    value = {t: shares.get(t, 0.0) * prices[t] for t in target_w.index}
    total = sum(value.values()) + cash
    rows = []
    for t in target_w.index:
        cur, tgt = value[t], target_w[t] * total
        gap = tgt - cur
        if abs(gap) < min_trade or (tgt > 0 and abs(gap) <= band * tgt and cur > 0):
            continue
        sw_now, sw_then = swing_now.get(t, np.nan), swing_then.get(t)
        if cur == 0:
            why = "new position for your plan"
        elif tgt == 0:
            why = "no longer in your plan"
        elif sw_then and np.isfinite(sw_now) and abs(sw_now - sw_then) / sw_then > 0.15:
            why = f"risk {'rose' if sw_now > sw_then else 'fell'} ±{sw_then:.1f}% → ±{sw_now:.1f}% a month"
        else:
            why = "prices moved it away from its target"
        rows.append({"ticker": t, "action": "BUY" if gap > 0 else "SELL", "amount": abs(gap),
                     "shares": abs(gap) / prices[t], "now": cur, "target": tgt, "why": why})
    return pd.DataFrame(rows, columns=["ticker", "action", "amount", "shares", "now", "target", "why"])
