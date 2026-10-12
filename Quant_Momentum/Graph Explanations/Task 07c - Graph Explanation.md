# Task 07c — Graph Explanation (Long-History Re-test)

**Previous:** [[Task 07b - Graph Explanation]] · **Index:** [[_Graph Explanations - README]] · **Method & numbers:** [[07c - Long-History Re-test]]
**Pictures:** `Figures/07c/` (6 files are generated; these 3 are the ones that matter) · out of sample, 2005 → 2026.

---

## G1 — Trend over 21 years

![[07c_ts_g1_equity.png]]

- 🧠 **Idea.** The same trend strategies as Task 07, now run over 21 years instead of 4.
- 🔎 **What it shows.** The model (blue) and rule (orange) now end clearly **above** 1 (net Sharpe 0.41 and 0.32), but far below long-only (grey, 1.20). Look at 2008: SPY (green) falls about 55%, while trend barely moves. From 2020 to 2022 trend climbs while the market stalls. In 2023–24, the bull years, trend goes flat. That's the stretch Task 07 tested, which is why it found nothing.
- 💡 **So what.** Trend makes a little money on its own, but its real value is that it **doesn't crash when everything else does**.
- ⚠️ **Trap.** Grey and SPY look great partly because the universe was picked with hindsight (NVDA, BTC…). Don't read their level as achievable.
- ✅ **Takeaway.** A small, real edge that shows up mainly in crises and big moves.

## G2 — Where trend predicts (per asset)

![[07c_ts_g2_per_asset_ic.png]]

- 🧠 **Idea.** For each asset, how well the trend prediction lined up with the next month, over 21 years.
- 🔎 **What it shows.** Bonds (SHY), crypto (SOL, BTC, ETH) and commodities (DBC, GLD, USO) lean positive. Single big-tech and oil stocks (CVX, GOOGL, MSFT, AAPL, META) and VNQ lean negative.
- 💡 **So what.** This is the textbook pattern. Trend works on **macro assets** driven by slow forces like rates, inflation and adoption cycles. Individual stocks tend to **mean-revert** on a one-month view.
- ⚠️ **Trap.** Dropping the negative assets now would be fitting to this test. It's a hypothesis for a future, pre-committed test, not a free improvement.

## G3 — Sizing by risk over 21 years

![[07c_vol_g1_equity.png]]

- 🧠 **Idea.** The always-long book, sized equally (1/N, grey) or by risk forecasts (EWMA, HAR, HAR-L).
- 🔎 **What it shows.** The three risk-sized lines overlap (Sharpe 1.22–1.25). They lost about 20% at worst, compared with **43% for 1/N** and **55% for SPY**. 1/N ends far higher in dollars, mainly because of crypto in 2020–21 (+85%, then +153% that year).
- 💡 **So what.** Sizing by risk halves the drawdowns. Which forecast you use barely matters, and EWMA edges out HAR because it reacts faster in crashes.
- ✅ **Takeaway.** Risk-sizing is the most valuable piece of the whole project so far.
