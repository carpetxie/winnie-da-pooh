# Critique — Iteration 4

STATUS: CONTINUE

## Overall Assessment

The paper has reached a high standard of rigor. The iteration 3 additions — CPI leave-one-out and formal heterogeneity tests — were exactly the right moves and substantially strengthen both claims. Every major finding now has multiple independent lines of evidence. The remaining issues are about narrative polish for blog readability, one code-level inconsistency in the heterogeneity test, and a missed opportunity to foreground the paper's most interesting insight (point vs distributional quality decoupling) as a co-headline finding.

## Reflection on Prior Feedback

Across iterations 1–3, the most impactful suggestions were: (1) tail-aware implied mean (iteration 1 — transformed both headline numbers), (2) leave-one-out analysis (iteration 1 — now the backbone of both series' robustness), and (3) signed-difference test (iteration 2 — JC p=0.001 is the single most robust test in the paper). The researcher's self-directed additions in iteration 3 (CPI LOO, formal heterogeneity test) were the right calls — I should have flagged these earlier.

Dead ends I'm dropping permanently: CRPS decomposition (infeasible at n=14, correctly declined), quantile-region CRPS (declined iteration 1 with good justification), snapshot ±1 sensitivity (declined iteration 1). The iteration 2 must-fix items (worked example error, serial correlation CI prose error) have been addressed — the worked example now uses KXJOBLESSCLAIMS-25JUN12 with correct numbers, and the serial correlation CI is correctly described as including 1.0.

The iteration 2 metric inconsistency concern (tail-aware primary but interior-only in sub-analyses) has been largely resolved: the horse race now uses tail-aware (horse_race.py lines 244–246 confirmed), the temporal table shows both specifications, and LOO is reported for both. The paper now correctly labels per-event ratios as interior-only with an explanatory note about tail-aware instability. This is well-handled.

## Scores
| Criterion | Score | Delta | Comment |
|-----------|-------|-------|---------|
| Novelty | 7/10 | +0 | Stable. CRPS/MAE diagnostic and per-series heterogeneity remain genuinely new |
| Methodological Rigor | 8/10 | +1 | CPI LOO + heterogeneity test close the gap. One code inconsistency remains |
| Economic Significance | 7/10 | +0 | Market design implications strong but the point-vs-distribution decoupling is underplayed |
| Narrative Clarity | 7/10 | +0 | Thorough but long for a blog post. Dual-metric reporting still creates cognitive load |
| Blog Publishability | 8/10 | +1 | Very close. One code fix + narrative tightening → accept |

## Strength of Claim Assessment

### Claim 1: "Jobless Claims distributions robustly add value (CRPS/MAE=0.66, CI [0.57, 0.76])"
**Evidence level: Conclusive. Correctly labeled.** Five independent lines of evidence: (1) CI excluding 1.0 under both mean specifications, (2) serial-correlation-adjusted CI still excluding 1.0, (3) all 16 LOO ratios below 1.0 (both specifications), (4) PIT near 0.5, (5) signed-difference test p=0.001 (14/16 negative). The tail-aware temporal analysis showing CIs exclude 1.0 at all five timepoints is the strongest possible temporal robustness. No change needed.

### Claim 2: "CPI distributions are actively harmful (CRPS/MAE=1.58, CI [1.04, 2.52])"
**Evidence level: Conclusive (converging evidence). Correctly labeled.** The CPI LOO (all 14 ratios > 1.0) transforms this from "suggestive-to-conclusive" to "conclusive." The serial-correlation-adjusted CI includes 1.0, and the paper now correctly describes this. The four-diagnostics convergence argument is compelling and well-stated. No change needed on claim strength.

### Claim 3: "Kalshi outperforms random walk (p_raw=0.015, p_adj=0.059, d=-0.71)"
**Evidence level: Suggestive, but the paper undersells it.** With d=-0.71 (large effect) and the power analysis showing the test is already at >80% power (n=14 available, n=13 needed), calling this "borderline significant" understates the result. The p_adj=0.059 misses 0.05 by a hair, but the effect size is large and the test is adequately powered. **Consider strengthening:** "significant at the 10% level after Bonferroni correction, with a large effect size (d=-0.71) and adequate statistical power" is more accurate than "borderline significant."

### Claim 4: "The CPI–JC divergence is statistically significant (permutation p<0.001, MWU p=0.003)"
**Evidence level: Conclusive, but with a code inconsistency.** The permutation test (ratio-of-means) is robust. The Mann-Whitney uses per-event tail-aware ratios, which the paper elsewhere identifies as unstable (see Robustness section below). The result is almost certainly robust to using interior-only ratios instead, but this should be verified.

## Novelty Assessment

Novelty is stable at 7/10. The CRPS/MAE diagnostic and per-series heterogeneity finding remain the core contributions. I don't see additional novelty to extract without new data or scope expansion.

**Underemphasized finding — the point-vs-distribution decoupling:** The paper's finding that CPI point forecasts beat all benchmarks (MAE=0.068, d=-0.71 vs random walk) while CPI distributions are actively harmful (CRPS/MAE=1.58) is, in my view, the single most interesting insight for the prediction market literature. This decoupling — accurate means with miscalibrated spreads — hasn't been documented this clearly before. The paper mentions it ("the irony deepens") but buries it as a subsidiary observation in the horse race section. For the Kalshi blog audience (traders deciding whether to use the distribution or just the midpoint), this IS the actionable headline. **Consider making this a co-headline alongside the CRPS/MAE diagnostic itself.**

## Robustness Assessment

### Code Issue: Mann-Whitney Heterogeneity Test Uses Unstable Per-Event Ratios

I verified in the data (lines 645–646 of experiment13/run.py) that the Mann-Whitney test uses `point_crps_tail_aware` for per-event ratios. These include extreme outliers caused by near-zero MAE denominators:

| Event | Tail-Aware Ratio | Interior Ratio |
|-------|-----------------|----------------|
| KXJOBLESSCLAIMS-26JAN29 | **10.36** | 1.20 |
| KXCPI-25MAY | **14.63** | 2.14 |
| KXCPI-25JUN | **21.50** | 4.51 |

The Mann-Whitney is rank-based, so outlier magnitudes don't affect the result. The JC outlier (10.36) actually works *against* finding heterogeneity by ranking alongside CPI events. So p=0.003 is conservative if anything. However, this creates an **internal inconsistency**: the paper explicitly acknowledges tail-aware per-event ratio instability and uses interior-only for the per-event discussion section, but then the formal heterogeneity test — a marquee statistical result — silently uses these same unstable ratios.

The fix is simple: run the Mann-Whitney with interior-only per-event ratios as a robustness check and report both. With 10/14 CPI events > 1.0 and 12/16 JC events < 1.0 (interior-only), the separation should be at least as strong. The permutation test (ratio-of-means) is already immune to this issue.

### KXJOBLESSCLAIMS-26JAN29: A Useful Illustration

This event's tail-aware mean (209,350) was extremely close to realized (209,000), producing MAE=350 vs CRPS=3,625 — a per-event ratio of 10.36. Interior-only gives MAE=3,018 and ratio=1.20. The aggregate ratio-of-means is unaffected (LOO dropping this event: 0.64–0.69), confirming the headline finding is robust. But this event is the perfect illustration of why the paper correctly prefers ratio-of-means over mean-of-ratios — if you averaged per-event ratios, this single event would dominate the JC result. The paper acknowledges the instability in general terms but doesn't give this specific JC example. Mentioning it would strengthen the methodological argument.

### Verified Code-Paper Alignment (Iteration 4)

| Claim | Code/Data | Status |
|-------|-----------|--------|
| Horse race uses tail-aware | horse_race.py lines 244–246 | ✓ |
| Temporal analysis has tail-aware CIs | run.py lines 963–997 | ✓ |
| CPI LOO all 14 > 1.0 (tail-aware) | run.py lines 618–632 | ✓ |
| JC LOO both specs reported | run.py lines 556–602 | ✓ |
| Permutation test preserves CRPS-MAE pairing | run.py lines 655–670 | ✓ |
| Kalshi CPI MAE = 0.068 (tail-aware) | crps_per_event.csv | ✓ (0.0683) |
| Worked example uses KXJOBLESSCLAIMS-25JUN12 | findings.md | ✓ |
| Serial correlation CI "includes 1.0" | findings.md | ✓ (fixed from iteration 2) |
| CRPS/MAE headline numbers | crps_per_event.csv | ✓ (CPI 1.576→1.58, JC 0.660→0.66) |

### Minor Code Issue: Dead CRPS Decomposition Stub

Phase 4 of experiment13/run.py contains a stubbed-out Hersbach reliability computation (`reliability = 0.0` with a `pass` loop body). This is dead code that won't affect results but could mislead future contributors. Either remove it or comment it with: `# Hersbach (2000) decomposition deferred: infeasible at n<20 per series`.

## The One Big Thing

**Tighten the narrative for blog readability and foreground the point-vs-distribution decoupling as a co-headline.** The paper's methodological thoroughness is its strength for academic credibility but its weakness for blog accessibility. The abstract is 150+ words and leads with the diagnostic rather than the actionable insight. The dual-metric reporting (interior-only and tail-aware for every analysis) creates cognitive load.

Concrete suggestions:
1. **Restructure the abstract** to lead with the decoupling insight: "Prediction market point forecasts and distributional forecasts can diverge dramatically in quality. We introduce the CRPS/MAE ratio as a diagnostic..."
2. **Consolidate dual-metric reporting.** Make tail-aware the sole in-text metric. Move interior-only results to a "Sensitivity: Interior-Only Mean" subsection or appendix. The paper already treats tail-aware as primary — make this cleaner.
3. **Add a visual "Practical Takeaway" box** after Section 2 with 3 bullet points: (a) use JC distributions, (b) use CPI point forecasts only, (c) the CRPS/MAE ratio tells you which regime you're in. This gives traders an immediate entry point.
4. **Compress the Monte Carlo strike-count simulation** — move the simulation details (distributional families, parameter choices) to an appendix and keep only the punchline in the main text ("≤5% of the observed gap under distributional assumptions consistent with our data").

## Other Issues

### Must Fix (blocks publication)

1. **Run interior-only Mann-Whitney as a robustness check for the heterogeneity test.** In experiment13/run.py around line 645, add:
   ```python
   cpi_per_event_int = cpi_events["kalshi_crps"].values / np.maximum(cpi_events["point_crps"].values, 1e-10)
   jc_per_event_int = jc_events["kalshi_crps"].values / np.maximum(jc_events["point_crps"].values, 1e-10)
   u_int, p_int = stats.mannwhitneyu(cpi_per_event_int, jc_per_event_int, alternative='two-sided')
   ```
   Report both the tail-aware and interior-only Mann-Whitney p-values in the paper. If both < 0.01, the heterogeneity finding is airtight across metric specifications. This resolves the internal inconsistency between acknowledging per-event tail-aware instability and using those same ratios in a formal test.

### Should Fix (strengthens paper)

1. **Strengthen the random walk horse race language.** "Borderline significant" with d=-0.71 and >80% power undersells the result. Consider: "The tail-aware Kalshi implied mean outperforms random walk with a large effect size (d=−0.71, p_adj=0.059), significant at the 10% level after Bonferroni correction. The power analysis confirms this test has adequate power (>80%) at the observed effect size."

2. **Mention KXJOBLESSCLAIMS-26JAN29 as a concrete example of ratio instability.** In the per-event discussion, add: "For example, KXJOBLESSCLAIMS-26JAN29 has a tail-aware per-event ratio of 10.36 (vs interior-only 1.20) because the tail-aware mean nearly matched the realized value by coincidence (MAE=350). The aggregate ratio-of-means (0.66) is immune to this instability."

3. **Remove the dead CRPS decomposition code** in Phase 4 of run.py, or add a comment explaining why it's stubbed out.

4. **Compress dual-metric reporting for blog readability.** Currently every analysis reports both tail-aware and interior-only. For the blog version, consider moving interior-only to a supplementary section, keeping it accessible but not cluttering the main narrative.

### New Experiments / Code to Write

1. **Interior-only Mann-Whitney heterogeneity test** (5 lines, described in Must Fix #1). Priority: high.

2. **Per-event CRPS/MAE scatter/strip visualization for the blog.** Generate a figure showing per-event CRPS/MAE (interior-only, y-axis) vs event (x-axis), color-coded by series (CPI red, JC blue), with a horizontal line at 1.0. This would be the single most compelling visualization for a blog audience — it immediately shows the series separation. The paper mentions a strip chart exists in experiment outputs but it's not included in the paper itself.

3. **Ratio-of-means vs mean-of-ratios comparison.** Add a brief comparison showing how the two aggregation methods differ:
   ```
   | Estimator | CPI | JC |
   | Ratio-of-means (primary) | 1.58 | 0.66 |
   | Median per-event | 1.60 | 0.65 |
   | Mean-of-ratios | ~X.X | ~X.X |
   ```
   The mean-of-ratios will be dominated by the extreme events (KXCPI-25JUN at 21.5, KXJOBLESSCLAIMS-26JAN29 at 10.4 for tail-aware), dramatically illustrating why ratio-of-means is the correct estimator.

4. **Blog-formatted "key findings" summary.** Write a 200-word standalone summary suitable for a blog lede, structured as: (1) the question, (2) the diagnostic, (3) the answer (it depends on the series), (4) the practical implication. This could be a new subsection or replace the current abstract.

### Acknowledged Limitations (inherent, not actionable)

1. **Small sample sizes (n=14 CPI, n=16 JC).** Inherent. Well-handled with power analysis and LOO.
2. **In-sample only.** Cannot be fixed at current n. Correctly flagged.
3. **Only two series with sufficient data.** Heterogeneity finding would be far more interesting with 5+ series. Inherent to current Kalshi offerings.
4. **No causal mechanism identified.** Four hypotheses are reasonable but untestable without additional series or non-public data.
5. **Per-event tail-aware ratios inherently unstable.** Mathematical property, not a bug. Correctly documented.

## Verdict

**MINOR REVISIONS**

The paper is very close to publishable. The core findings are well-supported by multiple independent lines of evidence. The iteration 3 additions (CPI LOO, heterogeneity test) were exactly what was needed. The one must-fix item (interior-only Mann-Whitney robustness) is a 5-line code change. The should-fix items are polish: narrative compression, stronger horse race language, and a concrete ratio-instability example. After these changes, this paper enhances Kalshi's research credibility and is ready for the blog.
