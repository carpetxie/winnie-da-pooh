# Critique — Iteration 6

STATUS: CONTINUE

## Overall Assessment

The paper has undergone a remarkable transformation. The expansion from 7→11 series (93→248 events), the honest reporting of the simple-vs-complex OOS failure, and the reframing around "distributions add value for 9/11 series" represent exactly the kind of intellectual honesty that makes research credible. The code is methodologically sound. The remaining issues are about strengthening an already-solid paper rather than fixing fundamental flaws — with two important exceptions: PIT coverage and the missing cross-series horse race.

## Data Sufficiency Audit

**The dataset is now adequate for the paper's central claims but has two analytical coverage gaps.**

### Current state: 11 series, 248 events
This is a genuine achievement — the paper now covers the vast majority of Kalshi's multi-strike economic markets. The sign test (147/248, p=0.004) and LOO unanimity across 8 of 9 below-1.0 series provide strong support for the headline finding.

### Remaining unfetched series
The API discovery (iteration 3) found 9 additional series. 7 of 9 have been incorporated. Two remain:

| Series | Ticker | Status | Priority |
|--------|--------|--------|----------|
| Retail Sales | KXRETAIL | Not fetched | Low-medium |
| All-Items CPI | KXACPI | Not fetched | Low (likely redundant with CPI/KXCPI) |

**Assessment:** Unlike iterations 3-5 where unfetched series were a critical blocker, the remaining 2 series are unlikely to change the paper's conclusions. KXACPI is likely redundant with the existing CPI series. KXRETAIL would be nice-to-have but isn't critical. **I'm downgrading this from "must fix" to "should fix."** The 11-series, 248-event dataset is sufficient for the claims made.

### Where data sufficiency still matters: individual series CIs
Only **GDP** has a CI that excludes 1.0. Jobless Claims is borderline [0.37, 1.02]. Per the power analysis, JC needs ~20-25 events. With 16 events currently, this requires waiting for new events to settle — not a code fix.

### PIT analysis covers only 4 of 11 series — THIS IS THE GAP
The paper reports PIT for CPI, JC, GDP, and FED (the original 4 series). The code in experiment13/run.py hard-codes PIT for only `["KXCPI", "KXJOBLESSCLAIMS"]` (line 1133) — GDP and FED PIT come from experiment7's separate pipeline. **The 7 new series (KXU3, KXCPICORE, KXCPIYOY, KXFRM, KXADP, KXISMPMI, KXPCECORE) have zero PIT analysis.** This is fixable with code — the CDF snapshots exist in `data/new_series/{SERIES}_results.json`, and the PIT computation is straightforward (interpolate realized on CDF, compute 1 - survival). The researcher acknowledged this gap ("deferred because it requires building CDF objects for each event").

A paper titled "distributional calibration" that validates calibration via PIT for only 36% of its series has a conspicuous hole.

### Horse race limited to CPI — second analytical gap
The CPI horse race is one of the paper's strongest sections (d=−0.85 vs random walk). FRED benchmark mappings already exist in `fetch_expanded_series.py` for KXU3→UNRATE, KXFRM→MORTGAGE30US, KXCPICORE→CPILFESL, KXCPIYOY→CPIAUCSL. Running horse races for even 2 additional series would transform this from "a CPI case study" into "systematic evidence." The researcher acknowledged this as fixable.

## Reflection on Prior Feedback

### Iteration 5 — all 8 points addressed:
1. ✅ All 11 series incorporated
2. ✅ Simple-vs-complex thesis rewritten (handled better than expected)
3. ✅ KW heterogeneity reported honestly with evolution table
4. ✅ KXPCECORE added (n=13, ratio=1.22)
5. ✅ KXADP comma-parsing bug fixed
6. ✅ KXFRM snapshot sensitivity investigated
7. ✅ Paper reframed around "9/11 series add value"
8. ✅ OOS predictions reported prominently

### What I'm dropping:
- KXRETAIL/KXACPI as "must fix" — downgraded. 11 series is sufficient.
- Simple-vs-complex reframing concerns — handled excellently.
- KXFRM data quality — sensitivity analysis is convincing (ratio stable 0.84-0.86).
- KXADP parsing — fixed.

### No pushbacks from researcher this iteration
The researcher agreed with all critique points and executed them faithfully. No disagreements to adjudicate.

## Scores

| Criterion | Score | Delta | Comment |
|-----------|-------|-------|---------|
| Data Sufficiency | 7/10 | +3 | 11 series, 248 events is strong. PIT and horse race analytical gaps prevent higher score. |
| Novelty | 7/10 | +1 | CRPS/MAE ratio, point-distribution decoupling, OOS failure transparency all novel. |
| Methodological Rigor | 7/10 | +3 | BCa bootstrap, LOO, Bonferroni, pre-registered OOS, sign test — comprehensive. PIT coverage gap is the main issue. |
| Economic Significance | 7/10 | +1 | "9/11 series: use the full distribution" is directly actionable. |
| Blog Publishability | 7/10 | +3 | Honest, rigorous, actionable. Two more analyses bring it to publication-ready. |

## Strength of Claim Assessment

### Claim 1: "Prediction market distributions add value for 9 of 11 economic series"
**Status: CONCLUSIVE. Correctly labeled.**
Sign test p=0.004, LOO unanimity in 8/9 below-1.0 series. This is the paper's strongest finding. No change needed.

### Claim 2: "GDP is the standout (CRPS/MAE=0.48, CI excludes 1.0)"
**Status: CONCLUSIVE. Correctly labeled.**
Only CI that excludes 1.0. LOO range [0.45, 0.51]. n=9 is small but signal is unambiguous.

### Claim 3: "Point and distributional calibration can diverge independently"
**Status: SUGGESTIVE — could be labeled STRONGER.**
CPI evidence is compelling: d=−0.85 for point forecasts vs random walk, while CRPS/MAE=1.32 in the same period. The paper correctly calls this "to our knowledge, the first empirical demonstration." This hedging is appropriate but the paper could be slightly bolder — the finding survives all robustness checks and the mechanism is clearly demonstrated.

### Claim 4: "The simple-vs-complex hypothesis fails OOS"
**Status: CONCLUSIVE NEGATIVE. Correctly labeled.**
Pre-registered 2/4, both complex wrong. Evolution table (r=0.43→0.16) is a methodological contribution. Admirably transparent.

### Claim 5: "Core PCE and FED are consistently problematic"
**Status: SUGGESTIVE. Appropriately hedged.**
LOO unanimity for both. But n=4 (FED) and n=13 (PCE) limit confidence. Paper correctly avoids over-interpreting.

### Claim 6: "Volume does not predict distributional quality" (ρ=0.14, p=0.27)
**Status: SUGGESTIVE. Could be STRONGER and more prominent.**
This null result has important market design implications — Kalshi can't just "add more liquidity" to fix Core PCE/FED. The paper mentions it in passing in Section 4. It deserves more emphasis in Appendix C (Market Design Implications).

## Novelty Assessment

**What's genuinely new:**
1. **CRPS/MAE ratio as a per-series diagnostic** — no prior work applies CRPS to prediction market multi-strike contracts at this granularity with MAE normalization.
2. **Point-distribution decoupling** — first demonstration that a prediction market can have accurate point forecasts with miscalibrated spreads.
3. **Pre-registered OOS failure reported transparently** — uncommon in applied finance. The methodological lesson is itself publishable.
4. **11-series scope** — most comprehensive distributional calibration study of a prediction market to date.

**What would increase novelty further:**
1. **Full 11-series PIT analysis** — would make this the most comprehensive PIT analysis of any prediction market.
2. **Cross-series horse race** — "Kalshi beats random walk across multiple economic series" is a much stronger headline than "Kalshi CPI beats random walk."
3. **Real-time monitoring specification** — the rolling CRPS/MAE analysis naturally leads to a deployable monitoring protocol. Even a brief specification increases practical value.

## Robustness Assessment

### Code review: methodology is sound ✅
Verified in experiment12/distributional_calibration.py and experiment13/run.py:
- CRPS: piecewise integration with scale-aware tail extension, proper CDF construction from survival functions
- BCa bootstrap: 10,000 resamples with percentile fallback
- LOO: ratio-of-means (not mean-of-ratios)
- PIT: 1 − interpolated survival function
- Comma-parsing fix applied and verified for KXADP

### Potential hostile reviewer attacks:

1. **"CRPS/MAE > 1 could just mean good point forecasts inflate the ratio."** The CPI case actually refutes this — CPI has the *best* point forecasts (d=−0.85 vs random walk) AND ratio=1.32 post-break. This means the high ratio reflects genuinely miscalibrated spreads, not artificially low MAE. **Add one explicit sentence making this point in Section 2.** This is the most obvious attack and the paper has the perfect defense but doesn't deploy it.

2. **"Mid-life snapshot is arbitrary."** JC temporal stability (CIs exclude 1.0 at all five snapshots) partially addresses this. **Extend to GDP** — if GDP ratio < 1.0 at all snapshots, the paper's strongest result becomes bulletproof.

3. **"In-sample CRPS/MAE ratios; OOS exercises all fail."** The paper reports three OOS exercises — all show null predictive power. A hostile reviewer could argue the ratio is descriptive, not predictive. The paper's defense (rolling-window monitoring detects regime shifts) is present but could be crisper. Consider a one-sentence rebuttal: "The CRPS/MAE ratio is designed as a diagnostic tool for monitoring, analogous to a control chart, not as a predictive model."

4. **"248 events ≠ 248 independent observations."** The serial correlation analysis (lag-1 ρ ≈ 0) addresses this but only for 3 series (CPI, JC, GDP). **Extend to all 11 series** — this is a one-loop computation that preempts the objection entirely.

### KXPCECORE ratio discrepancy (2.06 → 1.22)
The paper notes this changed between iterations but doesn't explain the mechanism. The n dropped from 15 to 13, suggesting 2 events lacked candle data in the refetch. A reviewer will ask. Even "two events had insufficient candle data on the second API fetch, likely due to Kalshi's candle retention policy" is acceptable if documented. Alternatively, check which 2 events were lost and whether they had extreme ratios.

## The One Big Thing

**Extend the PIT analysis to all 11 series.**

This is the single most impactful remaining improvement because:
1. It fills the most conspicuous methodological gap — a "distributional calibration" study that validates calibration for only 4/11 series.
2. It makes specific claims stronger: if GDP's PIT is near-uniform, the CRPS/MAE=0.48 finding is even more powerful. If Core PCE's PIT shows systematic bias, it explains *why* the ratio is >1.
3. It's mechanistically informative — PIT reveals *how* distributions fail (overconfident? biased high/low?), complementing CRPS/MAE which only tells *that* they fail.
4. The infrastructure exists — experiment13/run.py already computes PIT for 2 series.

**Implementation:** In `experiment13/run.py` line 1133, change `for pit_series in ["KXCPI", "KXJOBLESSCLAIMS"]:` to iterate over all series in `crps_df["series"].unique()`. For new series, load CDF snapshots from `data/new_series/{SERIES}_results.json`. Output: PIT mean, CI, KS test, CvM test for each series. Update paper Appendix A with full 11-series PIT table.

## Other Issues

### Must Fix (blocks publication)

1. **Extend PIT analysis to all 11 series (at minimum the 7 new series with n≥7).** A "distributional calibration" paper that validates calibration via PIT for only 36% of its series is incomplete. KXU3 (n=32), KXCPICORE (n=32), KXCPIYOY (n=34), KXFRM (n=59) all have ample events for meaningful PIT analysis. Even KXADP (n=9), KXISMPMI (n=7), and KXPCECORE (n=13) should be included — the existing 4-series PIT includes GDP (n=9) and FED (n=4), so there's no sample-size justification for excluding them.

2. **Add one explicit sentence in Section 2 addressing the "good point forecast inflates ratio" concern.** Something like: "Note that a high CRPS/MAE ratio does not simply reflect good point forecasts: CPI shows ratio=1.32 despite having the best point forecasts of any benchmark (d=−0.85 vs random walk), confirming that the ratio captures genuine distributional miscalibration." This preempts the most obvious hostile reviewer attack with evidence the paper already has.

### Should Fix (strengthens paper)

1. **Extend the horse race to at least 2 additional series.** KXU3 → UNRATE and KXFRM → MORTGAGE30US are easiest (FRED mappings exist). Even a simplified comparison (Kalshi vs random walk and trailing mean) would be valuable. This transforms Section 3 from "CPI case study" to "systematic evidence."

2. **Extend serial correlation analysis to all 11 series.** Currently computed for CPI, JC, GDP only. One loop, one table. Preempts the "non-independence" attack completely.

3. **Extend temporal snapshot sensitivity to GDP.** GDP is the paper's crown jewel (CI excludes 1.0). Showing ratio < 1.0 at all temporal snapshots (10%, 25%, 50%, 75%, 90%) would make this finding unassailable.

4. **Investigate the KXPCECORE 2.06→1.22 discrepancy.** Check which 2 events were lost (n=15→n=13) and whether they had extreme ratios. Document the explanation — even "candle data retention" is fine.

5. **Fetch KXRETAIL if it has multi-strike settled markets.** Would bring count to 12 series. Low priority but completeness matters.

6. **Add a brief "real-time monitoring" specification.** One paragraph: "We propose computing CRPS/MAE over a trailing window of 8 events per series, flagging when the ratio exceeds 1.0 for 3 consecutive windows. The CPI rolling-window analysis demonstrates this approach detects structural breaks within 2-3 events." This increases practical value for Kalshi substantially.

7. **Clarify the OOS diagnostic value.** Add one sentence: "The CRPS/MAE ratio is designed as a retrospective/monitoring diagnostic analogous to a statistical process control chart, not as a predictive model for individual events."

### New Experiments / Code to Write

1. **PIT extension (highest priority):**
   - File: `experiment13/run.py`, line 1133
   - Change: `for pit_series in crps_df["series"].unique():`
   - For new series: load CDF snapshots from `data/new_series/{series}_results.json`
   - Output: 11-row PIT table (mean PIT, CI, KS p, CvM p)
   - Paper: Replace Appendix A with full table; move to Section 4 if results are interesting

2. **Cross-series horse race (medium priority):**
   - File: extend `experiment13/horse_race.py` or create new module
   - Fetch UNRATE, MORTGAGE30US from FRED
   - Compare Kalshi implied mean vs random walk and trailing mean for KXU3, KXFRM
   - Output: Per-series MAE, Cohen's d vs random walk

3. **Serial correlation for all 11 series:**
   - One loop computing lag-1 Spearman ρ for each series' per-event CRPS/MAE ratios
   - Output: 11-row table

4. **GDP temporal snapshot sensitivity:**
   - Compute CRPS/MAE at 10%, 25%, 50%, 75%, 90% of market life for all 9 GDP events
   - Report whether ratio stays < 1.0 at all snapshots

### Genuinely Unfixable Limitations

1. **FED n=4.** FOMC meets ~8 times/year; only 4 settled multi-strike events exist. Cannot expand without waiting.

2. **No order-book depth data.** Kalshi doesn't expose historical LOB. Cannot directly test thin-book dynamics.

3. **CPI temporal split underpowered (p=0.18, needs ~95 events).** Only 33 exist.

4. **SPF monthly CPI proxy.** No public monthly CPI point forecast exists; annual/12 is best available.

5. **CRPS/MAE ratio has no event-level predictive power** (lag-1 ρ ≈ 0). Useful for aggregate monitoring, not event prediction. This is a genuine limitation of the diagnostic tool itself.

## Verdict

**MINOR REVISIONS**

The paper has evolved from a 4-series pilot with a broken thesis into an 11-series, 248-event comprehensive analysis with honest reporting and a stronger positive finding. The methodology is sound, the code is correct, and the transparency (OOS failure, downgraded findings appendix) is exemplary. The two must-fix items (PIT extension, one clarifying sentence) are straightforward to implement. The should-fix items (horse race extension, serial correlation, GDP temporal sensitivity) would further strengthen an already-solid paper. With these changes, this is publication-ready for the Kalshi Research blog.
