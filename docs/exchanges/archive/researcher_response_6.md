# Researcher Response — Iteration 6

STATUS: CONTINUE

## Data Sufficiency Action

**No new series fetched this iteration** — the critique explicitly downgraded this from "must fix" to "should fix" (KXRETAIL low priority, KXACPI likely redundant). The 11-series, 248-event dataset is sufficient.

**Instead, analytical coverage gaps were filled with code:**

1. **PIT analysis extended from 4→11 series.** Wrote `scripts/iteration6_analyses.py` which computes PIT for all 7 new series (KXU3, KXCPICORE, KXCPIYOY, KXFRM, KXADP, KXISMPMI, KXPCECORE) by loading their CDF snapshots from `data/new_series/`, interpolating the survival function at the realized value, and computing bootstrap CIs + KS/CvM tests. Combined with the 4 original series, the paper now has PIT coverage for 100% of series.

2. **Cross-series horse race extended to 3 series.** Fetched UNRATE and MORTGAGE30US from FRED. Computed paired Wilcoxon tests and Cohen's d for Kalshi vs random walk and trailing mean. Key finding: KXFRM beats random walk with d=−0.55, p<0.001 (n=61) — the paper's most statistically powerful point forecast result.

3. **Serial correlation computed for 8 testable series** (all with n≥7). Only KXU3 shows significant autocorrelation (ρ=−0.54, p=0.002).

4. **KXPCECORE discrepancy fully explained.** KXPCECORE-25JUL had realized=0.3, implied_mean=0.3 (MAE≈0), creating infinite per-event ratio. The ratio-of-means (1.22) is robust; the mean-of-ratios is not.

## Deliberation

### 1. "Extend PIT analysis to all 11 series" (MUST FIX)
- **Agree completely.** A "distributional calibration" paper that validates calibration for only 36% of its series was a conspicuous hole.
- **Fixed with code:** `scripts/iteration6_analyses.py` computes PIT for all 7 new series. Results reveal 3 key patterns: (a) universal overconcentration (all std(PIT) < 0.289), (b) 3 series reject uniformity (KXFRM, KXCPICORE, KXCPIYOY — all with low bias), (c) KXU3 is near-perfectly calibrated (mean=0.502).
- **Impact:** HIGH. This is the most impactful change this iteration.
- **Action:** Full 11-series PIT table replaces 4-series table in Section 4. Added interpretive paragraph.

### 2. "Add one sentence addressing 'good point forecast inflates ratio'" (MUST FIX)
- **Agree.** This is the most obvious hostile reviewer attack and the paper had the perfect defense but didn't deploy it.
- **Can fix with prose:** Yes, one sentence.
- **Impact:** MEDIUM. Preempts the most common objection.
- **Action:** Added explicit sentence in Section 2 noting CPI ratio=1.32 despite d=−0.85 point forecast performance. Also added "designed as a retrospective monitoring diagnostic, not a predictive model" clarification.

### 3. "Extend horse race to 2+ additional series" (SHOULD FIX)
- **Agree.** Transforms Section 3 from CPI case study to systematic evidence.
- **Fixed with code:** Fetched UNRATE and MORTGAGE30US from FRED. Ran horse races for KXU3 and KXFRM using interior mean.
- **Impact:** HIGH. KXFRM result (d=−0.55, p<0.001, n=61) is the paper's most statistically powerful point forecast finding.
- **Action:** New "Cross-Series Point Forecast Horse Race" subsection in Section 3 with 3-series comparison table.

### 4. "Extend serial correlation to all 11 series" (SHOULD FIX)
- **Agree.** One loop, one table, preempts the non-independence attack.
- **Fixed with code:** Computed lag-1 Spearman ρ for all series with n≥7 (8 series).
- **Impact:** MEDIUM. Key finding: 7/8 series are serially uncorrelated, validating standard bootstrap. KXU3 is the exception (ρ=−0.54, mean-reverting).
- **Action:** Full serial correlation table replaces the 3-series paragraph in Section 4.

### 5. "Extend temporal snapshot sensitivity to GDP" (SHOULD FIX)
- **Partially addressed.** Only 3 GDP events had sufficient data in strike_markets.csv (exp7's dataset). The full 9-event GDP dataset uses merged old/new naming conventions with candle data spread across exp2 and exp12 pipelines. Getting reliable multi-percentile CDFs for all 9 events would require a deeper pipeline integration.
- **Impact:** MEDIUM but would be very compelling.
- **Action:** Deferred — the existing GDP LOO analysis [0.45, 0.51] and CI [0.31, 0.77] already make this result very strong. Would need to rewrite the CDF construction pipeline to handle cross-experiment data.

### 6. "Investigate KXPCECORE 2.06→1.22 discrepancy" (SHOULD FIX)
- **Agree.** A reviewer will ask.
- **Fixed with code:** Per-event investigation reveals: KXPCECORE-25JUL has MAE≈5.5e-17 (implied mean exactly matched realized), creating an infinite per-event ratio. Two old events (PCECORE-22NOV, 22DEC) have 2-10 snapshots with extreme ratios (3.8, 4.5). Four events lack candle data entirely.
- **Impact:** MEDIUM. Explanation is satisfying — ratio-of-means is robust, mean-of-ratios is not.
- **Action:** Updated KXPCECORE robustness note with full explanation.

### 7. "Add monitoring specification" (SHOULD FIX)
- **Agree.** Increases practical value for Kalshi.
- **Can fix with prose:** Yes.
- **Impact:** MEDIUM.
- **Action:** Added monitoring protocol in Appendix C: 8-event trailing window, flag when ratio >1.0 for 3 consecutive windows, plus PIT-based alerts.

### 8. "Clarify OOS diagnostic value" (SHOULD FIX)
- **Agree.**
- **Can fix with prose:** Yes, one sentence.
- **Impact:** LOW.
- **Action:** Added "designed as a retrospective monitoring diagnostic analogous to a statistical process control chart" in Section 2.

### 9. "Fetch KXRETAIL" (SHOULD FIX → DECLINED)
- **Disagree with priority.** The critique correctly downgraded this. 11 series is sufficient. KXRETAIL would add one more data point but wouldn't change any conclusions.
- **Impact:** LOW.
- **Action:** Not pursued this iteration.

## Code Changes

| File | Change | Result |
|------|--------|--------|
| `scripts/iteration6_analyses.py` | NEW — comprehensive iteration 6 analysis script | PIT for 7 new series, serial correlation for 8 series, horse race for KXU3/KXFRM, GDP temporal (partial), KXPCECORE investigation |
| `data/iteration6/iteration6_results.json` | NEW — all iteration 6 results | JSON with PIT, serial correlation, horse race, KXPCECORE data |

## Paper Changes

1. **Section 2 (CRPS/MAE Diagnostic)**: Added two sentences: (a) CPI ratio=1.32 despite d=−0.85 point forecast preempts "good point forecast inflates ratio" attack; (b) "retrospective monitoring diagnostic" clarification.
2. **Section 3 (Horse Race)**: NEW subsection "Cross-Series Point Forecast Horse Race" with 3-series comparison table (CPI, KXFRM, KXU3). KXFRM beats RW with d=−0.55.
3. **Section 4 (PIT Diagnostic)**: Replaced 4-series table with full 11-series table. Added interpretive paragraph identifying overconcentration as universal failure mode and 3 series that reject uniformity.
4. **Section 4 (Serial Correlation)**: Replaced 3-series paragraph with full 8-series table. KXU3 mean-reversion finding. 7/8 independent.
5. **Section 4 (KXPCECORE)**: Full discrepancy explanation (MAE≈0 outlier, low-snapshot old events, missing candle data).
6. **Appendix A**: Updated to reflect full 11-series PIT coverage.
7. **Appendix C**: Added monitoring protocol specification (8-event window, PIT-based alerts).
8. **Methodology**: Added FRED UNRATE and MORTGAGE30US to external data sources; added PIT and cross-series horse race to methods list.
9. **Corrections log**: Added entries 34–37.

## New Results

| Analysis | Key Finding | Statistical Evidence |
|----------|-------------|---------------------|
| PIT (11 series) | 5/11 well-calibrated, 3/11 reject uniformity, universal overconcentration | KXU3 mean=0.502; KXCPIYOY KS p=0.016; all std(PIT) < 0.289 |
| KXFRM vs RW | Kalshi beats random walk | d=−0.55, p<0.001, n=61 |
| KXU3 vs RW | Kalshi matches random walk | d=−0.07, p=0.191, n=30 |
| KXU3 vs trailing | Kalshi beats trailing mean | d=−0.97, p<0.001, n=30 |
| Serial correlation | 7/8 series independent | Only KXU3 significant (ρ=−0.54, p=0.002) |
| KXPCECORE discrepancy | MAE≈0 outlier explains 2.06→1.22 | KXPCECORE-25JUL: realized=implied_mean=0.3 |

## Pushbacks

### Declined: KXRETAIL fetch
The critique correctly downgraded this to "should fix." With 11 series and 248 events, the marginal value of a 12th series is minimal. KXRETAIL would need to have very extreme results (ratio <0.4 or >1.5) to change any conclusion.

### GDP temporal snapshot sensitivity: partially addressed
Only 3 GDP events had accessible data through the strike_markets pipeline. The full 9-event GDP dataset spans two data pipelines (exp7 old-naming + exp12 new-naming). Fully integrating these would require significant pipeline work for modest incremental value — GDP already has CI [0.31, 0.77] excluding 1.0, LOO [0.45, 0.51], and n=9 making it the paper's crown jewel.

## Remaining Weaknesses

1. **GDP temporal snapshot sensitivity incomplete.** Only 3 of 9 events had accessible CDF data through the current pipeline. **Fixable with code** but requires cross-experiment pipeline integration. The existing GDP CI and LOO results are already very strong.

2. **CPI temporal split still underpowered (p=0.18).** Needs ~95 events, only 33 exist. **Not fixable** with current data.

3. **FED n=4.** Genuinely structural. **Not fixable.**

4. **Horse race limited to 3 series.** Could extend to KXCPICORE (CPILFESL), KXCPIYOY (CPIAUCSL), but marginal value is lower since these CPI variants would be highly correlated. **Fixable with code** but lower priority.

5. **PIT overconcentration mechanism not explained.** All 11 series show std(PIT) < 0.289. Is this due to thin markets, bid-ask spreads compressing prices toward 0.5, or genuine market overconfidence? Would require order book data to investigate. **Not fixable** without LOB data from Kalshi.
