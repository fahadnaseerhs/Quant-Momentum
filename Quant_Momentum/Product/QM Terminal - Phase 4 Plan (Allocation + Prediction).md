# QM Terminal — Phase 4 Plan: Smart Allocation + Next-Month Prediction

**Status (2026-10-11):** **Part A BUILT and TESTED** (the PLAN tab). **Part B TESTED: nothing passed**, so the terminal shows no return prediction. · **Builds on:** [[QM Terminal - Plan]] · [[11 - Robustness (No-Hindsight Universe)]]

## ✅ Part A — built, and what the test showed

**Code:** `terminal/allocate.py` (one engine for live and test) · PLAN tab in `terminal/app.py` · test `scripts/13_allocation_backtest.py` · holdings saved in `terminal/portfolio.json` (on this computer only).

**PLAN tab, top to bottom:**
1. **Risk per segment:** swing per month, level, vs its own history, $100 bad → good, share of money, share of risk.
2. **Buy list based on risk:** $, shares at the live price, and a reason per asset. **Your plan** card: the plan's swing and its typical / bad / good outcome. A heatmap of which segments move together.
3. **When to buy and sell:** Day 0 = buy the list. Every Monday = weekly check, trading only what is >20% off target (and ≥ $5), each trade with its reason. A holdings editor, plus **"I bought the plan"** and **"I made these trades"** buttons.

**A design change the test forced.** Profiles that are always fully invested lost about 48–54% in 2008, which showed up in the **design period (2005–15)** before the holdout was used. The profile with a fixed bad-month limit lost only about 10%. So **every profile now caps the 1-in-20 bad month**: Careful −3%, Balanced −6%, Bold −10% (+ growth tilt). In calm markets that means fully invested; in storms the invested share shrinks automatically. **That automatic step-down is the tested "when to sell".**

**Results** (weekly check, 20% band, 10 bps; Sharpe full / holdout; worst drop):

| Profile | Project 20 | | ETF 23 (no hindsight) | |
|---|---|---|---|---|
| CAREFUL (−3%) | 1.30 / 1.55 | −13% | 0.88 / 0.85 | −14% |
| **BALANCED (−6%)** | **1.23 / 1.56** | **−22%** | **0.80 / 0.83** | **−21%** |
| BOLD (−10%, growth ×2) | 1.04 / 1.52 | −30% | 0.61 / 0.82 | −35% |
| always fully invested (old design) | 0.99 / 1.44 | −48% | 0.50 / 0.86 | −54% |
| SPY buy & hold | 0.69 / 0.96 | −55% | 0.69 / 0.96 | −55% |

- **Costs:** about 0.5–0.6% a year (Bold on the project universe 1.6%, because of crypto). About 4–5 trade lines a week.
- **Is the "bad month" honest?** Months worse than the predicted 1-in-20: 3–4% on the project universe (slightly cautious) and about 7% on ETFs (slightly optimistic, closer to 1-in-14).
- **Honest limit:** on the hindsight-free ETFs, **SPY ended with more dollars** (the 2009–26 US bull market). The plans win on **risk** (a third to a half of the drawdown, and a better Sharpe over the full period), not on raw return. The holdout Sharpe there is slightly below SPY's (0.83 vs 0.96).
- *Caveat:* the capped versions were run after the first (uncapped) holdout had been seen, so their holdout numbers are slightly less clean. The decision itself rests on the design period.

![[13_g1_allocation_equity.png]]

---

## The two things wanted

1. **Divide my $X by risk, properly.** Today's "split by risk" gives every chosen asset the same risk. Wanted: the split also respects *how much risk I want to take*, and doesn't let one group (five crypto coins that move together) dominate.
2. **"Where should I invest / what's the prediction for next month."** Use today's information to predict the next period and show it on the terminal.

**The rule still applies:** a prediction only goes on screen if it passes a fair test that we write down **before** running it. Part A can be built straight away (risk is predictable). Part B is research first, with a gate.

---

## Revised design (2026-10-11, after the three requirements below)

**Requirements:** (1) risk is calculated **per bucket**; (2) the buy suggestions are **based on that risk**; (3) the terminal gives a **timeline: when to buy and when to sell**.

### Step 1 — Risk per bucket
For each of the 6 buckets:
1. Build the bucket as one mini-portfolio: its assets weighted so each carries equal risk.
2. **Bucket risk** = EWMA volatility of that mini-portfolio. Because it's computed on the mix, it already includes how the assets move together. It's shown as the expected monthly swing (±%) plus a label (stormy / lively / calm / very calm).
3. **Bucket bad month** = a 1-in-20 loss for $100, using the bucket's own history of big moves (same method as the Calculator).
4. **Risk vs its own history** (percentile) and **correlation between buckets** over the last year.

**SHY is the "safe part" (cash), not a bucket asset.** Counting it as risk pushed 70% of the money into it.

Live example (11 Oct 2026):

| Bucket | Monthly swing | Level | vs own history | $100 bad month | $100 good month |
|---|---|---|---|---|---|
| Crypto | ±13.6% | STORMY | 38th pct | $75 | $142 |
| Tech | ±4.1% | CALM | 8th pct | $92 | $106 |
| Gold | ±7.6% | LIVELY | 72nd pct | $88 | $114 |
| Oil | ±6.8% | LIVELY | 67th pct | $87 | $111 |
| Real assets | ±3.3% | CALM | 38th pct | $94 | $105 |
| Bonds (TLT; SHY = safe part) | ±2.8% | CALM | 24th pct | $96 | $105 |

### Step 2 — Buy list based on risk
1. **Risk budget per bucket.** By default each bucket gets an equal share of the total risk, taking correlations into account (oil and bonds currently move *against* each other, so together they count as less risk).
2. **Inside each bucket**, the bucket's money is split by equal risk across its assets.
3. **Risk profile** decides the safe part and the tilt:
   - **Careful:** bad month about −3% → about 70% in the mix, 30% safe (SHY).
   - **Balanced:** equal risk, bad month capped at about −6% (fully invested in calm markets). *Updated after the test; originally "always fully invested".*
   - **Bold:** **double the risk share for growth buckets** (crypto, tech, real assets), bad month capped at about −10%. *Updated after the test.*
   - **Custom:** sliders per bucket.
4. **Output:** ticker, $ to buy, number of shares at the live price, and a one-line reason ("calm, so a bigger slice").

Example, **Balanced, $1,000** today: Bonds $362 (TLT) · Tech $187 (AAPL 49, GOOGL 43, MSFT 38, NVDA 34, META 22) · Oil $185 (XOM 73, CVX 73, USO 39) · Real assets $141 (VNQ 74, DBC 54, MSTR 12) · Gold $84 (GLD 53, B 31) · Crypto $42 (BTC 13, ETH 10, SOL 9, LINK 7, AVAX 4). Crypto gets the least *money* because it carries the most *risk* per dollar.

### Step 3 — Timeline: when to buy, when to sell
| When | Rule | Basis |
|---|---|---|
| **Day 0** | buy the list | Step 2 |
| **Every week** (one fixed day) | recompute targets. **Trade only where an asset is off target by more than 20%** (and at least $5): sell the excess or buy the gap. Each line gets a reason ("BTC risk rose ±10% → ±16%: sell $4") | weekly beat daily and monthly in Task 10; the band avoids tiny costly trades |
| **Risk alarm** (any day) | if a bucket's risk jumps above 1.5× its level at the last rebalance, or turns STORMY from CALM → trim it now | **to be tested** in Part B before it's switched on |
| **Trend exit / entry** | sell a bucket when its trend turns down, buy back when it turns up | **only for buckets that pass the Part B gate** (likely candidates: bonds, gold, commodities) |
| **Full sell** | otherwise positions aren't sold outright; "sell" means trimming back to target | risk-sizing is the tested edge; timing isn't (yet) |

**Needs:** a **holdings log**. You enter what you actually bought, so the weekly trade list shows the exact sells and buys for your real portfolio. It's stored locally in `terminal/portfolio.json`.

**Before launch:** backtest this whole procedure (profiles + weekly band rebalancing) over 2005–2026 on both universes. That gives trades per year, the cost per year, and the worst drawdown vs SPY, with the same pass/fail discipline as Tasks 10–11.

---

## Part A — Allocation by risk (buildable now)

| # | Feature | What you do | What it shows |
|---|---|---|---|
| A1 | **Risk appetite** | choose *Careful / Balanced / Bold*, **or** type "in a bad month I can lose at most $L" | how much of $X goes into risky assets vs the safe part (SHY/cash), sized so a 1-in-20 bad month loses about $L |
| A2 | **Equal risk per bucket** | pick buckets (default: all 6) | each bucket gets the same share of risk, then split equally by risk inside it, so 5 crypto coins share one crypto slice instead of taking 5 |
| A3 | **Correlation-aware split** | — | true "equal risk contribution": assets that move together count as one risk. Uses the last year of correlations |
| A4 | **The plan card** | — | $ per asset, each asset's share of total risk (bar), plan outcome for the period (typical / bad / good), and a "rebalance weekly" reminder (Task 10 found weekly is best) |
| A5 | **Custom tilt** (optional) | sliders: more or less of a bucket | the plan's risk updates live |

*Why it's trustworthy:* it only uses risk forecasts (tested) and correlations, and makes no direction calls. Task 11 showed risk-sized diversified books beat SPY on a risk-adjusted basis on both universes.

---

## ❌ Part B — RESULT (2026-10-11): nothing passes, so no prediction goes on the terminal

**Code:** `scripts/14_prediction_lab.py` · tables `reports/tables/14_prediction_*.csv`

HOLDOUT 2016–2026. Brier skill > 0 means better than the base rate; timing t ≥ 2 is required to pass.

| Family | Project 20: skill / timing t | ETF 23: skill / timing t | Pass? |
|---|---|---|---|
| F1 macro trend | −0.002 / −1.2 | −0.002 / −2.3 | ❌ |
| F2 panic rebound | −0.004 / +0.3 | −0.015 / −0.5 | ❌ |
| F3 world regime | −0.032 / +0.3 | −0.020 / −0.5 | ❌ |
| F4 combined | −0.051 / +0.2 | −0.043 / −0.7 | ❌ |
| F5 boosted trees | −0.056 / −0.7 | −0.058 / −0.2 | ❌ |

- **Every family is worse than the base rate** in both periods and both universes. No family is positive in more than 1 group.
- **Controls** (same pipeline): "no information" scores 0.0000 and pure random noise about −0.001. The world-regime, combined and tree models (−0.02 to −0.06) are **worse than noise**: they learn past patterns that reverse later. Macro trend and panic rebound are at noise level.
- **What wins is the base rate itself:** "this group is up about 55–60% of months". Each model's hit rate was *below* the always-up hit rate.
- **Consistent with the whole project.** Return direction was not predictable on a fair test (Tasks 07, 07c, 11). Risk was, and it's already in the PLAN tab.

**Lesson for any future test (written before any new test is run):** the no-information control reached timing t = +2.65 on the ETFs from tiny shrinkage differences. A future pass rule must also require **Brier skill ≥ +0.005** (a real improvement, not rounding).

**Terminal decision:** no "next-month outlook" panel. Buy and sell guidance stays risk-based: the PLAN tab's weekly check, plus the automatic step-down when risk rises.

![[14_g1_prediction_scores.png]]

---

## Part B — PRE-REGISTRATION (frozen 2026-10-11, before any Part B run)

**Question:** given today's information, what is the chance each asset is **up over the next month**, and is that better than the plain base rate?

**Sampling.** One prediction per asset on the first trading day of every month. The label is "up or down until the next month's first day", so labels never overlap. The model is refit every month on all earlier months only (expanding window; at least 36 months to start). Universes: the project's 20 (minus SHY, the safe part) and the 23 ETFs (minus SHY).

**Features** (all known on the prediction day):
- trend z (the average of the 1/3/6-month skip-5 trend, vol-scaled)
- last-week move (vol-scaled)
- VIX (log), and "VIX ≥ 30"
- yield curve 10y−3m
- credit stress (HYG/IEF, 3 months)
- copper/gold (3 months)
- oil (3 months)
- TIP/IEF (3 months)
- 10y yield change (3 months)
- war-tension index (log, 7-day average)

**Signal families tested:**

| ID | Family | Assets | Model |
|---|---|---|---|
| F1 | **Macro trend** | bonds (TLT; ETF: IEF, TLT, LQD, TIP), gold (GLD), commodities (USO, DBC) | logistic: trend z (shared slope) + group intercepts |
| F2 | **Panic rebound** | stocks / equity funds | logistic: VIX ≥ 30 + log VIX (shared) + group intercepts |
| F3 | **World regime** | all, one model per bucket | logistic: the 7 world features |
| F4 | **Combined** | all, one model per bucket | logistic: all features |
| F5 | **Boosted trees** (challenger = Task 08) | all, pooled + bucket | gradient-boosted trees, depth 3, refit yearly |

The logistic models use standardised features fit on the training data only, with L2 regularisation (C = 0.5).

**Benchmark:** the **base rate**, meaning each group's expanding share of up-months. This is what a model with only an intercept would say.

**Scores per period** (design = predictions dated ≤ 2015, HOLDOUT = 2016 onwards):
- **Brier skill** = 1 − Brier(model) / Brier(base rate). Above 0 means the probabilities are better than the base rate.
- **Timing t-stat:** the t-stat over months of the average of (p − base rate) × next-month vol-scaled return. This is the "does betting on the prediction pay" test, and it is robust to assets moving together.
- **Hit rate** vs always-long, and per-group Brier skill.

**PASS (all on the HOLDOUT, on BOTH universes):**
1. Brier skill > 0 **and** timing t ≥ 2.
2. Works in at least 2/3 of its groups (F1: 2 of 3; F2: 2 of 3; F3–F5: 4 of 6 buckets on the project universe, 3 of 5 on ETFs) with Brier skill > 0.
3. Only for a family that passes 1 and 2: a Part A Balanced plan **tilted** by it (risk budget × (1 + 2·(p − base)), capped 0.5–1.5×) beats the untilted plan's holdout Sharpe after costs, on both universes.

Anything that fails stays off the terminal. The result gets written up here either way.

## Part B — Prediction lab (research first, then gate)

### B1. What exactly we predict
- **P(up next month)** for each asset and each bucket, as a probability (for example, "gold up next month: 58%").
- **Bucket ranking** for next month (which bucket is expected to do best relative to its risk).

### B2. Candidate signals (the list is fixed now; nothing added after seeing results)
| Signal | Idea | Evidence so far |
|---|---|---|
| Trend, **macro assets only** (bonds, gold, commodities, oil) | trends persist in slow-moving macro assets | positive IC on these in **both** universes (Tasks 07c, 11) |
| **Panic rebound** | after VIX ≥ 30, stocks tended to recover | SPY up in 12 of 14 episodes over 3 months (playbook) |
| **World regime** | recession / inflation / war gauges shift which bucket wins | 2008 vs 2022: bonds up vs bonds down |
| Volatility-managed exposure | cut exposure when risk spikes | literature (Moreira & Muir) and our vol results |
| *(challenger)* boosted trees on all of the above | non-linear combinations | Task 08, never run |

### B3. Models
1. **Logistic regression** (gives honest probabilities), walk-forward, refit monthly.
2. **Boosted trees** as a challenger (Task 08), same test.
3. The **benchmark every model must beat: the base rate**, meaning "it's up X% of months historically" with no model.

### B4. The fair test (same discipline as Tasks 10–11)
- Walk-forward with an embargo. **Design 2005–2015 → holdout 2016–2026.**
- Run on **both** universes: the project's 20 assets and the 23 no-hindsight ETFs.
- Scores: **Brier score vs base rate** (are the probabilities better than "always 55%"?), hit rate vs always-long, IC t-stat, and portfolio **Sharpe after costs vs the Part A risk-based plan**.

### B5. Pass rule (fixed now, before any test)
A signal or model goes on the terminal **only if all of these hold**:
1. Holdout Brier score beats the base rate, **and** IC t-stat ≥ 2, on **both** universes.
2. A plan tilted by it beats the Part A plan's holdout Sharpe after costs.
3. It works on at least 2 of the 3 buckets it claims to predict (not one lucky asset).

**If nothing passes:** the terminal shows no prediction. We write down why in Obsidian, and the plan stays risk-based.

### B6. If something passes → what you'll see
- **"NEXT MONTH OUTLOOK" panel:** per bucket and per asset, the probability of going up and the base rate next to it.
- **"Where to put $X" = the Part A plan tilted towards the predicted winners**, with tilts capped so one wrong call can't sink the plan.
- **Live scorecard:** every prediction is saved daily and scored a month later, so you can see whether it keeps working out of sample in real time. (The paper log starts recording on day 1 either way.)

---

## Part C — Order of work

| Step | What | Size |
|---|---|---|
| 1 | Part A (A1–A4) into the Calculator tab | 1 session |
| 2 | Part B research: features, logistic model, fair test, both universes | 1–2 sessions |
| 3 | Boosted-tree challenger (Task 08) | 1 session |
| 4 | If anything passes: Outlook panel, tilted plan, live scorecard | 1 session |

**Honest expectation:** Part A will work. For Part B, the most likely winners are *panic rebound* and *trend on macro assets*. Both are small edges, and it's quite possible nothing clears the bar on the no-hindsight universe. The gate exists so the terminal never shows a prediction we haven't proven.
