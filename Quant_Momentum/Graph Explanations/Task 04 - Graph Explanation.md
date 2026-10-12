# Task 04 — Graph Explanation (Feature Engineering)

**Full write-up of the task:** [[04 - Feature Engineering]] · **Index:** [[_Graph Explanations - README]] · **Dictionary of labels:** [[Graph and Table Labels]] · **Previous:** [[Task 03 - Graph Explanation]]

> **How to use this note.** Written so you *understand*, not just read. Each graph: 🧠 **The idea first** → 👀 **How to read the picture** → 🔎 **What it shows** → 💡 **So what?** → ⚠️ **Common trap** → ✅ **Takeaway**. New words are explained when first used.

---

## What is Task 04 about, in plain words?

A prediction model can't look at "the market". It needs **numbers describing each asset each day**. Those numbers are called **features** (think of them as *clues*). Task 04 builds the clues and checks they look sensible.

**The golden rule:** a clue computed at the close of day *t* may use **only information available by the close of day *t***. Using even a tiny piece of tomorrow's data is **cheating** (called *leakage*), and it makes fake strategies look amazing.

### The clues (features), in one place
| Clue | Column name | Plain meaning |
|---|---|---|
| **Momentum** | `mom_5d`, `mom_10d`, `mom_21d`, `mom_63d` | How much the price changed over the last 5 / 10 / 21 / 63 trading days. (21 days ≈ 1 month.) |
| **Volatility** | `ewma_vol`, `roll_vol_63d` | How bumpy the asset has been recently (**per day**, not per year) |
| **Vol-scaled momentum** | `vsmom_5d` … `vsmom_63d` | Momentum **divided by the asset's own bumpiness**: "a big move *for this asset*" |
| **Volume ratio** | `vol_ratio_20d` | Today's trading volume ÷ the average of the last 20 days. Above 1 = busier than usual |
| **Relative return** | `relret_5d` … `relret_63d` | The asset's momentum **minus SPY's** momentum: "is it beating the market?" |
| **Targets (the answers)** | `fwd_ret_1d`, `fwd_ret_3d` | What actually happened **next** (1 or 3 days later). **Never** used as a clue. They are the thing we want to predict. |

### Two things that will confuse you in the pictures
1. **Winsorising.** After building the clues, the **extreme 1% on each end are capped** at the 1st and 99th percentile. Analogy: when you average salaries in a room, one billionaire ruins the average, so you cap everyone above a certain level. In the graphs this shows up as **flat tops/bottoms and tall bars at the very edges. Those are the caps, not real data.** (Note: the code caps across all dates together, not day by day as the older write-up says.)
2. **Duplicate pictures.** `04_g2_momentum_21d_timeseries.png` and `04_g3_momentum_21d_timeseries.png` are the same chart. `04_g3_vsmom_before_after.png` also contains the same right panel as `04_g5_vsmom_boxplots.png`. Each is explained once below.

---

# Graph 1 — Which clues are copies of each other? (correlation matrix)

![[04_g1_feature_correlation.png]]

### 🧠 The idea first
**Correlation** (from −1 to +1) says whether two columns move together. If two clues have correlation 0.97, they are **almost the same clue wearing different clothes**, and keeping both adds almost nothing. This graph is a **"who is a copy of whom"** table.

### 👀 How to read it
1. It's a grid. Each **row and column** is one of the 17 columns. Only the lower triangle is shown (the upper half would be a mirror).
2. Each **cell** = correlation between its row and its column. **Dark red = move together, white = unrelated, blue = opposite.**
3. The **diagonal** is always 1.00 (every column equals itself).

### 🔎 What it shows
| Pair | Number | Why |
|---|---|---|
| `relret` vs `mom` (same window) | **0.95–0.98** | Subtracting SPY's momentum barely changes it |
| `ewma_vol` vs `roll_vol_63d` | **0.97** | Two ways to measure the same bumpiness |
| `vsmom` vs `mom` | ~0.80 | Dividing by risk keeps most of the ordering |
| Neighbouring windows (`mom_5d`–`mom_10d`) | 0.70 | The windows share days |
| `vsmom` vs `ewma_vol` | **≈ 0** | On purpose: dividing by risk removes the risk |
| `vol_ratio_20d` vs everything else | **≤ 0.22** | Volume is a *different kind* of clue |
| `fwd_ret_3d` vs `fwd_ret_1d` | **0.58** | The 3-day answer *contains* the 1-day answer |
| **Any clue vs the answers (`fwd_ret_*`)** | **0.00–0.09** | The bottom two rows. **Very weak.** |

### 💡 So what?
- Many columns are **near-duplicates**. 4 `mom` + 4 `relret` + 4 `vsmom` is not 12 independent clues. (Task 05 confirms `relret_21d` and `mom_21d` behave identically.)
- **The bottom two rows are the punchline.** A correlation of 0.05 with tomorrow's return means the clue explains only 0.05² = **0.25%** of what happens tomorrow. In finance that is *normal*, but it tells you the edge is tiny, and trading costs will decide whether it is usable.
- The 0.58 between the two answers is the **overlap problem** again (see Task 03 Graph 5c).

### ⚠️ Common trap
It's computed across all assets and days pooled together, which mixes "crypto is simply bumpier" with "things change over time". So a number like `ewma_vol` vs `mom_63d` = 0.19 mostly says "crypto has both big volatility and big momentum numbers".

### ✅ Takeaway
Lots of clues are copies of each other, volume is different, and every clue is only very weakly linked to the next-day return.

---

# Graph 2 — What does each clue's data look like? (histograms)

![[04_g2_feature_distributions.png]]

### 🧠 The idea first
A **histogram** answers: "how often does each value occur?" It cuts the range into bins and counts how many data points land in each. **Tall bar = common value. Short bar = rare value.** The shape tells you what the data is like: narrow and tall = most values similar; wide = lots of variety; long tail on one side = rare big values in that direction.

### 👀 How to read it
15 small histograms, one per clue, **all assets and all days pooled**. The **yellow dashed line = the median** (the middle value: half the data is below, half above). **The tall single bars at the far left/right edges are the capped extremes** (winsorising).

### 🔎 What it shows
| Panel | Shape | In plain words |
|---|---|---|
| `mom_*` | A sharp peak at ≈ 0 with a **long right tail** | Most months nothing much happens; but rallies can be huge (cap +0.77), while falls can't go below −100% (cap −0.37) |
| `ewma_vol`, `roll_vol_63d` | A hump near 0.015, a **second shoulder near 0.04**, and a **spike near 0.001** | Hump = stocks/gold/bonds; shoulder = crypto and MSTR; spike = **SHY**, the almost-flat bond fund |
| `vsmom_*` | **Bell-shaped, wide**, centred a bit above 0 | After dividing by risk the data is smooth and symmetric |
| `vol_ratio_20d` | Skewed right, median 0.92 | Most days are slightly quieter than average; a few days are very busy |
| `relret_*` | Peak centred on 0 | Half of assets beat the market, half lag it |

### 💡 So what?
- Nothing is a perfect bell curve (fat tails), which supports using **ranks**.
- `vsmom` gets **wider as the window grows** (5d → 63d). That's normal: a longer move is naturally bigger in "units of daily wiggle" (about √window times bigger). So only compare `vsmom` within the same window.

### ✅ Takeaway
The clues are peaked, skewed and fat-tailed; capped at the edges; and window length changes their scale.

---

# Graph 3 — What does 21-day momentum look like over time?

![[04_g2_momentum_21d_timeseries.png]]
*(`04_g3_momentum_21d_timeseries.png` is identical.)*

### 🧠 The idea first
**Momentum = how much the price moved over the last 21 trading days.** +0.20 means "up 20% in the last month". −0.10 means "down 10%". This graph just draws it through time, class by class.

### 👀 How to read it
Six panels (one per class). Each line = one asset (all the same colour inside a class, so you can't tell tickers apart). **Above zero = rose recently. Below zero = fell recently.** Height = size.

### 🔎 What it shows
- **Crypto:** swings between **−0.37 and +0.77**. The flat plateaus at the top and bottom are **the winsorising caps**, not real data. The five lines move as one bundle: one bet.
- **Tech:** about ±0.2, with NVDA/META spikes to 0.4–0.5 and a slump toward −0.37 in 2022.
- **Gold:** GLD ±0.1; the miner B reaches 0.39 in early 2026.
- **Oil:** ±0.2 with a spike near 0.6 in early 2026.
- **Real assets:** **MSTR swings like crypto**; VNQ and DBC stay near ±0.1.
- **Bonds:** TLT ±0.1 (peak 0.18 in late 2022); **SHY is flat near zero**.

### 💡 So what?
Look at the **vertical scales**: crypto spans −0.4 to +0.8, bonds only −0.1 to +0.18. **Same clue, totally different sizes.** If you rank assets by raw momentum, crypto will always be at the top or the bottom purely because it is bumpy. That is the motivation for Graph 4.

### ✅ Takeaway
Raw momentum is not comparable across classes.

---

# Graph 4 — The fix: divide by each asset's own bumpiness

![[04_g3_vsmom_before_after.png]]

### 🧠 The idea first
**Volatility-scaled momentum** = momentum ÷ the asset's typical daily wiggle. It answers: *"is this move big **for this asset**?"* A +5% month is boring for crypto and extraordinary for a bond fund; scaling treats it that way.

### 👀 How to read a boxplot (we use them here)
- The **coloured box** holds the **middle 50%** of the data. Its **height** tells you the "typical spread" (the *IQR*).
- The **line inside the box** = the median.
- The thin lines (**whiskers**) reach toward the extremes.

Left panel = raw momentum. Right panel = vol-scaled.

### 🔎 What it shows
| | Crypto | Tech | Gold | Oil | Real assets | Bonds |
|---|---|---|---|---|---|---|
| **Raw: box height** | **0.30** | 0.12 | 0.10 | 0.10 | 0.10 | **0.016** |
| **Scaled: box height** | 6.3 | 6.5 | 6.5 | 6.0 | 6.2 | 6.5 |

- Left: crypto's box is **about 19× taller** than bonds'. Bonds look like a flat line.
- Right: **all boxes have almost the same height.** A fair comparison.
- The long whiskers on the right (−8 to +12.6) are the caps again.

### 💡 So what?
Scaling makes "strong momentum" mean the same thing for every asset. **But** (spoiler from Task 05) in this dataset scaling did **not** improve prediction, so the problem on the left turned out to be less harmful than expected. A method can be elegant in theory and still need to be tested.

### ⚠️ Common trap
In this file the **colours of crypto and tech are swapped** compared with the project palette (crypto drawn blue, tech orange). Trust the x-axis labels. The clean version is below.

### Same panel with correct colours
![[04_g5_vsmom_boxplots.png]]

### ✅ Takeaway
Dividing by own risk makes classes comparable.

---

# Graph 5 — The risk number itself (EWMA volatility)

![[04_g4_ewma_volatility.png]]

### 🧠 The idea first
This is the **denominator** from Graph 4: each asset's bumpiness, updated daily. Remember **EWMA** = a risk meter with a **fading memory**: new shocks count a lot, old ones fade. Here it is **lagged by one day**: today's clue uses *yesterday's* risk, to avoid any chance of peeking.

### 👀 How to read it
All 20 assets on one chart. The y-axis is **daily** volatility (0.02 = 2% a day ≈ 32% a year), not annual. The lines start in **April 2021** because the first 63 days are a warm-up. **Higher line = rougher period. A sudden jump = a shock.**

### 🔎 What it shows
- **Three tiers:** crypto and MSTR on top (0.04–0.10); stocks and gold in the middle (0.01–0.04); **SHY alone at the bottom (~0.001)**.
- **Saw-tooth shape:** a sharp jump, then a smooth fade. A shock's weight **halves about every 11 trading days**.
- **April 2025:** many lines jump together (tariff shock).
- **Crypto calms over time:** 0.06–0.10 in 2021–22 to 0.02–0.04 by 2026.
- The flat tops at ~0.1016 are the winsorising cap.

### 💡 So what?
The risk number differs **by over 50×** between assets *and* changes over time. That's why a **daily-updated** risk estimate is needed.

### ✅ Takeaway
Risk is a moving target; EWMA tracks it with a fading memory.

---

# Graph 6 — Volume ratio (is today busier than usual?)

![[04_g6_volume_ratio.png]]

### 🧠 The idea first
**Volume** = how much of the asset was traded today. Raw volume is not comparable (stocks count shares, crypto counts dollars), so we use a **ratio**:

$$\text{volume ratio}=\frac{\text{today's volume}}{\text{average volume of the last 20 days}}$$

**1.0 = a normal day. 2.0 = twice as busy as usual. 0.5 = half as busy.** A unit-free "unusual attention" meter.

### 👀 How to read it
Six assets (SOL, AVAX, TLT, MSTR, GLD, USO). The yellow dashed line is 1.0. **Spikes above = busy days.**

### 🔎 What it shows
- Everything oscillates around 1.0 with no long-term trend.
- **Crypto and MSTR are spiky** and often hit the **2.6 ceiling** (cap) and 0.4 floor.
- TLT, GLD, USO are calmer (mostly 0.5–2).

### 💡 So what?
This is the clue that surprised us: in Task 05, `vol_ratio_20d` had the **best t-stat** (more on that there). So this is where its story starts.

### ✅ Takeaway
A unit-free measure of "unusual trading activity".

---

# Graph 7 — Can you *see* a relationship with tomorrow? (scatter)

![[04_g7_relret_vs_fwd_scatter.png]]

### 🧠 The idea first
A **scatter plot** puts one dot per observation: x = a clue today, y = what happened tomorrow. If the clue predicted the future, the dots would form a **slope going up to the right**. If not, a **flat blob**.

### 👀 How to read it
- x = `relret_21d` (how much the asset beat SPY over 21 days).
- y = `fwd_ret_1d` (its return the next day).
- Each dot = one asset on one day, coloured by class.
- The **red line** = the best straight-line fit (a *regression line*). Its **slope** says "for each +1 in x, y changes by this much".

### 🔎 What it shows
- A **horizontal blob**. The slope is **+0.0116**: beating SPY by 10 percentage points goes with only **+0.116 percentage points** more return tomorrow, while daily returns swing ±2 to ±10%.
- **Vertical stripes at the left and right edges** = values capped by winsorising.
- Crypto (orange) spreads widest vertically; bonds are a tiny dot cluster in the middle.

### 💡 So what?
**You cannot see the signal.** The correlation is about 0.05 (explains ~0.26% of the variance). That's why we **rank** assets instead of drawing straight lines through noisy raw values: Task 05's Information Coefficient measures *whether the ordering agrees*.

### ✅ Takeaway
Visually: a blob. A tiny slope is normal in finance and doesn't rule out a weak but usable signal.

---

# Graph 8 — Is any data missing? (NaN heatmap)

![[04_g8_nan_heatmap.png]]

### 🧠 The idea first
**NaN** means "not a number", i.e. an **empty cell**. Some empties are unavoidable. To say "the price moved over the last 21 days" you need 21 earlier days of data, so the first 21 days have **no value**. This is called **warm-up**. At the very end, the last 1–3 days have no "future" yet, so their answers are empty.

### 👀 How to read it
Rows = tickers, columns = clues. Each cell = **% of rows that are empty** (annotation in %, the colour bar in fractions: 0.04 = 4%).

### 🔎 What it shows
| Column | % empty | Days | Why |
|---|---|---|---|
| `mom_5d / 10d / 21d / 63d` | 0.3 / 0.7 / 1.5 / 4.4 | 5 / 10 / 21 / 63 | Need that many earlier prices |
| `ewma_vol`, `vsmom_*` | 4.5 | ~65 | Risk warm-up (63 days) + 1 lag day + first return |
| `vol_ratio_20d` | 1.3 | 19 | Need 19 earlier days |
| `fwd_ret_1d / 3d` | 0.1 / 0.2 | 1 / 3 | The last days have no future yet |

**Every ticker has exactly the same pattern.**

### 💡 So what?
1. **All missing data is at the start or the end.** No random holes in the middle: Task 02's alignment worked.
2. Identical rows = no asset silently lost data.
3. **It's a cheating alarm:** NaNs at the start prove nothing was back-filled, and NaNs at the end of the answers prove the answers only look forward.

### ✅ Takeaway
Missing values are only warm-up and look-ahead gaps, which is exactly what a correct build should produce.

---

# 🧭 What Task 04 means for Task 05

| We saw | So |
|---|---|
| `relret` ≈ `mom` (0.95–0.98) | Expect them to give nearly identical results |
| Every clue vs answer ≤ 0.09 | Expect tiny predictive numbers; a huge one would signal a bug |
| `vol_ratio_20d` is different | Test it separately |
| Capping puts many crypto values *tied* at the cap | Slightly blunts rankings inside crypto |
| NaNs only at the edges | Safe to rank each day with whatever assets have data |

**Next:** [[Task 05 - Graph Explanation]]
