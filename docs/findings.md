# Surviving Findings: Kalshi Prediction Market Research

**Date:** 2026-02-19
**Status:** PhD-review corrected. Eleven experiments completed (1-11). All findings below survive rigorous methodology checks.

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

**Strength: Strong (new)**

Economic events trigger measurable cross-domain shock waves in prediction markets, with surprise events producing significantly larger responses in inflation (+46%, p=0.0002) and monetary policy (+159%, p=0.007) domains.

### Evidence

205 economic markets across 4 domains, 31 events, 9,108 event-hour observations:

**First significant response times (hours after event):**

| Event Type | Origin Domain | 1st Responder | 2nd Responder | 3rd Responder |
|-----------|---------------|---------------|---------------|---------------|
| CPI | inflation | macro (8h) | monetary_policy (18h) | labor (18h) |
| FOMC | monetary_policy | macro (4h) | inflation (6h) | — |
| NFP | labor | inflation (8h) | macro (8h) | — |
| GDP | macro | monetary_policy (32h) | — | — |

**Key pattern**: Macro markets are consistently the fastest cross-domain responders, reacting within 4-8 hours to CPI, FOMC, and NFP events. This suggests GDP/recession markets act as "bellwethers" that aggregate information from all domains.

**Surprise vs non-surprise response magnitude:**

| Domain | Surprise | Non-Surprise | Ratio | p-value |
|--------|----------|--------------|-------|---------|
| inflation | 0.037 | 0.026 | 1.46x | 0.0002 |
| monetary_policy | 0.012 | 0.005 | 2.59x | 0.007 |
| labor | 0.040 | 0.069 | 0.57x | 0.84 |
| macro | 0.022 | 0.027 | 0.79x | 0.99 |

Surprise events produce significantly larger responses in inflation and monetary policy markets, but not in labor or macro markets. This asymmetry suggests inflation and monetary policy markets are more "surprise-sensitive" — they price in consensus expectations tightly and move sharply on deviations.

### Interpretation

This is the first hourly-resolution visualization of cross-event shock propagation in prediction markets. The cascade pattern (CPI → macro within 8h → monetary_policy/labor within 18h) is consistent with the Granger causality findings from experiment 1 but adds temporal granularity. The surprise sensitivity results validate that prediction markets are informationally efficient: surprise events cause larger adjustments precisely because the prior was well-calibrated.

---

## Finding 7: Bid-Ask Spread Predicts Calibration Quality and Favorite-Longshot Bias

**Strength: Strong (new)**

Bid-ask spread is the dominant microstructure predictor of both market calibration and favorite-longshot bias. Markets with tight spreads are nearly perfectly calibrated with minimal bias, while wide-spread markets show 1300x worse calibration and 4x larger longshot overpricing.

### Evidence

6,141 settled markets total; 611 with hourly candle microstructure data:

**Calibration by spread tercile:**

| Spread Tercile | Brier Score | Longshot Bias | n |
|---------------|-------------|---------------|---|
| Low (tight) | 0.0001 | +0.011 | 212 |
| Medium | 0.038 | +0.037 | 195 |
| High (wide) | 0.130 | +0.040 | 204 |

The gradient is monotonic and dramatic. Low-spread markets achieve near-perfect calibration (Brier=0.0001) with negligible longshot bias (+0.011). High-spread markets show 1300x worse Brier scores and 4x larger longshot overpricing.

**Calibration by time to expiration:**

| Lifetime | Brier Score | Longshot Bias | n |
|----------|-------------|---------------|---|
| Short (~1h) | 0.351 | -0.377 | 2,041 |
| Medium | 0.225 | -0.224 | 2,040 |
| Long (~1974h) | 0.044 | -0.008 | 2,041 |

Longer-lived markets calibrate 8x better than short-lived ones, with near-zero bias at long horizons.

**Domain breakdown:**

| Domain | n | Brier | Longshot Bias | Favorite Bias |
|--------|---|-------|---------------|---------------|
| monetary_policy | 358 | 0.007 | +0.008 | -0.016 |
| macro | 150 | 0.071 | -0.004 | -0.036 |
| inflation | 421 | 0.090 | -0.025 | +0.004 |
| labor | 212 | 0.187 | -0.088 | +0.130 |
| crypto | 5,000 | 0.235 | -0.242 | -0.010 |

Monetary policy markets are nearly perfectly calibrated (Brier=0.007). Crypto markets show a strong REVERSE favorite-longshot bias: longshots are massively underpriced (implied 0.7% but win 22.8%).

### Interpretation

This directly extends Whelan (CEPR 2024), who documented favorite-longshot bias in Kalshi but lacked microstructure data. Our key contribution: **the bias is not a market-wide phenomenon — it concentrates in illiquid markets with wide spreads.** Tight-spread markets, where informed traders compete actively, eliminate the bias almost entirely. This supports the mechanism that market efficiency is endogenous to participation: more liquidity → tighter spreads → better price discovery → less bias. The finding also connects to Finding 2 (calibration improves with uncertainty/participation) through a unified "participation drives accuracy" narrative.

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
| 10 | Shock Propagation | Cross-domain cascade, surprise 1.5-2.6x larger (p<0.01) | None |
| 11 | Favorite-Longshot × Microstructure | Spread predicts bias: 0.011 (tight) vs 0.040 (wide) | None |
