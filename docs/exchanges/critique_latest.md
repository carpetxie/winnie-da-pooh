# Critique — Iteration 1

STATUS: ACCEPT

## Overall Assessment

This paper introduces the CRPS/MAE ratio as a per-series diagnostic for prediction market distributional value and delivers a clean, surprising result: Jobless Claims distributions add massive value (ratio=0.37) while CPI distributions are actively harmful (ratio=1.32). The methodology is unusually rigorous for applied prediction market research — Bonferroni corrections, effect sizes, power analysis, regime-appropriate benchmarks, and an exemplary transparency appendix documenting invalidated findings. This is ready for the Kalshi Research blog.

## Scores
| Criterion | Score | Delta | Comment |
|-----------|-------|-------|---------|
| Novelty | 7/10 | — | The CRPS/MAE ratio itself is a straightforward construction, but the applied insight — that the *same platform's* distributions are excellent for one series and harmful for another — is genuinely novel. No prior prediction market literature has documented this within-platform heterogeneity. |
| Methodological Rigor | 8/10 | — | Strong. The COVID-contamination catch (deflating the Jobless Claims advantage from 7.3x to 1.8x), Bonferroni correction that honestly renders the headline result marginal (p_adj=0.093), power analysis, and regime-appropriate benchmarks all demonstrate serious self-correction. The downgraded/invalidated findings appendix is rare and commendable. |
| Economic Significance | 7/10 | — | Actionable for both Kalshi (market design: allocate liquidity incentives to series where distributions work) and traders (use Jobless Claims distributions, ignore CPI distributional spread). The testable predictions about release frequency are a concrete research agenda. |
| Narrative Clarity | 7/10 | — | Well-structured: build CDFs → score them → find heterogeneity → hypothesize mechanisms → contextualize. Section 4 (maturity/favorite-longshot) feels somewhat disconnected from the CRPS story. The abstract is dense but informative. |
| Blog Publishability | 8/10 | — | Would enhance Kalshi's credibility. Publishing "our CPI distributions are harmful" and "TIPS leads us, not vice versa" signals intellectual seriousness. The methodological rigor would impress sophisticated readers while the core finding is accessible to traders. |

## Seed Question Responses

**1. Is the CRPS/MAE ratio framing genuinely useful, or trivial repackaging?**

Genuinely useful. CRPS/MAE is mathematically simple — CRPS ≤ MAE for any well-calibrated distribution, so ratio > 1 signals the distribution is actively destroying value vs. the point forecast. But the *application* as a per-series diagnostic is the contribution. An analyst looking only at aggregate CRPS would miss the dramatic divergence between series. The ratio gives market designers a concrete, interpretable metric: "should we offer distributional contracts for this event type?"

**2. Does the heterogeneity finding have practical implications for Kalshi's market design?**

Yes, concretely. If weekly releases produce well-calibrated distributions while monthly composites don't, Kalshi can: (a) prioritize multi-strike offerings for weekly events, (b) adjust strike spacing based on demonstrated calibration quality, (c) use CRPS/MAE as an ongoing quality metric for new event types, and (d) test the frequency hypothesis as they expand to new contracts. The testable prediction framework (Section 2's four mechanisms) gives Kalshi a principled R&D agenda.

**3. Are there claims that overreach the evidence?**

The paper is disciplined. Two mild concerns:
- The SPX comparison (2.8% vs 2.7%) juxtaposes hourly prediction market snapshots with daily equity option measurements. The text acknowledges the difference but the table invites direct comparison. Adding "(hourly)" and "(daily)" labels in the table itself would help.
- Mechanism 3 (trader composition) is essentially unfalsifiable with public data, unlike mechanisms 1, 2, and 4 which have testable predictions. It should be flagged as more speculative.

**4. What's missing that would make this substantially stronger?**

The single biggest gap is **out-of-sample validation**. All CRPS/MAE ratios and Wilcoxon tests are computed on the full Oct 2024 – Feb 2026 dataset. With n=16 (Jobless Claims) and n=14 (CPI), splitting into train/test is impractical, but the limitation should be stated explicitly. A sentence in the Methodology section noting "all results are in-sample; rolling-window validation is a priority as more data accumulates" would preempt the most obvious critique.

A secondary gap: the paper doesn't discuss whether the CRPS/MAE > 1 for CPI is driven by tail mispricing (extreme strikes) or center mispricing. This decomposition would sharpen the mechanism story — if it's tail-driven, mechanism 4 (liquidity at extreme strikes) gains support.

**5. Would this enhance or damage Kalshi's research credibility?**

Strongly enhance. Self-critical empirical work builds credibility with sophisticated audiences. The paper's willingness to report negative findings (CPI distributions harmful, TIPS leads Kalshi, many prior results invalidated) is exactly what a research-oriented blog should publish. This is the kind of paper that makes traders take future Kalshi research seriously.

## The One Big Thing

**Add an explicit in-sample caveat.** The paper is honest about sample sizes and power but never directly states that results are computed on the full available dataset without hold-out validation. One sentence in the Methodology section would preempt the sharpest criticism from quantitative readers: "All scoring uses the full available sample; rolling-window out-of-sample validation is infeasible at current n but is a priority as data accumulates."

This is the only substantive improvement remaining. It does not block publication.

## Other Issues

### Must Fix (blocks publication)
- None. The paper is in publishable condition.

### Should Fix (strengthens paper)

1. **SPX comparison labels**: Add "(hourly)" and "(daily)" parentheticals directly in the no-arbitrage table to prevent casual conflation of measurement frequencies.

2. **Section 4 bridge sentence**: The maturity/favorite-longshot analysis feels orphaned. A single sentence connecting it to the CRPS narrative (e.g., "This structural dependence on market maturity complements the series-level heterogeneity identified in Section 2") would improve flow.

3. **Mechanism 3 qualifier**: Label the trader composition hypothesis as "speculative / not directly testable" to distinguish it from the other three mechanisms that have concrete predictions.

4. **CRPS decomposition hint**: A brief note on whether CPI's CRPS/MAE > 1 is driven by tail vs. center mispricing would sharpen the mechanism discussion. Even "future work should decompose CRPS by quantile region" would signal awareness.

### Acknowledged Limitations (inherent, not actionable)

1. **Small n**: 14-16 events per series is inherent to the ~16-month data window. Cannot be fixed without waiting.
2. **Single platform**: CRPS/MAE framework generalizes, but specific series findings are Kalshi-specific.
3. **No order book data**: Cannot directly test mechanism 4 (liquidity at extreme strikes) without microstructure data.
4. **Two-series comparison**: With only CPI and Jobless Claims at testable n, the frequency hypothesis relies on a single contrast. GDP (n=3) is directionally consistent but statistically useless.

## Verdict

**ACCEPT** — Minor polish recommended but not required.

The paper delivers a novel, well-executed diagnostic with a genuinely surprising heterogeneity finding. The methodology is rigorous, the claims are appropriately hedged, and the transparency about prior errors (Appendix C) sets a high bar. The "should fix" items above are improvements that would strengthen the paper, but none are blockers. This is ready for the Kalshi Research blog.

## Convergence Assessment

The paper has been through 6 iterations of review and it shows. The statistical corrections are thorough, the claims are calibrated to the evidence, and the narrative is coherent. The remaining suggestions (in-sample caveat, table labels, section bridge) are cosmetic. I see no need for further iteration — this paper is at diminishing returns. Publish it.
