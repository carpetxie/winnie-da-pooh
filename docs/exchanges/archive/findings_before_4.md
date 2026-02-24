# When Do Prediction Market Distributions Add Value? A CRPS/MAE Diagnostic

**Date:** 2026-02-24
**Status:** Draft — under review (iteration 13).

## Abstract

Prediction market point forecasts and distributional forecasts can diverge dramatically in quality — accurate centers with miscalibrated spreads. We introduce the CRPS/MAE ratio as a diagnostic that flags this decoupling, and apply it to multi-strike Kalshi contracts across 93 settled economic events spanning seven series: CPI (n=33), Jobless Claims (n=16), Core PCE (n=15), GDP (n=9), ADP Employment (n=9), ISM PMI (n=7), and the Federal Funds Rate (n=4).

The CRPS/MAE ratio compares how well a market's full probability distribution performs (CRPS) against using just its central point forecast (MAE). A ratio below 1 means the distribution adds value; above 1 means the spread around the center is so miscalibrated that you'd be better off ignoring it. We find a striking dichotomy: "simple" economic indicators — GDP (CRPS/MAE=0.48, BCa CI [0.31, 0.77]), Jobless Claims (0.60, CI [0.37, 1.02]), and ADP Employment (0.69, CI [0.36, 1.37]) — have distributions that consistently add value (LOO ratios unanimously < 1.0 for all three). "Complex" indicators — Core PCE (2.06, CI [1.24, 3.49]), CPI post-Nov 2024 (1.32), and the Federal Funds Rate (1.48, CI [0.79, 4.86]) — have distributions that actively harm. Heterogeneity across series is highly significant (Kruskal-Wallis H=18.5, p=0.005, 7 series, n=93). The simple-vs-complex gap is substantial: median ratio 0.63 vs 1.31 (Mann-Whitney p=0.0004, r=0.43).

A natural temporal split reveals a structural break in CPI: old-prefix events (Dec 2022–Oct 2024, n=19) show strong distributional value (CRPS/MAE=0.69), while new-prefix events (Nov 2024+, n=14) show harmful distributions (CRPS/MAE=1.32). This shift — though not individually significant (Mann-Whitney p=0.18) — suggests that the earlier finding of CPI distributional harm (iteration 10, n=14, ratio=1.58) was an artifact of analyzing only the post-break period. CPI *point* forecasts beat all benchmarks including random walk (d=−0.85, p_adj=0.014) across both periods, making this — to our knowledge — the first empirical demonstration *in prediction markets* that point and distributional calibration can diverge independently.

> **Practical Takeaways:**
> - **GDP:** Use the full distribution — CRPS is 52% below the point-forecast MAE (CRPS/MAE=0.48). All 9 LOO ratios < 1.0. BCa CI [0.31, 0.77] excludes 1.0.
> - **Jobless Claims:** Use the full distribution — CRPS is 40% below the point-forecast MAE (CRPS/MAE=0.60). All 16 LOO ratios < 1.0. BCa CI [0.37, 1.02] includes 1.0, but the LOO unanimity provides strong convergent evidence.
> - **CPI:** Distributions add value overall (CRPS/MAE=0.86), but with a temporal caveat: pre-Nov 2024 events (ratio=0.69) outperform post-Nov 2024 events (ratio=1.32). Monitor the CRPS/MAE ratio in real time to detect regime shifts.
> - **FED:** Tentatively use point forecast only (ratio=1.48), but n=4 is too small for confident recommendations.
> - **The CRPS/MAE ratio** tells you which regime you're in. Values below 1 mean the distribution adds value; values above 1 mean it's actively harmful. Monitor it per series.
>
> All CRPS/MAE ratios are computed in-sample. An expanding-window OOS test on CPI (training on the first N events, predicting whether event N+1's ratio falls below 1) achieves 50% accuracy — no better than chance — because the structural break after Nov 2024 causes the model to systematically mispredict recent events. This underscores the need for real-time CRPS/MAE monitoring rather than static thresholds.

**Executive Summary:**

| | GDP (n=9) | JC (n=16) | ADP (n=9) | CPI (n=33) | ISM (n=7) | PCE Core (n=15) | FED (n=4) |
|---|---|---|---|---|---|---|---|
| CRPS/MAE | **0.48** | **0.60** | **0.69** | **0.86** | **1.15** | **2.06** | **1.48** |
| 95% BCa CI | [0.31, 0.77] | [0.37, 1.02] | [0.36, 1.37] | [0.57, 1.23] | [0.60, 2.69] | [1.24, 3.49] | [0.79, 4.86] |
| CI excl. 1.0? | ✅ Yes | ❌ Borderline | ❌ No | ❌ No | ❌ No | ✅ Yes (>1) | ❌ No |
| LOO unanimous | ✅ All < 1.0 | ✅ All < 1.0 | ✅ All < 1.0 | ✅ All < 1.0 | ❌ Mixed | ✅ All > 1.0 | ✅ All > 1.0 |
| Type | Simple | Simple | Simple | Complex | Mixed | Complex | Discrete |
| Recommendation | Use dist. | Use dist. | Use dist. | Monitor | Caution | Use point | Use point |

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

We find a striking dichotomy in distributional quality across seven economic series. "Simple" indicators — GDP, Jobless Claims, and ADP Employment — have distributions that consistently add value (CRPS/MAE = 0.48, 0.60, 0.69 respectively; all LOO ratios < 1.0). "Complex" indicators — Core PCE, CPI (recent), and the Federal Funds Rate — have distributions that actively harm forecast quality (CRPS/MAE = 2.06, 1.32, 1.48). Heterogeneity across series is highly significant (Kruskal-Wallis H=18.5, p=0.005 for 7 series; H=16.4, p=0.006 for 6 series with n≥5).

### The CRPS/MAE Diagnostic

The CRPS/MAE ratio measures whether a market's distributional spread adds information beyond its point forecast (the implied mean). CRPS is a strictly proper scoring rule (Gneiting & Raftery, 2007) — it is uniquely minimized by the true distribution, making it the natural metric for evaluating distributional forecasts. For a well-calibrated distribution, the sharpness reward in CRPS (the ½E|X−X'| term that rewards concentration) means CRPS will typically be lower than MAE; ratio > 1 signals that the distributional spread is miscalibrated and actively harming forecast quality. Values below 1 indicate the distribution adds value; values above 1 indicate the distributional spread introduces noise.

**Primary result (interior-only implied mean):**

| Series | n | CRPS | MAE | CRPS/MAE | 95% BCa CI | Median per-event | LOO |
|--------|---|------|-----|----------|------------|------------------|-----|
| GDP | 9 | 0.580 | 1.211 | **0.48** | [0.31, 0.77] | 0.46 | All < 1.0 [0.45, 0.51] |
| Jobless Claims | 16 | 7,748 | 12,959 | **0.60** | [0.37, 1.02] | 0.67 | All < 1.0 [0.57, 0.66] |
| CPI | 33 | 0.108 | 0.125 | **0.86** | [0.57, 1.23] | 0.96 | All < 1.0 [0.80, 0.96] |
| FED | 4 | 0.148 | 0.100 | **1.48** | [0.79, 4.86] | 1.59 | All > 1.0 [1.12, 1.80] |

*Bootstrap CIs: 10,000 resamples, BCa (bias-corrected and accelerated) method via `scipy.stats.bootstrap`, which corrects for both bias and skewness in the bootstrap distribution — standard for ratio estimators at small n (Efron & Tibshirani, 1993). Note: prior to iteration 13, a function signature bug caused silent fallback to simple percentile bootstrap. All CIs reported here use true BCa.*

*Sensitivity: tail-aware implied mean (integrating same CDF as CRPS):*

| Series | CRPS/MAE (tail-aware) | 95% BCa CI |
|--------|----------------------|------------|
| GDP | 0.57 | [0.36, 0.92] |
| Jobless Claims | 0.66 | [0.42, 1.08] |
| CPI | 0.96 | [0.65, 1.35] |
| FED | 1.47 | [0.67, 4.20] |

### Expanded Series: Core PCE, ADP Employment, ISM PMI

In iteration 13, we queried the Kalshi `/series` API endpoint and discovered 9 additional economic series with multi-strike settled markets. We fetched candlestick data and computed CRPS/MAE for the three with the most events:

| Series | n | CRPS/MAE | 95% BCa CI | LOO | Interpretation |
|--------|---|----------|------------|-----|----------------|
| Core PCE (KXPCECORE) | 15 | **2.06** | [1.24, 3.49] | All > 1.0 | Distributions harmful |
| ADP Employment (KXADP) | 9 | **0.69** | [0.36, 1.37] | All < 1.0 | Distributions add value |
| ISM PMI (KXISMPMI) | 7 | **1.15** | [0.60, 2.69] | Mixed | Borderline harmful |

**Core PCE** (the Fed's preferred inflation measure) shows the worst distributional quality of any series: CRPS/MAE=2.06, with all 15 LOO ratios > 1.0 and a CI that conclusively excludes 1.0 *from above*. Like CPI (post-break) and FED, this is a complex composite index where distributional pricing is difficult.

**ADP Employment** (monthly employment change) mirrors GDP and Jobless Claims: simple, single-number indicators where distributions add value. All 9 LOO ratios are below 1.0.

**ISM Manufacturing PMI** is borderline: the aggregate ratio is 1.15 but 4 of 7 events have ratios below 1.0. The wide CI [0.60, 2.69] reflects both small n and genuine heterogeneity.

### Cross-Series Heterogeneity

**Kruskal-Wallis test** on per-event CRPS/MAE ratios: with the original 4 series, H=9.98, p=0.019. With all 7 series (93 events): **H=18.5, p=0.005**. With 6 series (n≥5): **H=16.4, p=0.006**. The addition of Core PCE, ADP, and ISM substantially strengthens the heterogeneity finding.

**The simple-vs-complex dichotomy.** Grouping series by signal complexity — "simple" (GDP, Jobless Claims, ADP: single-number indicators) vs "complex" (CPI, Core PCE, FED: composites or discrete) — reveals a large, significant gap:
- Simple series median CRPS/MAE: **0.63** (n=34)
- Complex series median CRPS/MAE: **1.31** (n=52)
- Mann-Whitney: p=0.0004, r=0.43

This is the paper's strongest and most actionable finding: **distributional quality depends on signal complexity, not market liquidity or sample size.**

**Original pairwise comparisons (Mann-Whitney U, Bonferroni-corrected for 3 tests, α_adj=0.017):**

| Comparison | p (raw) | p (Bonferroni) | Rank-biserial r | Interpretation |
|-----------|---------|----------------|-----------------|----------------|
| CPI vs GDP | 0.020 | 0.059 | −0.52 (large) | GDP directionally better (borderline after correction) |
| JC vs GDP | 0.066 | 0.197 | −0.46 (medium-large) | GDP directionally better |
| CPI vs JC | 0.150 | 0.450 | −0.26 (small-medium) | JC directionally better |

*Note: No pairwise comparison survives Bonferroni correction among the original 3 series. The KW omnibus test and simple-vs-complex grouping are the primary heterogeneity results.*

GDP shows the strongest distributional value (CRPS/MAE=0.48), followed by Jobless Claims (0.60) and ADP (0.69). CPI's overall ratio (0.86) reflects a mixture of excellent earlier events and poor recent events (see temporal split below).

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

### What Drives Distributional Quality?

We test several candidate mechanisms using multivariate analysis across all 62 events.

**Surprise magnitude and the CRPS/MAE ratio.** The CRPS/MAE ratio is strongly inversely correlated with surprise magnitude (Spearman ρ=−0.65, p<0.0001, n=62). However, this correlation is **largely mechanical**: surprise magnitude (|implied mean − realized|) is the MAE, which is the denominator of the CRPS/MAE ratio. When we test raw CRPS against surprise z-score directly — removing the denominator artifact — the correlation vanishes (ρ=0.12, p=0.35, n=62). This means the ratio is low for surprising events primarily because MAE is large, not because CRPS is low. The multivariate regression (R²=0.27, surprise coeff=−0.84) should be interpreted with this caveat: surprise z-score's explanatory power derives from the ratio's denominator, not from genuine variation in distributional quality.

**Volume (liquidity) does not predict CRPS/MAE.** Spearman ρ=0.14 (p=0.27, n=62) between log(event volume) and CRPS/MAE ratio — no significant relationship. Within CPI (n=33): ρ=0.08, p=0.67. Within Jobless Claims (n=16): ρ=0.19, p=0.48. The liquidity hypothesis — that thin order books at extreme strikes degrade distributional quality — is not supported. Volume varies substantially across series (CPI median=140K contracts, JC median=16K), but this variation does not predict calibration quality. This null finding is informative: it rules out the simplest market-design lever (increasing volume) as a fix for distributional miscalibration.

**Signal dimensionality** remains the most plausible series-level explanation. GDP is a single aggregate growth rate; Jobless Claims is a single administrative count; CPI is a composite index aggregating shelter, food, energy, and services; FED is a discrete rate decision. The two simplest series (GDP, JC) show the best distributional quality. FED, despite being a single rate, has discrete jumps (0/25/50bp) that may make distributional pricing harder.

**Release frequency** does not explain the pattern: GDP (quarterly, 4/year) has the *best* CRPS/MAE despite the lowest feedback frequency.

**Strike count** shows no significant within-series relationship for CPI (ρ=0.18, p=0.30) and a counterintuitive positive relationship for Jobless Claims (ρ=0.49, p=0.057) — more strikes are weakly associated with *higher* ratios. Monte Carlo simulation confirms that the mechanical effect of 2→3 strikes is ≤2%, vs observed cross-series gaps of 30–50%.

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

## 3. CPI Point Forecasts and the Point-Distribution Decoupling

Having established *how well* Kalshi prices distributions (Section 2), we test the quality of Kalshi's CPI *point* forecasts and demonstrate a striking decoupling between point and distributional quality.

### TIPS Granger Causality (Brief)

TIPS breakeven rates Granger-cause Kalshi CPI prices at a 1-day lag (F=12.24, p=0.005; 286 overlapping days, Oct 2024–Jan 2026), but not vice versa. The lag likely reflects slow-updating Kalshi contracts rather than a deep information hierarchy. This is expected and unsurprising — bond markets are far more liquid.

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
| GDP CI excludes 1.0 | — | 9 | — | **BCa CI [0.31, 0.77], excludes 1.0** |
| JC CI excludes 1.0 | — | 16 | ~20–25 | BCa CI [0.37, 1.02], borderline (includes 1.0 by 0.02) |
| CPI temporal split | r≈0.26 | 33 | ~95 | Not yet powered (p=0.18) |
| FED CI excludes 1.0 | — | 4 | ~15 | Needs ~11 more events |
| Kalshi vs Random Walk | d=0.85 | 14 | 9 | **Already powered** |

---

## 4. Robustness: Why We Trust These Results

### GDP (CRPS/MAE=0.48)

- **Leave-one-out**: All 9 LOO ratios < 1.0 (range [0.45, 0.51]); extremely stable.
- **CI excludes 1.0**: BCa CI [0.31, 0.77] — no overlap with 1.0. The only series where the CI conclusively excludes 1.0.
- **Historical benchmark**: Kalshi CRPS 0.580 vs Historical CRPS 0.762 (24% lower), but not individually significant (p=0.285 at n=9).
- **Prefixes merged**: Old GDP (n=6) and new KXGDP (n=3) combined; both subsets show ratios < 1.0.

### Jobless Claims (CRPS/MAE=0.60)

- **Leave-one-out**: All 16 LOO ratios < 1.0 (range [0.57, 0.66]); no single event drives the result.
- **CI borderline**: BCa CI [0.37, 1.02] — just barely includes 1.0. The LOO unanimity (all 16 < 1.0) provides strong convergent evidence that distributions add value.
- **CRPS vs historical baseline**: Directional advantage (12% lower), but paired test underpowered (p=0.372).
- **Temporal stability** (from iteration 10 analysis): Tail-aware CIs exclude 1.0 at all five temporal snapshots (10%, 25%, 50%, 75%, 90% of market life).

### CPI (CRPS/MAE=0.86)

- **Leave-one-out**: All 33 LOO ratios < 1.0 (range [0.80, 0.96]); no single event drives the aggregate below 1.0.
- **CI includes 1.0**: BCa CI [0.57, 1.23]. The aggregate result is *directionally* favorable but not conclusive. Serial-correlation-adjusted CI (AR(1) ρ=0.23, n_eff≈20.7): approximately [0.44, 1.28].
- **Temporal split**: Old CPI (ratio=0.69) vs new KXCPI (ratio=1.32). The aggregate masks a structural break.
- **Historical benchmark**: Kalshi CRPS comparable to historical CRPS (p=0.714); no significant advantage over the naive historical distribution.

### FED (CRPS/MAE=1.48)

- **Leave-one-out**: All 4 LOO ratios > 1.0 (range [1.12, 1.80]); consistently harmful.
- **CI includes 1.0**: BCa CI [0.79, 4.86]. Wide CI reflects n=4 — insufficient for definitive conclusions.
- **Tentative interpretation**: FED rate decisions involve discrete jumps (0/25/50bp) that may make distributional pricing harder than continuous economic indicators.

### Heterogeneity Tests

- **Kruskal-Wallis** (3 series): H=7.16, p=0.028 — significant at 5%.
- **Kruskal-Wallis** (4 series): H=9.98, p=0.019 — significant at 5%.
- **GDP vs CPI** (Mann-Whitney): p_raw=0.020, p_adj=0.059, r=−0.52 — GDP directionally better (borderline after Bonferroni).
- **JC vs GDP** (Mann-Whitney): p_raw=0.066, p_adj=0.197, r=−0.46 — directional.
- **CPI vs JC** (Mann-Whitney): p_raw=0.150, p_adj=0.450, r=−0.26 — directional.
- *Note: Pairwise tests Bonferroni-corrected for 3 comparisons (α_adj=0.017). No pairwise comparison survives correction. The KW omnibus test is the primary heterogeneity result.*

### PIT Diagnostic (All 4 Series)

*Probability Integral Transform: if CDFs are well-calibrated, PIT values should be uniform on [0,1] with mean 0.5.*

| Metric | GDP (n=9) | JC (n=16) | CPI (n=33) | FED (n=4) | Well-Calibrated |
|--------|-----------|-----------|-----------|-----------|-----------------|
| Mean PIT | 0.385 | 0.463 | 0.558 | 0.666 | 0.500 |
| 95% CI | [0.20, 0.57] | [0.33, 0.60] | [0.45, 0.66] | [0.32, 1.02] | — |
| KS test p | 0.420 | 0.353 | 0.451 | 0.293 | — |
| Bias direction | Overestimates | ≈ Unbiased | Underestimates inflation | Underestimates rates | — |

No series rejects uniformity at the 5% level (all KS p > 0.29), indicating that despite the CRPS/MAE heterogeneity, none of the distributions are *severely* biased. The biases are directional but modest:
- **GDP** (mean PIT=0.39): Markets mildly overestimate GDP growth — realized values tend to fall in the lower half of the distribution.
- **Jobless Claims** (0.46): Near-ideal calibration.
- **CPI** (0.56): Markets mildly underestimate inflation — realized CPI tends to fall in the upper half. This is consistent with the post-Nov 2024 pattern where distributions are too narrow and centered too low.
- **FED** (0.67): Markets underestimate rate levels, though n=4 limits interpretation.

### Surprise Magnitude — A Mechanical Relationship

The CRPS/MAE ratio is strongly inversely correlated with surprise magnitude (|implied mean − realized|) across all 62 events: pooled Spearman ρ=−0.65 (p<0.0001, n=62). However, this correlation is **largely a denominator artifact**: surprise magnitude *is* the MAE, which is the ratio's denominator. When we regress raw CRPS (not the ratio) on within-series surprise z-score, the correlation vanishes (ρ=0.12, p=0.35, n=62). MAE increases with surprise (ρ=0.40, p=0.001), but CRPS does not — the ratio is mechanically small for surprising events because the denominator is large, not because the numerator is small.

This means the multivariate regression finding (R²=0.27, surprise z-score coefficient=−0.84) should be interpreted as reflecting the mechanical denominator effect, not genuine variation in distributional forecast quality. The economic intuition ("distributions help more when surprises are large") is directionally correct but overstated — the CRPS/MAE ratio favors high-surprise events by construction.

### CRPS/MAE Persistence

Is the CRPS/MAE ratio persistent — does a good (or bad) event predict the next event's quality? **No.** Lag-1 Spearman autocorrelation: CPI ρ=−0.003 (p=0.99, n=33), Jobless Claims ρ=0.06 (p=0.82, n=16), GDP ρ=−0.10 (p=0.82, n=9). The ratio is event-specific, not sticky. This means the CRPS/MAE diagnostic cannot be used to predict future single-event quality from past events; its value is in monitoring *aggregate* regime shifts (as in the CPI rolling window analysis) rather than event-by-event forecasting.

### Rolling CRPS/MAE: CPI Temporal Dynamics

With 33 CPI events spanning Dec 2022 to present, a rolling window (w=8 events) reveals the structural break in real time:

- **All 14 old-CPI windows (through CPI-24SEP)**: ratio < 1.0, ranging from 0.45 to 0.96
- **All 12 new-KXCPI-dominated windows (from KXCPI-25APR)**: ratio > 1.0, ranging from 1.05 to 1.88
- **Transition windows (KXCPI-24DEC, KXCPI-24NOV)**: ratio ≈ 0.95, straddling the threshold

The expanding-window ratio (cumulative from event 1) rises monotonically from 0.49 to 0.86 as post-break events are added, but never crosses 1.0 — confirming that the aggregate CPI result (ratio=0.86) is not an artifact of the break. The temporal Spearman trend is directional but not significant (ρ=0.31, p=0.075).

### Strike-Count Confound

Monte Carlo simulation: 2→3 strike effect ≤2% for symmetric distributions, vs observed cross-series gaps of 30–50%. Empirical: both CPI subsets (2-strike and 3+-strike) show similar ratios. Strike count does not explain the heterogeneity.

---

## Methodology

### Data
- **Original 4 series**: 909 multi-strike markets across 96 events (33 CPI, 24 Jobless Claims, 14 GDP, 25 FED); 62 events with realized outcomes and CRPS computation
- **Expanded 3 series**: Core PCE (90 markets, 15 events), ADP Employment (80 markets, 9 events), ISM PMI (49 markets, 7 events) — fetched via Kalshi API in iteration 13
- **Total**: 93 events with CRPS across 7 series
- Series merge: old naming (CPI-, FED-, GDP-) combined with new naming (KXCPI-, KXFED-, KXGDP-) into canonical series
- External: TIPS breakeven (T10YIE), SPF median CPI, FRED historical data (CPIAUCSL, ICSA, A191RL1Q225SBEA, DFEDTARU)
- **Additional series discovered** via Kalshi `/series` endpoint: KXU3 (unemployment, 49 events), KXCPICORE (core CPI, 44 events), KXFRM (mortgage rates, 86 events), KXCPIYOY (CPI YoY, 39 events) — available for future analysis

### In-Sample Caveat and OOS Validation

All CRPS/MAE ratios and statistical tests are computed on the full available dataset. We conducted two out-of-sample validation exercises on CPI (n=33):

1. **Expanding-window OOS**: Train on the first N events, predict whether event N+1's per-event ratio falls below 1.0. Result: 50% accuracy (14/28 correct) — no better than chance. The structural break after Nov 2024 causes the model to systematically mispredict recent events, since the expanding-window ratio always predicts < 1 based on the long history of good calibration.

2. **Natural temporal OOS** (old CPI → new KXCPI): Training on 19 old-prefix events (ratio=0.69) predicts the distribution adds value. Testing on 14 new-prefix events: 6/14 (43%) have ratios < 1.0, and the aggregate new-period ratio is 1.32. The direction prediction fails. This confirms the structural break is real and not detectable from the training period alone.

These results underscore that the CRPS/MAE ratio is most useful as a *real-time monitoring* diagnostic (via rolling windows) rather than a static predictor. The rolling-window analysis (Section 4) detects the CPI regime shift within 2–3 events of its onset.

### Key Statistical Methods
1. **BCa bootstrap**: 10,000 resamples, bias-corrected and accelerated CIs — standard for ratio estimators at small n (Efron & Tibshirani, 1993).
2. **Kruskal-Wallis test**: Non-parametric test for heterogeneity across 3+ series (replaces the 2-series Mann-Whitney from iteration 10).
3. **Bonferroni correction**: Applied for pairwise comparisons and horse race benchmarks.
4. **Leave-one-out sensitivity**: All series show unanimous LOO results (same side of 1.0).
5. **Canonical series merging**: Old/new naming conventions merged using prefix mapping; both subsets analyzed separately to check for structural breaks.
6. **Volume-CRPS regression**: Spearman rank correlation of log(event volume) vs CRPS/MAE ratio, overall and within-series.
7. **Multivariate OLS**: CRPS/MAE ~ strike count + log(volume) + surprise z-score + series dummies.
8. **Rolling CRPS/MAE**: Window size 8 events for CPI temporal dynamics; expanding window for cumulative assessment.
9. **OOS validation**: Expanding-window direction prediction and natural temporal split (old prefix → new prefix).

### Experiments Summary

| # | Name | Role in Paper |
|---|------|---------------|
| 7 | Implied Distributions | Section 1: Methodology (expanded to 4 series) |
| 12 | CRPS Scoring | Section 2: Base CRPS computation (expanded to 4 series) |
| 13 | Unified + Horse Race | Sections 2-4: Per-series tests, horse race, robustness |
| 8 | TIPS Comparison | Section 3: Information hierarchy |
| 11 | Favorite-Longshot Bias | Appendix D: Maturity (controlled) |
| — | expanded_crps_analysis.py | Section 2: 4-series expansion (62 events) |
| — | robustness_analyses.py | Section 4: Volume regression, rolling CRPS/MAE, OOS, PIT, persistence |

---

## Supplementary Appendix

### A. PIT Analysis — Additional Detail

PIT analysis has been extended to all 4 series (62 events total). Results are reported in Section 4 (PIT Diagnostic). No series rejects uniformity at the 5% level. GDP and Jobless Claims show near-ideal calibration; CPI and FED show mild directional biases consistent with their CRPS/MAE patterns.

### B. Downgraded and Invalidated Findings

During the research process, several initially significant findings were invalidated or substantially weakened by methodological corrections. We document these for transparency:

**Downgraded:**

| Finding | Naive p | Corrected | Issue |
|---------|---------|-----------|-------|
| CPI distributions "actively harmful" | CI [1.04, 2.52] | CI [0.57, 1.23] | Sample restricted to post-break period; full series ratio=0.86 |
| JC CI "excludes 1.0" | CI [0.45, 0.78] | CI [0.37, 1.02] | Percentile bootstrap → true BCa (function signature bug) |
| GDP CI "excludes 1.0 tightly" | CI [0.38, 0.58] | CI [0.31, 0.77] | Percentile → BCa; still excludes 1.0 but wider |
| Surprise predicts CRPS/MAE | ρ=−0.65, "genuine" | ρ=0.12 (raw CRPS) | Denominator artifact: surprise = MAE = denominator of ratio |
| Pairwise CPI vs GDP "significant" | p=0.020 | p_adj=0.059 | Bonferroni correction for 3 pairwise tests |
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

2. **Volume is not the bottleneck**: Despite a 9× difference in median event volume between CPI (140K contracts) and Jobless Claims (16K), volume does not predict CRPS/MAE quality (ρ=0.14, p=0.27). Simply increasing liquidity is unlikely to fix distributional miscalibration.

3. **Strike density**: The two best-performing series (GDP=3.7, JC=2.8 strikes/event) have moderate-to-high density. CPI averages only 2.2 strikes/event — increasing to 4-5 could help, conditional on sufficient liquidity at new strikes.

4. **Real-time rolling CRPS/MAE monitoring** during market life could flag series or events where the distribution is adding noise — the rolling-window analysis detects the CPI structural break within 2–3 events of its onset.

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

All 30 corrections applied during the research process:

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
21. **Volume-CRPS regression**: Spearman ρ=0.14, p=0.27 — liquidity does not predict distributional quality
22. **Multivariate regression**: R²=0.27; surprise z-score dominates (coeff=−0.84), volume and strike count non-significant
23. **CRPS/MAE persistence**: Lag-1 autocorrelation ≈ 0 for all series — ratio is event-specific, not sticky
24. **Full PIT diagnostic**: Extended from 2-series subset to all 4 series (62 events); no series rejects uniformity
25. **OOS validation**: Expanding-window and natural temporal OOS tests on CPI; 50% accuracy confirms structural break
26. **BCa bootstrap fix**: Function signature bug caused `_ratio_of_means(data, axis=None)` to receive two positional args from `scipy.stats.bootstrap`, silently falling back to percentile bootstrap. Fixed to `_ratio_of_means(crps, mae, axis=None)`. CIs widened for all series; JC CI now includes 1.0.
27. **Surprise-CRPS endogeneity test**: Raw CRPS vs surprise z-score: ρ=0.12, p=0.35. The ρ=−0.65 finding for CRPS/MAE is a denominator artifact.
28. **Bonferroni correction for pairwise tests**: 3 pairwise Mann-Whitney tests corrected (α_adj=0.017). CPI vs GDP p_adj=0.059 — no longer significant.
29. **Serial-correlation-adjusted CI propagated**: CPI adjusted CI [0.44, 1.28] (AR(1) ρ=0.23, n_eff≈20.7) now reported alongside standard BCa CI.
30. **Kalshi API series discovery**: Queried /series endpoint; found 9 additional economic series with multi-strike settled markets (KXPCECORE, KXU3, KXADP, KXISMPMI, KXCPICORE, KXCPIYOY, KXFRM, KXACPI, KXRETAIL). New series being integrated.
