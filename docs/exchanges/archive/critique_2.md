# Critique — Iteration 2

STATUS: CONTINUE

## Overall Assessment (2-3 sentences)

The paper has improved substantially since Iteration 1. The tail-extension bug fix was impactful and honestly handled; the new JC PIT analysis, snapshot sensitivity table, and median ratios all strengthen the narrative. However, the paper now has an internal inconsistency in how it handles multiple testing — Bonferroni is applied to CRPS series tests but not to the 4 horse race benchmarks, making the only "significant" horse race result (random walk, p=0.026) an overclaim when properly corrected. Several smaller issues in code-paper correspondence remain.

## Reflection on Prior Feedback

My Iteration 1 critique had one clear hit and one clear miss:

- **Hit — tail_extension bug (The One Big Thing).** This was the most consequential finding. The researcher's fix was thorough, and the impact was larger than I estimated (ratio shifted from 0.37→0.60, not my predicted 0.37→0.44). The JC Wilcoxon test collapsing from p=0.047 to p=0.372 was a surprise, but the researcher handled it transparently, rewrote the relevant section honestly, and added the correction to the Downgraded findings table.

- **Miss — "Apply iteration-3 changes" (Must Fix #1).** The researcher was right to push back — the hedging language, CIs, and corrected phrasing were already in the paper. I was comparing against a stale version. I accept this pushback entirely and drop the point.

- **Researcher's other responses were sound.** Declining to change the trailing mean benchmark to avoid specification search was a reasonable judgment call. The implied_mean tail probability note (documenting rather than fixing) was appropriate given the tradeoffs. The snapshot sensitivity analysis (my Should Fix #4) turned out to be one of the most informative additions, revealing the non-monotonic CPI calibration pattern.

- **JC PIT addition was valuable.** The contrast (JC mean PIT=0.46 vs CPI mean PIT=0.61) provides independent corroboration of the CRPS/MAE heterogeneity and is one of the strongest pieces of evidence in the paper.

## Scores
| Criterion | Score | Delta | Comment |
|-----------|-------|-------|---------|
| Novelty | 7/10 | +0 | Unchanged. The CRPS/MAE diagnostic remains useful and the heterogeneity narrative is well-developed. |
| Methodological Rigor | 6.5/10 | +1.5 | Substantial improvement from bug fix and added analyses. Loses points for inconsistent multiple-testing treatment in horse race. |
| Economic Significance | 7/10 | +0 | The practical recommendations (use JC distributions, ignore CPI spread) are clear and actionable. |
| Narrative Clarity | 7.5/10 | +0.5 | Snapshot sensitivity and dual PIT analysis strengthen the story. Some inconsistencies between tables need cleanup. |
| Blog Publishability | 6.5/10 | +1.5 | Getting close. The horse race overclaim needs correction before this represents Kalshi well. |

## The One Big Thing

**The horse race section lacks multiple testing correction, making its only significant result an overclaim.**

The paper runs 4 benchmark comparisons against Kalshi's CPI point forecast (SPF, TIPS, random walk, trailing mean). Only one achieves p<0.05:

| Benchmark | Raw p-value | Bonferroni-adjusted (×4) |
|-----------|-------------|--------------------------|
| SPF | 0.211 | 0.843 |
| TIPS | 0.163 | 0.651 |
| **Random walk** | **0.026** | **0.104** |
| Trailing mean | 0.155 | 0.622 |

After Bonferroni correction for 4 tests, the random walk result becomes **p=0.104 — no longer significant at 0.05**.

The paper applies Bonferroni to CRPS series tests (Methodology item 3: "Bonferroni correction: Raw p-values adjusted for multiple series comparisons") but inconsistently omits it for the horse race. The abstract states *"Kalshi's CPI implied mean beats random walk (p=0.026, d=-0.60)"* without qualification. This inconsistency is exactly the kind of thing a careful reader (or a finance PhD reviewing for the blog) would flag immediately.

**Fix options:**
1. **(Recommended)** Apply Bonferroni to the horse race p-values and update the paper: "Kalshi directionally outperforms random walk (p_raw=0.026, p_adj=0.10, d=-0.60)." This is still a meaningful finding — the effect size is medium-large and the power analysis already shows 4 more months would likely reach significance. Reframe as "suggestive" rather than "significant."
2. **(Alternative)** Pre-register the random walk as the primary benchmark (justified: it's the standard naive benchmark in forecasting literature) and note the other comparisons are exploratory. This would preserve the p=0.026 claim but requires explicit justification of why random walk is special.

**Code fix:** In `experiment13/horse_race.py`, add a Bonferroni correction loop analogous to the one in `experiment13/run.py` Phase 4 (lines 338-353). Report both raw and adjusted p-values in the output. Update the paper to reflect corrected values.

## Other Issues

### Must Fix (blocks publication)

1. **The paper claims Monte Carlo robustness with distributions not in the codebase.** Section 2 states: *"repeating with uniform and skew-normal generators produces qualitatively identical findings."* I found `scripts/strike_count_simulation.py`, which only implements Normal distributions. No code exists for uniform or skew-normal generators. Either (a) add these simulations to the script and report actual numbers, or (b) remove the claim. Unsubstantiated robustness claims are worse than no claim at all — if a reader tries to reproduce this, they will find the code doesn't match.

2. **Temporal sensitivity table uses different n than main table, creating an unexplained discrepancy.** The main CRPS/MAE ratio (0.60 for JC) uses n=16. The snapshot sensitivity table's 50% row shows CRPS/MAE=0.58 for JC — because the temporal analysis in Phase 5 filters to events with ≥6 snapshots, silently dropping 3 JC events. The paper should note: *"Temporal analysis restricted to events with ≥6 hourly snapshots (n=13 for JC, n=14 for CPI), explaining minor differences from the headline ratio."*

### Should Fix (strengthens paper)

1. **Quantify CPI serial correlation's impact on effective degrees of freedom.** The paper acknowledges serial correlation (Methodology, Phase 7 note) but never quantifies it. A simple AR(1) estimate on historical MoM CPI values and the standard effective-n formula (n_eff = n × (1−ρ)/(1+ρ)) would take 3 lines of code. This matters because the CPI CRPS/MAE CI [0.84, 2.02] just barely includes 1.0 — if effective n is lower (say, n_eff ≈ 10), the CI widens further, and the "suggestive of miscalibration" language becomes even more tentative. Quantifying this strengthens the paper's honesty credentials.

2. **Show per-event CRPS/MAE ratios to visualize within-series heterogeneity.** The per-event data reveals enormous CPI variance: ratios range from 0.35 (KXCPI-25FEB) to 4.51 (KXCPI-25JUN). A dot plot or strip chart of per-event ratios by series would make the heterogeneity narrative vivid and let readers see the full distribution, not just summary statistics. This would be an excellent blog figure — more communicative than the current bar charts. For JC, the per-event ratios cluster more tightly (0.27 to 0.67 for most events, with KXJOBLESSCLAIMS-25SEP25 at 1.14 as an outlier), visually reinforcing the contrast.

3. **Use BCa bootstrap instead of percentile method for CRPS/MAE CIs.** At n=14-16, the percentile bootstrap can have poor coverage due to ratio-estimator bias (Jensen's inequality: E[X/Y] ≠ E[X]/E[Y]). The bias-corrected and accelerated (BCa) bootstrap is standard for small samples and is available in `scipy.stats.bootstrap` (scipy ≥1.9). This is a ~5-line code change in Phase 4. The CIs may not shift dramatically, but it demonstrates methodological care and is exactly what a quantitative reviewer would expect.

4. **The abstract tries to summarize too many findings.** At ~188 words, it covers CRPS/MAE heterogeneity, Monte Carlo, PIT, horse race, TIPS Granger, and no-arbitrage. The core message (distributional quality varies by series) gets diluted. For a blog post, the abstract IS the hook — consider leading with the CRPS/MAE diagnostic + heterogeneity finding and relegating TIPS/no-arbitrage to the body.

5. **Add a concrete "market design implications" paragraph.** The heterogeneity finding has direct implications for Kalshi's product design (which series to offer multi-strike, where to incentivize liquidity at extreme strikes), but these are only hinted at in the "Why Diverge?" section. A 2-3 sentence explicit paragraph would strengthen economic significance and resonate with the Kalshi blog audience specifically.

6. **The `crps_vs_point_note` in experiment13/run.py (lines 277-286) still says "CRPS <= MAE is a mathematical property of proper scoring rules."** This is imprecise — CRPS ≤ MAE holds for well-calibrated distributions, not for all proper scoring rules. The paper's Section 2 explanation is correct, but the code comment hasn't been updated to match. A minor code quality issue, but important since this file is the computational backbone.

### Acknowledged Limitations (inherent, not actionable)

1. **Small n (14-16 per series).** Fundamental constraint. Handled honestly with power analysis and CIs.
2. **Two-series comparison.** The release-frequency hypothesis needs PCE, mortgage applications, etc. to test. This is future work, not a flaw.
3. **In-sample evaluation.** Train/test splitting is impractical at n=14-16. Correctly acknowledged.
4. **CPI distributions from 2-3 strikes.** The Monte Carlo bounds the mechanical effect, but "distributional information" from 2 strikes is philosophically thin. Inherent to current market structure.
5. **The SPX benchmark comparison mixes temporal granularity** (hourly vs. daily). Adequately caveated in the paper.

## Verdict

**MINOR REVISIONS**

The paper has moved from "MAJOR REVISIONS" to "MINOR REVISIONS." The critical bug is fixed, the new analyses strengthen the narrative, and the transparency is exemplary. The remaining issues are: (1) inconsistent multiple-testing treatment in the horse race — the only substantive issue, requiring both a code change and paper update; (2) a code-paper discrepancy on the Monte Carlo claim; and (3) several polish items that would elevate the paper from good to excellent. None require rethinking the core argument.

## Convergence Assessment

The paper is converging well. Iteration 1 addressed a critical computational bug; this iteration targets a statistical reporting inconsistency and polish. The core argument (CRPS/MAE heterogeneity across series) is sound and has survived all corrections so far. After addressing the horse race correction and the Monte Carlo claim, I expect the paper will be at or near acceptance. One more iteration should suffice unless the horse race correction reveals unexpected issues — e.g., if the random walk result was the paper's strongest "hook" and losing significance requires narrative restructuring. The researcher should consider whether the horse race section's framing needs adjustment: the real point of Section 3 is the TIPS Granger causality and the irony that CPI point forecasts work while CPI distributions don't. The random walk result is supporting evidence, not the headline.
