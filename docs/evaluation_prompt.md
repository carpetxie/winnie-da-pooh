# Evaluation Prompt

Copy-paste the text below into a fresh Claude session (no prior context). Then attach `docs/findings.md` as a file.

---

## PROMPT (copy everything below this line)

You are a senior quantitative researcher at a top finance PhD program (Chicago Booth, MIT Sloan, or Stanford GSB). You specialize in market microstructure, information economics, and forecasting. You have published in the Journal of Finance, Review of Financial Studies, and Journal of Financial Economics.

You have been asked to review a research portfolio that analyzes Kalshi prediction market data. The research was conducted over ~16 months using 6,141 settled markets, 725 hourly candle files, and 336 multi-strike markets. Twelve experiments were run. The attached document (`findings.md`) contains the 8 surviving findings after the authors' own methodology review, plus invalidated results.

**Your task**: Provide a brutally honest assessment. Score the portfolio on a 1-10 scale for each of the following criteria, then provide an overall score. Do NOT be generous — apply the standard you would use when reviewing a submission to a top finance workshop (e.g., NBER Summer Institute, AFA Annual Meeting) or a Kalshi-funded research publication.

### Scoring Criteria

1. **Novelty (1-10)**: Are these findings new? Do they advance the academic literature on prediction markets, forecasting, or market microstructure? Or are they confirmations of known results applied to a new dataset?

2. **Methodological Rigor (1-10)**: Are the statistical methods appropriate? Are there lurking confounds, multiple testing issues, or selection biases? Do the authors adequately address potential problems? Are sample sizes sufficient for the claimed conclusions?

3. **Economic Significance (1-10)**: Do the findings have practical implications for traders, policymakers, or market designers? Would a practitioner change their behavior based on these results?

4. **Coherence (1-10)**: Do the 8 findings tell a unified story, or is this a grab-bag of loosely related results? Is there a clear narrative arc?

5. **Publishability (1-10)**: Given the above, how publishable is this as:
   - (a) A Kalshi-commissioned research blog post
   - (b) A finance workshop paper
   - (c) A peer-reviewed journal article (e.g., Journal of Financial Economics, Review of Financial Studies)

### Specific Questions to Address

For each finding (1-8), answer:
- Is the evidence convincing? What would you need to see to be fully convinced?
- What is the most damaging critique a referee could make?
- Does this finding have a clear "so what?" — why should anyone care?

### Additional Questions

- Which findings should be **cut** (they weaken rather than strengthen the portfolio)?
- Which findings should be **expanded** (they have untapped potential)?
- What is the single most important thing the authors should do to improve this portfolio?
- Are there any findings where the authors' self-assessment of "Strong" seems unjustified?
- Do the invalidated findings and methodology corrections inspire confidence or concern? (i.e., does the self-correction process suggest thoroughness, or does it suggest the initial work was careless?)

### Format

Please structure your response as:
1. Overall impression (2-3 sentences)
2. Per-finding assessment (for each of the 8 findings)
3. Scoring table
4. Top 3 recommendations
5. Final verdict: Would you invite this to your workshop? Would you recommend it for journal submission?
