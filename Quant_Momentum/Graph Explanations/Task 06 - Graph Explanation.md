# Task 06 — Graph Explanation (Baseline Strategies)

**Previous:** [[Task 05 - Graph Explanation]] · **Index:** [[_Graph Explanations - README]] · **Dictionary of labels:** [[Graph and Table Labels]]
**Code:** `scripts/06_baseline.py` (graphs + table) and `src/baseline.py` (the rules)

> **How to use this note.** Written so you *understand*, not just read. Part A teaches the concepts in plain words. Part B is the scoreboard table. Part C explains the 3 graphs (🧠 idea → 👀 how to read → 🔎 what it shows → 💡 so what → ⚠️ trap → ✅ takeaway). Part D is the honest verdict, including a few extra checks I ran that the original script does not do.
> *There is no Methodology note for Task 06 yet, so this note also explains what the task does.*

---

# Part A — What is Task 06, and the concepts you need

## What is it asking?
In Task 05 we found tiny hints: a few clues might rank winners from losers. Task 06 asks the next, more practical question:

> **If we turned the simplest possible clue-based rule into a real trading strategy, how would it have done over 2021–2026, compared with doing nothing clever?**

This is called a **baseline** (or "Model 0"): **no machine learning, no fitting, no tuning**. Just *"rank by one clue, hold the top ones."* Any fancier model we build later must **beat these** to be worth the complexity.

## The rules of the baseline strategies
Every day, after the close:
1. **Rank** the 20 assets by one clue (e.g. `vsmom_63d`).
2. **Hold the top 5**, each with an equal 20% weight, **for the next day only**.
3. **Repeat every day** (this is "rebalancing daily").

The "cheating" rule: the clue at day *t* chooses the positions, and we earn the return from *t* to *t+1* (`fwd_ret_1d`). No peeking.

## The strategies and benchmarks (the 7 lines you'll see)

| Name on the graph | What it does | Why it's here |
|---|---|---|
| `top5_vsmom_63d` | Hold the 5 assets with the highest **vol-scaled 3-month momentum** | The project's starting hypothesis |
| `top5_vsmom_21d` | Same, with **1-month** vol-scaled momentum | Test a shorter window |
| `top5_mom_63d` | Top 5 by **raw** 3-month momentum (not scaled by risk) | Isolates the effect of the vol-scaling |
| `ls_vsmom_63d` | **Long the top 5 and short the bottom 5** (explained next) | Tests the signal's *skill*, with market moves cancelled |
| `eq_weight_universe` | Hold **all 20 assets, 5% each**, every day | **The fair yardstick**: what the basket does with no skill |
| `random_top5` | Each day pick 5 assets **at random** | "Is our rule better than luck?" |
| `SPY` | Just own the US stock market | The usual benchmark everyone knows |

### Long vs short (in one minute)
- **Long** = you buy; you profit when the price rises.
- **Short** = you borrow and sell; you profit when the price **falls** (and lose when it rises).
- **Long–short** = long the 5 "strongest", short the 5 "weakest". If the whole market goes up 10%, your long gains and your short loses, so the market's tide roughly **cancels out**, and what's left is the **skill of the ranking**.

## The scoreboard words (explained like you're new)

| Word | Plain meaning | Analogy |
|---|---|---|
| **Cumulative return** | Total gain over the whole period. 7.47 = +747% (\$1 → \$8.47) | Your final bank balance |
| **Annual return** | The average yearly growth rate | The "speed" |
| **Annual volatility** | How bumpy the ride is (per year) | How rough the road is |
| **Sharpe ratio** | **Return per unit of bumpiness** = annual return ÷ annual vol | **Miles per gallon, but for investing.** Higher = more return for the same pain. Rough guide: <0.5 poor, ~1 decent, >2 excellent (or too good to be true) |
| **Max drawdown** | The **deepest fall from a previous peak** | "At the worst moment, how far underwater was I?" −0.41 = down 41% from the high |
| **Win rate** | % of days with a positive return | Most strategies sit at 51–54%: barely better than a coin; wins are about *size*, not frequency |
| **Turnover** | How much of the portfolio is swapped each day. 0.158 = 15.8% | High turnover = lots of trading = **costs** |
| **Equity curve** | \$1 invested on day one, tracked through time | The "growth of \$1" graph from Task 03, but for a strategy |

> ⚠️ **Everything here is "before costs".** The graphs ignore commissions, bid–ask spreads and slippage. Daily trading makes costs matter a lot (see Part D).
> ⚠️ **The Sharpe here is simplified:** the script doesn't subtract a risk-free interest rate (cash earns ~0–5%). Fine for comparing strategies with each other.

---

# Part B — The scoreboard (`06_baseline_metrics.csv`)

| Strategy | \$1 becomes | Annual return | Annual vol | **Sharpe** | Max drawdown | Win rate | Daily turnover |
|---|---|---|---|---|---|---|---|
| **top5_vsmom_21d** | **\$18.05** | **75.0%** | 32.7% | **2.29** | −35.8% | 52.1% | 15.8% |
| top5_mom_63d | \$9.57 | 62.8% | 42.7% | 1.47 | −43.7% | 52.5% | 8.3% |
| top5_vsmom_63d | \$8.47 | 53.1% | 32.2% | 1.65 | −40.9% | 51.3% | 8.8% |
| **eq_weight_universe** | **\$5.88** | **41.8%** | 27.9% | **1.50** | −42.7% | 53.9% | 0 |
| random_top5 (seed 42) | \$2.26 | 21.9% | 33.2% | 0.66 | −53.5% | 52.4% | n/a |
| SPY | \$2.26 | 17.0% | 16.7% | 1.02 | **−24.5%** | 54.3% | 0 |
| ls_vsmom_63d | \$1.67 | 20.8% | 44.5% | 0.47 | **−57.1%** | 47.7% | 19.4% |

**First reaction:** `top5_vsmom_21d` looks fantastic (Sharpe 2.29, \$1 → \$18). **Don't celebrate yet.** Look at the row in bold: the **equal-weight universe**, which requires zero skill, made 41.8% a year with Sharpe 1.50. And SPY made only 17%. We'll explain in Part D what that means.

---

# Part C — The three graphs

---

# Graph 1 — Equity curves ("growth of \$1" for each strategy)

![[06_g1_equity_curves.png]]

### 🧠 The idea
Imagine each strategy starts with \$1 on day one and trades by its rule every day. The line shows how that \$1 evolves. It's the same idea as Task 03's Graph 1, but for **trading rules** instead of single assets.

### 👀 How to read it
- **x-axis** = date. **y-axis** = value of \$1, on a **log scale** (equal vertical distance = equal % growth; 1→2 looks as tall as 5→10).
- **Higher at the end = more money. Steeper = faster growth. Jagged = bumpy.**
- Title says **"before costs"**.

### 🔎 What it shows
Final values of \$1:

| Line | Ends at |
|---|---|
| top5_vsmom_21d (orange) | **\$18.05** |
| top5_mom_63d (green) | \$9.57 |
| top5_vsmom_63d (blue) | \$8.47 |
| eq_weight_universe (purple) | \$5.88 |
| random_top5 (brown) | \$2.26 |
| SPY (pink) | \$2.26 |
| ls_vsmom_63d (red) | \$1.67 |

Things you can *see* in the picture:
1. **The strategy lines are flat at \$1 for the first ~3 months of 2021.** The clues need **63–65 days** of history to exist, so the strategies **sat in cash** until about 8 April 2021. The benchmarks (equal-weight, random, SPY) were invested from day 1. That is a small head start for the benchmarks, in a period when the basket rose fast.
2. **Until late 2023 the equal-weight basket (purple) is as high as, or higher than, most strategy lines.** The momentum strategies only pull clearly ahead from about **late 2023 into 2024** (the crypto and tech rally). So the outperformance is **concentrated in a stretch**, not steady.
3. **All lines fall together in 2022** (crypto winter, stocks and bonds down).
4. The **long-short (red)** line goes nowhere much: down to ~\$0.7 in 2023, up to ~\$2.8 in 2025, then back to \$1.67.

### 💡 So what?
- The long-only momentum strategies **beat SPY and random** by a lot.
- But the **proper comparison is the purple line** (the same 20 assets, no skill). Compared with that, only `vsmom_21d` is clearly ahead; the other two are modestly ahead.
- The **long-short** result is the most important clue about "skill" (see Part D): it earns far less than the long-only versions.

### ⚠️ Traps
- **A log chart makes late gains look smaller than they are** and early gains bigger, so read the numbers, not just the slopes.
- **Hindsight in the basket:** the 20 assets were chosen *today* (NVDA, SOL, MSTR…). The "do-nothing" basket made 41.8% a year vs SPY's 17%, which is partly because **we picked a basket of survivors and winners**. Everything on this graph, including the benchmark, is flattered by that.
- `random_top5` is **one single random draw** (seed 42). See Part D: it's an unlucky one.

### ✅ Takeaway
Strategies beat SPY and random, but compare with the equal-weight basket, and most of the edge arrived in one stretch.

---

# Graph 2 — Drawdowns ("how deep was the hole?")

![[06_g2_drawdowns.png]]

### 🧠 The idea
A **drawdown** at any day = *how far below its highest-ever value* the strategy currently is.

$$\text{drawdown}_t=\frac{\text{value}_t}{\text{highest value so far}}-1$$

Analogy: climbing a mountain with ups and downs. At every moment you ask, *"how far below my highest point so far am I standing?"* **0 = standing at a new peak. −0.30 = you're 30% below your best.** It shows the *emotional* risk of a strategy: could you stomach it?

### 👀 How to read it
- Line at **0** = at an all-time high.
- **Lower = deeper hole.** A long stretch below zero = a long time underwater (still waiting to recover).
- All 7 lines are on one chart.

### 🔎 What it shows (worst fall for each, from the table)
| Line | Max drawdown |
|---|---|
| SPY | **−24.5%** |
| top5_vsmom_21d | −35.8% |
| top5_vsmom_63d | −40.9% |
| eq_weight_universe | −42.7% |
| top5_mom_63d | −43.7% |
| random_top5 | −53.5% |
| ls_vsmom_63d | **−57.1%** (March 2023) |

- **Everything bottoms out in late 2022 – early 2023**, all within roughly the same few months. This is the same crypto/tech bear market.
- **A second dip in 2025** (tariff shock era), with the momentum strategies reaching −0.25 to −0.38.
- **The long-short strategy (red) has the worst hole, and falls hard again at the very end of the sample (−0.40 by September 2026).**
- SPY (pink) stays near the top the whole time.

### 💡 So what?
1. **The strategies did not protect you in the 2022 bear market.** They hold the same risky assets as the basket, so they sank together. Momentum-by-ranking is not a hedge.
2. Higher returns came with **roughly 1.5× to 2× SPY's worst fall**. That's the price of the 40–75% annual return.
3. The long–short (which should in theory cancel the market) was the **deepest** hole, which tells you it was not reliably "market-neutral" and the ranking sometimes got it badly wrong.

### ⚠️ Trap
A max drawdown is **one number from one path**. Worse could easily have happened with different luck. It's a lower bound on the pain, not a guarantee.

### ✅ Takeaway
All strategies had deep holes in 2022–23, much deeper than SPY, and the long–short was worst.

---

# Graph 3 — Rolling Sharpe ("how are we doing lately?")

![[06_g3_rolling_sharpe.png]]

### 🧠 The idea
The Sharpe in the table is **one number for 5.7 years**. But strategies have good periods and bad ones. So we compute a **Sharpe ratio for every 126-day stretch (about 6 months)**, sliding forward one day at a time, like the "rolling" meters in Task 03 and 05. It answers: *"how well has this been working over the **last half-year**?"*

### 👀 How to read it
- **y-axis** = the Sharpe over the last 126 days (annualised).
- **Above the dashed zero line** = profitable half-year. **Below** = losing half-year.
- Higher = more return per unit of bumpiness in that window.

### 🔎 What it shows
- **Huge swings.** Every line moves between about **−3 and +6**. A strategy that is "excellent" (Sharpe > 3) in one half-year is "terrible" (< −2) a year later.
- **The lines move together.** The strategies and the equal-weight basket rise and fall in the same months: **peak in early 2024** (the equal-weight line touches ≈ 5.9), **trough in late 2022** (≈ −3.3 for the momentum strategies).
- **The long–short (red) behaves differently:** it hugs zero or sits below it through 2021–2022, is positive in 2024–25, and plunges to about **−2.4 at the very end (Sept 2026)**.
- There is **no strategy that is reliably above the equal-weight line.** They cross it again and again.

### 💡 So what?
1. **Six-month results are mostly luck and market mood.** Any 6-month stretch can look brilliant or awful. This is why we never judge a strategy on a short window.
2. **The lines moving together is the key insight:** most of what these strategies earn is "the 20-asset basket went up" (the shared **market tide**), not the ranking skill. Only the long–short line, which cancels the tide, moves independently, and it's much weaker.
3. A strategy that looks great overall can have long stretches of **negative** rolling Sharpe, which is the stretch where real investors lose patience and quit.

### ⚠️ Trap
Rolling windows overlap heavily, so neighbouring points are almost the same data. Smooth-looking lines don't mean many independent observations.

### ✅ Takeaway
Performance is wildly unstable half-year to half-year and is mostly driven by the shared tide.

---

# Part D — The honest verdict (extra checks beyond the three graphs)

These checks use the same data as the script. I ran them to answer: *is the impressive scoreboard real skill, or the basket?*

## Check 1 — Is the right yardstick the equal-weight basket? Yes.
SPY and random aren't fair: SPY is a different set of assets, and the **basket itself earned 41.8%/yr**. A fair test: *do the strategies beat the basket they pick from?* Average extra return per year over the basket, and how strong the evidence is (t-stat, Task 05's Concept 2):

| Strategy | Extra return vs basket, per year | t-stat | Verdict |
|---|---|---|---|
| top5_vsmom_21d | **+21.1%** | **+1.86** | Best case: borderline, just under the usual "unlikely luck" bar of 2 |
| top5_mom_63d | +13.8% | +1.03 | Not distinguishable from luck |
| top5_vsmom_63d | +7.7% | +0.68 | Not distinguishable from luck |
| ls_vsmom_63d | −16.1% | −0.67 | Underperforms |

**In words:** "good-looking" is not "proven". Even the best one has a t-stat below 2.

## Check 2 — Is `random_top5` a fair "luck" benchmark? No: it was a bad draw.
The script uses **one random run** (seed 42): Sharpe 0.66. I re-ran random top-5 with **150 different seeds**:

- **Average Sharpe 1.22** (spread ±0.32), average annual return ≈ **41%**, nearly identical to the basket (as it should be: random picks have no skill, so on average they equal the basket).
- Seed 42's 0.66 sits near the bottom of that range. **The "floor" on the scoreboard is lower than it should be.**

How often does pure luck beat each strategy's Sharpe?

| Strategy | Sharpe | Random seeds that did as well |
|---|---|---|
| top5_vsmom_21d | 2.29 | **0.7%** (1 in 150) |
| top5_vsmom_63d | 1.65 | 6% |
| top5_mom_63d | 1.47 | **19%** (barely better than average luck) |

**So:** `vsmom_21d` is the only one that clearly beats luck. `mom_63d` is **indistinguishable from random picking.**

## Check 3 — Where does the long-only profit come from? Mostly the tide.
For `vsmom_63d`, average yearly return (simple average, ×252):
- Basket of all 20 assets: **35.0%**
- The **long** leg (top 5): **42.6%**, only about **7.6 points** better than average.
- The **short** leg (the bottom 5 that we short): those assets **still rose 23.8%/yr**, so shorting them **lost** money.

That is why the long-short earned only ~21% (Sharpe 0.47) while the long-only earned 53%: **the long side was riding a rising tide, and the short side fought against it.** The ranking has *some* edge, but it's small.

## Check 4 — Costs (rough illustration)
Turnover 0.158 per day means about 15.8% of the portfolio is bought (and the same sold) every day. If each trade costs **0.1%** (an optimistic number, particularly for crypto), the yearly drag is roughly

$$0.1\%\times 2\times0.158\times252\approx 8\%\ \text{per year}$$

for `vsmom_21d` (about 4% for the two 63-day strategies, about 10% for the long–short). The best strategy's edge over the basket (+21%) could survive modest costs, but its real cost depends on crypto's spreads and slippage. **Task 10 must test this properly.**

## Things to keep in mind (caveats)
1. **We looked at four strategies and are admiring the best one.** Picking the winner of 4 makes it look better than it is (a mild form of the lottery-ticket problem from Task 05).
2. **No train/test split.** Nothing was *fitted*, so it isn't overfitting in the usual sense, but the whole result is on one 5.7-year path that we've already studied in Tasks 03–05.
3. **Hindsight universe.** The assets were chosen using today's knowledge.
4. **Strategies sat in cash ~64 days** while benchmarks were invested.
5. **Task 05 consistency.** Task 05 §13.10 recommended baselining `mom_21d` (1-day) and `vol_ratio_20d` (3-day). Task 06 instead ran `vsmom_63d` (the starting hypothesis), `vsmom_21d`, `mom_63d` and a long–short. In Task 05 `vsmom_21d` had the *weakest* IC (0.0028, t = 0.35) and `vsmom_63d` was also weak (0.0053), yet `vsmom_21d` has the best portfolio here. This isn't a contradiction: **IC averages the ranking quality of all 20 assets, a top-5 portfolio only cares about the very top**, and Task 05's quintile graph shows `vsmom_21d`'s edge sat in its top group. But it means the Task 05 recommendation hasn't been tested yet.

## 🧭 Summary

| Graph / check | Verdict |
|---|---|
| G1 Equity curves | Long-only rank strategies beat SPY and random; only `vsmom_21d` clearly beats the basket; edge concentrated in late 2023–2024 |
| G2 Drawdowns | All sank 35–57% in 2022–23, vs SPY's −24.5%; long–short is worst |
| G3 Rolling Sharpe | −3 to +6 swings; everything moves with the market tide |
| Check 1 | Best excess vs basket: +21%/yr, t = 1.86 (borderline); others not distinguishable from luck |
| Check 2 | One random seed was misleadingly bad; real "luck" average Sharpe ≈ 1.22; `vsmom_21d` beats 99% of random runs, `mom_63d` only 81% |
| Check 3 | The long side's edge is small (+7.6 pts); the short side loses money |
| Check 4 | Daily trading costs could remove roughly 4–10 points a year |

**Bottom line:** the best baseline (`vsmom_21d` top-5) is a **promising candidate, not a proven strategy**. The target for later models is **Sharpe ≈ 1.5 (the basket) and ≈ 2.3 (the best baseline), after costs and out-of-sample**, not the SPY or random lines.

**Back to:** [[_Graph Explanations - README]]
