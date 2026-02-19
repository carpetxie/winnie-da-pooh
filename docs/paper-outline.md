# Paper Outline: Information Propagation in Prediction Markets

## Title Options
1. "Directional Information Flow in Prediction Markets: Evidence from Kalshi"
2. "How Fast Do Prediction Markets Process Economic Information? Hourly Evidence from Kalshi"
3. "Prediction Markets Calibrate Better Under Pressure: Evidence from Kalshi"

## Abstract (~150 words)
We construct a directed information propagation network from 379 statistically significant Granger-causal pairs across 4 economic domains (inflation, monetary policy, labor, macro) in Kalshi prediction markets. After ADF stationarity testing, within-pair and cross-pair Bonferroni correction, and permutation validation, we find: (1) inflation→monetary_policy propagation at 3h median is significantly faster than the reverse at 5h (Mann-Whitney p=0.0008, permutation p<0.001); (2) 39% of Granger pairs are bidirectional (co-movement), but the 231 unidirectional pairs preserve the directional asymmetry; (3) markets are genuinely better calibrated during high uncertainty — Murphy reliability 0.123 vs 0.262 (p<0.05), surviving base rate controls. We also report two invalidated findings: shock-regime acceleration (circular classification artifact) and a KUI→EPU Granger result (absolute return bias). Our methodology corrections illustrate common pitfalls in prediction market microstructure research.

## 1. Introduction
- Prediction markets aggregate dispersed information into prices
- Literature focuses on accuracy and calibration; information *speed* and *direction* are understudied
- Contribution: first hourly-resolution information propagation network within prediction market sub-domains
- Two key surviving findings: directional asymmetry, uncertainty-improved calibration
- Also contribute methodology: two invalidated findings with lessons

## 2. Data
- **Source**: Kalshi prediction markets (Oct 2024 - Feb 2026)
- **Markets**: 2,001 settled markets, 1,028 economics-relevant, 289 with hourly candle data
- **Domains**: inflation (CPI), monetary policy (Fed Funds), labor (Jobless Claims), macro (GDP)
- **External benchmarks**: EPU (Baker-Bloom-Davis), VIX (CBOE), S&P 500

## 3. Methodology

### 3.1 Granger Causality Pipeline
- ADF stationarity testing with automatic differencing (max 2 rounds)
- Pairwise F-tests at lags 1-24h on cross-domain pairs with 48h+ overlap
- **Within-pair Bonferroni**: p_corrected = p_raw × max_lag (corrects for selecting best of 24 lags)
- **Cross-pair Bonferroni**: at α=0.01
- F-stat overflow guards (reject > 10^6)
- Result: 3,957 tests → 379 significant pairs

### 3.2 Information Propagation Network
- Aggregate Granger pairs into domain-level directed graph
- Edge weight = median propagation lag (hours)
- Asymmetry test: Mann-Whitney U on lag distributions for bidirectional domain pairs
- Bidirectional pair flagging: remove pairs where both A→B and B→A significant

### 3.3 Permutation Validation
- Shuffle domain labels across tickers (1,000 permutations)
- Test: observed cross-domain pair count vs null distribution
- Test: observed inflation→MP asymmetry vs null

### 3.4 Calibration Analysis with Murphy Decomposition
- Mid-life price as probability forecast, Brier score by KUI tercile
- Murphy decomposition: Brier = reliability - resolution + uncertainty
- Isolates true calibration (reliability) from base rate effects (uncertainty)
- Bootstrap CI on reliability difference (1,000 iterations)

### 3.5 LLM Semantic Filtering
- Grok-3-mini assesses economic plausibility of all 379 pairs
- 5-point scale, threshold ≥ 4 for approval

## 4. Results

### 4.1 Propagation Network Structure
- Table: domain pair breakdown (6 directed edges)
- 231 unidirectional + 74 bidirectional pairs
- Key finding: inflation→monetary_policy at 3h is the fastest unidirectional channel

### 4.2 Directional Asymmetry (Validated)
- inflation→monetary_policy: 3h vs 5h reverse (p=0.0008)
- Permutation test: p<0.001 (both cross-domain count and asymmetry)
- Interpretation: CPI expectations propagate to Fed rate expectations faster than the reverse

### 4.3 Calibration Under Uncertainty (Validated)
- Murphy reliability: 0.123 (high KUI) vs 0.262 (low KUI), bootstrap CI [-0.209, -0.013]
- Base rates differ (0.362 vs 0.522) but reliability test isolates pure calibration
- GDP markets: Brier 0.196 vs 0.802 — dramatic improvement during uncertainty

### 4.4 Invalidated Findings (Methodology Lessons)
- **Shock acceleration**: circular classification artifact. Shock-fraction approach shows p=0.48.
- **KUI→EPU Granger**: absolute return bias. p=0.024 → p=0.658 after percentage returns.
- **Lag selection**: 67 of 446 pairs lost to within-pair Bonferroni correction.
- Lessons: stationarity matters (43% spurious), classification must be non-circular, return definition changes results.

### 4.5 Hourly Event Study (Suggestive)
- Kalshi leads EPU by ~56h for surprise events
- Wilcoxon p=0.10 — directionally consistent but underpowered

## 5. Discussion

### 5.1 Economic Mechanisms
- **Taylor Rule channel**: CPI data → inflation repricing → monetary policy repricing (3h)
- **Calibration paradox**: markets calibrate better when it matters most
- **Co-movement vs causation**: 39% bidirectional pairs warrant caution

### 5.2 Comparison with Literature
- Arrow et al. (2008): prediction markets as information aggregation → we add the speed dimension
- Berg et al. (2008): IEM accuracy → we extend to hourly resolution
- Ederington & Lee (1993): uncertainty and information processing speed in equity markets

### 5.3 Limitations
- **Bidirectional pairs**: 39% indicate confounding or synchronous information arrival
- **Trading failure**: statistical structure doesn't translate to profitable signals
- **Domain coverage**: only 4 domains have sufficient hourly data
- **Shock regime**: could not cleanly separate shock/calm with available data
- **Small n for hourly event study**: only 12 surprise events

## 6. Conclusion
- Prediction markets show statistically significant directional information flow at hourly timescales
- The inflation→monetary_policy channel is the fastest and most asymmetric (permutation-validated)
- Markets calibrate better under uncertainty (Murphy-decomposition-validated)
- Methodology matters: two initially significant findings were invalidated by proper corrections
- Future work: minute-resolution analysis, larger event sample, instrumental variable approaches

## Figures
1. Information propagation network (unidirectional pairs only)
2. Calibration curves by uncertainty regime
3. Murphy decomposition comparison (reliability by regime)
4. Permutation null distributions
5. Hourly event window panels (4 surprise events)

## Tables
1. Domain pair breakdown with lag statistics
2. Permutation test results
3. Murphy decomposition by uncertainty regime
4. Bidirectional vs unidirectional pair analysis
5. Invalidated findings summary
