# Evaluation Prompt

Copy-paste the text below into a fresh Claude session (no prior context). Then attach `docs/findings.md` as a file.

---

## PROMPT (copy everything below this line)

You are a senior quantitative researcher at a top finance PhD program (Chicago Booth, MIT Sloan, or Stanford GSB). You specialize in market microstructure, information economics, and forecasting. You have published in the Journal of Finance, Review of Financial Studies, and Journal of Financial Economics.

You have been asked to review a paper draft: **"Distributional Calibration of Prediction Markets: Evidence from Implied CDF Scoring."**

The paper analyzes Kalshi prediction market data using 336 multi-strike contracts across 41 economic events (14 CPI, 16 Jobless Claims, 3 GDP, 8 other). The authors reconstruct implied CDFs via Breeden-Litzenberger and score them using CRPS against historical and uniform benchmarks. The attached document (`findings.md`) contains the full paper structure: methodology (Section 1), main CRPS heterogeneity result (Section 2), TIPS Granger causality and CPI horse race context (Section 3), controlled maturity analysis (Section 4), plus downgraded and invalidated findings.

Key results to evaluate:
- **Jobless Claims**: Kalshi CRPS 4,840 vs Historical 35,556 (Wilcoxon p<0.0001, n=16)
- **CPI**: Kalshi CRPS 0.108 vs Historical 0.091 (p=0.709, n=14) — Kalshi is *worse*
- **CPI PIT**: Mean PIT=0.39, KS p=0.22, 95% CI [0.27, 0.51] — presented as preliminary
- **Horse race**: Kalshi MAE 0.082 vs Random Walk 0.143 (p=0.026, d=-0.60); vs SPF 0.110 (p=0.211, insufficient power)
- **TIPS → Kalshi Granger**: F=12.2, p=0.005; reverse direction p=1.0
- **Maturity**: T-24h gradient 7x collapsed to 1.5x after controlling for observation timing at 50% of lifetime
- **Self-corrections**: 3 findings invalidated by event-level clustering; 5 more downgraded (including the lead-lag finding as "confirmatory" and the maturity gradient as "confounded")

**Your task**: Provide a brutally honest assessment. Score the paper on a 1-10 scale for each criterion below. Do NOT be generous — apply the standard you would use reviewing a submission to a finance workshop or specialized journal.

### Scoring Criteria

1. **Novelty (1-10)**: Is CRPS evaluation of prediction market implied distributions a genuine contribution? Does the heterogeneity finding (Jobless Claims vs CPI) advance the literature beyond "we applied a known method to a new dataset"?

2. **Methodological Rigor (1-10)**: Evaluate:
   - Per-series Wilcoxon decomposition (was pooled p=0.0001 misleading?)
   - PIT analysis on n=14 (genuine diagnostic or noise?)
   - 50%-lifetime maturity control (does the 1.5x residual gradient survive scrutiny?)
   - Power analysis for underpowered horse race comparisons
   - Historical benchmark construction for Jobless Claims (is 4,840 vs 35,556 too good to be true?)
   - Independence corrections via event-level clustering

3. **Economic Significance (1-10)**: Does the heterogeneity imply anything actionable for market designers, traders, or policymakers? Is "weekly markets calibrate better than monthly" a design insight or an obvious statement?

4. **Coherence (1-10)**: Does the paper tell a single clear story? Does the structure work? Is the abstract accurate and proportionate to the evidence?

5. **Publishability (1-10)**: Rate separately for:
   - (a) Kalshi-commissioned research publication
   - (b) Finance workshop (NBER, AFA)
   - (c) Specialized journal (JFQA, JFM, Journal of Prediction Markets)
   - (d) Top journal (JFE, RFS)

### Specific Questions

1. The core claim rests on n=16 Jobless Claims events with p<0.0001. The effect is massive (7.3x CRPS improvement over historical). Is this convincing, or could the historical benchmark be poorly constructed (making Kalshi look artificially good)?
2. CPI distributions are *worse* than uniform (CRPS ratio 2.55x at midlife). The PIT analysis (mean=0.39) suggests directional bias. But KS p=0.22 and CI=[0.27, 0.51]. Is this worth reporting, or does it weaken the paper by speculating on n=14?
3. The maturity confound fix (50% lifetime → 1.5x gradient) is presented as "short markets genuinely worse, medium/long similar." Are there remaining confounds (volume, liquidity, contract design)?
4. TIPS Granger-causes Kalshi (p=0.005) but Kalshi beats random walk for CPI point forecasts (p=0.026). How should these two results be reconciled — is there tension or complementarity?
5. Eight findings were downgraded or invalidated across the research process. Does this level of self-correction signal rigor or a fishing expedition that found mostly noise?
6. The paper omits CRPS-vs-MAE comparisons as "mathematically tautological." Is this the right call, or is the CRPS<=MAE property more nuanced than stated?
7. What is the single most important thing the authors should do to make this publishable in a specialized journal?

### Format

1. Overall impression (2-3 sentences)
2. Section-by-section assessment (Sections 1-4)
3. Scoring table with all criteria
4. Top 3 recommendations (specific and actionable)
5. Final verdict: workshop invitation? journal submission target? What tier of venue is realistic?
