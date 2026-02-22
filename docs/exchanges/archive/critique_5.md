# Critique — Iteration 5

STATUS: CONTINUE

## Overall Assessment (2-3 sentences)

The paper has matured into a genuinely publishable piece. The iteration 4 changes — point-vs-distribution decoupling as co-headline, aggregation comparison table, interior-only MWU robustness, strengthened horse race language — all improved the paper meaningfully. The remaining issues are second-order: one code concern in the permutation test (scale-mixing), a potential alignment bug in the Granger causality pipeline, and narrative tightening for blog readability. The core statistical architecture is sound and the claims are now well-calibrated to the evidence.

## Reflection on Prior Feedback

My iteration 4 suggestions were largely productive:
- **Interior-only MWU** (must fix): Implemented correctly, yielding p=0.026 as a clean robustness check. This was the right call.
- **Point-vs-distribution decoupling as co-headline**: The researcher executed this well. The abstract now opens with the decoupling insight and the dedicated paragraph in Section 3 is compelling.
- **Aggregation comparison table**: Excellent addition. The mean-of-ratios numbers (CPI: 3.89, JC: 1.29 tail-aware) dramatically illustrate why ratio-of-means is correct.
- **Random walk language strengthening**: Good fix. "Significant at the 10% level with adequate power" is accurate.
- **Dual-metric consolidation pushback**: The researcher was right to keep both metrics visible in-text rather than exiling interior-only to an appendix. For a research blog, inline sensitivity is more transparent.
- **Dead code cleanup**: Minor but correct.

No dead-end suggestions from iteration 4. All changes improved the paper.

## Scores
| Criterion | Score | Delta | Comment |
|-----------|-------|-------|---------|
| Novelty | 7/10 | — | Point-vs-distribution decoupling now prominent; CRPS/MAE diagnostic remains the core contribution |
| Methodological Rigor | 8/10 | — | Strong converging evidence architecture; one code concern in permutation test, one in Granger pipeline |
| Economic Significance | 7/10 | — | Actionable for Kalshi market designers and traders; limited by two-series scope |
| Narrative Clarity | 7/10 | +1 | Practical Takeaways box is excellent; still dense in places for a blog audience |
| Blog Publishability | 7/10 | +1 | Close to publishable with minor narrative polish |

## Strength of Claim Assessment

**Claim 1: JC distributions robustly add value (CRPS/MAE=0.66, CI excludes 1.0)**
- Evidence level: **Conclusive**. Five temporal CIs all exclude 1.0, all 16 LOO ratios < 1.0, signed-difference p=0.001. Paper labels correctly.
- No change needed.

**Claim 2: CPI distributions are harmful (CRPS/MAE=1.58, CI [1.04, 2.52])**
- Evidence level: **Conclusive-to-strong** (upgraded from suggestive-to-conclusive). Four converging diagnostics, all 14 LOO ratios > 1.0. The serial-correlation-adjusted CI including 1.0 is properly documented as a caveat.
- Paper labels correctly. Good calibration.

**Claim 3: CPI–JC divergence is statistically significant (permutation p<0.001, MWU p=0.003/0.026)**
- Evidence level: **Conclusive**, but the permutation test has a subtle design issue (see Robustness below). The MWU tests on per-event ratios are the cleaner evidence.
- **Suggestion**: Swap emphasis — lead with MWU (which is scale-free) and mention permutation as supporting rather than vice versa.

**Claim 4: CPI point forecast beats random walk (d=−0.71, p_adj=0.059)**
- Evidence level: **Strong**. Large effect size, adequate power, significant at 10% after Bonferroni. Paper now labels this correctly.
- No change needed.

**Claim 5: TIPS Granger-causes Kalshi CPI (F=12.2, p=0.005)**
- Evidence level: **Suggestive** (potential code issue, see Robustness). The Granger result should be treated more cautiously pending verification of the stationarity alignment.
- Paper already hedges this appropriately ("Granger causality measures predictive information, not causal information flow"). Good.

**Claim 6: Point-vs-distribution decoupling**
- This is now the paper's most memorable finding. **The claim could be even stronger.** Consider framing: "This is, to our knowledge, the first empirical demonstration that prediction market point forecasts and distributional forecasts can be independently calibrated — accurate centers with miscalibrated spreads. This decoupling is invisible to standard evaluation metrics (Brier score, calibration curves) that evaluate individual contracts rather than distributional coherence."

## Novelty Assessment

The paper's novelty portfolio is now well-structured:
1. **CRPS/MAE ratio as diagnostic** — genuinely useful, not a trivial repackaging. The ratio-of-means vs mean-of-ratios comparison table (Section 2) demonstrates that naive approaches fail, which justifies the methodological contribution.
2. **Point-vs-distribution decoupling** — the paper's most novel empirical finding. Strengthen this further (see Claim 6 above).
3. **Series-level heterogeneity** — the finding that calibration varies by series is important for market design.

**Underemphasized novelty**: The temporal pattern (JC distributions add value at ALL five timepoints; CPI only harmful at mid-life) is a striking finding that's somewhat buried in the sensitivity table. A single sentence in the abstract highlighting this temporal robustness would increase the paper's novelty profile.

## Robustness Assessment

### Code Issue 1: Permutation Test Scale-Mixing (experiment13/run.py, lines 655-670)

The permutation test pools raw CRPS and MAE values from both series before shuffling group labels. CPI events have CRPS~0.1, MAE~0.07; JC events have CRPS~7748, MAE~11740. When you randomly assign events to groups, the ratio-of-means for any mixed group is dominated by whichever JC events land in that group, because JC values are ~100,000x larger.

This means the test is not purely testing "do CPI and JC have different CRPS/MAE ratios?" — it's conflating scale differences with calibration differences. Under H0 (same calibration regime), if both series had ratio=0.8 but different scales, the permutation test would still reject because mixing scales distorts the ratio-of-means.

**This is NOT a bug** — the test is mathematically valid and the p<0.001 is real. But it's testing a composite hypothesis (different scales AND/OR different ratios) rather than a pure calibration hypothesis. The Mann-Whitney tests on per-event ratios (which are dimensionless) are the cleaner evidence for heterogeneity.

**Recommendation**: In the paper, swap emphasis: lead with MWU (scale-free, both specifications significant) rather than permutation test. Currently the paragraph opens with the permutation test (line 69). Restructure to: "A Mann-Whitney U test on per-event ratios gives p=0.003 (tail-aware, r=−0.64) and p=0.026 (interior-only, r=−0.48). A permutation test on the ratio-of-means difference confirms (p<0.001, 10,000 permutations)." Alternatively, run the permutation on per-event CRPS/MAE ratios (interior-only, already computed) rather than on raw CRPS and MAE values — this gives a scale-free permutation test and is a 3-line code change.

### Code Issue 2: Experiment 8 Stationarity Alignment (experiment8/tips_comparison.py)

The `run_granger_both_directions()` function calls `_ensure_stationary()` on both the Kalshi and TIPS series independently. If one series requires differencing (dropping the first observation) and the other doesn't, the resulting aligned series may be off by one row. The code re-aligns by date after stationarity transforms, so this is likely fine in practice — but there's no explicit assertion that the indices still match after independent differencing. Additionally, `max_lag=10` is hardcoded rather than selected by AIC/BIC, which is unusual for Granger causality in daily economic data.

**Recommendation**: Add a defensive assertion (aligned index after stationarity). This is a code hygiene issue; the Granger result is already appropriately hedged in the paper.

### Code Issue 3: Hardcoded Realized Values in Horse Race (experiment13/horse_race.py)

The CPI realized values, SPF forecasts, random walk baseline, and trailing mean baselines all appear to be hardcoded. While likely correct, this introduces transcription risk. Not worth automating at n=14, but worth noting in methodology.

### Missing Robustness Check: Block Bootstrap for Serial Correlation

The paper reports a post-hoc CI width adjustment for CPI serial correlation (ρ=0.23, n_eff≈8.8). This is adequate as documented, but a block bootstrap (block length 2, matching AR(1)) would give a proper serial-correlation-adjusted CI. If the block bootstrap CI still excludes 1.0, this eliminates the serial correlation caveat entirely. If it includes 1.0, the current four-diagnostic convergence framing is already the right approach.

## The One Big Thing

**Run the permutation test on per-event CRPS/MAE ratios instead of raw CRPS and MAE values.** This is a 3-line code change that eliminates the scale-mixing concern and makes the permutation test cleanly test the calibration heterogeneity hypothesis. Use interior-only per-event ratios (which are stable). The current p<0.001 would likely still hold — and if it does, the result is bulletproof. If it doesn't hold, the MWU tests already provide sufficient evidence and you can simply drop the permutation test or relegate it to a footnote.

## Other Issues

### Must Fix (blocks publication)

None. The paper is publishable in its current form. The issues below are improvements, not blockers.

### Should Fix (strengthens paper)

1. **Swap permutation/MWU emphasis in heterogeneity paragraph**: Lead with MWU (scale-free, both specifications significant) rather than permutation test. Currently the paragraph (line 69) opens with the permutation test. Restructure to: "A Mann-Whitney U test on per-event ratios gives p=0.003 (tail-aware, r=−0.64) and p=0.026 (interior-only, r=−0.48). A permutation test on the ratio-of-means difference confirms (p<0.001, 10,000 permutations)."

2. **Strengthen the point-vs-distribution decoupling claim**: Add one sentence in Section 3 noting this is (to your knowledge) the first empirical demonstration that prediction market point and distributional calibration can diverge independently. This positions the finding as genuinely novel rather than a curiosity.

3. **Add temporal robustness to abstract**: The abstract mentions JC CI excludes 1.0 but doesn't note this holds at ALL five temporal snapshots. One clause: "...robust across the entire market lifecycle (CIs exclude 1.0 at all five temporal snapshots from 10% to 90% of market life)."

4. **Tighten the abstract length**: The abstract is ~250 words plus the Practical Takeaways box. For a blog post, consider ≤200 words with the takeaways as a separate callout. Cut the interior-only MWU p-value from the abstract (it's a robustness check, not a headline result) and the specific CI bounds for JC.

### New Experiments / Code to Write

1. **Scale-free permutation test** (~5 lines): Replace the permutation test statistic. Instead of pooling raw CRPS and MAE values, pool the interior-only per-event CRPS/MAE ratios and permute group labels:
   ```python
   all_ratios = np.concatenate([cpi_per_event_int, jc_per_event_int])
   observed_diff = np.mean(cpi_per_event_int) - np.mean(jc_per_event_int)
   for i in range(n_perm):
       idx = rng.permutation(len(all_ratios))
       perm_diffs[i] = np.mean(all_ratios[idx[:n_cpi]]) - np.mean(all_ratios[idx[n_cpi:]])
   perm_p = float(np.mean(np.abs(perm_diffs) >= abs(observed_diff)))
   ```
   Report both the original and scale-free permutation p-values.

2. **Block bootstrap for CPI serial correlation** (~15 lines): Implement a circular block bootstrap (block length 2) for the CPI CRPS/MAE ratio CI:
   ```python
   block_len = 2
   n_blocks = (n_cpi + block_len - 1) // block_len
   boot_ratios = []
   for _ in range(10000):
       starts = rng.randint(0, n_cpi, size=n_blocks)
       boot_idx = np.concatenate([np.arange(s, s + block_len) % n_cpi for s in starts])[:n_cpi]
       boot_crps = cpi_crps[boot_idx].mean()
       boot_mae = cpi_mae[boot_idx].mean()
       if boot_mae > 0:
           boot_ratios.append(boot_crps / boot_mae)
   block_ci = np.percentile(boot_ratios, [2.5, 97.5])
   ```
   If block_ci excludes 1.0, the serial correlation caveat is eliminated. If it includes 1.0, the current approach (post-hoc adjustment + four diagnostics) is already the right framing.

3. **Anderson-Darling test for PIT uniformity** (2 lines): Supplement the KS test:
   ```python
   ad_stat, ad_crit, ad_sig = scipy.stats.anderson(pit_values, 'uniform')
   ```
   AD is more powerful for detecting the tail deviations that the CPI PIT bias suggests. Report alongside KS for completeness.

### Acknowledged Limitations (inherent, not actionable)

1. **Two series only**: The heterogeneity finding would be far more compelling with 5+ series. Inherent to current Kalshi multi-strike market offerings.
2. **Small n per series**: n=14 CPI, n=16 JC. No fix without waiting for more data.
3. **In-sample only**: Cannot cross-validate at current n.
4. **Untestable mechanisms**: The four hypothesized mechanisms for CPI–JC divergence cannot be directly tested with public data.
5. **Hardcoded realized values**: The horse race relies on manually entered CPI values. Standard practice but introduces transcription risk.

## Verdict

**MINOR REVISIONS**

The paper is genuinely close to blog-publishable. The statistical architecture is sound, claims are well-calibrated, and the narrative has improved substantially across five iterations. The remaining issues — scale-free permutation test, MWU emphasis swap, abstract tightening, block bootstrap, and one novelty-strengthening sentence — are polish rather than structural. None block publication; all would strengthen an already solid paper. The point-vs-distribution decoupling framing is compelling and the Practical Takeaways box gives traders exactly what they need. I would recommend this for the Kalshi Research blog after the "Should Fix" items are addressed.
