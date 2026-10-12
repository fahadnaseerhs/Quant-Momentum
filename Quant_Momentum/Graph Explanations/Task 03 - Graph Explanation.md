# Task 03 — Graph Explanation (Exploring Returns)

**Full write-up of the task:** [[03 - Exploring Returns]] · **Index:** [[_Graph Explanations - README]] · **Dictionary of every label:** [[Graph and Table Labels]]

> **How to use this note.** It is written so you *understand*, not just read. Every graph has the same parts:
> 🧠 **The idea first** → 👀 **How to read the picture** → 🔎 **What it shows** → 💡 **So what?** → ⚠️ **Common trap** → ✅ **One-line takeaway**.
> Words are explained the first time they appear.

## What is Task 03 even about?

Before building any trading signal, we **look at how returns behave**, like a doctor examining the patient before prescribing. Six questions, six graphs:

| # | Question (plain words) | Short answer |
|---|---|---|
| 1 | What would \$1 invested in each asset have become? | Huge differences; clear boom/bust periods |
| 2 | Is "bumpiness" constant? | No, it comes in waves |
| 3 | Are returns "normal"? | No, wild days are far more common than the textbook says |
| 4 | Which assets move together? | About 5 groups; ~4 truly different bets in 20 assets |
| 5 | Does yesterday's return predict today's? | No consistent pattern |
| 6 | Does yesterday's *size of move* predict today's size? | Yes, strongly |

**Marks on many pictures:** dotted vertical lines are real events (2022 bear market · FTX collapse Nov 2022 · tariff shock Apr 2025 · gold crash Jan 2026). The dashed grey line is **SPY**, the US stock market, drawn as a yardstick.

---

# Graph 1 — Growth of \$1

![[03_g1_growth_of_1.png]]

### 🧠 The idea first
Imagine you had put **\$1 into each asset on day one (4 Jan 2021)** and never touched it. How much is it worth now? This is the simplest, most honest way to see what each asset "did".

### 👀 How to read the picture
1. **Six panels**, one per asset class. SPY (grey dashed) is repeated in each so you can compare.
2. **The y-axis is a log scale.** On a log scale, equal *distances* mean equal *percentage* moves. \$1→\$2 (+100%) looks the same height as \$10→\$20 (+100%). Without it, SOL's rise to \$100 would squash everything else flat.
3. The **black horizontal line is \$1**: above it you made money, below it you lost money.
4. A **steep** line = fast growth. A **jagged** line = bumpy. **Lines that move together** = assets that behave alike.

### 🔎 What it shows
| Class | Story |
|---|---|
| **Crypto** | SOL ended near **\$49** but peaked near \$100 and had a **−96%** crash on the way. LINK ended about \$1 after a −90% fall. BTC and ETH ended around \$2–3. |
| **Tech** | NVDA ≈ **\$17**, GOOGL ≈ \$4, the rest ≈ \$2.5. META dropped to about \$0.45 in late 2022. |
| **Gold** | GLD ≈ \$2.3. The gold miner **B** lagged for years, then rocketed in 2025–26. Both fell at the Jan 2026 gold crash. |
| **Oil** | All three roughly tripled, far ahead of SPY. |
| **Real assets** | MSTR is a rollercoaster (looks like crypto). VNQ and DBC are quiet. |
| **Bonds** | TLT **lost about 39%** (rates rose). SHY is a flat line near \$1.1. |

You can also spot **regimes** (periods with a shared mood): in **2022** stocks, bonds *and* crypto all fell together; 2023–24 was a recovery; April 2025 was a sudden dip.

### 💡 So what?
1. **Regimes exist**, so later we must test a strategy separately in each type of market, not just on the average.
2. Assets in a class move together (Graph 4 puts numbers on this).
3. **Data check:** if a line suddenly fell off a cliff with no real-world reason, that would mean a data error. None remain.

### ⚠️ Common trap
This is *looking back with hindsight*. "SOL turned \$1 into \$49" does **not** mean it was a good bet: you would have had to sit through a −96% crash. This graph describes the past; it does not prove an edge.

### ✅ Takeaway
Returns differ enormously between assets, and markets move in moods (regimes).

---

# Graph 2 — Volatility (bumpiness) over time

### 🧠 The idea first
In Task 02 we measured one bumpiness number per asset. But is a road equally bumpy the whole way? Or is it smooth for miles, then suddenly rough? If volatility **changes over time**, then one fixed number per asset is a bad description.

## 2a — 63-day rolling volatility

![[03_g2_rolling_vol.png]]

**What "rolling" means.** Every day, look only at the **last 63 trading days (about one quarter)**, compute the bumpiness, write it down. Next day, slide the window forward by one day and repeat. It is like a **moving "how rough was the last quarter?" meter**.

### 👀 How to read it
Each line = one asset. The y-axis is annualised volatility in % per year. Higher = rougher period. SPY is dashed.

### 🔎 What it shows
- **Not flat. Wavy.** SPY swings between about 9% and 34%. NVDA between about 30% and 80%. MSTR between 47% and 160%.
- **Crypto calms down over the years:** from 100–230% in 2021 to roughly 35–60% by 2026.
- The big SPY block in **April 2025** is the tariff shock.

### 💡 So what?
Calm periods and stormy periods come in **streaks**. This is called **volatility clustering**. Because of it, we can't use a single volatility number per asset; we need one that **updates over time**.

## 2b — Volatility compared with SPY

![[03_g2_vol_relative_to_spy.png]]

### 🧠 The idea
Instead of asking "how bumpy?", ask "**how many times** bumpier than the stock market?" 1× means as bumpy as SPY. 3× means three times as bumpy.

### 👀 How to read it
Each line is the **middle value (median)** of the class. **Log y-axis** again (1×, 10×).

### 🔎 What it shows
- **Crypto: about 3× to 16×** the market.
- **Bonds: about 0.3× to 1×.**
- Tech and oil: usually **1.5× to 3×**.
- **Notice April 2025:** *every* line drops at once. Not because everything calmed down, but because **SPY itself became very bumpy**, so the denominator exploded.

### 💡 So what?
How risky an asset is **relative to others** is not fixed either. If we compare assets using one fixed risk number each, the comparison will be wrong at some times. So the risk number used in our feature must **update daily**.

## 2c — Two ways to measure bumpiness: window vs EWMA

![[03_g2_rolling_vs_ewma.png]]

### 🧠 The idea
- **Rolling window (blue):** counts the last 63 days **equally**. Day 1 and day 63 matter the same, and day 64 is suddenly ignored.
- **EWMA (orange)**: *Exponentially Weighted Moving Average*. A **memory that fades**: yesterday matters most, two days ago a bit less, and so on. Settings used: λ = 0.94 (the standard from the bank-risk world "RiskMetrics").

Analogy: the blue meter remembers the last 63 days like a **notebook**; the orange meter remembers like a **human**, vividly recent, fuzzy older.

### 👀 How to read it
Three panels: SPY, Bitcoin, gold (GLD). Both lines estimate the same thing: bumpiness.

### 🔎 What it shows
- When a shock hits (SPY in April 2025; gold in January 2026), **orange jumps within days** (SPY to ~52%), blue rises slowly (~33%).
- Then blue **stays high like a plateau and suddenly falls off a cliff** about three months later. Nothing happened in the market that day. The shock simply **left the 63-day window**. (A "ghost" effect.)
- Orange fades smoothly: a shock's influence halves about every **11 trading days**.

### 💡 So what?
EWMA reacts faster and doesn't have fake cliffs, so it is our default for risk in Task 04.

### ✅ Takeaway for Graph 2
Volatility comes in **waves**; relative risk between assets also shifts; and EWMA tracks it better than a plain window.

---

# Graph 3 — "Normal" returns vs real returns (fat tails)

### 🧠 The idea first
Most textbook maths assumes returns follow a **normal distribution** (the "bell curve"). Think of the heights of adult men: most near average, very few extremes, and a 3-metre man basically never exists.

**Real market returns are not like that.** Every so often a 3-metre man shows up. These shockingly big days happen **far more often** than the bell curve allows. This is called **fat tails** ("tails" = the far left and far right ends of the curve).

To measure it we use one number:
- **Excess kurtosis**: 0 = exactly bell-shaped. The bigger the number, the fatter the tails.

We also use **z-scores**: a return measured in "how many standard deviations from normal". A day of **+3σ** (σ = standard deviation, the typical size of a wiggle) should happen about once in 370 days if returns were normal. A **+9σ** day should essentially never happen.

## 3a — Histograms and QQ plots

![[03_g3_hist_qq.png]]

### 👀 How to read it
**Top row — histogram.** Bars show how many days had each z-score. The **red curve** is the bell curve a normal market would give. The **y-axis is log**, so the rare extreme days (tiny bars) are visible. **Bars sticking out beyond the red curve at the far left/right = fat tails.**

**Bottom row — QQ plot.** (Q = quantile.) Imagine lining up all your days from worst to best, and next to them lining up what a perfect bell curve *would* give. Each dot compares the two.
- **Dots on the red straight line = looks normal.**
- **Dots that peel away at the ends = fat tails.** An "S" shape is the classic fat-tail signature: the lowest dots fall *below* the line (crashes bigger than normal predicts), the highest rise *above* it (rallies bigger than predicted).

### 🔎 What it shows
| Asset | Excess kurtosis | What happened |
|---|---|---|
| **SPY** | **7.9** | One day at **+9.5σ** (the April 2025 rebound), which "should never happen" |
| **NVDA** | 3.7 | +6.8σ and −5.9σ days |
| **BTC** | 4.7 | A −7.1σ day |
| **TLT** | 0.6 | Dots hug the line: almost normal |

All 21 assets have positive excess kurtosis (from 0.6 up to 23.5).

### 💡 So what?
Extreme days are **bigger and far more frequent than the textbook** says, and a few of them can wreck an ordinary average. So the project uses **rank-based** methods (only the *order* matters, not how huge a move was) and caps extreme feature values later.

## 3b — Does dividing by risk fix the fat tails?

![[03_g3_kurtosis_before_after.png]]

### 🧠 The idea
Maybe the wild days only look wild because **risk was already high** that day. So we divide each return by *yesterday's* risk level (EWMA volatility) and recheck the tails. If the tails shrink, it was just risk changing.

### 👀 How to read it
Blue bar = excess kurtosis of raw returns. Orange = after dividing by yesterday's risk. **Orange shorter than blue = tails got thinner (good). Orange taller = tails got fatter.**

### 🔎 What it shows
- **Thinner tails:** SPY (8.2→2.2), GLD (7.8→2.0), SOL, AAPL, SHY, MSTR, VNQ.
- **Fatter tails (7 of 21):** META (23.5→29.1), NVDA (3.8→7.4), GOOGL (3.2→5.5), LINK, AVAX, B, ETH (barely).

### 💡 So what? Two kinds of wild days
1. **Regime wild days.** The market was already stormy. Dividing by risk cancels them. (Indices, ETFs.)
2. **Jump wild days.** A sudden surprise (e.g. earnings) arrives in a **calm** period. Yesterday's risk was low, so dividing by it makes the surprise look **even bigger**.

So dividing by risk fixes half the problem. Rank-based methods are still needed.

## 3c — The same, as QQ plots

![[03_g3_qq_raw_vs_scaled.png]]

Blue dots = raw returns, orange dots = after dividing by risk. For **SPY** the orange dots hug the line better. For **NVDA** and **BTC** the orange dots still curl away at the ends, and NVDA's left end gets worse. This is the "picture version" of 3b.

### ✅ Takeaway for Graph 3
Real returns have fat tails. Dividing by recent risk helps for indices but not for assets with sudden jump days.

---

# Graph 4 — Who moves with whom? (correlation)

### 🧠 The idea first
**Correlation** measures whether two things move together, on a scale from −1 to +1.
- **+1**: perfectly together (two friends walking the same dog).
- **0**: unrelated.
- **−1**: perfectly opposite (a seesaw).

Why care? If you own 20 assets that all move together, you don't really own 20 different bets, you own the same bet 20 times. That is a **diversification** question.

## 4a — The clustered heatmap

![[03_g4_corr_clustered.png]]

### 👀 How to read it
1. It's a **grid**: every asset on the left against every asset on the bottom. Each cell is the correlation of that pair.
2. **Colour:** dark red = move together, white = unrelated, blue = move opposite. The number is printed in the cell.
3. The **tree on the top and left** (a *dendrogram*) groups similar assets; branches that join low = very similar.
4. Assets are **reordered so similar ones sit together**, which makes **red squares along the diagonal** = groups.

### 🔎 What it shows: five groups
| Group | Proof |
|---|---|
| **Crypto + MSTR** | BTC–ETH 0.82, ETH–LINK 0.79, **MSTR–BTC 0.72** |
| **Oil** | XOM–CVX 0.86, **USO–DBC 0.91** |
| **Gold** | GLD–B 0.73 |
| **Bonds** | TLT–SHY 0.61 |
| **US stocks** | SPY with AAPL 0.71, NVDA 0.70, MSFT 0.69, GOOGL 0.67 |

Also: oil vs long bonds are slightly **opposite** (TLT–USO −0.19).

### 💡 So what?
**Labels lie, behaviour doesn't.** MSTR is a stock but trades like crypto. DBC is "commodities" but trades like oil.

## 4b — Group-level view

![[03_g4_class_block_corr.png]]

**How to read:** the **diagonal** = how much assets inside one class move together; **off-diagonal** = between classes.
**Shows:** inside: gold 0.73, oil 0.69, crypto 0.68, bonds 0.61, tech 0.51, **real assets just 0.17** (a label, not a real group). Between classes it's mostly 0.02–0.3, and oil–bonds is **−0.13**.

### 🧮 How many *real* bets do we have?
Average pairwise correlation across the 20 assets: **0.21**. The formula for the **effective number of bets** is

$$N_{eff}=\frac{N}{1+(N-1)\bar\rho}=\frac{20}{1+19\times0.21}\approx3.9$$

**Meaning:** 20 assets, but it behaves like **~4 independent bets**. Like a meeting with 20 people but only 4 different opinions. This is why Task 05 tests ranking both across everything and within each group.

## 4c — "Is the correlation fooled by a few crazy days?"

![[03_g4_pearson_minus_spearman.png]]

### 🧠 The idea
There are two ways to compute correlation: **Pearson** (cares about *how big* the moves are) and **Spearman** (only cares about *order*, which is more robust). If they disagree a lot, a few extreme days are distorting the picture.

### 👀 / 🔎
Each cell = Pearson − Spearman. All gaps are small: **−0.08 to +0.11**.

### 💡 So what?
The groups in 4a are **real**, not outlier artefacts. Using rank-based (Spearman) methods later will not change the picture.

## 4d — Does correlation change in a crisis?

![[03_g4_rolling_avg_corr.png]]

### 👀 How to read
The line = **average correlation among the 20 assets**, recomputed daily over the last 63 days. Dashed line = overall average (0.21).

### 🔎 What it shows
- It climbs to **0.43 around the FTX collapse (Nov 2022)**.
- Another plateau at **~0.35 in April–July 2025** (tariff shock), then a sudden fall when the shock leaves the window (same "ghost" as 2c).
- Calm periods drop to about **0.10**.

### 💡 So what?
**In a crisis everything moves together.** Diversification fails exactly when you need it. Our strategy must be tested in these periods separately.

### ✅ Takeaway for Graph 4
There are ~5 groups, ~4 real bets, and correlation rises in a crisis.

---

# Graph 5 — Does yesterday predict today? (autocorrelation)

### 🧠 The idea first
**Autocorrelation** = correlation of a series **with its own past**. For returns: *if an asset went up yesterday, is it more likely to go up today?*

- **Positive autocorrelation = momentum** (winners keep winning).
- **Negative = reversal** (winners give back).
- **Zero = like coin flips: the past tells you nothing.**

**Lag** = how many days back. Lag 1 = yesterday vs today. Lag 2 = two days ago vs today.

The **grey band** on these graphs is a **"noise zone"**. A bar *inside* it could easily be pure luck. Only bars well *outside* are interesting. (The band is ±1.96/√T; you don't need to memorise it. Think of it as "the wobble that coin-flip data gives anyway".)

## 5a — Daily returns, lags 1–10

![[03_g5_acf_daily.png]]

### 👀 How to read it
21 small charts, one per asset. Each bar is the autocorrelation at that lag (green positive, red negative). **Bars inside the grey band = no evidence.** The dashed lines are a stricter band that allows for stormy-streak data.

### 🔎 What it shows
Almost all bars sit **inside** the band. A few poke out slightly (AVAX lag 10 −0.09, TLT lag 2 −0.07, USO lag 10 −0.07), and **signs are mixed**, no pattern like "crypto trends, stocks reverse". The biggest |lag-1| in the whole universe is **0.058**, which means yesterday explains about **0.34%** of today.

### 💡 So what? The "lottery ticket" check
We ran about **210 tests** (21 assets × 10 lags). At a 5% threshold, pure luck gives **about 10 bars outside the band**. We saw **about 9**. That's exactly what luck predicts. So: **an asset's own last 1–10 days don't predict its next day.**

> This is *not* the end of momentum. It only rules out one kind (own-history, 1–10 days). Task 05 tests a different kind: **ranking assets against each other.**

## 5b — 3-day returns that don't overlap

![[03_g5_acf_3day_nonoverlap.png]]

Same idea, using **3-day total returns in separate, non-overlapping blocks** (479 blocks). Bars outside the band: AVAX +0.14 and LINK −0.14 at lag 1, SPY about −0.105 at lags 1–2. With ~100 tests, a few edge-touching bars are expected. Again: **nothing consistent.**

## 5c — The overlap trap (very important)

![[03_g5_overlap_trap.png]]

### 🧠 The idea
Suppose each day's return is **pure random noise**. Now take 3-day returns **every day**:
- Monday's 3-day return = Tue + Wed + Thu.
- Tuesday's 3-day return = Wed + Thu + Fri.

They **share Wed and Thu**, so they look strongly related even though nothing is predictable! That's an **accounting illusion**, not momentum.

### 🔎 What it shows (Bitcoin)
- **Blue bars** (overlapping): 0.67 at lag 1, 0.34 at lag 2.
- **Grey bars** (what pure noise gives from overlap alone, $1-k/3$): 0.67 and 0.33. **Identical.**
- **Orange bars** (non-overlapping blocks): **≈ 0.** The honest answer.

### 💡 So what?
- Never read overlapping multi-day returns as momentum.
- It is why our 3-day targets need a **gap (embargo)** between training and testing data later.

### ✅ Takeaway for Graph 5
No consistent short-term pattern in an asset's own returns, and beware overlap illusions.

---

# Graph 6 — Does yesterday's *size* predict today's size?

### 🧠 The idea first
Even if the **direction** (up/down) is unpredictable, the **size** of the move can be very predictable. Weather analogy: you can't say if tomorrow will be warmer than today, but if there's a storm today, a storm tomorrow is likelier. This is **volatility clustering**.

To measure size without direction we use:
- **Squared returns** $r^2$ (always positive; bigger move = bigger number), or
- **Absolute returns** $|r|$ (the move ignoring its sign). This is more robust because squaring lets one giant day dominate.

## 6a — Autocorrelation of squared returns

![[03_g6_acf_squared.png]]

### 👀 How to read it
Same layout as 5a, but purple bars and lags 1–20.

### 🔎 What it shows
**Unlike Graph 5, bars are almost all positive and many far above the band.**
- SHY: ~0.30 at lags 1 and 2. GLD and AVAX: ~0.30 at lag 2.
- USO and TLT: positive across **all 20 lags**.
- META, MSFT, GOOGL, NVDA look flat, **but that's an artefact**: their few giant days dominate the squares. Using $|r|$ instead, **18 of 21 assets show clear clustering** (versus only 8 of 21 using $r^2$).

### 💡 So what?
A big move today means a big move tomorrow is more likely, whichever direction. This is the statistical proof of the "waves" you saw in Graph 2.

## 6b — Size vs direction, side by side

![[03_g6_size_vs_direction.png]]

### 👀 How to read it
Each line = the **median across all 21 assets** at each lag. Grey band = noise zone.

### 🔎 What it shows
- **Orange $|r|$:** starts ~0.125, still ~0.07–0.09 at lag 20. **Always above the band.**
- **Blue $r^2$:** starts ~0.11 and fades toward 0.03.
- **Green, raw returns (direction):** wobbles around 0 and **never leaves the band.**

### 💡 So what? "Direction is unpredictable, size is predictable."
1. We can forecast **risk** reasonably well → use time-varying volatility.
2. We **can't** forecast direction from an asset's own past → any edge must come from elsewhere.
3. Neighbouring days are **not independent**, so later significance tests must use special error bars (Newey–West).

### ✅ Takeaway for Graph 6
Risk is forecastable; direction (from own past) is not.

---

# 🧭 What Task 03 means for the next step

| What we learned | What we do about it (Task 04) |
|---|---|
| Volatility moves in waves; relative risk changes | Divide momentum by a **daily-updated** risk number (EWMA) |
| Fat tails, only half fixed by dividing by risk | Use **ranks**, and cap extreme feature values |
| ~5 groups, ~4 real bets | Test ranking across everything **and** inside each group |
| Own past (1–10 days) doesn't predict | Build several lookbacks (5, 10, 21, 63 days) and let Task 05 decide |
| Clustering lasts 20+ days | Use Newey–West error bars in all later tests |

**Next:** [[Task 04 - Graph Explanation]]
