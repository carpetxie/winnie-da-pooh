# Researcher Response — Iteration 2

STATUS: CONTINUE

## Data Sufficiency Action

No new series were added this iteration. Iteration 1 expanded from 2 to 4 series (62 events), which was the critique's #1 blocking issue. This iteration focused on extracting maximum value from the existing 62 events through new analyses the critique specifically requested: volume-CRPS regression, rolling CRPS/MAE, OOS validation, multivariate regression, persistence testing, and full 4-series PIT diagnostics.

**Why not add crypto (KXBTCD/KXETHD/KXSOLD)?** Candle data exists (146/57/26 files), but these series require fundamentally different benchmark construction (no FRED equivalent — would need historical crypto price data from an external source) and settle daily rather than at economic releases. They would be a different paper section, not a strengthening of the current economic series analysis. Deferred to a future iteration if the critique requests it.

**Why not add more economic series from the API?** The critique focused on using data already in the cache. The targeted_markets.json contains only the series already analyzed. Fetching entirely new series (e.g., nonfarm payrolls, retail sales, PCE) would require: (1) identifying the correct Kalshi series tickers, (2) fetching markets and candles via API, (3) finding FRED benchmarks, and (4) verifying strike/value parsing. This is feasible but was lower priority than the robustness analyses the critique specifically requested.

## Deliberation

### 1. "Volume/liquidity as a covariate" (Should Fix #3 from critique)
- **Agree**: This was a direct gap — the paper hypothesized liquidity drives CPI's poor distributions but never tested it.
- **Can I fix with code?** Yes — volume data exists in targeted_markets.json for every market.
- **Impact**: HIGH — and the finding is a null result that's more interesting than a positive one.
- **Action**: Built and ran volume-CRPS regression. **Result: ρ=0.14, p=0.27 — no relationship.** CPI has 9× the median volume of JC but worse distributional quality. This rules out the simplest market-design lever (increasing volume). Added to paper as a new subsection and to market design implications.

### 2. "Rolling CRPS/MAE" (critique suggestion for novelty)
- **Agree**: With 33 CPI events, this is now feasible and directly visualizes the structural break.
- **Can I fix with code?** Yes.
- **Impact**: HIGH — provides the most compelling visualization of the CPI structural break.
- **Action**: Implemented rolling window (w=8) and expanding window analyses. **Result: All 14 old-CPI windows show ratio < 1.0; all 12 new-KXCPI-dominated windows show ratio > 1.0. The transition is sharp and clear.** Added to paper as new subsection.

### 3. "No out-of-sample validation" (critique: "valid critique, partially addressable")
- **Agree**: This was a genuine gap.
- **Can I fix with code?** Yes — implemented expanding-window OOS and natural temporal OOS.
- **Impact**: MEDIUM — the OOS results are honest but unflattering (50% accuracy). This actually strengthens the paper by showing the diagnostic is best used as a real-time monitor, not a predictor.
- **Action**: Ran both OOS tests. **Expanding-window: 50% accuracy (chance). Natural OOS (old→new CPI): direction prediction fails.** This is reported honestly and reframes the CRPS/MAE ratio as a monitoring tool rather than a forecasting tool. Added to Methodology section.

### 4. "Cross-series prediction" (critique: "Can CRPS/MAE at t predict t+1?")
- **Agree**: Important for practical utility.
- **Can I fix with code?** Yes — implemented lag-1 autocorrelation test.
- **Impact**: MEDIUM — another null result that's informative.
- **Action**: **Result: Zero autocorrelation across all series (CPI ρ=−0.003, JC ρ=0.06, GDP ρ=−0.10).** The ratio is event-specific, not sticky. This means event-by-event prediction is impossible, but rolling-window monitoring catches regime shifts. Added to paper.

### 5. "Add volume/liquidity as a covariate in regression" (critique: "regression with covariates")
- **Agree**: Multivariate analysis strengthens the mechanism discussion.
- **Can I fix with code?** Yes — OLS with series dummies, strike count, volume, surprise.
- **Impact**: MEDIUM-HIGH — identifies surprise as the dominant driver (R²=0.27, surprise coeff=−0.84).
- **Action**: Ran multivariate regression. Series dummies and surprise z-score are the significant predictors; volume and strike count are not. Incorporated into "What Drives Distributional Quality?" section.

### 6. "Extend PIT to all 4 series" (noted as priority in paper itself)
- **Agree**: Was explicitly flagged as next-iteration priority.
- **Can I fix with code?** Yes.
- **Impact**: MEDIUM — completes the diagnostic picture.
- **Action**: Computed PIT for all 62 events across 4 series. **No series rejects uniformity (all KS p > 0.29).** GDP and JC near-ideal; CPI and FED show mild directional biases. Updated the PIT section from 2-series subset to full 4-series table.

### 7. "Promote point-vs-distribution decoupling to headline" (Should Fix #2)
- **Partially agree**: It's already in the abstract and Section 3. I've made it the section title for Section 3.
- **Action**: Retitled Section 3 to "CPI Point Forecasts and the Point-Distribution Decoupling."

### 8. "Drop or de-emphasize TIPS Granger causality" (Should Fix #4)
- **Agree**: TIPS→Kalshi Granger causality is expected and adds little novelty.
- **Action**: Condensed from full subsection with table to 2 sentences. Still present for completeness but no longer prominent.

### 9. "Clarify CRPS/MAE for general readers" (Should Fix #5)
- **Agree**: The Kalshi blog audience includes traders who may not know CRPS.
- **Action**: Added 2-sentence intuitive explanation in the abstract before the main results.

## Code Changes

- **`scripts/robustness_analyses.py`**: NEW — 7 analyses in one script:
  1. Volume-CRPS Spearman regression (overall + per-series)
  2. Rolling CRPS/MAE for CPI (window=8, expanding)
  3. Expanding-window OOS validation
  4. Multivariate OLS regression (CRPS/MAE ~ strikes + log_volume + surprise_z + series)
  5. CRPS/MAE lag-1 persistence test
  6. Full 4-series PIT diagnostic
  7. Within-series strike count prediction

- **`data/expanded_analysis/robustness_results.json`**: NEW — all results from the above analyses

## Paper Changes

1. **Abstract**: Added 2-sentence CRPS/MAE intuitive explanation for general readers.
2. **Practical Takeaways**: Updated OOS caveat with actual OOS results (50% accuracy → monitoring tool reframing).
3. **Section 2, "What Drives Distributional Quality?"**: Completely rewritten. Was speculative 4-mechanism hypothesis; now evidence-based with multivariate regression (R²=0.27, surprise dominates), volume null result, and within-series strike count analysis.
4. **Section 3**: Retitled to "CPI Point Forecasts and the Point-Distribution Decoupling." TIPS subsection condensed from full table to 2 sentences.
5. **Section 4, PIT Diagnostic**: Expanded from 2-series (n=30) to 4-series (n=62) table with bias direction.
6. **Section 4, Surprise Magnitude**: Updated from KXCPI-only (n=14) to pooled (n=62, ρ=−0.65, p<0.0001).
7. **Section 4, NEW: CRPS/MAE Persistence**: Null autocorrelation finding.
8. **Section 4, NEW: Rolling CRPS/MAE**: CPI temporal dynamics showing structural break in rolling window.
9. **Methodology, In-Sample Caveat**: Replaced vague OOS promise with actual OOS results and interpretation.
10. **Methodology, Key Statistical Methods**: Added methods 6-9 (volume regression, OLS, rolling, OOS).
11. **Appendix A**: Updated — PIT analysis now complete for all 4 series.
12. **Appendix C, Market Design**: Added volume null finding ("volume is not the bottleneck").
13. **Appendix F**: Added corrections 21-25 (volume, regression, persistence, PIT, OOS).

## New Results

| Analysis | Key Finding | Statistical Evidence |
|----------|-------------|---------------------|
| Volume-CRPS | **Null**: Volume does not predict CRPS/MAE | ρ=0.14, p=0.27 (n=62) |
| Rolling CRPS/MAE (CPI) | Structural break visible in rolling window | All old-CPI windows < 1.0, all new-KXCPI windows > 1.0 |
| Temporal trend (CPI) | Directional upward trend in per-event ratios | ρ=0.31, p=0.075 |
| OOS expanding-window | No predictive power for single events | 50% accuracy (chance) |
| OOS natural temporal | Direction prediction fails (old < 1 → new > 1) | Train=0.69, Test=1.32 |
| Multivariate regression | Surprise dominates; volume and strikes non-significant | R²=0.27, surprise coeff=−0.84 |
| Persistence | No autocorrelation in CRPS/MAE | CPI ρ=−0.003, JC ρ=0.06, GDP ρ=−0.10 |
| PIT (4-series) | No series rejects uniformity | All KS p > 0.29 |
| PIT bias | GDP overestimates (0.39), CPI underestimates (0.56) | CIs include 0.5 for all |

## Pushbacks

**None this iteration.** All critique points were well-founded and addressable with code. The volume null result and OOS failure are honest findings that strengthen the paper's credibility by showing what *doesn't* work.

## Remaining Weaknesses

1. **Only 4 economic series**: Could add nonfarm payrolls, PCE, retail sales from Kalshi API if they have multi-strike markets. **Fixable with code** — requires API exploration and FRED benchmark matching. Not done this iteration because the critique focused on using cached data and running robustness checks.

2. **Crypto as contrast case**: KXBTCD/KXETHD/KXSOLD have candle data but need external price benchmarks. **Fixable with code** — moderate effort.

3. **FED n=4 too small**: Cannot draw confident conclusions. **Not fixable** — need to wait for more FOMC decisions to settle on Kalshi.

4. **CPI temporal split not individually significant** (p=0.18): Need ~95 events for 80% power. **Not fixable** in the near term — CPI releases monthly.

5. **In-sample CRPS/MAE ratios**: The OOS tests show the ratio doesn't predict single events. The rolling window is more useful but is still in-sample in the sense that it uses all available data. **Partially fixable** — a held-out rolling approach could be implemented but would reduce already-small sample sizes.

6. **No order book depth data**: The paper hypothesizes thin order books at extreme strikes degrade quality, but Kalshi doesn't expose historical order book snapshots. **Not fixable** — data doesn't exist in accessible form.
