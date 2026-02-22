# Critique — Iteration 11

STATUS: CONTINUE

## Overall Assessment

The paper has comprehensively addressed all iteration 10 suggestions — the CRPS/uniform disentangling, absolute CRPS reporting, partition consistency fix, bootstrap method specification, Appendix C foregrounding, and prose precision on "34%." The surprise-magnitude section is now among the paper's strongest analytical contributions, with the mechanical vs informative decomposition clearly articulated. The remaining improvements are genuinely at the margin: one substantive analysis (volume/liquidity correlation), one framing issue (the CPI CRPS/uniform > 1.0 implication is undersold), and several minor prose items.

## Reflection on Prior Feedback

My iteration 10 suggestions were adopted completely and well:

- **Surprise-split mechanical caveat**: The paper now clearly states "part of the CRPS/MAE effect is mechanical" and provides both CRPS/uniform and absolute CRPS comparisons. This is exactly what I asked for, and the execution is strong. The CRPS/uniform comparison is the cleanest addition — it's genuinely independent of surprise magnitude and confirms the pattern is real.
- **Interior-only partition consistency**: Fixed. The paper now notes "Interior-only ratios use the same event partition as the tail-aware split."
- **Temporal CI bootstrap method**: Specified as "percentile method" in the section header.
- **Appendix C foregrounded**: Added to the abstract — "We document 13 initially significant findings that were invalidated or substantially weakened by methodological corrections." This is well-placed.
- **"34% CRPS improvement" language**: Now says "CRPS is 34% below the point-forecast MAE" — precise and correct.

**Dead-end awareness after 11 iterations:** The statistical architecture has been complete since iteration 9. The analytical additions (surprise split, CRPS/uniform, absolute CRPS) in iterations 10-11 were the last substantive improvements. We are now in prose-polishing and optional-enrichment territory. The paper is publishable in its current form; remaining suggestions increase quality at the margin but are not blocking.

## Scores
| Criterion | Score | Delta | Comment |
|-----------|-------|-------|---------|
| Novelty | 7.5/10 | — | Stable. CRPS/MAE diagnostic + decoupling finding + surprise-magnitude pattern |
| Methodological Rigor | 9/10 | — | Stable. Mechanical vs informative decomposition was the last gap; now closed |
| Economic Significance | 8.5/10 | +0.5 | CRPS/uniform confirmation strengthens the practical recommendation |
| Narrative Clarity | 8.5/10 | +0.5 | Surprise section is now clearly argued; mechanical caveat reads naturally |
| Blog Publishability | 8.5/10 | +0.5 | Publishable with minor polish. No remaining blockers |

## Strength of Claim Assessment

**Claim 1: JC distributions robustly add value (CRPS/MAE=0.66, CI [0.57, 0.76])**
- Evidence: **Conclusive.** Unchanged. Five temporal CIs all exclude 1.0. All 16 LOO ratios < 1.0. Bulletproof.
- Paper labels correctly. No change needed.

**Claim 2: CPI distributions are harmful (CRPS/MAE=1.58, CI [1.04, 2.52])**
- Evidence: **Conclusive with thin margins, correctly noted.** The dual bootstrap (BCa + block) both excluding 1.0 is compelling. The thin lower bounds (1.04, 1.06) are honestly acknowledged.
- **One subtle issue**: The interior-only CI [0.84, 2.02] *includes* 1.0 while the tail-aware CI [1.04, 2.52] excludes it. The "CPI distributions are harmful" claim is statistically significant only under the tail-aware specification. The paper correctly identifies tail-aware as preferred ("methodologically preferred because it ensures the numerator and denominator use consistent distributional assumptions"), but a hostile reviewer could note that specification-sensitivity of the significance boundary is a soft point. The paper could preempt this by adding one sentence: "Under the interior-only specification, the CI includes 1.0 [0.84, 2.02], though the converging evidence from LOO analysis (all 14 ratios > 1.0), PIT bias (mean=0.61), and signed-difference test (10/14 positive) supports the tail-aware conclusion."
- **Rating**: Correctly labeled as conclusive with five converging diagnostics. The CI margin concern is acknowledged. Good.

**Claim 3: Point-vs-distribution decoupling ("first empirical demonstration in prediction markets")**
- Evidence: **Strong.** The qualification "in prediction markets" is important and correctly scoped. The concept (calibration-sharpness decoupling) is well-established in forecast verification — Murphy 1993, Hersbach 2000 are cited. The novelty is demonstrating it empirically in a market context. Correctly labeled.
- **Could be STRONGER**: The paper hedges with "to our knowledge" — this is appropriate caution, but 10 iterations of thorough literature engagement give reasonable confidence this is genuinely novel. I won't push harder here; the hedging is good practice.

**Claim 4: Surprise-magnitude pattern**
- Evidence: **Suggestive, now correctly labeled.** The paper says "This finding has practical implications, though part of the CRPS/MAE effect is mechanical." It then provides the CRPS/uniform confirmation. This is well-calibrated framing. The Spearman ρ=−0.68 (p=0.008) provides independent support. The CRPS/uniform finding (CPI: 1.42 vs 2.34) confirms genuine signal beyond the mechanical component. No further adjustment needed.

**Claim 5: TIPS Granger-causes Kalshi (F=12.24, p=0.005)**
- Evidence: **Conclusive for the statistical test.** The caveat about stale prices in thin markets is appropriate. However, the paper could note that the asymmetry is itself informative: Kalshi→TIPS shows F=0.0, p=1.0. Even if the TIPS→Kalshi direction is partly stale pricing, the complete absence of reverse Granger causality suggests Kalshi CPI markets are purely derivative of bond market information at the daily frequency.

**Underemphasized finding: CPI CRPS/uniform > 1.0 for ALL subsets.**
The paper notes this parenthetically: "even the high-surprise CPI CRPS/uniform exceeds 1.0, meaning CPI distributions underperform uniform for all events." This deserves more emphasis. CPI distributions are not just worse than point forecasts — they are worse than a uniform distribution over the strike range. This is a stronger, more damning statement than CRPS/MAE > 1.0, because it means the distributions contain *negative* information relative to maximum ignorance. The practical takeaway could be sharpened: "CPI distributions are not merely uninformative — they are actively misleading, performing worse than random guessing within the strike range."

## Novelty Assessment

The novelty portfolio is mature and well-established:
1. **CRPS/MAE diagnostic** — genuine contribution to prediction market evaluation
2. **Point-vs-distribution decoupling** — the paper's most citable finding
3. **Surprise-magnitude pattern with CRPS/uniform confirmation** — methodologically clean
4. **Systematic downgrade documentation** (Appendix C) — distinctive for blog audience
5. **JC 2-strike > 3+-strike finding** — counterintuitive, practically relevant

**One missed novelty angle**: The paper does not examine whether distributional quality correlates with *trading volume or liquidity*. The data includes a `volume` column in the strike markets DataFrame (visible in experiment7/implied_distributions.py line 69). A Spearman correlation between per-event total volume and CRPS/MAE would directly test the liquidity mechanism (mechanism 4 in "Why Do Jobless Claims and CPI Diverge?"). This would be a genuinely new analysis that distinguishes between the four proposed mechanisms — currently they are all untested hypotheses.

## Robustness Assessment

### Code Verification (Iteration 11)

**CRPS computation (experiment12/distributional_calibration.py):**
- The piecewise-linear CDF model is correctly implemented. The `_integrate_squared_linear` helper uses the exact analytic formula for integrating a squared linear function — verified correct.
- Tail extension logic: `max(strike_range * 0.5, 1.0)` plus coverage of realized values. This is appropriate and well-documented.
- The breakpoint construction ensures the integration is exact (no numerical quadrature error beyond floating-point).
- **No bugs found.**

**Surprise split code (run.py lines 1560–1623):**
- Partition consistency fix verified: `s_int.loc[s_int.index.isin(high_events.index)]` correctly uses the tail-aware partition for interior-only ratios.
- CRPS/uniform computation correctly uses the same event groupings.
- **No bugs found.**

**Data verification from CSV:**
- CPI: 14 events, CRPS/MAE(TA) = 1.576 ≈ paper's 1.58 ✓
- JC: 16 events, CRPS/MAE(TA) = 0.660 ≈ paper's 0.66 ✓
- One notable edge case: KXJOBLESSCLAIMS-26JAN29 has MAE_TA=350 (tail-aware mean=209,350 vs realized=209,000). Per-event ratio ≈ 10.4. This is correctly handled by ratio-of-means aggregation (which doesn't let this dominate) and is exactly why the paper's discussion of mean-of-ratios instability (Table in Per-Event Heterogeneity) is important.

**PIT computation (run.py lines 1139–1199):**
- `survival = np.interp(realized, strikes, cdf_vals)` then `pit = 1.0 - survival` is correct because `cdf_values` stores P(X > strike) (survival function).
- However, `np.interp` linearly interpolates the *survival* function between strikes. For 2-strike CPI events, this means the PIT is based on a single linear segment — the PIT values are mechanically constrained to a narrow range. This is an inherent limitation of the 2-strike structure, not a code bug.

**Bootstrap CI for temporal analysis:**
- Percentile bootstrap (not BCa) is used, as now disclosed in the paper. This is conservative: BCa would likely produce tighter CIs. The inconsistency with the main analysis (BCa) is now transparently noted.

**One code issue I did NOT raise before:**
In `experiment12/distributional_calibration.py`, the `compute_uniform_crps` function uses `n_points = 50` to discretize the uniform CDF and then feeds it through the general `compute_crps` function. While this is correct in the limit, 50 points is more than sufficient for the trapezoidal integration used. However, for consistency, the function could compute the closed-form CRPS for the uniform distribution (which has an analytic expression). This is a code quality nit, not an accuracy issue — the 50-point discretization is accurate to within machine precision for this integral.

### Statistical Robustness

The paper's statistical architecture is thorough:
- BCa bootstrap (main CIs)
- Block bootstrap (serial correlation)
- Leave-one-out sensitivity
- Signed-difference test (non-ratio metric)
- Mann-Whitney + permutation (heterogeneity)
- CRPS/uniform (mechanically independent of surprise)
- Temporal stability (5 timepoints)
- PIT diagnostic (directional bias)
- Power analysis

**One missing check**: A simple temporal stability analysis — split the 14 CPI events into first 7 and last 7 chronologically, compute CRPS/MAE for each half. If the CPI distributional penalty is driven by early market immaturity (Kalshi launched CPI markets relatively recently), this would show improving ratios over time. If the penalty is persistent, the finding is more robust. This is ~5 lines of code and provides a proto-out-of-sample check.

## The One Big Thing

**Add a volume/liquidity correlation analysis to test the liquidity mechanism hypothesis.**

The paper proposes four mechanisms for the CPI-JC divergence (Section 2, "Why Do Jobless Claims and CPI Diverge?") but tests none of them directly. The `volume` field is available in the strike market data. Computing the Spearman correlation between per-event total volume and CRPS/MAE ratio would directly test mechanism 4 (liquidity). This is:

- **High impact**: If volume correlates with CRPS/MAE, it provides a *testable, actionable* insight for Kalshi — liquidity provision at extreme strikes would improve distributional quality. If it doesn't correlate, mechanisms 1-3 (frequency, complexity, trader composition) are more likely.
- **Low effort**: ~15 lines of code. Sum `volume` across markets for each event, merge with CRPS/MAE ratios, compute Spearman ρ.
- **Novel**: No prediction market paper tests the volume → distributional quality link.
- **Practically relevant**: Kalshi can directly act on liquidity findings (market-making incentives, fee adjustments).

This would transform the "Why Do They Diverge?" section from four untested hypotheses to three untested hypotheses plus one empirical finding.

## Other Issues

### Must Fix (blocks publication)

None. The paper is publishable as-is.

### Should Fix (strengthens paper)

1. **Sharpen the CPI CRPS/uniform > 1.0 implication.** The paper buries the fact that CPI distributions underperform uniform for *all* subsets (high-surprise: 1.42, low-surprise: 2.34). This means CPI distributions contain negative information relative to maximum ignorance — a stronger statement than CRPS/MAE > 1.0 alone. Add one sentence to the practical takeaways: "CPI distributions perform worse than a uniform (maximally uninformative) distribution over the strike range, indicating the market's probability assessments contain negative distributional information." This sharpens the recommendation from "ignore the spread" to "the spread is actively misleading."

2. **Preempt the specification-sensitivity objection for CPI.** The interior-only CI [0.84, 2.02] includes 1.0 while tail-aware [1.04, 2.52] excludes it. A hostile reviewer will note this. Add one sentence in the main result section: "Under the less-preferred interior-only specification (which discards tail probability mass), the CI includes 1.0; the converging evidence from five independent diagnostics (LOO, PIT, signed-difference, block bootstrap, CRPS/uniform) supports the tail-aware conclusion." This acknowledges the sensitivity while directing the reader to the convergence argument.

3. **Add a chronological stability check for CPI (first 7 vs last 7 events).** If the CPI distributional penalty is improving over time as the market matures, this is both practically relevant (the recommendation may become obsolete) and methodologically important (time-varying calibration). If the penalty is stable, it strengthens the claim. ~5 lines of code:
   ```python
   cpi_sorted = crps_df[crps_df["series"] == "KXCPI"].sort_values("event_ticker")
   first_half = cpi_sorted.head(7)
   second_half = cpi_sorted.tail(7)
   print(f"CPI first 7: CRPS/MAE = {first_half['kalshi_crps'].mean() / first_half['point_crps_tail_aware'].mean():.3f}")
   print(f"CPI last 7:  CRPS/MAE = {second_half['kalshi_crps'].mean() / second_half['point_crps_tail_aware'].mean():.3f}")
   ```

4. **Minor: the abstract is getting long.** At ~200 words, it's appropriate for a journal paper but long for a blog post. Consider splitting into a 2-sentence blog hook ("Prediction market point forecasts and distributional forecasts can diverge dramatically...") followed by the detailed abstract below the fold. This is a blog-format consideration, not a content issue.

### New Experiments / Code to Write

1. **Volume/liquidity correlation (~15 lines):**
   ```python
   # In experiment13/run.py, after CRPS results are computed:
   from experiment7.implied_distributions import load_targeted_markets, extract_strike_markets
   markets_df = load_targeted_markets()
   strike_df = extract_strike_markets(markets_df)

   # Per-event total volume
   event_volumes = strike_df.groupby("event_ticker")["volume"].sum().reset_index()
   event_volumes.columns = ["event_ticker", "total_volume"]

   # Merge with CRPS/MAE ratios
   merged = crps_df.merge(event_volumes, on="event_ticker", how="left")
   merged["crps_mae_ta"] = merged["kalshi_crps"] / merged["point_crps_tail_aware"].clip(lower=1e-10)

   for series in ["KXCPI", "KXJOBLESSCLAIMS"]:
       s = merged[merged["series"] == series].dropna(subset=["total_volume", "crps_mae_ta"])
       if len(s) >= 5:
           rho, p = stats.spearmanr(s["total_volume"], s["crps_mae_ta"])
           print(f"{series}: volume-CRPS/MAE Spearman ρ={rho:.3f}, p={p:.4f}")
   ```

2. **Chronological stability check (~5 lines, as shown in Should Fix #3 above).**

3. **Scatter plot: surprise vs CRPS/MAE** (suggested in iteration 10 — may not have been implemented yet as it's a visualization, not a statistical test). For the blog format, this would be the single most communicative figure. Two panels (CPI, JC), annotated with Spearman ρ. Even without the plot, adding the Spearman ρ to the executive summary table would help.

### Acknowledged Limitations (inherent, not actionable)

1. **Two series only.** Cannot be fixed without new Kalshi offerings.
2. **Small n per series** (14 CPI, 16 JC). Fundamental.
3. **In-sample only.** Cannot cross-validate at current n.
4. **2-strike CPI markets are inherently coarse.** The PIT, CRPS, and implied mean are all mechanically constrained by having only two points on the CDF. This limitation is real but the paper addresses it via the strike-count analysis.
5. **CPI CI lower bounds near 1.0.** Fundamental sample-size limitation.
6. **Mechanisms 1-3 (frequency, complexity, trader composition) are untestable with public data.** Even mechanism 4 (liquidity) can only be tested via volume as a proxy, not order book depth.

## Verdict

**MINOR REVISIONS**

The paper is substantively complete and blog-publishable. Eleven iterations have produced a rigorous, well-structured analysis with clear practical recommendations, thorough robustness architecture, and honest caveats. The core claims are well-supported. The remaining suggestions — volume/liquidity analysis, CRPS/uniform emphasis, specification-sensitivity preemption, chronological stability check — are quality improvements that would strengthen an already publishable paper. The volume analysis is the highest-value remaining addition because it moves one of the four proposed mechanisms from hypothesis to evidence. The paper could be published today without damage to Kalshi's research credibility; these changes would make it distinctly stronger.
