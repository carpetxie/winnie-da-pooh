# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Winnie** is a research platform exploring novel signals in Kalshi prediction market data, aimed at producing publishable work for Kalshi's research arm (`research@kalshi.com`). The goal is to demonstrate non-trivial, economically-valuable insights from Kalshi data.

Eleven experiments are implemented (1-11). See `docs/findings.md` for the seven strong findings plus supporting results after PhD-level methodology review.

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

# Run Experiment 6 (Market Microstructure — no API calls)
uv run python -m experiment6.run

# Run Experiment 7 (Implied Distributions & No-Arbitrage — no API calls)
uv run python -m experiment7.run

# Run Experiment 8 (TIPS Breakeven Comparison)
uv run python -m experiment8.run                    # Full run (fetches FRED data)
uv run python -m experiment8.run --skip-fetch       # Use cached TIPS data

# Run Experiment 9 (Indicator-Level Network — no API calls)
uv run python -m experiment9.run

# Run Experiment 10 (Cross-Event Shock Propagation — no API calls)
uv run python -m experiment10.run

# Run Experiment 11 (Favorite-Longshot Bias × Microstructure — no API calls)
uv run python -m experiment11.run

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

### Experiment 6 — Market Microstructure (`experiment6/`)
Pipeline: load all 725 cached candle files → extract bid-ask spread, open interest, OHLC range, volume → analyze spread as uncertainty → OI as conviction → event microstructure → spread vs KUI correlation.
No API calls required. Uses cached hourly candle data from exp2.

Key findings: Spread narrows after events (Wilcoxon p=0.013), range widens (p=0.017). Spread-KUI correlation r=0.25 (p<0.001). Higher-OI markets better calibrated (Brier 0.147 vs 0.246).

### Experiment 7 — Implied Distributions & No-Arbitrage (`experiment7/`)
Pipeline: load targeted markets with floor_strike → group by event_ticker → build implied CDFs at each hour → test monotonicity → reconstruct PDFs → compare to realized outcomes.
No API calls required. Uses cached data from exp2.

Key findings: CPI median forecast error 0.05pp. No-arbitrage violations in 2.8% of snapshots, 71% revert within 1h. 336 multi-strike markets across 41 events.

### Experiment 8 — TIPS Breakeven Comparison (`experiment8/`)
Pipeline: build daily Kalshi CPI index from candles → fetch TIPS breakeven from FRED → correlation → cross-correlation at lags → Granger causality both directions.
Requires FRED API fetch for T10YIE and T5YIE.

Key finding: TIPS Granger-causes Kalshi CPI (F=12.2, p=0.005). Kalshi does NOT Granger-cause TIPS. Bond market leads prediction market by 1 day.

### Experiment 9 — Indicator-Level Network (`experiment9/`)
Pipeline: load exp1 Granger results → classify by indicator (CPI/PCE/PPI/Fed Funds/etc.) → build indicator-level directed graph → centrality analysis → lag asymmetry tests.
No API calls required. Uses cached Granger results from exp1.

Key finding: CPI → Fed Funds at 3h median (57 pairs, Mann-Whitney p=0.009). CPI dominates over PCE/PPI as market-implied inflation signal.

### Experiment 10 — Cross-Event Shock Propagation (`experiment10/`)
Pipeline: load hourly series → compute event responses (-24h to +48h) → build propagation heatmap → analyze surprise vs non-surprise → cross-domain contagion analysis → temporal cascade matrix → visualization.
No API calls required. Uses cached hourly candle data from exp2.

Key findings: Macro markets respond first to CPI/NFP events (within 4-8h). Surprise events cause 1.5-2.6x larger responses in inflation (p=0.0002) and monetary policy (p=0.007). 205 markets, 31 events, 9,108 observations.

### Experiment 11 — Favorite-Longshot Bias × Microstructure (`experiment11/`)
Pipeline: load settled markets → load hourly microstructure → test overall FLB → analyze by OI/spread/volume tercile → analyze by time to expiration → domain breakdown → visualization.
No API calls required. Uses cached data from exp2.

Key findings: Spread predicts calibration quality: low-spread Brier=0.0001 vs high-spread Brier=0.130. Longshot bias concentrates in wide-spread markets (+0.040) and nearly vanishes in tight-spread markets (+0.011). Extends Whelan (CEPR 2024).

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
├── exp5/         # Embedding outputs (markets.csv, embeddings.npy, clusters)
├── exp6/         # Microstructure (microstructure_summary.csv, microstructure_results.json, plots)
├── exp7/         # Implied distributions (strike_markets.csv, implied_distribution_results.json, plots)
├── exp8/         # TIPS comparison (kalshi_cpi_daily.csv, T10YIE.csv, tips_comparison_results.json, plots)
├── exp9/         # Indicator network (granger_with_indicators.csv, indicator_network_results.json, plots)
├── exp10/        # Shock propagation (shock_propagation_results.json, event_responses.csv, plots)
└── exp11/        # Favorite-longshot bias (favorite_longshot_results.json, plots)
```

## Docs

```
docs/
└── findings.md     # Surviving findings after PhD-review methodology corrections
```
