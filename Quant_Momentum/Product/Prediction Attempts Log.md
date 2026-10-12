# Prediction Attempts Log

Every attempt so far to **predict returns** (not risk), what was tested, and why it failed. Read this before trying a new idea, so the same thing isn't tried twice.

**Related:** [[Task Log]] · [[QM Terminal - Phase 4 Plan (Allocation + Prediction)]] · [[Path A - Stock Selection Plan]]

---

| # | Date | Attempt | Question | Data | Result | Why it failed |
|---|---|---|---|---|---|---|
| 1 | 2026-10-08 | Linear regression, 15 features | next-day return, ranking 20 mixed assets | 2021–26 | OOS IC ≈ 0 (1d −0.003) | ranking crypto vs bonds vs stocks isn't meaningful; 5 asset classes ([[07 - Time-Series Momentum]] §2) |
| 2 | 2026-10-11 | Time-series momentum (ridge, 4 features) | each asset vs its own trend, 21 days | 2021–26 | IC −0.026, Sharpe −0.10 | 4 years is too short to detect a small edge ([[07 - Time-Series Momentum]]) |
| 3 | 2026-10-11 | Same, long history | same | 2004–26 | IC +0.052, net Sharpe 0.41 | looked real, **but** driven by hindsight-picked assets (crypto, SHY) ([[07c - Long-History Re-test]]) |
| 4 | 2026-10-11 | Same, on 23 broad ETFs (no hindsight) | same | 2004–26 | IC 0.008 (t 0.7), Sharpe 0.11 | the edge disappears without hindsight picks; trend fails on US stocks ([[11 - Robustness (No-Hindsight Universe)]]) |
| 5 | 2026-10-11 | **Phase 4B prediction lab**, pre-registered: macro trend, panic rebound, world regime, combined logistic, boosted trees | P(up next month) per asset vs base rate | both universes, 2005–26 | **all 5 worse than base rate**; regime/combined/trees worse than random noise | too few independent bets (about 5,000 asset-months) for a tiny edge; flexible models memorise noise; public price/macro data is already priced in |

| 6 | 2026-10-11 | **Path A1: S&P 500 stock ranking**, pre-registered: 6 published price signals + z-average + ridge + boosted trees | which stocks beat the others next month | 103,930 stock-months, 2005–26 (coverage 62% → 99%) | **none pass**; best = boosted trees, IC 0.031, t 2.51 (bar 2.6), +4.3%/yr top fifth | the near-miss is a **sector bet** (within-sector IC 0.0006); published price signals have decayed in large caps ([[Path A - Stock Selection Plan]]) |

## What *did* work (risk, not direction)
- EWMA / HAR **volatility forecasts** beat simpler ones (07b, 07c).
- **Risk-sized, bad-month-capped allocation** beat SPY on a risk-adjusted basis on both universes (Phase 4A).

## Lessons carried forward
1. **Breadth matters more than model power:** edge ≈ skill per bet × √(number of independent bets). 20 assets × 1 bet a month is too few.
2. **More flexible models do worse on small data** (trees came last).
3. **Pre-register, use a holdout, test on a no-hindsight universe, and run controls.** The "no information" and "pure noise" controls catch pipeline bias.
4. **Minimum effect rule:** the timing t-stat alone can be fooled by rounding-level differences, so a real minimum improvement is required (Brier skill ≥ 0.005; for rank IC, mean ≥ 0.01).
5. **Change the question, not the pass bar.** Next: rank many stocks *against each other* (Path A).
6. **Measure skill within sectors.** A model can look skilled just by overweighting the sector that happened to win (tech 2016–26). Check within-sector IC and use sector labels as they were at the time.
7. **Price-only signals in large-cap US stocks are crowded.** New information (fundamentals, text) is needed, not new ways of combining prices.
