# Critique — Iteration 1

STATUS: ACCEPT

## Overall Assessment

This paper introduces the CRPS/MAE ratio as a per-series diagnostic for whether prediction market implied distributions add value beyond point forecasts, and uncovers a striking heterogeneity: Jobless Claims distributions are excellent (ratio=0.37) while CPI distributions are actively harmful (ratio=1.32). The methodology is unusually rigorous for applied prediction market work — regime-appropriate benchmarks, Bonferroni correction, effect sizes, power analysis, and a remarkably honest appendix of invalidated findings. The paper is ready for the Kalshi Research blog.

## Scores
| Criterion | Score | Delta | Comment |
|-----------|-------|-------|---------|
| Novelty | 7/10 | — | CRPS/MAE is a simple construction, but applying it per-series to reveal within-platform distributional heterogeneity is genuinely new. No prior prediction market literature shows the same platform's distributions are excellent for one series and harmful for another. |
| Methodological Rigor | 8/10 | — | Catching COVID contamination (7.3x→1.8x), honest Bonferroni that weakens the headline (p_adj=0.093), power analysis for all tests, regime-appropriate windows. Appendix C documenting invalidated findings is rare and builds enormous credibility. Minor gap: no explicit in-sample caveat. |
| Economic Significance | 7/10 | — | Directly actionable for both traders (use Jobless Claims distributions, ignore CPI spread) and Kalshi (CRPS/MAE as ongoing quality metric for multi-strike offerings, prioritize liquidity incentives by series). |
| Narrative Clarity | 7/10 | — | Clean structure: build CDFs → score them → reveal heterogeneity → hypothesize mechanisms → contextualize. Section 4 (maturity) feels slightly disconnected from the main CRPS narrative. Abstract is dense but informative. |
| Blog Publishability | 8/10 | — | Publishing "our CPI distributions are harmful" and "TIPS leads us" signals intellectual seriousness. Self-critical empirical work is exactly what builds a research brand. Sophisticated readers will respect this. |

## Seed Question Responses

**1. Is the CRPS/MAE ratio framing genuinely useful, or trivial repackaging?**

Genuinely useful. The mathematical construction is straightforward — CRPS ≤ MAE for any distribution, so ratio > 1 means distributional spread destroys value. But the *application* as a per-series diagnostic is the real contribution. Aggregate CRPS would mask the CPI/Jobless Claims divergence entirely. The ratio gives market designers a concrete decision metric: "should we offer distributional contracts for this event type?" That's actionable and novel in the prediction market context.

**2. Does the heterogeneity finding have practical implications for Kalshi's market design?**

Yes, concretely. If weekly releases produce well-calibrated distributions while monthly composites don't, Kalshi can: (a) prioritize multi-strike offerings for weekly events, (b) use CRPS/MAE as an ongoing quality metric, (c) adjust strike spacing by demonstrated calibration quality, and (d) test the frequency hypothesis as they expand coverage. The four testable mechanisms give Kalshi a principled R&D agenda for new contract types.

**3. Are there claims that overreach the evidence?**

The paper is disciplined about hedging. Two mild concerns:

- The SPX comparison (2.8% vs 2.7%) juxtaposes hourly prediction market snapshots with daily equity option measurements. The text acknowledges this, but the table structure invites direct numerical comparison. Adding "(hourly)" and "(daily)" labels in the table would prevent casual conflation.
- Mechanism 3 (trader composition) is unfalsifiable with public data, unlike mechanisms 1, 2, and 4 which have concrete testable predictions. It should be flagged as more speculative than the others.

**4. What's missing that would make this substantially stronger?**

The single biggest gap is an **explicit in-sample caveat**. All CRPS/MAE ratios and Wilcoxon tests are computed on the full dataset. With n=14–16, train/test splitting is impractical, but the paper never directly states this limitation. One sentence — "All scoring uses the full available sample; rolling-window out-of-sample validation is infeasible at current n but is a priority as data accumulates" — would preempt the most predictable criticism from quantitative readers.

A secondary gap: no discussion of whether CPI's CRPS/MAE > 1 is driven by tail mispricing (thin liquidity at extreme strikes) or center mispricing. This decomposition would sharpen the mechanism story and provide direct evidence for or against mechanism 4.

**5. Would this enhance or damage Kalshi's research credibility?**

Strongly enhance. Publishing negative findings about your own platform (CPI distributions harmful, TIPS leads Kalshi, extensive appendix of prior errors) signals intellectual seriousness that sophisticated readers — the exact audience for a research blog — will respect. This is the kind of paper that says "we care about truth, not marketing."

## The One Big Thing

**Add an explicit in-sample caveat.** The paper is honest about sample sizes and power throughout, but never directly states that all results are computed on the full available dataset without hold-out validation. One sentence in the Methodology section would preempt the most predictable criticism. This does not block publication — it's a polish item.

## Other Issues

### Must Fix (blocks publication)
- None. The paper is in publishable condition.

### Should Fix (strengthens paper)

1. **SPX comparison frequency labels**: Add "(hourly)" and "(daily)" parentheticals in the no-arbitrage table to prevent casual conflation of measurement frequencies.

2. **Section 4 bridge sentence**: The maturity analysis feels orphaned. One sentence connecting it to the CRPS narrative (e.g., "This structural dependence on market maturity complements the series-level calibration heterogeneity in Section 2") would improve coherence.

3. **Mechanism 3 qualifier**: Flag trader composition as "speculative / not directly testable with public data" to distinguish it from the other three falsifiable mechanisms.

4. **CRPS tail decomposition note**: A brief mention that future work should decompose CRPS by quantile region to distinguish tail vs. center mispricing would signal methodological awareness and strengthen the mechanism discussion.

### Acknowledged Limitations (inherent, not actionable)

1. **Small n**: 14–16 events per series is inherent to the ~16-month data window. Cannot be fixed without waiting for more data.
2. **Single platform**: The CRPS/MAE framework generalizes, but specific findings are Kalshi-specific.
3. **No order book data**: Cannot directly test mechanism 4 (liquidity at extreme strikes) without non-public microstructure data.
4. **Two-series comparison**: The frequency hypothesis rests on a single CPI vs. Jobless Claims contrast. GDP (n=3) is directionally consistent but statistically useless. More series needed to test properly.

## Verdict

**ACCEPT** — Minor polish recommended but not required.

The paper delivers a novel diagnostic with a genuinely surprising heterogeneity finding, rigorous methodology, appropriately hedged claims, and an exemplary transparency appendix. The "should fix" items above are improvements, not blockers. This is ready for the Kalshi Research blog.

## Convergence Assessment

The paper has been through 6 iterations of internal review and it shows — statistical corrections are thorough, claims are calibrated to evidence, and the narrative is coherent. The remaining suggestions (in-sample caveat, table labels, section bridge, mechanism qualifier) are all minor polish. I see no need for further substantive iteration. This paper is at diminishing returns. Publish it.
