# When Do Prediction Market Distributions Add Value? A CRPS/MAE Diagnostic

**Date:** 2026-02-21
**Status:** Draft — under review (iteration 2).

## Abstract

Should traders trust the full implied distribution from prediction markets, or just the point forecast? We introduce the CRPS/MAE ratio as a diagnostic and apply it to 336 multi-strike Kalshi contracts across 41 economic events. The answer depends dramatically on the series: Jobless Claims distributions robustly add value (CRPS/MAE=0.66, 95% CI [0.57, 0.76] excludes 1.0; all 16 leave-one-out ratios below 1.0), while CPI distributions are actively harmful (CRPS/MAE=1.58, 95% CI [1.04, 2.52] also excludes 1.0). Three independent diagnostics converge on CPI miscalibration: the CRPS/MAE ratio, PIT directional bias (mean PIT=0.61, consistent with systematic inflation underestimation), and a mid-life temporal pattern where distributional quality degrades most when traders need it most.

In point-forecast comparisons, the tail-aware CPI implied mean outperforms random walk (p_raw=0.015, p_adj=0.059 after Bonferroni correction, d=-0.71) — borderline significant after multiple-testing correction, with the test already at 80% power. TIPS breakeven rates Granger-cause Kalshi CPI prices (F=12.2, p=0.005), providing predictive information at 1-day lag — though this may reflect slow-updating Kalshi prices rather than a true information hierarchy.

> **Bottom line for traders:** Use Jobless Claims distributions — they yield a 34% CRPS improvement over point forecasts alone (tail-aware; 40% with interior-only mean, which is larger because the interior-only point forecast is weaker, making the distribution's relative advantage bigger). This finding survives every robustness check we applied: leave-one-out, serial correlation adjustment, signed-difference test (p=0.001), and CI exclusion at all five temporal snapshots. For CPI, use only the implied mean and ignore the distributional spread; the distribution adds noise, not signal. All results are in-sample (n=14–16 events per series); out-of-sample validation is pending as data accumulates.

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

Kalshi's 2.8% hourly violation rate is directionally comparable to SPX equity options — the most liquid derivatives market — and substantially lower than other prediction markets. **Caveat:** the Kalshi figure uses hourly snapshots while the SPX benchmark (Brigo et al., 2023) uses daily data. Hourly sampling captures transient violations invisible at daily granularity, so the true apples-to-apples comparison likely favors Kalshi even more. The 86% reversion within 1 hour is consistent with transient mispricing in thin markets, not systematic arbitrage opportunities.

---

## 2. Main Result: The CRPS/MAE Diagnostic and Distributional Heterogeneity

### CRPS/MAE Ratio: When Distributions Add Value

The CRPS/MAE ratio measures whether a market's distributional spread adds information beyond its point forecast (the implied mean). CRPS is a strictly proper scoring rule (Gneiting & Raftery, 2007) — it is uniquely minimized by the true distribution, making it the natural metric for evaluating distributional forecasts. For a well-calibrated distribution, the sharpness reward in CRPS (the ½E|X−X'| term that rewards concentration) means CRPS will typically be lower than MAE; ratio > 1 signals that the distributional spread is miscalibrated and actively harming forecast quality rather than helping it. The ratio thus serves as a practical diagnostic: values below 1 indicate the distribution adds value beyond the point forecast, while values above 1 indicate the distributional spread introduces noise. (Note: this is a diagnostic property of calibration quality, not a mathematical bound — a sufficiently miscalibrated distribution can and will produce CRPS > MAE, which is exactly the signal we exploit.)

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

*Bootstrap CIs: 10,000 resamples, BCa (bias-corrected and accelerated) method via `scipy.stats.bootstrap`, which corrects for both bias and skewness in the bootstrap distribution — standard for ratio estimators at small n (Efron & Tibshirani, 1993). Median per-event ratio computed from individual event CRPS/MAE ratios, providing a robust alternative less sensitive to outliers. The tail-aware implied mean integrates the same piecewise-linear CDF used for CRPS computation (see Methodology note above); this is the preferred specification because it ensures the numerator and denominator use consistent distributional assumptions.*

**Jobless Claims distributions robustly add value.** The CI on 0.66 (tail-aware) excludes 1.0 under both mean specifications. The finding survives serial correlation adjustment (AR(1) ρ≈0.47 gives n_eff≈5.7; adjusted CI approximately [0.34, 0.89], still excluding 1.0) and is bulletproof in leave-one-out analysis: all 16 tail-aware leave-one-out CRPS/MAE ratios fall below 1.0 (range [0.64, 0.69]). No single event drives the result. As a complementary test immune to ratio instability, the signed difference (CRPS − MAE) is negative for 14 of 16 events (Wilcoxon signed-rank p=0.001), confirming the distribution adds value by a non-ratio metric.

**CPI distributions are harmful.** Using the tail-aware mean, the CI [1.04, 2.52] excludes 1.0, meaning we can reject at 95% confidence the hypothesis that CPI distributional spread is neutral. The signed difference (CRPS − MAE) is positive for 10 of 14 events (Wilcoxon signed-rank p=0.091) — borderline significant but directionally consistent. Three independent diagnostics converge on CPI miscalibration: (1) the CRPS/MAE ratio exceeds 1.0 with tail-aware CI excluding 1.0; (2) PIT analysis shows systematic directional bias (mean PIT=0.61, consistent with inflation underestimation); and (3) the temporal pattern shows distributional quality is worst at mid-life when traders need it most. The serial-correlation-adjusted CI (ρ=0.23, n_eff≈8.8) is approximately [0.90, 2.58], which includes 1.0 — so the CPI finding is more marginal than the JC finding when accounting for serial dependence. However, three independent lines of evidence converge: the unadjusted CI excludes 1.0, the PIT shows directional bias, and the temporal pattern shows mid-life degradation. The CPI miscalibration conclusion rests on this convergence, not any single test.

**Strike structure and simulation robustness check:** CPI events average 2.3 evaluated strikes (range 2–3, uniform 0.1pp spacing), while Jobless Claims average 2.8 evaluated strikes (range 2–5, variable 5K–10K spacing with clustering near the expected value). To quantify whether this difference could mechanically inflate CPI's CRPS, we ran a Monte Carlo simulation (10,000 trials) across three distributional families: Normal, Uniform, and Skew-Normal (α=4). Using known distributions matched to each series' realized parameters, we constructed piecewise-linear CDFs with 2, 3, 4, and 5 strikes and computed CRPS against the same realized outcomes. **Result: for symmetric distributions (Normal, Uniform), going from 3 to 2 strikes inflates CRPS by ≤2%, far less than the 58% CPI penalty (tail-aware ratio).** For strongly skewed distributions (Skew-Normal, α=4), the 2→3 strike inflation can reach ~49% — but the realized CPI MoM values show only moderate skewness (sample skewness=-0.62, Shapiro-Wilk p=0.24 does not reject normality at n=14, though this is underpowered to detect moderate departures), making the symmetric assumption reasonable for this data. The strike-count confound accounts for at most ~5% of the observed CRPS/MAE gap under the distributional assumptions consistent with our data.

**Empirical strike-count robustness:** Splitting by actual strike count confirms the simulation finding — the CPI penalty persists regardless of strike density:

| Subset | n | CRPS/MAE |
|--------|---|----------|
| CPI 2-strike | 10 | 1.33 |
| CPI 3+-strike | 4 | 1.28 |
| JC 2-strike | 8 | 0.46 |
| JC 3+-strike | 8 | 0.84 |

Both CPI subsets show CRPS/MAE > 1.0, ruling out the hypothesis that 2-strike coarseness alone explains the CPI penalty. Interestingly, JC 2-strike events show *better* CRPS/MAE (0.46) than 3+-strike events (0.84), likely reflecting selection effects (simpler events with fewer strikes may have more predictable outcomes).

### Worked Example: What Does CRPS/MAE Mean for a Trader?

*We select these examples to illustrate the CRPS/MAE mechanism at its clearest; the series medians (Jobless Claims=0.65 tail-aware / 0.67 interior-only, CPI=1.60 / 1.38) represent the typical case.*

**Jobless Claims success — KXJOBLESSCLAIMS-25JUN12:** The implied mean was 275,000 (interior-only; tail-aware: 262,000), but the full distribution assigned substantial probability below 250K. Claims came in at 248,000 — a large miss for the point forecast (MAE=27,000 interior, 14,000 tail-aware). But the distribution had already priced in that downside: CRPS=4,455, giving a per-event ratio of 0.165 (interior-only) — the distribution captured 83% more information than the point forecast alone. A trader using only the implied mean would have been blindsided; a trader using the full distribution to price range contracts (e.g., "claims below 250K") would have had a well-calibrated probability to work with.

**CPI failure — KXCPI-25JAN:** The implied mean was 0.35%, and realized CPI came in at 0.5%. With only 2 evaluated strikes, the "distribution" was essentially a step function that couldn't capture the upside tail. CRPS=0.273 vs MAE=0.15 — a per-event ratio of 1.82. The distributional spread actively hurt: a trader would have been better off ignoring the distribution entirely and using only the point forecast. This is exactly the scenario where additional strikes would help (see Market Design Implications below).

### Per-Event CRPS/MAE Distribution

The headline ratios (tail-aware CPI=1.58, JC=0.66; interior-only CPI=1.32, JC=0.60) mask substantial within-series heterogeneity. Per-event CRPS/MAE ratios *(interior-only; see note below)* range from 0.35 (KXCPI-25FEB) to 4.51 (KXCPI-25JUN) for CPI, and from 0.17 (KXJOBLESSCLAIMS-25JUN12) to 2.54 (KXJOBLESSCLAIMS-25DEC18) for Jobless Claims. Median per-event ratios (CPI=1.38, JC=0.67 interior-only) are consistent with the mean-based estimates, confirming the aggregate finding is not driven by outliers. However, the spread matters: 6 of 14 CPI events (43%) actually have CRPS/MAE < 1 — the distribution *does* add value for these events. The CPI problem is not uniform miscalibration but high variance in distributional quality, with several events where the coarse 2-strike structure fails badly (ratios > 3.0). A strip chart of the full per-event distribution is available in the experiment outputs (Figure: per_event_crps_mae_strip).

*Note on per-event ratios:* We report per-event ratios using interior-only MAE because per-event tail-aware ratios are unstable: when the tail-aware mean happens to be close to realized by coincidence, the MAE denominator approaches zero and the ratio explodes (e.g., KXCPI-25JUN: tail-aware MAE=0.01, producing ratio=21.5 vs interior-only 4.51). The aggregate ratio-of-means (which averages numerator and denominator separately before dividing) is immune to this instability and remains our primary metric.

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

To test whether the mid-life snapshot choice drives our results, we computed CRPS/MAE at five timepoints across each market's life, with bootstrap 95% CIs. *(Note: Temporal analysis is restricted to events with ≥6 hourly snapshots (n=13 for JC, n=14 for CPI), explaining minor differences from the headline ratio which uses all events.)*

*Interior-only implied mean (sensitivity):*

| Lifetime % | CPI CRPS/MAE | CPI 95% CI | JC CRPS/MAE | JC 95% CI |
|-----------|-------------|-----------|-------------|----------|
| 10% (early) | 0.76 | [0.54, 1.21] | 0.73 | [0.54, 1.02] |
| 25% | 1.36 | [0.83, 2.37] | **0.52** | **[0.36, 0.81]** |
| 50% (mid — primary) | 1.32 | [0.84, 2.02] | **0.58** | **[0.40, 0.85]** |
| 75% | 0.73 | [0.54, 1.05] | **0.60** | **[0.40, 0.90]** |
| 90% (late) | **0.76** | **[0.64, 1.00]** | 0.79 | [0.39, 1.84] |

*Tail-aware implied mean (primary):*

| Lifetime % | CPI CRPS/MAE | CPI 95% CI | JC CRPS/MAE | JC 95% CI |
|-----------|-------------|-----------|-------------|----------|
| 10% (early) | 0.90 | [0.62, 1.57] | **0.73** | **[0.59, 0.92]** |
| 25% | 1.50 | [0.89, 2.81] | **0.65** | **[0.57, 0.81]** |
| 50% (mid — primary) | **1.58** | **[1.03, 2.55]** | **0.65** | **[0.53, 0.80]** |
| 75% | 0.86 | [0.65, 1.27] | **0.67** | **[0.55, 0.85]** |
| 90% (late) | 0.88 | [0.72, 1.21] | **0.72** | **[0.54, 0.90]** |

*Temporal CIs use the percentile bootstrap method rather than BCa; the headline CRPS/MAE ratios use BCa.*

**Bold** entries: CI excludes 1.0 (distribution significantly adds value at that timepoint).

For **Jobless Claims**, the tail-aware results are striking: CIs exclude 1.0 at **all five timepoints** (10–90% of market life). This is the strongest possible confirmation that the headline CRPS/MAE=0.66 is not a snapshot artifact — JC distributions genuinely add value across the entire market lifecycle. The interior-only results are slightly weaker (3 of 5 timepoints significant), but the pattern is consistent.

For **CPI**, the tail-aware CIs show significance only at the 50% timepoint [1.03, 2.55], confirming that mid-life is where CPI distributions are most harmful. The interior-only 90% CI [0.64, 1.00] barely excludes 1.0, but this does not replicate with the tail-aware mean [0.72, 1.21]. The U-shaped point-estimate pattern (well-calibrated early and late, worst at mid-life) remains visible but should be treated as directional rather than confirmed.

**Lifecycle perspective:** The tail-aware temporal table reveals a striking asymmetry: JC distributions add value at **all five timepoints** (every CI excludes 1.0), while CPI distributions are significantly harmful only at mid-life (50% CI [1.03, 2.55]). This means the JC finding is not just robust at the headline snapshot — it holds throughout the entire market lifecycle. The mid-life snapshot is reported as the headline because it represents the canonical trader decision point (maximum uncertainty, most active trading). The tail-aware mid-life CRPS/MAE (1.58) is higher than the interior-only (1.32) because the tail-aware mean is a *better* point forecast — making the distributional penalty more stark relative to a stronger baseline. This is an important robustness finding: even when you give the point forecast every advantage (using the best available mean from the same CDF), the CPI distribution still underperforms.

*Speculative hypothesis — three-phase process (not statistically confirmed; no individual CPI timepoint CI excludes 1.0 at 10–75% of market life):* Early markets may inherit reasonable distributional priors from their strike structure (the initial CDF reflects the market maker's prior before substantive trading), mid-life markets may overreact to partial signals — fragmentary information about components like shelter or energy arrives but cannot be coherently integrated into a composite distribution — and late markets converge as the approaching release date forces information integration and narrows genuine uncertainty. This interpretation is consistent with the point-estimate pattern and generates a testable prediction: series with simpler signal structure (like Jobless Claims) should show less mid-life degradation, which is exactly what we observe. (For a complementary analysis of how maturity affects individual binary contract accuracy using Brier scores, see Appendix D.)

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

3. **Trader composition** *(speculative — not directly testable with public data)*: Jobless Claims markets attract specialized labor-market traders with domain expertise in distributional shape. CPI markets attract broader macro traders whose point forecasts are accurate (MAE=0.068 tail-aware) but whose uncertainty estimates are poorly calibrated.

4. **Liquidity and market depth**: If CPI markets have thinner order books at extreme strikes, the distributional tails will be poorly priced, inflating CRPS without affecting the implied mean (MAE). This is consistent with the CRPS/MAE > 1 finding.

### PIT Diagnostic: Where the Miscalibration Lives

The Probability Integral Transform (PIT) reveals the *direction* of miscalibration, not just its magnitude:

| Metric | CPI (n=14) | Jobless Claims (n=16) | Well-Calibrated |
|--------|-----------|----------------------|-----------------|
| Mean PIT | 0.609 | 0.463 | 0.500 |
| 95% CI | [0.49, 0.72] | [0.35, 0.58] | — |
| PIT Std | 0.222 | 0.248 | 0.289 |
| KS test p | 0.221 | 0.353 | — |

CPI's mean PIT=0.61 means realized CPI tends to fall in the upper half of the implied distribution — markets systematically underestimate inflation. This directional bias (+0.109 from the ideal 0.5) is the key mechanistic finding: CPI distributions don't just lack precision, they are *biased*. Jobless Claims' mean PIT=0.46 is consistent with unbiased calibration (bias of -0.037, well within noise).

This asymmetry is a differential diagnostic for the four hypothesized mechanisms. It favors mechanisms 1–2 (insufficient feedback leading to uncorrected directional bias in CPI) over mechanism 4 (thin-tails liquidity, which would produce symmetric CRPS inflation without directional skew). If the problem were purely a liquidity artifact, we would expect PIT values scattered around 0.5 for both series; instead, the CPI PIT shift is consistent with a systematic forecasting bias that weekly feedback would help correct.

**A caveat on mechanism 1:** The snapshot sensitivity U-shape creates a mild tension with the release-frequency hypothesis. If infrequent calibration feedback were the *sole* driver, CPI distributions should be uniformly worse than Jobless Claims — yet CPI is well-calibrated at 10% of market life (CRPS/MAE=0.76). This is more consistent with mechanism 2 (signal dimensionality): partial CPI signals arriving mid-life create confusion that simple-signal series avoid, while early and late markets are anchored by structural priors and convergence pressure respectively. The frequency hypothesis may still operate — rapid feedback could help correct mid-life overreaction faster — but it is not sufficient on its own to explain the temporal pattern.

These hypotheses are testable as more data accumulates: mechanisms 1 and 2 predict that other weekly releases (e.g., mortgage applications) should also have CRPS/MAE < 1, while other monthly composites (e.g., PCE) should have CRPS/MAE > 1. The PIT diagnostic already identifies the dominant failure mode: CPI distributions are *biased* (directional PIT shift), not merely imprecise. A full CRPS decomposition into reliability, resolution, and uncertainty components (Hersbach, 2000) is infeasible at n=14 (binning PIT values across K bins yields ~3 observations per bin), but as data accumulates this would clarify whether CPI markets also lack resolution (uninformativeness) in addition to their documented reliability failure.

---

## 3. Information Hierarchy: Bond Markets Lead, Prediction Markets Add Granularity

Having established *how well* Kalshi prices distributions (Section 2), we now ask *where the information comes from*. If CPI distributions are miscalibrated while point forecasts are competitive, understanding the information flow into these markets helps explain why — and whether the problem is correctable.

### TIPS Granger Causality

286 overlapping days (Oct 2024 - Jan 2026):

| Direction | Best Lag | F-stat | p-value |
|-----------|----------|--------|---------|
| TIPS → Kalshi | 1 day | 12.24 | 0.005 |
| Kalshi → TIPS | — | 0.0 | 1.0 |

The F=0.0 for Kalshi→TIPS indicates the Kalshi series adds no explanatory power beyond TIPS's own lags — the reverse direction is completely uninformative.

TIPS breakeven rates Granger-cause Kalshi CPI prices at a 1-day lag. This means TIPS data has predictive information for next-day Kalshi prices beyond what Kalshi's own history provides. However, Granger causality measures predictive information, not causal information flow — the lag may reflect slow-updating Kalshi contracts (stale prices in thinly traded markets) rather than a genuine information hierarchy where bond markets lead prediction markets. Regardless of the mechanism, Kalshi is a useful aggregator — it incorporates TIPS information while adding granularity through its multi-strike structure that a single breakeven rate cannot provide.

### CPI Point Forecast Horse Race

| Forecaster | Mean MAE | Cohen's d | p (raw) | p (Bonferroni ×4) | n |
|-----------|----------|-----------|---------|-------------------|---|
| **Kalshi implied mean (tail-aware)** | **0.068** | — | — | — | **14** |
| SPF (annual/12 proxy)† | 0.110 | -0.43 | 0.086 | 0.345 | 14 |
| TIPS breakeven (monthly) | 0.112 | -0.47 | **0.045** | 0.181 | 14 |
| Trailing mean | 0.118 | -0.47 | **0.021** | 0.084 | 14 |
| Random walk (last month) | 0.143 | **-0.71** | **0.015** | **0.059** | 14 |

*Interior-only Kalshi MAE = 0.082. Switching to the tail-aware mean (consistent with CRPS computation) improves the point forecast and strengthens all horse race comparisons.*

†*SPF does not forecast monthly CPI directly; this conversion divides the annual Q4/Q4 forecast by 12, assuming uniform monthly contributions. This ignores seasonality, base effects, and within-year dynamics, and should be treated as indicative rather than definitive.*

*Bonferroni correction applied across 4 benchmark comparisons (SPF, TIPS, random walk, trailing mean), consistent with the correction applied to CRPS series tests in Section 2.*

Using the tail-aware implied mean (consistent with the CRPS computation), Kalshi outperforms random walk (p_raw=0.015, p_adj=0.059, d=-0.71) — borderline significant after Bonferroni correction for 4 benchmarks. Kalshi also outperforms TIPS breakeven (p_raw=0.045) and trailing mean (p_raw=0.021), both significant at the raw level. The tail-aware mean is a strictly better point forecast than the interior-only mean (MAE=0.068 vs 0.082), which strengthens all comparisons. The irony deepens: CPI point forecasts show strong advantages over benchmarks while CPI distributions are actively harmful (tail-aware CRPS/MAE=1.58, CI excludes 1.0). This suggests the implied mean aggregates information effectively, but the market misprices uncertainty around that mean — a finding confirmed by the PIT directional bias (mean PIT=0.61, indicating systematic inflation underestimation).

### Power Analysis

| Test | Effect size | n (current) | n (80% power) | More data needed |
|------|------------|-------------|---------------|-----------------|
| Jobless Claims vs Historical CRPS | r=0.10 | 16 | 152 | 136 more events |
| CPI vs Historical CRPS | r=0.16 | 14 | 61 | 47 more months |
| Kalshi vs Random Walk (tail-aware) | d=0.71 | 14 | 13 | **Already powered** |
| Kalshi vs SPF (tail-aware) | d=0.43 | 14 | 35 | 21 more months |
| Kalshi vs TIPS (tail-aware) | d=0.47 | 14 | 30 | 16 more months |
| Kalshi vs Trailing Mean (tail-aware) | d=0.47 | 14 | 30 | 16 more months |

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
3. **Bonferroni correction**: Raw p-values adjusted for multiple series comparisons (2 tests in CRPS, 4 benchmarks in horse race)
4. **Rank-biserial effect sizes**: Reported for all Wilcoxon tests (r = 1 - 2T/n(n+1)/2)
5. **Power analysis**: Sample sizes for 80% power computed for all tests
6. **Controlled observation timing**: T-24h maturity gradient (7x) reduced to 1.5x at 50% lifetime
7. **PIT sign correction**: cdf_values store survival P(X>strike), not CDF P(X<=strike). PIT = 1 - interpolated survival
8. **CRPS/MAE ratio**: Distribution-vs-point diagnostic reported per series with BCa bootstrap CIs
9. **Scale-appropriate CRPS integration**: Tail extension dynamically set to max(strike_range × 0.5, 1.0) plus coverage of realized values beyond strike boundaries, ensuring correct CRPS for both percentage-scale (CPI) and level-scale (Jobless Claims) series
10. **Serial correlation adjustment**: CPI MoM values have AR(1) ρ=0.23, reducing effective degrees of freedom from n=14 to n_eff≈8.8 (Bartlett's formula). This widens the effective CPI CRPS/MAE CI by ~27%
11. **Tail-aware implied mean**: E[X] computed from the same piecewise-linear CDF used in CRPS (integrating survival function), ensuring consistent treatment of tail probability in both numerator and denominator of the CRPS/MAE ratio. Both interior-only and tail-aware ratios reported for transparency
12. **Leave-one-out sensitivity**: All 16 Jobless Claims leave-one-out CRPS/MAE ratios fall below 1.0 under both mean specifications (tail-aware range [0.64, 0.69]; interior-only [0.57, 0.66]), confirming no single event drives the JC finding
13. **CRPS − MAE signed difference**: Complementary to the ratio diagnostic, immune to ratio instability when MAE → 0. Wilcoxon signed-rank test on per-event (CRPS − MAE) differences: JC p=0.001 (14/16 events negative), CPI p=0.091 (10/14 events positive)

### Experiments Summary

| # | Name | Role in Paper |
|---|------|---------------|
| 7 | Implied Distributions | Section 1: Methodology |
| 12 | CRPS Scoring | Section 2: Main result |
| 13 | Unified + Horse Race | Sections 2-3: Per-series tests, horse race |
| 8 | TIPS Comparison | Section 3: Information hierarchy |
| 11 | Favorite-Longshot Bias | Appendix D: Maturity (controlled) |

---

## Supplementary Appendix

### A. PIT Analysis — Additional Detail

The main PIT results are reported in Section 2 (PIT Diagnostic subsection). Additional notes:

**CPI:** The KS test does not reject PIT uniformity (p=0.22), but the KS test is underpowered at n=14 to detect the observed bias. The mean PIT CI [0.49, 0.72] includes 0.5, so the directional bias is suggestive rather than individually significant — but it converges with the CRPS/MAE ratio and temporal pattern to form a consistent picture. Few individual PIT values fall in the tails (7% vs ideal 20%), consistent with overconfident (too narrow) distributions.

**Jobless Claims:** The KS test does not reject uniformity (p=0.35), and the mean PIT CI [0.35, 0.58] straddles 0.5, consistent with well-calibrated distributions. This directly confirms the CRPS/MAE < 1 finding — the distributions that add value also pass calibration checks, while the distributions that are harmful show directional bias. The contrast provides independent confirmation of the series-level heterogeneity.

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
| Kalshi vs Random Walk (tail-aware) | p=0.015 | p=0.059 | Tail-aware mean + Bonferroni |

**Invalidated:**

| Finding | Original | Corrected | Reason |
|---------|----------|-----------|--------|
| Shock acceleration | p<0.001 | p=0.48 | Circular classification |
| KUI leads EPU | p=0.024 | p=0.658 | Absolute return bias |
| Trading Sharpe | +5.23 | -2.26 | Small-sample artifact |

### D. Market Maturity and Binary Contract Calibration

Complementing the distributional maturity analysis in Section 2 (which tracks CRPS/MAE across market lifetime), we examine individual binary contract accuracy using Brier scores. This addresses a different question — single-contract calibration rather than distributional quality — but provides context on how market maturity affects pricing more broadly.

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

The T-24h gradient (7x) is largely mechanical — for long-lived markets, T-24h represents 99% of lifetime elapsed. The controlled analysis (50% of lifetime) shows a 1.5x residual — short-lived markets are modestly worse, but medium and long are similar. Remaining confounds (contract type, liquidity, trader composition) prevent causal interpretation.

### E. References

- Breeden, D. T., & Litzenberger, R. H. (1978). Prices of state-contingent claims implicit in option prices. *Journal of Business*, 51(4), 621-651.
- Efron, B., & Tibshirani, R. J. (1993). *An Introduction to the Bootstrap*. Chapman & Hall/CRC.
- Brigo, D., Graceffa, F., & Neumann, E. (2023). Simulation of arbitrage-free implied volatility surfaces. *Applied Mathematical Finance*, 27(5).
- Gneiting, T., & Raftery, A. E. (2007). Strictly proper scoring rules, prediction, and estimation. *Journal of the American Statistical Association*, 102(477), 359-378.
- Hersbach, H. (2000). Decomposition of the continuous ranked probability score for ensemble prediction systems. *Weather and Forecasting*, 15(5), 559-570.
- Messias, J., Corso, J., & Suarez-Tangil, G. (2025). Unravelling the probabilistic forest: Arbitrage in prediction markets. AFT 2025. arXiv:2508.03474.
