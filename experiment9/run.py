"""
experiment9/run.py

Experiment 9: Indicator-Level Information Network.

Refines the domain-level lead-lag finding (inflation → monetary_policy)
to indicator-level granularity (CPI vs PCE vs PPI → Fed Funds).
Tests whether the market-implied information hierarchy matches the Fed's
stated policy framework.

No API calls required. Uses cached Granger results from experiment1.

Usage:
    uv run python -m experiment9.run
"""

import os
import json
import numpy as np
import pandas as pd
from datetime import datetime

DATA_DIR = "data/exp9"


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "plots"), exist_ok=True)

    start_time = datetime.now()
    print(f"Experiment 9 started at {start_time.strftime('%H:%M:%S')}")

    from experiment9.indicator_network import (
        load_granger_results,
        classify_indicators,
        build_indicator_network,
        analyze_inflation_to_fed,
        analyze_bidirectional_pairs,
        compute_indicator_centrality,
        test_lag_asymmetry,
        plot_indicator_network,
    )

    # Phase 1: Load and classify
    print("\n" + "=" * 70)
    print("PHASE 1: LOADING GRANGER RESULTS")
    print("=" * 70)

    granger_df = load_granger_results()
    print(f"  Significant Granger pairs: {len(granger_df)}")

    granger_df = classify_indicators(granger_df)

    # Indicator distribution
    print("\n  Leader indicator distribution:")
    for ind, count in granger_df["leader_indicator"].value_counts().items():
        print(f"    {ind}: {count}")

    print("\n  Follower indicator distribution:")
    for ind, count in granger_df["follower_indicator"].value_counts().items():
        print(f"    {ind}: {count}")

    granger_df.to_csv(os.path.join(DATA_DIR, "granger_with_indicators.csv"), index=False)

    # Phase 2: Build network
    print("\n" + "=" * 70)
    print("PHASE 2: INDICATOR-LEVEL NETWORK")
    print("=" * 70)

    graph = build_indicator_network(granger_df)
    print(f"  Network edges: {len(graph)}")

    print("\n  Top edges by pair count:")
    for edge in graph[:15]:
        print(f"    {edge['source']:20s} → {edge['target']:20s}: "
              f"{edge['n_pairs']} pairs, median lag={edge['median_lag']:.0f}h")

    # Phase 3: Inflation → Fed deep-dive
    print("\n" + "=" * 70)
    print("PHASE 3: INFLATION → MONETARY POLICY DEEP-DIVE")
    print("=" * 70)

    infl_fed = analyze_inflation_to_fed(granger_df)
    for key, data in sorted(infl_fed.items()):
        if key == "comparison":
            print(f"\n  Summary:")
            print(f"    CPI → Fed: {data['cpi_to_fed_pairs']} pairs")
            print(f"    PCE → Fed: {data['pce_to_fed_pairs']} pairs")
            print(f"    PPI → Fed: {data['ppi_to_fed_pairs']} pairs")
            print(f"    Dominant: {data['dominant_inflation_indicator']}")
            print(f"    Interpretation: {data['interpretation']}")
        else:
            print(f"    {key}: forward={data['forward_pairs']}, "
                  f"reverse={data['reverse_pairs']}, "
                  f"asymmetry={'→' if data['is_asymmetric'] else '←'}")
            if data["forward_median_lag"] is not None:
                print(f"      Forward median lag: {data['forward_median_lag']:.0f}h")

    # Phase 4: Bidirectional analysis
    print("\n" + "=" * 70)
    print("PHASE 4: BIDIRECTIONAL PAIR ANALYSIS")
    print("=" * 70)

    bidir = analyze_bidirectional_pairs(granger_df)
    print(f"  Total directed edges: {bidir['n_forward_edges']}")
    print(f"  Bidirectional pairs (co-movement): {bidir['n_bidirectional_pairs']}")
    print(f"  Unidirectional edges (true information flow): {bidir['n_unidirectional_edges']}")

    if bidir["bidirectional_pairs"]:
        print("\n  Bidirectional pairs:")
        for pair in bidir["bidirectional_pairs"][:10]:
            print(f"    {pair[0]} ↔ {pair[1]}")

    # Phase 5: Centrality
    print("\n" + "=" * 70)
    print("PHASE 5: INDICATOR CENTRALITY ANALYSIS")
    print("=" * 70)

    centrality = compute_indicator_centrality(graph)

    # Sort by influence ratio
    sorted_indicators = sorted(centrality.items(),
                               key=lambda x: x[1]["influence_ratio"], reverse=True)

    print(f"\n  {'Indicator':20s} {'Influence':>10s} {'Receptivity':>12s} {'Ratio':>8s} {'Domain'}")
    print("  " + "-" * 70)
    for ind, stats in sorted_indicators:
        print(f"  {ind:20s} {stats['influence']:10d} {stats['receptivity']:12d} "
              f"{stats['influence_ratio']:8.2f} {stats['domain']}")

    # Phase 6: Lag asymmetry tests
    print("\n" + "=" * 70)
    print("PHASE 6: LAG ASYMMETRY TESTS")
    print("=" * 70)

    lag_tests = test_lag_asymmetry(granger_df)
    for pair_name, result in sorted(lag_tests.items()):
        if "mann_whitney_p" in result:
            print(f"  {pair_name}:")
            print(f"    A→B median: {result['ab_median_lag']:.0f}h (n={result['ab_n']})")
            print(f"    B→A median: {result['ba_median_lag']:.0f}h (n={result['ba_n']})")
            print(f"    Mann-Whitney p={result['mann_whitney_p']:.4f}, "
                  f"sig={result['significant']}")
            print(f"    Faster: {result['faster_direction']}")
        else:
            print(f"  {pair_name}: {result.get('note', 'no data')}")

    # Phase 7: Plots
    print("\n" + "=" * 70)
    print("PHASE 7: VISUALIZATION")
    print("=" * 70)

    plot_indicator_network(graph, centrality, os.path.join(DATA_DIR, "plots"))

    # Save
    all_results = {
        "network": graph,
        "inflation_to_fed": infl_fed,
        "bidirectional": bidir,
        "centrality": centrality,
        "lag_asymmetry": lag_tests,
    }

    with open(os.path.join(DATA_DIR, "indicator_network_results.json"), "w") as f:
        json.dump(all_results, f, indent=2, default=str)

    elapsed = datetime.now() - start_time
    print(f"\n{'=' * 70}")
    print(f"EXPERIMENT 9 COMPLETE ({elapsed.total_seconds():.0f}s)")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
