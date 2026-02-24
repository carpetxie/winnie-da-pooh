"""
Fetch expanded series from Kalshi API and compute CRPS/MAE.
Iteration 4: Fix API path, re-fetch KXADP/KXISMPMI, add KXU3/KXCPICORE/KXFRM/KXCPIYOY.

This script:
1. Fixes the candlestick API path to /series/{series}/markets/{ticker}/candlesticks
2. Re-fetches KXADP and KXISMPMI candles (previously empty due to wrong path)
3. Fetches 4 new series: KXU3, KXCPICORE, KXFRM, KXCPIYOY
4. Computes CRPS/MAE with BCa bootstrap CIs for all series
5. Runs unified heterogeneity analysis across all 11 series
"""
import os
import sys
import json
import time
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

# FRED series IDs for benchmarks
FRED_BENCHMARKS = {
    "KXPCECORE": "PCEPILFE",    # PCE Price Index Less Food and Energy
    "KXU3": "UNRATE",           # Unemployment Rate
    "KXADP": None,              # No standard FRED series for ADP (private data)
    "KXISMPMI": None,           # ISM PMI (reported by ISM, not in FRED directly)
    "KXCPICORE": "CPILFESL",    # CPI Less Food and Energy
    "KXFRM": "MORTGAGE30US",    # 30-Year Fixed Mortgage Rate
    "KXCPIYOY": "CPIAUCSL",     # CPI All Urban Consumers (need YoY transform)
}

# Pre-registered simple-vs-complex classifications for NEW series (before computing)
# Written BEFORE seeing CRPS/MAE results
OOS_PREDICTIONS = {
    "KXU3": {"type": "Simple", "prediction": "< 1.0",
             "rationale": "Single administratively-reported number (BLS unemployment rate)"},
    "KXCPICORE": {"type": "Complex", "prediction": "> 1.0",
                  "rationale": "Composite price index excluding food/energy (BLS)"},
    "KXFRM": {"type": "Simple", "prediction": "< 1.0",
              "rationale": "Single weekly average rate (Freddie Mac PMMS)"},
    "KXCPIYOY": {"type": "Complex", "prediction": "> 1.0",
                 "rationale": "Year-over-year transformation of composite CPI"},
}

# Save predictions before computing
predictions_path = os.path.join(OUTPUT_DIR, "oos_predictions.json")
with open(predictions_path, 'w') as f:
    json.dump({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "note": "Pre-registered predictions for OOS simple-vs-complex test. Written BEFORE computing CRPS/MAE.",
        "predictions": OOS_PREDICTIONS,
    }, f, indent=2)
print(f"Saved OOS predictions to {predictions_path}")


def fetch_series_markets(client, series_ticker):
    """Fetch all settled markets for a series."""
    markets = client.get_all_pages(
        '/markets',
        params={'series_ticker': series_ticker, 'status': 'settled'},
        result_key='markets'
    )
    return markets


def group_markets_by_event(markets):
    """Group markets by event_ticker, return only multi-strike events."""
    events = defaultdict(list)
    for m in markets:
        et = m.get('event_ticker', '')
        if et:
            events[et].append(m)
    # Only keep events with 2+ markets (multi-strike)
    return {et: ms for et, ms in events.items() if len(ms) >= 2}


def fetch_candles_for_market(client, series_ticker, ticker, open_time=None, close_time=None, max_retries=3):
    """Fetch candlestick data using the CORRECT API path with required timestamps."""
    params = {'period_interval': 60}  # hourly

    # API REQUIRES start_ts and end_ts — without them it returns 400
    if open_time and close_time:
        if isinstance(open_time, str):
            open_time = datetime.fromisoformat(open_time.replace('Z', '+00:00'))
        if isinstance(close_time, str):
            close_time = datetime.fromisoformat(close_time.replace('Z', '+00:00'))
        params['start_ts'] = int(open_time.timestamp())
        params['end_ts'] = int(close_time.timestamp())

    for attempt in range(max_retries):
        try:
            # FIXED: Use /series/{series}/markets/{ticker}/candlesticks
            candles = client.get_all_pages(
                f'/series/{series_ticker}/markets/{ticker}/candlesticks',
                params=params,
                result_key='candlesticks',
            )
            return candles
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                print(f"  Failed to fetch candles for {ticker}: {e}")
                return None


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

    # Build price series from candles
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

            # Try 1: yes_price.close (older format)
            yes_price = c.get('yes_price', {})
            if isinstance(yes_price, dict) and yes_price.get('close') is not None:
                close_price = yes_price['close']

            # Try 2: price.close (newer format)
            if close_price is None:
                price_obj = c.get('price', {})
                if isinstance(price_obj, dict) and price_obj.get('close') is not None:
                    close_price = price_obj['close']

            # Try 3: midpoint of yes_bid/yes_ask (most reliable for newer API)
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
                    prices[ts] = float(close_price) / 100.0  # cents to probability
                except (ValueError, TypeError):
                    continue
        if prices:
            price_series[ticker] = prices

    if len(price_series) < 2:
        return []

    # Find common timestamps
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

        # P(X > strike) should decrease as strike increases
        is_monotonic = all(cdf_values[i] >= cdf_values[i+1] for i in range(len(cdf_values)-1))

        snapshots.append({
            "timestamp": ts,
            "strikes": strikes,
            "cdf_values": cdf_values,
            "is_monotonic": is_monotonic,
            "n_strikes": len(cdf_points),
        })

    return snapshots


def parse_expiration_value(exp_val, series_ticker):
    """Parse the realized value from expiration_value string."""
    if exp_val is None:
        return None
    exp_val = str(exp_val).strip()
    try:
        return float(exp_val)
    except ValueError:
        pass
    import re
    nums = re.findall(r'[-+]?\d*\.?\d+', exp_val)
    if nums:
        try:
            return float(nums[0])
        except ValueError:
            pass
    return None


def compute_implied_mean(strikes, cdf_values):
    """Compute implied mean from CDF using trapezoidal integration."""
    if len(strikes) < 2:
        return None, None

    # Interior mean
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


def process_series(client, series_ticker):
    """Fetch and process a single series."""
    print(f"\n{'='*60}")
    print(f"Processing {series_ticker}")
    print(f"{'='*60}")

    # Check for cached markets
    markets_path = os.path.join(OUTPUT_DIR, f"{series_ticker}_markets.json")
    if os.path.exists(markets_path):
        print(f"  Loading cached markets from {markets_path}")
        with open(markets_path) as f:
            markets = json.load(f)
    else:
        print(f"  Fetching settled markets...")
        markets = fetch_series_markets(client, series_ticker)
        with open(markets_path, 'w') as f:
            json.dump(markets, f, indent=2, default=str)
    print(f"  Found {len(markets)} settled markets")

    # Group by event
    event_groups = group_markets_by_event(markets)
    print(f"  Multi-strike events: {len(event_groups)}")

    if not event_groups:
        return None

    # Build market lookup for timestamps
    market_lookup = {}
    for m in markets:
        market_lookup[m['ticker']] = m

    # Fetch candles for all markets in multi-strike events
    all_market_tickers = set()
    for ms in event_groups.values():
        for m in ms:
            all_market_tickers.add(m['ticker'])

    # Check for cached candles (only use if non-empty)
    candles_path = os.path.join(OUTPUT_DIR, f"{series_ticker}_candles.json")
    use_cache = False
    if os.path.exists(candles_path):
        fsize = os.path.getsize(candles_path)
        if fsize > 100:  # Skip empty/trivial files
            print(f"  Loading cached candles ({fsize/1024:.0f} KB)")
            with open(candles_path) as f:
                candles_by_ticker = json.load(f)
            # Verify non-empty
            non_empty = sum(1 for v in candles_by_ticker.values() if v)
            if non_empty > 0:
                use_cache = True
                print(f"  Cached: {non_empty} markets with candle data")

    if not use_cache:
        print(f"  Fetching candles for {len(all_market_tickers)} markets (FIXED API path + timestamps)...")
        candles_by_ticker = {}
        for i, ticker in enumerate(sorted(all_market_tickers)):
            m_info = market_lookup.get(ticker, {})
            candles = fetch_candles_for_market(
                client, series_ticker, ticker,
                open_time=m_info.get('open_time'),
                close_time=m_info.get('close_time'),
            )
            if candles:
                candles_by_ticker[ticker] = candles
            if (i + 1) % 10 == 0:
                print(f"    {i+1}/{len(all_market_tickers)} markets fetched ({len(candles_by_ticker)} with data)")
            time.sleep(0.7)

        print(f"  Got candles for {len(candles_by_ticker)}/{len(all_market_tickers)} markets")

        # Save candles
        with open(candles_path, 'w') as f:
            json.dump(candles_by_ticker, f, indent=2, default=str)

    # Compute CRPS for each event
    results = []
    for event_ticker, event_ms in sorted(event_groups.items()):
        realized = None
        exp_val = None
        for m in event_ms:
            ev = m.get('expiration_value')
            if ev is not None:
                exp_val = ev
                realized = parse_expiration_value(ev, series_ticker)
                if realized is not None:
                    break

        if realized is None:
            continue

        snapshots = build_cdf_from_candles(event_ms, candles_by_ticker)
        if len(snapshots) < 2:
            continue

        # Use mid-life snapshot
        mid_idx = len(snapshots) // 2
        mid_snap = snapshots[mid_idx]
        strikes = mid_snap['strikes']
        cdf_values = mid_snap['cdf_values']

        if len(strikes) < 2:
            continue

        try:
            kalshi_crps = compute_crps(strikes, cdf_values, realized)
        except Exception as e:
            print(f"  CRPS failed for {event_ticker}: {e}")
            continue

        try:
            interior_mean, tail_mean = compute_implied_mean(strikes, cdf_values)
        except Exception:
            continue

        mae_interior = abs(interior_mean - realized) if interior_mean is not None else None
        mae_ta = abs(tail_mean - realized) if tail_mean is not None else None

        results.append({
            'event_ticker': event_ticker,
            'series': series_ticker,
            'realized': realized,
            'implied_mean': interior_mean,
            'implied_mean_ta': tail_mean,
            'mae_interior': mae_interior,
            'mae_ta': mae_ta,
            'kalshi_crps': kalshi_crps,
            'n_strikes': len(strikes),
            'n_snapshots': len(snapshots),
            'n_markets': len(event_ms),
            'exp_val_raw': str(exp_val),
        })

    print(f"  Events with CRPS: {len(results)}")
    return results


def compute_crps_mae_with_bca(crps_arr, mae_arr, n_boot=10000, seed=42):
    """Compute CRPS/MAE with true BCa CI."""
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
        ci_lo = float(bca.confidence_interval.low)
        ci_hi = float(bca.confidence_interval.high)
        method = 'BCa'
    except Exception as e:
        print(f"    BCa failed ({e}), falling back to percentile")
        rng = np.random.default_rng(seed)
        boot = []
        for _ in range(n_boot):
            idx = rng.integers(0, len(crps_arr), size=len(crps_arr))
            br = crps_arr[idx].mean() / mae_arr[idx].mean() if mae_arr[idx].mean() > 0 else float('inf')
            boot.append(br)
        ci_lo = float(np.percentile(boot, 2.5))
        ci_hi = float(np.percentile(boot, 97.5))
        method = 'percentile'

    return ratio, ci_lo, ci_hi, method


def compute_loo(crps_arr, mae_arr):
    """Compute leave-one-out CRPS/MAE ratios."""
    loo_ratios = []
    for i in range(len(crps_arr)):
        loo_crps = np.delete(crps_arr, i).mean()
        loo_mae = np.delete(mae_arr, i).mean()
        if loo_mae > 0:
            loo_ratios.append(loo_crps / loo_mae)
    return loo_ratios


def main():
    client = KalshiClient()

    # ALL series to process (re-fetch KXADP/KXISMPMI + 4 new)
    target_series = [
        'KXADP',       # Re-fetch (empty candles)
        'KXISMPMI',    # Re-fetch (empty candles)
        'KXU3',        # NEW: Unemployment Rate
        'KXCPICORE',   # NEW: Core CPI m/m
        'KXFRM',       # NEW: 30Y Mortgage Rates
        'KXCPIYOY',    # NEW: CPI Year-over-Year
    ]

    # Delete empty candle files to force re-fetch
    for series in ['KXADP', 'KXISMPMI']:
        candles_path = os.path.join(OUTPUT_DIR, f"{series}_candles.json")
        if os.path.exists(candles_path):
            fsize = os.path.getsize(candles_path)
            if fsize < 100:
                print(f"Deleting empty candle file: {candles_path} ({fsize} bytes)")
                os.remove(candles_path)

    all_results = {}
    summaries = {}

    for series in target_series:
        results = process_series(client, series)
        if results:
            all_results[series] = results

            # Save per-series results
            results_path = os.path.join(OUTPUT_DIR, f"{series}_results.json")
            with open(results_path, 'w') as f:
                json.dump(results, f, indent=2, default=str)

            # Compute CRPS/MAE ratio with BCa
            df = pd.DataFrame(results)
            valid = df.dropna(subset=['kalshi_crps', 'mae_interior'])
            valid = valid[valid['mae_interior'] > 0]

            if len(valid) >= 2:
                crps_arr = valid['kalshi_crps'].values
                mae_arr = valid['mae_interior'].values
                ratio, ci_lo, ci_hi, method = compute_crps_mae_with_bca(crps_arr, mae_arr)

                per_event = (valid['kalshi_crps'] / valid['mae_interior']).replace(
                    [np.inf, -np.inf], np.nan).dropna()
                loo_ratios = compute_loo(crps_arr, mae_arr)

                loo_all_below = all(r < 1 for r in loo_ratios) if loo_ratios else False
                loo_all_above = all(r > 1 for r in loo_ratios) if loo_ratios else False
                if loo_all_below:
                    loo_label = "All < 1.0"
                elif loo_all_above:
                    loo_label = "All > 1.0"
                else:
                    loo_label = "Mixed"

                summary = {
                    'series': series,
                    'n': len(valid),
                    'crps_mae_ratio': round(ratio, 3),
                    'ci_lo': round(ci_lo, 2),
                    'ci_hi': round(ci_hi, 2),
                    'ci_method': method,
                    'median_per_event': round(per_event.median(), 3),
                    'loo_min': round(min(loo_ratios), 3) if loo_ratios else None,
                    'loo_max': round(max(loo_ratios), 3) if loo_ratios else None,
                    'loo_label': loo_label,
                    'mean_crps': round(crps_arr.mean(), 6),
                    'mean_mae': round(mae_arr.mean(), 6),
                    'n_snapshots_mean': round(valid['n_snapshots'].mean(), 1),
                }
                summaries[series] = summary

                print(f"\n  {series} CRPS/MAE Summary:")
                print(f"    n = {len(valid)}")
                print(f"    CRPS/MAE = {ratio:.3f} [{ci_lo:.2f}, {ci_hi:.2f}] ({method})")
                print(f"    Median per-event = {per_event.median():.3f}")
                print(f"    LOO range: [{min(loo_ratios):.3f}, {max(loo_ratios):.3f}]")
                print(f"    LOO: {loo_label}")
                print(f"    Mean n_snapshots: {valid['n_snapshots'].mean():.1f}")

    # Save all results
    output_path = os.path.join(OUTPUT_DIR, "expanded_series_results.json")
    with open(output_path, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)

    # Save summaries
    summary_path = os.path.join(OUTPUT_DIR, "expanded_series_summary.json")
    with open(summary_path, 'w') as f:
        json.dump(summaries, f, indent=2)

    # Print combined summary
    print(f"\n{'='*80}")
    print("COMBINED SUMMARY — EXPANDED SERIES (iteration 4)")
    print(f"{'='*80}")
    print(f"{'Series':<15} {'n':>4} {'CRPS/MAE':>10} {'95% BCa CI':>18} {'LOO':>12} {'Snapshots':>10}")
    print("-" * 80)
    for series, s in summaries.items():
        print(f"{s['series']:<15} {s['n']:>4} {s['crps_mae_ratio']:>10.3f} [{s['ci_lo']:.2f}, {s['ci_hi']:.2f}]{'':<3} {s['loo_label']:>12} {s['n_snapshots_mean']:>10.1f}")

    # OOS simple-vs-complex test
    print(f"\n{'='*80}")
    print("OUT-OF-SAMPLE SIMPLE-VS-COMPLEX TEST")
    print(f"{'='*80}")
    for series, pred in OOS_PREDICTIONS.items():
        if series in summaries:
            actual = summaries[series]['crps_mae_ratio']
            predicted_dir = pred['prediction']
            hit = (predicted_dir == "< 1.0" and actual < 1.0) or (predicted_dir == "> 1.0" and actual >= 1.0)
            print(f"  {series}: Predicted {predicted_dir} ({pred['type']}), Actual = {actual:.3f} → {'✅ HIT' if hit else '❌ MISS'}")
        else:
            print(f"  {series}: No data (fetch may have failed)")

    total_events = sum(s['n'] for s in summaries.values())
    print(f"\nTotal new/re-fetched events: {total_events}")
    print(f"Results saved to {output_path}")
    print(f"Summary saved to {summary_path}")


if __name__ == "__main__":
    main()
