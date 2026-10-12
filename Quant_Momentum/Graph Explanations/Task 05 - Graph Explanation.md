# Task 05 — Graph Explanation (Signal Analysis)

**Full write-up of the task:** [[05 - Signal Analysis]] · **Index:** [[_Graph Explanations - README]] · **Dictionary of labels:** [[Graph and Table Labels]] · **Previous:** [[Task 04 - Graph Explanation]]
**Code:** `scripts/05_signal_analysis.py` (plots) and `src/signals.py` (maths)

> **How to use this note.** Written so you *understand*, not just read. First you learn **6 short concepts** (Part A). Then every graph has: 🧠 **The idea** → 👀 **How to read it** → 🔎 **What it shows** → 💡 **So what?** → ⚠️ **Trap** → ✅ **Takeaway**.
> If you only read one part, read Part A. Once those click, every graph below is easy.

---

# Part A — The six concepts you need

## What is Task 05 asking?
In Task 04 we built clues (features). Now the first real test:

> **Does a clue we know at the end of today tell us anything about which assets will do better tomorrow?**

We're not asking "will BTC go up?". We're asking: **"among these 20 assets, can the clue tell me who will be among the better ones and who among the worse ones?"** (This is called *cross-sectional* ranking.)

---

## Concept 1 — IC (Information Coefficient): "how good was my ranking?"

**Analogy: guessing a horse race.** Before a race you rank 5 horses by your hunch. After the race you compare your ranking with the finishing order.
- Your ranking exactly right → score **+1**.
- Basically random → score **≈ 0**.
- Exactly backwards → score **−1**.

That score is the IC. In our project the "horses" are the 20 assets, the "hunch" is a clue (like 21-day momentum), and the "race result" is the next day's return. **We do this once per day**, so we get about 1,400 IC values.

**Tiny worked example (5 assets).**

| Asset | Rank by clue | Rank by next-day return | Difference d |
|---|---|---|---|
| A | 5 | 4 | 1 |
| B | 3 | 3 | 0 |
| C | 1 | 1 | 0 |
| D | 4 | 5 | −1 |
| E | 2 | 2 | 0 |

$$\text{IC}=1-\frac{6\sum d^2}{n(n^2-1)}=1-\frac{6\times2}{5\times24}=1-0.1=0.9$$

Almost right. (You don't have to memorise the formula; the idea is "how close are the two orderings?")

**Why ranks and not raw values?** Returns have **fat tails** (Task 03). One +40% day would dominate an ordinary calculation. Ranks only care about **order**, so one crazy day can't hijack the answer.

**What is a good IC?** In daily stock prediction, **0.02 to 0.05 is already decent.** If you ever see 0.3, suspect a bug or cheating. Markets are very hard to predict, so *small* is *normal*.

---

## Concept 2 — "Is it real, or luck?" the t-stat

Since each day's IC is noisy, we average them all: the **mean IC**. But averages can be flukes. A **coin analogy:** if you flip a coin 10 times and get 6 heads, you wouldn't claim the coin is rigged. If you get 600 heads in 1,000 flips, you would.

The **t-stat** puts a number on this:

$$t=\frac{\text{mean IC}}{\text{its uncertainty (error margin)}}$$

- **|t| under 1** → basically noise.
- **|t| around 2** → "unlikely to be luck" (roughly a 5% chance it is).
- **|t| 3 or more** → strong evidence.

**The uncertainty is calculated with "Newey–West" (NW).** Plain words: normal formulas assume each day is independent. But markets have stormy streaks and our 3-day windows overlap, so neighbouring days are related. Ignoring that would make the error margin **too small** and results look **too convincing**. Newey–West widens the margin honestly.

---

## Concept 3 — Quintiles: "what is the ranking worth in money?"

IC says "the ranking agrees a bit". To see it in returns:
1. Each day, sort the 20 assets by the clue.
2. Cut into **5 groups of 4**: **Q1 = weakest clue, Q5 = strongest clue**.
3. Average each group's **next-day return** over all days.

If the clue works, you'd expect a **staircase**: Q1 lowest, Q5 highest. **Q5 − Q1 ("the spread")** = what "buy the top 4, short the bottom 4" would have earned **on paper, before costs**.

---

## Concept 4 — Hit rate

The % of days on which the IC was **positive** (the clue pointed the right way). **50% = coin flip.** 53% = slightly better than a coin.

---

## Concept 5 — The multiple-testing trap ("lottery tickets")

A t-stat above 2 means "only a ~5% chance this is luck", **for one test**. But we ran **182 tests**. If you buy enough lottery tickets, someone wins by luck.

| Tests on pure noise | Expect to look "significant" by luck |
|---|---|
| 1 | 0.05 |
| 40 | ~2 |
| 100 | ~5 |

So **a lone t = 2.4 among many tests is not proof**. It is a candidate to double-check on fresh data. Real effects also tend to be **smooth**: if 21-day momentum works, 10-day and 63-day should lean the same way. Zig-zags = noise.

---

## Concept 6 — The three "hero" clues used in most graphs

| Colour | Clue | Meaning |
|---|---|---|
| 🟠 Orange | `mom_21d` | Return over the last 21 days |
| 🟢 Green | `vsmom_21d` | The same ÷ the asset's own risk |
| 🔵 Blue | `relret_21d` | The same minus SPY's 21-day return |

> **A key insight (it explains why you'll often see only blue lines).** `relret_21d` = `mom_21d` − (SPY's number). On any given day, SPY's number is **the same constant subtracted from every asset**. Subtracting the same number from everyone **cannot change the ranking**. So `relret_21d` and `mom_21d` give **identical results by mathematics**. The blue line is simply drawn on top of the orange.

---

# Part B — The headline table (the one you asked about)

| Feature | Horizon | Mean IC | NW t-stat | Hit rate | Q5−Q1 | N days |
|---|---|---|---|---|---|---|
| `vol_ratio_20d` | 3-day | +0.0263 | **+2.38** | 53.1% | +0.67% | 1,417 |
| `vol_ratio_20d` | 1-day | +0.0128 | +1.66 | 50.5% | +0.29% | 1,419 |
| `mom_21d` | 1-day | +0.0145 | +1.57 | 51.4% | +0.33% | 1,417 |
| `relret_21d` | 1-day | +0.0144 | +1.56 | 51.4% | +0.33% | 1,417 |
| `mom_21d` | 3-day | +0.0201 | +1.41 | 51.7% | +0.88% | 1,415 |

**Reading row 1 in plain words:** *"When an asset's volume was unusually high versus its recent norm, that asset tended to do slightly better over the next 3 days. The ranking was right on 53% of days (IC +0.026), and the t-stat of 2.38 is just past the 'probably not luck' bar. On paper, the top group beat the bottom group by 0.67% over 3 days."*

**But remember Concept 5:** one result just above 2 among many tests is a **candidate**, not proof.

---

# Part C — The seven graphs

---

# Graph 1 — Can we see the signal? (scatter)

![[05_g1_scatter_mom21d_vs_fwd1d.png]]

### 🧠 The idea
Plot **one dot per (asset, day)**: x = the clue today (`mom_21d`), y = what the asset returned **tomorrow**. If momentum predicted the future, the dots would form an **upward slope**.

### 👀 How to read it
There are 28,780 dots, coloured by asset class. The **white line** is the best straight-line fit. **Tilted up** = more momentum goes with higher next-day returns. **Flat** = no relation.

### 🔎 What it shows
A **horizontal blob**. The line's slope is **+0.0105**: 10 percentage points more 21-day momentum goes with only about 0.1 percentage points more return the next day, while individual days swing ±5–20%. **Vertical stripes at the left and right edges** are values capped by winsorising (mostly crypto).

### 💡 So what?
**You cannot see the signal by eye.** Noise dominates. That's exactly why we measure it with **ranks (IC)** instead of drawing lines through raw numbers. The graph exists to kill the idea that "just look at the scatter" is enough.

### ✅ Takeaway
Invisible to the eye → we need a better tool (IC).

---

# Graph 2 — IC every day, and its yearly average

![[05_g2_ic_timeseries.png]]

### 🧠 The idea
Compute the IC **every single day** (Concept 1), then plot it. To tame the noise, also plot the **rolling average**: *"the average IC over the last 252 trading days (≈ 1 year), recomputed every day."* Think of a **moving "how has this clue done in the last 12 months?" meter**.

### 👀 How to read it
Three panels (one per hero clue). In each:
- the **thin noisy line** = IC of each single day,
- the **thick line** = the 252-day rolling average,
- the **dotted line** = the average over the whole period (value printed in the legend).

**If the thick line is above zero, the clue was working that year. Below zero = it was working *backwards*.**

### 🔎 What it shows
| Clue         | Overall mean IC | Rolling IC ranges from…                | % of days rolling IC > 0 |
| ------------ | --------------- | -------------------------------------- | ------------------------ |
| `mom_21d`    | **+0.0145**     | −0.030 (Jun 2025) to +0.065 (Aug 2021) | 69%                      |
| `relret_21d` | +0.0144         | the same                               | 69%                      |
| `vsmom_21d`  | +0.0028         | −0.030 (Oct 2023) to +0.038 (Mar 2022) | 56%                      |

- **Daily** IC jumps between about **−0.9 and +0.9**. With only 20 assets, one day's ranking is extremely noisy. The typical wiggle is about **0.40**, while the average is only 0.0145.
- The thick line **drifts**: high in 2021–22, near zero or negative in 2023 and 2025, positive again from late 2025.

### 💡 So what?
- **No clue "always works".** It is a *small statistical tilt in a very noisy daily game*.
- `mom_21d` and `relret_21d` are the same line (see the key insight above).
- `vsmom_21d` is weaker. It barely differs from zero.
- The early period (2021–22) looked better than the later one. That's a warning for later: test on data the model never saw.

### ✅ Takeaway
A small average edge, hidden in big daily noise, which fluctuates in strength over the years.

---

# Graph 3 — Cumulative IC (the "odometer")

![[05_g3_cumulative_ic.png]]

### 🧠 The idea
**Add up** the daily ICs as you go: a running total. Analogy: a **car's odometer**. The **slope** of the line at any moment = the average speed = the average IC at that time.

### 👀 How to read it
- **Rising line** = the clue keeps paying.
- **Flat** = it has stopped working.
- **Falling** = it works backwards.
- A **single big jump then flat** = it worked once and never again (suspicious).

### 🔎 What it shows
- **`mom_21d` and `relret_21d`** (blue covering orange): up to ≈ 15 by mid-2022, **back down to ≈ 9 by late 2023**, up to ≈ 19 by mid-2024, **down to ≈ 11 by mid-2025**, then a **surge to ≈ 24 in March 2026**. Ends at about **+20.5**.
- **`vsmom_21d`**: peaks near 8.8 in 2022, drifts down to ≈ 0 in late 2025, ends at about **+3.8**.

### 💡 So what?
The overall direction is up, but it's a **slow grind with year-long pullbacks** (the 2024→2025 fall is about 8 units, a year of giving back). That is what a **weak-but-real** signal looks like. A fake one would look like a single step. And during the falling stretches, someone following the signal would have done *worse than random*.

### ⚠️ Trap
The old note called this "steady and gentle". The picture shows it is **choppy**.

### ✅ Takeaway
Persistent upward drift, with long painful pullbacks.

---

# Graph 4 — Quintile bar charts (the signal in money terms)

![[05_g4_bucket_bar.png]]

### 🧠 The idea
This is **Concept 3**. Each day: sort the 20 assets into 5 groups of 4 by the clue; average each group's next return across all days.

### 👀 How to read it
- **x-axis** = group (1 = weakest clue, 5 = strongest).
- **Bar height** = average next-period return (%).
- **Black whiskers** = ±1 "standard error" (the uncertainty). If the whisker crosses zero, that bar can't be told apart from zero.
- **Left column** = next **1-day** return, **right column** = next **3-day** return.
- Rows = `mom_21d`, `vsmom_21d`, `relret_21d`. The title gives the **Q5 − Q1 spread**.

### 🔎 What it shows (average return, %)
| Clue, horizon | Q1 | Q2 | Q3 | Q4 | Q5 | **Q5 − Q1** |
|---|---|---|---|---|---|---|
| `mom_21d`, 1-day | 0.016 | 0.075 | 0.048 | 0.121 | **0.351** | **+0.335** |
| `mom_21d`, 3-day | 0.085 | 0.227 | 0.200 | 0.339 | **0.966** | **+0.881** |
| `vsmom_21d`, 1-day | 0.046 | 0.062 | 0.058 | 0.091 | **0.277** | +0.231 |
| `vsmom_21d`, 3-day | 0.119 | 0.222 | 0.162 | 0.290 | **0.789** | +0.670 |

- The pattern is a **rough staircase, but not clean**: Q3 dips below Q2, and the real jump is **Q5**. Most of the spread comes from the top group.
- The 3-day spreads are about **2.6×** the 1-day ones (three days of return instead of one).
- Q1's whisker crosses zero.

### 💡 So what?
There is a tilt: **the strongest-momentum group does earn more**. But because the staircase is driven by Q5, it could reflect one or two assets, or simply crypto's higher average returns (crypto is often in Q5). And **these are before transaction costs**. With daily trading, costs could eat all of it (Task 10).

### ⚠️ Trap
Each group has only **4 assets**, so bars are noisy.

### ✅ Takeaway
The top group earns more, but the evidence is "suggestive", not "clean".

---

# Graph 5 — The big scoreboard (heatmap)

![[05_g5_ic_heatmap.png]]

### 🧠 The idea
One table for **every clue × both horizons**: the mean IC (Concept 1) and the t-stat (Concept 2).

### 👀 How to read it
- **Rows** = clues (`mom_5d` … `vol_ratio_20d`). **Columns** = prediction horizon (1-day, 3-day).
- Each cell = **mean IC**, with **(t = …)** underneath.
- **Colour:** **green = positive IC**, **red = negative**, **yellow = ~0**. The colour scale only reaches ±0.026, which shows how small everything is.

What to look for: **green cells with |t| ≳ 2**, and a **smooth pattern** down neighbouring rows (Concept 5).

### 🔎 What it shows
| Row | 1-day IC (t) | 3-day IC (t) |
|---|---|---|
| `mom_5d` | −0.001 (−0.1) | −0.004 (−0.3) |
| `mom_10d` | 0.002 (0.2) | 0.007 (0.4) |
| **`mom_21d`** | **0.0145 (1.57)** | **0.0201 (1.41)** |
| `mom_63d` | 0.006 (0.6) | 0.010 (0.6) |
| `vsmom_5d` / `10d` | −0.004 / −0.005 | −0.008 / −0.000 |
| `vsmom_21d` / `63d` | 0.003 / 0.005 | 0.007 / 0.006 |
| `relret_*` | identical to `mom_*` | |
| **`vol_ratio_20d`** | 0.0128 (1.66) | **0.0263 (2.38)** |

### 💡 So what?
1. **The window pattern is smooth:** negative at 5 days → positive at 21 days → smaller at 63 days. That supports 21-day momentum being a *weak but real* effect and not a lucky pick. Short windows lean slightly negative (a mild *reversal*, as Task 03 hinted).
2. **Dividing by risk doesn't help** here: each `vsmom` cell is weaker than its `mom` partner.
3. **Volume ratio is the surprise:** unusual volume was followed by higher 3-day returns.
4. **The honest check (Concept 5):** there are 28 whole-universe cells. By pure luck, about **1.4 of 28** would show |t| > 1.96. We see **one** (volume ratio, 3-day). That is *consistent with luck*. Across all 182 tests, nothing passes a strict luck-proof bar (|t| ≈ 3.1). **So: candidates, not proof.**

### ✅ Takeaway
21 days is the best momentum window, volume ratio is the standout, and nothing is proven.

---

# Graph 6 — Is the signal the same inside each asset class?

![[05_g6_block_ic.png]]

### 🧠 The idea
Remember Task 03: 20 assets ≈ 4 real bets. So an IC across all 20 can be inflated by **"crypto beat bonds today"**, a single big-picture fact counted several times. To remove that, rank **only within a class**: crypto vs crypto, tech vs tech. If the clue still works, it can pick winners **among similar assets**, a cleaner test of skill.

### 👀 How to read it
Bars = the mean 1-day IC for the 3 hero clues, **per class** (left bar group = the whole universe for comparison). **Bar above zero = the clue helps; below zero = it hurts.** Missing bars = not enough assets to rank.

### 🔎 What it shows
| Class (n assets) | `mom_21d` | `vsmom_21d` | `relret_21d` | t-stat (mom) |
|---|---|---|---|---|
| **Whole (20)** | +0.0145 | +0.0028 | +0.0144 | 1.57 |
| **Crypto (5)** | **+0.0173** | +0.0160 | +0.0167 | 1.27 |
| **Tech (5)** | **−0.0106** | −0.0133 | −0.0106 | −0.87 |
| Gold (2) / Bonds (2) | missing | missing | missing | too few assets |
| Oil (3) | −0.0042 | −0.0004 | −0.0042 | −0.24 |
| Real assets (3) | +0.0035 | +0.0223 | +0.0035 | 0.18 (vsmom 1.21) |

- **Crypto: positive** for all clues.
- **Tech: negative.** Inside big tech, a strong 21-day run tends to be followed by a *weaker* next day: a **short-term reversal**.
- **Real assets `vsmom` (+0.022)** looks tallest but is based on **3 assets**, so it's mostly noise.

### 💡 So what?
Momentum is **not one-size-fits-all**. The whole-universe number mixes crypto momentum, class rotation, and tech reversal. But **no single block is statistically significant** (all |t| ≤ 1.3), so read this as "suggestive and consistent with Task 03", not as "tech reverses and crypto trends".

### ✅ Takeaway
Crypto positive, tech negative, nothing individually proven.

---

# Graph 7 — Does the signal survive bad markets? (rolling IC + "bear" shading)

![[05_g7_rolling_ic_regime.png]]

### 🧠 The idea
A signal can have a nice average but **blow up in a bad market**. (This is the known "momentum crash" risk.) So we redraw the yearly-average IC (as in Graph 2), all three clues together, and **intended** to shade the days the market was weak.

### 👀 How to read it
Three lines = the 252-day rolling IC. The grey vertical shading was meant to mark **"bear days"** (SPY below its 126-day average). **Above zero = working; below zero = failing.**

### 🔎 What it shows
- `mom_21d` / `relret_21d` start high (**+0.05 to +0.065** in 2021), decline through 2022, **dip below zero from ~Feb–Dec 2023 and again ~Nov 2024–Nov 2025** (the low is −0.03), then recover to **+0.03–0.05 in 2026**.
- `vsmom_21d` (green) is lower and is **below zero from early 2023 to early 2024** (low −0.030, Oct 2023).
- Share of days above zero: **69%** (`mom_21d`), **56%** (`vsmom_21d`).

### 💡 So what?
The signal has **negative stretches lasting about a year**. It doesn't reliably protect you in stress. A strategy with a decent *average* can still lose for a long time, and the average hides that.

### ⚠️ Known flaws in this picture
- **The shading is almost invisible** (each day is drawn very faintly).
- **The part that *is* visible (first half of 2021) is a bug.** A 126-day average doesn't exist for the first 125 days, so those days were wrongly counted as "bear" (125 of the 419 "bear" days). The real bear stretches (2022, spring 2025) are too faint to see.
- So **do not read bull-vs-bear conclusions from the shading.** Read the lines and compare with known events.

### ✅ Takeaway
The signal weakens or flips for about a year at a time, twice.

---

# Bonus — The cheating test (leakage shift test)

This is a table, not a graph, but it's the safety check that makes everything above trustworthy.

| Clue | Horizon | Normal IC | Clue moved 1 day into the future |
|---|---|---|---|
| `mom_21d` | 1-day | +0.0145 | **+0.1736** |
| `mom_21d` | 3-day | +0.0201 | +0.1171 |
| `vsmom_21d` | 1-day | +0.0028 | +0.1634 |
| `relret_21d` | 1-day | +0.0144 | +0.1736 |

**How it works:** we deliberately **cheat on purpose**: feed in *tomorrow's* clue to predict tomorrow's return. Tomorrow's clue includes tomorrow's price, which is also inside the return. The IC explodes **more than ten times** (0.0145 → 0.17). That proves two things: (1) **the test can detect cheating**, and (2) since our normal setup gives the small numbers, **it is clean**. A leaky setup would already look like 0.17.

---

# 🧭 Summary of all seven graphs

| # | Graph | Verdict |
|---|---|---|
| 1 | Scatter | Signal invisible to the eye, so we rank instead |
| 2 | Daily/rolling IC | 21-day momentum ≈ +0.0145 on average; noisy daily; weaker after 2021 |
| 3 | Cumulative IC | Slow upward drift with year-long pullbacks |
| 4 | Quintiles | Top group earns more (+0.34% a day, +0.88% over 3 days), but driven by Q5 and before costs |
| 5 | Heatmap | 21 days is the best window; short windows lean negative; volume ratio has the best t (2.38) but is consistent with luck among 28 tests |
| 6 | Blocks | Crypto +, tech −, none significant alone |
| 7 | Regimes | Rolling IC dips below zero for ~a year, twice; the shading has flaws |

**Bottom line:** we found **small, plausible, not-proven signals**. They're a fair basis for the baseline models in Task 06. The big open questions are **transaction costs** and **whether it survives on data it has never seen**.

**Back to:** [[_Graph Explanations - README]]
