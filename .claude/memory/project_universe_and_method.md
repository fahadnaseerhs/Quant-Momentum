---
name: project-universe-and-method
description: Universe (21 yfinance tickers, mixed asset classes), daily frequency, 1-day/3-day targets, vol-scaled cross-sectional momentum.
metadata:
  type: project
---

**Universe (20 tradeables + 1 benchmark), all yfinance, defined in `src/universe.py`:**

- **Crypto tokens (5):** `BTC-USD`, `ETH-USD`, `SOL-USD`, `LINK-USD`, `AVAX-USD`
- **Tech stocks (5):** `AAPL`, `MSFT`, `NVDA`, `GOOGL`, `META`
- **Gold (2):** `GLD` (ETF), `B` (Barrick; NOT `GOLD`, which now returns Gold.com Inc.)
- **Oil (3):** `USO`, `XOM`, `CVX`
- **Real-asset diversifiers (3):** `VNQ`, `DBC`, `MSTR`
- **Bonds (2):** `TLT`, `SHY`
- **Benchmark, not traded:** `SPY`

**Frequency:** daily, on the NYSE calendar (SPY trading dates). Data 2021-01-04 onward, ~1439 trading days.

**Targets (both open, user has not picked one):** 1-day forward return $P_{t+1}/P_t - 1$ and 3-day forward return $P_{t+3}/P_t - 1$.

**Momentum method:** cross-sectional ranking on volatility-scaled momentum, $M_{i,t}/\sigma_{i,t}$. Momentum windows are in trading days; they get defined in Task 03. Annual vol ranges from 1.9% (SHY) to 115% (AVAX), which is why vol-scaling is required.

**Why:** User chose Path A + vol-scaling (see `decisions/2026-09-27-universe-and-methodology.md`) and switched monthly → daily (see `decisions/2026-09-27-daily-frequency-horizons.md`).

**How to apply:**
- 3-day targets overlap, so walk-forward splits need a ≥3-day embargo.
- Transaction costs dominate at daily frequency; never report results without them.
- Ticker symbols get reused: verify name/sector and price continuity before adding any ticker.
- ONDO/PAXG/XAUT = Version 2 (needs CoinGecko).
