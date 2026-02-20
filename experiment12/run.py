"""
experiment12/run.py

Experiment 12: CRPS Distributional Calibration Scoring.

Evaluates Kalshi's implied probability distributions using proper scoring
rules (CRPS) and compares to naive benchmarks (uniform, historical).

No new API calls for Kalshi data. Fetches FRED historical data for benchmarks.

Usage:
    uv run python -m experiment12.run
"""

import os
import json
import numpy as np
import pandas as pd
from datetime import datetime
from scipy import stats

DATA_DIR = "data/exp12"


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "plots"), exist_ok=True)

    start_time = datetime.now()
    print(f"Experiment 12 started at {start_time.strftime('%H:%M:%S')}")

    from experiment7.implied_distributions import (
        load_targeted_markets,
        extract_strike_markets,
        group_by_event,
        build_implied_cdf_snapshots,
        compute_implied_pdf,
        _parse_expiration_value,
    )
    from experiment12.distributional_calibration import (
        compute_crps,
        compute_uniform_crps,
        compute_historical_crps,
        compute_point_crps,
        extract_event_cdf_at_time,
        fetch_historical_cpi_from_fred,
        fetch_historical_jobless_claims,
        fetch_historical_gdp,
    )

    # Phase 1: Load strike markets and event groups
    print("\n" + "=" * 70)
    print("PHASE 1: LOADING MULTI-STRIKE MARKETS")
    print("=" * 70)

    markets_df = load_targeted_markets()
    strike_df = extract_strike_markets(markets_df)
    event_groups = group_by_event(strike_df)
    print(f"  {len(strike_df)} strike markets across {len(event_groups)} events")

    # Phase 2: Fetch historical benchmarks
    print("\n" + "=" * 70)
    print("PHASE 2: FETCHING HISTORICAL BENCHMARKS FROM FRED")
    print("=" * 70)

    historical = {}
    try:
        cpi_hist = fetch_historical_cpi_from_fred("2020-01-01", "2025-12-01")
        historical["KXCPI"] = cpi_hist
        print(f"  CPI history: {len(cpi_hist)} monthly changes, mean={np.mean(cpi_hist):.3f}%")
    except Exception as e:
        print(f"  CPI fetch failed: {e}")
        historical["KXCPI"] = []

    try:
        claims_hist = fetch_historical_jobless_claims("2020-01-01", "2025-12-01")
        historical["KXJOBLESSCLAIMS"] = claims_hist
        print(f"  Jobless Claims history: {len(claims_hist)} weekly values, mean={np.mean(claims_hist):.0f}")
    except Exception as e:
        print(f"  Jobless Claims fetch failed: {e}")
        historical["KXJOBLESSCLAIMS"] = []

    try:
        gdp_hist = fetch_historical_gdp("2015-01-01", "2025-12-01")
        historical["KXGDP"] = gdp_hist
        print(f"  GDP history: {len(gdp_hist)} quarterly values, mean={np.mean(gdp_hist):.2f}%")
    except Exception as e:
        print(f"  GDP fetch failed: {e}")
        historical["KXGDP"] = []

    # Phase 3: Compute CRPS for each event
    print("\n" + "=" * 70)
    print("PHASE 3: COMPUTING CRPS FOR KALSHI IMPLIED DISTRIBUTIONS")
    print("=" * 70)

    crps_results = []

    for event_ticker, event_markets in sorted(event_groups.items()):
        series = event_markets["series_prefix"].iloc[0]

        # Get realized value
        exp_val = event_markets["expiration_value"].iloc[0]
        realized = _parse_expiration_value(exp_val, series)
        if realized is None:
            continue

        # Build CDF snapshots
        snapshots = build_implied_cdf_snapshots(event_markets)
        if len(snapshots) < 2:
            continue

        # Use mid-life snapshot (same as experiment7)
        mid_idx = len(snapshots) // 2
        mid_snap = snapshots[mid_idx]
        strikes = mid_snap["strikes"]
        cdf_values = mid_snap["cdf_values"]

        if len(strikes) < 2:
            continue

        # Compute Kalshi CRPS
        try:
            kalshi_crps = compute_crps(strikes, cdf_values, realized)
        except Exception as e:
            print(f"  CRPS failed for {event_ticker}: {e}")
            continue

        # Compute implied mean for point forecast benchmark
        pdf = compute_implied_pdf(strikes, cdf_values)
        implied_mean = pdf.get("implied_mean") if pdf else None

        # Uniform benchmark
        try:
            uniform_crps = compute_uniform_crps(min(strikes), max(strikes), realized)
        except Exception:
            uniform_crps = None

        # Historical benchmark
        hist_key = series if series in historical else None
        hist_crps = None
        if hist_key and historical[hist_key]:
            try:
                hist_crps = compute_historical_crps(historical[hist_key], realized)
            except Exception:
                hist_crps = None

        # Point forecast benchmark
        point_crps = None
        if implied_mean is not None:
            point_crps = compute_point_crps(implied_mean, realized)

        crps_results.append({
            "event_ticker": event_ticker,
            "series": series,
            "realized": realized,
            "implied_mean": implied_mean,
            "n_strikes": len(strikes),
            "n_snapshots": len(snapshots),
            "kalshi_crps": kalshi_crps,
            "uniform_crps": uniform_crps,
            "historical_crps": hist_crps,
            "point_crps": point_crps,
            "crps_improvement_vs_uniform": (
                (uniform_crps - kalshi_crps) / uniform_crps * 100
                if uniform_crps and uniform_crps > 0 else None
            ),
            "crps_improvement_vs_historical": (
                (hist_crps - kalshi_crps) / hist_crps * 100
                if hist_crps and hist_crps > 0 else None
            ),
        })

    crps_df = pd.DataFrame(crps_results)
    print(f"\n  Events with CRPS: {len(crps_df)}")

    if len(crps_df) > 0:
        # Per-series summary
        for series in crps_df["series"].unique():
            s = crps_df[crps_df["series"] == series]
            print(f"\n  {series} (n={len(s)}):")
            print(f"    Kalshi CRPS:     mean={s['kalshi_crps'].mean():.4f}, median={s['kalshi_crps'].median():.4f}")
            if s["uniform_crps"].notna().any():
                print(f"    Uniform CRPS:    mean={s['uniform_crps'].mean():.4f}")
                imp = s["crps_improvement_vs_uniform"].dropna()
                if len(imp) > 0:
                    print(f"    Improvement:     {imp.mean():.1f}% better than uniform")
            if s["historical_crps"].notna().any():
                print(f"    Historical CRPS: mean={s['historical_crps'].mean():.4f}")
                imp = s["crps_improvement_vs_historical"].dropna()
                if len(imp) > 0:
                    print(f"    Improvement:     {imp.mean():.1f}% better than historical")

    # Phase 4: Statistical tests
    print("\n" + "=" * 70)
    print("PHASE 4: STATISTICAL TESTS (KALSHI vs BENCHMARKS)")
    print("=" * 70)

    test_results = {}

    # Kalshi vs Uniform
    valid = crps_df.dropna(subset=["kalshi_crps", "uniform_crps"])
    if len(valid) >= 5:
        stat, p = stats.wilcoxon(
            valid["kalshi_crps"], valid["uniform_crps"],
            alternative="less",
        )
        test_results["kalshi_vs_uniform"] = {
            "n": len(valid),
            "kalshi_mean": float(valid["kalshi_crps"].mean()),
            "uniform_mean": float(valid["uniform_crps"].mean()),
            "wilcoxon_stat": float(stat),
            "p_value": float(p),
            "significant": p < 0.05,
        }
        sig = "*" if p < 0.05 else ""
        print(f"  Kalshi vs Uniform (n={len(valid)}): "
              f"Kalshi={valid['kalshi_crps'].mean():.4f}, "
              f"Uniform={valid['uniform_crps'].mean():.4f}, "
              f"Wilcoxon p={p:.4f}{sig}")

    # Kalshi vs Historical
    valid = crps_df.dropna(subset=["kalshi_crps", "historical_crps"])
    if len(valid) >= 5:
        stat, p = stats.wilcoxon(
            valid["kalshi_crps"], valid["historical_crps"],
            alternative="less",
        )
        test_results["kalshi_vs_historical"] = {
            "n": len(valid),
            "kalshi_mean": float(valid["kalshi_crps"].mean()),
            "historical_mean": float(valid["historical_crps"].mean()),
            "wilcoxon_stat": float(stat),
            "p_value": float(p),
            "significant": p < 0.05,
        }
        sig = "*" if p < 0.05 else ""
        print(f"  Kalshi vs Historical (n={len(valid)}): "
              f"Kalshi={valid['kalshi_crps'].mean():.4f}, "
              f"Historical={valid['historical_crps'].mean():.4f}, "
              f"Wilcoxon p={p:.4f}{sig}")

    # Kalshi distributional vs point forecast
    valid = crps_df.dropna(subset=["kalshi_crps", "point_crps"])
    if len(valid) >= 5:
        # CRPS of distribution should be <= MAE of point forecast
        stat, p = stats.wilcoxon(
            valid["kalshi_crps"], valid["point_crps"],
            alternative="less",
        )
        test_results["kalshi_dist_vs_point"] = {
            "n": len(valid),
            "kalshi_crps_mean": float(valid["kalshi_crps"].mean()),
            "point_mae_mean": float(valid["point_crps"].mean()),
            "wilcoxon_stat": float(stat),
            "p_value": float(p),
            "significant": p < 0.05,
        }
        sig = "*" if p < 0.05 else ""
        print(f"  Kalshi CRPS vs Point MAE (n={len(valid)}): "
              f"CRPS={valid['kalshi_crps'].mean():.4f}, "
              f"MAE={valid['point_crps'].mean():.4f}, "
              f"Wilcoxon p={p:.4f}{sig}")

    # Phase 5: Visualization
    print("\n" + "=" * 70)
    print("PHASE 5: VISUALIZATION")
    print("=" * 70)

    _plot_crps_comparison(crps_df, os.path.join(DATA_DIR, "plots"))

    # Save results
    all_results = {
        "n_events": len(crps_df),
        "per_event_crps": crps_results,
        "statistical_tests": test_results,
        "per_series_summary": {},
    }

    for series in crps_df["series"].unique():
        s = crps_df[crps_df["series"] == series]
        all_results["per_series_summary"][series] = {
            "n": len(s),
            "kalshi_crps_mean": float(s["kalshi_crps"].mean()),
            "kalshi_crps_median": float(s["kalshi_crps"].median()),
            "uniform_crps_mean": float(s["uniform_crps"].mean()) if s["uniform_crps"].notna().any() else None,
            "historical_crps_mean": float(s["historical_crps"].mean()) if s["historical_crps"].notna().any() else None,
        }

    with open(os.path.join(DATA_DIR, "crps_results.json"), "w") as f:
        json.dump(all_results, f, indent=2, default=str)

    crps_df.to_csv(os.path.join(DATA_DIR, "crps_per_event.csv"), index=False)

    elapsed = datetime.now() - start_time
    print(f"\n{'=' * 70}")
    print(f"EXPERIMENT 12 COMPLETE ({elapsed.total_seconds():.0f}s)")
    print(f"{'=' * 70}")


def _plot_crps_comparison(crps_df, output_dir):
    """Plot CRPS comparison: Kalshi vs benchmarks."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    os.makedirs(output_dir, exist_ok=True)

    if len(crps_df) == 0:
        return

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Panel 1: Per-series CRPS comparison
    ax = axes[0]
    series_list = sorted(crps_df["series"].unique())
    x = np.arange(len(series_list))
    width = 0.2

    for i, (col, label, color) in enumerate([
        ("kalshi_crps", "Kalshi", "#2ecc71"),
        ("uniform_crps", "Uniform", "#e74c3c"),
        ("historical_crps", "Historical", "#3498db"),
    ]):
        means = []
        for s in series_list:
            vals = crps_df[crps_df["series"] == s][col].dropna()
            means.append(vals.mean() if len(vals) > 0 else 0)
        ax.bar(x + i * width, means, width, label=label, color=color, edgecolor="black")

    ax.set_xticks(x + width)
    ax.set_xticklabels(series_list)
    ax.set_ylabel("CRPS (lower = better)")
    ax.set_title("CRPS by Event Series: Kalshi vs Benchmarks")
    ax.legend()
    ax.grid(True, alpha=0.3, axis="y")

    # Panel 2: Per-event scatter (Kalshi vs Uniform)
    ax = axes[1]
    valid = crps_df.dropna(subset=["kalshi_crps", "uniform_crps"])
    if len(valid) > 0:
        colors = {"KXCPI": "#e74c3c", "KXGDP": "#3498db", "KXJOBLESSCLAIMS": "#2ecc71"}
        for series in valid["series"].unique():
            s = valid[valid["series"] == series]
            ax.scatter(
                s["uniform_crps"], s["kalshi_crps"],
                c=colors.get(series, "gray"), label=series,
                s=60, edgecolors="black", linewidths=0.5,
            )
        max_val = max(valid["kalshi_crps"].max(), valid["uniform_crps"].max()) * 1.1
        ax.plot([0, max_val], [0, max_val], "k--", alpha=0.5, label="Equal")
        ax.set_xlabel("Uniform CRPS")
        ax.set_ylabel("Kalshi CRPS")
        ax.set_title("Kalshi vs Uniform: Per-Event CRPS")
        ax.legend()
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "crps_comparison.png"), dpi=150)
    plt.close()
    print(f"  Saved {output_dir}/crps_comparison.png")


if __name__ == "__main__":
    main()
