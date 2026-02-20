# Kalshi Prediction Market Research: Surviving Findings

**Date:** 2026-02-20
**Status:** Post PhD-review with independence corrections (iteration 2). Five findings survive rigorous testing across thirteen experiments.

**Narrative arc**: Kalshi prediction markets encode genuine economic information structure (Finding 1), enabling extraction of implied probability distributions (Finding 2) whose calibration quality depends on market maturity (Finding 3) and event series (Finding 5). The bond market sets the level while prediction markets refine monthly estimates (Finding 4).

---

## Finding 1: Directional Information Asymmetry in Prediction Markets

**Strength: Moderate-Strong**

Inflation markets Granger-cause monetary policy markets with a 3-hour median lag, significantly faster than the 5-hour reverse direction (Mann-Whitney p=0.0008).

### Evidence

- **379 significant Granger-causal pairs** across 4 economic domains after ADF stationarity testing, within-pair Bonferroni (p x 24 lags), and cross-pair Bonferroni at alpha=0.01.
- **231 unidirectional pairs** after removing 74 bidirectional co-movement pairs (39%).
- **Permutation validation** (1,000 domain-label shuffles): cross-domain pair count 379 vs 265 +/- 12 null (p<0.001); inflation-to-MP asymmetry 21 excess pairs vs null mean 0 +/- 4.8 (p<0.001).

### Indicator-Level Refinement (Experiment 9)

| Leader | Follower | Pairs | Median Lag |
|--------|----------|-------|------------|
| CPI | Fed Funds | 57 | 3h |
| Fed Funds | CPI | 36 | 5h |

CPI → Fed Funds asymmetry: Mann-Whitney p=0.009. CPI (not PCE or PPI) is the dominant market-implied inflation signal.

### Caveats

The Bonferroni correction treats A→B and B→A as independent tests; effective N is approximately half the reported directional tests. The permutation test (shuffling domain labels) provides complementary validation less sensitive to this concern. No trading alpha — Sharpe ratio is negative across all strategies.

### Interpretation

Consistent with the Taylor Rule: CPI expectations propagate to Fed rate expectations faster than the reverse.

---

## Finding 2: Implied Probability Distributions from Multi-Strike Markets

**Strength: Moderate**

Kalshi's multi-strike market structure enables Breeden-Litzenberger-style reconstruction of implied probability distributions with strong no-arbitrage efficiency.

### Evidence

336 multi-strike markets across 41 events (CPI, GDP, Jobless Claims).

| Metric | Value |
|--------|-------|
| Total hourly CDF snapshots | 7,166 |
| Violating snapshots | 202 (2.8%) |
| Reversion rate | 168/195 = 86% within 1 hour |
| CPI median forecast error | 0.05 percentage points |

2.8% of CDF snapshots violate monotonicity, with 86% reverting within one hour — consistent with transient arbitrage in thin markets, not systematic mispricing.

---

## Finding 3: Calibration Depends on Market Maturity (Time-to-Expiration)

**Strength: Moderate**

Economics-domain prediction markets show a 7x calibration gradient driven by time to expiration, the dominant predictor of forecast quality.

### Evidence

1,141 economics-only settled markets. 288 with T-24h candle prices.

| Lifetime | Brier Score | Longshot Bias | n |
|----------|-------------|---------------|---|
| Short (~56h) | 0.156 | +0.033 | 381 |
| Medium (~304h) | 0.059 | +0.014 | 380 |
| Long (~1710h) | 0.023 | -0.003 | 380 |

The traditional favorite-longshot bias is small (+0.033 at worst). The dominant pattern is the maturity gradient: longer-lived markets achieve dramatically better calibration (Brier 0.023 vs 0.156). Monetary policy markets achieve Brier=0.007 (near-perfect). Extends Whelan (CEPR 2024).

---

## Finding 4: TIPS Breakeven Rates Lead Kalshi; Kalshi Refines Monthly Estimates

**Strength: Strong**

The bond market's inflation expectations lead Kalshi CPI prediction market prices, but Kalshi's implied mean is directionally more accurate for monthly CPI.

### TIPS Granger Causality

286 overlapping days (Oct 2024 - Jan 2026):

| Direction | Best Lag | F-stat | p-value |
|-----------|----------|--------|---------|
| TIPS → Kalshi | 1 day | 12.24 | 0.005 |
| Kalshi → TIPS | — | 0.0 | 1.0 |

### CPI Horse Race (Experiment 13)

Point forecast comparison (apples-to-apples MAE):

| Forecaster | Mean MAE | Median MAE | Cohen's d | p-value | n |
|-----------|----------|------------|-----------|---------|---|
| **Kalshi implied mean** | **0.082** | **0.056** | — | — | **14** |
| SPF (annual/12 proxy) | 0.110 | 0.092 | -0.25 | 0.211 | 14 |
| TIPS breakeven (monthly) | 0.112 | 0.107 | -0.27 | 0.163 | 14 |
| Trailing mean | 0.118 | 0.066 | -0.32 | 0.155 | 14 |
| Random walk (last month) | 0.143 | 0.100 | **-0.60** | **0.026*** | 14 |

Kalshi significantly beats the random walk naive benchmark (p=0.026, d=-0.60). Against professional forecasters (SPF, TIPS), effect sizes are small-to-medium (d=-0.25 to -0.32) but the comparison is underpowered at n=14.

**SPF caveat**: SPF forecasts annual CPI (Q4/Q4 %), converted to monthly via annual_rate/12 — an approximation.

### Interpretation

TIPS breakeven rates Granger-cause Kalshi (institutional bonds lead retail prediction markets), but Kalshi's point forecast accuracy is significantly better than naive benchmarks and directionally superior to professional forecasters for monthly CPI. The information hierarchy: bonds set the level, prediction markets refine the monthly estimate.

---

## Finding 5: Heterogeneous Distributional Calibration (CRPS Scoring)

**Strength: Strong (heterogeneous)**

Kalshi's implied probability distributions show heterogeneous calibration: Jobless Claims distributions robustly outperform historical benchmarks, while CPI distributions are persistently overconfident. This is the first proper scoring rule evaluation of prediction market implied distributions.

### CRPS by Event Series

33 events (14 CPI, 3 GDP, 16 Jobless Claims):

| Series | Kalshi CRPS | Uniform CRPS | Historical CRPS |
|--------|------------|-------------|----------------|
| KXCPI (n=14) | 0.108 | 0.042 | 0.091 |
| KXGDP (n=3) | 0.509 | 0.672 | 1.098 |
| KXJOBLESSCLAIMS (n=16) | 4,840 | 6,100 | 35,556 |

### Per-Series Wilcoxon Tests

| Test | p-value | Significant |
|------|---------|-------------|
| KXJOBLESSCLAIMS vs Historical (n=16) | **0.0000** | **Yes** |
| KXCPI vs Historical (n=14) | 0.709 | No |
| KXCPI vs Uniform (n=14) | 0.999 | No (worse) |
| KXGDP vs Historical (n=3) | — | Insufficient |
| Pooled Kalshi vs Historical (n=33) | 0.0001 | Yes* |

*The pooled result is dominated by Jobless Claims. Per-series tests are the honest metric.

### Temporal CRPS Evolution

| Lifetime % | CPI (vs uniform) | Jobless Claims (vs uniform) |
|-----------|-------------------|----------------------------|
| 10% (early) | 1.96x (worse) | 0.91x (better) |
| 50% (mid) | 2.55x (worse) | 0.79x (better) |
| 90% (late) | 1.16x (converging) | 0.78x (stable) |

CPI markets learn over time (converging from 1.96x to 1.16x vs uniform) but never overcome overconfidence. Jobless Claims beat uniform from inception.

### CPI Overconfidence Diagnostic (PIT Analysis)

Probability Integral Transform (PIT) analysis reveals the nature of CPI overconfidence:

| Metric | CPI (n=14) | Well-Calibrated |
|--------|-----------|-----------------|
| Mean PIT | 0.391 | 0.500 |
| Std PIT | 0.222 | 0.289 |
| % in IQR | 57% | 50% |
| % in tails | 7% | 20% |

The market is biased toward higher CPI: realized values consistently fall in the lower half of the implied distribution (mean PIT = 0.39). The distribution is also too wide (low tail density, compressed std). This is consistent with consensus herding around a high-CPI narrative during 2024-2025.

### Power Analysis

| Comparison | |d| | n now | n needed (80% power) |
|-----------|-----|-------|----------------------|
| vs Random Walk | 0.60 | 14 | 18 (+4 months) |
| vs Trailing Mean | 0.32 | 14 | 66 (+52 months) |
| vs SPF | 0.25 | 14 | 107 (+93 months) |
| vs TIPS | 0.27 | 14 | 90 (+76 months) |

The random walk comparison is near-powered (4 more months). Detecting differences vs professional forecasters requires years of data — a fundamental constraint of monthly CPI releases.

### Mathematical Note

CRPS <= MAE is a mathematical identity for any proper distribution. This analysis compares distribution-vs-distribution (Kalshi CDF vs historical CDF) for honest evaluation.

### Interpretation

The heterogeneity is the finding: Jobless Claims (weekly frequency, high liquidity) achieve well-calibrated distributional forecasts that massively beat historical baselines. CPI markets (monthly frequency, consensus herding) are biased toward overestimating inflation. The PIT analysis suggests this is directional bias (high-CPI narrative), not excess uncertainty. Distributional calibration is an emergent property of trading frequency and information diversity.

---

## Downgraded Findings (Suggestive Only)

These findings show directionally consistent effects but do not survive rigorous statistical testing:

| Finding | Direction | Naive p | Corrected p | Issue |
|---------|-----------|---------|-------------|-------|
| Calibration under uncertainty | High-uncertainty → better calibration | 0.016* | CI includes zero | Cluster-robust bootstrap (80 event clusters) |
| Microstructure event response | Spread narrows after events | 0.013* | 0.542 | 767 pairs from 31 events |
| Shock propagation (surprise) | Surprise → larger inflation response | 0.0002* | 0.436 | Hourly obs from 31 events |
| Hourly information speed | Kalshi reacts ~56h before EPU | 0.10 | 0.10 | n=5 events |

---

## Invalidated Findings

| Finding | Original | Corrected | Reason |
|---------|----------|-----------|--------|
| Shock acceleration | 4h vs 8h, p<0.001 | 6h vs 8h, p=0.48 | Circular classification artifact |
| KUI leads EPU (Granger) | p=0.024 | p=0.658 | Absolute return bias; fixed with percentage returns |
| Trading Sharpe | +5.23 (4 trades) | -2.26 (23 trades) | Small-sample artifact |

---

## Methodology

### Data
- 6,141 settled Kalshi markets with outcomes (Oct 2024 - Feb 2026)
- 1,028 economics-relevant, 289 with hourly candle data, 725 hourly candle files
- 336 multi-strike markets across 41 events (CPI, GDP, Jobless Claims)
- External benchmarks: TIPS breakeven (T10YIE), SPF median CPI, FRED historical data

### Key Corrections Applied
1. **ADF stationarity**: 43% of raw-level Granger results were spurious without differencing
2. **Within-pair Bonferroni**: corrected by p x max_lag for 24-lag selection
3. **Murphy decomposition**: Brier = reliability - resolution + uncertainty, isolating true calibration
4. **Permutation test**: 1,000 domain-label shuffles establish null distribution
5. **Bidirectional pair flagging**: 39% of pairs show co-movement, not directional causation
6. **Event-level clustering**: Experiments 3, 6, 10 report both naive and clustered statistics; three findings became non-significant
7. **Per-series Wilcoxon**: Each event series tested separately; pooled p=0.0001 was a Jobless Claims story
8. **CRPS <= MAE note**: Distribution-vs-point comparison acknowledged as partially tautological

### Experiments Summary

| # | Name | Status | Key Result |
|---|------|--------|------------|
| 1 | Causal Lead-Lag | **Finding 1** | Inflation → monetary policy at 3h |
| 2 | KUI Construction | Supporting | Uncertainty index (474 days) |
| 3 | Calibration Under Uncertainty | Downgraded | Cluster-robust CI includes zero |
| 4 | Hourly Information Speed | Downgraded | Underpowered (n=5) |
| 5 | Embeddings & Clustering | Supporting | k-NN beats random by 15.7% |
| 6 | Market Microstructure | Downgraded | Clustered p=0.542 |
| 7 | Implied Distributions | **Finding 2** | 2.8% arb violations, 86% revert |
| 8 | TIPS Comparison | **Finding 4** | TIPS leads Kalshi by 1 day |
| 9 | Indicator Network | **Finding 1** | CPI → Fed at 3h |
| 10 | Shock Propagation | Downgraded | Clustered p=0.436 |
| 11 | Favorite-Longshot Bias | **Finding 3** | Time-to-expiration 7x gradient |
| 12 | CRPS Distributional Scoring | **Finding 5** | Jobless Claims p=0.0000 |
| 13 | Unified Calibration + Horse Race | **Findings 4-5** | Per-series CRPS, horse race |
