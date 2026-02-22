# Researcher Response — Iteration 2

STATUS: CONTINUE

## Deliberation

### 1. Worked example factual error (KXJOBLESSCLAIMS-26JAN22 CRPS=751 → actual 9,189)
- **Agree**: Completely wrong. Verified against data/exp13/crps_per_event.csv: CRPS=9,189, MAE=17,500 (interior), ratio=0.525. The paper's claimed CRPS=751 and ratio=0.043 are off by an order of magnitude.
- **Feasible**: Yes — straightforward data correction.
- **Impact**: **HIGH** — factual errors undermine credibility.
- **Action**: Switched to KXJOBLESSCLAIMS-25JUN12 per reviewer suggestion. This event (realized=248K, implied_mean=275K, CRPS=4,455, MAE=27,000, ratio=0.165) is a cleaner illustration: the ratio is more dramatic (0.165 vs 0.525) and the narrative of "distribution capturing a large surprise" works better. Updated all numbers.
- **Code written**: No (data verification only).

### 2. Serial correlation CI prose error ([0.90, 2.58] "barely excludes 1.0" — it doesn't)
- **Agree**: 0.90 < 1.0, so the CI includes 1.0. This is a factual error that overclaims.
- **Feasible**: Yes — prose fix.
- **Impact**: **HIGH** — mischaracterizes statistical evidence.
- **Action**: Changed to "includes 1.0" and reframed: the CPI finding rests on converging evidence (unadjusted CI + PIT bias + temporal pattern), not any single test. This is actually more honest and arguably stronger — the three-diagnostics argument is the real basis for the claim.
- **Code written**: No.

### 3. Label per-event ratio ranges with mean specification
- **Agree**: The per-event ranges were reported without specifying they use interior-only mean.
- **Feasible**: Yes.
- **Impact**: Medium — improves clarity and consistency.
- **Action**: Added explicit "(interior-only; see note below)" label to the per-event section. Added a dedicated note explaining WHY per-event ratios use interior-only (tail-aware ratios are unstable when MAE→0).
- **Code written**: No.

### 4. Acknowledge tail-aware per-event instability
- **Agree**: Important methodological transparency. The KXCPI-25JUN example (ratio=21.5 tail-aware vs 4.51 interior) illustrates why the aggregate ratio-of-means is the right primary metric.
- **Feasible**: Yes.
- **Impact**: Medium — prevents reader confusion about why we use different metrics in different contexts.
- **Action**: Added explanatory note with concrete example in the per-event section.
- **Code written**: No.

### 5. Clarify "34% improvement" / "40% improvement" arithmetic
- **Agree**: Counterintuitive that the "worse" metric shows bigger improvement. A parenthetical explaining why resolves reader confusion.
- **Feasible**: Yes.
- **Impact**: Low-medium — prevents a predictable reader question.
- **Action**: Added parenthetical in the bottom line: "(which is larger because the interior-only point forecast is weaker, making the distribution's relative advantage bigger)".
- **Code written**: No.

### 6. Tail-aware LOO for JC
- **Agree**: Critical consistency fix. If the primary metric is tail-aware, the LOO should use it.
- **Feasible**: Yes — ~10 lines of code.
- **Impact**: **HIGH** — and the result is confirmatory: all 16 tail-aware LOO ratios < 1.0, range [0.64, 0.69]. Tighter range than interior-only [0.57, 0.66].
- **Action**: Implemented in experiment13/run.py. Updated paper to report tail-aware LOO as primary.
- **Code written**: Yes — experiment13/run.py (tail-aware LOO loop, ~20 lines).

### 7. Tail-aware horse race
- **Agree**: The horse race should use the same mean specification as the primary metric.
- **Feasible**: Yes — 5-line change in horse_race.py.
- **Impact**: **VERY HIGH** — and the results are dramatically better than expected:
  - Kalshi MAE drops from 0.082 (interior) to 0.068 (tail-aware)
  - vs Random Walk: p=0.015 (was 0.026), p_adj=0.059 (was 0.102), d=-0.71 (was -0.60)
  - vs TIPS: p=0.045 (was 0.163) — now significant at raw level!
  - vs Trailing: p=0.021 (was 0.155) — now significant at raw level!
  - Power analysis: Kalshi vs Random Walk already at 80% power (n=13 needed, have 14)
  The tail-aware mean is a strictly better point forecast, upgrading the entire horse race.
- **Action**: Modified horse_race.py to use tail-aware mean. Updated paper with all new numbers.
- **Code written**: Yes — experiment13/horse_race.py (tail-aware mean selection).

### 8. CRPS − MAE signed difference test
- **Agree**: Excellent complementary diagnostic. The ratio is unstable when MAE→0; the signed difference is immune to this.
- **Feasible**: Yes.
- **Impact**: **HIGH** — JC signed difference: Wilcoxon p=0.001 (14/16 events negative). This is the strongest individual statistical test in the entire paper. CPI: p=0.091 (10/14 events positive) — borderline but directionally consistent.
- **Action**: Implemented in experiment13/run.py. Reported for both series in the paper. Added to methodology list.
- **Code written**: Yes — experiment13/run.py (signed difference test, ~30 lines).

### 9. Tail-aware temporal CRPS/MAE table
- **Agree**: The temporal table should use the primary metric.
- **Feasible**: Yes.
- **Impact**: **VERY HIGH** — and the result is the most striking finding of this iteration:
  - JC tail-aware: CIs exclude 1.0 at ALL 5 timepoints (10%, 25%, 50%, 75%, 90%). The distribution adds value across the ENTIRE market lifecycle.
  - CPI tail-aware: CI excludes 1.0 only at 50% [1.03, 2.55]. Mid-life is the only statistically confirmed harmful timepoint.
  - Interior-only had JC significant at 3/5 and CPI at 1/5 (90%). Tail-aware gives JC 5/5 and CPI 1/5 (50%).
- **Action**: Added tail-aware temporal computation to experiment13/run.py. Paper now reports both tables with tail-aware as primary. Updated discussion text to highlight "all five timepoints" finding.
- **Code written**: Yes — experiment13/run.py (tail-aware temporal bootstrap, ~30 lines).

### 10. Highlight tail-aware vs interior-only asymmetry (underemphasized novelty)
- **Partially agree**: The reviewer's point is subtle and correct — the tail-aware mean being better yet the ratio going UP is a genuine insight. I've incorporated this in the lifecycle perspective paragraph.
- **Impact**: Medium — adds nuance.
- **Action**: Added sentence in lifecycle perspective: "even when you give the point forecast every advantage (using the best available mean from the same CDF), the CPI distribution still underperforms."

## Code Changes

1. **experiment13/run.py** — Added:
   - Tail-aware leave-one-out sensitivity for JC (~20 lines, after existing LOO)
   - CRPS − MAE signed difference test for both series (~35 lines, Wilcoxon signed-rank)
   - Tail-aware temporal CRPS/MAE bootstrap CIs (~30 lines, parallel to existing interior-only temporal CIs)
   - Tail-aware mean computation in temporal snapshots (5 lines, added `compute_tail_aware_mean` call + `point_mae_ta` field)

2. **experiment13/horse_race.py** — Modified:
   - Horse race now uses tail-aware implied mean by default (falls back to interior-only if unavailable)
   - Reports both interior and tail-aware MAE per event

## Paper Changes

- **Abstract**: Updated horse race result (p_raw=0.015, p_adj=0.059, d=-0.71; already at 80% power)
- **Bottom line**: Added signed-difference test, 5/5 temporal robustness, and 34%/40% arithmetic explanation
- **Section 2 — JC finding**: Added tail-aware LOO range [0.64, 0.69], signed difference p=0.001
- **Section 2 — CPI finding**: Fixed serial correlation CI prose (includes 1.0, not excludes). Added signed difference p=0.091. Reframed to rely on converging evidence
- **Section 2 — Per-event**: Labeled ranges as interior-only. Added instability note for tail-aware per-event ratios
- **Section 2 — Temporal table**: Added full tail-aware table alongside interior-only. Updated discussion to highlight JC 5/5 finding
- **Section 2 — Lifecycle perspective**: Highlighted tail-aware asymmetry (better point forecast → higher ratio)
- **Section 3 — Horse race table**: Updated all numbers (MAE=0.068, d=-0.71, p=0.015/0.059)
- **Section 3 — Power analysis**: Updated effect sizes. Kalshi vs Random Walk already powered.
- **Methodology**: Added tail-aware LOO and CRPS − MAE signed difference to corrections list
- **Appendix C**: Added tail-aware Kalshi vs Random Walk to downgraded findings

## New Results

| Analysis | Key Finding |
|----------|-------------|
| Tail-aware LOO (JC) | All 16 ratios < 1.0, range [0.64, 0.69] — confirmed bulletproof |
| CRPS − MAE signed difference (JC) | p=0.001, 14/16 events negative — strongest individual test in paper |
| CRPS − MAE signed difference (CPI) | p=0.091, 10/14 events positive — borderline, directionally consistent |
| Tail-aware temporal (JC) | CIs exclude 1.0 at ALL 5 timepoints — entire lifecycle adds value |
| Tail-aware temporal (CPI) | CI excludes 1.0 only at 50% [1.03, 2.55] — mid-life harm confirmed |
| Tail-aware horse race | Kalshi MAE=0.068 (was 0.082). vs RW: p=0.015/0.059, d=-0.71. Already at 80% power |
| Tail-aware horse race | vs TIPS: p=0.045 raw (was 0.163). vs Trailing: p=0.021 raw (was 0.155) |

## Pushbacks

None this iteration. All critique points were valid and actionable. The two must-fixes (factual error and CI prose) were straightforward. The four code suggestions all produced results that strengthened the paper, several dramatically so.

## Remaining Weaknesses

1. **Small sample sizes remain fundamental**: n=14 CPI, n=16 JC. The CPI finding rests on converging evidence from marginal tests; more data would either confirm or overturn it.

2. **In-sample only**: All results are in-sample. No cross-validation possible at current n.

3. **The CPI finding is the weakest link**: Serial-correlation-adjusted CI includes 1.0. Signed difference p=0.091 borderline. The convergence argument (ratio + PIT + temporal) is the real basis, but each individual test is marginal. A single additional CPI event with good distributional calibration could shift the aggregate.

4. **Horse race Bonferroni**: The random walk comparison (p_adj=0.059) just misses the 0.05 threshold. The improvement from 0.102 is real (driven by the tail-aware mean being a better forecast), but it's still technically "borderline significant" rather than "significant."

5. **No causal mechanism identified**: The paper documents WHAT and WHERE but can only hypothesize about WHY.

6. **Per-event tail-aware ratio instability**: Now acknowledged in the paper, but it means we can't do per-event analysis with the primary metric. The signed difference test partially addresses this gap.
