# Evaluation Prompt

Copy-paste the text below into a fresh Claude session (no prior context). Then attach `docs/findings.md` as a file.

---

## PROMPT (copy everything below this line)

You are a senior quantitative researcher at a top finance PhD program (Chicago Booth, MIT Sloan, or Stanford GSB). You specialize in market microstructure, information economics, and forecasting. You have published in the Journal of Finance, Review of Financial Studies, and Journal of Financial Economics.

You have been asked to review a paper draft: **"When Do Prediction Market Distributions Add Value? A CRPS/MAE Diagnostic."**

The attached document (`findings.md`) contains the full paper — four main sections, a methodology section, and a supplementary appendix. Read it carefully before scoring.

The paper's central claim is that the CRPS/MAE ratio serves as a diagnostic for whether prediction market implied distributions add value beyond point forecasts. The ratio reveals stark heterogeneity across event types: Jobless Claims (CRPS/MAE=0.37, distributions add massive value) vs CPI (CRPS/MAE=1.32, distributions are actively harmful). The authors also present a theoretical mechanism section, no-arbitrage benchmarks against equity options, a CPI horse race, TIPS Granger causality, and a controlled maturity analysis.

**Your task**: Provide a brutally honest assessment. Score the paper on a 1-10 scale for each criterion below. Do NOT be generous — apply the standard you would use reviewing a submission to a finance workshop or specialized journal.

### Scoring Criteria

1. **Novelty (1-10)**: Is the CRPS/MAE ratio a genuine methodological contribution, or is it a trivial repackaging of two known quantities? Does the heterogeneity finding (distributions help for some event types but hurt for others) advance the prediction market or forecasting literature?

2. **Methodological Rigor (1-10)**: Evaluate comprehensively:
   - Bonferroni correction across series (Jobless Claims raw p=0.047 → adjusted p=0.093)
   - Rank-biserial effect sizes for all Wilcoxon tests
   - Regime-appropriate benchmark windows (2022+ vs COVID-contaminated 2020+)
   - Power analysis showing which tests are adequately powered
   - The tension between "does not survive Bonferroni" and "well-powered at observed effect size"
   - Whether the statistical framework would survive a careful econometrician's scrutiny

3. **Economic Significance (1-10)**: Are the findings actionable for market designers, traders, or forecasters? Does the CRPS/MAE diagnostic have practical value?

4. **Coherence (1-10)**: Does the paper tell a single clear story? Does the abstract accurately represent the content? Do the four sections build logically toward a unified conclusion?

5. **Publishability (1-10)**: Rate for:
   - (a) Kalshi-commissioned research publication
   - (b) Finance workshop (NBER, AFA)
   - (c) Specialized journal (JFQA, JFM, Journal of Prediction Markets)
   - (d) Top journal (JFE, RFS)

### Specific Questions

1. The Jobless Claims result is p=0.047 raw, p=0.093 Bonferroni-adjusted, with r=0.49 and power analysis showing n=6 needed (they have n=16). The authors frame this as "real effect, conservative correction." Is this honest reporting or p-hacking rationalization?

2. The CRPS/MAE ratio is positioned as the paper's main contribution. But CRPS <= MAE is a mathematical identity — the ratio is just CRPS divided by MAE. Is framing this as a "diagnostic" genuinely novel, or is the contribution purely empirical (the heterogeneity finding)?

3. The theoretical mechanism section proposes four hypotheses (release frequency, signal dimensionality, trader composition, liquidity). Are these sufficiently specific and testable? Do they make the paper stronger or weaker?

4. The no-arbitrage benchmark claims Kalshi's 2.8% violation rate is comparable to SPX options' 2.7% call spread violations (Brigo et al., 2023). This is a striking comparison. Is the measurement methodology comparable enough to make this claim? Are the cited sources reliable?

5. The paper documents multiple self-corrections in its supplementary appendix (PIT sign error, COVID benchmark contamination, 3 invalidated findings, 6 downgraded). Does this transparency strengthen or undermine the paper?

6. What is the single biggest weakness of this paper, and what specific action would most improve it?

### Format

1. Overall impression (2-3 sentences)
2. Section-by-section assessment (Sections 1-4, plus Supplementary Appendix)
3. Scoring table with all criteria
4. Answers to the 6 specific questions above
5. Top 3 recommendations (specific and actionable)
6. Final verdict: workshop invitation? journal submission target?
