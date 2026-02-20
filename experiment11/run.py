"""
experiment11/run.py

Experiment 11: Favorite-Longshot Bias × Microstructure.

Tests whether the favorite-longshot bias (Whelan, CEPR 2024) disappears
in markets with higher OI, tighter spreads, and more volume.

No API calls required. Uses cached data from experiment2.

Usage:
    uv run python -m experiment11.run
"""

import os
import json
import numpy as np
import pandas as pd
from datetime import datetime

DATA_DIR = "data/exp11"


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "plots"), exist_ok=True)

    start_time = datetime.now()
    print(f"Experiment 11 started at {start_time.strftime('%H:%M:%S')}")

    from experiment11.favorite_longshot import (
        load_settled_markets,
        load_microstructure_from_candles,
        filter_economics_markets,
        extract_t_minus_prices,
        analyze_favorite_longshot_bias,
        analyze_bias_by_microstructure,
        analyze_bias_by_time_to_expiration,
        analyze_bias_by_domain,
        plot_favorite_longshot,
    )

    # Phase 1: Load settled markets and filter to economics
    print("\n" + "=" * 70)
    print("PHASE 1: LOADING SETTLED MARKETS (ECONOMICS ONLY)")
    print("=" * 70)

    all_markets = load_settled_markets()
    print(f"  All settled markets: {len(all_markets)}")

    markets = filter_economics_markets(all_markets)
    print(f"  Economics-only markets: {len(markets)}")
    print(f"  YES outcomes: {(markets['realized'] == 1).sum()} ({(markets['realized'] == 1).mean():.1%})")
    print(f"  NO outcomes: {(markets['realized'] == 0).sum()} ({(markets['realized'] == 0).mean():.1%})")
    print(f"  Mean implied probability: {markets['implied_prob'].mean():.3f}")
    print(f"  Mean open interest: {markets['open_interest'].mean():.0f}")
    print(f"  Mean volume: {markets['volume'].mean():.0f}")

    # Phase 1b: Extract T-24h prices
    print("\n  Extracting T-24h prices from candle data...")
    markets = extract_t_minus_prices(markets)
    n_candle = markets["has_candle_price"].sum()
    print(f"  Markets with T-24h candle price: {n_candle} ({n_candle/len(markets):.1%})")
    if n_candle > 0:
        candle_markets = markets[markets["has_candle_price"]]
        print(f"  T-24h mean implied prob: {candle_markets['implied_prob'].mean():.3f}")
        print(f"  T-24h mean spread: ${candle_markets['t_minus_spread'].mean():.4f}")

    # Phase 2: Load microstructure from candles
    print("\n" + "=" * 70)
    print("PHASE 2: LOADING HOURLY MICROSTRUCTURE DATA")
    print("=" * 70)

    micro = load_microstructure_from_candles()
    print(f"  Markets with candle data: {len(micro)}")
    print(f"  Mean spread: ${micro['mean_spread'].mean():.4f}")
    print(f"  Mean peak OI: {micro['peak_oi'].mean():.0f}")

    # Phase 3: Overall favorite-longshot bias
    print("\n" + "=" * 70)
    print("PHASE 3: OVERALL FAVORITE-LONGSHOT BIAS TEST")
    print("=" * 70)

    bias_result = analyze_favorite_longshot_bias(markets)
    print(f"  Overall Brier score: {bias_result.get('overall_brier', 'N/A'):.4f}")

    if "longshot" in bias_result:
        ls = bias_result["longshot"]
        print(f"\n  Longshots (p < 0.30):")
        print(f"    Mean implied: {ls['mean_implied']:.3f}")
        print(f"    Mean actual:  {ls['mean_actual']:.3f}")
        print(f"    Bias:         {ls['bias']:+.3f} ({'OVERPRICED' if ls['bias'] > 0 else 'underpriced'})")
        print(f"    Binomial p:   {ls['binomial_p']:.4f}")
        print(f"    n = {ls['n']}")

    if "favorite" in bias_result:
        fv = bias_result["favorite"]
        print(f"\n  Favorites (p > 0.70):")
        print(f"    Mean implied: {fv['mean_implied']:.3f}")
        print(f"    Mean actual:  {fv['mean_actual']:.3f}")
        print(f"    Bias:         {fv['bias']:+.3f} ({'overpriced' if fv['bias'] > 0 else 'UNDERPRICED'})")
        print(f"    Binomial p:   {fv['binomial_p']:.4f}")
        print(f"    n = {fv['n']}")

    # Phase 4: Bias by microstructure
    print("\n" + "=" * 70)
    print("PHASE 4: BIAS × MICROSTRUCTURE (OI, SPREAD, VOLUME)")
    print("=" * 70)

    micro_result = analyze_bias_by_microstructure(markets, micro)

    for metric in ["open_interest", "spread", "volume"]:
        if metric not in micro_result:
            continue

        print(f"\n  By {metric}:")
        for tercile in ["low", "medium", "high"]:
            t = micro_result[metric]["terciles"].get(tercile, {})
            if not t:
                continue
            lb = f"{t['longshot_bias']:+.3f}" if t.get("longshot_bias") is not None else "N/A"
            print(f"    {tercile}: Brier={t['brier']:.4f}, "
                  f"longshot_bias={lb}, n={t['n']}")

        comp = micro_result[metric].get("comparison", {})
        if comp:
            print(f"    Low vs High Brier: {comp.get('low_brier', 'N/A'):.4f} vs "
                  f"{comp.get('high_brier', 'N/A'):.4f}")
            print(f"    Mann-Whitney p={comp.get('p_value', 'N/A'):.4f}, "
                  f"significant={comp.get('significant', 'N/A')}")

    # Phase 5: Bias by time to expiration
    print("\n" + "=" * 70)
    print("PHASE 5: BIAS × TIME TO EXPIRATION")
    print("=" * 70)

    time_result = analyze_bias_by_time_to_expiration(markets)
    if "error" not in time_result:
        for tercile in ["short", "medium", "long"]:
            t = time_result.get(tercile, {})
            if not t:
                continue
            lb = f"{t['longshot_bias']:+.3f}" if t.get("longshot_bias") is not None else "N/A"
            print(f"  {tercile} lifetime ({t['mean_lifetime_hours']:.0f}h): "
                  f"Brier={t['brier']:.4f}, longshot_bias={lb}, n={t['n']}")
    else:
        print(f"  Error: {time_result['error']}")

    # Phase 6: Bias by domain
    print("\n" + "=" * 70)
    print("PHASE 6: BIAS × MARKET DOMAIN")
    print("=" * 70)

    domain_result = analyze_bias_by_domain(markets)
    for domain, vals in sorted(domain_result.items(), key=lambda x: x[1].get("n", 0), reverse=True):
        lb = f"{vals['longshot_bias']:+.3f}" if vals.get("longshot_bias") is not None else "N/A"
        fb = f"{vals['favorite_bias']:+.3f}" if vals.get("favorite_bias") is not None else "N/A"
        print(f"  {domain}: n={vals['n']}, Brier={vals['brier']:.4f}, "
              f"longshot_bias={lb}, favorite_bias={fb}")

    # Phase 7: Visualization
    print("\n" + "=" * 70)
    print("PHASE 7: VISUALIZATION")
    print("=" * 70)

    plot_favorite_longshot(markets, micro_result, os.path.join(DATA_DIR, "plots"))

    # Save results
    all_results = {
        "n_markets": len(markets),
        "overall_bias": bias_result,
        "microstructure_bias": micro_result,
        "time_to_expiration_bias": time_result,
        "domain_bias": domain_result,
    }

    with open(os.path.join(DATA_DIR, "favorite_longshot_results.json"), "w") as f:
        json.dump(all_results, f, indent=2, default=str)

    elapsed = datetime.now() - start_time
    print(f"\n{'=' * 70}")
    print(f"EXPERIMENT 11 COMPLETE ({elapsed.total_seconds():.0f}s)")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
