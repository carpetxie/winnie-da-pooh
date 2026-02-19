"""
experiment4/run.py

Experiment 4: Hourly Information Speed Event Study.

Measures how quickly Kalshi markets absorb economic information compared
to traditional indicators (EPU, VIX) at daily resolution.

Uses cached hourly candle data — no API calls required.

Usage:
    uv run python -m experiment4.run
"""

import os
import json
import numpy as np
import pandas as pd
from datetime import datetime

DATA_DIR = "data/exp4"


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "plots"), exist_ok=True)

    start_time = datetime.now()
    print(f"Experiment 4 started at {start_time.strftime('%H:%M:%S')}")

    from experiment4.hourly_event_study import (
        load_hourly_prices_from_candles,
        compute_hourly_kui_domain,
        compute_hourly_event_windows,
        run_hourly_event_study,
        test_information_speed_significance,
        plot_event_windows,
    )
    from experiment2.event_study import get_economic_events

    # Load data
    print("\n" + "=" * 70)
    print("PHASE 1: LOADING HOURLY CANDLE DATA")
    print("=" * 70)

    markets_df = pd.read_csv("data/exp2/markets.csv")
    hourly_prices = load_hourly_prices_from_candles()
    print(f"  Loaded {len(hourly_prices)} market hourly series")

    # Domain counts
    ticker_to_domain = dict(zip(markets_df["ticker"], markets_df["domain"]))
    domain_counts = {}
    for t in hourly_prices:
        d = ticker_to_domain.get(t, "unknown")
        domain_counts[d] = domain_counts.get(d, 0) + 1
    print(f"  By domain: {domain_counts}")

    # Compute hourly BV
    print("\n" + "=" * 70)
    print("PHASE 2: COMPUTING HOURLY BELIEF VOLATILITY")
    print("=" * 70)

    hourly_bv = compute_hourly_kui_domain(hourly_prices, markets_df)
    for domain, bv in sorted(hourly_bv.items()):
        valid = bv.dropna()
        print(f"  {domain}: {len(valid)} hourly observations "
              f"({valid.index.min().strftime('%Y-%m-%d')} to {valid.index.max().strftime('%Y-%m-%d')})")

    # Load EPU/VIX
    print("\n  Loading EPU and VIX daily data...")
    epu_daily = pd.Series(dtype=float, name="EPU")
    vix_daily = pd.Series(dtype=float, name="VIX")

    epu_path = "data/exp2/epu_daily.csv"
    vix_path = "data/exp2/vix_daily.csv"

    if os.path.exists(epu_path):
        epu_df = pd.read_csv(epu_path)
        epu_df["date"] = pd.to_datetime(epu_df["date"])
        epu_daily = epu_df.set_index("date")["value"].dropna()
        epu_daily.name = "EPU"
        print(f"  EPU: {len(epu_daily)} days")

    if os.path.exists(vix_path):
        vix_df = pd.read_csv(vix_path)
        vix_df["date"] = pd.to_datetime(vix_df["date"])
        vix_daily = vix_df.set_index("date")["value"].dropna()
        vix_daily.name = "VIX"
        print(f"  VIX: {len(vix_daily)} days")

    # Run event study
    print("\n" + "=" * 70)
    print("PHASE 3: HOURLY EVENT STUDY")
    print("=" * 70)

    events = get_economic_events()
    print(f"  {len(events)} events defined")
    print(f"  Surprise events: {events['surprise'].sum()}")

    results = run_hourly_event_study(hourly_bv, epu_daily, vix_daily, events)
    print(f"\n  Events with hourly data: {len(results)}")

    if not results.empty:
        kalshi_reacted = results["kalshi_reaction_hours"].notna().sum()
        print(f"  Events where Kalshi reacted: {kalshi_reacted}")

        ll_epu = results["lead_lag_vs_epu_hours"].dropna()
        if len(ll_epu) > 0:
            print(f"\n  Lead-lag vs EPU (hours):")
            print(f"    Mean: {ll_epu.mean():.1f}h")
            print(f"    Median: {ll_epu.median():.1f}h")
            print(f"    Kalshi leads: {(ll_epu < 0).sum()}/{len(ll_epu)} ({(ll_epu < 0).mean():.0%})")

        # By event type
        print("\n  By event type:")
        for et in results["event_type"].unique():
            subset = results[results["event_type"] == et]
            kr = subset["kalshi_reaction_hours"].dropna()
            if len(kr) > 0:
                print(f"    {et}: mean reaction={kr.mean():.1f}h, n={len(kr)}")

        results.to_csv(os.path.join(DATA_DIR, "hourly_event_results.csv"), index=False)

    # Statistical tests
    print("\n" + "=" * 70)
    print("PHASE 4: STATISTICAL TESTS")
    print("=" * 70)

    sig_results = test_information_speed_significance(results)

    for test_name, test_result in sig_results.items():
        if isinstance(test_result, dict) and "p_value" in test_result:
            print(f"  {test_name}: p={test_result['p_value']}, significant={test_result.get('significant')}")
        elif isinstance(test_result, dict) and "n" in test_result:
            print(f"  {test_name}: n={test_result['n']}, mean={test_result.get('mean_lead_lag_hours')}h")

    with open(os.path.join(DATA_DIR, "statistical_tests.json"), "w") as f:
        json.dump(sig_results, f, indent=2, default=str)

    # Plots
    print("\n" + "=" * 70)
    print("PHASE 5: VISUALIZATION")
    print("=" * 70)

    windows = compute_hourly_event_windows(hourly_bv, events, window_hours=72)
    plot_event_windows(windows, results, os.path.join(DATA_DIR, "plots"))

    # Summary
    print("\n" + "=" * 70)
    print("GENERATING RESULTS SUMMARY")
    print("=" * 70)

    summary = {
        "n_markets_with_hourly": len(hourly_prices),
        "domains": list(hourly_bv.keys()),
        "n_events_analyzed": len(results),
        "n_with_kalshi_reaction": int(results["kalshi_reaction_hours"].notna().sum()) if not results.empty else 0,
        "n_with_epu_comparison": int(results["lead_lag_vs_epu_hours"].notna().sum()) if not results.empty else 0,
        "statistical_tests": sig_results,
    }

    if not results.empty:
        ll = results["lead_lag_vs_epu_hours"].dropna()
        if len(ll) > 0:
            summary["mean_lead_lag_vs_epu_hours"] = round(float(ll.mean()), 1)
            summary["median_lead_lag_vs_epu_hours"] = round(float(ll.median()), 1)
            summary["pct_kalshi_leads_epu"] = round(float((ll < 0).mean()), 3)

    with open(os.path.join(DATA_DIR, "results_summary.json"), "w") as f:
        json.dump(summary, f, indent=2, default=str)

    elapsed = datetime.now() - start_time
    print(f"\n{'=' * 70}")
    print(f"EXPERIMENT 4 COMPLETE ({elapsed.total_seconds():.0f}s)")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
