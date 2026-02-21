# Critique — Iteration 1

STATUS: ACCEPT

## Overall Assessment

This paper introduces the CRPS/MAE ratio as a per-series diagnostic for prediction market distributional value and delivers a genuinely surprising result: Jobless Claims distributions add massive value (ratio=0.37) while CPI distributions are actively harmful (ratio=1.32). The methodology is unusually disciplined for applied prediction market work — regime-appropriate benchmarks, Bonferroni correction, effect sizes, power analysis, and an exemplary transparency appendix documenting downgraded and invalidated findings. The paper is ready for the Kalshi Research blog with minor polish.

## Scores
| Criterion | Score | Delta | Comment |
|-----------|-------|-------|---------|
| Novelty | 7/10 | — | CRPS/MAE is a straightforward construction, but applying it as a per-series diagnostic to reveal within-platform heterogeneity is genuinely new. No prior prediction market literature documents that the same platform's distributions are excellent for one series and harmful for another. |
| Methodological Rigor | 8/10 | — | Exemplary self-correction: catching COVID contamination (7.3x → 1.8x), honest Bonferroni adjustment that renders the headline marginal (p_adj=0.093), power analysis for all tests, regime-appropriate windows. The invalidated findings appendix is rare and builds enormous credibility. |
| Economic Significance | 7/10 | — | Directly actionable: traders should use Jobless Claims distributions but ignore CPI distributional spread; Kalshi can use CRPS/MAE as an ongoing quality metric for multi-strike offerings and prioritize liquidity incentives accordingly. |
| Narrative Clarity | 7/10 | — | Clean structure: build CDFs → score them → reveal heterogeneity → hypothesize mechanisms → contextualize. Section 4 (maturity/favorite-longshot) feels somewhat disconnected. The abstract packs a lot but remains informative. |
| Blog Publishability | 8/10 | — | Publishing "our CPI distributions are harmful" and "TIPS leads us, not vice versa" signals intellectual seriousness that sophisticated readers will respect. Self-critical empirical work is exactly what builds a research brand. |

## Seed Question Responses

**1. Is the CRPS/MAE ratio framing genuinely useful, or trivial repackaging?**

Genuinely useful. The mathematical construction is simple — CRPS ≤ MAE for any distribution, so ratio > 1 means the distributional spread destroys value relative to the point forecast. But the *application* as a per-series diagnostic is the real contribution. Aggregate CRPS would mask the dramatic CPI/Jobless Claims divergence. The ratio gives market designers a concrete, interpretable decision metric: "should we offer distributional contracts for this event type?" That's actionable.

**2. Does the heterogeneity finding have practical implications for Kalshi's market design?**

Yes, concretely. If weekly releases produce well-calibrated distributions while monthly composites don't, Kalshi can: (a) prioritize multi-strike offerings for weekly events, (b) use CRPS/MAE as an ongoing quality metric when launching new contract types, (c) adjust strike spacing based on demonstrated calibration quality, and (d) test the frequency hypothesis as they expand coverage. The four testable mechanisms in Section 2 give Kalshi a principled R&D agenda.

**3. Are there claims that overreach the evidence?**

The paper is disciplined about hedging. Two mild concerns:

- The SPX comparison (2.8% vs 2.7%) juxtaposes hourly prediction market snapshots with daily equity option measurements. The text notes this but the table invites direct numerical comparison. Adding "(hourly)" and "(daily)" labels in the table would prevent casual conflation.
- Mechanism 3 (trader composition) is essentially unfalsifiable with public data, unlike mechanisms 1, 2, and 4 which have concrete testable predictions. It should be flagged as more speculative.

**4. What's missing that would make this substantially stronger?**

The single biggest gap is an **explicit in-sample caveat**. All CRPS/MAE ratios and Wilcoxon tests are computed on the full Oct 2024 – Feb 2026 dataset. With n=14–16, train/test splitting is impractical, but the paper never directly states this limitation. One sentence in the Methodology section — "All scoring uses the full available sample; rolling-window out-of-sample validation is infeasible at current n but is a priority as data accumulates" — would preempt the sharpest criticism from quantitative readers.

A secondary gap: the paper doesn't discuss whether CPI's CRPS/MAE > 1 is driven by tail mispricing (extreme strikes with thin liquidity) or center mispricing. This decomposition would sharpen the mechanism story — if it's tail-driven, mechanism 4 gains direct support.

**5. Would this enhance or damage Kalshi's research credibility?**

Strongly enhance. Self-critical empirical work that publishes negative findings (CPI distributions harmful, TIPS leads Kalshi, extensive appendix of invalidated results) builds exactly the kind of credibility that makes sophisticated readers take future research seriously. This is the kind of paper that signals "we care about truth, not marketing."

## The One Big Thing

**Add an explicit in-sample caveat.** The paper is honest about sample sizes and power but never directly states that all results are computed on the full available dataset without hold-out validation. One sentence in the Methodology section would preempt the most predictable criticism from quantitative reviewers. This does not block publication — it's a polish item.

## Other Issues

### Must Fix (blocks publication)
- None. The paper is in publishable condition.

### Should Fix (strengthens paper)

1. **SPX comparison frequency labels**: Add "(hourly)" and "(daily)" parentheticals directly in the no-arbitrage table to prevent casual conflation of measurement frequencies across very different market structures.

2. **Section 4 bridge sentence**: The maturity/favorite-longshot analysis feels orphaned from the CRPS narrative. A single sentence connecting it back (e.g., "This structural dependence on market maturity complements the series-level calibration heterogeneity identified in Section 2") would improve coherence.

3. **Mechanism 3 qualifier**: Flag the trader composition hypothesis as "speculative / not directly testable with public data" to distinguish it from the other three mechanisms that have concrete, falsifiable predictions.

4. **CRPS tail decomposition note**: Even a brief mention — "future work should decompose CRPS contributions by quantile region to distinguish tail mispricing from center mispricing" — would signal methodological awareness and strengthen the mechanism discussion.

### Acknowledged Limitations (inherent, not actionable)

1. **Small n**: 14–16 events per series is inherent to the ~16-month data window. Cannot be addressed without waiting for more data.
2. **Single platform**: The CRPS/MAE framework generalizes, but the specific series findings are Kalshi-specific and may not transfer to other prediction markets.
3. **No order book data**: Cannot directly test mechanism 4 (liquidity at extreme strikes) without microstructure data that isn't publicly available.
4. **Two-series comparison**: The frequency hypothesis relies on a single CPI vs. Jobless Claims contrast. GDP (n=3) is directionally consistent but statistically useless. The hypothesis needs more series to test properly.

## Verdict

**ACCEPT** — Minor polish recommended but not required.

The paper delivers a novel, well-executed diagnostic with a genuinely surprising heterogeneity finding. The methodology is rigorous, claims are appropriately hedged, and the transparency about prior errors (Appendix C) sets a high bar for applied prediction market research. The "should fix" items above are improvements, not blockers. This is ready for the Kalshi Research blog.

## Convergence Assessment

The paper has been through 6 iterations of internal review and it shows — the statistical corrections are thorough, claims are calibrated to the evidence, and the narrative is coherent. The remaining suggestions (in-sample caveat, table labels, section bridge, mechanism qualifier) are all minor polish. I see no need for further substantive iteration. This paper is at diminishing returns. Publish it.
