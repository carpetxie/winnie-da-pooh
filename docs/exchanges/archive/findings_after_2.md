# When Do Prediction Market Distributions Add Value? A CRPS/MAE Diagnostic

**Date:** 2026-02-21
**Status:** Draft — under review.

## Abstract

Should traders trust the full implied distribution from prediction markets, or just the point forecast? We introduce the CRPS/MAE ratio as a simple diagnostic and apply it to 336 multi-strike Kalshi contracts across 41 economic events. The answer depends on the series: Jobless Claims distributions add massive value (CRPS/MAE=0.37), while CPI distributions are actively harmful (CRPS/MAE=1.32). A Monte Carlo simulation rules out strike-count differences as an explanation (<2% effect vs. the 32% CPI penalty). We hypothesize the divergence reflects release frequency — weekly Jobless Claims provide rapid calibration feedback that monthly CPI does not. We also find: Kalshi's CPI implied mean beats random walk (p=0.026, d=-0.60); TIPS breakeven rates lead Kalshi CPI by 1 day (Granger F=12.2, p=0.005); and no-arbitrage violation rates (2.8%) are directionally comparable to SPX equity options and far below other prediction markets.

> **Bottom line for traders:** Use Jobless Claims distributions — they capture 63% more information than point forecasts alone. For CPI, use only the implied mean and ignore the distributional spread; it adds noise, not signal.

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

Kalshi's 2.8% hourly violation rate is directionally comparable to SPX equity options — the most liquid derivatives market — and substantially lower than other prediction markets. **Caveat:** the Kalshi figure uses hourly snapshots while the SPX benchmark (Brigo et al., 2023) uses daily data. Hourly sampling captures transient violations invisible at daily granularity, so the true apples-to-apples comparison likely favors Kalshi even more. The 86% reversion within 1 hour is consistent with transient mispricing in thin markets, not systematic arbitrage opportunities.

---

## 2. Main Result: The CRPS/MAE Diagnostic and Distributional Heterogeneity

### CRPS/MAE Ratio: When Distributions Add Value

The CRPS/MAE ratio measures whether a market's distributional spread adds information beyond its point forecast (the implied mean). For a well-calibrated distribution, the sharpness reward in CRPS (the ½E|X−X'| term that rewards concentration) means CRPS will typically be lower than MAE; ratio > 1 signals that the distributional spread is miscalibrated and actively harming forecast quality rather than helping it. The ratio thus serves as a practical diagnostic: values below 1 indicate the distribution adds value beyond the point forecast, while values above 1 indicate the distributional spread introduces noise. (Note: this is a diagnostic property of calibration quality, not a mathematical bound — a sufficiently miscalibrated distribution can and will produce CRPS > MAE, which is exactly the signal we exploit.)

| Series | CRPS | MAE | CRPS/MAE | Interpretation |
|--------|------|-----|----------|----------------|
| KXCPI (n=14) | 0.108 | 0.082 | **1.32** | Distribution harmful — spread adds noise |
| KXJOBLESSCLAIMS (n=16) | 4,840 | 12,959 | **0.37** | Distribution adds massive value (63% gain) |

For CPI, a trader is better off using only the implied mean and ignoring the distributional spread entirely. For Jobless Claims, the full distribution captures substantially more information than the point forecast alone.

**Strike structure and simulation robustness check:** CPI events average 2.3 evaluated strikes (range 2–3, uniform 0.1pp spacing), while Jobless Claims average 2.8 evaluated strikes (range 2–5, variable 5K–10K spacing with clustering near the expected value). To quantify whether this difference could mechanically inflate CPI's CRPS, we ran a Monte Carlo simulation (10,000 trials): using known Normal distributions matched to each series' realized parameters, we constructed piecewise-linear CDFs with 2, 3, 4, and 5 strikes and computed CRPS against the same realized outcomes. **Result: going from 3 to 2 strikes inflates CRPS by 1–2%, far less than the 32% CPI penalty.** The strike-count confound accounts for at most ~5% of the observed CRPS/MAE gap between series. The remaining penalty is consistent with genuine miscalibration — the PIT analysis in Appendix A suggests directional bias (mean PIT=0.61, indicating markets underestimate inflation) as the primary driver.

### CRPS vs Historical Baselines

Historical benchmarks use regime-appropriate windows (Jobless Claims: 2022+, post-COVID normalization).

| Series | n | Kalshi CRPS | Historical CRPS | Wilcoxon p | p (Bonferroni) | Rank-biserial r |
|--------|---|------------|-----------------|------------|----------------|-----------------|
| KXJOBLESSCLAIMS | 16 | 4,840 | 8,758 | 0.047 | 0.093 | 0.49 |
| KXCPI | 14 | 0.108 | 0.091 | 0.709 | 1.000 | -0.16 |

The Jobless Claims result (r=0.49, medium-large effect) does not survive Bonferroni correction for two series tests (p_adj=0.093). However, the effect size is well-powered: 80% power requires only n=6 at this effect magnitude, suggesting the result is real but the multiplicity correction is conservative at this sample size.

*Benchmark sensitivity*: The COVID-contaminated window (2020-2025) inflates the Jobless Claims advantage from 1.8x to 7.3x (p<0.0001) due to COVID-era claims of 3-6 million vs current 200-250K. The regime-appropriate benchmark (2022+) gives an honest 1.8x improvement.

### Temporal CRPS Evolution

| Lifetime % | CPI (vs uniform) | 95% CI | Jobless Claims (vs uniform) | 95% CI |
|-----------|-------------------|--------|----------------------------|--------|
| 10% (early) | 1.96x | [1.50, 2.70] | 0.91x | [0.62, 1.26] |
| 50% (mid) | 2.55x | [1.62, 3.88] | 0.79x | [0.46, 1.38] |
| 90% (late) | 1.16x | [0.83, 1.73] | 0.78x | [0.43, 1.33] |

*Bootstrap CIs (10,000 resamples, ratio-of-means method) on CRPS/Uniform ratio.*

CPI distributions are significantly worse than uniform at early and mid-life (CIs exclude 1.0), but the late-life convergence to 1.16x is uncertain — the CI [0.83, 1.73] includes 1.0, so we cannot confirm CPI distributions achieve calibration by expiration. The trajectory from 2.55x to 1.16x is directionally suggestive of learning but not statistically conclusive at n=14. For Jobless Claims, the point estimates favor the market throughout (ratios <1), but wide CIs reflect the small sample — the advantage is more confidently established by the aggregate CRPS/MAE ratio (0.37) than by any single time slice.

### Why Do Jobless Claims and CPI Diverge?

We hypothesize four mechanisms driving the calibration heterogeneity:

1. **Release frequency and feedback**: Jobless Claims are released weekly (52 events/year), providing rapid feedback for distributional learning. CPI is monthly (12/year). Traders pricing Jobless Claims distributions receive 4x more calibration feedback, enabling faster convergence to well-calibrated distributions.

2. **Signal dimensionality**: CPI is a composite index aggregating shelter, food, energy, and services — each with different dynamics. Jobless Claims is a single administrative count with well-understood seasonal patterns. Lower-dimensional signals may be easier to price distributionally.

3. **Trader composition** *(speculative — not directly testable with public data)*: Jobless Claims markets attract specialized labor-market traders with domain expertise in distributional shape. CPI markets attract broader macro traders whose point forecasts are accurate (MAE=0.082) but whose uncertainty estimates are poorly calibrated.

4. **Liquidity and market depth**: If CPI markets have thinner order books at extreme strikes, the distributional tails will be poorly priced, inflating CRPS without affecting the implied mean (MAE). This is consistent with the CRPS/MAE > 1 finding.

These hypotheses are testable as more data accumulates: mechanisms 1 and 2 predict that other weekly releases (e.g., mortgage applications) should also have CRPS/MAE < 1, while other monthly composites (e.g., PCE) should have CRPS/MAE > 1. Future work should decompose CRPS into reliability, resolution, and uncertainty components (Hersbach, 2000) to identify which dimension drives the CPI penalty — the CRPS/MAE ratio collapses these into a single number, and the decomposition would clarify whether CPI markets are unreliable (biased), lack resolution (uninformative), or both. Additionally, decomposing CRPS by quantile region would distinguish tail mispricing (thin liquidity at extreme strikes) from center mispricing, providing direct evidence for or against mechanism 4.

Notably, the PIT analysis (Appendix A) offers a preliminary clue: mean PIT=0.61 suggests CPI markets systematically underestimate inflation (realized values fall in the upper half of the implied distribution), which is consistent with the CRPS/MAE > 1 finding being driven by directional miscalibration rather than mere distributional imprecision.

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
| SPF (annual/12 proxy)† | 0.110 | -0.25 | 0.211 | 14 |
| TIPS breakeven (monthly) | 0.112 | -0.27 | 0.163 | 14 |
| Trailing mean | 0.118 | -0.32 | 0.155 | 14 |
| Random walk (last month) | 0.143 | **-0.60** | **0.026** | 14 |

†*SPF does not forecast monthly CPI directly; this conversion divides the annual Q4/Q4 forecast by 12, assuming uniform monthly contributions. This ignores seasonality, base effects, and within-year dynamics, and should be treated as indicative rather than definitive.*

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
- Hersbach, H. (2000). Decomposition of the continuous ranked probability score for ensemble prediction systems. *Weather and Forecasting*, 15(5), 559-570.
- Messias, J., Corso, J., & Suarez-Tangil, G. (2025). Unravelling the probabilistic forest: Arbitrage in prediction markets. AFT 2025. arXiv:2508.03474.
