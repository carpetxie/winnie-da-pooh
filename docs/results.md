# Kalshi Prediction Market Research: Experiment Results

**Date:** 2026-02-18 (updated)
**Repository:** winnie-da-pooh

---

## Overview

We ran five experiments to discover novel signals in Kalshi prediction market data. The strongest result is that **information propagation between Kalshi sub-domains accelerates 2x during economic shocks** (median lag 4h vs 8h, p < 0.001), with inflation→monetary_policy showing a statistically significant directional asymmetry (3h vs 5h, p=0.0008).

| Experiment | Finding | Strength |
|------------|---------|----------|
| **1. Cross-Market Causal Lead-Lag** | Inflation leads monetary policy by 3h (p<0.001); shock-regime analysis shows 2x speed increase during crises | **Strong** |
| **2. Real-Time Uncertainty Index (KUI)** | Original KUI→EPU finding (p=0.024) invalidated by methodology fix; event study directionally consistent | Weak |
| **3. Calibration Under Uncertainty** | Markets significantly better calibrated during high uncertainty (Brier 0.353 vs 0.512, p<0.05); GDP markets drive the effect | **Moderate** |
| **4. Hourly Information Speed** | Kalshi reacts to surprise events ~56h before EPU on average; not significant (p=0.10) due to small n | Suggestive |
| **5. Embedding Similarity** | k-NN(k=20) beats random by 15.7% on Brier; cross-domain clusters are superficial | Dead end |

---

## Experiment 1: Cross-Market Causal Lead-Lag Discovery

### Question
Can we discover hidden causal dependencies between Kalshi markets across different economics sub-domains using Granger causality?

### Methodology
1. **Data**: 2,001 settled Kalshi markets across 7 domains
2. **Stationarity**: ADF-tested and differenced before Granger testing (43% of raw-level results were spurious)
3. **Granger Causality**: Pairwise F-tests at lags 1-24h, Bonferroni correction at alpha=0.01
4. **LLM Filtering**: All 446 significant pairs assessed by Grok-3-mini (score 1-5, threshold >= 4)
5. **Trading Simulation**: Signal-triggered portfolio with 75/25 temporal split

### Results

#### Granger Causality
- **3,957 directional tests** → **446 significant after Bonferroni**
- F-stats range: 3.06 - 549.99 (median 13.05)
- Median lag: 6 hours

#### Domain Pair Breakdown
| Leader | Follower | Pairs | Median Lag | Mean F-stat |
|--------|----------|-------|------------|-------------|
| macro | inflation | 114 | 5.5h | 30.3 |
| inflation | macro | 100 | 7.0h | 15.3 |
| labor | inflation | 75 | 6.0h | 38.4 |
| inflation | monetary_policy | 60 | 3.0h | 24.3 |
| inflation | labor | 56 | 8.0h | 22.3 |
| monetary_policy | inflation | 41 | 5.0h | 19.9 |

#### Propagation Network Asymmetry
**Statistically significant (Mann-Whitney U test):**
- **inflation → monetary_policy**: 3h median (n=60) vs reverse 5h (n=41), **p=0.0008**

**Directional but not significant:**
- labor → inflation: 6h vs reverse 8h, p=0.24
- macro → inflation: 5.5h vs reverse 7h, p=0.21

#### Shock-Regime Propagation (NEW)
Information flows **2x faster during economic shocks**:

| Domain Pair | Shock Median Lag | Calm Median Lag | p-value |
|-------------|-----------------|-----------------|---------|
| **Overall** | **4h** | **8h** | **< 0.001** |
| macro → inflation | 4h | 12h | 0.011 |
| inflation → macro | 6h | 13h | < 0.001 |
| inflation → monetary_policy | 3h (all shock) | — | — |

299/446 pairs (67%) fall in shock periods (+/- 3 days of surprise events). The inflation→monetary_policy channel operates exclusively during shock periods.

#### LLM Semantic Filtering (Expanded)
- **446 pairs assessed** (previously 50), **143 approved** (32% approval rate)
- Score distribution: 0→10, 2→37, 3→256, 4→141, 5→2
- Approved pairs by domain: inflation→monetary_policy (57), labor→inflation (36), macro→inflation (30)
- LLM correctly identifies Phillips Curve and Taylor Rule mechanisms

#### Trading Simulation (Updated)
| Portfolio | Trades | PnL | Sharpe | Win Rate |
|-----------|--------|-----|--------|----------|
| **A (All Granger)** | 40 | -0.110 | -1.01 | 27.5% |
| **B (LLM-filtered)** | 23 | -0.175 | -2.26 | 21.7% |

**Honest update**: The original +5.23 Sharpe (4 trades) was a small-sample artifact. With all 446 pairs assessed and 143 approved, Portfolio B shows 23 trades with negative Sharpe. The LLM correctly identifies economic mechanisms but this doesn't translate to profitable trading signals — the lead-lag relationships are too noisy at the individual market level.

**The publishable finding is the network structure, not trading alpha.**

---

## Experiment 2: Kalshi-Derived Real-Time Uncertainty Index (KUI)

### Question
Can we construct a real-time economic uncertainty index from Kalshi market belief volatility?

### Methodology
1. **Data**: 1,028 economics markets, 662 with candle data, Oct 2024 - Feb 2026
2. **KUI Construction**: Daily belief volatility using **percentage returns** (not absolute), **volume-weighted** within domains, **equal-weighted** across domains
3. **Validation**: Correlation, Granger causality, incremental R-squared, event study

### Results (After Methodology Fix)

#### Methodology Fix Impact
The original KUI used absolute price changes, which biased toward markets near $0.50. After switching to percentage returns + volume weighting:
- KUI-EPU correlation: +0.13 → **-0.08** (no longer correlated)
- KUI→EPU Granger: p=0.024 → **p=0.658** (no longer significant)
- The original finding was an artifact of the construction methodology

#### What Survives
- Event study still shows Kalshi leading EPU directionally (-1.0 days mean, 50% of events)
- CPI events: -1.4 days lead vs EPU (n=5)
- FOMC events: -4.0 days lead (n=1)
- The daily event study is cross-validated by Exp 4's hourly analysis

---

## Experiment 3: Prediction Market Calibration Under Uncertainty

### Question
Do prediction markets become less calibrated during high-uncertainty periods?

### Methodology
1. **Data**: 261 economics markets with mid-life prices as probability forecasts
2. **Uncertainty Regime**: Mean KUI during trading window, split into terciles
3. **Statistical Test**: Bootstrap Brier score difference (1,000 iterations)

### Results (Updated with Corrected KUI)

#### Calibration by Regime
| Regime | Brier Score | ECE | Mean KUI | n |
|--------|-------------|-----|----------|---|
| Low | **0.512** | 0.512 | 96.6 | 90 |
| Medium | 0.392 | 0.390 | 98.9 | 85 |
| High | **0.353** | 0.351 | 111.4 | 86 |

**Now statistically significant**: Bootstrap CI [-0.242, -0.016] excludes zero. Markets are meaningfully better calibrated during high uncertainty.

#### Fiscal Policy Deep-Dive (NEW)
The fiscal policy anomaly (all KXGDP markets) is dramatic and statistically significant:
- **Low uncertainty**: Brier = 0.802 (n=22) — markets nearly random
- **High uncertainty**: Brier = 0.196 (n=15) — markets well-calibrated
- Bootstrap CI: [-0.846, -0.321] — **significant**

Interpretation: GDP prediction markets are poorly calibrated during calm periods (possibly due to low trader attention / thin markets) but become dramatically well-calibrated during high uncertainty, likely because economic stress attracts more sophisticated participants.

---

## Experiment 4: Hourly Information Speed Event Study (NEW)

### Question
Does Kalshi absorb economic information within hours, while EPU/VIX take days?

### Methodology
1. **Data**: 725 cached hourly candle files, 289 markets across 4 economics domains
2. **Hourly BV**: Percentage-return belief volatility at hourly resolution
3. **Event windows**: +/- 72 hours around 31 economic events (12 surprises)
4. **Comparison**: Hourly Kalshi reaction time vs daily EPU/VIX reaction

### Results
- **20 events** with sufficient hourly data
- **16** with detectable Kalshi reaction
- **Mean lead-lag vs EPU**: -23.1 hours (Kalshi leads)
- Kalshi leads EPU in **58%** of events (7/12)

#### Reaction Speed by Event Type
| Event Type | Mean Kalshi Reaction | n |
|------------|---------------------|---|
| CPI | 16.6h | 8 |
| GDP | 24.0h | 3 |
| FOMC | 27.7h | 3 |
| NFP | 44.0h | 2 |

#### Surprise vs Non-Surprise
- **Surprise events**: Kalshi leads EPU by **-56.2h** (n=5)
- **Non-surprise**: Kalshi leads by **+0.6h** (n=7) — essentially simultaneous

#### Statistical Significance
- Sign test: p=0.77 (not significant)
- Wilcoxon signed-rank: p=0.10 (approaching significance)

The direction is consistent with Exp 1 and Exp 2 but the sample size (12 events with both Kalshi and EPU reaction data) is too small for statistical significance.

---

## Experiment 5: Market Description Embeddings as Economic Similarity Metric

(Unchanged — dead end for economics research. See previous version.)

---

## Unified Narrative

The experiments collectively reveal a multi-timescale information structure in Kalshi prediction markets:

1. **Hourly (Exp 1)**: Inflation markets Granger-cause monetary policy markets with 3h median lag (p<0.001). The propagation network shows 2x speed increase during economic shocks (4h vs 8h, p<0.001).

2. **Sub-daily (Exp 4)**: Kalshi reacts to surprise CPI/FOMC events within 17-28 hours. For surprise events, Kalshi leads EPU by ~56 hours. Directionally strong but underpowered (n=12).

3. **Regime-level (Exp 3)**: Markets are significantly better calibrated during high uncertainty (Brier 0.353 vs 0.512, p<0.05). GDP markets show a 4x calibration improvement during uncertainty.

4. **Methodology lesson (Exp 2)**: The original KUI→EPU Granger finding was an artifact of using absolute (not percentage) returns. Honest methodology invalidated the headline result while preserving the directional event study findings.

### Strongest Publishable Finding

The **shock-regime information propagation network**: during economic crises, information flows between Kalshi sub-domains at double the normal speed, with inflation→monetary_policy showing a statistically significant directional asymmetry. This is novel — no prior work has measured how prediction market information propagation speed varies with economic regime.

---

## Methodology Notes

### Stationarity Fix
ADF stationarity testing + automatic differencing reduced significant pairs from 781 to 446 (43% were spurious). All results use the corrected pipeline.

### F-stat Overflow Guards
Rejection of F-stats > 10^6 and near-zero RSS. Max F-stat dropped from ~10^26 to 550.

### KUI Construction Fix
Switching from absolute to percentage returns invalidated the KUI→EPU Granger finding (p=0.024 → p=0.658). Volume weighting and domain normalization were also added.

### Multiple Testing
Bonferroni correction for all pairwise Granger tests. Asymmetry tests use raw p-values (3 pre-specified hypotheses). Shock-regime comparison uses Mann-Whitney U on pre-specified domain pairs.

---

## Data Artifacts

| Artifact | Path |
|----------|------|
| Granger results (all) | `data/exp1/granger_results.csv` |
| Granger results (significant) | `data/exp1/granger_significant.csv` |
| Propagation network | `data/exp1/propagation_network.json` |
| LLM assessments (446 pairs) | `data/exp1/llm_assessments.json` |
| Trading simulation | `data/exp1/trading_results.json` |
| KUI daily index | `data/exp2/kui_daily.csv` |
| Event study (daily) | `data/exp2/event_study_results.csv` |
| Calibration results | `data/exp3/calibration_results.json` |
| Fiscal anomaly analysis | `data/exp3/fiscal_anomaly_analysis.json` |
| Hourly event study | `data/exp4/hourly_event_results.csv` |
| Statistical tests (Exp 4) | `data/exp4/statistical_tests.json` |
| Network plot (interactive) | `data/exp1/plots/propagation_network.html` |
| Hourly event windows | `data/exp4/plots/hourly_event_windows.png` |
| Calibration curves | `data/exp3/plots/calibration_by_regime.png` |
