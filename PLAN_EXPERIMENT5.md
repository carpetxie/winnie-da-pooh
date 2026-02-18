# Experiment 5: Market Description Embeddings as Economic Similarity Metric
## Comprehensive Planning Document

**Created:** 2026-02-11
**Status:** Implementation Plan

---

## 1. Objective

Demonstrate that LLM embeddings of Kalshi market descriptions, combined with settlement outcomes, reveal hidden economic structure. Markets with similar descriptions should have correlated outcomes. This similarity metric can predict new market outcomes from text alone, without price data.

**Key Deliverables:**
1. UMAP visualization of embedding space colored by domain/outcome/cluster
2. Prediction performance table: k-NN vs market price vs random baseline
3. Cluster catalog: Top 20 clusters with descriptions, outcome correlations
4. Cross-domain discoveries: 3-5 surprising relationships with LLM explanations
5. Market recommendation prototype: "Markets similar to X"

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    experiment5/run.py                         │
│                   (Main Orchestrator)                         │
└─────────────┬───────────────────────────────────┬───────────┘
              │                                   │
    ┌─────────▼──────────┐              ┌─────────▼──────────┐
    │  data_collection.py │              │   embeddings.py    │
    │  Fetch all settled  │──────────────▶  Generate vectors  │
    │  markets + text     │              │  sentence-transformers│
    └─────────┬──────────┘              └─────────┬──────────┘
              │                                   │
              │  data/exp5/markets.csv             │  data/exp5/embeddings.npy
              │                                   │
    ┌─────────▼──────────┐              ┌─────────▼──────────┐
    │  clustering.py      │◄─────────────│  prediction.py     │
    │  UMAP + HDBSCAN     │              │  k-NN predictor    │
    │  Outcome correlation │              │  Brier scores      │
    └─────────┬──────────┘              └─────────┬──────────┘
              │                                   │
    ┌─────────▼──────────┐              ┌─────────▼──────────┐
    │  cross_domain.py    │              │   visualize.py     │
    │  LLM explanations   │              │   UMAP plots       │
    │  (Grok API)         │              │   Performance tables│
    └────────────────────┘              └────────────────────┘
```

---

## 3. Data Requirements

### 3.1 Current State Problem
The existing cache (`settled_markets_6000.json`) contains 6000 markets but 98.8% are `KXMVESPORTSMULTIGAMEEXTENDED` (esports parlays). This is insufficient for cross-domain analysis.

### 3.2 Solution: Full Historical Fetch
Paginate through ALL settled markets from the past 12 months. Expected yield: 10,000-50,000+ markets spanning:
- **Economics:** CPI, NFP, Fed rate, jobless claims, GDP (KXCPI, KXNFP, KXFED, etc.)
- **Crypto:** BTC, ETH, SOL 15-min price movements (KXBTC15M, KXETH15M, KXSOL15M)
- **Sports:** NBA, NHL, NCAA, soccer, tennis, UFC
- **Esports:** Multi-game extended markets
- **Weather:** Temperature, precipitation
- **Politics:** Elections, government actions

### 3.3 Text Fields
| Field | Availability | Usage |
|-------|-------------|-------|
| `title` | 100% | Primary text for embedding |
| `rules_primary` | ~1-5% | Supplementary (when available) |
| `rules_secondary` | ~1-5% | Supplementary (when available) |
| `event_ticker` | 100% | Domain classification |
| `ticker` | 100% | Domain prefix extraction |

### 3.4 Embedding Text Construction
```
text = title
if rules_primary:
    text += " | " + rules_primary
```

### 3.5 Outcome Variable
- Binary: `result == "yes"` → 1, `result == "no"` → 0
- Scalar markets (result == "scalar"): Use `settlement_value_dollars` normalized

### 3.6 Train/Test Split
- 80% earliest by settlement date → train
- 20% most recent → test
- No leakage: k-NN predictions use only training set neighbors

---

## 4. Module Design

### 4.1 `experiment5/data_collection.py`

**Purpose:** Fetch and cache all settled markets with text descriptions.

**Functions:**
- `fetch_all_settled_markets_full(client) -> pd.DataFrame`: Paginate through entire settled market history
- `extract_text(row) -> str`: Build embedding text from title + rules
- `extract_domain(ticker) -> str`: Classify market domain from ticker prefix
- `prepare_dataset(df) -> pd.DataFrame`: Clean, filter, add domain labels

**Output:** `data/exp5/markets.csv`

**Columns:** ticker, event_ticker, domain, title, rules_primary, text_for_embedding, result_binary, volume, settlement_ts, open_time, close_time, last_price_dollars, split

### 4.2 `experiment5/embeddings.py`

**Purpose:** Generate and cache sentence embeddings.

**Model Choice:** `all-MiniLM-L6-v2` (384-dim)
- Fast on CPU (no GPU required)
- Good semantic similarity performance
- 80MB model size
- If quality insufficient, fall back to `bge-large-en-v1.5` (1024-dim)

**Functions:**
- `load_or_generate_embeddings(texts, model_name, cache_path) -> np.ndarray`: Generate or load cached embeddings
- `compute_similarity_matrix(embeddings) -> np.ndarray`: Pairwise cosine similarity (for analysis)

**Output:** `data/exp5/embeddings.npy`, `data/exp5/embedding_metadata.json`

### 4.3 `experiment5/clustering.py`

**Purpose:** Discover natural structure in embedding space.

**Functions:**
- `run_umap(embeddings, n_components=2) -> np.ndarray`: Dimensionality reduction
- `run_hdbscan(umap_coords, min_cluster_size=15) -> np.ndarray`: Cluster labels
- `compute_cluster_stats(df, cluster_labels) -> pd.DataFrame`: Outcome correlation, domain composition, size per cluster
- `permutation_test_clusters(df, cluster_labels, n_perms=1000) -> pd.DataFrame`: Statistical significance of outcome correlations

**Output:** `data/exp5/clusters.csv`, `data/exp5/umap_coords.npy`

### 4.4 `experiment5/prediction.py`

**Purpose:** k-NN prediction system.

**Functions:**
- `knn_predict(train_embeddings, train_outcomes, test_embeddings, k) -> np.ndarray`: Weighted k-NN prediction
- `compute_brier_score(predictions, actuals) -> float`: Brier score
- `evaluate_all_baselines(df, embeddings, k_values) -> pd.DataFrame`: Compare k-NN vs market price vs random
- `stratified_evaluation(df, embeddings, k) -> pd.DataFrame`: Performance by volume bucket (thin vs thick markets)

**Output:** `data/exp5/predictions.csv`, `data/exp5/evaluation_results.csv`

### 4.5 `experiment5/cross_domain.py`

**Purpose:** Identify cross-domain clusters and explain them.

**Functions:**
- `find_cross_domain_clusters(cluster_stats) -> pd.DataFrame`: Clusters with 2+ domains represented
- `explain_cluster_with_llm(cluster_markets, grok_api_key) -> str`: Use Grok to explain economic relationships
- `validate_cross_domain_correlations(df, cluster_labels) -> pd.DataFrame`: Test if cross-domain similarity = correlated outcomes

**Output:** `data/exp5/cross_domain_discoveries.json`

### 4.6 `experiment5/visualize.py`

**Purpose:** Generate all plots and tables.

**Functions:**
- `plot_umap_by_domain(umap_coords, domains)`: Colored by market domain
- `plot_umap_by_outcome(umap_coords, outcomes)`: Colored by YES/NO
- `plot_umap_by_cluster(umap_coords, cluster_labels)`: Colored by cluster
- `plot_prediction_comparison(results)`: Bar chart of Brier scores
- `plot_calibration_curve(predictions, actuals)`: Reliability diagram
- `generate_cluster_catalog(cluster_stats)`: Table of top 20 clusters

**Output:** `data/exp5/plots/` directory

### 4.7 `experiment5/run.py`

**Purpose:** End-to-end orchestrator.

**Phases:**
1. Data collection (or load cached)
2. Embedding generation (or load cached)
3. Clustering + structure discovery
4. k-NN prediction evaluation
5. Cross-domain discovery
6. Visualization + results summary

**CLI Arguments:**
- `--quick-test`: Run on 200 markets (for testing)
- `--skip-fetch`: Use cached market data
- `--skip-embed`: Use cached embeddings
- `--k-values`: Comma-separated k values (default: 5,10,20)

---

## 5. Dependencies

### New packages needed:
```
sentence-transformers>=3.0.0   # Embedding generation
umap-learn>=0.5.0              # Dimensionality reduction
hdbscan>=0.8.0                 # Density-based clustering
scipy>=1.14.0                  # Statistical tests
```

### Already available:
```
numpy, pandas, scikit-learn, matplotlib, requests, tqdm, python-dotenv, cryptography
```

---

## 6. Success Metrics

| Metric | Threshold | Measurement |
|--------|-----------|-------------|
| k-NN Brier < Random Brier | Statistically significant (p < 0.05) | Paired permutation test |
| k-NN beats market price on thin markets | Better Brier on volume < 50 bucket | Stratified evaluation |
| High-quality clusters | ≥ 10 clusters with outcome correlation > 0.3 | Permutation test p < 0.05 |
| Cross-domain discoveries | ≥ 3 clusters spanning 2+ domains | Manual + LLM validation |
| Domain separation in embedding space | Silhouette score > 0.1 | sklearn.metrics |

---

## 7. Testing Strategy

### 7.1 Unit Tests (Run First)
- Test data_collection with mock API responses
- Test embedding generation with synthetic texts
- Test clustering with known structure (3 well-separated clusters)
- Test k-NN prediction with toy data
- Test Brier score computation with known values

### 7.2 Integration Tests (Small Scale)
- Run full pipeline on 200 markets (--quick-test mode)
- Verify all files are generated
- Verify plots render without errors
- Verify metrics are computed correctly

### 7.3 Full Run
- Run on all available settled markets
- Validate results against success metrics
- Generate final deliverables

---

## 8. Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| API rate limiting | 0.7s delay between requests, cache all responses |
| Insufficient category diversity | Fetch ALL settled markets, not just recent |
| Embeddings dominated by sports | Domain-balanced sampling for evaluation |
| HDBSCAN noise points | Tune min_cluster_size; report noise fraction |
| Model download fails | Fallback to TF-IDF + SVD (no external model needed) |
| Memory issues with large embedding matrix | Batch processing, memory-mapped files |

---

## 9. Execution Order

1. Install dependencies
2. Write unit tests (test with synthetic data)
3. Build data_collection.py → run + verify
4. Build embeddings.py → run + verify
5. Build clustering.py → run + verify
6. Build prediction.py → run + verify
7. Build cross_domain.py → run + verify
8. Build visualize.py → run + verify
9. Build run.py orchestrator
10. Run --quick-test (200 markets)
11. Run full pipeline
12. Generate results_summary.md

---

## 10. File Layout

```
experiment5/
├── __init__.py
├── run.py                  # Orchestrator
├── data_collection.py      # Market fetching
├── embeddings.py           # Vector generation
├── clustering.py           # UMAP + HDBSCAN
├── prediction.py           # k-NN prediction
├── cross_domain.py         # LLM explanations
├── visualize.py            # Plots + tables
└── tests/
    ├── __init__.py
    ├── test_data_collection.py
    ├── test_embeddings.py
    ├── test_clustering.py
    ├── test_prediction.py
    └── test_integration.py

data/exp5/
├── markets.csv             # All markets with text
├── embeddings.npy          # Embedding vectors
├── embedding_metadata.json # Model info, dimensions
├── umap_coords.npy         # 2D UMAP projection
├── clusters.csv            # Cluster assignments + stats
├── predictions.csv         # k-NN predictions
├── evaluation_results.csv  # Brier scores, comparisons
├── cross_domain_discoveries.json
└── plots/
    ├── umap_by_domain.png
    ├── umap_by_outcome.png
    ├── umap_by_cluster.png
    ├── brier_comparison.png
    ├── calibration_curve.png
    └── cluster_catalog.png
```
