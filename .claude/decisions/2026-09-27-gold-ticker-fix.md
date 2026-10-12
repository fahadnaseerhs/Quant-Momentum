# Replace ticker GOLD with B (Barrick)

**Date:** 2026-09-27
**Made by:** assistant (autonomous correction restoring the intended asset)
**Status:** active

## Context
The first cleaning run showed `GOLD` with 49.7% annual volatility and ±17–19% daily moves, which is too wild for Barrick. `yfinance` identifies `GOLD` today as **Gold.com, Inc.** (a precious-metals dealer in the Financial Services sector). Barrick changed its NYSE symbol to **`B`** in 2025, and yfinance returns the current holder's history under the old symbol.

## Options
- Keep `GOLD`: this silently studies the wrong company.
- Switch to `B`: risky only if `B`'s history is spliced with Barnes Group, the previous holder of the symbol (acquired in early 2025).

## Verification of `B`
- Price series has no discontinuity (Barnes traded around $50, Barrick around $15–20; no such jump appears).
- 0.73 daily correlation with GLD, as expected for a gold miner.
- 36.3% annual vol, typical for a large gold miner.

## Decision
Use `B`. `src/universe.py` updated, raw data refetched, cleaning rerun.

## Lesson for later
Ticker symbols get reused. Fetching by today's symbol can return a different company's history. Any future universe change must check sector/name (`yf.Ticker(t).info`) and price continuity.
