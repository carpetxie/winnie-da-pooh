# Critique — Iteration 9

STATUS: CONTINUE

## Overall Assessment

The paper is mature, methodologically rigorous, and nearly publication-ready for the Kalshi Research blog. The iteration 8 improvements — formal overconcentration tests, std(PIT) vs CRPS/MAE correlation, KXFRM alert period identification — were all well-executed and close the major open items. Remaining issues are: (1) the overconcentration-performance correlation is elevated to the abstract but rests on n=11 series-level observations when a far more powerful per-event version is computable from existing data, (2) a novelty framing issue ("we introduce" vs prior art in weather forecasting), and (3) minor rhetorical strengthening around CI non-exclusion.

## Data Sufficiency Audit

**No change from iteration 8. Data sufficiency is not the binding constraint (8/10).**

- **11 series, 248 events** covers the vast majority of Kalshi's multi-strike economic markets.
- KXRETAIL and KXACPI remain unfetched but are explicitly deprioritized — not re-raising.
- Remaining small-n issues (FED n=4, CPI temporal split n=33) are genuinely structural.
- **One note:** The std(PIT) vs CRPS/MAE correlation (ρ=−0.68, p=0.022) is computed at the *series* level (n=11). This is NOT a data sufficiency problem in the traditional sense — the researcher has 248 per-event PIT values and 248 per-event CRPS/MAE ratios already computed. A per-event analysis would provide dramatically more statistical power and is trivially computable from existing data. See "The One Big Thing."

## Reflection on Prior Feedback

### Iteration 8 — all points addressed:
1. ✅ Formal overconcentration test (sign test p=0.0005, pooled bootstrap CI [0.225, 0.257])
2. ✅ KXFRM alert period identified (March–Nov 2023, true positive)
3. ✅ Strike-count Monte Carlo connected to overconcentration defense
4. ✅ Executive summary MAE footnote added
5. ✅ std(PIT) vs CRPS/MAE correlation computed (ρ=−0.68, p=0.022)

### What I'm dropping:
- All iteration 8 items — fully addressed.
- KXRETAIL/KXACPI — settled, not re-raising.
- Code review items from iteration 8 (ratio-of-means documented, bootstrap fallback noted) — all minor and acknowledged.

### Researcher pushbacks:
- None in iteration 8. All points accepted and implemented.

## Scores

| Criterion | Score | Delta | Comment |
|-----------|-------|-------|---------|
| Data Sufficiency | 8/10 | — | Unchanged. 11 series, 248 events adequate. Per-event correlation is a power issue, not a data gap. |
| Novelty | 8.5/10 | — | Overconcentration-performance correlation is genuinely novel. Per-event version and framing fix could push to 9. |
| Methodological Rigor | 8.5/10 | +0.5 | Formal overconcentration tests, KXFRM alert validation close prior gaps. Minor framing issues remain. |
| Economic Significance | 8.5/10 | — | Monitoring protocol validated. Market design implications concrete. |
| Blog Publishability | 8.5/10 | — | Very close. Items below are final polish. |

## Strength of Claim Assessment

### Claim 1: "9 of 11 series: distributions add value"
**CONCLUSIVE. Correctly labeled.** Sign test p=0.004, LOO unanimity 8/9. No change needed.

### Claim 2: "GDP is the standout (CI excludes 1.0)"
**CONCLUSIVE. Correctly labeled.** BCa CI [0.31, 0.77].

### Claim 3: "Universal overconcentration"
**CONCLUSIVE. Now properly formalized.** Sign test p=0.0005, pooled CI excludes 0.289. This was the iteration 8 must-fix and it's well-executed. No change needed.

### Claim 4: "More overconcentrated series have better distributional performance (ρ=−0.68, p=0.022)"
**SUGGESTIVE — and slightly overpromoted for n=11.** The correlation is elevated to both the abstract and practical takeaways. With only 11 data points, the confidence interval on ρ is very wide. The p=0.022 is significant but fragile — remove one outlier series and it could lose significance. The paper acknowledges "11 data points" in the researcher response but not prominently in the paper text itself.

**Critical point:** This claim can be dramatically strengthened using existing data. The researcher has 248 per-event PIT values and 248 per-event CRPS/MAE ratios. A per-event analysis (|PIT − 0.5| vs per-event CRPS/MAE) would either confirm the finding at n=248 or reveal it as a Simpson's paradox. See "The One Big Thing."

### Claim 5: "Point and distributional calibration can diverge independently"
**SUGGESTIVE. Correctly labeled.** CPI + KXFRM counterexample is well-presented.

### Claim 6: "Monitoring protocol detects degradation with low false-alarm rate"
**CONCLUSIVE for well-calibrated series (6/8 zero alerts). SUGGESTIVE overall.** The KXFRM alert period identification was well-executed — framing as true positive during mortgage rate volatility is convincing.

### Claim 7 (NEW): "We introduce the CRPS/MAE ratio"
**OVERSTATED.** The CRPS/MAE ratio (or closely related CRPS skill scores normalized by MAE-type baselines) has precedent in weather/climate forecast verification literature. The novelty is *applying it to prediction markets as a per-series monitoring diagnostic*, not inventing the ratio itself. See Must Fix #1.

## Novelty Assessment

**What's genuinely new:**
1. CRPS/MAE ratio *applied to prediction markets* as a per-series monitoring diagnostic — core contribution
2. Universal overconcentration across 11 prediction market series with formal tests — unprecedented scale
3. Overconcentration-performance paradox (ρ=−0.68) — genuinely surprising if confirmed at per-event level
4. Point-distribution decoupling — first demonstration in prediction markets
5. Pre-registered OOS failure with transparent reporting — rare methodological honesty
6. Monitoring protocol with validated backtest — directly actionable for Kalshi

**What would increase novelty:**
1. **Per-event overconcentration-performance analysis** — transforms the most surprising finding from suggestive (n=11) to conclusive (n=248), or reveals important ecological vs individual-level divergence
2. **Bootstrap CI on ρ=−0.68** — honestly communicates the precision of the series-level estimate

## Robustness Assessment

### Code review
Thorough review of `scripts/iteration8_analyses.py`, `scripts/expanded_crps_analysis.py`, and `experiment13/run.py` via subagent confirms:
- All statistical tests correctly implemented (sign test, bootstrap, Wilcoxon, rank-biserial, Bonferroni)
- CRPS piecewise-linear integration mathematically correct
- Ratio-of-means (not mean-of-ratios) used appropriately for main results
- BCa bootstrap with percentile fallback properly handles edge cases

**One minor code note:** Hard-coded std(PIT) values from iteration 7 in `iteration8_analyses.py` (lines ~227-239) could diverge if upstream data changes. Low risk since those values are frozen, but worth noting in the reproducibility documentation.

### Hostile reviewer attacks

1. **"Only 1 of 11 CIs excludes 1.0 — how can you claim distributions 'add value' for 9 series?"** This is the paper's biggest rhetorical vulnerability. The defense is sound (LOO unanimity + per-event sign test), but a sentence explicitly connecting CI width to sample sizes would preempt it: "With n=9–59 per series, BCa CIs for ratio-of-means statistics are expected to be wide; the convergent evidence from LOO unanimity (8/9 series) and the per-event sign test (p=0.004) provides robustness beyond any single CI."

2. **"The overconcentration-performance correlation has n=11."** Legitimate. Per-event analysis would defuse this completely.

3. **"CRPS/MAE isn't new — weather forecasting uses it."** The abstract says "we introduce." A knowledgeable reviewer will flag this. Easy fix: "we apply" or "we adapt" with a brief acknowledgment.

## The One Big Thing

**Run the overconcentration-performance correlation at the per-event level (n=248 instead of n=11).**

The current ρ=−0.68 (p=0.022) is computed across 11 series-level means. But the researcher already has 248 per-event PIT values and 248 per-event CRPS/MAE ratios. The per-event analysis would:

1. Compute **|PIT_i − 0.5|** for each event (per-event proxy for miscalibration/distance from ideal center)
2. Correlate with **per-event CRPS/MAE ratio** via Spearman ρ

This is ~5 lines of code using existing data. It transforms the finding from "suggestive with n=11 series" to either:
- **Confirmed at n=248** → the paradox is robust and the finding becomes one of the paper's strongest contributions
- **Not confirmed** → ecological fallacy / Simpson's paradox, which is itself informative and should be reported

The series-level correlation could be driven by between-series confounds (different data types, different participant bases). The per-event version tests whether the relationship holds *within* series and *across* individual events.

**Important nuance:** |PIT − 0.5| is a per-event proxy for calibration deviation, not directly for overconcentration (which is a distributional property requiring multiple observations). The per-event and series-level correlations may legitimately differ — **report both and discuss**. If they agree, the finding is robust. If they diverge, the divergence is itself a novel finding about ecological vs individual-level prediction market calibration.

```python
# ~10 lines in scripts/iteration9_analyses.py
import numpy as np
from scipy import stats

# Load per-event data (already computed)
pit_deviation = np.abs(all_event_pits - 0.5)  # 248 values
per_event_ratios = all_per_event_crps_mae      # 248 values

# Overall per-event correlation
rho_event, p_event = stats.spearmanr(pit_deviation, per_event_ratios)

# Within-series: partial correlation controlling for series identity
# (e.g., compute rank residuals after regressing on series dummies)
```

## Other Issues

### Must Fix (blocks publication)

1. **Soften "we introduce" in the abstract.** The CRPS/MAE ratio concept has precedent in weather/climate forecast verification (CRPS skill scores, CRPS decompositions relative to MAE-type baselines). The novelty is applying it *to prediction markets as a per-series monitoring diagnostic*, not inventing the ratio. Change "We introduce the CRPS/MAE ratio" to something like "We apply the CRPS/MAE ratio as a diagnostic for prediction market distributional forecasts" and add a brief clause acknowledging the weather forecasting context ("adapted from forecast verification methods"). A reviewer who knows Gneiting & Raftery (2007), Hersbach (2000), or the CRPS decomposition literature will flag "we introduce" immediately.

### Should Fix (strengthens paper)

1. **Run per-event overconcentration-performance correlation.** See "The One Big Thing" above. ~10 lines of code using existing data. Transforms the paper's newest and most surprising finding from suggestive to conclusive (or reveals a Simpson's paradox, which is equally valuable to report).

2. **Add a sentence on CI non-exclusion vs convergent evidence.** 10 of 11 CIs include 1.0. The defense (LOO + sign test) is already in the paper but could be more prominent. One sentence in the "Headline Finding" subsection: "Wide CIs are expected at these sample sizes (n=9–59); LOO unanimity and the per-event sign test provide convergent robustness evidence independent of distributional assumptions."

3. **Report a bootstrap CI on ρ=−0.68.** With n=11, the point estimate is interesting but uncertainty is large. A bootstrap CI (or Fisher z-transform CI) would honestly communicate precision. If the CI is ~[−0.9, −0.1], the finding is robust at the series level even before per-event analysis. If it spans zero, the paper should downweight the claim. ~5 lines of code.

4. **Add n=11 caveat to paper text for the ρ=−0.68 finding.** The abstract and takeaways report the correlation without noting the sample size. The researcher's response notes this as a remaining weakness, but it should appear in the paper itself — a parenthetical "(n=11 series)" in the abstract would suffice.

### New Experiments / Code to Write

1. **Per-event overconcentration-performance analysis (HIGH PRIORITY, ~10 lines):**
   ```python
   # In scripts/iteration9_analyses.py
   pit_deviation = np.abs(all_pits - 0.5)  # 248 values
   rho_event, p_event = stats.spearmanr(pit_deviation, per_event_ratios)
   print(f"Per-event: ρ={rho_event:.3f}, p={p_event:.4f}")

   # Within-series partial correlation
   from scipy.stats import rankdata
   # Rank-transform, regress on series dummies, correlate residuals
   ```

2. **Bootstrap CI on series-level ρ (LOW PRIORITY, ~5 lines):**
   ```python
   std_pits = np.array([0.266, 0.248, 0.228, 0.227, 0.245, 0.219, 0.227, 0.259, 0.136, 0.212, 0.226])
   ratios = np.array([0.48, 0.60, 0.67, 0.71, 0.75, 0.82, 0.85, 0.86, 0.97, 1.22, 1.48])
   boot_rhos = []
   rng = np.random.default_rng(42)
   for _ in range(10000):
       idx = rng.integers(0, 11, 11)
       r, _ = stats.spearmanr(std_pits[idx], ratios[idx])
       boot_rhos.append(r)
   ci = np.percentile(boot_rhos, [2.5, 97.5])
   print(f"Series-level ρ=−0.68, 95% bootstrap CI [{ci[0]:.2f}, {ci[1]:.2f}]")
   ```

3. **No new data fetching needed.** All proposed analyses use existing computed data.

### Genuinely Unfixable Limitations

1. **FED n=4.** FOMC meets ~8 times/year; only 4 settled multi-strike events exist. Cannot expand without waiting.
2. **CPI temporal split underpowered (p=0.18).** Only 33 events exist; ~95 needed for 80% power.
3. **No order-book depth data.** Kalshi doesn't expose historical LOB. Cannot distinguish overconcentration mechanisms (bid-ask compression vs overconfidence) without it.
4. **SPF monthly CPI proxy.** No public monthly CPI point forecast exists; annual/12 is the best available.
5. **Per-event |PIT − 0.5| is a proxy, not direct overconcentration.** Overconcentration is a distributional property requiring multiple observations. The per-event analysis tests a related but distinct hypothesis. The series-level and per-event analyses complement each other but need not agree.

## Verdict

**MINOR REVISIONS**

The paper is close to publication-ready. The must-fix item ("we introduce" → "we apply/adapt") is essentially a one-sentence change. The highest-value should-fix (per-event correlation) is ~10 lines of code using existing data and would either cement or correct the paper's most surprising finding. No structural changes needed. With these changes, the paper would be ready for the Kalshi Research blog.
