# Researcher Response — Iteration 10

STATUS: CONTINUE

## Deliberation

### 1. The One Big Thing: Disentangle mechanical vs informative components of surprise-magnitude finding
- **Agree**: Strongly. The reviewer correctly identifies the CRPS/MAE ratio has a mechanical denominator effect — high-surprise events have larger MAE denominators by construction. The paper overstated this by calling it "the paper's most actionable finding for traders."
- **Feasible**: Yes — the code already computes uniform_crps; I just needed to split it by surprise subsets.
- **Impact**: **HIGH** — This is the most important analytical fix of the iteration. The CRPS/uniform ratio is mechanically independent of surprise magnitude and provides a clean check.
- **Action**: Implemented CRPS/uniform computation for surprise subsets. Results:
  - **CPI**: high-surprise CRPS/uniform=1.42, low-surprise=2.34 → **genuine signal confirmed**
  - **JC**: high-surprise CRPS/uniform=0.69, low-surprise=1.07 → **genuine signal confirmed**
  - The pattern holds under the mechanically independent metric. High-surprise distributions are genuinely better calibrated, not just benefiting from larger denominators.
- **Key nuance**: Even with the genuine signal confirmed, CPI high-surprise CRPS/uniform=1.42 still exceeds 1.0 — distributions are still worse than uniform. The improvement is relative (much less harmful), not absolute (not actually good). This is honestly reported.
- **Code written**: Yes — ~15 lines added to Phase 7E in experiment13/run.py.

### 2. Fix interior-only partition inconsistency
- **Agree**: Good catch. The old code used different median splits for tail-aware vs interior-only, meaning different events in the "high" and "low" groups.
- **Feasible**: 3 lines of code.
- **Impact**: **MEDIUM-HIGH** — This actually changed the numbers meaningfully:
  - Old CPI high-surprise interior: 0.86 (below 1.0!)
  - New CPI high-surprise interior: 1.13 (above 1.0)
  - The previous "below 1.0" finding was partly an artifact of the inconsistent partition. The corrected number is more honest.
- **Action**: Fixed. Interior-only now uses `s_int.loc[s_int.index.isin(high_events.index)]` to ensure same events in both specifications.
- **Code written**: Yes — 3 lines modified in Phase 7E.

### 3. Specify bootstrap method for temporal CIs
- **Agree**: Minor but valid. The temporal CIs use percentile bootstrap while the main CIs use BCa.
- **Feasible**: One sentence edit.
- **Impact**: LOW — but precision costs nothing.
- **Action**: Added "(percentile method, 10,000 resamples)" to the temporal CI table header.

### 4. Foreground downgraded/invalidated findings in abstract
- **Agree**: Strongly. Appendix C is one of the paper's most distinctive features for a blog audience. The reviewer is right that documenting 13 downgraded findings builds credibility.
- **Feasible**: One sentence.
- **Impact**: MEDIUM — positions the paper as a methodological exemplar.
- **Action**: Added sentence to abstract: "We document 13 initially significant findings that were invalidated or substantially weakened by methodological corrections (Appendix C), illustrating the importance of rigorous statistical practice in prediction market research."

### 5. Fix "34% CRPS improvement" phrasing
- **Agree**: Good catch. "34% improvement" is ambiguous — improvement over what?
- **Feasible**: One sentence edit.
- **Impact**: LOW — but precision matters.
- **Action**: Changed to "CRPS is 34% below the point-forecast MAE (CRPS/MAE=0.66), meaning the distribution captures substantially more information than the implied mean alone."

### 6. Add scatter plot: surprise magnitude vs CRPS/MAE
- **Agree**: Good visualization for the blog audience.
- **Feasible**: ~30 lines of code.
- **Impact**: MEDIUM — communicates the core surprise finding at a glance.
- **Action**: Created two-panel scatter plot with Spearman ρ annotations and trend lines. Saved to data/exp13/plots/surprise_vs_crps_mae.png.
- **Code written**: Yes — ~40 lines in _plot_unified().

### 7. Downgrade "most actionable finding for traders"
- **Agree**: With the partition fix showing CPI high-surprise interior is 1.13 (not 0.86), and with the mechanical caveat, this claim was overstated.
- **Action**: Replaced with "This finding has practical implications, though part of the CRPS/MAE effect is mechanical." Added full decomposition paragraph distinguishing mechanical from genuine components.

## Code Changes

1. **experiment13/run.py — Phase 7E (lines ~1567-1620)**:
   - Fixed interior-only partition to use same events as tail-aware partition (consistent grouping)
   - Added CRPS/uniform ratio computation for high/low surprise subsets
   - Added absolute CRPS and MAE reporting
   - Added print statements for new metrics

2. **experiment13/run.py — _plot_unified() (lines ~1840-1880)**:
   - Added two-panel scatter plot: surprise magnitude vs CRPS/MAE
   - Separate panels for CPI and JC (different scales)
   - Annotated with Spearman ρ and p-values
   - Linear trend lines for visual

## Paper Changes

- **Status line**: Updated to iteration 10
- **Abstract**: Added CRPS/uniform confirmation of surprise finding; added Appendix C reference sentence
- **Practical takeaways**: Fixed "34% CRPS improvement" → precise phrasing; updated CPI takeaway with CRPS/uniform numbers
- **Executive summary table**: Added CRPS/uniform row
- **Section 2, Surprise Magnitude**:
  - Updated interior-only numbers (0.86→1.13, 2.73→1.77) after partition fix
  - Added CRPS/uniform column to surprise-split table
  - Added mechanical vs informative decomposition paragraph
  - Added absolute CRPS comparison paragraph
  - Downgraded "most actionable finding for traders" → "practical implications with mechanical caveat"
  - Added note on consistent partitioning
- **Section 4, Temporal CIs**: Added "percentile method" specification

## New Results

| Analysis | Result | Significance |
|----------|--------|-------------|
| CPI high-surprise CRPS/uniform | **1.42** | Genuinely better than low-surprise (2.34) |
| CPI low-surprise CRPS/uniform | **2.34** | Confirms pattern is not purely mechanical |
| JC high-surprise CRPS/uniform | **0.69** | Below 1.0 — genuinely good distributions |
| JC low-surprise CRPS/uniform | **1.07** | Near-parity with uniform |
| CPI high-surprise interior (corrected) | **1.13** | Was 0.86 — partition fix removed below-1.0 artifact |
| CPI low-surprise interior (corrected) | **1.77** | Was 2.73 — corrected |
| Scatter plot | surprise_vs_crps_mae.png | Two-panel visualization with Spearman annotations |

**Most important result this iteration:** The CRPS/uniform comparison confirms the surprise-magnitude finding is genuine — high-surprise distributions are better calibrated by a mechanically independent metric. But the partition fix also revealed that the previous CPI interior-only "below 1.0" finding was an artifact. Honest reporting of both strengthens the paper.

## Pushbacks

None. All critique points were valid and well-targeted. The partition inconsistency catch was particularly valuable — it corrected a result that was being over-interpreted.

## Remaining Weaknesses

1. **Small sample sizes**: n=14 CPI, n=16 JC. Fundamental.
2. **Two series only**: Cannot generalize beyond CPI and Jobless Claims.
3. **In-sample only**: No cross-validation feasible at current n.
4. **Surprise split is post-hoc**: Not pre-registered. Spearman ρ provides independent support.
5. **CPI CRPS/uniform > 1.0 even for high-surprise events**: The distribution never beats uniform for CPI — the improvement is only relative (less bad), not absolute (good).
6. **Temporal CIs use percentile bootstrap, not BCa**: Noted in paper but not upgraded — upgrading would require modifying the bootstrap code for the temporal analysis, and the difference is typically small at these sample sizes.
