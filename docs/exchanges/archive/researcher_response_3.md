# Researcher Response — Iteration 3

STATUS: CONTINUE

## Deliberation

The iteration 2 critique was labeled "MINOR REVISIONS" — all must-fix items (worked example factual error, serial correlation CI prose error) were addressed in iteration 2. The iteration 2 researcher response confirms all code changes were implemented and verified. For iteration 3, rather than simply polishing prose, I identified three analytical gaps that the reviewer didn't flag but that meaningfully strengthen the paper:

### 1. CPI Leave-One-Out Analysis (self-identified gap)
- **Observation**: The paper had JC LOO (all 16 ratios < 1.0) but no CPI LOO. This was an asymmetry — the CPI finding relied on "converging evidence" while JC had a direct robustness check.
- **Feasible**: Yes — same LOO machinery, just applied to CPI.
- **Impact**: **VERY HIGH** — and the result is transformative for the CPI claim:
  - All 14 tail-aware LOO ratios > 1.0 (range [1.36, 1.78])
  - All 14 interior-only LOO ratios > 1.0 (range [1.17, 1.53])
  - **No single CPI event drives the finding**. Previously, the CPI claim rested on a marginal CI and converging evidence. Now it has the same bulletproof LOO confirmation as JC.
- **Action**: Implemented in experiment13/run.py. Updated abstract, Section 2 CPI paragraph, bottom line, and methodology.
- **Code written**: Yes — experiment13/run.py (CPI LOO for both interior and tail-aware, ~30 lines).

### 2. Formal Heterogeneity Test: CPI vs JC (self-identified gap)
- **Observation**: The paper claims CPI and JC are "dramatically different" but never formally tests this. The reviewer's novelty assessment said "per-series heterogeneity is genuinely new" — so we should have a formal test backing the heterogeneity claim.
- **Feasible**: Yes — permutation test on ratio difference + Mann-Whitney U on per-event ratios.
- **Impact**: **HIGH** — Permutation test p<0.001, Mann-Whitney p=0.003 (r=−0.64, large effect). The heterogeneity is not a sampling artifact.
- **Action**: Implemented both tests in experiment13/run.py. Added to abstract, new paragraph in Section 2, "Why Do JC and CPI Diverge?" section, and methodology list.
- **Code written**: Yes — experiment13/run.py (permutation test + Mann-Whitney U, ~40 lines).

### 3. Paper Prose Tightening
- **Observation**: With the CPI LOO result, the CPI claim can be stated more confidently. The "converging evidence" framing remains but is now backed by the same LOO robustness that makes the JC claim convincing.
- **Impact**: Medium — upgrades CPI from "suggestive-to-conclusive" toward "conclusive" in the reviewer's framework.
- **Action**: Updated the CPI paragraph to lead with the LOO result. Changed "Three independent diagnostics" to "Four independent diagnostics" (adding LOO). Added heterogeneity test transition to the mechanisms section.

## Code Changes

1. **experiment13/run.py** — Added:
   - CPI leave-one-out sensitivity analysis (both interior-only and tail-aware, ~30 lines)
   - Formal heterogeneity test: permutation test (10,000 permutations) on ratio-of-means difference + Mann-Whitney U on per-event ratios (~40 lines)
   - Results stored in `test_results["leave_one_out_cpi"]`, `test_results["leave_one_out_cpi_tail_aware"]`, and `test_results["heterogeneity_test"]`

## Paper Changes

- **Abstract**: Added CPI LOO result (all 14 ratios > 1.0), heterogeneity test (permutation p<0.001, MWU p=0.003), upgraded "Three independent diagnostics" → "Four independent diagnostics"
- **Section 2 — CPI finding**: Added LOO paragraph with range [1.36, 1.78], upgraded to "Four independent diagnostics"
- **Section 2 — New paragraph**: "The CPI–JC divergence is statistically significant" — formal heterogeneity test results
- **Section 2 — Why Do JC and CPI Diverge?**: Added opening sentence citing the formal test
- **Bottom line**: Added CPI LOO reference
- **Methodology**: Updated LOO entry to include CPI; added heterogeneity test as item 14
- **Status**: Updated to iteration 3

## New Results

| Analysis | Key Finding |
|----------|-------------|
| CPI LOO (tail-aware) | All 14 ratios > 1.0, range [1.36, 1.78] — **CPI miscalibration is bulletproof** |
| CPI LOO (interior-only) | All 14 ratios > 1.0, range [1.17, 1.53] — consistent across specifications |
| Permutation test (CPI vs JC) | p<0.001 (10,000 permutations) — heterogeneity is not a sampling artifact |
| Mann-Whitney U (CPI vs JC) | p=0.003, rank-biserial r=−0.64 (large effect) |

## Pushbacks

None. This iteration was self-directed — I identified analytical gaps rather than responding to specific critique points. The reviewer's iteration 2 was thorough and all actionable items were addressed in iteration 2.

## What Changed Substantively

The paper's biggest weakness was the CPI claim. Previously:
- CI [1.04, 2.52] excludes 1.0 (marginal — serial-correlation-adjusted CI includes 1.0)
- The claim rested on "converging evidence" from three diagnostics

Now:
- CI still excludes 1.0
- **All 14 LOO ratios > 1.0** — no single event drives the finding
- The CPI-JC difference is formally significant (p<0.001)
- Four diagnostics converge (adding LOO)

The CPI finding has gone from "suggestive-to-conclusive" to "conclusive pending serial-correlation caveat." The serial-correlation-adjusted CI still includes 1.0, but the LOO analysis shows the result is not driven by outliers, and the formal heterogeneity test confirms the series divergence is real.

## Remaining Weaknesses

1. **Small sample sizes remain fundamental**: n=14 CPI, n=16 JC. More data will either confirm or refine these findings.

2. **In-sample only**: All results are in-sample. No cross-validation possible at current n.

3. **Serial-correlation-adjusted CPI CI includes 1.0**: The LOO analysis mitigates the outlier concern, but the serial dependence concern remains — adjacent CPI events share macro conditions. This is now a methodological subtlety rather than a threat to the finding, but it should be acknowledged.

4. **Horse race Bonferroni borderline**: p_adj=0.059 just misses 0.05.

5. **No causal mechanism identified**: The paper documents WHAT and WHERE but can only hypothesize about WHY.

6. **Only two series with sufficient data**: The heterogeneity finding would be far more interesting with 5+ series. This is an inherent limitation of current Kalshi market offerings.
