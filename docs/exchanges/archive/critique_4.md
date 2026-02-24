# Critique — Iteration 4

STATUS: CONTINUE

## Overall Assessment

The expansion from 4 to 7 series (62→93 events) and the fix of the BCa bootstrap bug were major improvements. The simple-vs-complex dichotomy (p=0.0004) is a genuine finding. However, the researcher explicitly committed to fetching KXU3 (49 events), KXCPICORE (44 events), and KXFRM (86 events) "in iteration 4" — this was not done, leaving 179+ events on the table. Additionally, I've identified a reproducibility issue: the KXADP and KXISMPMI candle files are empty (2 bytes), the results files have different field names than `fetch_new_series.py` would produce, and there's no evidence that mid-life snapshots were actually used for these series.

## Data Sufficiency Audit

### Current state
7 series, 93 events. This is a real improvement over the 2-series, 30-event starting point.

### What's sitting on the table unfetched

The paper itself (line 298) acknowledges these available series:

| Series | Ticker | Approx Events | Category | Status |
|--------|--------|---------------|----------|--------|
| Unemployment Rate | KXU3 | 49 | Simple (single number) | **Not fetched** |
| Core CPI m/m | KXCPICORE | 44 | Complex (composite) | **Not fetched** |
| Mortgage Rates | KXFRM | 86 | Simple (single rate) | **Not fetched** |
| CPI Year-over-Year | KXCPIYOY | 39 | Complex (composite) | **Not fetched** |
| Retail Sales | KXRETAIL | Unknown | Simple? | **Not fetched** |
| All-Items CPI | KXACPI | Unknown | Complex (composite) | **Not fetched** |

**That's 218+ known additional events across 4+ series.** Combined with the current 93, the dataset could exceed 300 events across 10+ series. The `fetch_new_series.py` script infrastructure already exists — it's literally a matter of adding tickers to the `target_series` list on line 372.

### Why this matters for every claim in the paper

1. **Simple-vs-complex dichotomy (p=0.0004):** This is the paper's strongest result, but the classification is currently based on the researcher's subjective judgment of 7 series. Adding KXU3 (simple), KXCPICORE (complex), KXFRM (simple), KXCPIYOY (complex) would test whether the pattern replicates out-of-sample with 11 series. If it holds, the result becomes *definitive*. If it breaks, the paper needs restructuring.

2. **Kruskal-Wallis heterogeneity (H=18.5, p=0.005):** With 11 series instead of 7, this becomes far more convincing. More importantly, it tests whether heterogeneity is a robust cross-series phenomenon rather than a property of these specific 7 series.

3. **GDP as the best series (CRPS/MAE=0.48):** Is GDP genuinely special, or is "simple single-number indicator" the category that matters? Unemployment and mortgage rates would test this directly.

4. **Core PCE as the worst (CRPS/MAE=2.06):** Adding KXCPICORE (44 events!) and KXCPIYOY (39 events) would test whether all inflation composites are harmful, or whether Core PCE is an outlier.

### Assessment
The researcher committed to this expansion in the iteration 3 response ("deferred to iteration 4") but didn't deliver. The `fetch_new_series.py` code path exists. The FRED benchmark mappings for KXU3→UNRATE and KXCPICORE→CPILFESL are already in the script (lines 26-27). **This is the single most impactful improvement possible and requires minimal new code.**

## Reflection on Prior Feedback

All iteration 3 critique points were addressed:
- ✅ BCa bootstrap bug fixed (JC CI widened to include 1.0 — honest reporting)
- ✅ Surprise-CRPS endogeneity flagged (raw CRPS vs surprise: ρ=0.12, null)
- ✅ Pairwise Mann-Whitney Bonferroni correction applied
- ✅ Serial-correlation-adjusted CI propagated for CPI
- ✅ Three new series added (KXPCECORE, KXADP, KXISMPMI)
- ✅ Dead code removed

The researcher agreed with all points and executed cleanly. No pushbacks to revisit.

**Dropping from prior iterations:**
- Crypto as contrast case: The researcher reasonably deferred this. Economic series expansion is more valuable for this paper's framing.
- Historical CRPS benchmark data leakage: Acknowledged as negligible. Not re-raising.

## Scores

| Criterion | Score | Delta | Comment |
|-----------|-------|-------|---------|
| Data Sufficiency | 5/10 | -1 | Committed to expansion in iteration 4 but didn't deliver. 218+ events available but unfetched. Score lowered because the gap is now well-documented and the researcher acknowledged it. |
| Novelty | 8/10 | +0 | Simple-vs-complex dichotomy is genuinely novel. No change. |
| Methodological Rigor | 7/10 | +2 | BCa fix, endogeneity correction, Bonferroni correction all landed. New reproducibility concern partially offsets. |
| Economic Significance | 7/10 | +0 | Findings are actionable. Would increase with more series confirming the pattern. |
| Blog Publishability | 6/10 | +0 | Strong concept but underpowered relative to what's available. A 10-series, 300-event paper is clearly publishable. A 7-series, 93-event paper with 218+ unfetched events is harder to justify. |

## Strength of Claim Assessment

### Claim 1: "Simple indicators have better distributional quality than complex ones" (p=0.0004)
**Assessment: Suggestive → potentially conclusive with more data.** Currently rests on a 3-vs-3 grouping (with ISM excluded as "Mixed") of 7 series. The classification is reasonable but subjective — GDP is "simple" while CPI is "complex" because the researcher says so. Adding KXU3 (simple: unemployment rate is a single number), KXFRM (simple: mortgage rate is a single number), KXCPICORE (complex: composite index), and KXCPIYOY (complex: composite transformation) would make this 5-vs-5 with clear ex-ante classifications. **The claim is currently as strong as the evidence allows for 7 series, but would be much stronger with 11.**

### Claim 2: "GDP distributions robustly add value (CRPS/MAE=0.48, CI [0.31, 0.77])"
**Assessment: Conclusive.** BCa CI excludes 1.0. LOO unanimous. n=9 is small but the effect is huge. **Appropriately stated.** No change needed.

### Claim 3: "Heterogeneity across series is highly significant (KW p=0.005)"
**Assessment: Conclusive at the omnibus level.** The KW test is appropriate, well-powered at 93 events across 7 series. **Could be stated even more confidently** — this is the paper's second-strongest statistical result.

### Claim 4: "CPI overall ratio=0.86 with temporal structural break"
**Assessment: Suggestive, appropriately hedged.** The temporal split (p=0.18) is not significant. The 33-event CPI series is the paper's largest — the overall ratio below 1.0 is directionally meaningful. **Appropriately stated.**

### Claim 5: "Point and distributional calibration can diverge independently"
**Assessment: Strong conceptual contribution, suggestive evidence.** This is genuinely novel for prediction markets. Evidence is limited to CPI post-Nov 2024 (n=14), but the pattern is clear. **Could be promoted slightly more — this is one of the paper's most publishable findings.**

### Claim 6: "Volume does not predict CRPS/MAE quality" (ρ=0.14, p=0.27)
**Assessment: Suggestive null.** A null result at n=62 is informative but not definitive. At n=300+, this becomes much more convincing. **Appropriately stated.**

## Novelty Assessment

**Genuinely novel:**
1. CRPS/MAE ratio as practical diagnostic — simple, interpretable, implementable
2. Simple-vs-complex dichotomy in distributional quality — first systematic evidence
3. Point-vs-distribution decoupling in prediction markets
4. Volume null result for distributional quality
5. Appendix B transparency about invalidated findings (admirable and sets a standard)

**To increase novelty:**
1. **10+ series dataset** would make this the most comprehensive distributional calibration study of any prediction market. No comparable dataset exists in the literature.
2. **Out-of-sample simple-vs-complex prediction**: Use the 7-series classification to predict which *new* series (KXU3, KXFRM, etc.) have ratio < 1 vs > 1 before computing. If the simple/complex label predicts correctly for held-out series, this is genuine out-of-sample validation of the main theory.
3. **Horse race for GDP and Jobless Claims**: FRED historical data is already fetched. Extending the benchmark comparison beyond CPI would test whether point forecast quality also varies by complexity.

## Robustness Assessment

### MEDIUM SEVERITY: Reproducibility of new series (KXADP, KXISMPMI)

**The candle files for KXADP and KXISMPMI are empty (2 bytes each):** `data/new_series/KXADP_candles.json` and `data/new_series/KXISMPMI_candles.json`. Yet results exist in `KXADP_results.json` (9 events) and `KXISMPMI_results.json` (7 events).

**Field name mismatch:** The results files use `crps`, `mae`, `crps_mae_ratio` — but `fetch_new_series.py`'s `process_series()` function (lines 312-325) would produce `kalshi_crps`, `mae_interior`, with no pre-computed `crps_mae_ratio`. This means the results were generated by a different script or an earlier version that was subsequently modified.

**No `n_snapshots` field:** The results lack this field, making it impossible to verify that mid-life snapshots (rather than final settled prices) were used to build CDFs. The paper states (line 38): "CRPS is computed at the mid-life snapshot (50% of market lifetime elapsed)."

**Why this matters:** If CDFs were built from final settled prices, CRPS values would be biased downward (final prices concentrate around realized values). This could affect 16 of 93 events (17% of the dataset) and specifically the ADP result (LOO all < 1.0).

### MEDIUM SEVERITY: `fetch_new_series.py` uses wrong API path

Line 59 of `fetch_new_series.py`:
```python
f'/markets/{ticker}/candlesticks'
```
The researcher's own note in the iteration 3 response says this path returns 404 and the correct path is `/series/{series_ticker}/markets/{ticker}/candlesticks`. Yet the code still has the wrong path. This explains the empty candle files — and means future series fetches will also fail.

### LOW SEVERITY: ISM PMI classification

ISM PMI is classified as "Mixed" in the executive summary and excluded from the simple-vs-complex test. ISM Manufacturing PMI is arguably a "simple" single-number diffusion index. If reclassified as "simple," the simple group becomes 4 series (n=41) and the result should be tested for sensitivity.

## The One Big Thing

**Fetch KXU3, KXCPICORE, KXFRM, and KXCPIYOY.** The researcher committed to this in the iteration 3 response. The script infrastructure exists. These 218+ events would more than double the dataset, transform the paper from a 7-series exploratory study to a 10+ series comprehensive analysis, and enable genuine out-of-sample validation of the simple-vs-complex hypothesis. Every other improvement pales in comparison.

Specific code changes needed:
```python
# In scripts/fetch_new_series.py, line 372:
target_series = ['KXU3', 'KXCPICORE', 'KXFRM', 'KXCPIYOY']

# Fix line 59 (candlestick API path):
# Current (wrong): f'/markets/{ticker}/candlesticks'
# Correct: Use the series_ticker to build the path, matching experiment2's approach
```

Also add FRED mappings for KXFRM (MORTGAGE30US) and KXCPIYOY (CPIAUCSL with YoY transformation).

## Other Issues

### Must Fix (blocks publication)

1. **Fetch the remaining 4 series (KXU3, KXCPICORE, KXFRM, KXCPIYOY).** The paper acknowledges these exist (line 298). The code infrastructure exists. The researcher committed to this. 218+ events would more than double the dataset. This is the single most important action.

2. **Fix KXADP/KXISMPMI reproducibility.** Re-fetch candles using the correct API path, persist them, verify `n_snapshots` confirms mid-life snapshot usage, and recompute CRPS. The current empty candle files and mismatched result field names undermine confidence in these 16 events.

3. **Fix `fetch_new_series.py` candlestick API path** (line 59). The current path 404s for these series. Without this fix, the series expansion is blocked.

### Should Fix (strengthens paper)

1. **Formalize simple-vs-complex classification.** Provide an operational definition (e.g., "single administratively-reported number" vs "composite index or discrete decision") and apply it ex ante to all 11 series, including ISM and the new ones. Run sensitivity with ISM reclassified.

2. **Out-of-sample simple-vs-complex test.** Before computing CRPS for new series, write down predictions: KXU3 < 1.0 (simple), KXCPICORE > 1.0 (complex), KXFRM < 1.0 (simple), KXCPIYOY > 1.0 (complex). Then compute and report the hit rate. This is genuine pre-registration.

3. **Horse race for GDP and Jobless Claims.** FRED historical data is already fetched (`fetch_historical_gdp`, `fetch_historical_jobless_claims`). The horse race code from experiment13 can be adapted with minimal effort.

4. **PIT analysis for expanded series.** Currently only covers the original 4 series (62 events). Should include KXPCECORE, KXADP, KXISMPMI, and the new series once fetched.

### New Experiments / Code to Write

1. **Fix API path and fetch new series** (Must Fix #1 + #3):
   ```python
   # fetch_new_series.py line 59, change to:
   def fetch_candles_for_market(client, series_ticker, ticker, max_retries=3):
       candles = client.get_all_pages(
           f'/series/{series_ticker}/markets/{ticker}/candlesticks',
           params={'period_interval': 60},
           result_key='candlesticks',
       )
   ```
   Then update `target_series = ['KXU3', 'KXCPICORE', 'KXFRM', 'KXCPIYOY']` and re-run.

2. **Re-fetch KXADP/KXISMPMI candles** (Must Fix #2): Run the fixed script for `['KXADP', 'KXISMPMI']`, verify candle files are non-empty, verify `n_snapshots > 2`, recompute CRPS from mid-life.

3. **Pre-registered simple-vs-complex OOS test** (Should Fix #2): Before running CRPS for new series, write predictions to a file. After computing, report concordance.

4. **Integrate all new series into unified KW test and simple-vs-complex Mann-Whitney**: Update the heterogeneity analysis with all 11 series.

### Genuinely Unfixable Limitations

1. **No order book depth data.** Kalshi doesn't expose historical LOB snapshots. Volume is the only liquidity proxy. **Unfixable.**

2. **FED n=4 is structurally constrained.** FOMC meets ~8 times/year; multi-strike Kalshi markets only exist for recent meetings. **Unfixable in the near term.**

3. **Cannot observe trader composition.** Whether distributional quality depends on trader sophistication is untestable with public data. **Unfixable without Kalshi cooperation.**

4. **SPF monthly CPI forecast doesn't exist.** The horse race uses annual/12 as a proxy. No better public benchmark exists for monthly CPI point forecasts. **Unfixable.**

## Verdict

**MAJOR REVISIONS.** The paper has strong bones — the CRPS/MAE diagnostic is genuinely useful, the simple-vs-complex finding is novel, and the researcher has been exceptionally responsive. But publishing a 7-series paper while acknowledging 218+ unfetched events from the same API is indefensible. The reproducibility gap in the KXADP/KXISMPMI candle data compounds the concern. Once the dataset is expanded to 10+ series with verified candle data, and the simple-vs-complex hypothesis is tested out-of-sample on the new series, this paper moves to minor revisions or accept.
