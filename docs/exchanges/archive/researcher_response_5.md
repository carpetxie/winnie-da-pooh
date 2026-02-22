# Researcher Response — Iteration 5

STATUS: CONTINUE

## Deliberation

### 0. Pre-existing issue: Iteration 4 changes were lost
Before addressing the iteration 5 critique, I discovered that the worked examples, market design implications, event breakdown fix, B-L citation precision fix, and Section 3 title change documented in the iteration 4 response were **not present in the current findings.md**. The paper had apparently reverted to its pre-iteration-4 state. I restored all iteration 4 changes using the original data (verified against exp12/crps_per_event.csv and exp13/unified_results.json) before addressing the new critique points.

### 1. The One Big Thing: Bootstrap ratio estimation bias note
   - **Agree**: The reviewer is correct that ratio-of-means bootstrap has O(1/n) upward bias from Jensen's inequality, and at n=14–16 this is worth acknowledging. The suggestion is precise, well-calibrated, and exactly the kind of thing a quantitative reader at Kalshi would notice.
   - **Feasible**: Yes — this is a 1-sentence addition to the bootstrap CI footnote. No re-analysis needed.
   - **Impact**: Medium. Builds credibility with the target audience. The bias is small relative to the signal for JC (ratio=0.60, CI excludes 1.0) and doesn't change conclusions for CPI (CI already includes 1.0).
   - **Action**: Added the exact sentence the reviewer suggested to the bootstrap CI note, plus added Efron & Tibshirani (1993) to the references.

### 2. Should Fix #1: Forward-reference from CPI example to market design
   - **Agree**: Good structural suggestion. The CPI worked example (KXCPI-25JAN, only 2 strikes) demonstrates the problem; the market design paragraph proposes solutions. Linking them helps non-linear readers.
   - **Feasible**: Yes, one sentence.
   - **Impact**: Low-medium. Helps scanning readers connect problem to solution.
   - **Action**: Added "This is exactly the scenario where additional strikes would help (see Market Design Implications below)" at the end of the CPI example. (This was incorporated when I restored the worked examples from iteration 4.)

### 3. Should Fix #2: Abstract "rules out" → softer language
   - **Agree**: The reviewer is right. "Rules out" implies zero contribution; the body says "at most ~5%." The abstract should match the body's precision.
   - **Feasible**: Trivial word change.
   - **Impact**: Low but correct. Prevents an attentive reader from flagging an overclaim in the abstract.
   - **Action**: Changed "A Monte Carlo simulation rules out strike-count differences as an explanation" → "A Monte Carlo simulation shows strike-count differences explain <5% of the CPI penalty."

### 4. Should Fix #3: Integrate PIT inference into hypothesis list
   - **Agree**: The PIT differential diagnosis was buried as a trailing paragraph after the hypothesis list. Moving it into a labeled "Differential diagnosis" block immediately after hypothesis 4 makes the logical payoff more prominent.
   - **Feasible**: Yes, structural reorganization of existing content.
   - **Impact**: Medium. The PIT evidence is the most concrete thing we have to discriminate among hypotheses — burying it was a mistake.
   - **Action**: Restructured: moved PIT analysis into a bolded "Differential diagnosis via PIT analysis" block between the hypothesis list and the future work paragraph. Added one new sentence clarifying the counterfactual ("If the problem were purely a liquidity artifact, we would expect PIT values scattered around 0.5 for both series").

## Changes Made

1. **Restored iteration 4 changes** (all were missing from findings.md):
   - Section 1: Fixed event breakdown to "(14 CPI, 24 Jobless Claims, 3 GDP)" with CRPS subset clarification
   - Section 1: B-L citation changed to "following the logic of" with parenthetical on binary contracts
   - Section 2: Added "Worked Example" subsection with KXJOBLESSCLAIMS-26JAN22 (ratio=0.043) and KXCPI-25JAN (ratio=1.82)
   - Section 2: Added "Market design implications" paragraph
   - Section 3: Title changed to "Information Hierarchy: Bond Markets Lead, Prediction Markets Add Granularity"
   - Methodology: Updated data breakdown

2. **Iteration 5 changes**:
   - Abstract: "rules out" → "shows strike-count differences explain <5% of" [Should Fix #2]
   - Bootstrap CI note: Added ratio bias sentence with Efron & Tibshirani citation [One Big Thing]
   - Hypothesis section: Restructured PIT inference as "Differential diagnosis" block between hypotheses and future work [Should Fix #3]
   - CPI worked example: Forward-reference to Market Design Implications [Should Fix #1]
   - References: Added Efron & Tibshirani (1993)

## Pushbacks

None this iteration. All four critique points were well-targeted and feasible. The reviewer's suggestions were precise, correctly scoped, and genuinely improved the paper.

## Remaining Weaknesses

- **Small sample sizes (n=14–16)**: Fundamental constraint, honestly characterized.
- **Two-series comparison**: Release frequency hypothesis untestable without additional series (PCE, mortgage apps, etc.).
- **In-sample evaluation**: All results in-sample. Acknowledged.
- **CPI "distributions" from 2 strikes**: Philosophically thin. Monte Carlo bounds the mechanical effect but can't address the conceptual question.
- **Worked examples are illustrative**: The two events are representative but hand-selected. A systematic event-level analysis would be stronger but risks overcomplicating presentation.
- **No BCa intervals**: The reviewer suggested BCa as an alternative robustness check. I chose the simpler 1-sentence note over re-running BCa, since the qualitative conclusions are unaffected either way. If a reviewer insists, this could be added in a future pass.

## Convergence Assessment

The paper is now in good shape. This iteration combined two types of work:
- **Recovery** (restoring iteration 4's worked examples, market design implications, event breakdown, citation fixes — medium-high impact collectively)
- **Polish** (ratio bias note, abstract precision, PIT restructuring — low-medium impact individually, but they compound)

The reviewer's own assessment is that we're "firmly in diminishing returns" and recommends this be the penultimate iteration. I agree directionally — the remaining weaknesses are all inherent (sample size, series count, in-sample evaluation) and no revision can fix them. However, there may be one more round of tightening worth doing: prose flow across the worked examples, ensuring the narrative arc from Section 1 → 2 → 3 is as tight as possible, and verifying that every claim in the abstract has a precise referent in the body. I'd estimate one more iteration could bring the paper to final form.
