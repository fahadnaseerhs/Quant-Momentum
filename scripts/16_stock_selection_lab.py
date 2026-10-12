"""
Path A1 — stock-selection lab (pre-registered in
Quant_Momentum/Product/Path A - Stock Selection Plan.md).

Each month, rank point-in-time S&P 500 members by 6 published price signals
(S1-S6) and 3 combinations (C1 z-average, C2 ridge, C3 boosted trees), then
score: monthly rank IC, long-only top quintile vs equal-weight universe after
10 bps costs, long-short decile (info). Controls: shuffled and random scores.
Design = predictions <= 2015, HOLDOUT = 2016+.

Outputs: data/sp500/panel.parquet, reports/tables/16_stock_lab.csv,
         reports/figures/16_g1_stock_lab.png (copied to Figures/16/)
"""
from __future__ import annotations

import shutil
import sys
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
warnings.filterwarnings("ignore")
from src import sp500  # noqa: E402

DATA = ROOT / "data" / "sp500"
FIG, TBL = ROOT / "reports" / "figures", ROOT / "reports" / "tables"
VAULT = ROOT / "Quant_Momentum" / "Figures" / "16"
VAULT.mkdir(parents=True, exist_ok=True)
DESIGN_END = pd.Timestamp("2015-12-31")
COST = 10e-4
MIN_TRAIN = 36
SIGNALS = {"S1 momentum 12-1": ("mom", +1), "S2 short-term reversal": ("rev", -1),
           "S3 low volatility": ("vol", -1), "S4 low beta": ("beta", -1),
           "S5 lottery (MAX)": ("max", -1), "S6 52-week high": ("hi52", +1)}
FEATS = [v[0] for v in SIGNALS.values()]


# ---------------------------------------------------------------------- #
# 1. Monthly panel: features at the first trading day of each month, label = next month return
# ---------------------------------------------------------------------- #

def build_panel() -> pd.DataFrame:
    px = pd.read_parquet(DATA / "prices.parquet")
    iv = pd.read_parquet(DATA / "membership.parquet")
    sec = sp500.sectors()
    spy = px["SPY"].to_numpy()
    stocks = px.drop(columns="SPY")
    cols = np.array(stocks.columns)
    col_pos = {t: k for k, t in enumerate(cols)}
    P = stocks.to_numpy(float)
    R = stocks.pct_change(fill_method=None).to_numpy(float)
    rs = np.r_[np.nan, spy[1:] / spy[:-1] - 1]
    cal = stocks.index
    firsts = cal[np.r_[True, cal.month[1:] != cal.month[:-1]]]
    firsts = firsts[firsts >= "2005-01-01"]
    out = []
    for d, nxt in zip(firsts[:-1], firsts[1:]):
        i, j = cal.get_loc(d), cal.get_loc(nxt)
        if i < 253:
            continue
        idx = np.array([col_pos[t] for t in sp500.members_on(iv, d) if t in col_pos])
        win = P[i - 252:i + 1, idx]
        ok = (np.isfinite(win).sum(0) >= 230) & np.isfinite(P[i, idx]) & np.isfinite(P[i - 252, idx]) \
            & np.isfinite(P[i - 21, idx])
        idx = idx[ok]
        if len(idx) < 100:
            continue
        p_i = P[i, idx]
        nxt_block = P[i + 1:j + 1, idx]                                # last price before/at next month start
        last = pd.DataFrame(nxt_block).ffill().to_numpy()[-1]
        ret = last / p_i - 1
        r63, r252, r21 = R[i - 62:i + 1, idx], R[i - 251:i + 1, idx], R[i - 20:i + 1, idx]
        y = rs[i - 251:i + 1][:, None]
        m = np.isfinite(r252) & np.isfinite(y)
        xm = np.nansum(np.where(m, r252, 0), 0) / m.sum(0)
        ym = np.nansum(np.where(m, y, 0), 0) / m.sum(0)
        beta = np.nansum(np.where(m, (r252 - xm) * (y - ym), 0), 0) / np.nansum(np.where(m, (y - ym) ** 2, 0), 0)
        out.append(pd.DataFrame({
            "date": d, "ticker": cols[idx], "sector": [sec.get(t, "Unknown") for t in cols[idx]],
            "mom": P[i - 21, idx] / P[i - 252, idx] - 1, "rev": p_i / P[i - 21, idx] - 1,
            "vol": np.nanstd(r63, 0), "beta": beta, "max": np.nanmax(r21, 0),
            "hi52": p_i / np.nanmax(win[:, ok], 0), "ret": ret}))
    panel = pd.concat(out, ignore_index=True)
    return panel[np.isfinite(panel["ret"])]


def zscore(s: pd.Series) -> pd.Series:
    lo, hi = s.quantile([0.01, 0.99])
    s = s.clip(lo, hi)
    return (s - s.mean()) / (s.std() or 1)


# ---------------------------------------------------------------------- #
# 2. Scores
# ---------------------------------------------------------------------- #

def add_scores(panel: pd.DataFrame) -> pd.DataFrame:
    g = panel.groupby("date")
    for name, (f, sign) in SIGNALS.items():
        panel[f"z_{f}"] = g[f].transform(zscore)
        panel[name] = sign * panel[f"z_{f}"]
    panel["C1 z-average"] = panel[list(SIGNALS)].mean(axis=1)
    panel["target"] = g["ret"].rank(pct=True) - 0.5
    zf = [f"z_{f}" for f in FEATS]
    sectors = sorted(panel["sector"].unique())
    sec_code = {s: k for k, s in enumerate(sectors)}
    dummies = pd.get_dummies(panel["sector"]).reindex(columns=sectors, fill_value=0).to_numpy(float)
    Xz = panel[zf].fillna(0).to_numpy()
    months = np.sort(panel["date"].unique())
    c2, c3 = np.full(len(panel), np.nan), np.full(len(panel), np.nan)
    tree, tree_year = None, None
    dates = panel["date"].to_numpy()
    for m in months[MIN_TRAIN:]:
        tr, te = dates < m, dates == m
        ridge = Ridge(alpha=10.0).fit(np.c_[Xz[tr], dummies[tr]], panel["target"].to_numpy()[tr])
        c2[te] = ridge.predict(np.c_[Xz[te], dummies[te]])
        yr = pd.Timestamp(m).year
        if tree is None or yr != tree_year:
            X = np.c_[Xz[tr], panel["sector"].map(sec_code).to_numpy()[tr]]
            tree = HistGradientBoostingRegressor(max_depth=3, learning_rate=0.05, max_iter=200,
                                                 min_samples_leaf=200, l2_regularization=1.0,
                                                 categorical_features=[len(zf)], random_state=0)
            tree.fit(X, panel["target"].to_numpy()[tr])
            tree_year = yr
        c3[te] = tree.predict(np.c_[Xz[te], panel["sector"].map(sec_code).to_numpy()[te]])
    panel["C2 ridge"], panel["C3 boosted trees"] = c2, c3
    rng = np.random.default_rng(42)
    panel["CONTROL shuffled momentum"] = panel.groupby("date")["S1 momentum 12-1"].transform(
        lambda s: rng.permutation(s.to_numpy()))
    panel["CONTROL random"] = rng.standard_normal(len(panel))
    return panel


# ---------------------------------------------------------------------- #
# 3. Evaluation
# ---------------------------------------------------------------------- #

def evaluate(panel: pd.DataFrame, score: str) -> pd.DataFrame:
    rows, prev_top = [], None
    for d, g in panel[["date", "ticker", "ret", score]].dropna().groupby("date"):
        if len(g) < 100:
            continue
        ic = g[score].rank().corr(g["ret"].rank())
        q = g[score].rank(pct=True)
        top = g[q > 0.8]
        top_set = set(top["ticker"])
        turn = 1.0 if prev_top is None else 1 - len(top_set & prev_top) / max(len(top_set), 1)
        prev_top = top_set
        dec_hi, dec_lo = g[q > 0.9]["ret"].mean(), g[q <= 0.1]["ret"].mean()
        rows.append({"date": d, "ic": ic, "top_q": top["ret"].mean(), "universe": g["ret"].mean(),
                     "excess_net": top["ret"].mean() - g["ret"].mean() - 2 * turn * COST,
                     "ls_net": dec_hi - dec_lo - 4 * turn * COST, "turnover": turn, "n": len(g)})
    return pd.DataFrame(rows).set_index("date")


def summarize(ev: pd.DataFrame) -> dict:
    t = lambda s: s.mean() / s.std() * np.sqrt(len(s)) if len(s) > 2 else np.nan  # noqa: E731
    return {"months": len(ev), "ic_mean": ev["ic"].mean(), "ic_t": t(ev["ic"]),
            "ic_hit": (ev["ic"] > 0).mean(), "excess_ann": ev["excess_net"].mean() * 12,
            "excess_t": t(ev["excess_net"]), "ls_ann": ev["ls_net"].mean() * 12,
            "ls_sharpe": ev["ls_net"].mean() / ev["ls_net"].std() * np.sqrt(12),
            "turnover": ev["turnover"].mean(), "stocks": ev["n"].mean()}


if __name__ == "__main__":
    panel = build_panel()
    print(f"panel: {len(panel):,} stock-months, {panel['date'].nunique()} months, "
          f"{panel['ticker'].nunique()} stocks", flush=True)
    panel = add_scores(panel)
    panel.to_parquet(DATA / "panel.parquet")
    names = list(SIGNALS) + ["C1 z-average", "C2 ridge", "C3 boosted trees",
                             "CONTROL shuffled momentum", "CONTROL random"]
    rows, evs = [], {}
    for s in names:
        ev = evaluate(panel, s)
        evs[s] = ev
        for per, mask in (("design", ev.index <= DESIGN_END), ("HOLDOUT", ev.index > DESIGN_END)):
            rows.append({"candidate": s, "period": per, **summarize(ev[mask])})
    T = pd.DataFrame(rows).set_index(["candidate", "period"])
    ho, de = T.xs("HOLDOUT", level="period"), T.xs("design", level="period")
    verdict = pd.DataFrame({
        "1 IC>=0.01 & t>=2.6": (ho["ic_mean"] >= 0.01) & (ho["ic_t"] >= 2.6),
        "2 design IC>0": de["ic_mean"] > 0,
        "3 top-quintile net excess t>=2": ho["excess_t"] >= 2})
    verdict["PASS"] = verdict.all(axis=1) & ~verdict.index.str.startswith("CONTROL")
    T.to_csv(TBL / "16_stock_lab.csv", float_format="%.4f")
    verdict.to_csv(TBL / "16_stock_lab_verdict.csv")
    pd.set_option("display.width", 220)
    print(T.round(4).to_string())
    print("\n=== PASS RULES (HOLDOUT 2016+) ===")
    print(verdict.to_string())

    fig, ax = plt.subplots(1, 2, figsize=(15, 5.5))
    y = np.arange(len(names))
    ax[0].barh(y, [ho.loc[n, "ic_t"] for n in names],
               color=["#9D9D9D" if n.startswith("CONTROL") else "#4C78A8" for n in names])
    ax[0].axvline(2.6, color="#E45756", ls="--", lw=1, label="pass bar t = 2.6")
    ax[0].axvline(0, color="k", lw=0.8)
    ax[0].set_yticks(y, names)
    ax[0].set_title("Holdout 2016-26: t-stat of monthly rank IC")
    ax[0].legend(fontsize=8)
    for n, c in (("C1 z-average", "#4C78A8"), ("C2 ridge", "#54A24B"), ("C3 boosted trees", "#E45756"),
                 ("S1 momentum 12-1", "#F58518"), ("CONTROL random", "#9D9D9D")):
        ev = evs[n]
        ax[1].plot((1 + ev["excess_net"]).cumprod(), label=n, color=c, lw=1.4 if not n.startswith("CONTROL") else 1)
    ax[1].axvline(pd.Timestamp("2016-01-01"), color="k", ls="--", lw=0.8)
    ax[1].axhline(1, color="k", lw=0.6)
    ax[1].set_title("Top fifth vs average S&P 500 stock, after costs (growth of $1 of excess)")
    ax[1].legend(fontsize=8)
    for a in ax:
        a.grid(True, ls=":", alpha=0.5)
    fig.suptitle("Path A1 — stock-selection lab (pre-registered)")
    fig.tight_layout()
    fig.savefig(FIG / "16_g1_stock_lab.png", dpi=130)
    shutil.copy2(FIG / "16_g1_stock_lab.png", VAULT / "16_g1_stock_lab.png")
    print("saved figure")
