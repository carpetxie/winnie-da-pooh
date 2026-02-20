"""
experiment13/run.py

Experiment 13: Unified Distributional Calibration & CPI Horse Race.

Merges experiments 7 (implied distributions) and 12 (CRPS scoring) into a
single coherent analysis, adding:
1. Per-series separate Wilcoxon tests (not just pooled)
2. CPI horse race vs SPF and TIPS benchmarks
3. Apples-to-apples point forecast comparison (MAE vs MAE)
4. Explicit documentation of CRPS <= MAE mathematical relationship
5. Enhanced temporal evolution analysis

No new Kalshi API calls. Fetches FRED data for benchmarks.

Usage:
    uv run python -m experiment13.run
"""

import os
import json
import numpy as np
import pandas as pd
from datetime import datetime
from scipy import stats

DATA_DIR = "data/exp13"


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "plots"), exist_ok=True)

    start_time = datetime.now()
    print(f"Experiment 13 started at {start_time.strftime('%H:%M:%S')}")

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
        fetch_historical_cpi_from_fred,
        fetch_historical_jobless_claims,
        fetch_historical_gdp,
    )
    from experiment13.horse_race import run_cpi_horse_race

    # ================================================================
    # PHASE 1: LOAD MULTI-STRIKE MARKETS
    # ================================================================
    print("\n" + "=" * 70)
    print("PHASE 1: LOADING MULTI-STRIKE MARKETS")
    print("=" * 70)

    markets_df = load_targeted_markets()
    strike_df = extract_strike_markets(markets_df)
    event_groups = group_by_event(strike_df)
    print(f"  {len(strike_df)} strike markets across {len(event_groups)} events")

    # ================================================================
    # PHASE 2: IMPLIED CDFs AND NO-ARBITRAGE
    # ================================================================
    print("\n" + "=" * 70)
    print("PHASE 2: IMPLIED CDFs AND NO-ARBITRAGE TESTING")
    print("=" * 70)

    total_snapshots = 0
    total_violations = 0
    total_checked = 0
    total_reverted = 0
    events_with_violations = 0

    for event_ticker, event_markets in sorted(event_groups.items()):
        snapshots = build_implied_cdf_snapshots(event_markets)
        n_snap = len(snapshots)
        total_snapshots += n_snap

        event_violations = sum(1 for s in snapshots if not s["is_monotonic"])
        total_violations += event_violations
        if event_violations > 0:
            events_with_violations += 1

        # Check reversion of violations
        for i, s in enumerate(snapshots):
            if not s["is_monotonic"] and i + 1 < n_snap:
                total_checked += 1
                if snapshots[i + 1]["is_monotonic"]:
                    total_reverted += 1

    violation_rate = total_violations / total_snapshots * 100 if total_snapshots > 0 else 0
    reversion_rate = total_reverted / total_checked * 100 if total_checked > 0 else 0

    print(f"  Total hourly snapshots: {total_snapshots:,}")
    print(f"  Violating snapshots: {total_violations} ({violation_rate:.1f}%)")
    print(f"  Events with violations: {events_with_violations}/{len(event_groups)}")
    print(f"  Reversion rate: {total_reverted}/{total_checked} = {reversion_rate:.0f}% within 1 hour")

    no_arb_results = {
        "total_snapshots": total_snapshots,
        "violating_snapshots": total_violations,
        "violation_rate_pct": round(violation_rate, 1),
        "reversion_checked": total_checked,
        "reversion_count": total_reverted,
        "reversion_rate_pct": round(reversion_rate, 0),
    }

    # ================================================================
    # PHASE 3: CRPS SCORING VS BENCHMARKS
    # ================================================================
    print("\n" + "=" * 70)
    print("PHASE 3: CRPS SCORING (KALSHI vs BENCHMARKS)")
    print("=" * 70)

    # Fetch historical data
    historical = {}
    try:
        cpi_hist = fetch_historical_cpi_from_fred("2020-01-01", "2025-12-01")
        historical["KXCPI"] = cpi_hist
        print(f"  CPI history: {len(cpi_hist)} monthly changes")
    except Exception as e:
        print(f"  CPI fetch failed: {e}")
        historical["KXCPI"] = []
    try:
        claims_hist = fetch_historical_jobless_claims("2020-01-01", "2025-12-01")
        historical["KXJOBLESSCLAIMS"] = claims_hist
        print(f"  Jobless Claims history: {len(claims_hist)} weekly values")
    except Exception as e:
        print(f"  Jobless Claims fetch failed: {e}")
        historical["KXJOBLESSCLAIMS"] = []
    try:
        gdp_hist = fetch_historical_gdp("2015-01-01", "2025-12-01")
        historical["KXGDP"] = gdp_hist
        print(f"  GDP history: {len(gdp_hist)} quarterly values")
    except Exception as e:
        print(f"  GDP fetch failed: {e}")
        historical["KXGDP"] = []

    crps_results = []
    for event_ticker, event_markets in sorted(event_groups.items()):
        series = event_markets["series_prefix"].iloc[0]
        exp_val = event_markets["expiration_value"].iloc[0]
        realized = _parse_expiration_value(exp_val, series)
        if realized is None:
            continue

        snapshots = build_implied_cdf_snapshots(event_markets)
        if len(snapshots) < 2:
            continue

        mid_idx = len(snapshots) // 2
        mid_snap = snapshots[mid_idx]
        strikes = mid_snap["strikes"]
        cdf_values = mid_snap["cdf_values"]
        if len(strikes) < 2:
            continue

        try:
            kalshi_crps = compute_crps(strikes, cdf_values, realized)
        except Exception as e:
            print(f"  CRPS failed for {event_ticker}: {e}")
            continue

        pdf = compute_implied_pdf(strikes, cdf_values)
        implied_mean = pdf.get("implied_mean") if pdf else None

        try:
            uniform_crps = compute_uniform_crps(min(strikes), max(strikes), realized)
        except Exception:
            uniform_crps = None

        hist_crps = None
        if series in historical and historical[series]:
            try:
                hist_crps = compute_historical_crps(historical[series], realized)
            except Exception:
                hist_crps = None

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
        })

    crps_df = pd.DataFrame(crps_results)
    print(f"\n  Events with CRPS: {len(crps_df)}")

    for series in crps_df["series"].unique():
        s = crps_df[crps_df["series"] == series]
        print(f"\n  {series} (n={len(s)}):")
        print(f"    Kalshi CRPS:     mean={s['kalshi_crps'].mean():.4f}, median={s['kalshi_crps'].median():.4f}")
        if s["uniform_crps"].notna().any():
            print(f"    Uniform CRPS:    mean={s['uniform_crps'].mean():.4f}")
        if s["historical_crps"].notna().any():
            print(f"    Historical CRPS: mean={s['historical_crps'].mean():.4f}")

    # ================================================================
    # PHASE 4: PER-SERIES WILCOXON TESTS (NOT JUST POOLED)
    # ================================================================
    print("\n" + "=" * 70)
    print("PHASE 4: STATISTICAL TESTS (POOLED AND PER-SERIES)")
    print("=" * 70)

    test_results = {}

    # Pooled tests
    for comparison, col_a, col_b, label in [
        ("kalshi_vs_uniform", "kalshi_crps", "uniform_crps", "Kalshi vs Uniform"),
        ("kalshi_vs_historical", "kalshi_crps", "historical_crps", "Kalshi vs Historical"),
        ("kalshi_dist_vs_point", "kalshi_crps", "point_crps", "Kalshi CRPS vs Point MAE"),
    ]:
        valid = crps_df.dropna(subset=[col_a, col_b])
        if len(valid) >= 5:
            stat, p = stats.wilcoxon(valid[col_a], valid[col_b], alternative="less")
            test_results[comparison] = {
                "n": len(valid),
                "kalshi_mean": float(valid[col_a].mean()),
                "benchmark_mean": float(valid[col_b].mean()),
                "wilcoxon_stat": float(stat),
                "p_value": float(p),
                "significant": p < 0.05,
                "scope": "pooled",
            }
            sig = "*" if p < 0.05 else ""
            print(f"  {label} (pooled, n={len(valid)}): "
                  f"Kalshi={valid[col_a].mean():.4f}, "
                  f"Benchmark={valid[col_b].mean():.4f}, "
                  f"p={p:.4f}{sig}")

    # Add note about CRPS <= MAE
    if "kalshi_dist_vs_point" in test_results:
        test_results["kalshi_dist_vs_point"]["mathematical_note"] = (
            "CRPS <= MAE is a mathematical property of proper scoring rules. "
            "Finding Kalshi CRPS < point MAE is expected for any well-formed "
            "distribution and does NOT demonstrate superior forecasting accuracy. "
            "The honest comparison is point-vs-point (Phase 6 horse race)."
        )

    # Per-series tests
    print("\n  --- Per-series Wilcoxon tests ---")
    for series in sorted(crps_df["series"].unique()):
        s = crps_df[crps_df["series"] == series]

        for comparison, col_b, label in [
            ("vs_uniform", "uniform_crps", "Uniform"),
            ("vs_historical", "historical_crps", "Historical"),
        ]:
            valid = s.dropna(subset=["kalshi_crps", col_b])
            key = f"kalshi_{comparison}_{series}"
            if len(valid) >= 5:
                stat, p = stats.wilcoxon(valid["kalshi_crps"], valid[col_b], alternative="less")
                test_results[key] = {
                    "n": len(valid),
                    "series": series,
                    "kalshi_mean": float(valid["kalshi_crps"].mean()),
                    "benchmark_mean": float(valid[col_b].mean()),
                    "wilcoxon_stat": float(stat),
                    "p_value": float(p),
                    "significant": p < 0.05,
                    "scope": f"per-series ({series})",
                }
                sig = "*" if p < 0.05 else ""
                print(f"  {series} vs {label} (n={len(valid)}): "
                      f"Kalshi={valid['kalshi_crps'].mean():.4f}, "
                      f"{label}={valid[col_b].mean():.4f}, "
                      f"p={p:.4f}{sig}")
            else:
                test_results[key] = {
                    "n": len(valid),
                    "series": series,
                    "note": f"Insufficient data (n={len(valid)}, need >=5)",
                }
                print(f"  {series} vs {label}: insufficient data (n={len(valid)})")

    # ================================================================
    # PHASE 5: TEMPORAL CRPS EVOLUTION
    # ================================================================
    print("\n" + "=" * 70)
    print("PHASE 5: TEMPORAL CRPS EVOLUTION")
    print("=" * 70)

    temporal_crps = []
    for event_ticker, event_markets in sorted(event_groups.items()):
        series = event_markets["series_prefix"].iloc[0]
        exp_val = event_markets["expiration_value"].iloc[0]
        realized = _parse_expiration_value(exp_val, series)
        if realized is None:
            continue

        snapshots = build_implied_cdf_snapshots(event_markets)
        if len(snapshots) < 6:
            continue

        n = len(snapshots)
        for pct_label, idx in [("10%", n // 10), ("25%", n // 4),
                                ("50%", n // 2), ("75%", 3 * n // 4),
                                ("90%", 9 * n // 10)]:
            idx = min(idx, n - 1)
            snap = snapshots[idx]
            strikes = snap["strikes"]
            cdf_values = snap["cdf_values"]
            if len(strikes) < 2:
                continue
            try:
                crps_val = compute_crps(strikes, cdf_values, realized)
                uniform_val = compute_uniform_crps(min(strikes), max(strikes), realized)
                temporal_crps.append({
                    "event_ticker": event_ticker,
                    "series": series,
                    "lifetime_pct": pct_label,
                    "snapshot_idx": idx,
                    "n_snapshots": n,
                    "kalshi_crps": crps_val,
                    "uniform_crps": uniform_val,
                    "beats_uniform": crps_val < uniform_val,
                })
            except Exception:
                continue

    temporal_df = pd.DataFrame(temporal_crps)
    if len(temporal_df) > 0:
        print(f"  Events with temporal data: {temporal_df['event_ticker'].nunique()}")

        for series in sorted(temporal_df["series"].unique()):
            s = temporal_df[temporal_df["series"] == series]
            print(f"\n  {series}:")
            for pct in ["10%", "25%", "50%", "75%", "90%"]:
                t = s[s["lifetime_pct"] == pct]
                if len(t) == 0:
                    continue
                ratio = t['kalshi_crps'].mean() / t['uniform_crps'].mean() if t['uniform_crps'].mean() > 0 else float('inf')
                print(f"    {pct}: CRPS={t['kalshi_crps'].mean():.4f}, "
                      f"uniform={t['uniform_crps'].mean():.4f}, "
                      f"ratio={ratio:.2f}x, "
                      f"beats_uniform={t['beats_uniform'].mean():.0%}")

    # ================================================================
    # PHASE 6: CPI HORSE RACE (POINT FORECASTS)
    # ================================================================
    print("\n" + "=" * 70)
    print("PHASE 6: CPI HORSE RACE (KALSHI vs SPF vs TIPS)")
    print("=" * 70)

    cpi_events = crps_df[crps_df["series"] == "KXCPI"].copy()
    horse_race_results = {}

    if len(cpi_events) >= 3:
        horse_race_results = run_cpi_horse_race(cpi_events)

        print(f"\n  CPI events in horse race: {horse_race_results['n_events']}")
        hr_df = pd.DataFrame(horse_race_results["per_event"])

        # Summary table
        print("\n  Point forecast MAE comparison:")
        for col, label in [
            ("kalshi_point_mae", "Kalshi implied mean"),
            ("spf_mae", "SPF (annual/12)"),
            ("tips_mae", "TIPS breakeven"),
            ("random_walk_mae", "Random walk (last month)"),
            ("trailing_mean_mae", "Trailing mean"),
        ]:
            if col in hr_df.columns and hr_df[col].notna().any():
                vals = hr_df[col].dropna()
                print(f"    {label}: mean MAE={vals.mean():.4f}, "
                      f"median MAE={vals.median():.4f}, n={len(vals)}")

        # Test results
        for test_name, test in horse_race_results.get("statistical_tests", {}).items():
            if "wilcoxon_p" in test:
                sig = "*" if test["significant"] else ""
                print(f"    {test_name}: p={test['wilcoxon_p']:.4f}{sig} (n={test['n']})")
    else:
        print("  Insufficient CPI events for horse race")

    # ================================================================
    # PHASE 7: SERIAL CORRELATION ACKNOWLEDGMENT
    # ================================================================
    serial_corr_note = {
        "cpi_serial_correlation": (
            "Sequential monthly CPI releases are serially correlated "
            "(actual CPI MoM changes have AR(1) structure). With n=14 CPI events, "
            "effective degrees of freedom for CPI-specific tests are lower than 14. "
            "This is a fundamental limitation of the available data."
        ),
        "pooled_scale_mixing": (
            "The pooled Wilcoxon (n=33) mixes series with different CRPS scales: "
            "KXJOBLESSCLAIMS CRPS is in thousands while KXCPI is in percentage points. "
            "Per-series tests (Phase 4) avoid this problem but have lower power."
        ),
    }

    # ================================================================
    # PHASE 8: VISUALIZATION
    # ================================================================
    print("\n" + "=" * 70)
    print("PHASE 8: VISUALIZATION")
    print("=" * 70)

    _plot_unified(crps_df, temporal_df, horse_race_results, os.path.join(DATA_DIR, "plots"))

    # ================================================================
    # SAVE RESULTS
    # ================================================================
    all_results = {
        "n_events": len(crps_df),
        "no_arbitrage": no_arb_results,
        "per_event_crps": crps_results,
        "statistical_tests": test_results,
        "temporal_crps": temporal_crps if len(temporal_crps) > 0 else [],
        "horse_race": horse_race_results,
        "serial_correlation_notes": serial_corr_note,
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

    with open(os.path.join(DATA_DIR, "unified_results.json"), "w") as f:
        json.dump(all_results, f, indent=2, default=str)

    crps_df.to_csv(os.path.join(DATA_DIR, "crps_per_event.csv"), index=False)

    elapsed = datetime.now() - start_time
    print(f"\n{'=' * 70}")
    print(f"EXPERIMENT 13 COMPLETE ({elapsed.total_seconds():.0f}s)")
    print(f"{'=' * 70}")


def _plot_unified(crps_df, temporal_df, horse_race_results, output_dir):
    """Generate unified plots for the distributional calibration paper."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    os.makedirs(output_dir, exist_ok=True)

    if len(crps_df) == 0:
        return

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # Panel 1: Per-series CRPS comparison
    ax = axes[0, 0]
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
    ax.set_title("CRPS by Event Series")
    ax.legend()
    ax.grid(True, alpha=0.3, axis="y")

    # Panel 2: Per-event scatter
    ax = axes[0, 1]
    valid = crps_df.dropna(subset=["kalshi_crps", "uniform_crps"])
    if len(valid) > 0:
        colors = {"KXCPI": "#e74c3c", "KXGDP": "#3498db", "KXJOBLESSCLAIMS": "#2ecc71"}
        for series in valid["series"].unique():
            s = valid[valid["series"] == series]
            ax.scatter(s["uniform_crps"], s["kalshi_crps"],
                      c=colors.get(series, "gray"), label=series,
                      s=60, edgecolors="black", linewidths=0.5)
        max_val = max(valid["kalshi_crps"].max(), valid["uniform_crps"].max()) * 1.1
        ax.plot([0, max_val], [0, max_val], "k--", alpha=0.5, label="Equal")
        ax.set_xlabel("Uniform CRPS")
        ax.set_ylabel("Kalshi CRPS")
        ax.set_title("Kalshi vs Uniform: Per-Event")
        ax.legend()
        ax.grid(True, alpha=0.3)

    # Panel 3: Temporal evolution
    ax = axes[1, 0]
    if len(temporal_df) > 0:
        pct_order = ["10%", "25%", "50%", "75%", "90%"]
        for series in sorted(temporal_df["series"].unique()):
            s = temporal_df[temporal_df["series"] == series]
            ratios = []
            for pct in pct_order:
                t = s[s["lifetime_pct"] == pct]
                if len(t) > 0 and t["uniform_crps"].mean() > 0:
                    ratios.append(t["kalshi_crps"].mean() / t["uniform_crps"].mean())
                else:
                    ratios.append(None)
            ax.plot(range(len(pct_order)), ratios, "o-",
                   label=series, markersize=6)
        ax.axhline(y=1.0, color="black", linestyle="--", alpha=0.5, label="Equal to Uniform")
        ax.set_xticks(range(len(pct_order)))
        ax.set_xticklabels(pct_order)
        ax.set_xlabel("Market Lifetime %")
        ax.set_ylabel("CRPS Ratio (Kalshi / Uniform)")
        ax.set_title("Temporal CRPS Evolution")
        ax.legend()
        ax.grid(True, alpha=0.3)

    # Panel 4: Horse race (if available)
    ax = axes[1, 1]
    if horse_race_results and "per_event" in horse_race_results:
        hr_df = pd.DataFrame(horse_race_results["per_event"])
        maes = {}
        for col, label in [
            ("kalshi_point_mae", "Kalshi"),
            ("spf_mae", "SPF"),
            ("tips_mae", "TIPS"),
        ]:
            if col in hr_df.columns and hr_df[col].notna().any():
                maes[label] = hr_df[col].dropna().values

        if maes:
            positions = range(len(maes))
            bp = ax.boxplot(list(maes.values()), labels=list(maes.keys()),
                          patch_artist=True)
            colors_bp = ["#2ecc71", "#e74c3c", "#3498db"]
            for patch, color in zip(bp["boxes"], colors_bp[:len(maes)]):
                patch.set_facecolor(color)
                patch.set_alpha(0.6)
            ax.set_ylabel("Absolute Error (MoM %)")
            ax.set_title("CPI Point Forecast Horse Race")
            ax.grid(True, alpha=0.3, axis="y")
    else:
        ax.text(0.5, 0.5, "No horse race data", ha="center", va="center",
               transform=ax.transAxes)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "unified_calibration.png"), dpi=150)
    plt.close()
    print(f"  Saved {output_dir}/unified_calibration.png")


if __name__ == "__main__":
    main()
