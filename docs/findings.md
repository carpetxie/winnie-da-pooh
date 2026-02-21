# Distributional Calibration of Prediction Markets: Evidence from Implied CDF Scoring

**Date:** 2026-02-20
**Status:** Post PhD-review, iteration 4. Restructured as single focused paper.

## Abstract

We evaluate the distributional calibration of Kalshi prediction markets using 336 multi-strike contracts across 41 economic events. Applying Breeden-Litzenberger reconstruction to extract implied CDFs, we score them using the Continuous Ranked Probability Score (CRPS) — the first proper scoring rule evaluation of prediction market implied distributions. We find striking heterogeneity: Jobless Claims markets (weekly frequency, n=16) achieve well-calibrated distributions that massively outperform historical baselines (Wilcoxon p<0.0001), while CPI markets (monthly frequency, n=14) do not beat historical baselines (p=0.709). PIT analysis suggests CPI overconfidence reflects directional bias (mean PIT=0.39), though this is preliminary at n=14. In a point forecast horse race, Kalshi's CPI implied mean significantly beats random walk (p=0.026, d=-0.60) but comparisons to professional forecasters (SPF, TIPS) are underpowered. TIPS breakeven rates Granger-cause Kalshi CPI prices (F=12.2, p=0.005) but not vice versa, establishing the information hierarchy between bond and prediction markets. We document that three initially "significant" findings were invalidated by event-level clustering corrections.

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

2.8% of snapshots violate CDF monotonicity, with 86% reverting within one hour — consistent with transient mispricing in thin markets, not systematic arbitrage. The implied distributions are well-formed enough to score.

---

## 2. Main Result: Heterogeneous Distributional Calibration

### CRPS by Event Series

33 events with complete CRPS scoring:

| Series | n | Kalshi CRPS | Uniform CRPS | Historical CRPS |
|--------|---|------------|-------------|----------------|
| KXJOBLESSCLAIMS | 16 | 4,840 | 6,100 | 35,556 |
| KXCPI | 14 | 0.108 | 0.042 | 0.091 |
| KXGDP | 3 | 0.509 | 0.672 | 1.098 |

### Per-Series Wilcoxon Tests

| Test | p-value | Significant |
|------|---------|-------------|
| **KXJOBLESSCLAIMS vs Historical (n=16)** | **<0.0001** | **Yes** |
| KXCPI vs Historical (n=14) | 0.709 | No |
| KXCPI vs Uniform (n=14) | 0.999 | No (worse than uniform) |
| KXGDP vs Historical (n=3) | — | Insufficient data |

The pooled Wilcoxon across all series (p=0.0001) is misleading — it is driven entirely by Jobless Claims. Per-series tests are the honest metric, and they reveal that CPI distributions are *not* well-calibrated.

**Note on CRPS <= MAE**: CRPS is bounded above by MAE for any proper distribution. Comparisons between distributional CRPS and point-forecast MAE are mathematically favorable to the distribution and are therefore omitted. All comparisons here are distribution-vs-distribution.

### Temporal CRPS Evolution

| Lifetime % | CPI (vs uniform) | Jobless Claims (vs uniform) |
|-----------|-------------------|----------------------------|
| 10% (early) | 1.96x (worse) | 0.91x (better) |
| 50% (mid) | 2.55x (worse) | 0.79x (better) |
| 90% (late) | 1.16x (converging) | 0.78x (stable) |

CPI markets learn over time (converging toward uniform) but never achieve calibration. Jobless Claims beat uniform from inception. This suggests distributional calibration is an emergent property of trading frequency.

### CPI Overconfidence Diagnostic (PIT Analysis)

| Metric | CPI (n=14) | Well-Calibrated |
|--------|-----------|-----------------|
| Mean PIT | 0.391 | 0.500 |
| Std PIT | 0.222 | 0.289 |
| % in IQR | 57% | 50% |
| % in tails | 7% | 20% |
| KS test for uniformity | p=0.221 | — |

The PIT distribution is shifted left (mean 0.39): realized CPI consistently falls in the lower half of the implied distribution, suggesting the market systematically overestimates inflation. However, the KS test does not reject uniformity at n=14 (p=0.22), so this is preliminary. The 95% CI on mean PIT is approximately [0.27, 0.51] — compatible with both modest and substantial bias.

---

## 3. Context: Information Hierarchy (TIPS → Kalshi)

### TIPS Granger Causality

286 overlapping days (Oct 2024 - Jan 2026):

| Direction | Best Lag | F-stat | p-value |
|-----------|----------|--------|---------|
| TIPS → Kalshi | 1 day | 12.24 | 0.005 |
| Kalshi → TIPS | — | 0.0 | 1.0 |

TIPS breakeven rates (institutional bond market) Granger-cause Kalshi CPI prices (retail prediction market), not vice versa. This establishes the information hierarchy: the bond market sets the level, while the prediction market adds granularity through its multi-strike structure.

### CPI Point Forecast Horse Race

| Forecaster | Mean MAE | Cohen's d | p-value | n |
|-----------|----------|-----------|---------|---|
| **Kalshi implied mean** | **0.082** | — | — | **14** |
| SPF (annual/12 proxy) | 0.110 | -0.25 | 0.211 | 14 |
| TIPS breakeven (monthly) | 0.112 | -0.27 | 0.163 | 14 |
| Trailing mean | 0.118 | -0.32 | 0.155 | 14 |
| Random walk (last month) | 0.143 | **-0.60** | **0.026*** | 14 |

Kalshi significantly outperforms the random walk benchmark (p=0.026, medium-large effect). Comparisons to professional forecasters have insufficient power to distinguish:

| Comparison | |d| | n needed (80% power) | Additional months |
|-----------|-----|----------------------|-------------------|
| vs Random Walk | 0.60 | 18 | +4 |
| vs Trailing Mean | 0.32 | 66 | +52 |
| vs SPF | 0.25 | 107 | +93 |
| vs TIPS | 0.27 | 90 | +76 |

**SPF caveat**: SPF forecasts annual CPI (Q4/Q4 %), converted to monthly via annual_rate/12. This is an approximation that may bias against SPF.

---

## 4. Supporting: Market Maturity and Calibration

Economics-domain markets (n=1,141) show a calibration gradient by contract lifetime, but most of the effect is mechanical.

### T-24h Analysis (confounded)

| Lifetime | Brier (T-24h) | n |
|----------|---------------|---|
| Short (~533h) | 0.156 | 374 |
| Medium (~2585h) | 0.059 | 374 |
| Long (~7650h) | 0.023 | 374 |

### 50%-Lifetime Analysis (controlled)

| Lifetime | Brier (50% of life) | n |
|----------|---------------------|---|
| Short (~147h) | 0.166 | 85 |
| Medium (~409h) | 0.110 | 85 |
| Long (~2054h) | 0.114 | 85 |

The T-24h gradient (7x) is largely mechanical: long-lived markets at T-24h are observed at ~99% of lifetime (near-terminal prices), while short-lived markets are at ~57%. The controlled analysis (all markets evaluated at 50% of lifetime) shows a 1.5x gradient — short-lived markets are genuinely worse, but medium and long markets are nearly identical. The dominant factor is total information aggregation time, not maturity per se.

---

## Downgraded and Invalidated Findings

### Downgraded to Suggestive

| Finding | Direction | Naive p | Corrected p | Issue |
|---------|-----------|---------|-------------|-------|
| Calibration under uncertainty | High-uncertainty → better calibration | 0.016* | CI includes zero | Cluster-robust bootstrap (80 event clusters) |
| Microstructure event response | Spread narrows after events | 0.013* | 0.542 | 767 pairs from 31 events |
| Shock propagation (surprise) | Surprise → larger inflation response | 0.0002* | 0.436 | Hourly obs from 31 events |
| Information asymmetry (lead-lag) | Inflation → monetary policy at 3h | 0.0008* | 0.0008 | Confirmatory (Taylor Rule); relegated from main findings |
| Maturity gradient (T-24h) | 7x Brier gradient | — | 1.5x controlled | Observation timing confound |

### Invalidated

| Finding | Original | Corrected | Reason |
|---------|----------|-----------|--------|
| Shock acceleration | 4h vs 8h, p<0.001 | 6h vs 8h, p=0.48 | Circular classification artifact |
| KUI leads EPU (Granger) | p=0.024 | p=0.658 | Absolute return bias |
| Trading Sharpe | +5.23 (4 trades) | -2.26 (23 trades) | Small-sample artifact |

---

## Methodology

### Data
- 6,141 settled Kalshi markets with outcomes (Oct 2024 - Feb 2026)
- 336 multi-strike markets across 41 events (CPI, GDP, Jobless Claims)
- External: TIPS breakeven (T10YIE), SPF median CPI, FRED historical data

### Key Corrections
1. **Event-level clustering**: Three findings invalidated by correcting independence violations
2. **Per-series Wilcoxon**: Pooled p=0.0001 was a Jobless Claims story; CPI is non-significant
3. **Controlled observation timing**: T-24h maturity gradient (7x) reduced to 1.5x at 50% lifetime
4. **CRPS <= MAE**: Distribution-vs-point comparisons omitted as mathematically tautological
5. **Effect sizes and power**: Reported for all underpowered comparisons

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
