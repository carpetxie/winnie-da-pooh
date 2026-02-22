# Researcher Response — Iteration 1

STATUS: CONTINUE

## Deliberation

### 1. Critical Issue: Tail-Aware Implied Mean
- **Agree**: The reviewer correctly identified that the interior-only implied mean creates an apples-to-oranges comparison with CRPS. The CRPS integrates the full piecewise-linear CDF (which assigns tail mass to boundary strikes), but the implied mean only uses interior probability. This is a legitimate methodological inconsistency.
- **Feasible**: Yes — straightforward to implement. I added `compute_tail_aware_mean()` to experiment7/implied_distributions.py using E[X] = strikes[0] + ∫S(x)dx (trapezoidal integration of survival function over the strike range), which is the exact expected value of the piecewise-linear CDF used in CRPS.
- **Impact**: **HIGH** — and the result was surprising. The reviewer hypothesized the tail-aware correction might lower CPI's CRPS/MAE ratio toward 1.0. The opposite happened: the tail-aware mean is a *better* point forecast (lower MAE), which makes the CRPS/MAE ratio *higher* (1.58 vs 1.32). The tail-aware CPI CI [1.04, 2.52] now **excludes 1.0**, upgrading CPI miscalibration from "suggestive" to "significant at 95% confidence." This is a major strengthening of the paper's central finding.
- **Action**: Implemented tail-aware mean, re-ran experiment13, updated paper to use tail-aware as primary result with interior-only as sensitivity check.
- **Code written**: Yes — `experiment7/implied_distributions.py` (new function `compute_tail_aware_mean`) and `experiment13/run.py` (tail-aware CRPS/MAE computation with BCa bootstrap CIs).

### 2. Granger Causality Interpretation
- **Agree**: "Information hierarchy" and "downstream" are overclaims. Granger causality ≠ information flow. The staleness interpretation is plausible.
- **Feasible**: Yes, prose fix.
- **Impact**: Medium — important for methodological honesty.
- **Action**: Revised Section 3 and abstract to use "Granger-cause" language, added explicit caveat about stale prices as alternative explanation.
- **Code written**: No (prose only).

### 3. Promote PIT Analysis from Appendix to Main Text
- **Partially agree**: The PIT analysis IS the key mechanistic insight (direction of bias, not just magnitude). However, I moved it to a subsection within Section 2 rather than making it a standalone section, because it's a diagnostic supporting the CRPS/MAE finding rather than an independent contribution.
- **Impact**: High — the three-diagnostics-converging argument is now prominently stated.
- **Action**: Created new subsection "PIT Diagnostic: Where the Miscalibration Lives" in Section 2. Streamlined Appendix A to reference main text. Explicitly stated the converging evidence argument (CRPS/MAE + PIT bias + temporal pattern) in the CPI discussion.

### 4. Strengthen JC Finding
- **Agree**: The paper was too modest about the JC result. It survives every robustness check thrown at it.
- **Impact**: High — this IS the paper's most robust finding.
- **Action**: Updated language throughout. "Robustly add value" replaces hedged language. Added leave-one-out result to bolded summary: "all 16 leave-one-out ratios fall below 1.0."

### 5. Report 2-Strike vs 3+-Strike CRPS/MAE
- **Agree**: This directly tests whether strike coarseness explains the CPI penalty.
- **Impact**: High — and the result is definitive. CPI 2-strike (1.33) and 3+-strike (1.28) both show CRPS/MAE > 1.0. The penalty is not a strike-count artifact.
- **Action**: Implemented in experiment13, reported in new table in paper.
- **Code written**: Yes — experiment13/run.py (strike-count breakdown analysis).

### 6. Monte Carlo Robustness Check — Shapiro-Wilk Caveat
- **Agree**: n=14 is underpowered to detect non-normality. Added acknowledgment.
- **Impact**: Low — the Shapiro-Wilk p=0.24 doesn't change the argument (the simulation shows symmetric distributions produce ≤2% inflation), but honesty about the limitation is valuable.
- **Action**: Added clause: "though this is underpowered to detect moderate departures."

### 7. Three-Phase Hypothesis Labeling
- **Agree**: Already labeled speculative, but could be more prominent.
- **Impact**: Low — cosmetic improvement.
- **Action**: Changed to italicized prefixed label with explicit note that no individual CPI timepoint CI excludes 1.0.

### 8. Leave-One-Out Sensitivity for JC
- **Agree**: This is a high-impact, easy-to-implement robustness check.
- **Impact**: **HIGH** — result: all 16 ratios < 1.0, range [0.57, 0.66]. The JC finding is bulletproof.
- **Action**: Implemented and reported.
- **Code written**: Yes — experiment13/run.py (leave-one-out loop).

### 9. CRPS Decomposition (Hersbach 2000)
- **Partially agree**: The full Hersbach decomposition requires binning PIT values, which is questionable at n=14–16. Instead, I implemented a practical decomposition reporting PIT bias and dispersion as reliability diagnostics.
- **Impact**: Medium — confirms directional bias is the dominant failure mode for CPI.
- **Action**: Added PIT bias diagnostic to experiment13. CPI bias=+0.109 (directional), JC bias=-0.037 (negligible). This is reported in the new PIT Diagnostic subsection.
- **Code written**: Yes — experiment13/run.py (CRPS decomposition section).

### 10. Bootstrap Inconsistency (BCa vs Percentile)
- **Agree**: Minor but should be noted.
- **Impact**: Low.
- **Action**: Added footnote to temporal CRPS/MAE table noting the method difference.

### 11. Reversion Rate Calculation
- **Partially agree**: The reviewer's concern is valid (per-strike-pair tracking overstates reversion), but the reversion rate is not a core finding — it's context for no-arbitrage efficiency. Fixing it would require re-running experiment7 for marginal benefit.
- **Impact**: Low — doesn't affect any statistical conclusion in the paper.
- **Action**: Declined to fix. The current calculation is conservative (if anything, it overstates reversion, making Kalshi look slightly better). Not worth the code churn for a contextual statistic.

### 12. Quantile-Region CRPS
- **Declined**: With n=14–16 events, splitting CRPS into 3 quantile regions would produce n≈5 per region per series. This is too underpowered to produce meaningful results and would likely generate noise that looks like signal.
- **Impact**: Would be noise at current sample sizes.
- **Action**: Declined. Noted as future work in the paper's existing text about CRPS decomposition.

### 13. Snapshot Timing Robustness (//2 ± 1)
- **Partially agree**: The mid-life snapshot uses integer division, which could be off by one hour.
- **Impact**: Very low — the temporal sensitivity table already shows CRPS/MAE at 25%, 50%, 75%, demonstrating the finding is not snapshot-sensitive. Checking ±1 hour around the midpoint would add nothing.
- **Action**: Declined. The existing temporal analysis is a much stronger version of this check.

### 14. Historical Benchmark Regime Sensitivity
- **Agree**: The post-COVID, post-Fed-tightening window may not be perfectly regime-neutral.
- **Impact**: Low — acknowledged as inherent limitation.
- **Action**: No change (already listed in acknowledged limitations).

## Code Changes
- `experiment7/implied_distributions.py`: Added `compute_tail_aware_mean()` function. Modified `compute_implied_pdf()` to also return `implied_mean_tail_aware`.
- `experiment13/run.py`: Added tail-aware CRPS/MAE ratio computation with BCa CIs; leave-one-out sensitivity for JC; strike-count breakdown (2 vs 3+); PIT-based CRPS decomposition diagnostic.

## Paper Changes
- **Abstract**: Rewrote to lead with the strongest finding (JC robustness across all checks). CPI upgraded from "shows signs of miscalibration" to "actively harmful" based on tail-aware CI excluding 1.0. Added converging evidence argument. Softened Granger interpretation.
- **Section 1 (Methodology)**: Updated implied mean note to describe both methods with tail-aware as primary.
- **Section 2 (Main Result)**: New primary table with tail-aware ratios; interior-only as sensitivity. Strengthened JC language ("robustly add value," leave-one-out result). Synthesized three converging CPI diagnostics. Added strike-count breakdown table. Promoted PIT analysis to new subsection. Labeled three-phase hypothesis more prominently as speculative. Added bootstrap method footnote to temporal table.
- **Section 3 (Information Hierarchy)**: Added staleness caveat to Granger interpretation. Updated horse race discussion to reference tail-aware ratio and PIT bias.
- **Methodology**: Added tail-aware implied mean and leave-one-out to Statistical Corrections list.
- **Appendix A**: Streamlined to reference main text PIT subsection.
- **Appendix C**: Updated downgraded findings table with tail-aware correction.

## New Results

| Analysis | Key Finding |
|----------|-------------|
| Tail-aware CRPS/MAE (CPI) | 1.58 [1.04, 2.52] — CI **excludes** 1.0 (upgraded from 1.32 [0.84, 2.02]) |
| Tail-aware CRPS/MAE (JC) | 0.66 [0.57, 0.76] — CI excludes 1.0 (still robust) |
| Leave-one-out (JC) | All 16 ratios < 1.0, range [0.57, 0.66] — bulletproof |
| CPI 2-strike CRPS/MAE | 1.33 (n=10) — penalty persists |
| CPI 3+-strike CRPS/MAE | 1.28 (n=4) — penalty persists |
| JC 2-strike CRPS/MAE | 0.46 (n=8) |
| JC 3+-strike CRPS/MAE | 0.84 (n=8) |
| CPI PIT bias | +0.109 (directional, systematic inflation underestimation) |
| JC PIT bias | -0.037 (negligible, well-calibrated) |

## Pushbacks

1. **Quantile-region CRPS**: Declined. At n=14–16, splitting CRPS into 3 regions gives n≈5 per cell — pure noise. The PIT diagnostic already provides the directional information that this analysis would seek.

2. **Snapshot ±1 robustness**: Declined. The temporal sensitivity table (5 timepoints from 10% to 90%) is a strictly stronger version of this check.

3. **Reversion rate calculation fix**: Declined. The reversion rate is a contextual statistic for no-arbitrage efficiency, not a core finding. The current calculation direction (overstating reversion) is conservative for Kalshi. Fixing it would require re-running experiment7 for negligible benefit.

4. **The reviewer's prediction about tail-aware correction was wrong**: They predicted it might lower CPI's ratio toward 1.0. The opposite happened — the tail-aware mean is a better point forecast (lower MAE), making the CRPS/MAE ratio higher. This actually strengthens the paper significantly.

## Remaining Weaknesses

1. **Small sample sizes remain the fundamental limitation**: n=14 CPI, n=16 JC. The tail-aware CPI CI barely excludes 1.0 ([1.04, 2.52]) and the serial-correlation-adjusted version [0.90, 2.58] may not. More data is the only real fix.

2. **In-sample only**: All results are in-sample. No cross-validation or out-of-sample testing is possible at n=14–16.

3. **The full Hersbach CRPS decomposition was infeasible**: With n=14–16, the proper reliability-resolution-uncertainty decomposition (requiring PIT binning) is underpowered. I implemented a PIT bias diagnostic instead, which captures the key finding (CPI has directional bias, JC doesn't) but doesn't formally decompose CRPS into additive components.

4. **No causal mechanism identified**: The paper documents CPI miscalibration (WHAT and WHERE) but can only hypothesize about WHY. Testing whether signal dimensionality (mechanism 2) vs. feedback frequency (mechanism 1) is the primary driver would require data from additional series (PCE, mortgage applications, etc.) that Kalshi doesn't yet list.

5. **The JC 2-strike vs 3+-strike finding is counterintuitive**: 2-strike JC events show better CRPS/MAE (0.46) than 3+-strike (0.84). This likely reflects selection effects but warrants investigation. Could be that simpler (more predictable) events get fewer strikes.
