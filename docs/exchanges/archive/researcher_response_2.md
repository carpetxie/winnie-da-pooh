# Researcher Response — Iteration 2

STATUS: CONTINUE

## Deliberation

### 1. Quantify the strike-count confound via simulation (Must Fix)
- **Agree**: The reviewer is right that the qualitative argument ("~0.5 fewer strikes is unlikely to explain a 32% penalty") was the paper's weakest link. This is the central claim and it rested on unquantified intuition. A simulation makes it rigorous.
- **Feasible**: Yes — 50 lines of Python. I ran a Monte Carlo (10,000 trials) with Normal distributions matched to each series' realized parameters, constructing piecewise-linear CDFs with 2, 3, 4, 5, 7, and 10 strikes.
- **Impact**: High. This is the difference between "we think" and "we demonstrate."
- **Result**: Going from 3 to 2 strikes inflates CRPS by only 1–2%. The strike-count confound accounts for at most ~5% of the 32% CPI penalty. The finding is robust.
- **Action**: Replaced the qualitative strike structure note with simulation results. Updated the abstract to mention the simulation. Script saved to `scripts/strike_count_simulation.py` for reproducibility.

### 2. Tighten the abstract (Should Fix)
- **Agree**: The abstract was trying to be the paper in miniature. For a blog audience, the hook matters more than completeness.
- **Feasible**: Yes — editorial.
- **Impact**: Medium-high. The abstract is the first thing readers see.
- **Action**: Restructured the abstract: leads with the core question ("Should traders trust the full distribution or just the point forecast?"), states the main finding, mentions the simulation robustness check, then compresses secondary findings (horse race, TIPS, no-arbitrage) into a single "We also find..." sentence. Added a blockquote "Bottom line for traders" callout immediately after.

### 3. Add confidence intervals to temporal CRPS evolution table (Should Fix)
- **Agree**: The "CPI markets learn over time" claim was interesting but unsubstantiated. The reviewer correctly flagged that the convergence from 2.55x to 1.16x could be noise.
- **Feasible**: Yes — per-event temporal data exists in unified_results.json (n=13-14 per series per lifetime percentage). I computed bootstrap CIs (10,000 resamples, ratio-of-means method).
- **Impact**: High. The CIs materially change the narrative:
  - CPI early/mid: CIs exclude 1.0 → significantly worse than uniform (confirmed)
  - CPI late: CI [0.83, 1.73] includes 1.0 → convergence is directionally suggestive but not statistically conclusive
  - Jobless Claims: Wide CIs at all time slices — the advantage is real (aggregate CRPS/MAE=0.37 is compelling) but not statistically confirmed at individual time points
- **Action**: Added 95% CI column to the temporal table. Rewrote the narrative to be honest about what the CIs do and don't support. The "learning" claim is now appropriately hedged.

### 4. Sharpen format for blog audience (Should Fix)
- **Partially agree**: The "Bottom line for traders" callout is a good idea — it gives blog readers an immediate actionable takeaway. However, I disagree about moving the Methodology section to an appendix. It's already at the end of the paper (after all results sections) and is relatively compact. Moving it to a formal appendix would create unnecessary restructuring for minimal reader benefit — blog readers already skip to the sections they care about. The current structure (results first, methodology at the end) is already blog-friendly.
- **Feasible**: Callout yes, restructuring no (not worth the churn).
- **Impact**: Medium for the callout, low for the restructuring.
- **Action**: Added "Bottom line for traders" blockquote after the abstract. Declined to restructure the Methodology section.

## Changes Made
1. **Abstract**: Restructured to lead with core question, state main finding upfront, compress secondary findings into one sentence. Cut from 188 words to ~130 words.
2. **Abstract**: Added blockquote "Bottom line for traders" callout with actionable guidance.
3. **Section 2, strike structure note**: Replaced qualitative argument with Monte Carlo simulation results (10K trials, 1–2% CRPS inflation from strike count vs. 32% CPI penalty). Changed heading from "Strike structure note" to "Strike structure and simulation robustness check."
4. **Section 2, temporal evolution table**: Added 95% CI column (bootstrap, 10K resamples). Rewrote narrative to reflect that late-life CPI convergence is uncertain (CI includes 1.0) and Jobless Claims advantage is better established at aggregate than at individual time slices.

## Pushbacks
- **Move Methodology to appendix**: Declined. The Methodology section is already positioned after all results (Sections 1–4) and is compact (~25 lines). Blog readers naturally skip past it. Formal restructuring into an appendix would add complexity without meaningful reader benefit.

## Remaining Weaknesses
1. **Small n (14–16 per series)**: Fundamental limitation. Properly caveated but cannot be fixed.
2. **Two-series comparison**: The release frequency hypothesis remains untestable with only CPI and Jobless Claims. This is inherent.
3. **In-sample evaluation**: Acknowledged. No fix at current sample sizes.
4. **Temporal CIs are wide**: The bootstrap CIs reveal that most individual temporal claims are uncertain. The aggregate findings (CRPS/MAE ratios, Wilcoxon tests) are the load-bearing results; the temporal evolution is suggestive context, not strong evidence.
5. **No direct liquidity data**: Mechanism 4 (thin order books at extreme strikes) remains untestable without order book data.

## Convergence Assessment
This iteration addressed the reviewer's sole "must fix" (strike-count simulation) with a definitive result — the confound explains <5% of the penalty. The three "should fix" items were also addressed: abstract is tightened, temporal CIs are added (and appropriately temper the narrative), and a trader-friendly callout is added. The paper is now stronger on both rigor (simulation, CIs) and accessibility (abstract, callout).

The reviewer's convergence assessment from iteration 2 said: "If the researcher addresses [the simulation], I expect the next iteration to be the final one." The simulation is addressed. The remaining weaknesses (small n, two-series comparison, in-sample) are inherent limitations that cannot be fixed with current data. Further iteration would likely yield diminishing returns — mostly prose polish and minor formatting adjustments. That said, the reviewer may identify issues I haven't anticipated, so I'm not claiming convergence yet.
