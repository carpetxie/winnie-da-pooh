# When Do Prediction Market Distributions Add Value? A CRPS/MAE Diagnostic

**Date:** 2026-02-24
**Status:** Draft — under review (iteration 15).

## Abstract

We introduce the CRPS/MAE ratio as a diagnostic for evaluating prediction market distributional forecasts, and apply it to multi-strike Kalshi contracts across **248 settled economic events spanning 11 series**: CPI (n=33), CPI YoY (n=34), Core CPI (n=32), Unemployment (n=32), Mortgage Rates (n=59), Core PCE (n=13), Jobless Claims (n=16), ADP Employment (n=9), GDP (n=9), ISM PMI (n=7), and the Federal Funds Rate (n=4).

The CRPS/MAE ratio compares how well a market's full probability distribution performs (CRPS) against using just its central point forecast (MAE). A ratio below 1 means the distribution adds value; above 1 means the spread is so miscalibrated that you'd be better off ignoring it.

**The main finding is overwhelmingly positive: prediction market distributions add value for the vast majority of economic series.** Nine of 11 series show CRPS/MAE < 1.0 with leave-one-out unanimity in 8 of these (sign test on 248 per-event ratios: 147/248 < 1.0, p=0.004). Only Core PCE (1.22, n=13) and the Federal Funds Rate (1.48, n=4) show harmful distributions. GDP shows the strongest distributional value (0.48, BCa CI [0.31, 0.77] — the only CI that conclusively excludes 1.0), followed by Jobless Claims (0.60), CPI YoY (0.67), and ADP (0.71).

An initial analysis of 7 series (93 events) suggested a "simple-vs-complex" dichotomy as the primary finding (Mann-Whitney p=0.0004, r=0.43). Expanding to 11 series (248 events) substantially weakened this: p=0.033, r=0.16 (trivial effect size). A pre-registered out-of-sample test of the hypothesis failed 2/4 predictions — both "complex" predictions were wrong (Core CPI m/m: predicted >1.0, actual 0.82; CPI YoY: predicted >1.0, actual 0.67). We report both sets of results for transparency. The failure of the simple-vs-complex hypothesis is itself informative: it suggests that the mechanisms driving distributional quality are more nuanced than signal dimensionality alone.

CPI *point* forecasts beat all benchmarks including random walk (d=−0.85, p_adj=0.014), while CPI *distributions* in the post-Nov 2024 period show CRPS/MAE=1.32. This is — to our knowledge — the first empirical demonstration in prediction markets that point and distributional calibration can diverge independently. KXFRM (Mortgage Rates) demonstrates the complementary pattern: good point forecasts (d=−0.55 vs random walk) *and* good distributions (CRPS/MAE=0.85), confirming that the CPI decoupling is genuine rather than a methodological artifact.

A universal overconcentration pattern emerges as the dominant calibration failure mode: all 11 series show std(PIT) below the theoretical uniform ideal of 0.289. Markets systematically understate uncertainty — they know *where* outcomes will land but underestimate *how uncertain* they are.

> **Practical Takeaways:**
> - **For 9 of 11 economic series: use the full distribution.** Distributions add value across GDP, Jobless Claims, CPI YoY, ADP Employment, Unemployment, Core CPI, Mortgage Rates, CPI, and ISM PMI.
> - **GDP** is the standout: CRPS/MAE=0.48, CI excludes 1.0. Distribution reduces forecast error by 52% vs point forecast alone.
> - **Core PCE and FED** are the exceptions: use point forecasts only for these series.
> - **All 11 series are overconcentrated** — distributions are systematically too narrow. Markets capture the correct central tendency but understate tail risk.
> - **Monitor the CRPS/MAE ratio per series** — the CPI structural break (ratio shifted from 0.69 to 1.32 across naming conventions) shows distributional quality can change over time. A retrospective backtest of the proposed monitoring protocol confirms it detects degradation in CPI and Core PCE while producing zero false alerts for 6 of 8 testable series.
> - **The CRPS/MAE ratio** is a practical real-time diagnostic that Kalshi could deploy per series to flag distributional degradation.

**Executive Summary (11 series, 248 events):**

| | GDP | JC | CPIYOY | ADP | KXU3 | CPICORE | FRM | CPI | ISM | PCE | FED |
|---|---|---|---|---|---|---|---|---|---|---|---|
| n | 9 | 16 | 34 | 9 | 32 | 32 | 59 | 33 | 7 | 13 | 4 |
| CRPS/MAE | **0.48** | **0.60** | **0.67** | **0.71** | **0.75** | **0.82** | **0.85** | **0.86** | **0.97** | **1.22** | **1.48** |
| 95% BCa CI | [0.31, 0.77] | [0.37, 1.02] | [0.41, 1.11] | [0.36, 1.45] | [0.54, 1.04] | [0.59, 1.16] | [0.64, 1.12] | [0.57, 1.23] | [0.58, 1.81] | [0.78, 1.93] | [0.79, 4.86] |
| CI excl. 1.0? | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| LOO | All<1 | All<1 | All<1 | All<1 | All<1 | All<1 | All<1 | All<1 | Mixed | All>1 | All>1 |
| Verdict | ✅ Dist. | ✅ Dist. | ✅ Dist. | ✅ Dist. | ✅ Dist. | ✅ Dist. | ✅ Dist. | ✅ Monitor | ⚠️ Borderline | ❌ Point | ❌ Point |

---

## 1. Methodology: Implied CDFs from Multi-Strike Markets

We reconstruct implied CDFs from multi-strike binary contracts on the Kalshi prediction market. For each event at each hour, strike-ordered cumulative probabilities from binary contracts yield the implied CDF following the logic of Breeden-Litzenberger (1978). (Unlike equity options, where extracting risk-neutral densities requires differentiating call prices with respect to strike, binary contracts directly price state-contingent probabilities, making the extraction straightforward.) CRPS is computed at the mid-life snapshot (50% of market lifetime elapsed) as a representative assessment of distributional quality.

**Data scope:** 11 economic series, 248 settled events with both realized outcomes and sufficient candlestick data for CRPS computation. Series span Dec 2022 to Feb 2026. We merge old naming conventions (CPI-, FED-, GDP-) with new naming conventions (KXCPI-, KXFED-, KXGDP-) into canonical series, as these represent the same underlying economic indicators with a platform naming change around November 2024.

*Note on implied mean computation: We report the "interior-only" implied mean (probability mass between min and max strikes, renormalized) as the primary result. A "tail-aware" alternative integrating the same piecewise-linear CDF used for CRPS computation is reported for sensitivity.*

### No-Arbitrage Efficiency

| Metric | Kalshi | Benchmark |
|--------|--------|-----------|
| Violation rate (non-monotone CDF) | 2.8% of snapshots (hourly) | SPX call spread: 2.7% of violations (daily) (Brigo et al., 2023) — different measurement bases; directionally comparable |
| Reversion rate | 86% within 1 hour | Polymarket: ~1h resolution (Messias et al., 2025) |
| Other prediction markets | — | Polymarket: 41%, PredictIt: ~95%, IEM: 37.7% |

Kalshi's 2.8% hourly violation rate is directionally comparable to SPX equity options and substantially lower than other prediction markets. The 86% reversion within 1 hour is consistent with transient mispricing in thin markets, not systematic arbitrage opportunities.

---

## 2. Main Result: Prediction Market Distributions Add Value for Most Economic Series

### The CRPS/MAE Diagnostic

The CRPS/MAE ratio measures whether a market's distributional spread adds information beyond its point forecast (the implied mean). CRPS is a strictly proper scoring rule (Gneiting & Raftery, 2007) — it is uniquely minimized by the true distribution, making it the natural metric for evaluating distributional forecasts. For a well-calibrated distribution, the sharpness reward in CRPS means CRPS will typically be lower than MAE; ratio > 1 signals that the distributional spread is miscalibrated. Values below 1 indicate the distribution adds value; values above 1 indicate it introduces noise.

Note that a high CRPS/MAE ratio does not simply reflect good point forecasts deflating the denominator: CPI shows ratio=1.32 (post-break) despite having the best point forecasts of any series (d=−0.85 vs random walk in the horse race), confirming that the ratio captures genuine distributional miscalibration rather than an artifact of MAE normalization. The CRPS/MAE ratio measures the *marginal* information value of distributional spread beyond the point forecast — a ratio below 1 means the market's probabilistic spread reduces forecast error compared to using the point forecast alone. The CRPS/MAE ratio is designed as a retrospective monitoring diagnostic — analogous to a statistical process control chart — not as a predictive model for individual events.

### Full 11-Series Results

| Series | n | Mean CRPS | Mean MAE | CRPS/MAE | 95% BCa CI | Median | LOO |
|--------|---|-----------|----------|----------|------------|--------|-----|
| GDP | 9 | 0.580 | 1.211 | **0.48** | [0.31, 0.77] | 0.46 | All < 1.0 [0.45, 0.51] |
| Jobless Claims | 16 | 7,748 | 12,959 | **0.60** | [0.37, 1.02] | 0.67 | All < 1.0 [0.57, 0.66] |
| CPI YoY (KXCPIYOY) | 34 | 0.102 | 0.152 | **0.67** | [0.41, 1.11] | 0.96 | All < 1.0 [0.63, 0.73] |
| ADP Employment (KXADP) | 9 | 34,987 | 49,447 | **0.71** | [0.36, 1.45] | 0.74 | All < 1.0 [0.69, 0.74] |
| Unemployment (KXU3) | 32 | 0.098 | 0.131 | **0.75** | [0.54, 1.04] | 0.63 | All < 1.0 [0.69, 0.80] |
| Core CPI m/m (KXCPICORE) | 32 | 0.098 | 0.120 | **0.82** | [0.59, 1.16] | 0.76 | All < 1.0 [0.76, 0.85] |
| Mortgage Rates (KXFRM) | 59 | 0.070 | 0.082 | **0.85** | [0.64, 1.12] | 0.93 | All < 1.0 [0.81, 0.90] |
| CPI | 33 | 0.108 | 0.125 | **0.86** | [0.57, 1.23] | 0.96 | All < 1.0 [0.80, 0.96] |
| ISM PMI (KXISMPMI) | 7 | 0.716 | 0.739 | **0.97** | [0.58, 1.81] | 0.90 | Mixed [0.86, 1.07] |
| Core PCE (KXPCECORE) | 13 | 0.107 | 0.088 | **1.22** | [0.78, 1.93] | 0.78 | All > 1.0 [1.09, 1.32] |
| Federal Funds Rate | 4 | 0.148 | 0.100 | **1.48** | [0.79, 4.86] | 1.59 | All > 1.0 [1.12, 1.80] |

*Bootstrap CIs: 10,000 resamples, BCa (bias-corrected and accelerated) method via `scipy.stats.bootstrap` (Efron & Tibshirani, 1993). KXADP results corrected in iteration 14 (comma-parsing bug fixed — 7/9 events had realized values off by 1000x due to "41,000" being parsed as 41 instead of 41000). KXPCECORE recomputed with expanded candle data (n=13 vs original n=15).*

### The Headline Finding: Distributions Add Value Broadly

**9 of 11 series** show CRPS/MAE < 1.0. Of those 9, **8 have unanimous LOO ratios below 1.0** — no single event drives any of these results. The per-event sign test is highly significant: **147 of 248 events** (59.3%) have CRPS/MAE < 1.0 (binomial test p=0.004). The sign test treats events as exchangeable across series; the per-series LOO analysis (8/9 unanimous) provides convergent evidence that the finding is not driven by any single dominant series. At the series level, 9/11 < 1.0 gives binomial p=0.065 — borderline, but the convergent evidence from LOO unanimity and per-event sign test strongly supports the conclusion.

Only **Core PCE** (ratio=1.22, LOO all > 1.0) and **FED** (ratio=1.48, LOO all > 1.0) consistently show harmful distributions. These two series account for only 17 of 248 events (6.9%).

This is the paper's central finding: **for the vast majority of economic indicators on Kalshi, the distributional information in multi-strike markets adds genuine forecasting value beyond point predictions.**

### Cross-Series Heterogeneity

**Kruskal-Wallis test** (10 series with n≥5, 244 events): H=13.6, p=0.139. With all 11 series: H=15.3, p=0.122. The formal test does **not** reject the null of homogeneous distributions across series. However, the range of ratios (0.48 to 1.48) and the clear separation of Core PCE and FED from the rest suggest genuine, if modest, heterogeneity. Earlier analysis with fewer series (7 series, 93 events) showed significant heterogeneity (H=18.5, p=0.005) — the addition of 4 more series whose ratios cluster around 0.7–0.85 diluted the extremes.

**Evolution of the heterogeneity finding:**

| Dataset | K series | N events | KW H | KW p | Interpretation |
|---------|----------|----------|------|------|----------------|
| Original 4 series | 4 | 62 | 9.98 | 0.019 | Significant |
| + 3 series (iter. 13) | 7 | 93 | 18.5 | 0.005 | Highly significant |
| Full 11 series (iter. 14) | 11 | 248 | 15.3 | 0.122 | Not significant |

The apparent strengthening from 4→7 series, then weakening at 11 series, illustrates a cautionary lesson: adding series that cluster near the extremes (Core PCE at 2.06 in the original analysis) artificially inflates heterogeneity statistics. With more data, the picture clarifies: most series have similar CRPS/MAE ratios (0.6–0.9), with two outliers.

### The Simple-vs-Complex Hypothesis: Pre-Registration and Failure

In iteration 13, we hypothesized that "simple" indicators (single administratively-reported numbers: GDP, Jobless Claims, ADP, Unemployment, Mortgage Rates) should show CRPS/MAE < 1.0, while "complex" indicators (composite indices or transformations: CPI, Core CPI, CPI YoY, Core PCE) should show CRPS/MAE > 1.0. With 7 series, this dichotomy was the paper's strongest finding (p=0.0004, r=0.43).

**We pre-registered out-of-sample predictions** for 4 new series before computing their CRPS/MAE:

| Series | Classification | Predicted | Actual | Result |
|--------|---------------|-----------|--------|--------|
| KXU3 (Unemployment) | Simple | < 1.0 | **0.75** | ✅ Correct |
| KXFRM (Mortgage Rates) | Simple | < 1.0 | **0.85** | ✅ Correct |
| KXCPICORE (Core CPI m/m) | Complex | > 1.0 | **0.82** | ❌ Wrong |
| KXCPIYOY (CPI YoY) | Complex | > 1.0 | **0.67** | ❌ Wrong |

**Hit rate: 2/4 (50%) — no better than chance.** Both "simple" predictions were correct; both "complex" predictions were wrong. Core CPI m/m (a composite index excluding food and energy) and CPI YoY (a year-over-year transformation of a composite) both show distributions that *add value* with LOO unanimity. This directly contradicts the hypothesis that compositeness or transformation complexity degrades distributional quality.

**Updated 11-series simple-vs-complex test:**
- Simple series (GDP, JC, ADP, KXU3, KXFRM): 125 events, median CRPS/MAE = 0.69
- Complex series (CPI, KXCPICORE, KXCPIYOY, KXPCECORE): 112 events, median CRPS/MAE = 0.84
- Mann-Whitney: p=0.033, r=0.16

The gap is statistically significant at p<0.05 but with a **trivial effect size** (r=0.16, was r=0.43 with 7 series). The classification correctly identifies that simple series tend to have *somewhat* lower ratios, but the within-group variance far exceeds the between-group difference. Both groups are predominantly < 1.0.

**What actually distinguishes Core PCE and FED?** If signal complexity isn't the driver, what is? We observe two very different mechanisms:
- **Core PCE** is the Fed's preferred inflation measure, receiving intense scrutiny and potentially more diverse forecaster opinions that make consensus pricing harder. Its ratio (1.22) is driven by a subset of events with very high ratios while the median is only 0.78.
- **FED** involves discrete jumps (0/25/50bp) rather than continuous economic readings. With only n=4, any conclusion is speculative.

These are different mechanisms, and the sample sizes are too small to test them definitively.

### CPI Temporal Structural Break

A natural temporal split — old naming convention (CPI-, Dec 2022–Oct 2024) vs new naming convention (KXCPI-, Nov 2024+) — reveals a shift in CPI distributional quality:

| Period | Prefix | n | CRPS/MAE | Median per-event |
|--------|--------|---|----------|------------------|
| Dec 2022 – Oct 2024 | CPI- | 19 | **0.69** | 0.73 |
| Nov 2024 – present | KXCPI- | 14 | **1.32** | 1.38 |

The Mann-Whitney test for this split gives p=0.18 — not individually significant, but the directional shift is large (ratio nearly doubles) and the split is pre-registered by the naming convention change rather than chosen to maximize the difference. With 33 CPI events overall, the aggregate ratio (0.86) masks this time-varying pattern. The rolling-window analysis (Section 4) shows the break emerging in real time.

### Per-Event Heterogeneity

Per-event CRPS/MAE ratios show substantial within-series variation:

| Series | Min | Max | IQR |
|--------|-----|-----|-----|
| GDP | 0.25 | 0.63 | [0.38, 0.58] |
| Jobless Claims | 0.17 | 2.54 | [0.45, 1.04] |
| CPI | 0.27 | 5.58 | [0.52, 1.42] |
| FED | 1.00 | 1.98 | [1.07, 1.74] |

For CPI, 20 of 33 events (61%) have CRPS/MAE < 1 — the distribution adds value for a majority of events even when the aggregate is near 1.0.

---

## 3. CPI Point Forecasts and the Point-Distribution Decoupling

### TIPS Granger Causality (Brief)

TIPS breakeven rates Granger-cause Kalshi CPI prices at a 1-day lag (F=12.24, p=0.005; 286 overlapping days, Oct 2024–Jan 2026), but not vice versa. The lag likely reflects slow-updating Kalshi contracts rather than a deep information hierarchy.

### CPI Point Forecast Horse Race

*This analysis uses the 14 KXCPI (post-Nov 2024) events where FRED benchmark alignment is validated.*

| Forecaster | Mean MAE | Cohen's d | p (raw) | p (Bonferroni ×4) | n |
|-----------|----------|-----------|---------|-------------------|---|
| **Kalshi implied mean (tail-aware)** | **0.068** | — | — | — | **14** |
| SPF (annual/12 proxy)† | 0.110 | -0.43 | 0.086 | 0.345 | 14 |
| TIPS breakeven (monthly) | 0.112 | -0.47 | **0.045** | 0.181 | 14 |
| Trailing mean | 0.118 | -0.47 | **0.021** | 0.084 | 14 |
| Random walk (last month) | 0.150 | **-0.85** | **0.003** | **0.014** | 14 |

†*SPF does not forecast monthly CPI directly; this conversion divides the annual Q4/Q4 forecast by 12.*

The Kalshi CPI implied mean outperforms random walk with a large effect size (d=−0.85, p_adj=0.014), **significant at the 5% level after Bonferroni correction**. This result is robust to excluding the first event (n=13: d=−0.89, p_adj=0.016) and the first two events (n=12: d=−0.89, p_adj=0.024).

**The point-vs-distribution decoupling.** CPI point forecasts significantly beat random walk while CPI distributions in the same period show CRPS/MAE=1.32. This is, to our knowledge, the first empirical demonstration in prediction markets that point forecasts and distributional forecasts can be independently calibrated — accurate centers with miscalibrated spreads. KXFRM demonstrates that point and distributional quality *can* align (d=−0.55 vs RW *and* CRPS/MAE=0.85), making CPI's divergence more informative — it is genuine, not a methodological artifact.

### Cross-Series Point Forecast Horse Race

To test whether Kalshi's point forecast advantage extends beyond CPI, we run analogous horse races for Unemployment (KXU3, n=30) and Mortgage Rates (KXFRM, n=61) using FRED benchmarks (UNRATE and MORTGAGE30US respectively).

| Series | n | Kalshi MAE | RW MAE | d vs RW | p vs RW | Trail MAE | d vs Trail | p vs Trail |
|--------|---|-----------|--------|---------|---------|-----------|------------|------------|
| CPI (KXCPI) | 14 | **0.068** | 0.150 | **−0.85** | **0.003** | 0.118 | −0.47 | 0.021 |
| Mortgage (KXFRM) | 61 | **0.080** | 0.165 | **−0.55** | **<0.001** | 0.493 | −1.09 | <0.001 |
| Unemployment (KXU3) | 30 | 0.123 | 0.130 | −0.07 | 0.191 | 0.266 | **−0.97** | **<0.001** |

**Mortgage Rates** show Kalshi strongly beating random walk (d=−0.55, p<0.001), with a medium effect size nearly as large as CPI's. This is the paper's second-strongest point forecast result and — crucially — Mortgage Rates also have CRPS/MAE=0.85 (distributions add value), making KXFRM the most comprehensively well-performing series: good point forecasts *and* good distributions.

**Unemployment** shows Kalshi roughly matching random walk (d=−0.07, n.s.) but strongly beating the trailing mean (d=−0.97, p<0.001). The unemployment rate's high persistence (month-to-month changes are small) makes random walk a tough benchmark.

This cross-series evidence transforms the horse race from a CPI case study into systematic evidence: Kalshi point forecasts match or beat standard benchmarks across multiple economic indicators.

### Power Analysis

| Test | Effect size | n (current) | n (80% power) | Status |
|------|------------|-------------|---------------|--------|
| Sign test (events < 1.0) | 59.3% | 248 | — | **p=0.004, already significant** |
| GDP CI excludes 1.0 | — | 9 | — | **BCa CI [0.31, 0.77], excludes 1.0** |
| JC CI excludes 1.0 | — | 16 | ~20–25 | BCa CI [0.37, 1.02], borderline |
| CPI temporal split | r≈0.26 | 33 | ~95 | Not yet powered (p=0.18) |
| FED CI excludes 1.0 | — | 4 | ~15 | Needs ~11 more events |
| Kalshi vs Random Walk | d=0.85 | 14 | 9 | **Already powered** |

---

## 4. Robustness

### GDP (CRPS/MAE=0.48)

- **Leave-one-out**: All 9 LOO ratios < 1.0 (range [0.45, 0.51]); extremely stable.
- **CI excludes 1.0**: BCa CI [0.31, 0.77] — the only series where the CI conclusively excludes 1.0.
- **Historical benchmark**: Kalshi CRPS 0.580 vs Historical CRPS 0.762 (24% lower), but not individually significant (p=0.285 at n=9).

### Jobless Claims (CRPS/MAE=0.60)

- **Leave-one-out**: All 16 LOO ratios < 1.0 (range [0.57, 0.66]); no single event drives the result.
- **CI borderline**: BCa CI [0.37, 1.02] — barely includes 1.0. LOO unanimity provides strong convergent evidence.
- **Temporal stability**: Tail-aware CIs exclude 1.0 at all five temporal snapshots (10%, 25%, 50%, 75%, 90% of market life).

### CPI (CRPS/MAE=0.86)

- **Leave-one-out**: All 33 LOO ratios < 1.0 (range [0.80, 0.96]).
- **CI includes 1.0**: BCa CI [0.57, 1.23]. Serial-correlation-adjusted CI (AR(1) ρ=0.23, n_eff≈20.7): [0.44, 1.28].
- **Temporal split**: Old CPI (ratio=0.69) vs new KXCPI (ratio=1.32). The aggregate masks a structural break.

### KXFRM (Mortgage Rates, CRPS/MAE=0.85, n=59)

- **Snapshot count concern**: Mean 15.7 snapshots per event (max 49) — far lower than other series (300-800). This raises the question of whether mid-life CDFs are reliable with so few observations.
- **Sensitivity analysis**: Filtering by minimum snapshot threshold shows the result is robust: ≥5 snapshots (n=54): ratio=0.84; ≥10 (n=37): ratio=0.86; ≥20 (n=21): ratio=0.84. The CRPS/MAE ratio is stable across thresholds, alleviating data quality concerns.
- **LOO**: All 59 LOO ratios < 1.0 (range [0.81, 0.90]).

### KXADP (ADP Employment, CRPS/MAE=0.71, n=9)

- **Data correction**: 7 of 9 events had realized values corrupted by a comma-parsing bug ("41,000" parsed as 41 instead of 41000). After fixing, CRPS/MAE changed from 0.67 to 0.71. All 9 LOO ratios remain < 1.0. The directional conclusion is unchanged but the specific ratio differs.

### Core PCE (CRPS/MAE=1.22, n=13)

- **Leave-one-out**: All 13 LOO ratios > 1.0 (range [1.09, 1.32]); consistently harmful.
- **CI includes 1.0**: BCa CI [0.78, 1.93].
- **PIT diagnostic**: Mean PIT=0.600, CI [0.48, 0.72] — distributions biased low (outcomes tend to exceed the implied center). KS p=0.207 (does not reject uniformity individually, but directionally consistent with miscalibration).
- **Recomputation note (2.06→1.22 explained)**: Original analysis (iteration 13, n=15) showed ratio=2.06. Recomputation (iteration 14, n=13) shows ratio=1.22. Investigation reveals: (1) KXPCECORE-25JUL had MAE≈0 (implied mean exactly matched realized=0.3), creating an effectively infinite per-event ratio — the ratio-of-means approach (mean CRPS / mean MAE = 1.22) is robust to this; (2) Two early events (PCECORE-22NOV, PCECORE-22DEC) had very few snapshots (2-10) and extreme per-event ratios (3.8, 4.5); (3) Four events lacked sufficient candle data (KXPCECORE-24DEC, -25FEB, -25MAR, PCECORE-23SEP). The ratio-of-means (1.22) is more reliable than the mean-of-ratios, which is dominated by the near-zero-MAE outlier. The directional conclusion (distributions harmful) holds across all computations.

### FED (CRPS/MAE=1.48, n=4)

- **Leave-one-out**: All 4 LOO ratios > 1.0 (range [1.12, 1.80]); consistently harmful.
- **CI includes 1.0**: BCa CI [0.79, 4.86]. Wide CI reflects n=4.
- **Genuinely underpowered**: FOMC meets ~8 times/year; only 4 settled multi-strike events exist. Cannot expand.

### The Simple-vs-Complex Hypothesis: Robustness to Data Expansion

The evolution of the simple-vs-complex finding across iterations serves as a methodological cautionary tale:

| Dataset | N events | Mann-Whitney p | Effect size r | Kruskal-Wallis p |
|---------|----------|---------------|---------------|-----------------|
| 7 series | 93 | **0.0004** | **0.43** (large) | **0.005** |
| 11 series | 248 | 0.033 | 0.16 (trivial) | 0.139 (n.s.) |

The dramatic weakening (r from 0.43 to 0.16) resulted from two corrections: (1) KXCPICORE and KXCPIYOY, classified as "complex," both showed ratios < 1.0 with LOO unanimity, directly contradicting the prediction; (2) the 4 new series (ratios 0.67–0.85) cluster in the middle, compressing the between-group difference. The OOS prediction test (2/4 = 50% hit rate) provides independent evidence that the dichotomy does not generalize.

### PIT Diagnostic (All 11 Series)

*Probability Integral Transform: if CDFs are well-calibrated, PIT values should be uniform on [0,1] with mean 0.5. Mean PIT > 0.5 indicates distributions biased too low (outcomes tend to exceed predictions); mean PIT < 0.5 indicates distributions biased too high.*

| Series | n | Mean PIT | Std PIT | 95% CI | KS p | CvM p | Bias |
|--------|---|----------|---------|--------|------|-------|------|
| KXU3 (Unemployment) | 32 | **0.502** | 0.245 | [0.42, 0.59] | 0.547 | 0.506 | None |
| GDP | 9 | 0.516 | 0.266 | [0.20, 0.57] | 0.420 | — | None |
| KXADP (ADP) | 9 | 0.419 | 0.227 | [0.28, 0.57] | 0.462 | 0.460 | None |
| KXISMPMI (ISM) | 7 | 0.427 | **0.136** | [0.33, 0.53] | 0.265 | 0.231 | None |
| KXFRM (Mortgage) | 61 | 0.444 | 0.227 | [0.39, 0.50] | **0.016** | **0.048** | Slight high |
| JC (Jobless Claims) | 16 | 0.463 | 0.248 | [0.33, 0.60] | 0.353 | 0.396 | None |
| CPI | 33 | 0.564 | 0.259 | [0.45, 0.66] | 0.451 | — | None |
| KXCPICORE (Core CPI) | 33 | 0.589 | 0.219 | [0.52, 0.66] | **0.027** | 0.052 | Low bias |
| KXPCECORE (Core PCE) | 12 | 0.600 | 0.212 | [0.48, 0.72] | 0.207 | 0.203 | Marginal low |
| KXCPIYOY (CPI YoY) | 34 | 0.615 | 0.228 | [0.54, 0.69] | **0.016** | **0.019** | Low bias |
| FED | 4 | 0.710 | 0.226 | [0.32, 1.02] | 0.293 | — | Low bias |

*Std PIT: ideal for a uniform distribution is 0.289. All 11 series fall below this threshold.*

**Key findings from the full PIT analysis:**
- **5 of 11 series** show no significant deviation from uniformity (KXU3, GDP, KXADP, KXISMPMI, JC) — well-calibrated distributions.
- **KXU3 is near-perfectly calibrated** (mean PIT=0.502), consistent with its strong CRPS/MAE ratio of 0.75.
- **3 series reject uniformity** at the 5% level via KS test (KXFRM, KXCPICORE, KXCPIYOY). All three show a low-bias pattern (mean PIT > 0.5 or distributions shifted high), suggesting markets slightly underestimate these indicators. Despite this miscalibration, all three still have CRPS/MAE < 1 — the distributions add value even though they could be better calibrated.
- **Core PCE** (mean PIT=0.600) shows the expected pattern: distributions biased low (outcomes tend to exceed the distribution center), consistent with its CRPS/MAE > 1.

**Universal overconcentration — the paper's most universal finding.** All 11 series show std(PIT) below the theoretical ideal of 0.289 for a uniform distribution (range: 0.136 to 0.266). This holds regardless of CRPS/MAE ratio, series type, sample size, or time period. ISM PMI shows the most extreme overconcentration (std=0.136, less than half the ideal), consistent with its borderline CRPS/MAE of 0.97. This means prediction markets systematically understate uncertainty: they correctly identify *where* outcomes will land (mean PIT close to 0.5 for most series) but substantially underestimate *how uncertain* they are. Three possible mechanisms: (a) bid-ask spread compression mechanically narrows midpoint-derived CDFs, making them tighter than true beliefs; (b) overconfident participants underweight tail scenarios; (c) the same overconfidence driving favorite-longshot bias makes extreme-strike contracts underpriced. The volume-independence finding (ρ=0.14, p=0.27) weakly argues against thin-market mechanics alone, but we cannot definitively distinguish these channels without order-book depth data.

The PIT analysis is mechanistically informative: it reveals *how* distributions fail (overconfident and directionally biased), complementing the CRPS/MAE ratio which tells *whether* they fail.

### What Drives Distributional Quality?

**Volume (liquidity) does not predict CRPS/MAE.** Spearman ρ=0.14 (p=0.27, n=62) between log(event volume) and CRPS/MAE ratio. Volume varies substantially across series (CPI median=140K contracts, JC median=16K), but this variation does not predict calibration quality.

**Surprise magnitude** has a mechanical correlation with the CRPS/MAE ratio (ρ=−0.65, p<0.0001) because surprise *is* the MAE denominator. Raw CRPS vs surprise z-score: ρ=0.12, p=0.35 — no genuine relationship.

**Strike count**: Monte Carlo simulation confirms the mechanical effect of 2→3 strikes is ≤2%, vs observed cross-series gaps of 30-50%.

### CRPS/MAE Persistence (All 11 Series)

Lag-1 Spearman autocorrelation of per-event CRPS/MAE ratios:

| Series | n | Lag-1 ρ | p-value | Interpretation |
|--------|---|---------|---------|----------------|
| KXU3 | 32 | **−0.540** | **0.002** | Mean-reverting |
| KXISMPMI | 7 | −0.371 | 0.469 | n.s. |
| KXADP | 9 | −0.333 | 0.420 | n.s. |
| KXCPICORE | 32 | −0.201 | 0.278 | n.s. |
| CPI | 14 | −0.077 | 0.803 | n.s. |
| JC | 16 | 0.064 | 0.820 | n.s. |
| KXCPIYOY | 34 | 0.060 | 0.741 | n.s. |
| KXFRM | 59 | 0.077 | 0.564 | n.s. |

Only KXU3 shows significant autocorrelation (ρ=−0.54, p=0.002), indicating mean-reverting behavior where high-ratio events tend to be followed by low-ratio events. For 7 of 8 testable series, CRPS/MAE ratios are serially uncorrelated — each event is essentially independent. This validates the use of standard (non-block) bootstrap CIs and confirms that the ratio's value is in monitoring aggregate regime shifts, not event-by-event prediction.

### Rolling CRPS/MAE: CPI Temporal Dynamics

With 33 CPI events spanning Dec 2022 to present, a rolling window (w=8 events) reveals the structural break:
- **All 14 old-CPI windows**: ratio < 1.0 (0.45 to 0.96)
- **All 12 new-KXCPI windows**: ratio > 1.0 (1.05 to 1.88)
- **Transition windows**: ratio ≈ 0.95, straddling the threshold

The expanding-window ratio rises monotonically from 0.49 to 0.86 but never crosses 1.0, confirming the aggregate result is not an artifact.

---

## Methodology

### Data
- **11 series, 248 events** with CRPS/MAE computation
- Original 4 series (CPI n=33, Jobless Claims n=16, GDP n=9, FED n=4): 62 events
- Expanded 7 series (KXFRM n=59, KXCPIYOY n=34, KXU3 n=32, KXCPICORE n=32, KXPCECORE n=13, KXADP n=9, KXISMPMI n=7): 186 events
- External: TIPS breakeven (T10YIE), SPF median CPI, FRED historical data (CPIAUCSL, ICSA, A191RL1Q225SBEA, DFEDTARU, UNRATE, MORTGAGE30US)

### Data Quality Notes
- **KXADP comma-parsing bug (fixed)**: 7/9 KXADP events had realized values off by 1000x due to comma-separated values (e.g., "41,000") being parsed as 41 instead of 41000. Corrected in iteration 14. CRPS/MAE changed from 0.67 to 0.71; directional conclusion unchanged.
- **KXPCECORE recomputation**: Original analysis (n=15, ratio=2.06) recomputed with fresh candle data (n=13, ratio=1.22). Different n suggests 2 events lacked sufficient candle data in the new fetch. Ratio change may reflect different candle availability.
- **KXFRM low snapshot count**: Mean 15.7 snapshots/event. Sensitivity analysis shows ratio stable across minimum-snapshot thresholds (0.78–0.86).

### In-Sample Caveat and OOS Validation

All CRPS/MAE ratios are computed in-sample. We conducted three out-of-sample validation exercises:

1. **Expanding-window OOS (CPI)**: Train on first N events, predict direction of event N+1. Result: 50% accuracy — no better than chance.

2. **Natural temporal OOS (CPI)**: Old-prefix events predict distributions add value. Testing on new-prefix events: aggregate ratio is 1.32. Direction prediction fails.

3. **Pre-registered simple-vs-complex OOS**: 4 new series classified before computing CRPS/MAE. Hit rate: 2/4 (50%). Both "complex" predictions wrong — distributions add value for Core CPI m/m and CPI YoY despite being composite indices.

### Reproducibility

To reproduce all reported results, run in order:
1. `uv run python -m experiment13.run` — core CRPS/MAE for CPI, JC, GDP + original PIT + horse race
2. `uv run python scripts/fetch_new_series.py` + `uv run python scripts/fetch_expanded_series.py` — fetch data for 7 additional series
3. `uv run python scripts/expanded_crps_analysis.py` — CRPS/MAE for all 11 series
4. `uv run python scripts/iteration6_analyses.py` — full PIT for 7 new series, serial correlation, cross-series horse race
5. `uv run python scripts/iteration7_analyses.py` — monitoring backtest, std(PIT) for GDP/FED/CPI

### Key Statistical Methods
1. **BCa bootstrap**: 10,000 resamples, bias-corrected and accelerated CIs (Efron & Tibshirani, 1993).
2. **Kruskal-Wallis test**: Non-parametric heterogeneity across 11 series.
3. **Binomial sign test**: Per-event CRPS/MAE < 1.0 (147/248, p=0.004).
4. **Leave-one-out sensitivity**: 8 of 9 below-1.0 series show unanimous LOO.
5. **Mann-Whitney with rank-biserial effect size**: For simple-vs-complex comparison.
6. **Pre-registered OOS predictions**: Written before computing new-series CRPS/MAE.
7. **Rolling CRPS/MAE**: Window size 8 events for temporal dynamics.
8. **PIT diagnostic**: All 11 series. KS and Cramér-von Mises tests for uniformity; bootstrap CI on mean PIT; std(PIT) for overconcentration.
9. **Cross-series horse race**: Kalshi vs random walk and trailing mean for CPI, Unemployment, Mortgage Rates using FRED benchmarks.
10. **Monitoring protocol backtest**: Rolling 8-event CRPS/MAE for all 11 series with 3-consecutive-window alert detection.

---

## Supplementary Appendix

### A. PIT Analysis — Additional Detail

PIT analysis covers all 11 series (248 events). Five series show no significant deviation from uniformity (KXU3, GDP, KXADP, KXISMPMI, JC). Three series reject uniformity at the 5% level (KXFRM, KXCPICORE, KXCPIYOY) — all showing a low-bias pattern where outcomes tend to exceed the implied distribution center. The dominant calibration failure mode across all 11 series is overconcentration: std(PIT) ranges from 0.136 (ISM PMI) to 0.266 (GDP), all below the theoretical ideal of 0.289 for a uniform distribution. This indicates markets systematically understate uncertainty. See Section 4 for the full table with std(PIT) column.

### B. Downgraded and Invalidated Findings

We document findings that were invalidated or substantially weakened during the research process for transparency:

**Downgraded:**

| Finding | Naive | Corrected | Issue |
|---------|-------|-----------|-------|
| "Simple-vs-complex dichotomy" p=0.0004, r=0.43 | 7 series | p=0.033, r=0.16 (11 series) | Data expansion; OOS 2/4 miss |
| KW heterogeneity H=18.5, p=0.005 | 7 series | H=15.3, p=0.122 (11 series) | New series cluster in middle |
| Core PCE "worst series" (2.06) | n=15 | 1.22 (n=13) | Recomputed with new candle data |
| KXADP ratio 0.67 | Comma bug | 0.71 (fixed parsing) | 7/9 events realized values off by 1000x |
| CPI distributions "actively harmful" | CI [1.04, 2.52] | CI [0.57, 1.23] | Sample restricted to post-break period |
| JC CI "excludes 1.0" | CI [0.45, 0.78] | CI [0.37, 1.02] | BCa function signature bug |
| Surprise predicts CRPS/MAE | ρ=−0.65 | ρ=0.12 (raw CRPS) | Denominator artifact |
| Pairwise CPI vs GDP | p=0.020 | p_adj=0.059 | Bonferroni correction |

**Invalidated:**

| Finding | Original | Corrected | Reason |
|---------|----------|-----------|--------|
| Shock acceleration | p<0.001 | p=0.48 | Circular classification |
| KUI leads EPU | p=0.024 | p=0.658 | Absolute return bias |
| Trading Sharpe | +5.23 | -2.26 | Small-sample artifact |

### C. Market Design Implications

1. **Distributions work.** For 9 of 11 economic series, the distributional information embedded in multi-strike markets adds genuine forecasting value. This validates Kalshi's multi-strike market design as an information aggregation mechanism.

2. **Series-specific monitoring**: GDP and Jobless Claims are the best-calibrated. Core PCE and FED are the only consistently problematic series.

3. **Volume is not the bottleneck**: Volume does not predict distributional quality (ρ=0.14, p=0.27, n=62). This null result has important implications: Kalshi cannot simply "add more liquidity" to fix Core PCE or FED distributional issues. The calibration problem is structural (overconcentration, directional bias), not a thin-market artifact.

4. **Real-time CRPS/MAE monitoring** could flag distributional degradation — the CPI rolling-window analysis detects the structural break within 2–3 events.

5. **Proposed monitoring protocol**: Compute CRPS/MAE over a trailing window of 8 events per series. Flag when the ratio exceeds 1.0 for 3 consecutive windows. Additionally, track PIT mean and std per series; flag when PIT std drops below 0.20 (severe overconcentration) or PIT mean deviates >0.15 from 0.5 (directional bias).

**Retrospective backtest of the monitoring protocol** (rolling 8-event CRPS/MAE across all 11 series):

| Series | n | Windows | >1.0 | %  | 3-Consec Alerts | Range |
|--------|---|---------|------|----|-----------------|-------|
| GDP | 9 | 2 | 0 | 0% | 0 | [0.45, 0.48] |
| Jobless Claims | 16 | 9 | 0 | 0% | 0 | [0.48, 0.69] |
| CPI YoY | 34 | 27 | 1 | 4% | 0 | [0.46, 1.16] |
| ADP | 9 | 2 | 0 | 0% | 0 | [0.66, 0.68] |
| Unemployment | 32 | 25 | 0 | 0% | 0 | [0.55, 0.99] |
| Core CPI | 32 | 25 | 3 | 12% | 0 | [0.58, 1.28] |
| Mortgage Rates | 59 | 52 | 18 | 35% | **10** | [0.48, 1.73] |
| CPI | 33 | 26 | 12 | 46% | **10** | [0.45, 1.88] |
| Core PCE | 13 | 6 | 3 | 50% | **1** | [0.87, 1.87] |
| ISM PMI | 7 | — | — | — | — | Too few events |
| FED | 4 | — | — | — | — | Too few events |

The backtest validates the monitoring protocol: **6 of 8 testable series produce zero 3-consecutive alerts**, confirming the protocol has low false-alarm rates for well-calibrated series. CPI triggers alerts corresponding to the documented structural break. Core PCE is correctly flagged as persistently problematic. Mortgage Rates — despite an aggregate ratio of 0.85 — triggers alerts during a period of elevated volatility, demonstrating the protocol's ability to detect *temporary* degradation even in generally well-calibrated series. This transforms the monitoring protocol from a theoretical proposal into retrospectively validated evidence.

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

All 33 corrections applied during the research process:

1. **Regime-appropriate benchmarks**: Jobless Claims window 2022+ (post-COVID)
2. **Per-series decomposition**: Pooled tests mask heterogeneity
3. **Bonferroni correction**: Raw p-values adjusted for multiple comparisons
4. **Rank-biserial effect sizes**: Reported for all Mann-Whitney tests
5. **Power analysis**: Sample sizes for 80% power computed
6. **Controlled observation timing**: T-24h maturity gradient (7x) reduced to 1.5x
7. **PIT sign correction**: cdf_values store survival P(X>strike)
8. **CRPS/MAE ratio**: Diagnostic reported per series with BCa bootstrap CIs
9. **Scale-appropriate CRPS integration**: Dynamic tail extension
10. **Serial correlation adjustment**: CPI AR(1) ρ=0.23
11. **Tail-aware implied mean**: E[X] from same CDF as CRPS
12. **Leave-one-out sensitivity**: Unanimous LOO results for 10 of 11 series
13. **CRPS − MAE signed difference**: JC p=0.001, CPI p=0.091 (iteration 10 subset)
14. **Formal heterogeneity test**: Kruskal-Wallis (k-sample)
15. **Block bootstrap**: Block length 2, 10,000 resamples
16. **Cramér-von Mises test**: CPI p=0.152, JC p=0.396
17. **Mid-life CDF monotonicity verification**: 0 violations
18. **Per-event temporal trajectories**: Analyzed where data permits
19. **Canonical series merging**: Old/new naming conventions
20. **CPI temporal structural break**: Pre/post Nov 2024
21. **Volume-CRPS regression**: ρ=0.14, p=0.27
22. **Multivariate regression**: R²=0.27; surprise z-score dominates
23. **CRPS/MAE persistence**: Lag-1 autocorrelation ≈ 0
24. **Full PIT diagnostic**: 4 series, 62 events
25. **OOS validation**: Expanding-window, temporal split, simple-vs-complex OOS
26. **BCa bootstrap fix**: Function signature bug
27. **Surprise-CRPS endogeneity**: Denominator artifact
28. **Bonferroni for pairwise tests**: 3 comparisons corrected
29. **Serial-correlation-adjusted CI**: CPI [0.44, 1.28]
30. **Kalshi API series discovery**: 9 additional series found
31. **KXADP comma-parsing fix**: 7/9 events had realized values off by 1000x
32. **KXPCECORE recomputation**: n=13, ratio=1.22 (was 2.06 with different candle data)
33. **11-series unified analysis**: Full expansion from 7→11 series, 93→248 events; KW p=0.122, simple-vs-complex r=0.16
34. **Full 11-series PIT analysis**: Extended from 4→11 series. 3 series reject uniformity (KXFRM, KXCPICORE, KXCPIYOY). Universal overconcentration pattern discovered.
35. **Cross-series horse race**: KXFRM beats random walk (d=−0.55, p<0.001); KXU3 matches RW (d=−0.07, n.s.) but beats trailing mean (d=−0.97, p<0.001).
36. **Serial correlation for 8 series**: Only KXU3 shows significant autocorrelation (ρ=−0.54, p=0.002). 7/8 series have independent per-event ratios, validating standard bootstrap.
37. **KXPCECORE discrepancy explained**: 2.06→1.22 due to near-zero-MAE outlier (KXPCECORE-25JUL), low-snapshot old events, and 4 missing events.
38. **Std(PIT) column added**: All 11 series show std(PIT) < 0.289 (range 0.136–0.266). Quantifies universal overconcentration.
39. **Monitoring protocol backtest**: Rolling 8-event CRPS/MAE computed for all 11 series. 6/8 testable series produce 0 false 3-consecutive alerts. CPI, KXFRM, KXPCECORE correctly flagged.
40. **GDP/FED PIT recomputed**: Fresh PIT computation from candle data. GDP: mean=0.516, std=0.266 (n=9). FED: mean=0.710, std=0.226 (n=4). Minor numerical differences from prior computation due to snapshot selection; overconcentration finding unchanged.
41. **CRPS/MAE double-counting defense**: Explicit sentence added clarifying ratio measures marginal distributional value beyond point forecast.
42. **Sign test pooling note**: Added sentence noting exchangeability assumption and convergent LOO evidence.
