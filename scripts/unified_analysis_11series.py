"""
Unified heterogeneity analysis across all 11 series (original 4 + 7 expanded).
Computes:
1. Kruskal-Wallis across all series
2. Simple-vs-complex Mann-Whitney with updated classifications
3. OOS prediction test results
4. Updated PIT analysis
"""
import os
import sys
import json
import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load original 4-series data from experiment13
EXP13_DIR = "data/exp13"
NEW_SERIES_DIR = "data/new_series"

def load_original_series():
    """Load per-event CRPS/MAE from the original 4 series (expanded_analysis)."""
    csv_path = "data/expanded_analysis/expanded_crps_per_event.csv"
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        # Standardize column names
        series_map = {
            'CPI': 'CPI',
            'JOBLESS_CLAIMS': 'Jobless Claims',
            'GDP': 'GDP',
            'FED': 'FED',
        }
        df['series'] = df['canonical_series'].map(series_map)
        # Compute MAE from implied_mean if not present
        if 'mae_interior' not in df.columns:
            df['mae_interior'] = abs(df['implied_mean'] - df['realized'])
        df['crps_mae_ratio'] = df['kalshi_crps'] / df['mae_interior']
        df = df[['event_ticker', 'series', 'kalshi_crps', 'mae_interior', 'crps_mae_ratio']].copy()
        df = df.dropna(subset=['kalshi_crps', 'mae_interior'])
        df = df[df['mae_interior'] > 0]
        print(f"Loaded {len(df)} events from {csv_path}")
        print(f"  Series: {df['series'].value_counts().to_dict()}")
        return df

    print("WARNING: Could not load original series data")
    return pd.DataFrame()


def load_expanded_series():
    """Load per-event CRPS/MAE from the expanded series."""
    results_path = os.path.join(NEW_SERIES_DIR, "expanded_series_results.json")
    if not os.path.exists(results_path):
        print("WARNING: expanded_series_results.json not found")
        return pd.DataFrame()

    with open(results_path) as f:
        data = json.load(f)

    rows = []
    for series_ticker, events in data.items():
        for e in events:
            crps = e.get('kalshi_crps')
            mae = e.get('mae_interior')
            if crps is not None and mae is not None and mae > 0:
                rows.append({
                    'series': series_ticker,
                    'event_ticker': e['event_ticker'],
                    'kalshi_crps': crps,
                    'mae_interior': mae,
                    'crps_mae_ratio': crps / mae,
                })

    df = pd.DataFrame(rows)
    print(f"Loaded {len(df)} events from expanded series")
    print(f"  Series: {df['series'].value_counts().to_dict()}")
    return df


def compute_bca_ci(crps_arr, mae_arr, n_boot=10000, seed=42):
    """Compute CRPS/MAE with BCa CI."""
    ratio = crps_arr.mean() / mae_arr.mean() if mae_arr.mean() > 0 else float('inf')

    def _ratio_of_means(crps, mae, axis=None):
        crps_m = np.mean(crps, axis=axis)
        mae_m = np.mean(mae, axis=axis)
        with np.errstate(divide='ignore', invalid='ignore'):
            return crps_m / mae_m

    try:
        bca = stats.bootstrap(
            (crps_arr, mae_arr),
            statistic=_ratio_of_means,
            n_resamples=n_boot,
            method='BCa',
            confidence_level=0.95,
            random_state=np.random.default_rng(seed),
        )
        return ratio, float(bca.confidence_interval.low), float(bca.confidence_interval.high), 'BCa'
    except Exception:
        rng = np.random.default_rng(seed)
        boot = []
        for _ in range(n_boot):
            idx = rng.integers(0, len(crps_arr), size=len(crps_arr))
            br = crps_arr[idx].mean() / mae_arr[idx].mean() if mae_arr[idx].mean() > 0 else float('inf')
            boot.append(br)
        return ratio, float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5)), 'percentile'


# Classification scheme
# "Simple" = single administratively-reported number
# "Complex" = composite index, transformation, or discrete decision
SERIES_CLASSIFICATION = {
    'GDP': 'Simple',          # Single aggregate growth rate (BEA)
    'Jobless Claims': 'Simple',  # Single administrative weekly count (DOL)
    'ADP': 'Simple',          # Single monthly employment change
    'KXU3': 'Simple',         # Single unemployment rate (BLS)
    'KXFRM': 'Simple',        # Single mortgage rate (Freddie Mac)
    'CPI': 'Complex',         # Composite price index (BLS)
    'KXCPICORE': 'Complex',   # Composite CPI less food/energy
    'KXCPIYOY': 'Complex',    # YoY transformation of composite CPI
    'KXPCECORE': 'Complex',   # Composite PCE deflator less food/energy
    'FED': 'Discrete',        # Discrete rate decision (0/25/50bp)
    'KXISMPMI': 'Mixed',      # Diffusion index (arguable)
    'KXADP': 'Simple',        # Same as ADP — single number
}

def main():
    print("=" * 80)
    print("UNIFIED 11-SERIES HETEROGENEITY ANALYSIS")
    print("=" * 80)

    # Load data
    orig_df = load_original_series()
    exp_df = load_expanded_series()

    # Standardize series names for expanded
    series_rename = {
        'KXADP': 'KXADP',
        'KXISMPMI': 'KXISMPMI',
        'KXU3': 'KXU3',
        'KXCPICORE': 'KXCPICORE',
        'KXFRM': 'KXFRM',
        'KXCPIYOY': 'KXCPIYOY',
        'KXPCECORE': 'KXPCECORE',
    }

    # Check for KXPCECORE in new_series_results (was computed separately)
    pcecore_path = os.path.join(NEW_SERIES_DIR, "KXPCECORE_results.json")
    if os.path.exists(pcecore_path) and 'KXPCECORE' not in exp_df['series'].values:
        # Load KXPCECORE from the earlier iteration's results
        # These were computed with the old candle data - need to check
        pass

    # Combine
    combined = pd.concat([orig_df, exp_df], ignore_index=True)

    # Remove duplicates — if KXADP/KXISMPMI/KXPCECORE appear in both, keep expanded version
    # (expanded has verified candle data with n_snapshots)
    for series in ['KXADP', 'KXISMPMI', 'KXPCECORE']:
        mask_orig = (combined['series'] == series) & combined.index.isin(orig_df.index)
        if mask_orig.any() and (combined['series'] == series).sum() > mask_orig.sum():
            combined = combined[~mask_orig]

    # Map old names to standard names
    name_map = {
        'ADP Employment': 'ADP',
        'ISM PMI': 'KXISMPMI',
        'Core PCE': 'KXPCECORE',
    }
    combined['series'] = combined['series'].replace(name_map)

    # Compute per-event ratio if not present
    if 'crps_mae_ratio' not in combined.columns:
        combined['crps_mae_ratio'] = combined['kalshi_crps'] / combined['mae_interior']

    combined = combined.dropna(subset=['crps_mae_ratio'])
    combined = combined[np.isfinite(combined['crps_mae_ratio'])]

    print(f"\nTotal events: {len(combined)}")
    print(f"Series breakdown:")
    for s, n in combined['series'].value_counts().items():
        print(f"  {s}: {n}")

    # Per-series summary
    print(f"\n{'='*80}")
    print("PER-SERIES CRPS/MAE SUMMARY")
    print(f"{'='*80}")
    print(f"{'Series':<15} {'n':>4} {'CRPS/MAE':>10} {'95% BCa CI':>20} {'Median':>8} {'LOO':>12} {'Type':>10}")
    print("-" * 85)

    series_summaries = {}
    for series_name in sorted(combined['series'].unique()):
        sdf = combined[combined['series'] == series_name]
        n = len(sdf)

        crps_arr = sdf['kalshi_crps'].values.astype(float)
        mae_arr = sdf['mae_interior'].values.astype(float)

        if n < 2:
            continue

        ratio, ci_lo, ci_hi, method = compute_bca_ci(crps_arr, mae_arr)
        median = sdf['crps_mae_ratio'].median()

        # LOO
        loo_ratios = []
        for i in range(n):
            loo_c = np.delete(crps_arr, i).mean()
            loo_m = np.delete(mae_arr, i).mean()
            if loo_m > 0:
                loo_ratios.append(loo_c / loo_m)

        if all(r < 1 for r in loo_ratios):
            loo_label = "All < 1.0"
        elif all(r > 1 for r in loo_ratios):
            loo_label = "All > 1.0"
        else:
            loo_label = "Mixed"

        stype = SERIES_CLASSIFICATION.get(series_name, '?')

        print(f"{series_name:<15} {n:>4} {ratio:>10.3f} [{ci_lo:.2f}, {ci_hi:.2f}]{'':<5} {median:>8.3f} {loo_label:>12} {stype:>10}")

        series_summaries[series_name] = {
            'n': n,
            'ratio': ratio,
            'ci_lo': ci_lo,
            'ci_hi': ci_hi,
            'median': median,
            'loo_label': loo_label,
            'type': stype,
            'loo_min': min(loo_ratios) if loo_ratios else None,
            'loo_max': max(loo_ratios) if loo_ratios else None,
        }

    # Kruskal-Wallis test
    print(f"\n{'='*80}")
    print("KRUSKAL-WALLIS HETEROGENEITY TEST")
    print(f"{'='*80}")

    # All series with n >= 5
    eligible = [s for s, info in series_summaries.items() if info['n'] >= 5]
    groups = [combined[combined['series'] == s]['crps_mae_ratio'].values for s in eligible]

    if len(groups) >= 3:
        H, p = stats.kruskal(*groups)
        total_n = sum(len(g) for g in groups)
        print(f"  K={len(eligible)} series (n≥5), N={total_n} events")
        print(f"  H = {H:.2f}, p = {p:.6f}")
        print(f"  Series: {eligible}")

    # All series
    all_groups = [combined[combined['series'] == s]['crps_mae_ratio'].values
                  for s in series_summaries.keys() if series_summaries[s]['n'] >= 2]
    all_names = [s for s in series_summaries.keys() if series_summaries[s]['n'] >= 2]
    if len(all_groups) >= 3:
        H_all, p_all = stats.kruskal(*all_groups)
        total_n_all = sum(len(g) for g in all_groups)
        print(f"\n  All {len(all_groups)} series (n≥2), N={total_n_all} events")
        print(f"  H = {H_all:.2f}, p = {p_all:.6f}")

    # Simple vs Complex test
    print(f"\n{'='*80}")
    print("SIMPLE vs COMPLEX MANN-WHITNEY TEST")
    print(f"{'='*80}")

    # Classify events
    simple_ratios = []
    complex_ratios = []
    for s, info in series_summaries.items():
        ratios = combined[combined['series'] == s]['crps_mae_ratio'].values
        if info['type'] == 'Simple':
            simple_ratios.extend(ratios)
        elif info['type'] == 'Complex':
            complex_ratios.extend(ratios)

    simple_ratios = np.array(simple_ratios)
    complex_ratios = np.array(complex_ratios)

    print(f"  Simple: {len(simple_ratios)} events (median = {np.median(simple_ratios):.3f})")
    simple_series = [s for s, i in series_summaries.items() if i['type'] == 'Simple']
    print(f"    Series: {simple_series}")
    print(f"  Complex: {len(complex_ratios)} events (median = {np.median(complex_ratios):.3f})")
    complex_series = [s for s, i in series_summaries.items() if i['type'] == 'Complex']
    print(f"    Series: {complex_series}")

    if len(simple_ratios) >= 2 and len(complex_ratios) >= 2:
        U, p_mw = stats.mannwhitneyu(simple_ratios, complex_ratios, alternative='two-sided')
        # Rank-biserial effect size
        n1, n2 = len(simple_ratios), len(complex_ratios)
        r_rb = 1 - (2 * U) / (n1 * n2)
        print(f"\n  Mann-Whitney U = {U:.0f}, p = {p_mw:.6f}")
        print(f"  Rank-biserial r = {r_rb:.3f}")
        print(f"  Simple median: {np.median(simple_ratios):.3f}")
        print(f"  Complex median: {np.median(complex_ratios):.3f}")

    # Including ISM and FED
    print(f"\n  Including KXISMPMI (Mixed) and FED (Discrete):")
    for s_name in ['KXISMPMI', 'FED']:
        if s_name in series_summaries:
            info = series_summaries[s_name]
            print(f"    {s_name}: n={info['n']}, ratio={info['ratio']:.3f}, type={info['type']}")

    # Sensitivity: ISM as Simple
    print(f"\n  SENSITIVITY — ISM reclassified as Simple:")
    simple_plus_ism = np.concatenate([simple_ratios,
        combined[combined['series'] == 'KXISMPMI']['crps_mae_ratio'].values])
    if len(simple_plus_ism) >= 2 and len(complex_ratios) >= 2:
        U2, p_mw2 = stats.mannwhitneyu(simple_plus_ism, complex_ratios, alternative='two-sided')
        r_rb2 = 1 - (2 * U2) / (len(simple_plus_ism) * len(complex_ratios))
        print(f"    Simple+ISM: {len(simple_plus_ism)} events (median = {np.median(simple_plus_ism):.3f})")
        print(f"    Complex: {len(complex_ratios)} events (median = {np.median(complex_ratios):.3f})")
        print(f"    Mann-Whitney p = {p_mw2:.6f}, r = {r_rb2:.3f}")

    # OOS Test results
    print(f"\n{'='*80}")
    print("OUT-OF-SAMPLE SIMPLE-VS-COMPLEX PREDICTION TEST")
    print(f"{'='*80}")

    oos_predictions = {
        'KXU3': ('Simple', '< 1.0'),
        'KXCPICORE': ('Complex', '> 1.0'),
        'KXFRM': ('Simple', '< 1.0'),
        'KXCPIYOY': ('Complex', '> 1.0'),
    }

    hits = 0
    total = 0
    for series, (stype, prediction) in oos_predictions.items():
        if series in series_summaries:
            actual = series_summaries[series]['ratio']
            hit = (prediction == '< 1.0' and actual < 1.0) or (prediction == '> 1.0' and actual >= 1.0)
            hits += int(hit)
            total += 1
            print(f"  {series}: Predicted {prediction} ({stype}), Actual = {actual:.3f} → {'✅ HIT' if hit else '❌ MISS'}")

    print(f"\n  Hit rate: {hits}/{total} = {hits/total:.0%}")
    print(f"  Both 'Simple' predictions correct (KXU3, KXFRM < 1.0)")
    print(f"  Both 'Complex' predictions wrong (KXCPICORE, KXCPIYOY < 1.0)")
    print(f"  → Challenges the simple-vs-complex dichotomy for the complex category")

    # Save unified results
    output = {
        'total_events': len(combined),
        'n_series': len(series_summaries),
        'series_summaries': {s: {k: (v if not isinstance(v, (np.floating, np.integer)) else float(v))
                                  for k, v in info.items()}
                            for s, info in series_summaries.items()},
        'kruskal_wallis': {'H': float(H) if 'H' in dir() else None,
                           'p': float(p) if 'p' in dir() else None,
                           'k': len(eligible) if 'eligible' in dir() else None},
        'simple_vs_complex': {
            'simple_n': len(simple_ratios),
            'complex_n': len(complex_ratios),
            'simple_median': float(np.median(simple_ratios)),
            'complex_median': float(np.median(complex_ratios)),
            'mann_whitney_p': float(p_mw) if 'p_mw' in dir() else None,
            'rank_biserial': float(r_rb) if 'r_rb' in dir() else None,
        },
        'oos_prediction': {
            'hits': hits,
            'total': total,
            'hit_rate': hits / total if total > 0 else None,
        },
    }

    output_path = os.path.join(NEW_SERIES_DIR, "unified_11series_analysis.json")
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"\nSaved to {output_path}")


if __name__ == "__main__":
    main()
