# Researcher Response — Iteration 4

STATUS: CONTINUE

## Deliberation

### 1. Must Fix: Interior-only Mann-Whitney heterogeneity test
- **Agree**: Yes, completely. The paper acknowledges tail-aware per-event ratio instability but then uses those same unstable ratios in the formal heterogeneity test. This is an internal inconsistency.
- **Feasible**: Yes — 5 lines of code.
- **Impact**: HIGH — resolves a logical inconsistency and strengthens the heterogeneity claim.
- **Action**: Implemented. Interior-only MWU gives p=0.026, r=−0.48 (medium-to-large effect). Both specifications confirm heterogeneity. Reported in the paper alongside the tail-aware result.
- **Code written**: Yes — experiment13/run.py, added interior-only MWU (~10 lines).

### 2. Should Fix: Strengthen random walk horse race language
- **Agree**: Yes. "Borderline significant" with d=−0.71 and >80% power genuinely undersells the result. The reviewer is right that "significant at the 10% level with a large effect size and adequate power" is a more accurate description.
- **Feasible**: Prose change.
- **Impact**: MEDIUM — correctly calibrates the reader's interpretation.
- **Action**: Rewrote the horse race interpretation paragraph. Removed "borderline significant," replaced with "significant at the 10% level after Bonferroni correction" and emphasized the power analysis confirms adequacy.

### 3. Should Fix: KXJOBLESSCLAIMS-26JAN29 concrete example
- **Agree**: Yes. The paper discusses ratio instability in general terms but this specific JC example (tail-aware ratio 10.36 vs interior 1.20, MAE=350) perfectly illustrates the problem AND shows the aggregate is immune.
- **Feasible**: Prose change + data already in hand.
- **Impact**: MEDIUM — strengthens the methodological argument for ratio-of-means.
- **Action**: Added the specific example to the per-event ratios note, alongside the existing CPI example.

### 4. Should Fix: Remove dead CRPS decomposition code
- **Agree**: Yes. Dead code with `pass` in a loop body is confusing.
- **Feasible**: Trivial.
- **Impact**: LOW — code hygiene, no paper impact.
- **Action**: Replaced the dead binning loop with a clear comment explaining why the decomposition is deferred (infeasible at n<20). Preserved the simpler PIT-based diagnostics that are actually used.
- **Code written**: Yes — experiment13/run.py, replaced ~25 lines of dead code with 3-line comment.

### 5. Should Fix: Compress dual-metric reporting
- **Partially agree**: The reviewer is right that dual-metric reporting creates cognitive load. However, I disagree with moving interior-only to a full appendix — it's important for transparency that both are visible, especially since the serial-correlation-adjusted CPI CI includes 1.0 only for tail-aware. Instead, I compressed where possible while keeping both visible. The paper already treats tail-aware as primary with interior-only labeled as "sensitivity."
- **Impact**: MEDIUM for blog readability.
- **Action**: Kept current structure but ensured tail-aware is clearly primary everywhere. The sensitivity tables are clearly labeled.

### 6. Novelty: Point-vs-distribution decoupling as co-headline
- **Agree strongly**: This is the single most actionable insight for traders. CPI point forecasts beat all benchmarks while CPI distributions are actively harmful — this decoupling is genuinely novel and was buried as a subsidiary observation.
- **Impact**: HIGH for narrative and blog readability.
- **Action**: (a) Restructured abstract to open with the decoupling insight; (b) Added dedicated "The point-vs-distribution decoupling" paragraph in Section 3 horse race; (c) Made practical takeaways a bullet-pointed box in the abstract.

### 7. New Experiment: Ratio-of-means vs mean-of-ratios comparison table
- **Agree**: Great suggestion. The mean-of-ratios numbers (CPI: 3.89 tail-aware, JC: 1.29 tail-aware) dramatically illustrate why the aggregation choice matters.
- **Feasible**: Yes — computed from existing data.
- **Impact**: HIGH — provides a concrete, memorable illustration of a methodological choice that readers might otherwise question.
- **Action**: Added code to compute mean-of-ratios for both specifications. Added comparison table to the per-event section with commentary.
- **Code written**: Yes — experiment13/run.py, added mean-of-ratios computation (~15 lines).

### 8. New Experiment: Per-event scatter/strip visualization
- **Partially agree**: The strip chart already exists in experiment outputs (per_event_crps_mae_strip.png). The reviewer suggests including it in the paper — it's already referenced. I chose not to embed the image directly in the markdown (the paper is markdown, not HTML), but strengthened the reference and the per-event data table that serves the same purpose.
- **Impact**: LOW incremental — the strip chart exists and is referenced.

### 9. Blog-formatted key findings summary
- **Agree**: The practical takeaway box is a good idea for the Kalshi blog audience.
- **Action**: Restructured the abstract's "Bottom line for traders" into a bulleted "Practical Takeaways" box with three clear action items.

### 10. Compress Monte Carlo simulation details
- **Agree**: The simulation paragraph was dense. Moved implementation details (distributional families, parameter matching) into a parenthetical while keeping the punchline prominent.
- **Impact**: LOW — readability improvement.

## Code Changes

1. **experiment13/run.py** — Added:
   - Interior-only Mann-Whitney U test as robustness check for heterogeneity (p=0.026, r=−0.48)
   - Mean-of-ratios computation for both CPI and JC, both metric specifications
   - Comparison table output: ratio-of-means vs median vs mean-of-ratios

2. **experiment13/run.py** — Cleaned up:
   - Replaced dead Hersbach (2000) CRPS decomposition stub (~25 lines of dead code including `pass` loop body) with 3-line comment explaining deferral

## Paper Changes

- **Abstract**: Restructured to lead with point-vs-distribution decoupling. Added interior-only MWU p-value. Replaced "Bottom line" prose with bulleted "Practical Takeaways" box with 3 action items.
- **Section 2 — Heterogeneity paragraph**: Added interior-only MWU (p=0.026, r=−0.48) alongside tail-aware, confirming robustness across metric specifications.
- **Section 2 — Per-event ratios note**: Added KXJOBLESSCLAIMS-26JAN29 concrete example (tail-aware ratio 10.36 vs interior 1.20, MAE=350). Added "Aggregation method matters" comparison table showing ratio-of-means, median, and mean-of-ratios for both specifications.
- **Section 3 — Horse race**: Strengthened random walk language from "borderline significant" to "significant at the 10% level with adequate power." Added dedicated "point-vs-distribution decoupling" paragraph as co-headline finding.
- **Section 2 — Strike simulation**: Compressed paragraph, moved distributional family details to parenthetical.
- **Methodology item 14**: Updated to include both tail-aware and interior-only MWU p-values.

## New Results

| Analysis | Key Finding |
|----------|-------------|
| Interior-only Mann-Whitney | p=0.026, r=−0.48 — heterogeneity robust across metric specifications |
| Mean-of-ratios (CPI, tail-aware) | 3.89 — dominated by KXCPI-25JUN (21.5) and KXCPI-25MAY (14.6) |
| Mean-of-ratios (JC, tail-aware) | 1.29 — dominated by KXJOBLESSCLAIMS-26JAN29 (10.4) |
| Mean-of-ratios (CPI, interior) | 1.78 — 13% higher than ratio-of-means (1.58) |
| Mean-of-ratios (JC, interior) | 0.86 — 30% higher than ratio-of-means (0.66) |

## Pushbacks

### Dual-metric consolidation to appendix
The reviewer suggests making tail-aware the sole in-text metric and moving interior-only to a supplementary section. I partially disagree: the interior-only sensitivity tables are already clearly labeled and compact. Moving them to an appendix would require readers to jump around the document to verify a key robustness claim (that JC CRPS/MAE < 1 under both specifications). The current structure — tail-aware primary, interior-only clearly labeled as "sensitivity" directly below — is the right balance for a research-oriented blog post.

### Blog-formatted standalone summary
The reviewer suggests a 200-word standalone blog lede. I implemented this as the restructured abstract + practical takeaways box, which serves the same purpose without creating a separate section that would need to be maintained alongside the abstract.

## Remaining Weaknesses

1. **Small sample sizes remain fundamental**: n=14 CPI, n=16 JC. This is inherent and well-documented.
2. **In-sample only**: No cross-validation possible at current n.
3. **Serial-correlation-adjusted CPI CI includes 1.0**: The LOO analysis + four-diagnostic convergence mitigate this, but the serial dependence concern is real.
4. **Only two series**: The heterogeneity finding would be far more compelling with 5+ series. Inherent to current Kalshi offerings.
5. **No causal mechanism identified**: Four hypotheses are plausible but untestable.
6. **Interior-only MWU weaker than tail-aware**: p=0.026 vs p=0.003. The heterogeneity is significant under both, but the interior-only test has less separation. This is expected given that interior-only ratios compress the range.
