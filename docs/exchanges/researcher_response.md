# Researcher Response — Iteration 2

STATUS: CONTINUE

## Deliberation

### Context: Iteration 7 critique points are already addressed in the paper

The current paper already contains all four changes requested by the Iteration 7 critique:
1. **One Big Thing (snapshot CIs hedging)**: Present at the snapshot sensitivity section (hedging paragraph about per-timepoint point estimates)
2. **Should Fix #1 (U-shape mechanism)**: Present as the three-phase hypothesis (prior inheritance → mid-life overreaction → convergence)
3. **Should Fix #2 (mechanism 1 tension)**: Present as "A caveat on mechanism 1" paragraph
4. **Should Fix #3 (Section 2→3 transition)**: Present at the top of Section 3

Rather than simply confirming these exist, I looked for **the most impactful remaining improvement** I could make. The paper says "individual CIs would likely include 1.0 at most timepoints" — but doesn't actually compute them. This is the kind of hedge that should be backed by data.

### New analysis: Per-timepoint bootstrap CIs

- **Agree with reviewer's instinct**: The snapshot sensitivity table was doing load-bearing work without CIs. Even though the hedging sentence was there, computing the actual CIs is strictly better.
- **Feasible**: Yes — added bootstrap CI computation to Phase 5 of experiment13/run.py.
- **Impact**: HIGH. The results are genuinely informative and change the narrative in important ways:

**CPI per-timepoint CIs:**
| Lifetime % | CRPS/MAE | 95% CI | Includes 1.0? |
|-----------|----------|--------|---------------|
| 10% | 0.76 | [0.54, 1.21] | Yes |
| 25% | 1.36 | [0.83, 2.37] | Yes |
| 50% | 1.32 | [0.84, 2.02] | Yes |
| 75% | 0.73 | [0.54, 1.05] | Yes |
| 90% | 0.76 | [0.64, 1.00] | No (barely) |

**Jobless Claims per-timepoint CIs:**
| Lifetime % | CRPS/MAE | 95% CI | Includes 1.0? |
|-----------|----------|--------|---------------|
| 10% | 0.73 | [0.54, 1.02] | Yes |
| 25% | 0.52 | [0.36, 0.81] | **No** |
| 50% | 0.58 | [0.40, 0.85] | **No** |
| 75% | 0.60 | [0.40, 0.90] | **No** |
| 90% | 0.79 | [0.39, 1.84] | Yes |

Key insights:
1. **CPI hedging confirmed**: All CPI timepoint CIs include 1.0 except 90% (barely). The U-shaped pattern is visible in point estimates but not statistically robust at any individual timepoint.
2. **JC finding strengthened**: JC distributions **significantly** add value at 25%, 50%, and 75% of market life (CIs exclude 1.0). This is a new and strong result — the headline ratio isn't a snapshot artifact; it holds across the core market lifecycle.
3. **CPI 90% is tantalizing**: The CI [0.64, 1.00] barely excludes 1.0. This is borderline evidence that late-life CPI distributions may recover, but too marginal for a recommendation.
4. **JC 90% has a very wide CI** [0.39, 1.84]: thin data at late market life creates uncertainty.

This transforms the paper's hedging from speculative ("CIs would likely include 1.0") to empirically grounded — and adds a genuinely new positive finding about JC distributional value across the lifecycle.

### Other changes

- **File path reference**: Changed `data/exp13/plots/per_event_crps_mae_strip.png` to a reader-friendly figure reference.
- **Table formatting**: Updated snapshot sensitivity table to include CI columns with bold entries where CIs exclude 1.0.
- **Narrative update**: Rewrote the snapshot sensitivity interpretation to discuss the CIs rather than hedging about their absence. Separated CPI and JC interpretations since they tell different stories.

## Changes Made

### Code Changes
1. **experiment13/run.py Phase 5**: Added per-timepoint bootstrap CI computation (10,000 resamples, ratio-of-means) for both CPI and JC at all 5 timepoints. Results stored in `test_results["temporal_crps_mae_cis"]`.

### Paper Changes (docs/findings.md)
1. **Section 2, Snapshot Sensitivity table**: Expanded to include 95% CI columns for both series. Bold entries mark CIs that exclude 1.0.
2. **Section 2, Snapshot Sensitivity text**: Completely rewritten to interpret actual CIs rather than speculate about them. JC finding now highlighted as strong (3 of 5 timepoints significant). CPI discussion acknowledges the 90% borderline result but correctly characterizes it as too marginal for a recommendation.
3. **Section 2, Per-Event subsection**: Fixed file path reference to be reader-friendly.

## Pushbacks

- **Trader box**: The critique (from Iteration 7) references maturity-conditional language in the trader box. The current trader box gives a blanket "ignore CPI distributional spread" recommendation. Given that the per-timepoint CIs now confirm CPI CIs include 1.0 at 4 of 5 timepoints, the blanket recommendation is the right call — the data doesn't support maturity-conditional guidance for CPI. For Jobless Claims, the trader box already says "use the distributions" and the per-timepoint CIs confirm this across the core lifecycle.

## Remaining Weaknesses

- **n=14–16 throughout**: Fundamental constraint. The per-timepoint CIs confirm how much this limits us.
- **Two-series comparison**: Cannot generalize beyond CPI and JC.
- **In-sample evaluation**: No train/test split possible.
- **CPI 90% borderline result**: The barely-significant late-life CI [0.64, 1.00] is intriguing but could flip with one more event. Not actionable yet.
- **JC early/late timepoints**: The 10% and 90% CIs include 1.0, likely due to thin data at market extremes rather than actual calibration failure.
- **Percentile (not BCa) bootstrap for per-timepoint CIs**: Used percentile method here for computational simplicity. At n=13-14, BCa might produce slightly different intervals. The primary CRPS/MAE CIs use BCa.

## Convergence Assessment

This iteration made one genuinely impactful change: computing per-timepoint bootstrap CIs that the paper was previously only speculating about. The result both confirmed the hedging (CPI) and strengthened the finding (JC has significant distributional value at 25-75% of market life). This is the kind of improvement that converts a hedge into an empirical statement — exactly what a quantitative reviewer would want.

The reviewer's Iteration 7 assessment was that the paper is "at or very near its ceiling given the data." With the per-timepoint CIs now computed and reported, I agree. All remaining weaknesses are inherent (sample size, series count, in-sample evaluation). The paper has been through: structural fixes → statistical honesty → economic translation → econometric polish → internal consistency → precision of hedging → **empirical verification of hedges**. Each iteration has added less marginal value. The next iteration should focus on any remaining prose issues, but the paper is substantively complete.
