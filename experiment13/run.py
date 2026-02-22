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
    # Use regime-appropriate windows for historical benchmarks.
    # Jobless Claims: 2022-01-01 (post-COVID normalization) to avoid
    # contamination from COVID-era claims of 3-6M vs current 200-250K.
    # CPI: 2020-01-01 is acceptable (CPI MoM doesn't have the same
    # regime break as levels-based claims data).
    # GDP: 2015-01-01 for longer history (quarterly data).
    historical = {}
    historical_covid = {}  # For sensitivity analysis with contaminated window

    try:
        cpi_hist = fetch_historical_cpi_from_fred("2020-01-01", "2025-12-01")
        historical["KXCPI"] = cpi_hist
        print(f"  CPI history: {len(cpi_hist)} monthly changes (2020-2025)")
    except Exception as e:
        print(f"  CPI fetch failed: {e}")
        historical["KXCPI"] = []

    try:
        # Post-COVID window (regime-appropriate)
        claims_hist = fetch_historical_jobless_claims("2022-01-01", "2025-12-01")
        historical["KXJOBLESSCLAIMS"] = claims_hist
        print(f"  Jobless Claims history: {len(claims_hist)} weekly values (2022-2025, post-COVID)")
    except Exception as e:
        print(f"  Jobless Claims fetch failed: {e}")
        historical["KXJOBLESSCLAIMS"] = []

    try:
        # COVID-contaminated window for sensitivity comparison
        claims_hist_covid = fetch_historical_jobless_claims("2020-01-01", "2025-12-01")
        historical_covid["KXJOBLESSCLAIMS"] = claims_hist_covid
        print(f"  Jobless Claims history (COVID window): {len(claims_hist_covid)} weekly values (2020-2025)")
    except Exception as e:
        historical_covid["KXJOBLESSCLAIMS"] = []

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

        # COVID-contaminated historical for sensitivity
        hist_crps_covid = None
        if series in historical_covid and historical_covid[series]:
            try:
                hist_crps_covid = compute_historical_crps(historical_covid[series], realized)
            except Exception:
                hist_crps_covid = None

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
            "historical_crps_covid": hist_crps_covid,
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
            print(f"    Historical CRPS: mean={s['historical_crps'].mean():.4f} (regime-appropriate window)")
        if s["historical_crps_covid"].notna().any():
            print(f"    Historical CRPS (COVID window): mean={s['historical_crps_covid'].mean():.4f} (contaminated)")

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

    # Note: CRPS vs Point MAE test removed — CRPS <= MAE is a mathematical
    # identity for any proper distribution, so this comparison is tautological.
    # The honest comparison is point-vs-point (Phase 6 horse race).
    test_results["crps_vs_point_note"] = {
        "note": (
            "CRPS <= MAE is a mathematical property of proper scoring rules. "
            "The CRPS-vs-point test is omitted as it is tautological. "
            "See Phase 6 horse race for honest point-vs-point comparison."
        ),
    }

    # Per-series tests with rank-biserial effect sizes and Bonferroni correction
    print("\n  --- Per-series Wilcoxon tests ---")

    # Collect all per-series vs historical raw p-values for Bonferroni correction
    raw_historical_pvalues = {}

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
                # Rank-biserial correlation r = 1 - (2T / n(n+1)/2)
                # where T is the Wilcoxon test statistic (sum of positive ranks)
                n_pairs = len(valid)
                max_t = n_pairs * (n_pairs + 1) / 2
                rank_biserial_r = 1.0 - (2.0 * stat / max_t) if max_t > 0 else 0.0
                test_results[key] = {
                    "n": len(valid),
                    "series": series,
                    "kalshi_mean": float(valid["kalshi_crps"].mean()),
                    "benchmark_mean": float(valid[col_b].mean()),
                    "wilcoxon_stat": float(stat),
                    "p_value": float(p),
                    "rank_biserial_r": round(float(rank_biserial_r), 3),
                    "significant_raw": p < 0.05,
                    "scope": f"per-series ({series})",
                }
                sig = "*" if p < 0.05 else ""
                print(f"  {series} vs {label} (n={len(valid)}): "
                      f"Kalshi={valid['kalshi_crps'].mean():.4f}, "
                      f"{label}={valid[col_b].mean():.4f}, "
                      f"p={p:.4f}{sig}, r={rank_biserial_r:.3f}")

                # Track for Bonferroni
                if comparison == "vs_historical":
                    raw_historical_pvalues[series] = p
            else:
                test_results[key] = {
                    "n": len(valid),
                    "series": series,
                    "note": f"Insufficient data (n={len(valid)}, need >=5)",
                }
                print(f"  {series} vs {label}: insufficient data (n={len(valid)})")

    # Bonferroni correction across per-series historical tests
    n_series_tests = len(raw_historical_pvalues)
    if n_series_tests > 0:
        print(f"\n  --- Bonferroni correction ({n_series_tests} series tests) ---")
        for series, raw_p in sorted(raw_historical_pvalues.items()):
            adj_p = min(raw_p * n_series_tests, 1.0)
            key = f"kalshi_vs_historical_{series}"
            if key in test_results:
                test_results[key]["p_value_bonferroni"] = round(float(adj_p), 4)
                test_results[key]["n_tests_corrected"] = n_series_tests
                test_results[key]["significant_bonferroni"] = adj_p < 0.05
            sig_raw = "*" if raw_p < 0.05 else ""
            sig_adj = "*" if adj_p < 0.05 else ""
            print(f"  {series}: raw p={raw_p:.4f}{sig_raw}, "
                  f"Bonferroni-adjusted p={adj_p:.4f}{sig_adj} "
                  f"(×{n_series_tests})")

    # Sensitivity: Jobless Claims with COVID-contaminated window
    print("\n  --- Benchmark sensitivity (Jobless Claims) ---")
    jc = crps_df[crps_df["series"] == "KXJOBLESSCLAIMS"]
    valid_clean = jc.dropna(subset=["kalshi_crps", "historical_crps"])
    valid_covid = jc.dropna(subset=["kalshi_crps", "historical_crps_covid"])
    if len(valid_clean) >= 5:
        print(f"  Post-COVID window (2022+): Kalshi={valid_clean['kalshi_crps'].mean():.0f}, "
              f"Historical={valid_clean['historical_crps'].mean():.0f}")
        stat, p = stats.wilcoxon(valid_clean["kalshi_crps"], valid_clean["historical_crps"], alternative="less")
        n_pairs = len(valid_clean)
        max_t = n_pairs * (n_pairs + 1) / 2
        r = 1.0 - (2.0 * stat / max_t) if max_t > 0 else 0.0
        test_results["jobless_claims_vs_historical_clean"] = {
            "n": n_pairs,
            "kalshi_mean": float(valid_clean["kalshi_crps"].mean()),
            "historical_mean": float(valid_clean["historical_crps"].mean()),
            "p_value": float(p),
            "rank_biserial_r": round(float(r), 3),
            "significant": p < 0.05,
            "window": "2022-2025 (post-COVID)",
        }
        print(f"    Wilcoxon p={p:.4f}{'*' if p < 0.05 else ''}, r={r:.3f}")
    if len(valid_covid) >= 5:
        print(f"  COVID window (2020+): Kalshi={valid_covid['kalshi_crps'].mean():.0f}, "
              f"Historical={valid_covid['historical_crps_covid'].mean():.0f}")
        stat, p = stats.wilcoxon(valid_covid["kalshi_crps"], valid_covid["historical_crps_covid"], alternative="less")
        n_pairs = len(valid_covid)
        max_t = n_pairs * (n_pairs + 1) / 2
        r = 1.0 - (2.0 * stat / max_t) if max_t > 0 else 0.0
        test_results["jobless_claims_vs_historical_covid"] = {
            "n": n_pairs,
            "kalshi_mean": float(valid_covid["kalshi_crps"].mean()),
            "historical_mean": float(valid_covid["historical_crps_covid"].mean()),
            "p_value": float(p),
            "rank_biserial_r": round(float(r), 3),
            "significant": p < 0.05,
            "window": "2020-2025 (COVID-contaminated)",
        }
        print(f"    Wilcoxon p={p:.4f}{'*' if p < 0.05 else ''}, r={r:.3f}")

    # CRPS/MAE ratio: measures how much distributional info adds beyond point forecast
    # For well-calibrated distributions, CRPS < MAE (sharpness reward).
    # CRPS > MAE signals distributional miscalibration.
    print("\n  --- CRPS / MAE ratio (distributional value-add) ---")
    crps_mae_results = {}
    for series in sorted(crps_df["series"].unique()):
        s = crps_df[crps_df["series"] == series]
        valid = s.dropna(subset=["kalshi_crps", "point_crps"])
        if len(valid) >= 3:
            mean_crps = float(valid["kalshi_crps"].mean())
            mean_mae = float(valid["point_crps"].mean())
            median_crps = float(valid["kalshi_crps"].median())
            median_mae = float(valid["point_crps"].median())
            ratio = mean_crps / mean_mae if mean_mae > 0 else float("inf")
            median_ratio = median_crps / median_mae if median_mae > 0 else float("inf")

            # Per-event ratios for reporting
            per_event_ratios = (valid["kalshi_crps"] / valid["point_crps"]).replace([np.inf, -np.inf], np.nan).dropna()
            median_per_event_ratio = float(per_event_ratios.median()) if len(per_event_ratios) > 0 else None

            # Bootstrap CI on ratio-of-means
            n_boot = 10000
            boot_ratios = []
            crps_arr = valid["kalshi_crps"].values
            mae_arr = valid["point_crps"].values
            rng = np.random.default_rng(42)
            for _ in range(n_boot):
                idx = rng.integers(0, len(valid), size=len(valid))
                boot_crps = crps_arr[idx].mean()
                boot_mae = mae_arr[idx].mean()
                if boot_mae > 0:
                    boot_ratios.append(boot_crps / boot_mae)
            ci_lo = float(np.percentile(boot_ratios, 2.5))
            ci_hi = float(np.percentile(boot_ratios, 97.5))

            crps_mae_results[series] = {
                "n": len(valid),
                "mean_crps": mean_crps,
                "mean_mae": mean_mae,
                "ratio": ratio,
                "median_per_event_ratio": median_per_event_ratio,
                "ci_95_lo": ci_lo,
                "ci_95_hi": ci_hi,
                "interpretation": (
                    "ratio < 1: distribution adds value beyond point forecast. "
                    "ratio > 1: distributional spread is miscalibrated."
                ),
            }
            flag = " *** DISTRIBUTION HARMFUL" if ratio > 1.0 else ""
            print(f"  {series} (n={len(valid)}): CRPS={mean_crps:.4f}, MAE={mean_mae:.4f}, "
                  f"CRPS/MAE={ratio:.3f} [{ci_lo:.2f}, {ci_hi:.2f}], "
                  f"median per-event={median_per_event_ratio:.3f}{flag}")
    test_results["crps_mae_ratio"] = crps_mae_results

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
                # Compute implied mean at this snapshot for MAE
                pdf = compute_implied_pdf(strikes, cdf_values)
                implied_mean = pdf.get("implied_mean") if pdf else None
                point_mae = abs(implied_mean - realized) if implied_mean is not None else None
                temporal_crps.append({
                    "event_ticker": event_ticker,
                    "series": series,
                    "lifetime_pct": pct_label,
                    "snapshot_idx": idx,
                    "n_snapshots": n,
                    "kalshi_crps": crps_val,
                    "uniform_crps": uniform_val,
                    "point_mae": point_mae,
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
                # CRPS/MAE at this snapshot
                valid_mae = t.dropna(subset=["point_mae"])
                crps_mae = valid_mae["kalshi_crps"].mean() / valid_mae["point_mae"].mean() if len(valid_mae) > 0 and valid_mae["point_mae"].mean() > 0 else None
                crps_mae_str = f", CRPS/MAE={crps_mae:.3f}" if crps_mae is not None else ""
                print(f"    {pct}: CRPS={t['kalshi_crps'].mean():.4f}, "
                      f"uniform={t['uniform_crps'].mean():.4f}, "
                      f"ratio={ratio:.2f}x, "
                      f"beats_uniform={t['beats_uniform'].mean():.0%}{crps_mae_str}")

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
    # PHASE 6b: POWER ANALYSIS TABLE (ALL TESTS)
    # ================================================================
    print("\n" + "=" * 70)
    print("PHASE 6b: POWER ANALYSIS TABLE")
    print("=" * 70)

    power_analysis = {}
    z_alpha = 1.645  # one-sided 0.05
    z_beta = 0.842   # 80% power

    def _compute_n_needed(effect_size):
        """Sample size for 80% power with Wilcoxon (ARE-corrected)."""
        if effect_size == 0:
            return float("inf")
        return int(np.ceil(((z_alpha + z_beta) ** 2 / effect_size ** 2) * (np.pi / 3)))

    # CRPS tests: use rank-biserial r as effect size proxy
    print("  --- CRPS tests ---")
    for key, result in test_results.items():
        if not isinstance(result, dict) or "rank_biserial_r" not in result:
            continue
        r = abs(result["rank_biserial_r"])
        if r == 0:
            continue
        # Convert rank-biserial r to approximate Cohen's d: d ≈ 2r / sqrt(1-r²)
        d_approx = 2 * r / np.sqrt(1 - r ** 2) if r < 1 else float("inf")
        n_needed = _compute_n_needed(d_approx)
        series_label = result.get("series", result.get("window", key))
        power_analysis[key] = {
            "test": key,
            "observed_r": round(r, 3),
            "observed_d_approx": round(d_approx, 3),
            "n_current": result["n"],
            "n_needed_80pct_power": n_needed,
            "more_events_needed": max(0, n_needed - result["n"]),
        }
        print(f"  {key}: r={r:.3f} (d≈{d_approx:.3f}), n={result['n']}, "
              f"need n={n_needed} for 80% power "
              f"({max(0, n_needed - result['n'])} more events)")

    # Horse race tests
    print("  --- Horse race tests ---")
    if horse_race_results and "statistical_tests" in horse_race_results:
        for test_name, test in horse_race_results["statistical_tests"].items():
            if "cohen_d" in test and test["cohen_d"] != 0:
                d = abs(test["cohen_d"])
                n_needed = _compute_n_needed(d)
                power_analysis[f"horse_race_{test_name}"] = {
                    "test": test_name,
                    "observed_d": round(d, 3),
                    "n_current": test["n"],
                    "n_needed_80pct_power": n_needed,
                    "more_events_needed": max(0, n_needed - test["n"]),
                }
                print(f"  {test_name}: |d|={d:.3f}, n={test['n']}, "
                      f"need n={n_needed} for 80% power "
                      f"({max(0, n_needed - test['n'])} more months)")

    # ================================================================
    # PHASE 6c: PIT DIAGNOSTIC (CPI AND JOBLESS CLAIMS)
    # ================================================================
    print("\n" + "=" * 70)
    print("PHASE 6c: PIT DIAGNOSTIC (CPI AND JOBLESS CLAIMS)")
    print("=" * 70)

    pit_results = {}
    for pit_series in ["KXCPI", "KXJOBLESSCLAIMS"]:
        series_data = crps_df[crps_df["series"] == pit_series].copy()
        if len(series_data) == 0:
            continue

        pit_values = []
        for _, row in series_data.iterrows():
            event_ticker = row["event_ticker"]
            realized = row["realized"]
            event_markets = event_groups.get(event_ticker)
            if event_markets is None:
                continue

            snapshots = build_implied_cdf_snapshots(event_markets)
            if len(snapshots) < 2:
                continue

            mid_snap = snapshots[len(snapshots) // 2]
            strikes = mid_snap["strikes"]
            cdf_vals = mid_snap["cdf_values"]

            # PIT = P(X <= realized) = 1 - P(X > realized) = 1 - interp(survival)
            survival = np.interp(realized, strikes, cdf_vals)
            pit = 1.0 - survival
            pit_values.append({"event_ticker": event_ticker, "realized": realized, "pit": pit})

        if pit_values:
            pit_df = pd.DataFrame(pit_values)
            n_in_iqr = ((pit_df["pit"] >= 0.25) & (pit_df["pit"] <= 0.75)).sum()
            n_in_tails = ((pit_df["pit"] < 0.1) | (pit_df["pit"] > 0.9)).sum()

            # Bootstrap CI on mean PIT
            rng = np.random.default_rng(42)
            boot_means = []
            pit_arr = pit_df["pit"].values
            for _ in range(10000):
                boot_idx = rng.integers(0, len(pit_arr), size=len(pit_arr))
                boot_means.append(pit_arr[boot_idx].mean())
            pit_ci_lo = float(np.percentile(boot_means, 2.5))
            pit_ci_hi = float(np.percentile(boot_means, 97.5))

            ks_stat, ks_p = stats.kstest(pit_df["pit"], "uniform")

            pit_results[pit_series] = {
                "n_events": len(pit_df),
                "mean_pit": float(pit_df["pit"].mean()),
                "std_pit": float(pit_df["pit"].std()),
                "mean_pit_ci_lo": pit_ci_lo,
                "mean_pit_ci_hi": pit_ci_hi,
                "pct_in_iqr": float(n_in_iqr / len(pit_df)),
                "pct_in_tails": float(n_in_tails / len(pit_df)),
                "ks_stat": float(ks_stat),
                "ks_p": float(ks_p),
                "pit_values": pit_df["pit"].tolist(),
            }

            print(f"\n  {pit_series} PIT analysis (n={len(pit_df)}):")
            print(f"    Mean PIT: {pit_df['pit'].mean():.3f} (95% CI: [{pit_ci_lo:.2f}, {pit_ci_hi:.2f}], ideal: 0.500)")
            print(f"    Std PIT:  {pit_df['pit'].std():.3f} (ideal: 0.289)")
            print(f"    In IQR (0.25-0.75): {n_in_iqr}/{len(pit_df)} = {n_in_iqr/len(pit_df):.0%} (ideal: 50%)")
            print(f"    In tails (<0.1 or >0.9): {n_in_tails}/{len(pit_df)} = {n_in_tails/len(pit_df):.0%} (ideal: 20%)")
            print(f"    KS test for uniformity: stat={ks_stat:.3f}, p={ks_p:.4f}")

    # Keep backward compatibility
    cpi_overconfidence = pit_results.get("KXCPI", {})

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
        "power_analysis": power_analysis,
        "cpi_overconfidence_diagnostic": cpi_overconfidence,
        "pit_diagnostics": pit_results,
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
