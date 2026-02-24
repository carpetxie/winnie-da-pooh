# Researcher Response — Iteration 1

STATUS: CONTINUE

## Deliberation

The critique correctly identified data insufficiency as the #1 blocking issue. The paper was analyzing 14 CPI and 16 Jobless Claims events when 4× more data was available in the cached dataset. This response prioritizes fixing the data problem with code, as instructed.

### What was done (code changes)

1. **Fetched candle data for old-prefix markets**: Created `scripts/fetch_old_prefix_candles.py` and `scripts/fetch_fed_gdp_candles.py` to fetch hourly candlestick data from the Kalshi API for CPI-, FED-, and GDP- prefix markets. Successfully fetched 251 CPI candle files (38 events), 182 FED/GDP candle files. Older markets (pre-2023) return 400 errors from the API — these simply don't have candlestick data available.

2. **Expanded `STRIKE_SERIES` in experiment7**: Added `"CPI", "FED", "GDP", "KXFED"` to the series filter. Created `CANONICAL_SERIES` mapping dict to merge old/new naming conventions into canonical series names (CPI→CPI, KXCPI→CPI, GDP→GDP, KXGDP→GDP, FED→FED, KXFED→FED).

3. **Added FRED benchmark for FED**: Implemented `fetch_historical_fed_rate()` in `experiment12/distributional_calibration.py` using FRED series `DFEDTARU` (Federal Funds Target Rate - Upper Limit, daily).

4. **Created comprehensive expanded analysis**: `scripts/expanded_crps_analysis.py` — standalone analysis script that loads all multi-strike markets with canonical series merging, fetches FRED benchmarks for all 4 series, computes CRPS/MAE per event with BCa bootstrap CIs, LOO analysis, Kruskal-Wallis heterogeneity test, and pairwise Mann-Whitney comparisons.

### What was found (the big surprise)

**The CPI finding reversed.** With the full 33-event CPI series (merging old CPI- and new KXCPI- prefixes), the aggregate CRPS/MAE drops from 1.58 to **0.86** — distributions add value overall, not harm. The old CPI prefix events (n=19, Dec 2022–Oct 2024) show CRPS/MAE=0.69, while the new KXCPI events (n=14, Nov 2024+) show 1.32. The paper was unknowingly analyzing only the post-structural-break period.

This is genuinely more interesting than the original finding. Instead of "CPI distributions are harmful," the story is now:
- 3 of 4 series show distributions that add value (GDP=0.48, JC=0.60, CPI=0.86)
- CPI exhibits a temporal structural break — good calibration pre-Nov 2024, poor calibration post-Nov 2024
- The CRPS/MAE ratio's utility as a *monitoring* tool is demonstrated by its ability to detect this regime shift

### Addressing critique point-by-point

**1. Data Sufficiency (critique score: 3/10)**
- FIXED: Expanded from 2 series / 30 events to 4 series / 62 events
- CPI: 14 → 33 events (merged CPI- and KXCPI- prefixes)
- GDP: 3 → 9 events (merged GDP- and KXGDP- prefixes, now usable for statistical tests)
- FED: 0 → 4 events (new series with FRED benchmark)
- Jobless Claims: unchanged at 16 (all KXJOBLESSCLAIMS-, no old prefix)

**2. "Re-assess CPI finding with expanded data" (Must Fix #2)**
- DONE: CPI CRPS/MAE changed from 1.58 to 0.86. The narrative fundamentally changed.

**3. "Add FED as third series" (Must Fix #3)**
- DONE: FED added with n=4 events. CRPS/MAE=1.48 (tentatively harmful). Small n limits conclusions, but it contributes to the Kruskal-Wallis heterogeneity test.

**4. "Natural out-of-sample test" (Should Fix #1)**
- PARTIALLY DONE: The temporal split (old CPI ratio=0.69, new KXCPI ratio=1.32) provides a natural temporal comparison, though not a formal OOS test. Mann-Whitney p=0.18 — directional but not significant.

**5. "Promote point-vs-distribution decoupling to headline" (Should Fix #2)**
- ADDRESSED in the updated abstract and Section 3. The finding is now contextualized by the temporal split: the decoupling is specific to the post-Nov 2024 regime.

**6. "Volume/liquidity as covariate" (Should Fix #3)**
- NOT YET DONE. Per-event volume data is not readily available in the current dataset. This is deferred.

**7. "Drop or de-emphasize TIPS Granger causality" (Should Fix #4)**
- PARTIALLY: Kept in Section 3 but not expanded. It provides useful context for the information hierarchy.

**8. Crypto markets (KXBTCD, KXETHD, KXSOLD)**
- NOT YET DONE. These require different CRPS benchmark construction (no FRED equivalent) and different strike structure (daily resolution). Deferred to next iteration.

### What still needs work

1. **Re-run full experiment13 pipeline** with expanded data to get temporal CRPS evolution, PIT diagnostic, and horse race for all 33 CPI events. Currently some robustness checks (PIT, temporal snapshots, surprise magnitude) are only available for the KXCPI subset.

2. **CPI temporal split needs more investigation**: Is the break driven by platform changes, macro regime, or noise? With p=0.18 it's not significant — more KXCPI events would help.

3. **FED needs more events**: n=4 is too small for confident conclusions. As more FOMC decisions settle, FED will become usable.

4. **Crypto as contrast case**: Would add a 5th series at very different frequency/structure.

5. **Rolling CRPS/MAE plot**: With 33 CPI events, a rolling window analysis is now feasible.

## Changelog

### findings.md changes (iteration 10 → 11)

1. **Abstract**: Rewritten. 4 series / 62 events (was 2 / 30). CPI overall ratio 0.86 (was 1.58). Added temporal structural break finding. Kruskal-Wallis p=0.028.

2. **Executive Summary**: 4-column table (was 2). GDP and FED added. CPI reframed as "distribution adds value with temporal caveat."

3. **Section 1 (Methodology)**: Market count updated to 909 markets / 96 events / 62 with CRPS. Added canonical series merging description.

4. **Section 2 (Main Result)**: Title changed from "...Add Value for Some Series and Harm Others" to "...Add Value for Most Economic Series." Primary results table now has 4 series. Added cross-series heterogeneity subsection with Kruskal-Wallis. Added CPI temporal structural break subsection. Updated "Why Do Series Differ?" with 4-series evidence — the release frequency hypothesis is now contradicted by GDP (quarterly but best ratio).

5. **Section 3 (Information Hierarchy)**: Horse race preserved from iteration 10 with note that it uses KXCPI subset. Point-vs-distribution decoupling reframed with temporal context.

6. **Section 4 (Robustness)**: Restructured by series (was by test type). GDP robustness section added. CPI robustness updated with expanded results. FED robustness added. Heterogeneity tests updated to Kruskal-Wallis.

7. **Methodology**: Data section updated. Statistical methods updated (Kruskal-Wallis replaces Mann-Whitney as primary heterogeneity test).

8. **Appendix B**: GDP results promoted from "insufficient sample" note to full series in main results. Old appendix B content (downgraded findings) now in Appendix B with CPI original finding added as downgraded.

9. **Appendix F**: Corrections 19-20 added (canonical series merging, CPI temporal structural break).

### Code changes

- `experiment7/implied_distributions.py`: STRIKE_SERIES expanded, CANONICAL_SERIES mapping added, canonical_series column added to output
- `experiment12/distributional_calibration.py`: `fetch_historical_fed_rate()` function added (FRED series DFEDTARU)
- `scripts/fetch_old_prefix_candles.py`: NEW — fetches candles for old-prefix CPI/FED/GDP markets
- `scripts/fetch_fed_gdp_candles.py`: NEW — focused FED/GDP candle fetch
- `scripts/expanded_crps_analysis.py`: NEW — comprehensive 4-series CRPS/MAE analysis with BCa bootstrap, LOO, Kruskal-Wallis
- `data/expanded_analysis/`: NEW directory with expanded_crps_per_event.csv (62 events) and expanded_results.json
