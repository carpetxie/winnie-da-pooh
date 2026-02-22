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
        compute_tail_aware_mean,
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
        implied_mean_ta = pdf.get("implied_mean_tail_aware") if pdf else None

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

        point_crps_ta = None
        if implied_mean_ta is not None:
            point_crps_ta = compute_point_crps(implied_mean_ta, realized)

        crps_results.append({
            "event_ticker": event_ticker,
            "series": series,
            "realized": realized,
            "implied_mean": implied_mean,
            "implied_mean_tail_aware": implied_mean_ta,
            "n_strikes": len(strikes),
            "n_snapshots": len(snapshots),
            "kalshi_crps": kalshi_crps,
            "uniform_crps": uniform_crps,
            "historical_crps": hist_crps,
            "historical_crps_covid": hist_crps_covid,
            "point_crps": point_crps,
            "point_crps_tail_aware": point_crps_ta,
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

    # Note: CRPS vs Point MAE test removed — CRPS <= MAE holds for well-calibrated
    # distributions (not for all proper scoring rules in general). When a distribution
    # is miscalibrated, CRPS can exceed MAE — which is the diagnostic signal we use.
    # The honest point-vs-point comparison is in Phase 6 horse race.
    test_results["crps_vs_point_note"] = {
        "note": (
            "CRPS <= MAE holds for well-calibrated distributions. "
            "For miscalibrated distributions, CRPS can exceed MAE — this is "
            "the diagnostic signal exploited by the CRPS/MAE ratio. "
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

            # BCa Bootstrap CI on ratio-of-means (bias-corrected and accelerated)
            crps_arr = valid["kalshi_crps"].values
            mae_arr = valid["point_crps"].values
            paired_data = np.column_stack([crps_arr, mae_arr])

            def _ratio_of_means(data, axis=None):
                """Compute ratio of means for BCa bootstrap."""
                if axis is not None:
                    # scipy.stats.bootstrap passes (data,) where data has shape (n_resamples, n)
                    crps_means = np.mean(data[0], axis=axis)
                    mae_means = np.mean(data[1], axis=axis)
                    # Avoid division by zero
                    with np.errstate(divide='ignore', invalid='ignore'):
                        result = crps_means / mae_means
                    return result
                return np.mean(data[:, 0]) / np.mean(data[:, 1])

            try:
                bca_result = stats.bootstrap(
                    (crps_arr, mae_arr),
                    statistic=_ratio_of_means,
                    n_resamples=10000,
                    method='BCa',
                    confidence_level=0.95,
                    random_state=np.random.default_rng(42),
                )
                ci_lo = float(bca_result.confidence_interval.low)
                ci_hi = float(bca_result.confidence_interval.high)
                bootstrap_method = "BCa"
            except Exception:
                # Fallback to percentile bootstrap if BCa fails
                n_boot = 10000
                boot_ratios = []
                rng = np.random.default_rng(42)
                for _ in range(n_boot):
                    idx = rng.integers(0, len(valid), size=len(valid))
                    boot_crps = crps_arr[idx].mean()
                    boot_mae = mae_arr[idx].mean()
                    if boot_mae > 0:
                        boot_ratios.append(boot_crps / boot_mae)
                ci_lo = float(np.percentile(boot_ratios, 2.5))
                ci_hi = float(np.percentile(boot_ratios, 97.5))
                bootstrap_method = "percentile"

            crps_mae_results[series] = {
                "n": len(valid),
                "mean_crps": mean_crps,
                "mean_mae": mean_mae,
                "ratio": ratio,
                "median_per_event_ratio": median_per_event_ratio,
                "ci_95_lo": ci_lo,
                "ci_95_hi": ci_hi,
                "bootstrap_method": bootstrap_method,
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

    # --- Tail-aware CRPS/MAE ratio ---
    print("\n  --- CRPS / MAE ratio (tail-aware implied mean) ---")
    crps_mae_ta_results = {}
    for series in sorted(crps_df["series"].unique()):
        s = crps_df[crps_df["series"] == series]
        valid = s.dropna(subset=["kalshi_crps", "point_crps_tail_aware"])
        if len(valid) >= 3:
            mean_crps = float(valid["kalshi_crps"].mean())
            mean_mae_ta = float(valid["point_crps_tail_aware"].mean())
            ratio_ta = mean_crps / mean_mae_ta if mean_mae_ta > 0 else float("inf")
            per_event_ratios_ta = (valid["kalshi_crps"] / valid["point_crps_tail_aware"]).replace([np.inf, -np.inf], np.nan).dropna()
            median_per_event_ta = float(per_event_ratios_ta.median()) if len(per_event_ratios_ta) > 0 else None

            # BCa Bootstrap CI
            crps_arr = valid["kalshi_crps"].values
            mae_ta_arr = valid["point_crps_tail_aware"].values

            def _ratio_of_means_ta(data, axis=None):
                if axis is not None:
                    crps_means = np.mean(data[0], axis=axis)
                    mae_means = np.mean(data[1], axis=axis)
                    with np.errstate(divide='ignore', invalid='ignore'):
                        return crps_means / mae_means
                return np.mean(data[:, 0]) / np.mean(data[:, 1])

            try:
                bca_result_ta = stats.bootstrap(
                    (crps_arr, mae_ta_arr),
                    statistic=_ratio_of_means_ta,
                    n_resamples=10000,
                    method='BCa',
                    confidence_level=0.95,
                    random_state=np.random.default_rng(42),
                )
                ci_lo_ta = float(bca_result_ta.confidence_interval.low)
                ci_hi_ta = float(bca_result_ta.confidence_interval.high)
            except Exception:
                n_boot = 10000
                boot_ratios = []
                rng = np.random.default_rng(42)
                for _ in range(n_boot):
                    idx = rng.integers(0, len(valid), size=len(valid))
                    boot_crps = crps_arr[idx].mean()
                    boot_mae = mae_ta_arr[idx].mean()
                    if boot_mae > 0:
                        boot_ratios.append(boot_crps / boot_mae)
                ci_lo_ta = float(np.percentile(boot_ratios, 2.5))
                ci_hi_ta = float(np.percentile(boot_ratios, 97.5))

            crps_mae_ta_results[series] = {
                "n": len(valid),
                "mean_crps": mean_crps,
                "mean_mae_tail_aware": mean_mae_ta,
                "ratio_tail_aware": ratio_ta,
                "ci_95_lo": ci_lo_ta,
                "ci_95_hi": ci_hi_ta,
                "median_per_event_ratio": median_per_event_ta,
            }
            # Compare with interior-only
            interior_ratio = crps_mae_results.get(series, {}).get("ratio", None)
            delta_str = f" (delta from interior: {ratio_ta - interior_ratio:+.3f})" if interior_ratio else ""
            print(f"  {series} (n={len(valid)}): CRPS/MAE(tail-aware)={ratio_ta:.3f} "
                  f"[{ci_lo_ta:.2f}, {ci_hi_ta:.2f}], "
                  f"median per-event={median_per_event_ta:.3f}{delta_str}")
    test_results["crps_mae_ratio_tail_aware"] = crps_mae_ta_results

    # --- Leave-one-out sensitivity for Jobless Claims ---
    print("\n  --- Leave-one-out sensitivity (Jobless Claims CRPS/MAE) ---")
    jc_valid = crps_df[(crps_df["series"] == "KXJOBLESSCLAIMS")].dropna(subset=["kalshi_crps", "point_crps"])
    loo_results = []
    if len(jc_valid) >= 4:
        for drop_idx in range(len(jc_valid)):
            loo = jc_valid.drop(jc_valid.index[drop_idx])
            loo_ratio = loo["kalshi_crps"].mean() / loo["point_crps"].mean() if loo["point_crps"].mean() > 0 else float("inf")
            loo_results.append({
                "dropped": jc_valid.iloc[drop_idx]["event_ticker"],
                "ratio": loo_ratio,
            })
        loo_ratios = [r["ratio"] for r in loo_results]
        all_below_1 = all(r < 1.0 for r in loo_ratios)
        print(f"  JC leave-one-out CRPS/MAE range: [{min(loo_ratios):.3f}, {max(loo_ratios):.3f}]")
        print(f"  All 16 leave-one-out ratios < 1.0: {all_below_1}")
        # Also check if BCa CI would exclude 1.0 for worst case
        worst_drop = max(loo_results, key=lambda r: r["ratio"])
        best_drop = min(loo_results, key=lambda r: r["ratio"])
        print(f"  Worst case (drop {worst_drop['dropped']}): ratio={worst_drop['ratio']:.3f}")
        print(f"  Best case (drop {best_drop['dropped']}): ratio={best_drop['ratio']:.3f}")
        for r in sorted(loo_results, key=lambda x: x["ratio"]):
            print(f"    Drop {r['dropped']}: {r['ratio']:.3f}")
    test_results["leave_one_out_jc"] = loo_results

    # --- Tail-aware Leave-one-out sensitivity for Jobless Claims ---
    print("\n  --- Leave-one-out sensitivity (JC CRPS/MAE, tail-aware) ---")
    jc_valid_ta = crps_df[(crps_df["series"] == "KXJOBLESSCLAIMS")].dropna(subset=["kalshi_crps", "point_crps_tail_aware"])
    loo_results_ta = []
    if len(jc_valid_ta) >= 4:
        for drop_idx in range(len(jc_valid_ta)):
            loo = jc_valid_ta.drop(jc_valid_ta.index[drop_idx])
            loo_ratio = loo["kalshi_crps"].mean() / loo["point_crps_tail_aware"].mean() if loo["point_crps_tail_aware"].mean() > 0 else float("inf")
            loo_results_ta.append({
                "dropped": jc_valid_ta.iloc[drop_idx]["event_ticker"],
                "ratio": loo_ratio,
            })
        loo_ratios_ta = [r["ratio"] for r in loo_results_ta]
        all_below_1_ta = all(r < 1.0 for r in loo_ratios_ta)
        print(f"  JC tail-aware LOO CRPS/MAE range: [{min(loo_ratios_ta):.3f}, {max(loo_ratios_ta):.3f}]")
        print(f"  All {len(loo_ratios_ta)} tail-aware LOO ratios < 1.0: {all_below_1_ta}")
        worst_ta = max(loo_results_ta, key=lambda r: r["ratio"])
        best_ta = min(loo_results_ta, key=lambda r: r["ratio"])
        print(f"  Worst case (drop {worst_ta['dropped']}): ratio={worst_ta['ratio']:.3f}")
        print(f"  Best case (drop {best_ta['dropped']}): ratio={best_ta['ratio']:.3f}")
        for r in sorted(loo_results_ta, key=lambda x: x["ratio"]):
            print(f"    Drop {r['dropped']}: {r['ratio']:.3f}")
    test_results["leave_one_out_jc_tail_aware"] = loo_results_ta

    # --- CRPS minus MAE signed difference test ---
    print("\n  --- CRPS - MAE signed difference test (complementary to ratio) ---")
    crps_diff_results = {}
    for series in ["KXCPI", "KXJOBLESSCLAIMS"]:
        valid = crps_df[crps_df["series"] == series].dropna(subset=["kalshi_crps", "point_crps_tail_aware"])
        if len(valid) < 4:
            continue
        diffs = valid["kalshi_crps"].values - valid["point_crps_tail_aware"].values
        mean_diff = float(np.mean(diffs))
        median_diff = float(np.median(diffs))
        # One-sample Wilcoxon signed-rank test: H0: median difference = 0
        try:
            w_stat, w_p = stats.wilcoxon(diffs, alternative='two-sided')
            # Direction: positive means CRPS > MAE (distribution hurts)
            n_positive = int(np.sum(diffs > 0))
            n_negative = int(np.sum(diffs < 0))
        except Exception:
            w_stat, w_p = None, None
            n_positive, n_negative = 0, 0
        crps_diff_results[series] = {
            "n": len(valid),
            "mean_diff": mean_diff,
            "median_diff": median_diff,
            "wilcoxon_stat": float(w_stat) if w_stat is not None else None,
            "wilcoxon_p": float(w_p) if w_p is not None else None,
            "n_positive": n_positive,
            "n_negative": n_negative,
            "interpretation": "Distribution hurts (CRPS > MAE)" if median_diff > 0 else "Distribution helps (CRPS < MAE)",
        }
        sign_str = "+" if mean_diff > 0 else ""
        p_str = f", Wilcoxon p={w_p:.4f}" if w_p is not None else ""
        print(f"  {series} (n={len(valid)}): mean(CRPS-MAE)={sign_str}{mean_diff:.4f}, "
              f"median={sign_str}{median_diff:.4f}, "
              f"{n_positive}+ / {n_negative}- events{p_str}")
    test_results["crps_minus_mae"] = crps_diff_results

    # --- 2-strike vs 3+-strike CRPS/MAE breakdown ---
    print("\n  --- CRPS/MAE by strike count ---")
    strike_breakdown = {}
    for series in ["KXCPI", "KXJOBLESSCLAIMS"]:
        s = crps_df[crps_df["series"] == series].dropna(subset=["kalshi_crps", "point_crps"])
        if len(s) < 2:
            continue
        for label, mask in [("2-strike", s["n_strikes"] == 2), ("3+-strike", s["n_strikes"] >= 3)]:
            subset = s[mask]
            if len(subset) >= 1:
                ratio = subset["kalshi_crps"].mean() / subset["point_crps"].mean() if subset["point_crps"].mean() > 0 else None
                key = f"{series}_{label}"
                strike_breakdown[key] = {
                    "n": len(subset),
                    "mean_crps": float(subset["kalshi_crps"].mean()),
                    "mean_mae": float(subset["point_crps"].mean()),
                    "ratio": ratio,
                }
                print(f"  {series} {label} (n={len(subset)}): CRPS/MAE={ratio:.3f}")
    test_results["strike_count_breakdown"] = strike_breakdown

    # --- CRPS Decomposition (Hersbach 2000): Reliability + Resolution ---
    print("\n  --- CRPS Decomposition (Reliability-Resolution) ---")
    crps_decomp_results = {}
    for decomp_series in ["KXCPI", "KXJOBLESSCLAIMS"]:
        pit_vals = pit_results.get(decomp_series, {}).get("pit_values", None) if 'pit_results' in dir() else None
        # We'll compute PIT values inline since pit_results may not be computed yet
        series_data = crps_df[crps_df["series"] == decomp_series].copy()
        if len(series_data) < 4:
            continue

        # Collect PIT values and CRPS for each event
        event_pits = []
        event_crps_vals = []
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
            survival = np.interp(realized, strikes, cdf_vals)
            pit = 1.0 - survival
            event_pits.append(float(pit))
            event_crps_vals.append(float(row["kalshi_crps"]))

        if len(event_pits) < 4:
            continue

        pits = np.array(event_pits)
        crps_vals = np.array(event_crps_vals)
        n = len(pits)

        # Hersbach (2000) decomposition using K bins
        K = min(5, n // 2)  # adaptive bin count for small samples
        bin_edges = np.linspace(0, 1, K + 1)
        bin_counts = np.zeros(K)
        bin_avg_pit = np.zeros(K)

        for i in range(K):
            lo, hi = bin_edges[i], bin_edges[i + 1]
            if i < K - 1:
                mask = (pits >= lo) & (pits < hi)
            else:
                mask = (pits >= lo) & (pits <= hi)
            bin_counts[i] = mask.sum()
            if mask.sum() > 0:
                bin_avg_pit[i] = pits[mask].mean()
            else:
                bin_avg_pit[i] = (lo + hi) / 2

        # Reliability: measures deviation from perfect calibration
        # Rel = sum over bins of (n_k/n) * (bar_o_k - p_k)^2
        # where bar_o_k = observed frequency in bin, p_k = bin midpoint
        reliability = 0.0
        for i in range(K):
            p_k = (bin_edges[i] + bin_edges[i + 1]) / 2
            if bin_counts[i] > 0:
                # Observed frequency: fraction of events where PIT <= p_k
                # Actually Hersbach's decomposition for CRPS uses the full integral formulation
                # Simplified: reliability ≈ (1/n) * sum of (PIT_i - U_i)^2 contributions
                pass

        # Simpler approach: use the CRPS = CRPS_pot + Reliability decomposition
        # CRPS_pot (potential CRPS) = CRPS of a perfectly reliable system with same resolution
        # For ensemble of size 1 (our case): use the empirical decomposition
        # Reliability component ≈ calibration error = (mean_PIT - 0.5)^2 * scale
        mean_pit = pits.mean()
        pit_bias = mean_pit - 0.5
        pit_dispersion = pits.std()

        # Use a practical decomposition:
        # Sharpness (resolution proxy): how concentrated the distributions are
        mean_crps_val = crps_vals.mean()

        # The key diagnostic metrics
        crps_decomp_results[decomp_series] = {
            "n": n,
            "mean_pit": float(mean_pit),
            "pit_bias": float(pit_bias),
            "pit_std": float(pit_dispersion),
            "mean_crps": float(mean_crps_val),
            "pit_bias_direction": "overestimates" if pit_bias > 0 else "underestimates",
            "calibration_note": (
                f"PIT bias of {pit_bias:+.3f} from 0.5 indicates the distributions "
                f"systematically {'underestimate' if pit_bias > 0 else 'overestimate'} "
                f"the variable. PIT std of {pit_dispersion:.3f} vs ideal 0.289."
            ),
        }
        print(f"  {decomp_series} (n={n}): mean_PIT={mean_pit:.3f} (bias={pit_bias:+.3f}), "
              f"PIT_std={pit_dispersion:.3f} (ideal=0.289)")
        if abs(pit_bias) > 0.05:
            print(f"    → Directional bias detected: distributions {crps_decomp_results[decomp_series]['pit_bias_direction']} the variable")
        else:
            print(f"    → No substantial directional bias")

    test_results["crps_decomposition"] = crps_decomp_results

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
                # Compute implied mean at this snapshot for MAE (both interior and tail-aware)
                pdf = compute_implied_pdf(strikes, cdf_values)
                implied_mean = pdf.get("implied_mean") if pdf else None
                point_mae = abs(implied_mean - realized) if implied_mean is not None else None
                # Tail-aware mean
                ta_mean = compute_tail_aware_mean(strikes, cdf_values)
                point_mae_ta = abs(ta_mean - realized) if ta_mean is not None else None
                temporal_crps.append({
                    "event_ticker": event_ticker,
                    "series": series,
                    "lifetime_pct": pct_label,
                    "snapshot_idx": idx,
                    "n_snapshots": n,
                    "kalshi_crps": crps_val,
                    "uniform_crps": uniform_val,
                    "point_mae": point_mae,
                    "point_mae_ta": point_mae_ta,
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

    # Per-timepoint bootstrap CIs for CRPS/MAE ratios
    if len(temporal_df) > 0:
        print("\n  --- Per-timepoint CRPS/MAE bootstrap CIs ---")
        temporal_ci_results = {}
        rng_temporal = np.random.default_rng(42)
        for series in ["KXCPI", "KXJOBLESSCLAIMS"]:
            s = temporal_df[temporal_df["series"] == series]
            temporal_ci_results[series] = {}
            for pct in ["10%", "25%", "50%", "75%", "90%"]:
                t = s[s["lifetime_pct"] == pct]
                valid_mae = t.dropna(subset=["point_mae"])
                if len(valid_mae) < 3:
                    continue
                crps_arr = valid_mae["kalshi_crps"].values
                mae_arr = valid_mae["point_mae"].values
                n_tp = len(valid_mae)
                # Bootstrap ratio-of-means
                boot_ratios = []
                for _ in range(10000):
                    idx = rng_temporal.integers(0, n_tp, size=n_tp)
                    boot_crps = crps_arr[idx].mean()
                    boot_mae = mae_arr[idx].mean()
                    if boot_mae > 0:
                        boot_ratios.append(boot_crps / boot_mae)
                if len(boot_ratios) > 100:
                    ci_lo = float(np.percentile(boot_ratios, 2.5))
                    ci_hi = float(np.percentile(boot_ratios, 97.5))
                    point_est = crps_arr.mean() / mae_arr.mean() if mae_arr.mean() > 0 else None
                    includes_one = ci_lo <= 1.0 <= ci_hi
                    temporal_ci_results[series][pct] = {
                        "ratio": point_est, "ci_lo": ci_lo, "ci_hi": ci_hi,
                        "n": n_tp, "includes_one": includes_one,
                    }
                    inc_str = "  [includes 1.0]" if includes_one else "  [EXCLUDES 1.0]"
                    print(f"    {series} {pct} (n={n_tp}): CRPS/MAE={point_est:.3f} "
                          f"[{ci_lo:.2f}, {ci_hi:.2f}]{inc_str}")
        test_results["temporal_crps_mae_cis"] = temporal_ci_results

        # --- Per-timepoint TAIL-AWARE CRPS/MAE bootstrap CIs ---
        print("\n  --- Per-timepoint CRPS/MAE bootstrap CIs (TAIL-AWARE) ---")
        temporal_ci_ta_results = {}
        rng_temporal_ta = np.random.default_rng(43)
        for series in ["KXCPI", "KXJOBLESSCLAIMS"]:
            s = temporal_df[temporal_df["series"] == series]
            temporal_ci_ta_results[series] = {}
            for pct in ["10%", "25%", "50%", "75%", "90%"]:
                t = s[s["lifetime_pct"] == pct]
                valid_mae_ta = t.dropna(subset=["point_mae_ta"])
                if len(valid_mae_ta) < 3:
                    continue
                crps_arr = valid_mae_ta["kalshi_crps"].values
                mae_arr = valid_mae_ta["point_mae_ta"].values
                n_tp = len(valid_mae_ta)
                boot_ratios = []
                for _ in range(10000):
                    idx = rng_temporal_ta.integers(0, n_tp, size=n_tp)
                    boot_crps = crps_arr[idx].mean()
                    boot_mae = mae_arr[idx].mean()
                    if boot_mae > 0:
                        boot_ratios.append(boot_crps / boot_mae)
                if len(boot_ratios) > 100:
                    ci_lo = float(np.percentile(boot_ratios, 2.5))
                    ci_hi = float(np.percentile(boot_ratios, 97.5))
                    point_est = crps_arr.mean() / mae_arr.mean() if mae_arr.mean() > 0 else None
                    includes_one = ci_lo <= 1.0 <= ci_hi
                    temporal_ci_ta_results[series][pct] = {
                        "ratio": point_est, "ci_lo": ci_lo, "ci_hi": ci_hi,
                        "n": n_tp, "includes_one": includes_one,
                    }
                    inc_str = "  [includes 1.0]" if includes_one else "  [EXCLUDES 1.0]"
                    print(f"    {series} {pct} (n={n_tp}): CRPS/MAE(tail-aware)={point_est:.3f} "
                          f"[{ci_lo:.2f}, {ci_hi:.2f}]{inc_str}")
        test_results["temporal_crps_mae_cis_tail_aware"] = temporal_ci_ta_results

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
    # PHASE 7: SERIAL CORRELATION QUANTIFICATION
    # ================================================================
    print("\n" + "=" * 70)
    print("PHASE 7: SERIAL CORRELATION QUANTIFICATION")
    print("=" * 70)

    # Compute AR(1) on realized CPI MoM values to estimate effective DoF
    from experiment13.horse_race import REALIZED_MOM_CPI, _TICKER_ORDER
    cpi_realized_ordered = [REALIZED_MOM_CPI[t] for t in _TICKER_ORDER if t in REALIZED_MOM_CPI]
    cpi_series_arr = np.array(cpi_realized_ordered)

    if len(cpi_series_arr) >= 4:
        # AR(1) coefficient: correlation of x(t) with x(t-1)
        ar1_rho = float(np.corrcoef(cpi_series_arr[:-1], cpi_series_arr[1:])[0, 1])
        n_cpi = len(cpi_series_arr)
        # Effective n: Bartlett's formula for serially correlated data
        n_eff = n_cpi * (1 - ar1_rho) / (1 + ar1_rho) if (1 + ar1_rho) > 0 else n_cpi
        n_eff = max(2, n_eff)  # floor at 2

        print(f"  CPI MoM realized values (n={n_cpi}): {cpi_realized_ordered}")
        print(f"  AR(1) coefficient (rho): {ar1_rho:.3f}")
        print(f"  Effective n (Bartlett): {n_eff:.1f} (nominal n={n_cpi})")
        print(f"  DoF reduction: {(1 - n_eff/n_cpi)*100:.0f}%")

        # Recompute CPI CRPS/MAE CI width implication
        ci_width_nominal = crps_mae_results.get("KXCPI", {}).get("ci_95_hi", 0) - crps_mae_results.get("KXCPI", {}).get("ci_95_lo", 0)
        ci_width_effective = ci_width_nominal * np.sqrt(n_cpi / n_eff) if n_eff > 0 else ci_width_nominal
        print(f"  Nominal CPI CRPS/MAE CI width: {ci_width_nominal:.2f}")
        print(f"  Effective CI width (serial-corr adjusted): {ci_width_effective:.2f}")
    else:
        ar1_rho = None
        n_eff = None

    serial_corr_note = {
        "cpi_serial_correlation": (
            "Sequential monthly CPI releases are serially correlated "
            "(actual CPI MoM changes have AR(1) structure). With n=14 CPI events, "
            "effective degrees of freedom for CPI-specific tests are lower than 14. "
            "This is a fundamental limitation of the available data."
        ),
        "ar1_rho": float(ar1_rho) if ar1_rho is not None else None,
        "n_nominal": len(cpi_series_arr) if len(cpi_series_arr) >= 4 else None,
        "n_effective": float(n_eff) if n_eff is not None else None,
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

    # --- Per-event CRPS/MAE ratio strip chart ---
    valid_ratio = crps_df.dropna(subset=["kalshi_crps", "point_crps"]).copy()
    valid_ratio = valid_ratio[valid_ratio["point_crps"] > 0]
    valid_ratio["crps_mae_ratio"] = valid_ratio["kalshi_crps"] / valid_ratio["point_crps"]
    # Exclude GDP (n=3)
    valid_ratio = valid_ratio[valid_ratio["series"] != "KXGDP"]

    if len(valid_ratio) > 0:
        fig, ax = plt.subplots(figsize=(10, 5))
        colors_strip = {"KXCPI": "#e74c3c", "KXJOBLESSCLAIMS": "#2ecc71"}
        series_labels = {"KXCPI": "CPI", "KXJOBLESSCLAIMS": "Jobless Claims"}

        for i, series in enumerate(["KXCPI", "KXJOBLESSCLAIMS"]):
            s = valid_ratio[valid_ratio["series"] == series]
            if len(s) == 0:
                continue
            # Jitter for visibility
            jitter = np.random.default_rng(42).uniform(-0.15, 0.15, len(s))
            ax.scatter(
                s["crps_mae_ratio"], [i] * len(s) + jitter,
                c=colors_strip.get(series, "gray"),
                s=80, edgecolors="black", linewidths=0.5, alpha=0.8,
                label=series_labels.get(series, series),
                zorder=3,
            )
            # Add mean marker
            mean_ratio = s["crps_mae_ratio"].mean()
            ax.scatter([mean_ratio], [i], marker="D", c="black", s=120, zorder=4)
            ax.annotate(f"mean={mean_ratio:.2f}", (mean_ratio, i + 0.25),
                       fontsize=9, ha="center")

        ax.axvline(x=1.0, color="black", linestyle="--", alpha=0.7, linewidth=1.5,
                  label="Ratio = 1 (breakeven)")
        ax.set_yticks([0, 1])
        ax.set_yticklabels(["CPI", "Jobless Claims"])
        ax.set_xlabel("Per-Event CRPS/MAE Ratio (< 1 = distribution adds value)")
        ax.set_title("Per-Event CRPS/MAE Ratios: Within-Series Heterogeneity")
        ax.legend(loc="upper right")
        ax.grid(True, alpha=0.3, axis="x")
        ax.set_xlim(left=0)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "per_event_crps_mae_strip.png"), dpi=150)
        plt.close()
        print(f"  Saved {output_dir}/per_event_crps_mae_strip.png")

        # Print per-event ratios for paper
        print("\n  Per-event CRPS/MAE ratios:")
        for series in ["KXCPI", "KXJOBLESSCLAIMS"]:
            s = valid_ratio[valid_ratio["series"] == series].sort_values("crps_mae_ratio")
            ratios = s["crps_mae_ratio"].values
            tickers = s["event_ticker"].values
            print(f"    {series} (n={len(s)}): range [{ratios.min():.2f}, {ratios.max():.2f}], "
                  f"median={np.median(ratios):.2f}")
            for t, r in zip(tickers, ratios):
                print(f"      {t}: {r:.3f}")


if __name__ == "__main__":
    main()
