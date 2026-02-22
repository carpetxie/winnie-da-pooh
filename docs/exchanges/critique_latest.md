# Critique — Iteration 1

STATUS: CONTINUE

## Overall Assessment

This is a well-structured empirical paper with a genuinely useful diagnostic (CRPS/MAE ratio) and an honest, self-critical methodology section. The core finding — that distributional calibration varies dramatically across event types — is interesting and actionable. However, the paper contains a mathematical misstatement about the CRPS/MAE bound that undermines its central framing, the no-arbitrage benchmark comparison is not apples-to-apples, and the SPF horse race uses a conversion so crude it arguably shouldn't be presented without much stronger caveats.

## Scores

| Criterion | Score | Delta | Comment |
|-----------|-------|-------|---------|
| Novelty | 7/10 | — | The per-series CRPS/MAE diagnostic and the heterogeneity finding are a genuine contribution. Not methodologically novel (CRPS is standard), but the application to prediction markets and the per-series decomposition are new and useful. |
| Methodological Rigor | 6/10 | — | The CRPS/MAE > 1 interpretation rests on an incorrect mathematical claim. The SPF conversion is crude. The no-arbitrage comparison mixes hourly vs daily granularity. Bonferroni, power analysis, and regime-appropriate benchmarks are all strengths, but the foundation has cracks. |
| Economic Significance | 7/10 | — | Actionable for both Kalshi (which series to invest in for distributional products) and traders (ignore CPI distributions, use Jobless Claims distributions). The information hierarchy finding (TIPS leads Kalshi) is useful context. |
| Narrative Clarity | 7/10 | — | The paper tells a coherent story and the structure is logical. Section 4 (maturity) still feels slightly disconnected despite the bridge sentence. The transparency appendix is excellent. |
| Blog Publishability | 6/10 | — | Close to publishable but the mathematical misstatement and the apples-to-oranges no-arbitrage comparison would draw justified criticism from quantitative readers. Fixing these is straightforward and would move this to 7-8. |

## Seed Questions Addressed

### 1. Is the CRPS/MAE ratio framing genuinely useful, or is it a trivial repackaging?

It is genuinely useful. The ratio provides a single number that answers a practical question: "Should I pay attention to the full distribution, or just use the point forecast?" This is directly actionable for traders. The decomposition by series (revealing that the answer differs for CPI vs Jobless Claims) is the real contribution. That said, the paper should acknowledge that CRPS decomposition into reliability/resolution/uncertainty components (Hersbach, 2000) is a more informative diagnostic that the ratio collapses into a single dimension. The ratio is a useful *summary* but not a *complete* diagnostic.

### 2. Does the heterogeneity finding have practical implications for Kalshi's market design?

Yes, meaningfully. If CPI distributions are actively harmful (CRPS/MAE > 1), Kalshi should consider whether the multi-strike structure adds value for CPI markets, or whether resources would be better deployed on series where distributional information is well-calibrated. For traders, this is an explicit signal: use Jobless Claims distributions, ignore CPI distributional spread. For market designers, the release-frequency hypothesis (if validated) would suggest prioritizing multi-strike structures for high-frequency releases.

### 3. Are there claims that overreach the evidence?

Yes, two:

**a) "CRPS is always ≤ MAE for any distribution, so ratio < 1 means the distribution helps, while ratio > 1 indicates the distributional spread is actively harmful."**

This is incorrect as stated. There is no general mathematical theorem that CRPS(F, y) ≤ |μ_F − y| for arbitrary distributions F. What is true: CRPS(F, y) = E_F|X − y| − ½E_F|X − X'|, and for a point mass at μ, CRPS = |μ − y|. A well-calibrated distribution will on average have CRPS < MAE (the sharpness reward of proper scoring), but for a miscalibrated distribution CRPS can exceed MAE — which is exactly what happens for CPI. The paper presents ratio > 1 as violating a bound; in fact, it's the *expected diagnostic signal* of a poorly calibrated distribution. The fix is simple: reframe the ratio as a diagnostic of distributional calibration quality rather than as a violation of a mathematical inequality. The finding is the same; the framing just needs to be precise.

**b) The no-arbitrage comparison to SPX options.** The paper compares Kalshi's 2.8% hourly violation rate to Brigo et al.'s 2.7% daily call-spread violation rate for SPX options. But hourly sampling captures transient violations that would be invisible at daily granularity. If you measured SPX at hourly granularity, you'd likely find a higher violation rate. Conversely, if you measured Kalshi daily, the rate would likely be lower. The comparison is directionally interesting but the paper presents it as "comparable" without acknowledging the granularity mismatch. This needs a caveat.

### 4. What's missing that would make this substantially stronger?

Three things, in priority order:

**a) CRPS decomposition by quantile region.** The paper mentions this as future work (mechanism 4 discussion), but it's feasible now. Decomposing CRPS into contributions from the center vs tails of the distribution would directly distinguish between "CPI markets misprice the center of the distribution" vs "CPI markets misprice the tails due to thin liquidity at extreme strikes." This would transform the paper from "we found heterogeneity" to "we found heterogeneity and here's the mechanism." Even a simplified version (CRPS contribution from strikes within 1σ vs outside) would be valuable.

**b) Strike spacing analysis.** The paper uses piecewise-linear interpolation between Kalshi's discrete strikes to construct CDFs, but never reports how many strikes each event has or how they're spaced. If CPI events have fewer strikes or wider spacing than Jobless Claims, the piecewise-linear CDF for CPI is a cruder approximation, mechanically inflating CRPS. The number of strikes per event and the spacing granularity relative to realized variability should be reported — this could partially explain the CRPS/MAE > 1 finding for CPI as a measurement artifact rather than genuine miscalibration.

**c) Stronger SPF horse race caveats.** The SPF comparison uses `annual_rate / 12` to convert annual CPI forecasts to monthly. This is a very rough approximation — it ignores seasonality, base effects, and the fact that SPF panelists forecast annual Q4/Q4 changes, not the average monthly rate. The paper acknowledges this ("annual/12 proxy") but still presents it as a row in the horse race table alongside more comparable benchmarks. Either add a much more prominent caveat (e.g., a footnote explaining exactly why this is approximate) or move SPF to a separate "indicative only" section. As is, a reader could reasonably criticize the comparison as unfair.

### 5. Would this enhance or damage Kalshi's research credibility?

Enhance, with caveats. The self-critical methodology (documenting invalidated findings, conservative corrections, honest power analysis) is exactly the right tone for a research blog. The finding that some Kalshi distributions are "harmful" is counterintuitively *good* for credibility — it shows Kalshi is willing to publish uncomfortable truths. The risk is that the mathematical misstatement about CRPS ≤ MAE would be caught by quantitative readers and undermine trust. Fix that, and this strengthens Kalshi's research brand.

## The One Big Thing

**Fix the CRPS/MAE mathematical framing.** The claim that "CRPS is always ≤ MAE for any distribution" is incorrect and it's the conceptual foundation of the paper's main diagnostic. The finding itself is valid and interesting — when the ratio exceeds 1, it really does mean the distributional spread is hurting rather than helping. But the paper needs to frame this correctly: CRPS(F, y) ≤ |μ − y| is *not* a mathematical bound; it's an *expected property of well-calibrated distributions* (because the sharpness term ½E|X − X'| rewards distributional spread only when that spread is informative). The ratio > 1 is a diagnostic signal of miscalibration, not a violation of a theorem. This is a 2-sentence fix that makes the paper bulletproof.

## Other Issues

### Must Fix (blocks publication)

1. **CRPS ≤ MAE mathematical misstatement** (Section 2, paragraph 1): Reframe as a calibration diagnostic rather than a mathematical bound. The sentence "CRPS is always <= MAE for any distribution" should be replaced with something like: "For a well-calibrated distribution, the sharpness reward in CRPS means it will be lower than MAE; ratio > 1 signals that the distributional spread is miscalibrated and actively harming forecast quality."

2. **No-arbitrage granularity caveat** (Section 1, table): Add a note that the SPX comparison uses daily data while Kalshi uses hourly snapshots, making direct numerical comparison approximate. The paper already notes "(hourly)" and "(daily)" in the table — good — but the prose below says "comparable" without qualifying the granularity mismatch.

### Should Fix (strengthens paper)

1. **Report strike counts and spacing per series.** Add a row or footnote showing average number of strikes per event for CPI vs Jobless Claims and their typical spacing. If CPI has fewer or wider-spaced strikes, this is an important confound for the CRPS/MAE finding.

2. **CRPS decomposition reference.** Cite Hersbach (2000) for CRPS decomposition into reliability, resolution, and uncertainty components. Acknowledge that the CRPS/MAE ratio collapses these dimensions into a single number and that future work should decompose them. This preempts the obvious critique from forecasting specialists.

3. **Strengthen SPF caveat.** The "(annual/12 proxy)" label is easy to miss. Add a sentence explicitly stating: "SPF does not forecast monthly CPI; this conversion assumes uniform monthly contributions to annual inflation and should be treated as indicative rather than definitive."

4. **PIT analysis framing.** The appendix PIT analysis (mean PIT = 0.61) is suggestive of systematic underestimation of inflation, which would be a very interesting finding if confirmed. Rather than burying this as "warrants monitoring," briefly note in the main text that the PIT diagnostic hints at directional bias (overconfident low CPI outcomes) and that this is consistent with the CRPS/MAE > 1 finding — the distribution is miscalibrated specifically in the direction of underestimating inflation. This connects two otherwise disconnected findings.

### Acknowledged Limitations (inherent, not actionable)

1. **Small n (14-16 per series)** — fundamental constraint of the data window. Cannot be addressed without waiting for more events.
2. **Two-series comparison** — the release frequency hypothesis rests entirely on CPI vs Jobless Claims contrast. Cannot be tested more rigorously without additional series with sufficient n.
3. **In-sample evaluation** — acknowledged in the paper. Train/test splitting is infeasible at n=14-16.
4. **No order book data** — cannot directly test the liquidity/thin-tails mechanism without non-public data.
5. **Single platform** — all findings are Kalshi-specific. Generalization to Polymarket or other venues is untested.

## Verdict

**MINOR REVISIONS** — The paper is fundamentally sound and tells an interesting, honest story. The CRPS/MAE mathematical misstatement is the only item that genuinely blocks publication (because it's in the conceptual core and would be caught by any quantitative reader). The no-arbitrage granularity caveat is a close second. Both are fixable in under an hour. After those fixes, this is ready for the Kalshi Research blog.

## Convergence Assessment

The paper is already at 6-7/10 across criteria. The must-fix items are straightforward (reframing, not new analysis). The should-fix items would collectively move this to 7-8/10. I expect one more iteration to reach publishable quality. If the researcher addresses the two must-fix items and at least the strike spacing and SPF caveat from the should-fix list, I would likely issue ACCEPT on the next pass. We are close to convergence but not there yet.
