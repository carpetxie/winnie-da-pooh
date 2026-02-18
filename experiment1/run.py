"""
experiment1/run.py

Main orchestrator for Experiment 1: Cross-Market Causal Lead-Lag Discovery.

Discovers hidden causal dependencies between Kalshi markets across different
domains using Granger causality + LLM semantic filtering.

Usage:
    uv run python -m experiment1.run                     # Full run
    uv run python -m experiment1.run --quick-test        # Small subset
    uv run python -m experiment1.run --skip-fetch        # Use cached data
    uv run python -m experiment1.run --skip-granger      # Use cached Granger results
    uv run python -m experiment1.run --skip-llm          # Use cached LLM assessments
"""

import os
import json
import argparse
import numpy as np
import pandas as pd
from datetime import datetime

DATA_DIR = "data/exp1"


def phase1_data_collection(quick_test: bool = False, max_markets: int = None):
    """Phase 1: Fetch markets, find concurrent pairs, extract hourly prices."""
    print("\n" + "=" * 70)
    print("PHASE 1: DATA COLLECTION")
    print("=" * 70)

    from experiment1.data_collection import (
        load_all_markets,
        prepare_market_metadata,
        find_concurrent_pairs,
        fetch_hourly_prices,
    )
    from kalshi.client import KalshiClient

    # Load all markets (fast - just reads JSON), then filter metadata
    markets = load_all_markets()
    df = prepare_market_metadata(markets)

    # Save metadata
    df.to_csv(os.path.join(DATA_DIR, "markets.csv"), index=False)

    # Find concurrent pairs
    pairs = find_concurrent_pairs(
        df,
        min_overlap_hours=48,
        max_pairs=50000 if not quick_test else 5000,
        cross_domain_only=True,
    )

    # Save pairs
    with open(os.path.join(DATA_DIR, "concurrent_pairs.json"), "w") as f:
        json.dump(pairs, f)

    # Fetch hourly prices
    client = KalshiClient()
    # Only fetch candles for tickers that appear in pairs
    pair_tickers = set()
    for a, b in pairs:
        pair_tickers.add(a)
        pair_tickers.add(b)
    df_pairs = df[df["ticker"].isin(pair_tickers)]
    print(f"  Fetching candles for {len(df_pairs)} markets involved in pairs...")

    hourly_prices = fetch_hourly_prices(client, df_pairs, max_markets=max_markets)

    return df, pairs, hourly_prices


def phase2_granger(hourly_prices, pairs, market_df):
    """Phase 2: Pairwise Granger causality + Bonferroni correction."""
    print("\n" + "=" * 70)
    print("PHASE 2: GRANGER CAUSALITY ANALYSIS")
    print("=" * 70)

    from experiment1.granger_pipeline import run_granger_stage

    all_results, significant = run_granger_stage(
        hourly_prices, pairs, market_df, max_lag=24, alpha=0.01
    )

    print(f"\n  Total directional tests: {len(all_results)}")
    print(f"  Significant after Bonferroni: {len(significant)}")

    if not significant.empty:
        print("\n  Top 10 most significant pairs:")
        for _, row in significant.head(10).iterrows():
            print(f"    {row['leader_domain']}:{row['leader_ticker'][:30]} -> "
                  f"{row['follower_domain']}:{row['follower_ticker'][:30]} "
                  f"(lag={row['best_lag']}h, p={row['adjusted_p']:.6f})")

    return all_results, significant


def phase3_llm_filtering(significant_pairs, market_df):
    """Phase 3: LLM semantic plausibility filtering."""
    print("\n" + "=" * 70)
    print("PHASE 3: LLM SEMANTIC FILTERING")
    print("=" * 70)

    from experiment1.llm_filtering import run_llm_filtering
    from dotenv import load_dotenv
    load_dotenv()

    grok_api_key = os.getenv("GROK_API_KEY")
    if not grok_api_key:
        print("  WARNING: No GROK_API_KEY found. Skipping LLM filtering.")
        significant_pairs = significant_pairs.copy()
        significant_pairs["plausibility_score"] = 0
        significant_pairs["llm_explanation"] = "No API key"
        significant_pairs["llm_approved"] = False
        return significant_pairs

    filtered = run_llm_filtering(significant_pairs, grok_api_key, min_score=4)

    # Save
    filtered.to_csv(os.path.join(DATA_DIR, "llm_filtered_pairs.csv"), index=False)

    n_approved = filtered["llm_approved"].sum() if "llm_approved" in filtered.columns else 0
    print(f"\n  LLM-approved pairs: {n_approved}")

    if n_approved > 0:
        print("\n  Top LLM-approved pairs:")
        approved = filtered[filtered["llm_approved"]].head(10)
        for _, row in approved.iterrows():
            print(f"    [{row['plausibility_score']}/5] "
                  f"{row['leader_domain']} -> {row['follower_domain']}: "
                  f"{row.get('llm_explanation', '')[:80]}")

    return filtered


def phase4_trading_simulation(hourly_prices, all_significant, llm_filtered):
    """Phase 4: Signal-triggered trading simulation."""
    print("\n" + "=" * 70)
    print("PHASE 4: TRADING SIMULATION")
    print("=" * 70)

    from experiment1.trading_simulation import (
        temporal_split_prices,
        run_portfolio_simulation,
    )

    # Temporal split
    train_prices, test_prices = temporal_split_prices(hourly_prices, train_frac=0.75)
    print(f"  Train: {len(train_prices)} markets, Test: {len(test_prices)} markets")

    # Run simulation
    results = run_portfolio_simulation(
        test_prices, all_significant, llm_filtered,
        signal_threshold=0.05, hold_hours=24,
    )

    # Save results
    with open(os.path.join(DATA_DIR, "trading_results.json"), "w") as f:
        json.dump(results, f, indent=2, default=str)

    return results


def generate_results_summary(
    market_df, all_granger, significant, llm_filtered, trading_results
):
    """Generate results_summary.md with all findings."""
    print("\n" + "=" * 70)
    print("GENERATING RESULTS SUMMARY")
    print("=" * 70)

    n_markets = len(market_df)
    n_domains = market_df["domain"].nunique()
    n_tests = len(all_granger)
    n_significant = len(significant)
    n_llm_approved = llm_filtered["llm_approved"].sum() if "llm_approved" in llm_filtered.columns else 0

    # Domain pair breakdown
    if not significant.empty:
        domain_pairs = significant.groupby(["leader_domain", "follower_domain"]).size()
        domain_pair_str = domain_pairs.to_string()
    else:
        domain_pair_str = "No significant pairs found"

    # Trading metrics
    def _fmt_metrics(m):
        return f"Trades={m['n_trades']}, PnL={m['total_pnl']:.4f}, Sharpe={m['sharpe_ratio']:.2f}, WinRate={m['win_rate']:.1%}"

    pa = trading_results.get("portfolio_a_all_granger", {}).get("metrics", {})
    pb = trading_results.get("portfolio_b_llm_filtered", {}).get("metrics", {})
    pc = trading_results.get("portfolio_c_random", {}).get("metrics", {})

    summary = f"""# Experiment 1: Results Summary
## Cross-Market Causal Lead-Lag Discovery

**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

---

## Dataset
- **Total markets analyzed:** {n_markets}
- **Domains:** {n_domains}
- **Domain distribution:** {market_df['domain'].value_counts().head(10).to_dict()}

---

## Stage 1: Statistical Signal Discovery (Granger Causality)
- **Total directional tests:** {n_tests}
- **Significant after Bonferroni (α=0.01):** {n_significant}
- **Spurious pair rate:** {(1 - n_significant / max(n_tests, 1)) * 100:.1f}%

### Domain Pair Breakdown
```
{domain_pair_str}
```

---

## Stage 2: LLM Semantic Filtering
- **Pairs assessed:** {len(llm_filtered)}
- **LLM-approved (score ≥ 4):** {n_llm_approved}
- **Rejection rate:** {(1 - n_llm_approved / max(len(llm_filtered), 1)) * 100:.1f}%

---

## Stage 3: Trading Simulation

| Portfolio | Description | {_fmt_metrics.__doc__ or 'Metrics'} |
|-----------|-------------|---------|
| **A (All Granger)** | No LLM filtering | {_fmt_metrics(pa) if pa else 'N/A'} |
| **B (LLM-filtered)** | Score ≥ 4 only | {_fmt_metrics(pb) if pb else 'N/A'} |
| **C (Random)** | Control | {_fmt_metrics(pc) if pc else 'N/A'} |

### Key Metrics
- **Sharpe (filtered vs unfiltered):** {pb.get('sharpe_ratio', 0):.2f} vs {pa.get('sharpe_ratio', 0):.2f}
- **Win rate (filtered):** {pb.get('win_rate', 0):.1%}
- **Precision improvement:** {'Yes' if pb.get('win_rate', 0) > pa.get('win_rate', 0) else 'No'}

---

## Success Metrics Assessment
| Metric | Threshold | Result | Status |
|--------|-----------|--------|--------|
| Sharpe (LLM-filtered) | > 0.5 | {pb.get('sharpe_ratio', 0):.2f} | {'PASS' if pb.get('sharpe_ratio', 0) > 0.5 else 'CHECK'} |
| Sharpe improvement | > 30% | {((pb.get('sharpe_ratio', 0) - pa.get('sharpe_ratio', 0)) / max(abs(pa.get('sharpe_ratio', 0.01)), 0.01) * 100):.1f}% | {'PASS' if pb.get('sharpe_ratio', 0) > pa.get('sharpe_ratio', 0) * 1.3 else 'CHECK'} |
| LLM filter precision | > 60% | {pb.get('win_rate', 0):.1%} | {'PASS' if pb.get('win_rate', 0) > 0.6 else 'CHECK'} |
| Spurious elimination | > 50% | {(1 - n_llm_approved / max(len(llm_filtered), 1)) * 100:.1f}% | {'PASS' if n_llm_approved < len(llm_filtered) * 0.5 else 'CHECK'} |
| Cross-domain discoveries | ≥ 3 | {n_llm_approved} approved pairs | {'PASS' if n_llm_approved >= 3 else 'CHECK'} |

---

## Deliverables
- [x] Granger causality results (data/exp1/granger_results.csv)
- [x] Significant pairs (data/exp1/granger_significant.csv)
- [x] LLM assessments (data/exp1/llm_assessments.json)
- [x] Trading simulation (data/exp1/trading_results.json)
- [x] Results summary (data/exp1/results_summary.md)
"""

    output_path = os.path.join(DATA_DIR, "results_summary.md")
    with open(output_path, "w") as f:
        f.write(summary)
    print(f"  Saved results summary to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Experiment 1: Cross-Market Causal Lead-Lag Discovery")
    parser.add_argument("--quick-test", action="store_true", help="Run on small subset")
    parser.add_argument("--max-markets", type=int, default=None, help="Max markets to fetch")
    parser.add_argument("--skip-fetch", action="store_true", help="Use cached market/price data")
    parser.add_argument("--skip-granger", action="store_true", help="Use cached Granger results")
    parser.add_argument("--skip-llm", action="store_true", help="Use cached LLM assessments")
    parser.add_argument("--skip-trading", action="store_true", help="Skip trading simulation")
    args = parser.parse_args()

    os.makedirs(DATA_DIR, exist_ok=True)

    start_time = datetime.now()
    print(f"Experiment 1 started at {start_time.strftime('%H:%M:%S')}")

    if args.quick_test:
        args.max_markets = args.max_markets or 500

    # Phase 1: Data Collection
    markets_path = os.path.join(DATA_DIR, "markets.csv")
    pairs_path = os.path.join(DATA_DIR, "concurrent_pairs.json")
    prices_path = os.path.join(DATA_DIR, "hourly_prices.json")

    if args.skip_fetch and os.path.exists(markets_path) and os.path.exists(pairs_path):
        print(f"\nLoading cached data...")
        market_df = pd.read_csv(markets_path)
        with open(pairs_path) as f:
            pairs = json.load(f)
        # Load hourly prices
        from experiment1.data_collection import fetch_hourly_prices
        hourly_prices = {}
        if os.path.exists(prices_path):
            with open(prices_path) as f:
                raw = json.load(f)
            for ticker, entries in raw.items():
                timestamps = [e[0] for e in entries]
                prices = [e[1] for e in entries]
                idx = pd.to_datetime(timestamps, unit="s", utc=True)
                hourly_prices[ticker] = pd.Series(prices, index=idx, name=ticker, dtype=float)
            print(f"  Loaded {len(hourly_prices)} market price series")
    else:
        market_df, pairs, hourly_prices = phase1_data_collection(
            quick_test=args.quick_test,
            max_markets=args.max_markets,
        )

    # Phase 2: Granger Causality
    granger_path = os.path.join(DATA_DIR, "granger_significant.csv")
    all_granger_path = os.path.join(DATA_DIR, "granger_results.csv")

    if args.skip_granger and os.path.exists(granger_path):
        print(f"\nLoading cached Granger results...")
        significant = pd.read_csv(granger_path)
        all_granger = pd.read_csv(all_granger_path) if os.path.exists(all_granger_path) else significant
    else:
        all_granger, significant = phase2_granger(hourly_prices, pairs, market_df)

    # Phase 3: LLM Filtering
    llm_path = os.path.join(DATA_DIR, "llm_filtered_pairs.csv")

    if args.skip_llm and os.path.exists(llm_path):
        print(f"\nLoading cached LLM assessments...")
        llm_filtered = pd.read_csv(llm_path)
    elif significant.empty:
        print("\nNo significant pairs to filter.")
        llm_filtered = significant.copy()
    else:
        # Assess all significant pairs (caching means only uncached pairs hit the API)
        print(f"\n  LLM filtering all {len(significant)} significant pairs")
        llm_filtered = phase3_llm_filtering(significant, market_df)

    # Phase 4: Trading Simulation
    if args.skip_trading:
        print("\nSkipping trading simulation.")
        trading_results = {}
    else:
        trading_results = phase4_trading_simulation(
            hourly_prices, significant, llm_filtered
        )

    # Results Summary
    generate_results_summary(market_df, all_granger, significant, llm_filtered, trading_results)

    elapsed = datetime.now() - start_time
    print(f"\n{'=' * 70}")
    print(f"EXPERIMENT 1 COMPLETE ({elapsed.total_seconds():.0f}s)")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
