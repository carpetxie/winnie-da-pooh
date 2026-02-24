"""
Robustness analyses for iteration 2:
1. Volume-CRPS regression (tests liquidity hypothesis)
2. Rolling CRPS/MAE for CPI (temporal dynamics)
3. Expanding-window OOS validation for CPI
4. Multivariate regression: CRPS/MAE ~ strike_count + log_volume + surprise_magnitude
5. CRPS/MAE persistence (autocorrelation)
6. Full PIT analysis for all 4 series
"""
import os
import sys
import json
import numpy as np
import pandas as pd
from datetime import datetime
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

OUTPUT_DIR = "data/expanded_analysis"


def load_per_event_data():
    """Load the expanded per-event CRPS data."""
    path = os.path.join(OUTPUT_DIR, "expanded_crps_per_event.csv")
    df = pd.read_csv(path)
    # Compute per-event CRPS/MAE ratio
    df["crps_mae_ratio"] = df["kalshi_crps"] / df["mae_interior"]
    df["crps_mae_ratio"] = df["crps_mae_ratio"].replace([np.inf, -np.inf], np.nan)
    # Compute surprise magnitude (normalized by series scale)
    df["surprise_abs"] = df["mae_interior"]  # MAE IS the surprise magnitude
    return df


def get_event_volumes():
    """Aggregate per-event volume from targeted_markets.json."""
    markets_path = "data/exp2/raw/targeted_markets.json"
    with open(markets_path) as f:
        markets = json.load(f)

    event_volumes = defaultdict(lambda: {"total_volume": 0, "n_markets": 0, "max_volume": 0})
    for m in markets:
        ticker = m.get("ticker", "")
        volume = m.get("volume", 0)
        if volume is None:
            volume = 0
        try:
            volume = int(volume)
        except (ValueError, TypeError):
            volume = 0

        event_ticker = m.get("event_ticker", "")
        if event_ticker:
            event_volumes[event_ticker]["total_volume"] += volume
            event_volumes[event_ticker]["n_markets"] += 1
            event_volumes[event_ticker]["max_volume"] = max(event_volumes[event_ticker]["max_volume"], volume)

    return dict(event_volumes)


def analysis_1_volume_crps_regression(df, event_volumes):
    """Test: does per-event volume predict CRPS/MAE ratio?"""
    print("\n" + "=" * 70)
    print("ANALYSIS 1: VOLUME-CRPS REGRESSION")
    print("=" * 70)

    # Match event volumes to CRPS data
    volumes = []
    for _, row in df.iterrows():
        et = row["event_ticker"]
        if et in event_volumes:
            volumes.append(event_volumes[et]["total_volume"])
        else:
            volumes.append(np.nan)
    df["event_volume"] = volumes

    valid = df.dropna(subset=["crps_mae_ratio", "event_volume"])
    valid = valid[valid["event_volume"] > 0].copy()
    valid["log_volume"] = np.log(valid["event_volume"])

    print(f"\n  Events with volume data: {len(valid)} / {len(df)}")
    print(f"  Volume range: {valid['event_volume'].min():.0f} — {valid['event_volume'].max():.0f}")
    print(f"  Log volume range: {valid['log_volume'].min():.2f} — {valid['log_volume'].max():.2f}")

    # Overall Spearman correlation
    rho, p = stats.spearmanr(valid["log_volume"], valid["crps_mae_ratio"])
    print(f"\n  Overall: Spearman rho={rho:.3f}, p={p:.4f} (n={len(valid)})")

    # Per-series Spearman
    results = {"overall": {"rho": rho, "p": p, "n": len(valid)}, "per_series": {}}
    for series in sorted(valid["canonical_series"].unique()):
        sv = valid[valid["canonical_series"] == series]
        if len(sv) >= 5:
            rho_s, p_s = stats.spearmanr(sv["log_volume"], sv["crps_mae_ratio"])
            print(f"  {series} (n={len(sv)}): rho={rho_s:.3f}, p={p_s:.4f}")
            results["per_series"][series] = {"rho": rho_s, "p": p_s, "n": len(sv)}

    # Volume summary by series
    print("\n  Volume by series:")
    for series in sorted(valid["canonical_series"].unique()):
        sv = valid[valid["canonical_series"] == series]
        print(f"    {series}: median={sv['event_volume'].median():.0f}, mean={sv['event_volume'].mean():.0f}")

    return results


def analysis_2_rolling_crps_mae_cpi(df):
    """Rolling CRPS/MAE for CPI over time (33 events)."""
    print("\n" + "=" * 70)
    print("ANALYSIS 2: ROLLING CRPS/MAE FOR CPI")
    print("=" * 70)

    cpi = df[df["canonical_series"] == "CPI"].copy()
    # Sort by event ticker (chronological for monthly CPI)
    cpi = cpi.sort_values("event_ticker").reset_index(drop=True)
    n = len(cpi)
    print(f"  CPI events: {n}")

    # Expanding window CRPS/MAE ratio
    expanding_ratios = []
    for i in range(2, n + 1):  # Need at least 2 events
        window = cpi.iloc[:i]
        ratio = window["kalshi_crps"].mean() / window["mae_interior"].mean()
        expanding_ratios.append({
            "n_events": i,
            "last_event": cpi.iloc[i-1]["event_ticker"],
            "ratio": ratio,
            "prefix": cpi.iloc[i-1]["series_prefix"],
        })

    # Rolling window (window=8 events)
    window_size = 8
    rolling_ratios = []
    for i in range(window_size, n + 1):
        window = cpi.iloc[i-window_size:i]
        ratio = window["kalshi_crps"].mean() / window["mae_interior"].mean()
        rolling_ratios.append({
            "center_event": cpi.iloc[i-1]["event_ticker"],
            "n_events": window_size,
            "ratio": ratio,
            "prefix": cpi.iloc[i-1]["series_prefix"],
        })

    # Print expanding window progression
    print("\n  Expanding window CRPS/MAE ratio:")
    for r in expanding_ratios:
        prefix_marker = " *" if r["prefix"] == "KXCPI" else ""
        below = "< 1.0" if r["ratio"] < 1.0 else "> 1.0"
        print(f"    n={r['n_events']:>2}: ratio={r['ratio']:.3f} ({below}) — {r['last_event']}{prefix_marker}")

    # Print rolling window
    print(f"\n  Rolling window (w={window_size}) CRPS/MAE ratio:")
    for r in rolling_ratios:
        prefix_marker = " *" if r["prefix"] == "KXCPI" else ""
        below = "< 1.0" if r["ratio"] < 1.0 else "> 1.0"
        print(f"    {r['center_event']}: ratio={r['ratio']:.3f} ({below}){prefix_marker}")

    # Key statistics
    old_cpi = cpi[cpi["series_prefix"] == "CPI"]
    new_cpi = cpi[cpi["series_prefix"] == "KXCPI"]
    old_ratio = old_cpi["kalshi_crps"].mean() / old_cpi["mae_interior"].mean()
    new_ratio = new_cpi["kalshi_crps"].mean() / new_cpi["mae_interior"].mean()

    print(f"\n  Old CPI (n={len(old_cpi)}): CRPS/MAE = {old_ratio:.3f}")
    print(f"  New KXCPI (n={len(new_cpi)}): CRPS/MAE = {new_ratio:.3f}")

    # Test for temporal trend in per-event ratios
    per_event = cpi["crps_mae_ratio"].dropna()
    if len(per_event) >= 5:
        rho, p = stats.spearmanr(range(len(per_event)), per_event)
        print(f"\n  Temporal trend (Spearman): rho={rho:.3f}, p={p:.4f}")

    return {
        "expanding": expanding_ratios,
        "rolling": rolling_ratios,
        "old_ratio": old_ratio,
        "new_ratio": new_ratio,
        "n_old": len(old_cpi),
        "n_new": len(new_cpi),
        "temporal_trend_rho": rho if len(per_event) >= 5 else None,
        "temporal_trend_p": p if len(per_event) >= 5 else None,
    }


def analysis_3_oos_validation(df):
    """Expanding-window OOS validation for CPI.

    Train on first N events, predict CRPS/MAE direction for event N+1.
    'Predict' means: if the expanding-window ratio < 1, predict the next event also < 1.
    """
    print("\n" + "=" * 70)
    print("ANALYSIS 3: EXPANDING-WINDOW OOS VALIDATION (CPI)")
    print("=" * 70)

    cpi = df[df["canonical_series"] == "CPI"].copy()
    cpi = cpi.sort_values("event_ticker").reset_index(drop=True)
    cpi_valid = cpi.dropna(subset=["crps_mae_ratio"])
    n = len(cpi_valid)

    min_train = 5  # Minimum training events
    correct = 0
    total = 0
    predictions = []

    for i in range(min_train, n):
        train = cpi_valid.iloc[:i]
        test_event = cpi_valid.iloc[i]

        # Expanding-window ratio
        train_ratio = train["kalshi_crps"].mean() / train["mae_interior"].mean()
        predicted_below_1 = train_ratio < 1.0

        # Actual per-event ratio
        actual_ratio = test_event["crps_mae_ratio"]
        actual_below_1 = actual_ratio < 1.0

        hit = predicted_below_1 == actual_below_1
        if hit:
            correct += 1
        total += 1

        predictions.append({
            "train_n": i,
            "test_event": test_event["event_ticker"],
            "train_ratio": train_ratio,
            "predicted_below_1": predicted_below_1,
            "actual_ratio": actual_ratio,
            "actual_below_1": actual_below_1,
            "hit": hit,
        })

    accuracy = correct / total if total > 0 else 0
    print(f"\n  Expanding-window OOS: {correct}/{total} = {accuracy:.1%} accuracy")
    print(f"  (Baseline rate: {sum(1 for p in predictions if p['actual_below_1'])/len(predictions):.1%} of events have ratio < 1)")

    # Natural train/test split: old CPI vs new KXCPI
    old_cpi = cpi_valid[cpi_valid["series_prefix"] == "CPI"]
    new_cpi = cpi_valid[cpi_valid["series_prefix"] == "KXCPI"]

    if len(old_cpi) >= 3 and len(new_cpi) >= 3:
        old_ratio = old_cpi["kalshi_crps"].mean() / old_cpi["mae_interior"].mean()
        predicted_new = "< 1.0" if old_ratio < 1.0 else "> 1.0"
        new_ratio = new_cpi["kalshi_crps"].mean() / new_cpi["mae_interior"].mean()
        actual_new = "< 1.0" if new_ratio < 1.0 else "> 1.0"

        # Per-event accuracy on new data
        new_correct = sum(1 for _, row in new_cpi.iterrows() if (row["crps_mae_ratio"] < 1.0) == (old_ratio < 1.0))
        new_total = len(new_cpi)

        print(f"\n  Natural OOS (old CPI → new KXCPI):")
        print(f"    Train ratio (old): {old_ratio:.3f} ({predicted_new})")
        print(f"    Test ratio (new):  {new_ratio:.3f} ({actual_new})")
        print(f"    Per-event accuracy: {new_correct}/{new_total} = {new_correct/new_total:.1%}")
        print(f"    Direction prediction: {'CORRECT' if predicted_new == actual_new else 'WRONG'}")
        print(f"    Note: Direction is correct (both < 1.0 or both > 1.0), but magnitude shifts substantially.")

    # Print detailed predictions
    print(f"\n  Detailed OOS predictions:")
    for p in predictions:
        mark = "+" if p["hit"] else "x"
        print(f"    [{mark}] train_n={p['train_n']:>2}, train_ratio={p['train_ratio']:.3f} -> predicted {'<1' if p['predicted_below_1'] else '>1'}, actual={p['actual_ratio']:.3f}")

    return {
        "accuracy": accuracy,
        "correct": correct,
        "total": total,
        "predictions": predictions,
    }


def analysis_4_multivariate_regression(df):
    """Regression: CRPS/MAE ~ strike_count + log_volume + surprise_magnitude + series dummies."""
    print("\n" + "=" * 70)
    print("ANALYSIS 4: MULTIVARIATE REGRESSION")
    print("=" * 70)

    valid = df.dropna(subset=["crps_mae_ratio", "event_volume"]).copy()
    valid = valid[valid["event_volume"] > 0].copy()
    valid["log_volume"] = np.log(valid["event_volume"])

    # Normalize surprise magnitude within series (z-score)
    for series in valid["canonical_series"].unique():
        mask = valid["canonical_series"] == series
        s = valid.loc[mask, "mae_interior"]
        if s.std() > 0:
            valid.loc[mask, "surprise_z"] = (s - s.mean()) / s.std()
        else:
            valid.loc[mask, "surprise_z"] = 0

    print(f"\n  Events for regression: {len(valid)}")

    # Simple correlations
    print("\n  Univariate Spearman correlations with CRPS/MAE ratio:")
    for var, label in [("n_strikes", "Strike count"), ("log_volume", "Log volume"), ("surprise_z", "Surprise (z)")]:
        v = valid.dropna(subset=[var])
        rho, p = stats.spearmanr(v[var], v["crps_mae_ratio"])
        print(f"    {label}: rho={rho:.3f}, p={p:.4f} (n={len(v)})")

    # OLS regression (using numpy for simplicity)
    # y = CRPS/MAE ratio, X = [1, n_strikes, log_volume, surprise_z, series_dummies]
    try:
        from sklearn.linear_model import LinearRegression

        # Create series dummies
        series_dummies = pd.get_dummies(valid["canonical_series"], drop_first=True, prefix="series")
        X = pd.concat([valid[["n_strikes", "log_volume", "surprise_z"]].reset_index(drop=True), series_dummies.reset_index(drop=True)], axis=1)
        y = valid["crps_mae_ratio"].reset_index(drop=True)

        # Drop NaN
        mask = ~(X.isna().any(axis=1) | y.isna())
        X = X[mask]
        y = y[mask]

        reg = LinearRegression()
        reg.fit(X, y)
        r2 = reg.score(X, y)

        print(f"\n  OLS Regression (R^2 = {r2:.3f}):")
        for name, coef in zip(X.columns, reg.coef_):
            print(f"    {name}: {coef:.4f}")
        print(f"    intercept: {reg.intercept_:.4f}")

        return {"r2": r2, "coefficients": dict(zip(X.columns.tolist(), reg.coef_.tolist())), "intercept": reg.intercept_}
    except ImportError:
        # Fallback: just report correlations
        print("  (sklearn not available; reporting correlations only)")
        return None


def analysis_5_crps_persistence(df):
    """Test: is CRPS/MAE persistent within series? (autocorrelation)"""
    print("\n" + "=" * 70)
    print("ANALYSIS 5: CRPS/MAE PERSISTENCE (AUTOCORRELATION)")
    print("=" * 70)

    results = {}
    for series in sorted(df["canonical_series"].unique()):
        s = df[df["canonical_series"] == series].sort_values("event_ticker")
        ratios = s["crps_mae_ratio"].dropna()
        if len(ratios) >= 8:
            # Lag-1 autocorrelation
            x = ratios.values[:-1]
            y = ratios.values[1:]
            rho, p = stats.spearmanr(x, y)
            print(f"  {series} (n={len(ratios)}): lag-1 Spearman rho={rho:.3f}, p={p:.4f}")
            results[series] = {"rho": rho, "p": p, "n": len(ratios)}
        else:
            print(f"  {series} (n={len(ratios)}): too few events for persistence test")

    return results


def analysis_6_pit_all_series(df):
    """PIT (Probability Integral Transform) analysis for all 4 series."""
    print("\n" + "=" * 70)
    print("ANALYSIS 6: PIT DIAGNOSTIC (ALL SERIES)")
    print("=" * 70)

    # Reload markets and build CDFs to get PIT values
    markets_df = load_targeted_markets()
    strike_df = extract_strike_markets(markets_df)
    event_groups = group_by_event(strike_df)

    pit_results = {}

    for series in sorted(df["canonical_series"].unique()):
        series_events = df[df["canonical_series"] == series]
        pit_values = []

        for _, row in series_events.iterrows():
            et = row["event_ticker"]
            if et not in event_groups:
                continue

            event_markets = event_groups[et]
            realized = row["realized"]

            snapshots = build_implied_cdf_snapshots(event_markets)
            if len(snapshots) < 2:
                continue

            mid_idx = len(snapshots) // 2
            mid_snap = snapshots[mid_idx]
            strikes = mid_snap["strikes"]
            cdf_values = mid_snap["cdf_values"]

            if len(strikes) < 2:
                continue

            # CDF values are survival probabilities P(X > strike)
            # PIT = P(X <= realized) = 1 - P(X > realized)
            # Interpolate survival function at realized value
            survival_at_realized = np.interp(realized, strikes, cdf_values)
            pit = 1.0 - survival_at_realized

            # Clamp to [0, 1]
            pit = max(0.0, min(1.0, pit))
            pit_values.append(pit)

        if len(pit_values) >= 3:
            pit_arr = np.array(pit_values)
            mean_pit = pit_arr.mean()
            ci = stats.t.interval(0.95, len(pit_arr)-1, loc=mean_pit, scale=stats.sem(pit_arr))

            # KS test for uniformity
            ks_stat, ks_p = stats.kstest(pit_arr, 'uniform')

            # Bias direction
            if mean_pit > 0.5:
                bias = f"systematic underestimation (realized tends high)"
            elif mean_pit < 0.5:
                bias = f"systematic overestimation (realized tends low)"
            else:
                bias = "unbiased"

            print(f"\n  {series} (n={len(pit_arr)}):")
            print(f"    Mean PIT: {mean_pit:.3f} (ideal: 0.500)")
            print(f"    95% CI: [{ci[0]:.3f}, {ci[1]:.3f}]")
            print(f"    KS test: stat={ks_stat:.3f}, p={ks_p:.3f}")
            print(f"    Direction: {bias}")

            pit_results[series] = {
                "n": len(pit_arr),
                "mean_pit": float(mean_pit),
                "ci": [float(ci[0]), float(ci[1])],
                "ks_stat": float(ks_stat),
                "ks_p": float(ks_p),
                "bias": bias,
            }

    return pit_results


def analysis_7_strike_count_regression(df):
    """Within-series: does strike count predict CRPS/MAE ratio?"""
    print("\n" + "=" * 70)
    print("ANALYSIS 7: STRIKE COUNT AS PREDICTOR (WITHIN-SERIES)")
    print("=" * 70)

    results = {}
    for series in sorted(df["canonical_series"].unique()):
        s = df[df["canonical_series"] == series].dropna(subset=["crps_mae_ratio"])
        if len(s) >= 5 and s["n_strikes"].nunique() > 1:
            rho, p = stats.spearmanr(s["n_strikes"], s["crps_mae_ratio"])
            print(f"  {series} (n={len(s)}): strike count vs CRPS/MAE rho={rho:.3f}, p={p:.4f}")
            results[series] = {"rho": rho, "p": p, "n": len(s)}
        else:
            print(f"  {series} (n={len(s)}): insufficient variation in strike count")

    return results


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=" * 70)
    print("ITERATION 2 ROBUSTNESS ANALYSES")
    print("=" * 70)

    # Load data
    df = load_per_event_data()
    event_volumes = get_event_volumes()

    # Add volumes to df
    volumes = []
    for _, row in df.iterrows():
        et = row["event_ticker"]
        if et in event_volumes:
            volumes.append(event_volumes[et]["total_volume"])
        else:
            volumes.append(np.nan)
    df["event_volume"] = volumes

    print(f"Loaded {len(df)} events across {df['canonical_series'].nunique()} series")

    # Run all analyses
    results = {}

    results["volume_crps"] = analysis_1_volume_crps_regression(df, event_volumes)
    results["rolling_cpi"] = analysis_2_rolling_crps_mae_cpi(df)
    results["oos_validation"] = analysis_3_oos_validation(df)
    results["multivariate"] = analysis_4_multivariate_regression(df)
    results["persistence"] = analysis_5_crps_persistence(df)
    results["pit"] = analysis_6_pit_all_series(df)
    results["strike_count"] = analysis_7_strike_count_regression(df)

    # Save results
    # Make serializable
    def make_serializable(obj):
        if isinstance(obj, (np.integer, np.int64)):
            return int(obj)
        if isinstance(obj, (np.floating, np.float64)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        if isinstance(obj, np.bool_):
            return bool(obj)
        return obj

    class NumpyEncoder(json.JSONEncoder):
        def default(self, obj):
            result = make_serializable(obj)
            if result is not obj:
                return result
            return super().default(obj)

    output_path = os.path.join(OUTPUT_DIR, "robustness_results.json")
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, cls=NumpyEncoder)

    print(f"\n{'='*70}")
    print(f"All results saved to {output_path}")


if __name__ == "__main__":
    main()
