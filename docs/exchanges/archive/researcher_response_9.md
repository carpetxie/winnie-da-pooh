# Researcher Response — Iteration 9

STATUS: CONTINUE

## Deliberation

### 1. The One Big Thing: Restructure the paper for blog readability
- **Agree**: Strongly. The reviewer is right that the paper accumulated robustness checks over 8 iterations and reads like accretion rather than narrative. The statistical work is done — presentation is the bottleneck.
- **Feasible**: Yes — purely editorial restructuring, no new computation needed (except for the two new analyses below).
- **Impact**: **HIGH** — This is the single most impactful change. The paper went from ~5,800 words of interleaved results/robustness to a cleaner structure with: (a) punchline-first Section 2 opening, (b) worked examples immediately after CRPS/MAE table, (c) dedicated Section 4 "Robustness" gathering all checks, (d) methodology section trimmed from 18 items to 5 key ones (full 18 moved to Appendix F), (e) trimmed temporal hypothesis to one paragraph.
- **Action**: Complete restructuring implemented. Key changes:
  - Section 2 now opens with the punchline: "We find that prediction market distributions add significant value for some economic series and actively harm forecast quality for others."
  - Worked examples moved from halfway through Section 2 to immediately after CRPS/MAE table.
  - Created new Section 4 "Robustness: Why We Trust These Results" consolidating all robustness checks (LOO, signed-difference, serial correlation, temporal stability, etc.)
  - Methodology corrections trimmed from 18 numbered items to 5 key methods; full 18 moved to Appendix F.
  - Temporal hypothesis trimmed from ~200 words to one paragraph in Section 4.

### 2. Add executive summary table at top
- **Agree**: Good blog-format addition — gives readers the punchline in tabular form before diving into details.
- **Feasible**: Just editing (plus I added the new surprise-split row from the new analysis).
- **Impact**: MEDIUM — helps blog readers who want the bottom line fast.
- **Action**: Added executive summary table after the abstract with CRPS/MAE, recommendation, strongest evidence, point forecast quality, and surprise-dependent rows.

### 3. Foreground surprise magnitude implication
- **Agree**: Strongly. The ρ=−0.68 finding was buried as a methodological property. The reviewer correctly identifies it should be reframed as a positive practical finding.
- **Feasible**: Yes, and I went further — implemented the high/low surprise CPI split as a new analysis.
- **Impact**: **HIGH** — The split produced the paper's most actionable new finding: CPI high-surprise events have CRPS/MAE=1.19 (tail-aware) / 0.86 (interior-only), near or below 1.0. The CPI penalty is concentrated in routine small-surprise events. This refines the practical recommendation from "always ignore CPI distributions" to "ignore for routine prints; distributions approach parity for large surprises."
- **Action**: (1) Implemented Phase 7E in experiment13/run.py. (2) Added high/low surprise table to Section 2 with full interpretation. (3) Updated abstract and practical takeaways to reflect the nuanced finding.
- **Code written**: Yes — ~40 lines in experiment13/run.py Phase 7E.

### 4. Horse race sensitivity excluding first two events
- **Agree**: Good check. KXCPI-24DEC trailing mean uses only n=1 observation — a warm-up artifact.
- **Feasible**: ~20 lines of code.
- **Impact**: MEDIUM — confirms the random walk result is robust. d=−0.893, p_bonf=0.024 (significant).
- **Action**: Added sensitivity_excl_first_two_events to horse_race.py. Updated paper Section 3 to report: "robust to excluding the first event (n=13: d=−0.89, p_adj=0.016) and the first two events (n=12: d=−0.89, p_adj=0.024)."
- **Code written**: Yes — ~20 lines in experiment13/horse_race.py.

### 5. Clean up dual permutation test in code
- **Agree**: Good code hygiene. The raw-value permutation test (lines 653-670) mixes CPI and JC scales and isn't reported.
- **Feasible**: One comment.
- **Impact**: LOW — code hygiene, not paper impact.
- **Action**: Added a clear comment explaining why the raw-value permutation is retained as sensitivity only, and why the scale-free version is reported.
- **Code written**: Yes — comment addition in experiment13/run.py.

### 6. Add strike-count caveat to practical takeaways
- **Agree**: Yes — the JC 2-strike > 3+-strike finding (p=0.028) should appear in the takeaways.
- **Feasible**: One bullet point.
- **Impact**: MEDIUM — important for Kalshi blog readers who are market designers.
- **Action**: Added "Market designers" bullet to practical takeaways.

### 7. Cut methodology corrections from 18 to ~5
- **Agree**: Strongly. The 18-item list reads as a changelog. Blog readers need trust, not a audit trail.
- **Feasible**: Editorial.
- **Impact**: MEDIUM — the paper is now cleaner. Sophisticated readers can still find the full 18 in Appendix F.
- **Action**: Methodology section now has 5 key methods; full 18 preserved in new Appendix F.

### 8. Trim temporal hypothesis section
- **Agree**: Yes. Now that per-event trajectories show the U-shape in only 50% of events, this section was overweight.
- **Feasible**: Editorial.
- **Impact**: MEDIUM — reduces paper length and moves descriptive content to where it belongs (robustness section).
- **Action**: Reduced from ~200 words of detailed discussion to one paragraph in Section 4.

## Code Changes

1. **experiment13/run.py** — Phase 7E: "High-Surprise vs Low-Surprise CRPS/MAE Split" (~40 lines):
   - Splits each series at median surprise magnitude
   - Computes CRPS/MAE for high and low surprise halves (both tail-aware and interior-only)
   - Results: CPI high-surprise=1.19/0.86, low-surprise=3.08/2.73; JC high=0.60/0.51, low=0.82/0.93
   - All results saved to unified_results.json

2. **experiment13/horse_race.py** — Sensitivity excluding first two events (~20 lines):
   - Same battery of Wilcoxon + Cohen's d tests, excluding KXCPI-24NOV and KXCPI-24DEC
   - Results: Random walk d=−0.893, p_bonf=0.024 (significant); trailing mean d=−0.514, p_bonf=0.054

3. **experiment13/run.py** — Dual permutation test cleanup:
   - Added comment explaining why raw-value permutation is retained as sensitivity only

4. **experiment13/run.py** — Print excl-first-two sensitivity results in Phase 6 output

## Paper Changes

- **Status line**: Updated to iteration 9
- **Abstract**: Added surprise-magnitude split finding; updated CPI takeaway to reflect nuance
- **Practical takeaways**: Added "Market designers" bullet with strike-count caveat; refined CPI bullet for large vs small surprises
- **Executive summary table**: New, placed after abstract
- **Section 2 opening**: Now leads with punchline before methodology explanation
- **Worked examples**: Moved from mid-Section 2 to immediately after CRPS/MAE table
- **Section 2, Surprise Magnitude**: Added high/low surprise split table with full interpretation; reframed as "the paper's most actionable finding for traders"
- **Section 2, Per-Event Heterogeneity**: Trimmed from ~300 to ~150 words (detail moved to robustness)
- **Section 3, Horse Race**: Added excl-first-two sensitivity (n=12: d=−0.89, p_adj=0.024)
- **New Section 4**: "Robustness: Why We Trust These Results" — consolidates JC robustness, CPI robustness, heterogeneity test, strike-count confound, snapshot sensitivity, temporal hypothesis, and temporal CRPS vs uniform
- **Methodology**: Trimmed from 18 numbered items to 5 key methods
- **New Appendix F**: Full 18-item statistical corrections log

## New Results

| Analysis | Result | Significance |
|----------|--------|-------------|
| CPI high-surprise CRPS/MAE (TA) | 1.19 | Near parity — penalty concentrated in small surprises |
| CPI high-surprise CRPS/MAE (int) | 0.86 | **Below 1.0** — distribution adds value for large surprises |
| CPI low-surprise CRPS/MAE (TA) | 3.08 | Heavily penalized for routine events |
| CPI low-surprise CRPS/MAE (int) | 2.73 | Confirms TA finding |
| JC high-surprise CRPS/MAE (TA) | 0.60 | Better than low-surprise |
| JC low-surprise CRPS/MAE (TA) | 0.82 | Still good but weaker |
| Horse race excl first two: vs RW | d=−0.893, p_bonf=0.024 | **Significant** — robust to warm-up |
| Horse race excl first two: vs TM | d=−0.514, p_bonf=0.054 | Borderline |

**The most important new result:** CPI distributions with large surprises have interior-only CRPS/MAE=0.86 — *below* 1.0. This transforms the practical recommendation from "always ignore CPI distributions" to "CPI distributions are uninformative for routine prints but approach parity for surprise events — exactly when distributional information matters most."

## Pushbacks

None this iteration. All critique points were well-reasoned. The restructuring recommendation was spot-on — the paper reads much better as a narrative with a dedicated robustness section. The high/low surprise split was the reviewer's best analytical suggestion across all 9 iterations.

## Remaining Weaknesses

1. **Small sample sizes**: n=14 CPI, n=16 JC. Fundamental.
2. **Two series only**: Need replication across more series.
3. **In-sample only**: No cross-validation feasible.
4. **High/low surprise split is post-hoc**: The CPI split at median surprise is suggestive but not pre-registered. A hostile reviewer could argue this is data-snooping. The Spearman ρ=−0.68 (p=0.008) provides independent support, but the specific split is chosen to maximize narrative clarity, not statistical power.
5. **CPI high-surprise interior-only CRPS/MAE=0.86 is based on n=7**: Too small for a standalone CI. The finding is directional, not confirmed at conventional significance.
6. **Blog length**: Now ~4,800 words (down from ~5,800). Better, but still long for a blog post. Further trimming possible in appendices.
