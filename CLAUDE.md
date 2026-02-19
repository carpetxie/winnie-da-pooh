# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Winnie** is a research platform exploring novel signals in Kalshi prediction market data, aimed at producing publishable work for Kalshi's research arm (`research@kalshi.com`). The goal is to demonstrate non-trivial, economically-valuable insights from Kalshi data.

Five experiments are implemented (1, 2, 3, 4, 5). See `docs/findings.md` for the two surviving findings after PhD-level methodology review.

## Commands

**Package manager:** `uv` (not pip). All commands use `uv run`.

```bash
# Install dependencies
uv sync

# Run Experiment 1 (Causal Lead-Lag)
uv run python -m experiment1.run                     # Full run
uv run python -m experiment1.run --skip-fetch        # Use cached data
uv run python -m experiment1.run --skip-granger      # Use cached Granger results
uv run python -m experiment1.run --skip-llm          # Use cached LLM assessments

# Run Experiment 2 (KUI)
uv run python -m experiment2.run                    # Full run
uv run python -m experiment2.run --skip-fetch       # Use cached data
uv run python -m experiment2.run --skip-candles     # Use cached candles

# Run Experiment 3 (Calibration Under Uncertainty — no API calls)
uv run python -m experiment3.run

# Run Experiment 4 (Hourly Information Speed — no API calls)
uv run python -m experiment4.run

# Run Experiment 5 (Embeddings)
uv run python -m experiment5.run                    # Full run (~20K markets)
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
Pipeline: data collection → ADF stationarity + differencing → pairwise Granger causality (hourly, max_lag=24) → Bonferroni correction → LLM semantic filtering (Grok API) → signal-triggered trading simulation → propagation network analysis.

Key finding: inflation → monetary_policy at 3h median (Mann-Whitney p=0.0008), validated by permutation test (p<0.001). 231 unidirectional pairs after removing 74 bidirectional co-movement pairs. Shock acceleration finding invalidated by corrected classification. No trading alpha.

### Experiment 2 — Kalshi Uncertainty Index (`experiment2/`)
Pipeline: data collection → index construction → validation → event study → visualization.
Produces `data/exp2/kui_daily.csv` with daily KUI + 6 domain sub-indices.

Note: Original KUI→EPU Granger finding (p=0.024) invalidated by methodology fix (percentage returns). Event study directionally consistent but weak.

### Experiment 3 — Calibration Under Uncertainty (`experiment3/`)
Pipeline: load exp2 markets + KUI → assign uncertainty regimes → compute Brier/ECE per regime → bootstrap significance test.
No API calls required. Uses existing exp2 data.

Key finding: Markets genuinely better calibrated during high uncertainty (Murphy reliability 0.123 vs 0.262, p<0.05). Survives base rate controls via Murphy decomposition. GDP markets show 4x improvement.

### Experiment 4 — Hourly Information Speed (`experiment4/`)
Pipeline: load cached hourly candles → compute hourly BV per domain → event windows ±72h → detect first significant move → compare vs EPU/VIX daily.
No API calls required. Uses cached hourly candle data from exp2.

Key finding: Kalshi reacts to surprise events ~56h before EPU. Directionally consistent but underpowered (Wilcoxon p=0.10).

### Experiment 5 — Market Description Embeddings (`experiment5/`)
Pipeline: data collection → embeddings (BAAI/bge-large-en-v1.5) → clustering (PCA+UMAP+HDBSCAN) → k-NN prediction → cross-domain discovery.

Key finding: k-NN(k=20) beats random by 15.7% on Brier. Cross-domain clusters are superficial (linguistic, not economic).

### Common Patterns
- **Phase-based pipelines**: Each module is independent; expensive steps cached and skippable via `--skip-*` flags.
- **Stationarity**: Granger tests use ADF-tested, differenced series (not raw price levels).
- **Domain classification**: Experiment 1 uses fine-grained `FINE_DOMAIN_MAP` (inflation, monetary_policy, labor, macro, fiscal). Experiment 2 uses `UNCERTAINTY_DOMAIN_MAP`.
- **Synthetic test data**: All unit tests use synthetic data (no API calls, no downloads).

## Data Layout

```
data/
├── exp1/         # Lead-lag outputs (granger_results, propagation_network, trading)
├── exp2/         # KUI outputs (kui_daily.csv, correlations, event_study, plots, raw/candles/)
├── exp3/         # Calibration outputs (calibration_results.json, fiscal_anomaly, plots)
├── exp4/         # Hourly event study (hourly_event_results.csv, statistical_tests, plots)
└── exp5/         # Embedding outputs (markets.csv, embeddings.npy, clusters)
```

## Docs

```
docs/
└── findings.md     # Surviving findings after PhD-review methodology corrections
```
