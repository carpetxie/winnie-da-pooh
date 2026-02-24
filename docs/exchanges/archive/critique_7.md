# Critique — Iteration 7

STATUS: CONTINUE

## Overall Assessment

The paper has matured substantially. The 11-series, 248-event dataset with full PIT coverage, cross-series horse races, and serial correlation analysis represents a genuinely comprehensive study. The researcher's execution of iteration 6 feedback was thorough — PIT extended to all 11 series, horse race expanded to 3 series, KXPCECORE discrepancy explained, monitoring protocol added. The remaining issues are about sharpening presentation and elevating underplayed findings, not fixing structural problems.

## Data Sufficiency Audit

**The dataset is now adequate for the paper's claims. I am not raising data expansion as a priority this iteration.**

- **11 series, 248 events** covers the vast majority of Kalshi's multi-strike economic markets.
- **Remaining unfetched series** (KXRETAIL, KXACPI): KXACPI is likely redundant with CPI/KXCPI. KXRETAIL would add marginal value. Neither would change conclusions. Keeping as low-priority "nice to have."
- **Per-series power**: GDP CI excludes 1.0. JC borderline [0.37, 1.02] — needs ~20-25 events; only solvable by waiting for new events to settle. Not a code fix.
- **CPI temporal split**: p=0.18, needs ~95 events. Not fixable.
- **FED n=4**: Genuinely structural.

**Assessment: Data sufficiency is no longer the binding constraint.** The binding constraints are now analytical presentation and making the novel contributions as prominent as possible.

## Reflection on Prior Feedback

### Iteration 6 — all actionable points addressed:
1. ✅ PIT extended to all 11 series (was #1 must-fix)
2. ✅ "Good point forecast inflates ratio" defense added
3. ✅ Horse race extended to 3 series (KXFRM d=−0.55, KXU3 d=−0.07)
4. ✅ Serial correlation extended to 8 series (7/8 independent)
5. ✅ KXPCECORE 2.06→1.22 discrepancy explained
6. ✅ Monitoring protocol added
7. ✅ OOS diagnostic value clarified

### What I'm dropping:
- **KXRETAIL/KXACPI**: Low priority, won't change conclusions.
- **GDP temporal snapshot sensitivity**: Researcher reasonably explained pipeline integration complexity. Existing GDP CI [0.31, 0.77] and LOO [0.45, 0.51] are already conclusive.
- All previously addressed points — no circular feedback.

### Researcher pushbacks accepted:
- KXRETAIL declined — reasonable given 11-series coverage.
- GDP temporal sensitivity deferred — reasonable given existing strength of GDP result.

## Scores

| Criterion | Score | Delta | Comment |
|-----------|-------|-------|---------|
| Data Sufficiency | 8/10 | +1 | 11 series, 248 events, full PIT and serial correlation coverage. Marginal gains remain but non-critical. |
| Novelty | 8/10 | +1 | Universal overconcentration finding and cross-series horse race are genuinely new. Could be made more prominent. |
| Methodological Rigor | 8/10 | +1 | Full PIT, serial correlation for 8 series, BCa bootstrap, LOO, Bonferroni. One reproducibility concern (see below). |
| Economic Significance | 8/10 | +1 | "9/11 series: use the full distribution" + monitoring protocol — directly actionable. Overconcentration finding underplayed. |
| Blog Publishability | 8/10 | +1 | Close to publication-ready. Issues below are polish, not structural. |

## Strength of Claim Assessment

### Claim 1: "Prediction market distributions add value for 9 of 11 economic series"
**Status: CONCLUSIVE. Correctly labeled.** No change needed. Sign test p=0.004, LOO unanimity in 8/9. Rock solid.

### Claim 2: "GDP is the standout (CRPS/MAE=0.48, CI excludes 1.0)"
**Status: CONCLUSIVE. Correctly labeled.** No change needed.

### Claim 3: "Point and distributional calibration can diverge independently"
**Status: SUGGESTIVE → could be labeled STRONGER.** The CPI evidence (d=−0.85 vs RW, CRPS/MAE=1.32) is compelling. The paper could strengthen this by explicitly noting that KXFRM shows the *complementary* pattern — good point forecasts (d=−0.55) AND good distributions (0.85). This demonstrates the decoupling is genuine: CPI diverges while KXFRM aligns, proving point and distributional quality are truly independent dimensions.

### Claim 4: "Markets universally understate uncertainty (overconcentration)"
**Status: SUGGESTIVE — SIGNIFICANTLY UNDERPLAYED.** All 11 series show std(PIT) < 0.289. This is the paper's most *universal* finding — it holds for every single series regardless of CRPS/MAE ratio, series type, sample size, or time period. Yet it appears as one bullet point in Section 4. This deserves headline treatment. "Prediction markets are systematically overconfident across all economic series" is arguably as important as the main CRPS/MAE finding.

### Claim 5: "Volume does not predict distributional quality"
**Status: SUGGESTIVE — UNDERPLAYED.** ρ=0.14, p=0.27. Important market design implication (liquidity alone won't fix calibration) buried in Section 4. Should feature more prominently in Appendix C.

### Claim 6: "Kruskal-Wallis p=0.122, heterogeneity not significant at 11 series"
**Status: CORRECTLY REPORTED.** The evolution table (p=0.019→0.005→0.122) is a methodological contribution. No change needed.

## Novelty Assessment

**What's genuinely new (ranked):**
1. **Universal overconcentration** — All 11 series show std(PIT) below the uniform ideal. No prior prediction market study documents this at this scale. This should be elevated to a headline finding.
2. **CRPS/MAE ratio as a per-series diagnostic** — Novel application to prediction markets.
3. **Point-distribution decoupling** — First demonstration that accurate point forecasts can coexist with miscalibrated distributions.
4. **Pre-registered OOS failure** — Rare transparency in applied finance.
5. **Cross-series horse race** — KXFRM result (d=−0.55, n=61) is the paper's most statistically powerful finding.

**What would increase novelty further:**
1. **Elevate overconcentration** — Move from Section 4 to abstract + takeaways. Frame as: "Markets know *where* outcomes will land but understate *how uncertain* they are."
2. **Backtest the monitoring protocol** — Run the proposed 8-event window on all 11 series retrospectively to show detection rates (see New Experiments below).

## Robustness Assessment

### Code review: methodology is sound ✅
Verified in experiment12/distributional_calibration.py, experiment13/run.py, and scripts/iteration6_analyses.py:
- CRPS: piecewise integration with dynamic tail extension (scale-aware), proper CDF construction
- PIT: 1 − interpolated survival function, correct implementation
- Bootstrap: BCa with 10,000 resamples, fixed seed (42)
- LOO: ratio-of-means (robust to outliers, not mean-of-ratios)
- Serial correlation: lag-1 Spearman ρ for 8 series, block bootstrap for CPI
- Scale-mixing in heterogeneity tests: documented and mitigated with scale-free variant

### Code reproducibility concern ⚠️
The iteration 6 analyses (PIT for 7 new series, cross-series horse race, serial correlation for 8 series) live in `scripts/iteration6_analyses.py` — separate from the main `experiment13/run.py` pipeline. Running `uv run python -m experiment13.run` alone does **not** reproduce the full 11-series PIT table or cross-series horse race. This isn't a methodological bug but it's a reproducibility gap. At minimum, document which scripts need to be run to reproduce all reported results.

### Potential hostile reviewer attacks:

1. **"Overconcentration could be a bid-ask spread artifact."** Midpoint prices mechanically compress toward 0.5, making implied CDFs narrower than true beliefs. The paper doesn't discuss this mechanism. The volume-independence result (ρ=0.14, p=0.27) weakly argues against thin-market mechanics as the sole driver, but a sentence acknowledging the bid-ask possibility would help.

2. **"The sign test pools heterogeneous series."** 248 events from 11 series with different dynamics are treated as exchangeable. CPI (n=33) contributes 5x the weight of ISM (n=7). The per-series LOO analysis mitigates this, but one sentence noting the pooling assumption would preempt the attack.

3. **"CRPS/MAE ratio double-counts the point forecast."** Since CRPS incorporates point forecast quality and MAE *is* point forecast quality, a reviewer might argue the ratio is circular. Defense: the ratio measures the *marginal* value of distributional spread beyond the point forecast. Making this explicit would help.

## The One Big Thing

**Elevate the universal overconcentration finding to a headline result.**

All 11 series — every single one in the dataset — show std(PIT) below the theoretical 0.289 for a uniform distribution. This means prediction markets *systematically understate uncertainty*. This is:
- **Universal** (not series-specific, unlike CRPS/MAE which varies)
- **Novel** (not documented at this scale for prediction markets)
- **Actionable** (Kalshi could design interventions; traders should account for wider uncertainty)
- **Mechanistically interesting** (bid-ask compression? overconfident crowds? herding?)

Currently this finding is buried in one bullet point in Section 4. It should:
1. Appear in the abstract (one sentence)
2. Appear in the practical takeaways
3. Get 2-3 sentences discussing possible mechanisms

This is a *presentation* change for findings already in the paper — no new data or code needed for the core change.

## Other Issues

### Must Fix (blocks publication)

1. **Elevate overconcentration to abstract and takeaways.** Add one sentence to abstract: "A universal overconcentration pattern — markets systematically understate uncertainty across all 11 series — emerges as the dominant calibration failure mode." Add to practical takeaways: "All series show overconcentration; markets know *where* outcomes will land but understate *how uncertain* they are." Add 2-3 sentences discussing possible mechanisms: (a) bid-ask spread compression making midpoints narrower than true beliefs, (b) overconfident participants, (c) the same favorite-longshot bias making tail strikes too cheap. Note that volume-independence weakly argues against thin-market mechanics alone.

2. **Add std(PIT) values to the PIT table.** The overconcentration claim requires quantitative evidence in the table itself. Currently the PIT table shows mean PIT, CI, KS p, CvM p, and bias direction. Adding a std(PIT) column (ideal = 0.289) makes the overconcentration visible at a glance and supports the elevated claim. This is trivially computable from existing data.

### Should Fix (strengthens paper)

1. **Document reproducibility path.** Add a note (in methodology or CLAUDE.md) listing which scripts reproduce all reported results: `experiment13/run.py` for core CRPS/MAE + old PIT, `scripts/iteration6_analyses.py` for expanded PIT + horse race + serial correlation. Alternatively, integrate the iteration6 results into the main pipeline.

2. **Strengthen point-distribution decoupling with KXFRM counterexample.** KXFRM has good point forecasts (d=−0.55 vs RW) AND good distributions (CRPS/MAE=0.85). Mention explicitly: "KXFRM demonstrates that point and distributional quality *can* align, making CPI's divergence more informative — it is genuine, not a methodological artifact."

3. **Add sentence on sign test pooling assumption.** "The sign test treats events as exchangeable across series; per-series LOO analysis (8/9 unanimous) provides convergent evidence that the finding is not driven by any single dominant series."

4. **Address the CRPS/MAE "double-counting" concern.** Add one sentence: "The CRPS/MAE ratio measures the *marginal* information value of distributional spread beyond the point forecast — a ratio below 1 means the market's probabilistic spread reduces forecast error compared to using the point forecast alone."

### New Experiments / Code to Write

1. **Backtest the monitoring protocol on all 11 series (medium priority):**
   - Compute rolling 8-event CRPS/MAE for each series (the paper already does this for CPI)
   - For each series, report: number of windows, number with ratio > 1.0, number of "3-consecutive-window" alerts
   - Expected: CPI triggers alert at structural break; Core PCE and FED persistently flagged; 8 other series have 0 or very few alerts
   - This transforms the monitoring protocol from a *proposal* into *validated evidence*
   - Implementation: one loop extending the existing rolling-window code from CPI to all series

2. **Report std(PIT) in the paper (trivial):**
   - Add column to existing PIT table
   - Values already computed in the analysis — just need to be reported

### Genuinely Unfixable Limitations

1. **FED n=4.** FOMC meets ~8 times/year; only 4 settled multi-strike events exist. Cannot expand without waiting.
2. **No order-book depth data.** Kalshi doesn't expose historical LOB. Cannot directly test bid-ask spread mechanisms for overconcentration.
3. **CPI temporal split underpowered (p=0.18, needs ~95 events).** Only 33 exist.
4. **SPF monthly CPI proxy.** No public monthly CPI point forecast; annual/12 is the best available.
5. **Overconcentration mechanism untestable.** Can speculate about causes (bid-ask, overconfidence, herding) but cannot distinguish without LOB data or experimental manipulation.

## Verdict

**MINOR REVISIONS**

The paper is close to publication-ready. The dataset (11 series, 248 events) is adequate. The methodology is rigorous and the code is correct. The must-fix items are purely presentational — elevating the overconcentration finding and adding std(PIT) to the table require no new data or analysis. The should-fix items (reproducibility note, KXFRM counterexample, pooling/double-counting sentences) are single-sentence additions. With these changes, the paper is ready for the Kalshi Research blog.
