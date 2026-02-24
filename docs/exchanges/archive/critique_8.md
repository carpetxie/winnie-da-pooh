# Critique — Iteration 8

STATUS: CONTINUE

## Overall Assessment

The paper is now a mature, well-documented study with 11 series, 248 events, and thorough robustness checks. The researcher's execution of iteration 7 feedback was complete — overconcentration elevated to abstract, std(PIT) added to PIT table, monitoring backtest run, reproducibility documented, KXFRM counterexample added, pooling and double-counting defenses inserted. The remaining issues are (1) a missing formal test for the paper's most universal claim (overconcentration), (2) monitoring protocol calibration concerns for KXFRM, and (3) minor code hygiene. None are structural; all are fixable with code.

## Data Sufficiency Audit

**No change from iteration 7. Data sufficiency is not the binding constraint.**

- **11 series, 248 events** covers the vast majority of Kalshi's multi-strike economic markets.
- **KXRETAIL and KXACPI** remain unfetched. KXACPI is likely redundant with CPI/KXCPI. KXRETAIL could add one more data point but would not change any conclusion. I am not re-raising this.
- **Per-series power**: GDP CI excludes 1.0 ✅. JC borderline [0.37, 1.02] — only solvable by waiting for new events. FED n=4 genuinely structural.
- **No new series discovered** since the `/series` endpoint scan in iteration 13.

**Assessment: 8/10. The dataset is adequate. Marginal gains from KXRETAIL are not worth the effort at this stage.**

## Reflection on Prior Feedback

### Iteration 7 — all points addressed:
1. ✅ Overconcentration elevated to abstract and takeaways
2. ✅ std(PIT) column added to PIT table (all 11 series)
3. ✅ Reproducibility path documented (5 scripts listed)
4. ✅ KXFRM counterexample added for point-distribution decoupling
5. ✅ Sign test pooling note added
6. ✅ CRPS/MAE double-counting defense added
7. ✅ Monitoring protocol backtest computed for all 11 series
8. ✅ Bid-ask compression listed as overconcentration mechanism

### What I'm dropping:
- All iteration 7 items — fully addressed, no circular feedback.
- KXRETAIL/KXACPI — explicitly deprioritized, not re-raising.
- GDP temporal snapshot sensitivity — researcher reasonably deferred; existing CI [0.31, 0.77] is conclusive.

### Researcher pushbacks accepted:
- No pushbacks in iteration 7. All critique points accepted and implemented.

## Scores

| Criterion | Score | Delta | Comment |
|-----------|-------|-------|---------|
| Data Sufficiency | 8/10 | — | Unchanged. 11 series, 248 events adequate. |
| Novelty | 8.5/10 | +0.5 | Overconcentration elevation and monitoring backtest increase visibility of novel findings. Formal test would push higher. |
| Methodological Rigor | 8/10 | — | Solid overall. Overconcentration claim now elevated to headline but lacks formal statistical test to support that prominence. |
| Economic Significance | 8.5/10 | +0.5 | Monitoring backtest transforms protocol from proposal to validated evidence. |
| Blog Publishability | 8.5/10 | +0.5 | Very close. Items below are final polish. |

## Strength of Claim Assessment

### Claim 1: "9 of 11 series: distributions add value"
**CONCLUSIVE. Correctly labeled.** Sign test p=0.004, LOO unanimity in 8/9. No change needed.

### Claim 2: "GDP is the standout (CI excludes 1.0)"
**CONCLUSIVE. Correctly labeled.** No change needed.

### Claim 3: "Universal overconcentration across all 11 series"
**SUGGESTIVE — needs a trivial formal test to become CONCLUSIVE.** The claim is now elevated to the abstract and takeaways, which is appropriate given the evidence. But the supporting statistics are purely descriptive: "all 11 series show std(PIT) < 0.289." No formal test is reported. This is easy to fix:
- **Sign test**: 11/11 series below 0.289. Binomial p = 0.5^11 ≈ 0.0005. State this.
- **Pooled bootstrap**: Compute std(PIT) on all 248 PIT values; bootstrap a CI. If it excludes 0.289, the claim is population-level conclusive.
- **Per-series bootstrap**: For series with n ≥ 10, report which CIs on std(PIT) individually exclude 0.289.

The claim *deserves* to be conclusive — the evidence supports it — but it needs the statistical infrastructure to match its prominence.

### Claim 4: "Point and distributional calibration can diverge independently"
**SUGGESTIVE. Correctly labeled.** KXFRM counterexample now included. Good.

### Claim 5: "Monitoring protocol detects degradation with low false alarm rate"
**SUGGESTIVE — KXFRM alerts need clarification.** The paper says "6 of 8 testable series produce zero 3-consecutive alerts," which is true. But KXFRM triggers **10** 3-consecutive alerts out of 52 windows despite an aggregate ratio of 0.85. The paper frames this as "detecting temporary degradation even in generally well-calibrated series." A hostile reviewer will compute 10/52 = 19% and question the protocol's specificity. The paper needs to either: (a) identify the specific KXFRM degradation period to show these are true positives, or (b) acknowledge the trade-off between sensitivity (correctly flagging CPI/Core PCE) and specificity (KXFRM false alarms).

### Claim 6: "Simple-vs-complex hypothesis failed OOS"
**CONCLUSIVE. Correctly labeled.** Pre-registration and transparent reporting remain a methodological strength.

## Novelty Assessment

**What's genuinely new (unchanged ranking):**
1. Universal overconcentration across 11 prediction market series — unprecedented scale
2. CRPS/MAE ratio as a per-series prediction market diagnostic
3. Point-distribution decoupling (first demonstration in prediction markets)
4. Pre-registered OOS failure with transparent reporting
5. Cross-series horse race with monitoring backtest

**What would further increase novelty:**
1. **Formal overconcentration test** — transforms the strongest descriptive finding into a formal result
2. **std(PIT) vs CRPS/MAE correlation** — tests whether overconcentration is the *mechanism* behind distributional failure or an independent dimension. A Spearman ρ across 11 series (std(PIT) vs CRPS/MAE ratio) would answer this in one line of code. Either result is publishable: if correlated, overconcentration *explains* CRPS/MAE variation; if uncorrelated, they are independent calibration dimensions.

## Robustness Assessment

### Deep code review (new this iteration)

I conducted a thorough review of `experiment12/distributional_calibration.py` and `experiment13/run.py`. The core methodology (CRPS piecewise integration, ratio-of-means, BCa bootstrap) is sound. Specific findings:

1. **CRPS computation** ✅: Piecewise-linear CDF integration with dynamic tail extension (`tail_extension = max(strike_range * 0.5, 1.0)`). Closed-form integration of squared linear functions via `_integrate_squared_linear()`. Mathematically correct.

2. **Ratio-of-means vs mean-of-ratios** ✅: The code correctly uses ratio-of-means (`mean(CRPS) / mean(MAE)`) for the main result and bootstrap CI. Mean-of-ratios is reported as a diagnostic (median per-event ratio) but not used for inference. This is the right choice — ratio-of-means is robust to near-zero MAE outliers (cf. KXPCECORE-25JUL).

3. **BCa bootstrap** ✅: Paired resampling of (CRPS, MAE) with `scipy.stats.bootstrap`, 10,000 resamples, seeded (42). BCa method handles skewness correctly.

4. **Bootstrap fallback inconsistency (minor)**: The BCa path allows inf/nan via `np.errstate(divide='ignore')`, while the percentile fallback filters `boot_mae > 0`. In practice BCa almost always succeeds, so this rarely matters. Not publication-blocking but worth noting.

5. **Interior-only vs tail-aware point forecast**: The code computes two CRPS/MAE ratios — one using interior-only implied mean, one using tail-aware. Both use the *same* CRPS (from the full piecewise-linear CDF). The interior-only ratio has a conceptual mismatch: the numerator integrates over the full CDF including tails, but the denominator uses only interior probability mass. The tail-aware ratio is theoretically consistent. The paper correctly notes "interior-only" as primary and "tail-aware" as sensitivity, but should clarify which is used in the executive summary table.

6. **Unused variable**: `paired_data = np.column_stack([crps_arr, mae_arr])` is computed but never referenced. Harmless dead code.

### Hostile reviewer attacks (new):

1. **"Overconcentration could be an artifact of discrete strikes."** With only 2-5 strikes per market, the piecewise-linear CDF mechanically has lower variance than a smooth distribution. **Defense available**: The Monte Carlo simulation (Section 4) already shows strike count effects ≤2%. Connect this explicitly to the overconcentration finding: "The observed overconcentration gap (std(PIT) 17-52% below ideal) far exceeds the ≤2% mechanical effect of discrete strikes."

2. **"KXFRM monitoring alerts suggest poor specificity."** 10/52 = 19% alert rate for a well-calibrated series. The paper needs a clear defense.

## The One Big Thing

**Add a formal statistical test for universal overconcentration.**

The paper's most universal finding — all 11 series show std(PIT) < 0.289 — is now appropriately elevated to the abstract and takeaways. But it rests on descriptive evidence alone: "we observe all 11 below 0.289." For a finding of this prominence, it needs formal statistical backing:

1. **Sign test (trivial):** 11/11 series below 0.289 → binomial p = 0.5^11 ≈ 0.0005. One sentence.
2. **Pooled bootstrap:** std(PIT) on all 248 values, bootstrap CI. If CI excludes 0.289, the claim is population-level conclusive.
3. **Per-series bootstrap (optional):** For n ≥ 10 series, report which CIs individually exclude 0.289.

This is ~15 lines of code and transforms the paper's most universal claim from descriptive observation to formal statistical result. Given the claim's prominence (abstract, takeaways, full paragraph in Section 4), the formal test is mandatory.

## Other Issues

### Must Fix (blocks publication)

1. **Formalize the overconcentration test.** Add: (a) binomial sign test: "All 11 series show std(PIT) < 0.289 (binomial p = 0.0005)"; (b) pooled bootstrap CI on std(PIT) for the full 248-event sample; (c) optionally, per-series bootstrap CIs for the 8 series with n ≥ 10. This is ~15 lines of code (`np.std(all_pits)` + `scipy.stats.bootstrap`). Add one sentence to the overconcentration paragraph citing the formal p-value.

### Should Fix (strengthens paper)

1. **Clarify KXFRM monitoring alerts.** Add 1-2 sentences identifying the specific period of elevated KXFRM ratios (which events fall in the 10 alert windows?). If they cluster during a period of mortgage rate volatility, frame as true detection of a genuine degradation period. If they're scattered, acknowledge the specificity trade-off. A hostile reviewer will note 10/52 = 19%.

2. **Connect strike-count Monte Carlo to overconcentration defense.** Add one sentence: "Monte Carlo simulation confirms that the mechanical effect of discrete strikes on distributional variance is ≤2%, far smaller than the observed overconcentration gap (std(PIT) 17-52% below the ideal)." This preempts the "artifact of few strikes" attack.

3. **Clarify which point forecast generates the executive summary MAE.** The methodology note says "interior-only" is primary and "tail-aware" is sensitivity. The horse race (Section 3) uses tail-aware for headline CPI MAE (0.068). The executive summary table presumably uses interior-only. Add a brief footnote to the table specifying this.

4. **std(PIT) vs CRPS/MAE correlation (5 lines of code).** Compute Spearman ρ between std(PIT) and CRPS/MAE ratio across 11 series. This tests whether overconcentration *explains* CRPS/MAE variation (if correlated) or is an independent calibration dimension (if uncorrelated). Either result is novel and interesting. One sentence to report.

### New Experiments / Code to Write

1. **Formal overconcentration test (HIGH PRIORITY, ~15 lines):**
   ```python
   import numpy as np
   from scipy import stats

   # Per-series sign test
   n_below = 11  # all series have std(PIT) < 0.289
   p_sign = 0.5 ** n_below  # = 0.000488

   # Pooled bootstrap
   all_pits = np.concatenate([pits_by_series[s] for s in all_series])  # 248 values
   pooled_std = np.std(all_pits)
   result = stats.bootstrap((all_pits,), np.std, n_resamples=10000,
                             method='BCa', random_state=np.random.default_rng(42))
   ci_lo, ci_hi = result.confidence_interval
   print(f"Pooled std(PIT) = {pooled_std:.3f}, 95% CI [{ci_lo:.3f}, {ci_hi:.3f}]")
   # If ci_hi < 0.289: overconcentration is formally conclusive
   ```

2. **std(PIT) vs CRPS/MAE correlation (LOW PRIORITY, ~5 lines):**
   ```python
   std_pits = [0.266, 0.248, 0.228, 0.227, 0.245, 0.219, 0.227, 0.259, 0.136, 0.212, 0.226]
   ratios =   [0.48,  0.60,  0.67,  0.71,  0.75,  0.82,  0.85,  0.86,  0.97,  1.22,  1.48]
   rho, p = stats.spearmanr(std_pits, ratios)
   print(f"Spearman ρ = {rho:.3f}, p = {p:.3f}")
   ```

3. **KXFRM alert window identification (MEDIUM PRIORITY):**
   From the monitoring backtest, identify which specific KXFRM events fall in the 10 alert windows. Report the date range and whether it coincides with mortgage rate volatility (e.g., Fed rate changes). This transforms the "false alarm" concern into a "true detection" narrative.

### Genuinely Unfixable Limitations

1. **FED n=4.** FOMC meets ~8 times/year; only 4 settled multi-strike events exist. Cannot expand.
2. **No order-book depth data.** Kalshi doesn't expose historical LOB. Cannot directly test bid-ask spread mechanisms for overconcentration.
3. **CPI temporal split underpowered (p=0.18, needs ~95 events).** Only 33 exist.
4. **SPF monthly CPI proxy.** No public monthly CPI point forecast; annual/12 is the best available.
5. **Overconcentration mechanism untestable.** Can speculate (bid-ask, overconfidence, herding) but cannot distinguish without LOB data.

## Verdict

**MINOR REVISIONS**

The paper is close to publication-ready. The single must-fix item (formal overconcentration test) is ~15 lines of code and one additional sentence — the claim is already well-supported descriptively and just needs the statistical infrastructure to match its elevated prominence. The should-fix items are individually small (1-2 sentences each). No structural changes needed. With these changes, the paper would be ready for the Kalshi Research blog.
