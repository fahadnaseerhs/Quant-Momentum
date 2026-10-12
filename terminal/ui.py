"""QM Terminal — presentation helpers: HTML snippets, Plotly charts, plain-English statements.

Pure presentation. Every number comes from the engines (risk, allocate, world,
alerts); this module only formats them. Statements DESCRIBE the data (what is,
what happened) and never say what will happen.
"""
from __future__ import annotations

import html as _h

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from terminal import data, risk, world

AMBER, UP, DOWN, DIM, LINE, BLUE, TXT = "#FFA028", "#19D27F", "#FF433D", "#8A8A8A", "#262626", "#3A8DFF", "#E6E6E6"
GRID = "#1a1a1a"
STATUS_COLOR = {0: UP, 1: AMBER, 2: DOWN}
# chart data colours: green = up / good, red = down / bad, blue = neutral lines, black background
TENSION_SCALE = [[0, "#06101f"], [0.45, "#1d4f91"], [0.75, "#3A8DFF"], [1, "#FF433D"]]
SEVERITY = {2: ("HIGH", DOWN), 1: ("NOTE", AMBER), 0: ("EASING", UP)}
PLOT = dict(paper_bgcolor="#000", plot_bgcolor="#000", margin=dict(l=40, r=10, t=30, b=30),
            font=dict(family="IBM Plex Mono, Consolas, monospace", color=TXT, size=11),
            hoverlabel=dict(bgcolor="#111", bordercolor=AMBER, font=dict(family="IBM Plex Mono, monospace", size=12)))
CFG = {"displayModeBar": False}
LEGEND_TOP = dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0, font=dict(size=11),
                  bgcolor="rgba(0,0,0,0)")


# ---------------------------------------------------------------------- #
# Formatting
# ---------------------------------------------------------------------- #

def esc(s) -> str:
    return _h.escape(str(s))


def fmt_price(p: float) -> str:
    return f"{p:,.2f}" if p >= 100 else f"{p:.2f}" if p >= 1 else f"{p:.4f}"


def money(v: float) -> str:
    return f"${v:,.0f}" if abs(v) >= 100 else f"${v:,.2f}"


def pct(v: float, d: int = 2) -> str:
    if not np.isfinite(v):
        return "<span class='dim'>—</span>"
    return f"<span class='{'up' if v >= 0 else 'down'}'>{v:+.{d}f}%</span>"


def ordinal(v: float) -> str:
    n = int(round(v))
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def lvl_span(level: str) -> str:
    return f"<span style='color:{risk.LEVEL_COLOR[level]}'>{level.lower()}</span>"


def seg_title(s: str) -> str:
    return data.SEGMENT_NAMES.get(s, s).title()


# ---------------------------------------------------------------------- #
# Statement box (top of every tab)
# ---------------------------------------------------------------------- #

def say(lines: list[str], title: str = "AT A GLANCE", right: str = "") -> str:
    items = "".join(f"<li>{ln}</li>" for ln in lines if ln)
    return (f"<div class='qm-say'><div class='k'><span>{title}</span><span>{right}</span></div>"
            f"<ul>{items}</ul></div>")


def segment_swing(snap: pd.DataFrame) -> pd.Series:
    """Median monthly swing per segment (same number the overview panels use for their level)."""
    return snap.groupby("bucket")["swing"].median().sort_values()


def market_lines(snap: pd.DataFrame) -> list[str]:
    med = snap["swing"].median()
    lv = risk.level(med)
    counts = snap["level"].value_counts()
    parts = ", ".join(f"{counts[k]} {lvl_span(k)}" for k in ("STORMY", "LIVELY", "CALM", "VERY CALM") if k in counts)
    seg = segment_swing(snap)
    hi, lo = seg.index[-1], seg.index[0]
    above = int((snap["swing"] > snap["usual_swing"]).sum())
    out = [f"Markets are {lvl_span(lv)} overall: the typical asset swings <b>±{med:.1f}%</b> a month ({parts}).",
           f"<b>{seg_title(hi)}</b> is the stormiest segment (±{seg[hi]:.1f}% a month); "
           f"<b>{seg_title(lo)}</b> the calmest (±{seg[lo]:.1f}%).",
           f"{above} of {len(snap)} assets are swinging more than they usually do."]
    k = snap["day_sigmas"].abs().dropna()
    if len(k):
        t = k.idxmax()
        r = snap.loc[t]
        out.append(f"Biggest move today: <span class='amb'>{esc(data.name(t))}</span> {pct(r['day_pct'], 1)} "
                   f"({abs(r['day_sigmas']):.1f}x a normal day).")
    return out


GAUGE_WORD = {"war": "War tension", "fear": "Fear", "recession": "Recession risk", "inflation": "Inflation pressure"}


def gauge_line(key: str, g: dict) -> str:
    """One factual sentence for an active gauge (status > 0)."""
    s = int(g["status"].iloc[-1])
    word = f"<span style='color:{STATUS_COLOR[s]}'>{'at alarm' if s == 2 else 'rising'}</span>"
    comps = g["components"]
    if key == "war":
        v = comps[0]["series"].dropna()
        if len(v) and v.iloc[-1] >= world.GPR_ELEVATED:
            x = v.iloc[-1]
            top = "3%" if x >= world.GPR_ALARM else "5%" if x >= world.GPR_TOP5 else "10%"
            return (f"World: war tension is {word} — the index is at <b>{x:.0f}</b>, "
                    f"in its top {top} since 1985.")
    on = [c for c in comps if bool(c["flag"].iloc[-1])] or comps[:1]
    facts = "; ".join(f"{c['label']} <b>{c['fmt'].format(c['series'].dropna().iloc[-1])}</b>"
                      for c in on if c["series"].notna().any())
    return f"World: {GAUGE_WORD[key].lower()} is {word} — {facts}."


def world_lines(gauges: dict) -> list[str]:
    order = ("war", "fear", "recession", "inflation")
    active = [k for k in order if int(gauges[k]["status"].iloc[-1]) > 0]
    out = [gauge_line(k, gauges[k]) for k in sorted(active, key=lambda k: -int(gauges[k]["status"].iloc[-1]))]
    calm = [GAUGE_WORD[k].lower() for k in order if k not in active]
    if calm:
        out.append(("World: " if not active else "") + ", ".join(calm).capitalize()
                   + (" is" if len(calm) == 1 else " are") + " <span class='up'>normal</span>.")
    return out


# ---------------------------------------------------------------------- #
# Alerts
# ---------------------------------------------------------------------- #

def sev_pill(level: int) -> str:
    lab, c = SEVERITY[int(level)]
    return f"<span class='qm-sev' style='color:{c};border-color:{c}'>{lab}</span>"


def alert_row(a, date: bool = True) -> str:
    c = SEVERITY[int(a["level"])][1]
    d = f"<span class='dim'>{pd.Timestamp(a['date']):%d %b}</span>" if date else ""
    return (f"<div class='qm-alert' style='border-left-color:{c}'>{d}{sev_pill(a['level'])}"
            f"<span class='qm-pill'>{esc(a['source'])}</span><span class='txt'>{esc(a['text'])}</span></div>")


def top_alerts(feed: pd.DataFrame, n: int = 3, days: int = 7) -> pd.DataFrame:
    """The newest most-important alerts: highest severity first, then newest, from the last `days` days."""
    if feed.empty:
        return feed
    d = pd.to_datetime(feed["date"])
    recent = feed[d >= d.max() - pd.Timedelta(days=days)]
    top = recent.assign(_d=pd.to_datetime(recent["date"])).sort_values(
        ["level", "_d"], ascending=[False, False]).head(n).drop(columns="_d")
    if len(top) < n:                                  # quiet week: fill with the newest older alerts
        top = pd.concat([top, feed.drop(index=top.index).head(n - len(top))])
    return top


def headline_lines(top: pd.DataFrame) -> list[str]:
    return [f"{sev_pill(a['level'])} <span class='dim'>{pd.Timestamp(a['date']):%a %d %b}</span> · {esc(a['text'])}"
            for _, a in top.iterrows()]


def alerts_by_day(df: pd.DataFrame) -> str:
    if df.empty:
        return "<div class='dim'>No alerts for this filter.</div>"
    out = []
    d = pd.to_datetime(df["date"]).dt.normalize()
    for day, grp in df.groupby(d, sort=False):
        n_hi = int((grp["level"] == 2).sum())
        out.append(f"<div class='qm-day'><span>{day:%A %d %b %Y}</span><span>{len(grp)} alert{'s' * (len(grp) > 1)}"
                   f"{f' · {n_hi} high' if n_hi else ''}</span></div>")
        out.extend(alert_row(a, date=False) for _, a in grp.sort_values("level", ascending=False).iterrows())
    return "".join(out)


# ---------------------------------------------------------------------- #
# Panels (overview)
# ---------------------------------------------------------------------- #

def bucket_panel(bucket: str, snap: pd.DataFrame) -> str:
    rows = snap[snap["bucket"] == bucket]
    if rows.empty:
        return ""
    lvl = risk.level(rows["swing"].median())
    head = (f"<div class='qm-h'><span>{data.SEGMENT_NAMES[bucket]}</span>"
            f"<span class='tag' style='background:{risk.LEVEL_COLOR[lvl]}'>{lvl}</span></div>")
    body = ["<table class='qm-t'><tr><th>NAME</th><th class='r'>LAST</th><th class='r'>DAY</th>"
            "<th title='expected swing over the next month'>SWING</th><th class='r'>±</th><th>RISK</th>"
            "<th class='c' title='trend over the past months'>TR</th></tr>"]
    for t, r in rows.sort_values("swing", ascending=False).iterrows():
        col = risk.LEVEL_COLOR[r["level"]]
        w = min(100, r["swing"] / 25 * 100)
        u = min(100, r["usual_swing"] / 25 * 100)
        body.append(
            f"<tr><td class='amb nm'>{data.name(t)}</td><td class='r'>{fmt_price(r['price'])}</td>"
            f"<td class='r'>{pct(r['day_pct'])}</td>"
            f"<td class='barcell'><div class='qm-bar' title='white tick = its usual level'><i style='width:{w:.0f}%;background:{col}'></i>"
            f"<u style='left:{u:.0f}%'></u></div></td>"
            f"<td class='r'>{r['swing']:.1f}%</td><td style='color:{col}'>{r['level']}</td>"
            f"<td class='c {'up' if r['trend_z'] > 0.3 else 'down' if r['trend_z'] < -0.3 else 'dim'}'>{r['trend']}</td></tr>")
    body.append("</table>")
    return f"<div class='qm-panel'>{head}<div class='qm-body qm-scroll'>{''.join(body)}</div></div>"


def news_items(nd: pd.DataFrame, n: int | None = None, tags: bool = False) -> str:
    """Headlines as clickable cards that open the original article in a new tab."""
    out = []
    for r in (nd if n is None else nd.head(n)).itertuples():
        when = f"{r.time.tz_convert('America/New_York'):%d %b %H:%M}" if pd.notna(r.time) else ""
        segs = "".join(f"<span class='qm-pill'>{esc(b.upper().replace('_', ' '))}</span>"
                       for b in (r.buckets or [])) if tags else ""
        link = _h.escape(r.link or "#", quote=True)
        out.append(f"<a class='qm-news' href='{link}' target='_blank' rel='noopener noreferrer'>"
                   f"<div class='t'>{esc(r.title)}</div>"
                   f"<div class='meta'><span class='qm-pill'>{esc(r.theme.upper())}</span>{segs}"
                   f"<span>{esc(r.source)}{' · ' + when if when else ''}</span></div></a>")
    return "".join(out) or "<div class='dim'>No headlines right now.</div>"


def trade_card(r) -> str:
    """One weekly-check trade as a sentence: 'SELL $5.53 of Bitcoin — it is 40% above its target.'"""
    nm = esc(data.name(r.ticker))
    col = UP if r.action == "BUY" else DOWN
    if r.now <= 0 or r.target <= 0:
        gap = esc(r.why)
        why = ""
    else:
        d = (r.now / r.target - 1) * 100
        gap = f"it is {abs(d):.0f}% {'above' if d > 0 else 'below'} its target"
        why = f" · {esc(r.why)}"
    return (f"<div class='qm-card' style='border-left-color:{col}'>"
            f"<div class='t'><b style='color:{col}'>{r.action}</b> <b>${r.amount:,.2f}</b> of "
            f"<span class='amb'>{nm}</span> — {gap}.</div>"
            f"<div class='dim'>≈ {r.shares:,.4f} shares · holding ${r.now:,.2f} → target ${r.target:,.2f}{why}</div></div>")


# ---------------------------------------------------------------------- #
# Charts
# ---------------------------------------------------------------------- #

def _base(fig: go.Figure, height: int, title: str | None = None, **kw) -> go.Figure:
    lay = {**PLOT, "height": height, **kw}
    if title:
        lay["title"] = dict(text=title, font=dict(size=13, color=AMBER), x=0, xanchor="left")
    fig.update_layout(**lay)
    return fig


def globe(ct: pd.DataFrame, height: int = 380) -> go.Figure:
    fig = go.Figure(go.Choropleth(
        locations=ct["iso3"], z=ct["pct"], zmin=0, zmax=100,
        colorscale=TENSION_SCALE,
        marker_line_color="#3a3a3a", marker_line_width=0.4,
        text=ct["country"], customdata=ct["level"],
        hovertemplate="<b>%{text}</b><br>tension vs its own history: %{z:.0f}th percentile<extra></extra>",
        colorbar=dict(title=dict(text="TENSION<br>pct", font=dict(size=10)), thickness=8, len=0.6,
                      tickfont=dict(size=9), outlinewidth=0)))
    fig.update_geos(projection_type="orthographic", projection_rotation=dict(lon=35, lat=25),
                    showocean=True, oceancolor="#020812", showland=True, landcolor="#141414",
                    showcountries=True, countrycolor="#2e2e2e", showcoastlines=True, coastlinecolor="#3a3a3a",
                    showframe=False, bgcolor="#000", lataxis_showgrid=True, lonaxis_showgrid=True,
                    lataxis_gridcolor="#101820", lonaxis_gridcolor="#101820")
    return _base(fig, height, margin=dict(l=0, r=0, t=0, b=0))


def extremes_fig(snap: pd.DataFrame, n: int = 4) -> go.Figure:
    """Stormiest and calmest assets as one bar chart (swing per month)."""
    ex = snap.sort_values("swing")
    pick = pd.concat([ex.head(n), ex.tail(n)])
    names = [data.name(t) for t in pick.index]
    fig = go.Figure(go.Bar(
        y=names, x=pick["swing"], orientation="h", marker_color=[risk.LEVEL_COLOR[v] for v in pick["level"]],
        text=[f"±{v:.1f}%" for v in pick["swing"]], textposition="outside", cliponaxis=False,
        textfont=dict(color=TXT, size=11), customdata=pick["level"],
        hovertemplate="<b>%{y}</b><br>%{customdata}: a normal month swings ±%{x:.1f}%<extra></extra>"))
    fig.add_hline(y=n - 0.5, line_color=LINE, line_dash="dot")
    return _base(fig, 250, "EXTREMES · SWING PER MONTH (calmest ↓ stormiest ↑)",
                 margin=dict(l=10, r=50, t=30, b=10), bargap=0.25,
                 xaxis=dict(visible=False, range=[0, pick["swing"].max() * 1.2]),
                 yaxis=dict(automargin=True, tickfont=dict(color=AMBER)))


def range_fig(rng: pd.DataFrame, amount: float, period: str) -> go.Figure:
    if not risk.VERIFIED["typical"]:
        return bad_case_fig(rng, amount, period)
    show_good = risk.VERIFIED["good"]
    fig = go.Figure()
    for t, r in rng.iterrows():
        col = risk.LEVEL_COLOR[r["risk"]]
        fig.add_trace(go.Scatter(x=[r["bad"], r["good"] if show_good else r["low"]], y=[t, t], mode="lines",
                                 line=dict(color=col, width=3), opacity=0.45, showlegend=False, hoverinfo="skip"))
        good_txt = f" · good (1 in 20) ${r['good']:,.2f}" if show_good else ""
        fig.add_trace(go.Scatter(
            x=[r["low"], r["high"]], y=[t, t], mode="lines", line=dict(color=col, width=11), showlegend=False,
            hovertemplate=(f"<b>{t}</b> · {r['segment']} · {r['risk'].lower()}<br>"
                           f"typical (2 in 3) ${r['low']:,.2f} – ${r['high']:,.2f}<br>"
                           f"bad case (1 in 20) ${r['bad']:,.2f}{good_txt}<extra></extra>")))
    for lv, c in risk.LEVEL_COLOR.items():                     # legend for the level colours
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="lines", line=dict(color=c, width=8), name=lv.lower()))
    fig.add_vline(x=amount, line_color=DIM, line_dash="dot")
    return _base(fig, 620, f"${amount:,.0f} held for {period}: where it could end up",
                 margin=dict(l=10, r=10, t=60, b=40), legend=LEGEND_TOP,
                 xaxis=dict(title="$ value at the end (thick = typical, 2 in 3 · thin = down to the 1-in-20 bad case)",
                            gridcolor=GRID, tickprefix="$"),
                 yaxis=dict(gridcolor="#111", automargin=True))


def bad_case_fig(rng: pd.DataFrame, amount: float, period: str) -> go.Figure:
    """Verified numbers only: how much each asset could lose in a 1-in-20 bad case."""
    r_ = rng.sort_values("bad")
    fig = go.Figure()
    for t, r in r_.iterrows():
        col = risk.LEVEL_COLOR[r["risk"]]
        fig.add_trace(go.Scatter(
            x=[r["bad"], amount], y=[t, t], mode="lines+markers", line=dict(color=col, width=9),
            marker=dict(size=[9, 0], color=col), showlegend=False,
            hovertemplate=(f"<b>{t}</b> · {r['segment']} · {r['risk'].lower()}<br>"
                           f"bad case (1 in 20): ${r['bad']:,.2f} (−${amount - r['bad']:,.2f})<extra></extra>")))
    for lv, c in risk.LEVEL_COLOR.items():
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="lines", line=dict(color=c, width=8), name=lv.lower()))
    fig.add_vline(x=amount, line_color=DIM, line_dash="dot")
    return _base(fig, 620, f"${amount:,.0f} held for {period}: how low it could go in a 1-in-20 bad case",
                 margin=dict(l=10, r=10, t=60, b=40), legend=LEGEND_TOP,
                 xaxis=dict(title="$ value at the end in the bad case (bar = possible loss)", gridcolor=GRID,
                            tickprefix="$"),
                 yaxis=dict(gridcolor="#111", automargin=True))


def segment_risk_fig(seg: pd.DataFrame, safe_swing: float, period: str) -> go.Figure:
    """Swing per month per segment, coloured by level; $100 bad case on hover."""
    s = seg.sort_values("swing")
    names = [seg_title(x) for x in s.index]
    up = (lambda r: f" → good ${r['good']:.0f}") if risk.VERIFIED["good"] else (lambda r: "")
    hover = [f"{', '.join(data.name(t) for t in r['assets'])}<br>riskier than {r['vs_history_pct']:.0f}% of its own history"
             f"<br>$100 after {period}: bad case ${r['bad']:.0f}{up(r)}" for _, r in s.iterrows()]
    y = ["Safe part"] + names
    x = [safe_swing] + list(s["swing"])
    lv = ["VERY CALM"] + list(s["level"])
    hover = [f"{data.name('SHY')}"] + hover
    fig = go.Figure(go.Bar(
        y=y, x=x, orientation="h", marker_color=[risk.LEVEL_COLOR[v] for v in lv],
        text=[f"±{v:.1f}%  {l.lower()}" for v, l in zip(x, lv)], textposition="outside", cliponaxis=False,
        textfont=dict(color=TXT), customdata=hover,
        hovertemplate="<b>%{y}</b> · ±%{x:.1f}% a month<br>%{customdata}<extra></extra>"))
    return _base(fig, 60 + 36 * len(y), "Swing per month, each segment",
                 margin=dict(l=10, r=110, t=30, b=10), bargap=0.3,
                 xaxis=dict(visible=False, range=[0, max(x) * 1.15]),
                 yaxis=dict(automargin=True, tickfont=dict(color=AMBER)))


def share_fig(seg: pd.DataFrame, scale: float, safe_share: float) -> go.Figure:
    """Money share vs risk share per segment (grouped bars, one axis in %)."""
    s = seg.sort_values("swing")
    y = ["Safe part"] + [seg_title(x) for x in s.index]
    money_ = [safe_share * 100] + list(s["money_share"] * scale * 100)
    risk_ = [0.0] + list(s["risk_share"] * 100)
    fig = go.Figure()
    fig.add_trace(go.Bar(y=y, x=money_, orientation="h", name="share of money", marker_color=UP,
                         text=[f"{v:.0f}%" for v in money_], textposition="outside", cliponaxis=False,
                         textfont=dict(color=TXT, size=10),
                         hovertemplate="<b>%{y}</b><br>%{x:.1f}% of the money<extra></extra>"))
    fig.add_trace(go.Bar(y=y, x=risk_, orientation="h", name="share of risk", marker_color=BLUE,
                         text=["—"] + [f"{v:.0f}%" for v in risk_[1:]], textposition="outside", cliponaxis=False,
                         textfont=dict(color=TXT, size=10),
                         hovertemplate="<b>%{y}</b><br>%{x:.1f}% of the plan's ups and downs<extra></extra>"))
    return _base(fig, 60 + 36 * len(y), "Money vs risk, each segment",
                 margin=dict(l=10, r=40, t=50, b=10), barmode="group", bargap=0.25, bargroupgap=0.08,
                 legend=LEGEND_TOP, xaxis=dict(visible=False, range=[0, max(money_ + risk_) * 1.18]),
                 yaxis=dict(automargin=True, tickfont=dict(color=AMBER)))


def buy_treemap(buy: pd.DataFrame) -> go.Figure:
    """Buy list as a treemap: segment → asset, area = $ to buy, colour = risk level. Exact $/shares on hover."""
    ids, labels, parents, values, colors, text, hover, ink = [], [], [], [], [], [], [], []
    for sg, grp in buy.groupby("segment", sort=False):
        tot = grp["dollars"].sum()
        ids.append(f"s:{sg}"); labels.append(sg); parents.append(""); values.append(tot)
        colors.append("#0d0d0d"); ink.append(AMBER); text.append(f"${tot:,.2f} · {grp['pct'].sum():.1f}%")
        hover.append(f"<b>{sg}</b><br>${tot:,.2f} · {grp['pct'].sum():.1f}% of the plan")
        for _, r in grp.iterrows():
            ids.append(f"a:{r['ticker']}"); labels.append(r["name"]); parents.append(f"s:{sg}")
            values.append(r["dollars"]); colors.append(risk.LEVEL_COLOR[r["level"]]); ink.append("#000")
            text.append(f"${r['dollars']:,.2f}")
            hover.append(f"<b>{esc(r['name'])}</b> · {sg}<br>buy <b>${r['dollars']:,.2f}</b> = {r['shares']:,.4f} shares"
                         f" at ${r['price']:,.2f}<br>{r['pct']:.1f}% of the plan<br>{esc(r['why'])}")
    fig = go.Figure(go.Treemap(
        ids=ids, labels=labels, parents=parents, values=values, branchvalues="total",
        marker=dict(colors=colors, line=dict(color="#000", width=2)), text=text, customdata=hover,
        texttemplate="<b>%{label}</b><br>%{text}", hovertemplate="%{customdata}<extra></extra>",
        textfont=dict(family="IBM Plex Mono, monospace", color=ink, size=12),
        outsidetextfont=dict(color=AMBER), pathbar=dict(visible=False), tiling=dict(pad=2)))
    return _base(fig, 430, margin=dict(l=0, r=0, t=4, b=0))


def corr_fig(corr: pd.DataFrame) -> go.Figure:
    fig = go.Figure(go.Heatmap(z=corr.values, x=corr.columns, y=corr.index, zmin=-1, zmax=1,
                               colorscale=[[0, BLUE], [0.5, "#111111"], [1, DOWN]],
                               text=np.round(corr.values, 2), texttemplate="%{text}", showscale=False,
                               hovertemplate="%{y} vs %{x}: %{z:.2f}<extra></extra>"))
    return _base(fig, 280, "Which segments moved together (last year)", margin=dict(l=10, r=10, t=30, b=10))


def playbook_fig(pb: pd.DataFrame) -> go.Figure:
    """Median move after past episodes, 1M and 3M, with 'up N of M' labels."""
    y = [s.title() if s != "S&P 500" else s for s in pb.index][::-1]
    fig = go.Figure()
    for lab, op in (("1M", 1.0), ("3M", 0.5)):
        v = pb[f"median {lab}"][::-1]
        ups = pb[f"up {lab}"][::-1]
        fig.add_trace(go.Bar(
            y=y, x=v, orientation="h", name=f"next {'1 month' if lab == '1M' else '3 months'} (lighter)" if op < 1
            else "next 1 month", marker_color=[UP if x >= 0 else DOWN for x in v], opacity=op,
            text=[f"{x:+.1f}% · up {u}" if np.isfinite(x) else "—" for x, u in zip(v, ups)],
            textposition="outside", cliponaxis=False, textfont=dict(color=TXT, size=10),
            customdata=list(ups),
            hovertemplate=f"<b>%{{y}}</b> · next {lab}<br>median move %{{x:+.1f}}%<br>up in %{{customdata}} episodes<extra></extra>"))
    m = np.nanmax(np.abs(pb[["median 1M", "median 3M"]].to_numpy(dtype=float))) if pb.size else 1
    m = m if np.isfinite(m) and m > 0 else 1
    fig.add_vline(x=0, line_color=DIM, line_width=1)
    return _base(fig, 330, margin=dict(l=10, r=10, t=30, b=10), barmode="group", bargap=0.22, bargroupgap=0.06,
                 legend=LEGEND_TOP, xaxis=dict(range=[-m * 1.9, m * 1.9], gridcolor=GRID, ticksuffix="%", zeroline=False),
                 yaxis=dict(automargin=True, tickfont=dict(color=AMBER)))


def famous_heatmap(famous: pd.DataFrame) -> go.Figure:
    z = famous.to_numpy(dtype=float)
    m = np.nanmax(np.abs(z)) or 1
    cols = [c.title() if c != "S&P 500" else c for c in famous.columns]
    rows = [r.replace(" (", "<br>(") for r in famous.index]
    fig = go.Figure(go.Heatmap(
        z=z, x=cols, y=rows, zmin=-m, zmax=m, zmid=0, colorscale=[[0, DOWN], [0.5, "#141414"], [1, UP]],
        text=[[f"{v:+.1f}%" if np.isfinite(v) else "—" for v in row] for row in z], texttemplate="%{text}",
        textfont=dict(size=12), showscale=False, xgap=2, ygap=2,
        hovertemplate="%{y}<br><b>%{x}</b>: %{z:+.1f}%<extra></extra>"))
    return _base(fig, 330, margin=dict(l=10, r=10, t=10, b=10),
                 yaxis=dict(autorange="reversed", automargin=True, tickfont=dict(color=AMBER)),
                 xaxis=dict(side="top", tickfont=dict(color=AMBER)))


def tension_fig(ct: pd.DataFrame, n: int = 8) -> go.Figure:
    top = ct.sort_values("pct", ascending=False).head(n)[::-1]
    fig = go.Figure(go.Bar(
        y=top["country"], x=top["pct"], orientation="h",
        marker=dict(color=top["pct"], cmin=0, cmax=100,
                    colorscale=TENSION_SCALE),
        text=[f"{ordinal(v)} pct" for v in top["pct"]], textposition="outside", cliponaxis=False,
        textfont=dict(color=TXT),
        hovertemplate="<b>%{y}</b><br>tension higher than %{x:.0f}% of its own months since 2000<extra></extra>"))
    return _base(fig, 60 + 26 * len(top), f"Most tense vs their own history · {ct.attrs['month']:%b %Y}",
                 margin=dict(l=10, r=70, t=30, b=10), bargap=0.3,
                 xaxis=dict(visible=False, range=[0, 112]), yaxis=dict(automargin=True, tickfont=dict(color=AMBER)))


def line_fig(s: pd.Series, title: str, color: str = BLUE, height: int = 260, hover: str = "%{y:,.2f}",
             **kw) -> go.Figure:
    yax = dict(gridcolor=GRID, **kw.pop("yaxis", {}))
    fig = go.Figure(go.Scatter(x=s.index, y=s, line=dict(color=color, width=1.6),
                               hovertemplate=hover + "<extra></extra>"))
    return _base(fig, height, title, hovermode="x unified", xaxis=dict(gridcolor=GRID), yaxis=yax, **kw)


# ---------------------------------------------------------------------- #
# ASSET tab: next month, past months, risk now (each with a plain explanation)
# ---------------------------------------------------------------------- #

def explain(html_text: str) -> str:
    return f"<div class='qm-brief' style='margin-top:-4px'>{html_text}</div>"


def cone_fig(p: pd.Series, sigma: float, q: np.ndarray, name: str, months_back: int = 6, h: int = 21):
    """Last few months of price + the next month's cone (2-in-3 range and 1-in-20 bad case)."""
    hist = p.loc[p.index[-1] - pd.DateOffset(months=months_back):]
    last, today = float(p.iloc[-1]), p.index[-1]
    fut = pd.bdate_range(today + pd.Timedelta(days=1), periods=h)
    steps = np.arange(1, h + 1)
    lo = last * np.exp(q[1] * sigma * np.sqrt(steps))
    hi = last * np.exp(q[3] * sigma * np.sqrt(steps))
    bad = last * np.exp(q[0] * sigma * np.sqrt(steps))
    x0 = [today] + list(fut)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x0, y=[last] + list(hi), line=dict(width=0), hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(x=x0, y=[last] + list(lo), fill="tonexty", fillcolor="rgba(58,141,255,0.25)",
                             line=dict(width=0), name="most likely (2 in 3)",
                             customdata=np.c_[[last] + list(hi)],
                             hovertemplate="%{x|%d %b}: $%{y:,.2f} – $%{customdata[0]:,.2f}<extra>most likely</extra>"))
    fig.add_trace(go.Scatter(x=x0, y=[last] + list(bad), line=dict(color=DOWN, width=1.5, dash="dash"),
                             name="bad case (1 in 20)", hovertemplate="%{x|%d %b}: $%{y:,.2f}<extra>bad case</extra>"))
    fig.add_trace(go.Scatter(x=hist.index, y=hist, line=dict(color=BLUE, width=1.8), name="price",
                             hovertemplate="%{x|%d %b %Y}: $%{y:,.2f}<extra></extra>"))
    month_start = today.replace(day=1)
    fig.add_vrect(x0=month_start, x1=today, fillcolor="#ffffff", opacity=0.05, line_width=0,
                  annotation_text=f"{today:%B} so far", annotation_position="top left",
                  annotation_font=dict(color=DIM, size=10))
    fig.add_vline(x=today, line_color=DIM, line_dash="dot")
    return _base(fig, 380, f"{name}: last {months_back} months and the next month (to {fut[-1]:%d %b})",
                 legend=LEGEND_TOP, margin=dict(l=10, r=10, t=60, b=30), hovermode="x unified",
                 xaxis=dict(gridcolor=GRID), yaxis=dict(gridcolor=GRID, tickprefix="$")), fut[-1], lo[-1], hi[-1], bad[-1]


def month_hist_fig(moves: pd.Series, band: np.ndarray, name: str) -> go.Figure:
    """Past monthly moves: green = up months, red = down months; blue = today's likely range."""
    lo_x, hi_x = np.nanpercentile(moves, [1, 99])
    m = moves.clip(lo_x, hi_x)
    width = (hi_x - lo_x) / 60
    bins = dict(start=lo_x, end=hi_x + width, size=width)
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=m[m >= 0], xbins=bins, marker_color=UP, name="up months",
                               hovertemplate="%{x:.0f}%: %{y} months<extra></extra>"))
    fig.add_trace(go.Histogram(x=m[m < 0], xbins=bins, marker_color=DOWN, name="down months",
                               hovertemplate="%{x:.0f}%: %{y} months<extra></extra>"))
    fig.add_vrect(x0=band[1], x1=band[3], fillcolor=BLUE, opacity=0.22, line_width=0,
                  annotation_text="most likely now", annotation_position="top left",
                  annotation_font=dict(color=BLUE, size=10))
    fig.add_vline(x=band[0], line_color=DOWN, line_dash="dash", annotation_text="bad case",
                  annotation_position="bottom left", annotation_font=dict(color=DOWN, size=10))
    return _base(fig, 330, f"How big a month usually is for {name}", barmode="overlay", bargap=0.05,
                 legend=LEGEND_TOP, margin=dict(l=10, r=10, t=60, b=30),
                 xaxis=dict(title="move over a month", ticksuffix="%", gridcolor=GRID),
                 yaxis=dict(title="number of months", gridcolor=GRID))


def risk_zoom_fig(sw: pd.Series, usual: float, name: str, years: int = 2) -> go.Figure:
    """Expected monthly swing over the last `years`, vs its usual level."""
    s = sw.loc[sw.index[-1] - pd.DateOffset(years=years):]
    fig = go.Figure(go.Scatter(x=s.index, y=s, line=dict(color=BLUE, width=1.6), name="expected swing",
                               hovertemplate="%{x|%d %b %Y}: ±%{y:.1f}%<extra></extra>"))
    fig.add_hline(y=usual, line_color=TXT, line_dash="dot", annotation_text=f"its usual ±{usual:.1f}%",
                  annotation_font=dict(color=TXT, size=10))
    now = float(s.iloc[-1])
    fig.add_trace(go.Scatter(x=[s.index[-1]], y=[now], mode="markers",
                             marker=dict(size=10, color=UP if now <= usual else DOWN), name="now",
                             hovertemplate=f"now: ±{now:.1f}%<extra></extra>"))
    return _base(fig, 300, f"How stormy {name} has been (last {years} years)", legend=LEGEND_TOP,
                 margin=dict(l=10, r=10, t=60, b=30), xaxis=dict(gridcolor=GRID),
                 yaxis=dict(ticksuffix="%", gridcolor=GRID, rangemode="tozero"))
