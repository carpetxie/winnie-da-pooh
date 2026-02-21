# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Winnie** is a research platform analyzing Kalshi prediction market data, producing a focused paper: "When Do Prediction Market Distributions Add Value? A CRPS/MAE Diagnostic." See `docs/findings.md` for the paper.

Core result: The CRPS/MAE ratio reveals heterogeneous distributional calibration — Jobless Claims distributions add massive value (ratio=0.37) while CPI distributions are actively harmful (ratio=1.32).

## Commands

**Package manager:** `uv` (not pip). All commands use `uv run`.

```bash
# Install dependencies
uv sync

# Run Experiment 1 (Causal Lead-Lag — data provider)
uv run python -m experiment1.run                     # Full run
uv run python -m experiment1.run --skip-fetch        # Use cached data
uv run python -m experiment1.run --skip-granger      # Use cached Granger results
uv run python -m experiment1.run --skip-llm          # Use cached LLM assessments

# Run Experiment 2 (KUI — data provider, cached candles used by 7, 11, 12, 13)
uv run python -m experiment2.run                    # Full run
uv run python -m experiment2.run --skip-fetch       # Use cached data
uv run python -m experiment2.run --skip-candles     # Use cached candles

# Run Experiment 7 (Implied Distributions & No-Arbitrage — no API calls)
uv run python -m experiment7.run

# Run Experiment 8 (TIPS Breakeven Comparison)
uv run python -m experiment8.run                    # Full run (fetches FRED data)
uv run python -m experiment8.run --skip-fetch       # Use cached TIPS data

# Run Experiment 11 (Favorite-Longshot Bias × Microstructure — no API calls)
uv run python -m experiment11.run

# Run Experiment 12 (CRPS Distributional Calibration — fetches FRED data)
uv run python -m experiment12.run

# Run Experiment 13 (Unified Distributional Calibration + CPI Horse Race — fetches FRED data)
uv run python -m experiment13.run

# Tests
uv run python -m pytest experiment1/tests/test_unit.py -v
uv run python -m pytest experiment2/tests/test_unit.py -v
```

## Architecture

### Kalshi API (`kalshi/`)
- `client.py`: RSA-PSS SHA256 authenticated REST client. Credentials loaded from `.env` (`KALSHI_KEY_ID`, `KALSHI_PRIVATE_KEY_PATH`). Rate-limited (0.7s delay), cursor-based pagination.
- `market_data.py`: Market fetching utilities and volatility calculations.

### Experiment 1 — Causal Lead-Lag Discovery (`experiment1/`)
Data provider. Pipeline: data collection → ADF stationarity + differencing → pairwise Granger causality (hourly, max_lag=24) → Bonferroni correction → LLM semantic filtering → propagation network analysis.

### Experiment 2 — Kalshi Uncertainty Index (`experiment2/`)
Data provider. Pipeline: data collection → index construction → validation → event study → visualization. Produces cached candle data used by experiments 7, 11, 12, 13.

### Experiment 7 — Implied Distributions & No-Arbitrage (`experiment7/`)
Section 1 of paper. Pipeline: load targeted markets → group by event → build implied CDFs at each hour → test monotonicity → reconstruct PDFs.

Key findings: 336 multi-strike markets across 41 events. No-arbitrage violations in 2.8% of snapshots (comparable to SPX options), 86% revert within 1h.

### Experiment 8 — TIPS Breakeven Comparison (`experiment8/`)
Section 3 of paper. Pipeline: build daily Kalshi CPI index → fetch TIPS breakeven from FRED → Granger causality both directions.

Key finding: TIPS Granger-causes Kalshi CPI (F=12.2, p=0.005). Bond market leads prediction market by 1 day.

### Experiment 11 — Favorite-Longshot Bias × Microstructure (`experiment11/`)
Section 4 of paper. Pipeline: load settled markets → analyze by time to expiration → 50%-lifetime controlled analysis.

Key findings: T-24h gradient 7x collapses to 1.5x after controlling for observation timing.

### Experiment 12 — CRPS Distributional Calibration (`experiment12/`)
Section 2 of paper (base functions). Pipeline: load multi-strike markets → fetch FRED historical benchmarks → compute CRPS per event.

### Experiment 13 — Unified Distributional Calibration + CPI Horse Race (`experiment13/`)
Main paper pipeline (Sections 2-3). Merges exp7+exp12 → per-series Wilcoxon with Bonferroni correction and rank-biserial effect sizes → CRPS/MAE ratio → temporal CRPS evolution → CPI horse race vs SPF + TIPS + naive benchmarks → power analysis → PIT diagnostic.

Key findings: CRPS/MAE ratio CPI=1.32 (harmful), Jobless Claims=0.37 (adds value). Jobless Claims vs Historical p=0.047 raw (p_adj=0.093 Bonferroni, r=0.49). Kalshi beats random walk (p=0.026, d=-0.60).

### Common Patterns
- **Phase-based pipelines**: Each module is independent; expensive steps cached and skippable via `--skip-*` flags.
- **Synthetic test data**: All unit tests use synthetic data (no API calls, no downloads).

## Data Layout

```
data/
├── exp1/         # Lead-lag outputs (granger_results, propagation_network)
├── exp2/         # KUI outputs (kui_daily.csv, raw/candles/ — shared data provider)
├── exp7/         # Implied distributions (strike_markets.csv, implied_distribution_results.json, plots)
├── exp8/         # TIPS comparison (kalshi_cpi_daily.csv, T10YIE.csv, tips_comparison_results.json, plots)
├── exp11/        # Favorite-longshot bias (favorite_longshot_results.json, plots)
├── exp12/        # CRPS distributional calibration (crps_results.json, crps_per_event.csv, plots)
└── exp13/        # Unified calibration + horse race (unified_results.json, crps_per_event.csv, plots)
```

## Docs

```
docs/
├── findings.md            # Paper: "When Do Prediction Market Distributions Add Value?"
└── evaluation_prompt.md   # PhD-level review prompt for external evaluation
```
