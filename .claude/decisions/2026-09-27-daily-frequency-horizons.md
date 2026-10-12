# Switch from monthly to daily frequency; predict 1-day and 3-day forward returns

**Date:** 2026-09-27
**Made by:** user
**Status:** active — supersedes the monthly framing in the scope doc (Sections 2, 5, 12–14, 23)

## Context
The scope doc framed everything at monthly frequency (features at month-end, predict $R_{t+1}$ = next month). While Task 02 cleaning was being written, the user changed the plan to daily data.

## Decision
- Research frequency: **daily** (NYSE trading days).
- Prediction targets, both kept open for now:
  - 1-day: $R_{i,t\to t+1} = P_{i,t+1}/P_{i,t} - 1$
  - 3-day: $R_{i,t\to t+3} = P_{i,t+3}/P_{i,t} - 1$ (cumulative over the next three days, not the third day's return alone)
- Monthly resampling removed from cleaning. Momentum windows will be defined in trading days in Task 03.

## Consequences
- **Overlapping targets:** consecutive 3-day targets share 2 of 3 days. Walk-forward splits must leave a ≥3-day embargo between train and test, or training rows contain part of the test answer.
- **Turnover:** daily rebalancing trades far more than monthly; transaction costs (Section 29 of the scope doc) become the deciding test, not a footnote.
- **Noise:** daily returns have a much lower signal-to-noise ratio; expect small predictive correlations and weigh statistical significance carefully.
- **Crypto/equity close mismatch:** yfinance crypto daily bars close at 00:00 UTC (8 pm ET), equities at 4 pm ET. At daily frequency this 4-hour offset can let crypto "see" after-hours equity news. Document it; revisit if cross-asset features are built.
- Sample size: ~1438 daily observations per asset instead of ~69 monthly.
