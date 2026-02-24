"""
Expanded CRPS/MAE analysis across all available series:
- CPI (old + new prefix merged)
- Jobless Claims (KXJOBLESSCLAIMS)
- FED (old + new prefix merged)
- GDP (old + new prefix merged)

This script:
1. Loads all multi-strike markets from targeted_markets.json
2. Uses candle data to build CDFs at mid-life
3. Computes CRPS and MAE for each event
4. Fetches FRED benchmarks for each series
5. Computes CRPS/MAE ratios with bootstrap CIs
6. Reports results suitable for updating the paper
"""
import os
import sys
import json
import re
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from scipy import stats
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from experiment7.implied_distributions import (
    load_targeted_markets,
    extract_strike_markets,
    group_by_event,
    build_implied_cdf_snapshots,
    compute_implied_pdf,
    _parse_expiration_value,
    CANONICAL_SERIES,
)
from experiment12.distributional_calibration import (
    compute_crps,
    compute_uniform_crps,
    compute_historical_crps,
    fetch_historical_cpi_from_fred,
    fetch_historical_jobless_claims,
    fetch_historical_gdp,
    fetch_historical_fed_rate,
)

OUTPUT_DIR = "data/expanded_analysis"


def fetch_all_historical():
    """Fetch historical benchmarks from FRED for all series."""
    historical = {}

    print("Fetching FRED historical data...")

    try:
        cpi_hist = fetch_historical_cpi_from_fred("2020-01-01", "2026-06-01")
        historical["CPI"] = cpi_hist
        print(f"  CPI: {len(cpi_hist)} monthly changes")
    except Exception as e:
        print(f"  CPI fetch failed: {e}")
        historical["CPI"] = []

    try:
        claims_hist = fetch_historical_jobless_claims("2022-01-01", "2026-06-01")
        historical["JOBLESS_CLAIMS"] = claims_hist
        print(f"  Jobless Claims: {len(claims_hist)} weekly values (post-COVID)")
    except Exception as e:
        print(f"  Jobless Claims fetch failed: {e}")
        historical["JOBLESS_CLAIMS"] = []

    try:
        gdp_hist = fetch_historical_gdp("2015-01-01", "2026-06-01")
        historical["GDP"] = gdp_hist
        print(f"  GDP: {len(gdp_hist)} quarterly values")
    except Exception as e:
        print(f"  GDP fetch failed: {e}")
        historical["GDP"] = []

    try:
        fed_hist = fetch_historical_fed_rate("2020-01-01", "2026-06-01")
        historical["FED"] = fed_hist
        print(f"  FED rate: {len(fed_hist)} daily values")
    except Exception as e:
        print(f"  FED rate fetch failed: {e}")
        historical["FED"] = []

    return historical


def compute_crps_for_all_events(event_groups, historical):
    """Compute CRPS/MAE for all events across all series."""
    results = []

    for event_ticker, event_markets in sorted(event_groups.items()):
        series_prefix = event_markets["series_prefix"].iloc[0]
        canonical = event_markets["canonical_series"].iloc[0] if "canonical_series" in event_markets.columns else series_prefix

        exp_val = event_markets["expiration_value"].iloc[0]
        realized = _parse_expiration_value(exp_val, series_prefix)
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

        # Check mid-life CDF monotonicity
        is_monotonic = mid_snap.get("is_monotonic", True)

        try:
            kalshi_crps = compute_crps(strikes, cdf_values, realized)
        except Exception as e:
            print(f"  CRPS failed for {event_ticker}: {e}")
            continue

        pdf = compute_implied_pdf(strikes, cdf_values)
        implied_mean = pdf.get("implied_mean") if pdf else None
        implied_mean_ta = pdf.get("implied_mean_tail_aware") if pdf else None

        # MAE (point forecast error)
        mae_interior = abs(implied_mean - realized) if implied_mean is not None else None
        mae_ta = abs(implied_mean_ta - realized) if implied_mean_ta is not None else None

        # Uniform CRPS
        try:
            uniform_crps = compute_uniform_crps(min(strikes), max(strikes), realized)
        except Exception:
            uniform_crps = None

        # Historical CRPS
        hist_crps = None
        if canonical in historical and historical[canonical]:
            try:
                hist_crps = compute_historical_crps(historical[canonical], realized)
            except Exception:
                hist_crps = None

        results.append({
            "event_ticker": event_ticker,
            "series_prefix": series_prefix,
            "canonical_series": canonical,
            "realized": realized,
            "implied_mean": implied_mean,
            "implied_mean_ta": implied_mean_ta,
            "mae_interior": mae_interior,
            "mae_ta": mae_ta,
            "n_strikes": len(strikes),
            "n_snapshots": len(snapshots),
            "kalshi_crps": kalshi_crps,
            "uniform_crps": uniform_crps,
            "historical_crps": hist_crps,
            "mid_monotonic": is_monotonic,
        })

    return pd.DataFrame(results)


def compute_crps_mae_ratio_with_ci(crps_arr, mae_arr, n_boot=10000, seed=42):
    """Compute CRPS/MAE ratio with BCa bootstrap CI."""
    mean_crps = crps_arr.mean()
    mean_mae = mae_arr.mean()
    ratio = mean_crps / mean_mae if mean_mae > 0 else float("inf")

    def _ratio_of_means(data, axis=None):
        if axis is not None:
            crps_means = np.mean(data[0], axis=axis)
            mae_means = np.mean(data[1], axis=axis)
            with np.errstate(divide='ignore', invalid='ignore'):
                return crps_means / mae_means
            return result
        return np.mean(data[:, 0]) / np.mean(data[:, 1])

    try:
        bca_result = stats.bootstrap(
            (crps_arr, mae_arr),
            statistic=_ratio_of_means,
            n_resamples=n_boot,
            method='BCa',
            confidence_level=0.95,
            random_state=np.random.default_rng(seed),
        )
        ci_lo = float(bca_result.confidence_interval.low)
        ci_hi = float(bca_result.confidence_interval.high)
    except Exception:
        # Fallback to percentile bootstrap
        rng = np.random.default_rng(seed)
        boot_ratios = []
        for _ in range(n_boot):
            idx = rng.integers(0, len(crps_arr), size=len(crps_arr))
            boot_crps = crps_arr[idx].mean()
            boot_mae = mae_arr[idx].mean()
            if boot_mae > 0:
                boot_ratios.append(boot_crps / boot_mae)
        ci_lo = float(np.percentile(boot_ratios, 2.5))
        ci_hi = float(np.percentile(boot_ratios, 97.5))

    return ratio, ci_lo, ci_hi


def analyze_series(df, series_name):
    """Analyze CRPS/MAE for a single canonical series."""
    s = df[df["canonical_series"] == series_name].copy()
    if len(s) < 2:
        return None

    # Interior-only CRPS/MAE
    valid_int = s.dropna(subset=["kalshi_crps", "mae_interior"])
    if len(valid_int) < 2:
        return None

    crps_arr = valid_int["kalshi_crps"].values
    mae_int_arr = valid_int["mae_interior"].values

    ratio_int, ci_lo_int, ci_hi_int = compute_crps_mae_ratio_with_ci(crps_arr, mae_int_arr)

    # Tail-aware CRPS/MAE
    valid_ta = s.dropna(subset=["kalshi_crps", "mae_ta"])
    ratio_ta, ci_lo_ta, ci_hi_ta = None, None, None
    if len(valid_ta) >= 2:
        ratio_ta, ci_lo_ta, ci_hi_ta = compute_crps_mae_ratio_with_ci(
            valid_ta["kalshi_crps"].values, valid_ta["mae_ta"].values
        )

    # Per-event ratios
    per_event_int = (valid_int["kalshi_crps"] / valid_int["mae_interior"]).replace([np.inf, -np.inf], np.nan).dropna()

    # LOO analysis
    loo_ratios = []
    for i in range(len(valid_int)):
        loo_crps = np.delete(crps_arr, i).mean()
        loo_mae = np.delete(mae_int_arr, i).mean()
        if loo_mae > 0:
            loo_ratios.append(loo_crps / loo_mae)

    # Historical CRPS comparison
    valid_hist = s.dropna(subset=["kalshi_crps", "historical_crps"])
    hist_comparison = None
    if len(valid_hist) >= 5:
        stat, p = stats.wilcoxon(
            valid_hist["kalshi_crps"], valid_hist["historical_crps"],
            alternative="less"
        )
        n_pairs = len(valid_hist)
        max_t = n_pairs * (n_pairs + 1) / 2
        r = 1.0 - (2.0 * stat / max_t) if max_t > 0 else 0.0
        hist_comparison = {
            "n": n_pairs,
            "kalshi_mean": float(valid_hist["kalshi_crps"].mean()),
            "hist_mean": float(valid_hist["historical_crps"].mean()),
            "p_value": float(p),
            "rank_biserial_r": round(float(r), 3),
        }

    return {
        "series": series_name,
        "n_events": len(s),
        "n_with_realized": len(valid_int),
        "mean_crps": float(crps_arr.mean()),
        "mean_mae_int": float(mae_int_arr.mean()),
        "ratio_interior": ratio_int,
        "ci_interior": [ci_lo_int, ci_hi_int],
        "ratio_tail_aware": ratio_ta,
        "ci_tail_aware": [ci_lo_ta, ci_hi_ta] if ci_lo_ta is not None else None,
        "median_per_event": float(per_event_int.median()) if len(per_event_int) > 0 else None,
        "loo_ratios": loo_ratios,
        "loo_all_same_side": all(r < 1.0 for r in loo_ratios) or all(r > 1.0 for r in loo_ratios),
        "loo_side": "< 1.0" if all(r < 1.0 for r in loo_ratios) else ("> 1.0" if all(r > 1.0 for r in loo_ratios) else "mixed"),
        "n_strikes_mean": float(s["n_strikes"].mean()),
        "hist_comparison": hist_comparison,
        "prefixes_used": sorted(s["series_prefix"].unique().tolist()),
    }


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=" * 70)
    print("EXPANDED CRPS/MAE ANALYSIS — ALL SERIES")
    print("=" * 70)

    # Load and filter markets
    markets_df = load_targeted_markets()
    strike_df = extract_strike_markets(markets_df)
    event_groups = group_by_event(strike_df)

    print(f"\nTotal: {len(strike_df)} strike markets across {len(event_groups)} events")

    # Show breakdown by canonical series
    if "canonical_series" in strike_df.columns:
        for cs in sorted(strike_df["canonical_series"].unique()):
            sub = strike_df[strike_df["canonical_series"] == cs]
            n_events = sub["event_ticker"].nunique()
            prefixes = sub["series_prefix"].unique()
            print(f"  {cs}: {len(sub)} markets, {n_events} events (prefixes: {list(prefixes)})")

    # Fetch historical benchmarks
    historical = fetch_all_historical()

    # Compute CRPS for all events
    print("\nComputing CRPS for all events...")
    crps_df = compute_crps_for_all_events(event_groups, historical)
    print(f"  Events with CRPS: {len(crps_df)}")

    # Save raw results
    crps_df.to_csv(os.path.join(OUTPUT_DIR, "expanded_crps_per_event.csv"), index=False)

    # Analyze each canonical series
    print("\n" + "=" * 70)
    print("CRPS/MAE RATIOS BY SERIES")
    print("=" * 70)

    all_results = {}
    for series in sorted(crps_df["canonical_series"].unique()):
        result = analyze_series(crps_df, series)
        if result is None:
            print(f"\n  {series}: insufficient data")
            continue

        all_results[series] = result
        r = result

        print(f"\n  {series} (n={r['n_with_realized']}, prefixes={r['prefixes_used']}):")
        print(f"    Mean CRPS: {r['mean_crps']:.4f}")
        print(f"    Mean MAE (interior): {r['mean_mae_int']:.4f}")
        print(f"    CRPS/MAE (interior): {r['ratio_interior']:.3f} [{r['ci_interior'][0]:.2f}, {r['ci_interior'][1]:.2f}]")
        if r["ratio_tail_aware"] is not None:
            print(f"    CRPS/MAE (tail-aware): {r['ratio_tail_aware']:.3f} [{r['ci_tail_aware'][0]:.2f}, {r['ci_tail_aware'][1]:.2f}]")
        print(f"    Median per-event ratio: {r['median_per_event']:.3f}" if r['median_per_event'] else "    Median per-event: N/A")
        print(f"    LOO: all {r['loo_side']} (n={len(r['loo_ratios'])})")
        print(f"    Mean strikes per event: {r['n_strikes_mean']:.1f}")
        if r["hist_comparison"]:
            hc = r["hist_comparison"]
            print(f"    vs Historical: Kalshi={hc['kalshi_mean']:.4f}, Hist={hc['hist_mean']:.4f}, p={hc['p_value']:.4f}, r={hc['rank_biserial_r']:.3f}")

    # Cross-series heterogeneity test
    print("\n" + "=" * 70)
    print("HETEROGENEITY TESTS")
    print("=" * 70)

    # Get per-event ratios for each series with enough data
    series_ratios = {}
    for series in crps_df["canonical_series"].unique():
        s = crps_df[crps_df["canonical_series"] == series].dropna(subset=["kalshi_crps", "mae_interior"])
        ratios = (s["kalshi_crps"] / s["mae_interior"]).replace([np.inf, -np.inf], np.nan).dropna()
        if len(ratios) >= 5:
            series_ratios[series] = ratios.values

    if len(series_ratios) >= 2:
        # Pairwise Mann-Whitney tests
        series_names = sorted(series_ratios.keys())
        print(f"\n  Series with enough data for comparison: {series_names}")

        for i in range(len(series_names)):
            for j in range(i+1, len(series_names)):
                s1, s2 = series_names[i], series_names[j]
                stat, p = stats.mannwhitneyu(series_ratios[s1], series_ratios[s2], alternative="two-sided")
                n1, n2 = len(series_ratios[s1]), len(series_ratios[s2])
                r = 1 - (2 * stat) / (n1 * n2)
                print(f"  {s1} vs {s2}: U-stat={stat:.1f}, p={p:.4f}, r={r:.3f} (n1={n1}, n2={n2})")

        # Kruskal-Wallis test (if 3+ series)
        if len(series_ratios) >= 3:
            groups = [series_ratios[s] for s in series_names]
            kw_stat, kw_p = stats.kruskal(*groups)
            print(f"\n  Kruskal-Wallis test (k={len(groups)}): H={kw_stat:.2f}, p={kw_p:.4f}")

    # Save all results
    output = {
        "timestamp": datetime.now().isoformat(),
        "series_results": {},
        "crps_df_shape": list(crps_df.shape),
    }
    for series, r in all_results.items():
        # Make serializable
        r_clean = {k: v for k, v in r.items() if k != "loo_ratios"}
        r_clean["loo_range"] = [min(r["loo_ratios"]), max(r["loo_ratios"])] if r["loo_ratios"] else None
        output["series_results"][series] = r_clean

    with open(os.path.join(OUTPUT_DIR, "expanded_results.json"), "w") as f:
        json.dump(output, f, indent=2, default=str)

    print(f"\n  Results saved to {OUTPUT_DIR}/")
    print(f"\n{'='*70}")
    print("SUMMARY TABLE")
    print("=" * 70)
    print(f"{'Series':<20} {'n':>4} {'CRPS/MAE':>10} {'95% CI':>20} {'LOO':>8} {'Interpretation'}")
    print("-" * 80)
    for series in sorted(all_results.keys()):
        r = all_results[series]
        ci_str = f"[{r['ci_interior'][0]:.2f}, {r['ci_interior'][1]:.2f}]"
        interp = "Dist adds value" if r["ratio_interior"] < 1.0 else "Dist harmful"
        print(f"{series:<20} {r['n_with_realized']:>4} {r['ratio_interior']:>10.3f} {ci_str:>20} {r['loo_side']:>8} {interp}")


if __name__ == "__main__":
    main()
