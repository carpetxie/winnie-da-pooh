"""
Iteration 5: Fix KXADP comma-parsing bug, fetch KXPCECORE candles,
re-run unified 11-series analysis, run KXFRM sensitivity analysis.

Fixes:
1. KXADP realized values: "41,000" was parsed as 41 instead of 41000
2. KXPCECORE: fetch candles and compute CRPS/MAE (was missing from expanded analysis)
3. KXFRM: analyze snapshot count sensitivity

Then re-runs full unified analysis with corrected data.
"""
import os
import sys
import json
import time
import re
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from scipy import stats
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kalshi.client import KalshiClient
from experiment12.distributional_calibration import compute_crps

OUTPUT_DIR = "data/new_series"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def parse_expiration_value_fixed(exp_val, series_ticker=None):
    """Parse the realized value from expiration_value string.
    FIXED: Remove commas before parsing (e.g., '41,000' -> 41000)."""
    if exp_val is None:
        return None
    exp_val = str(exp_val).strip()
    # Remove commas (thousands separators)
    cleaned = exp_val.replace(",", "")
    # Remove percentage signs
    cleaned = cleaned.replace("%", "").strip()
    # Remove text prefixes like "Above", "Below", etc.
    cleaned = re.sub(r"^(Above|Below|At least|At most)\s*", "", cleaned, flags=re.IGNORECASE)
    try:
        return float(cleaned)
    except ValueError:
        # Last resort: extract first number
        nums = re.findall(r'[-+]?\d*\.?\d+', cleaned)
        if nums:
            try:
                return float(nums[0])
            except ValueError:
                pass
    return None


def compute_implied_mean(strikes, cdf_values):
    """Compute implied mean from CDF."""
    if len(strikes) < 2:
        return None, None
    total_prob = 0
    weighted_sum = 0
    for i in range(len(strikes) - 1):
        prob = cdf_values[i] - cdf_values[i+1]
        if prob < 0:
            prob = 0
        midpoint = (strikes[i] + strikes[i+1]) / 2
        weighted_sum += prob * midpoint
        total_prob += prob
    prob_below = 1.0 - cdf_values[0]
    prob_above = cdf_values[-1]
    if total_prob > 0:
        interior_mean = weighted_sum / total_prob
    else:
        interior_mean = np.mean(strikes)
    # Tail-aware mean
    tail_extend = max((strikes[-1] - strikes[0]) * 0.5, 1.0)
    below_point = strikes[0] - tail_extend
    above_point = strikes[-1] + tail_extend
    total_mean = (prob_below * below_point + weighted_sum + prob_above * above_point)
    return interior_mean, total_mean


def build_cdf_from_candles(event_markets, candles_by_ticker):
    """Build CDF snapshots from candle data for an event."""
    tickers_and_strikes = []
    for m in event_markets:
        ticker = m['ticker']
        floor_strike = m.get('floor_strike')
        if floor_strike is not None:
            try:
                strike = float(floor_strike)
                tickers_and_strikes.append((ticker, strike))
            except (ValueError, TypeError):
                continue
    if len(tickers_and_strikes) < 2:
        return []
    tickers_and_strikes.sort(key=lambda x: x[1])

    price_series = {}
    for ticker, strike in tickers_and_strikes:
        if ticker not in candles_by_ticker or not candles_by_ticker[ticker]:
            continue
        candles = candles_by_ticker[ticker]
        prices = {}
        for c in candles:
            ts = c.get('end_period_ts') or c.get('period_start')
            if not ts:
                continue
            close_price = None
            yes_price = c.get('yes_price', {})
            if isinstance(yes_price, dict) and yes_price.get('close') is not None:
                close_price = yes_price['close']
            if close_price is None:
                price_obj = c.get('price', {})
                if isinstance(price_obj, dict) and price_obj.get('close') is not None:
                    close_price = price_obj['close']
            if close_price is None:
                yes_bid = c.get('yes_bid', {})
                yes_ask = c.get('yes_ask', {})
                bid_close = yes_bid.get('close') if isinstance(yes_bid, dict) else None
                ask_close = yes_ask.get('close') if isinstance(yes_ask, dict) else None
                if bid_close is not None and ask_close is not None:
                    close_price = (float(bid_close) + float(ask_close)) / 2.0
                elif bid_close is not None:
                    close_price = float(bid_close)
                elif ask_close is not None:
                    close_price = float(ask_close)
            if close_price is not None:
                try:
                    prices[ts] = float(close_price) / 100.0
                except (ValueError, TypeError):
                    continue
        if prices:
            price_series[ticker] = prices
    if len(price_series) < 2:
        return []

    all_ts = set()
    for ps in price_series.values():
        all_ts.update(ps.keys())

    snapshots = []
    for ts in sorted(all_ts):
        cdf_points = []
        for ticker, strike in tickers_and_strikes:
            if ticker in price_series and ts in price_series[ticker]:
                cdf_points.append((strike, price_series[ticker][ts]))
        if len(cdf_points) < 2:
            continue
        cdf_points.sort(key=lambda x: x[0])
        strikes = [p[0] for p in cdf_points]
        cdf_values = [p[1] for p in cdf_points]
        is_monotonic = all(cdf_values[i] >= cdf_values[i+1] for i in range(len(cdf_values)-1))
        snapshots.append({
            "timestamp": ts,
            "strikes": strikes,
            "cdf_values": cdf_values,
            "is_monotonic": is_monotonic,
            "n_strikes": len(cdf_points),
        })
    return snapshots


def compute_event_crps_mae(event_markets, candles_by_ticker, series_ticker):
    """Compute CRPS and MAE for a single event."""
    # Get realized value
    realized = None
    exp_val_raw = None
    for m in event_markets:
        ev = m.get('expiration_value')
        if ev:
            exp_val_raw = ev
            realized = parse_expiration_value_fixed(ev, series_ticker)
            if realized is not None:
                break
    if realized is None:
        return None

    # Build CDFs
    snapshots = build_cdf_from_candles(event_markets, candles_by_ticker)
    if not snapshots:
        return None

    # Get mid-life snapshot
    mid_idx = len(snapshots) // 2
    mid = snapshots[mid_idx]
    strikes = mid['strikes']
    cdf_values = mid['cdf_values']

    # Compute CRPS
    tail_extend = max((strikes[-1] - strikes[0]) * 0.5, 1.0)
    kalshi_crps = compute_crps(strikes, cdf_values, realized, tail_extension=tail_extend)

    # Compute implied mean
    interior_mean, ta_mean = compute_implied_mean(strikes, cdf_values)
    if interior_mean is None:
        return None

    mae_interior = abs(interior_mean - realized)
    mae_ta = abs(ta_mean - realized) if ta_mean is not None else None

    return {
        'event_ticker': event_markets[0].get('event_ticker', ''),
        'series': series_ticker,
        'realized': realized,
        'implied_mean': interior_mean,
        'implied_mean_ta': ta_mean,
        'mae_interior': mae_interior,
        'mae_ta': mae_ta,
        'kalshi_crps': kalshi_crps,
        'n_strikes': len(strikes),
        'n_snapshots': len(snapshots),
        'n_markets': len(event_markets),
        'exp_val_raw': str(exp_val_raw),
    }


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
    except Exception as e:
        print(f"  BCa failed ({e}), falling back to percentile")
        rng = np.random.default_rng(seed)
        boot = []
        for _ in range(n_boot):
            idx = rng.integers(0, len(crps_arr), size=len(crps_arr))
            br = crps_arr[idx].mean() / mae_arr[idx].mean() if mae_arr[idx].mean() > 0 else float('inf')
            boot.append(br)
        return ratio, float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5)), 'percentile'


# ============================================================
# STEP 1: Fix KXADP comma-parsing bug
# ============================================================
def fix_kxadp():
    """Recompute KXADP with correct comma-removed parsing."""
    print("=" * 80)
    print("STEP 1: Fixing KXADP comma-parsing bug")
    print("=" * 80)

    results_path = os.path.join(OUTPUT_DIR, "KXADP_results.json")
    markets_path = os.path.join(OUTPUT_DIR, "KXADP_markets.json")
    candles_path = os.path.join(OUTPUT_DIR, "KXADP_candles.json")

    if not os.path.exists(results_path):
        print("ERROR: KXADP_results.json not found")
        return None

    with open(results_path) as f:
        old_results = json.load(f)
    with open(markets_path) as f:
        markets = json.load(f)
    with open(candles_path) as f:
        candles_data = json.load(f)

    # Group markets by event
    events = defaultdict(list)
    for m in markets:
        et = m.get('event_ticker', '')
        if et:
            events[et].append(m)

    # Build candles lookup
    candles_by_ticker = {}
    if isinstance(candles_data, dict):
        candles_by_ticker = candles_data
    elif isinstance(candles_data, list):
        # Might be flat list - need to group
        for item in candles_data:
            ticker = item.get('ticker', '')
            if ticker not in candles_by_ticker:
                candles_by_ticker[ticker] = []
            candles_by_ticker[ticker].append(item)

    print(f"\n  Old results: {len(old_results)} events")
    print(f"  Checking comma-parsing bug:")

    fixed_count = 0
    for r in old_results:
        raw = r.get('exp_val_raw', '')
        old_realized = r['realized']
        new_realized = parse_expiration_value_fixed(raw)
        if new_realized != old_realized:
            print(f"    {r['event_ticker']}: '{raw}' -> old={old_realized}, fixed={new_realized}")
            fixed_count += 1

    print(f"\n  {fixed_count} events need fixing")

    if fixed_count == 0:
        print("  No fixes needed!")
        return old_results

    # Recompute from candles with fixed parsing
    new_results = []
    for event_ticker in sorted(events.keys()):
        event_markets = events[event_ticker]
        if len(event_markets) < 2:
            continue

        # Build per-ticker candle lookup for this event's markets
        event_candles = {}
        for m in event_markets:
            t = m['ticker']
            if t in candles_by_ticker:
                event_candles[t] = candles_by_ticker[t]

        result = compute_event_crps_mae(event_markets, event_candles, 'KXADP')
        if result and result['mae_interior'] > 0:
            new_results.append(result)

    print(f"\n  Recomputed {len(new_results)} events with fixed parsing")
    for r in new_results:
        print(f"    {r['event_ticker']}: realized={r['realized']}, CRPS={r['kalshi_crps']:.2f}, MAE={r['mae_interior']:.2f}, ratio={r['kalshi_crps']/r['mae_interior']:.3f}")

    # Save fixed results
    fixed_path = os.path.join(OUTPUT_DIR, "KXADP_results_fixed.json")
    with open(fixed_path, 'w') as f:
        json.dump(new_results, f, indent=2)
    print(f"  Saved to {fixed_path}")

    # Overwrite original
    with open(results_path, 'w') as f:
        json.dump(new_results, f, indent=2)
    print(f"  Updated {results_path}")

    return new_results


# ============================================================
# STEP 2: Fetch KXPCECORE candles and compute CRPS/MAE
# ============================================================
def fetch_kxpcecore():
    """Fetch KXPCECORE candles and compute CRPS/MAE."""
    print("\n" + "=" * 80)
    print("STEP 2: Fetching KXPCECORE candles and computing CRPS/MAE")
    print("=" * 80)

    results_path = os.path.join(OUTPUT_DIR, "KXPCECORE_results.json")
    if os.path.exists(results_path):
        print(f"  Loading cached results from {results_path}")
        with open(results_path) as f:
            return json.load(f)

    markets_path = os.path.join(OUTPUT_DIR, "KXPCECORE_markets.json")
    if not os.path.exists(markets_path):
        print("  ERROR: KXPCECORE_markets.json not found")
        return None

    with open(markets_path) as f:
        markets = json.load(f)

    # Group by event
    events = defaultdict(list)
    for m in markets:
        et = m.get('event_ticker', '')
        if et:
            events[et].append(m)
    multi_strike = {et: ms for et, ms in events.items() if len(ms) >= 2}
    print(f"  Found {len(multi_strike)} multi-strike events")

    # Check for cached candles
    candles_path = os.path.join(OUTPUT_DIR, "KXPCECORE_candles.json")
    if os.path.exists(candles_path):
        print(f"  Loading cached candles")
        with open(candles_path) as f:
            candles_by_ticker = json.load(f)
    else:
        # Fetch candles from API
        client = KalshiClient()
        candles_by_ticker = {}
        tickers_needed = set()
        for et, ms in multi_strike.items():
            for m in ms:
                tickers_needed.add(m['ticker'])

        print(f"  Fetching candles for {len(tickers_needed)} tickers...")
        for i, ticker in enumerate(sorted(tickers_needed)):
            m = next(m for m in markets if m['ticker'] == ticker)
            open_time = m.get('open_time')
            close_time = m.get('close_time')
            candles = []
            try:
                params = {'period_interval': 60}
                if open_time and close_time:
                    from datetime import datetime as dt
                    if isinstance(open_time, str):
                        open_time_dt = dt.fromisoformat(open_time.replace('Z', '+00:00'))
                    else:
                        open_time_dt = open_time
                    if isinstance(close_time, str):
                        close_time_dt = dt.fromisoformat(close_time.replace('Z', '+00:00'))
                    else:
                        close_time_dt = close_time
                    params['start_ts'] = int(open_time_dt.timestamp())
                    params['end_ts'] = int(close_time_dt.timestamp())
                candles = client.get_all_pages(
                    f'/series/KXPCECORE/markets/{ticker}/candlesticks',
                    params=params,
                    result_key='candlesticks',
                )
            except Exception as e:
                print(f"    Failed: {ticker}: {e}")
            candles_by_ticker[ticker] = candles
            if (i + 1) % 10 == 0:
                print(f"    {i+1}/{len(tickers_needed)} tickers fetched")

        with open(candles_path, 'w') as f:
            json.dump(candles_by_ticker, f)
        print(f"  Saved candles to {candles_path}")

    # Compute CRPS/MAE for each event
    results = []
    for event_ticker in sorted(multi_strike.keys()):
        event_markets = multi_strike[event_ticker]
        event_candles = {}
        for m in event_markets:
            t = m['ticker']
            if t in candles_by_ticker:
                event_candles[t] = candles_by_ticker[t]

        result = compute_event_crps_mae(event_markets, event_candles, 'KXPCECORE')
        if result and result['mae_interior'] > 0:
            results.append(result)

    print(f"\n  Computed {len(results)} events")
    for r in results:
        ratio = r['kalshi_crps'] / r['mae_interior']
        print(f"    {r['event_ticker']}: realized={r['realized']}, ratio={ratio:.3f}, snapshots={r['n_snapshots']}")

    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"  Saved to {results_path}")

    return results


# ============================================================
# STEP 3: KXFRM snapshot sensitivity analysis
# ============================================================
def analyze_kxfrm_snapshots():
    """Analyze KXFRM data quality based on snapshot count."""
    print("\n" + "=" * 80)
    print("STEP 3: KXFRM snapshot sensitivity analysis")
    print("=" * 80)

    results_path = os.path.join(OUTPUT_DIR, "KXFRM_results.json")
    with open(results_path) as f:
        results = json.load(f)

    df = pd.DataFrame(results)
    df['ratio'] = df['kalshi_crps'] / df['mae_interior']

    print(f"\n  Total KXFRM events: {len(df)}")
    print(f"  Snapshot distribution:")
    print(f"    Mean: {df['n_snapshots'].mean():.1f}")
    print(f"    Median: {df['n_snapshots'].median():.0f}")
    print(f"    Min: {df['n_snapshots'].min()}")
    print(f"    Max: {df['n_snapshots'].max()}")
    print(f"    <10: {(df['n_snapshots'] < 10).sum()} events")
    print(f"    <20: {(df['n_snapshots'] < 20).sum()} events")
    print(f"    <50: {(df['n_snapshots'] < 50).sum()} events")
    print(f"    ≥50: {(df['n_snapshots'] >= 50).sum()} events")

    # Full vs filtered
    full_crps = df['kalshi_crps'].values
    full_mae = df['mae_interior'].values
    full_ratio = full_crps.mean() / full_mae.mean()

    thresholds = [5, 10, 20, 50]
    print(f"\n  Sensitivity to minimum snapshot threshold:")
    print(f"  {'Threshold':<12} {'n events':>10} {'CRPS/MAE':>10} {'Change':>10}")
    print(f"  {'-'*42}")
    print(f"  {'None':<12} {len(df):>10} {full_ratio:>10.3f} {'—':>10}")

    sensitivity = {'full': {'n': len(df), 'ratio': full_ratio}}

    for thresh in thresholds:
        filt = df[df['n_snapshots'] >= thresh]
        if len(filt) < 3:
            continue
        filt_ratio = filt['kalshi_crps'].mean() / filt['mae_interior'].mean()
        change = (filt_ratio - full_ratio) / full_ratio * 100
        print(f"  ≥{thresh:<10} {len(filt):>10} {filt_ratio:>10.3f} {change:>+9.1f}%")
        sensitivity[f'min_{thresh}'] = {'n': len(filt), 'ratio': filt_ratio}

    return sensitivity


# ============================================================
# STEP 4: Unified 11-series analysis
# ============================================================
def run_unified_analysis():
    """Run the unified analysis across all 11 series with corrected data."""
    print("\n" + "=" * 80)
    print("STEP 4: UNIFIED 11-SERIES ANALYSIS (with corrections)")
    print("=" * 80)

    # Load original 4 series
    csv_path = "data/expanded_analysis/expanded_crps_per_event.csv"
    if os.path.exists(csv_path):
        orig_df = pd.read_csv(csv_path)
        series_map = {
            'CPI': 'CPI', 'JOBLESS_CLAIMS': 'Jobless Claims',
            'GDP': 'GDP', 'FED': 'FED',
        }
        orig_df['series'] = orig_df['canonical_series'].map(series_map)
        if 'mae_interior' not in orig_df.columns:
            orig_df['mae_interior'] = abs(orig_df['implied_mean'] - orig_df['realized'])
        orig_df['crps_mae_ratio'] = orig_df['kalshi_crps'] / orig_df['mae_interior']
        orig_df = orig_df[['event_ticker', 'series', 'kalshi_crps', 'mae_interior', 'crps_mae_ratio']].copy()
        orig_df = orig_df.dropna(subset=['kalshi_crps', 'mae_interior'])
        orig_df = orig_df[orig_df['mae_interior'] > 0]
        print(f"  Original 4 series: {len(orig_df)} events")
        print(f"    {orig_df['series'].value_counts().to_dict()}")
    else:
        print("  ERROR: Could not load original series data")
        return None

    # Load expanded series (KXADP now fixed, KXPCECORE now included)
    expanded_series = ['KXADP', 'KXISMPMI', 'KXU3', 'KXCPICORE', 'KXFRM', 'KXCPIYOY', 'KXPCECORE']
    exp_rows = []
    for st in expanded_series:
        rpath = os.path.join(OUTPUT_DIR, f"{st}_results.json")
        if not os.path.exists(rpath):
            print(f"  WARNING: {st}_results.json not found, skipping")
            continue
        with open(rpath) as f:
            events = json.load(f)
        for e in events:
            crps = e.get('kalshi_crps')
            mae = e.get('mae_interior')
            if crps is not None and mae is not None and mae > 0:
                exp_rows.append({
                    'series': st,
                    'event_ticker': e['event_ticker'],
                    'kalshi_crps': crps,
                    'mae_interior': mae,
                    'crps_mae_ratio': crps / mae,
                })
    exp_df = pd.DataFrame(exp_rows)
    print(f"  Expanded series: {len(exp_df)} events")
    print(f"    {exp_df['series'].value_counts().to_dict()}")

    # Combine
    combined = pd.concat([orig_df, exp_df], ignore_index=True)
    combined = combined.dropna(subset=['crps_mae_ratio'])
    combined = combined[np.isfinite(combined['crps_mae_ratio'])]

    print(f"\n  Total combined: {len(combined)} events across {combined['series'].nunique()} series")

    # Series classifications
    SERIES_CLASSIFICATION = {
        'GDP': 'Simple',
        'Jobless Claims': 'Simple',
        'KXADP': 'Simple',
        'KXU3': 'Simple',
        'KXFRM': 'Simple',
        'CPI': 'Complex',
        'KXCPICORE': 'Complex',
        'KXCPIYOY': 'Complex',
        'KXPCECORE': 'Complex',
        'FED': 'Discrete',
        'KXISMPMI': 'Mixed',
    }

    # Per-series summary
    print(f"\n{'='*80}")
    print("PER-SERIES CRPS/MAE SUMMARY")
    print(f"{'='*80}")
    print(f"{'Series':<15} {'n':>4} {'CRPS/MAE':>10} {'95% BCa CI':>22} {'Median':>8} {'LOO':>12} {'Type':>10}")
    print("-" * 85)

    series_summaries = {}
    for series_name in sorted(combined['series'].unique()):
        sdf = combined[combined['series'] == series_name]
        n = len(sdf)
        if n < 2:
            continue

        crps_arr = sdf['kalshi_crps'].values.astype(float)
        mae_arr = sdf['mae_interior'].values.astype(float)
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
            'n': int(n),
            'ratio': float(ratio),
            'ci_lo': float(ci_lo),
            'ci_hi': float(ci_hi),
            'ci_method': method,
            'median': float(median),
            'loo_label': loo_label,
            'loo_min': float(min(loo_ratios)) if loo_ratios else None,
            'loo_max': float(max(loo_ratios)) if loo_ratios else None,
            'type': stype,
            'mean_crps': float(crps_arr.mean()),
            'mean_mae': float(mae_arr.mean()),
        }

    # Sort by ratio for display
    sorted_series = sorted(series_summaries.items(), key=lambda x: x[1]['ratio'])
    print(f"\n  Sorted by CRPS/MAE ratio:")
    for s, info in sorted_series:
        adds_value = "✅" if info['ratio'] < 1 else "❌"
        print(f"    {adds_value} {s}: {info['ratio']:.3f} (n={info['n']}, LOO={info['loo_label']})")

    n_below_1 = sum(1 for s, info in series_summaries.items() if info['ratio'] < 1.0)
    n_total = len(series_summaries)
    print(f"\n  {n_below_1}/{n_total} series show CRPS/MAE < 1.0 (distributions add value)")

    # Kruskal-Wallis tests
    print(f"\n{'='*80}")
    print("KRUSKAL-WALLIS HETEROGENEITY TESTS")
    print(f"{'='*80}")

    # All series with n >= 5
    eligible = [s for s, info in series_summaries.items() if info['n'] >= 5]
    groups = [combined[combined['series'] == s]['crps_mae_ratio'].values for s in eligible]
    H_5, p_5 = stats.kruskal(*groups) if len(groups) >= 3 else (None, None)
    total_n_5 = sum(len(g) for g in groups)
    print(f"  K={len(eligible)} series (n≥5), N={total_n_5} events")
    if H_5 is not None:
        print(f"  H = {H_5:.2f}, p = {p_5:.6f}")
    print(f"  Series: {eligible}")

    # All series with n >= 2
    all_groups = [combined[combined['series'] == s]['crps_mae_ratio'].values
                  for s in series_summaries.keys() if series_summaries[s]['n'] >= 2]
    all_names = [s for s in series_summaries.keys() if series_summaries[s]['n'] >= 2]
    H_all, p_all = stats.kruskal(*all_groups) if len(all_groups) >= 3 else (None, None)
    total_n_all = sum(len(g) for g in all_groups)
    print(f"\n  All {len(all_groups)} series (n≥2), N={total_n_all} events")
    if H_all is not None:
        print(f"  H = {H_all:.2f}, p = {p_all:.6f}")

    # Simple vs Complex
    print(f"\n{'='*80}")
    print("SIMPLE vs COMPLEX MANN-WHITNEY TEST")
    print(f"{'='*80}")

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

    simple_series = [s for s, i in series_summaries.items() if i['type'] == 'Simple']
    complex_series = [s for s, i in series_summaries.items() if i['type'] == 'Complex']

    print(f"  Simple: {len(simple_ratios)} events (median = {np.median(simple_ratios):.3f})")
    print(f"    Series: {simple_series}")
    print(f"  Complex: {len(complex_ratios)} events (median = {np.median(complex_ratios):.3f})")
    print(f"    Series: {complex_series}")

    U_sc, p_sc = stats.mannwhitneyu(simple_ratios, complex_ratios, alternative='two-sided')
    n1, n2 = len(simple_ratios), len(complex_ratios)
    r_rb = 1 - (2 * U_sc) / (n1 * n2)

    print(f"\n  Mann-Whitney U = {U_sc:.0f}, p = {p_sc:.6f}")
    print(f"  Rank-biserial r = {r_rb:.3f}")

    # OOS Prediction test
    print(f"\n{'='*80}")
    print("OUT-OF-SAMPLE PREDICTION TEST")
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
            print(f"  {series}: Predicted {prediction} ({stype}), Actual = {actual:.3f} → {'✅' if hit else '❌'}")

    print(f"\n  Hit rate: {hits}/{total} = {hits/total:.0%}")

    # Count series where distributions add value with LOO unanimity
    unanimous_below = sum(1 for s, info in series_summaries.items()
                          if info['loo_label'] == 'All < 1.0')
    unanimous_above = sum(1 for s, info in series_summaries.items()
                          if info['loo_label'] == 'All > 1.0')

    print(f"\n  LOO Summary:")
    print(f"    Unanimous < 1.0 (distributions add value): {unanimous_below} series")
    print(f"    Unanimous > 1.0 (distributions harmful): {unanimous_above} series")
    print(f"    Mixed: {n_total - unanimous_below - unanimous_above} series")

    # Binomial test: are most series < 1.0?
    n_series_with_ratio = len(series_summaries)
    n_below = sum(1 for s, info in series_summaries.items() if info['ratio'] < 1.0)
    binom_p = stats.binomtest(n_below, n_series_with_ratio, 0.5).pvalue
    print(f"\n  Binomial test (H0: P(ratio<1) = 0.5):")
    print(f"    {n_below}/{n_series_with_ratio} series < 1.0, p = {binom_p:.4f}")

    # Sign test on per-event ratios
    all_ratios = combined['crps_mae_ratio'].values
    n_events_below = (all_ratios < 1.0).sum()
    n_events_total = len(all_ratios)
    sign_p = stats.binomtest(n_events_below, n_events_total, 0.5).pvalue
    print(f"\n  Sign test on per-event ratios:")
    print(f"    {n_events_below}/{n_events_total} events < 1.0, p = {sign_p:.4f}")

    # KXFRM snapshot sensitivity (subset)
    print(f"\n{'='*80}")
    print("KXFRM SNAPSHOT SENSITIVITY")
    print(f"{'='*80}")

    kxfrm_events = combined[combined['series'] == 'KXFRM']
    # Need to load snapshot counts
    frm_results_path = os.path.join(OUTPUT_DIR, "KXFRM_results.json")
    if os.path.exists(frm_results_path):
        with open(frm_results_path) as f:
            frm_data = json.load(f)
        snap_counts = {e['event_ticker']: e['n_snapshots'] for e in frm_data}

        # Recompute ratio excluding low-snapshot events
        for thresh in [5, 10, 20, 50]:
            kept_tickers = {et for et, n in snap_counts.items() if n >= thresh}
            filt = kxfrm_events[kxfrm_events['event_ticker'].isin(kept_tickers)]
            if len(filt) >= 3:
                filt_ratio = filt['kalshi_crps'].mean() / filt['mae_interior'].mean()
                print(f"  KXFRM (≥{thresh} snapshots): n={len(filt)}, CRPS/MAE={filt_ratio:.3f}")

    # Save unified results
    output = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'total_events': int(len(combined)),
        'n_series': len(series_summaries),
        'corrections': [
            'KXADP comma-parsing bug fixed (7/9 events had realized values off by 1000x)',
            'KXPCECORE added (was missing from previous unified analysis)',
        ],
        'series_summaries': series_summaries,
        'kruskal_wallis_n5': {
            'H': float(H_5) if H_5 is not None else None,
            'p': float(p_5) if p_5 is not None else None,
            'k': len(eligible),
            'n': total_n_5,
            'series': eligible,
        },
        'kruskal_wallis_all': {
            'H': float(H_all) if H_all is not None else None,
            'p': float(p_all) if p_all is not None else None,
            'k': len(all_groups),
            'n': total_n_all,
        },
        'simple_vs_complex': {
            'simple_n': int(len(simple_ratios)),
            'complex_n': int(len(complex_ratios)),
            'simple_median': float(np.median(simple_ratios)),
            'complex_median': float(np.median(complex_ratios)),
            'simple_mean': float(np.mean(simple_ratios)),
            'complex_mean': float(np.mean(complex_ratios)),
            'mann_whitney_U': float(U_sc),
            'mann_whitney_p': float(p_sc),
            'rank_biserial': float(r_rb),
            'simple_series': simple_series,
            'complex_series': complex_series,
        },
        'oos_prediction': {
            'hits': hits,
            'total': total,
            'hit_rate': float(hits / total) if total > 0 else None,
        },
        'distributions_add_value': {
            'n_series_below_1': n_below,
            'n_series_total': n_series_with_ratio,
            'binomial_p': float(binom_p),
            'n_events_below_1': int(n_events_below),
            'n_events_total': int(n_events_total),
            'sign_test_p': float(sign_p),
        },
    }

    output_path = os.path.join(OUTPUT_DIR, "unified_11series_analysis.json")
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"\nSaved unified results to {output_path}")

    return output


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    # Step 1: Fix KXADP
    kxadp_results = fix_kxadp()

    # Step 2: Fetch/compute KXPCECORE
    kxpcecore_results = fetch_kxpcecore()

    # Step 3: KXFRM sensitivity
    kxfrm_sensitivity = analyze_kxfrm_snapshots()

    # Step 4: Unified analysis
    unified_results = run_unified_analysis()

    print("\n" + "=" * 80)
    print("ALL STEPS COMPLETE")
    print("=" * 80)
