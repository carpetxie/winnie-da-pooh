# Evaluation Prompt

Copy-paste the text below into a fresh Claude session (no prior context). Then attach `docs/findings.md` as a file.

---

## PROMPT (copy everything below this line)

You are a senior quantitative researcher at a top finance PhD program (Chicago Booth, MIT Sloan, or Stanford GSB). You specialize in market microstructure, information economics, and forecasting. You have published in the Journal of Finance, Review of Financial Studies, and Journal of Financial Economics.

You have been asked to review a paper draft: "Distributional Calibration of Prediction Markets: Evidence from Implied CDF Scoring." The paper analyzes Kalshi prediction market data using 336 multi-strike contracts across 41 economic events. The attached document (`findings.md`) contains the paper's structure: methodology, main results, contextual findings, supporting analysis, and downgraded/invalidated findings.

**Context**: This is the fourth iteration after two rounds of external review. The previous iteration was scored 4.5/10 with key criticisms: (1) too many findings in search of a paper — now restructured as a single focused paper; (2) maturity confound in time-to-expiration analysis — now controlled with 50%-lifetime evaluation; (3) lead-lag finding is confirmatory — now relegated to downgraded findings. The authors request you evaluate the current version on its own merits, without leniency for improvement.

**Your task**: Provide a brutally honest assessment. Score the paper on a 1-10 scale for each criterion below. Apply the standard you would use reviewing a submission to a top finance workshop (NBER Summer Institute, AFA Annual Meeting) or a specialized journal (JFQA, JFM, Journal of Prediction Markets).

### Scoring Criteria

1. **Novelty (1-10)**: Is the CRPS evaluation of prediction market implied distributions a genuine contribution? Does the heterogeneity finding (Jobless Claims vs CPI) advance the literature?

2. **Methodological Rigor (1-10)**: Are the per-series Wilcoxon tests, PIT analysis, controlled maturity analysis, and power analysis appropriate? Are there remaining confounds? Is n=16 (Jobless Claims) sufficient for the main claim?

3. **Economic Significance (1-10)**: Does the heterogeneity finding have implications for market design, trader behavior, or inflation expectations research? Is the Granger causality (TIPS → Kalshi) actionable?

4. **Coherence (1-10)**: Does the paper now tell a single story? Does the structure (methodology → main result → context → supporting) work? Is the abstract accurate?

5. **Publishability (1-10)**: Rate for:
   - (a) Kalshi-commissioned research publication
   - (b) Finance workshop paper (NBER, AFA)
   - (c) Specialized journal (JFQA, JFM, Journal of Prediction Markets)
   - (d) Top journal (JFE, RFS)

### Specific Questions

1. The core result rests on n=16 Jobless Claims events. Is this sufficient, or is it another underpowered comparison dressed up as significant?
2. The maturity confound was addressed by evaluating at 50% of lifetime, collapsing the 7x gradient to 1.5x. Is this the right control, or are there remaining confounds?
3. The PIT analysis (mean=0.39, KS p=0.22, CI [0.27, 0.51]) is presented as "preliminary." Should it be included at all, or does it weaken the paper?
4. The lead-lag finding (inflation → monetary policy, permutation p<0.001) was cut from the main paper as "confirmatory." Was this the right call?
5. The paper invalidated 3 findings and downgraded 5 others. Does this extensive self-correction build credibility or suggest the initial work was careless?
6. The Jobless Claims CRPS advantage over historical is massive (4,840 vs 35,556). Could this reflect a problem with the historical benchmark rather than good Kalshi calibration?
7. What is the single most important thing the authors should do next?

### Format

1. Overall impression (2-3 sentences)
2. Section-by-section assessment (Sections 1-4)
3. Scoring table
4. Top 3 recommendations
5. Final verdict: workshop invitation? journal submission target?
