# Researcher Response — Iteration 1

STATUS: CONTINUE

## Deliberation

### 1. The One Big Thing: CRPS tail_extension bug
- **Agree**: Fully agree. The reviewer correctly identified that `tail_extension=1.0` is scale-inappropriate for Jobless Claims (200K+ scale). The integration domain was effectively `[199999, 250001]`, truncating CRPS for realized values outside this range.
- **Feasible**: Yes, straightforward fix.
- **Impact**: HIGH. This was the most consequential change. The fix changed the headline number more than the reviewer predicted:
  - JC CRPS: 4,840 → **7,748**
  - JC CRPS/MAE: 0.37 → **0.60** (reviewer estimated ~0.44)
  - JC vs Historical Wilcoxon: p=0.047 → **p=0.372** (no longer significant at any level!)
- **Action**: Fixed `compute_crps()` to use scale-appropriate tail extension: `max(strike_range * 0.5, 1.0)`. Also added coverage of realized values beyond strike boundaries (`x_min = min(strikes[0] - ext, realized - ext)`). Updated all numbers throughout the paper. Added this correction to the Downgraded findings table in Appendix C.

The qualitative conclusion survives (0.60 < 1.0, distributions add value) but the effect is substantially more modest. The Wilcoxon vs Historical test is now thoroughly non-significant, which required rewriting the CRPS vs Historical section. This is a healthy correction.

### 2. Apply iteration-3 changes to the paper
- **Partially disagree**: The reviewer states "the abstract still says 'actively harmful' for CPI without hedging, the CRPS/MAE table lacks a CI column, and the trader callout still says '63% more information.'" However, examining the paper as it stood:
  - The abstract says "CPI distributions show signs of miscalibration... though the penalty is not statistically conclusive at n=14" — this IS hedged.
  - The CRPS/MAE table DOES have a CI column with [0.83, 2.04] and [0.25, 0.55].
  - The trader callout says "63% CRPS improvement" — NOT "63% more information."
  - The paper correctly states "CI includes 1.0" for CPI.
- **Impact**: LOW. The iteration-3 changes were already applied. The reviewer appears to have been comparing against a stale version.
- **Action**: No additional changes needed for this point. The hedging language, CIs, and corrected phrasing were already present. (The numbers have now changed due to the tail-extension fix, so I updated 63% → 40% and all CI values.)

### 3. Code comment contradiction in horse_race.py line 378
- **Agree**: The comment says "CRPS <= MAE is a mathematical identity for any proper distribution" which is false. CRPS <= MAE holds for well-calibrated distributions, not all distributions.
- **Feasible**: Yes, one-line fix.
- **Impact**: LOW (code comment only, doesn't affect results).
- **Action**: Fixed. Updated comment to correctly state this is a property of well-calibrated distributions, not a universal identity.

### 4. Justify mid-life snapshot choice
- **Agree**: Valid critique. The mid-life choice was unexplained.
- **Feasible**: Yes — addressed both by adding a justification sentence AND by running the snapshot sensitivity analysis (critique point #4 under "Should Fix").
- **Impact**: MEDIUM. The sensitivity analysis turned out to be very informative — it revealed a non-monotonic CPI pattern.
- **Action**: Added justification in Section 1 methodology, and added new "Snapshot Sensitivity" subsection in Section 2 with CRPS/MAE at 10/25/50/75/90% of market life. Key finding: JC CRPS/MAE < 1 at all timepoints (robust), CPI shows non-monotonic pattern (worst at 25-50%, better at 10% and 75-90%).

### 5. Add Jobless Claims PIT analysis
- **Agree**: Excellent suggestion. JC is the stronger finding, and PIT analysis provides independent confirmation.
- **Feasible**: Yes, straightforward extension of existing CPI PIT code.
- **Impact**: MEDIUM-HIGH. The JC PIT result (mean=0.46, KS p=0.35) is directly consistent with CRPS/MAE < 1 and provides a clean contrast with CPI PIT (mean=0.61). This strengthens the heterogeneity narrative.
- **Action**: Extended Phase 6c to compute PIT for both CPI and JC. Updated Appendix A from "CPI PIT Analysis" to "PIT Analysis (CPI and Jobless Claims)" with side-by-side comparison.

### 6. implied_mean tail probability limitation
- **Agree**: Valid concern. The code normalizes to interior probability only.
- **Feasible**: Fixing the code would require choosing a point for tail mass allocation (e.g., min_strike - half_spacing), which introduces its own assumptions.
- **Impact**: LOW. This affects MAE calculations but not CRPS (which integrates the full CDF). The practical impact is small since most events have modest tail probability.
- **Action**: Added a note in Section 1 documenting this limitation rather than changing the code, which would introduce new assumptions.

### 7. Sensitivity test: CRPS at different snapshot times
- **Agree**: Valuable robustness check, directly addresses the mid-life concern.
- **Feasible**: Yes, Phase 5 already computed temporal CRPS.
- **Impact**: HIGH. Extended Phase 5 to also compute CRPS/MAE (not just CRPS/Uniform) at each timepoint. Results are very informative — see Snapshot Sensitivity section above.
- **Action**: Modified experiment13/run.py Phase 5 to compute point MAE at each snapshot. Added new Snapshot Sensitivity table to paper.

### 8. Trailing mean benchmark weakness for early events
- **Partially agree**: The hardcoded fallback (0.25 for first event) is inelegant but reasonable — 0.25% was approximately the 2024 average MoM CPI. Using FRED historical CPI would be cleaner but the impact on results is negligible (affects 1-2 of 14 events).
- **Impact**: LOW. The random walk benchmark (which IS significant) doesn't have this issue.
- **Action**: Declined. The 0.25% fallback is documented and defensible. Changing the benchmark mid-analysis risks looking like p-hacking.

### 9. Report median CRPS/MAE alongside mean
- **Agree**: Easy and useful, especially with skewed distributions.
- **Feasible**: Yes, trivial computation.
- **Impact**: LOW-MEDIUM. Added median per-event ratios. CPI median=1.38 (close to mean 1.32), JC median=0.67 (close to mean 0.60). The means and medians tell the same story, which is reassuring.
- **Action**: Added median per-event ratio column to CRPS/MAE table and modified experiment13 to compute and report it.

## Changes Made

### Code changes:
1. **`experiment12/distributional_calibration.py`**: Fixed `compute_crps()` tail_extension from fixed `1.0` to scale-appropriate `max(strike_range * 0.5, 1.0)`. Also added coverage of realized values beyond strike boundaries. This is the critical bug fix.
2. **`experiment13/horse_race.py`**: Fixed misleading code comment about CRPS <= MAE being a "mathematical identity."
3. **`experiment13/run.py`**:
   - Phase 4: Added median per-event CRPS/MAE ratio and bootstrap CIs to CRPS/MAE computation.
   - Phase 5: Added point MAE computation at each temporal snapshot for CRPS/MAE sensitivity.
   - Phase 6c: Expanded PIT analysis from CPI-only to both CPI and Jobless Claims, with bootstrap CIs on mean PIT.

### Paper changes (`docs/findings.md`):
1. **Abstract**: Updated JC CRPS/MAE from 0.37 to 0.60, CI from [0.25, 0.55] to [0.45, 0.78]. Added JC PIT finding. Changed "63% CRPS improvement" to "40%."
2. **Trader callout**: Updated from 63% to 40% CRPS improvement.
3. **Section 1**: Added justification for mid-life snapshot choice. Added note about implied_mean tail probability limitation.
4. **Section 2 CRPS/MAE table**: Updated all JC numbers. Added median per-event column.
5. **Section 2 CRPS vs Historical**: Completely rewritten. JC Wilcoxon now p=0.372 (was 0.047). Removed claim about effect size being "well-powered" since effect size itself changed.
6. **New: Snapshot Sensitivity subsection**: CRPS/MAE at 10/25/50/75/90% of market life. Shows JC robust across all timepoints, CPI non-monotonic.
7. **Temporal CRPS Evolution**: Updated with corrected numbers.
8. **Power Analysis table**: Updated JC effect size from r=0.49 to r=0.10 (much weaker after correction).
9. **Appendix A**: Expanded from CPI PIT to CPI + JC PIT with side-by-side comparison table.
10. **Appendix B**: Updated GDP CRPS number.
11. **Appendix C**: Added two new entries to Downgraded findings: JC CRPS/MAE (0.37→0.60) and JC vs Historical (p=0.047→p=0.372).
12. **Methodology**: Added item 9 (scale-appropriate CRPS integration) to Statistical Corrections.

## Pushbacks

1. **"Apply iteration-3 changes" (Must Fix #1)**: The reviewer claims these changes were not applied. They were. The abstract was already hedged, the table already had CIs, and the trader callout already said "CRPS improvement" not "information." I suspect the reviewer was comparing against a cached or older version. No additional action needed on this point.

2. **Trailing mean benchmark (Should Fix #5)**: The reviewer suggests using FRED historical CPI instead of the internal REALIZED_MOM_CPI dict. While technically cleaner, changing the benchmark after seeing results would look like specification search. The 0.25% fallback for the first event is documented and reasonable. Declined.

## Remaining Weaknesses

1. **The JC Wilcoxon result is now non-significant.** The tail-extension fix turned the p=0.047 result into p=0.372. The CRPS/MAE ratio (0.60, CI [0.45, 0.78]) remains the primary evidence, but the paper now relies on a single metric rather than two corroborating tests. This is honest but weaker.

2. **Power for the JC vs Historical test is now very poor.** The effect size shrank from r=0.49 to r=0.10, requiring n=152 instead of n=6. This test is essentially useless at current sample sizes.

3. **The CPI snapshot sensitivity pattern (non-monotonic) is unexplained.** Why would CPI distributions be well-calibrated early and late but worst at mid-life? This is interesting but I don't have a compelling mechanism. It could be noise at n=14.

4. **Serial correlation in CPI.** The paper acknowledges this in the methodology but doesn't quantify the effective degrees of freedom reduction. At n=14, even a modest AR(1) coefficient could halve effective n.

5. **Two-series limitation.** Still can't test the release-frequency hypothesis with only CPI and JC. Need PCE, mortgage applications, or other series.

## Convergence Assessment

This iteration made the largest changes so far — a critical bug fix that materially altered the headline numbers, plus three new analyses (JC PIT, snapshot sensitivity, median ratios). The paper is significantly more honest and robust. The core insight survives (heterogeneous distributional value-add) but the evidence is more nuanced.

The next iteration should focus on:
- Whether the snapshot sensitivity pattern for CPI is robust or noise
- Whether the paper's framing needs to shift given the weaker JC effect
- Any remaining overclaims that need hedging

Not yet converged — the framing adjustments to accommodate the corrected numbers may need refinement.
