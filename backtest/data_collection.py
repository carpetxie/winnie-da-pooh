"""
backtest/data_collection.py

Phase 1: Universal Calibration Data Collection

Fetches N=3000 random settled markets from Kalshi, computes features at
each market's midpoint, and saves to universal_features.csv.

Run with: uv run python -m backtest.data_collection
"""

import os
import json
import time
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone

from backtest.kalshi_client import KalshiClient

# Configuration
N_MARKETS = 3000  # Target sample size
RAW_DIR = "data/raw"
PROCESSED_DIR = "data/processed"


def fetch_all_settled_markets(client: KalshiClient) -> pd.DataFrame:
    """
    Fetch ALL settled markets from past 12 months.

    Returns:
        DataFrame with all settled markets (ticker, series_ticker, open_time, close_time, result, etc.)
    """
    twelve_months_ago = int((datetime.now(timezone.utc) - timedelta(days=365)).timestamp())

    cache_path = os.path.join(RAW_DIR, "all_settled_markets.json")

    if os.path.exists(cache_path):
        print("Loading cached settled markets...")
        with open(cache_path) as f:
            markets = json.load(f)
    else:
        print("Fetching ALL settled markets from Kalshi (this may take 2-3 minutes)...")
        markets = client.get_all_pages(
            "/markets",
            params={
                "status": "settled",
                "min_settled_ts": twelve_months_ago,
            },
            result_key="markets",
        )

        with open(cache_path, "w") as f:
            json.dump(markets, f, indent=2, default=str)

    print(f"✓ Fetched {len(markets)} settled markets")
    return pd.DataFrame(markets)


def sample_markets(df: pd.DataFrame, n: int) -> pd.DataFrame:
    """
    Sample N markets, prioritizing weekly frequency.

    Strategy:
    1. Group by series_ticker
    2. Get series metadata (frequency)
    3. Prioritize weekly series
    4. Sample N markets with diversity across series
    """
    # Add series frequency (requires fetching series metadata)
    # For simplicity, just do random sampling across all markets
    # You can enhance this later to filter by frequency

    if len(df) <= n:
        print(f"⚠ Only {len(df)} markets available, using all")
        return df

    # Random sample
    sampled = df.sample(n=n, random_state=42)
    print(f"✓ Sampled {n} markets")
    return sampled


def fetch_candlesticks(client: KalshiClient, ticker: str, series_ticker: str,
                       start_ts: int, end_ts: int) -> list:
    """
    Fetch daily candlesticks for a market.

    Args:
        ticker: Market ticker (e.g., "KXJOBLESSCLAIMS-26FEB05-270000")
        series_ticker: Series ticker (e.g., "KXJOBLESSCLAIMS")
        start_ts: Start timestamp (Unix seconds)
        end_ts: End timestamp (Unix seconds)

    Returns:
        List of candlestick dicts
    """
    cache_path = os.path.join(RAW_DIR, f"candles_{ticker.replace('/', '_')}.json")

    if os.path.exists(cache_path):
        with open(cache_path) as f:
            return json.load(f)

    try:
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

        return candles

    except Exception as e:
        print(f"⚠ Candlestick fetch failed for {ticker}: {e}")
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

    # Extract price (in dollars, already 0.0-1.0)
    price_obj = closest.get('price', {})
    close_dollars = price_obj.get('close_dollars')

    if close_dollars is not None:
        try:
            return float(close_dollars)
        except (ValueError, TypeError):
            pass

    # Fallback to previous price
    previous_dollars = price_obj.get('previous_dollars')
    if previous_dollars:
        try:
            return float(previous_dollars)
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
            price_obj = c.get('price', {})
            close_dollars = price_obj.get('close_dollars')
            if close_dollars:
                try:
                    prices.append(float(close_dollars))
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

    for idx, row in markets_df.iterrows():
        ticker = row['ticker']
        series_ticker = row.get('series_ticker', 'UNKNOWN')

        # Parse timestamps
        open_time = pd.to_datetime(row['open_time'])
        close_time = pd.to_datetime(row['close_time'])
        midpoint = open_time + (close_time - open_time) / 2

        # Calculate days remaining
        days_remaining = (close_time - midpoint).total_seconds() / 86400

        # Get result
        result_str = row.get('result', '')
        y_true = 1 if result_str == 'yes' else 0

        # Fetch candlesticks
        start_ts = int(open_time.timestamp())
        end_ts = int(close_time.timestamp())

        candles = fetch_candlesticks(client, ticker, series_ticker, start_ts, end_ts)

        # Extract features
        midpoint_ts = midpoint.timestamp()
        feature_price = extract_price_at_midpoint(candles, midpoint_ts)
        feature_volatility = calculate_volatility(candles, midpoint_ts)

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

        if (idx + 1) % 100 == 0:
            print(f"  Processed {idx + 1}/{len(markets_df)} markets...")

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
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    client = KalshiClient()

    # Step 1: Fetch all settled markets
    print("=" * 60)
    print("STEP 1: Fetch All Settled Markets")
    print("=" * 60)
    all_markets_df = fetch_all_settled_markets(client)

    # Step 2: Sample N markets
    print("\n" + "=" * 60)
    print(f"STEP 2: Sample {N_MARKETS} Markets")
    print("=" * 60)
    sampled_df = sample_markets(all_markets_df, N_MARKETS)

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
