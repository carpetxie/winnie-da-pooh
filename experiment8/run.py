"""
experiment8/run.py

Experiment 8: Kalshi vs TIPS Breakeven Inflation Comparison.

Tests whether Kalshi CPI prediction markets contain price discovery
information beyond the US Treasury bond market (TIPS breakeven rates).

Requires FRED API fetch for T10YIE and T5YIE.

Usage:
    uv run python -m experiment8.run
    uv run python -m experiment8.run --skip-fetch  # Use cached TIPS data
"""

import os
import json
import argparse
import numpy as np
import pandas as pd
from datetime import datetime

DATA_DIR = "data/exp8"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-fetch", action="store_true",
                        help="Use cached TIPS data")
    args = parser.parse_args()

    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "plots"), exist_ok=True)

    start_time = datetime.now()
    print(f"Experiment 8 started at {start_time.strftime('%H:%M:%S')}")

    from experiment8.tips_comparison import (
        fetch_fred_series,
        build_kalshi_cpi_index,
        run_granger_both_directions,
        compute_lead_lag_correlation,
        plot_tips_comparison,
        TIPS_SERIES,
    )

    # Phase 1: Build Kalshi CPI index
    print("\n" + "=" * 70)
    print("PHASE 1: BUILDING KALSHI CPI EXPECTATIONS INDEX")
    print("=" * 70)

    kalshi_cpi, cpi_count = build_kalshi_cpi_index()
    print(f"  Daily CPI index: {len(kalshi_cpi)} days")
    print(f"  Date range: {kalshi_cpi.index.min()} to {kalshi_cpi.index.max()}")
    print(f"  Mean price: {kalshi_cpi.mean():.4f}")
    print(f"  Mean active markets/day: {cpi_count.mean():.1f}")

    # Save
    cpi_df = pd.DataFrame({"date": kalshi_cpi.index, "kalshi_cpi": kalshi_cpi.values,
                            "n_markets": cpi_count.reindex(kalshi_cpi.index).values})
    cpi_df.to_csv(os.path.join(DATA_DIR, "kalshi_cpi_daily.csv"), index=False)

    # Phase 2: Fetch TIPS data
    print("\n" + "=" * 70)
    print("PHASE 2: LOADING TIPS BREAKEVEN DATA")
    print("=" * 70)

    tips_data = {}
    for series_id, description in TIPS_SERIES.items():
        cache_path = os.path.join(DATA_DIR, f"{series_id}.csv")

        if args.skip_fetch and os.path.exists(cache_path):
            df = pd.read_csv(cache_path, parse_dates=["date"], index_col="date")
            tips_data[series_id] = df["value"]
            print(f"  Loaded cached {series_id}: {len(tips_data[series_id])} days")
        else:
            try:
                series = fetch_fred_series(series_id)
                tips_data[series_id] = series
                # Cache
                pd.DataFrame({"date": series.index, "value": series.values}).to_csv(
                    cache_path, index=False
                )
                print(f"  Fetched {series_id} ({description}): {len(series)} days")
                print(f"    Range: {series.index.min()} to {series.index.max()}")
                print(f"    Mean: {series.mean():.3f}%")
            except Exception as e:
                print(f"  Failed to fetch {series_id}: {e}")

    if not tips_data:
        print("  ERROR: No TIPS data available. Cannot proceed.")
        return

    # Phase 3: Correlation analysis
    print("\n" + "=" * 70)
    print("PHASE 3: CORRELATION ANALYSIS")
    print("=" * 70)

    from scipy import stats

    correlation_results = {}
    for series_id, tips_series in tips_data.items():
        combined = pd.concat([
            kalshi_cpi.rename("kalshi"),
            tips_series.rename("tips"),
        ], axis=1).dropna()

        if len(combined) < 20:
            print(f"  {series_id}: insufficient overlap ({len(combined)} days)")
            continue

        r_pearson, p_pearson = stats.pearsonr(combined["kalshi"], combined["tips"])
        r_spearman, p_spearman = stats.spearmanr(combined["kalshi"], combined["tips"])

        # Also correlate changes (returns)
        changes = combined.diff().dropna()
        if len(changes) >= 20:
            r_change, p_change = stats.pearsonr(changes["kalshi"], changes["tips"])
        else:
            r_change, p_change = np.nan, np.nan

        correlation_results[series_id] = {
            "n_days": len(combined),
            "pearson_r": float(r_pearson),
            "pearson_p": float(p_pearson),
            "spearman_r": float(r_spearman),
            "spearman_p": float(p_spearman),
            "change_correlation_r": float(r_change) if not np.isnan(r_change) else None,
            "change_correlation_p": float(p_change) if not np.isnan(p_change) else None,
        }

        print(f"\n  {series_id} ({len(combined)} overlapping days):")
        print(f"    Levels:  Pearson r={r_pearson:.3f} (p={p_pearson:.4f}), "
              f"Spearman r={r_spearman:.3f} (p={p_spearman:.4f})")
        print(f"    Changes: Pearson r={r_change:.3f} (p={p_change:.4f})" if not np.isnan(r_change) else "")

    # Phase 4: Lead-lag analysis
    print("\n" + "=" * 70)
    print("PHASE 4: LEAD-LAG CROSS-CORRELATION")
    print("=" * 70)

    lead_lag_results = {}
    for series_id, tips_series in tips_data.items():
        ll = compute_lead_lag_correlation(kalshi_cpi, tips_series, max_lag=15)
        lead_lag_results[series_id] = ll

        if "error" not in ll:
            print(f"\n  {series_id}:")
            print(f"    Best lag: {ll['best_lag']} days (r={ll['best_r']:.3f}, p={ll['best_p']:.4f})")
            print(f"    Interpretation: {ll['interpretation']}")

    # Phase 5: Granger causality
    print("\n" + "=" * 70)
    print("PHASE 5: GRANGER CAUSALITY")
    print("=" * 70)

    granger_results = {}
    for series_id, tips_series in tips_data.items():
        result = run_granger_both_directions(kalshi_cpi, tips_series, max_lag=10)
        granger_results[series_id] = result

        if "error" in result:
            print(f"  {series_id}: {result['error']}")
            continue

        xy = result["x_causes_y"]
        yx = result["y_causes_x"]
        print(f"\n  {series_id} (n={result['n_obs']}):")
        print(f"    Kalshi → TIPS: lag={xy['best_lag']}, F={xy['f_stat']}, "
              f"p={xy['p_value']:.4f}, sig={xy['significant']}" if xy['p_value'] else
              f"    Kalshi → TIPS: no valid test")
        print(f"    TIPS → Kalshi: lag={yx['best_lag']}, F={yx['f_stat']}, "
              f"p={yx['p_value']:.4f}, sig={yx['significant']}" if yx['p_value'] else
              f"    TIPS → Kalshi: no valid test")

    # Phase 6: Plots
    print("\n" + "=" * 70)
    print("PHASE 6: VISUALIZATION")
    print("=" * 70)

    plot_tips_comparison(kalshi_cpi, tips_data, lead_lag_results,
                        os.path.join(DATA_DIR, "plots"))

    # Save all results
    all_results = {
        "kalshi_cpi_stats": {
            "n_days": len(kalshi_cpi),
            "mean": float(kalshi_cpi.mean()),
            "std": float(kalshi_cpi.std()),
            "date_range": [str(kalshi_cpi.index.min()), str(kalshi_cpi.index.max())],
        },
        "correlations": correlation_results,
        "lead_lag": {k: {kk: vv for kk, vv in v.items() if kk != "correlations"}
                     for k, v in lead_lag_results.items()},
        "granger": granger_results,
    }

    with open(os.path.join(DATA_DIR, "tips_comparison_results.json"), "w") as f:
        json.dump(all_results, f, indent=2, default=str)

    elapsed = datetime.now() - start_time
    print(f"\n{'=' * 70}")
    print(f"EXPERIMENT 8 COMPLETE ({elapsed.total_seconds():.0f}s)")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
