# Surviving Findings: Kalshi Prediction Market Research

**Date:** 2026-02-20
**Status:** PhD-review corrected with independence corrections. Thirteen experiments completed (1-13). All findings below report both naive and event-level clustered statistics where applicable.

---

## Finding 1: Directional Information Asymmetry in Prediction Markets

**Strength: Moderate-Strong**

Inflation markets Granger-cause monetary policy markets with a 3-hour median lag, significantly faster than the 5-hour reverse direction (Mann-Whitney p=0.0008).

### Evidence

- **379 significant Granger-causal pairs** across 4 economic domains (inflation, monetary policy, labor, macro) after:
  - ADF stationarity testing with automatic differencing
  - Within-pair Bonferroni correction (p x 24 lags)
  - Cross-pair Bonferroni at alpha=0.01
- **Permutation validation** (1,000 domain-label shuffles):
  - Cross-domain pair count: 379 observed vs 265 +/- 12 null. p < 0.001.
  - Inflation-to-monetary-policy asymmetry: 21 excess pairs vs null mean 0 +/- 4.8. p < 0.001.
- **Bidirectional filtering**: 74 pairs (39%) are bidirectional (co-movement, not directional flow). The 231 remaining unidirectional pairs preserve the asymmetry: inflation-to-MP (50) vs MP-to-inflation (29).

### Independence Caveat

The Bonferroni correction treats A→B and B→A as independent tests. In practice, they share the same aligned price data. The effective number of independent pairs is approximately half the reported N directional tests. The Mann-Whitney lag asymmetry test (p=0.0008) treats each pair as independent, but pairs sharing the same leader or follower ticker have correlated lag estimates. The effective N is lower than reported, though the permutation test (which shuffles domain labels) provides a complementary validation that is less sensitive to this concern.

### Indicator-Level Refinement (Experiment 9)

| Leader | Follower | Pairs | Median Lag |
|--------|----------|-------|------------|
| CPI | Fed Funds | 57 | 3h |
| Fed Funds | CPI | 36 | 5h |
| Jobless Claims | CPI | 64 | 6h |
| CPI | Jobless Claims | 42 | 8h |
| GDP | CPI | 100 | 7h |
| CPI | GDP | 80 | 6.5h |

**CPI → Fed Funds asymmetry**: Mann-Whitney p=0.009. CPI (not PCE or PPI) is the dominant market-implied inflation signal for monetary policy.

### Interpretation

Consistent with the Taylor Rule: CPI expectations propagate to Fed rate expectations faster than the reverse. CPI dominates over PCE despite the Fed's stated preference. No trading alpha — Sharpe ratio is negative across all strategies.

---

## Finding 2: Prediction Markets Calibrate Better Under Uncertainty

**Strength: Suggestive** *(downgraded from Strong after cluster-robust bootstrap)*

Markets appear better calibrated during high-uncertainty periods, but the effect does not survive cluster-robust resampling.

### Evidence

| Regime | Brier | Reliability | Resolution | Uncertainty | Base Rate | n |
|--------|-------|-------------|------------|-------------|-----------|---|
| Low | 0.512 | 0.262 | 0.000 | 0.250 | 0.522 | 90 |
| Medium | 0.392 | 0.152 | 0.000 | 0.240 | 0.400 | 85 |
| High | 0.353 | 0.123 | 0.000 | 0.231 | 0.360 | 86 |

### Statistical Tests

| Test | CI Lower | CI Upper | Significant |
|------|----------|----------|-------------|
| Naive bootstrap (Brier diff) | -0.242 | -0.016 | Yes |
| **Cluster-robust bootstrap (Brier diff)** | **-0.251** | **0.017** | **No** |
| Naive bootstrap (reliability diff) | -0.209 | -0.013 | Yes |
| **Cluster-robust bootstrap (reliability diff)** | **-0.226** | **0.013** | **No** |

The cluster-robust bootstrap resamples 80 high-uncertainty and 72 low-uncertainty event clusters (not individual markets), accounting for within-event correlation of market outcomes. Both the Brier and reliability differences become non-significant.

### Interpretation

The direction of the effect is consistent (high-uncertainty periods → better calibration), but with only ~80 independent event clusters per regime, the evidence is suggestive rather than conclusive. The KUI circularity concern (KUI constructed from the same prices used for calibration) remains.

---

## Finding 3: Market Microstructure Responds to Economic Events

**Strength: Suggestive** *(downgraded from Strong after event-level clustering)*

Prediction market bid-ask spreads narrow and price ranges widen after economic announcements at the pair level, but these effects are not significant when properly accounting for within-event correlation.

### Evidence

767 event-market pairs across 31 economic events:

| Test | Spread Change | Spread p | Range Change | Range p |
|------|--------------|----------|--------------|---------|
| Naive (pair-level, n=767) | -0.8% | 0.013* | +14.7% | 0.017* |
| **Event-level (n=31)** | **-2.7%** | **0.542** | **+35.8%** | **0.232** |

When collapsed to event-level means (one observation per event date), neither the spread narrowing nor the range widening is statistically significant. The naive significance was driven by treating correlated within-event observations as independent.

### What Survives

- Spread-KUI correlation: r=0.241 (p<0.001), 462 days — this is at the daily aggregate level and does not suffer from the within-event clustering problem.
- OI-calibration pattern: Higher-OI markets are better calibrated (Brier 0.147-0.157 vs 0.246 for low OI).

---

## Finding 4: Implied Probability Distributions from Multi-Strike Markets

**Strength: Moderate** *(merged with Finding 8 in Experiment 13)*

Kalshi's multi-strike market structure enables Breeden-Litzenberger-style reconstruction of implied probability distributions. See Finding 8 for full distributional evaluation.

### No-Arbitrage Efficiency

| Metric | Value |
|--------|-------|
| Events tested | 41 |
| Total hourly snapshots | 7,166 |
| Violating snapshots | 202 (2.8%) |
| Events with violations | 25/41 |
| Reversion rate | 168/195 = 86% within 1 hour |

---

## Finding 5: TIPS Breakeven Rates Granger-Cause Kalshi CPI Markets

**Strength: Strong**

The bond market's inflation expectations lead Kalshi CPI prediction market prices, not the reverse.

### Evidence

286 overlapping days (Oct 2024 - Jan 2026):

| Test | Direction | Best Lag | F-stat | p-value | Significant |
|------|-----------|----------|--------|---------|-------------|
| Granger | TIPS → Kalshi | 1 day | 12.24 | 0.005 | Yes |
| Granger | Kalshi → TIPS | — | 0.0 | 1.0 | No |

### CPI Horse Race (Experiment 13)

Point forecast comparison (apples-to-apples MAE vs MAE):

| Forecaster | Mean MAE | Median MAE | n |
|-----------|----------|------------|---|
| **Kalshi implied mean** | **0.082** | **0.056** | **14** |
| SPF (annual/12 proxy) | 0.111 | 0.083 | 13 |
| TIPS breakeven (monthly) | 0.112 | 0.107 | 13 |

Kalshi's implied mean outperforms SPF and TIPS-implied forecasts on average, but the difference is not statistically significant (Kalshi vs SPF: p=0.227, Kalshi vs TIPS: p=0.170, n=13). With only 14 CPI events, the comparison is underpowered. Effect sizes favor Kalshi.

**Note on SPF comparison**: SPF forecasts annual CPI (Q4/Q4 %), converted to monthly via annual_rate/12. This is an approximation — SPF does not directly forecast MoM CPI.

### Interpretation

TIPS breakeven rates Granger-cause Kalshi (institutional bonds lead retail prediction markets), but Kalshi's point forecast accuracy is directionally superior to both SPF and TIPS for monthly CPI. The information hierarchy is: bonds set the level, prediction markets refine the monthly estimate.

---

## Finding 6: Cross-Event Shock Propagation

**Strength: Suggestive** *(downgraded from Moderate-Strong after event-level clustering)*

Economic events trigger cross-domain responses in prediction markets, but the surprise sensitivity finding does not survive event-level clustering.

### Evidence

205 markets, 31 events, 9,108 event-hour observations.

**Surprise vs non-surprise (event-level clustered):**

| Domain | Surprise Mean | Non-Surprise Mean | Ratio | Naive p | Clustered p | n_surprise | n_nonsurprise |
|--------|-------------|-------------------|-------|---------|-------------|-----------|--------------|
| inflation | 0.028 | 0.024 | 1.18x | 0.0002* | **0.436** | 12 | 16 |
| monetary_policy | — | — | — | 0.007* | insufficient | 2 | 2 |
| labor | — | — | — | 0.84 | insufficient | 2 | 8 |
| macro | 0.021 | 0.023 | 0.92x | 0.99 | **0.396** | 10 | 14 |

The inflation surprise effect (naive p=0.0002) collapses to p=0.436 when using one observation per (event_date, domain) instead of treating each hourly observation as independent.

**Response ordering (event-level clustered):**

Only CPI origin vs macro cross-domain survives clustering: p=0.006 (n=8 events). Most other comparisons become underpowered.

### What Survives

The descriptive finding that origin domains tend to respond more strongly than cross-domains is directionally consistent but mostly underpowered at event-level granularity.

---

## Finding 7: Favorite-Longshot Bias in Economics Markets

**Strength: Moderate**

Economics-domain prediction markets show a time-to-expiration gradient in calibration quality. The FLB itself is small.

### Evidence

1,141 economics-only settled markets. 288 with T-24h candle prices.

**Calibration by time to expiration:**

| Lifetime | Brier Score | Longshot Bias | n |
|----------|-------------|---------------|---|
| Short (~56h) | 0.156 | +0.033 | 381 |
| Medium (~304h) | 0.059 | +0.014 | 380 |
| Long (~1710h) | 0.023 | -0.003 | 380 |

The 7x calibration gradient (short vs long lifetime) is the most robust pattern. Monetary policy markets achieve Brier=0.007 (near-perfect).

---

## Finding 8: Distributional Calibration via CRPS Scoring

**Strength: Strong (heterogeneous)** *(updated with per-series tests and horse race from Experiment 13)*

Kalshi's implied probability distributions show heterogeneous calibration: Jobless Claims distributions robustly outperform historical benchmarks, while CPI distributions are persistently overconfident.

### Evidence

33 events with CRPS scores (14 CPI, 3 GDP, 16 Jobless Claims).

**CRPS by event series:**

| Series | Kalshi CRPS | Uniform CRPS | Historical CRPS |
|--------|------------|-------------|----------------|
| KXCPI (n=14) | 0.108 | 0.042 | 0.091 |
| KXGDP (n=3) | 0.509 | 0.672 | 1.098 |
| KXJOBLESSCLAIMS (n=16) | 4,840 | 6,100 | 35,556 |

### Statistical Tests: Pooled vs Per-Series

| Test | Scope | p-value | Significant |
|------|-------|---------|-------------|
| Kalshi vs Historical | Pooled (n=33) | 0.0001 | Yes |
| Kalshi vs Uniform | Pooled (n=33) | 0.598 | No |
| KXCPI vs Historical | Per-series (n=14) | **0.709** | **No** |
| KXCPI vs Uniform | Per-series (n=14) | 0.999 | No (worse) |
| KXJOBLESSCLAIMS vs Historical | Per-series (n=16) | **0.0000** | **Yes** |
| KXJOBLESSCLAIMS vs Uniform | Per-series (n=16) | 0.248 | No |
| KXGDP vs Historical | Per-series (n=3) | — | Insufficient data |

**Critical insight**: The pooled Wilcoxon (p=0.0001) is dominated by Jobless Claims' massive improvement over historical. Per-series tests reveal that CPI distributions are NOT better than historical (p=0.709) — they are actually overconfident. The "Kalshi beats historical" headline finding is a Jobless Claims story, not a universal prediction market story.

### Mathematical Note on CRPS vs MAE

CRPS ≤ MAE is a mathematical identity for any proper distribution derived from the same information set. Finding that Kalshi distributional CRPS < point MAE (pooled p=0.0031) is expected by construction and does NOT demonstrate superior forecasting accuracy. The honest comparison is point-vs-point (Finding 5 horse race) or distribution-vs-distribution (Kalshi CDF vs historical CDF).

### Temporal CRPS Evolution

| Lifetime % | CPI | GDP | Jobless Claims |
|-----------|-----|-----|----------------|
| 10% (early) | 1.96x | 1.33x | 0.91x |
| 25% | 2.82x | 0.93x | 0.54x |
| 50% (mid) | 2.55x | 0.76x | 0.79x |
| 75% | 1.64x | 0.72x | 0.80x |
| 90% (late) | 1.16x | 0.86x | 0.78x |

CPI markets learn over time (converging from 1.96x to 1.16x vs uniform) but never overcome overconfidence. Jobless Claims beat uniform from inception.

### Interpretation

This is the first proper scoring rule evaluation of prediction market implied distributions. The heterogeneity is the finding: Jobless Claims (weekly frequency, high liquidity) achieve well-calibrated distributional forecasts that massively beat historical baselines. CPI markets (monthly frequency, herding around consensus) suffer persistent overconfidence. The temporal convergence pattern suggests distributional calibration is an emergent property of trading frequency and market maturation.

---

## Suggestive Finding: Hourly Information Speed

**Strength: Suggestive (underpowered)**

Kalshi appears to react to surprise events ~56h before EPU, but n=5 is too small. Wilcoxon p=0.10.

---

## Invalidated Findings

These findings were initially reported as significant but were invalidated during methodology review:

| Finding | Original | Corrected | Reason |
|---------|----------|-----------|--------|
| Shock acceleration | 4h vs 8h, p<0.001 | 6h vs 8h, p=0.48 | Circular classification artifact |
| KUI leads EPU (Granger) | p=0.024 | p=0.658 | Absolute return bias; fixed with percentage returns |
| Trading Sharpe | +5.23 (4 trades) | -2.26 (23 trades) | Small-sample artifact |
| **Microstructure event response** | **p=0.013 (spread)** | **p=0.542** | **Within-event correlation; 767 pairs from 31 events** |
| **Surprise shock sensitivity** | **p=0.0002 (inflation)** | **p=0.436** | **Within-event correlation; hourly obs from 31 events** |
| **Calibration under uncertainty** | **CI: [-0.242, -0.016]** | **CI: [-0.251, 0.017]** | **Within-event correlation in bootstrap** |

---

## Methodology

### Data
- 6,141 settled Kalshi markets with outcomes (Oct 2024 - Feb 2026)
- 7,695 markets with text embeddings (experiment 5)
- 1,028 economics-relevant, 289 with hourly candle data
- 725 hourly candle files with full OHLC, bid-ask, open interest, and volume
- 336 multi-strike markets across 41 events (CPI, GDP, Jobless Claims)
- 4 domains: inflation (CPI), monetary policy (Fed Funds), labor (Jobless Claims), macro (GDP)
- External benchmarks: EPU (Baker-Bloom-Davis), VIX, S&P 500, TIPS breakeven (T10YIE, T5YIE), SPF median CPI

### Key Corrections Applied
1. **ADF stationarity**: 43% of raw-level Granger results were spurious without differencing
2. **Within-pair Bonferroni**: testing 24 lags and selecting best inflates p-values; corrected by p x max_lag
3. **Shock-fraction classification**: replaced binary market-lifetime overlap with continuous shock-fraction measure
4. **Murphy decomposition**: Brier = reliability - resolution + uncertainty. Isolates true calibration from base rate effects
5. **Permutation test**: 1,000 domain-label shuffles establish null distribution for cross-domain structure
6. **Bidirectional pair flagging**: 39% of pairs show A-to-B and B-to-A, indicating co-movement not causation
7. **F-stat overflow guards**: reject F > 10^6 and near-zero RSS (numerical artifacts)
8. **Event-level clustering** (NEW): Experiments 3, 6, 10 now report both naive (pair/market-level) and event-level clustered statistics. Three previously "significant" findings became non-significant after clustering.
9. **Per-series Wilcoxon** (NEW): Experiment 13 tests each event series separately rather than pooling across scales. The pooled p=0.0001 was driven by Jobless Claims; CPI is not significant per-series.
10. **CRPS ≤ MAE note** (NEW): The CRPS-vs-point-forecast comparison is acknowledged as partially tautological (mathematical property, not empirical finding).

### Experiments Summary

| # | Name | Key Finding | API Calls |
|---|------|-------------|-----------|
| 1 | Causal Lead-Lag | Inflation → monetary policy at 3h | Kalshi, Grok |
| 2 | KUI Construction | Uncertainty index (474 days) | Kalshi, FRED |
| 3 | Calibration Under Uncertainty | Suggestive (cluster-robust CI includes zero) | None |
| 4 | Hourly Information Speed | ~56h lead vs EPU (underpowered) | None |
| 5 | Embeddings & Clustering | k-NN beats random by 15.7% | Kalshi |
| 6 | Market Microstructure | Spread narrows after events (naive p=0.013, **clustered p=0.542**) | None |
| 7 | Implied Distributions | CPI 0.05pp median error, 2.8% arb violations | None |
| 8 | TIPS Comparison | TIPS leads Kalshi by 1 day (p=0.005) | FRED |
| 9 | Indicator Network | CPI → Fed at 3h, p=0.009 | None |
| 10 | Shock Propagation | Origin responds strongest (naive p<0.05, **clustered mostly underpowered**) | None |
| 11 | Favorite-Longshot Bias | Time-to-expiration predicts calibration (7x) | None |
| 12 | CRPS Distributional Scoring | Jobless Claims beats historical (**per-series p=0.0000**), CPI overconfident | FRED |
| 13 | Unified Calibration + Horse Race | Per-series CRPS, CPI horse race (Kalshi MAE 0.082 vs SPF 0.111) | FRED |
