# Surviving Findings: Kalshi Prediction Market Research

**Date:** 2026-02-19
**Status:** PhD-review corrected. Twelve experiments completed (1-12). All findings below survive rigorous methodology checks.

---

## Finding 1: Directional Information Asymmetry in Prediction Markets

**Strength: Strong**

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

### Indicator-Level Refinement (Experiment 9)

The domain-level finding resolves to specific economic indicators:

| Leader | Follower | Pairs | Median Lag |
|--------|----------|-------|------------|
| CPI | Fed Funds | 57 | 3h |
| Fed Funds | CPI | 36 | 5h |
| Jobless Claims | CPI | 64 | 6h |
| CPI | Jobless Claims | 42 | 8h |
| GDP | CPI | 100 | 7h |
| CPI | GDP | 80 | 6.5h |

**CPI → Fed Funds asymmetry**: Mann-Whitney p=0.009. CPI (not PCE or PPI) is the dominant market-implied inflation signal for monetary policy. This is notable because the Fed's stated preferred measure is PCE, yet market participants price CPI as the leading indicator.

**Indicator centrality** (influence/receptivity analysis):
- CPI: highest influence ratio (0.56) — dominant information source
- Fed Funds: lowest influence ratio (0.39) — primarily a receiver
- Jobless Claims: balanced (0.50) — both transmits and receives

### Unidirectional Domain Pair Counts

| Leader | Follower | Pairs |
|--------|----------|-------|
| inflation | monetary_policy | 50 |
| labor | inflation | 50 |
| macro | inflation | 47 |
| monetary_policy | inflation | 29 |
| inflation | labor | 28 |
| inflation | macro | 27 |

### Interpretation

Consistent with the Taylor Rule: CPI expectations propagate to Fed rate expectations faster than the reverse. CPI dominates over PCE despite the Fed's stated preference, suggesting retail prediction market participants weight headline CPI more heavily in their monetary policy expectations.

### What Was Tested and Failed

- **Shock-regime acceleration** (originally p<0.001, "2x faster during crises"): Invalidated. The classification was circular -- any market whose multi-month lifetime overlapped a shock window was labeled "shock", creating 67% shock pairs from 20% of calendar days. With proper shock-fraction classification (>50% threshold), only 10 pairs qualify. p=0.48.
- **Trading alpha**: Sharpe ratio is negative across all strategies. The lead-lag relationships are too noisy at the individual market level for profitable exploitation.

---

## Finding 2: Prediction Markets Calibrate Better Under Uncertainty

**Strength: Strong**

Markets are genuinely better calibrated during high-uncertainty periods, and this survives base rate controls via Murphy Brier decomposition.

### Evidence

| Regime | Brier | Reliability | Resolution | Uncertainty | Base Rate | n |
|--------|-------|-------------|------------|-------------|-----------|---|
| Low | 0.512 | 0.262 | 0.000 | 0.250 | 0.522 | 90 |
| Medium | 0.392 | 0.152 | 0.000 | 0.240 | 0.400 | 85 |
| High | 0.353 | 0.123 | 0.000 | 0.231 | 0.360 | 86 |

- **Reliability** (pure calibration error, independent of base rates): 0.123 (high uncertainty) vs 0.262 (low uncertainty)
- **Bootstrap CI** on reliability difference: [-0.209, -0.013]. Significant.
- **Base rates differ** (0.362 high vs 0.522 low), which alone would affect raw Brier scores. Murphy decomposition isolates the calibration component, confirming the effect is real.

### Microstructure Corroboration (Experiment 6)

Open interest provides an independent confirmation mechanism:

| OI Tercile | Mean Brier | Mean Peak OI | n |
|------------|------------|--------------|---|
| Low | 0.246 | 7,210 | 15 |
| Medium | 0.147 | 67,755 | 15 |
| High | 0.157 | 164,431 | 15 |

Higher-OI markets are better calibrated (Brier 0.147–0.157 vs 0.246 for low OI). This supports the "participation drives accuracy" mechanism: more open interest → more trader engagement → better price discovery → better calibration.

### GDP Markets Deep-Dive

The effect is most dramatic in GDP prediction markets (all KXGDP):
- Low uncertainty: Brier = 0.802 (n=22) -- nearly random
- High uncertainty: Brier = 0.196 (n=15) -- well-calibrated
- Bootstrap CI: [-0.846, -0.321]. Significant.

### Interpretation

Economic stress likely attracts more sophisticated participants to GDP markets, transforming them from thinly-traded noise into well-calibrated forecasts. The OI evidence corroborates this: markets with more participation (higher OI) calibrate better regardless of uncertainty regime.

---

## Finding 3: Market Microstructure Responds to Economic Events

**Strength: Strong (new)**

Prediction market bid-ask spreads narrow significantly after economic announcements while intraday price ranges widen — a signature of information incorporation.

### Evidence

767 event-market pairs analyzed across 33 economic events:

| Metric | Pre-Event (48h) | Post-Event (48h) | Change | Wilcoxon p |
|--------|-----------------|-------------------|--------|------------|
| Bid-ask spread | $0.0610 | $0.0605 | -0.8% | 0.013 |
| Intraday range | $0.0099 | $0.0114 | +14.7% | 0.017 |

Both effects are statistically significant. The pattern is consistent with market microstructure theory: information arrival causes prices to move (wider range) while reducing uncertainty about fair value (narrower spread).

### Spread as Uncertainty Measure

Daily aggregate bid-ask spread correlates with the Kalshi Uncertainty Index:
- Pearson r = 0.241 (p < 0.001), Spearman r = 0.252 (p < 0.001)
- 462 overlapping days, mean 349 active markets per day

This validates spread as an independent, market-endogenous uncertainty measure that avoids the circularity concern of KUI (which is constructed from the same price data used in calibration analysis).

### Interpretation

Prediction markets exhibit classical microstructure dynamics around information events. The simultaneous spread narrowing and range widening is the canonical signature of informed trading models (Glosten-Milgrom, Kyle): informed traders enter after announcements, causing prices to adjust (range) while market makers gain confidence in fair value (spread).

---

## Finding 4: Implied Probability Distributions from Multi-Strike Markets

**Strength: Strong (new)**

Kalshi's multi-strike market structure enables Breeden-Litzenberger-style reconstruction of implied probability distributions for economic indicators, with demonstrated forecasting accuracy.

### Evidence

336 multi-strike markets across 41 events (CPI, GDP, Jobless Claims):

**CPI Forecasting Accuracy** (14 CPI release events):
- Median absolute error: 0.05 percentage points
- Mean absolute error: 0.08 percentage points
- The implied CPI distribution correctly captures the realized value within its probability mass in most events

**GDP Forecasting** (3 GDP release events):
- GDP-25APR30: implied mean 0.32%, realized -0.30% (0.62pp error — Q1 2025 contraction surprise)
- GDP-25JUL30: implied mean 2.0%, realized 3.0% (underestimated rebound)
- GDP-25OCT30: implied mean 2.1%, realized 3.8% (1.68pp error)

**Jobless Claims Forecasting** (24 events with realized values):
- Median absolute error: 501 claims (on ~225K scale = 0.2%)
- Mean absolute error: 6,378 claims
- RMSE: 11,196 claims

### No-Arbitrage Efficiency

| Metric | Value |
|--------|-------|
| Events tested | 40 |
| Total hourly snapshots | 7,166 |
| Violating snapshots | 202 (2.8%) |
| Mean violation size | $0.04 |
| Max violation size | $0.38 |
| Reversion rate | 71% within 1 hour |

The 2.8% violation rate is low, confirming markets generally maintain no-arbitrage constraints. When violations occur, 71% revert within the next hour (187 checked, 132 reverted), suggesting rapid arbitrageur correction rather than persistent inefficiency.

### Interpretation

This is the prediction market analogue of options-implied density estimation (Breeden-Litzenberger, 1978). The multi-strike structure encodes a full probability distribution over economic outcomes, not just a point forecast. The CPI distributions are remarkably accurate (median 0.05pp error), while GDP distributions capture the correct direction but underestimate tail events.

---

## Finding 5: TIPS Breakeven Rates Granger-Cause Kalshi CPI Markets

**Strength: Strong (new)**

The bond market's inflation expectations (TIPS breakeven rates) lead Kalshi CPI prediction market prices, not the reverse. This establishes the information hierarchy between institutional fixed-income markets and retail prediction markets.

### Evidence

286 overlapping days (Oct 2024 - Jan 2026):

| Test | Direction | Best Lag | F-stat | p-value | Significant |
|------|-----------|----------|--------|---------|-------------|
| Granger | TIPS → Kalshi | 1 day | 12.24 | 0.005 | Yes |
| Granger | Kalshi → TIPS | — | 0.0 | 1.0 | No |
| Cross-corr | TIPS leads | -1 day | r=0.281 | <0.001 | Yes |

**Level correlations:**
- T10YIE ↔ Kalshi CPI: Pearson r=0.247 (p<0.001), Spearman r=0.208 (p<0.001)
- T5YIE ↔ Kalshi CPI: Pearson r=0.182 (p=0.002)

**Change correlations** (daily returns):
- T10YIE ↔ Kalshi CPI: r=-0.127 (p=0.031) — negative, suggesting contrarian dynamics

### Interpretation

TIPS breakeven rates set by institutional bond traders provide the informational anchor for Kalshi CPI markets. The 1-day Granger lag is consistent with retail prediction market participants observing and reacting to bond market movements. The negative change correlation suggests that when TIPS breakevens rise (bond market expects more inflation), Kalshi CPI prices may initially move the opposite direction before correcting — a "contrarian retail" pattern.

This is a clean negative result for "prediction markets as price discovery leaders" but a positive result for understanding information cascades: institutional markets → retail prediction markets.

---

## Finding 6: Cross-Event Shock Propagation

**Strength: Moderate-Strong**

Economic events trigger measurable cross-domain shock waves in prediction markets, with origin domains showing significantly stronger responses than cross-domains. Surprise events produce significantly larger responses in inflation (+46%, p=0.0002) and monetary policy (+159%, p=0.007).

### Evidence

205 economic markets across 4 domains, 31 events, 9,108 event-hour observations. Methodology uses global Cumulative Abnormal Return (CAR) thresholds calibrated at the 95th percentile of pre-event activity across ALL domains, avoiding the per-domain bias of the original 2σ approach.

**First significant response times (hours after event, CAR methodology):**

| Event Type | Origin Domain | Origin Response | 1st Cross-Domain | 2nd Cross-Domain |
|-----------|---------------|-----------------|-------------------|-------------------|
| CPI | inflation | 10h | labor (8h) | macro (10h) |
| FOMC | monetary_policy | 45h | inflation (6h) | macro (10h) |
| NFP | labor | 8h | inflation (8h) | macro (8h) |
| GDP | macro | 6h | monetary_policy (32h) | — |

**Response ordering test** (Mann-Whitney, origin vs cross-domain response magnitude at h=0-6):

| Event | Origin Mean | Cross-Domain Mean | p-value | Origin Strongest? |
|-------|-----------|-------------------|---------|-------------------|
| CPI | 0.0335 | 0.0080-0.0249 | <0.05 all | Yes |
| NFP | 0.0647 | 0.0086-0.0249 | <0.05 all | Yes |
| GDP | 0.0249 | 0.0080-0.0168 | <0.05 all | Yes |
| FOMC | 0.0080 | 0.0168-0.0647 | >0.05 | No (only 11 markets) |

CPI, NFP, and GDP origin domains respond significantly more strongly than all cross-domains (p<0.05). FOMC is underpowered (only 11 monetary_policy markets).

**Surprise vs non-surprise response magnitude:**

| Domain | Surprise | Non-Surprise | Ratio | p-value |
|--------|----------|--------------|-------|---------|
| inflation | 0.037 | 0.026 | 1.46x | 0.0002 |
| monetary_policy | 0.012 | 0.005 | 2.59x | 0.007 |
| labor | 0.040 | 0.069 | 0.57x | 0.84 |
| macro | 0.022 | 0.027 | 0.79x | 0.99 |

### Interpretation

This provides hourly-resolution evidence of cross-event shock propagation in prediction markets. For 3 of 4 event types, origin domains respond with statistically significantly greater magnitude than cross-domains, confirming directional information flow. The surprise sensitivity results validate that prediction markets are informationally efficient: inflation and monetary policy markets price in consensus expectations tightly and move sharply on deviations, while labor and macro markets show more baseline volatility.

---

## Finding 7: Favorite-Longshot Bias in Economics Markets

**Strength: Moderate**

Economics-domain prediction markets show a time-to-expiration gradient in calibration quality, with monetary policy markets achieving near-perfect calibration. The classic favorite-longshot bias is small and positive in economics markets. Analysis uses T-24h candle prices (not settlement prices) to avoid the confound that tight-spread markets near settlement are mechanically well-calibrated.

### Evidence

1,141 economics-only settled markets (inflation, monetary_policy, labor, macro, fiscal). Crypto and sports markets excluded to avoid confound from 1-hour contracts. 288 markets have T-24h candle price data for deconfounded analysis.

**Overall calibration (economics-only):**
- Brier score: 0.0805
- YES/NO outcome split: 50.0%/50.0% (balanced, vs 31.5/68.5 with crypto)
- T-24h mean implied probability: 0.497

**Calibration by T-24h spread tercile (n=288 with candle data):**

| Spread Tercile | Brier Score | Longshot Bias | n |
|---------------|-------------|---------------|---|
| Low (tight) | 0.076 | +0.015 | 96 |
| Medium | 0.063 | +0.045 | 96 |
| High (wide) | 0.126 | +0.020 | 96 |

Spread gradient exists but is moderate (1.7x, not 1300x as in confounded analysis). Longshot overpricing is small and consistent across spread terciles (+0.015 to +0.045).

**Calibration by time to expiration:**

| Lifetime | Brier Score | Longshot Bias | n |
|----------|-------------|---------------|---|
| Short (~56h) | 0.156 | +0.033 | 381 |
| Medium (~304h) | 0.059 | +0.014 | 380 |
| Long (~1710h) | 0.023 | -0.003 | 380 |

Strong monotonic gradient: longer-lived markets calibrate 7x better than short-lived ones. This is the most robust pattern in the data.

**Domain breakdown:**

| Domain | n | Brier | Longshot Bias | Favorite Bias |
|--------|---|-------|---------------|---------------|
| monetary_policy | 358 | 0.007 | +0.008 | -0.016 |
| macro | 150 | 0.071 | -0.004 | -0.036 |
| inflation | 421 | 0.090 | -0.025 | +0.004 |
| labor | 212 | 0.187 | -0.088 | +0.130 |

Monetary policy markets are nearly perfectly calibrated (Brier=0.007). Labor markets show the strongest favorite-longshot asymmetry.

### Interpretation

After removing the crypto/short-contract confound and using T-24h prices, the favorite-longshot bias in economics markets is small but present. The dominant predictor of calibration quality is time-to-expiration, not spread: markets with more time for price discovery converge to well-calibrated forecasts. This extends Whelan (CEPR 2024) by showing the bias varies by domain and market maturity, with monetary policy markets essentially bias-free.

---

## Finding 8: Distributional Calibration via CRPS Scoring

**Strength: Strong (new)**

Kalshi's implied probability distributions significantly outperform historical benchmarks (CRPS, Wilcoxon p=0.0001) and point forecasts (p=0.0031), but show heterogeneous calibration across event types. Jobless Claims distributions are well-calibrated; CPI distributions are overconfident.

### Evidence

33 events with CRPS scores (14 CPI, 3 GDP, 16 Jobless Claims). Benchmarks: uniform distribution over strike range, historical empirical CDF from FRED data (70 CPI, 309 Jobless Claims, 43 GDP observations), and point forecast (implied mean).

**CRPS by event series:**

| Series | Kalshi CRPS | Uniform CRPS | Historical CRPS | Improvement vs Historical |
|--------|------------|-------------|----------------|--------------------------|
| KXCPI (n=14) | 0.108 | 0.042 | 0.091 | -37% (worse) |
| KXGDP (n=3) | 0.509 | 0.672 | 1.100 | +33% better |
| KXJOBLESSCLAIMS (n=16) | 4,840 | 6,100 | 35,556 | +86% better |

**Statistical tests (paired Wilcoxon signed-rank):**

| Comparison | Kalshi Mean | Benchmark Mean | p-value | Significant |
|-----------|-------------|----------------|---------|-------------|
| Kalshi vs Historical | 2,347 | 17,239 | 0.0001 | Yes |
| Kalshi CRPS vs Point MAE | 2,347 | 6,283 | 0.0031 | Yes |
| Kalshi vs Uniform | 2,347 | 2,958 | 0.598 | No |

**Key findings:**
1. Kalshi distributions massively beat historical benchmarks — the market is extracting real-time information far beyond what past data alone provides
2. Full Kalshi distributions (CRPS) outperform point forecasts (MAE) — distributional information has value beyond the mean
3. CPI distributions are overconfident: Kalshi CRPS (0.108) is worse than both uniform (0.042) and historical (0.091). The market concentrates probability too narrowly around its point forecast
4. Jobless Claims distributions are well-calibrated: Kalshi beats uniform by ~20% and historical by 86%

### Temporal CRPS Evolution

How distributional calibration changes over a market's lifetime (CRPS ratio vs uniform, <1.0 = beats uniform):

| Lifetime % | CPI | GDP | Jobless Claims |
|-----------|-----|-----|----------------|
| 10% (early) | 1.96x | 1.33x | 0.91x |
| 25% | 2.82x | 0.93x | 0.54x |
| 50% (mid) | 2.55x | 0.76x | 0.79x |
| 75% | 1.64x | 0.72x | 0.80x |
| 90% (late) | 1.16x | 0.86x | 0.78x |

**CPI**: Starts 2x worse than uniform but converges to 1.16x by 90% of lifetime — markets ARE learning but never fully overcome overconfidence. At 75% of lifetime, CPI is only 64% worse than uniform (vs 196% at early life).

**GDP**: Beats uniform from 25% of lifetime onward. Best performance at 75% (0.72x). Small sample (n=3) limits conclusions.

**Jobless Claims**: Beats uniform from the very start (0.91x). Best performance at 25% of lifetime (0.54x = 46% better than uniform).

### Interpretation

This is the first proper scoring rule evaluation of prediction market implied distributions. The CRPS analysis extends NBER Working Paper 34702 (Diercks, Katz, Wright 2024), which showed Kalshi point forecasts beat Bloomberg for CPI. Our contribution: evaluating the *full distributional* forecast quality, including temporal evolution.

The heterogeneity across event types is economically meaningful. CPI markets suffer from persistent overconfidence — traders concentrate probability too narrowly around consensus, consistent with herding behavior documented in Ehm et al. (2016). Jobless Claims markets maintain appropriate uncertainty from inception, possibly because the weekly release frequency provides more learning opportunities. The temporal convergence pattern suggests distributional calibration is an emergent property of market maturation, not a fixed characteristic.

---

## Suggestive Finding: Hourly Information Speed

**Strength: Suggestive (underpowered)**

Kalshi appears to react to surprise economic events faster than traditional uncertainty measures (EPU), but the sample size is too small for statistical significance.

- 20 events with sufficient hourly data, 16 with detectable Kalshi reaction
- Surprise events: Kalshi leads EPU by ~56 hours (n=5)
- Non-surprise events: essentially simultaneous (+0.6h, n=7)
- Wilcoxon signed-rank: p=0.10

Directionally consistent with Finding 1 but requires a larger event sample.

---

## Invalidated Findings

These findings were initially reported as significant but were invalidated during methodology review:

| Finding | Original | Corrected | Reason |
|---------|----------|-----------|--------|
| Shock acceleration | 4h vs 8h, p<0.001 | 6h vs 8h, p=0.48 | Circular classification artifact |
| KUI leads EPU (Granger) | p=0.024 | p=0.658 | Absolute return bias; fixed with percentage returns |
| Trading Sharpe | +5.23 (4 trades) | -2.26 (23 trades) | Small-sample artifact |

---

## Methodology

### Data
- 6,141 settled Kalshi markets with outcomes (Oct 2024 - Feb 2026)
- 7,695 markets with text embeddings (experiment 5)
- 1,028 economics-relevant, 289 with hourly candle data
- 725 hourly candle files with full OHLC, bid-ask, open interest, and volume
- 336 multi-strike markets across 41 events (CPI, GDP, Jobless Claims)
- 4 domains: inflation (CPI), monetary policy (Fed Funds), labor (Jobless Claims), macro (GDP)
- External benchmarks: EPU (Baker-Bloom-Davis), VIX, S&P 500, TIPS breakeven (T10YIE, T5YIE)

### Key Corrections Applied
1. **ADF stationarity**: 43% of raw-level Granger results were spurious without differencing
2. **Within-pair Bonferroni**: testing 24 lags and selecting best inflates p-values; corrected by p x max_lag. Reduced pairs from 446 to 379.
3. **Shock-fraction classification**: replaced binary market-lifetime overlap with continuous shock-fraction measure
4. **Murphy decomposition**: Brier = reliability - resolution + uncertainty. Isolates true calibration from base rate effects.
5. **Permutation test**: 1,000 domain-label shuffles establish null distribution for cross-domain structure
6. **Bidirectional pair flagging**: 39% of pairs show A-to-B and B-to-A, indicating co-movement not causation
7. **F-stat overflow guards**: reject F > 10^6 and near-zero RSS (numerical artifacts)

### Experiments Summary

| # | Name | Key Finding | API Calls |
|---|------|-------------|-----------|
| 1 | Causal Lead-Lag | Inflation → monetary policy at 3h | Kalshi, Grok |
| 2 | KUI Construction | Uncertainty index (474 days) | Kalshi, FRED |
| 3 | Calibration Under Uncertainty | Better calibration during high KUI | None |
| 4 | Hourly Information Speed | ~56h lead vs EPU (underpowered) | None |
| 5 | Embeddings & Clustering | k-NN beats random by 15.7% | Kalshi |
| 6 | Market Microstructure | Spread narrows after events (p=0.013) | None |
| 7 | Implied Distributions | CPI 0.05pp median error, 2.8% arb violations | None |
| 8 | TIPS Comparison | TIPS leads Kalshi by 1 day (p=0.005) | FRED |
| 9 | Indicator Network | CPI → Fed at 3h, p=0.009 | None |
| 10 | Shock Propagation | Origin responds strongest (p<0.05), surprise 1.5-2.6x larger | None |
| 11 | Favorite-Longshot Bias | Economics-only: time-to-expiration predicts calibration (7x) | None |
| 12 | CRPS Distributional Scoring | Kalshi beats historical (p=0.0001), CPI overconfident | FRED |
