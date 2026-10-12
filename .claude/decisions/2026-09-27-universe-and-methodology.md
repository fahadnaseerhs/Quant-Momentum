# Universe selection and momentum methodology

**Date:** 2026-09-27
**Made by:** user (assistant proposed, user chose)
**Status:** active

## Context

The scope document proposed "approximately 20 liquid stocks" without specifying which market or asset class. The user asked for a genuinely diverse universe covering crypto tokens (not just BTC/ETH/SOL), oil, gold, tech stocks — an asset-class mix rather than a single-sector list. This changes both the data-source problem and the momentum methodology, because ranking BTC against gold against SHY (short Treasuries) is not comparable in raw return space.

## Options considered

**Data source**
- Path A: yfinance only. Covers major crypto tokens (BTC, ETH, SOL, LINK, AVAX, etc.), all US equities, all major ETFs. Does NOT cover true RWA tokens like ONDO, PAXG, XAUT.
- Path B: yfinance + CoinGecko. Adds real RWA-token coverage but doubles the data-plumbing work — two APIs, two formats, two date grids to reconcile.

**Momentum methodology**
- M1: cross-sectional momentum (as written in the scope doc) — rank all 20 assets by 3M return, buy top, sell bottom. Breaks when volatility varies by 10x+ across the universe.
- M2: cross-sectional with volatility scaling — divide each asset's return by its trailing volatility before ranking. Rank is on risk-adjusted momentum.
- M3: time-series momentum — for each asset, buy if own 3M return > 0, sell if < 0. Standard multi-asset momentum approach.

## Decision

- **Data source: Path A** (yfinance only).
- **Methodology: M2** (cross-sectional momentum on volatility-scaled returns).
- **Universe (20 tradeables + 1 benchmark):**

| Bucket | Tickers |
|---|---|
| Crypto tokens | `BTC-USD`, `ETH-USD`, `SOL-USD`, `LINK-USD`, `AVAX-USD` |
| Tech stocks | `AAPL`, `MSFT`, `NVDA`, `GOOGL`, `META` |
| Gold | `GLD`, `GOLD` |
| Oil | `USO`, `XOM`, `CVX` |
| Real-asset diversifiers | `VNQ`, `DBC`, `MSTR` |
| Bonds (contrast) | `TLT`, `SHY` |
| Benchmark (not traded) | `SPY` |

## Rationale

- **Path A** keeps the first pipeline pass simple. One API, one data grid, one debugging surface. RWA tokens can be added in Version 2 once the end-to-end pipeline works. User agreed with this framing.
- **Volatility scaling** was the user's own choice after being shown that raw cross-sectional ranks on a mixed universe would let BTC dominate every top/bottom bucket. Scaling preserves the scope doc's ranking-based framework while making the ranks meaningful across asset classes.
- **The universe** covers every asset class the user named (crypto, tech, gold, oil, real assets, diversifiers) using instruments that all have clean daily history from 2021 onward on yfinance.

## Consequences

- The scope document's exact "rank raw returns" formulation from Sections 12–13 is superseded here. Ranking is now on $M_{i,t}^{scaled} = M_{i,t}^{3M} / \sigma_{i,t}$, where $\sigma_{i,t}$ is the trailing volatility of asset $i$. Update the scope doc or annotate it before the next session.
- Crypto trades 24/7; equities trade weekday sessions. Data cleaning must resample everything to a common trading calendar (probably US weekdays, forward-filling crypto weekends is defensible for a monthly-frequency study — decide during data cleaning).
- Sukuk is dropped from Version 1 (poor data quality on yfinance). Revisit in Version 2 alongside a PSX port.
- Downstream tickets: data collection needs to fetch these 21 symbols from 2021-01-01 to today, adjusted close, daily frequency, and save as parquet.
