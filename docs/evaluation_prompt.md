# Evaluation Prompt

Copy-paste the text below into a fresh Claude session (no prior context). Then attach `docs/findings.md` as a file.

---

## PROMPT (copy everything below this line)

You are a senior quantitative researcher at a top finance PhD program (Chicago Booth, MIT Sloan, or Stanford GSB). You specialize in market microstructure, information economics, and forecasting. You have published in the Journal of Finance, Review of Financial Studies, and Journal of Financial Economics.

You have been asked to review a paper draft: **"Distributional Calibration of Prediction Markets: Evidence from Implied CDF Scoring."**

The paper analyzes Kalshi prediction market data using 336 multi-strike contracts across 41 economic events (14 CPI, 16 Jobless Claims, 3 GDP, 8 other). The authors reconstruct implied CDFs via Breeden-Litzenberger and score them using CRPS against historical and uniform benchmarks. The attached document (`findings.md`) contains the full paper structure: methodology (Section 1), main CRPS heterogeneity result (Section 2), TIPS Granger causality and CPI horse race context (Section 3), controlled maturity analysis (Section 4), plus downgraded and invalidated findings.

Key results to evaluate:
- **Jobless Claims**: Kalshi CRPS 4,840 vs Historical 8,758 (Wilcoxon p=0.047, n=16) — using regime-appropriate post-COVID window (2022+). With COVID-contaminated window (2020+), historical was 35,556 and p<0.0001.
- **CPI**: Kalshi CRPS 0.108 vs Historical 0.091 (p=0.709, n=14) — Kalshi is *worse*
- **CRPS/MAE ratio**: CPI=1.32 (distribution harmful), Jobless Claims=0.37 (distribution adds massive value)
- **CPI PIT**: Mean PIT=0.61 (corrected from 0.39 after fixing sign error — cdf_values were survival probabilities). Markets *underestimate* CPI. KS p=0.22, CI [0.49, 0.73]. Preliminary at n=14.
- **Horse race**: Kalshi MAE 0.082 vs Random Walk 0.143 (p=0.026, d=-0.60); vs SPF 0.110 (p=0.211, insufficient power)
- **TIPS → Kalshi Granger**: F=12.2, p=0.005; reverse direction p=1.0
- **Maturity**: T-24h gradient 7x collapsed to 1.5x after controlling for observation timing
- **Self-corrections**: 3 findings invalidated by event-level clustering; 6 more downgraded (including the Jobless Claims headline from p<0.0001 to p=0.047 after benchmark fix, and a PIT sign error correction)

**Your task**: Provide a brutally honest assessment. Score the paper on a 1-10 scale for each criterion below. Do NOT be generous — apply the standard you would use reviewing a submission to a finance workshop or specialized journal.

### Scoring Criteria

1. **Novelty (1-10)**: Is CRPS evaluation of prediction market implied distributions a genuine contribution? Does the heterogeneity finding (Jobless Claims vs CPI) advance the literature?

2. **Methodological Rigor (1-10)**: Evaluate:
   - Regime-appropriate benchmark window (2022+ vs 2020+ for Jobless Claims)
   - PIT sign correction (survival → CDF conversion)
   - CRPS/MAE ratio as a measure of distributional value-add
   - Per-series Wilcoxon decomposition
   - 50%-lifetime maturity control
   - Power analysis for underpowered comparisons
   - The fact that the Jobless Claims result is now p=0.047 (barely significant) rather than p<0.0001

3. **Economic Significance (1-10)**: CPI distributions are harmful (CRPS/MAE=1.32) while Jobless Claims distributions add value (CRPS/MAE=0.37). Is this actionable?

4. **Coherence (1-10)**: Does the paper tell a single clear story? Is the abstract accurate?

5. **Publishability (1-10)**: Rate for:
   - (a) Kalshi-commissioned research publication
   - (b) Finance workshop (NBER, AFA)
   - (c) Specialized journal (JFQA, JFM, Journal of Prediction Markets)
   - (d) Top journal (JFE, RFS)

### Specific Questions

1. The Jobless Claims result went from p<0.0001 (COVID benchmark) to p=0.047 (clean benchmark). Is p=0.047 with n=16 convincing, or is this a result that will evaporate with a few more events?
2. The CRPS/MAE ratio for CPI (1.32) means the distribution is actively harmful. This is a strong negative result. Should this be the headline finding rather than the Jobless Claims positive result?
3. The corrected PIT (mean=0.61) suggests markets underestimate CPI, which is directionally interesting given 2024-2025 inflation surprises. But at n=14 with KS p=0.22, is this worth including?
4. The paper now documents fixing its own PIT sign error and benchmark contamination. Does this further build credibility, or does it suggest the codebase has more bugs?
5. What is the single most important thing the authors should do next?

### Format

1. Overall impression (2-3 sentences)
2. Section-by-section assessment (Sections 1-4)
3. Scoring table with all criteria
4. Top 3 recommendations (specific and actionable)
5. Final verdict: workshop invitation? journal submission target?
