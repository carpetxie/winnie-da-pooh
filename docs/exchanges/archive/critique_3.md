# Critique — Iteration 3

STATUS: CONTINUE

## Overall Assessment

The paper has improved substantially since iteration 1: expanding from 2 series (30 events) to 4 series (62 events), adding the volume-CRPS null result, rolling CRPS/MAE, OOS validation, multivariate regression, persistence test, and full 4-series PIT diagnostics. The researcher responded to every critique point constructively. However, I have identified a **high-severity code bug** in the bootstrap CI computation that likely invalidates the claimed "BCa" confidence intervals — the paper is actually reporting percentile bootstrap CIs while claiming BCa. Additionally, the surprise-CRPS/MAE correlation (ρ=−0.65) is partly a mechanical denominator artifact that needs explicit acknowledgment.

## Data Sufficiency Audit

### What's been done (good)
The researcher expanded from 2 to 4 series and from 30 to 62 events. Old/new prefix merging is correctly implemented. The cached targeted_markets.json is now fully exploited for economic series — all 4 canonical series (CPI, JC, GDP, FED) are included.

### What remains
The targeted_markets.json contains only series that were fetched at some earlier point. **Has anyone queried the Kalshi `/series` endpoint to discover what other multi-strike economic series exist?** The API client (`kalshi/client.py`) supports `get_all_pages("/series", result_key="series")` — this is a zero-cost query that would reveal whether Kalshi offers:

- **Nonfarm Payrolls** (likely KXNFP or similar)
- **PCE Price Index**
- **Retail Sales**
- **Unemployment Rate**
- **Consumer Confidence**
- **Housing starts / Home Sales**

If even 2-3 of these exist with multi-strike structure and settled events, the paper would jump from 4 to 6-7 series. This would make the Kruskal-Wallis test far more powerful. **This is a 15-minute exploration task.**

### Crypto as contrast
The 5 crypto series (KXBTC, KXBTCD, KXETH, KXETHD, KXSOLD) with ~5,000 markets remain unexplored. The researcher's pushback — that these need different benchmarks — is reasonable for the *horse race* comparison, but **not for the core CRPS/MAE diagnostic**. The CRPS/MAE ratio only requires (1) implied CDF from binary contracts and (2) a realized value. Crypto daily closes are freely available. No FRED needed for the CRPS/MAE ratio itself.

### Assessment
The 4-series economic dataset is reasonable for the core claims but not exhaustive. The #1 priority is no longer raw data expansion — it's the bootstrap bug described below. But discovering additional Kalshi series via the API remains a should-fix.

## Reflection on Prior Feedback

**All iteration 1 and 2 recommendations were addressed:**
- ✅ Expand to 4 series (CPI=33, JC=16, GDP=9, FED=4)
- ✅ Old/new prefix merging with canonical series mapping
- ✅ Kruskal-Wallis replaces Mann-Whitney (H=7.16, p=0.028)
- ✅ Natural temporal OOS split (50% accuracy, honest reporting)
- ✅ Volume-CRPS regression (null: ρ=0.14, p=0.27)
- ✅ Rolling CRPS/MAE for CPI (structural break clearly visible)
- ✅ Multivariate regression (R²=0.27, surprise dominates)
- ✅ Persistence test (zero autocorrelation)
- ✅ Full 4-series PIT diagnostic
- ✅ TIPS section condensed; point-distribution decoupling promoted

The researcher has been exceptionally responsive. No points from prior critiques need re-raising. All pushbacks were well-reasoned.

## Scores

| Criterion | Score | Delta | Comment |
|-----------|-------|-------|---------|
| Data Sufficiency | 6/10 | +3 | 4 series is a major improvement; further expansion possible via API discovery and crypto |
| Novelty | 8/10 | +1 | CRPS/MAE ratio, point-vs-distribution decoupling, and volume null result are all novel |
| Methodological Rigor | 5/10 | -2 | **Bootstrap bug** means claimed BCa CIs are actually percentile CIs; surprise regression is endogenous |
| Economic Significance | 7/10 | +1 | Volume null result is directly actionable for market design; per-series monitoring is practical |
| Blog Publishability | 6/10 | +1 | Strong concept, good presentation, but the bootstrap issue must be fixed first |

## Strength of Claim Assessment

### Claim 1: "GDP distributions robustly add value (CRPS/MAE=0.48, CI [0.38, 0.58])"
**Assessment: Conclusive IF bootstrap CIs are correct.** LOO unanimous, CI excludes 1.0, n=9 but tight spread. However, if the CIs are actually percentile rather than BCa (see bug below), they may shift. At this effect size the conclusion likely survives, but must be verified. **Appropriately stated.**

### Claim 2: "Jobless Claims distributions add value (CRPS/MAE=0.60, CI [0.45, 0.78])"
**Assessment: Conclusive IF CIs are correct.** Same bootstrap caveat. LOO unanimous, n=16. **Appropriately stated.**

### Claim 3: "CPI overall ratio=0.86, with structural break"
**Assessment: Suggestive — appropriately hedged.** CI includes 1.0 ([0.62, 1.23]), temporal split p=0.18. The paper correctly frames this as "distributions add value overall, but quality is time-varying." One improvement: state more clearly that the *majority* of CPI events (20/33, 61%) have per-event ratios < 1.0. **Well-stated.**

### Claim 4: "Heterogeneity is statistically significant (KW p=0.028)"
**Assessment: Conclusive at the omnibus level.** The Kruskal-Wallis test is appropriate and significant. But the pairwise Mann-Whitney tests (Section 2) lack Bonferroni correction — with 3 tests, the corrected threshold is 0.017, making CPI vs GDP borderline (p=0.020). **The KW result should be stated more confidently; the pairwise results need correction.**

### Claim 5: "Point and distributional calibration can diverge independently"
**Assessment: Strong conceptual contribution, suggestive evidence.** Evidence is confined to CPI post-Nov 2024 (n=14). Pre-Nov 2024 CPI shows both good point AND good distributional forecasts, so decoupling is regime-specific. **Could be promoted more.**

### Claim 6: "Surprise magnitude is the strongest predictor of CRPS/MAE (ρ=−0.65)"
**Assessment: Mechanically inflated — needs restatement.** The surprise variable (|implied mean − realized|) is the MAE, which appears in the denominator of CRPS/MAE. When MAE is large, the ratio is mechanically small. The correlation is partly tautological. **Currently overstated.** The paper should either (a) regress CRPS (not the ratio) on surprise, or (b) explicitly flag the mechanical component. See robustness section below.

## Novelty Assessment

**Genuinely novel:**
1. CRPS/MAE ratio as a practical diagnostic — simple, interpretable, actionable
2. Point-vs-distribution decoupling in prediction markets — first empirical demonstration
3. Volume null result for distributional quality — informative and counter-intuitive
4. Rolling CRPS/MAE as real-time monitoring tool — directly implementable
5. Appendix B's transparency about invalidated findings — sets a standard

**New analyses to increase novelty:**
1. **Surprise-adjusted heterogeneity**: Since surprise mechanically affects the ratio, compute the residual CRPS/MAE after regressing out surprise, then re-test cross-series heterogeneity. This would be a much cleaner test.
2. **Crypto contrast case**: CRPS/MAE for KXBTCD using realized crypto prices. Tests generalizability beyond macro.

## Robustness Assessment

### CRITICAL BUG: Bootstrap CIs are percentile, not BCa

**The `_ratio_of_means` function signature is incompatible with `scipy.stats.bootstrap`'s calling convention.**

In `experiment13/run.py` (line 430) and `scripts/expanded_crps_analysis.py` (line 172):
```python
def _ratio_of_means(data, axis=None):
    if axis is not None:
        crps_means = np.mean(data[0], axis=axis)
        mae_means = np.mean(data[1], axis=axis)
```

When `scipy.stats.bootstrap((crps_arr, mae_arr), statistic=_ratio_of_means)` is called, scipy unpacks the data tuple and calls: `_ratio_of_means(crps_resampled, mae_resampled, axis=-1)`. This maps `data=crps_resampled` and then `axis` receives TWO values — `mae_resampled` (as second positional arg) and `-1` (as keyword) — causing `TypeError: got multiple values for argument 'axis'`.

This error is silently caught by the `except Exception` block, which falls back to a simple percentile bootstrap:
```python
except Exception:
    # Fallback to percentile bootstrap if BCa fails
    ...
    ci_lo = float(np.percentile(boot_ratios, 2.5))
    ci_hi = float(np.percentile(boot_ratios, 97.5))
```

**Consequence:** The paper states "BCa (bias-corrected and accelerated) method via `scipy.stats.bootstrap`" (Section 2 footnote, Methodology section) but is actually computing simple percentile CIs. For ratio estimators at small n (especially GDP n=9, FED n=4), BCa correction adjusts for bias and skewness — the correction can shift CI bounds by 5-15%.

**Fix:** Change the function signature to accept unpacked arguments:
```python
def _ratio_of_means(crps, mae, axis=None):
    crps_means = np.mean(crps, axis=axis)
    mae_means = np.mean(mae, axis=axis)
    with np.errstate(divide='ignore', invalid='ignore'):
        return crps_means / mae_means
```

Apply in three places: `experiment13/run.py` (lines 430 and 506) and `scripts/expanded_crps_analysis.py` (line 172). Then re-run to get true BCa CIs and verify the reported bounds still hold.

### Surprise regression endogeneity (medium severity)

The multivariate regression (CRPS/MAE ~ surprise_z + ..., R²=0.27) and Spearman correlation (ρ=−0.65) are partly mechanical. `surprise_z` derives from `mae_interior = |implied_mean - realized|`, which is the denominator of the dependent variable. When MAE is large, CRPS/MAE is mechanically small. The paper acknowledges this obliquely ("when the point forecast is wrong by a large amount...even modestly calibrated spread helps") but should flag the mechanical component explicitly.

**Fix:** Run a supplementary Spearman correlation of raw CRPS (not the ratio) on surprise magnitude. If CRPS doesn't decrease with surprise, the entire ρ=−0.65 finding is a denominator artifact. If CRPS also decreases, there is genuine economic content.

### Historical CRPS benchmark data leakage (low severity)

In `experiment12/distributional_calibration.py`, the FRED historical window (e.g., `2020-01-01` to `2026-06-01` for CPI) overlaps with the events being scored. Each event's realized CPI value is included in the historical distribution used as its benchmark. For CPI this is ~1 value in ~72 months — negligible, but should be noted.

### Pairwise Mann-Whitney corrections missing

Section 2 reports 3 pairwise Mann-Whitney tests but applies no Bonferroni correction. With 3 tests, corrected α=0.017; CPI vs GDP at p=0.020 becomes borderline. This doesn't weaken the Kruskal-Wallis omnibus result (p=0.028), which is the primary test, but the pairwise tests should note the correction.

### Serial-correlation-adjusted CI not propagated

The serial-correlation-adjusted CI width is computed (Phase 7, experiment13/run.py) but only printed — it doesn't replace the primary CI in the output. The paper mentions serial correlation (Appendix F, item 10) but the reported CPI CI [0.62, 1.23] is the unadjusted version. With AR(1) ρ=0.23 and n_eff≈8.8, the adjusted CI would be approximately [0.55, 1.31].

### Dead code

`expanded_crps_analysis.py` line 178: `return result` is unreachable (the `with` block returns on line 177) and `result` is undefined. Harmless but messy.

## The One Big Thing

**Fix the bootstrap function signature bug.** The paper's headline claims — that GDP and JC CIs exclude 1.0, that CPI's CI includes 1.0 — are all based on confidence intervals labeled as BCa but actually computed via simple percentile bootstrap. For GDP (n=9) and FED (n=4), the BCa correction for ratio estimators can shift bounds meaningfully. The fix is a 3-line code change in 3 files, followed by a re-run. This must be done before any other work.

## Other Issues

### Must Fix (blocks publication)

1. **Fix `_ratio_of_means` function signature** in `experiment13/run.py` (lines 430, 506) and `scripts/expanded_crps_analysis.py` (line 172). Change `def _ratio_of_means(data, axis=None)` to `def _ratio_of_means(crps, mae, axis=None)` and update `data[0]`/`data[1]` to `crps`/`mae`. Re-run all analyses. Update paper if CIs change. Either confirm BCa is now working or explicitly state percentile bootstrap in the paper.

2. **Flag the mechanical component in the surprise-CRPS/MAE correlation.** Add a supplementary CRPS-on-surprise regression (not the ratio) to separate the denominator effect from genuine economic content. If the raw-CRPS correlation is near zero, restate the finding as "the CRPS/MAE ratio mechanically favors high-surprise events because MAE is large."

3. **Apply Bonferroni correction to pairwise Mann-Whitney tests** in Section 2. Note that only the KW omnibus test (p=0.028) is the primary result; pairwise comparisons are exploratory.

### Should Fix (strengthens paper)

1. **Query the Kalshi `/series` endpoint** to discover additional multi-strike economic series. Run: `client.get_all_pages("/series", result_key="series")` and filter for economic-sounding series. If nonfarm payrolls, PCE, retail sales, etc. exist with settled multi-strike markets, fetch and analyze them.

2. **Add crypto CRPS/MAE as supplementary analysis.** KXBTCD has ~1,000 markets across 14 events. Realized daily BTC closes are freely available. No FRED benchmark needed for the ratio. This tests generalizability.

3. **Propagate the serial-correlation-adjusted CI** for CPI to the primary results, or report both standard and adjusted CIs.

4. **Remove dead code** in `expanded_crps_analysis.py` line 178.

### New Experiments / Code to Write

1. **Bootstrap fix** (Must Fix #1): 3-line change × 3 locations, then re-run `scripts/expanded_crps_analysis.py`.

2. **CRPS-on-surprise regression** (Must Fix #2): In `scripts/robustness_analyses.py`, add:
   ```python
   rho_crps_surprise, p_crps_surprise = stats.spearmanr(df["surprise_z"], df["crps"])
   print(f"Raw CRPS vs surprise: rho={rho_crps_surprise:.3f}, p={p_crps_surprise:.3f}")
   ```

3. **API series discovery** (Should Fix #1):
   ```python
   client = KalshiClient()
   all_series = client.get_all_pages("/series", result_key="series")
   for s in all_series:
       title = s.get("title", "").lower()
       if any(kw in title for kw in ["payroll", "retail", "pce", "unemployment", "housing", "confidence", "mortgage", "inflation"]):
           print(s["ticker"], s["title"])
   ```

4. **Crypto CRPS/MAE** (Should Fix #2): Add `"KXBTCD"` to `STRIKE_SERIES`. Fetch BTC daily closes from CoinGecko or similar free API.

### Genuinely Unfixable Limitations

1. **No order book depth data.** Kalshi doesn't expose historical LOB snapshots. Volume is the only liquidity proxy. **Unfixable.**

2. **FED n=4 is structurally constrained.** FOMC meets ~8 times/year; only recent meetings have multi-strike Kalshi markets. **Unfixable in the near term.**

3. **Cannot observe trader composition.** Whether distributional quality depends on trader sophistication is untestable with public data. **Unfixable without Kalshi cooperation.**

## Verdict

**MAJOR REVISIONS.** The bootstrap bug is a blocking issue — the paper's claimed BCa CIs are actually percentile CIs. This is a quick fix (3-line change × 3 files + re-run), but the results may change and all downstream claims depend on these CIs. The surprise regression endogeneity and missing pairwise corrections are lesser but real issues. Once the bootstrap is fixed and CIs verified, this paper is close to publishable — the conceptual framework is strong, the analyses are thorough, and the researcher has demonstrated exceptional responsiveness.
