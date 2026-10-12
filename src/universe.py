"""Locked universe of 20 tradeable assets + 1 benchmark.

Decision reference: .claude/decisions/2026-09-27-universe-and-methodology.md
"""

UNIVERSE = {
    "crypto":       ["BTC-USD", "ETH-USD", "SOL-USD", "LINK-USD", "AVAX-USD"],
    "tech":         ["AAPL", "MSFT", "NVDA", "GOOGL", "META"],
    # Barrick is "B" since 2025; "GOLD" now returns Gold.com Inc. history.
    "gold":         ["GLD", "B"],
    "oil":          ["USO", "XOM", "CVX"],
    "real_assets":  ["VNQ", "DBC", "MSTR"],
    "bonds":        ["TLT", "SHY"],
}

BENCHMARK = "SPY"

TRADEABLES = [t for bucket in UNIVERSE.values() for t in bucket]
ALL_TICKERS = TRADEABLES + [BENCHMARK]

START_DATE = "2021-01-01"
