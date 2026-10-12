# Tasks 10 & 11 — Graph Explanation (Costs, Combined Book, Robustness)

**Previous:** [[Task 07c - Graph Explanation]] · **Index:** [[_Graph Explanations - README]]
**Method & numbers:** [[10 - Costs and Combined Book]] · [[11 - Robustness (No-Hindsight Universe)]]
**Pictures:** `Figures/10/`, `Figures/11/` · all net of 10 bps; positions drift between weekly rebalances.

---

## G1 — Trading less often (Task 10)

![[10_g2_cost_vs_rebalance.png]]

- 🧠 **Idea.** The same trend model, rebalanced daily, weekly or monthly, at three cost levels (5, 10, 20 bps per trade).
- 🔎 **What it shows.** Daily trading collapses as costs rise (0.56 → 0.07). Weekly and monthly hold up (about 0.5–0.6 at 5–10 bps, still 0.37–0.49 at 20 bps).
- 💡 **So what.** The signal changes slowly (21-day trends), so trading it every day mostly pays costs for noise.
- ⚠️ **Trap.** Monthly looks best here, but on the design period it was worse than weekly (0.30 vs 0.52). Its result depends on which day of the month you trade. Weekly was chosen on 2005–15 and held up on 2016–26.

## G2 — The combined book, with a fair holdout (Task 10)

![[10_g1_combined_equity.png]]

- 🧠 **Idea.** The long risk-sized book (grey), trend (blue), 70% long + 30% trend (red) and SPY (green). The dashed line at 2016 marks where the **holdout** starts: every setting was chosen using only the data to its left.
- 🔎 **What it shows.** Right of the line, red and grey have the same Sharpe (1.51 vs 1.52), but red's dips are shallower (worst −11% vs −17.5%). Trend alone (blue) rises slowly and stays flat through calm bull markets.
- 💡 **So what.** On this universe trend works like **insurance**: the same reward per unit of risk, with smaller crashes.
- ⚠️ **Trap.** Grey ends higher in dollars only because it carries more risk. Compare Sharpe and drawdown, not the final value.

## G3 — The robustness test: 23 broad ETFs (Task 11)

![[11_g1_etf_equity.png]]

- 🧠 **Idea.** The exact same strategy, with no re-tuning, on funds anyone could have picked in 2005.
- 🔎 **What it shows.** Trend (blue) goes nowhere over 21 years (Sharpe 0.11). It rose through 2008 but lost in 2020 and 2022. The long risk-sized book (grey) grows steadily: Sharpe 0.83 vs SPY's 0.69, and its worst fall is −24% vs SPY's −55%. The combined book (red) has the smallest worst fall (−15%) but a lower Sharpe (0.76).
- 💡 **So what.** The **risk-sized diversified book is the robust result** of the project. Trend's edge on the original universe depended on which assets were in it.
- ✅ **Takeaway.** A strategy is only as good as its worst honest test, and this one exposed the hindsight in the original universe.
