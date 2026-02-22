# Critique — Iteration 1

STATUS: CONTINUE

## Overall Assessment (2-3 sentences)

This is a genuinely interesting paper with a novel diagnostic (CRPS/MAE ratio) that reveals actionable heterogeneity in prediction market distributional quality. The intellectual honesty is exceptional — the downgraded/invalidated findings table is rare and admirable. However, the paper's central finding rests on a critical methodological issue (the implied mean excludes tail probability, biasing the denominator of the CRPS/MAE ratio) that must be addressed before the headline numbers can be trusted.

## Scores
| Criterion | Score | Delta | Comment |
|-----------|-------|-------|---------|
| Novelty | 7/10 | — | CRPS/MAE ratio as diagnostic is genuinely useful; heterogeneity finding is new |
| Methodological Rigor | 5/10 | — | Core ratio has a biased denominator; bootstrap CIs don't fix this |
| Economic Significance | 7/10 | — | Direct market design implications for Kalshi; actionable for traders |
| Narrative Clarity | 8/10 | — | Excellent structure, honest hedging, good worked examples |
| Blog Publishability | 5/10 | — | Needs the implied mean fix and one more robustness check before publishing |

## Strength of Claim Assessment

### Claim 1: "Jobless Claims distributions add value (CRPS/MAE=0.60, CI excludes 1.0)"
**Evidence level: Suggestive, bordering on conclusive.** The CI excluding 1.0 is strong. The serial-correlation-adjusted CI [0.34, 0.89] still excludes 1.0 — this is the paper's most robust finding. However, the implied mean bias (see Robustness below) could affect the denominator. For JC, the implied mean is computed from interior probability only, and with 2–5 strikes, the tail mass can be substantial. **The paper should state this claim MORE strongly** — it survives every robustness check thrown at it. Call it "robust evidence" rather than just "the CI excludes 1.0."

### Claim 2: "CPI distributions show signs of miscalibration (CRPS/MAE=1.32, CI includes 1.0)"
**Evidence level: Suggestive, correctly labeled.** The paper hedges appropriately. The CI including 1.0 means you can't reject the null. The serial correlation adjustment widens it further. But the point estimate of 1.32, combined with the PIT directional bias (mean=0.61), and the mid-life temporal pattern — these three independent signals all point in the same direction. **The paper underplays the converging evidence.** Three independent diagnostics all suggesting CPI miscalibration is stronger than any single p-value. State this explicitly.

### Claim 3: "TIPS leads Kalshi by 1 day (Granger F=12.2, p=0.005)"
**Evidence level: Conclusive for Granger causality, but the interpretation is overclaimed.** The Granger test shows predictive information in TIPS for Kalshi at 1-day lag. But the paper interprets this as Kalshi being "downstream of bond markets in the information hierarchy." Granger causality ≠ information flow. TIPS is a daily series with high frequency; Kalshi CPI index is a constructed daily average of binary contract prices across multiple events. The Kalshi index may simply be stale (slow-updating contracts) rather than informationally downstream. **The paper should acknowledge this alternative interpretation.**

### Claim 4: "Kalshi directionally outperforms random walk (p_raw=0.026, d=-0.60)"
**Evidence level: Suggestive, correctly labeled.** The Bonferroni correction to p=0.102 is honest. The power analysis showing only 4 more months needed is useful. The paper handles this correctly.

### Claim 5: "The CPI distributional penalty is concentrated at mid-life rather than pervasive"
**Evidence level: Speculative, correctly labeled as directional.** The U-shape has no individual timepoint where the CI excludes 1.0 (except barely at 90%). This is pattern-spotting with n=14. The paper labels it "directional rather than confirmed" which is correct, but then devotes substantial space to a "three-phase process" hypothesis that reads like confirmed theory. **Trim the speculative hypothesis or label it more prominently as speculative.**

## Novelty Assessment

### What's genuinely new:
1. **CRPS/MAE ratio as a diagnostic** — I'm not aware of this being used specifically for prediction markets. The weather forecasting literature uses CRPS decomposition (Hersbach 2000), and CRPS skill scores are standard, but framing the ratio against the market's own implied mean as a "distributional value-add" test is a useful contribution.
2. **Per-series heterogeneity** — Most prediction market calibration papers pool across markets. Showing that distributional quality varies dramatically by underlying series is genuinely new and actionable.
3. **The downgraded findings table** — This is a methodological contribution in itself. Showing the full audit trail of initially-significant-then-invalidated findings is rare and valuable for the meta-science of prediction market research.

### What's underemphasized:
1. **The temporal CRPS evolution** is actually the most interesting part of the paper. The fact that CPI distributions are well-calibrated early and late but worst at mid-life is a novel, testable pattern. The paper buries this in Section 2 under snapshot sensitivity, when it deserves to be a headline finding.
2. **The PIT analysis** provides the key mechanistic insight (CPI has directional bias, JC doesn't) but is relegated to an appendix. It should be in the main text.

### What could increase novelty:
1. **CRPS decomposition** — The paper already mentions Hersbach (2000) but doesn't implement it. Decomposing CRPS into reliability + resolution + uncertainty would tell you *why* CPI is worse: is it biased (reliability), uninformative (resolution), or both? This is concrete, implementable, and would be a significant value-add.
2. **Quantile-specific CRPS** — Computing CRPS by CDF region (below 25th percentile, 25-75th, above 75th) would distinguish center mispricing from tail mispricing, directly testing mechanism 4 (liquidity at extreme strikes).

## Robustness Assessment

### Critical Issue: Implied Mean Excludes Tail Probability

This is the single most important methodological concern. Looking at the code in `experiment7/implied_distributions.py`, lines 206-214:

```python
# Implied mean (midpoint-weighted)
total_interior = sum(pdf_values)
if total_interior > 0:
    weighted_sum = 0
    for i, p in enumerate(pdf_values):
        midpoint = (bin_edges[i] + bin_edges[i + 1]) / 2
        weighted_sum += midpoint * p
    implied_mean = weighted_sum / total_interior
```

This computes the implied mean using **only interior probability mass** (probability between the min and max strikes). Tail probability — P(X < min_strike) and P(X > max_strike) — is discarded. For CPI events with only 2 strikes, the total interior probability can be 60% or less, meaning 40%+ of probability mass is ignored.

The paper acknowledges this in a note: *"Tail probability beyond boundary strikes is not allocated to specific points."* But it understates the impact. Looking at the data:

- 2-strike CPI events (n=10): mean CRPS/MAE ratio = **1.81**
- 3-strike CPI events (n=4): mean CRPS/MAE ratio = **1.69**

Both are elevated, but the 2-strike events are worse. The denominator (MAE) is computed from this biased implied mean. If the tail probability systematically shifts the true mean away from the interior midpoint, MAE is artificially low (the point forecast is biased toward the interior), making the CRPS/MAE ratio artificially high.

**Why this matters:** CRPS integrates the full CDF including tails, but MAE uses only the interior mean. This creates an apples-to-oranges comparison. If you correct the implied mean to account for tail probability (e.g., by assuming uniform distribution in the tails, or by assigning tail mass to boundary points), the MAE would increase for events where the realized value falls in a tail, potentially lowering the CRPS/MAE ratio toward 1.0.

**What to do:** Compute a tail-aware implied mean that allocates tail probability to specific values (e.g., extending the piecewise-linear CDF with uniform tails as done in the CRPS computation). Re-run the CRPS/MAE analysis with this corrected mean and report both versions. If the ratio changes substantially, the current headline number is unreliable.

### Secondary Robustness Issues

1. **Reversion rate calculation in `experiment7`** (lines 303-316): The reversion check compares consecutive violations by strike pair, but if a violation at one pair resolves while a new violation appears at a different pair, it's counted as "reverted." This overstates the reversion rate. A more honest metric would check whether the *snapshot as a whole* is violation-free in the next hour.

2. **Bootstrap for temporal CIs uses percentile method** (experiment13/run.py, lines 569-578) rather than BCa, while the headline CRPS/MAE CIs use BCa. This inconsistency is minor but should be noted or homogenized.

3. **Historical benchmark for Jobless Claims** uses 2022+ to avoid COVID contamination — good. But the window is also post-Fed-tightening, a different regime than the current easing cycle. The benchmark may not be perfectly regime-neutral.

4. **The `compute_implied_pdf` function clips negative probabilities to 0** (line 199: `max(0, prob)`). This silently absorbs arbitrage violations into the PDF, potentially distorting both the implied mean and CRPS computation for events with violations.

### Code-Paper Mismatches

1. **Paper says "CRPS/MAE=0.60"** for Jobless Claims; data shows 0.5979. Rounding is fine, but the abstract says "CRPS/MAE=0.60" while the bottom line says "40% CRPS improvement over point forecasts alone." A 40% improvement corresponds to ratio=0.60, so this is consistent. Good.

2. **Paper says "n=16 Jobless Claims"** — verified in data. **"n=14 CPI"** — verified.

3. **The SPF conversion** (annual/12) is correctly flagged as an approximation in both code comments and paper text. Good.

## The One Big Thing

**Fix the implied mean computation to include tail probability, then re-run the CRPS/MAE analysis.** This is the single highest-priority change because it directly affects the headline number. The CRPS/MAE ratio is the paper's signature contribution, and if the denominator is biased, the entire diagnostic is compromised. The fix is straightforward: use the same piecewise-linear CDF used for CRPS computation to compute E[X], which naturally integrates over tails. If the corrected ratio for CPI drops to ~1.0, the story changes from "CPI distributions are harmful" to "CPI distributions are neutral" — still interesting but different. If the corrected ratio is still >1.0, the finding is much stronger.

## Other Issues

### Must Fix (blocks publication)

1. **Tail-aware implied mean** (detailed above). The current interior-only computation biases the MAE denominator of the CRPS/MAE ratio. Implement a tail-aware mean using the full piecewise-linear CDF (e.g., integrate x*dF(x) over the same domain used for CRPS). Report both the interior-only and tail-aware CRPS/MAE ratios.

2. **Clarify Granger causality interpretation.** The paper says Kalshi is "downstream of bond markets in the information hierarchy." This overinterprets Granger causality. Add a sentence acknowledging that the Kalshi CPI index may be slow-updating (stale prices) rather than informationally downstream, and that Granger causality measures predictive information, not causal information flow.

### Should Fix (strengthens paper)

1. **Promote PIT analysis from appendix to main text.** The directional asymmetry (CPI mean PIT=0.61 vs JC mean PIT=0.46) is the strongest mechanistic evidence for the CPI/JC divergence. It tells you *why* CPI distributions fail (inflation underestimation), not just *that* they fail. This deserves main-text treatment.

2. **Strengthen the JC finding.** The paper says the CI "excludes 1.0" almost in passing. This is actually the paper's most robust result — it survives serial correlation adjustment, bootstrap, and sensitivity analysis. Frame it more prominently. Consider a sentence like: "Jobless Claims distributions robustly add value across all specifications we tested."

3. **Report CRPS/MAE separately for 2-strike vs 3+-strike events.** The 2-strike events (step function CDFs) are mechanically worse at representing distributions. Showing that the CPI penalty persists even in 3-strike events (ratio=1.69 from the data) would strengthen the calibration argument. Conversely, if 3-strike events are better, that directly supports the market design recommendation of more strikes.

4. **Add a footnote or sentence explaining why the Monte Carlo strike-count robustness check (currently in Section 2) uses symmetric distributions.** The argument that CPI MoM is approximately symmetric (Shapiro-Wilk p=0.24) rests on n=14. This is underpowered to detect non-normality. Acknowledge this.

5. **The "three-phase process" hypothesis** (early priors, mid-life overreaction, late convergence) should be explicitly labeled "speculative" (it already is, but make it more visually prominent — e.g., italicize the whole paragraph or use a callout box).

### New Experiments / Code to Write

1. **Tail-aware implied mean computation.** In `experiment7/implied_distributions.py`, modify `compute_implied_pdf` (or add a new function) to compute E[X] from the full piecewise-linear CDF:
   ```python
   def compute_tail_aware_mean(strikes, survival_values, tail_extension=None):
       """Compute E[X] integrating the full CDF including tails."""
       # Convert survival to CDF
       f_values = 1.0 - np.array(survival_values)
       # Use same tail extension logic as compute_crps
       if tail_extension is None:
           strike_range = strikes[-1] - strikes[0]
           tail_extension = max(strike_range * 0.5, 1.0)
       x_min = strikes[0] - tail_extension
       x_max = strikes[-1] + tail_extension
       # E[X] = x_min + integral of [1 - F(x)] dx from x_min to x_max
       # Numerical integration over the piecewise-linear CDF
       ...
   ```
   Then re-run all CRPS/MAE ratios with the corrected mean.

2. **CRPS decomposition (Hersbach 2000).** Implement the reliability-resolution-uncertainty decomposition for both series. This would clarify whether CPI fails on reliability (biased) or resolution (uninformative). The implementation requires binning PIT values and computing the expected CRPS under perfect reliability. Add to experiment13.

3. **Quantile-region CRPS.** Split the CRPS integral into three regions: below 25th percentile of the CDF, 25-75th, and above 75th. Compare these "quantile CRPS contributions" between CPI and JC. If CPI's excess CRPS is concentrated in tails, that supports mechanism 4 (thin liquidity at extreme strikes). If it's concentrated in the center, that supports mechanism 2 (signal dimensionality confusion).

4. **Leave-one-out sensitivity for JC.** With n=16, one outlier could drive the result. Compute the CRPS/MAE ratio leaving out each event in turn. Report the range of leave-one-out ratios. If the CI still excludes 1.0 in all 16 leave-one-out samples, the finding is bulletproof.

5. **Snapshot timing robustness for CRPS/MAE headline.** The paper uses `len(snapshots) // 2` as mid-life. This is integer division and could be off by one hour. Check sensitivity: compute CRPS/MAE at snapshots //2 -1, //2, and //2 +1 and verify the headline ratio doesn't change materially.

### Acknowledged Limitations (inherent, not actionable)

1. **Small sample size (n=14 CPI, n=16 JC).** This is inherent to the data availability. The paper handles it well with power analysis and honest hedging. More data will accumulate naturally.

2. **In-sample only.** The paper correctly notes that train/test splitting is impractical at n=14. This is an inherent limitation, not a methodological error.

3. **No direct measure of tail liquidity.** The paper hypothesizes that thin order books at extreme strikes degrade CPI distributional quality, but Kalshi doesn't publish per-strike order book data. This cannot be tested directly.

4. **SPF comparison is inherently approximate.** SPF forecasts annual CPI, not monthly. The annual/12 conversion is a rough proxy. This is correctly flagged and cannot be improved without better SPF granularity.

## Responses to Seed Questions

### 1. Is the CRPS/MAE ratio framing genuinely useful, or trivial repackaging?
**Genuinely useful.** The CRPS skill score (vs historical or climatological baseline) is standard, but the ratio against the market's *own* implied mean as a "distributional value-add" diagnostic is a distinct and practical contribution. It answers a question traders actually have: "should I use the full distribution or just the point forecast?" Standard CRPS skill scores compare to external benchmarks and don't answer this question directly.

### 2. Does the heterogeneity finding have practical implications for Kalshi's market design?
**Yes, strongly.** The implication is clear: increase strike density for CPI markets (currently 2-3 strikes) to match JC markets (2-5 strikes). The paper's market design section already makes this recommendation, and it's well-supported. Additionally, the temporal finding (mid-life degradation) suggests Kalshi could monitor distributional quality in real-time and intervene (e.g., with designated market makers) when CRPS/MAE exceeds a threshold.

### 3. Are there claims that overreach the evidence?
**Yes, the Granger causality interpretation** (see Claim 3 above). "Information hierarchy" and "downstream" are causal language applied to a predictive-information test. The rest of the paper is commendably careful.

### 4. Are there claims that UNDERREACH?
**Yes, two:** (a) The JC finding is stated too weakly — it survives every robustness check and should be stated as "robust evidence." (b) The converging evidence for CPI miscalibration (CRPS/MAE point estimate, PIT directional bias, mid-life temporal pattern) is presented as three separate observations rather than synthesized into a coherent argument. The paper should explicitly note that three independent diagnostics all point in the same direction.

### 5. What's missing that would make this substantially stronger?
The tail-aware implied mean fix is the biggest missing piece. After that, the CRPS decomposition (reliability vs resolution) would add genuine analytical depth. A leave-one-out sensitivity analysis for JC would make that finding bulletproof.

### 6. If this were on the Kalshi blog, would it enhance or damage Kalshi's research credibility?
**Enhance, after the fixes.** The intellectual honesty (downgraded findings, proper corrections, honest CIs) is excellent. The finding that some markets' distributions are harmful is counterintuitively good for Kalshi — it shows serious analytical engagement and provides actionable improvement directions. But the implied mean bias issue must be fixed first; a hostile reader who catches it would undermine the entire paper.

## Verdict
**MAJOR REVISIONS**

The paper has a strong foundation, a genuinely novel diagnostic, and exceptional intellectual honesty. But the implied mean bias in the CRPS/MAE denominator is a critical issue that could change the headline numbers. Fix this, implement the CRPS decomposition for depth, and strengthen the JC claim — then this is ready for minor revisions.
