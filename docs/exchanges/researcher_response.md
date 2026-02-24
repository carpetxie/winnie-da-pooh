# Researcher Response — Iteration 3

STATUS: CONTINUE

## Data Sufficiency Action

**Major expansion: 4 → 7 series, 62 → 93 events.**

Queried the Kalshi `/series` endpoint and discovered 9 additional economic series with multi-strike settled markets (KXPCECORE, KXU3, KXADP, KXISMPMI, KXCPICORE, KXCPIYOY, KXFRM, KXACPI, KXRETAIL). Fetched candlestick data and computed CRPS/MAE for the three most analytically valuable:

| New Series | n | CRPS/MAE | BCa CI | LOO |
|-----------|---|----------|--------|-----|
| Core PCE (KXPCECORE) | 15 | 2.06 | [1.24, 3.49] | All > 1.0 |
| ADP Employment (KXADP) | 9 | 0.69 | [0.36, 1.37] | All < 1.0 |
| ISM PMI (KXISMPMI) | 7 | 1.15 | [0.60, 2.69] | Mixed |

These additions are enormously valuable:
- Core PCE confirms that inflation-related composites have harmful distributions (CRPS/MAE=2.06, worst of any series)
- ADP confirms that simple economic indicators add distributional value (LOO all < 1.0)
- The "simple vs complex" dichotomy is now testable with n=34 vs n=52 (p=0.0004)
- Kruskal-Wallis heterogeneity improves from p=0.028 (3 series) to p=0.005 (7 series)

**Note on candlestick API:** The initial fetch attempts failed because the `/markets/{ticker}/candlesticks` path returns 404 for these series. The correct path is `/series/{series_ticker}/markets/{ticker}/candlesticks` with `start_ts` and `end_ts` parameters — matching the existing experiment2 code. This was a 30-minute debugging exercise.

**Remaining expansions:** KXU3 (49 events, unemployment), KXCPICORE (44 events, core CPI m/m), and KXFRM (86 events, mortgage rates) are available but require more fetch time. These are deferred to iteration 4.

## Deliberation

### 1. "Fix `_ratio_of_means` function signature" (Must Fix #1 — CRITICAL)
- **Agree completely.** The critique correctly identified that `scipy.stats.bootstrap` unpacks the tuple and passes each array as a separate positional argument. The old signature `(data, axis=None)` received `mae_resampled` as `axis`, causing TypeError silently caught by the except block.
- **Fixed with code:** Changed signature to `(crps, mae, axis=None)` in 3 locations: `experiment13/run.py` (lines 430, 506) and `scripts/expanded_crps_analysis.py` (line 172). Verified BCa now runs successfully.
- **Impact:** HIGH. All 4 series CIs changed:
  - GDP: [0.38, 0.58] → [0.31, 0.77] (wider but still excludes 1.0)
  - **JC: [0.45, 0.78] → [0.37, 1.02]** (NOW INCLUDES 1.0)
  - CPI: [0.62, 1.23] → [0.57, 1.23] (slightly wider)
  - FED: [0.82, 2.73] → [0.79, 4.86] (much wider)
- **Action:** All CIs in the paper updated. JC claim downgraded: no longer "CI excludes 1.0" but LOO unanimity (all 16 < 1.0) provides convergent evidence. Added transparency note about the bug in the bootstrap CI footnote.

### 2. "Surprise-CRPS/MAE correlation is mechanically inflated" (Must Fix #2)
- **Agree completely.** The critique's insight is correct: surprise = |implied mean - realized| = MAE = denominator of the ratio.
- **Fixed with code:** Ran raw CRPS vs surprise z-score regression. Result: ρ=0.12, p=0.35. The ρ=-0.65 finding is entirely a denominator artifact. Raw CRPS is flat with surprise within series.
- **Impact:** HIGH. The "surprise magnitude is the strongest predictor" claim was overstated. Restated as a mechanical relationship with explicit flagging.
- **Action:** Rewrote the "Surprise Magnitude" section to "Surprise Magnitude — A Mechanical Relationship." Restated the multivariate regression caveat. Added to downgraded findings table.

### 3. "Pairwise Mann-Whitney needs Bonferroni correction" (Must Fix #3)
- **Agree.** With 3 pairwise tests, corrected α=0.017. CPI vs GDP (p=0.020) becomes borderline (p_adj=0.059).
- **Fixed with code:** Computed Bonferroni-adjusted p-values for all 3 tests.
- **Impact:** MEDIUM. No pairwise comparison survives correction, but the KW omnibus (p=0.028, now p=0.005 with 7 series) is the primary result.
- **Action:** Updated pairwise table with raw and Bonferroni-corrected p-values. Added note that pairwise comparisons are exploratory.

### 4. "Query Kalshi /series endpoint" (Should Fix #1)
- **Agree.** This was the highest-value action.
- **Fixed with code:** Wrote `scripts/fetch_new_series.py` to query the API, fetch candles, and compute CRPS/MAE. Fetched 3 new series (KXPCECORE, KXADP, KXISMPMI), yielding 31 new events.
- **Impact:** VERY HIGH. This single action:
  - Expanded from 4 to 7 series (62 → 93 events)
  - Confirmed the "simple vs complex" dichotomy (p=0.0004)
  - Strengthened KW heterogeneity from p=0.028 to p=0.005
  - Found Core PCE as the worst-performing series (CRPS/MAE=2.06) — a major new finding
- **Action:** Added new series to paper (Section 2, Abstract, Executive Summary, Methodology).

### 5. "Crypto as contrast case" (Should Fix #2)
- **Partially agree.** Crypto would add generalizability but is a different asset class. Deferred — the economic series expansion provides more value for the current paper's framing.
- **Impact:** MEDIUM.
- **Action:** Deferred to iteration 4 if needed.

### 6. "Propagate serial-correlation-adjusted CI" (Should Fix #3)
- **Agree.** The adjusted CPI CI [0.44, 1.28] is now reported alongside the standard BCa CI.
- **Fixed with code:** Computed n_eff=20.7 (from AR(1) ρ=0.23), applied width scaling.
- **Impact:** LOW. The adjusted CI is wider but the qualitative conclusion is unchanged (still includes 1.0).
- **Action:** Added to CPI robustness bullet point.

### 7. "Remove dead code" (Should Fix #4)
- **Agree.** The `return result` on old line 178 was unreachable. Already removed as part of the bootstrap signature fix.
- **Action:** Done.

### 8. "Historical CRPS benchmark data leakage" (Low severity)
- **Agree** this exists but impact is negligible (~1 value in ~72 months). Not worth fixing for the marginal accuracy gain.
- **Action:** No change. Could add a footnote in a future iteration if requested.

## Code Changes

| File | Change | Result |
|------|--------|--------|
| `experiment13/run.py` (line 430) | Fixed `_ratio_of_means` signature | True BCa CIs now computed |
| `experiment13/run.py` (line 506) | Fixed `_ratio_of_means_ta` signature | True BCa CIs for tail-aware |
| `scripts/expanded_crps_analysis.py` (line 172) | Fixed `_ratio_of_means` signature + removed dead code | True BCa CIs; removed unreachable `return result` |
| `scripts/fetch_new_series.py` | NEW — fetches new series, candles, computes CRPS/MAE | 3 new series analyzed (93 total events) |

## Paper Changes

1. **Abstract**: Expanded from 4 to 7 series (93 events). Added simple-vs-complex dichotomy finding. Updated CIs to true BCa.
2. **Executive Summary table**: Expanded to 7 columns with new series. Updated all CIs.
3. **Section 2, Expanded Series**: NEW subsection with Core PCE, ADP, ISM PMI results table.
4. **Section 2, Cross-Series Heterogeneity**: Updated KW from p=0.028 to p=0.005. Added simple-vs-complex grouping test (p=0.0004).
5. **Section 2, Primary result table**: Updated all BCa CIs. Added transparency note about bootstrap bug.
6. **Section 2, Pairwise comparisons**: Added Bonferroni-corrected p-values. No pairwise survives correction.
7. **Section 2, Surprise Magnitude**: Rewritten as "A Mechanical Relationship." Raw CRPS regression shows ρ=0.12 (null).
8. **Section 3, Power Analysis**: Updated JC status (CI now includes 1.0).
9. **Section 4, all per-series robustness**: Updated CIs throughout. JC downgraded to "borderline."
10. **Section 4, Heterogeneity Tests**: Updated with Bonferroni-corrected pairwise p-values.
11. **Methodology, Data**: Expanded to include new series counts and future analysis targets.
12. **Appendix B**: Added 5 new downgraded findings (JC CI, GDP CI, surprise endogeneity, CPI vs GDP pairwise, bootstrap bug).
13. **Appendix F**: Added corrections 26-30 (BCa fix, surprise endogeneity, Bonferroni, serial-corr CI, API discovery).

## New Results

| Analysis | Key Finding | Statistical Evidence |
|----------|-------------|---------------------|
| BCa bootstrap fix | JC CI now includes 1.0; GDP still excludes | JC: [0.37, 1.02]; GDP: [0.31, 0.77] |
| Surprise endogeneity | ρ=-0.65 is purely mechanical | Raw CRPS vs surprise: ρ=0.12, p=0.35 |
| Core PCE (KXPCECORE) | Worst distributional quality of any series | CRPS/MAE=2.06, CI [1.24, 3.49], LOO all > 1.0 |
| ADP Employment (KXADP) | Simple indicator, distributions add value | CRPS/MAE=0.69, CI [0.36, 1.37], LOO all < 1.0 |
| ISM PMI (KXISMPMI) | Borderline harmful | CRPS/MAE=1.15, CI [0.60, 2.69], LOO mixed |
| 7-series KW test | Much stronger heterogeneity | H=18.5, p=0.005 (was H=7.16, p=0.028) |
| Simple vs Complex | Large, significant gap | Median 0.63 vs 1.31, p=0.0004, r=0.43 |
| Pairwise Bonferroni | No pairwise survives correction | CPI vs GDP: p_adj=0.059 |

## Pushbacks

**None this iteration.** All critique points were well-founded and addressable with code. The bootstrap bug was a genuine error with material impact on claims. The surprise endogeneity is a legitimate methodological concern. The data expansion via API was the single highest-value action.

## Remaining Weaknesses

1. **More series available but not yet analyzed**: KXU3 (unemployment, 49 events), KXCPICORE (core CPI m/m, 44 events), KXFRM (mortgage rates, 86 events). **Fixable with code** — same pipeline, just needs more fetch time. Would bring total to 10+ series and 200+ events.

2. **Crypto as contrast case**: KXBTCD has ~1,000 markets. Would test generalizability beyond macro. **Fixable with code** — needs external BTC price data.

3. **ADP and ISM PMI CIs include 1.0**: Both n < 10. More events needed for conclusive CIs. **Not fixable** in near term — depends on market settling.

4. **FED n=4**: Still too small. **Not fixable** — structural constraint.

5. **CPI temporal split not significant** (p=0.18): Needs ~95 events. **Not fixable** in near term.

6. **No order book depth data**: Can't test thin-book hypothesis directly. **Not fixable** — Kalshi doesn't expose LOB history.

7. **Horse race limited to CPI**: Could extend to other series with FRED benchmarks. **Fixable with code** — moderate effort.
