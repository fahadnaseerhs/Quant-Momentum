# Task 07b — Graph Explanation (Volatility Forecasting)

**Previous:** [[Task 07 - Graph Explanation]] · **Index:** [[_Graph Explanations - README]] · **Method & numbers:** [[07b - Volatility Forecasting]]
**Code:** `scripts/07b_vol_forecast.py` · **Pictures:** `Figures/07b/` · all out of sample, 2022-05 → 2026-08.

---

## G1 — Does better risk forecasting make money? (equity curves)

![[07b_g1_equity.png]]

- 🧠 **Idea.** The same "always long" portfolio, run 4 ways. The only difference is how position sizes are set: equal 1/N (grey), or sized by the EWMA, HAR or HAR-L risk forecast.
- 🔎 **What it shows.** The three sized lines lie almost exactly on top of each other (Sharpe 1.22–1.23). Grey 1/N ends higher in dollars, but it carried 2.7× the volatility and fell 30% in 2022. The sized books fell only 11%.
- 💡 **So what.** Sizing by risk matters a lot. *Which* risk forecast you use barely matters for this portfolio.
- ⚠️ **Trap.** Grey "made more money" only because it took far more risk. Compare Sharpe and drawdown, not the final value.
- ✅ **Takeaway.** Keep vol-sizing. Switching EWMA to HAR is a small, free improvement, not a game changer.

## G2 — Where does HAR forecast better? (per-asset)

![[07b_g2_per_asset_qlike.png]]

- 🧠 **Idea.** For each asset, how much HAR reduced the forecast error compared with EWMA. Bars to the right mean HAR is better.
- 🔎 **What it shows.** 16 of 20 bars point right. The biggest wins are big tech (META, GOOGL, MSFT, NVDA), DBC, CVX and BTC. Small losses on MSTR, USO, SHY and AVAX.
- 💡 **So what.** Unlike Task 07's return predictions, which were scattered noise, this improvement is broad and consistent. That's what a real, if modest, signal looks like.
- ⚠️ **Trap.** A ±5% bar for one asset is noise. The evidence is the overall pattern and the t-stat of 2.8 in the methodology note.

## G3 — What a forecast looks like (BTC and TLT)

![[07b_g3_forecast_vs_realized.png]]

- 🧠 **Idea.** Black = the volatility that actually happened over the next 21 days. Orange = the EWMA forecast. Blue = the HAR forecast. Both forecasts were made *before* the black line was known.
- 🔎 **What it shows.** Both forecasts follow the general level well: TLT's slow fall from 22% to 10%, and BTC's range of 30–80%. But at every spike, black jumps **first** and the forecasts catch up a few weeks later. EWMA (orange) jumps higher and then overshoots after the spike. HAR (blue) is smoother and overshoots less, which is where its accuracy gain comes from.
- 💡 **So what.** Volatility *levels* are predictable. Sudden *spikes* aren't, at least not from daily prices alone.
- ✅ **Takeaway.** HAR = "EWMA with less over-reaction".
