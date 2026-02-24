# Critique — Iteration 5

STATUS: CONTINUE

## Overall Assessment (2-3 sentences)

The paper reports 7 series and 93 events, but the researcher has already computed CRPS/MAE for 10 series and 235 events — and the expanded results **contradict the paper's central thesis.** The simple-vs-complex dichotomy (currently presented as the paper's "strongest and most actionable finding" at p=0.0004, r=0.43) collapses to p=0.044, r=0.16 with 10 series, the Kruskal-Wallis test becomes non-significant (p=0.133), and the pre-registered OOS predictions fail 2/4 (both "complex" predictions wrong). The paper must be rewritten around the actual data, not a cherry-picked subset of it.

## Data Sufficiency Audit

**CRITICAL: The researcher has computed results they haven't incorporated into the paper.**

The file `data/new_series/unified_11series_analysis.json` contains a complete 10-series analysis (235 events) that dramatically changes every major finding. The file `data/new_series/oos_predictions.json` contains a pre-registered OOS test of the simple-vs-complex hypothesis that fails. The paper still reports only 7 series (93 events).

### What's been computed but not reported:

| Series | n | CRPS/MAE | LOO | Type (pre-registered) | In paper? |
|--------|---|----------|-----|----------------------|-----------|
| GDP | 9 | 0.48 | All < 1.0 | Simple | ✅ |
| Jobless Claims | 16 | 0.60 | All < 1.0 | Simple | ✅ |
| ADP Employment | 9 | 0.67 | All < 1.0 | Simple | ✅ |
| CPI YoY (KXCPIYOY) | 34 | **0.67** | **All < 1.0** | **Complex** | ❌ |
| KXU3 (Unemployment) | 32 | **0.75** | **All < 1.0** | Simple | ❌ |
| KXCPICORE (Core CPI m/m) | 32 | **0.82** | **All < 1.0** | **Complex** | ❌ |
| CPI | 33 | 0.86 | All < 1.0 | Complex | ✅ |
| KXFRM (Mortgage Rates) | 59 | **0.85** | **All < 1.0** | Simple | ❌ |
| ISM PMI | 7 | 0.97 | Mixed | Mixed | ✅ |
| FED | 4 | 1.48 | All > 1.0 | Discrete | ✅ |
| Core PCE (KXPCECORE) | 15 | 2.06 | All > 1.0 | Complex | ✅ |

**Key observations:**
1. **8 of 10 series** show CRPS/MAE < 1.0 with LOO unanimity. Only FED and KXPCECORE are consistently harmful.
2. KXCPICORE (Complex, predicted >1.0) has ratio **0.82** — distributions ADD value. OOS prediction WRONG.
3. KXCPIYOY (Complex, predicted >1.0) has ratio **0.67** — distributions ADD value. OOS prediction WRONG.
4. The "complex" series don't behave as predicted. The simple-vs-complex dichotomy is an artifact of KXPCECORE and FED, not a systematic pattern.

### What this means for the paper's claims:

| Claim (current paper) | 7-series evidence | 10-series evidence | Status |
|----------------------|-------------------|-------------------|--------|
| Simple-vs-complex dichotomy p=0.0004, r=0.43 | Strong | **p=0.044, r=0.16** | **BROKEN** |
| Kruskal-Wallis H=18.5, p=0.005 | Strong | **H=12.4, p=0.133** | **BROKEN** |
| "Complex indicators have harmful distributions" | Supported by PCE, CPI post-break, FED | **Contradicted by KXCPICORE (0.82) and KXCPIYOY (0.67)** | **BROKEN** |
| "Distributional quality depends on signal complexity" | Plausible | **OOS prediction 50% hit rate** | **BROKEN** |
| Most series show distributions add value | True for 5/7 | **True for 8/10** | Strengthened |

### What's still available but not fetched:

- **KXRETAIL** (Retail Sales): Mentioned in API discovery, not fetched
- **KXACPI** (Adjusted CPI?): Mentioned in API discovery, not fetched
- These are minor — the 10-series dataset is already sufficient to draw conclusions

### KXFRM data quality concern:

KXFRM has a mean of only **15.5 snapshots per event** — vastly lower than other series (298–817). This suggests very thin candle data, possibly because markets are short-lived or illiquid. With only 15 hourly snapshots, the mid-life CDF may not be representative. This needs investigation before including KXFRM with equal weight.

### KXADP parsing concern:

Some KXADP events show realized values of 41.0 and 104.0 when the raw values are "41,000" and similar — suggesting a comma-parsing bug that strips the thousands. If realized values are wrong by 1000x, CRPS and MAE are both wrong. The paper already reports KXADP values from the original fetch; verify the expanded results use correctly parsed values.

## Reflection on Prior Feedback

### Iteration 4 raised:
1. **"Promised expansion not delivered"** — This has been PARTIALLY addressed. The researcher fetched the data (KXU3, KXCPICORE, KXFRM, KXCPIYOY) and ran the unified analysis. But they haven't incorporated the results into the paper. This is now the critical blocker.
2. **"API path bug"** — Fixed in `fetch_expanded_series.py`.
3. **"KXADP/KXISMPMI reproducibility"** — Expanded data now has `n_snapshots` field, addressing the concern.
4. **"Simple-vs-complex needs OOS validation"** — The researcher ran an OOS test. It failed 2/4. But the paper doesn't report this.

### What I'm dropping:
- The API path bug (fixed)
- Reproducibility of KXADP/KXISMPMI (now have n_snapshots)
- Crypto as contrast case (the economic series expansion is sufficient)

## Scores

| Criterion | Score | Delta | Comment |
|-----------|-------|-------|---------|
| Data Sufficiency | 4/10 | -1 | Data EXISTS (235 events, 10 series) but paper reports only 93 events from 7 series. The unreported data contradicts central claims. |
| Novelty | 6/10 | -2 | The CRPS/MAE ratio remains novel, but the "simple-vs-complex" framing — the paper's strongest claim — fails OOS. The actual finding ("most series add value, 2 outliers don't") is less novel but more honest. |
| Methodological Rigor | 4/10 | -3 | Selectively reporting 7 of 10 computed series is a fatal methodological flaw, regardless of whether it's intentional. The paper presents p=0.0004 when the full-data p is 0.044 with trivial effect size. |
| Economic Significance | 6/10 | -1 | The revised finding ("distributions add value for 80% of series") is still actionable for Kalshi but less dramatic than the current framing. |
| Blog Publishability | 4/10 | -1 | Cannot publish with known contradictory evidence sitting in the data directory. |

## Strength of Claim Assessment

### Claim 1: "Simple-vs-complex dichotomy is the paper's strongest finding" (p=0.0004, r=0.43)
**Current label:** Conclusive. **Actual status: REFUTED by the researcher's own data.**

With 10 series (235 events): Mann-Whitney p=0.044, r=0.157 — technically significant at 5% but with a **trivial effect size** (was "large" at r=0.43). The pre-registered OOS test fails 2/4. KXCPICORE (core CPI m/m, a composite index) shows ratio=0.82 with all LOO < 1.0, and KXCPIYOY (CPI year-over-year) shows ratio=0.67 with all LOO < 1.0. These are textbook "complex" indicators that behave like "simple" ones.

**Recommendation:** This claim must be either abandoned or substantially reframed. The honest finding is: "Most series show distributional value. Two series (Core PCE and FED) are outliers. The mechanism driving these outliers is unclear."

### Claim 2: "Kruskal-Wallis heterogeneity is highly significant" (H=18.5, p=0.005)
**Current label:** Conclusive. **Actual status: NON-SIGNIFICANT with full data.**

With 10 series: H=12.4, p=0.133. There is some heterogeneity (the ratios range from 0.48 to 2.06), but the formal test does not reject the null. Note: KXPCECORE is missing from the unified analysis (10 series, not 11). Adding it back would likely increase H, potentially restoring significance. But the paper cannot claim p=0.005 when p=0.133 is the full-data result.

**Recommendation:** Report both. If KXPCECORE inclusion restores significance, report that as well. But the paper must lead with the full-data result.

### Claim 3: "Distributions add value for most economic series"
**Current label:** Suggestive. **Actual status: This is now the paper's STRONGEST finding and should be CONCLUSIVE.**

8 of 10 series have CRPS/MAE < 1.0 with LOO unanimity. This is a much stronger and more interesting finding than the dichotomy. The paper should lead with this: "Prediction market distributions add value across the vast majority of economic series."

### Claim 4: "CPI point forecasts beat random walk" (d=-0.85, p_adj=0.014)
**Status: Conclusive, correctly labeled.** No change needed.

### Claim 5: "Point and distributional calibration can diverge independently"
**Status: Suggestive, could be STRONGER.** This finding is genuine and novel — it doesn't depend on the simple-vs-complex framing. The CPI temporal break demonstrates it clearly.

## Novelty Assessment

**What's genuinely new (survives the expanded data):**
1. CRPS/MAE ratio as a diagnostic tool — still novel, still useful
2. Point-distribution decoupling — still novel, still demonstrated
3. "Distributions add value for most series" — now supported by 8/10 series, stronger than before
4. CPI temporal structural break — still interesting
5. OOS failure of the simple-vs-complex hypothesis — genuinely informative and publishable if reported honestly

**What's NOT new (fails with expanded data):**
1. "Simple-vs-complex dichotomy" as the main finding — refuted OOS
2. "Signal complexity determines distributional quality" — refuted by KXCPICORE and KXCPIYOY

**New analyses that would increase novelty:**
1. **What distinguishes KXPCECORE and FED from other series?** If it's not "complexity," what is it? KXPCECORE is the Fed's preferred inflation measure — maybe attention/stakes matter more than signal complexity. FED involves discrete decisions. These are 2 very different mechanisms.
2. **Cross-series horse race:** Extend the CPI horse race (vs SPF, TIPS, trailing mean, random walk) to other series with FRED benchmarks. You have the FRED series IDs already mapped in `fetch_expanded_series.py`.

## Robustness Assessment

### The full-data analysis breaks the paper's robustness story
The paper currently has an extensive robustness section (Section 4) built around the 7-series results. With 10 series, the heterogeneity tests fail, the simple-vs-complex grouping becomes trivial in effect size, and the "which mechanism?" section needs rewriting.

### KXFRM data quality is a concern
59 events but only 15.5 mean snapshots per event. If mid-life CDFs are built from very few price observations, CRPS estimates may be noisy. The paper should either:
- Investigate and report this
- Apply a minimum-snapshots threshold (e.g., ≥50) and show sensitivity
- Or note it as a robustness caveat

### KXADP parsing issue
Per-event data shows `realized=41.0` with `exp_val_raw="41,000"` for KXADP-25DEC. If "41,000" was parsed as 41 instead of 41000, the entire KXADP CRPS computation is wrong for that event. Check all events in expanded results for similar parsing errors.

### Missing: KXPCECORE in unified analysis
The unified 11-series analysis file actually contains 10 series (KXPCECORE is absent). This needs to be corrected. Adding KXPCECORE (n=15, ratio=2.06) would increase total events to ~250 and might restore Kruskal-Wallis significance — this is important to test.

## The One Big Thing

**Incorporate the full 10+ series results into the paper and rewrite the central thesis.**

The paper's central thesis (simple-vs-complex dichotomy) is contradicted by the researcher's own expanded data sitting in `data/new_series/`. The paper must:
1. Report all 10 (ideally 11 with KXPCECORE) series
2. Acknowledge the OOS prediction failure honestly
3. Reframe the central finding from "simple-vs-complex dichotomy" to "distributions add value for 80%+ of series; two outliers (KXPCECORE and FED) drive most of the heterogeneity"
4. Investigate what makes KXPCECORE and FED different (it's NOT just "complexity")

This is not a minor revision. The entire narrative arc — abstract, executive summary, Section 2, Section 4 — needs restructuring around the actual finding.

## Other Issues

### Must Fix (blocks publication)

1. **INCORPORATE ALL COMPUTED DATA.** The paper reports 7 series (93 events) while 10 series (235 events) sit in `data/new_series/`. The full-data results contradict the paper's central claim. You cannot publish a paper that selectively reports a subset of computed results when the full dataset tells a different story.

2. **REWRITE THE SIMPLE-VS-COMPLEX THESIS.** The pre-registered OOS test (in `oos_predictions.json`) shows 50% hit rate — KXCPICORE (0.82) and KXCPIYOY (0.67) were predicted >1.0 but show distributions adding value. The simple-vs-complex dichotomy at p=0.0004 is an artifact of analyzing 7 series. With 10 series: p=0.044, r=0.157 (trivial effect). The paper must honestly report both results and reframe accordingly.

3. **ADD KXPCECORE TO UNIFIED ANALYSIS.** The unified analysis JSON has 10 series but omits KXPCECORE (which was analyzed separately in the first expansion). Re-run the unified analysis with all 11 series and report the result. This may partially restore the KW significance, which is worth knowing.

4. **VERIFY KXADP REALIZED VALUE PARSING.** KXADP-25DEC shows `realized=41.0` but `exp_val_raw="41,000"`. If this is a comma-parsing bug, CRPS/MAE for affected events is meaningless. Check all events in expanded results for similar parsing errors.

### Should Fix (strengthens paper)

1. **Investigate KXFRM snapshot count.** Mean 15.5 snapshots vs 300-800 for other series. Either apply a minimum threshold, show results are robust to excluding low-snapshot events, or note the limitation.

2. **Reframe the paper around the ACTUAL finding.** "Prediction market distributions add value across 80% of economic series" is a STRONGER and more interesting claim than "there's a simple-vs-complex dichotomy." Lead with the positive finding. The outliers (KXPCECORE, FED) become the interesting puzzle, not the main result.

3. **Update the executive summary table to 10-11 series.** The current 7-column table is incomplete.

4. **Report both 7-series and 10-series results for transparency.** Show the reader how the heterogeneity result changes as you add data. This demonstrates intellectual honesty and the danger of premature generalization — which is itself a publishable methodological lesson.

5. **Investigate what actually drives KXPCECORE's poor performance.** Core PCE at 2.06 is a massive outlier. Is it a liquidity issue? Strike structure? Market age? The paper says "volume doesn't predict CRPS/MAE" but that was computed on 7 series — re-run with 10.

6. **Report the OOS prediction results prominently.** The fact that you pre-registered predictions and they partially failed is GOOD SCIENCE. Report it honestly — the failure of the complex predictions is informative. "We hypothesized X, tested it, and found the hypothesis was partially wrong" is far more credible than omitting the test.

### New Experiments / Code to Write

1. **Re-run `scripts/unified_analysis_11series.py` with KXPCECORE included.** Currently outputs 10 series. Load KXPCECORE per-event data and include it. Report 11-series KW test and updated simple-vs-complex Mann-Whitney.

2. **Sensitivity analysis: minimum snapshot threshold.** Re-compute unified results excluding events with <50 snapshots (primarily affects KXFRM with mean=15.5). Report whether main findings change.

3. **Volume-CRPS regression with all series.** Re-run Spearman correlation from `robustness_analyses.py` with all 235+ events. Does the null result hold?

4. **PIT diagnostic for new series.** The paper reports PIT for 4 series. Extend to all 10-11.

5. **Per-series horse race.** Extend the CPI horse race to Unemployment (vs UNRATE), Mortgage Rates (vs MORTGAGE30US), and GDP (vs A191RL1Q225SBEA). FRED series IDs already mapped in `fetch_expanded_series.py`.

6. **Comma-parsing audit.** Search all per-event results for `exp_val_raw` values containing commas and verify `realized` was correctly parsed.

### Genuinely Unfixable Limitations

1. **FED n=4.** FOMC meets ~8 times/year; Kalshi only has 4 settled multi-strike events. Cannot expand without waiting. Truly structural.

2. **No order-book depth data.** Kalshi doesn't expose historical LOB. Cannot directly test the thin-book hypothesis. No API endpoint exists.

3. **CPI temporal split underpowered (p=0.18).** Would need ~95 events; only 33 exist. Cannot manufacture more CPI releases.

4. **SPF monthly CPI proxy.** No public monthly CPI point forecast exists; annual/12 is the best available proxy.

## Verdict

**MAJOR REVISIONS**

The paper has a genuine contribution (CRPS/MAE diagnostic, point-distribution decoupling, 8/10 series showing distributional value), but its central thesis is contradicted by its own computed data. The researcher has done the hard work of fetching and analyzing 10 series — now the paper must honestly report all of them and rewrite the narrative accordingly. The good news: the revised finding ("distributions add value for 80%+ of series") is arguably **more interesting and more useful for Kalshi** than the original dichotomy claim. A paper that says "prediction market distributions work!" is better for the Kalshi Research blog than one that says "they work for some but not others."
