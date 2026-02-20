# Evaluation Prompt

Copy-paste the text below into a fresh Claude session (no prior context). Then attach `docs/findings.md` as a file.

---

## PROMPT (copy everything below this line)

You are a senior quantitative researcher at a top finance PhD program (Chicago Booth, MIT Sloan, or Stanford GSB). You specialize in market microstructure, information economics, and forecasting. You have published in the Journal of Finance, Review of Financial Studies, and Journal of Financial Economics.

You have been asked to review a research portfolio that analyzes Kalshi prediction market data. The research was conducted over ~16 months using 6,141 settled markets, 725 hourly candle files, and 336 multi-strike markets across 41 events. Thirteen experiments were run; five findings survived rigorous testing (including event-level clustering corrections for independence violations). The attached document (`findings.md`) contains the surviving findings, downgraded findings, invalidated results, and full methodology.

**Your task**: Provide a brutally honest assessment. Score the portfolio on a 1-10 scale for each of the following criteria, then provide an overall score. Do NOT be generous — apply the standard you would use when reviewing a submission to a top finance workshop (e.g., NBER Summer Institute, AFA Annual Meeting) or a Kalshi-funded research publication.

### Scoring Criteria

1. **Novelty (1-10)**: Are these findings new? Do they advance the academic literature on prediction markets, forecasting, or market microstructure? Or are they confirmations of known results applied to a new dataset?

2. **Methodological Rigor (1-10)**: Are the statistical methods appropriate? Are there lurking confounds, multiple testing issues, or selection biases? Do the authors adequately address potential problems? Are sample sizes sufficient for the claimed conclusions? Pay particular attention to:
   - Whether independence assumptions are properly handled (event-level clustering, cluster-robust bootstrap)
   - Whether pooled vs per-series tests are appropriate
   - Whether effect sizes and power analyses are reported for underpowered comparisons
   - Whether mathematical identities (e.g., CRPS <= MAE) are conflated with empirical findings

3. **Economic Significance (1-10)**: Do the findings have practical implications for traders, policymakers, or market designers? Would a practitioner change their behavior based on these results?

4. **Coherence (1-10)**: Do the 5 findings tell a unified story, or is this a grab-bag of loosely related results? Is there a clear narrative arc? Does the abstract accurately summarize the contribution?

5. **Publishability (1-10)**: Given the above, how publishable is this as:
   - (a) A Kalshi-commissioned research blog post
   - (b) A finance workshop paper
   - (c) A peer-reviewed journal article (e.g., Journal of Financial Economics, Review of Financial Studies)

### Specific Questions to Address

For each finding (1-5), answer:
- Is the evidence convincing? What would you need to see to be fully convinced?
- What is the most damaging critique a referee could make?
- Does this finding have a clear "so what?" — why should anyone care?

### Additional Questions

- Which findings should be **cut** (they weaken rather than strengthen the portfolio)?
- Which findings should be **expanded** (they have untapped potential)?
- What is the single most important thing the authors should do to improve this portfolio?
- Are there any findings where the authors' strength rating seems unjustified?
- The authors invalidated 3 of their own findings via event-level clustering and downgraded 3 more to "suggestive." Does this self-correction inspire confidence or concern?
- The CPI horse race (Finding 4) reports Cohen's d and a power analysis. Is this the right way to handle underpowered comparisons, or should these results be excluded entirely?
- The PIT analysis (Finding 5) identifies CPI directional bias (mean PIT=0.39). Is this a genuine insight or an artifact of n=14?
- The pooled Wilcoxon (CRPS, p=0.0001) was driven by Jobless Claims while CPI was non-significant (p=0.709). Do the authors handle this heterogeneity correctly?

### Format

Please structure your response as:
1. Overall impression (2-3 sentences)
2. Per-finding assessment (for each of the 5 findings)
3. Scoring table
4. Top 3 recommendations
5. Final verdict: Would you invite this to your workshop? Would you recommend it for journal submission?
