"""
backtest/kalshi_client.py

Thin wrapper around the Kalshi v2 REST API.
Handles RSA-PSS request signing and cursor-based pagination.
"""

import os
import time
import base64
import datetime
import requests as http_lib  # aliased to avoid shadowing
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()


class KalshiClient:
    """
    Authenticated client for the Kalshi trading API.

    Usage:
        client = KalshiClient()
        markets = client.get("/markets", params={"series_ticker": "KCPI", "status": "settled"})
    """

    BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"
    # Sandbox for testing (no real money):
    # BASE_URL = "https://demo-api.kalshi.co/trade-api/v2"

    def __init__(self):
        self.key_id = os.getenv("KALSHI_KEY_ID")
        if not self.key_id:
            raise ValueError("KALSHI_KEY_ID not found in .env")

        key_path = os.getenv("KALSHI_PRIVATE_KEY_PATH")
        if not key_path or not os.path.exists(key_path):
            raise FileNotFoundError(f"Private key not found at: {key_path}")

        with open(key_path, "rb") as f:
            self.private_key = serialization.load_pem_private_key(
                f.read(), password=None, backend=default_backend()
            )

    def _sign(self, timestamp_ms: int, method: str, path: str) -> str:
        """
        Create RSA-PSS SHA256 signature over: "{timestamp}{METHOD}{path}"
        Returns base64-encoded signature string.
        """
        msg = f"{timestamp_ms}{method}{path}".encode("utf-8")
        sig = self.private_key.sign(
            msg,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.DIGEST_LENGTH,
            ),
            hashes.SHA256(),
        )
        return base64.b64encode(sig).decode("utf-8")

    def _headers(self, method: str, path: str) -> dict:
        """
        Build the three required authentication headers.
        `path` should NOT include query parameters — we strip them here
        as a safety measure.
        """
        ts = int(datetime.datetime.now().timestamp() * 1000)
        path_no_query = path.split("?")[0]
        return {
            "KALSHI-ACCESS-KEY": self.key_id,
            "KALSHI-ACCESS-TIMESTAMP": str(ts),
            "KALSHI-ACCESS-SIGNATURE": self._sign(ts, method, path_no_query),
        }

    def get(self, path: str, params: dict = None) -> dict:
        """
        Make a single authenticated GET request.

        `path` is relative to BASE_URL, e.g. "/markets" or "/markets/KCPI-25JAN-T0.3".
        `params` are query parameters passed to requests.get().
        Returns the parsed JSON response body as a dict.
        Raises on HTTP errors (4xx, 5xx).
        """
        r = http_lib.get(
            self.BASE_URL + path,
            headers=self._headers("GET", path),
            params=params,
        )
        r.raise_for_status()
        return r.json()

    def get_all_pages(
        self,
        path: str,
        params: dict = None,
        result_key: str = "markets",
        page_limit: int = 1000,
        delay: float = 0.7,
        show_progress: bool = False,
    ) -> list:
        """
        Fetch all pages of a paginated endpoint and return the concatenated list.

        Kalshi paginates via a `cursor` field in the response. An empty or missing
        cursor means there are no more pages.

        Arguments:
            path:        API path, e.g. "/markets"
            params:      Query parameters dict. Will be copied (not mutated).
            result_key:  The JSON key that holds the array of results.
                         For /markets this is "markets".
                         For /series this is "series".
                         For /candlesticks this is "candlesticks".
            page_limit:  Max items per page (sent as `limit` param). Kalshi max is 1000.
            delay:       Seconds to sleep between pages to stay under rate limit.
                         0.7s ≈ 85 requests/min, safely under the 100/min cap.
            show_progress: Show progress bar during pagination.

        Returns:
            A flat list of all result items across all pages.
        """
        params = dict(params or {})
        params["limit"] = page_limit
        all_results = []

        # Progress bar (unknown total, so counts items fetched)
        pbar = tqdm(desc=f"Fetching {result_key}", unit=" items", disable=not show_progress)

        page_num = 0
        while True:
            resp = self.get(path, params)
            items = resp.get(result_key, [])
            all_results.extend(items)

            if show_progress:
                pbar.update(len(items))
                pbar.set_postfix({"pages": page_num + 1})

            cursor = resp.get("cursor", "")
            if not cursor or len(items) < page_limit:
                break

            params["cursor"] = cursor
            page_num += 1
            time.sleep(delay)

        if show_progress:
            pbar.close()

        return all_results