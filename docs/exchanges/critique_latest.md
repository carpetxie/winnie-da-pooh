# Critique — Iteration 1

STATUS: CONTINUE

## Overall Assessment (2-3 sentences)

A well-structured empirical paper with a genuinely useful diagnostic (CRPS/MAE ratio) and a compelling heterogeneity finding. The core insight — that distributional quality varies dramatically across event series — is both novel and actionable. However, a scale-dependent bug in the CRPS tail integration systematically biases the Jobless Claims headline number, and the paper has not yet incorporated the confidence intervals and hedged language described in the iteration-3 researcher response.

## Reflection on Prior Feedback

A researcher response from a prior loop (iteration 3) exists, describing changes including bootstrap CIs on headline ratios, CPI claim hedging, PIT-mechanism connections, and phrasing fixes. However, **the paper in `docs/findings.md` has not been updated to reflect these changes** — the abstract still says "actively harmful" for CPI without hedging, the CRPS/MAE table lacks a CI column, and the trader callout still says "63% more information." The researcher's analysis in that response was sound (e.g., CPI CI [0.83, 2.04] includes 1.0), so these changes should be implemented, not just described.

## Scores
| Criterion | Score | Delta | Comment |
|-----------|-------|-------|---------|
| Novelty | 7/10 | — | CRPS/MAE ratio as a per-series diagnostic is a genuine contribution. Not groundbreaking but useful and actionable. |
| Methodological Rigor | 5/10 | — | Scale-dependent CRPS bug, missing CIs on headlines, mid-life snapshot choice unjustified. |
| Economic Significance | 7/10 | — | Actionable for traders (use JC distributions, ignore CPI spread) and market designers (series-specific calibration quality). |
| Narrative Clarity | 7/10 | — | Clean structure, honest about limitations. Transparency appendix (Section C) is excellent. |
| Blog Publishability | 5/10 | — | Needs the CI/hedging changes applied and the CRPS bug fixed before it represents Kalshi well. |

## Seed Questions

### 1. Is the CRPS/MAE ratio genuinely useful, or trivial repackaging?

**Genuinely useful, with caveats.** The ratio operationalizes a question traders actually care about: "Should I use the full distribution or just the point forecast?" The per-series decomposition is the key insight — pooling across series would hide the heterogeneity. The paper correctly notes this isn't a mathematical bound (CRPS ≤ MAE holds only for well-calibrated distributions, not all distributions). However, the paper should be clearer that when CRPS/MAE > 1, this is specifically a signal of *distributional miscalibration* — the market's implied distribution is worse than a point mass at the implied mean, which is a strong statement.

### 2. Does the heterogeneity finding have practical implications for Kalshi's market design?

**Yes, substantially.** If Kalshi can identify which series produce well-calibrated distributions (weekly, low-dimensional signals) vs. poorly calibrated ones (monthly composites), they could: (a) adjust the number of strikes offered, (b) provide calibration warnings to traders, (c) prioritize liquidity incentives for series where distributions add value. The release-frequency hypothesis is testable as more series accumulate.

### 3. Are there claims that overreach the evidence?

**Yes, several:**
- "Distributions add massive value (63% gain)" for Jobless Claims — the "63%" figure is (1 - 0.37) × 100, which measures CRPS improvement over MAE, not "information gain." This phrasing conflates scoring improvement with information content.
- "CPI distributions are actively harmful" — as the iteration-3 response correctly identified, the CI [0.83, 2.04] includes 1.0. The current paper doesn't reflect this.
- The SPX comparison (2.8% vs 2.7%) compares hourly Kalshi snapshots to daily SPX data. The paper acknowledges this but still presents them side-by-side in a comparison table, which implicitly invites apples-to-apples reading.

### 4. What's missing that would make this substantially stronger?

See "The One Big Thing" and "Must Fix" below.

### 5. If this were on the Kalshi blog, would it enhance or damage Kalshi's research credibility?

**Enhance, after fixes.** The transparency appendix showing downgraded/invalidated findings is remarkable and builds trust. The per-series heterogeneity finding is genuinely informative. But publishing with the current overclaims on CPI (without CIs) and an unfixed CRPS computation bug would risk credibility with quantitative readers.

## The One Big Thing

**The `tail_extension=1.0` parameter in `compute_crps()` is scale-inappropriate for Jobless Claims and introduces a systematic downward bias in Jobless Claims CRPS.**

In `experiment12/distributional_calibration.py` (line 41), the default `tail_extension=1.0` defines how far beyond the min/max strikes to integrate:

```python
x_min = strikes[0] - tail_extension  # e.g., 200000 - 1.0 = 199999
x_max = strikes[-1] + tail_extension  # e.g., 250000 + 1.0 = 250001
```

For **CPI** (strikes from -0.1 to 0.6), this extends 1.0 percentage points — generous, covering the entire range beyond strikes. For **Jobless Claims** (strikes from 200,000 to 270,000), this extends **1 unit** on a 200K-scale domain — **effectively zero tail coverage**.

**Concrete impact:** KXJOBLESSCLAIMS-25SEP11 has realized=263,000 but max_strike=250,000. The code filters the realized value from the breakpoint list because 263,000 > x_max=250,001. This truncates ~13,000 of CRPS from the upper tail (the integral of F(x)²=1 from 250,001 to 263,000). The reported CRPS is 13,652; the true CRPS is approximately 26,000+.

**Aggregate effect:** Correcting this one event shifts the mean JC CRPS from 4,840 to ~5,653, and the CRPS/MAE ratio from 0.37 to ~0.44. The qualitative conclusion survives (still well below 1.0), but the headline number changes meaningfully. Other events where realized values land near strike boundaries may also have smaller biases.

**Fix:** Replace `tail_extension=1.0` with a scale-appropriate value, e.g.:
```python
strike_range = strikes[-1] - strikes[0]
tail_extension = max(strike_range * 0.5, 1.0)
```

This is a ~5-line fix that materially changes the headline number. It should be the top priority.

## Other Issues

### Must Fix (blocks publication)

1. **Apply the iteration-3 changes to the actual paper.** The researcher response describes adding CIs, hedging the CPI claim, changing "63% more information" to "63% CRPS improvement," and connecting PIT to mechanisms. None of these appear in `docs/findings.md`. These are substantive improvements that have been analyzed and agreed upon but not implemented.

2. **Add bootstrap CIs to the CRPS/MAE table.** (Subsumed by #1 above, but emphasizing: the two numbers the paper is built around have no uncertainty quantification in the current text.)

3. **Fix the code comment contradiction in `horse_race.py` line 378.** The methodology notes state "CRPS <= MAE is a mathematical identity for any proper distribution" — this is false. CRPS ≤ MAE holds only when the distribution is well-calibrated. The paper's own Section 2 correctly explains this ("this is a diagnostic property of calibration quality, not a mathematical bound"). Fix the code comment to match the paper.

### Should Fix (strengthens paper)

1. **Justify the mid-life snapshot choice for CRPS.** The code uses `snapshots[len(snapshots) // 2]` (experiment13/run.py line 179) — the midpoint of the market's life. Why not the final snapshot (when the market is most informed), or an average across the last N hours? This is a consequential analytical choice with no justification in the paper. Different snapshot choices could materially change the CPI CRPS numbers, especially for events like KXCPI-25JUN (n=438 snapshots) where early vs. late distributions may differ substantially.

2. **Add Jobless Claims PIT analysis.** The paper has a CPI PIT analysis (Appendix A) showing mean PIT=0.61, but no equivalent for Jobless Claims. Since JC is the stronger finding, a PIT analysis showing uniformity (or near-uniformity) would powerfully complement the CPI non-uniformity result and provide direct evidence that JC distributions are well-calibrated in a way CPI is not.

3. **The `implied_mean` calculation ignores tail probability.** In `experiment7/implied_distributions.py` line 207, the implied mean is computed by normalizing only to interior probability (`total_interior`), discarding `prob_below_min` and `prob_above_max`. For events with substantial tail probability (e.g., CPI events at boundary strikes), this biases the implied mean toward the interior. The paper should note this limitation, and ideally assign tail mass to the boundary midpoints (e.g., allocate `prob_below_min` to a point at `min_strike - half_spacing`).

4. **Sensitivity test: CRPS at different snapshot times.** Run the CRPS analysis at 10%, 25%, 50%, 75%, and 90% of market life (the temporal data already exists in Phase 5) and report the CRPS/MAE ratio at each timepoint. This would show whether the ratio is stable or if it improves as markets mature — directly connecting Section 2's main result to Section 4's maturity analysis.

5. **The trailing mean benchmark in `horse_race.py` is weak for early events.** For the first event (KXCPI-24NOV), `get_trailing_mean_forecast` returns a hardcoded 0.25, and for the second event it uses only one data point. Consider using FRED historical CPI data to construct the trailing mean rather than relying on the internal `REALIZED_MOM_CPI` dict, which creates circularity for early events.

6. **Report median CRPS/MAE alongside mean.** With n=14-16 and skewed CRPS distributions (per-event ratios range from 0.35 to 4.51 for CPI), the mean ratio is heavily influenced by outliers. The median per-event ratio would be more robust and may tell a different story.

### Acknowledged Limitations (inherent, not actionable)

1. **Small n (14-16 per series).** Fundamental constraint of available data. Cannot be fixed without waiting months.
2. **Two-series comparison.** The release-frequency hypothesis cannot be tested with only CPI and Jobless Claims. Need additional series (PCE, mortgage applications, etc.).
3. **In-sample evaluation.** Train/test splitting at n=14-16 is impractical. The paper acknowledges this correctly.
4. **Serial correlation in CPI releases.** Sequential monthly CPI values have AR(1) structure, reducing effective degrees of freedom below 14. The code acknowledges this (experiment13/run.py Phase 7) but the paper doesn't quantify the impact.
5. **The SPX benchmark comparison mixes temporal granularity** (hourly vs. daily). The paper acknowledges this caveat clearly.

## Verdict

**MAJOR REVISIONS**

The CRPS tail_extension bug is a genuine computational error that affects the headline number. Combined with the unapplied iteration-3 changes (CIs, hedging), the paper needs substantive revision before it's ready for the Kalshi blog. The fixes are straightforward — a few lines of code and applying already-agreed textual changes — but they must be done before the numbers can be trusted.

## Convergence Assessment

This is iteration 1, so convergence is not yet applicable. The paper has strong bones — the core insight is sound, the transparency is exemplary, and the structure is clean. The main issues are: (1) a fixable code bug, (2) unapplied textual improvements, and (3) missing robustness checks (JC PIT, snapshot sensitivity, median ratios). I expect 2-3 more iterations to reach publication quality, assuming the researcher addresses the tail_extension bug and applies the pending changes.
