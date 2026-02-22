# Researcher Response — Iteration 7

STATUS: CONTINUE

## Deliberation

### 1. The One Big Thing: CRPS/MAE vs surprise magnitude analysis
- **Agree**: Strongly. This is the most analytically important suggestion in the critique. The reviewer correctly identified that the per-event data directionally suggests an inverse relationship, and the formal test confirms it decisively.
- **Feasible**: Yes — implemented in ~50 lines of code added to experiment13/run.py.
- **Impact**: **HIGH** — This is a genuinely novel finding that adds important nuance to the paper's headline CPI result and has direct market design implications.
- **Action**: Implemented Spearman correlation, per-event autocorrelation, and conditional CRPS/MAE by direction. Results:
  - CPI: ρ=−0.68 (p=0.008) — distributions fail more on small surprises, perform better on large ones
  - JC: ρ=−0.55 (p=0.029) — same pattern, confirming this is a general property of CRPS/MAE
  - This is NOT merely a ratio artifact: the same pattern in JC (where CRPS/MAE < 1 overall) shows it's a genuine feature of how distributional quality interacts with surprise magnitude
- **Code written**: Yes — experiment13/run.py, Phase 7B (~50 lines). Computes Spearman correlations, AR(1) of per-event ratios, and conditional CRPS/MAE by surprise direction for CPI.

### 2. Scope "first empirical demonstration" to prediction markets
- **Agree**: Completely. The calibration-sharpness decomposition is well-known from Hersbach (2000) and Murphy (1993). What's novel is documenting it in a market context. The one-phrase fix preempts the most predictable objection.
- **Feasible**: One phrase.
- **Impact**: MEDIUM — credibility with knowledgeable readers.
- **Action**: Changed to "first empirical demonstration *in prediction markets*" in both the abstract and Section 3 decoupling paragraph. Added parenthetical citing Murphy 1993 and Hersbach 2000.

### 3. Note low autocorrelation of per-event ratios
- **Agree**: Yes, this is a clean finding that directly strengthens the bootstrap CI interpretation and adds a novel observation about event-specific vs persistent calibration failure.
- **Feasible**: One sentence, now backed by code results.
- **Impact**: MEDIUM — strengthens CI claims and adds interpretive depth.
- **Action**: Added parenthetical after block bootstrap CI: "The per-event CRPS/MAE ratios themselves show lower autocorrelation — CPI AR(1)≈0.12, JC AR(1)≈0.04 — making this adjustment conservative. The near-zero per-event autocorrelation means distributional quality is approximately independent across events, consistent with event-specific calibration failures rather than persistent structural bias."
- **Code written**: Yes — AR(1) computed in Phase 7B. Results: CPI interior AR(1)=0.123, JC interior AR(1)=0.035 — exactly matching the reviewer's priors.

### 4. Fix PIT claim consistency
- **Agree**: Yes. The Section 3 decoupling paragraph used "indicating" while the PIT section proper correctly hedged. Fixed.
- **Feasible**: One word.
- **Impact**: LOW — consistency fix.
- **Action**: Changed "indicating systematic inflation underestimation" → "consistent with systematic inflation underestimation" in Section 3.

### 5. Update iteration status
- **Agree**: Trivial.
- **Action**: Updated to "iteration 7."

### 6. Conditional CRPS/MAE by surprise direction
- **Partially agree**: Implemented, but the results are dominated by the small-MAE mechanical effect rather than a directional asymmetry. Downside surprises (n=5) show CRPS/MAE=2.22 vs upside (n=9) at 1.34, but the downside events have mean MAE=0.038 vs 0.085 for upside — this is the Spearman finding in disguise, not an independent directional signal. Reported for completeness but framed as confirming the surprise magnitude finding rather than as an independent result.
- **Impact**: LOW independently; confirms the Spearman result.

## Code Changes

1. **experiment13/run.py** — Added Phase 7B: "Surprise Magnitude & Autocorrelation Diagnostics" (~50 lines):
   - Spearman rank correlation between surprise magnitude (MAE) and per-event CRPS/MAE ratio, for both tail-aware and interior specifications
   - AR(1) autocorrelation of per-event CRPS/MAE ratios (both specifications)
   - Conditional CRPS/MAE split by inflation surprise direction (CPI only: realized > vs ≤ implied mean)
   - All results saved to `unified_results.json` under `surprise_magnitude_diagnostics`

## Paper Changes

- **Abstract**: Scoped "first empirical demonstration" to "in prediction markets"
- **Section 2, new subsection "Surprise Magnitude: When Do Distributions Fail?"**: Added Spearman correlation table, interpretation, two implications (nuancing the CPI finding + explaining the ratio mechanic), and conditional analysis by direction
- **Section 2, CPI block bootstrap paragraph**: Added parenthetical noting low per-event autocorrelation (CPI ρ≈0.12, JC ρ≈0.04) and conservative bootstrap adjustment
- **Section 3, decoupling paragraph**: (a) Scoped novelty claim to "in prediction markets" with Murphy/Hersbach citations, (b) changed "indicating" → "consistent with" for PIT finding
- **Section 3, iteration status**: Updated to 7
- **References**: Added Murphy (1993)

## New Results

| Analysis | Result | Significance |
|----------|--------|-------------|
| CPI Spearman(surprise, CRPS/MAE) | ρ=−0.68 | p=0.008 |
| JC Spearman(surprise, CRPS/MAE) | ρ=−0.55 | p=0.029 |
| CPI per-event ratio AR(1) (interior) | 0.123 | Low — supports event independence |
| JC per-event ratio AR(1) (interior) | 0.035 | Very low — events approximately independent |
| CPI conditional: upside (n=9) | CRPS/MAE=1.34 | Distributions less harmful for upside surprises |
| CPI conditional: downside (n=5) | CRPS/MAE=2.22 | Dominated by small-MAE mechanical effect |

**The surprise magnitude finding (ρ=−0.68, p=0.008) is the most analytically significant new result since the data leakage fix in iteration 6.** It adds genuine nuance: CPI distributions are harmful on average, but the penalty is concentrated in low-surprise events. For the large surprises where distributional information matters most, performance approaches parity. This is novel, statistically significant, and directly actionable for market design.

## Pushbacks

None this iteration. All critique points were well-reasoned and feasible. The conditional-by-direction analysis is less informative than the reviewer hoped (dominated by the small-MAE effect), but this is itself an informative null — the directional bias from PIT doesn't map cleanly onto conditional CRPS/MAE because the ratio mechanic dominates.

## Remaining Weaknesses

1. **Small sample sizes**: n=14 CPI, n=16 JC. Fundamental and well-documented.
2. **Two series only**: The heterogeneity finding and surprise magnitude pattern need replication across more series.
3. **In-sample only**: No cross-validation feasible.
4. **The surprise magnitude finding creates a slight tension**: The paper recommends "ignore CPI distributions entirely," but the new analysis shows they perform reasonably for large surprises. The paper now notes this nuance, but a reader could argue the recommendation should be "use CPI distributions only for large surprise scenarios." At current n, we can't reliably estimate the surprise threshold where CRPS/MAE crosses 1.0, so the conservative "ignore" recommendation stands.
5. **Mechanisms remain untestable**: The four hypotheses still cannot be directly tested with public data.
6. **Blog length continues to grow**: ~5,000 words now. The surprise magnitude subsection adds ~250 words but is substantively important enough to justify the length.
