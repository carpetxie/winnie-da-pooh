# Critique — Iteration 8

STATUS: CONTINUE

## Overall Assessment

The paper has matured substantially across seven iterations — the statistical architecture is now robust, the claims are well-calibrated, and the code correctly implements the described methodology. The iteration 7 additions (surprise magnitude analysis, per-event autocorrelation, scoped novelty claim) were all productive. However, the paper's temporal analysis — its most speculative section — remains inadequately tested. The "three-phase" hypothesis is presented as a suggestive narrative but could be rigorously tested with per-event temporal trajectories, which would either strengthen it into a real finding or reveal it as an aggregation artifact. This is the highest-impact remaining improvement.

## Reflection on Prior Feedback

My iteration 7 suggestions were well-received and productively implemented:
- **Surprise magnitude analysis** (the "one big thing"): Excellent execution. Spearman ρ=−0.68 (p=0.008) for CPI is a genuinely novel finding that adds important nuance. The researcher correctly identified that the conditional-by-direction analysis is dominated by the small-MAE effect rather than independent directional signal — this was an honest assessment.
- **Scope "first empirical demonstration"**: Adopted cleanly. One-phrase fix that preempts the most predictable objection.
- **Per-event autocorrelation**: Adopted with exact values (CPI AR(1)=0.12, JC AR(1)=0.04). Strengthens the independence assumption.
- **PIT claim consistency**: Fixed from "indicating" to "consistent with." Minor but correct.

**Pushbacks I accept:**
- The researcher's assessment that the conditional-by-direction split is dominated by small-MAE mechanics rather than an independent directional signal was well-reasoned. The Spearman correlation subsumes this finding. No need to re-raise.

No dead-end suggestions from iteration 7. All accepted changes improved the paper.

**Code verification note**: I verified the three most severe issues flagged by automated code review — the PIT calculation is correct (cdf_values stores survival P(X>strike), so `1.0 - survival` correctly gives CDF), the Spearman correlation pairs are correct (both arrays from the same DataFrame rows after identical dropna), and the circular block bootstrap wrapping is standard methodology (Politis & Romano, 1992). No genuine bugs found in the critical statistical computations.

## Scores
| Criterion | Score | Delta | Comment |
|-----------|-------|-------|---------|
| Novelty | 7.5/10 | +0.5 | Surprise magnitude finding is genuinely new and well-integrated |
| Methodological Rigor | 8.5/10 | +0.5 | Statistical architecture is thorough; temporal analysis remains the weak link |
| Economic Significance | 7.5/10 | +0.5 | Surprise magnitude finding has direct trading implications |
| Narrative Clarity | 7/10 | — | Dense but coherent; blog length remains a concern |
| Blog Publishability | 7.5/10 | — | Close; temporal hypothesis needs tightening before final publication |

## Strength of Claim Assessment

**Claim 1: JC distributions robustly add value (CRPS/MAE=0.66, CI [0.57, 0.76])**
- Evidence level: **Conclusive**. Paper labels correctly. All 5 temporal CIs exclude 1.0 (tail-aware). All 16 LOO ratios < 1.0. Signed-difference p=0.001. Nothing to change.

**Claim 2: CPI distributions are harmful (CRPS/MAE=1.58, block bootstrap CI [1.06, 2.63])**
- Evidence level: **Conclusive, but the margin is thin.** The lower bound (1.06) barely excludes 1.0. The paper correctly presents five converging diagnostics. However, an underemphasis: the BCa bootstrap CI [1.04, 2.52] and the block bootstrap CI [1.06, 2.63] independently exclude 1.0. This convergence of two different CI methods — one iid, one serial-correlation-adjusted — is itself a form of robustness evidence that deserves explicit highlighting, not just sequential presentation.

**Claim 3: Three-phase temporal pattern (well-calibrated early, worst mid-life, convergent late)**
- Evidence level: **Speculative — paper labels it correctly as "not statistically confirmed" but gives it too much narrative weight.** The point estimates show the U-shape, but no individual CPI temporal CI excludes 1.0 except at 50%. The paper correctly hedges with "speculative hypothesis," but the three-phase narrative occupies ~300 words and generates testable predictions as if it were established. The critical missing test: **does the U-shape persist at the per-event level, or is it an aggregation artifact?** (See "One Big Thing" below.)

**Claim 4: Surprise magnitude inverse correlation (CPI ρ=−0.68, p=0.008)**
- Evidence level: **Strong**. Well-labeled. The two implications are correctly differentiated. The caveat that the ratio is "most informative for large surprises" is a valuable methodological insight. This is now one of the paper's strongest secondary findings.

**Claim 5: JC 2-strike events show *better* CRPS/MAE (0.46) than 3+-strike events (0.84)**
- Evidence level: **Suggestive, but the paper underplays the tension.** The paper attributes this to "selection effects," but it creates a direct tension with the market design recommendation to add more CPI strikes. If more strikes can *hurt* distributional quality in thin markets, the recommendation needs a liquidity caveat. Currently one sentence dismisses this finding; it deserves 2–3 sentences acknowledging the tension explicitly.

## Novelty Assessment

The novelty portfolio is solid:
1. **CRPS/MAE ratio as diagnostic** — genuine contribution, well-established across iterations
2. **Point-vs-distribution decoupling in prediction markets** — now properly scoped
3. **Surprise magnitude correlation** (new in iteration 7) — genuinely novel, significant, and actionable
4. **Series-level heterogeneity** — well-supported and important for market design

**Underemphasized finding**: The JC 2-strike vs 3+-strike reversal (0.46 vs 0.84) is potentially the most counterintuitive finding in the paper and is buried in one sentence. If more strikes can hurt distributional quality in thin markets — because each additional strike is an additional opportunity for mispricing — this complicates the neat narrative that "more strikes → better distributions." The paper's recommendation to add CPI strikes from 2–3 to 4–5 might need a caveat: this only works if the additional strikes attract sufficient liquidity. This nuance differentiates the paper from naive "more data = better" thinking and is practically important for market designers.

## Robustness Assessment

### Code Verification Summary

I verified the following against the paper's claims:
- **CRPS/MAE ratios**: Manually recomputed from per_event_crps data in unified_results.json. CPI tail-aware ratio-of-means = 1.576 (paper: 1.58), JC = 0.660 (paper: 0.66). Match confirmed.
- **Block bootstrap**: CI [1.063, 2.629] matches paper [1.06, 2.63]. Circular block bootstrap implementation is correct (standard Politis & Romano methodology with modular indexing).
- **Horse race**: Random walk MAE = 0.150, Kalshi MAE = 0.068. Cohen's d = −0.849 (paper: −0.85). Bonferroni p = 0.014. All match.
- **Surprise magnitude**: Spearman ρ = −0.679 (paper: −0.68), p = 0.0076 (paper: 0.008). Per-event AR(1): CPI interior = 0.123 (paper: 0.12), JC interior = 0.035 (paper: 0.04). All match.
- **PIT**: Correctly computes 1.0 − survival(realized) where cdf_values stores survival P(X > strike). Implementation is correct.

All numbers in the paper match unified_results.json. No bugs found in statistical computations.

### Genuine Minor Code Issue: CRPS on Non-Monotone CDFs

In `experiment12/distributional_calibration.py`, the CDF is constructed from survival values (line 77: `f_values = 1.0 - np.array(cdf_values, dtype=float)`). After clipping to [0,1] (line 80), there is no monotonicity enforcement. If a mid-life snapshot has a no-arbitrage violation (2.8% rate across all hourly snapshots), the CRPS for that event would be computed on a non-distribution. The paper's violation rate is across all hourly snapshots; it would be worth verifying that none of the ~30 mid-life snapshots used for the headline CRPS computation have violations. A one-line assertion would make this bulletproof.

### Hardcoded FRED Date Windows

`experiment13/run.py` uses `"2025-12-01"` as the FRED fetch end date. Since the analysis extends through KXCPI-25DEC (released Jan 2026), this should be updated to `"2026-06-01"` or computed dynamically. This doesn't affect current results but makes the code fragile for future runs.

### Missing Temporal Analysis: Per-Event Trajectories

The temporal CRPS/MAE table (Section 2) aggregates across events at each timepoint. The "three-phase" hypothesis — well-calibrated early, worst at mid-life, convergent late — is tested only at the aggregate level. If 3–4 CPI events drive the mid-life peak while others are flat, the narrative overstates the evidence. Per-event temporal trajectories would either confirm or refute the hypothesis at the individual level.

## The One Big Thing

**Compute per-event CRPS/MAE trajectories and test whether the three-phase pattern is consistent across events or an aggregation artifact.**

Currently, the temporal table shows aggregate CRPS/MAE at 5 timepoints. A key question is unanswered: does every CPI event show the U-shaped pattern (well-calibrated early → worst mid-life → convergent late), or is the aggregate pattern driven by a few events while others are flat or inverted?

This matters because:
1. If the U-shape is consistent across events, the three-phase hypothesis is strongly supported and could be promoted from "speculative" to "suggestive"
2. If it's driven by outliers, the three-phase narrative should be significantly downgraded or removed
3. Per-event trajectories would reveal whether early-life calibration quality predicts mid-life quality — which would be directly actionable for traders (if a CPI market looks well-calibrated at 10% of life, can you trust it at 50%?)

**Specific implementation** (~40 lines in experiment13/run.py, after Phase 5):

```python
# Per-event temporal CRPS/MAE at 10%, 50%, 90% of market life
per_event_temporal = []
for event_ticker in cpi_event_tickers:
    snapshots = get_event_snapshots(event_ticker)  # from build_implied_cdf_snapshots
    if len(snapshots) < 6:
        continue
    realized = get_realized(event_ticker)
    row = {"event_ticker": event_ticker}
    for pct_label, pct in [("10%", 0.1), ("50%", 0.5), ("90%", 0.9)]:
        idx = min(int(pct * len(snapshots)), len(snapshots) - 1)
        snap = snapshots[idx]
        crps_t = compute_crps(snap["strikes"], snap["cdf_values"], realized)
        mean_ta = compute_tail_aware_mean(snap["strikes"], snap["cdf_values"])
        mae_t = abs(mean_ta - realized)
        row[f"crps_mae_{pct_label}"] = crps_t / mae_t if mae_t > 0 else None
    per_event_temporal.append(row)

# Test 1: What fraction of CPI events individually show U-shape?
n_ushape = sum(1 for r in per_event_temporal
               if r.get("crps_mae_10%") and r.get("crps_mae_50%") and r.get("crps_mae_90%")
               and r["crps_mae_10%"] < r["crps_mae_50%"] > r["crps_mae_90%"])
print(f"CPI events with U-shape pattern: {n_ushape}/{len(per_event_temporal)}")

# Test 2: Spearman correlation between 10% and 50% CRPS/MAE
early = [r["crps_mae_10%"] for r in per_event_temporal if r.get("crps_mae_10%")]
mid = [r["crps_mae_50%"] for r in per_event_temporal if r.get("crps_mae_50%")]
if len(early) >= 4 and len(mid) >= 4:
    rho, p = spearmanr(early, mid)
    print(f"Early-mid correlation: rho={rho:.3f}, p={p:.4f}")
```

Report: (1) fraction of events showing U-shape, (2) early-mid correlation. If < 50% of events show U-shape, downgrade the three-phase hypothesis. If > 70%, upgrade it.

## Other Issues

### Must Fix (blocks publication)

None. The paper has no remaining blockers.

### Should Fix (strengthens paper)

1. **Expand the JC 2-strike vs 3+-strike discussion.** The finding that JC 2-strike events have *better* CRPS/MAE (0.46) than 3+-strike events (0.84) creates a tension with the recommendation to add more CPI strikes. Add 2–3 sentences: "This finding cautions against assuming more strikes automatically improve distributional quality — the benefit of finer resolution must be weighed against the cost of thinner liquidity per strike. The recommendation to increase CPI strike density is predicated on sufficient order flow at the new strikes, as observed in the higher-volume Jobless Claims markets."

2. **Highlight convergence of two independent CI methods.** Both BCa CI [1.04, 2.52] and block bootstrap CI [1.06, 2.63] independently exclude 1.0. This convergence — two bootstrap methods with different assumptions about serial correlation — is itself robustness evidence. One sentence: "Two independent bootstrap methods (BCa assuming iid, block bootstrap adjusting for serial correlation ρ=0.23) both exclude 1.0, confirming the finding is not an artifact of either independence or serial-dependence assumptions."

3. **Acknowledge the thin margin on CPI significance.** Both CI lower bounds (1.04, 1.06) are close to 1.0. A reader demanding a 99% CI would not find significance for CPI alone. The five-diagnostic convergence is what makes the overall case conclusive, not any single CI. One sentence of explicit acknowledgment strengthens credibility with sophisticated readers who will notice the margin themselves.

4. **Update FRED fetch date window.** Change `"2025-12-01"` to a dynamic date or `"2026-06-01"` in experiment13/run.py to future-proof the code.

### New Experiments / Code to Write

1. **Per-event temporal CRPS/MAE trajectories (priority: HIGH, ~40 lines)**: As described in "The One Big Thing." Tests the three-phase hypothesis at the individual event level. Report fraction of events showing U-shape and early-mid correlation.

2. **Verify mid-life snapshot monotonicity (priority: MEDIUM, ~10 lines)**: Check that none of the ~30 mid-life snapshots used for CRPS computation have CDF violations. Log any violations found:
   ```python
   for event_ticker, snap in mid_life_snapshots.items():
       for i in range(len(snap["cdf_values"]) - 1):
           if snap["cdf_values"][i] < snap["cdf_values"][i + 1]:
               print(f"WARNING: {event_ticker} mid-life has CDF violation")
   ```
   If any are found, either exclude them or monotone-project the CDF before CRPS computation.

3. **JC 2-strike vs 3+-strike significance test (priority: LOW, ~5 lines)**: Mann-Whitney test on per-event CRPS/MAE ratios between JC 2-strike and 3+-strike events. If significant, this is a genuine novel finding about strike structure and calibration quality that strengthens the market design discussion.

### Acknowledged Limitations (inherent, not actionable)

1. **Two series only**: Inherent to current Kalshi multi-strike offerings. Well-documented.
2. **Small n per series**: n=14 CPI, n=16 JC. Cannot be fixed without more data.
3. **In-sample only**: Cannot cross-validate at current n.
4. **Untestable mechanisms**: The four hypothesized mechanisms cannot be directly tested with public data.
5. **Blog length**: ~5,500+ words. A blog version would need aggressive editing; the full analysis should be preserved as a technical companion.
6. **CPI CI lower bound margin**: Both CIs exclude 1.0 but barely (1.04, 1.06). Fundamental sample-size limitation.

## Verdict

**MINOR REVISIONS**

The paper is substantively strong and close to blog-publishable. The statistical architecture is thorough, the claims are well-calibrated, and the code correctly implements the methodology. The remaining high-priority item is testing the three-phase temporal hypothesis at the per-event level — this would either promote the hypothesis from "speculative" to "suggestive" or reveal it as an aggregation artifact, both of which improve the paper's credibility. The should-fix items (JC strike-count discussion, dual CI convergence note, thin-margin acknowledgment) are prose improvements that strengthen credibility with sophisticated readers. None of these are blockers, but the per-event temporal analysis is important enough to implement before publication — the three-phase narrative currently occupies ~300 words of prime real estate in the paper and deserves empirical backing commensurate with its prominence.
