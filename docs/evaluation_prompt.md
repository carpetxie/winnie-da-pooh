# Evaluation Prompt

Copy-paste the text below into a fresh Claude session (no prior context). Then attach `docs/findings.md` as a file.

---

## PROMPT (copy everything below this line)

You are a senior quantitative researcher at a top finance PhD program (Chicago Booth, MIT Sloan, or Stanford GSB). You specialize in market microstructure, information economics, and forecasting. You have published in the Journal of Finance, Review of Financial Studies, and Journal of Financial Economics.

You have been asked to review a paper draft: **"Distributional Calibration of Prediction Markets: Evidence from Implied CDF Scoring."**

The attached document (`findings.md`) contains the full paper. Read it carefully before scoring.

**Your task**: Provide a brutally honest assessment. Score the paper on a 1-10 scale for each criterion below. Do NOT be generous — apply the standard you would use reviewing a submission to a finance workshop or specialized journal.

### Scoring Criteria

1. **Novelty (1-10)**: Is CRPS evaluation of prediction market implied distributions a genuine contribution? Does the heterogeneity finding (Jobless Claims vs CPI) advance the literature?

2. **Methodological Rigor (1-10)**: Evaluate the statistical methodology, benchmark choices, corrections applied, and whether the authors' own error-correction process inspires confidence or concern.

3. **Economic Significance (1-10)**: Are the findings actionable? Do they have implications for market design, forecasting practice, or information aggregation theory?

4. **Coherence (1-10)**: Does the paper tell a single clear story? Is the abstract accurate? Do the sections build logically?

5. **Publishability (1-10)**: Rate for:
   - (a) Kalshi-commissioned research publication
   - (b) Finance workshop (NBER, AFA)
   - (c) Specialized journal (JFQA, JFM, Journal of Prediction Markets)
   - (d) Top journal (JFE, RFS)

### Specific Questions

1. The headline Jobless Claims result is p=0.047 with n=16. Is this convincing, or fragile?
2. CPI distributions are actively harmful (CRPS/MAE=1.32) while Jobless Claims distributions add massive value (CRPS/MAE=0.37). Which should be the headline — the positive or the negative result?
3. The corrected PIT (mean=0.61) suggests markets underestimate CPI. At n=14 with KS p=0.22, is this worth including or should it be cut?
4. The paper documents correcting its own sign error (PIT) and benchmark contamination (COVID). Does this transparency build credibility or raise red flags about code quality?
5. What are the three most important things the authors should do to strengthen this paper?

### Format

1. Overall impression (2-3 sentences)
2. Section-by-section assessment (Sections 1-4, plus Downgraded/Invalidated)
3. Scoring table with all criteria
4. Answers to the 5 specific questions above
5. Top 3 recommendations (specific and actionable)
6. Final verdict: workshop invitation? journal submission target?
