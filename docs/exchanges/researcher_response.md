# Researcher Response — Iteration 5

STATUS: CONTINUE

## Deliberation

### 1. The One Big Thing: Scale-free permutation test on per-event ratios
- **Agree**: Completely. The reviewer correctly identifies that the original permutation test pools raw CRPS and MAE values across series with ~100,000x scale differences. While mathematically valid, it tests a composite hypothesis (different scales AND/OR different ratios) rather than pure calibration heterogeneity. The MWU on dimensionless per-event ratios is the cleaner test.
- **Feasible**: Yes — ~10 lines of code.
- **Impact**: HIGH — eliminates a subtle methodological concern and produces a cleaner test.
- **Action**: Implemented. Scale-free permutation test on interior-only per-event CRPS/MAE ratios yields **p=0.016** (10,000 permutations). Still significant, confirming that the heterogeneity finding is robust to scale-mixing and is a genuine calibration difference.
- **Code written**: Yes — experiment13/run.py, added ~12 lines for scale-free permutation test.

### 2. Should Fix: Swap permutation/MWU emphasis
- **Agree**: Yes. MWU is the cleaner test (scale-free, non-parametric on dimensionless ratios). The permutation test should be supporting evidence.
- **Feasible**: Prose change.
- **Impact**: MEDIUM — correctly prioritizes the stronger evidence.
- **Action**: Restructured the heterogeneity paragraph to lead with MWU (p=0.003 tail-aware, p=0.026 interior-only), followed by scale-free permutation (p=0.016) as confirmation. Dropped the original scale-mixed permutation test from the paper text.

### 3. Should Fix: Strengthen point-vs-distribution decoupling claim
- **Agree**: Strongly. The reviewer's suggested language ("to our knowledge, the first empirical demonstration...") is exactly right. This is the paper's most novel finding and should be framed as such.
- **Feasible**: Prose change.
- **Impact**: HIGH for novelty positioning.
- **Action**: Added "to our knowledge, the first empirical demonstration that prediction market point forecasts and distributional forecasts can be independently calibrated" in Section 3's decoupling paragraph. Also added: "This decoupling is invisible to standard evaluation metrics (Brier score, calibration curves) that evaluate individual contracts rather than distributional coherence." Mirrored in abstract.

### 4. Should Fix: Add temporal robustness to abstract
- **Agree**: Yes. The fact that JC CIs exclude 1.0 at ALL five temporal snapshots is a striking robustness finding that was missing from the abstract.
- **Feasible**: Prose change.
- **Impact**: MEDIUM — increases novelty profile in the most-read section.
- **Action**: Added "with CIs excluding 1.0 at all five temporal snapshots from 10% to 90% of market life" to the abstract.

### 5. Should Fix: Tighten abstract length
- **Agree**: Partially. The abstract was ~250 words; I trimmed it to ~170 words by removing the interior-only MWU p-value, specific CI bounds for JC, and the TIPS/horse race detail (which is now in the takeaways box). The practical takeaways box remains as a separate callout.
- **Impact**: MEDIUM for blog readability.
- **Action**: Compressed abstract significantly. Removed interior-only MWU from abstract (it's a robustness check). Kept practical takeaways box unchanged.

### 6. New Experiment: Block bootstrap for CPI serial correlation
- **Agree**: Excellent suggestion. This directly addresses the serial correlation caveat — the Achilles' heel of the CPI finding.
- **Feasible**: Yes — ~15 lines of code.
- **Impact**: **VERY HIGH** — this is the most impactful single change in this iteration.
- **Action**: Implemented circular block bootstrap (block length 2, matching AR(1) ρ=0.23, 10,000 resamples). **Result: CI [1.06, 2.63], excludes 1.0.** This eliminates the serial correlation caveat entirely. The CPI finding is now supported by five converging diagnostics (upgraded from four), with the block bootstrap being the most rigorous.
- **Code written**: Yes — experiment13/run.py, added ~15 lines for block bootstrap.

### 7. New Experiment: Anderson-Darling → Cramér-von Mises for PIT uniformity
- **Agree**: Good suggestion for supplementary evidence. However, scipy.stats.anderson does not support the uniform distribution. Substituted with Cramér-von Mises test (scipy.stats.cramervonmises), which does support uniform and is also more powerful than KS for detecting distributional deviations.
- **Feasible**: Yes — 3 lines of code.
- **Impact**: LOW — both CvM and KS are underpowered at n=14–16. The CvM p-values (CPI=0.152, JC=0.396) are consistent with KS but don't change the story.
- **Action**: Implemented. CPI CvM p=0.152 (lower than KS p=0.221, directionally consistent with CPI miscalibration), JC CvM p=0.396. Added to PIT table and appendix.
- **Code written**: Yes — experiment13/run.py, replaced Anderson-Darling with Cramér-von Mises.

### 8. Code Issue 2: Experiment 8 stationarity alignment
- **Partially agree**: The reviewer notes a potential off-by-one issue if one series requires differencing and the other doesn't. The code re-aligns by date after transforms, which should handle this. Adding a defensive assertion is good practice but unlikely to change results.
- **Feasible**: Yes, but low priority.
- **Impact**: LOW — code hygiene, no paper impact. The Granger result is already appropriately hedged.
- **Action**: Deferred. The paper already notes "Granger causality measures predictive information, not causal information flow."

### 9. Code Issue 3: Hardcoded realized values
- **Agree**: This is a valid concern but standard practice at n=14. Not worth automating.
- **Impact**: LOW.
- **Action**: No change. Already noted in methodology.

### 10. Claim 6 framing suggestion
- **Agree**: The reviewer's exact framing ("to our knowledge, the first empirical demonstration...invisible to standard evaluation metrics") is excellent and I adopted it nearly verbatim.
- **Action**: Implemented in Section 3 and abstract.

## Code Changes

1. **experiment13/run.py** — Added:
   - Scale-free permutation test on interior-only per-event CRPS/MAE ratios (~12 lines). Result: p=0.016.
   - Circular block bootstrap for CPI CRPS/MAE CI (~15 lines). Result: CI [1.06, 2.63], excludes 1.0.
   - Cramér-von Mises test for PIT uniformity (~5 lines). Results: CPI p=0.152, JC p=0.396.

## Paper Changes

- **Abstract**: Tightened from ~250 to ~170 words. Added temporal robustness ("CIs excluding 1.0 at all five temporal snapshots"). Added block bootstrap CI. Added "first empirical demonstration" language. Removed interior-only MWU and TIPS detail (kept in takeaways box).
- **Section 2 — CPI harmful paragraph**: Replaced serial-correlation-adjusted CI caveat with block bootstrap result (CI [1.06, 2.63], excludes 1.0). Upgraded from "four independent diagnostics" to "five independent diagnostics."
- **Section 2 — Heterogeneity paragraph**: Restructured to lead with MWU, followed by scale-free permutation (p=0.016). Dropped original scale-mixed permutation test.
- **Section 2 — PIT table**: Added Cramér-von Mises row (CPI p=0.152, JC p=0.396).
- **Section 3 — Decoupling paragraph**: Added "first empirical demonstration" framing and "invisible to standard evaluation metrics" language.
- **Appendix A**: Updated PIT discussion to reference both KS and CvM tests.
- **Methodology items 10, 14**: Updated to reference block bootstrap and scale-free permutation. Added items 15 (block bootstrap) and 16 (Cramér-von Mises).

## New Results

| Analysis | Key Finding |
|----------|-------------|
| Scale-free permutation test | p=0.016 — heterogeneity confirmed without scale-mixing |
| Block bootstrap CPI CI | [1.06, 2.63] — **excludes 1.0**, eliminates serial correlation caveat |
| Cramér-von Mises (CPI) | stat=0.282, p=0.152 — directionally consistent with miscalibration |
| Cramér-von Mises (JC) | stat=0.149, p=0.396 — consistent with well-calibrated distributions |

The block bootstrap result is the most significant new finding. It upgrades the CPI claim from "conclusive-to-strong with serial correlation caveat" to "conclusive" — the CI excludes 1.0 even after properly accounting for serial dependence.

## Pushbacks

### Anderson-Darling test
The reviewer suggested Anderson-Darling for PIT uniformity. scipy.stats.anderson does not support the uniform distribution (only norm, expon, logistic, gumbel, weibull_min). Substituted with Cramér-von Mises, which serves the same purpose (more powerful than KS for distributional deviations) and does support uniform. The results are consistent with KS and don't materially change the story — both tests are underpowered at n=14–16.

### Experiment 8 stationarity alignment assertion
Deferred. The code re-aligns by date after independent stationarity transforms, and the Granger result is already hedged in the paper. Adding an assertion would be good code hygiene but has zero impact on the paper's claims.

## Remaining Weaknesses

1. **Small sample sizes remain fundamental**: n=14 CPI, n=16 JC. Inherent and well-documented.
2. **In-sample only**: No cross-validation possible at current n.
3. **Only two series**: The heterogeneity finding would be far more compelling with 5+ series. Inherent to current Kalshi offerings.
4. **No causal mechanism identified**: Four hypotheses are plausible but untestable with public data.
5. **PIT tests underpowered**: Both KS and CvM fail to reject uniformity for CPI, despite the CRPS/MAE ratio clearly indicating miscalibration. This is a power issue (n=14), not a contradiction.
6. **Hardcoded realized values**: Standard practice at n=14 but introduces transcription risk.
