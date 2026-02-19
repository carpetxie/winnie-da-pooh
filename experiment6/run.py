"""
experiment6/run.py

Experiment 6: Market Microstructure Analysis.

Extracts bid-ask spread, open interest, OHLC range, and volume from
cached hourly candles. Tests whether microstructure signals predict
calibration quality and respond to economic events.

No API calls required. Uses cached data from experiment2.

Usage:
    uv run python -m experiment6.run
"""

import os
import json
import numpy as np
import pandas as pd
from datetime import datetime

DATA_DIR = "data/exp6"


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "plots"), exist_ok=True)

    start_time = datetime.now()
    print(f"Experiment 6 started at {start_time.strftime('%H:%M:%S')}")

    from experiment6.microstructure import (
        load_all_candles,
        build_microstructure_panel,
        analyze_spread_as_uncertainty,
        analyze_oi_dynamics,
        analyze_event_microstructure,
        analyze_spread_vs_kui,
        plot_microstructure,
    )
    from experiment2.event_study import get_economic_events

    # Phase 1: Load candles
    print("\n" + "=" * 70)
    print("PHASE 1: LOADING HOURLY CANDLE DATA")
    print("=" * 70)

    all_candles = load_all_candles()
    print(f"  Loaded candles for {len(all_candles)} markets")

    markets_df = pd.read_csv("data/exp2/markets.csv")
    print(f"  Market metadata: {len(markets_df)} markets")

    # Phase 2: Extract microstructure
    print("\n" + "=" * 70)
    print("PHASE 2: EXTRACTING MICROSTRUCTURE FEATURES")
    print("=" * 70)

    ticker_dfs, summary_df = build_microstructure_panel(all_candles, markets_df)
    print(f"  Extracted features for {len(ticker_dfs)} markets")

    summary_df.to_csv(os.path.join(DATA_DIR, "microstructure_summary.csv"), index=False)

    # Stats
    econ_domains = {"inflation", "monetary_policy", "labor_market", "fiscal_policy"}
    econ = summary_df[summary_df["domain"].isin(econ_domains)]
    print(f"\n  Economics markets: {len(econ)}")
    print(f"  Mean spread: ${econ['mean_spread'].mean():.4f}")
    print(f"  Mean peak OI: {econ['max_oi'].mean():.0f}")
    print(f"  Mean intraday range: ${econ['mean_range'].mean():.4f}")

    for domain in sorted(econ_domains):
        subset = econ[econ["domain"] == domain]
        if len(subset) > 0:
            print(f"    {domain}: n={len(subset)}, "
                  f"spread=${subset['mean_spread'].mean():.4f}, "
                  f"OI={subset['max_oi'].mean():.0f}, "
                  f"range=${subset['mean_range'].mean():.4f}")

    # Phase 3: Spread as uncertainty measure
    print("\n" + "=" * 70)
    print("PHASE 3: BID-ASK SPREAD AS DISAGREEMENT MEASURE")
    print("=" * 70)

    spread_results = analyze_spread_as_uncertainty(ticker_dfs, markets_df)
    print(f"  Markets analyzed: {spread_results.get('n_markets', 0)}")

    if "spread_brier_correlation" in spread_results:
        corr = spread_results["spread_brier_correlation"]
        print(f"  Spread-Brier correlation: r={corr['spearman_r']:.3f}, p={corr['p_value']:.4f}")
        print(f"  Significant: {corr['significant']}")

    if "spread_tercile_calibration" in spread_results:
        print("\n  Calibration by spread tercile:")
        for tercile, stats in sorted(spread_results["spread_tercile_calibration"].items()):
            print(f"    {tercile}: Brier={stats['mean_brier']:.3f}, "
                  f"spread=${stats['mean_spread']:.4f}, n={stats['n']}")

    # Phase 4: Open interest dynamics
    print("\n" + "=" * 70)
    print("PHASE 4: OPEN INTEREST DYNAMICS")
    print("=" * 70)

    oi_results = analyze_oi_dynamics(ticker_dfs, markets_df)
    print(f"  Markets analyzed: {oi_results.get('n_markets', 0)}")

    if "peak_oi_brier_correlation" in oi_results:
        corr = oi_results["peak_oi_brier_correlation"]
        print(f"  Peak OI-Brier correlation: r={corr['spearman_r']:.3f}, p={corr['p_value']:.4f}")
        print(f"  Significant: {corr['significant']}")

    if "oi_convergence_test" in oi_results and oi_results["oi_convergence_test"]:
        ct = oi_results["oi_convergence_test"]
        print(f"\n  OI acceleration → price convergence:")
        print(f"    Accelerating OI: {ct['oi_accelerating_convergence_rate']:.1%} converge (n={ct['n_accelerating']})")
        print(f"    Decelerating OI: {ct['oi_decelerating_convergence_rate']:.1%} converge (n={ct['n_decelerating']})")
        print(f"    Fisher exact p={ct['fisher_exact_p']:.4f}")

    if "oi_tercile_calibration" in oi_results:
        print("\n  Calibration by OI tercile:")
        for tercile, stats in sorted(oi_results["oi_tercile_calibration"].items()):
            print(f"    {tercile}: Brier={stats['mean_brier']:.3f}, "
                  f"peak_OI={stats['mean_peak_oi']:.0f}, n={stats['n']}")

    # Phase 5: Event microstructure
    print("\n" + "=" * 70)
    print("PHASE 5: MICROSTRUCTURE AROUND ECONOMIC EVENTS")
    print("=" * 70)

    events = get_economic_events()
    event_results = analyze_event_microstructure(ticker_dfs, markets_df, events)
    print(f"  Event-market pairs: {event_results.get('n_event_market_pairs', 0)}")

    if "spread_change" in event_results:
        sc = event_results["spread_change"]
        print(f"  Spread change: {sc['direction']} ({sc['change_pct']:.1f}%)")
        print(f"    Pre: ${sc['pre_mean']:.4f} → Post: ${sc['post_mean']:.4f}")
        print(f"    Wilcoxon p={sc['wilcoxon_p']:.4f}, significant={sc['significant']}")

    if "range_change" in event_results:
        rc = event_results["range_change"]
        print(f"  Range change: {rc['direction']} ({rc['change_pct']:.1f}%)")
        print(f"    Pre: ${rc['pre_mean']:.4f} → Post: ${rc['post_mean']:.4f}")
        print(f"    Wilcoxon p={rc['wilcoxon_p']:.4f}, significant={rc['significant']}")

    # Phase 6: Spread vs KUI correlation
    print("\n" + "=" * 70)
    print("PHASE 6: SPREAD INDEX vs KUI CORRELATION")
    print("=" * 70)

    kui_results = analyze_spread_vs_kui(ticker_dfs, markets_df)
    if "error" not in kui_results:
        print(f"  Overlapping days: {kui_results['n_days']}")
        print(f"  Pearson r={kui_results['pearson_r']:.3f}, p={kui_results['pearson_p']:.4f}")
        print(f"  Spearman r={kui_results['spearman_r']:.3f}, p={kui_results['spearman_p']:.4f}")
        print(f"  Mean active markets/day: {kui_results['mean_active_markets']:.1f}")
    else:
        print(f"  Error: {kui_results['error']}")

    # Phase 7: Plots
    print("\n" + "=" * 70)
    print("PHASE 7: VISUALIZATION")
    print("=" * 70)

    plot_microstructure(ticker_dfs, summary_df, os.path.join(DATA_DIR, "plots"))

    # Save all results
    all_results = {
        "spread_analysis": spread_results,
        "oi_analysis": oi_results,
        "event_microstructure": event_results,
        "spread_vs_kui": kui_results,
    }

    with open(os.path.join(DATA_DIR, "microstructure_results.json"), "w") as f:
        json.dump(all_results, f, indent=2, default=str)

    elapsed = datetime.now() - start_time
    print(f"\n{'=' * 70}")
    print(f"EXPERIMENT 6 COMPLETE ({elapsed.total_seconds():.0f}s)")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
