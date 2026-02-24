"""
Fetch hourly candle data for old-prefix markets (CPI, FED, GDP)
that exist in targeted_markets.json but lack candle files.
"""
import os
import json
import time
import re
from datetime import datetime, timezone
from tqdm import tqdm

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kalshi.client import KalshiClient

CANDLE_DIR = "data/exp2/raw/candles"
TARGETED_MARKETS_PATH = "data/exp2/raw/targeted_markets.json"

# Old-prefix series we want candles for
OLD_PREFIXES = {"CPI", "FED", "GDP"}


def main():
    os.makedirs(CANDLE_DIR, exist_ok=True)

    # Load markets
    with open(TARGETED_MARKETS_PATH) as f:
        markets = json.load(f)

    # Filter to old-prefix markets that need candles
    need_fetch = []
    for m in markets:
        ticker = m.get("ticker", "")
        prefix_match = re.match(r"^([A-Z]+)", ticker)
        if not prefix_match:
            continue
        prefix = prefix_match.group(1)
        if prefix not in OLD_PREFIXES:
            continue

        candle_path = os.path.join(CANDLE_DIR, f"{ticker}_60.json")
        if os.path.exists(candle_path):
            continue

        need_fetch.append(m)

    print(f"Found {len(need_fetch)} old-prefix markets needing candle data")

    # Group by prefix
    by_prefix = {}
    for m in need_fetch:
        ticker = m["ticker"]
        prefix = re.match(r"^([A-Z]+)", ticker).group(1)
        by_prefix.setdefault(prefix, []).append(m)

    for prefix, ms in by_prefix.items():
        events = set()
        for m in ms:
            et = m.get("event_ticker", "")
            events.add(et)
        print(f"  {prefix}: {len(ms)} markets across {len(events)} events")

    if not need_fetch:
        print("All candle files already exist!")
        return

    # Initialize client
    client = KalshiClient()

    success = 0
    failed = 0
    empty = 0

    for m in tqdm(need_fetch, desc="Fetching candles"):
        ticker = m["ticker"]
        # series_ticker for old-prefix markets: just the prefix
        series_ticker = ticker.split("-")[0]

        open_time = m.get("open_time", "")
        close_time = m.get("close_time", "")

        try:
            start_ts = int(datetime.fromisoformat(open_time.replace("Z", "+00:00")).timestamp())
            end_ts = int(datetime.fromisoformat(close_time.replace("Z", "+00:00")).timestamp())
        except (ValueError, TypeError):
            failed += 1
            continue

        candle_path = os.path.join(CANDLE_DIR, f"{ticker}_60.json")

        try:
            candles = client.get_all_pages(
                f"/series/{series_ticker}/markets/{ticker}/candlesticks",
                params={
                    "start_ts": start_ts,
                    "end_ts": end_ts,
                    "period_interval": 60,
                },
                result_key="candlesticks",
            )

            with open(candle_path, "w") as f:
                json.dump(candles, f, indent=2, default=str)

            if candles:
                success += 1
            else:
                empty += 1

        except Exception as e:
            # If the series_ticker doesn't work, the API might use a different convention
            tqdm.write(f"  Failed {ticker} (series={series_ticker}): {e}")
            failed += 1

        time.sleep(0.7)  # Rate limiting

    print(f"\nDone: {success} success, {empty} empty, {failed} failed")


if __name__ == "__main__":
    main()
