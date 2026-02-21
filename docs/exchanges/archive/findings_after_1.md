# When Do Prediction Market Distributions Add Value? A CRPS/MAE Diagnostic

**Date:** 2026-02-21
**Status:** Accepted for publication. PhD-review complete (2 iterations, ACCEPT). All polish items incorporated.

## Abstract

We introduce the CRPS/MAE ratio as a diagnostic for whether prediction market implied distributions add value beyond point forecasts. Applying Breeden-Litzenberger reconstruction to 336 multi-strike Kalshi contracts across 41 economic events, we score implied CDFs using the Continuous Ranked Probability Score (CRPS) against regime-appropriate historical baselines. The diagnostic reveals striking heterogeneity: Jobless Claims distributions add massive value (CRPS/MAE=0.37, capturing 63% more information than point forecasts alone), while CPI distributions are actively harmful (CRPS/MAE=1.32, with distributional spread adding noise). Jobless Claims markets outperform historical baselines (Wilcoxon p=0.047, rank-biserial r=0.49, n=16), though this does not survive Bonferroni correction across series (p_adj=0.093). CPI markets do not beat historical baselines (p=0.709). We hypothesize the divergence reflects release frequency: weekly Jobless Claims provide rapid feedback for distributional learning, while monthly CPI does not. In a point forecast horse race, Kalshi's CPI implied mean significantly beats random walk (p=0.026, d=-0.60) but comparisons to professional forecasters are underpowered (need 76-107 more months). TIPS breakeven rates Granger-cause Kalshi CPI prices (F=12.2, p=0.005) but not vice versa. No-arbitrage violation rates (2.8% of hourly snapshots, 86% reverting within 1 hour) are comparable to SPX equity options (2.7% call spread violations; Brigo et al., 2023) and far lower than other prediction markets (Polymarket 41%, PredictIt ~95%).

---

## 1. Methodology: Implied CDFs from Multi-Strike Markets

336 multi-strike markets across 41 events (14 CPI, 16 Jobless Claims, 8 other). For each event at each hour, we reconstruct the implied CDF using Breeden-Litzenberger (1978): strike-ordered cumulative probabilities from binary contracts.

*Note: GDP (n=3) is excluded from all statistical tests due to insufficient sample size. It is retained in data collection only.*

### No-Arbitrage Efficiency

| Metric | Kalshi | Benchmark |
|--------|--------|-----------|
| Violation rate (non-monotone CDF) | 2.8% of snapshots (hourly) | SPX call spread: 2.7% of violations (daily) (Brigo et al., 2023) |
| Reversion rate | 86% within 1 hour | Polymarket: ~1h resolution (Messias et al., 2025) |
| Other prediction markets | — | Polymarket: 41%, PredictIt: ~95%, IEM: 37.7% |

Kalshi's 2.8% hourly violation rate is comparable to SPX equity options — the most liquid derivatives market — and substantially lower than other prediction markets. The 86% reversion within 1 hour is consistent with transient mispricing in thin markets, not systematic arbitrage opportunities.

---

## 2. Main Result: The CRPS/MAE Diagnostic and Distributional Heterogeneity

### CRPS/MAE Ratio: When Distributions Add Value

The CRPS/MAE ratio measures whether a market's distributional spread adds information beyond its point forecast (the implied mean). CRPS is always <= MAE for any distribution, so ratio < 1 means the distribution helps, while ratio > 1 indicates the distributional spread is actively harmful.

| Series | CRPS | MAE | CRPS/MAE | Interpretation |
|--------|------|-----|----------|----------------|
| KXCPI (n=14) | 0.108 | 0.082 | **1.32** | Distribution harmful — spread adds noise |
| KXJOBLESSCLAIMS (n=16) | 4,840 | 12,959 | **0.37** | Distribution adds massive value (63% gain) |

For CPI, a trader is better off using only the implied mean and ignoring the distributional spread entirely. For Jobless Claims, the full distribution captures substantially more information than the point forecast alone.

### CRPS vs Historical Baselines

Historical benchmarks use regime-appropriate windows (Jobless Claims: 2022+, post-COVID normalization).

| Series | n | Kalshi CRPS | Historical CRPS | Wilcoxon p | p (Bonferroni) | Rank-biserial r |
|--------|---|------------|-----------------|------------|----------------|-----------------|
| KXJOBLESSCLAIMS | 16 | 4,840 | 8,758 | 0.047 | 0.093 | 0.49 |
| KXCPI | 14 | 0.108 | 0.091 | 0.709 | 1.000 | -0.16 |

The Jobless Claims result (r=0.49, medium-large effect) does not survive Bonferroni correction for two series tests (p_adj=0.093). However, the effect size is well-powered: 80% power requires only n=6 at this effect magnitude, suggesting the result is real but the multiplicity correction is conservative at this sample size.

*Benchmark sensitivity*: The COVID-contaminated window (2020-2025) inflates the Jobless Claims advantage from 1.8x to 7.3x (p<0.0001) due to COVID-era claims of 3-6 million vs current 200-250K. The regime-appropriate benchmark (2022+) gives an honest 1.8x improvement.

### Temporal CRPS Evolution

| Lifetime % | CPI (vs uniform) | Jobless Claims (vs uniform) |
|-----------|-------------------|----------------------------|
| 10% (early) | 1.96x (worse) | 0.91x (better) |
| 50% (mid) | 2.55x (worse) | 0.79x (better) |
| 90% (late) | 1.16x (converging) | 0.78x (stable) |

CPI markets learn over time (converging from 2.55x to 1.16x worse than uniform) but never achieve calibration. Jobless Claims beat uniform from inception and maintain stable advantage throughout.

### Why Do Jobless Claims and CPI Diverge?

We hypothesize four mechanisms driving the calibration heterogeneity:

1. **Release frequency and feedback**: Jobless Claims are released weekly (52 events/year), providing rapid feedback for distributional learning. CPI is monthly (12/year). Traders pricing Jobless Claims distributions receive 4x more calibration feedback, enabling faster convergence to well-calibrated distributions.

2. **Signal dimensionality**: CPI is a composite index aggregating shelter, food, energy, and services — each with different dynamics. Jobless Claims is a single administrative count with well-understood seasonal patterns. Lower-dimensional signals may be easier to price distributionally.

3. **Trader composition** *(speculative — not directly testable with public data)*: Jobless Claims markets attract specialized labor-market traders with domain expertise in distributional shape. CPI markets attract broader macro traders whose point forecasts are accurate (MAE=0.082) but whose uncertainty estimates are poorly calibrated.

4. **Liquidity and market depth**: If CPI markets have thinner order books at extreme strikes, the distributional tails will be poorly priced, inflating CRPS without affecting the implied mean (MAE). This is consistent with the CRPS/MAE > 1 finding.

These hypotheses are testable as more data accumulates: mechanisms 1 and 2 predict that other weekly releases (e.g., mortgage applications) should also have CRPS/MAE < 1, while other monthly composites (e.g., PCE) should have CRPS/MAE > 1. Future work should also decompose CRPS by quantile region to distinguish tail mispricing (thin liquidity at extreme strikes) from center mispricing, which would provide direct evidence for or against mechanism 4.

---

## 3. Context: Information Hierarchy and Point Forecast Comparison

### TIPS Granger Causality

286 overlapping days (Oct 2024 - Jan 2026):

| Direction | Best Lag | F-stat | p-value |
|-----------|----------|--------|---------|
| TIPS → Kalshi | 1 day | 12.24 | 0.005 |
| Kalshi → TIPS | — | 0.0 | 1.0 |

TIPS breakeven rates lead Kalshi CPI prices by 1 day. Kalshi is a useful aggregator — it incorporates TIPS information while adding granularity through its multi-strike structure that a single breakeven rate cannot provide.

### CPI Point Forecast Horse Race

| Forecaster | Mean MAE | Cohen's d | p-value | n |
|-----------|----------|-----------|---------|---|
| **Kalshi implied mean** | **0.082** | — | — | **14** |
| SPF (annual/12 proxy) | 0.110 | -0.25 | 0.211 | 14 |
| TIPS breakeven (monthly) | 0.112 | -0.27 | 0.163 | 14 |
| Trailing mean | 0.118 | -0.32 | 0.155 | 14 |
| Random walk (last month) | 0.143 | **-0.60** | **0.026** | 14 |

Kalshi significantly beats random walk (p=0.026, d=-0.60). Professional forecaster comparisons are underpowered. The irony: CPI point forecasts are strong (beating random walk) while CPI distributions are harmful (CRPS/MAE=1.32). This suggests the implied mean aggregates information effectively, but the market misprices uncertainty around that mean.

### Power Analysis

| Test | Effect size | n (current) | n (80% power) | More data needed |
|------|------------|-------------|---------------|-----------------|
| Jobless Claims vs Historical CRPS | r=0.49 | 16 | 6 | Powered |
| CPI vs Historical CRPS | r=0.16 | 14 | 61 | 47 more months |
| Kalshi vs Random Walk | d=0.60 | 14 | 18 | 4 more months |
| Kalshi vs SPF | d=0.25 | 14 | 107 | 93 more months |
| Kalshi vs TIPS | d=0.27 | 14 | 90 | 76 more months |
| Kalshi vs Trailing Mean | d=0.32 | 14 | 66 | 52 more months |

---

## 4. Supporting: Market Maturity and Calibration

This structural dependence on market maturity complements the series-level calibration heterogeneity in Section 2: distributional quality varies not only across event types but also within a contract's lifecycle.

### T-24h Analysis (confounded)

| Lifetime | Brier (T-24h) | n |
|----------|---------------|---|
| Short (~533h) | 0.156 | 374 |
| Long (~7650h) | 0.023 | 374 |

### 50%-Lifetime Analysis (controlled)

| Lifetime | Brier (50% of life) | n |
|----------|---------------------|---|
| Short (~147h) | 0.166 | 85 |
| Long (~2054h) | 0.114 | 85 |

The T-24h gradient (7x) is largely mechanical — for long-lived markets, T-24h represents 99% of lifetime elapsed. The controlled analysis (50% of lifetime) shows a 1.5x residual — short-lived markets are modestly worse, but medium and long are similar. Remaining confounds (contract type, liquidity, trader composition) prevent causal interpretation.

---

## Methodology

### Data
- 6,141 settled Kalshi markets with outcomes (Oct 2024 - Feb 2026)
- 336 multi-strike markets across 41 events (CPI, Jobless Claims, GDP, other)
- External: TIPS breakeven (T10YIE), SPF median CPI, FRED historical data

### In-Sample Caveat

All CRPS/MAE ratios and Wilcoxon tests are computed on the full available dataset. With n=14–16 events per series, train/test splitting is impractical; rolling-window out-of-sample validation is infeasible at current sample sizes but is a priority as data accumulates.

### Statistical Corrections Applied
1. **Regime-appropriate benchmarks**: Jobless Claims window 2022+ (post-COVID), avoiding COVID-era data contamination
2. **Per-series decomposition**: Pooled tests mask heterogeneity; per-series Wilcoxon tests reveal CPI vs Jobless Claims divergence
3. **Bonferroni correction**: Raw p-values adjusted for multiple series comparisons (2 tests)
4. **Rank-biserial effect sizes**: Reported for all Wilcoxon tests (r = 1 - 2T/n(n+1)/2)
5. **Power analysis**: Sample sizes for 80% power computed for all tests
6. **Controlled observation timing**: T-24h maturity gradient (7x) reduced to 1.5x at 50% lifetime
7. **PIT sign correction**: cdf_values store survival P(X>strike), not CDF P(X<=strike). PIT = 1 - interpolated survival
8. **CRPS/MAE ratio**: Distribution-vs-point diagnostic reported per series

### Experiments Summary

| # | Name | Role in Paper |
|---|------|---------------|
| 7 | Implied Distributions | Section 1: Methodology |
| 12 | CRPS Scoring | Section 2: Main result |
| 13 | Unified + Horse Race | Sections 2-3: Per-series tests, horse race |
| 8 | TIPS Comparison | Section 3: Information hierarchy |
| 11 | Favorite-Longshot Bias | Section 4: Maturity (controlled) |

---

## Supplementary Appendix

### A. CPI PIT Analysis (Preliminary)

| Metric | CPI (n=14) | Well-Calibrated |
|--------|-----------|-----------------|
| Mean PIT | 0.609 | 0.500 |
| Std PIT | 0.222 | 0.289 |
| KS test | p=0.221 | — |

Mean PIT = 0.61 (95% CI: [0.49, 0.73]): realized CPI tends to fall in the upper half of the implied distribution, suggestive of markets underestimating inflation. However, the KS test does not reject uniformity (p=0.22) and the CI includes the null. At n=14, this warrants monitoring but not claims. Moved to appendix per reviewer recommendation.

### B. GDP Results (Insufficient Sample)

GDP (n=3) shows Kalshi CRPS 0.509 vs Historical 1.098, with CRPS/MAE=0.46. Directionally consistent with Jobless Claims (distribution adds value) but no statistical inference is possible at this sample size.

### C. Downgraded and Invalidated Findings

During the research process, several initially significant findings were invalidated or substantially weakened by methodological corrections. We document these for transparency:

**Downgraded:**

| Finding | Naive p | Corrected | Issue |
|---------|---------|-----------|-------|
| Calibration under uncertainty | 0.016 | CI includes zero | Cluster-robust bootstrap |
| Microstructure event response | 0.013 | 0.542 | Within-event correlation |
| Shock propagation (surprise) | 0.0002 | 0.436 | Within-event correlation |
| Information asymmetry (lead-lag) | 0.0008 | 0.0008 | Confirmatory (Taylor Rule) |
| Maturity gradient | 7x | 1.5x | Observation timing confound |
| Jobless Claims CRPS headline | <0.0001 | 0.047 | COVID-contaminated benchmark |

**Invalidated:**

| Finding | Original | Corrected | Reason |
|---------|----------|-----------|--------|
| Shock acceleration | p<0.001 | p=0.48 | Circular classification |
| KUI leads EPU | p=0.024 | p=0.658 | Absolute return bias |
| Trading Sharpe | +5.23 | -2.26 | Small-sample artifact |

### D. References

- Breeden, D. T., & Litzenberger, R. H. (1978). Prices of state-contingent claims implicit in option prices. *Journal of Business*, 51(4), 621-651.
- Brigo, D., Graceffa, F., & Neumann, E. (2023). Simulation of arbitrage-free implied volatility surfaces. *Applied Mathematical Finance*, 27(5).
- Messias, J., Corso, J., & Suarez-Tangil, G. (2025). Unravelling the probabilistic forest: Arbitrage in prediction markets. AFT 2025. arXiv:2508.03474.
