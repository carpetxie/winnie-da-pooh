"""
experiment7/run.py

Experiment 7: Implied Probability Distributions & No-Arbitrage.

Reconstructs implied probability distributions from Kalshi's multi-strike
market structure. Tests monotonicity (no-arbitrage) constraints and measures
distribution forecasting accuracy.

No API calls required. Uses cached data from experiment2.

Usage:
    uv run python -m experiment7.run
"""

import os
import json
import numpy as np
import pandas as pd
from datetime import datetime

DATA_DIR = "data/exp7"


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "plots"), exist_ok=True)

    start_time = datetime.now()
    print(f"Experiment 7 started at {start_time.strftime('%H:%M:%S')}")

    from experiment7.implied_distributions import (
        load_targeted_markets,
        extract_strike_markets,
        group_by_event,
        analyze_no_arbitrage,
        build_distribution_snapshots,
        plot_implied_distributions,
    )

    # Phase 1: Load and classify strike markets
    print("\n" + "=" * 70)
    print("PHASE 1: LOADING MULTI-STRIKE MARKETS")
    print("=" * 70)

    all_markets = load_targeted_markets()
    print(f"  Total markets in cache: {len(all_markets)}")

    strike_markets = extract_strike_markets(all_markets)
    print(f"  Multi-strike markets: {len(strike_markets)}")

    for series in sorted(strike_markets["series_prefix"].unique()):
        subset = strike_markets[strike_markets["series_prefix"] == series]
        events = subset["event_ticker"].nunique()
        strikes = subset["floor_strike"].nunique()
        print(f"    {series}: {len(subset)} markets, {events} events, {strikes} unique strikes")

    strike_markets.to_csv(os.path.join(DATA_DIR, "strike_markets.csv"), index=False)

    # Phase 2: Group by event
    print("\n" + "=" * 70)
    print("PHASE 2: GROUPING BY EVENT")
    print("=" * 70)

    event_groups = group_by_event(strike_markets)
    print(f"  Events with >= 2 strikes: {len(event_groups)}")

    for event, group in sorted(event_groups.items()):
        strikes = sorted(group["floor_strike"].unique())
        print(f"    {event}: strikes = {strikes}")

    # Phase 3: No-arbitrage analysis
    print("\n" + "=" * 70)
    print("PHASE 3: NO-ARBITRAGE MONOTONICITY TESTS")
    print("=" * 70)

    arb_results = analyze_no_arbitrage(event_groups)
    print(f"  Events analyzed: {arb_results['events_analyzed']}")
    print(f"  Total hourly snapshots: {arb_results['total_snapshots']}")
    print(f"  Violating snapshots: {arb_results['violating_snapshots']}")
    print(f"  Violation rate: {arb_results['overall_violation_rate']:.1%}")
    print(f"  Mean violation size: ${arb_results['mean_violation_size']:.4f}")
    print(f"  Total violations: {arb_results['total_violations']}")

    if arb_results["reversion"]:
        rev = arb_results["reversion"]
        if rev.get("reversion_rate") is not None:
            print(f"\n  Violation reversion:")
            print(f"    Checked: {rev['n_violations_checked']}")
            print(f"    Reverted: {rev['n_reverted']} ({rev['reversion_rate']:.1%})")
            print(f"    Persisted: {rev['n_persisted']}")

    # Per-event breakdown
    print("\n  Per-event violation rates:")
    for event, stats in sorted(arb_results["per_event"].items()):
        if stats["n_violating"] > 0:
            print(f"    {event}: {stats['violation_rate']:.1%} "
                  f"({stats['n_violating']}/{stats['n_snapshots']}), "
                  f"max=${stats['max_violation_size']:.4f}")

    # Phase 4: Implied distributions
    print("\n" + "=" * 70)
    print("PHASE 4: IMPLIED PROBABILITY DISTRIBUTIONS")
    print("=" * 70)

    dist_results = build_distribution_snapshots(event_groups)
    print(f"  Events with distributions: {len(dist_results)}")

    for event, data in sorted(dist_results.items()):
        implied = data.get("implied_mean")
        realized = data.get("realized_value")
        error = data.get("forecast_error")
        print(f"    {event}: implied_mean={implied:.3f}" if implied else f"    {event}: no implied mean", end="")
        if realized is not None:
            print(f", realized={realized:.3f}", end="")
        if error is not None:
            print(f", error={error:.3f}", end="")
        print()

    # Aggregate accuracy
    errors = [v["forecast_error"] for v in dist_results.values()
              if v.get("forecast_error") is not None]
    if errors:
        print(f"\n  Forecast accuracy:")
        print(f"    Mean absolute error: {np.mean(errors):.4f}")
        print(f"    Median absolute error: {np.median(errors):.4f}")
        print(f"    RMSE: {np.sqrt(np.mean(np.array(errors)**2)):.4f}")

    # Phase 5: Plots
    print("\n" + "=" * 70)
    print("PHASE 5: VISUALIZATION")
    print("=" * 70)

    plot_implied_distributions(dist_results, os.path.join(DATA_DIR, "plots"))

    # Save results
    # Serialize — convert timestamps for JSON
    serializable_arb = _make_serializable(arb_results)
    serializable_dist = _make_serializable(dist_results)

    all_results = {
        "no_arbitrage": serializable_arb,
        "distributions": serializable_dist,
        "summary": {
            "n_strike_markets": len(strike_markets),
            "n_events": len(event_groups),
            "violation_rate": arb_results["overall_violation_rate"],
            "mean_forecast_error": float(np.mean(errors)) if errors else None,
        },
    }

    with open(os.path.join(DATA_DIR, "implied_distribution_results.json"), "w") as f:
        json.dump(all_results, f, indent=2, default=str)

    elapsed = datetime.now() - start_time
    print(f"\n{'=' * 70}")
    print(f"EXPERIMENT 7 COMPLETE ({elapsed.total_seconds():.0f}s)")
    print(f"{'=' * 70}")


def _make_serializable(obj):
    """Recursively convert non-serializable types."""
    if isinstance(obj, dict):
        return {k: _make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_make_serializable(v) for v in obj]
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    elif isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    elif isinstance(obj, (np.ndarray,)):
        return obj.tolist()
    return obj


if __name__ == "__main__":
    main()
