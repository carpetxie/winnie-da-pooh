"""
backtest/data_collection.py

Phase 1: Universal Calibration Data Collection

Fetches N random settled markets from Kalshi, computes features at
each market's midpoint, and saves to universal_features.csv.

Run with:
    uv run python -m backtest.data_collection --n-markets 5     # Quick test
    uv run python -m backtest.data_collection --n-markets 3000  # Full run
    uv run python -m backtest.data_collection                   # Default (3000)
"""

import os
import json
import time
import argparse
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone
from tqdm import tqdm

from backtest.kalshi_client import KalshiClient

# Configuration
RAW_DIR = "data/raw"
PROCESSED_DIR = "data/processed"


def fetch_all_settled_markets(client: KalshiClient, quick_test: bool = False, n_needed: int = 5) -> pd.DataFrame:
    """
    Fetch settled markets from past 12 months.

    Args:
        client: KalshiClient instance
        quick_test: If True, only fetch a small subset for testing (default: False)
        n_needed: Number of markets needed (used for quick test sizing)

    Returns:
        DataFrame with all settled markets (ticker, series_ticker, open_time, close_time, result, etc.)
    """
    twelve_months_ago = int((datetime.now(timezone.utc) - timedelta(days=365)).timestamp())

    if quick_test:
        # Quick test mode: fetch only ONE page (no pagination)
        # Only fetch markets settled at least 2 days ago (so candlestick data exists)
        two_days_ago = int((datetime.now(timezone.utc) - timedelta(days=2)).timestamp())

        print(f"Quick test mode: Fetching markets settled 2+ days ago...")
        response = client.get(
            "/markets",
            params={
                "status": "settled",
                "min_settled_ts": twelve_months_ago,
                "max_settled_ts": two_days_ago,  # Only markets settled BEFORE 2 days ago
                "limit": max(10, n_needed * 2),
            }
        )
        markets = response.get("markets", [])

        # DEBUG: Print first market's keys to see available fields
        if markets:
            print(f"DEBUG: Market fields available: {list(markets[0].keys())}")

        print(f"✓ Fetched {len(markets)} settled markets")
        return pd.DataFrame(markets)

    # Full mode: fetch enough markets for sampling (not necessarily ALL)
    # Only fetch markets settled at least 2 days ago (so candlestick data exists)
    two_days_ago = int((datetime.now(timezone.utc) - timedelta(days=2)).timestamp())

    # Fetch 2x what we need for sampling diversity (capped at reasonable limit)
    target_fetch = min(n_needed * 2, 10000)  # Don't fetch more than 10k

    cache_path = os.path.join(RAW_DIR, f"settled_markets_{target_fetch}.json")

    if os.path.exists(cache_path):
        print(f"Loading cached settled markets (target: {target_fetch})...")
        with open(cache_path) as f:
            markets = json.load(f)
    else:
        print(f"Fetching ~{target_fetch} settled markets (settled 2+ days ago)...")

        # Fetch in batches until we have enough
        all_markets = []
        cursor = None
        page_limit = 1000

        pbar = tqdm(desc="Fetching markets", unit=" items", total=target_fetch)

        while len(all_markets) < target_fetch:
            params = {
                "status": "settled",
                "min_settled_ts": twelve_months_ago,
                "max_settled_ts": two_days_ago,
                "limit": page_limit,
            }
            if cursor:
                params["cursor"] = cursor

            resp = client.get("/markets", params=params)
            items = resp.get("markets", [])

            if not items:
                break

            all_markets.extend(items)
            pbar.update(len(items))
            pbar.set_postfix({"fetched": len(all_markets)})

            cursor = resp.get("cursor", "")
            if not cursor:
                break

            time.sleep(0.7)  # Rate limiting

        pbar.close()
        markets = all_markets

        with open(cache_path, "w") as f:
            json.dump(markets, f, indent=2, default=str)

    print(f"✓ Fetched {len(markets)} settled markets")
    return pd.DataFrame(markets)


def sample_markets(df: pd.DataFrame, n: int) -> pd.DataFrame:
    """
    Sample N markets, prioritizing those with longer lifespans.

    Strategy:
    1. Filter to markets open for at least 2 days (so candlestick data exists)
    2. Sample N markets with diversity
    """
    # Calculate market lifespan
    df['open_time'] = pd.to_datetime(df['open_time'], format='ISO8601')
    df['close_time'] = pd.to_datetime(df['close_time'], format='ISO8601')
    df['lifespan_days'] = (df['close_time'] - df['open_time']).dt.total_seconds() / 86400

    # Filter to markets open for at least 2 days
    df_long = df[df['lifespan_days'] >= 2].copy()

    print(f"✓ Filtered {len(df)} markets → {len(df_long)} with lifespan ≥ 2 days")

    if len(df_long) <= n:
        print(f"⚠ Only {len(df_long)} markets available, using all")
        return df_long

    # Random sample
    sampled = df_long.sample(n=n, random_state=42)
    print(f"✓ Sampled {n} markets")
    return sampled


def fetch_candlesticks(client: KalshiClient, ticker: str, series_ticker: str,
                       start_ts: int, end_ts: int, debug: bool = False) -> list:
    """
    Fetch daily candlesticks for a market.

    Args:
        ticker: Market ticker (e.g., "KXJOBLESSCLAIMS-26FEB05-270000")
        series_ticker: Series ticker (e.g., "KXJOBLESSCLAIMS")
        start_ts: Start timestamp (Unix seconds)
        end_ts: End timestamp (Unix seconds)
        debug: Print debug info

    Returns:
        List of candlestick dicts
    """
    cache_path = os.path.join(RAW_DIR, f"candles_{ticker.replace('/', '_')}.json")

    if os.path.exists(cache_path):
        with open(cache_path) as f:
            candles = json.load(f)
            if debug:
                print(f"  ✓ Loaded {len(candles)} cached candles for {ticker}")
            return candles

    try:
        if debug:
            print(f"  Fetching /series/{series_ticker}/markets/{ticker}/candlesticks")

        candles = client.get_all_pages(
            f"/series/{series_ticker}/markets/{ticker}/candlesticks",
            params={
                "start_ts": start_ts,
                "end_ts": end_ts,
                "period_interval": 1440,  # Daily
            },
            result_key="candlesticks",
        )

        with open(cache_path, "w") as f:
            json.dump(candles, f, indent=2, default=str)

        if debug:
            print(f"  ✓ Fetched {len(candles)} candles for {ticker}")

        return candles

    except Exception as e:
        if debug:
            print(f"  ✗ Candlestick fetch failed for {ticker}: {e}")
        return []


def extract_price_at_midpoint(candles: list, midpoint_ts: float) -> float:
    """
    Find candle closest to midpoint timestamp and extract price.

    Args:
        candles: List of candlestick dicts
        midpoint_ts: Target timestamp (Unix seconds)

    Returns:
        Price at midpoint (0.0-1.0), or NaN if no data
    """
    if not candles:
        return np.nan

    # Find closest candle
    closest = min(candles, key=lambda c: abs(c.get('end_period_ts', 0) - midpoint_ts))

    # Try 1: price.close_dollars (direct price)
    price_obj = closest.get('price', {})
    close_dollars = price_obj.get('close_dollars')
    if close_dollars is not None:
        try:
            return float(close_dollars)
        except (ValueError, TypeError):
            pass

    # Try 2: Midpoint of bid-ask spread
    yes_bid = closest.get('yes_bid', {})
    yes_ask = closest.get('yes_ask', {})

    bid_close = yes_bid.get('close_dollars')
    ask_close = yes_ask.get('close_dollars')

    if bid_close is not None and ask_close is not None:
        try:
            bid = float(bid_close)
            ask = float(ask_close)
            return (bid + ask) / 2.0  # Midpoint of bid-ask
        except (ValueError, TypeError):
            pass

    # Try 3: Just use bid if available
    if bid_close is not None:
        try:
            return float(bid_close)
        except (ValueError, TypeError):
            pass

    # Try 4: Just use ask if available
    if ask_close is not None:
        try:
            return float(ask_close)
        except (ValueError, TypeError):
            pass

    return np.nan


def calculate_volatility(candles: list, midpoint_ts: float, lookback_days: int = 7) -> float:
    """
    Calculate standard deviation of prices in the lookback_days before midpoint.

    Args:
        candles: List of candlestick dicts
        midpoint_ts: Midpoint timestamp
        lookback_days: Days to look back

    Returns:
        Volatility (std dev of prices), or 0.0 if insufficient data
    """
    if not candles:
        return 0.0

    lookback_start = midpoint_ts - (lookback_days * 86400)

    # Filter candles in lookback window
    prices = []
    for c in candles:
        ts = c.get('end_period_ts', 0)
        if lookback_start <= ts < midpoint_ts:
            # Try price.close_dollars first
            price_obj = c.get('price', {})
            close_dollars = price_obj.get('close_dollars')

            if close_dollars is not None:
                try:
                    prices.append(float(close_dollars))
                    continue
                except (ValueError, TypeError):
                    pass

            # Fallback to bid-ask midpoint
            yes_bid = c.get('yes_bid', {})
            yes_ask = c.get('yes_ask', {})
            bid_close = yes_bid.get('close_dollars')
            ask_close = yes_ask.get('close_dollars')

            if bid_close is not None and ask_close is not None:
                try:
                    bid = float(bid_close)
                    ask = float(ask_close)
                    prices.append((bid + ask) / 2.0)
                except (ValueError, TypeError):
                    pass

    if len(prices) < 2:
        return 0.0

    return float(np.std(prices))


def compute_features(client: KalshiClient, markets_df: pd.DataFrame) -> pd.DataFrame:
    """
    For each market, compute features at midpoint.

    Returns:
        DataFrame with columns: ticker, series_ticker, open_time, close_time, midpoint,
                                feature_price, feature_volatility, feature_days_remaining, y_true
    """
    results = []

    # Progress bar for feature computation
    debug = len(markets_df) <= 10  # Enable debug for small samples

    for idx, row in tqdm(markets_df.iterrows(), total=len(markets_df), desc="Computing features", disable=debug):
        ticker = row['ticker']

        # Infer series_ticker from ticker (no series_ticker field in API)
        # Format: SERIESNAME-DATE-DETAILS → extract SERIESNAME
        # Example: KXIPODEEL-26FEB01 → KXIPODEEL
        series_ticker = ticker.split('-')[0] if '-' in ticker else 'UNKNOWN'

        # Parse timestamps
        open_time = pd.to_datetime(row['open_time'], format='ISO8601')
        close_time = pd.to_datetime(row['close_time'], format='ISO8601')
        midpoint = open_time + (close_time - open_time) / 2

        # Calculate days remaining
        days_remaining = (close_time - midpoint).total_seconds() / 86400

        # Get result
        result_str = row.get('result', '')
        y_true = 1 if result_str == 'yes' else 0

        if debug:
            print(f"\n[{idx+1}/{len(markets_df)}] {ticker}")
            print(f"  series_ticker: {series_ticker}")
            print(f"  midpoint: {midpoint}")
            print(f"  open: {open_time}, close: {close_time}")

        # Fetch candlesticks
        start_ts = int(open_time.timestamp())
        end_ts = int(close_time.timestamp())

        candles = fetch_candlesticks(client, ticker, series_ticker, start_ts, end_ts, debug=debug)

        # Extract features
        midpoint_ts = midpoint.timestamp()
        feature_price = extract_price_at_midpoint(candles, midpoint_ts)
        feature_volatility = calculate_volatility(candles, midpoint_ts)

        if debug:
            print(f"  feature_price: {feature_price}")
            print(f"  feature_volatility: {feature_volatility}")

        results.append({
            'ticker': ticker,
            'series_ticker': series_ticker,
            'open_time': open_time,
            'close_time': close_time,
            'midpoint': midpoint,
            'feature_price': feature_price,
            'feature_volatility': feature_volatility,
            'feature_days_remaining': days_remaining,
            'y_true': y_true,
        })

        # Rate limiting
        time.sleep(0.1)

    return pd.DataFrame(results)


def temporal_split(df: pd.DataFrame, train_frac: float = 0.8) -> pd.DataFrame:
    """
    Split into train/test by close_time (earliest 80% = train, latest 20% = test).

    Adds 'split' column: "train" or "test"
    """
    df = df.sort_values('close_time').copy()
    split_idx = int(len(df) * train_frac)

    df['split'] = 'test'
    df.loc[df.index[:split_idx], 'split'] = 'train'

    n_train = (df['split'] == 'train').sum()
    n_test = (df['split'] == 'test').sum()

    print(f"✓ Split: {n_train} train, {n_test} test")
    return df


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Collect market data for Universal Calibration')
    parser.add_argument('--n-markets', type=int, default=3000,
                        help='Number of markets to sample (default: 3000, use 5 for quick testing)')
    args = parser.parse_args()

    n_markets = args.n_markets

    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    client = KalshiClient()

    # Determine if quick test mode (< 100 markets)
    quick_test = n_markets < 100

    # Step 1: Fetch all settled markets
    print("=" * 60)
    print("STEP 1: Fetch Settled Markets")
    print("=" * 60)
    all_markets_df = fetch_all_settled_markets(client, quick_test=quick_test, n_needed=n_markets)

    # Step 2: Sample N markets
    print("\n" + "=" * 60)
    print(f"STEP 2: Sample {n_markets} Markets")
    print("=" * 60)
    sampled_df = sample_markets(all_markets_df, n_markets)

    # Step 3: Compute features
    print("\n" + "=" * 60)
    print("STEP 3: Compute Features (this will take ~10-15 minutes)")
    print("=" * 60)
    features_df = compute_features(client, sampled_df)

    # Step 4: Temporal split
    print("\n" + "=" * 60)
    print("STEP 4: Temporal Split (80/20)")
    print("=" * 60)
    features_df = temporal_split(features_df)

    # Step 5: Save
    output_path = os.path.join(PROCESSED_DIR, "universal_features.csv")
    features_df.to_csv(output_path, index=False)

    print("\n" + "=" * 60)
    print("✅ DATA COLLECTION COMPLETE")
    print("=" * 60)
    print(f"Saved: {output_path}")
    print(f"Total markets: {len(features_df)}")
    print(f"Markets with valid price: {features_df['feature_price'].notna().sum()}")
    print(f"Train: {(features_df['split'] == 'train').sum()}")
    print(f"Test: {(features_df['split'] == 'test').sum()}")


if __name__ == "__main__":
    main()
