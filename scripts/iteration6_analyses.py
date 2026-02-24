"""
Iteration 6: Comprehensive analyses to address reviewer critique.

1. PIT analysis for ALL 11 series (was only 4)
2. Cross-series horse race (KXU3 → UNRATE, KXFRM → MORTGAGE30US)
3. Serial correlation (lag-1 Spearman) for all 11 series
4. GDP temporal snapshot sensitivity
5. KXPCECORE discrepancy investigation
"""
import os
import sys
import json
import numpy as np
import pandas as pd
from scipy import stats
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from experiment12.distributional_calibration import compute_crps

OUTPUT_DIR = "data/iteration6"
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# UTILITY FUNCTIONS (from fix_and_recompute.py)
# ============================================================
import re

def parse_expiration_value_fixed(exp_val, series_ticker=None):
    if exp_val is None:
        return None
    exp_val = str(exp_val).strip()
    cleaned = exp_val.replace(",", "").replace("%", "").strip()
    cleaned = re.sub(r"^(Above|Below|At least|At most)\s*", "", cleaned, flags=re.IGNORECASE)
    try:
        return float(cleaned)
    except ValueError:
        nums = re.findall(r'[-+]?\d*\.?\d+', cleaned)
        if nums:
            try:
                return float(nums[0])
            except ValueError:
                pass
    return None


def build_cdf_from_candles(event_markets, candles_by_ticker):
    """Build CDF snapshots from candle data."""
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
        strikes_list = [p[0] for p in cdf_points]
        cdf_values_list = [p[1] for p in cdf_points]
        snapshots.append({
            "timestamp": ts,
            "strikes": strikes_list,
            "cdf_values": cdf_values_list,
            "n_strikes": len(cdf_points),
        })
    return snapshots


def compute_implied_mean(strikes, cdf_values):
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
    tail_extend = max((strikes[-1] - strikes[0]) * 0.5, 1.0)
    below_point = strikes[0] - tail_extend
    above_point = strikes[-1] + tail_extend
    total_mean = prob_below * below_point + weighted_sum + prob_above * above_point
    return interior_mean, total_mean


def load_series_data(series_ticker):
    """Load markets and candles for a new series."""
    markets_path = f"data/new_series/{series_ticker}_markets.json"
    candles_path = f"data/new_series/{series_ticker}_candles.json"

    if not os.path.exists(markets_path) or not os.path.exists(candles_path):
        return None, None

    with open(markets_path) as f:
        markets = json.load(f)
    with open(candles_path) as f:
        candles = json.load(f)

    return markets, candles


def group_markets_by_event(markets):
    """Group markets by event_ticker."""
    groups = defaultdict(list)
    for m in markets:
        et = m.get('event_ticker')
        if et:
            groups[et].append(m)
    return groups


def get_candles_by_ticker(candles_data):
    """Extract candles indexed by market ticker."""
    if isinstance(candles_data, dict):
        return candles_data
    # If list, need to index
    result = defaultdict(list)
    for item in candles_data:
        ticker = item.get('ticker')
        if ticker:
            result[ticker].append(item)
    return result


# ============================================================
# LOAD ALL DATA
# ============================================================
print("=" * 70)
print("LOADING ALL SERIES DATA")
print("=" * 70)

NEW_SERIES = ["KXU3", "KXCPICORE", "KXCPIYOY", "KXFRM", "KXADP", "KXISMPMI", "KXPCECORE"]

# Load unified analysis for per-event data
with open("data/new_series/unified_11series_analysis.json") as f:
    unified = json.load(f)

# Load per-series results (new series)
new_series_events = {}
for series in NEW_SERIES:
    results_path = f"data/new_series/{series}_results.json"
    if series == "KXADP":
        fixed_path = f"data/new_series/{series}_results_fixed.json"
        if os.path.exists(fixed_path):
            results_path = fixed_path
    if os.path.exists(results_path):
        with open(results_path) as f:
            new_series_events[series] = json.load(f)
        print(f"  {series}: {len(new_series_events[series])} events")

# Load original 4 series data from experiment data
# For original series (CPI, JC, GDP, FED), PIT is already computed in experiment13
# We need data from exp7/exp12 for these

# Load expanded_series_results for the full per-event data
with open("data/new_series/expanded_series_results.json") as f:
    expanded_results = json.load(f)

print(f"\nExpanded results: {len(expanded_results)} series")
for series, events in expanded_results.items():
    print(f"  {series}: {len(events)} events")


# ============================================================
# ANALYSIS 1: PIT FOR ALL 11 SERIES (NEW 7 SERIES)
# ============================================================
print("\n" + "=" * 70)
print("ANALYSIS 1: PIT FOR ALL NEW SERIES (7 series)")
print("=" * 70)

pit_results = {}

for series_ticker in NEW_SERIES:
    markets, candles = load_series_data(series_ticker)
    if markets is None:
        print(f"  {series_ticker}: No data available, skipping")
        continue

    event_groups = group_markets_by_event(markets)
    candles_by_ticker = get_candles_by_ticker(candles)

    # Get results for realized values
    if series_ticker not in new_series_events:
        print(f"  {series_ticker}: No results, skipping")
        continue

    results = new_series_events[series_ticker]

    pit_values = []
    for event_result in results:
        event_ticker = event_result['event_ticker']
        realized = event_result['realized']

        if event_ticker not in event_groups:
            continue

        event_markets = event_groups[event_ticker]
        snapshots = build_cdf_from_candles(event_markets, candles_by_ticker)

        if len(snapshots) < 2:
            continue

        mid_snap = snapshots[len(snapshots) // 2]
        strikes = mid_snap['strikes']
        cdf_vals = mid_snap['cdf_values']  # These are survival P(X > strike)

        # PIT = P(X <= realized) = 1 - P(X > realized) = 1 - interp(survival)
        survival = np.interp(realized, strikes, cdf_vals)
        pit = 1.0 - survival
        pit_values.append({
            "event_ticker": event_ticker,
            "realized": realized,
            "pit": float(pit)
        })

    if not pit_values:
        print(f"  {series_ticker}: No PIT values computed")
        continue

    pit_arr = np.array([p['pit'] for p in pit_values])
    n = len(pit_arr)

    # Bootstrap CI on mean
    rng = np.random.default_rng(42)
    boot_means = []
    for _ in range(10000):
        boot_idx = rng.integers(0, n, size=n)
        boot_means.append(pit_arr[boot_idx].mean())
    ci_lo = float(np.percentile(boot_means, 2.5))
    ci_hi = float(np.percentile(boot_means, 97.5))

    # KS test
    ks_stat, ks_p = stats.kstest(pit_arr, 'uniform')

    # Cramér-von Mises
    cvm_result = stats.cramervonmises(pit_arr, 'uniform')

    # IQR and tails
    n_iqr = int(((pit_arr >= 0.25) & (pit_arr <= 0.75)).sum())
    n_tails = int(((pit_arr < 0.1) | (pit_arr > 0.9)).sum())

    pit_results[series_ticker] = {
        "n": n,
        "mean_pit": float(pit_arr.mean()),
        "std_pit": float(pit_arr.std()),
        "ci_lo": ci_lo,
        "ci_hi": ci_hi,
        "ks_stat": float(ks_stat),
        "ks_p": float(ks_p),
        "cvm_stat": float(cvm_result.statistic),
        "cvm_p": float(cvm_result.pvalue),
        "pct_iqr": float(n_iqr / n),
        "pct_tails": float(n_tails / n),
        "pit_values": [float(p) for p in pit_arr],
    }

    print(f"\n  {series_ticker} (n={n}):")
    print(f"    Mean PIT: {pit_arr.mean():.3f} (CI [{ci_lo:.2f}, {ci_hi:.2f}], ideal=0.500)")
    print(f"    Std PIT:  {pit_arr.std():.3f} (ideal=0.289)")
    print(f"    KS p={ks_p:.4f}, CvM p={cvm_result.pvalue:.4f}")
    print(f"    IQR: {n_iqr}/{n} = {n_iqr/n:.0%}, Tails: {n_tails}/{n} = {n_tails/n:.0%}")

# Also include original 4 series PIT from experiment13 results
exp13_results_path = "data/exp13/unified_results.json"
if os.path.exists(exp13_results_path):
    with open(exp13_results_path) as f:
        exp13_data = json.load(f)
    if "pit_analysis" in exp13_data:
        for series_key, pit_data in exp13_data["pit_analysis"].items():
            canonical = {
                "KXCPI": "CPI",
                "KXJOBLESSCLAIMS": "Jobless Claims"
            }.get(series_key, series_key)
            pit_results[f"ORIG_{canonical}"] = pit_data
            print(f"\n  [Original] {canonical}: mean={pit_data.get('mean_pit', 'N/A'):.3f}, "
                  f"n={pit_data.get('n_events', 'N/A')}")

# Load original GDP and FED PIT from exp7 if available
exp7_results_path = "data/exp7/implied_distribution_results.json"
if os.path.exists(exp7_results_path):
    with open(exp7_results_path) as f:
        exp7_data = json.load(f)
    print(f"\n  [Exp7 data available: {list(exp7_data.keys())[:10]}]")


# ============================================================
# ANALYSIS 2: SERIAL CORRELATION FOR ALL 11 SERIES
# ============================================================
print("\n" + "=" * 70)
print("ANALYSIS 2: SERIAL CORRELATION FOR ALL 11 SERIES")
print("=" * 70)

serial_corr_results = {}

# Build per-event CRPS/MAE ratios for each series
for series_key, events in unified.get("per_event_data", {}).items():
    if not events or len(events) < 4:
        print(f"  {series_key}: n={len(events) if events else 0}, too few for serial correlation")
        serial_corr_results[series_key] = {
            "n": len(events) if events else 0,
            "lag1_rho": None,
            "lag1_p": None,
            "reason": "too few events"
        }
        continue

    # Sort by event ticker (chronological proxy)
    sorted_events = sorted(events, key=lambda x: x.get('event_ticker', ''))
    ratios = []
    for e in sorted_events:
        crps = e.get('kalshi_crps', 0)
        mae = e.get('mae_interior', 0) or e.get('mae_ta', 0)
        if mae > 0:
            ratios.append(crps / mae)

    if len(ratios) < 4:
        serial_corr_results[series_key] = {
            "n": len(ratios),
            "lag1_rho": None,
            "lag1_p": None,
            "reason": "too few ratios"
        }
        continue

    ratios_arr = np.array(ratios)
    rho, p = stats.spearmanr(ratios_arr[:-1], ratios_arr[1:])

    serial_corr_results[series_key] = {
        "n": len(ratios),
        "lag1_rho": float(rho),
        "lag1_p": float(p),
    }
    print(f"  {series_key} (n={len(ratios)}): ρ={rho:.3f}, p={p:.4f}")

# If per_event_data not in unified, compute from expanded_results
if not unified.get("per_event_data"):
    print("\n  Per-event data not in unified, computing from expanded_results...")

    # Original series from exp12/exp13
    exp13_crps_path = "data/exp13/crps_per_event.csv"
    if os.path.exists(exp13_crps_path):
        crps_df = pd.read_csv(exp13_crps_path)
        for series in crps_df['series'].unique():
            sdf = crps_df[crps_df['series'] == series].sort_values('event_ticker')
            if 'kalshi_crps' in sdf.columns and 'point_crps' in sdf.columns:
                ratios = (sdf['kalshi_crps'] / sdf['point_crps']).dropna().values
            elif 'crps_mae_ratio' in sdf.columns:
                ratios = sdf['crps_mae_ratio'].dropna().values
            else:
                continue

            if len(ratios) >= 4:
                rho, p = stats.spearmanr(ratios[:-1], ratios[1:])
                serial_corr_results[series] = {
                    "n": len(ratios),
                    "lag1_rho": float(rho),
                    "lag1_p": float(p),
                }
                print(f"  {series} (n={len(ratios)}): ρ={rho:.3f}, p={p:.4f}")

    # New series from expanded_results
    for series, events in expanded_results.items():
        if series in serial_corr_results and serial_corr_results[series].get('lag1_rho') is not None:
            continue
        sorted_events = sorted(events, key=lambda x: x.get('event_ticker', ''))
        ratios = []
        for e in sorted_events:
            crps = e.get('kalshi_crps', 0)
            mae = e.get('mae_interior', 0)
            if mae and mae > 0:
                ratios.append(crps / mae)

        if len(ratios) >= 4:
            ratios_arr = np.array(ratios)
            rho, p = stats.spearmanr(ratios_arr[:-1], ratios_arr[1:])
            serial_corr_results[series] = {
                "n": len(ratios),
                "lag1_rho": float(rho),
                "lag1_p": float(p),
            }
            print(f"  {series} (n={len(ratios)}): ρ={rho:.3f}, p={p:.4f}")
        else:
            serial_corr_results[series] = {
                "n": len(ratios),
                "lag1_rho": None,
                "lag1_p": None,
                "reason": "too few ratios"
            }


# ============================================================
# ANALYSIS 3: GDP TEMPORAL SNAPSHOT SENSITIVITY
# ============================================================
print("\n" + "=" * 70)
print("ANALYSIS 3: GDP TEMPORAL SNAPSHOT SENSITIVITY")
print("=" * 70)

# Load GDP data from experiment12/13 data
gdp_temporal = {}

# GDP is an original series — load from exp12/exp2 data
exp12_crps_path = "data/exp12/crps_results.json"
if os.path.exists(exp12_crps_path):
    with open(exp12_crps_path) as f:
        exp12_results = json.load(f)

# We need to recompute CRPS at different snapshot percentiles for GDP
# Check if we have candle data for GDP events
# GDP uses old-naming (GDP-*) and possibly KXGDP-*
# The candle data is in data/exp2/raw/candles/

exp2_candles_dir = "data/exp2/raw/candles"
strike_markets_path = "data/exp7/strike_markets.csv"

if os.path.exists(strike_markets_path):
    sm_df = pd.read_csv(strike_markets_path)
    gdp_markets = sm_df[sm_df['event_ticker'].str.startswith(('GDP-', 'KXGDP-'))].copy()
    gdp_events = gdp_markets['event_ticker'].unique()
    print(f"  Found {len(gdp_events)} GDP events in strike_markets.csv")

    # For each GDP event, we need candle data to build CDFs at different percentiles
    gdp_snapshot_results = {}
    percentiles = [0.10, 0.25, 0.50, 0.75, 0.90]

    for event_ticker in gdp_events:
        event_markets_df = gdp_markets[gdp_markets['event_ticker'] == event_ticker]
        tickers = event_markets_df['ticker'].unique()

        # Load candles for these tickers
        candles_by_ticker = {}
        for ticker in tickers:
            candle_path = os.path.join(exp2_candles_dir, f"{ticker}.json")
            if os.path.exists(candle_path):
                with open(candle_path) as f:
                    candles_by_ticker[ticker] = json.load(f)

        if len(candles_by_ticker) < 2:
            continue

        # Build event markets list compatible with build_cdf_from_candles
        event_market_list = []
        for _, row in event_markets_df.iterrows():
            event_market_list.append({
                'ticker': row['ticker'],
                'floor_strike': row.get('floor_strike'),
                'event_ticker': event_ticker,
            })

        # Get realized value
        realized = None
        for _, row in event_markets_df.iterrows():
            exp_val = row.get('expiration_value')
            if pd.notna(exp_val):
                realized = parse_expiration_value_fixed(str(exp_val))
                if realized is not None:
                    break

        if realized is None:
            # Try from exp12 results
            if os.path.exists("data/exp12/crps_per_event.csv"):
                crps_ev_df = pd.read_csv("data/exp12/crps_per_event.csv")
                gdp_row = crps_ev_df[crps_ev_df['event_ticker'] == event_ticker]
                if len(gdp_row) > 0:
                    realized = gdp_row.iloc[0].get('realized')

        if realized is None:
            continue

        snapshots = build_cdf_from_candles(event_market_list, candles_by_ticker)
        if len(snapshots) < 5:
            continue

        # Compute CRPS at each percentile
        event_snap_results = {}
        for pct in percentiles:
            idx = int(pct * (len(snapshots) - 1))
            snap = snapshots[idx]
            strikes = snap['strikes']
            cdf_values = snap['cdf_values']
            tail_ext = max((strikes[-1] - strikes[0]) * 0.5, 1.0)
            crps = compute_crps(strikes, cdf_values, realized, tail_extension=tail_ext)
            interior_mean, ta_mean = compute_implied_mean(strikes, cdf_values)
            mae = abs(interior_mean - realized) if interior_mean is not None else None
            ratio = crps / mae if mae and mae > 0 else None
            event_snap_results[str(pct)] = {
                "crps": float(crps),
                "mae": float(mae) if mae else None,
                "ratio": float(ratio) if ratio else None,
            }

        gdp_snapshot_results[event_ticker] = {
            "realized": realized,
            "n_snapshots": len(snapshots),
            "percentile_results": event_snap_results,
        }
        print(f"  {event_ticker}: realized={realized}, n_snapshots={len(snapshots)}, "
              f"ratios={[event_snap_results.get(str(p), {}).get('ratio', 'N/A') for p in percentiles]}")

    # Aggregate: compute mean ratio at each percentile
    print(f"\n  GDP Temporal Snapshot Summary:")
    for pct in percentiles:
        pct_key = str(pct)
        ratios = [r['percentile_results'].get(pct_key, {}).get('ratio')
                  for r in gdp_snapshot_results.values() if r['percentile_results'].get(pct_key, {}).get('ratio') is not None]
        if ratios:
            mean_r = np.mean(ratios)
            all_below = all(r < 1.0 for r in ratios)
            print(f"    {int(pct*100)}%: mean ratio={mean_r:.3f}, "
                  f"all<1.0={all_below}, n={len(ratios)}, "
                  f"range=[{min(ratios):.3f}, {max(ratios):.3f}]")
            gdp_temporal[pct_key] = {
                "mean_ratio": float(mean_r),
                "all_below_1": all_below,
                "n": len(ratios),
                "min": float(min(ratios)),
                "max": float(max(ratios)),
                "ratios": [float(r) for r in ratios],
            }
else:
    print("  No strike_markets.csv found — GDP temporal analysis skipped")


# ============================================================
# ANALYSIS 4: KXPCECORE DISCREPANCY INVESTIGATION
# ============================================================
print("\n" + "=" * 70)
print("ANALYSIS 4: KXPCECORE DISCREPANCY INVESTIGATION")
print("=" * 70)

pcecore_path = "data/new_series/KXPCECORE_results.json"
if os.path.exists(pcecore_path):
    with open(pcecore_path) as f:
        pcecore_events = json.load(f)

    print(f"  Current KXPCECORE: {len(pcecore_events)} events")

    # Compute per-event ratios
    pcecore_ratios = []
    for e in pcecore_events:
        crps = e.get('kalshi_crps', 0)
        mae = e.get('mae_interior', 0)
        if mae and mae > 0:
            ratio = crps / mae
            pcecore_ratios.append({
                "event": e['event_ticker'],
                "realized": e.get('realized'),
                "crps": crps,
                "mae": mae,
                "ratio": ratio,
                "n_snapshots": e.get('n_snapshots', 0),
                "n_strikes": e.get('n_strikes', 0),
            })
            print(f"    {e['event_ticker']}: ratio={ratio:.3f}, "
                  f"CRPS={crps:.4f}, MAE={mae:.4f}, "
                  f"snaps={e.get('n_snapshots', 0)}, "
                  f"strikes={e.get('n_strikes', 0)}")

    if pcecore_ratios:
        ratios_arr = np.array([r['ratio'] for r in pcecore_ratios])
        print(f"\n  Summary: n={len(ratios_arr)}, mean={ratios_arr.mean():.3f}, "
              f"median={np.median(ratios_arr):.3f}")
        print(f"  Events with ratio > 2.0: "
              f"{[r['event'] for r in pcecore_ratios if r['ratio'] > 2.0]}")
        print(f"  Events with ratio > 1.5: "
              f"{[r['event'] for r in pcecore_ratios if r['ratio'] > 1.5]}")

    # Load KXPCECORE markets to find total available events
    pce_markets_path = "data/new_series/KXPCECORE_markets.json"
    if os.path.exists(pce_markets_path):
        with open(pce_markets_path) as f:
            pce_markets = json.load(f)
        pce_event_tickers = set(m.get('event_ticker') for m in pce_markets)
        print(f"\n  Total KXPCECORE events in markets data: {len(pce_event_tickers)}")
        computed_tickers = set(e['event_ticker'] for e in pcecore_events)
        missing = pce_event_tickers - computed_tickers
        if missing:
            print(f"  Missing events (no CRPS computed): {sorted(missing)}")
            # Check if these missing events have candle data
            pce_candles_path = "data/new_series/KXPCECORE_candles.json"
            if os.path.exists(pce_candles_path):
                with open(pce_candles_path) as f:
                    pce_candles = json.load(f)
                print(f"  Candle data covers {len(pce_candles)} tickers")


# ============================================================
# ANALYSIS 5: CROSS-SERIES HORSE RACE (KXU3, KXFRM)
# ============================================================
print("\n" + "=" * 70)
print("ANALYSIS 5: CROSS-SERIES HORSE RACE")
print("=" * 70)

def fetch_fred_csv(series_id, start_date="2020-01-01", end_date="2026-06-01"):
    """Fetch FRED data via CSV API (no key needed)."""
    import urllib.request
    url = (f"https://fred.stlouisfed.org/graph/fredgraph.csv"
           f"?id={series_id}&cosd={start_date}&coed={end_date}")
    print(f"  Fetching FRED {series_id}...")
    try:
        response = urllib.request.urlopen(url, timeout=30)
        content = response.read().decode('utf-8')
        lines = content.strip().split('\n')
        data = []
        for line in lines[1:]:
            parts = line.split(',')
            if len(parts) >= 2 and parts[1] != '.':
                try:
                    data.append({
                        'date': pd.Timestamp(parts[0]),
                        'value': float(parts[1])
                    })
                except ValueError:
                    continue
        df = pd.DataFrame(data)
        print(f"    Got {len(df)} observations")
        return df
    except Exception as e:
        print(f"    Error: {e}")
        return pd.DataFrame()


# Horse race for KXU3 (Unemployment Rate) vs UNRATE
print("\n--- KXU3 (Unemployment) vs UNRATE ---")
fred_unrate = fetch_fred_csv("UNRATE", "2022-01-01", "2026-06-01")

if len(fred_unrate) > 0 and "KXU3" in new_series_events:
    kxu3_events = new_series_events["KXU3"]

    # For each event, get the realized value and the Kalshi implied mean
    # Then compare with random walk (previous month) and trailing mean
    horse_race_u3 = []

    # Get sorted UNRATE values
    fred_unrate = fred_unrate.sort_values('date')
    unrate_values = fred_unrate['value'].values
    unrate_dates = fred_unrate['date'].values

    for event in sorted(kxu3_events, key=lambda x: x['event_ticker']):
        realized = event['realized']
        kalshi_mean = event.get('implied_mean_ta', event.get('implied_mean'))

        if realized is None or kalshi_mean is None:
            continue

        # Find the previous UNRATE observation as random walk
        # Extract month from event ticker (e.g., KXU3-25JAN → Jan 2025)
        ticker = event['event_ticker']

        # Find the FRED observation closest to but before the release
        # Use realized value directly since UNRATE is the unemployment rate
        prev_values = fred_unrate[fred_unrate['value'] != realized].copy()

        # Simple: use the FRED values up to one month before the likely release
        # For monthly data, random walk = previous month's reading
        idx = None
        for i, val in enumerate(unrate_values):
            if abs(val - realized) < 0.01:  # Found the matching release
                idx = i
                break

        if idx is not None and idx >= 1:
            random_walk = unrate_values[idx - 1]
        elif idx is not None and idx >= 0:
            random_walk = unrate_values[idx]  # fallback
        else:
            # Can't find matching, use simple heuristic
            random_walk = None

        # Trailing mean (last 12 months)
        if idx is not None and idx >= 2:
            start = max(0, idx - 12)
            trailing = float(np.mean(unrate_values[start:idx]))
        else:
            trailing = None

        kalshi_mae = abs(kalshi_mean - realized)
        rw_mae = abs(random_walk - realized) if random_walk is not None else None
        trail_mae = abs(trailing - realized) if trailing is not None else None

        horse_race_u3.append({
            "event": ticker,
            "realized": realized,
            "kalshi_mean": kalshi_mean,
            "kalshi_mae": kalshi_mae,
            "random_walk": random_walk,
            "rw_mae": rw_mae,
            "trailing": trailing,
            "trail_mae": trail_mae,
        })

    if horse_race_u3:
        print(f"\n  KXU3 horse race: {len(horse_race_u3)} events")

        # Compute paired tests
        kalshi_maes = np.array([e['kalshi_mae'] for e in horse_race_u3])
        rw_maes = np.array([e['rw_mae'] for e in horse_race_u3 if e['rw_mae'] is not None])
        trail_maes = np.array([e['trail_mae'] for e in horse_race_u3 if e['trail_mae'] is not None])

        # Filter to matched pairs
        paired_rw = [(e['kalshi_mae'], e['rw_mae']) for e in horse_race_u3 if e['rw_mae'] is not None]
        paired_trail = [(e['kalshi_mae'], e['trail_mae']) for e in horse_race_u3 if e['trail_mae'] is not None]

        print(f"    Mean Kalshi MAE: {kalshi_maes.mean():.4f}")

        if len(paired_rw) >= 5:
            k_arr = np.array([p[0] for p in paired_rw])
            r_arr = np.array([p[1] for p in paired_rw])
            print(f"    Mean RW MAE: {r_arr.mean():.4f}")

            if not np.all(k_arr == r_arr):
                w_stat, w_p = stats.wilcoxon(k_arr, r_arr, alternative='less')
                # Cohen's d
                diff = k_arr - r_arr
                d = diff.mean() / diff.std() if diff.std() > 0 else 0
                print(f"    Kalshi vs RW: d={d:.3f}, p={w_p:.4f}")
            else:
                w_p = 1.0
                d = 0.0
                print(f"    Kalshi vs RW: identical, no test")

        if len(paired_trail) >= 5:
            k_arr = np.array([p[0] for p in paired_trail])
            t_arr = np.array([p[1] for p in paired_trail])
            print(f"    Mean Trailing MAE: {t_arr.mean():.4f}")

            if not np.all(k_arr == t_arr):
                w_stat, w_p_trail = stats.wilcoxon(k_arr, t_arr, alternative='less')
                diff = k_arr - t_arr
                d_trail = diff.mean() / diff.std() if diff.std() > 0 else 0
                print(f"    Kalshi vs Trail: d={d_trail:.3f}, p={w_p_trail:.4f}")


# Horse race for KXFRM (Mortgage Rates) vs MORTGAGE30US
print("\n--- KXFRM (Mortgage Rates) vs MORTGAGE30US ---")
fred_mortgage = fetch_fred_csv("MORTGAGE30US", "2022-01-01", "2026-06-01")

if len(fred_mortgage) > 0 and "KXFRM" in new_series_events:
    kxfrm_events = new_series_events["KXFRM"]

    fred_mortgage = fred_mortgage.sort_values('date')
    mortgage_values = fred_mortgage['value'].values
    mortgage_dates = fred_mortgage['date'].values

    horse_race_frm = []

    for event in sorted(kxfrm_events, key=lambda x: x['event_ticker']):
        realized = event['realized']
        kalshi_mean = event.get('implied_mean_ta', event.get('implied_mean'))

        if realized is None or kalshi_mean is None:
            continue

        # Find closest FRED observation to the realized value
        idx = None
        for i, val in enumerate(mortgage_values):
            if abs(val - realized) < 0.02:
                idx = i
                break

        if idx is not None and idx >= 1:
            random_walk = mortgage_values[idx - 1]
        else:
            random_walk = None

        if idx is not None and idx >= 2:
            start = max(0, idx - 12)
            trailing = float(np.mean(mortgage_values[start:idx]))
        else:
            trailing = None

        kalshi_mae = abs(kalshi_mean - realized)
        rw_mae = abs(random_walk - realized) if random_walk is not None else None
        trail_mae = abs(trailing - realized) if trailing is not None else None

        horse_race_frm.append({
            "event": event['event_ticker'],
            "realized": realized,
            "kalshi_mean": kalshi_mean,
            "kalshi_mae": kalshi_mae,
            "random_walk": random_walk,
            "rw_mae": rw_mae,
            "trailing": trailing,
            "trail_mae": trail_mae,
        })

    if horse_race_frm:
        print(f"\n  KXFRM horse race: {len(horse_race_frm)} events")
        kalshi_maes = np.array([e['kalshi_mae'] for e in horse_race_frm])

        paired_rw = [(e['kalshi_mae'], e['rw_mae']) for e in horse_race_frm if e['rw_mae'] is not None]
        paired_trail = [(e['kalshi_mae'], e['trail_mae']) for e in horse_race_frm if e['trail_mae'] is not None]

        print(f"    Mean Kalshi MAE: {kalshi_maes.mean():.4f}")

        if len(paired_rw) >= 5:
            k_arr = np.array([p[0] for p in paired_rw])
            r_arr = np.array([p[1] for p in paired_rw])
            print(f"    Mean RW MAE: {r_arr.mean():.4f}")

            if not np.all(k_arr == r_arr):
                w_stat, w_p = stats.wilcoxon(k_arr, r_arr, alternative='less')
                diff = k_arr - r_arr
                d = diff.mean() / diff.std() if diff.std() > 0 else 0
                print(f"    Kalshi vs RW: d={d:.3f}, p={w_p:.4f}")

        if len(paired_trail) >= 5:
            k_arr = np.array([p[0] for p in paired_trail])
            t_arr = np.array([p[1] for p in paired_trail])
            print(f"    Mean Trailing MAE: {t_arr.mean():.4f}")

            if not np.all(k_arr == t_arr):
                w_stat, w_p_trail = stats.wilcoxon(k_arr, t_arr, alternative='less')
                diff = k_arr - t_arr
                d_trail = diff.mean() / diff.std() if diff.std() > 0 else 0
                print(f"    Kalshi vs Trail: d={d_trail:.3f}, p={w_p_trail:.4f}")


# ============================================================
# SAVE ALL RESULTS
# ============================================================
print("\n" + "=" * 70)
print("SAVING RESULTS")
print("=" * 70)

all_results = {
    "pit_results": pit_results,
    "serial_correlation": serial_corr_results,
    "gdp_temporal_snapshots": gdp_temporal,
    "gdp_snapshot_per_event": gdp_snapshot_results if 'gdp_snapshot_results' in dir() else {},
    "pcecore_investigation": {
        "n_events": len(pcecore_events) if 'pcecore_events' in dir() else 0,
        "per_event_ratios": pcecore_ratios if 'pcecore_ratios' in dir() else [],
    },
    "horse_race_kxu3": horse_race_u3 if 'horse_race_u3' in dir() else [],
    "horse_race_kxfrm": horse_race_frm if 'horse_race_frm' in dir() else [],
}

output_path = os.path.join(OUTPUT_DIR, "iteration6_results.json")
with open(output_path, 'w') as f:
    json.dump(all_results, f, indent=2, default=str)
print(f"  Saved to {output_path}")

print("\n" + "=" * 70)
print("ALL ANALYSES COMPLETE")
print("=" * 70)
