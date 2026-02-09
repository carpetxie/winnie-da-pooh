# Project OOLONG-Kalshi: Recursive Market Intelligence

This project explores the intersection of **Recursive Language Models (RLMs)** and **Probabilistic Forecasting**. The goal is not just to fine-tune a model on financial data (which is noisy), but to build a composite system where "Hard" statistical priors are refined by "Soft" semantic reasoning.

We are building a **Two-Track System** that fuses historical market correlations with recursive news analysis.

## 1. Market Selection: The Terrain
We avoid 1-hour or daily markets dominated by HFTs and noise. We focus on markets where deep reasoning provides an edge over pure speed.

* **Target:** Weekly to Monthly Binary Markets (e.g., "Will CPI > 3.1%?", "Will Fed Cut Rates in March?").
* **Constraint:** Markets must resolve in a set timeframe (e.g., every Friday) to provide frequent training signals for calibration.
* **Advantage:** These markets often rely on dispersed information (reports, speeches, filings) that humans struggle to synthesize quickly.

## 2. Track A: The Statistical Prior (Lasso Logistic Regression)

We treat the current beliefs of *other* Kalshi markets as our primary dataset.

* **The Problem with Naive Bayes:** Initially was thinking of Naive Bayes. It assumes independence. In finance, if Market A (Oil) and Market B (Exxon) both predict Market C, Naive Bayes double-counts the signal, leading to extreme overconfidence.
* **The Solution:** Regularized Logistic Regression (Lasso/L1).
    * **Input (`k_t`):** A vector of prices from $n$ related markets (e.g., bond yields, similar political events) at a particular time `t` before the resolution of the primary market. **HYPERPARAMETER of how much time before the expected resolution of the primary market. (Note for later use is perhaps we can combine multiple time increments)**
    * **Target (`A_k`):** The binary resolution (0 or 1) of the target market.
    * **Mechanism:** The L1 penalty forces the coefficients of redundant markets to zero. It automatically selects the "best" predictors from the pool of 300+ active markets.
* **Output:** A calibrated probability P_stat. We convert this to Log-Odds such that `L_p = P_stat / ( 1 - P_stat)`.

Note: We do not include the primary market in `k_t`. 
## 3. Track B: The Recursive Language Model (RLM)
*Using tooling to expand context and Self-Consistency for stability.*

This track operates "blind" to the current market price to prevent bias (anchoring). It uses a recursive agentic workflow to generate an independent probability estimate by gathering evidence and mapping it to a rigorous rubric.

* **Structure:** Root Node -> Recursive Decomposition -> **Ensemble Synthesis**.
* **Method:** MECE (Mutually Exclusive, Collectively Exhaustive) breakdown.
    * *Root Node* receives query `q`. `q` in a format analog to:
    `q` + "Search for the top 50(**HYPERPARAMETER**) news headlines relevant to this particular question" and executes(**NOTE FOR LATER: Research agents best at retrieving news information / also determine which market is best for this**): 
    
    This is akin to the probing step of the RLM. The root node receives the headlines and URLs. It spawns sub-agents for the relevant non-redundant headers that are worth researching. 
    * *Sub-Agent 1-n:* Retrieves content and summarizes akin to how the recursively called sub-agents in RLMs summarizes article information. All of this information is stored together. 
    * **(NOTE FOR LATER: *Sub-Agent 3 (The Devil's Advocate):* "Find specific evidence contradicting the findings of Agents 1 & 2.")**

* **Tooling:** Python-based REPL environment (`read_context`, `search_news`, `spawn_subagent`).
* **Output Strategy:** **Categorical Self-Consistency**.
    * *The Problem:* Research shows LLMs struggle to output precise probabilities (e.g., "0.73") and suffer from high variance between runs.
    * *The Fix:* We force the RLM to classify evidence into discrete **Verbal Bins** rather than generating a float.
    * *The Mechanism:* We run this final synthesis step $k$ times (**HYPERPARAMETER**) (e.g., $k=5$) in parallel and average the results.

| Verbal Bin | Implication | Log-Odds ($L_{news}$) |
| :--- | :--- | :--- |
| **Strong Buy** | "Smoking gun" evidence confirming the event. | +2.0 |
| **Weak Buy** | Correlated evidence suggests "Yes". | +0.8 |
| **Neutral** | Conflicting evidence or noise. | 0.0 |
| **Weak Sell** | Correlated evidence suggests "No". | -0.8 |
| **Strong Sell** | "Smoking gun" evidence against the event. | -2.0 |

* **Final $L_{news}$:** The mean of the mapped Log-Odds across the k samples. This effectively filters out hallucination noise. The values for the binning are based on Jeffreys Scale of Evidence, a model for binning Bayesian updates. 

## 4. The Synthesis: Log-Odds Ensemble
We do not feed the statistical probability from Track A into the LLM, as this causes "precision smearing" (the LLM ignores the specific number). Instead, we combine the two independent tracks at the very end using a weighted ensemble.

**The Formula:**
$$L_{final} = \alpha \cdot L_{stat} + (1 - \alpha) \cdot L_{news}$$

* **$L_{stat}$:** The Log-Odds derived from our L1 Lasso Logistic Regression (Track A).
* **$L_{news}$:** The averaged Log-Odds from the RLM's verbal bins (Track B).
* **$\alpha$ (The Hyperparameter):** Represents our trust balance. An $\alpha$ of 0.7 implies we rely 70% on market correlations and 30% on our proprietary news analysis. (**TUNABLE HYPERPARAMETER**)

 
**Final Probability Calculation:**
$$P_{final} = \frac{1}{1 + e^{-L_{final}}}$$

We will sweep the alpha hyperparameter from 0 to 1 in bins of 0.05. We will backtest on the past 1 year of Kalshi data. The Lasso will be trained on the first 6 months. We will stick with one hyperparameter for a reasonable `t` for the Track A. We will target a set of recurring markets.
### Novelty & Research Value
This approach validates **Recursive Context** as a mechanism for **Calibration**, not just generation. By visualizing "Recursion Depth vs. Brier Score," we can prove that deeper tool-use leads to better probabilistic reasoning.