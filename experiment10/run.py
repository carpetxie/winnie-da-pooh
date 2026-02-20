"""
experiment10/run.py

Experiment 10: Cross-Event Shock Propagation Heatmap.

Tracks how economic event shocks (CPI, FOMC, NFP, GDP) ripple across
domains (inflation, monetary_policy, labor, macro) hour-by-hour.

No API calls required. Uses cached hourly candle data from experiment2.

Usage:
    uv run python -m experiment10.run
"""

import os
import json
import numpy as np
import pandas as pd
from datetime import datetime

DATA_DIR = "data/exp10"


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "plots"), exist_ok=True)

    start_time = datetime.now()
    print(f"Experiment 10 started at {start_time.strftime('%H:%M:%S')}")

    from experiment10.shock_propagation import (
        load_hourly_series,
        compute_event_responses,
        build_propagation_heatmap,
        analyze_surprise_vs_nonsurprise,
        analyze_cross_domain_contagion,
        build_temporal_cascade_matrix,
        plot_propagation_heatmap,
    )
    from experiment2.event_study import get_economic_events

    # Phase 1: Load hourly series
    print("\n" + "=" * 70)
    print("PHASE 1: LOADING HOURLY CANDLE DATA")
    print("=" * 70)

    ticker_series = load_hourly_series()
    print(f"  Loaded {len(ticker_series)} economic market series")

    # Domain breakdown
    from experiment10.shock_propagation import _ticker_to_domain, ECON_DOMAINS
    domain_counts = {}
    for ticker in ticker_series:
        d = _ticker_to_domain(ticker)
        domain_counts[d] = domain_counts.get(d, 0) + 1
    for d in ECON_DOMAINS:
        print(f"    {d}: {domain_counts.get(d, 0)} markets")

    # Phase 2: Compute event responses
    print("\n" + "=" * 70)
    print("PHASE 2: COMPUTING EVENT RESPONSES (-24h to +48h)")
    print("=" * 70)

    events = get_economic_events()
    print(f"  {len(events)} economic events in calendar")
    print(f"  Surprise events: {events['surprise'].sum()}")

    responses = compute_event_responses(ticker_series, events)
    print(f"  Total event-ticker-hour observations: {len(responses):,}")
    print(f"  Unique event-ticker pairs: {responses.groupby(['event_date', 'ticker']).ngroups:,}")

    # Phase 3: Build propagation heatmap
    print("\n" + "=" * 70)
    print("PHASE 3: BUILDING SHOCK PROPAGATION HEATMAP")
    print("=" * 70)

    heatmap_result = build_propagation_heatmap(responses)

    print("\n  First significant response (hours after event):")
    for event_type, fr in sorted(heatmap_result["first_significant_response"].items()):
        origin = {"CPI": "inflation", "FOMC": "monetary_policy",
                  "NFP": "labor", "GDP": "macro"}.get(event_type, "?")
        domains_str = ", ".join(f"{d}={h}h" for d, h in sorted(fr.items(), key=lambda x: x[1]))
        print(f"    {event_type} (origin: {origin}): {domains_str}")

    if heatmap_result["propagation_speeds"]:
        print("\n  Propagation delays (from origin domain):")
        for p in sorted(heatmap_result["propagation_speeds"],
                       key=lambda x: x["propagation_delay"]):
            print(f"    {p['event_type']}: {p['source']} → {p['target']}: "
                  f"+{p['propagation_delay']}h "
                  f"(origin at {p['source_lag_hours']}h, target at {p['target_lag_hours']}h)")

    # Phase 4: Surprise vs non-surprise
    print("\n" + "=" * 70)
    print("PHASE 4: SURPRISE vs NON-SURPRISE RESPONSE MAGNITUDE")
    print("=" * 70)

    surprise_results = analyze_surprise_vs_nonsurprise(responses)
    for domain, stats_dict in sorted(surprise_results.items()):
        ratio_str = f"{stats_dict['ratio']:.2f}x" if stats_dict['ratio'] else "N/A"
        sig = "*" if stats_dict["significant"] else ""
        print(f"  {domain}: surprise={stats_dict['surprise_mean']:.4f}, "
              f"non-surprise={stats_dict['nonsurprise_mean']:.4f}, "
              f"ratio={ratio_str}, p={stats_dict['p_value']:.4f}{sig}")

    # Phase 5: Cross-domain contagion
    print("\n" + "=" * 70)
    print("PHASE 5: CROSS-DOMAIN CONTAGION ANALYSIS")
    print("=" * 70)

    contagion = analyze_cross_domain_contagion(responses)
    if "contagion_summary" in contagion:
        print(f"  Total contagion pairs: {contagion['n_total_pairs']}")
        for event_type, targets in sorted(contagion["contagion_summary"].items()):
            print(f"\n  {event_type} →")
            for target, vals in sorted(targets.items()):
                print(f"    {target}: mean ratio={vals['mean_contagion_ratio']:.3f}, "
                      f"n={vals['n_events']}")

        if contagion.get("surprise_contagion_test"):
            st = contagion["surprise_contagion_test"]
            print(f"\n  Surprise events → higher contagion?")
            print(f"    Surprise mean: {st['surprise_mean_contagion']:.3f}")
            print(f"    Non-surprise mean: {st['nonsurprise_mean_contagion']:.3f}")
            print(f"    Mann-Whitney p={st['mann_whitney_p']:.4f}, "
                  f"significant={st['significant']}")

    # Phase 6: Build temporal cascade matrix
    print("\n" + "=" * 70)
    print("PHASE 6: BUILDING TEMPORAL CASCADE MATRIX")
    print("=" * 70)

    matrices = build_temporal_cascade_matrix(responses)
    for event_type, matrix in sorted(matrices.items()):
        domains = list(matrix.keys())
        hours = set()
        for d in domains:
            hours.update(matrix[d].keys())
        print(f"  {event_type}: {len(domains)} domains × {len(hours)} hours")

    # Phase 7: Visualization
    print("\n" + "=" * 70)
    print("PHASE 7: VISUALIZATION")
    print("=" * 70)

    plot_propagation_heatmap(
        matrices,
        heatmap_result["first_significant_response"],
        os.path.join(DATA_DIR, "plots"),
    )

    # Save results
    results = {
        "n_markets": len(ticker_series),
        "n_events": len(events),
        "n_observations": len(responses),
        "domain_counts": domain_counts,
        "first_significant_response": heatmap_result["first_significant_response"],
        "propagation_speeds": heatmap_result["propagation_speeds"],
        "surprise_analysis": surprise_results,
        "contagion_analysis": {
            k: v for k, v in contagion.items() if k != "raw_scores"
        },
    }

    with open(os.path.join(DATA_DIR, "shock_propagation_results.json"), "w") as f:
        json.dump(results, f, indent=2, default=str)

    # Save response data for potential further analysis
    responses.to_csv(os.path.join(DATA_DIR, "event_responses.csv"), index=False)

    elapsed = datetime.now() - start_time
    print(f"\n{'=' * 70}")
    print(f"EXPERIMENT 10 COMPLETE ({elapsed.total_seconds():.0f}s)")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
