"""
experiment1/data_collection.py

Fetch markets, identify concurrent pairs, and extract hourly price series
for pairwise Granger causality analysis.
"""

import os
import json
import time
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone
from tqdm import tqdm

from kalshi.client import KalshiClient
from experiment5.data_collection import CACHE_PATH as EXP5_CACHE

# Fine-grained domain map for lead-lag analysis.
# Splits "economics" into sub-domains so we can find cross-sub-domain causal links.
FINE_DOMAIN_MAP = {
    # Inflation
    "KXCPI": "inflation", "KXPCE": "inflation", "KXPPI": "inflation",
    "CPI": "inflation",
    # Monetary policy
    "KXFED": "monetary_policy", "KXFFR": "monetary_policy",
    "FED": "monetary_policy",
    # Labor
    "KXNFP": "labor", "KXJOBLESSCLAIMS": "labor",
    "KXUNEMPLOYMENT": "labor", "KXBRAZILJOBS": "labor",
    # Macro
    "KXGDP": "macro", "KXRETAILSALES": "macro", "KXISM": "macro",
    "KXRECESSION": "macro", "GDP": "macro",
    # Fiscal
    "KXDEBTCEILING": "fiscal", "KXSHUTDOWN": "fiscal",
    # Finance
    "KXUSDBRL": "finance", "KXEARNINGS": "finance", "KXEARNINGSMENTIO": "finance",
    "KXSPY": "finance", "KXSP500": "finance", "KXNASDAQ": "finance", "KXDOW": "finance",
    # Crypto
    "KXBTC": "crypto", "KXBTCD": "crypto", "KXBTCW": "crypto",
    "KXETH": "crypto", "KXETHD": "crypto", "KXETHW": "crypto",
    "KXSOL": "crypto", "KXSOLD": "crypto", "KXSOLW": "crypto",
    # Sports
    "KXNBA": "basketball", "KXNCAAMBGAME": "basketball",
    "KXNCAAMBSPREAD": "basketball", "KXNCAAMBTOTAL": "basketball",
    "KXNBASPREAD": "basketball", "KXNBATOTAL": "basketball", "KXNBAPTS": "basketball",
    "KXNBAGAME": "basketball",
    # Politics
    "KXELECTION": "politics", "KXTARIFF": "politics",
    "KXTRUMP": "politics", "KXPOTUS": "politics",
}


def extract_fine_domain(ticker: str) -> str:
    """Classify market into fine-grained domain from ticker prefix."""
    prefix = ticker.split("-")[0] if "-" in ticker else ticker
    if prefix in FINE_DOMAIN_MAP:
        return FINE_DOMAIN_MAP[prefix]
    for key, domain in FINE_DOMAIN_MAP.items():
        if prefix.startswith(key):
            return domain
    return "other"

DATA_DIR = "data/exp1"
RAW_DIR = os.path.join(DATA_DIR, "raw")

EXP2_TARGETED_CACHE = "data/exp2/raw/targeted_markets.json"


def load_all_markets(max_markets: int = None) -> list:
    """Load settled markets from experiment caches.

    Merges exp5 generic cache with exp2 targeted economics/finance cache
    to ensure cross-domain coverage for lead-lag analysis.
    """
    seen_tickers = set()
    markets = []

    # Load exp2 targeted markets first (economics, finance, politics)
    if os.path.exists(EXP2_TARGETED_CACHE):
        print(f"Loading targeted markets from exp2 cache ({EXP2_TARGETED_CACHE})...")
        with open(EXP2_TARGETED_CACHE) as f:
            targeted = json.load(f)
        for m in targeted:
            ticker = m.get("ticker", "")
            if ticker and ticker not in seen_tickers:
                seen_tickers.add(ticker)
                markets.append(m)
        print(f"  Loaded {len(markets)} targeted markets")

    # Add exp5 generic markets (sports, weather, esports, etc.)
    if os.path.exists(EXP5_CACHE):
        print(f"Loading markets from exp5 cache ({EXP5_CACHE})...")
        with open(EXP5_CACHE) as f:
            generic = json.load(f)
        added = 0
        for m in generic:
            ticker = m.get("ticker", "")
            if ticker and ticker not in seen_tickers:
                seen_tickers.add(ticker)
                markets.append(m)
                added += 1
        print(f"  Added {added} generic markets (total: {len(markets)})")

    if not markets:
        # Fallback: fetch fresh from API
        print("No caches found, fetching from API...")
        client = KalshiClient()
        twelve_months_ago = int((datetime.now(timezone.utc) - timedelta(days=365)).timestamp())
        two_days_ago = int((datetime.now(timezone.utc) - timedelta(days=2)).timestamp())
        markets = client.get_all_pages(
            "/markets",
            params={
                "status": "settled",
                "min_settled_ts": twelve_months_ago,
                "max_settled_ts": two_days_ago,
                "limit": 1000,
            },
            result_key="markets",
            page_limit=max_markets // 1000 + 1 if max_markets else 100,
            show_progress=True,
        )

    if max_markets:
        markets = markets[:max_markets]
    return markets


def prepare_market_metadata(markets: list, min_lifespan_hours: int = 24) -> pd.DataFrame:
    """Extract metadata for concurrent pair analysis.

    Filters to binary-outcome markets with volume >= 10, valid time windows,
    and minimum lifespan to exclude ultra-short-lived markets (e.g. 15-min crypto).
    """
    rows = []
    for m in markets:
        result = m.get("result", "")
        if result not in ("yes", "no"):
            continue

        ticker = m.get("ticker", "")
        if not ticker:
            continue
        # Derive series_ticker from ticker prefix (e.g., KXBTC15M-26FEB092315-15 -> KXBTC15M)
        series_ticker = m.get("series_ticker") or (ticker.split("-")[0] if "-" in ticker else ticker)

        volume = int(m.get("volume", 0))
        if volume < 10:
            continue

        open_time = m.get("open_time", "")
        close_time = m.get("close_time", "")
        if not open_time or not close_time:
            continue

        domain = extract_fine_domain(ticker)

        rows.append({
            "ticker": ticker,
            "series_ticker": series_ticker,
            "event_ticker": m.get("event_ticker", ""),
            "domain": domain,
            "title": m.get("title", ""),
            "result": 1 if result == "yes" else 0,
            "volume": volume,
            "open_time": open_time,
            "close_time": close_time,
            "settlement_ts": m.get("settlement_ts", ""),
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df["open_time"] = pd.to_datetime(df["open_time"], format="ISO8601", errors="coerce")
    df["close_time"] = pd.to_datetime(df["close_time"], format="ISO8601", errors="coerce")
    df["settlement_ts"] = pd.to_datetime(df["settlement_ts"], format="ISO8601", errors="coerce")

    # Drop rows with invalid timestamps
    df = df.dropna(subset=["open_time", "close_time"]).reset_index(drop=True)

    # Filter by minimum lifespan
    if min_lifespan_hours > 0:
        lifespan = (df["close_time"] - df["open_time"]).dt.total_seconds() / 3600
        before = len(df)
        df = df[lifespan >= min_lifespan_hours].reset_index(drop=True)
        print(f"  Filtered by lifespan >= {min_lifespan_hours}h: {before} -> {len(df)}")

    print(f"  Prepared {len(df)} markets across {df['domain'].nunique()} domains")
    print(f"  Domain distribution: {df['domain'].value_counts().head(10).to_dict()}")

    return df


def find_concurrent_pairs(
    df: pd.DataFrame,
    min_overlap_hours: int = 48,
    max_pairs: int = 50000,
    cross_domain_only: bool = True,
) -> list[tuple[str, str]]:
    """Find all pairs of markets with overlapping time windows.

    Args:
        df: Market metadata with open_time, close_time columns
        min_overlap_hours: Minimum overlap in hours to form a pair
        max_pairs: Cap on total pairs to prevent explosion
        cross_domain_only: If True, only pair markets from different domains

    Returns:
        List of (ticker_A, ticker_B) tuples
    """
    pairs = []
    n = len(df)

    # Pre-compute for speed
    tickers = df["ticker"].values
    event_tickers = df["event_ticker"].values
    domains = df["domain"].values
    opens = df["open_time"].values
    closes = df["close_time"].values

    min_overlap = np.timedelta64(min_overlap_hours, "h")

    print(f"Finding concurrent pairs from {n} markets (min overlap: {min_overlap_hours}h)...")
    checked = 0
    for i in range(n):
        for j in range(i + 1, n):
            # Skip same-event pairs (trivially correlated)
            if event_tickers[i] == event_tickers[j]:
                continue

            # Skip same-domain if cross_domain_only
            if cross_domain_only and domains[i] == domains[j]:
                continue

            # Compute overlap
            overlap_start = max(opens[i], opens[j])
            overlap_end = min(closes[i], closes[j])
            overlap = overlap_end - overlap_start

            if overlap >= min_overlap:
                pairs.append((tickers[i], tickers[j]))

            checked += 1
            if len(pairs) >= max_pairs:
                break
        if len(pairs) >= max_pairs:
            print(f"  Hit max_pairs cap ({max_pairs})")
            break

    print(f"  Found {len(pairs)} concurrent pairs (checked {checked} combinations)")
    return pairs


def fetch_hourly_prices(
    client: KalshiClient,
    df: pd.DataFrame,
    max_markets: int = None,
) -> dict[str, pd.Series]:
    """Fetch hourly candlestick data for all markets, return as {ticker: pd.Series}.

    Reuses experiment2's candle fetching and caching infrastructure.
    """
    cache_path = os.path.join(DATA_DIR, "hourly_prices.json")
    if os.path.exists(cache_path):
        print(f"Loading cached hourly prices from {cache_path}...")
        with open(cache_path) as f:
            raw = json.load(f)
        # Convert back to pd.Series
        result = {}
        for ticker, entries in raw.items():
            timestamps = [e[0] for e in entries]
            prices = [e[1] for e in entries]
            idx = pd.to_datetime(timestamps, unit="s", utc=True)
            result[ticker] = pd.Series(prices, index=idx, name=ticker, dtype=float)
        print(f"  Loaded prices for {len(result)} markets")
        return result

    from experiment2.data_collection import fetch_candles_for_market, extract_candle_price

    markets_to_fetch = df if max_markets is None else df.head(max_markets)
    result = {}
    raw_for_cache = {}

    for _, row in tqdm(markets_to_fetch.iterrows(), total=len(markets_to_fetch), desc="Fetching candles"):
        ticker = row["ticker"]
        series_ticker = row["series_ticker"]
        start_ts = int(row["open_time"].timestamp())
        end_ts = int(row["close_time"].timestamp())

        candles = fetch_candles_for_market(
            client, ticker, series_ticker, start_ts, end_ts, period_interval=60
        )

        if not candles:
            continue

        # Extract hourly prices
        timestamps = []
        prices = []
        for c in candles:
            ts = c.get("end_period_ts")
            price = extract_candle_price(c)
            if ts is not None and not np.isnan(price):
                timestamps.append(int(ts))
                prices.append(float(price))

        if len(timestamps) < 10:
            continue

        idx = pd.to_datetime(timestamps, unit="s", utc=True)
        result[ticker] = pd.Series(prices, index=idx, name=ticker, dtype=float)
        raw_for_cache[ticker] = list(zip(timestamps, prices))

    # Cache
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(cache_path, "w") as f:
        json.dump(raw_for_cache, f)
    print(f"  Cached hourly prices for {len(result)} markets")

    return result


def build_aligned_pair_series(
    hourly_prices: dict[str, pd.Series],
    pair: tuple[str, str],
    min_overlap: int = 48,
) -> tuple[pd.Series, pd.Series] | None:
    """For a pair of tickers, align their hourly series on common timestamps.

    Returns (series_a, series_b) or None if insufficient overlap.
    """
    ticker_a, ticker_b = pair
    if ticker_a not in hourly_prices or ticker_b not in hourly_prices:
        return None

    series_a = hourly_prices[ticker_a]
    series_b = hourly_prices[ticker_b]

    # Align on common timestamps
    combined = pd.concat([series_a, series_b], axis=1).dropna()

    if len(combined) < min_overlap:
        return None

    return combined.iloc[:, 0], combined.iloc[:, 1]
