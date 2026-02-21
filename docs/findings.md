# Distributional Calibration of Prediction Markets: Evidence from Implied CDF Scoring

**Date:** 2026-02-20
**Status:** Post PhD-review, iteration 5. Fixed historical benchmark contamination, PIT sign error, added CRPS/MAE ratio.

## Abstract

We evaluate the distributional calibration of Kalshi prediction markets using 336 multi-strike contracts across 41 economic events. Applying Breeden-Litzenberger reconstruction to extract implied CDFs, we score them using the Continuous Ranked Probability Score (CRPS) — the first proper scoring rule evaluation of prediction market implied distributions. We find heterogeneous calibration: Jobless Claims markets (weekly frequency, n=16) outperform regime-appropriate historical baselines (CRPS 4,840 vs 8,758; Wilcoxon p=0.047), while CPI markets (monthly frequency, n=14) do not beat historical baselines (p=0.709) and their distributional spread is actively harmful (CRPS/MAE=1.32). PIT analysis suggests CPI markets underestimate inflation (mean PIT=0.61), though this is preliminary at n=14 (KS p=0.22). In a point forecast horse race, Kalshi's CPI implied mean significantly beats random walk (p=0.026, d=-0.60) but comparisons to professional forecasters are underpowered. TIPS breakeven rates Granger-cause Kalshi CPI prices (F=12.2, p=0.005) but not vice versa. We document that three initially "significant" findings were invalidated by event-level clustering corrections, and the original Jobless Claims benchmark was contaminated by COVID-era data (inflating the CRPS advantage from 1.8x to 7.3x).

---

## 1. Methodology: Implied CDFs from Multi-Strike Markets

336 multi-strike markets across 41 events (14 CPI, 3 GDP, 16 Jobless Claims, 8 other). For each event at each hour, we reconstruct the implied CDF using Breeden-Litzenberger (1978): strike-ordered cumulative probabilities from binary contracts.

### No-Arbitrage Efficiency

| Metric | Value |
|--------|-------|
| Total hourly CDF snapshots | 7,166 |
| Violating snapshots (non-monotone CDF) | 202 (2.8%) |
| Reversion rate | 168/195 = 86% within 1 hour |
| CPI median forecast error | 0.05 percentage points |

2.8% of snapshots violate CDF monotonicity, with 86% reverting within one hour — consistent with transient mispricing in thin markets, not systematic arbitrage.

---

## 2. Main Result: Heterogeneous Distributional Calibration

### CRPS by Event Series

33 events with complete CRPS scoring. Historical benchmarks use regime-appropriate windows (Jobless Claims: 2022+, post-COVID normalization).

| Series | n | Kalshi CRPS | Uniform CRPS | Historical CRPS |
|--------|---|------------|-------------|----------------|
| KXJOBLESSCLAIMS | 16 | 4,840 | 6,100 | 8,758 |
| KXCPI | 14 | 0.108 | 0.042 | 0.091 |
| KXGDP | 3 | 0.509 | 0.672 | 1.098 |

### Per-Series Wilcoxon Tests

| Test | p-value | Significant |
|------|---------|-------------|
| **KXJOBLESSCLAIMS vs Historical (n=16, post-COVID)** | **0.047** | **Yes** |
| KXJOBLESSCLAIMS vs Historical (n=16, COVID-contaminated) | <0.0001 | Yes* |
| KXCPI vs Historical (n=14) | 0.709 | No |
| KXCPI vs Uniform (n=14) | 0.999 | No (worse) |
| Pooled Kalshi vs Historical (n=33, post-COVID) | 0.117 | No |

*The COVID-contaminated benchmark (2020-2025) includes claims of 3-6 million vs current 200-250K, inflating the CRPS advantage from 1.8x to 7.3x. The regime-appropriate benchmark (2022+) gives an honest 1.8x improvement.

### CRPS/MAE Ratio (Distributional Value-Add)

| Series | CRPS | MAE | CRPS/MAE | Interpretation |
|--------|------|-----|----------|----------------|
| KXCPI | 0.108 | 0.082 | **1.32** | Distribution harmful (spread adds noise) |
| KXGDP | 0.509 | 1.097 | 0.46 | Distribution adds substantial value |
| KXJOBLESSCLAIMS | 4,840 | 12,959 | **0.37** | Distribution adds massive value |

For CPI, CRPS > MAE — the distributional spread is *actively harmful*. A point forecast (the implied mean) performs better than the full distribution. For Jobless Claims, the distribution captures 63% more information than the point forecast alone.

### Temporal CRPS Evolution

| Lifetime % | CPI (vs uniform) | Jobless Claims (vs uniform) |
|-----------|-------------------|----------------------------|
| 10% (early) | 1.96x (worse) | 0.91x (better) |
| 50% (mid) | 2.55x (worse) | 0.79x (better) |
| 90% (late) | 1.16x (converging) | 0.78x (stable) |

CPI markets learn over time but never achieve calibration. Jobless Claims beat uniform from inception.

### CPI PIT Analysis (Appendix-Level)

| Metric | CPI (n=14) | Well-Calibrated |
|--------|-----------|-----------------|
| Mean PIT | 0.609 | 0.500 |
| Std PIT | 0.222 | 0.289 |
| KS test | p=0.221 | — |

Mean PIT = 0.61 (95% CI: [0.49, 0.73]): realized CPI tends to fall in the upper half of the implied distribution, suggesting markets *underestimate* inflation. However, the KS test does not reject uniformity (p=0.22), so this is suggestive only. At n=14, this observation warrants monitoring, not strong claims.

---

## 3. Context: Information Hierarchy (TIPS → Kalshi)

### TIPS Granger Causality

286 overlapping days (Oct 2024 - Jan 2026):

| Direction | Best Lag | F-stat | p-value |
|-----------|----------|--------|---------|
| TIPS → Kalshi | 1 day | 12.24 | 0.005 |
| Kalshi → TIPS | — | 0.0 | 1.0 |

TIPS breakeven rates lead Kalshi CPI prices. Kalshi is a useful aggregator even though it's not the first mover — it incorporates TIPS information while adding granularity through its multi-strike structure (distributional information that a single breakeven rate cannot provide).

### CPI Point Forecast Horse Race

| Forecaster | Mean MAE | Cohen's d | p-value | n |
|-----------|----------|-----------|---------|---|
| **Kalshi implied mean** | **0.082** | — | — | **14** |
| SPF (annual/12 proxy) | 0.110 | -0.25 | 0.211 | 14 |
| TIPS breakeven (monthly) | 0.112 | -0.27 | 0.163 | 14 |
| Trailing mean | 0.118 | -0.32 | 0.155 | 14 |
| Random walk (last month) | 0.143 | **-0.60** | **0.026*** | 14 |

Kalshi significantly beats random walk (p=0.026, d=-0.60). Comparisons to professional forecasters are underpowered (need 76-107 more months at observed effect sizes).

---

## 4. Supporting: Market Maturity and Calibration

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

The T-24h gradient (7x) is largely mechanical. The controlled analysis (50% of lifetime) shows a 1.5x residual — short-lived markets are modestly worse, but medium and long are similar. Remaining confounds (contract type, liquidity, trader composition) prevent causal interpretation.

---

## Downgraded and Invalidated Findings

### Downgraded

| Finding | Naive | Corrected | Issue |
|---------|-------|-----------|-------|
| Calibration under uncertainty | p=0.016* | CI includes zero | Cluster-robust bootstrap |
| Microstructure event response | p=0.013* | p=0.542 | Within-event correlation |
| Shock propagation (surprise) | p=0.0002* | p=0.436 | Within-event correlation |
| Information asymmetry (lead-lag) | p=0.0008* | p=0.0008 | Confirmatory (Taylor Rule) |
| Maturity gradient | 7x | 1.5x | Observation timing confound |
| **Jobless Claims CRPS headline** | **p<0.0001** | **p=0.047** | **COVID-contaminated benchmark** |

### Invalidated

| Finding | Original | Corrected | Reason |
|---------|----------|-----------|--------|
| Shock acceleration | p<0.001 | p=0.48 | Circular classification |
| KUI leads EPU | p=0.024 | p=0.658 | Absolute return bias |
| Trading Sharpe | +5.23 | -2.26 | Small-sample artifact |

---

## Methodology

### Data
- 6,141 settled Kalshi markets with outcomes (Oct 2024 - Feb 2026)
- 336 multi-strike markets across 41 events (CPI, GDP, Jobless Claims)
- External: TIPS breakeven (T10YIE), SPF median CPI, FRED historical data

### Key Corrections
1. **Event-level clustering**: Three findings invalidated by correcting independence violations
2. **Per-series Wilcoxon**: Pooled p=0.0001 was misleading; per-series tests reveal heterogeneity
3. **Controlled observation timing**: T-24h maturity gradient (7x) reduced to 1.5x at 50% lifetime
4. **Regime-appropriate benchmarks**: Jobless Claims historical window changed from 2020+ to 2022+ (post-COVID), reducing advantage from 7.3x to 1.8x
5. **PIT sign correction**: cdf_values store survival P(X>strike), not CDF P(X≤strike). Corrected PIT = 1 - interpolated survival. Mean PIT changed from 0.39 to 0.61 (reversed interpretation)
6. **CRPS/MAE ratio**: Distribution-vs-point ratio reported per series. CPI ratio > 1 (distribution harmful); Jobless Claims ratio = 0.37 (distribution adds value)
7. **Effect sizes and power**: Cohen's d and power analysis for all underpowered comparisons

### Experiments Summary

| # | Name | Role in Paper |
|---|------|---------------|
| 7 | Implied Distributions | Section 1: Methodology |
| 12 | CRPS Scoring | Section 2: Main result |
| 13 | Unified + Horse Race | Sections 2-3: Per-series tests, horse race |
| 8 | TIPS Comparison | Section 3: Information hierarchy |
| 11 | Favorite-Longshot Bias | Section 4: Maturity (controlled) |
| 1, 9 | Lead-Lag, Indicator Network | Downgraded (confirmatory) |
| 2-6, 10 | Supporting experiments | Downgraded or invalidated |
