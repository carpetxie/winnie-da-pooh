# Kalshi Prediction Market Research: Experiment Results

**Date:** 2026-02-18 (PhD-review corrected)
**Repository:** winnie-da-pooh

---

## Overview

We ran five experiments to discover novel signals in Kalshi prediction market data. After rigorous methodology corrections (within-pair Bonferroni, shock-fraction classification, Murphy decomposition, permutation tests), the strongest surviving findings are:

1. **Directional information asymmetry**: inflation→monetary_policy propagation is significantly faster than the reverse (3h vs 5h, p=0.0008), validated by permutation test (p<0.001)
2. **Calibration improves under uncertainty**: markets are genuinely better calibrated during high uncertainty (reliability 0.123 vs 0.262, p<0.05), surviving base rate controls

| Experiment | Finding | Strength |
|------------|---------|----------|
| **1. Cross-Market Causal Lead-Lag** | Inflation leads monetary policy by 3h; directional asymmetry confirmed by permutation test. ~~Shock acceleration~~ invalidated by corrected classification. | **Strong** (network), **Invalidated** (shock) |
| **2. Real-Time Uncertainty Index (KUI)** | KUI→EPU Granger invalidated (p=0.658); event study directionally consistent | Weak |
| **3. Calibration Under Uncertainty** | Reliability (pure calibration) significantly better during high uncertainty; survives Murphy decomposition base rate control | **Strong** |
| **4. Hourly Information Speed** | Kalshi reacts ~56h before EPU for surprises; underpowered (p=0.10) | Suggestive |
| **5. Embedding Similarity** | Dead end | Dead end |

---

## Experiment 1: Cross-Market Causal Lead-Lag Discovery

### Question
Can we discover hidden causal dependencies between Kalshi markets across different economics sub-domains using Granger causality?

### Methodology
1. **Data**: 2,001 settled Kalshi markets across 7 domains
2. **Stationarity**: ADF-tested and differenced before Granger testing (43% of raw-level results were spurious)
3. **Granger Causality**: Pairwise F-tests at lags 1-24h, within-pair Bonferroni (p × max_lag), then cross-pair Bonferroni at α=0.01
4. **Permutation Test**: 1,000 domain-label shuffles to establish null distribution
5. **LLM Filtering**: All significant pairs assessed by Grok-3-mini (score 1-5, threshold ≥ 4)

### Results

#### Granger Causality (Corrected)
- **3,957 directional tests** → **379 significant** after within-pair + cross-pair Bonferroni
- (Previous: 446 significant without within-pair correction — 67 were inflated by lag selection)
- Median lag: 6 hours

#### Permutation Test Validation
- **Cross-domain pairs**: 379 observed vs 265 ± 12 expected under null → **p<0.001**
- **Inflation→MP asymmetry**: 21 excess pairs vs null mean 0 ± 4.8 → **p<0.001**
- The network structure is real, not an artifact of domain sizes or testing procedures.

#### Bidirectional Pair Analysis
- **74 pairs** (39%) are bidirectional (A→B AND B→A significant), indicating **co-movement** rather than directional information flow
- **231 unidirectional pairs** remain after removing bidirectional pairs
- Unidirectional network: inflation→MP (50), labor→inflation (50), macro→inflation (47), monetary_policy→inflation (29), inflation→labor (28), inflation→macro (27)

#### Propagation Network Asymmetry (Unidirectional Only)
**Statistically significant (Mann-Whitney U test):**
- **inflation → monetary_policy**: 3h median (n=50) vs reverse 5h (n=29), **p=0.0008**
- Confirmed by permutation test (p<0.001)

#### ~~Shock-Regime Propagation~~ (INVALIDATED)
The original finding (4h shock vs 8h calm, p<0.001) was driven by **circular classification**: any market whose lifetime overlapped a shock window was labeled "shock", causing 67% of pairs to be classified as shock from only 20% of calendar days.

**After fix (shock-fraction > 50% classification):**
- Only 10 pairs (2.6%) are truly shock-dominated
- Overall: 6h shock vs 8h calm, **p=0.48** (not significant)
- Mean shock fraction (14.6%) matches calendar baseline (14.7%) — no evidence Granger pairs cluster preferentially in shock periods.

#### LLM Semantic Filtering
- **379 pairs assessed**, **~130 approved** (32% approval rate)
- Score distribution: mostly 3s (near-threshold), few 4-5s
- LLM correctly identifies Phillips Curve and Taylor Rule mechanisms
- Trading: negative Sharpe — network structure is publishable, trading alpha is not

---

## Experiment 2: Kalshi-Derived Real-Time Uncertainty Index (KUI)

### Question
Can we construct a real-time economic uncertainty index from Kalshi market belief volatility?

### Results (After Methodology Fix)

#### Methodology Fix Impact
The original KUI used absolute price changes, which biased toward markets near $0.50. After switching to percentage returns + volume weighting:
- KUI-EPU correlation: +0.13 → **-0.08** (no longer correlated)
- KUI→EPU Granger: p=0.024 → **p=0.658** (no longer significant)
- The original finding was an artifact of the construction methodology

#### What Survives
- Event study still shows Kalshi leading EPU directionally (-1.0 days mean, 50% of events)
- Cross-validated by Exp 4's hourly analysis

---

## Experiment 3: Prediction Market Calibration Under Uncertainty

### Question
Do prediction markets become better calibrated during high-uncertainty periods?

### Methodology
1. **Data**: 261 economics markets with mid-life prices as probability forecasts
2. **Uncertainty Regime**: Mean KUI during trading window, split into terciles
3. **Statistical Test**: Bootstrap Brier score difference + Murphy decomposition (1,000 iterations)

### Results (With Base Rate Controls)

#### Murphy Decomposition by Regime
| Regime | Brier | Reliability | Resolution | Uncertainty | Base Rate | n |
|--------|-------|-------------|------------|-------------|-----------|---|
| Low | 0.512 | **0.262** | 0.000 | 0.250 | 0.522 | 90 |
| Medium | 0.392 | 0.152 | 0.000 | 0.240 | 0.400 | 85 |
| High | 0.353 | **0.123** | 0.000 | 0.231 | 0.360 | 86 |

#### Base Rate Control
Base rates differ across regimes (0.522 low vs 0.362 high), which could confound raw Brier comparisons. **However, reliability (pure calibration error, independent of base rates) is also significantly better during high uncertainty:**
- Reliability difference CI: **[-0.209, -0.013]** — significant
- The calibration improvement is genuine, not a base rate artifact.

#### Fiscal Policy Deep-Dive
All 37 fiscal markets are KXGDP. Dramatic improvement: Brier 0.802 (low) vs 0.196 (high), bootstrap CI [-0.846, -0.321] — significant.

---

## Experiment 4: Hourly Information Speed Event Study

### Results
- **20 events** with sufficient hourly data, 16 with detectable Kalshi reaction
- **Mean lead-lag vs EPU**: -23.1 hours (Kalshi leads)
- **Surprise events**: Kalshi leads by -56.2h (n=5)
- **Non-surprise**: +0.6h (essentially simultaneous)
- Wilcoxon p=0.10 — directionally consistent but underpowered

---

## Experiment 5: Market Description Embeddings

Dead end. See previous version.

---

## Unified Narrative (Post-Correction)

After rigorous methodology corrections, two findings survive PhD-level scrutiny:

### Finding 1: Directional Information Asymmetry (Strong)
Inflation markets Granger-cause monetary policy markets with 3h median lag, significantly faster than the 5h reverse (p=0.0008). This is validated by permutation test (p<0.001) and holds after removing 74 bidirectional co-movement pairs (231 unidirectional remain). Consistent with the Taylor Rule: CPI expectations drive Fed rate expectations, not the reverse.

### Finding 2: Calibration Improves Under Uncertainty (Strong)
Markets are genuinely better calibrated during high uncertainty. Murphy decomposition isolates reliability (pure calibration error) at 0.123 (high uncertainty) vs 0.262 (low), with bootstrap CI [-0.209, -0.013]. This survives base rate controls. GDP markets show a 4x improvement.

### What Was Invalidated
- **Shock acceleration**: The original 2x speed-up (4h vs 8h, p<0.001) was entirely driven by circular classification. With proper shock-fraction classification, p=0.48.
- **KUI→EPU Granger**: Artifact of absolute returns. p=0.024 → p=0.658 after percentage returns.
- **Trading alpha**: Sharpe ratio is negative across all strategies.

---

## Methodology Corrections (PhD Review)

### 1. Within-Pair Bonferroni (Lag Selection)
Testing 24 lags per pair and selecting the best inflates significance. Applied p × max_lag correction. Reduced significant pairs from 446 to 379.

### 2. Shock-Fraction Classification
Replaced binary overlap classification (any intersection → "shock") with continuous shock-fraction (% of overlap days in shock windows). Threshold: >50% for shock, <20% for calm. Result: shock acceleration finding invalidated.

### 3. Murphy Brier Decomposition
Separated Brier = reliability - resolution + uncertainty to isolate true calibration effects from base rate differences across regimes. Result: calibration finding confirmed.

### 4. Permutation Test
1,000 domain-label shuffles confirm cross-domain structure (p<0.001) and directional asymmetry (p<0.001) are real.

### 5. Bidirectional Pair Flagging
39% of Granger pairs are bidirectional (co-movement), not directional information flow. Unidirectional subset (231 pairs) preserves the inflation→MP asymmetry.

---

## Data Artifacts

| Artifact | Path |
|----------|------|
| Granger results (all) | `data/exp1/granger_results.csv` |
| Granger results (significant) | `data/exp1/granger_significant.csv` |
| Propagation network | `data/exp1/propagation_network.json` |
| LLM assessments | `data/exp1/llm_assessments.json` |
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
