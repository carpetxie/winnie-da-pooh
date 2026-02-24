"""Fetch hourly candle data for FED and GDP old-prefix markets."""
import os
import json
import time
import re
from datetime import datetime
from tqdm import tqdm
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from kalshi.client import KalshiClient

CANDLE_DIR = "data/exp2/raw/candles"
TARGETED_MARKETS_PATH = "data/exp2/raw/targeted_markets.json"

def main():
    os.makedirs(CANDLE_DIR, exist_ok=True)
    with open(TARGETED_MARKETS_PATH) as f:
        markets = json.load(f)

    need_fetch = []
    for m in markets:
        ticker = m.get("ticker", "")
        if not (ticker.startswith("FED-") or ticker.startswith("GDP-")):
            continue
        candle_path = os.path.join(CANDLE_DIR, f"{ticker}_60.json")
        if os.path.exists(candle_path):
            continue
        need_fetch.append(m)

    print(f"Need to fetch candles for {len(need_fetch)} FED/GDP markets")
    if not need_fetch:
        print("All candle files already exist!")
        return

    client = KalshiClient()
    success = 0
    failed = 0
    empty = 0

    for m in tqdm(need_fetch, desc="Fetching candles"):
        ticker = m["ticker"]
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
                params={"start_ts": start_ts, "end_ts": end_ts, "period_interval": 60},
                result_key="candlesticks",
            )
            with open(candle_path, "w") as f:
                json.dump(candles, f, indent=2, default=str)
            if candles:
                success += 1
            else:
                empty += 1
        except Exception as e:
            tqdm.write(f"  Failed {ticker}: {e}")
            failed += 1
        time.sleep(0.7)

    print(f"\nDone: {success} success, {empty} empty, {failed} failed")

if __name__ == "__main__":
    main()
