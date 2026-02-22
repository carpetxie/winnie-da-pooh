# Researcher Response — Iteration 4

STATUS: CONTINUE

## Deliberation

### 1. The One Big Thing: Economic Translation / Worked Example
   - **Agree**: This is the right call. The paper had a gap between "CRPS/MAE = 0.37" and "what should I do?" The statistical finding was rigorous but lacked a concrete anchor for non-specialist readers.
   - **Feasible**: Yes — the per-event data in exp13 provides CRPS, MAE, implied mean, and realized values for every event. Experiment 7 provides the full implied CDF (strike probabilities). All the ingredients exist.
   - **Impact**: High. This is the single highest-value change for the blog audience.
   - **Action**: Added a "Worked Example" subsection in Section 2 with two contrasting events:
     - KXJOBLESSCLAIMS-26JAN22: implied mean 217.5K, distribution assigned 54% below 215K, realized 200K. CRPS=9,189 vs MAE=17,500 (ratio=0.53). Shows how the distribution captures downside risk the point forecast misses, with a concrete range-contract framing.
     - KXCPI-25JAN: implied mean 0.35%, realized 0.5%, only 2 strikes. CRPS=0.273 vs MAE=0.15 (ratio=1.82). Shows how a coarse distribution actively hurts.
   - Also added a "Market design implications" paragraph connecting CRPS/MAE to actionable levers (more strikes, liquidity incentives, real-time quality monitoring). This addresses the reviewer's suggestion #3 and adds value for Kalshi as an organization.

### 2. Should Fix #1: Clarify "41 events" breakdown
   - **Agree**: The parenthetical "(14 CPI, 16 Jobless Claims, 8 other)" sums to 38, not 41, and is misleading. The actual breakdown from the data is 14 CPI + 24 Jobless Claims + 3 GDP = 41.
   - **Feasible**: Yes, trivial fix.
   - **Impact**: Medium — an attentive reader would stumble on this.
   - **Action**: Changed to "(14 CPI, 24 Jobless Claims, 3 GDP)" in both Section 1 and the Methodology section. Added clarification that CRPS analysis uses the subset with realized outcomes (n=14 CPI, n=16 Jobless Claims) to explain why n=16 appears in the CRPS table despite 24 total Jobless Claims events.

### 3. Should Fix #2: Lead with strong result in trader callout
   - **Partial disagree**: Re-reading the callout, it already leads with the strong result: "Use Jobless Claims distributions — they yield a 63% CRPS improvement over point forecasts alone (CI excludes 1.0)." The CPI caveat comes second. The current structure is fine.
   - **Feasible**: Yes, but unnecessary.
   - **Impact**: Low — the current structure already does what the reviewer asks.
   - **Action**: No change. The callout already leads with the punchline.

### 4. Should Fix #3: Section 3 title undersells results
   - **Agree**: "Context: Information Hierarchy and Point Forecast Comparison" buries the TIPS Granger result, which is genuinely novel.
   - **Feasible**: Trivial.
   - **Impact**: Medium — better framing for a real contribution.
   - **Action**: Changed to "Information Hierarchy: Bond Markets Lead, Prediction Markets Add Granularity." This is assertive without overclaiming — the TIPS result is a lead finding, and Kalshi's multi-strike structure adds granularity that a single breakeven rate cannot.

### 5. Should Fix #4: Breeden-Litzenberger citation precision
   - **Agree**: The reviewer is right that B-L's original method involves differentiating call prices, while binary contracts directly price state-contingent probabilities. The extraction is conceptually related but mechanically trivial.
   - **Feasible**: Trivial.
   - **Impact**: Low-medium — demonstrates methodological awareness.
   - **Action**: Changed to "following the logic of Breeden-Litzenberger (1978)" and added a parenthetical: "(Unlike equity options, where extracting risk-neutral densities requires differentiating call prices with respect to strike, binary contracts directly price state-contingent probabilities, making the extraction straightforward.)"

## Changes Made

1. **Section 2, new subsection "Worked Example: What Does CRPS/MAE < 1 Mean for a Trader?"** — Two contrasting event-level examples (Jobless Claims success, CPI failure) with concrete CRPS vs MAE numbers and range-contract pricing framing.
2. **Section 2, new paragraph "Market design implications"** — Connects CRPS/MAE diagnostic to actionable market design levers (strike count, liquidity incentives, real-time quality monitoring).
3. **Section 1, event breakdown** — Fixed from "(14 CPI, 16 Jobless Claims, 8 other)" to "(14 CPI, 24 Jobless Claims, 3 GDP)" with note clarifying CRPS subset sizes.
4. **Section 1, B-L citation** — Softened to "following the logic of" with parenthetical explaining why binary contracts make extraction trivial.
5. **Section 3 title** — Changed from "Context: Information Hierarchy and Point Forecast Comparison" to "Information Hierarchy: Bond Markets Lead, Prediction Markets Add Granularity."
6. **Methodology, Data section** — Updated event breakdown to match.

## Pushbacks

- **Trader callout restructuring (Should Fix #2)**: The reviewer suggests restructuring the bottom-line box to lead with the strong result. It already does. "Use Jobless Claims distributions — they yield a 63% CRPS improvement" is the opening sentence. The CPI caveat follows naturally. No change needed.

## Remaining Weaknesses

- **Small sample sizes**: n=14–16 remains the fundamental constraint. No revision can fix this.
- **Two-series comparison**: The frequency hypothesis is suggestive but untestable with only CPI and Jobless Claims. Need PCE, mortgage applications, etc.
- **In-sample evaluation**: All results are in-sample. Acknowledged but unfixable at current n.
- **CPI strike coarseness**: 2–3 strikes is barely a "distribution." The Monte Carlo addresses mechanical inflation, but the philosophical question of what distributional information means with 2 strikes remains.
- **Worked example is illustrative, not systematic**: The two events chosen are representative but hand-picked. A systematic analysis of event-level CRPS/MAE distributions would be stronger but risks overcomplicating the presentation.

## Convergence Assessment

This iteration addressed the main presentational gap identified by the reviewer (economic translation). The paper now has:
- Rigorous methodology with appropriate caveats (iterations 1–3)
- Honest confidence intervals and hedged claims (iteration 3)
- Concrete worked examples and market design implications (iteration 4)

The remaining weaknesses are all inherent (sample size, series count, in-sample evaluation). Further iterations could polish prose and transitions, but the marginal value is declining. I expect one more round of minor polish could bring this to final form.
