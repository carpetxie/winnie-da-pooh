# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Winnie** is a research platform exploring novel signals in Kalshi prediction market data, aimed at producing publishable work for Kalshi's research arm (`research@kalshi.com`). The goal is to demonstrate non-trivial, economically-valuable insights from Kalshi data. See `Kalshi_Research.md` for submission guidelines and `crisis_alpha.md` for the quality/style bar.

Three experiments are implemented (1, 2, 5); two are designed but unimplemented (3, 4). See `EXPERIMENT.md` for full methodology.

## Commands

**Package manager:** `uv` (not pip). All commands use `uv run`.

```bash
# Install dependencies
uv sync

# Run Experiment 1 (Causal Lead-Lag)
uv run python -m experiment1.run                     # Full run
uv run python -m experiment1.run --quick-test        # Small subset
uv run python -m experiment1.run --skip-fetch        # Use cached data
uv run python -m experiment1.run --skip-granger      # Use cached Granger results
uv run python -m experiment1.run --skip-llm          # Use cached LLM assessments

# Run Experiment 2 (KUI)
uv run python -m experiment2.run                    # Full run
uv run python -m experiment2.run --quick-test       # 50 markets
uv run python -m experiment2.run --skip-fetch       # Use cached data
uv run python -m experiment2.run --skip-candles     # Use cached candles

# Run Experiment 5 (Embeddings)
uv run python -m experiment5.run                    # Full run (~20K markets)
uv run python -m experiment5.run --quick-test       # 500 markets
uv run python -m experiment5.run --skip-fetch       # Use cached markets.csv
uv run python -m experiment5.run --skip-embed       # Use cached embeddings.npy

# Tests
uv run python -m pytest experiment1/tests/test_unit.py -v
uv run python -m pytest experiment2/tests/test_unit.py -v
uv run python -m pytest experiment5/tests/test_unit.py -v
```

## Architecture

### Kalshi API (`kalshi/`)
- `client.py`: RSA-PSS SHA256 authenticated REST client. Credentials loaded from `.env` (`KALSHI_KEY_ID`, `KALSHI_PRIVATE_KEY_PATH`). Rate-limited (0.7s delay), cursor-based pagination.
- `market_data.py`: Market fetching utilities and volatility calculations.

### Experiment 1 — Causal Lead-Lag Discovery (`experiment1/`)
Pipeline: data collection → pairwise Granger causality (hourly, max_lag=24) → Bonferroni correction → LLM semantic filtering (Grok API) → signal-triggered trading simulation.
Discovers hidden causal dependencies across Kalshi domains. Compares 3 portfolios: all Granger pairs, LLM-filtered, random control.
Produces `data/exp1/` with granger_results, llm_assessments, trading_results.

### Experiment 2 — Kalshi Uncertainty Index (`experiment2/`)
Pipeline: data collection → index construction → validation → event study → visualization.
Produces `data/exp2/kui_daily.csv` with daily KUI + 6 domain sub-indices.
Includes regime-conditional analysis: `detect_shock_regime`, `regime_conditional_granger`, `regime_conditional_incremental_r2`, and `compute_shock_propagation` for cross-domain uncertainty transmission.

Key finding: KUI Granger-causes EPU (p=0.024, 2-day lag). During surprise/shock events, KUI leads EPU by 3 days and VIX by 2.25 days.

### Experiment 5 — Market Description Embeddings (`experiment5/`)
Pipeline: data collection → embeddings (BAAI/bge-base-en-v1.5, 768-dim) → clustering (PCA+t-SNE+HDBSCAN) → k-NN prediction → cross-domain discovery → visualization.
Produces `data/exp5/` with markets, embeddings, clustering results. Supports `--embedding-model` CLI flag for model swaps.

Key finding: On thin markets (<50 trades), k-NN text-only predictor beats random by 47.8% (Brier 0.1734 vs 0.3322).

### Common Patterns
- **Phase-based pipelines**: Each module is independent; expensive steps cached and skippable via `--skip-*` flags.
- **Caching with validation**: `.npy` embeddings cached with metadata (model name, n_texts) to detect stale cache.
- **Synthetic test data**: All unit tests use synthetic data (no API calls, no downloads).
- **Domain classification**: Kalshi tickers mapped to economic domains via `UNCERTAINTY_DOMAIN_MAP`.

## Data Layout

```
data/
├── raw/          # Raw API responses
├── exp1/         # Lead-lag outputs (granger_results, llm_assessments, trading)
├── exp2/         # KUI outputs (kui_daily.csv, correlations, regime_conditional, plots)
├── exp5/         # Embedding outputs (markets.csv, embeddings.npy, clusters)
├── processed/    # Intermediate processing
└── evaluation/   # Test results, metrics
```

## Key Research Context

The Kalshi research quality bar is set by `crisis_alpha.md` — rigorous, evidence-led, with statistical validation and clear practical implications. Submissions should lead with concrete quantitative findings.

Unimplemented experiments:
1. **Experiment 4** (Information Speed): Kalshi vs. traditional markets around economic releases.
2. **Experiment 3** (Self-Play DPO): Fine-tune LLM on Kalshi outcomes. Requires GPU.
