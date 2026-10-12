"""
Phase 4B — Prediction lab: can today's information beat the base rate for
"will this asset be up next month?"  Pre-registered in
Quant_Momentum/Product/QM Terminal - Phase 4 Plan (Allocation + Prediction).md

Monthly, non-overlapping labels; expanding walk-forward refit every month
(trees: yearly); base rate = each group's expanding share of up-months.
Families F1-F5, two universes, design (<=2015) vs HOLDOUT (2016+).

Outputs: reports/tables/14_prediction_results.csv, 14_prediction_groups.csv
         reports/figures/14_g1_prediction_scores.png (copied to Figures/14/)
"""
from __future__ import annotations

import shutil
import sys
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
warnings.filterwarnings("ignore")

from src.tsmom import ewma_vol  # noqa: E402
from terminal import data as tdata  # noqa: E402
from terminal.risk import trend_scores  # noqa: E402

DESIGN_END, MIN_TRAIN, C = pd.Timestamp("2015-12-31"), 36, 0.5
FIG, TBL = ROOT / "reports" / "figures", ROOT / "reports" / "tables"
VAULT = ROOT / "Quant_Momentum" / "Figures" / "14"
VAULT.mkdir(parents=True, exist_ok=True)

WORLD7 = ["curve", "credit", "cugold", "oil63", "tipief", "y10", "gpr"]
ALL = ["trend", "rev5", "log_vix", "vix30"] + WORLD7

UNIVERSES = {
    "PROJECT 20": {
        "path": ROOT / "data/long/processed/prices_daily_clean.parquet",
        "F1": {"bonds": ["TLT"], "gold": ["GLD"], "commodities": ["USO", "DBC"]},
        "F2": {"tech": ["AAPL", "MSFT", "NVDA", "GOOGL", "META"], "energy stocks": ["XOM", "CVX"],
               "other stocks": ["B", "VNQ", "MSTR"]},
        "ALL": {"crypto": ["BTC-USD", "ETH-USD", "SOL-USD", "LINK-USD", "AVAX-USD"],
                "tech": ["AAPL", "MSFT", "NVDA", "GOOGL", "META"], "gold": ["GLD", "B"],
                "oil": ["USO", "XOM", "CVX"], "real_assets": ["VNQ", "DBC", "MSTR"], "bonds": ["TLT"]},
        "need_all": 4,
    },
    "ETF 23": {
        "path": ROOT / "data/etf/processed/prices_daily_clean.parquet",
        "F1": {"bonds": ["IEF", "TLT", "LQD", "TIP"], "gold": ["GLD"], "commodities": ["DBC", "USO"]},
        "F2": {"equity index": ["SPY", "QQQ", "IWM", "EFA", "EEM"],
               "sector": ["XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY"], "real estate": ["VNQ"]},
        "ALL": {"equity index": ["SPY", "QQQ", "IWM", "EFA", "EEM"],
                "sector": ["XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY"],
                "bond": ["IEF", "TLT", "LQD", "TIP"], "commodity": ["GLD", "DBC", "USO"], "real estate": ["VNQ"]},
        "need_all": 3,
    },
}
FAMILIES = {"F1 macro trend": ("F1", "pooled", ["trend"]),
            "F2 panic rebound": ("F2", "pooled", ["vix30", "log_vix"]),
            "F3 world regime": ("ALL", "per_group", WORLD7),
            "F4 combined": ("ALL", "per_group", ALL),
            "F5 boosted trees": ("ALL", "trees", ALL)}

raw = tdata.history()
WORLD = tdata.world_prices(raw)
GPR = tdata.gpr("daily")["GPRD_MA7"]


def world_features(idx: pd.DatetimeIndex) -> pd.DataFrame:
    w = WORLD.reindex(idx.union(WORLD.index)).ffill(limit=3).reindex(idx)
    pc = lambda s, d: s.pct_change(d, fill_method=None) * 100  # noqa: E731
    g = GPR.reindex(idx.union(GPR.index)).ffill().reindex(idx)
    return pd.DataFrame({
        "log_vix": np.log(w["^VIX"]), "vix30": (w["^VIX"] >= 30).astype(float),
        "curve": w["^TNX"] - w["^IRX"], "credit": pc(w["HYG"] / w["IEF"], 63),
        "cugold": pc(w["HG=F"] / w["GC=F"], 63), "oil63": pc(w["CL=F"], 63),
        "tipief": pc(w["TIP"] / w["IEF"], 63), "y10": w["^TNX"].diff(63), "gpr": np.log(g)}, index=idx)


def build_panel(prices: pd.DataFrame, groups: dict) -> pd.DataFrame:
    assets = [t for v in groups.values() for t in v]
    px = prices[assets]
    sig = ewma_vol(px.pct_change(fill_method=None))
    tz = trend_scores(px, sig)
    rev5 = (px / px.shift(5) - 1) / (sig * np.sqrt(5))
    wf = world_features(px.index)
    idx = px.index
    firsts = idx[np.r_[True, idx.month[1:] != idx.month[:-1]]]
    rows = []
    for d, nxt in zip(firsts[:-1], firsts[1:]):
        n = idx.get_loc(nxt) - idx.get_loc(d)
        wrow = wf.loc[d].to_dict()
        for g, ts in groups.items():
            for t in ts:
                p0, p1, s, tr = px.at[d, t], px.at[nxt, t], sig.at[d, t], tz.at[d, t]
                if not all(np.isfinite([p0, p1, s, tr])) or s <= 0:
                    continue
                r = p1 / p0 - 1
                rows.append({"date": d, "asset": t, "group": g, "trend": tr, "rev5": rev5.at[d, t], **wrow,
                             "ret": r, "z": r / (s * np.sqrt(n)), "y": int(r > 0)})
    return pd.DataFrame(rows)


def _std(tr: pd.DataFrame, te: pd.DataFrame, feats: list[str]):
    mu, sd = tr[feats].mean(), tr[feats].std().replace(0, 1)
    return ((tr[feats] - mu) / sd).fillna(0).to_numpy(), ((te[feats] - mu) / sd).fillna(0).to_numpy()


def logit(Xtr, ytr, Xte):
    if len(np.unique(ytr)) < 2:
        return np.full(len(Xte), ytr.mean())
    return LogisticRegression(C=C, max_iter=2000).fit(Xtr, ytr).predict_proba(Xte)[:, 1]


def walk(df: pd.DataFrame, kind: str, feats: list[str]) -> pd.DataFrame:
    months = np.sort(df["date"].unique())
    groups = sorted(df["group"].unique())
    out, tree, tree_year = [], None, None
    for m in months[MIN_TRAIN:]:
        tr, te = df[df["date"] < m], df[df["date"] == m].copy()
        if te.empty:
            continue
        base = tr.groupby("group")["y"].agg(lambda s: (s.sum() + 1) / (len(s) + 2))
        te["base"] = te["group"].map(base).fillna(0.5).to_numpy()
        if kind == "pooled":
            Xtr, Xte = _std(tr, te, feats)
            dtr = pd.get_dummies(tr["group"]).reindex(columns=groups, fill_value=0).to_numpy(float)
            dte = pd.get_dummies(te["group"]).reindex(columns=groups, fill_value=0).to_numpy(float)
            te["p"] = logit(np.c_[Xtr, dtr], tr["y"].to_numpy(), np.c_[Xte, dte])
        elif kind == "per_group":
            p = te["base"].to_numpy().copy()
            for g in te["group"].unique():
                trg, mask = tr[tr["group"] == g], (te["group"] == g).to_numpy()
                if len(trg) >= 24:
                    Xtr, Xte = _std(trg, te[mask], feats)
                    p[mask] = logit(Xtr, trg["y"].to_numpy(), Xte)
            te["p"] = p
        else:
            year = pd.Timestamp(m).year
            code = {g: i for i, g in enumerate(groups)}
            if tree is None or year != tree_year:
                X = np.c_[tr[feats].to_numpy(), tr["group"].map(code).to_numpy()]
                empty = np.isnan(X).all(axis=0)          # e.g. credit stress before HYG existed (2007)
                X[:, empty] = 0.0
                tree = HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05, max_iter=150,
                                                      l2_regularization=1.0, min_samples_leaf=50,
                                                      categorical_features=[len(feats)], random_state=0)
                tree.fit(X, tr["y"].to_numpy())
                tree_year = year
            Xte = np.c_[te[feats].to_numpy(), te["group"].map(code).to_numpy()]
            Xte[:, empty] = 0.0
            te["p"] = tree.predict_proba(Xte)[:, 1]
        out.append(te)
    return pd.concat(out)


def score(res: pd.DataFrame) -> dict:
    res = res.assign(bm=(res["p"] - res["y"]) ** 2, bb=(res["base"] - res["y"]) ** 2,
                     x=(res["p"] - res["base"]) * res["z"])
    by = res.groupby("date")
    d, x = by["bb"].mean() - by["bm"].mean(), by["x"].mean()
    tstat = lambda s: s.mean() / s.std() * np.sqrt(len(s)) if len(s) > 2 and s.std() > 0 else np.nan  # noqa: E731
    grp = res.groupby("group").apply(lambda g: 1 - g["bm"].sum() / g["bb"].sum())
    return {"brier_skill": 1 - res["bm"].sum() / res["bb"].sum(), "t_brier": tstat(d), "t_timing": tstat(x),
            "hit_rate": ((res["p"] > 0.5) == res["y"]).mean(), "always_long_hit": res["y"].mean(),
            "groups_positive": int((grp > 0).sum()), "n_groups": len(grp), "n_months": len(x),
            "group_skill": grp.round(4).to_dict()}


results, group_rows = [], []
for uname, u in UNIVERSES.items():
    px = pd.read_parquet(u["path"])
    px.index = pd.to_datetime(px.index)
    panels = {k: build_panel(px, u[k]) for k in ("F1", "F2", "ALL")}
    print(f"\n=== {uname}: {len(panels['ALL'])} asset-months, "
          f"{panels['ALL']['date'].min():%Y-%m} -> {panels['ALL']['date'].max():%Y-%m} ===", flush=True)
    for fam, (pkey, kind, feats) in FAMILIES.items():
        res = walk(panels[pkey], kind, feats)
        for per, mask in (("design", res["date"] <= DESIGN_END), ("HOLDOUT", res["date"] > DESIGN_END)):
            s = score(res[mask])
            need = 2 if pkey in ("F1", "F2") else u["need_all"]
            results.append({"universe": uname, "family": fam, "period": per, "need_groups": need,
                            **{k: v for k, v in s.items() if k != "group_skill"}})
            for g, v in s["group_skill"].items():
                group_rows.append({"universe": uname, "family": fam, "period": per, "group": g, "brier_skill": v})
        print(f"  done {fam}", flush=True)

R = pd.DataFrame(results).set_index(["universe", "family", "period"])
R["pass_1"] = (R["brier_skill"] > 0) & (R["t_timing"] >= 2)
R["pass_2"] = R["groups_positive"] >= R["need_groups"]
R.to_csv(TBL / "14_prediction_results.csv", float_format="%.4f")
pd.DataFrame(group_rows).to_csv(TBL / "14_prediction_groups.csv", index=False, float_format="%.4f")

pd.set_option("display.width", 200)
cols = ["brier_skill", "t_brier", "t_timing", "hit_rate", "always_long_hit", "groups_positive", "n_groups",
        "n_months", "pass_1", "pass_2"]
print("\n" + R[cols].round(4).to_string())
ho = R.xs("HOLDOUT", level="period")
verdict = (ho["pass_1"] & ho["pass_2"]).groupby(level="family").all()
print("\n=== PASS on HOLDOUT, both universes (rules 1+2) ===")
print(verdict.to_string())

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fams = list(FAMILIES)
for ax, metric, title in zip(axes, ["brier_skill", "t_timing"],
                             ["Brier skill vs base rate (>0 = better probabilities)", "Timing t-stat (pass needs >= 2)"]):
    for k, (uname, c) in enumerate([("PROJECT 20", "#4C78A8"), ("ETF 23", "#F58518")]):
        v = [ho.loc[(uname, f), metric] for f in fams]
        ax.barh(np.arange(len(fams)) + (k - 0.5) * 0.38, v, height=0.36, color=c, label=uname)
    ax.axvline(0, color="k", lw=0.8)
    if metric == "t_timing":
        ax.axvline(2, color="#E45756", ls="--", lw=1)
    ax.set_yticks(range(len(fams)), fams)
    ax.set_title(title)
    ax.grid(True, axis="x", ls=":", alpha=0.5)
    ax.legend(fontsize=8)
fig.suptitle("Phase 4B — prediction lab, HOLDOUT 2016-2026 (pre-registered test)")
fig.tight_layout()
fig.savefig(FIG / "14_g1_prediction_scores.png", dpi=130)
shutil.copy2(FIG / "14_g1_prediction_scores.png", VAULT / "14_g1_prediction_scores.png")
print("saved figure")
