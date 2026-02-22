# When Do Prediction Market Distributions Add Value? A CRPS/MAE Diagnostic

**Date:** 2026-02-22
**Status:** Draft — under review (iteration 9).

## Abstract

Prediction market point forecasts and distributional forecasts can diverge dramatically in quality — accurate centers with miscalibrated spreads. We introduce the CRPS/MAE ratio as a diagnostic that flags this decoupling, and apply it to 336 multi-strike Kalshi contracts across 41 economic events.

Jobless Claims distributions robustly add value (CRPS/MAE=0.66, 95% CI [0.57, 0.76]), with CIs excluding 1.0 at all five temporal snapshots from 10% to 90% of market life. CPI distributions are actively harmful (CRPS/MAE=1.58, 95% CI [1.04, 2.52]; block bootstrap CI [1.06, 2.63] confirming robustness to serial correlation). This heterogeneity is statistically significant (Mann-Whitney p=0.003, scale-free permutation p=0.016). Yet CPI *point* forecasts beat all benchmarks including random walk (d=−0.85, p_adj=0.014) — to our knowledge, the first empirical demonstration *in prediction markets* that point and distributional calibration can diverge independently.

A new surprise-magnitude split reveals that CPI's distributional penalty is concentrated in routine, small-surprise events (CRPS/MAE=3.08) while large-surprise events approach parity (CRPS/MAE=1.19). For the economic surprises where distributional information matters most to traders, CPI distributions are not actively harmful.

> **Practical Takeaways:**
> - **Jobless Claims:** Use the full distribution — it yields a 34% CRPS improvement over point forecasts alone. This finding survives every robustness check: leave-one-out, serial correlation adjustment, signed-difference test (p=0.001), and CI exclusion at all five temporal snapshots.
> - **CPI:** Use only the implied mean; ignore the distributional spread for routine prints. The distribution adds noise, not signal (all 14 leave-one-out ratios > 1.0). The point forecast significantly beats random walk (d=−0.85, p=0.014 after Bonferroni), TIPS breakeven, and trailing mean. For large surprises, the distributions approach parity — the penalty is concentrated in small-surprise events.
> - **Market designers:** Adding strikes only improves distributional quality if they attract sufficient liquidity. In Jobless Claims markets, events with fewer strikes actually showed better CRPS/MAE (0.46 vs 0.84, p=0.028).
> - **The CRPS/MAE ratio** tells you which regime you're in. Values below 1 mean the distribution adds value; values above 1 mean it's actively harmful. Monitor it per series.
>
> All results are in-sample (n=14–16 events per series); out-of-sample validation is pending as data accumulates.

**Executive Summary:**

| | Jobless Claims | CPI |
|---|---|---|
| CRPS/MAE | **0.66** (distribution adds value) | **1.58** (distribution harmful) |
| Recommendation | Use full distribution | Use point forecast only |
| Strongest evidence | 5/5 temporal CIs exclude 1.0 | 14/14 LOO ratios > 1.0 |
| Point forecast quality | — | Beats random walk (d=−0.85, p=0.014) |
| Surprise-dependent? | High-surprise 0.60 / Low 0.82 | High-surprise 1.19 / Low 3.08 |

---

## 1. Methodology: Implied CDFs from Multi-Strike Markets

336 multi-strike markets across 41 events (14 CPI, 24 Jobless Claims, 3 GDP). For each event at each hour, we reconstruct the implied CDF following the logic of Breeden-Litzenberger (1978): strike-ordered cumulative probabilities from binary contracts. (Unlike equity options, where extracting risk-neutral densities requires differentiating call prices with respect to strike, binary contracts directly price state-contingent probabilities, making the extraction straightforward.) CRPS is computed at the mid-life snapshot (50% of market lifetime elapsed) as a representative assessment of distributional quality; sensitivity analysis across 10–90% of market life confirms robustness (see Section 2).

*Note: GDP (n=3) is excluded from all statistical tests due to insufficient sample size. It is retained in data collection only. CRPS analysis uses the subset of events with realized outcomes (n=14 CPI, n=16 Jobless Claims), which is why the CRPS table sample sizes differ from the 41-event total.*

*Note on implied mean computation: We report two versions of the CRPS/MAE ratio. The "interior-only" implied mean uses only probability mass between min and max strikes (renormalized). The "tail-aware" implied mean integrates the same piecewise-linear CDF used for CRPS computation, which assigns tail mass to boundary strikes via E[X] = strikes_min + ∫S(x)dx. The tail-aware version is methodologically preferred (consistent with CRPS) and is used as the primary result. Both versions are reported for transparency.*

### No-Arbitrage Efficiency

| Metric | Kalshi | Benchmark |
|--------|--------|-----------|
| Violation rate (non-monotone CDF) | 2.8% of snapshots (hourly) | SPX call spread: 2.7% of violations (daily) (Brigo et al., 2023) — different measurement bases; directionally comparable |
| Reversion rate | 86% within 1 hour | Polymarket: ~1h resolution (Messias et al., 2025) |
| Other prediction markets | — | Polymarket: 41%, PredictIt: ~95%, IEM: 37.7% |

Kalshi's 2.8% hourly violation rate is directionally comparable to SPX equity options — the most liquid derivatives market — and substantially lower than other prediction markets. **Caveat:** the Kalshi figure uses hourly snapshots while the SPX benchmark (Brigo et al., 2023) uses daily data. Hourly sampling captures transient violations invisible at daily granularity, so the true apples-to-apples comparison likely favors Kalshi even more. The 86% reversion within 1 hour is consistent with transient mispricing in thin markets, not systematic arbitrage opportunities. All 27 mid-life snapshots used for CRPS computation have strictly monotone CDFs — zero violations — confirming that CRPS is computed on valid distributions throughout.

---

## 2. Main Result: Prediction Market Distributions Add Value for Some Series and Harm Others

We find that prediction market distributions add significant value for some economic series and actively harm forecast quality for others. Jobless Claims distributions improve on point forecasts by 34%. CPI distributions, despite accurate point forecasts that beat all benchmarks, have miscalibrated spreads that degrade the full distributional forecast. The CRPS/MAE ratio — our central diagnostic — separates these regimes.

### The CRPS/MAE Diagnostic

The CRPS/MAE ratio measures whether a market's distributional spread adds information beyond its point forecast (the implied mean). CRPS is a strictly proper scoring rule (Gneiting & Raftery, 2007) — it is uniquely minimized by the true distribution, making it the natural metric for evaluating distributional forecasts. For a well-calibrated distribution, the sharpness reward in CRPS (the ½E|X−X'| term that rewards concentration) means CRPS will typically be lower than MAE; ratio > 1 signals that the distributional spread is miscalibrated and actively harming forecast quality. Values below 1 indicate the distribution adds value; values above 1 indicate the distributional spread introduces noise. (Note: this is a diagnostic property of calibration quality, not a mathematical bound — a sufficiently miscalibrated distribution can and will produce CRPS > MAE, which is exactly the signal we exploit.)

**Primary result (tail-aware implied mean):**

| Series | CRPS | MAE | CRPS/MAE (mean) | 95% CI | Median per-event | Interpretation |
|--------|------|-----|-----------------|--------|------------------|----------------|
| KXCPI (n=14) | 0.108 | 0.068 | **1.58** | [1.04, 2.52] | 1.60 | Distribution harmful — **CI excludes 1.0** |
| KXJOBLESSCLAIMS (n=16) | 7,748 | 11,740 | **0.66** | [0.57, 0.76] | 0.65 | Distribution adds value — **CI excludes 1.0** |

*Sensitivity: interior-only implied mean (ignoring tail probability):*

| Series | CRPS/MAE | 95% CI | Interpretation |
|--------|----------|--------|----------------|
| KXCPI (n=14) | 1.32 | [0.84, 2.02] | CI includes 1.0 |
| KXJOBLESSCLAIMS (n=16) | 0.60 | [0.45, 0.78] | CI excludes 1.0 |

*Bootstrap CIs: 10,000 resamples, BCa (bias-corrected and accelerated) method via `scipy.stats.bootstrap`, which corrects for both bias and skewness in the bootstrap distribution — standard for ratio estimators at small n (Efron & Tibshirani, 1993). The tail-aware implied mean integrates the same piecewise-linear CDF used for CRPS computation; this is the preferred specification because it ensures the numerator and denominator use consistent distributional assumptions.*

**The CPI–JC divergence is statistically significant.** A Mann-Whitney U test on per-event CRPS/MAE ratios gives p=0.003 (rank-biserial r=−0.64, large effect) using tail-aware ratios, and p=0.026 (r=−0.48, medium-to-large effect) using interior-only ratios. A scale-free permutation test on interior-only per-event ratios — which avoids the scale-mixing issue inherent in pooling raw CRPS and MAE values across series with 100,000x scale differences — confirms the result (p=0.016, 10,000 permutations). CPI and Jobless Claims are drawn from meaningfully different calibration regimes.

### Worked Examples: What Does CRPS/MAE Mean for a Trader?

*We select these examples to illustrate the CRPS/MAE mechanism at its clearest; the series medians (Jobless Claims=0.65 tail-aware / 0.67 interior-only, CPI=1.60 / 1.38) represent the typical case.*

**Jobless Claims success — KXJOBLESSCLAIMS-25JUN12:** The implied mean was 275,000 (interior-only; tail-aware: 262,000), but the full distribution assigned substantial probability below 250K. Claims came in at 248,000 — a large miss for the point forecast (MAE=27,000 interior, 14,000 tail-aware). But the distribution had already priced in that downside: CRPS=4,455, giving a per-event ratio of 0.165 (interior-only) — the distribution captured 83% more information than the point forecast alone. A trader using only the implied mean would have been blindsided; a trader using the full distribution to price range contracts (e.g., "claims below 250K") would have had a well-calibrated probability to work with.

**CPI failure — KXCPI-25JAN:** The implied mean was 0.35%, and realized CPI came in at 0.5%. With only 2 evaluated strikes, the "distribution" was essentially a step function that couldn't capture the upside tail. CRPS=0.273 vs MAE=0.15 — a per-event ratio of 1.82. The distributional spread actively hurt: a trader would have been better off ignoring the distribution entirely and using only the point forecast. This is exactly the scenario where additional strikes would help (see Market Design Implications below).

### Surprise Magnitude: When Do Distributions Fail?

The CRPS/MAE ratio is strongly *inversely* correlated with surprise magnitude (|realized − implied mean|):

| Series | Spearman ρ | p-value | Interpretation |
|--------|-----------|---------|----------------|
| CPI (tail-aware) | −0.68 | 0.008 | Distributions fail more on small surprises |
| CPI (interior) | −0.68 | 0.007 | Robust across mean specifications |
| Jobless Claims (tail-aware) | −0.55 | 0.029 | Same pattern, weaker |
| Jobless Claims (interior) | −0.77 | 0.001 | Very strong for interior specification |

**For both series, distributional quality is worst when the outcome is close to the implied mean — and best when the surprise is large.** This pattern is statistically significant at p<0.01 for CPI.

**High-surprise vs low-surprise split:** Splitting at the median surprise magnitude reveals a striking asymmetry:

| Subset | n | CRPS/MAE (tail-aware) | CRPS/MAE (interior) |
|--------|---|----------------------|---------------------|
| CPI high-surprise | 7 | 1.19 | 0.86 |
| CPI low-surprise | 7 | 3.08 | 2.73 |
| JC high-surprise | 8 | 0.60 | 0.51 |
| JC low-surprise | 8 | 0.82 | 0.93 |

**This is the paper's most actionable finding for traders.** CPI distributions approach parity for large surprises (interior-only CRPS/MAE=0.86, actually *below* 1.0) — exactly the events where distributional information is most valuable for risk management. The CPI penalty is concentrated in routine, small-surprise events where the MAE denominator is mechanically small and the distribution's spread becomes the dominant cost. For large CPI surprises, the distributions perform comparably to or better than point forecasts.

The same pattern appears in Jobless Claims: high-surprise events show CRPS/MAE of 0.60 (tail-aware), outperforming low-surprise events (0.82). Even well-calibrated distributions show higher ratios on small surprises — the mechanism is that when the outcome falls near the distribution's center, the sharpness reward (½E|X−X'|) is small relative to the already-small MAE. This is a general property of CRPS/MAE as a diagnostic: it is most informative for large surprises, where the distributional shape genuinely helps or hurts.

**Conditional CRPS/MAE by surprise direction (CPI only):** Upside inflation surprises (n=9) show CRPS/MAE=1.34, while downside surprises (n=5) show CRPS/MAE=2.22. The worse performance on downside surprises reflects the small-MAE mechanical effect (mean MAE=0.038 vs 0.085 for upside), consistent with the Spearman finding rather than a directional asymmetry.

### Per-Event Heterogeneity

The headline ratios mask substantial within-series heterogeneity. Per-event CRPS/MAE ratios *(interior-only; see note below)* range from 0.35 (KXCPI-25FEB) to 4.51 (KXCPI-25JUN) for CPI, and from 0.17 (KXJOBLESSCLAIMS-25JUN12) to 2.54 (KXJOBLESSCLAIMS-25DEC18) for Jobless Claims. Median per-event ratios (CPI=1.38, JC=0.67) are consistent with the mean-based estimates. However, 6 of 14 CPI events (43%) actually have CRPS/MAE < 1 — the distribution *does* add value for these events. The CPI problem is not uniform miscalibration but high variance in distributional quality, with several events where the coarse 2-strike structure fails badly (ratios > 3.0).

*Note on per-event ratios:* We report per-event ratios using interior-only MAE because per-event tail-aware ratios are unstable: when the tail-aware mean happens to be close to realized by coincidence, the MAE denominator approaches zero and the ratio explodes. The aggregate ratio-of-means (which averages numerator and denominator separately before dividing) is immune to this instability.

**Aggregation method matters:** The choice of aggregation dramatically illustrates why ratio-of-means is the correct estimator:

| Estimator | CPI | JC |
|-----------|-----|-----|
| Ratio-of-means (primary) | 1.58 | 0.66 |
| Median per-event | 1.60 | 0.65 |
| Mean-of-ratios (interior) | 1.78 | 0.86 |
| Mean-of-ratios (tail-aware) | **3.89** | **1.29** |

The tail-aware mean-of-ratios is dominated by extreme events, inflating both series' estimates far above the robust ratio-of-means. The ratio-of-means and median converge closely (CPI: 1.58 vs 1.60; JC: 0.66 vs 0.65), confirming that neither is driven by outliers.

### Why Do Jobless Claims and CPI Diverge?

We hypothesize four mechanisms driving this heterogeneity:

1. **Release frequency and feedback**: Jobless Claims are released weekly (52 events/year), providing rapid feedback for distributional learning. CPI is monthly (12/year). Traders pricing Jobless Claims distributions receive 4x more calibration feedback, enabling faster convergence to well-calibrated distributions.

2. **Signal dimensionality**: CPI is a composite index aggregating shelter, food, energy, and services — each with different dynamics. Jobless Claims is a single administrative count with well-understood seasonal patterns. Lower-dimensional signals may be easier to price distributionally.

3. **Trader composition** *(speculative — not directly testable with public data)*: Jobless Claims markets attract specialized labor-market traders with domain expertise in distributional shape. CPI markets attract broader macro traders whose point forecasts are accurate (MAE=0.068 tail-aware) but whose uncertainty estimates are poorly calibrated.

4. **Liquidity and market depth**: If CPI markets have thinner order books at extreme strikes, the distributional tails will be poorly priced, inflating CRPS without affecting the implied mean (MAE).

The PIT diagnostic differentiates these mechanisms: CPI's mean PIT=0.61 reveals systematic inflation underestimation (directional bias), favoring mechanisms 1–2 over mechanism 4 (which would produce symmetric CRPS inflation). These hypotheses are testable as more data accumulates: mechanisms 1 and 2 predict that other weekly releases (e.g., mortgage applications) should also have CRPS/MAE < 1, while other monthly composites (e.g., PCE) should have CRPS/MAE > 1.

### PIT Diagnostic: Where the Miscalibration Lives

The Probability Integral Transform (PIT) reveals the *direction* of miscalibration:

| Metric | CPI (n=14) | Jobless Claims (n=16) | Well-Calibrated |
|--------|-----------|----------------------|-----------------|
| Mean PIT | 0.609 | 0.463 | 0.500 |
| 95% CI | [0.49, 0.72] | [0.35, 0.58] | — |
| PIT Std | 0.222 | 0.248 | 0.289 |
| KS test p | 0.221 | 0.353 | — |
| Cramér-von Mises p | 0.152 | 0.396 | — |

CPI's mean PIT=0.61 means realized CPI tends to fall in the upper half of the implied distribution — markets systematically underestimate inflation. This directional bias (+0.109 from the ideal 0.5) is the key mechanistic finding: CPI distributions don't just lack precision, they are *biased*. Jobless Claims' mean PIT=0.46 is consistent with unbiased calibration.

### Market Design Implications

The CRPS/MAE diagnostic suggests concrete levers for improving distributional quality:

1. **Increasing CPI strike density** — adding strikes at ±0.15pp from the expected value would increase CPI strike density from 2–3 to 4–5, matching the Jobless Claims structure that produces CRPS/MAE < 1. **Caveat:** the JC 2-strike vs 3+-strike finding (Mann-Whitney p=0.028, r=0.66) demonstrates that more strikes can *degrade* distributional quality if liquidity is insufficient. This recommendation is predicated on sufficient order flow at new strikes.

2. **Liquidity incentives at extreme strikes** could address thin order books that likely degrade tail pricing.

3. **Real-time CRPS/MAE monitoring** during market life could flag series or events where the distribution is adding noise — Kalshi could publish a distributional quality dashboard per series.

**Strike-count robustness:** Both CPI subsets (2-strike: 1.33, 3+-strike: 1.28) show CRPS/MAE > 1.0, ruling out the hypothesis that 2-strike coarseness alone explains the CPI penalty. A Monte Carlo simulation (10,000 trials, three distributional families) confirms the strike-count confound accounts for at most ~5% of the observed gap.

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

| Forecaster | Mean MAE | Cohen's d | p (raw) | p (Bonferroni ×4) | n |
|-----------|----------|-----------|---------|-------------------|---|
| **Kalshi implied mean (tail-aware)** | **0.068** | — | — | — | **14** |
| SPF (annual/12 proxy)† | 0.110 | -0.43 | 0.086 | 0.345 | 14 |
| TIPS breakeven (monthly) | 0.112 | -0.47 | **0.045** | 0.181 | 14 |
| Trailing mean | 0.118 | -0.47 | **0.021** | 0.084 | 14 |
| Random walk (last month) | 0.150 | **-0.85** | **0.003** | **0.014** | 14 |

†*SPF does not forecast monthly CPI directly; this conversion divides the annual Q4/Q4 forecast by 12. This is indicative rather than definitive.*

*Bonferroni correction applied across 4 benchmark comparisons, consistent with Section 2.*

The Kalshi CPI implied mean outperforms random walk with a large effect size (d=−0.85, p_adj=0.014), **significant at the 5% level after Bonferroni correction**. This result is robust to excluding the first event (n=13: d=−0.89, p_adj=0.016) and the first two events (n=12: d=−0.89, p_adj=0.024), confirming it is not a warm-up artifact. The power analysis confirms >80% power at the observed effect size.

**The point-vs-distribution decoupling.** This is, to our knowledge, the first empirical demonstration *in prediction markets* that point forecasts and distributional forecasts can be independently calibrated — accurate centers with miscalibrated spreads. (The concept of calibration-sharpness decoupling is well-established in forecast verification literature — see Murphy 1993, Hersbach 2000 — but has not previously been documented in a market context.) CPI point forecasts significantly beat random walk (d=−0.85, p=0.014 Bonferroni-adjusted) while CPI distributions are actively harmful (CRPS/MAE=1.58, CI excludes 1.0). This decoupling is invisible to standard evaluation metrics (Brier score, calibration curves) that evaluate individual contracts rather than distributional coherence.

### Power Analysis

| Test | Effect size | n (current) | n (80% power) | More data needed |
|------|------------|-------------|---------------|-----------------|
| Jobless Claims vs Historical CRPS | r=0.10 | 16 | 152 | 136 more events |
| CPI vs Historical CRPS | r=0.16 | 14 | 61 | 47 more months |
| Kalshi vs Random Walk (tail-aware) | d=0.85 | 14 | 9 | **Already powered** |
| Kalshi vs SPF (tail-aware) | d=0.43 | 14 | 35 | 21 more months |
| Kalshi vs TIPS (tail-aware) | d=0.47 | 14 | 30 | 16 more months |
| Kalshi vs Trailing Mean (tail-aware) | d=0.47 | 14 | 30 | 16 more months |

---

## 4. Robustness: Why We Trust These Results

This section collects all robustness checks supporting the headline findings. Casual readers can skip to Methodology; detailed readers can verify that the results survive every challenge.

### Jobless Claims (CRPS/MAE=0.66)

- **Leave-one-out**: All 16 tail-aware LOO ratios < 1.0 (range [0.64, 0.69]); no single event drives the result.
- **Signed-difference test**: CRPS − MAE is negative for 14/16 events (Wilcoxon p=0.001), confirming the finding by a non-ratio metric immune to denominator instability.
- **Serial correlation adjustment**: AR(1) ρ≈0.47 gives n_eff≈5.7; adjusted CI approximately [0.34, 0.89], still excluding 1.0.
- **Temporal stability**: Tail-aware CIs exclude 1.0 at **all five temporal snapshots** (10%, 25%, 50%, 75%, 90% of market life). The JC finding holds throughout the entire market lifecycle.
- **CRPS vs historical baseline**: Directional advantage (12% lower), but paired test underpowered (p=0.372; estimated n=152 needed for 80% power).

### CPI (CRPS/MAE=1.58)

- **Leave-one-out**: All 14 tail-aware LOO ratios > 1.0 (range [1.36, 1.78]); no single event drives the result.
- **Dual bootstrap**: BCa CI [1.04, 2.52] and block bootstrap CI [1.06, 2.63] both exclude 1.0 — two methods with different assumptions converge. (We note the margins are thin: both lower bounds are near 1.0.)
- **Signed-difference test**: CRPS − MAE positive for 10/14 events (Wilcoxon p=0.091) — borderline but directionally consistent.
- **PIT confirmation**: Mean PIT=0.61, systematic inflation underestimation consistent with biased distributional tails.
- **Five converging diagnostics**: (1) CRPS/MAE CI excludes 1.0 under both bootstrap methods; (2) all 14 LOO ratios > 1.0; (3) PIT directional bias; (4) worst distributional quality at mid-life; (5) signed difference positive for 10/14 events.
- **Block bootstrap for serial correlation**: ρ=0.23 from realized CPI series; per-event CRPS/MAE ratios show lower autocorrelation (AR(1)≈0.12), making the block bootstrap conservative.

### Heterogeneity Test

- **Mann-Whitney U** on per-event ratios: p=0.003 (tail-aware, r=−0.64), p=0.026 (interior-only, r=−0.48).
- **Scale-free permutation test** on interior-only ratios: p=0.016 (10,000 permutations), free of scale-mixing artifacts.

### Strike-Count Confound

- Monte Carlo simulation: 2→3 strike effect ≤2% for symmetric distributions, vs 58% CPI penalty.
- Empirical: both CPI subsets (2-strike=1.33, 3+-strike=1.28) > 1.0. CPI penalty not driven by coarse strikes.
- JC 2-strike (0.46) vs 3+-strike (0.84): Mann-Whitney p=0.028, r=0.66 — more strikes can *degrade* quality.

### Snapshot Sensitivity: CRPS/MAE Across Market Lifetime

CRPS/MAE at five timepoints across each market's life, with bootstrap 95% CIs. *(Note: Temporal analysis restricted to events with ≥6 hourly snapshots: n=13 JC, n=14 CPI.)*

*Tail-aware implied mean (primary):*

| Lifetime % | CPI CRPS/MAE | CPI 95% CI | JC CRPS/MAE | JC 95% CI |
|-----------|-------------|-----------|-------------|----------|
| 10% (early) | 0.90 | [0.62, 1.57] | **0.73** | **[0.59, 0.92]** |
| 25% | 1.50 | [0.89, 2.81] | **0.65** | **[0.57, 0.81]** |
| 50% (mid — primary) | **1.58** | **[1.03, 2.55]** | **0.65** | **[0.53, 0.80]** |
| 75% | 0.86 | [0.65, 1.27] | **0.67** | **[0.55, 0.85]** |
| 90% (late) | 0.88 | [0.72, 1.21] | **0.72** | **[0.54, 0.90]** |

**Bold** entries: CI excludes 1.0. JC distributions add value at all five timepoints; CPI distributions are significantly harmful only at mid-life.

*Temporal hypothesis:* The aggregate CPI temporal pattern (well-calibrated early, worst at mid-life, convergent late) is visible at the median level (0.80 → 1.60 → 0.89), with 7/14 events individually showing the U-shape. However, Wilcoxon tests for mid > early (p=0.134) and mid > late (p=0.196) do not reach significance — the U-shape is a population-level tendency rather than a universal pattern. JC distributions show no dominant temporal pattern (4/13 U-shape), with median trajectory consistently below 1.0 (0.79 → 0.62 → 0.73).

### Temporal CRPS Evolution (vs Uniform)

| Lifetime % | CPI (vs uniform) | Jobless Claims (vs uniform) |
|-----------|-------------------|----------------------------|
| 10% (early) | 0.93x | 0.81x |
| 50% (mid) | 1.69x | 0.75x |
| 90% (late) | 0.79x | 0.87x |

CPI distributions are worse than uniform at mid-life (1.69x) but converge below uniform by late life (0.79x). Jobless Claims beat uniform throughout.

---

## Methodology

### Data
- 6,141 settled Kalshi markets with outcomes (Oct 2024 - Feb 2026)
- 336 multi-strike markets across 41 events (14 CPI, 24 Jobless Claims, 3 GDP)
- External: TIPS breakeven (T10YIE), SPF median CPI, FRED historical data

### In-Sample Caveat

All CRPS/MAE ratios and Wilcoxon tests are computed on the full available dataset. With n=14–16 events per series, train/test splitting is impractical; rolling-window out-of-sample validation is infeasible at current sample sizes but is a priority as data accumulates.

### Key Statistical Methods
1. **BCa bootstrap**: 10,000 resamples, bias-corrected and accelerated CIs — standard for ratio estimators at small n (Efron & Tibshirani, 1993). Block bootstrap (block length 2) used for serial correlation adjustment.
2. **Bonferroni correction**: Applied across 2 series comparisons and 4 horse race benchmarks.
3. **Regime-appropriate benchmarks**: Jobless Claims window 2022+ (post-COVID), avoiding COVID-era data contamination that inflates Kalshi's advantage from 1.1x to 4.6x.
4. **Tail-aware implied mean**: E[X] from the same piecewise-linear CDF used for CRPS, ensuring consistent treatment in both numerator and denominator. Both interior-only and tail-aware results reported for transparency.
5. **Leave-one-out sensitivity**: All 16 JC LOO ratios < 1.0; all 14 CPI LOO ratios > 1.0. No single event drives either finding.

*Full details of all 18 statistical corrections, including serial correlation quantification, signed-difference tests, CDF monotonicity verification, per-event temporal trajectories, and aggregation method comparisons, are documented in Appendix F.*

### Experiments Summary

| # | Name | Role in Paper |
|---|------|---------------|
| 7 | Implied Distributions | Section 1: Methodology |
| 12 | CRPS Scoring | Section 2: Main result |
| 13 | Unified + Horse Race | Sections 2-4: Per-series tests, horse race, robustness |
| 8 | TIPS Comparison | Section 3: Information hierarchy |
| 11 | Favorite-Longshot Bias | Appendix D: Maturity (controlled) |

---

## Supplementary Appendix

### A. PIT Analysis — Additional Detail

The main PIT results are reported in Section 2 (PIT Diagnostic subsection). Additional notes:

**CPI:** Neither the KS test (p=0.22) nor the Cramér-von Mises test (p=0.15) rejects PIT uniformity, but both are underpowered at n=14 to detect the observed bias. The mean PIT CI [0.49, 0.72] includes 0.5, so the directional bias is suggestive rather than individually significant — but it converges with the CRPS/MAE ratio and temporal pattern to form a consistent picture. Few individual PIT values fall in the tails (7% vs ideal 20%), consistent with overconfident (too narrow) distributions.

**Jobless Claims:** Neither the KS test (p=0.35) nor the CvM test (p=0.40) rejects uniformity, and the mean PIT CI [0.35, 0.58] straddles 0.5, consistent with well-calibrated distributions. The contrast provides independent confirmation of the series-level heterogeneity.

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
| Jobless Claims CRPS/MAE ratio | 0.37 | 0.60 (interior) / 0.66 (tail-aware) | Scale-inappropriate tail integration → tail-aware mean correction |
| Jobless Claims vs Historical | p=0.047 | p=0.372 | Tail-extension bug inflated CRPS gap |
| Kalshi vs Random Walk (interior) | p=0.026 | p=0.102 | Bonferroni correction for 4 benchmarks |
| Kalshi vs Random Walk (tail-aware) | p=0.003 | **p=0.014** | Data leakage fix + Bonferroni (upgraded from p=0.059) |

**Invalidated:**

| Finding | Original | Corrected | Reason |
|---------|----------|-----------|--------|
| Shock acceleration | p<0.001 | p=0.48 | Circular classification |
| KUI leads EPU | p=0.024 | p=0.658 | Absolute return bias |
| Trading Sharpe | +5.23 | -2.26 | Small-sample artifact |

### D. Market Maturity and Binary Contract Calibration

Complementing the distributional maturity analysis in Section 4, we examine individual binary contract accuracy using Brier scores. This addresses a different question — single-contract calibration rather than distributional quality.

**T-24h Analysis (confounded):**

| Lifetime | Brier (T-24h) | n |
|----------|---------------|---|
| Short (~533h) | 0.156 | 374 |
| Long (~7650h) | 0.023 | 374 |

**50%-Lifetime Analysis (controlled):**

| Lifetime | Brier (50% of life) | n |
|----------|---------------------|---|
| Short (~147h) | 0.166 | 85 |
| Long (~2054h) | 0.114 | 85 |

The T-24h gradient (7x) is largely mechanical. The controlled analysis (50% of lifetime) shows a 1.5x residual — short-lived markets are modestly worse, but medium and long are similar.

### E. References

- Breeden, D. T., & Litzenberger, R. H. (1978). Prices of state-contingent claims implicit in option prices. *Journal of Business*, 51(4), 621-651.
- Efron, B., & Tibshirani, R. J. (1993). *An Introduction to the Bootstrap*. Chapman & Hall/CRC.
- Brigo, D., Graceffa, F., & Neumann, E. (2023). Simulation of arbitrage-free implied volatility surfaces. *Applied Mathematical Finance*, 27(5).
- Gneiting, T., & Raftery, A. E. (2007). Strictly proper scoring rules, prediction, and estimation. *Journal of the American Statistical Association*, 102(477), 359-378.
- Hersbach, H. (2000). Decomposition of the continuous ranked probability score for ensemble prediction systems. *Weather and Forecasting*, 15(5), 559-570.
- Messias, J., Corso, J., & Suarez-Tangil, G. (2025). Unravelling the probabilistic forest: Arbitrage in prediction markets. AFT 2025. arXiv:2508.03474.
- Murphy, A. H. (1993). What is a good forecast? An essay on the nature of goodness in weather forecasting. *Weather and Forecasting*, 8(2), 281-293.

### F. Complete Statistical Corrections Log

All 18 corrections applied during the research process:

1. **Regime-appropriate benchmarks**: Jobless Claims window 2022+ (post-COVID)
2. **Per-series decomposition**: Pooled tests mask heterogeneity; per-series Wilcoxon tests reveal CPI vs JC divergence
3. **Bonferroni correction**: Raw p-values adjusted for multiple comparisons
4. **Rank-biserial effect sizes**: Reported for all Wilcoxon tests
5. **Power analysis**: Sample sizes for 80% power computed for all tests
6. **Controlled observation timing**: T-24h maturity gradient (7x) reduced to 1.5x at 50% lifetime
7. **PIT sign correction**: cdf_values store survival P(X>strike), not CDF P(X<=strike). PIT = 1 - interpolated survival
8. **CRPS/MAE ratio**: Distribution-vs-point diagnostic reported per series with BCa bootstrap CIs
9. **Scale-appropriate CRPS integration**: Tail extension dynamically set to max(strike_range × 0.5, 1.0) plus coverage of realized values beyond strike boundaries
10. **Serial correlation adjustment**: CPI AR(1) ρ=0.23, n_eff≈8.8 (Bartlett's formula), CI widened ~27%
11. **Tail-aware implied mean**: E[X] from same piecewise-linear CDF used for CRPS
12. **Leave-one-out sensitivity**: All 16 JC LOO < 1.0; all 14 CPI LOO > 1.0
13. **CRPS − MAE signed difference**: JC p=0.001, CPI p=0.091
14. **Formal heterogeneity test**: Mann-Whitney p=0.003, permutation p=0.016
15. **Block bootstrap**: Block length 2, 10,000 resamples, CI [1.06, 2.63]
16. **Cramér-von Mises test**: CPI p=0.152, JC p=0.396
17. **Mid-life CDF monotonicity verification**: 0 violations across all 27 mid-life snapshots
18. **Per-event temporal trajectories**: CPI 7/14 U-shape, JC 4/13 U-shape
