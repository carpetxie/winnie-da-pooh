"""
experiment5/data_collection.py

Fetches all settled Kalshi markets with text descriptions and outcomes.
Classifies markets into domains based on ticker prefix.
"""

import os
import json
import time
import pandas as pd
from datetime import datetime, timedelta, timezone
from tqdm import tqdm

from kalshi.client import KalshiClient

RAW_DIR = "data/exp5"
CACHE_PATH = os.path.join(RAW_DIR, "all_settled_markets.json")

# Domain classification from ticker prefix
DOMAIN_MAP = {
    # Economics
    "KXCPI": "economics", "KXPCE": "economics", "KXNFP": "economics",
    "KXFED": "economics", "KXFFR": "economics", "KXGDP": "economics",
    "KXJOBLESSCLAIMS": "economics", "KXRETAILSALES": "economics",
    "KXUNEMPLOYMENT": "economics", "KXDEBTCEILING": "economics",
    "KXSHUTDOWN": "economics", "KXRECESSION": "economics",
    "KXISM": "economics", "KXPPI": "economics",
    # Crypto
    "KXBTC": "crypto", "KXBTC15M": "crypto", "KXBTCW": "crypto",
    "KXETH": "crypto", "KXETH15M": "crypto", "KXETHW": "crypto",
    "KXSOL": "crypto", "KXSOL15M": "crypto", "KXSOLW": "crypto",
    "KXDOGE": "crypto", "KXXRP": "crypto",
    # Politics
    "KXELECTION": "politics", "KXTARIFF": "politics",
    "KXTRUMP": "politics", "KXPOTUS": "politics",
    "KXSENATE": "politics", "KXHOUSE": "politics",
    "KXSUPREMECOURT": "politics", "KXGOVERNOR": "politics",
    # Weather
    "KXTEMP": "weather", "KXHIGHTEMP": "weather",
    "KXLOWTEMP": "weather", "KXRAIN": "weather",
    "KXSNOW": "weather", "KXHURRICANE": "weather",
    # Sports - Basketball
    "KXNBA": "basketball", "KXNCAAMBGAME": "basketball",
    "KXNCAAMBSPREAD": "basketball", "KXNCAAMBTOTAL": "basketball",
    "KXNBASPREAD": "basketball", "KXNBATOTAL": "basketball",
    "KXNBAPTS": "basketball",
    # Sports - Hockey
    "KXNHL": "hockey", "KXNHLPTS": "hockey", "KXNHLAST": "hockey",
    "KXNHLGAME": "hockey", "KXNHLTOTAL": "hockey",
    # Sports - Football
    "KXNFL": "football", "KXNCAAFB": "football",
    "KXSUPERBOWL": "football",
    # Sports - Soccer
    "KXLALIGA": "soccer", "KXLALIGATOTAL": "soccer",
    "KXPREMIERLEAGUE": "soccer", "KXFACUP": "soccer",
    "KXFACUPGAME": "soccer", "KXUEFACL": "soccer",
    "KXMLS": "soccer", "KXSERIEA": "soccer",
    # Sports - Tennis
    "KXATP": "tennis", "KXATPMATCH": "tennis",
    "KXWTA": "tennis", "KXWTAMATCH": "tennis",
    # Sports - Other
    "KXUFC": "mma", "KXBOXING": "boxing",
    "KXMLB": "baseball", "KXF1": "motorsport",
    "KXNASCAR": "motorsport", "KXGOLF": "golf",
    # Esports
    "KXMVESPORTSMULTIGAMEEXTENDED": "esports",
    "KXMVESPORTS": "esports",
    # Market indices / finance
    "KXSPY": "finance", "KXSP500": "finance",
    "KXNASDAQ": "finance", "KXDOW": "finance",
    "KXRUSSIA": "geopolitics", "KXCHINA": "geopolitics",
}


def extract_domain(ticker: str) -> str:
    """Classify market domain from ticker prefix."""
    prefix = ticker.split("-")[0] if "-" in ticker else ticker

    # Direct match
    if prefix in DOMAIN_MAP:
        return DOMAIN_MAP[prefix]

    # Partial match (some tickers have extra suffixes)
    for key, domain in DOMAIN_MAP.items():
        if prefix.startswith(key):
            return domain

    return "other"


def extract_text(row: dict) -> str:
    """Build text for embedding from market fields."""
    parts = [row.get("title", "")]
    rules = row.get("rules_primary", "")
    if rules:
        parts.append(rules)
    return " | ".join(p for p in parts if p)


def extract_result_binary(row: dict) -> int:
    """Convert market result to binary outcome."""
    result = row.get("result", "")
    if result == "yes":
        return 1
    elif result == "no":
        return 0
    else:
        # Scalar results - treat as NaN (will be filtered)
        return -1


def fetch_all_settled_markets_full(client: KalshiClient, max_markets: int = None) -> list:
    """
    Fetch ALL settled markets from the past 12 months.
    Paginates through entire history without a cap.

    Args:
        client: Authenticated KalshiClient
        max_markets: Optional cap (None = fetch everything)

    Returns:
        List of market dicts
    """
    if os.path.exists(CACHE_PATH):
        print(f"Loading cached markets from {CACHE_PATH}...")
        with open(CACHE_PATH) as f:
            markets = json.load(f)
        print(f"  Loaded {len(markets)} cached markets")
        return markets

    twelve_months_ago = int((datetime.now(timezone.utc) - timedelta(days=365)).timestamp())
    two_days_ago = int((datetime.now(timezone.utc) - timedelta(days=2)).timestamp())

    print("Fetching ALL settled markets from past 12 months...")
    all_markets = []
    cursor = None
    page_limit = 1000
    page_num = 0

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
        page_num += 1
        pbar.set_postfix({"pages": page_num})

        if max_markets and len(all_markets) >= max_markets:
            all_markets = all_markets[:max_markets]
            break

        cursor = resp.get("cursor", "")
        if not cursor:
            break

        time.sleep(0.7)

    pbar.close()
    print(f"  Fetched {len(all_markets)} total settled markets")

    # Cache results
    os.makedirs(RAW_DIR, exist_ok=True)
    with open(CACHE_PATH, "w") as f:
        json.dump(all_markets, f, indent=2, default=str)
    print(f"  Cached to {CACHE_PATH}")

    return all_markets


def prepare_dataset(markets: list) -> pd.DataFrame:
    """
    Clean and prepare market data for the experiment.

    Returns DataFrame with columns:
        ticker, event_ticker, domain, title, rules_primary,
        text_for_embedding, result_binary, volume, settlement_ts,
        last_price_dollars, split
    """
    rows = []
    for m in markets:
        result_binary = extract_result_binary(m)
        if result_binary == -1:
            continue  # Skip scalar markets

        text = extract_text(m)
        if not text or len(text.strip()) < 5:
            continue  # Skip markets with no useful text

        domain = extract_domain(m.get("ticker", ""))

        rows.append({
            "ticker": m.get("ticker", ""),
            "event_ticker": m.get("event_ticker", ""),
            "domain": domain,
            "title": m.get("title", ""),
            "rules_primary": m.get("rules_primary", ""),
            "text_for_embedding": text,
            "result_binary": result_binary,
            "volume": int(m.get("volume", 0)),
            "settlement_ts": m.get("settlement_ts", ""),
            "last_price_dollars": float(m.get("last_price_dollars", 0)),
            "open_time": m.get("open_time", ""),
            "close_time": m.get("close_time", ""),
        })

    df = pd.DataFrame(rows)

    if df.empty:
        return df

    # Parse settlement timestamp for temporal split
    df["settlement_ts"] = pd.to_datetime(df["settlement_ts"], format="ISO8601", errors="coerce")

    # Domain balancing: cap any single domain to max 2x the second-largest domain
    # This prevents esports (which can be 80%+ of data) from drowning signal
    domain_counts = df["domain"].value_counts()
    if len(domain_counts) >= 2:
        second_largest = domain_counts.iloc[1]
        cap = max(second_largest * 2, 500)  # At least 500, or 2x second-largest
        largest_domain = domain_counts.index[0]
        if domain_counts.iloc[0] > cap:
            print(f"  Capping {largest_domain} from {domain_counts.iloc[0]} to {cap} markets")
            domain_mask = df["domain"] == largest_domain
            keep_idx = df[domain_mask].sample(n=cap, random_state=42).index
            drop_idx = df[domain_mask].index.difference(keep_idx)
            df = df.drop(drop_idx).reset_index(drop=True)

    # Temporal split: 80% train, 20% test
    df = df.sort_values("settlement_ts").reset_index(drop=True)
    split_idx = int(len(df) * 0.8)
    df["split"] = "test"
    df.loc[df.index[:split_idx], "split"] = "train"

    n_train = (df["split"] == "train").sum()
    n_test = (df["split"] == "test").sum()
    print(f"  Dataset: {len(df)} markets ({n_train} train, {n_test} test)")
    print(f"  Domains: {df['domain'].value_counts().to_dict()}")
    print(f"  Outcome balance: YES={df['result_binary'].sum()}, NO={len(df) - df['result_binary'].sum()}")

    return df


def main(quick_test: bool = False, max_markets: int = None):
    """Run data collection pipeline."""
    os.makedirs(RAW_DIR, exist_ok=True)

    client = KalshiClient()

    if quick_test:
        max_markets = max_markets or 500

    markets = fetch_all_settled_markets_full(client, max_markets=max_markets)
    df = prepare_dataset(markets)

    output_path = os.path.join(RAW_DIR, "markets.csv")
    df.to_csv(output_path, index=False)
    print(f"  Saved to {output_path}")

    return df


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick-test", action="store_true")
    parser.add_argument("--max-markets", type=int, default=None)
    args = parser.parse_args()
    main(quick_test=args.quick_test, max_markets=args.max_markets)
