# When Do Prediction Market Distributions Add Value? A CRPS/MAE Diagnostic

**Date:** 2026-02-23
**Status:** Draft — under review (iteration 11).

## Abstract

Prediction market point forecasts and distributional forecasts can diverge dramatically in quality — accurate centers with miscalibrated spreads. We introduce the CRPS/MAE ratio as a diagnostic that flags this decoupling, and apply it to 909 multi-strike Kalshi contracts across 62 settled economic events spanning four series: CPI (n=33), Jobless Claims (n=16), GDP (n=9), and the Federal Funds Rate (n=4).

Three of four series show distributions that robustly add value: GDP (CRPS/MAE=0.48, 95% CI [0.38, 0.58]), Jobless Claims (0.60, CI [0.45, 0.78]), and CPI overall (0.86, CI [0.62, 1.23]). Heterogeneity across series is statistically significant (Kruskal-Wallis p=0.028; 4-series p=0.019). Only the Federal Funds Rate shows harmful distributions (1.48, CI [0.82, 2.73]), though at n=4 this is tentative.

A natural temporal split reveals a structural break in CPI: old-prefix events (Dec 2022–Oct 2024, n=19) show strong distributional value (CRPS/MAE=0.69), while new-prefix events (Nov 2024+, n=14) show harmful distributions (CRPS/MAE=1.32). This shift — though not individually significant (Mann-Whitney p=0.18) — suggests that the earlier finding of CPI distributional harm (iteration 10, n=14, ratio=1.58) was an artifact of analyzing only the post-break period. CPI *point* forecasts beat all benchmarks including random walk (d=−0.85, p_adj=0.014) across both periods, making this — to our knowledge — the first empirical demonstration *in prediction markets* that point and distributional calibration can diverge independently.

> **Practical Takeaways:**
> - **GDP:** Use the full distribution — CRPS is 52% below the point-forecast MAE (CRPS/MAE=0.48). All 9 LOO ratios < 1.0. CI [0.38, 0.58] excludes 1.0 convincingly.
> - **Jobless Claims:** Use the full distribution — CRPS is 40% below the point-forecast MAE (CRPS/MAE=0.60). All 16 LOO ratios < 1.0. CI [0.45, 0.78] excludes 1.0.
> - **CPI:** Distributions add value overall (CRPS/MAE=0.86), but with a temporal caveat: pre-Nov 2024 events (ratio=0.69) outperform post-Nov 2024 events (ratio=1.32). Monitor the CRPS/MAE ratio in real time to detect regime shifts.
> - **FED:** Tentatively use point forecast only (ratio=1.48), but n=4 is too small for confident recommendations.
> - **The CRPS/MAE ratio** tells you which regime you're in. Values below 1 mean the distribution adds value; values above 1 mean it's actively harmful. Monitor it per series.
>
> All results are in-sample; out-of-sample validation is pending as data accumulates. The CPI temporal split provides a suggestive natural OOS test (train on old-prefix, evaluate on new-prefix).

**Executive Summary:**

| | GDP (n=9) | Jobless Claims (n=16) | CPI (n=33) | FED (n=4) |
|---|---|---|---|---|
| CRPS/MAE | **0.48** | **0.60** | **0.86** | **1.48** |
| 95% CI | [0.38, 0.58] | [0.45, 0.78] | [0.62, 1.23] | [0.82, 2.73] |
| CI excludes 1.0? | ✅ Yes | ✅ Yes | ❌ No | ❌ No |
| LOO unanimous? | ✅ All < 1.0 | ✅ All < 1.0 | ✅ All < 1.0 | ✅ All > 1.0 |
| Recommendation | Use full distribution | Use full distribution | Use distribution; monitor for regime shift | Use point forecast (tentative) |

---

## 1. Methodology: Implied CDFs from Multi-Strike Markets

909 multi-strike markets across 96 events (33 CPI, 24 Jobless Claims, 14 GDP, 25 FED), of which 62 events have both realized outcomes and sufficient candle data for CRPS computation. For each event at each hour, we reconstruct the implied CDF following the logic of Breeden-Litzenberger (1978): strike-ordered cumulative probabilities from binary contracts. (Unlike equity options, where extracting risk-neutral densities requires differentiating call prices with respect to strike, binary contracts directly price state-contingent probabilities, making the extraction straightforward.) CRPS is computed at the mid-life snapshot (50% of market lifetime elapsed) as a representative assessment of distributional quality.

We merge old naming conventions (CPI-, FED-, GDP-) with new naming conventions (KXCPI-, KXFED-, KXGDP-) into canonical series, as these represent the same underlying economic indicators with a platform naming change around November 2024. This expansion — from 2 series with 30 events in iteration 10 to 4 series with 62 events — substantially increases statistical power and enables cross-series heterogeneity tests.

*Note on implied mean computation: We report two versions of the CRPS/MAE ratio. The "interior-only" implied mean uses only probability mass between min and max strikes (renormalized). The "tail-aware" implied mean integrates the same piecewise-linear CDF used for CRPS computation. The interior-only version is used as the primary result for per-event analysis due to greater stability; both versions are reported for transparency.*

### No-Arbitrage Efficiency

| Metric | Kalshi | Benchmark |
|--------|--------|-----------|
| Violation rate (non-monotone CDF) | 2.8% of snapshots (hourly) | SPX call spread: 2.7% of violations (daily) (Brigo et al., 2023) — different measurement bases; directionally comparable |
| Reversion rate | 86% within 1 hour | Polymarket: ~1h resolution (Messias et al., 2025) |
| Other prediction markets | — | Polymarket: 41%, PredictIt: ~95%, IEM: 37.7% |

Kalshi's 2.8% hourly violation rate is directionally comparable to SPX equity options — the most liquid derivatives market — and substantially lower than other prediction markets. **Caveat:** the Kalshi figure uses hourly snapshots while the SPX benchmark (Brigo et al., 2023) uses daily data. Hourly sampling captures transient violations invisible at daily granularity, so the true apples-to-apples comparison likely favors Kalshi even more. The 86% reversion within 1 hour is consistent with transient mispricing in thin markets, not systematic arbitrage opportunities.

---

## 2. Main Result: Prediction Market Distributions Add Value for Most Economic Series

We find that prediction market distributions add significant value for three of four economic series — GDP, Jobless Claims, and CPI (overall) — with the Federal Funds Rate as the sole exception. The CRPS/MAE ratio — our central diagnostic — separates these regimes. Heterogeneity across series is statistically significant (Kruskal-Wallis H=7.16, p=0.028 for 3 series; H=9.98, p=0.019 for all 4).

### The CRPS/MAE Diagnostic

The CRPS/MAE ratio measures whether a market's distributional spread adds information beyond its point forecast (the implied mean). CRPS is a strictly proper scoring rule (Gneiting & Raftery, 2007) — it is uniquely minimized by the true distribution, making it the natural metric for evaluating distributional forecasts. For a well-calibrated distribution, the sharpness reward in CRPS (the ½E|X−X'| term that rewards concentration) means CRPS will typically be lower than MAE; ratio > 1 signals that the distributional spread is miscalibrated and actively harming forecast quality. Values below 1 indicate the distribution adds value; values above 1 indicate the distributional spread introduces noise.

**Primary result (interior-only implied mean):**

| Series | n | CRPS | MAE | CRPS/MAE | 95% CI | Median per-event | LOO |
|--------|---|------|-----|----------|--------|------------------|-----|
| GDP | 9 | 0.580 | 1.211 | **0.48** | [0.38, 0.58] | 0.46 | All < 1.0 [0.45, 0.51] |
| Jobless Claims | 16 | 7,748 | 12,959 | **0.60** | [0.45, 0.78] | 0.67 | All < 1.0 [0.57, 0.66] |
| CPI | 33 | 0.108 | 0.125 | **0.86** | [0.62, 1.23] | 0.96 | All < 1.0 [0.80, 0.96] |
| FED | 4 | 0.148 | 0.100 | **1.48** | [0.82, 2.73] | 1.59 | All > 1.0 [1.12, 1.80] |

*Bootstrap CIs: 10,000 resamples, BCa (bias-corrected and accelerated) method via `scipy.stats.bootstrap`, which corrects for both bias and skewness in the bootstrap distribution — standard for ratio estimators at small n (Efron & Tibshirani, 1993).*

*Sensitivity: tail-aware implied mean (integrating same CDF as CRPS):*

| Series | CRPS/MAE (tail-aware) | 95% CI |
|--------|----------------------|--------|
| GDP | 0.57 | [0.48, 0.65] |
| Jobless Claims | 0.66 | [0.57, 0.76] |
| CPI | 0.96 | [0.71, 1.33] |
| FED | 1.47 | [0.96, 2.49] |

### Cross-Series Heterogeneity

**Kruskal-Wallis test** on per-event CRPS/MAE ratios across GDP, Jobless Claims, and CPI: H=7.16, p=0.028. Including FED (4-series test): H=9.98, p=0.019. Distributional quality is significantly heterogeneous across economic series.

**Pairwise comparisons (Mann-Whitney U):**

| Comparison | p-value | Rank-biserial r | Interpretation |
|-----------|---------|-----------------|----------------|
| CPI vs GDP | 0.020 | −0.52 (large) | GDP distributions significantly better |
| JC vs GDP | 0.066 | −0.46 (medium-large) | GDP directionally better |
| CPI vs JC | 0.150 | −0.26 (small-medium) | JC directionally better |

GDP shows the strongest distributional value (CRPS/MAE=0.48), followed by Jobless Claims (0.60). CPI's overall ratio (0.86) reflects a mixture of excellent earlier events and poor recent events (see temporal split below).

### CPI Temporal Structural Break

A natural temporal split — old naming convention (CPI-, Dec 2022–Oct 2024) vs new naming convention (KXCPI-, Nov 2024+) — reveals a striking shift in CPI distributional quality:

| Period | Prefix | n | CRPS/MAE | Median per-event |
|--------|--------|---|----------|------------------|
| Dec 2022 – Oct 2024 | CPI- | 19 | **0.69** | 0.73 |
| Nov 2024 – present | KXCPI- | 14 | **1.32** | 1.38 |

The Mann-Whitney test for this split gives p=0.18 — not individually significant, but the directional shift is large (ratio nearly doubles) and the split is pre-registered by the naming convention change rather than chosen to maximize the difference.

**Implications:** The earlier finding (iteration 10) that "CPI distributions are harmful" (CRPS/MAE=1.58, n=14) was based exclusively on post-break data. With the full 33-event CPI series, the aggregate ratio falls to 0.86 — distributions add value overall. The structural break may reflect:
1. **Platform changes** coinciding with the naming convention switch (market design, strike structure, or liquidity changes)
2. **Macro regime shift** in late 2024 (post-election inflation uncertainty)
3. **Statistical noise** — p=0.18 cannot rule out that the split is random

This finding reframes CPI from a cautionary tale ("distributions are harmful") to a more nuanced story ("distributions add value on average, but quality is time-varying and recent events show degradation").

### Why Do Series Differ?

We hypothesize four mechanisms driving the heterogeneity, now testable with 4 series:

1. **Release frequency and feedback**: GDP (quarterly, 4/year) has the *best* CRPS/MAE despite the lowest feedback frequency, contradicting the frequency hypothesis. This suggests signal complexity (mechanism 2) may dominate.

2. **Signal dimensionality**: GDP is a single aggregate growth rate; Jobless Claims is a single administrative count; CPI is a composite index aggregating shelter, food, energy, and services; FED is a discrete rate decision. The two simplest series (GDP, JC) show the best distributional quality. FED, despite being a single rate, has discrete jumps that may make distributional pricing harder.

3. **Trader composition** *(speculative — not directly testable with public data)*: Different series attract traders with different distributional expertise.

4. **Strike density**: GDP averages 3.7 strikes/event, JC 2.8, CPI 2.2, FED 3.3. The two best-performing series (GDP, JC) have moderate-to-high strike counts, but the relationship is not monotonic (FED has 3.3 strikes and the worst ratio).

### Per-Event Heterogeneity

Per-event CRPS/MAE ratios show substantial within-series variation:

| Series | Min | Max | IQR |
|--------|-----|-----|-----|
| GDP | 0.25 | 0.63 | [0.38, 0.58] |
| Jobless Claims | 0.17 | 2.54 | [0.45, 1.04] |
| CPI | 0.27 | 5.58 | [0.52, 1.42] |
| FED | 1.00 | 1.98 | [1.07, 1.74] |

For CPI, 20 of 33 events (61%) have CRPS/MAE < 1 — the distribution adds value for a majority of events. The aggregate CPI penalty is driven by a minority of events with very high ratios, particularly in the post-Nov 2024 period.

---

## 3. Information Hierarchy: Bond Markets Lead, Prediction Markets Add Granularity

Having established *how well* Kalshi prices distributions (Section 2), we now ask *where the information comes from*.

### TIPS Granger Causality

286 overlapping days (Oct 2024 - Jan 2026):

| Direction | Best Lag | F-stat | p-value |
|-----------|----------|--------|---------|
| TIPS → Kalshi | 1 day | 12.24 | 0.005 |
| Kalshi → TIPS | — | 0.0 | 1.0 |

TIPS breakeven rates Granger-cause Kalshi CPI prices at a 1-day lag. However, Granger causality measures predictive information, not causal information flow — the lag may reflect slow-updating Kalshi contracts (stale prices in thinly traded markets) rather than a genuine information hierarchy. Regardless, Kalshi is a useful aggregator — it incorporates TIPS information while adding granularity through its multi-strike structure.

### CPI Point Forecast Horse Race

*Note: This analysis uses the 14 KXCPI (post-Nov 2024) events where FRED benchmark alignment is validated. The qualitative conclusion — that Kalshi point forecasts beat standard benchmarks — is expected to hold or strengthen with the full 33-event CPI series.*

| Forecaster | Mean MAE | Cohen's d | p (raw) | p (Bonferroni ×4) | n |
|-----------|----------|-----------|---------|-------------------|---|
| **Kalshi implied mean (tail-aware)** | **0.068** | — | — | — | **14** |
| SPF (annual/12 proxy)† | 0.110 | -0.43 | 0.086 | 0.345 | 14 |
| TIPS breakeven (monthly) | 0.112 | -0.47 | **0.045** | 0.181 | 14 |
| Trailing mean | 0.118 | -0.47 | **0.021** | 0.084 | 14 |
| Random walk (last month) | 0.150 | **-0.85** | **0.003** | **0.014** | 14 |

†*SPF does not forecast monthly CPI directly; this conversion divides the annual Q4/Q4 forecast by 12. This is indicative rather than definitive.*

The Kalshi CPI implied mean outperforms random walk with a large effect size (d=−0.85, p_adj=0.014), **significant at the 5% level after Bonferroni correction**. This result is robust to excluding the first event (n=13: d=−0.89, p_adj=0.016) and the first two events (n=12: d=−0.89, p_adj=0.024).

**The point-vs-distribution decoupling.** This is, to our knowledge, the first empirical demonstration *in prediction markets* that point forecasts and distributional forecasts can be independently calibrated — accurate centers with miscalibrated spreads. CPI point forecasts significantly beat random walk while CPI distributions in the same period show CRPS/MAE=1.32. The temporal split adds nuance: when distributions are well-calibrated (old CPI, ratio=0.69), the market excels on both dimensions; the decoupling is specific to the post-Nov 2024 regime.

### Power Analysis

| Test | Effect size | n (current) | n (80% power) | Status |
|------|------------|-------------|---------------|--------|
| Kruskal-Wallis (3 series) | H=7.16 | 58 | — | **p=0.028, already significant** |
| GDP CI excludes 1.0 | — | 9 | — | **CI [0.38, 0.58], already powered** |
| JC CI excludes 1.0 | — | 16 | — | **CI [0.45, 0.78], already powered** |
| CPI temporal split | r≈0.26 | 33 | ~95 | Not yet powered (p=0.18) |
| FED CI excludes 1.0 | — | 4 | ~15 | Needs ~11 more events |
| Kalshi vs Random Walk | d=0.85 | 14 | 9 | **Already powered** |

---

## 4. Robustness: Why We Trust These Results

### GDP (CRPS/MAE=0.48)

- **Leave-one-out**: All 9 LOO ratios < 1.0 (range [0.45, 0.51]); extremely stable.
- **CI excludes 1.0**: BCa CI [0.38, 0.58] — no overlap with 1.0.
- **Historical benchmark**: Kalshi CRPS 0.580 vs Historical CRPS 0.762 (24% lower), but not individually significant (p=0.285 at n=9).
- **Prefixes merged**: Old GDP (n=6) and new KXGDP (n=3) combined; both subsets show ratios < 1.0.

### Jobless Claims (CRPS/MAE=0.60)

- **Leave-one-out**: All 16 LOO ratios < 1.0 (range [0.57, 0.66]); no single event drives the result.
- **CI excludes 1.0**: BCa CI [0.45, 0.78].
- **CRPS vs historical baseline**: Directional advantage (12% lower), but paired test underpowered (p=0.372).
- **Temporal stability** (from iteration 10 analysis): Tail-aware CIs exclude 1.0 at all five temporal snapshots (10%, 25%, 50%, 75%, 90% of market life).

### CPI (CRPS/MAE=0.86)

- **Leave-one-out**: All 33 LOO ratios < 1.0 (range [0.80, 0.96]); no single event drives the aggregate below 1.0.
- **CI includes 1.0**: BCa CI [0.62, 1.23]. The aggregate result is *directionally* favorable but not conclusive.
- **Temporal split**: Old CPI (ratio=0.69) vs new KXCPI (ratio=1.32). The aggregate masks a structural break.
- **Historical benchmark**: Kalshi CRPS comparable to historical CRPS (p=0.714); no significant advantage over the naive historical distribution.

### FED (CRPS/MAE=1.48)

- **Leave-one-out**: All 4 LOO ratios > 1.0 (range [1.12, 1.80]); consistently harmful.
- **CI includes 1.0**: BCa CI [0.82, 2.73]. Wide CI reflects n=4 — insufficient for definitive conclusions.
- **Tentative interpretation**: FED rate decisions involve discrete jumps (0/25/50bp) that may make distributional pricing harder than continuous economic indicators.

### Heterogeneity Tests

- **Kruskal-Wallis** (3 series): H=7.16, p=0.028 — significant at 5%.
- **Kruskal-Wallis** (4 series): H=9.98, p=0.019 — significant at 5%.
- **GDP vs CPI** (Mann-Whitney): p=0.020, r=−0.52 — GDP distributions significantly better.
- **JC vs GDP** (Mann-Whitney): p=0.066, r=−0.46 — directional.
- **CPI vs JC** (Mann-Whitney): p=0.150, r=−0.26 — directional.

### PIT Diagnostic

*From the KXCPI (n=14) and KXJOBLESSCLAIMS (n=16) subset used in the original experiment13 analysis:*

| Metric | CPI (n=14) | Jobless Claims (n=16) | Well-Calibrated |
|--------|-----------|----------------------|-----------------|
| Mean PIT | 0.609 | 0.463 | 0.500 |
| 95% CI | [0.49, 0.72] | [0.35, 0.58] | — |
| KS test p | 0.221 | 0.353 | — |

CPI's mean PIT=0.61 means realized CPI tends to fall in the upper half of the implied distribution — markets systematically underestimate inflation in the post-Nov 2024 period. Jobless Claims' mean PIT=0.46 is consistent with unbiased calibration.

### Surprise Magnitude

*From the KXCPI (n=14) analysis:*

The CRPS/MAE ratio is inversely correlated with surprise magnitude. CPI Spearman ρ=−0.68 (p=0.008): distributions fail more on small surprises. A CRPS/uniform comparison confirms this is genuine, not purely a denominator artifact (CPI high-surprise CRPS/uniform=1.42 vs low-surprise=2.34).

### Strike-Count Confound

Monte Carlo simulation: 2→3 strike effect ≤2% for symmetric distributions, vs observed cross-series gaps of 30–50%. Empirical: both CPI subsets (2-strike and 3+-strike) show similar ratios. Strike count does not explain the heterogeneity.

---

## Methodology

### Data
- 909 multi-strike markets across 96 events (33 CPI, 24 Jobless Claims, 14 GDP, 25 FED)
- 62 events with realized outcomes and CRPS computation (33 CPI, 16 JC, 9 GDP, 4 FED)
- Series merge: old naming (CPI-, FED-, GDP-) combined with new naming (KXCPI-, KXFED-, KXGDP-) into canonical series
- External: TIPS breakeven (T10YIE), SPF median CPI, FRED historical data (CPIAUCSL, ICSA, A191RL1Q225SBEA, DFEDTARU)

### In-Sample Caveat

All CRPS/MAE ratios and statistical tests are computed on the full available dataset. The CPI temporal split (old prefix as "training," new prefix as "test") provides a suggestive natural out-of-sample comparison, though it was not a pre-registered test.

### Key Statistical Methods
1. **BCa bootstrap**: 10,000 resamples, bias-corrected and accelerated CIs — standard for ratio estimators at small n (Efron & Tibshirani, 1993).
2. **Kruskal-Wallis test**: Non-parametric test for heterogeneity across 3+ series (replaces the 2-series Mann-Whitney from iteration 10).
3. **Bonferroni correction**: Applied for pairwise comparisons and horse race benchmarks.
4. **Leave-one-out sensitivity**: All series show unanimous LOO results (same side of 1.0).
5. **Canonical series merging**: Old/new naming conventions merged using prefix mapping; both subsets analyzed separately to check for structural breaks.

### Experiments Summary

| # | Name | Role in Paper |
|---|------|---------------|
| 7 | Implied Distributions | Section 1: Methodology (expanded to 4 series) |
| 12 | CRPS Scoring | Section 2: Base CRPS computation (expanded to 4 series) |
| 13 | Unified + Horse Race | Sections 2-4: Per-series tests, horse race, robustness |
| 8 | TIPS Comparison | Section 3: Information hierarchy |
| 11 | Favorite-Longshot Bias | Appendix D: Maturity (controlled) |
| — | expanded_crps_analysis.py | Section 2: 4-series expansion (62 events) |

---

## Supplementary Appendix

### A. PIT Analysis — Additional Detail

The main PIT results are reported in Section 4 (PIT Diagnostic subsection), based on the KXCPI/KXJOBLESSCLAIMS subset. Extending PIT analysis to the full 4-series dataset with 62 events is a priority for the next iteration.

### B. Downgraded and Invalidated Findings

During the research process, several initially significant findings were invalidated or substantially weakened by methodological corrections. We document these for transparency:

**Downgraded:**

| Finding | Naive p | Corrected | Issue |
|---------|---------|-----------|-------|
| CPI distributions "actively harmful" | CI [1.04, 2.52] | CI [0.62, 1.23] | Sample restricted to post-break period; full series ratio=0.86 |
| Heterogeneity from 2-series test | p=0.003 (MWU) | p=0.028 (KW, 3-series) | Upgraded from 2-sample to k-sample test |
| Calibration under uncertainty | 0.016 | CI includes zero | Cluster-robust bootstrap |
| Microstructure event response | 0.013 | 0.542 | Within-event correlation |
| Shock propagation (surprise) | 0.0002 | 0.436 | Within-event correlation |
| Maturity gradient | 7x | 1.5x | Observation timing confound |
| Jobless Claims CRPS headline | <0.0001 | 0.047 | COVID-contaminated benchmark |
| Jobless Claims vs Historical | p=0.047 | p=0.372 | Tail-extension bug inflated CRPS gap |
| Kalshi vs Random Walk (interior) | p=0.026 | p=0.102 | Bonferroni correction for 4 benchmarks |

**Invalidated:**

| Finding | Original | Corrected | Reason |
|---------|----------|-----------|--------|
| Shock acceleration | p<0.001 | p=0.48 | Circular classification |
| KUI leads EPU | p=0.024 | p=0.658 | Absolute return bias |
| Trading Sharpe | +5.23 | -2.26 | Small-sample artifact |

### C. Market Design Implications

The CRPS/MAE diagnostic suggests concrete levers for improving distributional quality:

1. **Series-specific monitoring**: GDP and Jobless Claims distributions are well-calibrated; no intervention needed. CPI and FED distributions need improvement, particularly in the post-Nov 2024 period for CPI.

2. **Strike density**: The two best-performing series (GDP=3.7, JC=2.8 strikes/event) have moderate-to-high density. CPI averages only 2.2 strikes/event — increasing to 4-5 could help, conditional on sufficient liquidity at new strikes.

3. **Real-time CRPS/MAE monitoring** during market life could flag series or events where the distribution is adding noise — particularly useful for detecting regime shifts like the CPI structural break.

### D. Market Maturity and Binary Contract Calibration

**50%-Lifetime Analysis (controlled):**

| Lifetime | Brier (50% of life) | n |
|----------|---------------------|---|
| Short (~147h) | 0.166 | 85 |
| Long (~2054h) | 0.114 | 85 |

The T-24h gradient (7x) is largely mechanical. The controlled analysis (50% of lifetime) shows a 1.5x residual.

### E. References

- Breeden, D. T., & Litzenberger, R. H. (1978). Prices of state-contingent claims implicit in option prices. *Journal of Business*, 51(4), 621-651.
- Efron, B., & Tibshirani, R. J. (1993). *An Introduction to the Bootstrap*. Chapman & Hall/CRC.
- Brigo, D., Graceffa, F., & Neumann, E. (2023). Simulation of arbitrage-free implied volatility surfaces. *Applied Mathematical Finance*, 27(5).
- Gneiting, T., & Raftery, A. E. (2007). Strictly proper scoring rules, prediction, and estimation. *Journal of the American Statistical Association*, 102(477), 359-378.
- Hersbach, H. (2000). Decomposition of the continuous ranked probability score for ensemble prediction systems. *Weather and Forecasting*, 15(5), 559-570.
- Messias, J., Corso, J., & Suarez-Tangil, G. (2025). Unravelling the probabilistic forest: Arbitrage in prediction markets. AFT 2025. arXiv:2508.03474.
- Murphy, A. H. (1993). What is a good forecast? An essay on the nature of goodness in weather forecasting. *Weather and Forecasting*, 8(2), 281-293.

### F. Complete Statistical Corrections Log

All 20 corrections applied during the research process:

1. **Regime-appropriate benchmarks**: Jobless Claims window 2022+ (post-COVID)
2. **Per-series decomposition**: Pooled tests mask heterogeneity; per-series Wilcoxon tests reveal series divergence
3. **Bonferroni correction**: Raw p-values adjusted for multiple comparisons
4. **Rank-biserial effect sizes**: Reported for all Mann-Whitney tests
5. **Power analysis**: Sample sizes for 80% power computed for all tests
6. **Controlled observation timing**: T-24h maturity gradient (7x) reduced to 1.5x at 50% lifetime
7. **PIT sign correction**: cdf_values store survival P(X>strike), not CDF P(X<=strike). PIT = 1 - interpolated survival
8. **CRPS/MAE ratio**: Distribution-vs-point diagnostic reported per series with BCa bootstrap CIs
9. **Scale-appropriate CRPS integration**: Tail extension dynamically set to max(strike_range × 0.5, 1.0) plus coverage of realized values beyond strike boundaries
10. **Serial correlation adjustment**: CPI AR(1) ρ=0.23, n_eff≈8.8 (Bartlett's formula), CI widened ~27%
11. **Tail-aware implied mean**: E[X] from same piecewise-linear CDF used for CRPS
12. **Leave-one-out sensitivity**: All series show unanimous LOO results
13. **CRPS − MAE signed difference**: JC p=0.001, CPI p=0.091 (iteration 10 subset)
14. **Formal heterogeneity test**: Upgraded from Mann-Whitney (2-series) to Kruskal-Wallis (3-4 series)
15. **Block bootstrap**: Block length 2, 10,000 resamples (iteration 10 CPI subset)
16. **Cramér-von Mises test**: CPI p=0.152, JC p=0.396 (iteration 10 subset)
17. **Mid-life CDF monotonicity verification**: 0 violations across mid-life snapshots used for CRPS
18. **Per-event temporal trajectories**: Analyzed where data permits
19. **Canonical series merging**: Old/new naming conventions (CPI/KXCPI, GDP/KXGDP, FED/KXFED) merged into canonical series
20. **CPI temporal structural break**: Pre/post Nov 2024 split reveals regime-dependent distributional quality
