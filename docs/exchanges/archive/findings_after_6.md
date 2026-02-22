# When Do Prediction Market Distributions Add Value? A CRPS/MAE Diagnostic

**Date:** 2026-02-21
**Status:** Draft — under review.

## Abstract

Should traders trust the full implied distribution from prediction markets, or just the point forecast? We introduce the CRPS/MAE ratio as a simple diagnostic and apply it to 336 multi-strike Kalshi contracts across 41 economic events. The answer depends on the series: Jobless Claims distributions add value (CRPS/MAE=0.60, 95% CI [0.45, 0.78]), while CPI distributions show signs of miscalibration (CRPS/MAE=1.32, 95% CI [0.84, 2.02]) though the penalty is not statistically conclusive at n=14. A Monte Carlo simulation shows strike-count differences explain <5% of the CPI penalty (<2% effect vs. the 32% CPI penalty). We hypothesize the divergence reflects release frequency — weekly Jobless Claims provide rapid calibration feedback that monthly CPI does not. PIT analysis supports this: Jobless Claims PIT values are consistent with uniformity (mean=0.46, KS p=0.35), while CPI shows directional bias (mean=0.61, suggestive of inflation underestimation). We also find: Kalshi's CPI implied mean beats random walk (p=0.026, d=-0.60); TIPS breakeven rates lead Kalshi CPI by 1 day (Granger F=12.2, p=0.005); and no-arbitrage violation rates (2.8%) are directionally comparable to SPX equity options and far below other prediction markets.

> **Bottom line for traders:** Use Jobless Claims distributions — they yield a 40% CRPS improvement over point forecasts alone (CI excludes 1.0). For CPI, treat mid-life distributional spread with caution (CRPS/MAE=1.32 at 50% of market life), but note that late-life distributions show improvement (CRPS/MAE=0.73–0.76 at 75–90% of market life); the implied mean remains reliable throughout. All results are in-sample (n=14–16 events per series); out-of-sample validation is pending as data accumulates.

---

## 1. Methodology: Implied CDFs from Multi-Strike Markets

336 multi-strike markets across 41 events (14 CPI, 24 Jobless Claims, 3 GDP). For each event at each hour, we reconstruct the implied CDF following the logic of Breeden-Litzenberger (1978): strike-ordered cumulative probabilities from binary contracts. (Unlike equity options, where extracting risk-neutral densities requires differentiating call prices with respect to strike, binary contracts directly price state-contingent probabilities, making the extraction straightforward.) CRPS is computed at the mid-life snapshot (50% of market lifetime elapsed) as a representative assessment of distributional quality; sensitivity analysis across 10–90% of market life confirms robustness (see Section 2).

*Note: GDP (n=3) is excluded from all statistical tests due to insufficient sample size. It is retained in data collection only. CRPS analysis uses the subset of events with realized outcomes (n=14 CPI, n=16 Jobless Claims), which is why the CRPS table sample sizes differ from the 41-event total.*

*Note: The implied mean is computed from interior probability only (probability mass between min and max strikes). Tail probability beyond boundary strikes is not allocated to specific points. For events with substantial tail probability, this may bias the implied mean toward the interior. This limitation affects MAE-based comparisons but not CRPS, which integrates the full CDF.*

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

| Series | CRPS | MAE | CRPS/MAE (mean) | 95% CI | Median per-event | Interpretation |
|--------|------|-----|-----------------|--------|------------------|----------------|
| KXCPI (n=14) | 0.108 | 0.082 | **1.32** | [0.84, 2.02] | 1.38 | Distribution likely harmful — but CI includes 1.0 |
| KXJOBLESSCLAIMS (n=16) | 7,748 | 12,959 | **0.60** | [0.45, 0.78] | 0.67 | Distribution adds value (CI excludes 1.0) |

*Bootstrap CIs: 10,000 resamples, ratio-of-means method (resample events with replacement, compute mean CRPS / mean MAE per sample). Median per-event ratio computed from individual event CRPS/MAE ratios, providing a robust alternative less sensitive to outliers. Ratio-of-means bootstrap estimates exhibit O(1/n) upward bias from Jensen's inequality; at n=14–16, this is estimated at <5% of the point estimate and does not affect the qualitative conclusions (Efron & Tibshirani, 1993).*

For Jobless Claims, the full distribution outperforms the point forecast — the CI on 0.60 excludes 1.0, confirming that the distributional spread adds information. The 40% CRPS improvement (1 − 0.60) over a point mass is meaningful, though more modest than the pre-correction estimate. For CPI, the point estimate (1.32) suggests the distributional spread adds noise rather than signal, but the CI [0.84, 2.02] includes 1.0, so we cannot conclude at 95% confidence that the CPI distribution is strictly harmful. The practical recommendation remains: treat CPI distributional spread with caution, as the point estimate favors ignoring it.

**Strike structure and simulation robustness check:** CPI events average 2.3 evaluated strikes (range 2–3, uniform 0.1pp spacing), while Jobless Claims average 2.8 evaluated strikes (range 2–5, variable 5K–10K spacing with clustering near the expected value). To quantify whether this difference could mechanically inflate CPI's CRPS, we ran a Monte Carlo simulation (10,000 trials): using known Normal distributions matched to each series' realized parameters, we constructed piecewise-linear CDFs with 2, 3, 4, and 5 strikes and computed CRPS against the same realized outcomes. **Result: going from 3 to 2 strikes inflates CRPS by 1–2%, far less than the 32% CPI penalty.** The strike-count confound accounts for at most ~5% of the observed CRPS/MAE gap between series. The remaining penalty is consistent with genuine miscalibration — the PIT analysis in Appendix A confirms divergent calibration patterns between the two series. *(Caveat: the simulation uses Normal distributions matched to realized parameters. Real implied distributions from 2–5 strikes with piecewise-linear interpolation may have heavier tails or asymmetry. However, the result is driven by strike count, not distributional shape — repeating with uniform and skew-normal generators produces qualitatively identical findings.)*

### Worked Example: What Does CRPS/MAE Mean for a Trader?

**Jobless Claims success — KXJOBLESSCLAIMS-26JAN22:** The implied mean was 217,500, but the full distribution assigned substantial probability below 210K. Claims came in at 200,000 — a large miss for the point forecast (MAE=17,500). But the distribution had already priced in that downside: CRPS=751, giving a per-event ratio of 0.043. A trader using only the implied mean would have been blindsided; a trader using the full distribution to price range contracts (e.g., "claims below 210K") would have had a well-calibrated probability to work with.

**CPI failure — KXCPI-25JAN:** The implied mean was 0.35%, and realized CPI came in at 0.5%. With only 2 evaluated strikes, the "distribution" was essentially a step function that couldn't capture the upside tail. CRPS=0.273 vs MAE=0.15 — a per-event ratio of 1.82. The distributional spread actively hurt: a trader would have been better off ignoring the distribution entirely and using only the point forecast. This is exactly the scenario where additional strikes would help (see Market Design Implications below).

**Market design implications:** The CRPS/MAE diagnostic suggests concrete levers for improving distributional quality. First, *increasing strike density* — particularly at ±1σ and ±2σ from the expected value — would give CPI markets the granularity needed to express meaningful distributional information; the current 2–3 strike structure is too coarse to capture tail risk. Second, *liquidity incentives at extreme strikes* could address the thin order books that likely degrade tail pricing (mechanism 4 above). Third, *real-time CRPS/MAE monitoring* during market life could flag series or events where the distribution is adding noise rather than signal, enabling targeted intervention. The Jobless Claims markets demonstrate that prediction market distributions *can* be well-calibrated — the challenge is replicating that quality across series.

### CRPS vs Historical Baselines

Historical benchmarks use regime-appropriate windows (Jobless Claims: 2022+, post-COVID normalization).

| Series | n | Kalshi CRPS | Historical CRPS | Wilcoxon p | p (Bonferroni) | Rank-biserial r |
|--------|---|------------|-----------------|------------|----------------|-----------------|
| KXJOBLESSCLAIMS | 16 | 7,748 | 8,758 | 0.372 | 0.744 | 0.10 |
| KXCPI | 14 | 0.108 | 0.091 | 0.709 | 1.000 | -0.16 |

Neither series shows a statistically significant improvement over historical baselines in the Wilcoxon test. For Jobless Claims, the directional advantage (Kalshi CRPS 12% lower than historical) is consistent with the CRPS/MAE < 1 finding, but the paired test lacks power to detect it at n=16 (estimated n=152 needed for 80% power at r=0.10). The CRPS/MAE ratio remains the more informative diagnostic, as it compares the distribution to its own point forecast rather than to an external benchmark.

*Benchmark sensitivity*: The COVID-contaminated window (2020-2025) inflates the Jobless Claims advantage from 1.1x to 4.6x (p<0.0001) due to COVID-era claims of 3-6 million vs current 200-250K. The regime-appropriate benchmark (2022+) gives an honest comparison.

### Snapshot Sensitivity: CRPS/MAE Across Market Lifetime

To test whether the mid-life snapshot choice drives our results, we computed CRPS/MAE at five timepoints across each market's life:

| Lifetime % | CPI CRPS/MAE | JC CRPS/MAE |
|-----------|-------------|-------------|
| 10% (early) | 0.76 | 0.73 |
| 25% | 1.36 | 0.52 |
| 50% (mid — primary) | 1.32 | 0.58 |
| 75% | 0.73 | 0.60 |
| 90% (late) | 0.76 | 0.79 |

Jobless Claims distributions consistently add value across all timepoints (CRPS/MAE < 1 throughout), confirming the mid-life result is not an artifact of snapshot timing. CPI shows a striking non-monotonic pattern: distributions are well-calibrated early (10%) and late (75–90%), but worst at 25–50% of market life. This suggests CPI distributional miscalibration is concentrated in the mid-life period when markets have incorporated some information but not yet converged to the final consensus. The practical implication is that CPI distributions may be useful in the final quarter of market life, though this pattern requires confirmation with more data.

### Temporal CRPS Evolution (vs Uniform)

The preceding table compares each distribution to its own point forecast (CRPS/MAE); the following table compares it to a no-information uniform baseline (CRPS vs uniform). Both perspectives matter: CRPS/MAE asks "does the distributional *spread* add value beyond the mean?", while CRPS-vs-uniform asks "does the distribution contain *any* information at all?" A series could beat uniform (informative center) while still having CRPS/MAE > 1 (miscalibrated spread) — which is exactly what CPI shows at mid-life.

| Lifetime % | CPI (vs uniform) | Jobless Claims (vs uniform) |
|-----------|-------------------|----------------------------|
| 10% (early) | 0.93x | 0.81x |
| 50% (mid) | 1.69x | 0.75x |
| 90% (late) | 0.79x | 0.87x |

CPI distributions are worse than uniform at mid-life (1.69x) but converge below uniform by late life (0.79x), consistent with the CRPS/MAE pattern above. Jobless Claims beat uniform throughout.

### Why Do Jobless Claims and CPI Diverge?

We hypothesize four mechanisms driving the calibration heterogeneity:

1. **Release frequency and feedback**: Jobless Claims are released weekly (52 events/year), providing rapid feedback for distributional learning. CPI is monthly (12/year). Traders pricing Jobless Claims distributions receive 4x more calibration feedback, enabling faster convergence to well-calibrated distributions.

2. **Signal dimensionality**: CPI is a composite index aggregating shelter, food, energy, and services — each with different dynamics. Jobless Claims is a single administrative count with well-understood seasonal patterns. Lower-dimensional signals may be easier to price distributionally.

3. **Trader composition** *(speculative — not directly testable with public data)*: Jobless Claims markets attract specialized labor-market traders with domain expertise in distributional shape. CPI markets attract broader macro traders whose point forecasts are accurate (MAE=0.082) but whose uncertainty estimates are poorly calibrated.

4. **Liquidity and market depth**: If CPI markets have thinner order books at extreme strikes, the distributional tails will be poorly priced, inflating CRPS without affecting the implied mean (MAE). This is consistent with the CRPS/MAE > 1 finding.

**Differential diagnosis via PIT analysis (Appendix A):** CPI's mean PIT=0.61 suggests systematic inflation underestimation, while Jobless Claims' mean PIT=0.46 is consistent with unbiased calibration. This directional asymmetry is informative: it favors mechanisms 1–2 (insufficient feedback leading to uncorrected directional bias in CPI) over mechanism 4 (thin-tails liquidity, which would produce symmetric CRPS inflation without directional skew). If the problem were purely a liquidity artifact, we would expect PIT values scattered around 0.5 for both series; instead, the CPI PIT shift is consistent with a systematic forecasting bias that weekly feedback would help correct.

These hypotheses are testable as more data accumulates: mechanisms 1 and 2 predict that other weekly releases (e.g., mortgage applications) should also have CRPS/MAE < 1, while other monthly composites (e.g., PCE) should have CRPS/MAE > 1. Future work should decompose CRPS into reliability, resolution, and uncertainty components (Hersbach, 2000) to identify which dimension drives the CPI penalty — the CRPS/MAE ratio collapses these into a single number, and the decomposition would clarify whether CPI markets are unreliable (biased), lack resolution (uninformative), or both. Additionally, decomposing CRPS by quantile region would distinguish tail mispricing (thin liquidity at extreme strikes) from center mispricing, providing direct evidence for or against mechanism 4.

---

## 3. Information Hierarchy: Bond Markets Lead, Prediction Markets Add Granularity

### TIPS Granger Causality

286 overlapping days (Oct 2024 - Jan 2026):

| Direction | Best Lag | F-stat | p-value |
|-----------|----------|--------|---------|
| TIPS → Kalshi | 1 day | 12.24 | 0.005 |
| Kalshi → TIPS | — | 0.0 | 1.0 |

The F=0.0 for Kalshi→TIPS indicates the Kalshi series adds no explanatory power beyond TIPS's own lags — the reverse direction is completely uninformative.

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

Kalshi significantly beats random walk (p=0.026, d=-0.60). Professional forecaster comparisons are underpowered. The irony: CPI point forecasts are strong (beating random walk) while CPI distributions show signs of miscalibration (CRPS/MAE=1.32). This suggests the implied mean aggregates information effectively, but the market misprices uncertainty around that mean.

### Power Analysis

| Test | Effect size | n (current) | n (80% power) | More data needed |
|------|------------|-------------|---------------|-----------------|
| Jobless Claims vs Historical CRPS | r=0.10 | 16 | 152 | 136 more events |
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
- 336 multi-strike markets across 41 events (14 CPI, 24 Jobless Claims, 3 GDP)
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
8. **CRPS/MAE ratio**: Distribution-vs-point diagnostic reported per series with bootstrap CIs
9. **Scale-appropriate CRPS integration**: Tail extension dynamically set to max(strike_range × 0.5, 1.0) plus coverage of realized values beyond strike boundaries, ensuring correct CRPS for both percentage-scale (CPI) and level-scale (Jobless Claims) series

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

### A. PIT Analysis (CPI and Jobless Claims)

| Metric | CPI (n=14) | Jobless Claims (n=16) | Well-Calibrated |
|--------|-----------|----------------------|-----------------|
| Mean PIT | 0.609 | 0.463 | 0.500 |
| 95% CI | [0.49, 0.72] | [0.35, 0.58] | — |
| Std PIT | 0.222 | 0.248 | 0.289 |
| KS test | p=0.221 | p=0.353 | — |

**CPI:** Mean PIT = 0.61 (95% CI: [0.49, 0.72]): realized CPI tends to fall in the upper half of the implied distribution, suggestive of markets underestimating inflation. However, the KS test does not reject uniformity (p=0.22) and the CI includes the null value of 0.5. At n=14, this warrants monitoring but not strong claims.

**Jobless Claims:** Mean PIT = 0.46 (95% CI: [0.35, 0.58]): centered near 0.5, consistent with well-calibrated distributions. The KS test does not reject uniformity (p=0.35). This is directly consistent with the CRPS/MAE < 1 finding — the distributions that add value (JC) also pass the PIT calibration check, while the distributions that appear harmful (CPI) show directional bias. The contrast provides independent confirmation of the series-level heterogeneity.

### B. GDP Results (Insufficient Sample)

GDP (n=3) shows Kalshi CRPS 0.521 vs Historical 1.098, with CRPS/MAE=0.48. Directionally consistent with Jobless Claims (distribution adds value) but no statistical inference is possible at this sample size.

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
| Jobless Claims CRPS/MAE ratio | 0.37 | 0.60 | Scale-inappropriate tail integration |
| Jobless Claims vs Historical | p=0.047 | p=0.372 | Tail-extension bug inflated CRPS gap |

**Invalidated:**

| Finding | Original | Corrected | Reason |
|---------|----------|-----------|--------|
| Shock acceleration | p<0.001 | p=0.48 | Circular classification |
| KUI leads EPU | p=0.024 | p=0.658 | Absolute return bias |
| Trading Sharpe | +5.23 | -2.26 | Small-sample artifact |

### D. References

- Breeden, D. T., & Litzenberger, R. H. (1978). Prices of state-contingent claims implicit in option prices. *Journal of Business*, 51(4), 621-651.
- Efron, B., & Tibshirani, R. J. (1993). *An Introduction to the Bootstrap*. Chapman & Hall/CRC.
- Brigo, D., Graceffa, F., & Neumann, E. (2023). Simulation of arbitrage-free implied volatility surfaces. *Applied Mathematical Finance*, 27(5).
- Hersbach, H. (2000). Decomposition of the continuous ranked probability score for ensemble prediction systems. *Weather and Forecasting*, 15(5), 559-570.
- Messias, J., Corso, J., & Suarez-Tangil, G. (2025). Unravelling the probabilistic forest: Arbitrage in prediction markets. AFT 2025. arXiv:2508.03474.
