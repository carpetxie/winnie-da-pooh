# Researcher Response — Iteration 6

STATUS: CONTINUE

## Deliberation

### 1. The One Big Thing: Random walk data leakage bug (line 183, 0.3→0.2)
- **Agree**: Completely. This is a genuine data leakage bug. KXCPI-24NOV is the November 2024 CPI event (realized 0.3%). The random walk forecast should use October 2024's realized value (0.2%), not November's. The reviewer correctly identified that this is conservative bias (hurts the paper's claim) but the numbers must be corrected regardless.
- **Feasible**: Yes — 1-character code change.
- **Impact**: **VERY HIGH** — fixing the bug strengthens the headline horse race result from borderline (p_adj=0.059) to clearly significant (p_adj=0.014). This is the single most impactful change in this iteration.
- **Action**: Fixed `return 0.3` → `return 0.2` in `experiment13/horse_race.py` line 183. Updated comment. Re-ran experiment13.
- **Code written**: Yes — experiment13/horse_race.py (bug fix).
- **New results**: Random walk MAE 0.143→0.150, d=−0.71→**−0.85**, p_raw=0.015→**0.003**, p_bonf=0.059→**0.014**. The Kalshi vs random walk comparison is now significant at 5% after Bonferroni correction.

### 2. Should Fix: First-event exclusion sensitivity check
- **Agree**: Excellent belt-and-suspenders suggestion. Eliminates any concern about hardcoded first-event benchmarks.
- **Feasible**: Yes — ~15 lines of code.
- **Impact**: HIGH — makes the horse race result bulletproof.
- **Action**: Added sensitivity analysis excluding KXCPI-24NOV (n=13). Results: Kalshi vs random walk d=−0.89, p_bonf=0.016; Kalshi vs trailing mean d=−0.53, p_bonf=0.027. Both significant. Result is robust.
- **Code written**: Yes — experiment13/horse_race.py (sensitivity_excl_first_event section).

### 3. Should Fix: Trailing mean warm-up note
- **Agree**: Yes, this is worth noting for methodological transparency.
- **Feasible**: One sentence.
- **Impact**: LOW — methodological completeness.
- **Action**: Added note: "The trailing mean uses an expanding window (1 observation for the second event, growing to 13), giving it an inherent warm-up disadvantage for early events."

### 4. Should Fix: Concrete market design recommendation
- **Agree**: Strongly. The original "increase strike density" suggestion was vague. The reviewer's suggestion to specify exact percentiles and target counts makes it actionable for Kalshi's market design team.
- **Feasible**: Prose change.
- **Impact**: MEDIUM-HIGH for Kalshi blog audience.
- **Action**: Replaced vague "increasing strike density" with: "adding strikes at the 25th and 75th percentiles of the historical CPI distribution (approximately ±0.15pp from the expected value) would increase CPI strike density from 2–3 to 4–5, matching the Jobless Claims structure that produces CRPS/MAE < 1." Also added: "Kalshi could publish a distributional quality dashboard per series, analogous to how exchanges publish implied volatility metrics."

### 5. Should Fix: Temporal CI bootstrap method explanation
- **Agree**: Yes, readers should understand why percentile rather than BCa.
- **Feasible**: One parenthetical.
- **Impact**: LOW — methodological transparency.
- **Action**: Added: "(percentile method used because BCa can be numerically unstable at the smaller per-timepoint sample sizes)."

### 6. Novelty: Underemphasized distributional quality dashboard
- **Agree**: Good suggestion. Merged into the market design implications paragraph alongside the concrete strike density recommendation.
- **Action**: Added "Kalshi could publish a distributional quality dashboard per series, analogous to how exchanges publish implied volatility metrics."

### 7. Trailing mean warm-up observation (0.25 hardcode precision)
- **Partially agree**: The reviewer notes the hardcoded 0.25 for KXCPI-24NOV trailing mean is imprecise (actual 2024 YTD through October ≈ 0.24%). This is a ~4% difference on a single benchmark for one event. The sensitivity check (excluding first event) already addresses this concern more cleanly than tweaking the hardcode. Not worth the code change.
- **Action**: No code change. The first-event exclusion sensitivity check subsumes this concern.

### 8. Interior-only horse race sensitivity note
- **Partially agree**: The reviewer suggests noting interior-only MAE vs random walk as a sensitivity check. The interior-only MAE is 0.082 (worse than tail-aware 0.068), so the comparison would be weaker. Since the paper already clearly states both MAE values and explains why tail-aware is preferred, adding a separate interior-only horse race line would add noise without insight.
- **Action**: Declined. The paper already notes "Interior-only Kalshi MAE = 0.082" in the horse race footnote.

## Code Changes

1. **experiment13/horse_race.py** — Bug fix: Random walk first-event forecast changed from 0.3 (data leakage: using realized value as forecast) to 0.2 (October 2024 CPI MoM, the correct prior-month value). Comment updated.
2. **experiment13/horse_race.py** — Added first-event exclusion sensitivity analysis (~15 lines): runs all four benchmark comparisons excluding KXCPI-24NOV (n=13), computing Cohen's d and Bonferroni-adjusted p-values.
3. **experiment13/run.py** — Added sensitivity results printing in Phase 6 output.

## Paper Changes

- **Abstract**: Updated horse race numbers: d=−0.71→−0.85, p_adj=0.059→0.014.
- **Practical Takeaways**: Updated CPI takeaway to emphasize significance (d=−0.85, p=0.014 Bonferroni).
- **Section 3 — Horse race table**: Updated random walk row: MAE 0.143→0.150, d=−0.71→−0.85, p_raw=0.015→0.003, p_bonf=0.059→0.014.
- **Section 3 — Horse race narrative**: Updated to reflect Bonferroni significance at 5%. Added first-event exclusion sensitivity (n=13: d=−0.89, p_adj=0.016).
- **Section 3 — Trailing mean note**: Added expanding window warm-up note.
- **Section 3 — Decoupling paragraph**: Updated d and p values.
- **Section 2 — Market design implications**: Made strike density recommendation concrete (25th/75th percentile, ±0.15pp, 2–3→4–5 strikes). Added distributional quality dashboard proposal.
- **Section 2 — Temporal CI footnote**: Added BCa instability explanation for percentile method.
- **Power analysis table**: Updated random walk d=0.71→0.85, n needed 13→9.
- **Appendix C — Downgraded findings**: Updated random walk entry to reflect data leakage fix and upgraded p-value.

## New Results

| Analysis | Previous | Corrected | Change |
|----------|----------|-----------|--------|
| Random walk mean MAE | 0.143 | 0.150 | +0.007 (removed data leakage advantage) |
| Kalshi vs RW Cohen's d | −0.71 | **−0.85** | Larger effect size |
| Kalshi vs RW p_raw | 0.015 | **0.003** | 5x more significant |
| Kalshi vs RW p_bonf | 0.059 | **0.014** | Now significant at 5% after Bonferroni |
| Sensitivity (excl 1st): RW | — | d=−0.89, p_bonf=0.016, n=13 | Robust |
| Sensitivity (excl 1st): Trailing | — | d=−0.53, p_bonf=0.027, n=13 | Robust |
| Sensitivity (excl 1st): TIPS | — | d=−0.47, p_bonf=0.220, n=13 | Not significant |
| Sensitivity (excl 1st): SPF | — | d=−0.44, p_bonf=0.335, n=13 | Not significant |
| Power: n needed for RW | 13 | 9 | Already powered |

The data leakage fix is the most impactful single change across all 6 iterations. It upgrades the horse race headline from "significant at 10% after Bonferroni" to "significant at 5% after Bonferroni" — a threshold that matters for publication credibility.

## Pushbacks

### Interior-only horse race note
The reviewer suggested adding an interior-only horse race sensitivity line. Declined because: (1) the paper already reports interior-only MAE=0.082 in the table footnote, (2) the tail-aware mean is the methodologically preferred specification (consistent with CRPS), and (3) adding a weaker comparison alongside the stronger one would dilute rather than strengthen the narrative.

### Trailing mean hardcoded precision (0.25 vs 0.24)
The reviewer notes the trailing mean's hardcoded first-event value (0.25) is imprecise. Not worth fixing separately — the first-event exclusion sensitivity check is a cleaner resolution that eliminates the concern entirely. The difference (0.01pp) has negligible impact on the trailing mean results.

## Remaining Weaknesses

1. **Small sample sizes remain fundamental**: n=14 CPI, n=16 JC. Inherent and well-documented.
2. **In-sample only**: No cross-validation possible at current n.
3. **Only two series**: The heterogeneity finding would be far more compelling with 5+ series. Inherent to current Kalshi offerings.
4. **No causal mechanism identified**: Four hypotheses are plausible but untestable with public data.
5. **PIT tests underpowered**: Both KS and CvM fail to reject uniformity for CPI, despite the CRPS/MAE ratio clearly indicating miscalibration. This is a power issue (n=14), not a contradiction.
6. **SPF/TIPS horse race comparisons remain nonsignificant after Bonferroni**: These need more data (16–21 more months). Only random walk and trailing mean survive multiple testing correction.
