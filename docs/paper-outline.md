# Paper Outline: Information Propagation Speed in Prediction Markets

## Title Options
1. "Shock-Accelerated Information Flow: Hourly Propagation Networks in Kalshi Prediction Markets"
2. "How Fast Do Prediction Markets Process Economic Information? Evidence from Kalshi"
3. "Information Propagation Speed Doubles During Economic Crises: Evidence from Prediction Markets"

## Abstract (~150 words)
We construct a directed information propagation network from 446 statistically significant Granger-causal pairs across 4 economic domains (inflation, monetary policy, labor, macro) in Kalshi prediction markets. After ADF stationarity testing and Bonferroni correction, we find: (1) inflation→monetary_policy propagation at 3h median is significantly faster than the reverse at 5h (Mann-Whitney p=0.0008); (2) information flows 2x faster during economic shocks — median lag drops from 8h to 4h (p<0.001); (3) markets become significantly better calibrated during high uncertainty (Brier 0.353 vs 0.512, p<0.05). An LLM-based semantic filter identifies economically plausible mechanisms (Phillips Curve, Taylor Rule) with 32% approval rate but these do not translate to trading alpha. Our findings suggest prediction markets function as a high-frequency information aggregation mechanism that accelerates during periods of economic stress.

## 1. Introduction
- Prediction markets aggregate dispersed information into prices
- Literature focuses on accuracy and calibration; information *speed* is understudied
- Contribution: first hourly-resolution information propagation network within prediction market sub-domains
- Three key findings: directional asymmetry, shock acceleration, uncertainty-improved calibration

## 2. Data
- **Source**: Kalshi prediction markets (Oct 2024 - Feb 2026)
- **Markets**: 2,001 settled markets, 1,028 economics-relevant, 289 with hourly candle data
- **Domains**: inflation (CPI), monetary policy (Fed Funds), labor (Jobless Claims), macro (GDP)
- **External benchmarks**: EPU (Baker-Bloom-Davis), VIX (CBOE), S&P 500
- **Economic events**: 31 curated events (12 surprises), CPI/FOMC/NFP/GDP releases

## 3. Methodology

### 3.1 Granger Causality Pipeline
- ADF stationarity testing with automatic differencing (max 2 rounds)
- Pairwise F-tests at lags 1-24h on cross-domain pairs with 48h+ overlap
- Bonferroni correction at α=0.01
- F-stat overflow guards (reject > 10^6)
- Result: 3,957 tests → 446 significant pairs

### 3.2 Information Propagation Network
- Aggregate Granger pairs into domain-level directed graph
- Edge weight = median propagation lag (hours)
- Node metrics: influence score (outgoing speed × volume), receptivity score (incoming)
- Asymmetry test: Mann-Whitney U on lag distributions for bidirectional domain pairs

### 3.3 Shock-Regime Analysis
- Define shock windows: ±3 days around 12 surprise economic events
- Classify each Granger pair by shock/calm overlap
- Compare median lags across regimes

### 3.4 Calibration Analysis
- KUI (Kalshi Uncertainty Index): hourly percentage-return belief volatility, volume-weighted
- Regime assignment: mean KUI during market lifetime → terciles
- Brier score comparison with bootstrap CI (1,000 iterations)

### 3.5 LLM Semantic Filtering
- Grok-3-mini assesses economic plausibility of all 446 pairs
- 5-point scale, threshold ≥ 4 for approval
- Compare trading performance of all-Granger vs LLM-filtered portfolios

## 4. Results

### 4.1 Propagation Network Structure
- Table: domain pair breakdown (6 directed edges)
- Figure: interactive network visualization (nodes by market count, edges by lag speed)
- Key finding: inflation→monetary_policy at 3h is the fastest channel

### 4.2 Directional Asymmetry
- inflation→monetary_policy: 3h vs 5h reverse (p=0.0008)
- Interpretation: CPI expectations propagate to Fed rate expectations faster than the reverse
- Consistent with forward-looking Taylor Rule

### 4.3 Shock Acceleration
- Overall: 4h shock vs 8h calm (p<0.001)
- macro→inflation: 4h vs 12h (p=0.011)
- inflation→macro: 6h vs 13h (p<0.001)
- Figure: lag distribution histograms, shock vs calm overlay

### 4.4 Calibration Under Uncertainty
- Brier: 0.353 (high KUI) vs 0.512 (low KUI), bootstrap CI [-0.242, -0.016]
- GDP markets: 0.196 vs 0.802 — dramatic improvement during uncertainty
- Interpretation: economic stress attracts more informed/sophisticated participation

### 4.5 LLM Filtering
- 143/446 approved (32%): Phillips Curve (labor→inflation), Taylor Rule (inflation→monetary_policy)
- Trading: Sharpe -2.26 with 23 trades — network structure is publishable, trading alpha is not
- LLM correctly identifies mechanisms but lead-lag is too noisy for individual market exploitation

### 4.6 Cross-Validation: Hourly Event Study
- 20 events with hourly data, Kalshi reacts within 17-28h depending on event type
- Surprise events: -56h lead vs EPU; non-surprise: ~0h
- Directionally consistent with Exp 1 network but underpowered (Wilcoxon p=0.10)

## 5. Discussion

### 5.1 Economic Mechanisms
- **Information cascade**: CPI data → inflation market repricing → monetary policy repricing (3h)
- **Shock acceleration**: uncertainty increases trader attention, narrows bid-ask spreads, speeds information incorporation — parallels findings in equity markets (Ederington & Lee 1993)
- **Calibration paradox**: markets are better calibrated when it matters most, supporting the "wisdom of crowds under pressure" hypothesis

### 5.2 Comparison with Literature
- Dreber et al. (2015): prediction market accuracy improves with more participants → our regime finding aligns
- Arrow et al. (2008): prediction markets as information aggregation → we add the speed dimension
- Berg et al. (2008): IEM accuracy → we extend to hourly resolution within domain structure

### 5.3 Limitations
- **Small n for event study**: only 12 surprise events with both hourly and daily data
- **Trading failure**: statistical structure doesn't translate to profitable signals
- **KUI invalidation**: methodology fix destroyed the KUI→EPU finding — highlights sensitivity to construction choices
- **Domain coverage**: only 4 domains have sufficient hourly data; crypto/politics excluded
- **Confounding**: shock periods may coincide with higher volume/liquidity → speed increase may be mechanical

### 5.4 Methodology Lessons
- ADF stationarity is critical: 43% of results were spurious without it
- F-stat overflow: numerical artifacts can produce seemingly significant results at F>10^6
- Construction choices matter: absolute vs percentage returns changed KUI correlation sign

## 6. Conclusion
- Prediction markets process economic information at hourly timescales
- Information flow accelerates 2x during shocks — markets work best when it matters most
- The inflation→monetary_policy channel is the fastest and most asymmetric
- Future work: minute-resolution analysis (Kalshi API supports 1-min candles), larger event sample, causal identification strategies

## Figures
1. Information propagation network (interactive HTML + static PNG)
2. Lag distribution histograms by domain pair
3. Shock vs calm lag comparison (boxplots)
4. Hourly event window panels (4 surprise events)
5. Calibration curves by uncertainty regime
6. Reaction speed by event type (bar chart)

## Tables
1. Domain pair breakdown (6 edges)
2. Shock-regime lag comparison (with p-values)
3. Calibration by uncertainty regime (Brier scores)
4. LLM filtering results (score distribution)
5. Event study results (hourly + daily comparison)
