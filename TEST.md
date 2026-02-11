# Dynamic Confidence Steering: LLM Calibration via Prediction Market Signals

## Table of Contents
1. [Executive Summary](#1-executive-summary)
2. [System Architecture](#2-system-architecture)
3. [Theoretical Foundation](#3-theoretical-foundation)
4. [Implementation Phases](#4-implementation-phases)
5. [File-by-File Breakdown](#5-file-by-file-breakdown)
6. [Data Flow & Dependencies](#6-data-flow--dependencies)
7. [Evaluation Methodology](#7-evaluation-methodology)
8. [Next Steps & Extensions](#8-next-steps--extensions)

---

## 1. Executive Summary

### The Problem
Large Language Models exhibit personality-driven overconfidence—they generate predictions with calibration that reflects their training persona rather than actual uncertainty in the underlying events. When asked about future events, LLMs often produce confident assertions that don't match real-world probabilities.

### The Core Insight
**The true value of prediction market data is not just the price (probability of X), but the stability (certainty of the probability).**

- **Prediction markets** possess "reality-driven" uncertainty → volatility reflects genuine epistemic uncertainty
- **LLMs** suffer from "personality-driven" overconfidence → outputs reflect helpful assistant persona, not true confidence

### The Solution
We will **steer** the LLM's internal confidence state using vectors derived from Kalshi's historical volatility patterns. This transforms the model from "Arrogant & Smart" to "Calibrated & Wise."

**Key Innovation:** Rather than fine-tuning the LLM to predict market prices, we extract a neural direction representing "uncertainty" and modulate it dynamically based on market-derived signals.

### Success Criteria
The steered model should:
1. **Match market volatility patterns**: Low-volatility domains (Economics) → high confidence; High-volatility domains (Politics) → appropriate hedging
2. **Preserve capabilities**: Maintain performance on standard benchmarks while improving calibration
3. **Enable dynamic control**: Single inference-time intervention that scales with market signal strength

---

## 2. System Architecture

### High-Level Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 1: Signal Extraction (Kalshi → Entropy Mapping)          │
├─────────────────────────────────────────────────────────────────┤
│ 1. Fetch historical Kalshi markets (12 months)                 │
│ 2. Categorize into domains: Econ, Politics, Sci, World, Crypto │
│ 3. Calculate volatility σ for each category                    │
│ 4. Create "Ground Truth Entropy" map: Category → α (magnitude) │
│    Output: entropy_map.json                                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 2: Vector Extraction (Contrastive Prompts → Direction)   │
├─────────────────────────────────────────────────────────────────┤
│ 1. Generate "Hindsight vs Foresight" prompt pairs              │
│    - Positive (Certainty): "The Fed did cut rates"             │
│    - Negative (Uncertainty): "The Fed might cut rates"         │
│ 2. Extract activations at target layer L (e.g., layer 16)      │
│ 3. Compute difference: D = Act_Uncertain - Act_Certain         │
│ 4. Aggregate across prompt pairs → Uncertainty Vector          │
│    Output: uncertainty_vector.npy                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 3: Inference-Time Steering (Dynamic Calibration)         │
├─────────────────────────────────────────────────────────────────┤
│ 1. Classify input text → Domain category                       │
│ 2. Lookup: σ_domain (from entropy_map.json)                    │
│ 3. Compute steering magnitude: α = σ_domain                    │
│ 4. Apply steering: h ← h + α · v_uncertainty                   │
│    (at target layer, add scaled uncertainty vector)            │
│ 5. Continue generation with steered activations                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 4: Evaluation (Kelly Criterion Test)                     │
├─────────────────────────────────────────────────────────────────┤
│ 1. Simulate betting portfolio based on LLM confidence          │
│ 2. Compare: Unsteered vs Steered model                         │
│ 3. Measure: ROI, Brier Score, Calibration Curves               │
│ 4. Success = Steered model survives volatility (no bankruptcy) │
└─────────────────────────────────────────────────────────────────┘
```

### Component Modules

```
winnie/
├── kalshi/
│   ├── __init__.py
│   ├── client.py              # Kalshi API authentication (RSA-PSS signing)
│   └── market_data.py         # Fetch markets, calculate volatility by category
│
├── steering/
│   ├── __init__.py
│   ├── vector_extraction.py   # Generate contrastive prompts, extract activation vectors
│   ├── entropy_mapping.py     # Map categories to steering magnitudes (σ)
│   ├── router.py              # Classify input text → domain category
│   └── inference.py           # Apply activation steering at inference time
│
├── models/
│   ├── __init__.py
│   └── loader.py              # Download and load HuggingFace models
│
├── evaluation/
│   ├── __init__.py
│   ├── kelly_criterion.py     # Simulate betting portfolio, compute ROI
│   ├── calibration.py         # Brier score, calibration curves
│   └── benchmarks.py          # Capability preservation tests
│
├── data/
│   ├── raw/                   # Cached Kalshi market data
│   ├── processed/             # Volatility statistics by category
│   └── vectors/               # Extracted steering vectors (.npy files)
│
└── test.md                    # This file
```

---

## 3. Theoretical Foundation

### 3.1 The Uncertainty Vector: Hindsight vs Foresight

**Intuition:** The neural representation of uncertainty can be isolated by contrasting how the model processes *resolved facts* versus *speculative predictions*.

**Methodology (following AssistantAxis.pdf extraction approach):**

1. **Generate Contrastive Prompt Pairs**
   - **Positive (Certainty)**: Statements about known outcomes
     - "The Federal Reserve cut interest rates by 25 basis points in March 2024."
     - "Inflation was measured at 3.2% in Q4 2023."
     - "The S&P 500 closed at 4,783.45 on December 29, 2023."

   - **Negative (Uncertainty)**: Statements about future/unknown outcomes
     - "The Federal Reserve might cut interest rates in the upcoming meeting."
     - "Inflation is expected to trend around 3.2% this quarter."
     - "The S&P 500 could close near 4,800 by month-end."

2. **Extract Activations**
   - Run both versions through the LLM
   - Cache residual stream activations at target layer L (e.g., middle layers: 12-20 for 40-layer models)
   - For each pair: `D_i = Act_uncertain - Act_certain`

3. **Aggregate Across Pairs**
   - Collect difference vectors: `D = [D_1, D_2, ..., D_N]` (N ≈ 100-200 pairs)
   - Compute mean difference: `v_uncertainty = mean(D)`
   - Normalize: `v_uncertainty ← v_uncertainty / ||v_uncertainty||`

**Why this works:**
- Avoids contamination from generic refusal behaviors ("I don't know")
- Isolates the *epistemic uncertainty* dimension (known vs unknown)
- Creates a direction that generalizes across domains

### 3.2 The Signal: Market Volatility as Entropy Proxy

**From Kalshi prices to uncertainty magnitude:**

```
σ_category = std_dev(daily_price_changes) across all markets in category
```

**Example:**
- **Economics markets** (Fed rates, jobless claims): σ ≈ 0.15 (low volatility → high confidence appropriate)
- **Politics markets** (election outcomes, policy passage): σ ≈ 0.65 (high volatility → hedging appropriate)

**The mapping:**
```
α = normalize(σ_category, range=[0.0, 1.5])
```
- α = 0.0 → No steering (high certainty domain)
- α = 1.5 → Maximum steering (maximum epistemic uncertainty)

### 3.3 The Intervention: Activation Capping

At inference time, for each token position:

```python
h_original = residual_stream[layer_L]
projection = dot(h_original, v_uncertainty)
steering_magnitude = α_category  # from entropy map

if projection < steering_magnitude:
    # Already uncertain enough, no intervention
    h_steered = h_original
else:
    # Too confident, apply steering
    h_steered = h_original + α_category * v_uncertainty
```

**Result:** Model's confidence (as measured by logit spreads) is modulated to match domain-appropriate uncertainty levels.

---

## 4. Implementation Phases

### Phase 1: Data Preparation (Kalshi Signal Extraction)

**Goal:** Create a mapping from text domains to appropriate uncertainty levels, derived from market data.

**Tasks:**
- [ ] Ingest Kalshi historical data (12 months, all settled markets)
- [ ] Define 5 core categories: `Economics`, `Politics`, `Science`, `World_Events`, `Crypto`
- [ ] Calculate per-category volatility statistics
- [ ] Create `data/processed/entropy_map.json`:
  ```json
  {
    "Economics": {"sigma": 0.18, "alpha": 0.3},
    "Politics": {"sigma": 0.72, "alpha": 1.2},
    "Science": {"sigma": 0.45, "alpha": 0.7},
    "World_Events": {"sigma": 0.58, "alpha": 0.9},
    "Crypto": {"sigma": 0.81, "alpha": 1.4}
  }
  ```

**Key File:** `kalshi/entropy_mapping.py` (not yet created)

**Output:** `data/processed/entropy_map.json`

---

### Phase 2: Vector Extraction (Neural Direction Discovery)

**Goal:** Extract a reusable "uncertainty vector" that generalizes across contexts.

**Tasks:**
- [ ] Generate 100-200 contrastive prompt pairs (Hindsight vs Foresight)
- [ ] Load target model from HuggingFace (e.g., Llama-3.3-70B-Instruct)
- [ ] Extract activations at layers 12, 16, 20 (test multiple depths)
- [ ] Compute mean difference vector for each layer
- [ ] Validate vector via projection onto test prompts
- [ ] Save best-performing vector: `data/vectors/uncertainty_L16.npy`

**Key File:** `steering/vector_extraction.py` (not yet created)

**Output:** `data/vectors/uncertainty_L{layer}.npy` for selected layers

---

### Phase 3: Routing & Inference (Dynamic Steering System)

**Goal:** Deploy inference-time steering based on input classification.

**Tasks:**
- [ ] Build simple domain classifier (BERT-based or keyword heuristic)
  - Input: "Will the Fed raise rates in Q2 2025?"
  - Output: Category = "Economics"
- [ ] Implement steering hook in model forward pass
  - Load `uncertainty_vector.npy`
  - Load `entropy_map.json`
  - At layer L: `h ← h + α * v_uncertainty`
- [ ] Test on example queries across categories

**Key Files:**
- `steering/router.py` (not yet created)
- `steering/inference.py` (not yet created)

**Output:** Steered model inference pipeline

---

### Phase 4: Evaluation (Kelly Criterion Validation)

**Goal:** Prove that market-derived steering improves financial survival and calibration.

**The Kelly Bet Simulation:**
```
For each historical Kalshi market:
  1. At market midpoint, ask LLM to predict outcome
  2. Extract confidence from steered vs unsteered model
  3. Compute Kelly bet size: f* = (p - (1-p)/b)
  4. Simulate betting outcome based on actual resolution
  5. Track bankroll over time
```

**Metrics:**
- **Portfolio ROI:** Final bankroll / initial bankroll
- **Bankruptcy rate:** % of simulations where bankroll → 0
- **Brier Score:** Mean squared error of probability predictions
- **Calibration Curve:** Predicted probability vs actual frequency

**Key File:** `evaluation/kelly_criterion.py` (not yet created)

**Success Condition:** Steered model achieves:
- Higher ROI than unsteered
- Lower bankruptcy rate
- Better Brier score (closer to 0)

---

## 5. File-by-File Breakdown

### 5.1 `kalshi/client.py`

**Purpose:** Handle Kalshi API authentication and HTTP requests.

**Status:** ✅ Exists (preserved from previous project)

**Key Functions:**
- `KalshiClient.__init__()`: Load API credentials, initialize RSA private key
- `KalshiClient._sign()`: Generate RSA-PSS signature for authenticated requests
- `KalshiClient.get()`: Execute single GET request
- `KalshiClient.get_all_pages()`: Cursor-based pagination for large datasets

**Dependencies:** `cryptography`, `requests`, `python-dotenv`

**No modifications needed.** This module is API-generic and works for any Kalshi data fetching.

---

### 5.2 `kalshi/market_data.py`

**Purpose:** Fetch settled markets and compute volatility statistics by category.

**Status:** ✅ Exists (adapted from previous `data_collection.py`)

**Key Functions:**
- `fetch_all_settled_markets()`: Pull 12 months of settled markets
- `calculate_volatility()`: Compute σ from daily price movements
- `categorize_market()`: Map market metadata to domain category (Economics, Politics, etc.)

**Modifications Needed:**
- Add categorization logic (currently missing)
- Group markets by category before computing statistics
- Output category-level volatility summary

**Input:** Kalshi API (via `client.py`)

**Output:** `data/processed/category_volatility.csv`
```csv
category,mean_volatility,std_volatility,n_markets
Economics,0.18,0.05,423
Politics,0.72,0.12,891
...
```

---

### 5.3 `steering/entropy_mapping.py`

**Purpose:** Convert volatility statistics to steering magnitudes (α values).

**Status:** ⚠️ Not yet created

**Key Functions:**
- `load_volatility_stats()`: Read `category_volatility.csv`
- `normalize_to_alpha()`: Map σ → α using chosen scaling function
  ```python
  def normalize_to_alpha(sigma, sigma_min=0.1, sigma_max=0.9, alpha_range=(0.0, 1.5)):
      # Linear scaling or nonlinear (e.g., sqrt, log)
      normalized = (sigma - sigma_min) / (sigma_max - sigma_min)
      alpha = alpha_range[0] + normalized * (alpha_range[1] - alpha_range[0])
      return np.clip(alpha, *alpha_range)
  ```
- `save_entropy_map()`: Write `entropy_map.json`

**Input:** `data/processed/category_volatility.csv`

**Output:** `data/processed/entropy_map.json`

**Pseudo-logic:**
```
1. Load volatility data
2. Determine global min/max σ across categories
3. For each category:
     alpha = normalize(sigma, range=[0.0, 1.5])
4. Save mapping as JSON
```

---

### 5.4 `models/loader.py`

**Purpose:** Download and initialize HuggingFace models with caching.

**Status:** ⚠️ Not yet created

**Key Functions:**
- `download_model()`: Download model weights if not cached locally
  ```python
  from transformers import AutoModelForCausalLM, AutoTokenizer

  def load_model(model_name="meta-llama/Llama-3.3-70B-Instruct", device="cuda"):
      tokenizer = AutoTokenizer.from_pretrained(model_name)
      model = AutoModelForCausalLM.from_pretrained(
          model_name,
          torch_dtype=torch.float16,
          device_map="auto"
      )
      return model, tokenizer
  ```

**Input:** Model name (string)

**Output:** (`model`, `tokenizer`) tuple

**Design Notes:**
- Support model swapping via config file (e.g., `config.yaml`)
- Cache models in `~/.cache/huggingface/` (default HF behavior)
- Handle quantization options (8-bit, 4-bit for memory efficiency)

---

### 5.5 `steering/vector_extraction.py`

**Purpose:** Extract uncertainty vectors via contrastive activation analysis.

**Status:** ⚠️ Not yet created

**Key Functions:**
- `generate_contrastive_pairs()`: Create Hindsight vs Foresight prompts
  ```python
  pairs = [
      ("The Fed cut rates by 25bp.", "The Fed might cut rates by 25bp."),
      ("Inflation was 3.2% in Q4.", "Inflation is expected around 3.2%."),
      ...
  ]
  ```
- `extract_activations()`: Run prompts through model, cache hidden states
  ```python
  def extract_activations(model, tokenizer, text, layer_idx):
      inputs = tokenizer(text, return_tensors="pt")
      with torch.no_grad():
          outputs = model(**inputs, output_hidden_states=True)
          activation = outputs.hidden_states[layer_idx]  # [batch, seq, hidden_dim]
      return activation.mean(dim=1)  # Average over sequence
  ```
- `compute_difference_vector()`: `D = mean(Act_uncertain - Act_certain)`
- `save_vector()`: Write `.npy` file for reuse

**Input:** Pre-defined prompt pairs, target model

**Output:** `data/vectors/uncertainty_L{layer}.npy`

**Implementation Note:**
Follow methodology from AssistantAxis.pdf Section 2.1.2:
- Use middle residual stream layer (not too early, not too late)
- Average activations across token positions
- Normalize final vector to unit length

---

### 5.6 `steering/router.py`

**Purpose:** Classify input text into domain categories.

**Status:** ⚠️ Not yet created

**Two Implementation Options:**

**Option A: Keyword Heuristic (Simple, Fast)**
```python
KEYWORDS = {
    "Economics": ["fed", "inflation", "gdp", "unemployment", "interest rate"],
    "Politics": ["election", "senate", "congress", "president", "legislation"],
    ...
}

def classify_domain(text):
    text_lower = text.lower()
    scores = {cat: sum(kw in text_lower for kw in keywords)
              for cat, keywords in KEYWORDS.items()}
    return max(scores, key=scores.get)
```

**Option B: BERT Classifier (Robust, Slower)**
- Fine-tune small BERT on labeled Kalshi market titles
- Input: Market question → Output: Category logits

**Recommendation:** Start with Option A for prototyping, upgrade to Option B if needed.

**Input:** Text string (e.g., user query or market title)

**Output:** Category label (string)

---

### 5.7 `steering/inference.py`

**Purpose:** Apply activation steering during model inference.

**Status:** ⚠️ Not yet created

**Key Functions:**
- `load_steering_config()`: Load vector and entropy map
  ```python
  config = {
      "vector": np.load("data/vectors/uncertainty_L16.npy"),
      "entropy_map": json.load(open("data/processed/entropy_map.json")),
      "target_layer": 16
  }
  ```
- `steering_hook()`: PyTorch forward hook for activation modification
  ```python
  def steering_hook(module, input, output):
      # output is (batch, seq, hidden_dim)
      category = classify_domain(current_input_text)
      alpha = entropy_map[category]["alpha"]
      output += alpha * uncertainty_vector  # Broadcasting
      return output
  ```
- `run_with_steering()`: Main inference wrapper
  ```python
  def generate_with_steering(model, tokenizer, prompt, category=None):
      if category is None:
          category = classify_domain(prompt)

      # Register hook
      handle = model.model.layers[target_layer].register_forward_hook(steering_hook)

      # Generate
      outputs = model.generate(**tokenizer(prompt, return_tensors="pt"))

      # Cleanup
      handle.remove()
      return tokenizer.decode(outputs[0])
  ```

**Input:** Prompt text, optional category override

**Output:** Generated text with steered confidence

---

### 5.8 `evaluation/kelly_criterion.py`

**Purpose:** Simulate betting strategy based on model confidence.

**Status:** ⚠️ Not yet created

**Key Functions:**
- `kelly_bet_size()`: Compute optimal bet fraction
  ```python
  def kelly_fraction(p_win, odds):
      """
      p_win: Model's predicted probability of YES
      odds: Market odds (b in Kelly formula)
      Returns: Fraction of bankroll to bet
      """
      q_lose = 1 - p_win
      f = (p_win * odds - q_lose) / odds
      return max(0, f)  # Never bet negative (implies don't bet)
  ```
- `simulate_portfolio()`: Run backtest on historical markets
  ```python
  def simulate_portfolio(model, markets, initial_bankroll=10000):
      bankroll = initial_bankroll
      for market in markets:
          p_predicted = get_model_confidence(model, market.question)
          bet_fraction = kelly_fraction(p_predicted, market.odds)
          bet_amount = bankroll * bet_fraction

          if market.resolved_yes:
              bankroll += bet_amount * market.odds
          else:
              bankroll -= bet_amount

      return bankroll / initial_bankroll  # ROI
  ```

**Input:** Steered/unsteered model, historical Kalshi markets

**Output:**
- `results.csv`: Per-market bet outcomes
- ROI metric
- Bankruptcy flag

---

### 5.9 `evaluation/calibration.py`

**Purpose:** Measure probability calibration quality.

**Status:** ⚠️ Not yet created

**Key Metrics:**
1. **Brier Score:** `mean((p_predicted - y_actual)²)`
2. **Calibration Curve:** Plot predicted probability bins vs actual frequency
3. **Expected Calibration Error (ECE):** Weighted average of bin-wise errors

**Key Functions:**
- `compute_brier_score(predictions, outcomes)`
- `plot_calibration_curve(predictions, outcomes, n_bins=10)`
- `compute_ece(predictions, outcomes, n_bins=10)`

**Input:** Arrays of (predicted probabilities, actual outcomes)

**Output:** Metrics dictionary, calibration plot PNG

---

### 5.10 `evaluation/benchmarks.py`

**Purpose:** Ensure steering doesn't degrade core capabilities.

**Status:** ⚠️ Not yet created

**Benchmarks to Test:**
- **MMLU** (Massive Multitask Language Understanding): General knowledge
- **GSM8k**: Math reasoning
- **HumanEval**: Code generation
- **TruthfulQA**: Factual accuracy

**Implementation:**
```python
from lm_eval import evaluator

def run_benchmark(model, benchmark_name):
    results = evaluator.simple_evaluate(
        model=model,
        tasks=[benchmark_name],
        num_fewshot=5
    )
    return results["results"][benchmark_name]["acc"]
```

**Success Criterion:** Steered model performance ≥ 95% of unsteered baseline across all benchmarks.

---

## 6. Data Flow & Dependencies

### End-to-End Pipeline Diagram

```
┌──────────────────────────────────────────────────────────────┐
│ USER INPUT: "Will the Fed raise rates in Q2 2025?"          │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │ steering/router.py    │
         │ classify_domain()     │
         └───────────┬───────────┘
                     │ category = "Economics"
                     ▼
         ┌───────────────────────────────────┐
         │ Load entropy_map.json             │
         │ Lookup: alpha_econ = 0.3          │
         └───────────┬───────────────────────┘
                     │
                     ▼
         ┌───────────────────────────────────┐
         │ Load uncertainty_vector.npy       │
         │ v_uncertainty ∈ ℝ^4096            │
         └───────────┬───────────────────────┘
                     │
                     ▼
         ┌───────────────────────────────────┐
         │ models/loader.py                  │
         │ Load Llama-3.3-70B                │
         └───────────┬───────────────────────┘
                     │
                     ▼
         ┌───────────────────────────────────┐
         │ steering/inference.py             │
         │ Register forward hook at layer 16 │
         │ h ← h + 0.3 * v_uncertainty       │
         └───────────┬───────────────────────┘
                     │
                     ▼
         ┌───────────────────────────────────┐
         │ model.generate(prompt)            │
         │ Steered activations → output      │
         └───────────┬───────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────────┐
│ OUTPUT: "Based on current economic indicators, the Fed's      │
│ decision will likely depend on upcoming inflation data.       │
│ Confidence: Moderate (40-60% range)"                          │
└────────────────────────────────────────────────────────────────┘
```

### File Dependency Graph

```
entropy_map.json ──────┐
                       │
uncertainty_vector.npy ┼──→ steering/inference.py → STEERED MODEL
                       │         ↑
steering/router.py ────┘         │
                                 │
models/loader.py ────────────────┘

                    ↓ (evaluation)

kelly_criterion.py ←── historical Kalshi markets (kalshi/market_data.py)
calibration.py ────────  test set predictions
benchmarks.py ─────────  standard datasets (MMLU, GSM8k, etc.)
```

### Data Storage Structure

```
data/
├── raw/
│   └── kalshi_markets_12mo.json       # Cached API responses
│
├── processed/
│   ├── category_volatility.csv        # Per-category σ statistics
│   └── entropy_map.json               # Category → α mapping
│
└── vectors/
    ├── uncertainty_L12.npy            # Extracted vectors by layer
    ├── uncertainty_L16.npy            # (Primary vector)
    └── uncertainty_L20.npy

evaluation/
└── results/
    ├── kelly_simulation_steered.csv   # Bet outcomes
    ├── kelly_simulation_baseline.csv
    ├── calibration_curve.png          # Visualization
    └── benchmark_scores.json          # Capability preservation
```

---

## 7. Evaluation Methodology

### 7.1 Primary Metric: Kelly Criterion ROI

**Hypothesis:** Steered model will survive market volatility better than unsteered baseline.

**Simulation Setup:**
1. **Dataset:** 500 historical Kalshi markets (held-out test set, not used in volatility calculation)
2. **Models:**
   - Baseline (unsteered)
   - Steered (α from entropy map)
3. **Process:**
   - At market midpoint, ask model: "Will [market question] resolve YES?"
   - Extract confidence from model outputs (via logit analysis or explicit probability elicitation)
   - Compute Kelly bet size
   - Track bankroll over 500 sequential bets

**Success Criteria:**
- Steered model achieves **≥20% higher final ROI** than baseline
- Steered model **bankruptcy rate < 5%** (baseline expected ~20-30%)

### 7.2 Secondary Metric: Calibration Quality

**Brier Score Comparison:**
```
Brier_baseline = mean((p_unsteered - y_actual)²)
Brier_steered  = mean((p_steered - y_actual)²)

Improvement = (Brier_baseline - Brier_steered) / Brier_baseline
```

**Target:** ≥15% Brier score improvement

**Calibration Curve Analysis:**
- Plot 10 bins of predicted probability vs actual frequency
- Compute Expected Calibration Error (ECE)
- Ideal: Steered curve hugs diagonal (perfect calibration)

### 7.3 Capability Preservation

**Benchmark Suite:**
| Benchmark | Domain | Metric | Baseline Target |
|-----------|--------|--------|-----------------|
| MMLU | General Knowledge | Accuracy | ≥95% of unsteered |
| GSM8k | Math Reasoning | Accuracy | ≥95% of unsteered |
| HumanEval | Code Generation | pass@1 | ≥95% of unsteered |
| TruthfulQA | Factual Accuracy | % True | ≥95% of unsteered |

**Rationale:** Steering should improve calibration *without* degrading task performance.

### 7.4 Ablation Studies

**A. Layer Selection:**
- Test steering at layers: [8, 12, 16, 20, 24]
- Hypothesis: Middle layers (12-20) are most effective

**B. Magnitude Scaling:**
- Test α ranges: [0.0, 0.5, 1.0, 1.5, 2.0]
- Find optimal scale that balances calibration vs capability

**C. Category Granularity:**
- Compare: 5 categories vs 10 vs 20
- Hypothesis: Diminishing returns beyond ~10 categories

---

## 8. Next Steps & Extensions

### 8.1 Immediate Priorities

**Week 1-2: Phase 1 (Signal Extraction)**
- [ ] Implement `kalshi/entropy_mapping.py`
- [ ] Run volatility analysis on 12 months of Kalshi data
- [ ] Generate `entropy_map.json` with initial 5 categories

**Week 3-4: Phase 2 (Vector Extraction)**
- [ ] Create 100 Hindsight/Foresight prompt pairs
- [ ] Implement `steering/vector_extraction.py`
- [ ] Extract uncertainty vectors for layers 12, 16, 20
- [ ] Validate via manual inspection of steering effects

**Week 5-6: Phase 3 (Inference Integration)**
- [ ] Build `steering/router.py` (keyword-based classifier)
- [ ] Implement `steering/inference.py` with PyTorch hooks
- [ ] Test on example queries, verify steering is applied correctly

**Week 7-8: Phase 4 (Evaluation)**
- [ ] Implement Kelly Criterion simulation
- [ ] Run calibration analysis
- [ ] Execute capability benchmarks
- [ ] Compile results, write findings report

### 8.2 Potential Extensions

**A. Multi-Vector Steering (Mixture of Steers)**
- Extract not just PC1 (uncertainty magnitude) but also PC2-PC5 (uncertainty "texture")
- Test hypothesis: Different volatility *types* require different steering dimensions
  - Thin-tailed uncertainty (Economics) → PC1 only
  - Fat-tailed uncertainty (Crypto) → PC1 + PC2 (risk aversion)

**B. Adaptive α (Meta-Learning)**
- Rather than fixed entropy map, learn α dynamically based on context
- Train small MLP: `context_embedding → α_optimal`
- Could capture nuances beyond simple category labels

**C. Multi-Model Validation**
- Test steering on: Llama-3, Mistral-Large, Qwen-2.5
- Verify that uncertainty vectors transfer across model families
- If not, extract model-specific vectors

**D. Real-Time Deployment**
- Build API wrapper for steered inference
- Monitor calibration drift over time
- Retrain vectors quarterly as markets evolve

### 8.3 Open Questions

1. **Generalization:** Will vectors extracted from market-related prompts generalize to non-market domains (e.g., scientific predictions)?

2. **Composability:** Can we combine uncertainty steering with other interventions (e.g., factuality steering, toxicity reduction)?

3. **Interpretability:** What semantic concepts do the uncertainty vector components represent? Can we decompose it further?

4. **Optimal Extraction:** Is mean difference vector the best approach, or should we use PCA/sparse autoencoders for extraction?

---

## 9. Technical Considerations

### 9.1 Computational Requirements

**Model Loading:**
- Llama-3.3-70B in FP16: ~140GB VRAM
- Recommended: 2x A100 (80GB) or 4x A6000 (48GB)
- Alternative: Use quantized version (8-bit: ~70GB, 4-bit: ~35GB)

**Vector Extraction:**
- Single forward pass: ~2-5 seconds per prompt (with caching)
- 100 prompt pairs × 2 versions × 3 layers = ~10-15 minutes total
- One-time cost, reusable vectors

**Evaluation:**
- Kelly simulation on 500 markets: ~1-2 hours (sequential inference)
- Parallelizable across markets if needed

### 9.2 Reproducibility

**Random Seeds:**
- Set `torch.manual_seed(42)` for activation extraction
- Set `np.random.seed(42)` for data sampling

**Version Pinning:**
- `transformers==4.41.0`
- `torch==2.3.0`
- Model weights: Pin specific HuggingFace commit hash

**Data Snapshot:**
- Save exact Kalshi data pull timestamp
- Archive raw market JSON for future replication

### 9.3 Failure Modes & Mitigation

**Failure Mode 1: Vector doesn't generalize**
- *Symptom:* Steering works on market prompts but not general queries
- *Mitigation:* Expand prompt pairs to include non-market uncertainty examples

**Failure Mode 2: Steering degrades capabilities**
- *Symptom:* MMLU/GSM8k scores drop >5%
- *Mitigation:* Reduce α magnitude, apply steering only to specific layers

**Failure Mode 3: Category classifier is too coarse**
- *Symptom:* High within-category variance in optimal α
- *Mitigation:* Increase category granularity or use continuous α prediction

---

## Appendix A: Prompt Pair Examples

### Economics (Low Volatility)
```
Certain:   "The Federal Reserve raised interest rates by 25 basis points on March 22, 2023."
Uncertain: "The Federal Reserve may raise interest rates in the upcoming FOMC meeting."

Certain:   "US unemployment was 3.7% in December 2023."
Uncertain: "US unemployment is projected to be around 3.5-4.0% this quarter."
```

### Politics (High Volatility)
```
Certain:   "Joe Biden won the 2020 Presidential election with 306 electoral votes."
Uncertain: "The incumbent party might retain control of the Senate in the midterms."

Certain:   "The Infrastructure Investment and Jobs Act was signed into law on November 15, 2021."
Uncertain: "Congress could pass new climate legislation before the end of the session."
```

### Science (Medium Volatility)
```
Certain:   "The James Webb Space Telescope launched on December 25, 2021."
Uncertain: "The next Mars rover mission might discover signs of ancient microbial life."

Certain:   "The Higgs boson was discovered at CERN in 2012."
Uncertain: "Researchers may confirm room-temperature superconductivity within five years."
```

---

## Appendix B: Configuration Template

### `config.yaml`
```yaml
# Model Configuration
model:
  name: "meta-llama/Llama-3.3-70B-Instruct"
  device: "cuda"
  torch_dtype: "float16"
  quantization: null  # Options: null, "8bit", "4bit"

# Steering Configuration
steering:
  enabled: true
  target_layers: [16]  # Can specify multiple
  vector_path: "data/vectors/uncertainty_L16.npy"
  entropy_map_path: "data/processed/entropy_map.json"

# Kalshi Data
kalshi:
  api_key_id: "${KALSHI_API_KEY_ID}"  # From .env
  api_secret_path: "${KALSHI_API_SECRET_PATH}"
  lookback_months: 12
  categories:
    - Economics
    - Politics
    - Science
    - World_Events
    - Crypto

# Evaluation
evaluation:
  kelly_simulation:
    initial_bankroll: 10000
    n_test_markets: 500
  calibration:
    n_bins: 10
  benchmarks:
    - mmlu
    - gsm8k
    - humaneval
    - truthfulqa
```

---

## Appendix C: Expected Timeline

### 8-Week Implementation Plan

| Week | Phase | Deliverables |
|------|-------|-------------|
| 1 | Setup | Repo structure, Kalshi integration tested, initial data pull |
| 2 | Phase 1 | `entropy_map.json` generated, categories validated |
| 3 | Phase 2.1 | Prompt pairs created (100+), extraction pipeline tested |
| 4 | Phase 2.2 | Uncertainty vectors extracted for L12, L16, L20 |
| 5 | Phase 3.1 | Router implemented, steering hooks working |
| 6 | Phase 3.2 | End-to-end steered inference validated on examples |
| 7 | Phase 4.1 | Kelly simulation complete, calibration curves plotted |
| 8 | Phase 4.2 | Capability benchmarks run, final report written |

---

## Appendix D: Success Metrics Summary

### Minimum Viable Success
- ✅ Steered model ROI > Baseline ROI by ≥15%
- ✅ Brier score improvement ≥10%
- ✅ Zero capability degradation on MMLU/GSM8k

### Stretch Goals
- 🎯 ROI improvement ≥30%
- 🎯 Brier score improvement ≥20%
- 🎯 ECE < 0.05 (near-perfect calibration)
- 🎯 Steering vectors transfer across model families

---

**Last Updated:** 2026-02-11
**Version:** 1.0
**Status:** Blueprint (Pre-Implementation)
