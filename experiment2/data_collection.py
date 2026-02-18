"""
experiment2/data_collection.py

Fetches Kalshi markets, classifies them into uncertainty domains,
fetches daily candlestick price data, and downloads EPU + VIX external data.

Reuses experiment5's cached settled markets where available.
"""

import os
import json
import time
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone
from tqdm import tqdm

DATA_DIR = "data/exp2"
RAW_DIR = os.path.join(DATA_DIR, "raw")
EXP5_CACHE = "data/exp5/all_settled_markets.json"

# Fine-grained uncertainty domain classification
UNCERTAINTY_DOMAIN_MAP = {
    # Monetary Policy
    "KXFED": "monetary_policy",
    "KXFFR": "monetary_policy",
    # Inflation
    "KXCPI": "inflation",
    "KXPCE": "inflation",
    "KXPPI": "inflation",
    # Labor Market
    "KXJOBLESSCLAIMS": "labor_market",
    "KXNFP": "labor_market",
    "KXUNEMPLOYMENT": "labor_market",
    # Fiscal / Macro
    "KXDEBTCEILING": "fiscal_policy",
    "KXSHUTDOWN": "fiscal_policy",
    "KXRECESSION": "fiscal_policy",
    "KXGDP": "fiscal_policy",
    "KXRETAILSALES": "fiscal_policy",
    "KXISM": "fiscal_policy",
    # Crypto
    "KXBTC": "crypto",
    "KXBTC15M": "crypto",
    "KXBTCW": "crypto",
    "KXETH": "crypto",
    "KXETH15M": "crypto",
    "KXETHW": "crypto",
    "KXSOL": "crypto",
    "KXSOL15M": "crypto",
    "KXSOLW": "crypto",
    "KXDOGE": "crypto",
    "KXXRP": "crypto",
    # Finance / Market Indices
    "KXSPY": "finance",
    "KXSP500": "finance",
    "KXNASDAQ": "finance",
    "KXDOW": "finance",
    # Geopolitics
    "KXTARIFF": "geopolitics",
    "KXRUSSIA": "geopolitics",
    "KXCHINA": "geopolitics",
    # Politics
    "KXELECTION": "politics",
    "KXTRUMP": "politics",
    "KXPOTUS": "politics",
    "KXSENATE": "politics",
    "KXHOUSE": "politics",
    "KXSUPREMECOURT": "politics",
    "KXGOVERNOR": "politics",
}

# Domains relevant to economic uncertainty (exclude sports, weather, esports)
KUI_DOMAINS = {
    "monetary_policy", "inflation", "labor_market", "fiscal_policy",
    "crypto", "finance", "geopolitics", "politics",
}


def classify_uncertainty_domain(ticker: str) -> str:
    """Classify a market ticker into an uncertainty domain.

    Returns the domain name or 'excluded' for irrelevant markets.
    """
    prefix = ticker.split("-")[0] if "-" in ticker else ticker

    # Direct match
    if prefix in UNCERTAINTY_DOMAIN_MAP:
        return UNCERTAINTY_DOMAIN_MAP[prefix]

    # Partial match (some tickers have extra suffixes)
    for key, domain in UNCERTAINTY_DOMAIN_MAP.items():
        if prefix.startswith(key):
            return domain

    return "excluded"


def load_settled_markets(client=None, max_markets: int = None) -> list:
    """Load all settled markets, reusing experiment5 cache if available.

    Args:
        client: Optional KalshiClient (only needed if cache doesn't exist)
        max_markets: Optional cap on markets to fetch

    Returns:
        List of market dicts
    """
    # Try experiment5 cache first
    if os.path.exists(EXP5_CACHE):
        print(f"Loading cached markets from {EXP5_CACHE}...")
        with open(EXP5_CACHE) as f:
            markets = json.load(f)
        print(f"  Loaded {len(markets)} cached markets")
        if max_markets:
            markets = markets[:max_markets]
        return markets

    # Try our own cache
    our_cache = os.path.join(RAW_DIR, "all_settled_markets.json")
    if os.path.exists(our_cache):
        print(f"Loading cached markets from {our_cache}...")
        with open(our_cache) as f:
            markets = json.load(f)
        print(f"  Loaded {len(markets)} cached markets")
        if max_markets:
            markets = markets[:max_markets]
        return markets

    # Fetch from API
    if client is None:
        from kalshi.client import KalshiClient
        client = KalshiClient()

    twelve_months_ago = int((datetime.now(timezone.utc) - timedelta(days=365)).timestamp())
    two_days_ago = int((datetime.now(timezone.utc) - timedelta(days=2)).timestamp())

    print("Fetching ALL settled markets from past 12 months...")
    all_markets = []
    cursor = None
    page_limit = 1000

    pbar = tqdm(desc="Fetching markets", unit=" markets")

    while True:
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

        if max_markets and len(all_markets) >= max_markets:
            all_markets = all_markets[:max_markets]
            break

        cursor = resp.get("cursor", "")
        if not cursor:
            break

        time.sleep(0.7)

    pbar.close()
    print(f"  Fetched {len(all_markets)} total settled markets")

    os.makedirs(RAW_DIR, exist_ok=True)
    with open(our_cache, "w") as f:
        json.dump(all_markets, f, indent=2, default=str)

    return all_markets


# Series tickers to specifically target for KUI-relevant markets
KUI_TARGET_SERIES = [
    # Economics - core
    "KXCPI", "KXPCE", "KXPPI",           # Inflation
    "KXFED", "KXFFR",                     # Monetary policy
    "KXNFP", "KXJOBLESSCLAIMS",           # Labor
    "KXUNEMPLOYMENT",
    "KXGDP", "KXRETAILSALES", "KXISM",    # Macro
    "KXRECESSION", "KXDEBTCEILING", "KXSHUTDOWN",  # Fiscal
    # Crypto (daily/weekly only, skip 15-min)
    "KXBTCD", "KXBTCW",                   # BTC daily/weekly
    "KXETHD", "KXETHW",                   # ETH daily/weekly
    "KXSOLD", "KXSOLW",                   # SOL daily/weekly
    "KXBTC", "KXETH", "KXSOL",           # BTC/ETH/SOL range markets
    # Finance
    "KXSPY", "KXSP500", "KXNASDAQ", "KXDOW",
    # Geopolitics / politics
    "KXTARIFF", "KXTRUMP", "KXPOTUS",
    "KXELECTION", "KXSENATE", "KXHOUSE",
]


def fetch_targeted_markets(client, series_tickers: list = None) -> list:
    """Fetch settled markets for specific series tickers.

    This targets economics/finance series that generic pagination misses.

    Args:
        client: KalshiClient
        series_tickers: List of series tickers to query

    Returns:
        List of market dicts
    """
    cache_path = os.path.join(RAW_DIR, "targeted_markets.json")
    if os.path.exists(cache_path):
        print(f"Loading cached targeted markets from {cache_path}...")
        with open(cache_path) as f:
            markets = json.load(f)
        print(f"  Loaded {len(markets)} cached targeted markets")
        return markets

    if series_tickers is None:
        series_tickers = KUI_TARGET_SERIES

    twelve_months_ago = int((datetime.now(timezone.utc) - timedelta(days=365)).timestamp())

    all_markets = []
    seen_tickers = set()

    print(f"Fetching targeted markets for {len(series_tickers)} series...")
    for series in tqdm(series_tickers, desc="Series"):
        try:
            resp = client.get("/markets", params={
                "series_ticker": series,
                "status": "settled",
                "limit": 1000,
            })
            items = resp.get("markets", [])

            for m in items:
                ticker = m.get("ticker", "")
                if ticker not in seen_tickers:
                    seen_tickers.add(ticker)
                    all_markets.append(m)

            time.sleep(0.7)

        except Exception as e:
            print(f"  Warning: failed to fetch series {series}: {e}")
            continue

    print(f"  Fetched {len(all_markets)} unique targeted markets")

    os.makedirs(RAW_DIR, exist_ok=True)
    with open(cache_path, "w") as f:
        json.dump(all_markets, f, indent=2, default=str)

    return all_markets


def prepare_market_dataset(markets: list) -> pd.DataFrame:
    """Classify markets into uncertainty domains and filter to KUI-relevant ones.

    Returns DataFrame with columns:
        ticker, event_ticker, domain, title, open_time, close_time,
        settlement_ts, result, volume, last_price_dollars, series_ticker
    """
    rows = []
    for m in markets:
        ticker = m.get("ticker", "")
        domain = classify_uncertainty_domain(ticker)

        if domain == "excluded":
            continue

        # Parse series_ticker from ticker
        series_ticker = ticker.split("-")[0] if "-" in ticker else ticker

        rows.append({
            "ticker": ticker,
            "event_ticker": m.get("event_ticker", ""),
            "series_ticker": series_ticker,
            "domain": domain,
            "title": m.get("title", ""),
            "open_time": m.get("open_time", ""),
            "close_time": m.get("close_time", ""),
            "settlement_ts": m.get("settlement_ts", ""),
            "result": m.get("result", ""),
            "volume": int(m.get("volume", 0)),
            "last_price_dollars": float(m.get("last_price_dollars", 0)),
        })

    df = pd.DataFrame(rows)

    if df.empty:
        return df

    # Parse timestamps
    df["open_time"] = pd.to_datetime(df["open_time"], format="ISO8601", errors="coerce")
    df["close_time"] = pd.to_datetime(df["close_time"], format="ISO8601", errors="coerce")
    df["settlement_ts"] = pd.to_datetime(df["settlement_ts"], format="ISO8601", errors="coerce")

    # Filter to markets with minimum volume
    min_vol = 5
    df = df[df["volume"] >= min_vol].reset_index(drop=True)

    print(f"  KUI-relevant markets: {len(df)}")
    print(f"  Domain distribution:")
    for domain, count in df["domain"].value_counts().items():
        print(f"    {domain}: {count}")

    return df


def fetch_candles_for_market(
    client, ticker: str, series_ticker: str,
    start_ts: int, end_ts: int,
    period_interval: int = 60,
) -> list:
    """Fetch candlestick data for a single market.

    Args:
        period_interval: 60 = hourly, 1440 = daily. Hourly gives better
            coverage for short-lived markets.

    Returns list of candlestick dicts.
    """
    cache_path = os.path.join(
        RAW_DIR, "candles", f"{ticker.replace('/', '_')}_{period_interval}.json"
    )

    if os.path.exists(cache_path):
        with open(cache_path) as f:
            return json.load(f)

    try:
        candles = client.get_all_pages(
            f"/series/{series_ticker}/markets/{ticker}/candlesticks",
            params={
                "start_ts": start_ts,
                "end_ts": end_ts,
                "period_interval": period_interval,
            },
            result_key="candlesticks",
        )

        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, "w") as f:
            json.dump(candles, f, indent=2, default=str)

        return candles

    except Exception as e:
        return []


def extract_candle_price(candle: dict) -> float:
    """Extract a price from a candlestick dict. Returns NaN if unavailable."""
    # Try price.close_dollars
    price_obj = candle.get("price", {})
    if price_obj:
        close = price_obj.get("close_dollars")
        if close is not None:
            try:
                return float(close)
            except (ValueError, TypeError):
                pass

    # Fallback: bid-ask midpoint
    yes_bid = candle.get("yes_bid", {})
    yes_ask = candle.get("yes_ask", {})
    bid_close = yes_bid.get("close_dollars") if yes_bid else None
    ask_close = yes_ask.get("close_dollars") if yes_ask else None

    if bid_close is not None and ask_close is not None:
        try:
            return (float(bid_close) + float(ask_close)) / 2.0
        except (ValueError, TypeError):
            pass

    if bid_close is not None:
        try:
            return float(bid_close)
        except (ValueError, TypeError):
            pass

    if ask_close is not None:
        try:
            return float(ask_close)
        except (ValueError, TypeError):
            pass

    return np.nan


def fetch_all_market_candles(
    client, df: pd.DataFrame, max_markets: int = None
) -> dict:
    """Fetch candlestick data for all KUI-relevant markets and aggregate to daily.

    Uses hourly candles (period_interval=60) for better coverage of
    short-lived markets, then aggregates to daily closing prices.

    Args:
        client: KalshiClient
        df: Market dataset (from prepare_market_dataset)
        max_markets: Optional cap for testing

    Returns:
        Dict mapping ticker -> list of (date_str, price) tuples (daily)
    """
    candles_cache = os.path.join(DATA_DIR, "daily_prices_by_ticker.json")
    if os.path.exists(candles_cache):
        print(f"Loading cached daily prices from {candles_cache}...")
        with open(candles_cache) as f:
            return json.load(f)

    markets_to_fetch = df
    if max_markets:
        markets_to_fetch = df.head(max_markets)

    print(f"Fetching hourly candles for {len(markets_to_fetch)} markets...")
    daily_prices = {}
    n_empty = 0

    for _, row in tqdm(markets_to_fetch.iterrows(), total=len(markets_to_fetch),
                       desc="Fetching candles"):
        ticker = row["ticker"]
        series_ticker = row["series_ticker"]

        open_time = row["open_time"]
        close_time = row["close_time"]

        if pd.isna(open_time) or pd.isna(close_time):
            continue

        start_ts = int(open_time.timestamp())
        end_ts = int(close_time.timestamp())

        candles = fetch_candles_for_market(
            client, ticker, series_ticker, start_ts, end_ts,
            period_interval=60,  # Hourly candles
        )

        if not candles:
            n_empty += 1
            continue

        # Extract hourly prices and aggregate to daily (last price per day)
        hourly_prices = {}
        for c in candles:
            ts = c.get("end_period_ts", 0)
            price = extract_candle_price(c)
            if not np.isnan(price) and ts > 0:
                date_str = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
                # Keep the latest price for each day
                hourly_prices[date_str] = price

        if hourly_prices:
            daily_prices[ticker] = sorted(hourly_prices.items())

        time.sleep(0.1)

    print(f"  Markets with candle data: {len(daily_prices)}")
    print(f"  Markets with no data: {n_empty}")

    # Cache results
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(candles_cache, "w") as f:
        json.dump(daily_prices, f, indent=2)
    print(f"  Cached daily prices for {len(daily_prices)} markets")

    return daily_prices


def fetch_fred_csv(series_id: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Fetch a time series from FRED as CSV.

    Args:
        series_id: FRED series ID (e.g., 'VIXCLS', 'USEPUINDXD')
        start_date: 'YYYY-MM-DD'
        end_date: 'YYYY-MM-DD'

    Returns:
        DataFrame with columns: date, value
    """
    import requests

    url = (
        f"https://fred.stlouisfed.org/graph/fredgraph.csv"
        f"?id={series_id}&cosd={start_date}&coed={end_date}"
    )

    cache_path = os.path.join(RAW_DIR, f"fred_{series_id}.csv")
    if os.path.exists(cache_path):
        print(f"Loading cached FRED {series_id} from {cache_path}")
        df = pd.read_csv(cache_path)
        df.columns = ["date", "value"]
        df["date"] = pd.to_datetime(df["date"])
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        return df.dropna()

    print(f"Fetching FRED series {series_id}...")
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()

        os.makedirs(RAW_DIR, exist_ok=True)
        with open(cache_path, "w") as f:
            f.write(resp.text)

        df = pd.read_csv(cache_path)
        df.columns = ["date", "value"]
        df["date"] = pd.to_datetime(df["date"])
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        return df.dropna()

    except Exception as e:
        print(f"  Failed to fetch FRED {series_id}: {e}")
        return pd.DataFrame(columns=["date", "value"])


def fetch_vix_daily(start_date: str = "2025-02-01", end_date: str = "2026-02-11") -> pd.DataFrame:
    """Fetch VIX daily close from FRED (VIXCLS series)."""
    return fetch_fred_csv("VIXCLS", start_date, end_date)


def fetch_epu_daily(start_date: str = "2025-02-01", end_date: str = "2026-02-11") -> pd.DataFrame:
    """Fetch US Economic Policy Uncertainty Index (daily) from FRED."""
    df = fetch_fred_csv("USEPUINDXD", start_date, end_date)
    if df.empty:
        # Fallback: try monthly EPU
        print("  Daily EPU not available, trying monthly...")
        df = fetch_fred_csv("USEPUINDXM", start_date, end_date)
    return df


def fetch_sp500_daily(start_date: str = "2025-02-01", end_date: str = "2026-02-11") -> pd.DataFrame:
    """Fetch S&P 500 daily close from FRED (SP500 series)."""
    return fetch_fred_csv("SP500", start_date, end_date)


def main(quick_test: bool = False, max_markets: int = None):
    """Run the full data collection pipeline."""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(RAW_DIR, exist_ok=True)

    # Step 1: Load settled markets — use targeted fetch for economics series
    print("=" * 70)
    print("STEP 1: Fetch Targeted KUI-Relevant Markets")
    print("=" * 70)

    from kalshi.client import KalshiClient
    client = KalshiClient()

    # Targeted fetch: query specific series for economics/finance markets
    targeted = fetch_targeted_markets(client)

    # Also load general cache for broader coverage
    general_cap = max_markets or (500 if quick_test else None)
    general = load_settled_markets(client, max_markets=general_cap)

    # Merge: targeted markets + any KUI-relevant from general
    seen = {m.get("ticker") for m in targeted}
    combined = list(targeted)
    for m in general:
        t = m.get("ticker", "")
        if t not in seen and classify_uncertainty_domain(t) != "excluded":
            combined.append(m)
            seen.add(t)

    print(f"  Combined: {len(combined)} KUI-relevant markets")

    # Step 2: Classify into uncertainty domains
    print("\n" + "=" * 70)
    print("STEP 2: Classify Markets into Uncertainty Domains")
    print("=" * 70)
    df = prepare_market_dataset(combined)
    df.to_csv(os.path.join(DATA_DIR, "markets.csv"), index=False)

    # Step 3: Fetch hourly candlesticks (aggregated to daily)
    print("\n" + "=" * 70)
    print("STEP 3: Fetch Candlestick Data")
    print("=" * 70)
    candle_cap = 50 if quick_test else None
    daily_prices = fetch_all_market_candles(client, df, max_markets=candle_cap)

    # Step 4: Fetch external data
    print("\n" + "=" * 70)
    print("STEP 4: Fetch External Data (VIX, EPU, S&P 500)")
    print("=" * 70)
    vix = fetch_vix_daily()
    epu = fetch_epu_daily()
    sp500 = fetch_sp500_daily()

    vix.to_csv(os.path.join(DATA_DIR, "vix_daily.csv"), index=False)
    epu.to_csv(os.path.join(DATA_DIR, "epu_daily.csv"), index=False)
    sp500.to_csv(os.path.join(DATA_DIR, "sp500_daily.csv"), index=False)

    print(f"\n  VIX: {len(vix)} days")
    print(f"  EPU: {len(epu)} days")
    print(f"  S&P 500: {len(sp500)} days")
    print(f"  Kalshi markets with candle data: {len(daily_prices)}")

    return df, daily_prices, vix, epu, sp500


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick-test", action="store_true")
    parser.add_argument("--max-markets", type=int, default=None)
    args = parser.parse_args()
    main(quick_test=args.quick_test, max_markets=args.max_markets)
