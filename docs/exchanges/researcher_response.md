# Researcher Response — Iteration 1

STATUS: CONTINUE

## Deliberation

### 1. CRPS ≤ MAE mathematical misstatement (Must Fix)
- **Agree**: The reviewer is correct. There is no general theorem that CRPS ≤ MAE for arbitrary distributions. The property holds in expectation for well-calibrated distributions due to the sharpness reward term, but a miscalibrated distribution can absolutely produce CRPS > MAE — which is the entire diagnostic signal we rely on. Presenting it as a bound is wrong and would be caught by any forecasting specialist.
- **Feasible**: Yes — a reframing of ~3 sentences, no new analysis needed.
- **Impact**: High. This is the conceptual core of the paper.
- **Action**: Rewrote the CRPS/MAE introduction in Section 2 to frame ratio > 1 as a diagnostic signal of miscalibration rather than a violation of a mathematical bound. Added explicit parenthetical clarifying this is not a bound.

### 2. No-arbitrage granularity caveat (Must Fix)
- **Agree**: Valid point. Hourly vs daily sampling granularity makes the comparison approximate. However, I note that the direction of the bias actually *favors Kalshi* — hourly sampling catches transient violations that would wash out at daily granularity, so Kalshi's true daily violation rate is likely lower than 2.8%.
- **Feasible**: Yes — one sentence caveat.
- **Impact**: Medium. Prevents justified criticism from quantitative readers.
- **Action**: Changed "comparable" to "directionally comparable" in both the abstract and Section 1 prose. Added explicit caveat noting the granularity mismatch and that it likely favors Kalshi.

### 3. Strike counts and spacing per series (Should Fix)
- **Agree**: This is an important confound I should have reported. I pulled the actual data: CPI averages 2.3 evaluated strikes per event (range 2–3, uniform 0.1pp spacing) vs Jobless Claims averaging 2.8 (range 2–5, variable 5K–10K spacing with clustering near expected values). Fewer strikes = cruder CDF = mechanically higher CRPS. This is a legitimate confound.
- **Feasible**: Yes — data already exists in the experiment outputs.
- **Impact**: High. This is a potential alternative explanation for the main finding that readers will immediately ask about.
- **Action**: Added a "Strike structure note" paragraph after the main CRPS/MAE table reporting strike counts, spacing patterns, and my assessment that ~0.5 fewer strikes is unlikely to fully explain a 32% penalty, especially given the corroborating PIT evidence of directional miscalibration (mean PIT=0.61).

### 4. CRPS decomposition reference / Hersbach (2000) (Should Fix)
- **Agree**: Standard citation that should be included. The CRPS/MAE ratio does collapse reliability/resolution/uncertainty into a single dimension, and forecasting specialists will notice the omission.
- **Feasible**: Yes — citation and framing, no new analysis.
- **Impact**: Medium. Preempts the obvious critique and signals awareness of the broader CRPS literature.
- **Action**: Added Hersbach (2000) reference in the future work paragraph of Section 2, noting that decomposition would clarify which dimension drives the CPI penalty. Added to References section.

### 5. Strengthen SPF caveat (Should Fix)
- **Agree**: The "(annual/12 proxy)" label is indeed easy to miss, and the conversion is genuinely crude — SPF panelists forecast annual Q4/Q4 changes, not monthly rates.
- **Feasible**: Yes — one footnote.
- **Impact**: Medium. The SPF comparison is interesting but the current presentation invites criticism.
- **Action**: Added a dagger (†) to the SPF row and an explicit footnote explaining the conversion assumes uniform monthly contributions, ignores seasonality and base effects, and should be treated as indicative rather than definitive.

### 6. PIT analysis framing — connect to main text (Should Fix)
- **Agree**: Good suggestion. The PIT finding (mean=0.61) directly supports the CRPS/MAE > 1 finding — both point to CPI distributions underestimating inflation. Currently these are disconnected findings in separate sections.
- **Feasible**: Yes — one paragraph in Section 2.
- **Impact**: Medium-high. Creates a coherent narrative thread between Section 2 and Appendix A, strengthening the "miscalibration, not noise" interpretation.
- **Action**: Added a paragraph in Section 2 connecting PIT to CRPS/MAE: mean PIT=0.61 suggests directional miscalibration (underestimating inflation) rather than mere distributional imprecision. Also referenced PIT evidence in the strike structure note as corroboration that the CPI penalty isn't purely a measurement artifact.

### 7. CRPS quantile decomposition as future work (from Seed Question 4a)
- **Partially agree**: The reviewer says this is "feasible now" but I disagree. Our strike data has only 2–3 strikes per CPI event — you cannot meaningfully decompose CRPS into "center vs tails" contributions with 2 strikes. This would require substantially more strike granularity than we have. I've noted CRPS decomposition as future work (via Hersbach) but decline to implement a misleading analysis on insufficient data.
- **Feasible**: No — insufficient strike granularity.
- **Impact**: Would be high if feasible, but producing it with 2–3 strikes would be misleading.
- **Action**: Declined. Noted Hersbach decomposition as priority future work instead.

## Changes Made
1. **Section 2, CRPS/MAE definition**: Rewrote to frame as calibration diagnostic, not mathematical bound. Added parenthetical: "this is a diagnostic property of calibration quality, not a mathematical bound."
2. **Abstract + Section 1**: Changed "comparable" to "directionally comparable" for SPX comparison. Added granularity caveat noting hourly vs daily mismatch and that it likely favors Kalshi.
3. **Section 2, new paragraph**: Added strike structure note with counts (CPI: 2.3 avg, Jobless: 2.8 avg), spacing patterns, and confound assessment.
4. **Section 2, future work**: Added Hersbach (2000) CRPS decomposition as priority future work. Connected PIT finding to CRPS/MAE diagnostic.
5. **Section 3, horse race table**: Added SPF footnote explaining annual/12 conversion ignores seasonality and base effects.
6. **References**: Added Hersbach (2000).
7. **Status line**: Changed from "Accepted for publication" to "Draft — under review" (previous status was stale/premature).

## Pushbacks
- **CRPS quantile decomposition "feasible now"**: Disagree. With 2–3 strikes per CPI event, decomposing CRPS into center vs tail contributions would produce meaningless numbers. The strike granularity is too coarse. I've acknowledged this as future work (via Hersbach decomposition) but decline to implement a misleading analysis. The reviewer's instinct is correct that this would be valuable — it's just not feasible with the current data resolution.

## Remaining Weaknesses
1. **Strike count confound is acknowledged but not quantified.** I argue ~0.5 fewer strikes can't explain a 32% penalty, but I haven't run a simulation to prove this. A synthetic CDF study (2 vs 3 vs 5 strikes, known true distribution, measure CRPS inflation) would be definitive but is new analysis.
2. **Release frequency hypothesis is untestable** with only two series. Inherent limitation.
3. **In-sample evaluation.** No fix possible at n=14–16.
4. **Temporal CRPS evolution table** reports ratios vs uniform without confidence intervals. Not flagged by reviewer but it's a weak spot.
5. **Abstract is dense** — tries to communicate every finding in one paragraph. Could benefit from tightening to focus on the core diagnostic.

## Convergence Assessment
This iteration addressed all "must fix" items and 4 of 5 "should fix" items. The mathematical misstatement — the most critical issue — is resolved. The paper is meaningfully stronger: CRPS/MAE framing is now precise, strike structure confounds are documented, disconnected findings are connected (PIT → CRPS/MAE), and the SPF comparison is properly caveated. I pushed back on one suggestion (CRPS quantile decomposition) with clear reasoning.

I expect the next critique to focus on prose quality, remaining confounds, or issues I haven't anticipated. We are making good progress but not yet converged — the reviewer may identify new structural issues now that the foundation is solid.
