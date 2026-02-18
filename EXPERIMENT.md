# Kalshi Data Signal Experiments: Novel Value Discovery

## Table of Contents
1. [Context & Motivation](#1-context--motivation)
2. [Experiment 1: Cross-Market Causal Lead-Lag Discovery](#2-experiment-1-cross-market-causal-lead-lag-discovery)
3. [Experiment 2: Kalshi-Derived Real-Time Uncertainty Index](#3-experiment-2-kalshi-derived-real-time-uncertainty-index)
4. [Experiment 3: Outcome-Driven Self-Play Fine-Tuning](#4-experiment-3-outcome-driven-self-play-fine-tuning)
5. [Experiment 4: Information Speed Event Study](#5-experiment-4-information-speed-event-study)
6. [Experiment 5: Market Description Embeddings as Economic Similarity Metric](#6-experiment-5-market-description-embeddings-as-economic-similarity-metric)
7. [Comparative Ranking](#7-comparative-ranking)
8. [Key References](#8-key-references)

---

## 1. Context & Motivation

### The Goal
Demonstrate that Kalshi prediction market data contains value that is **not immediately obvious** — something compelling enough to pitch Kalshi on a collaboration.

### Constraints
- Must be **non-trivial**: the result cannot be true by construction (e.g., "ensemble of two signals beats either one" is trivially true when you optimize the blend weight on test data)
- Must be **feasible to validate** in approximately 8 hours with A100 GPU access
- Must be something **Kalshi would actually care about**: demonstrates their data has hidden value, enables new products, or strengthens their competitive position
- Should leverage **LLMs** where the LLM component is essential, not bolted-on

### Rejected Directions (and Why)
- **Market price calibration**: Works but trivial — just applies isotonic regression to already-efficient prices
- **LLM + Market ensemble with alpha sweep**: Trivially better by construction — sweeping alpha on the evaluation set guarantees the blend ≥ either signal alone
- **LLM confidence steering via activation vectors**: The uncertainty vector controls *linguistic hedging*, not actual *epistemic calibration*. Market volatility as steering magnitude is arbitrary. Kelly evaluation is trivially satisfied by any conservative intervention

### What We're Looking For
A result where:
1. The outcome is genuinely uncertain (could fail)
2. Success would demonstrate something non-obvious about Kalshi data
3. The experiment design doesn't guarantee the conclusion

---

## 2. Experiment 1: Cross-Market Causal Lead-Lag Discovery

### 2.1 Executive Summary

**Hypothesis:** Kalshi markets across different domains (economics, politics, crypto, weather, sports) contain hidden causal dependencies that are not priced into any individual contract. A hybrid statistical + LLM pipeline can discover these dependencies and trade them profitably.

**Core Insight:** Pure statistical methods (Granger causality) find many spurious lead-lag pairs due to multiple comparisons. An LLM acts as a semantic prior, filtering to pairs where a plausible economic transmission mechanism exists. This dramatically reduces false discovery and improves trading performance.

**Why It Matters to Kalshi:** Proves that their multi-domain market structure creates **emergent informational value** beyond any single market — a direct argument for why their breadth is a competitive moat. Produces a concrete data product: a real-time "causal dependency graph" across Kalshi markets.

### 2.2 Background & Prior Work

Two recent papers validate this approach:

- **"LLM as a Risk Manager: LLM Semantic Filtering for Lead-Lag Trading in Prediction Markets"** (arXiv:2602.07048, February 2026) — Proposes exactly this two-stage pipeline on Kalshi Economics markets. Shows the hybrid approach consistently outperforms pure statistical baselines.

- **"Semantic Trading: Agentic AI for Clustering and Relationship Discovery in Prediction Markets"** (arXiv:2512.02436, December 2025, IBM/Columbia) — Similar pipeline on Polymarket achieving ~20% average returns over week-long horizons.

**What's novel about our version:** Neither paper runs the pipeline comprehensively across ALL Kalshi domains. Existing work focuses on economics-only or Polymarket-only. Running it across economics + crypto + weather + politics + sports on Kalshi is the novel contribution.

### 2.3 Methodology

#### Stage 1: Statistical Signal Discovery

For all pairs of concurrent Kalshi markets with overlapping time windows:

1. Extract hourly price time series for each market
2. Compute pairwise Granger causality at lags of 1h, 4h, 12h, 24h
3. Apply Bonferroni correction for multiple comparisons
4. Keep pairs with corrected p < 0.01

**What Granger causality measures:** Market A "Granger-causes" Market B if past values of A's price series improve predictions of B's price series, beyond what B's own past values provide. This is a statistical test for predictive lead-lag, not true causation.

**Expected outcome:** Hundreds to thousands of statistically significant pairs, many of which are spurious (coincidental correlations, confounded by common causes, or artifacts of thin trading).

#### Stage 2: LLM Semantic Filtering

For each statistically significant pair (A → B):

1. Provide the LLM with both market descriptions (title, rules, category)
2. Prompt: *"Market A: [description]. Market B: [description]. Is there a plausible economic transmission mechanism by which a price movement in Market A would cause or predict a price movement in Market B? Explain in 2 sentences and rate plausibility on a scale of 1-5."*
3. Filter to pairs scoring ≥ 4

**Why the LLM is essential (not bolted-on):** The Granger test has no notion of economic meaning. It will flag "Fed rate market leads NHL hockey market" if there's a coincidental correlation. The LLM provides the economic reasoning layer that determines whether a statistical relationship is likely genuine or spurious. This is a classification task that could genuinely fail — the LLM might not have the economic knowledge to distinguish real from spurious transmission mechanisms.

#### Stage 3: Validation via Trading Simulation

On held-out data (last 3 months, not used in Stage 1-2):

1. **Signal-triggered trading protocol:** When the "leader" market price moves by > X% (calibrated on training data), enter a position in the "follower" market in the predicted direction
2. **Hold period:** Hold until the follower market moves by > Y% or until a timeout (24h)
3. **Compare three portfolios:**
   - (a) All Granger-significant pairs (no LLM filtering)
   - (b) LLM-filtered pairs only
   - (c) Random pairs as control (same number of trades, random entry)

### 2.4 Experiment Timeline (~8 hours)

| Hour | Task | Output |
|------|------|--------|
| 1 | Data collection: Pull all settled Kalshi markets (12 months). Extract hourly candlestick price series via API. | `data/raw/all_markets_12mo.json`, `data/processed/hourly_prices/` |
| 2 | Statistical stage: Compute pairwise Granger causality for all concurrent market pairs. Apply Bonferroni correction. | `data/processed/granger_pairs.csv` |
| 3-5 | LLM semantic stage: For each significant pair, prompt Llama-3.1-70B to assess economic plausibility. Filter to high-confidence pairs. | `data/processed/llm_filtered_pairs.csv` |
| 6-7 | Validation: Run signal-triggered trading simulation on held-out data. Compare filtered vs. unfiltered vs. random portfolios. | `data/evaluation/trading_results.csv` |
| 8 | Analysis: Generate causal dependency graph visualization. Compute precision/recall of LLM filtering. Write results summary. | `causal_graph.png`, `results_summary.md` |

### 2.5 Success Metrics

| Metric | What It Measures | Success Threshold |
|--------|-----------------|-------------------|
| **Sharpe ratio (LLM-filtered)** | Risk-adjusted return of filtered portfolio | > 0.5 (annualized) |
| **Sharpe improvement** | Filtered vs. unfiltered portfolio | > 30% improvement |
| **Precision of LLM filter** | % of LLM-approved pairs that are profitable | > 60% |
| **Spurious pair elimination** | % of Granger pairs rejected by LLM | > 50% |
| **Cross-domain discoveries** | Non-obvious causal links across different domains | ≥ 3 compelling examples |

### 2.6 Failure Modes

- **Too few concurrent markets:** If most Kalshi markets don't overlap in time, there are insufficient pairs to test. Mitigation: focus on series with recurring markets (weekly jobless claims, daily crypto, recurring sports).
- **LLM filtering too aggressive/lenient:** If the LLM approves everything or rejects everything, the filter adds no value. Mitigation: calibrate the threshold (try scores ≥ 3, ≥ 4, ≥ 5).
- **No genuine cross-domain dependencies:** If Kalshi domains are truly informationally independent, the experiment produces a null result. This is still a publishable finding — it means Kalshi markets are efficient within domains.

### 2.7 Deliverables

1. **Causal dependency graph:** Visual network where nodes are Kalshi market categories and edges are LLM-validated lead-lag relationships, weighted by statistical significance and trading profitability
2. **Trading performance comparison:** Equity curves for filtered vs. unfiltered vs. random portfolios
3. **Discovery examples:** 3-5 non-obvious cross-domain causal links with LLM-generated explanations of the transmission mechanism
4. **Quantified LLM value-add:** How much the semantic filtering improves trading performance over pure statistics

---

## 3. Experiment 2: Kalshi-Derived Real-Time Uncertainty Index

### 3.1 Executive Summary

**Hypothesis:** Kalshi market price movements can be aggregated into a real-time, domain-decomposed uncertainty index that **leads** traditional uncertainty indicators (VIX, Baker-Bloom-Davis Economic Policy Uncertainty Index) around major economic events.

**Core Insight:** The EPU index is built from newspaper mentions — it's slow, coarse, and backward-looking. The VIX measures S&P 500 implied volatility — it's real-time but domain-agnostic (you can't decompose it into "monetary policy uncertainty" vs. "fiscal policy uncertainty"). Kalshi data enables both: real-time AND domain-specific uncertainty measurement.

**Why It Matters to Kalshi:** Positions Kalshi as an **economic data infrastructure provider**, not just a trading platform. A Kalshi Uncertainty Index (KUI) would be directly comparable to EPU/VIX and potentially licensable to Bloomberg, FRED, and Reuters. Aligns with their new research arm's stated mission to turn platform data into "actionable insights."

### 3.2 Background & Prior Work

- **Baker-Bloom-Davis EPU Index** (policyuncertainty.com): Constructed from newspaper mentions of "uncertainty" + "economy" + "policy." Updated monthly/daily. Widely used in academic research and policy analysis. Available on FRED.

- **VIX (CBOE Volatility Index):** Measures 30-day implied volatility of S&P 500 options. Real-time but captures only aggregate equity market uncertainty. Cannot decompose into policy domains.

- **"Toward Black-Scholes for Prediction Markets"** (arXiv:2510.15205, October 2025): Proposes extracting "belief volatility" as a quotable risk factor from prediction market data, analogous to implied volatility in options. Provides the theoretical foundation for our approach.

- **Kalshi Research Arm** (December 2025): Kalshi launched a research division explicitly aimed at demonstrating their data's value for policymakers and investors. Published an initial study claiming 40% accuracy edge over Wall Street on inflation forecasting.

### 3.3 Methodology

#### Step 1: Market Classification

Use an LLM to classify each Kalshi market into uncertainty domains:

| Domain | Example Markets | Example Series Tickers |
|--------|----------------|----------------------|
| Monetary Policy | Fed rate decisions, FOMC statements | KXFED, KXFFR |
| Inflation | CPI prints, PCE data | KXCPI, KXPCE |
| Labor Market | Jobless claims, NFP | KXJOBLESSCLAIMS, KXNFP |
| Fiscal Policy | Debt ceiling, government shutdown | KXDEBTCEILING, KXSHUTDOWN |
| Crypto | BTC/ETH/SOL price movements | KXBTC, KXETH, KXSOL |
| Geopolitics | Tariffs, sanctions, conflicts | Various |

**Classification approach:** For each market, provide the title and rules to the LLM and ask it to assign one of the above domains. Markets that don't fit any domain are excluded.

#### Step 2: Belief Volatility Computation

For each domain and each day:

```
BV_domain(t) = (1/N) * Σ |Δp_i(t)| for all active markets i in domain
```

Where:
- `Δp_i(t)` is the daily price change of market i
- N is the number of active markets in the domain on day t
- This measures average absolute price movement — how much beliefs are shifting

**Additional sub-metrics:**
- **Cross-market dispersion:** Standard deviation of price changes within a domain (do all markets agree or disagree?)
- **Volume-weighted belief volatility:** Weight each market's price change by its trading volume (liquid markets contribute more)

#### Step 3: Index Construction

**Kalshi Uncertainty Index (KUI):**
```
KUI(t) = weighted_average(BV_domain(t)) across all domains
```

**Domain sub-indices:**
```
KUI_monetary(t) = BV_monetary_policy(t)
KUI_inflation(t) = BV_inflation(t)
KUI_labor(t) = BV_labor_market(t)
...
```

Normalize all indices to have mean=100 and std=15 (matching EPU convention).

#### Step 4: Validation

**Test 1: Correlation with existing indices**
- Compute daily correlation of KUI with EPU and VIX
- Expected: moderate correlation (0.3-0.6) — they should be related but not redundant

**Test 2: Lead-lag analysis**
- Granger causality test: Does KUI lead EPU? Does KUI lead VIX?
- If KUI leads by 1-3 days, that's the key finding

**Test 3: Incremental predictive power**
- Regression: `RealizedVol_SP500(t+5) = β₁·VIX(t) + β₂·EPU(t) + β₃·KUI(t) + ε`
- Does adding KUI improve R²? (F-test for significance)

**Test 4: Event study**
- Identify major economic surprises in the past year (unexpected CPI prints, surprise Fed decisions, tariff announcements)
- For each event, plot the KUI domain sub-index in a [-7d, +7d] window
- Show that the relevant domain sub-index spikes BEFORE the EPU reacts
- Quantify the average lead time in hours/days

### 3.4 Experiment Timeline (~8 hours)

| Hour | Task | Output |
|------|------|--------|
| 1-2 | Data collection: Pull all Kalshi markets (12 months). Download EPU from FRED, VIX from Yahoo Finance. Use LLM to classify markets into domains. | `data/raw/`, `data/processed/market_domains.csv` |
| 3 | Index construction: Compute daily belief volatility per domain. Construct KUI and sub-indices. | `data/processed/kui_daily.csv` |
| 4-5 | Validation vs. existing indices: Correlation analysis, Granger causality, incremental R² test. | `data/evaluation/kui_validation.csv` |
| 6-7 | Event study: Identify surprise events. Plot domain sub-indices around events. Quantify lead times. | `data/evaluation/event_studies/` |
| 8 | LLM narrative generation + analysis: Generate natural-language uncertainty reports from index decomposition. Write results. | `results_summary.md`, example narratives |

### 3.5 Success Metrics

| Metric | What It Measures | Success Threshold |
|--------|-----------------|-------------------|
| **KUI-EPU correlation** | Index validity | 0.3 - 0.7 (related but not redundant) |
| **KUI leads EPU** | Information speed advantage | Granger-causal at p < 0.05 |
| **Incremental R² for realized vol** | Unique predictive content | ΔR² > 0.02 (statistically significant) |
| **Event study lead time** | Speed advantage around surprises | KUI domain sub-index spikes ≥ 1 day before EPU |
| **Domain decomposition** | Unique capability vs. VIX/EPU | At least 3 domains with distinct dynamics |

### 3.6 Failure Modes

- **Insufficient market liquidity per domain:** If most domains have < 5 active markets on any given day, the index is too noisy. Mitigation: aggregate into broader domains (e.g., "economic" = monetary + inflation + labor).
- **KUI lags EPU/VIX:** If newspapers and options markets process information faster than Kalshi traders, the index has no speed advantage. This is a meaningful null result.
- **No incremental predictive power:** KUI is just a noisy version of VIX. Mitigation: focus on domain decomposition as the unique value proposition even if the aggregate index doesn't lead.

### 3.7 Deliverables

1. **KUI time series:** Daily index + domain sub-indices for the past 12 months
2. **Lead-lag analysis:** Evidence that KUI leads or lags EPU/VIX, with quantified lead times
3. **Event study plots:** Domain sub-indices around major economic surprises, showing early detection
4. **Incremental R² analysis:** Statistical evidence of unique predictive content
5. **LLM-generated uncertainty narratives:** Example automated reports decomposing uncertainty by domain

---

## 4. Experiment 3: Outcome-Driven Self-Play Fine-Tuning

### 4.1 Executive Summary

**Hypothesis:** An LLM fine-tuned via self-play + DPO on Kalshi market data — with candlestick price history as additional context during reasoning — produces better-calibrated probability estimates than the base model, a model fine-tuned without price context, or the market price itself.

**Core Insight:** Rather than blending LLM predictions with market prices at inference time (the ensemble approach, which is trivially better), we bake the market signal into the model's weights. After fine-tuning, the model operates independently — no market data needed at inference time. The non-trivial claim: exposure to price history during training teaches the model to reason about uncertainty more carefully.

**Why It Matters to Kalshi:** "Kalshi data makes AI smarter" is a compelling licensing narrative. It demonstrates that Kalshi's historical data has lasting value for training better AI systems, creating a recurring data licensing opportunity. Directly addresses the KalshiBench finding (arXiv:2512.16030) that frontier LLMs are systematically overconfident on Kalshi-type questions (ECE = 0.12–0.39).

### 4.2 Background & Prior Work

- **"LLMs Can Teach Themselves to Better Predict the Future"** (arXiv:2502.05253, February 2025): Shows self-play + DPO on Polymarket data achieves 7-10% accuracy improvements on 14B models, bringing them to parity with GPT-4o.

- **"KalshiBench: Evaluating Epistemic Calibration via Prediction Markets"** (arXiv:2512.16030, December 2025): Frontier LLMs are poorly calibrated on Kalshi-type questions. Reasoning-enhanced models are actually *worse* calibrated (more overconfident). This means significant room for improvement exists.

- **DPO (Direct Preference Optimization):** A fine-tuning method that trains the model to prefer "winning" responses over "losing" ones, without needing a separate reward model. Here, "winning" = closer to the actual outcome, "losing" = further from outcome.

### 4.3 Methodology

#### Step 1: Data Preparation

For ~500 settled Kalshi markets with rich price history:

1. Record: market title, full rules text, settlement outcome (YES/NO), final settlement value
2. Extract hourly candlestick price series from open to close
3. Compute midpoint price (price at the temporal midpoint of the market's lifetime)
4. Split: 400 training, 100 test (temporal split — test markets are more recent)

#### Step 2: Self-Play Reasoning Trace Generation

For each training market, generate 8 diverse reasoning traces using Llama-3.1-8B:

**Condition A — Base (no price history):**
```
System: You are a forecasting analyst. Given a prediction market question,
reason step-by-step about the likely outcome and provide a probability estimate
(0.0 to 1.0) that the market resolves YES.

User: Market: "Will weekly initial jobless claims for the week ending Feb 5
come in at or above 270,000?"

Think step by step, then provide your probability estimate as P(YES) = X.XX
```

**Condition B — Price-Augmented:**
```
System: You are a forecasting analyst. Given a prediction market question and
its historical price data, reason step-by-step about the likely outcome and
provide a probability estimate (0.0 to 1.0) that the market resolves YES.

User: Market: "Will weekly initial jobless claims for the week ending Feb 5
come in at or above 270,000?"

Price history (market midpoint): The market price was 0.35 two weeks before
resolution, rose to 0.42 one week before, and reached 0.55 at midpoint.
Current traders believe there is a 55% chance of YES.

Think step by step, then provide your probability estimate as P(YES) = X.XX
```

For each market, generate 8 traces with temperature=0.8 for diversity.

#### Step 3: DPO Pair Construction

For each market:
1. Extract the probability estimate from each trace
2. Compute Brier score: `(p_estimated - y_actual)²`
3. Rank traces by Brier score (lower = better)
4. Form DPO pairs: (winner = lowest Brier trace, loser = highest Brier trace)
5. Multiple pairs per market: top-1 vs bottom-1, top-2 vs bottom-2, etc.

#### Step 4: DPO Fine-Tuning

Fine-tune two model variants:

- **DPO-Base:** Trained on Condition A pairs (no price history)
- **DPO-Price:** Trained on Condition B pairs (price history in prompt)

Training configuration:
- Base model: Llama-3.1-8B-Instruct
- DPO β = 0.1 (standard)
- Learning rate: 5e-7
- Epochs: 3
- LoRA rank 16 for memory efficiency on A100

#### Step 5: Evaluation

On 100 held-out test markets, compare four models:

| Model | Description |
|-------|-------------|
| **Base Llama-3.1-8B** | No fine-tuning, direct probability elicitation |
| **DPO-Base** | Fine-tuned on reasoning traces without price history |
| **DPO-Price** | Fine-tuned on reasoning traces with price history |
| **Market Price** | Kalshi midpoint price as the probability estimate |

**Key comparison:** DPO-Price vs. DPO-Base isolates the effect of exposure to price history during training.

### 4.4 Experiment Timeline (~8 hours)

| Hour | Task | Output |
|------|------|--------|
| 1 | Data collection: Fetch 500 settled markets with price history. Prepare train/test split. | `data/processed/finetune_markets.csv` |
| 2-4 | Self-play generation: Generate 8 reasoning traces per market (×2 conditions). ~4000 traces total on A100. | `data/processed/reasoning_traces/` |
| 4-5 | DPO pair construction: Rank traces by Brier score, form preference pairs. | `data/processed/dpo_pairs/` |
| 5-7 | DPO fine-tuning: Train DPO-Base and DPO-Price variants. ~1 hour each with LoRA on A100. | `models/dpo_base/`, `models/dpo_price/` |
| 7-8 | Evaluation: Run all 4 models on 100 test markets. Compute Brier, ECE, calibration curves. | `data/evaluation/finetune_results.csv` |

### 4.5 Success Metrics

| Metric | What It Measures | Success Threshold |
|--------|-----------------|-------------------|
| **Brier (DPO-Price) < Brier (Base)** | Fine-tuning improves calibration | ≥ 10% improvement |
| **Brier (DPO-Price) < Brier (DPO-Base)** | Price history adds value during training | Statistically significant (paired t-test p < 0.05) |
| **Brier (DPO-Price) < Brier (Market Price)** | Model beats the market | Any improvement (this is the stretch goal) |
| **ECE (DPO-Price)** | Calibration quality | < 0.10 (better than KalshiBench frontier models) |

### 4.6 Failure Modes

- **All models produce similar Brier scores:** The fine-tuning doesn't help, or 500 markets isn't enough training data. Mitigation: use all ~6000 settled markets if available, or use a smaller model (3B) that's easier to shift.
- **DPO-Price ≈ DPO-Base:** Price history doesn't add value during training. This is an interesting null result — it means the LLM's parametric knowledge already captures what the price series contains.
- **Models are worse than market price:** Expected for thick markets. Focus analysis on thin markets where the model has an information advantage.

### 4.7 Deliverables

1. **Brier score comparison table:** Four models × test set, with confidence intervals
2. **Calibration curves:** Predicted probability vs. actual frequency for each model
3. **Per-market analysis:** Which markets does the fine-tuned model beat the market price on? (Hypothesis: thin/illiquid markets)
4. **Training dynamics:** How Brier score evolves during fine-tuning (proves the model is learning, not just memorizing)

---

## 5. Experiment 4: Information Speed Event Study

### 5.1 Executive Summary

**Hypothesis:** Kalshi market prices systematically absorb information **faster** than traditional market indicators (Treasury yields, S&P 500 futures, VIX) around scheduled economic releases, making Kalshi data a leading indicator for financial markets.

**Core Insight:** Prediction markets aggregate diverse beliefs in real-time. If Kalshi traders are well-informed, their prices should move before traditional indicators. This has been claimed anecdotally (e.g., a 4% Kalshi price shift within 400ms of a leaked Congressional memo, vs. 3 minutes for news wires) but never systematically studied across many events.

**Why It Matters to Kalshi:** If proven, this is a direct sales pitch to every hedge fund and trading desk: "subscribe to Kalshi data for faster economic signals than Bloomberg." Kalshi's research arm published a study claiming a 40% accuracy edge over Wall Street on inflation forecasting — this experiment provides the time-series mechanism underlying *why*.

### 5.2 Methodology

#### Step 1: Event Identification

Use an LLM to identify all major scheduled economic releases in the past 12 months:

| Event Type | Frequency | Example | Relevant Kalshi Series |
|-----------|-----------|---------|----------------------|
| CPI Release | Monthly | "CPI for January 2026" | KXCPI |
| Nonfarm Payrolls | Monthly | "NFP for January 2026" | KXNFP |
| Fed Rate Decision | 8x/year | "FOMC January 2026" | KXFED, KXFFR |
| Jobless Claims | Weekly | "Claims week ending Feb 5" | KXJOBLESSCLAIMS |
| GDP Release | Quarterly | "Q4 2025 GDP" | KXGDP |

Target: ~100 events across all types.

For each event, use the LLM to classify whether the actual outcome was a **"surprise"** (significantly different from consensus expectations) or **"in-line"** (matched expectations). Surprise events are more informative for lead-lag analysis.

#### Step 2: High-Resolution Data Collection

For each event, collect data in a [-24h, +24h] window:

**Kalshi data:**
- 1-minute candlestick data for the most relevant Kalshi market
- Volume per minute (trade activity)

**Traditional market data:**
- S&P 500 futures (ES) — minute-level from Yahoo Finance or similar
- 10-Year Treasury yield — daily from FRED (minute-level may require paid source)
- VIX — minute-level from CBOE

**Important limitation:** Minute-level traditional market data may require paid data feeds. Fallback: use daily data and measure lead-lag in days rather than minutes.

#### Step 3: Event Study Analysis

For each event in the [-24h, +24h] window:

1. **Detect first significant move:** Identify the timestamp at which the price first moves > 2 standard deviations from its pre-event mean (measured over [-48h, -24h])
2. **Compute for both Kalshi and traditional indicators**
3. **Lead-lag = T_kalshi - T_traditional**
   - Negative = Kalshi leads (Kalshi moved first)
   - Positive = Kalshi lags (traditional markets moved first)
   - Zero = simultaneous

#### Step 4: Aggregate Analysis

- Compute average lead-lag across all events
- Compute average lead-lag by event type (CPI vs. NFP vs. Fed decisions)
- Compute conditional lead-lag: surprise events vs. in-line events
- Run time-varying Granger causality between Kalshi price changes and traditional market returns in the [-2h, +2h] event window

### 5.3 Experiment Timeline (~8 hours)

| Hour | Task | Output |
|------|------|--------|
| 1 | Event identification: Use LLM to catalog 100 economic releases from past 12 months. Classify as surprise vs. in-line. | `data/processed/economic_events.csv` |
| 2-3 | Data collection: Pull Kalshi 1-minute candles for relevant markets around each event. Pull traditional market data. | `data/raw/event_windows/` |
| 4-6 | Event study analysis: Detect first significant moves. Compute lead-lag for each event. | `data/evaluation/leadlag_results.csv` |
| 7 | Conditional analysis: Split by event type and surprise classification. Run Granger causality in event windows. | `data/evaluation/conditional_analysis.csv` |
| 8 | Visualization and write-up: Event study plots, aggregate statistics, key examples. | `event_study_plots/`, `results_summary.md` |

### 5.4 Success Metrics

| Metric | What It Measures | Success Threshold |
|--------|-----------------|-------------------|
| **Average lead time** | How far ahead Kalshi moves | Kalshi leads by ≥ 30 minutes on average |
| **% events where Kalshi leads** | Consistency of speed advantage | > 60% of events |
| **Surprise event lead time** | Speed on most informative events | Kalshi leads by ≥ 1 hour on surprises |
| **Granger causality** | Statistical significance of lead relationship | p < 0.05 in event windows |

### 5.5 Failure Modes

- **Kalshi lags traditional markets:** Kalshi traders are watching Bloomberg and reacting to equity/bond moves, not the other way around. This is a meaningful null result but bad for a Kalshi pitch. However, it's still publishable and honest.
- **Insufficient minute-level data:** Kalshi's 1-minute candle API may have gaps or thin data around events. Mitigation: use hourly candles and measure lead-lag in hours.
- **Too few surprise events:** If most events are in-line, the signal is weak. Mitigation: include non-scheduled events (tariff announcements, geopolitical shocks) identified by the LLM.

### 5.6 Deliverables

1. **Lead-lag distribution:** Histogram of Kalshi lead times across all events
2. **Event study plots:** Kalshi price + traditional indicator overlays for the 5 most dramatic events
3. **Conditional analysis:** Lead time by event type and surprise classification
4. **Granger causality results:** Statistical evidence of directional information flow
5. **Headline finding:** "Kalshi markets lead traditional indicators by X minutes/hours on economic releases"

---

## 6. Experiment 5: Market Description Embeddings as Economic Similarity Metric

### 6.1 Executive Summary

**Hypothesis:** LLM embeddings of Kalshi market descriptions, combined with settlement outcomes, reveal a hidden economic structure — markets with similar descriptions also have correlated outcomes. This similarity metric can predict new market outcomes from text alone, without any price data.

**Core Insight:** Kalshi's market descriptions are natural-language specifications of economic events. The embedding space should capture economic relationships (e.g., "CPI above 3.5%" is semantically close to "Fed holds rates") that also have correlated outcomes. If this works, it means Kalshi's curated market descriptions contain extractable economic intelligence.

**Why It Matters to Kalshi:** Demonstrates that their market descriptions — which they carefully write — are themselves a valuable data asset. Could power a market recommendation engine, a "similar markets" feature for traders, or inform which new markets to create based on information gaps in the embedding space.

### 6.2 Methodology

#### Step 1: Embedding Generation

For all ~10,000 settled Kalshi markets:

1. Extract full text: title + subtitle + rules_primary
2. Generate embeddings using a local embedding model on A100:
   - Option A: `bge-large-en-v1.5` (1024-dim, fast)
   - Option B: `e5-large-v2` (1024-dim, good for semantic similarity)
   - Option C: Llama-3.1-8B last-hidden-state mean pooling (4096-dim, most expressive)
3. Store as a matrix: `N_markets × embedding_dim`

#### Step 2: Clustering and Structure Discovery

1. **Dimensionality reduction:** UMAP to 2D for visualization
2. **Clustering:** HDBSCAN to find natural clusters
3. **Outcome correlation within clusters:** For each cluster, compute:
   - Outcome correlation: do markets in this cluster tend to resolve the same way?
   - Price correlation: do markets in this cluster have correlated price movements?
4. **Identify high-quality clusters:** Clusters where outcome correlation is significantly above chance (permutation test)

#### Step 3: Nearest-Neighbor Prediction

For each market in a held-out test set:

1. Find k nearest neighbors in embedding space from the training set (k = 5, 10, 20)
2. Predict outcome as weighted average of neighbors' outcomes:
   ```
   P(YES) = Σ (similarity_i × outcome_i) / Σ similarity_i
   ```
3. Compare this "text-only" predictor to:
   - (a) Market's own midpoint price (the efficient baseline)
   - (b) Random baseline (base rate of YES outcomes in training set)
   - (c) Most frequent outcome in the nearest-neighbor cluster

#### Step 4: Cross-Domain Discovery

1. Identify clusters that contain markets from multiple domains (e.g., weather + labor markets clustering together)
2. For each cross-domain cluster, use the LLM to explain *why* these markets are related
3. Test whether the cross-domain similarity is economically meaningful (do they actually have correlated outcomes, or is it just linguistic similarity?)

### 6.3 Experiment Timeline (~8 hours)

| Hour | Task | Output |
|------|------|--------|
| 1 | Data collection: Fetch all settled markets with full text descriptions and outcomes. | `data/raw/all_markets_text.json` |
| 2 | Embedding generation: Run embedding model on all market descriptions. | `data/vectors/market_embeddings.npy` |
| 3-4 | Clustering: UMAP + HDBSCAN. Compute within-cluster outcome correlations. Identify high-quality clusters. | `data/processed/clusters.csv`, `embedding_space.png` |
| 5-6 | Prediction task: k-NN prediction on held-out test set. Compare to market price and random baselines. | `data/evaluation/knn_predictions.csv` |
| 7 | Cross-domain discovery: Identify surprising cross-domain clusters. Use LLM to explain relationships. | `data/evaluation/cross_domain_discoveries.md` |
| 8 | Analysis and visualization: UMAP plots colored by domain/outcome, performance tables, write-up. | `embedding_visualization.png`, `results_summary.md` |

### 6.4 Success Metrics

| Metric | What It Measures | Success Threshold |
|--------|-----------------|-------------------|
| **k-NN Brier < Random Brier** | Embeddings capture outcome-relevant structure | Statistically significant improvement |
| **k-NN Brier on thin markets** | Value for illiquid markets specifically | k-NN beats market price on markets with volume < 50 |
| **High-quality clusters** | Economically meaningful groupings | ≥ 10 clusters with outcome correlation > 0.3 |
| **Cross-domain discoveries** | Non-obvious economic relationships | ≥ 3 compelling cross-domain clusters |
| **LLM explanation quality** | Interpretability of discovered structure | Explanations are economically sensible |

### 6.5 Failure Modes

- **Embeddings cluster by surface linguistics, not economics:** Markets about "temperature" cluster together but have uncorrelated outcomes. Mitigation: use outcome-weighted similarity rather than pure embedding distance.
- **k-NN prediction is no better than base rate:** The embedding space doesn't capture outcome-relevant information. This means market descriptions are not economically informative — an interesting null result.
- **Market price always wins:** On thick markets, the efficient price will always beat a text-only predictor. Focus the analysis on thin markets where the text-based predictor fills an information gap.

### 6.6 Deliverables

1. **UMAP visualization:** Embedding space colored by domain, outcome, and cluster membership
2. **Prediction performance table:** k-NN vs. market price vs. random, overall and stratified by market liquidity
3. **Cluster catalog:** Top 20 clusters with descriptions, outcome correlations, and representative markets
4. **Cross-domain discoveries:** 3-5 surprising relationships with LLM-generated economic explanations
5. **Market recommendation prototype:** "Markets similar to [X] that you might want to trade"

---

## 7. Comparative Ranking

### Overall Assessment

| Experiment | Novelty | Non-Triviality | Feasibility (8h) | Kalshi Appeal | LLM Leverage | Recommended |
|:-----------|:--------|:---------------|:-----------------|:-------------|:-------------|:------------|
| **1. Causal Lead-Lag** | HIGH | HIGH | HIGH | VERY HIGH | HIGH | **Best Overall** |
| **2. Uncertainty Index** | VERY HIGH | HIGH | MEDIUM-HIGH | VERY HIGH | MEDIUM | **Highest Ceiling** |
| **3. Self-Play DPO** | MEDIUM | MEDIUM-HIGH | HIGH | HIGH | VERY HIGH | **Most LLM-Heavy** |
| **4. Information Speed** | HIGH | VERY HIGH | MEDIUM | VERY HIGH | LOW | **Riskiest** |
| **5. Embedding Space** | MEDIUM-HIGH | MEDIUM-HIGH | VERY HIGH | HIGH | HIGH | **Fastest to Run** |

### Decision Framework

**Choose Experiment 1 if:** You want the highest probability of a compelling result with strong prior validation from recent papers.

**Choose Experiment 2 if:** You want to pitch Kalshi on a data product with clear revenue potential (licensable index).

**Choose Experiment 3 if:** You want to maximize LLM usage and your A100 time, and can tolerate that the base result (DPO helps) is partially expected from prior work.

**Choose Experiment 4 if:** You're willing to take risk for a potentially headline-grabbing finding ("Kalshi beats Bloomberg by X minutes").

**Choose Experiment 5 if:** You want the safest, fastest experiment that still produces interesting visualizations and discoveries.

### Recommended Strategy

**Primary experiment:** Experiment 1 (Causal Lead-Lag Discovery) — highest expected value.

**Backup / complementary:** Experiment 5 (Embedding Space) — can run in parallel as a warm-up, or pivot to if Experiment 1 hits data issues.

---

## 8. Key References

### Directly Relevant Papers

1. **LLM as a Risk Manager: LLM Semantic Filtering for Lead-Lag Trading in Prediction Markets**
   - arXiv:2602.07048 (February 2026)
   - Validates the Experiment 1 approach on Kalshi Economics markets

2. **Semantic Trading: Agentic AI for Clustering and Relationship Discovery in Prediction Markets**
   - arXiv:2512.02436 (December 2025, IBM/Columbia)
   - Similar pipeline on Polymarket, ~20% average returns

3. **KalshiBench: Evaluating Epistemic Calibration via Prediction Markets**
   - arXiv:2512.16030 (December 2025)
   - Frontier LLMs are overconfident on Kalshi questions (ECE 0.12-0.39)

4. **LLMs Can Teach Themselves to Better Predict the Future**
   - arXiv:2502.05253 (February 2025)
   - Self-play + DPO on Polymarket data, 7-10% accuracy improvement

5. **Toward Black-Scholes for Prediction Markets**
   - arXiv:2510.15205 (October 2025)
   - Theoretical framework for extracting "belief volatility" from prediction market data

### Background References

6. **Makers and Takers: The Economics of the Kalshi Prediction Market**
   - SSRN (2025)
   - Comprehensive analysis of Kalshi market microstructure

7. **Baker-Bloom-Davis Economic Policy Uncertainty Index**
   - policyuncertainty.com
   - The benchmark EPU index for Experiment 2

8. **Kalshi Research Arm Launch**
   - news.kalshi.com (December 2025)
   - Kalshi's own research initiatives and data product strategy

9. **The Market Knows Best**
   - U.S. Army Military Intelligence Professional Bulletin (2025)
   - Anecdotal evidence of prediction market information speed

10. **Beyond the VIX: Alternate Measures of Uncertainty**
    - Two Sigma (2025)
    - Context for alternative uncertainty indices

---

**Last Updated:** 2026-02-11
**Version:** 1.0
**Status:** Experiment Design (Pre-Execution)
