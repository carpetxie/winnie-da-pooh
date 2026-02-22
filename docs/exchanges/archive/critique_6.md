# Critique — Iteration 6

STATUS: CONTINUE

## Overall Assessment

The paper has reached a high level of statistical rigor after five iterations — the block bootstrap, scale-free permutation test, and strengthened decoupling framing were all well-executed improvements. However, I've identified a genuine data leakage bug in the random walk benchmark that inflates the baseline and affects the horse race results. Additionally, the paper's narrative arc could benefit from a sharper "so what" for Kalshi as a business — the market design implications are currently buried and underspecified. These are tractable fixes that would meaningfully strengthen what is already a strong paper.

## Reflection on Prior Feedback

My iteration 5 suggestions were largely productive:
- **Scale-free permutation test** (the "one big thing"): Implemented correctly, p=0.016. This was the right call — it eliminates the scale-mixing concern cleanly.
- **Block bootstrap for CPI serial correlation**: The most impactful change. CI [1.06, 2.63] excluding 1.0 upgrades the CPI finding from "strong with caveat" to "conclusive." Excellent execution.
- **MWU/permutation emphasis swap**: Done correctly. MWU now leads.
- **Strengthen decoupling claim**: Adopted nearly verbatim. The "first empirical demonstration" framing is compelling.
- **Temporal robustness in abstract**: Good addition.
- **Cramér-von Mises substitution for Anderson-Darling**: Researcher was right that scipy doesn't support uniform for AD. CvM is a reasonable substitute. Results are consistent with KS (both underpowered). Low impact, as expected.
- **Experiment 8 stationarity assertion**: Deferred with reasonable justification. I won't re-raise this.

No dead-end suggestions from iteration 5. All accepted changes improved the paper.

## Scores
| Criterion | Score | Delta | Comment |
|-----------|-------|-------|---------|
| Novelty | 7/10 | — | Decoupling framing is now prominent and compelling; CRPS/MAE diagnostic remains a genuine contribution |
| Methodological Rigor | 7/10 | -1 | Random walk data leakage bug (see below) downgrades from 8; otherwise the statistical architecture is excellent |
| Economic Significance | 7/10 | — | Market design implications still underspecified |
| Narrative Clarity | 7/10 | — | Dense but well-structured; abstract is tighter |
| Blog Publishability | 7/10 | — | Data leakage fix is needed before publication; otherwise close |

## Strength of Claim Assessment

**Claim 1: JC distributions robustly add value (CRPS/MAE=0.66)**
- Evidence level: **Conclusive**. Paper labels correctly. No change needed.

**Claim 2: CPI distributions are harmful (CRPS/MAE=1.58, block bootstrap CI [1.06, 2.63])**
- Evidence level: **Conclusive** (upgraded from prior iteration thanks to block bootstrap). Five converging diagnostics are compelling. Paper labels correctly.

**Claim 3: CPI–JC divergence is statistically significant**
- Evidence level: **Conclusive**. Three independent tests (MWU tail-aware p=0.003, MWU interior p=0.026, scale-free permutation p=0.016) all converge. Paper structure is now correct (MWU leads, permutation confirms).

**Claim 4: CPI point forecast beats random walk (d=−0.71, p_adj=0.059)**
- Evidence level: **Compromised by data leakage bug** (see Robustness section). The random walk baseline is inflated for the first event (KXCPI-24NOV). After correction, the random walk MAE will increase, making the Kalshi advantage *larger*. So the direction of the finding is safe — if anything, the claim should be *stronger* after the fix — but the current numbers are wrong. The claim should be re-stated with corrected values.

**Claim 5: TIPS Granger-causes Kalshi CPI**
- Evidence level: **Suggestive**. Paper hedges appropriately. No change needed.

**Claim 6: Point-vs-distribution decoupling is novel**
- Evidence level: **Strong**. The "first empirical demonstration" framing is now well-supported and appropriately prominent.

## Novelty Assessment

The paper's novelty portfolio is well-established at this point:
1. **CRPS/MAE ratio as diagnostic** — genuine methodological contribution
2. **Point-vs-distribution decoupling** — the paper's most memorable finding
3. **Series-level heterogeneity** — important for market design

**Underemphasized opportunity**: The paper mentions "real-time CRPS/MAE monitoring" as a market design implication but doesn't flesh this out. Given that this is targeting the Kalshi Research blog, a concrete proposal — e.g., "Kalshi could publish a distributional quality dashboard per series, analogous to how exchanges publish implied volatility metrics" — would make the paper more actionable and differentiated. This is a 2-sentence addition, not a major restructuring, but it would resonate with Kalshi's audience (market designers and sophisticated traders).

## Robustness Assessment

### Code Bug: Random Walk Data Leakage (experiment13/horse_race.py, line 183)

**This is a genuine bug, not a design choice.** The `get_random_walk_forecast()` function handles the first event (KXCPI-24NOV) with:

```python
if idx == 0:
    # For the first event, use Nov 2024 CPI MoM (0.3%) from BLS data
    return 0.3
```

But KXCPI-24NOV **is** the November 2024 CPI event, with realized value 0.3%. The random walk forecast for November 2024 should use **October 2024's** realized CPI MoM, which was **0.2%** (BLS CPI-U SA, released November 13, 2024). Using 0.3% means:

- The random walk gets MAE=0.0 on this event (perfect score by data leakage)
- The correct MAE should be |0.2 - 0.3| = 0.1
- This inflates the random walk baseline, making Kalshi look *relatively worse*
- The bias is *conservative* (hurts the paper's claim), so the direction of all horse race results is safe
- But the specific numbers (d=−0.71, p_adj=0.059) will change after correction

**Fix**: Change line 183 from `return 0.3` to `return 0.2` (October 2024 BLS CPI-U MoM SA = 0.2%). Update the comment accordingly. Re-run the horse race.

**Impact estimate**: The random walk's mean MAE will increase from 0.143 to approximately 0.150 (adding 0.1/14 ≈ 0.007 to the mean). This will *increase* Cohen's d and likely push the Bonferroni-adjusted p-value below 0.05. The fix actually *strengthens* the paper's headline claim.

### Code Observation: Trailing Mean Bootstrap Window

The trailing mean forecast uses a growing window that starts with just 1 observation for KXCPI-24DEC and 2 for KXCPI-25JAN. The hardcoded 0.25 for KXCPI-24NOV (described as "2024 average MoM CPI") is also imprecise — the actual 2024 YTD average through October was approximately 0.24% (computed from BLS data). This isn't a bug per se — the trailing mean's disadvantage at small windows is a feature of the benchmark's design — but it's worth noting in the methodology that the trailing mean has an inherent "warm-up" disadvantage for the first several events.

### Block Bootstrap Verification

Verified the block bootstrap implementation (experiment13/run.py, lines 1229-1254). The circular block bootstrap with block_len=2 is correctly implemented: random start positions, modular indexing for circularity, ratio-of-means statistic. The result CI [1.06, 2.63] is consistent with the standard BCa CI [1.04, 2.52] — slightly wider lower bound (as expected with serial correlation adjustment), confirming the approach is working correctly. No issues found.

### Scale-Free Permutation Test Verification

Verified (lines 703-717). Interior-only per-event ratios are used, which are dimensionless and stable. The implementation is clean. p=0.016 is consistent with MWU results. No issues found.

## The One Big Thing

**Fix the random walk data leakage bug (line 183 of horse_race.py: change 0.3 to 0.2) and re-run the horse race.** This is a 1-character code change that fixes a genuine data integrity issue. The correction will likely *strengthen* the horse race results, potentially pushing the Kalshi-vs-random-walk Bonferroni p-value below 0.05. Report the corrected numbers in the paper.

## Other Issues

### Must Fix (blocks publication)

1. **Random walk data leakage**: Change `return 0.3` to `return 0.2` in `get_random_walk_forecast()` for `idx == 0`. Re-run horse race. Update all affected numbers in the paper (random walk mean MAE, Cohen's d, raw and Bonferroni p-values). Also update the comment from "Nov 2024 CPI MoM (0.3%)" to "Oct 2024 CPI MoM (0.2%)."

### Should Fix (strengthens paper)

1. **Note the trailing mean warm-up issue**: Add one sentence to the horse race methodology noting that the trailing mean uses an expanding window. Suggested text: "*The trailing mean uses an expanding window (1 observation for the second event, growing to 12), giving it an inherent warm-up disadvantage for early events.*"

2. **Make market design implications more concrete**: The "Market design implications" paragraph in Section 2 lists three levers (strike density, liquidity incentives, real-time monitoring) but doesn't commit to specifics. For a Kalshi Research blog post, add one concrete sentence: e.g., "Adding strikes at the 25th and 75th percentiles of the historical CPI distribution (approximately ±0.15pp from the expected value) would increase CPI strike density from 2–3 to 4–5, matching the Jobless Claims structure that produces CRPS/MAE < 1." This transforms a vague recommendation into an actionable, testable proposal.

3. **Clarify the temporal CI bootstrap method discrepancy**: The paper notes "Temporal CIs use the percentile bootstrap method rather than BCa" but doesn't explain why. Add a brief parenthetical: "(percentile method used because BCa can be numerically unstable at the smaller per-timepoint sample sizes)."

### New Experiments / Code to Write

1. **Corrected horse race** (~1 min): Fix the random walk first-event value from 0.3 to 0.2 in `experiment13/horse_race.py`, line 183. Re-run `uv run python -m experiment13.run`. Report new horse race statistics. Expected: random walk MAE increases, Kalshi advantage grows, d and p improve.

2. **Sensitivity check: exclude first event entirely** (~5 lines): As a belt-and-suspenders robustness check for the horse race, run all four benchmark comparisons excluding KXCPI-24NOV (n=13 instead of n=14). This eliminates any concern about the hardcoded first-event forecasts for both random walk and trailing mean. If the Kalshi advantage persists at n=13, it's bulletproof.
   ```python
   # In horse_race.py run_cpi_horse_race(), after computing results_df:
   results_excl = results_df[results_df["event_ticker"] != _TICKER_ORDER[0]]
   for naive_col, label in [...]:
       valid = results_excl.dropna(subset=["kalshi_point_mae", naive_col])
       stat, p = stats.wilcoxon(valid["kalshi_point_mae"], valid[naive_col], alternative="less")
       # Store as sensitivity results
   ```
   Report in the paper as: "Excluding the first event (which requires hardcoded benchmarks) does not change the result (n=13, d=X, p=Y)."

3. **Interior-only horse race sensitivity note** (prose only): The paper reports the tail-aware horse race as primary. Add a one-line note with the interior-only results (MAE=0.082 vs random walk MAE≈0.150) as a sensitivity check demonstrating the advantage holds regardless of mean specification.

### Acknowledged Limitations (inherent, not actionable)

1. **Two series only**: Inherent to current Kalshi multi-strike offerings.
2. **Small n per series**: n=14 CPI, n=16 JC. Cannot be fixed without waiting for more data.
3. **In-sample only**: Cannot cross-validate at current n.
4. **Untestable mechanisms**: The four hypothesized mechanisms cannot be directly tested with public data.
5. **Hardcoded realized values**: Standard practice at n=14 but introduces transcription risk.

## Verdict

**MINOR REVISIONS**

The paper is close to blog-publishable. The random walk data leakage is the only genuine blocker — it's a 1-character fix that will likely *strengthen* the results, but the current numbers are technically wrong and must be corrected before publication. The irony is that fixing this bug makes the paper's claims *stronger*, not weaker. The other suggestions (trailing mean warm-up note, concrete market design recommendation, temporal CI explanation) are polish that would improve the paper's credibility and actionability for the Kalshi Research blog audience. After the random walk fix and number update, this paper is ready for a final polish pass.
