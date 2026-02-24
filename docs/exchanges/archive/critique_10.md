# Critique — Iteration 10

STATUS: CONTINUE

## Overall Assessment

The paper is methodologically mature — the iteration 9 improvements (per-event overconcentration analysis, attribution fix, bootstrap CIs, ecological amplification discussion) were all well-executed and close every major statistical gap. The 11-series, 248-event dataset is adequate. The binding constraint is now **presentation**: the paper reads like a 500+ line iterative research log (50 corrections, 6 appendices, extensive inline caveats) rather than a clean narrative suitable for the Kalshi Research blog. A blog editor would send this back for restructuring before even evaluating the content.

## Data Sufficiency Audit

**No change from iteration 9. Data sufficiency is not the binding constraint (8/10).**

- 11 series, 248 events covers the vast majority of Kalshi's multi-strike economic markets.
- The Kalshi API (`client.py`) supports fetching any series via `get_all_pages("/markets", params={"series_ticker": "...", "status": "settled"})`. The researcher expanded from 4 → 7 → 11 series across iterations. Remaining unfetched series (KXRETAIL, KXACPI) were deprioritized in iteration 9 — not re-raising.
- Small-n issues (FED n=4, ISM n=7) are genuinely structural.
- **No new data fetching recommended.** The marginal return on a 12th or 13th series is low compared to the return on restructuring for readability.

## Reflection on Prior Feedback

### Iteration 9 — all points addressed well:
1. ✅ "We introduce" → "We apply" (attribution fix)
2. ✅ Per-event overconcentration-performance analysis (n=232, ρ=−0.19, p=0.004)
3. ✅ Bootstrap CI on ρ=−0.68 ([−0.96, −0.10])
4. ✅ CI non-exclusion defense sentence
5. ✅ n=11 caveat added throughout

### What I'm dropping:
- All iteration 9 statistical items — fully addressed.
- Data sufficiency expansion — settled at 8/10.
- Code hardcoding of series-level values in `iteration9_analyses.py` (lines 554–556) — noted below as a reproducibility concern but not a must-fix since values are frozen analysis artifacts.

### Researcher pushbacks:
- None in iteration 9. All points accepted.

## Scores

| Criterion | Score | Delta | Comment |
|-----------|-------|-------|---------|
| Data Sufficiency | 8/10 | — | Unchanged. 11 series, 248 events adequate. |
| Novelty | 9/10 | +0.5 | Per-event ecological amplification finding is genuinely novel. Attribution properly corrected. |
| Methodological Rigor | 9/10 | +0.5 | Per-event analysis, bootstrap CIs, ecological amplification discussion close all statistical gaps. |
| Economic Significance | 8.5/10 | — | Monitoring protocol validated. Market design implications concrete. |
| Blog Publishability | 6.5/10 | −2 | **This is the binding constraint.** Paper is too long and structured like a research diary. See "The One Big Thing." |

## Strength of Claim Assessment

### Claim 1: "9 of 11 series: distributions add value"
**CONCLUSIVE. Correctly labeled.** Sign test p=0.004, LOO unanimity 8/9. No change needed.

### Claim 2: "Universal overconcentration"
**CONCLUSIVE. Properly formalized.** Sign test p=0.0005, pooled CI excludes 0.289. No change needed.

### Claim 3: "Overconcentration-performance paradox"
**SUGGESTIVE but now properly qualified.** Series-level ρ=−0.68 with bootstrap CI [−0.96, −0.10] and per-event ρ=−0.19 (p=0.004). The ecological amplification discussion is excellent and honest. **No change needed to the statistical content** — but this section is too long for a blog post. Consider moving the within-series breakdown to an appendix.

### Claim 4: "Point-distribution decoupling"
**SUGGESTIVE. Correctly labeled.** CPI + KXFRM counterexample is compelling. No change needed.

### Claim 5: "Monitoring protocol"
**CONCLUSIVE for well-calibrated series (6/8 zero alerts).** KXFRM alert period analysis is convincing. No change needed.

### Claim 6: "Simple-vs-complex hypothesis failure"
**CONCLUSIVE (that it failed).** Pre-registered OOS 2/4. However, this takes ~20% of the paper's word count and the takeaway is "this didn't work." For a blog post, compress to 2-3 sentences.

## Novelty Assessment

**What's genuinely new and should be foregrounded:**
1. CRPS/MAE applied to prediction markets across 11 economic series — first systematic evaluation
2. "9 of 11 distributions add value" — the headline positive finding for Kalshi
3. Universal overconcentration with formal tests — unprecedented scale
4. Ecological amplification of overconcentration-performance relationship — novel statistical finding
5. Point-distribution decoupling — first demonstration in prediction markets
6. Monitoring protocol with validated backtest — directly actionable

**What's currently overweight in the paper but low novelty:**
1. Simple-vs-complex hypothesis and its failure — methodologically honest but not the paper's contribution. ~20% of word count for a negative result.
2. 50-item corrections log — essential for reproducibility but belongs in a supplement.
3. Per-series robustness subsections (GDP, JC, CPI, KXFRM, KXADP, Core PCE, FED) — ~500 words of prose that could be a single table.

## Robustness Assessment

### Code review (new findings this iteration)

Thorough review of `experiment13/run.py`, `scripts/expanded_crps_analysis.py`, `scripts/iteration9_analyses.py`, and `kalshi/market_data.py` confirms:

1. **All statistical tests correctly implemented.** Sign test, bootstrap, Wilcoxon, rank-biserial, Bonferroni, BCa with percentile fallback — all sound.
2. **CRPS piecewise-linear integration correct.** Ratio-of-means (not mean-of-ratios) used appropriately.
3. **PIT-to-event matching by index** (`iteration9_analyses.py`, lines 377–395): merge relies on implicit ordering rather than explicit event_ticker joins. A sort mismatch would silently misalign data. **MEDIUM risk.** Worth adding an assertion.
4. **Hardcoded series-level arrays** (`iteration9_analyses.py`, lines 554–556): The 11 std(PIT) and CRPS/MAE values are frozen rather than dynamically loaded. **LOW risk** — these are frozen artifacts — but worth a comment.
5. **`point_crps` naming** in `experiment13/run.py`: Semantically MAE (absolute deviation of implied mean from realized). Technically correct (CRPS of a point forecast = MAE) but could confuse readers. Minor.

### Hostile reviewer attacks (remaining after iteration 9 fixes)

1. **"The paper is 500+ lines with 50 corrections — is this a paper or a lab notebook?"** This is the most likely blog editor pushback. The content is solid but buried under process documentation. **This is the paper's biggest remaining weakness.**

2. **"Multiple testing across 11 series without family-wise correction on the main claim."** The paper claims 9/11 have CRPS/MAE < 1.0 but no Bonferroni or Holm correction is applied to this claim. **Defense:** The per-event sign test (147/248, p=0.004) is the primary test and doesn't require per-series correction. Individual series ratios are descriptive. **Recommendation:** Add one sentence making this framing explicit.

3. **"You can't use CRPS/MAE < 1.0 as a threshold without a null distribution."** Under what null is CRPS/MAE exactly 1.0? Answer: under the null that the market distribution is a step function at the implied mean (i.e., point forecast only), CRPS = MAE exactly. This is the correct and implicit null — make it explicit in one sentence in the methodology.

## The One Big Thing

**Restructure the paper for blog publishability.**

The statistical content is publication-ready. The presentation is not. The paper currently reads like an iterative research diary. A Kalshi blog reader wants:

1. **The headline** (1 sentence): Prediction market distributions add value for 9 of 11 economic series.
2. **The method** (3 paragraphs max): CRPS/MAE ratio, what it is, how it's computed.
3. **The results table**: The executive summary table is excellent — lead with it.
4. **The key findings** (2-3 paragraphs each): Universal overconcentration, point-distribution decoupling, two series where distributions hurt.
5. **The actionable takeaway** (1-2 paragraphs): Monitoring protocol.
6. **Technical supplement**: Everything else (corrections log, per-series robustness details, simple-vs-complex forensics, ecological amplification breakdown, full PIT tables).

Concrete restructuring recommendations:

- **Compress the abstract from ~350 words to ~150 words.** Lead with "9 of 11 add value." Move simple-vs-complex failure, ecological amplification details, and monitoring validation to the body.
- **Compress Section 2.3 (Simple-vs-Complex) from ~500 words to ~100 words.** "We initially hypothesized a simple-vs-complex dichotomy. Pre-registered OOS predictions achieved 50% accuracy — no better than chance. See Appendix B for the full analysis." The methodological honesty is preserved; the forensic trail moves to an appendix.
- **Convert per-series robustness (Section 4, ~500 words) into a summary table.** Columns: Series | LOO range | CI | Key note. Reserve prose for the 2-3 series with interesting stories (CPI structural break, KXFRM alert period).
- **Move corrections log to a separate supplement.** The 50-item log is valuable for reproducibility but should not be in the main text of a blog post.
- **Target: ~2,500 words main text + technical supplement.** Currently the paper is 5,000+ words.

This is not about cutting content — it's about restructuring into a clean narrative + detailed technical appendix.

## Other Issues

### Must Fix (blocks blog publication)

1. **Paper length and structure.** See "The One Big Thing." The paper has ~2,500 words of core findings buried in ~5,000+ words of process documentation. Restructure into (a) a streamlined main text (~2,500 words) and (b) a technical supplement for interested readers.

2. **Abstract length.** ~350 words → compress to ~150 words. Focus on: method, headline finding (9/11 add value), the two exceptions, universal overconcentration, monitoring protocol. Move everything else to the body.

3. **Make the CRPS/MAE=1.0 null explicit.** Add one sentence in Section 2: "Under the null that the market's distributional information adds nothing beyond the point forecast — i.e., the CDF is a step function at the implied mean — CRPS equals MAE exactly (ratio = 1.0)." This is implicit but a hostile reviewer could challenge the threshold.

### Should Fix (strengthens paper)

1. **Add a one-sentence multiple-testing defense for the 9/11 claim.** "Individual series ratios are descriptive; the paper's central statistical test is the per-event sign test (147/248 < 1.0, p=0.004), which does not require per-series correction."

2. **Compress per-series robustness into a table.** GDP, JC, CPI, KXFRM, KXADP, Core PCE, FED subsections → single table with columns: Series | LOO range | CI | Key note. Prose reserved for CPI structural break and KXFRM alert period only.

3. **Add an event_ticker assertion in `iteration9_analyses.py`.** The PIT-to-event merge at lines 377–395 relies on implicit ordering. Add `assert all(pit_ticker == event_ticker for ...)` to catch silent misalignment. Reproducibility improvement, not a paper change.

### New Experiments / Code to Write

1. **No new experiments needed.** The statistical content is complete. All effort should go to presentation restructuring.

2. **Optional (low priority): CRPS/MAE null simulation (~20 lines).** Generate synthetic markets where CDF = step function at implied mean. Verify CRPS/MAE = 1.0 exactly. Bulletproofs the threshold interpretation. Not essential — the mathematical argument is trivial — but a nice robustness addition.

### Genuinely Unfixable Limitations

1. **FED n=4.** FOMC meets ~8x/year; only 4 settled multi-strike events exist.
2. **CPI temporal split underpowered (p=0.18).** Only 33 events; ~95 needed for 80% power.
3. **No order-book depth data.** Cannot distinguish overconcentration mechanisms.
4. **SPF monthly CPI proxy.** No public monthly CPI point forecast; annual/12 is best available.
5. **Per-event |PIT−0.5| is a proxy, not direct overconcentration.** Conceptual distinction, properly discussed.

## Verdict

**MINOR REVISIONS**

The statistical methodology and content are publication-ready. No new data or experiments are needed. The paper requires a structural reorganization: compress the main narrative to ~2,500 words, move process documentation to a technical supplement, compress the abstract, and add two defensive sentences (CRPS/MAE null, multiple-testing framing). With these changes, the paper is ready for the Kalshi Research blog.
