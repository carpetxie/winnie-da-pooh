"""
Fetch new series from Kalshi API and compute CRPS/MAE.
Targets: KXPCECORE, KXU3, KXADP, KXISMPMI, KXCPICORE
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
    "KXPCECORE": "PCEPILFE",   # PCE Price Index Less Food and Energy
    "KXU3": "UNRATE",          # Unemployment Rate
    "KXADP": None,             # No standard FRED series for ADP
    "KXISMPMI": "MANEMP",      # Manufacturing Employment (proxy)
    "KXCPICORE": "CPILFESL",   # CPI Less Food and Energy
}


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


def fetch_candles_for_market(client, ticker, max_retries=3):
    """Fetch candlestick data for a single market."""
    for attempt in range(max_retries):
        try:
            candles = client.get_all_pages(
                f'/markets/{ticker}/candlesticks',
                params={'period_interval': 60},  # hourly
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
    # Parse strikes and tickers
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
            price = c.get('yes_price', {})
            if isinstance(price, dict):
                close_price = price.get('close')
            else:
                close_price = price
            if ts and close_price is not None:
                try:
                    prices[ts] = float(close_price) / 100.0  # Convert cents to probability
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

        # Check monotonicity (P(X > strike) should decrease as strike increases)
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

    # Try direct float parse
    try:
        return float(exp_val)
    except ValueError:
        pass

    # Try extracting number from string like "above X" or "X or more"
    import re
    # Look for numbers in the string
    nums = re.findall(r'[-+]?\d*\.?\d+', exp_val)
    if nums:
        try:
            return float(nums[0])
        except ValueError:
            pass

    return None


def compute_implied_mean(strikes, cdf_values):
    """Compute implied mean from CDF using trapezoidal integration."""
    # CDF values are P(X > strike) = survival function
    # E[X] = integral of S(x) dx from min to max
    # Using trapezoidal rule
    if len(strikes) < 2:
        return None

    # Interior mean: probability-weighted using only interior mass
    total_prob = 0
    weighted_sum = 0
    for i in range(len(strikes) - 1):
        # Probability mass in bin [strikes[i], strikes[i+1]]
        prob = cdf_values[i] - cdf_values[i+1]
        if prob < 0:
            prob = 0  # Handle violations
        midpoint = (strikes[i] + strikes[i+1]) / 2
        weighted_sum += prob * midpoint
        total_prob += prob

    # Add tails
    # Mass below min strike
    prob_below = 1.0 - cdf_values[0]
    # Mass above max strike
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
    # Don't divide by total prob for tail-aware; it should sum to ~1

    return interior_mean, total_mean


def process_series(client, series_ticker):
    """Fetch and process a single series."""
    print(f"\n{'='*60}")
    print(f"Processing {series_ticker}")
    print(f"{'='*60}")

    # Fetch markets
    print(f"  Fetching settled markets...")
    markets = fetch_series_markets(client, series_ticker)
    print(f"  Found {len(markets)} settled markets")

    # Group by event
    event_groups = group_markets_by_event(markets)
    print(f"  Multi-strike events: {len(event_groups)}")

    if not event_groups:
        return None

    # Save markets
    markets_path = os.path.join(OUTPUT_DIR, f"{series_ticker}_markets.json")
    with open(markets_path, 'w') as f:
        json.dump(markets, f, indent=2)

    # Fetch candles for all markets in multi-strike events
    all_market_tickers = set()
    for ms in event_groups.values():
        for m in ms:
            all_market_tickers.add(m['ticker'])

    print(f"  Fetching candles for {len(all_market_tickers)} markets...")
    candles_by_ticker = {}
    for i, ticker in enumerate(sorted(all_market_tickers)):
        candles = fetch_candles_for_market(client, ticker)
        if candles:
            candles_by_ticker[ticker] = candles
        if (i + 1) % 20 == 0:
            print(f"    {i+1}/{len(all_market_tickers)} markets fetched")
        time.sleep(0.7)

    print(f"  Got candles for {len(candles_by_ticker)}/{len(all_market_tickers)} markets")

    # Save candles
    candles_path = os.path.join(OUTPUT_DIR, f"{series_ticker}_candles.json")
    with open(candles_path, 'w') as f:
        json.dump(candles_by_ticker, f, indent=2, default=str)

    # Compute CRPS for each event
    results = []
    for event_ticker, event_ms in sorted(event_groups.items()):
        # Get realized value
        # Check expiration_value from any market in the event
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

        # Build CDF snapshots
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

        # Compute CRPS
        try:
            kalshi_crps = compute_crps(strikes, cdf_values, realized)
        except Exception as e:
            print(f"  CRPS failed for {event_ticker}: {e}")
            continue

        # Compute implied mean
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
    except Exception:
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


def main():
    client = KalshiClient()

    # Process each new series
    # Prioritize by event count and FRED availability
    target_series = ['KXPCECORE', 'KXADP', 'KXISMPMI']

    all_results = {}
    for series in target_series:
        results = process_series(client, series)
        if results:
            all_results[series] = results

            # Compute CRPS/MAE ratio
            df = pd.DataFrame(results)
            valid = df.dropna(subset=['kalshi_crps', 'mae_interior'])
            valid = valid[valid['mae_interior'] > 0]

            if len(valid) >= 2:
                crps_arr = valid['kalshi_crps'].values
                mae_arr = valid['mae_interior'].values
                ratio, ci_lo, ci_hi, method = compute_crps_mae_with_bca(crps_arr, mae_arr)

                # Per-event ratios
                per_event = (valid['kalshi_crps'] / valid['mae_interior']).replace([np.inf, -np.inf], np.nan).dropna()

                # LOO
                loo_ratios = []
                for i in range(len(valid)):
                    loo_crps = np.delete(crps_arr, i).mean()
                    loo_mae = np.delete(mae_arr, i).mean()
                    if loo_mae > 0:
                        loo_ratios.append(loo_crps / loo_mae)

                print(f"\n  {series} CRPS/MAE Summary:")
                print(f"    n = {len(valid)}")
                print(f"    CRPS/MAE = {ratio:.3f} [{ci_lo:.2f}, {ci_hi:.2f}] ({method})")
                print(f"    Median per-event = {per_event.median():.3f}")
                print(f"    LOO range: [{min(loo_ratios):.3f}, {max(loo_ratios):.3f}]")
                print(f"    LOO all same side: {all(r < 1 for r in loo_ratios) or all(r > 1 for r in loo_ratios)}")
                if all(r < 1 for r in loo_ratios):
                    print(f"    LOO: all < 1.0")
                elif all(r > 1 for r in loo_ratios):
                    print(f"    LOO: all > 1.0")
                else:
                    print(f"    LOO: mixed")

    # Save all results
    output_path = os.path.join(OUTPUT_DIR, "new_series_crps_results.json")

    # Make serializable
    serializable = {}
    for series, results in all_results.items():
        serializable[series] = results

    with open(output_path, 'w') as f:
        json.dump(serializable, f, indent=2, default=str)

    print(f"\nResults saved to {output_path}")

    # Combined summary
    print(f"\n{'='*60}")
    print("COMBINED SUMMARY — NEW SERIES")
    print(f"{'='*60}")
    for series, results in all_results.items():
        df = pd.DataFrame(results)
        valid = df.dropna(subset=['kalshi_crps', 'mae_interior'])
        valid = valid[valid['mae_interior'] > 0]
        if len(valid) >= 2:
            ratio = valid['kalshi_crps'].mean() / valid['mae_interior'].mean()
            per_event = valid['kalshi_crps'] / valid['mae_interior']
            print(f"  {series}: n={len(valid)}, CRPS/MAE={ratio:.3f}, median={per_event.median():.3f}")


if __name__ == "__main__":
    main()
