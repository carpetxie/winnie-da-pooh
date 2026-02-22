# Researcher Response — Iteration 8

STATUS: CONTINUE

## Deliberation

### 1. The One Big Thing: Per-event temporal CRPS/MAE trajectories
- **Agree**: Strongly. This is the most important remaining analytical gap. The reviewer correctly identified that the three-phase hypothesis occupies ~300 words of prime real estate and needs empirical backing.
- **Feasible**: Yes — implemented in ~120 lines added to experiment13/run.py (Phase 7C).
- **Impact**: **HIGH** — The results are clarifying: 50% of CPI events show the U-shape, which is a "population-level tendency" rather than universal. This is honest and strengthens credibility. The Wilcoxon tests for mid > early (p=0.134) and mid > late (p=0.196) don't reach significance, and early-mid Spearman ρ=0.06 means early quality doesn't predict mid-life quality.
- **Action**: Implemented full per-event trajectory analysis. Rewrote the three-phase hypothesis paragraph to report the per-event data honestly: 50% U-shape, not statistically confirmed at the individual test level, but visible at the median level (0.80 → 1.60 → 0.89). This is the right framing — a population tendency, not a universal law.
- **Code written**: Yes — experiment13/run.py Phase 7C (~120 lines). Computes per-event trajectories at 10%/50%/90%, classifies patterns, runs Wilcoxon and Spearman tests, checks CDF monotonicity at mid-life.

### 2. Expand JC 2-strike vs 3+-strike discussion
- **Agree**: Completely. The finding that JC 2-strike (0.46) < 3+-strike (0.84) creates genuine tension with the "add more CPI strikes" recommendation. The reviewer correctly identified this was underplayed.
- **Feasible**: Yes, and I went further — added a Mann-Whitney significance test (Phase 7D).
- **Impact**: **HIGH** — The significance test reveals p=0.028, r=0.66 (large effect). This is a genuine finding: more strikes *can* hurt distributional quality. This transforms a one-sentence observation into a statistically significant result with market design implications.
- **Action**: (1) Expanded the strike-count paragraph from 1 sentence to a full discussion acknowledging the tension. (2) Added a liquidity caveat to the market design recommendation. (3) Added Mann-Whitney test code.
- **Code written**: Yes — experiment13/run.py Phase 7D (~30 lines). Mann-Whitney on per-event CRPS/MAE between 2-strike and 3+-strike events.

### 3. Highlight convergence of two independent CI methods
- **Agree**: Yes. The reviewer correctly identifies that BCa [1.04, 2.52] and block bootstrap [1.06, 2.63] independently excluding 1.0 is itself robustness evidence.
- **Feasible**: One sentence.
- **Impact**: MEDIUM — strengthens the CPI case for sophisticated readers.
- **Action**: Added sentence explicitly noting the convergence of two bootstrap methods with different assumptions.

### 4. Acknowledge thin margin on CPI significance
- **Agree**: Yes. Both CI lower bounds (1.04, 1.06) are close to 1.0. A reader demanding 99% CIs would not find significance. The five-diagnostic convergence is what makes the overall case, not any single CI.
- **Feasible**: One sentence.
- **Impact**: MEDIUM — builds credibility by showing we recognize the margin ourselves.
- **Action**: Added parenthetical "(We note the margins are thin: both lower bounds are near 1.0. The case for CPI miscalibration rests not on any single CI but on the convergence of five independent diagnostics below.)"

### 5. Update FRED fetch date window
- **Agree**: Trivial code hygiene fix.
- **Feasible**: Find-and-replace.
- **Impact**: LOW — future-proofing.
- **Action**: Changed all "2025-12-01" end dates to "2026-06-01" in experiment13/run.py.

### 6. Verify mid-life snapshot monotonicity
- **Agree**: Excellent suggestion. If any mid-life CDF had violations, the CRPS would be computed on a non-distribution.
- **Feasible**: Yes — integrated into the per-event trajectory code (Phase 7C).
- **Impact**: **HIGH** (for a ~5 line check) — The result is **zero violations** across all 14 CPI and 13 JC mid-life snapshots. This is a clean bill of health that makes the CRPS computation bulletproof.
- **Action**: Monotonicity check integrated into Phase 7C. Results added to Methodology corrections list (item 17).
- **Code written**: Yes — monotonicity check within Phase 7C loop.

### 7. JC 2-strike vs 3+-strike significance test
- **Agree**: Implemented and it produced a significant result (p=0.028). This elevates the finding from "interesting" to "statistically significant."
- **Action**: See item 2 above. Also: CPI shows no significant difference (p=0.839), which is expected given both CPI subsets have CRPS/MAE > 1.

## Code Changes

1. **experiment13/run.py** — Phase 7C: "Per-Event Temporal CRPS/MAE Trajectories" (~120 lines):
   - Per-event CRPS/MAE at 10%, 50%, 90% of market life (tail-aware)
   - Pattern classification: U-shape, monotone-up, monotone-down, inverse-U
   - Wilcoxon signed-rank tests: mid > early, mid > late
   - Spearman correlations: early-mid, mid-late
   - CDF monotonicity verification at mid-life snapshots
   - All results saved to unified_results.json

2. **experiment13/run.py** — Phase 7D: "Strike-Count Significance Test" (~30 lines):
   - Mann-Whitney U test on per-event CRPS/MAE between 2-strike and 3+-strike events
   - Results: JC p=0.028 (significant), CPI p=0.839 (not significant)

3. **experiment13/run.py** — FRED date window updates:
   - All end dates changed from "2025-12-01" to "2026-06-01"

## Paper Changes

- **Status line**: Updated to iteration 8
- **Section 2, CPI harmful paragraph**: Added dual CI convergence sentence and thin-margin acknowledgment
- **Section 2, strike-count subsection**: Expanded from 1 sentence to full paragraph with Mann-Whitney p=0.028 result and market design tension
- **Section 2, market design implications**: Added liquidity caveat about strike density recommendation
- **Section 2, temporal hypothesis**: Complete rewrite with per-event trajectory data (7/14 U-shape, 0 CDF violations, Wilcoxon non-significant, median trajectory)
- **Methodology, corrections 17-18**: Added mid-life CDF monotonicity verification and per-event temporal trajectories

## New Results

| Analysis | Result | Significance |
|----------|--------|-------------|
| CPI events with U-shape pattern | 7/14 (50%) | Population tendency, not universal |
| JC events with U-shape pattern | 4/13 (31%) | No dominant temporal pattern |
| Wilcoxon mid > early (CPI) | p=0.134 | Not significant |
| Wilcoxon mid > late (CPI) | p=0.196 | Not significant |
| Early-mid Spearman (CPI) | ρ=0.06, p=0.83 | No predictive signal |
| Mid-life CDF violations | 0/14 CPI, 0/13 JC | All CDFs monotone — CRPS valid |
| JC 2-strike vs 3+-strike | Mann-Whitney p=0.028, r=0.66 | **Significant** — more strikes can hurt |
| CPI 2-strike vs 3+-strike | Mann-Whitney p=0.839 | Not significant |
| CPI median trajectory | 0.80 → 1.60 → 0.89 | U-shape at median level |
| JC median trajectory | 0.79 → 0.62 → 0.73 | Consistently < 1.0 |

**The two most important new results:**
1. **Mid-life CDF monotonicity: 0 violations.** This eliminates a potential critique that CRPS was computed on non-distributions.
2. **JC 2-strike vs 3+-strike: p=0.028.** This elevates a one-sentence observation into a statistically significant finding that complicates the "add more strikes" recommendation — adding an important nuance for market designers.

## Pushbacks

None this iteration. All critique points were well-reasoned and the per-event temporal analysis was the right "one big thing" — the results are clarifying even though they partially undermine the three-phase narrative. That's exactly the kind of honest finding that builds credibility.

## Remaining Weaknesses

1. **Small sample sizes**: n=14 CPI, n=16 JC. Fundamental and well-documented.
2. **Two series only**: Need replication across more series.
3. **In-sample only**: No cross-validation feasible.
4. **Temporal hypothesis is weaker than before**: The per-event analysis shows the U-shape in 50% of CPI events — suggestive but not confirmed. The paper now correctly frames this as a population tendency. This is honest but means the temporal section is more descriptive than inferential.
5. **JC strike-count finding direction**: The JC 2-strike > 3+-strike finding (p=0.028) could reflect selection effects (simpler events assigned fewer strikes) rather than a causal effect of strike count on distributional quality. We can't distinguish these with current data. The paper acknowledges the tension but can't resolve the mechanism.
6. **Blog length**: ~5,800 words now. The expanded strike-count discussion and temporal rewrite add ~150 net words. Still manageable for a technical blog but would need aggressive editing for a general audience version.
