# Surviving Findings: Kalshi Prediction Market Research

**Date:** 2026-02-18
**Status:** PhD-review corrected. All findings below survive rigorous methodology checks.

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

Consistent with the Taylor Rule: CPI expectations propagate to Fed rate expectations faster than the reverse. Inflation is the dominant information source in the network, with labor and macro domains feeding into it, and monetary policy responding downstream.

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

### GDP Markets Deep-Dive

The effect is most dramatic in GDP prediction markets (all KXGDP):
- Low uncertainty: Brier = 0.802 (n=22) -- nearly random
- High uncertainty: Brier = 0.196 (n=15) -- well-calibrated
- Bootstrap CI: [-0.846, -0.321]. Significant.

### Interpretation

Economic stress likely attracts more sophisticated participants to GDP markets, transforming them from thinly-traded noise into well-calibrated forecasts. This "wisdom of crowds under pressure" effect suggests prediction markets function best precisely when accurate forecasting matters most.

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
- 2,001 settled Kalshi markets (Oct 2024 - Feb 2026)
- 1,028 economics-relevant, 289 with hourly candle data
- 4 domains: inflation (CPI), monetary policy (Fed Funds), labor (Jobless Claims), macro (GDP)
- External benchmarks: EPU (Baker-Bloom-Davis), VIX, S&P 500

### Key Corrections Applied
1. **ADF stationarity**: 43% of raw-level Granger results were spurious without differencing
2. **Within-pair Bonferroni**: testing 24 lags and selecting best inflates p-values; corrected by p x max_lag. Reduced pairs from 446 to 379.
3. **Shock-fraction classification**: replaced binary market-lifetime overlap with continuous shock-fraction measure
4. **Murphy decomposition**: Brier = reliability - resolution + uncertainty. Isolates true calibration from base rate effects.
5. **Permutation test**: 1,000 domain-label shuffles establish null distribution for cross-domain structure
6. **Bidirectional pair flagging**: 39% of pairs show A-to-B and B-to-A, indicating co-movement not causation
7. **F-stat overflow guards**: reject F > 10^6 and near-zero RSS (numerical artifacts)
