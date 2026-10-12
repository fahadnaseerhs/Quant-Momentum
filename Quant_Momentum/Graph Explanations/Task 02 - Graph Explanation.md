# Task 02 — Graph Explanation (Data Cleaning)

**Full write-up of the task:** [[02 - Data Cleaning]] · **Index:** [[_Graph Explanations - README]]

> **How to use this note.** It is written to be *understood*, not just read. Every graph has the same five parts:
> 🧠 **The idea first** (the concept, in plain words) → 👀 **How to read the picture** (step by step) → 🔎 **What it shows** → 💡 **So what?** (why the project cares) → ⚠️ **Common trap**.
> If a word is new, it is explained the first time it appears.

> **Heads-up.** Task 02 originally had *no graphs*, only a text log. I made the two graphs below afterwards (script: `scripts/02_cleaning_figures.py`) so you can *see* the two main ideas of Task 02. They use your real data.

---

## Words you need first

| Word | Plain meaning |
|---|---|
| **Trading day** | A day the stock exchange (NYSE) is open. Monday–Friday, minus holidays. About 252 a year. |
| **Calendar day** | Any day, including weekends. 365 a year. |
| **Price** | What one unit of the asset costs at the end of the day (the "close"). |
| **Return** | How much the price changed, in %. If it goes 100 → 102, the return is +2%. |
| **Volatility** | How *bumpy* the price is. Calm asset = small daily moves. Wild asset = big daily moves. Think of it as **how bumpy a road is**. |
| **Annualised** | "Scaled up to a one-year number" so it is easy to compare. A daily wobble of 1% becomes about 16% a year. |

---

## Graph 1 — One common calendar

![[02_g1_calendar_alignment.png]]

### 🧠 The idea first
Imagine two shops:
- **Shop A (crypto)** is open **every single day**, 24/7.
- **Shop B (the stock market)** is open **only on weekdays**, and closed on holidays.

You want to compare how both shops did, **day by day**. But on Saturday, Shop B has no number at all. What do you do?

For this project, every day we **rank all 20 assets** ("who is strongest today?"). A ranking with half the assets missing is meaningless. So we choose **one calendar for everyone: the days the stock market was open.** (You can't trade stocks on a Sunday anyway.)

### 👀 How to read the picture
1. Each **column** is one calendar day (18 Nov → 8 Dec 2024). The grey stripes are weekends. The red stripe is Thanksgiving (US holiday, stock market closed).
2. Each **row** is one dataset.
3. A **filled dot** = a price exists that day. A **hollow circle** = no price.

| Row | What it is |
|---|---|
| Top: BTC-USD (raw) | Bitcoin before cleaning |
| Middle: SPY (raw) | The US stock market before cleaning |
| Bottom: BTC-USD (after alignment) | Bitcoin after we keep **only** the days the stock market was open |

### 🔎 What it shows
- **Top row: no hollow circles.** Bitcoin trades every day.
- **Middle row: hollow circles on every weekend and on Thanksgiving.** Stocks only trade on open days.
- **Bottom row: it now has hollow circles in exactly the same places as the middle row.** We threw away Bitcoin's weekend and holiday rows so everyone shares one calendar.

Result in numbers: **2,096 calendar days → 1,439 trading days.**

### 💡 So what?
**The order of the steps matters, and the picture hides a clever detail.** Look at **Monday 25 Nov** in the bottom row. Bitcoin's return for Monday is measured from **Friday's price to Monday's price**. So Monday's return *includes everything that happened over the weekend*.

- ✅ **Align first, then compute returns** → the weekend's movement is **kept**, folded into Monday.
- ❌ If we computed returns on all 7 days and *then* deleted weekends, Saturday's and Sunday's moves would be **lost forever**.

There is also a **rule about missing data**: if a price is missing, we may copy the **last known price forward** ("yesterday's price"), but we must **never** copy a price from the **future** backward. Using tomorrow's price to fill today's gap would be **cheating** (this is called *lookahead bias*, and it is the #1 reason fake strategies look amazing in tests and fail with real money). In your data it didn't even come up: 0 fills needed.

### ⚠️ Common trap
After alignment, crypto and stocks still do **not measure exactly the same 24 hours**. A crypto "day" ends at midnight UTC (8 pm New York), a stock day ends at 4 pm New York. So crypto's "close" contains 4 extra hours of news. Small, but real, and written down as a known limitation.

---

## Graph 2 — How bumpy is each asset? (annual volatility)

![[02_g2_annual_vol_by_ticker.png]]

### 🧠 The idea first
**Volatility = how bumpy the road is.** A short-term government bond fund is a smooth highway. A crypto token is a mountain trail. We measure bumpiness as the typical size of the daily move, then scale it to a yearly number:

$$\text{annual volatility} = \text{daily volatility} \times \sqrt{252}$$

(You don't need to memorise the maths. "× √252" is just the standard conversion from "per day" to "per year".)

**How to feel the number:** 27% annual volatility means "this asset typically moves about ±27% over a year", which is about ±1.7% on a typical day.

### 👀 How to read the picture
1. One **bar per asset**. Longer bar = bumpier.
2. Colours = asset class (orange crypto, blue tech, brown oil, gold gold, purple "real assets", green bonds, grey SPY = the market).
3. **Important: the x-axis is a log scale.** On a normal ruler, each tick adds the same amount (10, 20, 30…). On a **log scale** each tick *multiplies* (10, 100, 1000). It is like the Richter scale for earthquakes. We need it because the values go from 1.9% to 115%, and on a normal ruler the small bars would be invisible.

### 🔎 What it shows
| Group | Annual volatility | Feels like |
|---|---|---|
| Short Treasury fund (SHY) | **1.9%** | Almost flat |
| Long bonds, market, gold, REIT, commodities | 15–19% | Smooth road |
| Large tech, oil, gold miner | 25–37% | Bumpy |
| NVDA, META | 44–51% | Very bumpy |
| Crypto + MSTR | **57–116%** | Mountain trail |

The calmest (SHY) and wildest (AVAX) differ by about **61 times**.

### 💡 So what?
This one chart is **the reason for a big design decision later** (volatility-scaled momentum).

Imagine ranking assets by "who rose most in the last month". A crypto token moves ±30% in a month **all the time**. A bond fund *never* does. If you rank by raw % change, **crypto will always be at the very top or very bottom**, simply because it is bumpy, not because it is "strong". To compare fairly you must measure each asset's move **relative to its own bumpiness**. We fix that in Task 04.

This chart also caught a **bug**: the first run showed "GOLD" at ~50% volatility, way too high for a big gold company. The ticker symbol had been taken over by a different company. A bar that "looks wrong" is a signal to check the data.

### ⚠️ Common trap
- This is **one number for the whole 2021–2026 period**. In reality volatility changes over time (Task 03, Graph 2 shows that).
- MSTR is filed under "real assets" (purple), but its bar sits among the crypto names. It *behaves like crypto*. Labels aren't behaviour.

---

## ✅ Task 02 in one paragraph
Raw data had two different calendars. We forced everything onto the stock-market calendar (Graph 1) without losing weekend moves and without ever peeking into the future. Then we checked each asset's bumpiness (Graph 2) and learned that assets differ by up to 61×, which means we can't compare raw moves fairly. That sets up Tasks 03 and 04.

**Next:** [[Task 03 - Graph Explanation]]
