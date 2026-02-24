# Critique — Iteration 1

STATUS: CONTINUE

## Overall Assessment (2-3 sentences)

The CRPS/MAE ratio framing is genuinely novel and the paper demonstrates impressive methodological self-discipline (Appendix C is excellent). However, the headline finding — that distributional quality is heterogeneous across series — rests on only 2 series (CPI and Jobless Claims), while the researcher's own cached data contains **at least 4 additional multi-strike series** (old-prefix CPI with 23 more events, FED with 23 events, old-prefix GDP with 11 events, plus crypto daily markets) that are unused. This is the paper's critical weakness and it is entirely fixable.

## Data Sufficiency Audit

**This is the #1 issue and blocks publication in its current form.**

### What's in the data vs. what's analyzed

I audited `data/exp2/raw/targeted_markets.json` and the `STRIKE_SERIES` filter in `experiment7/implied_distributions.py`. The filter is set to `{"KXCPI", "KXGDP", "KXJOBLESSCLAIMS"}`, but the cached data contains these additional multi-strike series:

| Series | Prefix | Events | Markets | Status in Paper |
|--------|--------|--------|---------|----------------|
| CPI (old naming) | `CPI` | 23 | 209 | **UNUSED — same series, older data (Dec 2022 – Oct 2024)** |
| Fed Funds Rate | `FED` | 23 | 259 | **UNUSED — entirely new series** |
| GDP (old naming) | `GDP` | 11 | 94 | **UNUSED — same series, older data** |
| KXCPI (new naming) | `KXCPI` | 14 | 91 | ✅ Used |
| KXJOBLESSCLAIMS | `KXJOBLESSCLAIMS` | 24 | 212 | ✅ Used (16 with realized) |
| KXGDP (new naming) | `KXGDP` | 5 | 33 | Excluded (n=3 too small) |
| KXFED | `KXFED` | 1 | 11 | Excluded |
| BTC Daily | `KXBTCD` | 14 | 1000 | **UNUSED — crypto multi-strike** |
| ETH Daily | `KXETHD` | 14 | 1000 | **UNUSED — crypto multi-strike** |
| SOL Daily | `KXSOLD` | 14 | 1000 | **UNUSED — crypto multi-strike** |

**Key finding:** The `CPI` and `KXCPI` prefixes are the **same underlying series** with a naming convention change around Nov 2024. The `CPI` prefix covers Dec 2022 – Oct 2024 (23 events), and `KXCPI` covers Nov 2024 – present (14 events). Combined, that's **37 CPI events**, nearly 3× what the paper uses. The same applies to `GDP` vs `KXGDP`.

**The regex `r'^([A-Z]+)'` in `extract_strike_markets()` correctly extracts `CPI` and `FED` as prefixes — they're simply not in the `STRIKE_SERIES` set.**

### What this means for the paper's claims

1. **"n=14 CPI events" is artificially small.** Adding the 23 old-prefix CPI events would give n=37, dramatically improving power. The power analysis says CPI vs Historical needs n=61 for 80% power — going from 14 to 37 cuts the gap by more than half.

2. **"Heterogeneity rests on only 2 series" is fixable.** Adding FED (23 events) gives a third independent economic series. The paper's hypothesis that "monthly composites should have CRPS/MAE > 1" is directly testable with FED rate markets (which settle at FOMC meetings — roughly 8 per year, not monthly, and covering a single rate, not a composite).

3. **Crypto daily markets** (KXBTCD, KXETHD, KXSOLD) provide ~14 events each at very different scales and frequencies. They're not economic releases but could serve as a high-frequency contrast case.

4. **GDP goes from n=3 to n=14+** by combining old and new prefixes, making it usable for statistical tests.

### What code changes are needed

1. **Expand `STRIKE_SERIES`** in `experiment7/implied_distributions.py`:
   ```python
   STRIKE_SERIES = {"KXCPI", "CPI", "KXGDP", "GDP", "KXJOBLESSCLAIMS", "FED", "KXFED"}
   ```
   Then merge old/new prefixes into canonical series names for analysis.

2. **Fetch candle data** for old-prefix markets (CPI-*, FED-*, GDP-*) via experiment2's pipeline. These may already exist in `data/exp2/raw/candles/`.

3. **Add FRED benchmark for FED**: fetch the effective federal funds rate (FRED series `FEDFUNDS` or `DFF`) for historical CRPS comparison.

4. **Update `_parse_expiration_value()`** if old-prefix markets use different value formats.

5. **Re-run experiments 7, 12, 13** with expanded dataset.

This is ~2-4 hours of engineering work that would transform the paper from "suggestive with n=14–16" to "well-powered with n=30–40+ across 4 series."

## Scores

| Criterion | Score | Delta | Comment |
|-----------|-------|-------|---------|
| Data Sufficiency | 3/10 | — | 2–3× more data available in cached files alone; FED series completely ignored |
| Novelty | 7/10 | — | CRPS/MAE ratio framing is genuinely new; point-vs-distribution decoupling finding is interesting |
| Methodological Rigor | 7/10 | — | Impressive correction log; BCa bootstrap, LOO, block bootstrap all sound; but in-sample only |
| Economic Significance | 6/10 | — | Actionable for market design, but claims are necessarily tentative at n=14–16 |
| Blog Publishability | 5/10 | — | Interesting enough concept, underpowered enough execution; would not recommend in current form |

## Strength of Claim Assessment

### Claim 1: "Jobless Claims distributions add value (CRPS/MAE=0.66)"
**Assessment: Suggestive, approaching conclusive.** The CI excludes 1.0, LOO is unanimous, temporal stability is strong. With n=16, this is about as strong as you can get. Could the researcher add more JC events? The data has 24 events but only 16 have realized outcomes — check whether the 8 excluded events could be recovered. **The claim is stated at appropriate strength.**

### Claim 2: "CPI distributions are harmful (CRPS/MAE=1.58)"
**Assessment: Suggestive, but artificially underpowered.** The CI barely excludes 1.0 (lower bound 1.04). With 23 additional CPI events available under the old prefix, this claim could be made much more strongly — or potentially refuted if the old-prefix events show different behavior. **The paper hedges appropriately given n=14, but n=14 is the researcher's choice, not a data constraint.**

### Claim 3: "Point and distributional calibration can diverge independently"
**Assessment: The strongest conceptual contribution.** This is genuinely novel in the prediction market context. The evidence is adequate (CPI beats random walk at d=-0.85 while CRPS/MAE=1.58). **This claim could be stated MORE strongly** — the paper buries it in Section 3 when it should arguably be the headline.

### Claim 4: "Heterogeneity is statistically significant (Mann-Whitney p=0.003)"
**Assessment: Speculative at 2 series, would be conclusive at 4+.** A test comparing 2 groups is inherently limited. Adding FED and expanded GDP would turn this from "these two series differ" into "there's a systematic pattern across economic series." **This is underreached — the finding is likely real but the evidence base is artificially narrow.**

### Claim 5: "Surprise magnitude explains CRPS/MAE variation"
**Assessment: Suggestive, well-analyzed.** The CRPS/uniform comparison is a smart way to disentangle mechanical effects. The Spearman ρ=−0.68 (p=0.008) is reasonably powered. **Appropriately stated.**

## Novelty Assessment

**What's genuinely new:**
1. CRPS/MAE ratio as a diagnostic — I'm not aware of this specific ratio being proposed elsewhere, though the CRPS/MAE decomposition is implicit in ensemble forecast verification.
2. Point-vs-distribution calibration decoupling in a market context — novel application of known forecasting concepts.
3. The "Appendix C" honesty about invalidated findings — unusual and valuable for research credibility.

**What's less novel than claimed:**
- The no-arbitrage comparison to SPX options is interesting but has been done better in other contexts (and the measurement base difference the paper acknowledges weakens it).
- The TIPS Granger-causality finding is expected and not especially informative.

**New analyses to increase novelty:**
1. **Cross-series prediction:** Can CRPS/MAE at time t predict CRPS/MAE at time t+1? If the ratio is persistent, it's useful as a real-time monitor.
2. **Liquidity-CRPS relationship:** Correlate per-event volume/bid-ask spread with CRPS/MAE. This would test mechanism 4 directly.
3. **Rolling CRPS/MAE:** With 37 CPI events, you could plot CRPS/MAE over time to see if it's improving as the market matures.

## Robustness Assessment

### Code review findings

1. **CRPS computation (`distributional_calibration.py`):** The piecewise linear integration is correct. The `_integrate_squared_linear` formula `(y0² + y0·y1 + y1²)/3 × width` is mathematically sound for integrating a squared linear function.

2. **CDF construction:** Uses survival function values `P(X > strike)` converted to standard CDF via `1 - survival`. Piecewise linear interpolation with flat tails (0 below min strike, 1 above max strike). This is standard.

3. **Tail extension:** Dynamic `max(strike_range × 0.5, 1.0)` plus coverage of realized values. Reasonable, but could still truncate in edge cases. No obvious bugs.

4. **Potential issue: `_parse_expiration_value` for FED series.** The function handles "Above 3.50%" but the old `FED` prefix has raw numeric expiration values (e.g., `3.75`). Need to verify parsing works for both formats.

### Missing robustness checks

1. **No out-of-sample validation.** The paper acknowledges this. With 37 CPI events, a rolling-window validation becomes feasible (e.g., expanding window with minimum 10 events).

2. **No adjustment for strike count as covariate.** The paper does a 2-strike vs 3+-strike split but doesn't include strike count as a regression covariate. A logistic or ordered regression with CRPS/MAE as the dependent variable and (series, strike count, surprise magnitude, volume) as covariates would be more rigorous.

3. **Serial correlation treatment is ad hoc.** Using block bootstrap with block length 2 is reasonable but the choice of block length isn't justified beyond AR(1) estimates. With more data points, you could use Politis & Romano's automatic block length selection.

### Hostile reviewer attacks

1. **"You only have 2 series — this could be random."** This is the strongest attack and it's valid. The Mann-Whitney p=0.003 compares 14 CPI ratios to 16 JC ratios, but the fundamental claim is about *series-level* heterogeneity, which is n=2. Expanding to 4+ series addresses this.

2. **"The CPI result is driven by low strike count."** The paper addresses this well with the Monte Carlo simulation and the within-CPI 2-strike vs 3+-strike comparison. Solid defense.

3. **"CRPS/MAE > 1 is trivially possible for miscalibrated distributions."** The paper could be clearer that this is exactly the point — the ratio *diagnoses* miscalibration. It's not a bound, it's a signal.

4. **"In-sample only."** Valid critique, partially addressable with more data.

## The One Big Thing

**Expand the dataset by adding old-prefix CPI events (23), FED events (23), and old-prefix GDP events (11).** This requires changing one line in `experiment7/implied_distributions.py` (`STRIKE_SERIES`), adding a prefix-merging step, fetching FED historical data from FRED, and re-running the pipeline. This single change would:

- Nearly triple the CPI sample (14 → 37)
- Add a third independent economic series (FED, n≈20+ with realized outcomes)
- Make GDP usable for statistical tests (3 → 14)
- Transform every claim from "suggestive" to "approaching conclusive"
- Enable out-of-sample validation on CPI (train on old-prefix, test on new-prefix)

**Nothing else matters until this is done.** Fixing prose, tightening methods, or adding new analyses on n=14–16 is polishing a fundamentally underpowered study.

## Other Issues

### Must Fix (blocks publication)

1. **Expand dataset to include old-prefix series (`CPI`, `FED`, `GDP`).** The data is already cached in `targeted_markets.json`. This is the single highest-impact change. See "Data Sufficiency Audit" above for details.

2. **With expanded data, re-assess the CPI CRPS/MAE finding.** If 23 earlier CPI events show CRPS/MAE < 1, the narrative changes fundamentally — from "CPI distributions are harmful" to "CPI distributions *became* harmful after a structural break."

3. **Add FED as a third series** to test whether heterogeneity is systematic. FED rate markets settle at FOMC meetings; they have different structure than monthly economic releases.

### Should Fix (strengthens paper)

1. **Natural out-of-sample test:** Old-prefix CPI (Dec 2022 – Oct 2024) as training, new-prefix KXCPI (Nov 2024+) as test. This is a genuine temporal OOS split.

2. **Promote the point-vs-distribution decoupling to headline.** This is the paper's strongest conceptual contribution and it's currently buried in Section 3.

3. **Add volume/liquidity as a covariate.** The paper hypothesizes liquidity drives CPI's poor distributions but never tests it directly. Per-event volume data should be available from the market metadata.

4. **Drop or de-emphasize the TIPS Granger causality section.** It's expected, adds little novelty, and the measurement caveat (stale prices in thin markets) largely explains the finding.

5. **Clarify the CRPS/MAE ratio interpretation for general readers.** The paper explains it well for quant readers but the Kalshi blog audience includes traders who may not know CRPS. A 2-sentence intuitive explanation in the abstract would help.

### New Experiments / Code to Write

1. **`experiment7/implied_distributions.py` line 32:** Change `STRIKE_SERIES = {"KXCPI", "KXGDP", "KXJOBLESSCLAIMS"}` to include `"CPI", "FED", "GDP", "KXFED"`. Add a mapping to merge old/new prefixes into canonical names.

2. **Check candle availability for old-prefix series:**
   ```bash
   ls data/exp2/raw/candles/CPI-* | head -5
   ls data/exp2/raw/candles/FED-* | head -5
   ```
   If candles don't exist, fetch them via experiment2's pipeline.

3. **Add FRED benchmark for FED:** Fetch `FEDFUNDS` (monthly effective rate) or `DFEDTARU` (upper target) from FRED in `experiment12/distributional_calibration.py`.

4. **Implement rolling CRPS/MAE with expanded CPI data:** Plot CRPS/MAE ratio over time across 37 CPI events to test for temporal trends or structural breaks.

5. **Volume-CRPS regression:** Add a quick OLS/rank regression of per-event CRPS/MAE on log(volume) to test the liquidity hypothesis.

6. **Crypto as contrast case (lower priority):** KXBTCD has 14 events with multi-strike structure. These are daily resolution, high-liquidity markets with realized values. Adding them would test whether the CRPS/MAE diagnostic generalizes beyond economic releases.

### Genuinely Unfixable Limitations

1. **Cannot observe order book depth.** The paper hypothesizes that thin order books at extreme strikes degrade distributional quality, but Kalshi doesn't expose historical order book snapshots via the public API. Only volume is available, which is a noisy proxy. **Unfixable: the data does not exist in any accessible form.**

2. **Cannot directly measure trader composition.** Mechanism 3 (specialized vs generalist traders) is not testable with public data. **Unfixable: would require proprietary Kalshi data on user segmentation.**

## Verdict

**MAJOR REVISIONS.** The conceptual framework is strong and the methodology is sound, but the paper is publishing at ~30% of the available statistical power. Expanding the dataset from 2 to 4+ series, and from n=14–16 to n=30–40 per series, is feasible with ~2–4 hours of engineering work and would transform the paper's evidentiary base. No amount of methodological polish compensates for analyzing 14 CPI events when 37 are available in the researcher's own data cache.
