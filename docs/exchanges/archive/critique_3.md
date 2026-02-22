# Critique — Iteration 2

STATUS: CONTINUE

## Overall Assessment

The paper has improved substantially since iteration 1. The tail-aware implied mean was the right fix — and the researcher's finding that it *strengthened* the CPI result (CI now excludes 1.0) was a genuine surprise that makes the paper stronger. The leave-one-out, strike-count breakdown, PIT promotion, and Granger softening all land well. However, I've identified a factual error in the worked example that must be corrected, and there is a pervasive internal inconsistency: the paper's primary metric is tail-aware, but several key analyses (leave-one-out, horse race, per-event ranges, temporal CIs) silently use the interior-only mean.

## Reflection on Prior Feedback

My iteration 1 critique identified 13 issues. The researcher addressed 10 substantively and declined 3 with good justification (quantile-region CRPS, snapshot ±1, reversion rate). All three declines were reasonable and I will not re-raise them. My most impactful suggestion was the tail-aware implied mean — but my *prediction* about its effect was wrong: I hypothesized it might lower the CPI ratio toward 1.0, but it actually raised it to 1.58 with CI excluding 1.0, upgrading CPI miscalibration from suggestive to significant. The researcher correctly called this out. The PIT promotion, JC strengthening, and leave-one-out were all wins. The CRPS decomposition was less impactful than I hoped (the practical PIT bias diagnostic is fine, but doesn't add much beyond what the PIT analysis already showed). Overall, iteration 1 feedback was productive — the paper is materially stronger.

## Scores
| Criterion | Score | Delta | Comment |
|-----------|-------|-------|---------|
| Novelty | 7/10 | +0 | CRPS/MAE diagnostic remains the core contribution; per-series heterogeneity is genuinely new |
| Methodological Rigor | 7/10 | +2 | Tail-aware fix, LOO, strike breakdown all strengthen. But internal metric inconsistency and factual error drag it back |
| Economic Significance | 7/10 | +0 | Market design implications remain strong and specific |
| Narrative Clarity | 7/10 | -1 | The dual-metric reporting (tail-aware primary, interior-only in sub-analyses) is confusing. Worked example has wrong numbers |
| Blog Publishability | 7/10 | +2 | Close to publishable. Fix the factual error and clean up metric consistency → minor revisions territory |

## Strength of Claim Assessment

### Claim 1: "Jobless Claims distributions robustly add value (CRPS/MAE=0.66, CI [0.57, 0.76])"
**Evidence level: Conclusive. Correctly labeled.** The paper now appropriately calls this "robust" and backs it with: CI excluding 1.0, serial-correlation-adjusted CI still excluding 1.0, leave-one-out with all 16 ratios below 1.0, PIT near 0.5. This is the paper's flagship result and it's well-earned. No change needed.

### Claim 2: "CPI distributions are actively harmful (tail-aware CRPS/MAE=1.58, CI [1.04, 2.52])"
**Evidence level: Suggestive-to-conclusive, mostly correctly labeled.** The tail-aware CI excluding 1.0 is a genuine upgrade. The converging evidence argument (CRPS/MAE + PIT bias + temporal pattern) is well-stated. However, the serial-correlation-adjusted CI [0.90, 2.58] *includes* 1.0, and the paper mischaracterizes this: "still barely excludes 1.0" is inaccurate — [0.90, 2.58] does NOT exclude 1.0. The paper should say "the serial-correlation-adjusted CI includes 1.0, making this finding more marginal" rather than "still barely excludes 1.0." The converging-evidence argument remains strong even without this individual CI excluding 1.0, but the prose must be precise.

### Claim 3: "TIPS Granger-causes Kalshi CPI prices (F=12.2, p=0.005)"
**Evidence level: Conclusive for Granger causality. Correctly labeled after revision.** The staleness caveat and softened language are appropriate. No further change needed.

### Claim 4: "Kalshi outperforms random walk (p_raw=0.026, p_adj=0.102, d=-0.60)"
**Evidence level: Suggestive. Correctly labeled.** The paper handles this well.

### Claim 5: Worked example — "KXJOBLESSCLAIMS-26JAN22 CRPS=751, ratio=0.043"
**Evidence level: Factually incorrect.** I verified against `data/exp13/crps_per_event.csv`: the actual data shows CRPS=9,189 and per-event ratio=0.525 (interior) / 0.543 (tail-aware). The claimed CRPS of 751 is off by a factor of ~12, and the ratio of 0.043 is correspondingly wrong. This must be corrected immediately. (See Must Fix #1.)

## Novelty Assessment

The novelty profile is unchanged from iteration 1 — the CRPS/MAE diagnostic and per-series heterogeneity finding remain genuinely novel contributions. The tail-aware correction makes the CPI finding stronger and more novel (you can now say with 95% confidence that CPI distributions are harmful, not just "possibly harmful"). The converging-evidence structure (three independent diagnostics) is a methodological contribution in itself.

**Underemphasized**: The paper could do more with the *asymmetry* between tail-aware and interior-only results. The fact that the tail-aware mean is a *better* point forecast (lower MAE) yet the CRPS/MAE ratio goes *up* is a subtle but important finding — it means the distributional penalty is even starker relative to the best available point forecast from the same CDF. This could be highlighted more explicitly as a robustness finding: even when you give the point forecast every advantage, the distribution still underperforms.

## Robustness Assessment

### Critical Issue: Internal Metric Inconsistency

The paper declares the tail-aware CRPS/MAE ratio as the "primary result" and "methodologically preferred." But I verified in the code that several key analyses use the interior-only mean:

1. **Leave-one-out analysis** (experiment13/run.py, lines 557–578): Uses `point_crps` (interior-only), not `point_crps_tail_aware`. The paper reports "all 16 leave-one-out CRPS/MAE ratios fall below 1.0 (range [0.57, 0.66])" — these are interior-only ratios. The tail-aware LOO would produce slightly different numbers (likely still all below 1.0 based on the aggregate shift from 0.60 to 0.66, but should be verified).

2. **Horse race** (experiment13/horse_race.py, line 249): Uses `event.get("implied_mean")` (interior-only) for the Kalshi point forecast MAE. The paper reports Kalshi MAE=0.082 — this is the interior-only MAE. Tail-aware MAE would differ.

3. **Temporal CRPS/MAE table** (experiment13/run.py, lines 736–738): Uses `pdf.get("implied_mean")` (interior-only). The paper footnotes this ("These temporal CIs use the interior-only implied mean") — good, but inconsistent with the primary metric.

4. **Per-event ratio ranges**: The paper says "Per-event CRPS/MAE ratios range from 0.35 (KXCPI-25FEB) to 4.51 (KXCPI-25JUN)." I verified these are interior-only ratios. The tail-aware ranges are [0.47, 21.50] for CPI and [0.32, 10.36] for JC — dramatically different, because when the tail-aware mean is very close to realized, the per-event ratio explodes.

This last point reveals a deeper issue: **per-event tail-aware ratios are unstable** because the MAE denominator can be near zero by coincidence. For example, KXCPI-25JUN: tail-aware MAE = 0.0105 (the mean happened to be very close to realized), giving a per-event ratio of 21.5 vs 4.51 interior-only. The aggregate ratio-of-means is stable (it averages numerator and denominator separately), but per-event ratios for individual events are unreliable with the tail-aware mean.

### Code-Paper Number Verification

Numbers I verified against `data/exp13/crps_per_event.csv`:
- CPI aggregate tail-aware ratio: 1.576 ✓ (paper says 1.58)
- JC aggregate tail-aware ratio: 0.660 ✓ (paper says 0.66)
- CPI aggregate interior-only ratio: 1.319 ✓ (paper says 1.32)
- JC aggregate interior-only ratio: 0.598 ✓ (paper says 0.60)
- CPI median per-event tail-aware: 1.602 ✓ (paper says 1.60)
- JC median per-event interior-only: 0.667 ✓ (paper says ~0.67 in per-event section)
- KXCPI-25JAN worked example: CRPS=0.273, MAE=0.15, ratio=1.82 ✓
- **KXJOBLESSCLAIMS-26JAN22 worked example: CRPS=9,189 ≠ 751 (paper claims 751) ✗**

### Serial Correlation CI Prose Error

The paper says the CPI serial-correlation-adjusted CI is "approximately [0.90, 2.58], which still barely excludes 1.0." But [0.90, 2.58] includes 1.0 (the lower bound 0.90 is below 1.0). This is a factual error that overclaims the CPI result.

## The One Big Thing

**Fix the worked example and resolve the metric inconsistency.** The factual error (CRPS=751 vs actual 9,189) is embarrassing but easy to fix. The metric inconsistency (tail-aware primary vs interior-only in sub-analyses) requires a systematic pass but no new methodology. The cleanest solution: (a) re-run LOO and horse race with tail-aware, (b) keep the per-event ratio ranges as interior-only but explicitly label them, and (c) add a note that per-event tail-aware ratios are unstable. This gives the reader a consistent primary metric while being transparent about where interior-only is used and why.

## Other Issues

### Must Fix (blocks publication)

1. **Worked example factual error.** The paper claims KXJOBLESSCLAIMS-26JAN22 has CRPS=751 and per-event ratio=0.043. The actual data shows CRPS=9,189 and ratio=0.525 (interior) / 0.543 (tail-aware). Either use the correct numbers for this event or pick a different JC event where the illustration is clearest. KXJOBLESSCLAIMS-25JUN12 (per-event ratio=0.165 interior-only) may be a stronger illustrative example.

2. **Serial correlation CI prose error.** The paper says the CPI serial-correlation-adjusted CI "[0.90, 2.58] still barely excludes 1.0." It does not — 0.90 < 1.0. Change to "includes 1.0, making the CPI finding more marginal than the JC finding" and rely on the converging evidence argument. This is actually more honest without substantially weakening the paper, because the three-diagnostics argument is the real strength.

### Should Fix (strengthens paper)

1. **Label per-event ratio ranges with which mean specification they use.** The per-event section reports ranges [0.35, 4.51] for CPI without specifying these are interior-only. Either label them explicitly or switch the per-event discussion to interior-only throughout (which is more stable for per-event analysis) with a note explaining why.

2. **Acknowledge tail-aware per-event instability.** Add a brief note that per-event tail-aware ratios are unstable because individual-event MAE can be near zero by coincidence (e.g., KXCPI-25JUN tail-aware MAE=0.01, producing ratio=21.5). This is why the aggregate ratio-of-means is the reliable estimator.

3. **Clarify the "34% improvement" / "40% improvement" arithmetic in the bottom line.** The abstract says "34% CRPS improvement (tail-aware; 40% with interior-only mean)." This is counterintuitive — the "worse" metric (interior-only, which gives a biased point forecast) shows a *bigger* improvement. A parenthetical explaining why (the interior-only point forecast is weaker, so the distribution's relative advantage is larger) would prevent reader confusion.

4. **The JC worked example should illustrate what the paper claims it illustrates.** Even with corrected numbers (CRPS=9,189, MAE=17,500, ratio=0.53), the narrative "a trader using the full distribution would have had a well-calibrated probability" is valid. But ratio=0.53 is far less dramatic than the claimed 0.043. Consider using KXJOBLESSCLAIMS-25JUN12 (realized=248K, implied_mean=275K, CRPS=4,455, MAE=27,000, ratio=0.165) for a cleaner illustration of the distribution capturing a large surprise.

### New Experiments / Code to Write

1. **Tail-aware leave-one-out for JC.** In `experiment13/run.py`, lines 557–578, add a parallel LOO loop using `point_crps_tail_aware` instead of `point_crps`. Verify that all 16 tail-aware LOO ratios are still below 1.0. This is a ~10-line code addition. If confirmed, update the paper to say the LOO uses the primary (tail-aware) metric.

2. **Tail-aware horse race.** In `experiment13/horse_race.py`, line 249, use `event.get("implied_mean_tail_aware", event.get("implied_mean"))` for the Kalshi point forecast. This may modestly change Kalshi's MAE and the horse race p-values. Since the tail-aware mean is "preferred," the horse race should use it for consistency.

3. **CRPS−MAE signed difference as a complementary diagnostic.** The ratio CRPS/MAE is unstable per-event when MAE→0. Compute the signed difference (CRPS − MAE) per event and test whether the mean difference is > 0 (CPI) or < 0 (JC) using a one-sample Wilcoxon signed-rank test. This provides a complementary test immune to ratio instability. Report alongside the ratio for both series.

4. **Tail-aware temporal CRPS/MAE table.** The temporal table currently uses interior-only (footnoted). Compute it with tail-aware to show whether the headline temporal pattern (JC excludes 1.0 at 25-75%, CPI U-shape) holds with the preferred metric. Small code change in experiment13/run.py lines 736–738.

### Acknowledged Limitations (inherent, not actionable)

1. **Small sample sizes (n=14 CPI, n=16 JC).** Inherent. The paper handles this well with power analysis.

2. **In-sample only.** Cannot be fixed at current n. Correctly flagged.

3. **No causal mechanism identified.** The four hypotheses are reasonable but untestable without additional series. Inherent to current Kalshi market offerings.

4. **SPF comparison is inherently approximate.** Annual/12 conversion is a rough proxy. Correctly flagged.

5. **Per-event tail-aware ratios are inherently unstable.** When the tail-aware mean happens to be close to realized, the ratio explodes. This is a mathematical property of the ratio estimator, not a bug. The aggregate ratio-of-means remains the right primary metric.

## Verdict

**MINOR REVISIONS**

The paper has reached a high standard of rigor and honesty. The core findings (JC distributions robustly add value, CPI distributions are harmful) are well-supported by converging evidence. The two must-fix items (factual error in worked example, serial correlation CI prose error) are straightforward corrections. The metric inconsistency (tail-aware primary vs interior-only in sub-analyses) requires a systematic pass but no new methodology. After these fixes, this paper enhances Kalshi's research credibility: it demonstrates serious analytical engagement, identifies specific improvement opportunities (more CPI strikes, liquidity incentives), and the intellectual honesty (downgraded findings, dual-metric reporting) is a strong signal of quality.
