# Quant-Momentum: A 20-Year Empirical Journey from Return Prediction to Risk-First Capital Allocation

Repository: [https://github.com/fahadnaseerhs/Quant-Momentum](https://github.com/fahadnaseerhs/Quant-Momentum)

---

## The Genesis: Can Asset Mobility Actually Be Predicted?

When I started this project, I began with the question that virtually every market participant, retail trader, and investment fund asks:

**Can we predict asset mobility? Can we know whether a stock is going up or down tomorrow, next week, or next month?**

This is the question on which multi-billion-dollar fortunes are staked. If a model can consistently forecast price direction, even by a few basis points of statistical edge, compounding wealth becomes a mechanical certainty.

I took 20 years of daily market data (from 2004 through 2026) across 20 distinct assets spanning every major asset class: technology giants, physical commodities, energy, precious metals, sovereign debt, and digital assets. I built six pre-registered quantitative models designed to extract directional momentum:

1. **Short-horizon momentum regressions:** Predicting next-day and next-month returns from skip-5 price trajectories.
2. **Cross-sectional decile sorting:** Ranking assets by past relative strength, buying the winners and shorting the losers.
3. **Multi-horizon feature walk-forward engines:** Normalizing returns across 1-month, 3-month, and 6-month momentum lookbacks.
4. **Machine learning models:** Testing decision trees and gradient-boosted trees on non-linear price patterns.
5. **Cross-asset spillover signals:** Attempting to forecast equities from commodity and currency trends.
6. **Large-universe stock selection:** Expanding the testing engine across the entire S&P 500 panel.

### What Happened When Theory Met Reality

Every single directional model broke down out-of-sample once realistic transaction costs, execution lag, and bid-ask slippage were introduced.

The Information Coefficients (correlation between predicted direction and realized return) collapsed toward zero. Assets that were top momentum performers over three months routinely reversed into brutal drawdowns. Daily price changes in liquid modern financial markets behave remarkably close to a random walk with an extremely high noise-to-signal ratio. High-frequency turnover quickly eroded any theoretical gross margin through frictional trading costs.

Directional prediction, as an edge for capital preservation, proved to be an illusion.

---

## The Pivot: What Actually Persists Over Time

While price direction is essentially unpredictable noise, something else in the 20-year dataset was overwhelmingly structured, stable, and persistent:

**The size of the move. The swings. The volatility.**

If an asset experiences an exceptionally violent day today, tomorrow is far more likely to be violent as well. Conversely, if an asset is quiet and compressed today, it is far more likely to remain compressed tomorrow. This phenomenon, known in econometrics as **volatility clustering**, has held true across every market panic and bubble in modern history.

This realization changed the entire architecture of the project:

- **We stopped asking:** "Will this asset go up or down?"
- **We started asking:** "How wide is the gap between its normal swings and its worst-case swings? What is the empirical 1-in-20 bad-case loss over the next month, and how can we allocate capital so that no single asset crash can ever destroy the portfolio?"

By measuring the exact swing width of every asset daily and sizing positions inversely to their volatility, capital stays naturally insulated. Calm assets carry larger slices; stormy assets carry tiny slices. Total risk contribution is equalized across the book.

---

## Historical Crises and How Assets Actually Behave

To verify this framework, we stress-tested 20 years of market behavior through the most violent dislocations of the modern era.

```
Historical Episode          Equity Move (SPY)     Long Bonds (TLT)      Real Assets / Oil     Effective Hedge
----------------------------------------------------------------------------------------------------------------
2008 Subprime Mortgage GFC  -55% (Crash)          +34% (Surge)          -50% (Crushed)        Sovereign Bonds
2020 Covid Liquidity Shock  -34% (Crash)          +21% (Surge)          Negative prints       Sovereign Bonds
2022 Inflation & Rate Hike  -24% (Bear Market)    -31% (Crash)          +65% (Surge)          Oil & Real Assets
```

### 1. The 2008 Global Financial Crisis: The Deflationary Collapse

- **Economic Reality:** The subprime mortgage securitization market froze, leading to the collapse of Lehman Brothers, a global credit freeze, and immediate demand destruction. Consumer spending collapsed and corporate earnings evaporated.
- **Asset Behavior:** Equities tumbled into a −55% peak-to-trough collapse. Commodities and crude oil, which had peaked in July 2008 near \$145 per barrel, plummeted by over 70% as industrial demand dried up.
- **The Hedge:** Central banks slashed the Fed Funds rate toward zero. In this deflationary environment, long-maturity Treasury bonds (TLT) surged +34%. Fixed-coupon government debt acted as a powerful capital protector because the risk was deflation and economic depression, not inflation.

### 2. The 2020 Covid-19 Shock: The Sudden Liquidity Freeze

- **Economic Reality:** Global lockdowns halted trade and travel overnight. A sudden liquidity shock forced market participants to liquidate even safe assets to meet margin calls.
- **Asset Behavior:** The S&P 500 plunged −34% in less than five weeks, marking the fastest collapse from an all-time high in history. WTI Crude Oil futures famously traded into negative territory (−\$37.63/bbl) on April 20, 2020, as physical storage capacity filled up.
- **The Hedge:** Emergency central bank intervention, infinite quantitative easing, and interest rate reductions triggered an immediate flight to safety. Long Treasuries and gold served as the primary recovery buffers.

### 3. The 2022 Inflation Shock: The Breakdown of Traditional Portfolios

- **Economic Reality:** Trillions of dollars of pandemic fiscal stimulus combined with supply chain snarls and the outbreak of the Russia-Ukraine war drove global inflation to 40-year highs (CPI exceeding 9%). The Federal Reserve and global central banks initiated the fastest interest rate hiking cycle in 40 years.
- **Asset Behavior:** Equities entered a prolonged bear market (−24%), high-growth tech stocks crashed −35% to −70%, and speculative crypto plummeted −75%.
- **The Breakdown of Maturity Bonds:** **Long-maturity government bonds failed completely as a safe haven.** Because bond prices are inversely tied to interest rate expectations, 20+ Year Treasuries (TLT) suffered a catastrophic −31% drawdown in 2022. Traditional 60/40 balanced portfolios experienced their worst annual performance since the Great Depression.
- **The Hedge:** Only real assets—energy equities (XOM, CVX), crude oil futures (USO), and physical commodities (DBC)—rose sharply (+30% to +70%), absorbing the shock and saving diversified portfolios from catastrophic drawdown.

---

## The Bond Fallacy: Why Maturity Bonds Are Not Always Safe

Traditional wealth management teaches an overly simplified rule: *when stocks drop, buy bonds.*

Our 20-year empirical research reveals that this rule only works in one specific type of crisis: **growth and deflation scares**.

When the market crashes due to an economic slowdown (2008 or 2020), interest rates drop, and long-maturity bonds appreciate. But when the market drops due to an **inflation shock** (1970s or 2022), interest rates must rise. In an inflation shock, long-maturity debt crashes alongside equities. An investor holding only equities and long-duration Treasuries is left completely unprotected.

**The practical takeaway:** The *type* of crisis matters far more than the *size* of the crisis. True capital preservation requires allocating across uncorrelated segments that respond to different macro regimes:
- **Bonds (TLT, SHY):** Protect against deflationary banking freezes and recessions.
- **Energy and Commodities (USO, XOM, DBC):** Protect against unexpected inflation and cost-push supply shocks.
- **Gold (GLD, B):** Protects against real interest rate compression, currency debasement, and geopolitical flight.
- **Productive Equities (Large Tech):** Drive capital expansion during disinflationary economic growth.
- **Digital Assets (Crypto):** Convex technological optionality held in strictly controlled, tiny risk slices.

---

## Understanding the Graphs and Empirical Intuition

Below is an analysis of what each research graph reveals, explaining the axes, data points, and practical lessons.

### Graph 1: Cumulative Performance vs Benchmark

![Allocation Equity Curves](reports/figures/13_g1_allocation_equity.png)

#### What the Axes and Lines Show
- **Horizontal axis (X):** 20-year timeline from 2004 through 2026, spanning multiple business cycles, crashes, and bull runs.
- **Vertical axis (Y):** Growth of \$1 on a logarithmic scale. Equal vertical distances represent equal percentage gains.
- **Gray dashed curve:** The S&P 500 index (SPY).
- **Orange/Blue curves:** The risk-parity allocation framework across different risk tiers (Careful, Balanced, Bold).

#### What the Graph Reveals
Notice how the gray benchmark curve plummets during the 2008 crisis (falling from \$1.50 down to \$0.70) and remains underwater for years before recovering. In contrast, the risk-allocated curve experiences only a shallow dip, continuing its upward trajectory.

#### The Practical Lesson
You do not need to forecast market tops or identify high-flying individual stocks to build long-term wealth. By capping drawdown losses during major recessions to −22% rather than −55%, the portfolio maintains capital compounding. A portfolio that loses 55% requires a 122% gain just to get back to even; a portfolio that loses 22% needs only a 28% gain to reach new all-time highs.

---

### Graph 2: Drawdowns and the Anatomy of Capital Destruction

![Drawdown Comparison](reports/figures/06_g2_drawdowns.png)

#### What the Axes and Lines Show
- **Horizontal axis (X):** Trading dates from 2004 to 2026.
- **Vertical axis (Y):** Drawdown percentage from the previous all-time peak (0% represents being at an all-time high).
- **Gray filled area:** The S&P 500 drawdown depth and recovery duration.
- **Colored overlay lines:** Drawdown profile of the risk-budgeted portfolio.

#### What the Graph Reveals
The gray area illustrates how investors in the standard market index spent nearly six consecutive years (2008 to 2013) underwater, waiting to recover from the subprime collapse. During the 2020 crash, the index dropped −34% in weeks; during 2022, it fell −24%.

The risk-managed portfolio's maximum drawdown over the entire 20-year span was −22.1%. During the 2022 bear market, while benchmark equities and long bonds both cratered, the portfolio's drawdown was contained at −12.8%.

#### The Practical Lesson
Drawdown duration is the primary reason retail and institutional investors abandon investment plans at market bottoms. Containing drawdown depth preserves psychological resilience and allows mechanical rebalancing to compound capital uninterrupted.

---

### Graph 3: Volatility Clustering and Measuring Swings (Rolling vs EWMA)

![Volatility Modeling](reports/figures/03_g2_rolling_vs_ewma.png)

#### What the Axes and Lines Show
- **Horizontal axis (X):** Time series over trading sessions.
- **Vertical axis (Y):** Annualized percentage volatility (the expected wiggle or swing).
- **Blue line:** Standard 63-day rolling window volatility.
- **Orange line:** Exponentially Weighted Moving Average (EWMA with decay $\lambda = 0.94$).

#### What the Graph Reveals
When a volatility shock hits (such as the market dislocations in early 2020 or 2022), the orange EWMA line jumps immediately within days, adjusting its risk estimate to protect capital. The blue rolling line reacts slowly and sluggishly.

Furthermore, exactly 63 days after the shock ends, the blue line suddenly drops off a cliff—not because the market calmed down that day, but because the shock dropped out of the fixed lookback window (a statistical artifact known as a "ghost feature"). The orange EWMA line fades naturally and smoothly, with a true half-life of approximately 11 trading days.

#### The Practical Lesson
Fixed lookback windows create lag and false signals. EWMA volatility reacts immediately to regime shifts, allowing the portfolio to reduce position sizes as soon as risk widens, and restore position sizes as volatility recedes.

---

### Graph 4: Fat Tails and Why the Gaussian Bell Curve Fails

![Fat Tails and Histograms](reports/figures/03_g3_hist_qq.png)

#### What the Axes and Lines Show
- **Top panels (Histograms):** Distribution of daily moves standardized into z-scores ($z = (r - \mu) / \sigma$). The red line is the theoretical Gaussian bell curve. The vertical axis is plotted on a log scale.
- **Bottom panels (QQ Plots):** Empirical quantiles plotted against theoretical normal quantiles. Dots along the straight line indicate normal behavior; dots that peel away into an "S" shape indicate extreme fat tails.

#### What the Graph Reveals
In every single asset analyzed (SPY, Bitcoin, Nvidia, Treasuries), extreme days peel away from the red line. SPY displays an excess kurtosis of 7.9, featuring a +9.5 standard deviation move in early 2025 that the normal distribution claims should virtually never occur in the history of the universe. Bitcoin exhibits a −7.1 standard deviation day.

#### The Practical Lesson
If you calculate risk using textbook formulas that assume normal distributions, your model will fail during market stress. Real markets have fat tails. Modeling risk requires capturing empirical percentiles directly from market history, without assuming Gaussian symmetry.

---

### Graph 5: The Clustered Correlation Heatmap (How Many Real Bets Do You Have?)

![Correlation Heatmap](reports/figures/03_g4_corr_clustered.png)

#### What the Axes and Cells Show
- **Grid:** Every asset plotted against every other asset.
- **Color Scale:** Deep red indicates positive correlation (+1.0); white indicates zero correlation (0.0); blue indicates inverse movement (−1.0).
- **Tree Dendrogram:** Hierarchical clustering grouping assets that trade together.

#### What the Graph Reveals
The assets naturally cluster into distinct blocks:
1. **Crypto and MicroStrategy:** BTC, ETH, and MSTR trade as a single synchronized block (correlation 0.72 to 0.82). MSTR is legally an equity, but behaviorally it trades as a leveraged crypto proxy.
2. **Oil and Commodities:** USO, XOM, CVX, and DBC form a tight block (USO and DBC correlation is 0.91).
3. **Gold:** GLD and gold miner Barrick Mining (B) move together (0.73).
4. **Bonds:** TLT and SHY form a cohesive rates block (0.61).
5. **US Big Tech:** AAPL, MSFT, NVDA, GOOGL, META move with SPY (0.67 to 0.71).

Across 20 assets, the average pairwise correlation is 0.21. Using the diversification formula:

$$N_{\text{eff}} = \frac{N}{1 + (N - 1)\bar{\rho}} = \frac{20}{1 + 19 \times 0.21} \approx 3.9$$

#### The Practical Lesson
Owning 20 ticker symbols does not mean you have 20 independent investments. In reality, you have **approximately four independent economic bets**. Diversification is not about the number of positions; it is about allocating across uncorrelated macroeconomic behavioral blocks.

---

### Graph 6: The Risk Model Report Card (Statistical Verification)

![Risk Report Card](reports/figures/17_g1_risk_report_card.png)

#### What the Bars and Tests Show
- **Left section:** Kupiec Likelihood Ratio test evaluating breach frequency over out-of-sample holdouts. The nominal target is 5.0% (a 1-in-20 bad-month event).
- **Right section:** Christoffersen independence test evaluating whether tail loss breaches cluster together in consecutive panics.

#### What the Graph Reveals
The realized breach rate for the bad-case warning across the 10-year holdout was **5.9%** on the project universe and **5.7%** on an uncurated ETF universe, passing the Kupiec test ($p > 0.05$). Crucially, **100% of assets passed the Christoffersen test**, confirming zero significant clustering during market stress.

#### The Practical Lesson
The risk numbers displayed by the system are verified against realized history. When the terminal warns that an asset has an expected monthly downside of 12%, that boundary holds true as an honest, un-clustered tail metric.

---

## How to Minimize Risk in Practice

To implement these findings, the framework follows four mechanical rules:

### 1. Sizing by Inverse Volatility
Capital is allocated inversely proportional to each asset's forecast swing:

$$w_i \propto \frac{1}{\sigma_i}$$

- An asset with an expected monthly swing of $\pm 30\%$ (such as Bitcoin or high-beta semiconductor equities) receives a small allocation of 2% to 5%.
- An asset with an expected monthly swing of $\pm 2.5\%$ (such as short-term Treasuries) receives a larger allocation of 20% to 30%.
- **Result:** Each dollar invested carries proportional risk, preventing volatile instruments from dominating portfolio variance.

### 2. Multi-Segment Balance
The portfolio distributes capital across the six macroeconomic segments: Crypto, Tech, Gold, Oil, Real Assets, and Bonds. No individual segment is allowed to dominate the risk budget, ensuring that whether the market encounters inflation, deflation, or growth, at least one segment acts as a counterweight.

### 3. Weekly Rebalancing Bands ($\pm 25\%$)
Frequent trading erodes capital through transaction costs. The terminal checks allocations once per week on Monday:
- Positions that remain within $\pm 25\%$ of their target allocation are left untouched.
- Trades smaller than \$25 are suppressed.
- Only when an asset drifts outside its tolerance band is a rebalancing order generated.
- **Result:** Turnover is reduced by over 80% compared to daily rebalancing, allowing the portfolio to harvest the volatility rebalancing premium while absorbing trading costs.

---

## Terminal Architecture and Live Monitoring

The live application provides seven functional workspaces:

1. **OVERVIEW:** Live ticker tape, segment risk cards with visual swing indicators, a 3D interactive orthographic globe tracking geopolitical tension across 44 countries, and macroeconomic warning gauges.
2. **PLAN:** Real-time risk budgeting calculator across Careful, Balanced, Bold, and Custom profiles, with order generation and weekly portfolio tracking.
3. **CALCULATOR:** Empirical capital simulator showing typical (2-in-3) and tail (1-in-20) dollar outcomes for any invested amount based on verified distributions.
4. **ASSET DETAIL:** Individual asset view showing 80-bin 21-day return histograms, 12-month historical price trajectories, and rolling volatility regimes.
5. **WORLD:** Macroeconomic indicators (VIX, yield curve inversion, credit default spreads, Sahm recession rule, breakeven inflation) and historical crisis playbook analysis.
6. **NEWS:** Live financial RSS headlines from BBC and CNBC with direct clickable links to source articles, themed tags, and optional Claude AI macro summaries.
7. **ALERTS:** Auditable 60-day feed of debounced factual market events (volatility regime shifts, $3\sigma$ moves, trend reversals).

---

## About the Author

**Fahad Naseer**  
Quantitative researcher and software developer specializing in empirical financial econometrics, volatility modeling, systematic capital allocation, and trading infrastructure.

- GitHub: [https://github.com/fahadnaseerhs](https://github.com/fahadnaseerhs)
- Repository: [https://github.com/fahadnaseerhs/Quant-Momentum](https://github.com/fahadnaseerhs/Quant-Momentum)
- Email: [fahadnaser451@gmail.com](mailto:fahadnaser451@gmail.com)

---

## License

This project is open-source and licensed under the MIT License. See the [LICENSE](LICENSE) file for complete details.
