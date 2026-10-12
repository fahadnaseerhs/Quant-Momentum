"""QM Terminal — live market terminal for the Quant Momentum Lab.

Run from the project folder:
    .venv/Scripts/python.exe -m streamlit run terminal/app.py

Plan and phases: Quant_Momentum/Product/QM Terminal - Plan.md
Layout only; numbers come from the engines (risk, allocate, world, alerts, news),
charts and plain-English statements from terminal/ui.py.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.universe import UNIVERSE  # noqa: E402
from terminal import allocate, alerts, data, news, risk, world  # noqa: E402
from terminal import ui  # noqa: E402
from terminal.ui import AMBER, CFG, DIM, DOWN, LINE, PLOT, STATUS_COLOR, UP, esc  # noqa: E402

st.set_page_config(page_title="Quant Momentum", page_icon="▣", layout="wide", initial_sidebar_state="collapsed")
st.markdown(f"<style>{(ROOT / 'terminal' / 'theme.css').read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
ENV = data.load_env()
A = data.ASSETS


def html(s: str):
    st.markdown(s, unsafe_allow_html=True)


# ---------------------------------------------------------------------- #
# Data + computations (cached)
#   history / world ........ 1 h      live quotes ...... 55 s
#   live market state ...... keyed on the live quotes (one EWMA pass per minute, shared by all tabs)
#   alerts, plan, ranges ... 5 min
# ---------------------------------------------------------------------- #

@st.cache_data(ttl=3600, show_spinner="Loading 20 years of prices…")
def load_static():
    raw = data.history()
    return data.asset_prices(raw), data.world_prices(raw), data.gpr("daily"), data.gpr("monthly")


@st.cache_data(ttl=55, show_spinner=False)
def load_live():
    return data.live_quotes(data.ASSETS + [data.BENCHMARK, "^VIX"])


@st.cache_data(ttl=600, max_entries=3, show_spinner=False)
def _market(live: pd.DataFrame):
    px, *_ = load_static()
    pxl = data.with_live(px, live)
    return pxl, risk.snapshot(pxl), risk.sigma_history(pxl)


def live_state():
    """(prices incl. live row, snapshot, EWMA sigma history, quote time) — computed once per new quote set."""
    live, ts = load_live()
    pxl, snap, sig = _market(live)
    return pxl, snap, sig, ts


@st.cache_data(ttl=3600, show_spinner=False)
def load_world(fred_key: str):
    px, w, gd, gm = load_static()
    g = world.build_gauges(w, gd, fred_key)
    books = {k: world.playbook(v["trigger"], px) for k, v in g.items()}
    return g, books, world.country_tension(gm), world.famous_crises(px)


@st.cache_data(ttl=1800, show_spinner="Reading the news…")
def load_news(api_key: str):
    df = news.headlines()
    ai = news.ai_briefing(df, api_key)
    return news.tagged(df, ai), ai


@st.cache_data(ttl=300, show_spinner=False)
def alert_feed():
    """One feed (last 60 trading days) for both the overview and the ALERTS tab."""
    pxl, *_ = live_state()
    g, *_ = load_world(ENV["FRED_API_KEY"])
    return alerts.merge(alerts.price_alerts(pxl, lookback=60), world.world_alerts(g, lookback=60), limit=300)


@st.cache_data(ttl=3600, show_spinner=False)
def load_z_bad():
    px, *_ = load_static()
    return allocate.live_z_bad(px[A], UNIVERSE)


@st.cache_data(ttl=300, show_spinner=False)
def plan_weights(profile: str, custom: tuple | None):
    pxl, _, sig, _ = live_state()
    rets = pxl[A].pct_change(fill_method=None)
    base = "BALANCED" if profile == "CUSTOM" else profile
    w, info = allocate.allocation(rets.iloc[-252:], sig[A].iloc[-1], UNIVERSE, base,
                                  dict(custom) if custom else None, load_z_bad())
    return w.reindex(A).fillna(0.0), info


@st.cache_data(ttl=300, show_spinner=False)
def plan_segments(profile: str, custom: tuple | None, days: int):
    pxl, *_ = live_state()
    _, info = plan_weights(profile, custom)
    return allocate.segment_table(pxl[A], UNIVERSE, info, 100.0, days)


@st.cache_data(ttl=300, show_spinner=False)
def plan_range(w: pd.Series, days: int):
    """Outcome range of the whole plan per $1 (ranges scale linearly with the amount) + monthly swing."""
    pxl, *_ = live_state()
    rng, mix_swing, _ = allocate.plan_outcome(pxl[A], w, 1.0, days)
    return rng, mix_swing


@st.cache_data(ttl=3600, show_spinner=False)
def asset_drift() -> float:
    """Universe-wide typical monthly move (step-1b fix for per-asset ranges)."""
    pxl, _, sig, _ = live_state()
    return risk.universe_drift(pxl[data.ASSETS], sig[data.ASSETS])


@st.cache_data(ttl=300, show_spinner=False)
def calc_ranges(days: int) -> pd.DataFrame:
    """Outcome range per $1 for every asset (verified method: drift shift + K_TYP)."""
    pxl, snap, sig, _ = live_state()
    rows, drift = [], asset_drift()
    for t, r in snap.iterrows():
        q = risk.z_quantiles(pxl[t].dropna(), sig[t].dropna(), days, drift=drift, k_typ=risk.K_TYP)
        o = risk.outcome_range(1.0, r["sigma"], q, days)
        rows.append({"name": data.name(t), "segment": data.SEGMENT_NAMES[r["bucket"]], "risk": r["level"],
                     "bad": o[0], "low": o[1], "high": o[3], "good": o[4]})
    return pd.DataFrame(rows).set_index("name")


# ---------------------------------------------------------------------- #
# Top bar + ticker tape (live)
# ---------------------------------------------------------------------- #

@st.fragment(run_every="60s")
def top_bar():
    pxl, snap, _, ts = live_state()
    g, *_ = load_world(ENV["FRED_API_KEY"])
    name, lvl = world.weather(g)[0]
    tape = "".join(f"<span class='it'><span class='amb'>{data.name(t)}</span> {ui.fmt_price(r['price'])} "
                   f"{ui.pct(r['day_pct'])}</span>" for t, r in snap.iterrows())
    html(f"<div class='qm-top'><span><b>QUANT MOMENTUM</b></span>"
         f"<span>WORLD: <span style='color:{STATUS_COLOR[lvl]}'>{name}</span></span>"
         f"<span class='dim'>{ts:%a %d %b %Y  %H:%M:%S} NY · <span class='qm-live'>● LIVE</span> "
         f"refresh 60s · stocks ~15 min delayed</span></div>"
         f"<div class='qm-tape'><div class='qm-tape-inner'>{tape}{tape}</div></div>")


top_bar()
tabs = st.tabs(["OVERVIEW", "PLAN", "CALCULATOR", "ASSET", "WORLD"])


# ---------------------------------------------------------------------- #
# OVERVIEW
# ---------------------------------------------------------------------- #

@st.fragment(run_every="60s")
def overview():
    pxl, snap, _, ts = live_state()
    g, books, ct, _ = load_world(ENV["FRED_API_KEY"])
    html(ui.say(ui.market_lines(snap) + ui.world_lines(g), "MARKETS & WORLD · NOW", f"{ts:%H:%M} NY"))

    left, mid, right = st.columns([1.2, 1.35, 1.2], gap="small")
    with left:
        html("".join(ui.bucket_panel(b, snap) for b in ("crypto", "tech", "gold")))
    with right:
        html("".join(ui.bucket_panel(b, snap) for b in ("oil", "real_assets", "bonds")))
    with mid:
        st.plotly_chart(ui.globe(ct), width="stretch", config=CFG)
        caption = (f"<div class='dim qm-caption'>Countries coloured by geopolitical tension vs "
                   f"their own history · {ct.attrs['month']:%b %Y} · drag to rotate</div>")
        tiles = []
        for key, label in (("fear", "FEAR"), ("recession", "RECESSION"), ("inflation", "INFLATION"), ("war", "WAR / TENSION")):
            s = int(g[key]["status"].iloc[-1])
            c0 = g[key]["components"][0]
            v = c0["series"].dropna()
            val = c0["fmt"].format(v.iloc[-1]) if len(v) else "n/a"
            on = sum(bool(c["flag"].iloc[-1]) for c in g[key]["components"])
            tiles.append(f"<div class='qm-g' style='border-top:2px solid {STATUS_COLOR[s]}'><div class='n'>{label}</div>"
                         f"<div class='s' style='color:{STATUS_COLOR[s]}'>{world.STATUS[s]}</div>"
                         f"<div class='dim'>{c0['label']}: <span class='amb'>{val}</span> · signals on {on}/{len(g[key]['components'])}</div></div>")
        html(f"<div class='qm-stack'>{caption}<div class='qm-gauges'>{''.join(tiles)}</div></div>")
        st.plotly_chart(ui.extremes_fig(snap), width="stretch", config=CFG)



with tabs[0]:
    overview()


# ---------------------------------------------------------------------- #
# PLAN — risk per segment, buy list by risk, holdings, weekly trade list
# ---------------------------------------------------------------------- #

with tabs[1]:
    pxl, snap, sig, _ = live_state()
    p_now = pxl[A].iloc[-1]
    swing_now = sig[A].iloc[-1] * np.sqrt(risk.MONTH) * 100
    port = allocate.load_portfolio()
    held = sum(port["shares"].get(t, 0.0) * p_now[t] for t in A) + port["cash"]

    profiles = ["CAREFUL", "BALANCED", "BOLD", "CUSTOM"]
    c1, c2, c3 = st.columns([1.4, 1, 1])
    profile = c1.radio("RISK PROFILE", profiles, horizontal=True,
                       index=profiles.index(port.get("profile", "BALANCED")))
    amount = c2.number_input("AMOUNT TO PLAN ($)", min_value=10.0, step=100.0,
                             value=float(round(held, 2)) if held > 0 else 1000.0)
    period = c3.selectbox("OUTCOME PERIOD", list(risk.PERIODS), index=0, key="plan_period")
    days = risk.PERIODS[period]
    custom, safe_extra = None, 0.0
    if profile == "CUSTOM":
        seg_list = list(allocate.segments(UNIVERSE))
        sc = st.columns(len(seg_list) + 1)
        custom = tuple((s, sc[i].slider(f"{data.SEGMENT_NAMES[s]} risk", 0.0, 3.0, 1.0, 0.25))
                       for i, s in enumerate(seg_list))
        safe_extra = sc[-1].slider("SAFE %", 0, 90, 0, 5) / 100
    base = "BALANCED" if profile == "CUSTOM" else profile
    w, info = plan_weights(profile, custom)
    if safe_extra:
        w = w * (1 - safe_extra)
        w[allocate.SAFE] += safe_extra
    seg = plan_segments(profile, custom, days)
    scale = 1 - safe_extra
    safe_share = w[allocate.SAFE]
    rng1, mix_swing = plan_range(w, days)
    rng = rng1 * amount
    bad_month = amount * (1 - plan_range(w, risk.MONTH)[0][0])

    today = pd.Timestamp.now(tz="America/New_York").normalize().tz_localize(None)
    tl = (allocate.trade_list(port["shares"], port["cash"], p_now, w, swing_now, port.get("swing_at_rebalance", {}))
          if held > 0 else None)

    # ---- statements ----
    rk = seg.sort_values("swing").iloc[-1]
    rk_name = ui.seg_title(seg.sort_values("swing").index[-1])
    if safe_share < 0.005:
        inv = "is <b>fully invested</b>"
    else:
        why = (f" so that a bad month stays under about {allocate.PROFILES[base]['bad_month']:.0%}"
               if profile != "CUSTOM" and info["invest"] < 1 else "")
        inv = (f"puts <b>${amount * (1 - safe_share):,.0f}</b> ({1 - safe_share:.0%}) into the segments and keeps "
               f"<b>${amount * safe_share:,.0f}</b> in the safe part{why}")
    lines = [f"Your <b>{profile}</b> plan for <b>${amount:,.0f}</b> {inv}.",
             f"A bad month (1 in 20) would cost about <span class='down'><b>${bad_month:,.0f}</b></span> "
             f"({bad_month / amount:.1%}); the whole plan swings about ±{mix_swing:.1f}% a month.",
             (f"After {period}: typical <b>${rng[1]:,.0f} – ${rng[3]:,.0f}</b> (2 in 3 cases); "
              f"bad case (1 in 20) <span class='down'>${rng[0]:,.0f}</span> · good case <span class='up'>${rng[4]:,.0f}</span>."
              if risk.VERIFIED["typical"] and risk.VERIFIED["good"] else
              f"After {period}, in a 1-in-20 bad case the plan would be worth about "
              f"<span class='down'><b>${rng[0]:,.0f}</b></span>."),
             f"<b>{rk_name}</b> is the stormiest segment (±{rk['swing']:.1f}% a month): it gets "
             f"{rk['money_share'] * scale:.0%} of the money and {rk['risk_share']:.0%} of the risk."]
    if tl is not None:
        n_tr = len(tl)
        lines.append(f"You hold <b>${held:,.2f}</b>. Weekly check: " +
                     (f"<span class='amb'>{n_tr} trade{'s' * (n_tr > 1)}</span> would bring it back to target."
                      if n_tr else "<span class='up'>nothing to trade</span>, every position is within "
                                   f"{allocate.BAND:.0%} of its target."))
    html(ui.say(lines, "YOUR PLAN", (allocate.PROFILES[base]["text"] if profile != "CUSTOM"
                                     else "your own risk shares per segment, plus an optional safe part")))

    # ---- 1. risk per segment ----
    html("<div class='qm-h' style='margin-top:4px'><span>1 · RISK PER SEGMENT</span>"
         "<span>hover a bar for the assets and the $100 bad case</span></div>")
    r1, r2 = st.columns(2, gap="small")
    r1.plotly_chart(ui.segment_risk_fig(seg, swing_now[allocate.SAFE], period), width="stretch", config=CFG)
    r2.plotly_chart(ui.share_fig(seg, scale, safe_share), width="stretch", config=CFG)

    # ---- 2. buy list ----
    buy = []
    for t in A:
        if w[t] <= 0:
            continue
        sgm = data.BUCKET_OF[t]
        lvl = risk.level(swing_now[t])
        if t == allocate.SAFE:
            why = "safe part of your plan"
        else:
            peers = [x for x in allocate.segments(UNIVERSE).get(sgm, []) if w.get(x, 0) > 0]
            bigger = swing_now[t] <= swing_now[peers].median()
            why = (f"{lvl.lower()} (±{swing_now[t]:.1f}%/month) → {'bigger' if bigger else 'smaller'} slice of "
                   f"{data.SEGMENT_NAMES[sgm].lower()}")
        buy.append({"ticker": t, "name": data.name(t),
                    "segment": "SAFE PART" if t == allocate.SAFE else data.SEGMENT_NAMES[sgm],
                    "level": lvl, "dollars": w[t] * amount, "shares": w[t] * amount / p_now[t],
                    "price": p_now[t], "pct": w[t] * 100, "why": why})
    buy_df = pd.DataFrame(buy).sort_values(["segment", "dollars"], ascending=[True, False])
    b1, b2 = st.columns([1.6, 1], gap="small")
    with b1:
        html("<div class='qm-h'><span>2 · BUY LIST (based on risk)</span><span>area = $ to buy · colour = risk · hover for shares</span></div>")
        st.plotly_chart(ui.buy_treemap(buy_df), width="stretch", config=CFG)
        with st.expander("Exact amounts as a list (for placing orders)"):
            html("".join(f"<div class='qm-alert'><span class='amb'>{esc(r['name'])}</span>"
                         f"<span class='txt'>${r['dollars']:,.2f} · {r['shares']:,.4f} shares · {r['pct']:.1f}%</span></div>"
                         for _, r in buy_df.iterrows()))
    with b2:
        corr = info["corr"].rename(index=data.SEGMENT_NAMES, columns=data.SEGMENT_NAMES)
        st.plotly_chart(ui.corr_fig(corr), width="stretch", config=CFG)

    # ---- 3. when to buy and sell (amount-based, plain steps) ----
    nxt = allocate.next_check(port.get("last_rebalance"), today)
    last = port.get("last_rebalance")
    n_buy = int((w > 0).sum())
    html("<div class='qm-h' style='margin-top:6px'><span>3 · WHEN TO BUY AND SELL</span>"
         f"<span>next check: {nxt:%a %d %b}</span></div>")
    if tl is None:
        html(ui.say([
            f"<b>Step 1 — buy now:</b> split your <b>${amount:,.0f}</b> exactly as the buy list above "
            f"({n_buy} assets; open <i>Exact amounts as a list</i> for each dollar amount).",
            "<b>Step 2 — tell the terminal:</b> press <b>I bought this plan</b>. It remembers what you hold "
            "(only on this computer).",
            f"<b>Step 3 — every Monday</b> (next: {nxt:%a %d %b}): come back here. It lists only the trades needed — "
            f"anything more than {allocate.BAND:.0%} away from its target — each with the reason. "
            "If markets turn stormy, part of the money moves to the safe part automatically."],
            "YOUR STEPS", f"${amount:,.0f} · {profile}"))
        if st.button(f"I bought this plan (${amount:,.0f})", type="primary"):
            port.update({"shares": {t: float(w[t] * amount / p_now[t]) for t in A if w[t] > 0}, "cash": 0.0,
                         "profile": profile, "last_rebalance": str(today.date()),
                         "swing_at_rebalance": {t: float(swing_now[t]) for t in A}})
            allocate.save_portfolio(port)
            st.rerun()
    else:
        due = last is None or (today - pd.Timestamp(last)).days >= 7 or today.weekday() == 0
        head = [f"You hold <b>${held:,.2f}</b> in {sum(v > 0 for v in port['shares'].values())} assets "
                f"(last check {last or 'never'}; next {nxt:%a %d %b})."]
        if tl.empty:
            head.append(f"<span class='up'>Nothing to do this week</span> — every position is within "
                        f"{allocate.BAND:.0%} of its target.")
        else:
            head.append(f"<span class='amb'>{len(tl)} trade{'s' * (len(tl) > 1)}</span> "
                        f"{'due now' if due else 'waiting for the Monday check'}:")
        html(ui.say(head, "YOUR HOLDINGS", profile))
        if not tl.empty:
            html("".join(ui.trade_card(r) for r in tl.sort_values("action", ascending=False).itertuples()))
        b1, b2 = st.columns([1, 1])
        if not tl.empty and b1.button("I made these trades", type="primary"):
            for r in tl.itertuples():
                sign = 1 if r.action == "BUY" else -1
                port["shares"][r.ticker] = max(0.0, port["shares"].get(r.ticker, 0.0) + sign * r.shares)
                port["cash"] = port["cash"] - sign * r.amount
            port.update({"cash": max(0.0, port["cash"]), "profile": profile, "last_rebalance": str(today.date()),
                         "swing_at_rebalance": {t: float(swing_now[t]) for t in A}})
            allocate.save_portfolio(port)
            st.rerun()
        if b2.button("Start over (keeps a backup)"):
            allocate.PORTFOLIO_FILE.rename(allocate.PORTFOLIO_FILE.with_name(
                f"portfolio_backup_{pd.Timestamp.now():%Y%m%d_%H%M%S}.json"))
            st.rerun()

    with st.expander("Advanced: edit my holdings by hand"):
        hold = pd.DataFrame({"ticker": A, "name": [data.name(t) for t in A],
                             "shares": [float(port["shares"].get(t, 0.0)) for t in A],
                             "price": [float(p_now[t]) for t in A]}).set_index("ticker")
        edited = st.data_editor(hold, disabled=["name", "price"], width="stretch", height=420,
                                column_config={"shares": st.column_config.NumberColumn(format="%.6f", min_value=0.0),
                                               "price": st.column_config.NumberColumn(format="$%.2f")})
        cash = st.number_input("Cash not invested ($)", min_value=0.0, value=float(port["cash"]), step=10.0)
        if st.button("Save my holdings"):
            port.update({"shares": {t: float(v) for t, v in edited["shares"].items() if v > 0},
                         "cash": cash, "profile": profile})
            allocate.save_portfolio(port)
            st.rerun()


# ---------------------------------------------------------------------- #
# CALCULATOR — one asset-by-asset range chart
# ---------------------------------------------------------------------- #

with tabs[2]:
    c1, c2, _ = st.columns([1, 1, 3])
    amount = c1.number_input("AMOUNT ($)", min_value=1.0, value=100.0, step=10.0)
    period = c2.selectbox("PERIOD", list(risk.PERIODS), index=0)
    days = risk.PERIODS[period]
    rng = calc_ranges(days).copy()
    rng[["bad", "low", "high", "good"]] *= amount
    loss = amount - rng["bad"]
    calm, storm = loss.idxmin(), loss.idxmax()
    lines = [f"${amount:,.0f} held for {period}: in a 1-in-20 bad case <span class='amb'>{esc(storm)}</span> "
             f"(the stormiest) would be worth <span class='down'><b>${rng.loc[storm, 'bad']:,.2f}</b></span>; "
             f"<span class='amb'>{esc(calm)}</span> (the calmest) <span class='down'><b>${rng.loc[calm, 'bad']:,.2f}</b></span>."]
    if risk.VERIFIED["typical"]:
        lines.append(f"In 2 of 3 cases {esc(calm)} ends between <b>${rng.loc[calm, 'low']:,.2f} – "
                     f"${rng.loc[calm, 'high']:,.2f}</b>; {esc(storm)} between <b>${rng.loc[storm, 'low']:,.2f} – "
                     f"${rng.loc[storm, 'high']:,.2f}</b>.")
    lines.append("Built from today's risk and each asset's own history of big moves; no asset is assumed to go up or down.")
    html(ui.say(lines, "BAD CASE (1 IN 20)" if not risk.VERIFIED["typical"] else "OUTCOME RANGES"))
    st.plotly_chart(ui.range_fig(rng, amount, period), width="stretch", config=CFG)


# ---------------------------------------------------------------------- #
# ASSET DETAIL
# ---------------------------------------------------------------------- #

with tabs[3]:
    pxl, snap, sig, _ = live_state()
    t = st.selectbox("ASSET", list(snap.index), index=list(snap.index).index("BTC-USD"), format_func=data.name)
    nm = data.name(t)
    r = snap.loc[t]
    p = pxl[t].dropna()
    s_ = sig[t].dropna()
    q = risk.z_quantiles(p, s_, risk.MONTH, drift=asset_drift(), k_typ=risk.K_TYP)
    prev = p[p.index < p.index[-1].replace(day=1)]
    mtd = (p.iloc[-1] / prev.iloc[-1] - 1) * 100 if len(prev) else np.nan
    calmer = r["swing"] <= r["usual_swing"]
    html(ui.say([
        f"<span class='amb'><b>{esc(nm)}</b></span> {ui.fmt_price(r['price'])} {ui.pct(r['day_pct'])} today · "
        f"{p.index[-1]:%B} so far {ui.pct(mtd, 1)} · segment {data.SEGMENT_NAMES[r['bucket']]}.",
        f"It is {ui.lvl_span(r['level'])}: a normal month swings <b>±{r['swing']:.1f}%</b>, "
        f"{'calmer' if calmer else 'stormier'} than its usual ±{r['usual_swing']:.1f}%.",
        f"In the past: {risk.trend_words(r) or 'not enough history'}."], "ASSET", nm.upper()))

    # 1. next month cone
    fig, end, lo, hi, bad = ui.cone_fig(p, float(r["sigma"]), q, nm)
    st.plotly_chart(fig, width="stretch", config=CFG)
    html(ui.explain(
        f"<b>What this means:</b> the blue line is {esc(nm)}'s price; the shaded cone is the next month. "
        f"<b>Most likely (2 in 3 chance): between ${lo:,.2f} and ${hi:,.2f} by {end:%d %b}.</b> "
        f"In a bad month (1 in 20) it could fall to about <span class='down'>${bad:,.2f}</span> or lower. "
        f"The cone's width comes from how much {esc(nm)} is swinging right now — it shows <i>how far</i> it can move, "
        f"not <i>which way</i> (a direction call failed every test we ran)."))

    h1, h2 = st.columns(2, gap="small")
    # 2. past months
    moves = risk.monthly_moves(p)
    band = (np.exp(q * r["sigma"] * np.sqrt(risk.MONTH)) - 1) * 100
    with h1:
        st.plotly_chart(ui.month_hist_fig(moves, band, nm), width="stretch", config=CFG)
        html(ui.explain(
            f"<b>What this means:</b> each bar counts past months by how much {esc(nm)} moved "
            f"(<span class='up'>green = up</span>, <span class='down'>red = down</span>; "
            f"{(moves > 0).mean():.0%} of its months were up). The blue band is where 2 in 3 months land at "
            f"<b>today's</b> risk ({band[1]:+.0f}% to {band[3]:+.0f}%); the red line is the bad case ({band[0]:+.0f}%). "
            f"A narrow band means a calm month ahead, a wide one a stormy month."))
    # 3. risk now vs usual
    sw = s_ * np.sqrt(risk.MONTH) * 100
    with h2:
        st.plotly_chart(ui.risk_zoom_fig(sw, float(r["usual_swing"]), nm), width="stretch", config=CFG)
        html(ui.explain(
            f"<b>What this means:</b> how big {esc(nm)}'s monthly moves are expected to be, over the last 2 years. "
            f"Today ±{r['swing']:.1f}% — <span class='{'up' if calmer else 'down'}'>"
            f"{'calmer' if calmer else 'stormier'} than its usual ±{r['usual_swing']:.1f}%</span>. "
            f"When this line rises, expect bigger moves in either direction — and the PLAN tab gives it less money."))


# ---------------------------------------------------------------------- #
# WORLD
# ---------------------------------------------------------------------- #

with tabs[4]:
    g, books, ct, famous = load_world(ENV["FRED_API_KEY"])
    tc = ct.sort_values("pct", ascending=False).iloc[0]
    html(ui.say(ui.world_lines(g) + [
        f"Most tense country vs its own history: <span class='amb'>{esc(tc['country'])}</span> "
        f"({ui.ordinal(tc['pct'])} percentile, {ct.attrs['month']:%b %Y})."], "WORLD"))
    gl, gr = st.columns([1, 1.2])
    with gl:
        st.plotly_chart(ui.globe(ct, 470), width="stretch", config=CFG)
        st.plotly_chart(ui.tension_fig(ct), width="stretch", config=CFG)
    with gr:
        for key, label in (("fear", "FEAR"), ("recession", "RECESSION / GROWTH SCARE"),
                           ("inflation", "INFLATION"), ("war", "WAR / GEOPOLITICAL TENSION")):
            s_ = int(g[key]["status"].iloc[-1])
            rows = "".join(
                f"<tr><td>{c['label']}</td><td class='r amb'>"
                f"{c['fmt'].format(c['series'].dropna().iloc[-1]) if c['series'].notna().any() else 'n/a'}</td>"
                f"<td style='color:{DOWN if bool(c['flag'].iloc[-1]) else UP}'>{'SIGNAL ON' if bool(c['flag'].iloc[-1]) else 'normal'}</td></tr>"
                for c in g[key]["components"])
            html(f"<div class='qm-panel'><div class='qm-h'><span>{label}</span>"
                 f"<span class='tag' style='background:{STATUS_COLOR[s_]}'>{world.STATUS[s_]}</span></div>"
                 f"<div class='qm-body'><table class='qm-t'>{rows}</table></div></div>")
        c0 = g["war"]["components"][0]["series"].dropna().loc["2019":]
        fw = ui.line_fig(c0, "War-tension index (7-day average) since 2019", height=230, hover="%{y:.0f}")
        for y, n in ((world.GPR_ELEVATED, "elevated"), (world.GPR_ALARM, "alarm")):
            fw.add_hline(y=y, line_color=DOWN if n == "alarm" else AMBER, line_dash="dot", annotation_text=n,
                          annotation_position="top left")
        st.plotly_chart(fw, width="stretch", config=CFG)

    st.markdown("#### LAST TIMES IT LOOKED LIKE THIS")
    st.caption("Every past episode since 2004 when each signal switched on, and what each segment did next: "
               "median move and how many times it was up. History, not a forecast.")
    pcols = st.columns(2)
    for i, (key, label) in enumerate((("war", "WAR / TENSION"), ("recession", "RECESSION / GROWTH SCARE"),
                                      ("inflation", "INFLATION"), ("fear", "FEAR / PANIC"))):
        pb, starts = books[key]
        active = int(g[key]["status"].iloc[-1]) > 0
        with pcols[i % 2]:
            html(f"<div class='qm-h' style='margin-top:6px'><span>{label} · {g[key]['trigger_text']}</span>"
                 f"<span>{'ACTIVE NOW' if active else ''}</span></div>")
            if starts and "S&P 500" in pb.index and np.isfinite(pb.loc["S&P 500", "median 3M"]):
                spx = pb.loc["S&P 500"]
                html(f"<div class='qm-note'>{len(starts)} past episodes. Over the next 3 months the S&amp;P 500 "
                     f"was up in {spx['up 3M']} (median {spx['median 3M']:+.1f}%).</div>")
                st.plotly_chart(ui.playbook_fig(pb), width="stretch", config=CFG)
                st.caption("Episodes: " + ", ".join(f"{d:%b %Y}" for d in starts))
            else:
                st.caption("No past episodes with enough history after them.")
    st.markdown("#### HOW THE SEGMENTS BEHAVED IN FAMOUS CRISES")
    st.plotly_chart(ui.famous_heatmap(famous), width="stretch", config=CFG)
    st.caption("Average % move of each segment from the start to the end of each crisis. "
               "Bonds protected in the depression scare and the Covid crash but fell in the 2022 inflation shock, "
               "when oil soared. The type of crisis mattered more than its size.")
