# QM Terminal — Product Plan

**What it is.** A live market terminal that runs on your own computer and opens in the browser. It turns the research from Tasks 07–11 into a screen a normal person can read: how risky each asset is right now, which way it has been moving, what $X could turn into, and what the world is doing (war tension, recession risk, inflation) and how the buckets behaved last time the world looked like this.

**Look.** A dark terminal style inspired by professional market terminals: black background, amber and orange text, a monospace font, green for up and red for down, dense panels. It is inspired by them, not a copy, and no third-party brand names appear anywhere. There's a globe in the centre showing war and tension levels by country.

**The one rule.** Only things that passed our tests go on screen. Anything we couldn't verify is left out.

| On screen ✅ | Why it's allowed | Left out ❌ | Why |
|---|---|---|---|
| Risk: how much each asset is likely to swing | Volatility is predictable (Tasks 07b, 07c) | "Asset X will make the most profit" | Return prediction failed a fair test (Task 11) |
| Outcome range for $X over a period | Built from the risk forecast and the asset's own history of fat tails | Buy and sell signals | Same reason |
| Equal-risk split of $X | The most robust result of the project (Task 11) | Price targets | Not testable |
| Trend, described as the past ("up 12% in 3 months") | Facts | Trend as a promise | Trend was fragile out of sample |
| World gauges and "last times it looked like this", with counts | Facts plus history | "War is coming, so buy oil" | Too few episodes to be a rule |

**Buckets** (the project's 6, from `src/universe.py`): Crypto (BTC, ETH, SOL, LINK, AVAX) · Tech (AAPL, MSFT, NVDA, GOOGL, META) · Gold (GLD, B) · Oil (USO, XOM, CVX) · Real assets (VNQ, DBC, MSTR) · Bonds (TLT, SHY).

---

## Phase 1 — Market core

| Feature | What you see | How it's computed |
|---|---|---|
| **Ticker tape** | live price and today's % for every asset | Yahoo 1-minute data, refreshed every 60 s (crypto is near-live; stocks are ~15 min delayed) |
| **6 bucket panels** | each asset with its risk bar coloured **stormy / lively / calm / very calm**, its expected monthly swing (±%), and a trend arrow | EWMA volatility (λ = 0.94) including today's live move. Monthly swing = σ·√21. Bands: <2% very calm, 2–6% calm, 6–12% lively, >12% stormy |
| **"Most stormy … most calm" ranking** | the extremes across all 20 assets | sorted by monthly swing; also flags "higher than usual for this asset" (above its own 80th percentile) |
| **Asset detail + histogram** | the distribution of past monthly moves, with this month's likely range shaded; a 6-month price chart | the asset's own history since 2004 or since listing |
| **Investment box** | type $10 or $100 and pick 1 week / 1 month / 3 months / 6 months / 1 year → a typical range (2 in 3 chance) and bad/good cases (1 in 20) per asset | today's risk × the asset's own historical fat tails, with the average drift removed (no direction is predicted) |
| **Split my $X by risk** | how much to put in each chosen asset so each carries equal risk, plus the range for the whole mix | inverse-volatility weights; mix risk uses the correlation matrix |
| **Trend** | ↑↑ ↑ → ↓ ↓↓ plus "up/down X% over 1 / 3 / 6 months" | skip-5 trend z-scores from Task 07, worded as the past |
| **Price alerts** | "Oil turned stormy", "BTC moved −9% today (3× a normal day)", "TLT trend flipped down" | changes vs yesterday's close plus the last 30 days of label changes, from history |

## Phase 2 — World view

| Gauge | Inputs | Source |
|---|---|---|
| **Fear** | VIX level and percentile | Yahoo |
| **Recession** | 10-year minus 3-month yield (inverted = warning), credit stress (HYG vs IEF), copper/gold trend; + jobless trend (Sahm rule) and high-yield spread with a FRED key | Yahoo (+ FRED) |
| **Inflation** | oil 3-month change, inflation expectations (TIP vs IEF), 10-year yield change; + breakeven inflation with a FRED key | Yahoo (+ FRED) |
| **War / tension** | Geopolitical Risk Index (daily, newspaper-based), oil spike, defence stocks (ITA) vs the market | Caldara & Iacoviello GPR (free) + Yahoo |

- **"What kind of weather is building"**: calm · panic shock · growth scare / depression risk · inflation shock · war tension (more than one can be active).
- **Globe** (centre): countries coloured by their own geopolitical risk level (44 countries, monthly).
- **"Last times it looked like this"**: for each active gauge, every past episode since 2004 and what each bucket did over the next 1 and 3 months, shown as median plus "up in N of M times".
- **World alerts**: "Yield curve just inverted", "War-tension index at its highest since 2022", and so on.

Why the *type* of crisis matters (from our data; Bonds = long-term Treasuries TLT, SHY excluded since 2026-10-11):

| | Crypto | Tech | Gold | Oil | Real assets | Bonds |
|---|---|---|---|---|---|---|
| 2008 depression scare | — | −57% | −4% | −39% | −52% | **+25%** |
| 2020 Covid crash | −44% | −31% | −11% | −52% | −33% | **+14%** |
| 2022 war starts (5 weeks) | +30% | +12% | +5% | +13% | +17% | −3% |
| 2022 inflation shock | −78% | −42% | −4% | **+58%** | −27% | **−31%** |

## Phase 3 — News and AI summary

- **Headlines** from public RSS feeds (BBC World, BBC Business, CNBC), refreshed every 30 minutes.
- **AI briefing** (needs an Anthropic API key): a short "what's happening in the world" paragraph, which gauge each story relates to (war / recession / inflation / calm), and which buckets the news touches. The AI **only summarises the news**; it never predicts prices.
- Without a key, the headlines are still shown, grouped by keyword.

---

## How to run (once built)

```bash
.venv/Scripts/python.exe -m streamlit run terminal/app.py
```

**Keys (optional)** go in a `.env` file in the project folder. You get them yourself, free for FRED:
```
FRED_API_KEY=...        # https://fred.stlouisfed.org → My Account → API Keys
ANTHROPIC_API_KEY=...   # https://console.anthropic.com (Phase 3 AI briefing)
```

## Code layout

`terminal/app.py` (screen) · `terminal/data.py` (prices, live quotes, cache) · `terminal/risk.py` (swing, labels, ranges, split, trend) · `terminal/alerts.py` · `terminal/world.py` (gauges, regime, playbook, globe data) · `terminal/news.py` (RSS + AI) · `terminal/theme.css`

## Status

- [x] **Phase 1 — Market core** (built 2026-10-11): ticker tape, 6 bucket panels, extremes, Calculator (all 20 assets' outcome ranges + split by risk), Asset tab (histogram, 12-month chart, risk over time), price alerts.
- [x] **Phase 2 — World view** (built 2026-10-11): 4 gauges, weather banner, globe (44 countries), playbook for 4 triggers, famous-crises table, world alerts. FRED signals are coded and switch on when `FRED_API_KEY` is in `.env`.
- [x] **Phase 3 — News** (built 2026-10-11): live headlines from BBC World, BBC Business and CNBC with keyword tags. The AI briefing (Claude Opus 5.5, structured JSON, refusal fallback, cached 30 min) is coded but **untested until `ANTHROPIC_API_KEY` is added**.

## Screen layout

**Top bar**: name · world weather · New York time · ● LIVE. **Ticker tape** scrolling below it.

**Tabs:** `OVERVIEW` (crypto, tech and gold on the left · weather + globe + 4 gauges + extremes in the centre · oil, real assets and bonds on the right · alerts + news underneath) · `CALCULATOR` · `ASSET` · `WORLD` · `NEWS` · `ALERTS`. The overview and top bar refresh every 60 s.

## What the first live run showed (Sun 11 Oct 2026)

- **World:** WAR / GEOPOLITICAL TENSION (rising: tension index 7-day average 177, top 5% since 1985) + INFLATION (rising: 10y yield +0.63 pp in 3 months). Fear normal (VIX 14.8), recession normal.
- **Playbook, war tension in its top 5%:** 13 episodes since 2004. Over the next 3 months, tech rose in 8 of 13 and oil in 6 of 13. Mixed, which is why it's shown as history and not as a rule.
- **Most stormy:** AVAX (±33%/month), MSTR, LINK, SOL. **Most calm:** SHY (±0.4%), TLT, VNQ, DBC.

## Build log — problems found and fixed

| Problem | Fix |
|---|---|
| Alerts flickered when an asset sat on a band edge (AAPL calm ↔ lively daily) | A new state must hold **3 days** before it's announced (`alerts.debounce`) |
| At weekends, Friday's last 1-minute stock bar counted as "live" | A live price only counts if it traded **after** the last daily close |
| SHY's "good case" showed +8.7% on a ±0.4%-a-month asset | The fat-tail scaling was centred on the **mean**, which a few near-zero-volatility days (Feb 2020) dragged off. It's now centred on the **median**. All 20 assets checked: each 1-in-20 band holds about 86–89% of past months |
| GDELT news API rate-limited (429) | Switched to RSS feeds |

## Not yet done / ideas

- Add your FRED key to switch on 3 extra recession and inflation signals.
- Add an Anthropic key for the AI briefing, then check its output for a few days.
- Possible later: push alerts to your phone; let the `check` list hold your own tickers.

Related: [[Task Log]] · [[11 - Robustness (No-Hindsight Universe)]] · [[07c - Long-History Re-test]]

## UI update (2026-10-11) — what changed

- **Removed:** Calculator "Split my money by risk" (the PLAN tab does this) · the big Calculator table (same numbers as the range chart, now on hover) · the "Your plan" box on PLAN (folded into the plan statement) · the "What kind of weather is building" block on OVERVIEW (same as the top bar + gauges + statement) · the 12-row alerts list on OVERVIEW (now top 3 headlines + 8 latest; the ALERTS tab is the one full feed) · Overview and ALERTS now share one alerts feed instead of computing two.
- **Tables → charts:** PLAN segment risk → bar chart of swing per segment coloured by level (assets, vs-history and $100 bad→good on hover) + money-share vs risk-share bars · buy list → treemap by segment/asset (exact $, shares, price on hover; an "exact amounts" list sits in a collapsed expander) · WORLD playbooks → bar charts of median 1M/3M move labelled "up N of M" · famous crises → heatmap · most-tense countries → bar chart · overview extremes → bar chart · ALERTS → alerts-per-day chart by severity.
- **Statements:** every tab opens with plain-English facts generated from the live data (market level, stormiest/calmest segment, world gauges, plan size / bad month / typical range, calculator calmest vs stormiest, asset risk and past moves, news counts, alert counts). Weekly trades are now one card per trade ("SELL $X of Bitcoin — it is 40% above its target"). Alerts carry severity colours (HIGH / NOTE / EASING), the ALERTS tab is grouped by day with a severity filter, and OVERVIEW shows the 3 most important newest alerts as headlines. Nothing predicts a direction.
- **Speed:** live prices + risk snapshot + EWMA sigma history computed once per new quote set and shared by all tabs (was 5 snapshot and 3 sigma passes per run); alerts, plan and outcome ranges cached 5 min; world 1 h. Warm full run 3.5 s → 1.8 s (AppTest); cold run 26 s → 18–21 s (mostly the data download). The 60-s overview refresh now does about 0.1 s of maths instead of about 0.6 s.
- Code: presentation helpers and charts live in `terminal/ui.py`; the engines were not changed.

## UI update (2026-10-12) — your feedback
- **Removed** the NEWS and ALERTS tabs, plus the news and alert panels on OVERVIEW and the alert line on ASSET. The terminal now has 5 tabs: OVERVIEW · PLAN · CALCULATOR · ASSET · WORLD. The `news.py` / `alerts.py` code is kept but not shown.
- **Removed** the "Add FRED_API_KEY…" note on WORLD.
- **Chart colours:** no brown or amber in the data. **Green = up / good, red = down / bad, blue = neutral lines and ranges, black background.** Applies to the histogram, playbook bars, money share, correlation and the globe/tension scale.
- **ASSET tab rebuilt around now and next month.** Each chart has a "What this means" line:
  1. **Price, last 6 months, plus the next-month cone** (current month shaded): "Most likely (2 in 3 chance) between $X and $Y by <date>", plus the bad case. A range, not a direction call.
  2. **How big a month usually is:** green up-months / red down-months, today's likely range shaded in blue, the bad-case line, and the share of months that were up.
  3. **How stormy it has been (last 2 years)** vs its usual level, with a "now" dot (green = calmer than usual, red = stormier).
- **PLAN "When to buy and sell"** is now plain steps based on the amount: Step 1 buy the list for $X → Step 2 press **I bought this plan** → Step 3 every Monday, see only the trades needed. When holdings exist it shows "You hold $X…" + trade cards + **I made these trades** / **Start over (keeps a backup)**. The share table moved into a closed **Advanced** expander.
- The $75.5M test holdings were moved to `terminal/portfolio_backup_20261012_test_75M.json` (not deleted), so the PLAN tab starts clean at $1,000.
