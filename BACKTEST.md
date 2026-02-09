# BACKTEST.md: Kalshi RLM Backtesting Guide

## Table of Contents
1. [Overview](#1-overview)
2. [Prerequisites & API Setup](#2-prerequisites--api-setup)
3. [Project Setup with UV](#3-project-setup-with-uv)
4. [File Architecture & Data Flow](#4-file-architecture--data-flow)
5. [File 1: `backtest/kalshi_client.py`](#5-file-1-backtestkalshi_clientpy)
6. [File 2: `backtest/data_collection.py`](#6-file-2-backtestdata_collectionpy)
7. [File 3: `backtest/track_a.py`](#7-file-3-backtesttrack_apy)
8. [File 4: `backtest/track_b.py`](#8-file-4-backtesttrack_bpy)
9. [File 5: `backtest/backtest.py`](#9-file-5-backtestbacktestpy)
10. [File 6: `backtest/visualize.py`](#10-file-6-backtestvisualizepy)
11. [File 7: `run.py`](#11-file-7-runpy)
12. [Next Steps](#12-next-steps)
13. [Troubleshooting](#13-troubleshooting)

---

## 1. Overview

We are building a backtesting pipeline for the OOLONG-Kalshi system described in `RLM.md`. The system has two independent prediction tracks that get combined via a weighted log-odds ensemble:

- **Track A**: Lasso Logistic Regression using prices of related Kalshi markets as features
- **Track B**: Recursive Language Model analyzing news (initially **synthetic** to validate the pipeline)
- **Synthesis**: $L_{final} = \alpha \cdot L_{stat} + (1 - \alpha) \cdot L_{news}$, swept over $\alpha \in [0, 1]$ in 0.05 steps

**Methodology order:**
1. Build Phases 1–4 with **synthetic** Track B predictions
2. Run end-to-end, confirm the pipeline works and outputs are sane
3. **Then** replace Track B with real LLM calls (separate effort, not in this doc)

**Scope:**
- Most recent 12 months of Kalshi data
- First 6 months = training, last 6 months = testing
- Recurring binary markets with ≤2 week resolution (ideally weekly)
- Focus on economic indicator markets (CPI/PCE, Fed rates)

---

## 2. Prerequisites & API Setup

### 2.1 Kalshi API

Kalshi is a CFTC-regulated prediction market. We need their API to fetch historical prices and resolutions.

**Get your credentials:**

1. Create an account at https://kalshi.com (KYC required, no deposit needed)
2. Go to **Account Settings → Profile Settings** (https://kalshi.com/account/profile)
3. In the **"API Keys"** section, click **"Create New API Key"**
4. You'll get:
   - **Key ID**: a UUID like `a952bcbe-ec3b-4b5b-b8f9-11dae589608c`
   - **Private Key**: an RSA key in PEM format, auto-downloaded as a **`.txt` file**

   The private key looks like:
   ```
   -----BEGIN PRIVATE KEY-----
   MIIEvQIBADANBgkqhkiG9w0BAQEFAASC...
   -----END PRIVATE KEY-----
   ```

   **The private key is shown ONLY ONCE.** Save the `.txt` file immediately.

**Authentication mechanism:**

Kalshi uses **RSA-PSS with SHA256** to sign every request. Three headers are required:

| Header | Value |
|--------|-------|
| `KALSHI-ACCESS-KEY` | Your Key ID |
| `KALSHI-ACCESS-TIMESTAMP` | Current time in milliseconds since epoch |
| `KALSHI-ACCESS-SIGNATURE` | Base64-encoded RSA-PSS signature of `{timestamp}{HTTP_METHOD}{path}` |

**Important**: When signing, strip query parameters from the path. Sign `/markets`, NOT `/markets?limit=10`.

**Production base URL** (from OpenAPI spec):
```
https://api.elections.kalshi.com/trade-api/v2
```

**Demo/sandbox base URL:**
```
https://demo-api.kalshi.co/trade-api/v2
```

**API docs**: https://docs.kalshi.com/welcome

**Key endpoints** (paths are relative to base URL):
- `GET /markets` — list/filter markets (supports `series_ticker`, `status`, timestamp filters)
- `GET /markets/{ticker}` — single market details + resolution
- `GET /markets/{ticker}/candlesticks` — historical OHLC price data (`period_interval`: 1, 60, or 1440 min)
- `GET /series` — list all series (recurring event templates)
- `GET /series/{ticker}` — single series details

**Rate limit**: 100 requests/minute (standard tier).

---

### 2.2 LLM API (Grok) — Not Needed Yet

Track B starts as synthetic. When you're ready for real LLM calls:

1. Get a Grok API key from https://x.ai
2. Add `GROK_API_KEY=your_key_here` to `.env`

The code should use a simple provider-agnostic interface so you can swap to Claude, GPT-4, etc. later. Don't build this abstraction until Stage 2.

---

### 2.3 News/Web Search API — Not Needed Yet

Track B (real version) will need a news source. Two options:

| Provider | Free Tier | Paid | Notes |
|----------|-----------|------|-------|
| **SerpAPI** | 100 searches/month | $50/mo for 5k | Scrapes Google News |
| **NewsAPI** | 100 requests/day | $449/mo | 80k+ sources, 1-month lookback on free tier |

Pick one when you reach Stage 2. Add the key to `.env` as `SERPAPI_KEY` or `NEWSAPI_KEY`.

---

### 2.4 Credential Storage

Create a `.env` file in your project root:
```bash
# Kalshi
KALSHI_KEY_ID=your-uuid-here
KALSHI_PRIVATE_KEY_PATH=./kalshi_private_key.txt

# (Stage 2 — not needed yet)
# GROK_API_KEY=...
# SERPAPI_KEY=...
```

---

## 3. Project Setup with UV

### 3.1 Install UV

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv --version  # verify
```

### 3.2 Initialize Project

```bash
cd /Users/jeffreyxie/Desktop/winnie
uv init
```

### 3.3 Install Dependencies

```bash
uv add numpy pandas scikit-learn   # data science + Lasso
uv add requests python-dotenv      # HTTP + env loading
uv add cryptography                # RSA signing for Kalshi
uv add matplotlib                  # visualization
```

### 3.4 Project Structure

```
winnie/
├── .env                        # API keys (DO NOT COMMIT)
├── .gitignore
├── kalshi_private_key.txt      # RSA key from Kalshi (DO NOT COMMIT)
├── pyproject.toml
├── run.py                      # Orchestrator — runs all phases
├── RLM.md
├── BACKTEST.md
├── backtest/
│   ├── __init__.py
│   ├── kalshi_client.py        # Kalshi API wrapper
│   ├── data_collection.py      # Market discovery + feature engineering
│   ├── track_a.py              # Lasso Logistic Regression
│   ├── track_b.py              # RLM predictions (synthetic for now)
│   ├── backtest.py             # Synthesis + alpha sweep + evaluation
│   └── visualize.py            # Plotting
└── data/                        # All intermediate + output data
    ├── raw/                     # Raw API responses (JSON cache)
    └── processed/               # Cleaned CSVs
```

### 3.5 Set Up `.gitignore`

```
.env
kalshi_private_key.*
data/
*.pyc
__pycache__/
.venv/
```

---

## 4. File Architecture & Data Flow

### 4.1 Dependency Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          run.py                                     │
│         Calls each module's main() in order (top to bottom)         │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         │                     │                     │
         ▼                     │                     │
┌──────────────────┐           │                     │
│ kalshi_client.py │           │                     │
│                  │           │                     │
│ KalshiClient     │           │                     │
│  .get()          │           │                     │
│  .get_all_pages()│           │                     │
└────────┬─────────┘           │                     │
         │                     │                     │
         │ (imported by)       │                     │
         ▼                     │                     │
┌──────────────────────────┐   │                     │
│ data_collection.py       │   │                     │
│                          │   │                     │
│ WRITES:                  │   │                     │
│  data/raw/*.json         │   │                     │
│  data/processed/         │   │                     │
│    markets.csv           │   │                     │
│    features.csv          │   │                     │
└────────┬─────────────────┘   │                     │
         │                     │                     │
         │ (reads CSVs)        │ (reads CSVs)        │
         ▼                     ▼                     │
┌──────────────────┐  ┌──────────────────┐           │
│ track_a.py       │  │ track_b.py       │           │
│                  │  │                  │           │
│ READS:           │  │ READS:           │           │
│  features.csv    │  │  track_a output  │           │
│  markets.csv     │  │  (for tickers)   │           │
│                  │  │                  │           │
│ WRITES:          │  │ WRITES:          │           │
│  track_a_preds   │  │  track_b_preds   │           │
│  .csv            │  │  .csv            │           │
└────────┬─────────┘  └──────┬───────────┘           │
         │                   │                       │
         └─────────┬─────────┘                       │
                   │ (reads both prediction CSVs)    │
                   ▼                                 │
         ┌──────────────────┐                        │
         │ backtest.py      │                        │
         │                  │                        │
         │ WRITES:          │                        │
         │  alpha_sweep.csv │                        │
         │  best_preds.csv  │                        │
         └────────┬─────────┘                        │
                  │                                  │
                  │ (reads evaluation CSVs)           │
                  ▼                                   │
         ┌──────────────────┐                         │
         │ visualize.py     │                         │
         │                  │                         │
         │ WRITES:          │                         │
         │  brier_vs_alpha  │                         │
         │   .png           │                         │
         │  calibration.png │                         │
         └─────────────────-┘                         │
```

### 4.2 Implementation Order

You must implement and verify the files in this exact order, because each file depends on the outputs of the previous one:

| Order | File | Why This Order |
|-------|------|----------------|
| 1 | `kalshi_client.py` | Everything else needs API access. Test this in isolation first. |
| 2 | `data_collection.py` | Fetches and processes all data. Produces the CSVs that all downstream files consume. |
| 3 | `track_a.py` | Trains the Lasso model on features.csv. Must run before track_b because track_b reads track_a's output to know which tickers are in the test set. |
| 4 | `track_b.py` | Generates synthetic predictions for the same test-set tickers that track_a predicted on. |
| 5 | `backtest.py` | Merges track_a + track_b predictions, sweeps alpha, computes metrics. |
| 6 | `visualize.py` | Reads backtest outputs and produces plots. |
| 7 | `run.py` | Thin orchestrator that calls 2–6 in order. Implement last. |

### 4.3 Data Flow (What Gets Passed Between Files)

The files communicate **exclusively through CSV/JSON files on disk**. No file imports another file (except `kalshi_client.py` which is imported by `data_collection.py`). This makes it easy to re-run any individual phase without re-running everything.

**Phase 1 outputs** (from `data_collection.py`):
- `data/processed/markets.csv` — One row per target market. Contains ticker, event_ticker, title, open_time, close_time, midpoint, result, resolved_yes. Used by `track_a.py` for the temporal train/test split.
- `data/processed/features.csv` — One row per target market, one column per feature market. Values are prices (0–1) of feature markets at the target's midpoint. The `y_true` column is the target's resolution. This is the input to the Lasso model.

**Phase 2 output** (from `track_a.py`):
- `data/processed/track_a_predictions.csv` — One row per **test-set** market. Contains ticker, P_stat (probability), L_stat (log-odds), y_true (ground truth).

**Phase 3 output** (from `track_b.py`):
- `data/processed/track_b_predictions.csv` — One row per **test-set** market (same tickers as track_a). Contains ticker, L_news (log-odds), mode ("SYNTHETIC"), y_true.

**Phase 4 outputs** (from `backtest.py`):
- `data/evaluation/alpha_sweep.csv` — One row per alpha value (0.00 to 1.00). Contains alpha, brier score, log loss.
- `data/evaluation/best_predictions.csv` — Predictions at optimal alpha. Contains ticker, y_true, P_final, alpha.

**Phase 4 outputs** (from `visualize.py`):
- `data/evaluation/brier_vs_alpha.png`
- `data/evaluation/calibration.png`

---

## 5. File 1: `backtest/kalshi_client.py`

### 5.1 Purpose

This is a thin wrapper around the Kalshi REST API. It handles:
- Loading your RSA private key from disk
- Signing every request with RSA-PSS SHA256
- Cursor-based pagination (Kalshi returns results in pages)
- Rate-limit-friendly delays between paginated requests

Every other file that talks to Kalshi does so through this client. It is the **only** file that knows about HTTP, signatures, or API paths.

### 5.2 Dependencies

- **External packages**: `requests`, `cryptography`, `python-dotenv`
- **Reads from**: `.env` file (for `KALSHI_KEY_ID` and `KALSHI_PRIVATE_KEY_PATH`)
- **Imported by**: `data_collection.py`

### 5.3 Complete Code

```python
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

        Returns:
            A flat list of all result items across all pages.
        """
        params = dict(params or {})
        params["limit"] = page_limit
        all_results = []

        while True:
            resp = self.get(path, params)
            items = resp.get(result_key, [])
            all_results.extend(items)

            cursor = resp.get("cursor", "")
            if not cursor or len(items) < page_limit:
                break

            params["cursor"] = cursor
            time.sleep(delay)

        return all_results
```

### 5.4 Function Reference

| Function | What It Does | Called By |
|----------|-------------|-----------|
| `__init__()` | Loads API key ID from `.env`, loads RSA private key from the `.txt` file on disk. Raises clear errors if either is missing. | `data_collection.py` when it creates a `KalshiClient()` |
| `_sign(timestamp_ms, method, path)` | Constructs the message string `"{ts}{METHOD}{path}"`, signs it with RSA-PSS SHA256, returns base64. This is the core of Kalshi's auth. | `_headers()` |
| `_headers(method, path)` | Builds the 3 required headers dict. Strips query params from `path` before signing (Kalshi requirement). | `get()` |
| `get(path, params)` | Makes one HTTP GET request with signed headers. Returns parsed JSON. | `get_all_pages()`, or directly by `data_collection.py` for single-item fetches |
| `get_all_pages(path, params, result_key, ...)` | Handles cursor-based pagination. Keeps calling `get()` with the cursor from each response until no more pages. Concatenates all results into one list. The `result_key` argument tells it which JSON key holds the array (e.g., `"markets"`, `"candlesticks"`, `"series"`). Sleeps between pages to respect rate limits. | `data_collection.py` when fetching all markets in a series, or all candlesticks |

### 5.5 Verification

After creating this file, test it in isolation:

```bash
uv run python -c "
from backtest.kalshi_client import KalshiClient
client = KalshiClient()
# Fetch 1 settled market to verify auth works
resp = client.get('/markets', params={'status': 'settled', 'limit': 1})
print(resp)
"
```

**What to check:**
- Does it authenticate without errors? If you get a 401, double-check your `KALSHI_KEY_ID` and key file path.
- Does the response contain a `"markets"` array with one item?
- Inspect the market object's fields. You should see: `ticker`, `event_ticker`, `title`, `open_time`, `close_time`, `result`, `last_price`, etc.

**If using the sandbox for testing**, temporarily change `BASE_URL` to `"https://demo-api.kalshi.co/trade-api/v2"`. Note that the sandbox may have different data than production.

---

## 6. File 2: `backtest/data_collection.py`

### 6.1 Purpose

This is the most complex file. It is responsible for all communication with the Kalshi API and produces the two CSVs that the entire rest of the pipeline consumes. It runs in three stages:

1. **Discovery**: Fetch available series from Kalshi, print them so you can choose which to use as targets and features.
2. **Market Fetching**: For the chosen series, fetch all settled markets from the past 12 months.
3. **Feature Matrix Construction**: For each target market, fetch daily candlestick prices of all related markets at the target's midpoint date, producing the feature matrix for Track A.

This file is designed to be run **twice**:
- **First run**: With `DISCOVERY_MODE = True`. It prints available series and exits. You inspect the output and update the configuration.
- **Second run**: With `DISCOVERY_MODE = False`. It does the full data collection.

### 6.2 Dependencies

- **Imports**: `backtest.kalshi_client.KalshiClient`
- **External packages**: `pandas`, `numpy`, `json`, `os`, `datetime`
- **Reads from**: Kalshi API (via KalshiClient), and optionally `data/raw/` cache files on re-runs
- **Writes to**: `data/raw/*.json` (cached API responses), `data/processed/markets.csv`, `data/processed/features.csv`
- **Consumed by**: `track_a.py`, `track_b.py`

### 6.3 Complete Code

```python
"""
backtest/data_collection.py

Phase 1: Discovers target markets on Kalshi, fetches historical candlestick
data, and builds the feature matrix for Track A.

Run with:  uv run python -m backtest.data_collection

First run:  Set DISCOVERY_MODE = True, inspect output, update config.
Second run: Set DISCOVERY_MODE = False, full data collection.
"""

import os
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone

from backtest.kalshi_client import KalshiClient

# ── Configuration ──────────────────────────────────────────────────────────

# Set to True on your first run. This will print available series and exit.
# After inspecting the output, set to False and update the series lists below.
DISCOVERY_MODE = True

# Series we want to PREDICT (our target markets).
# These must be recurring series with >= MIN_INSTANCES resolved markets.
# Update these after running in discovery mode.
TARGET_SERIES = [
    # "KCPI",   # CPI inflation — uncomment after verifying via discovery
    # "KPCE",   # PCE inflation — uncomment after verifying via discovery
]

# Series we use as FEATURES (inputs to Track A's Lasso model).
# Should include target series + economically related series.
# The Lasso will automatically select the most predictive ones.
# Update these after running in discovery mode.
FEATURE_SERIES = [
    # "KCPI",
    # "KPCE",
    # "KFED",   # Fed rate decisions
    # Add more after discovery — GDP, unemployment, treasury yields, etc.
]

# Minimum instances for a series to be considered "recurring enough"
MIN_INSTANCES = 6

# Paths
RAW_DIR = "data/raw"
PROCESSED_DIR = "data/processed"


# ── Step 1: Discovery ─────────────────────────────────────────────────────

def discover_series(client: KalshiClient) -> None:
    """
    PURPOSE: Fetch all available series from Kalshi and print them.
    This helps you identify which series_tickers to use for TARGET_SERIES
    and FEATURE_SERIES.

    HOW IT WORKS:
    Calls GET /series, which returns all series templates. Each series
    represents a recurring event type (e.g., "Monthly CPI Report").
    We print the ticker and title so you can pick the relevant ones.

    WHAT TO DO WITH THE OUTPUT:
    Look for economy/finance-related series. Note their tickers.
    Update TARGET_SERIES and FEATURE_SERIES at the top of this file.

    CALLED BY: main() when DISCOVERY_MODE is True.
    CALLS: client.get_all_pages()
    """
    print("Fetching all series from Kalshi...")
    series_list = client.get_all_pages("/series", result_key="series", page_limit=200)

    print(f"\nFound {len(series_list)} series. Showing all:\n")
    print(f"{'TICKER':<20} {'TITLE'}")
    print("-" * 80)
    for s in sorted(series_list, key=lambda x: x.get("ticker", "")):
        ticker = s.get("ticker", "???")
        title = s.get("title", s.get("name", "???"))
        print(f"{ticker:<20} {title}")

    # Also save raw response for reference
    os.makedirs(RAW_DIR, exist_ok=True)
    with open(os.path.join(RAW_DIR, "all_series.json"), "w") as f:
        json.dump(series_list, f, indent=2, default=str)

    print(f"\nRaw data saved to {RAW_DIR}/all_series.json")
    print("\n── NEXT STEP ──")
    print("1. Find economy-related series tickers in the list above")
    print("2. Update TARGET_SERIES and FEATURE_SERIES at the top of this file")
    print("3. Set DISCOVERY_MODE = False")
    print("4. Re-run this script")


# ── Step 2: Fetch Markets ─────────────────────────────────────────────────

def fetch_settled_markets(client: KalshiClient, series_list: list[str]) -> pd.DataFrame:
    """
    PURPOSE: Fetch all settled (resolved) markets for the given series,
    limited to the past 12 months.

    HOW IT WORKS:
    For each series ticker, calls GET /markets with:
      - status=settled (only resolved markets)
      - series_ticker=<ticker>
      - min_settled_ts=<12 months ago as unix timestamp>
    Concatenates results into a single DataFrame.

    WHY PER-SERIES: The Kalshi API only accepts one series_ticker at a time.
    We loop through our list and combine.

    CACHING: Saves raw API responses to data/raw/ so re-runs don't hit the API.

    CALLED BY: main()
    CALLS: client.get_all_pages()
    RETURNS: DataFrame with one row per market (raw API fields).
    """
    twelve_months_ago = int((datetime.now(timezone.utc) - timedelta(days=365)).timestamp())
    all_markets = []

    for series in series_list:
        cache_path = os.path.join(RAW_DIR, f"markets_{series}.json")

        # Use cache if available
        if os.path.exists(cache_path):
            print(f"  Loading cached markets for {series}")
            with open(cache_path) as f:
                markets = json.load(f)
        else:
            print(f"  Fetching settled markets for series: {series}")
            markets = client.get_all_pages(
                "/markets",
                params={
                    "series_ticker": series,
                    "status": "settled",
                    "min_settled_ts": twelve_months_ago,
                },
            )
            # Cache for re-runs
            with open(cache_path, "w") as f:
                json.dump(markets, f, indent=2, default=str)

        print(f"    → {len(markets)} markets")
        all_markets.extend(markets)

    if not all_markets:
        raise RuntimeError("No markets found. Check your series tickers and date range.")

    return pd.DataFrame(all_markets)


# ── Step 3: Clean & Filter ────────────────────────────────────────────────

def clean_markets(df: pd.DataFrame, target_series: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    PURPOSE: Clean raw market data and split into target markets
    (what we predict) and all markets (used as features).

    HOW IT WORKS:
    1. Parses timestamps (open_time, close_time) into pandas datetime.
    2. Converts result ("yes"/"no") to binary (1/0).
    3. Computes the midpoint: halfway between open_time and close_time.
       This is the timestamp at which we'll snapshot feature prices.
    4. Filters out markets with result="" (unresolved — shouldn't happen
       with status=settled, but defensive).
    5. Identifies target markets (those whose ticker starts with a
       TARGET_SERIES prefix) vs. all markets.

    WHY MIDPOINT: Per RLM.md, we want the price at time `t` before
    resolution. Using the midpoint of the market's trading window is a
    reasonable default — not too early (no signal) and not too late
    (price has converged to outcome).

    CALLED BY: main()
    RETURNS: (target_df, all_df) — both are cleaned DataFrames.
    """
    df = df.copy()

    # Parse times. Kalshi returns ISO 8601 strings like "2025-01-15T16:00:00Z"
    df["open_time"] = pd.to_datetime(df["open_time"], utc=True)
    df["close_time"] = pd.to_datetime(df["close_time"], utc=True)

    # Binary resolution
    df = df[df["result"].isin(["yes", "no"])].copy()
    df["resolved_yes"] = (df["result"] == "yes").astype(int)

    # Midpoint of trading window
    df["midpoint"] = df["open_time"] + (df["close_time"] - df["open_time"]) / 2

    # Infer series from ticker prefix (e.g., "KCPI-25JAN-T0.3" → "KCPI")
    # This works because Kalshi tickers follow the pattern: SERIES-DATE-DETAILS
    df["inferred_series"] = df["ticker"].str.split("-").str[0]

    # Select useful columns
    keep_cols = [
        "ticker", "event_ticker", "title", "inferred_series",
        "open_time", "close_time", "midpoint",
        "result", "resolved_yes",
    ]
    # Only keep columns that actually exist (defensive against API changes)
    keep_cols = [c for c in keep_cols if c in df.columns]
    df = df[keep_cols].copy()
    df = df.sort_values("close_time").reset_index(drop=True)

    # Split: target markets vs all markets
    target_df = df[df["inferred_series"].isin(target_series)].copy()
    all_df = df.copy()

    print(f"\nCleaned: {len(all_df)} total markets, {len(target_df)} target markets")
    print(f"Target series: {target_df['inferred_series'].value_counts().to_dict()}")

    if len(target_df) < MIN_INSTANCES:
        print(f"\n⚠️  WARNING: Only {len(target_df)} target markets found.")
        print(f"   Need at least {MIN_INSTANCES} for meaningful results.")
        print(f"   Consider adding more TARGET_SERIES or lowering MIN_INSTANCES.")

    return target_df, all_df


# ── Step 4: Fetch Candlestick Data ────────────────────────────────────────

def fetch_candlesticks_cached(client: KalshiClient, ticker: str) -> list[dict]:
    """
    PURPOSE: Fetch daily candlestick data for a single market, with file caching.

    HOW IT WORKS:
    Calls GET /markets/{ticker}/candlesticks with period_interval=1440 (daily).
    Caches the response to data/raw/candles_{ticker}.json so subsequent runs
    don't hit the API.

    WHY DAILY: We only need one price per day. Daily candles (1440 min) give us
    that. Finer granularity would waste bandwidth without improving our features.

    ⚠️  VERIFY: The candlestick response format. The code assumes each candle
    has fields like: end_period_ts (or ts), yes_price/close, volume.
    After your first run, inspect data/raw/candles_*.json to confirm field names.
    If they differ, update price_from_candle() below.

    CALLED BY: build_feature_matrix()
    CALLS: client.get_all_pages()
    RETURNS: List of candlestick dicts (raw API response).
    """
    cache_path = os.path.join(RAW_DIR, f"candles_{ticker}.json")

    if os.path.exists(cache_path):
        with open(cache_path) as f:
            return json.load(f)

    candles = client.get_all_pages(
        f"/markets/{ticker}/candlesticks",
        params={"period_interval": 1440},
        result_key="candlesticks",
    )

    with open(cache_path, "w") as f:
        json.dump(candles, f, indent=2, default=str)

    return candles


def price_from_candle(candle: dict) -> float:
    """
    PURPOSE: Extract a price (0-1 probability) from a single candlestick object.

    HOW IT WORKS:
    Tries several possible field names for the closing price, since the exact
    Kalshi response format should be verified on first run.

    ⚠️  VERIFY: Inspect a raw candle object in data/raw/candles_*.json.
    Update this function if the field names don't match.

    Kalshi prices may be in cents (0-99) or dollars ("0.5600").
    We normalize to a 0-1 float.

    CALLED BY: find_price_at_date()
    RETURNS: Float between 0 and 1.
    """
    # Try common field names (adjust after inspecting raw data)
    for key in ["yes_price", "close", "price", "close_price"]:
        if key in candle:
            val = candle[key]
            if isinstance(val, str):
                val = float(val)
            # If value > 1, assume it's in cents (0-100 scale)
            if val > 1:
                return val / 100.0
            return val

    # Fallback: try nested structure like {"price": {"close": 65}}
    if "price" in candle and isinstance(candle["price"], dict):
        val = candle["price"].get("close", candle["price"].get("yes", 50))
        if isinstance(val, str):
            val = float(val)
        if val > 1:
            return val / 100.0
        return val

    # Last resort: uninformative prior
    return 0.5


def find_price_at_date(candles: list[dict], target_dt: datetime) -> float:
    """
    PURPOSE: From a list of daily candles, find the one closest to `target_dt`
    and return its price.

    HOW IT WORKS:
    Each candle has a timestamp field. We compute the absolute time difference
    between each candle's timestamp and our target datetime, then pick the
    closest one.

    ⚠️  VERIFY: The timestamp field name. Tries "end_period_ts", "ts",
    "start_period_ts". Check your raw data.

    If the candle timestamps are Unix seconds (int), we compare directly.
    If they're ISO strings, we parse them.

    CALLED BY: build_feature_matrix()
    RETURNS: Float between 0 and 1. Returns 0.5 if no candles available.
    """
    if not candles:
        return 0.5

    target_ts = target_dt.timestamp()

    def candle_ts(c):
        for key in ["end_period_ts", "ts", "start_period_ts", "timestamp"]:
            if key in c:
                val = c[key]
                if isinstance(val, str):
                    return pd.to_datetime(val).timestamp()
                return float(val)
        return 0

    closest = min(candles, key=lambda c: abs(candle_ts(c) - target_ts))
    return price_from_candle(closest)


# ── Step 5: Build Feature Matrix ──────────────────────────────────────────

def build_feature_matrix(
    client: KalshiClient,
    target_df: pd.DataFrame,
    all_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    PURPOSE: For each target market, construct a feature vector of related
    market prices at the target's midpoint. This is the input matrix X for
    Track A's Lasso Logistic Regression.

    HOW IT WORKS:
    For each target market T with midpoint M:
      1. Find all OTHER markets in all_df that were actively trading at time M.
         "Actively trading" means: open_time <= M <= close_time.
      2. For each of those feature markets, look up its price at time M
         using cached candlestick data.
      3. Store as one row: {ticker: T, feature_market_1: price, ..., y_true: 0/1}

    The resulting DataFrame has:
      - Rows: one per target market
      - Columns: one per feature market ticker + "y_true"
      - Values: prices as floats 0-1
      - Index: target market ticker

    WHY EXCLUDE SELF: Including the target market's own price as a feature
    would be data leakage. Its price at midpoint already encodes the market's
    best guess — we'd be predicting the outcome from a near-direct signal.

    MISSING VALUES: Not all feature markets exist at every target's midpoint
    (markets come and go). We fill missing values with 0.5, which represents
    "no opinion" — a 50/50 price conveys zero directional information, so it
    won't bias the Lasso.

    PERFORMANCE: This function makes one API call per unique feature market
    (cached after first call). With ~200 markets, expect ~200 calls ≈ 2-3 min.

    CALLED BY: main()
    CALLS: fetch_candlesticks_cached(), find_price_at_date()
    RETURNS: DataFrame (rows=targets, cols=features + y_true).
    """
    # Pre-fetch candlesticks for all markets (cached to disk)
    all_tickers = all_df["ticker"].unique()
    print(f"\nPre-fetching candlestick data for {len(all_tickers)} markets...")
    candle_cache = {}
    for i, ticker in enumerate(all_tickers):
        if (i + 1) % 25 == 0:
            print(f"  {i + 1}/{len(all_tickers)}")
        candle_cache[ticker] = fetch_candlesticks_cached(client, ticker)
        time.sleep(0.1)  # Light rate limiting for non-cached fetches

    # Build feature rows
    print(f"\nBuilding feature matrix for {len(target_df)} target markets...")
    rows = []

    for _, target in target_df.iterrows():
        midpoint = target["midpoint"]
        target_ticker = target["ticker"]

        # Find markets active at this midpoint (excluding self)
        active = all_df[
            (all_df["open_time"] <= midpoint)
            & (all_df["close_time"] >= midpoint)
            & (all_df["ticker"] != target_ticker)
        ]

        # Look up each active market's price at the midpoint
        row = {"ticker": target_ticker, "y_true": target["resolved_yes"]}
        for _, feat_market in active.iterrows():
            feat_ticker = feat_market["ticker"]
            candles = candle_cache.get(feat_ticker, [])
            price = find_price_at_date(candles, midpoint)
            row[feat_ticker] = price

        rows.append(row)

    df = pd.DataFrame(rows).set_index("ticker")
    df = df.fillna(0.5)  # Missing features → uninformative prior

    n_features = len(df.columns) - 1  # Subtract y_true
    print(f"Feature matrix: {len(df)} targets × {n_features} features")

    return df


# We need time for the rate limiting in build_feature_matrix
import time


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    client = KalshiClient()

    # ── Discovery mode ──
    if DISCOVERY_MODE:
        discover_series(client)
        return

    # ── Validation ──
    if not TARGET_SERIES:
        raise ValueError(
            "TARGET_SERIES is empty. Run with DISCOVERY_MODE=True first, "
            "then update TARGET_SERIES and FEATURE_SERIES."
        )

    # ── Fetch all markets ──
    all_series = list(set(TARGET_SERIES + FEATURE_SERIES))
    print(f"Fetching markets for series: {all_series}")
    raw_df = fetch_settled_markets(client, all_series)

    # ── Clean and split ──
    target_df, all_df = clean_markets(raw_df, TARGET_SERIES)

    # Save markets metadata
    target_df.to_csv(os.path.join(PROCESSED_DIR, "markets.csv"), index=False)

    # ── Build feature matrix ──
    features_df = build_feature_matrix(client, target_df, all_df)
    features_df.to_csv(os.path.join(PROCESSED_DIR, "features.csv"))

    print(f"\n✅ Phase 1 complete.")
    print(f"   {os.path.join(PROCESSED_DIR, 'markets.csv')}")
    print(f"   {os.path.join(PROCESSED_DIR, 'features.csv')}")


if __name__ == "__main__":
    main()
```

### 6.4 Function Reference

| Function | Purpose | Reads | Writes | Called By |
|----------|---------|-------|--------|-----------|
| `discover_series(client)` | Prints all available Kalshi series so you can choose targets/features. Run once, inspect, then update config. | Kalshi API (`GET /series`) | `data/raw/all_series.json` | `main()` |
| `fetch_settled_markets(client, series_list)` | For each series ticker, fetches all settled markets from past 12 months. Uses file cache to avoid re-fetching. | Kalshi API (`GET /markets`) or cache | `data/raw/markets_{series}.json` | `main()` |
| `clean_markets(df, target_series)` | Parses timestamps, computes midpoints, converts results to binary, infers series from ticker prefix. Splits into target vs all markets. | Raw DataFrame from fetch_settled_markets | Nothing (returns DataFrames) | `main()` |
| `fetch_candlesticks_cached(client, ticker)` | Fetches daily candlestick data for one market. Caches to JSON file so re-runs are instant. | Kalshi API (`GET /markets/{ticker}/candlesticks`) or cache | `data/raw/candles_{ticker}.json` | `build_feature_matrix()` |
| `price_from_candle(candle)` | Extracts a 0-1 price from a candlestick dict. Handles multiple possible field names and cent-vs-dollar formats. **Verify this after first run.** | Single candle dict | Nothing | `find_price_at_date()` |
| `find_price_at_date(candles, target_dt)` | Given a list of daily candles and a target datetime, returns the price of the closest candle. Falls back to 0.5 if no data. | Candle list | Nothing | `build_feature_matrix()` |
| `build_feature_matrix(client, target_df, all_df)` | The core function. For each target market, finds all other markets active at its midpoint, looks up their prices, and assembles the feature matrix. Pre-fetches all candlestick data with caching. | Cached candle data | Nothing (returns DataFrame) | `main()` |
| `main()` | Orchestrates everything. In discovery mode: prints series and exits. Otherwise: fetches markets, cleans them, builds features, saves CSVs. | Everything above | `data/processed/markets.csv`, `data/processed/features.csv` | `run.py` or direct execution |

### 6.5 Verification

**After first run (discovery mode):**
```bash
uv run python -m backtest.data_collection
```
- Check the printed series list. Look for economy-related tickers.
- Inspect `data/raw/all_series.json` if you want more detail on each series.
- Update `TARGET_SERIES`, `FEATURE_SERIES`, set `DISCOVERY_MODE = False`.

**After second run (full collection):**
```bash
uv run python -m backtest.data_collection
```
- Open `data/processed/markets.csv`. Verify:
  - Tickers look reasonable (e.g., `KCPI-25JAN-T0.3`)
  - `resolved_yes` column has both 0s and 1s
  - `midpoint` dates span ~12 months
- Open `data/processed/features.csv`. Verify:
  - Rows are target market tickers
  - Columns are other market tickers
  - Values are between 0 and 1
  - `y_true` column matches `resolved_yes` from markets.csv
- **Inspect one raw candle file** (e.g., `data/raw/candles_KCPI-25JAN-T0.3.json`):
  - What fields does each candlestick have?
  - If the field names don't match what `price_from_candle()` expects, update that function.

---

## 7. File 3: `backtest/track_a.py`

### 7.1 Purpose

Implements Track A from RLM.md: a Lasso Logistic Regression that predicts market outcomes using prices of related markets as features.

This file reads `features.csv` and `markets.csv`, splits the data temporally (first 6 months = train, last 6 months = test), trains the Lasso model, and outputs predictions for the test set.

### 7.2 Dependencies

- **External packages**: `pandas`, `numpy`, `scikit-learn`
- **Reads from**: `data/processed/features.csv`, `data/processed/markets.csv`
- **Writes to**: `data/processed/track_a_predictions.csv`, `data/models/track_a_coefficients.csv`
- **Consumed by**: `track_b.py` (reads track_a output to know test set tickers), `backtest.py`

### 7.3 Complete Code

```python
"""
backtest/track_a.py

Phase 2: Trains a Lasso Logistic Regression on the feature matrix from Phase 1.
Predicts probabilities and log-odds for the test set.

Run with:  uv run python -m backtest.track_a
"""

import os
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegressionCV

PROCESSED_DIR = "data/processed"
MODELS_DIR = "data/models"


def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    PURPOSE: Load the feature matrix and market metadata produced by data_collection.py.

    RETURNS:
        features: DataFrame indexed by ticker. Columns are feature market tickers + "y_true".
        markets:  DataFrame with target market metadata (we need close_time for temporal split).

    CALLED BY: main()
    """
    features = pd.read_csv(os.path.join(PROCESSED_DIR, "features.csv"), index_col="ticker")
    markets = pd.read_csv(
        os.path.join(PROCESSED_DIR, "markets.csv"),
        parse_dates=["open_time", "close_time", "midpoint"],
    )
    return features, markets


def temporal_split(
    features: pd.DataFrame, markets: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    PURPOSE: Split data into train (first 6 months) and test (last 6 months)
    based on market close_time.

    HOW IT WORKS:
    1. Joins features with markets on ticker to get close_time for each row.
    2. Finds the earliest close_time, adds 182 days (~6 months) → split_date.
    3. Markets closing on or before split_date → train set.
       Markets closing after split_date → test set.
    4. Drops close_time from the result (it's not a feature).

    WHY TEMPORAL (not random): Random splits would leak future information.
    If a March 2025 market appears in training, the model could learn patterns
    that help predict February 2025 markets in the test set — but in real
    trading, you wouldn't have March data when predicting February.

    CALLED BY: main()
    RETURNS: (train_df, test_df) — both have same columns as features.
    """
    # Join close_time onto features
    close_times = markets.set_index("ticker")["close_time"]
    merged = features.join(close_times, how="inner")
    merged = merged.sort_values("close_time")

    # Split at 6-month mark
    min_date = merged["close_time"].min()
    split_date = min_date + pd.Timedelta(days=182)

    train = merged[merged["close_time"] <= split_date].drop(columns=["close_time"])
    test = merged[merged["close_time"] > split_date].drop(columns=["close_time"])

    print(f"Temporal split at {split_date.date()}")
    print(f"  Train: {len(train)} markets (before)")
    print(f"  Test:  {len(test)} markets (after)")

    if len(train) < 10:
        print("⚠️  WARNING: Very few training samples. Lasso may not learn meaningful patterns.")
    if len(test) < 5:
        print("⚠️  WARNING: Very few test samples. Evaluation metrics will be noisy.")

    return train, test


def train_model(X_train: np.ndarray, y_train: np.ndarray) -> LogisticRegressionCV:
    """
    PURPOSE: Train a Lasso (L1-penalized) Logistic Regression with
    cross-validated regularization strength.

    HOW IT WORKS:
    LogisticRegressionCV tries multiple regularization strengths (C values)
    and picks the one with the best cross-validation score. We use:
      - penalty='l1':       L1 regularization (Lasso) to force sparsity
      - solver='liblinear': The only solver that supports L1 penalty
      - cv=5:               5-fold cross-validation
      - scoring='neg_brier_score': Optimize for calibration, not just accuracy
      - max_iter=5000:      Enough iterations for convergence

    WHY LogisticRegressionCV instead of LogisticRegression:
    It auto-tunes the regularization strength. Without this, you'd need to
    manually sweep over C values — an extra hyperparameter to worry about.

    CALLED BY: main()
    RETURNS: Fitted LogisticRegressionCV model.
    """
    model = LogisticRegressionCV(
        penalty="l1",
        solver="liblinear",
        cv=min(5, len(y_train)),  # Can't have more folds than samples
        scoring="neg_brier_score",
        max_iter=5000,
    )
    model.fit(X_train, y_train)
    return model


def predict(model: LogisticRegressionCV, X_test: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    PURPOSE: Generate probability and log-odds predictions from the trained model.

    HOW IT WORKS:
    1. model.predict_proba() returns [P(no), P(yes)] for each sample.
       We take column 1 = P(yes) = P_stat.
    2. Clip probabilities to [1e-6, 1-1e-6] to avoid log(0) or log(inf).
    3. Convert to log-odds: L_stat = log(P / (1-P)).

    WHY LOG-ODDS: The synthesis formula (RLM.md §4) combines tracks in
    log-odds space: L_final = α·L_stat + (1-α)·L_news. Working in log-odds
    makes the weighting additive and well-behaved.

    CALLED BY: main()
    RETURNS: (P_stat, L_stat) — both numpy arrays of shape (n_test,)
    """
    P_stat = model.predict_proba(X_test)[:, 1]
    P_stat = np.clip(P_stat, 1e-6, 1 - 1e-6)
    L_stat = np.log(P_stat / (1 - P_stat))
    return P_stat, L_stat


def main():
    os.makedirs(MODELS_DIR, exist_ok=True)

    # Load
    features, markets = load_data()
    train_df, test_df = temporal_split(features, markets)

    # Separate X (features) from y (target)
    X_train = train_df.drop(columns=["y_true"]).values
    y_train = train_df["y_true"].values
    X_test = test_df.drop(columns=["y_true"]).values
    y_test = test_df["y_true"].values
    test_tickers = test_df.index

    # Train
    print("\nTraining Lasso Logistic Regression...")
    model = train_model(X_train, y_train)

    # Predict
    P_stat, L_stat = predict(model, X_test)

    # Save predictions
    results = pd.DataFrame({
        "ticker": test_tickers,
        "P_stat": P_stat,
        "L_stat": L_stat,
        "y_true": y_test,
    })
    results.to_csv(os.path.join(PROCESSED_DIR, "track_a_predictions.csv"), index=False)

    # Save coefficients for inspection
    feature_names = train_df.drop(columns=["y_true"]).columns
    coefs = pd.DataFrame({
        "feature": feature_names,
        "coefficient": model.coef_[0],
    })
    coefs = coefs.sort_values("coefficient", key=abs, ascending=False)
    coefs.to_csv(os.path.join(MODELS_DIR, "track_a_coefficients.csv"), index=False)

    n_nonzero = (model.coef_[0] != 0).sum()
    print(f"\n✅ Track A complete.")
    print(f"   {len(results)} test predictions saved.")
    print(f"   Non-zero coefficients: {n_nonzero} / {len(model.coef_[0])}")
    print(f"   Best C (regularization): {model.C_[0]:.4f}")


if __name__ == "__main__":
    main()
```

### 7.4 Function Reference

| Function | Purpose | Key Detail |
|----------|---------|------------|
| `load_data()` | Reads features.csv and markets.csv from disk. | Parses dates in markets.csv for temporal split. |
| `temporal_split(features, markets)` | Joins features with close_time, sorts by time, splits at 6-month mark. | Returns two DataFrames with same schema as features. Train has earlier markets, test has later ones. |
| `train_model(X_train, y_train)` | Fits `LogisticRegressionCV` with L1 penalty. Auto-tunes regularization via 5-fold CV optimizing Brier score. | `cv` is capped at sample count for small datasets. |
| `predict(model, X_test)` | Runs `predict_proba`, clips, converts to log-odds. | Clipping prevents numerical issues in log conversion. |
| `main()` | Load → split → train → predict → save. Also saves model coefficients for debugging. | Prints non-zero coefficient count as a sanity check. |

### 7.5 Verification

```bash
uv run python -m backtest.track_a
```

**Check:**
- `data/processed/track_a_predictions.csv` exists with columns: ticker, P_stat, L_stat, y_true
- P_stat values are between 0 and 1
- L_stat values are real numbers (positive and negative)
- `data/models/track_a_coefficients.csv` — inspect the top coefficients. Do the non-zero feature tickers make economic sense?
- If ALL coefficients are zero: regularization is too strong. This can happen with very few training samples.

---

## 8. File 4: `backtest/track_b.py`

### 8.1 Purpose

Generates Track B predictions. **For now, these are SYNTHETIC (fake).**

The sole purpose of this file in Stage 1 is to produce a CSV of log-odds predictions with the same tickers as Track A's test set, so the synthesis pipeline (backtest.py) can run end-to-end.

### 8.2 Dependencies

- **External packages**: `pandas`, `numpy`
- **Reads from**: `data/processed/track_a_predictions.csv` (to know which tickers need predictions)
- **Writes to**: `data/processed/track_b_predictions.csv`
- **Consumed by**: `backtest.py`

### 8.3 Complete Code

```python
"""
backtest/track_b.py

Phase 3: Generate Track B (RLM) predictions.

⚠️  CURRENTLY SYNTHETIC. All outputs are tagged mode=SYNTHETIC.
    Replace with real LLM-based predictions in Stage 2.

Run with:  uv run python -m backtest.track_b
"""

import os
import pandas as pd
import numpy as np

PROCESSED_DIR = "data/processed"


def synthetic_log_odds(y_true: np.ndarray, noise_std: float = 1.0, seed: int = 42) -> np.ndarray:
    """
    PURPOSE: Generate synthetic (fake) log-odds predictions that are correlated
    with the true outcome but noisy.

    HOW IT WORKS:
    - If the true outcome is YES (1): base log-odds = +1.0
    - If the true outcome is NO  (0): base log-odds = -1.0
    - Add Gaussian noise ~ N(0, noise_std²)

    This produces predictions that are "somewhat informative" — they lean in the
    right direction ~73% of the time (since P(noise > 1) ≈ 16%, so directional
    accuracy ≈ 84% before noise, degraded by overlap).

    WHY THIS APPROACH: We need predictions that behave like a real but imperfect
    RLM. Pure random would be useless (all noise). Perfect predictions would be
    unrealistically good. This heuristic sits in between.

    ⚠️  IMPORTANT: This function uses y_true (the ground truth) as input.
    This means the synthetic predictions are "cheating" — they have access to
    the answer. This is intentional for pipeline validation only. When you
    interpret backtest results with synthetic Track B, remember that any
    apparent Track B performance is artificial.

    CALLED BY: main()
    RETURNS: numpy array of log-odds values.
    """
    rng = np.random.default_rng(seed)
    base = 2.0 * y_true - 1.0  # Maps: 0 → -1.0, 1 → +1.0
    return base + rng.normal(0, noise_std, size=len(y_true))


def main():
    # Read Track A predictions to get the test set tickers and ground truth
    track_a = pd.read_csv(os.path.join(PROCESSED_DIR, "track_a_predictions.csv"))

    L_news = synthetic_log_odds(track_a["y_true"].values)

    results = pd.DataFrame({
        "ticker": track_a["ticker"],
        "L_news": L_news,
        "mode": "SYNTHETIC",
        "y_true": track_a["y_true"],
    })
    results.to_csv(os.path.join(PROCESSED_DIR, "track_b_predictions.csv"), index=False)

    print(f"⚠️  Track B (SYNTHETIC): {len(results)} predictions saved.")
    print(f"   Mode: SYNTHETIC — these are NOT real LLM predictions.")


if __name__ == "__main__":
    main()
```

### 8.4 Function Reference

| Function | Purpose |
|----------|---------|
| `synthetic_log_odds(y_true, noise_std, seed)` | Maps ground truth to noisy log-odds. Fixed seed ensures reproducibility. |
| `main()` | Reads Track A output for tickers/y_true, generates synthetic predictions, saves CSV. |

### 8.5 Verification

```bash
uv run python -m backtest.track_b
```

**Check:**
- `data/processed/track_b_predictions.csv` exists with columns: ticker, L_news, mode, y_true
- `mode` column is `"SYNTHETIC"` for every row
- Tickers match those in `track_a_predictions.csv`
- L_news values are roughly in [-3, +3] range (noise_std=1.0 means ~99.7% within ±3 of the base ±1)

---

## 9. File 5: `backtest/backtest.py`

### 9.1 Purpose

The synthesis engine. Combines Track A and Track B predictions using the weighted log-odds formula from RLM.md, sweeps over α values, and computes evaluation metrics.

### 9.2 Dependencies

- **External packages**: `pandas`, `numpy`, `scikit-learn`
- **Reads from**: `data/processed/track_a_predictions.csv`, `data/processed/track_b_predictions.csv`
- **Writes to**: `data/evaluation/alpha_sweep.csv`, `data/evaluation/best_predictions.csv`
- **Consumed by**: `visualize.py`

### 9.3 Complete Code

```python
"""
backtest/backtest.py

Phase 4: Combine Track A + Track B predictions via weighted log-odds ensemble.
Sweep alpha from 0 to 1, evaluate with Brier Score and Log Loss.

Run with:  uv run python -m backtest.backtest
"""

import os
import pandas as pd
import numpy as np
from sklearn.metrics import brier_score_loss, log_loss

PROCESSED_DIR = "data/processed"
EVAL_DIR = "data/evaluation"


def load_predictions() -> pd.DataFrame:
    """
    PURPOSE: Load Track A and Track B predictions and merge them on ticker.

    HOW IT WORKS:
    Reads both CSVs and joins on ['ticker', 'y_true']. This ensures
    we only evaluate markets that have predictions from both tracks.

    CALLED BY: main()
    RETURNS: DataFrame with columns: ticker, P_stat, L_stat, L_news, mode, y_true
    """
    a = pd.read_csv(os.path.join(PROCESSED_DIR, "track_a_predictions.csv"))
    b = pd.read_csv(os.path.join(PROCESSED_DIR, "track_b_predictions.csv"))

    merged = a.merge(b[["ticker", "L_news", "mode"]], on="ticker")

    print(f"Loaded {len(merged)} markets with predictions from both tracks.")
    print(f"Track B mode: {merged['mode'].iloc[0]}")

    return merged


def sweep_alpha(data: pd.DataFrame) -> pd.DataFrame:
    """
    PURPOSE: Test every alpha value from 0.0 to 1.0 (step 0.05) and compute
    Brier Score and Log Loss for each.

    HOW IT WORKS:
    For each alpha:
      1. Compute L_final = alpha * L_stat + (1 - alpha) * L_news
      2. Convert to probability: P_final = sigmoid(L_final) = 1 / (1 + exp(-L_final))
      3. Compute Brier Score: mean((P_final - y_true)²)
      4. Compute Log Loss: -mean(y·log(P) + (1-y)·log(1-P))

    WHY BRIER SCORE AS PRIMARY METRIC:
    Brier Score directly measures calibration — how close your predicted
    probabilities are to the actual outcomes. A well-calibrated model that says
    "70% chance" should be right ~70% of the time. This matters more for
    trading than raw accuracy, because position sizing depends on calibration.

    CALLED BY: main()
    RETURNS: DataFrame with columns: alpha, brier, log_loss, n_markets
    """
    alphas = np.arange(0, 1.05, 0.05)
    results = []

    for a in alphas:
        L_final = a * data["L_stat"] + (1 - a) * data["L_news"]
        P_final = 1 / (1 + np.exp(-L_final))
        # Clip for log_loss stability
        P_final = np.clip(P_final, 1e-6, 1 - 1e-6)

        results.append({
            "alpha": round(a, 2),
            "brier": brier_score_loss(data["y_true"], P_final),
            "log_loss": log_loss(data["y_true"], P_final),
            "n_markets": len(data),
        })

    return pd.DataFrame(results)


def main():
    os.makedirs(EVAL_DIR, exist_ok=True)

    data = load_predictions()
    results = sweep_alpha(data)
    results.to_csv(os.path.join(EVAL_DIR, "alpha_sweep.csv"), index=False)

    # Find best alpha
    best_idx = results["brier"].idxmin()
    best_alpha = results.loc[best_idx, "alpha"]
    best_brier = results.loc[best_idx, "brier"]

    print(f"\n── Alpha Sweep Results ──")
    print(results.to_string(index=False))
    print(f"\nBest alpha: {best_alpha:.2f}")
    print(f"Best Brier: {best_brier:.4f}")
    print(f"Baseline (random guess): 0.2500")

    # Save predictions at best alpha
    L_final = best_alpha * data["L_stat"] + (1 - best_alpha) * data["L_news"]
    P_final = 1 / (1 + np.exp(-L_final))

    best_preds = pd.DataFrame({
        "ticker": data["ticker"],
        "y_true": data["y_true"],
        "P_final": np.clip(P_final, 1e-6, 1 - 1e-6),
        "alpha": best_alpha,
        "track_b_mode": data["mode"],
    })
    best_preds.to_csv(os.path.join(EVAL_DIR, "best_predictions.csv"), index=False)

    print(f"\n✅ Phase 4 complete.")
    print(f"   {os.path.join(EVAL_DIR, 'alpha_sweep.csv')}")
    print(f"   {os.path.join(EVAL_DIR, 'best_predictions.csv')}")


if __name__ == "__main__":
    main()
```

### 9.4 Function Reference

| Function | Purpose | Key Detail |
|----------|---------|------------|
| `load_predictions()` | Merges Track A + Track B CSVs on ticker. | Prints Track B mode so you always know if you're evaluating synthetic or real. |
| `sweep_alpha(data)` | For each α in [0, 1] (step 0.05): compute L_final, convert to probability, score with Brier and LogLoss. | 21 alpha values tested. Clips P_final for numerical stability. |
| `main()` | Load → sweep → find best α → save results and best-alpha predictions. | Prints full sweep table to stdout for quick inspection. |

### 9.5 Verification

```bash
uv run python -m backtest.backtest
```

**Check:**
- `data/evaluation/alpha_sweep.csv` has 21 rows (alpha 0.00 to 1.00)
- All Brier scores are between 0 and 1
- With synthetic Track B: optimal α should be **near 1.0** (meaning Track A alone is best, and adding synthetic noise hurts). If you see α near 0.0, something is wrong.
- Brier scores should be **below 0.25** (the random-guessing baseline) for at least some alpha values.
- `best_predictions.csv` has `track_b_mode = SYNTHETIC`

---

## 10. File 6: `backtest/visualize.py`

### 10.1 Purpose

Produces the two key diagnostic plots from the backtest results.

### 10.2 Dependencies

- **External packages**: `pandas`, `numpy`, `matplotlib`, `scikit-learn`
- **Reads from**: `data/evaluation/alpha_sweep.csv`, `data/evaluation/best_predictions.csv`
- **Writes to**: `data/evaluation/brier_vs_alpha.png`, `data/evaluation/calibration.png`

### 10.3 Complete Code

```python
"""
backtest/visualize.py

Produces diagnostic plots from backtest results.

Run with:  uv run python -m backtest.visualize
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.calibration import calibration_curve

EVAL_DIR = "data/evaluation"


def plot_brier_vs_alpha():
    """
    PURPOSE: Visualize how the ensemble Brier Score changes as we shift
    weight between Track A (α=1) and Track B (α=0).

    HOW IT WORKS:
    Reads alpha_sweep.csv, plots Brier Score on y-axis vs alpha on x-axis.
    Marks the optimal alpha with a red dot and dashed line.
    Draws a horizontal line at 0.25 (random-guessing baseline).

    HOW TO READ THIS PLOT:
    - The lowest point on the curve is the best alpha.
    - If the curve is flat: both tracks are similarly (un)informative.
    - If the curve is U-shaped with minimum in the middle: both tracks
      contribute unique information. (Unlikely with synthetic Track B.)
    - If the minimum is at α=1.0: Track A alone is best.

    CALLED BY: main()
    """
    results = pd.read_csv(os.path.join(EVAL_DIR, "alpha_sweep.csv"))

    best_idx = results["brier"].idxmin()
    best_alpha = results.loc[best_idx, "alpha"]
    best_brier = results.loc[best_idx, "brier"]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(results["alpha"], results["brier"], "o-", linewidth=2, markersize=5)
    ax.axvline(best_alpha, color="red", linestyle="--", alpha=0.7,
               label=f"Best α = {best_alpha:.2f}")
    ax.scatter([best_alpha], [best_brier], color="red", s=150, zorder=5)
    ax.axhline(0.25, color="gray", linestyle=":", alpha=0.5,
               label="Random baseline (0.25)")

    ax.set_xlabel("α  (1.0 = Track A only, 0.0 = Track B only)")
    ax.set_ylabel("Brier Score (lower = better)")
    ax.set_title("Ensemble Performance: Brier Score vs. Alpha")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()

    path = os.path.join(EVAL_DIR, "brier_vs_alpha.png")
    fig.savefig(path, dpi=150)
    print(f"Saved {path}")
    plt.close(fig)


def plot_calibration():
    """
    PURPOSE: Check whether the model's predicted probabilities match
    observed frequencies.

    HOW IT WORKS:
    Reads best_predictions.csv (predictions at optimal alpha).
    Bins predictions into ~10 groups by predicted probability.
    For each bin, computes the actual fraction of YES outcomes.
    Plots predicted vs. observed. A perfectly calibrated model
    lies on the diagonal.

    HOW TO READ THIS PLOT:
    - Points above the diagonal: model is under-confident
      (predicts 30% but outcome happens 50% of the time)
    - Points below the diagonal: model is over-confident
      (predicts 80% but outcome only happens 60% of the time)
    - Points on the diagonal: perfect calibration

    NOTE: With few test samples (<30), this plot will be very noisy.
    Don't over-interpret individual points.

    CALLED BY: main()
    """
    preds = pd.read_csv(os.path.join(EVAL_DIR, "best_predictions.csv"))

    n_bins = min(10, len(preds) // 2)  # Need at least 2 samples per bin
    if n_bins < 3:
        print("⚠️  Too few samples for a meaningful calibration curve. Skipping.")
        return

    prob_true, prob_pred = calibration_curve(
        preds["y_true"], preds["P_final"], n_bins=n_bins, strategy="uniform"
    )

    fig, ax = plt.subplots(figsize=(8, 8))
    ax.plot([0, 1], [0, 1], "k--", alpha=0.5, label="Perfect calibration")
    ax.plot(prob_pred, prob_true, "o-", linewidth=2, markersize=8, label="Model")

    ax.set_xlabel("Predicted probability")
    ax.set_ylabel("Observed frequency")
    ax.set_title(f"Calibration Curve (α = {preds['alpha'].iloc[0]:.2f})")
    ax.legend()
    ax.grid(alpha=0.3)
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.05, 1.05)
    fig.tight_layout()

    path = os.path.join(EVAL_DIR, "calibration.png")
    fig.savefig(path, dpi=150)
    print(f"Saved {path}")
    plt.close(fig)


def main():
    plot_brier_vs_alpha()
    plot_calibration()
    print("\n✅ Visualizations complete.")


if __name__ == "__main__":
    main()
```

### 10.4 Verification

```bash
uv run python -m backtest.visualize
```

Open `data/evaluation/brier_vs_alpha.png` and `data/evaluation/calibration.png`. The Brier plot should show a clear minimum. The calibration plot may be noisy with few samples — that's expected.

---

## 11. File 7: `run.py`

### 11.1 Purpose

Thin orchestrator at the project root. Calls each phase's `main()` in order. You can also run each phase independently via `uv run python -m backtest.<module>`.

### 11.2 Complete Code

```python
"""
run.py

Runs all backtest phases in order.
Expects DISCOVERY_MODE = False in data_collection.py (i.e., you've already
done the discovery step and configured your series).

Run with:  uv run python run.py
"""

from backtest import data_collection, track_a, track_b, backtest, visualize


def main():
    print("=" * 60)
    print("PHASE 1: Data Collection")
    print("=" * 60)
    data_collection.main()

    print("\n" + "=" * 60)
    print("PHASE 2: Track A — Lasso Logistic Regression")
    print("=" * 60)
    track_a.main()

    print("\n" + "=" * 60)
    print("PHASE 3: Track B — SYNTHETIC predictions")
    print("=" * 60)
    track_b.main()

    print("\n" + "=" * 60)
    print("PHASE 4: Synthesis & Evaluation")
    print("=" * 60)
    backtest.main()

    print("\n" + "=" * 60)
    print("VISUALIZATION")
    print("=" * 60)
    visualize.main()

    print("\n" + "=" * 60)
    print("BACKTEST COMPLETE")
    print("=" * 60)
    print("Check data/evaluation/ for results.")


if __name__ == "__main__":
    main()
```

---

## 12. Next Steps

**After pipeline validation (synthetic Track B):**
1. Confirm backtest runs end-to-end without errors
2. Verify optimal α is near 1.0 (expected with synthetic data)
3. Inspect Track A coefficients — do selected markets make economic sense?

**Stage 2 — real RLM (separate effort):**
1. Pick a news API (SerpAPI or NewsAPI)
2. Implement the recursive agent workflow from `RLM.md` §3
3. Wire up Grok API with a provider-agnostic interface
4. Re-run backtest with `mode=REAL` and compare

**Hyperparameter tuning (later):**
- Vary snapshot time `t` (3 days, 7 days, 14 days before resolution instead of midpoint)
- Vary self-consistency `k` (3, 5, 10 runs)
- Try multiple time increments as combined features

---

## 13. Troubleshooting

| Problem | Likely Cause | Fix |
|---------|-------------|-----|
| `401 Unauthorized` from Kalshi | Wrong key ID, wrong key file, or wrong base URL | Verify `.env` values. Try the demo URL first. |
| `discover_series()` returns nothing | API or auth issue | Check the raw response by adding `print(resp)` in `KalshiClient.get()`. |
| Candlestick field names don't match | Kalshi API returns different fields than expected | Inspect `data/raw/candles_*.json`, update `price_from_candle()`. |
| `features.csv` has very few columns | Few markets were active at target midpoints | Expand FEATURE_SERIES to include more series. |
| Lasso coefficients all zero | Regularization too strong, or too few training samples | Check `model.C_` — if very small, there may not be enough signal. |
| Brier > 0.25 (worse than random) | Target leaked into features, or train/test contamination | Verify target ticker excluded from feature columns. Verify temporal split. |
| Optimal α is 0.0 | Track A is useless | Inspect features — are prices actually varying, or all 0.5? |
| Optimal α is 1.0 | Track B is useless | Expected with synthetic data. Not a bug. |

---

## Summary Checklist

- [ ] Kalshi account created, API key generated
- [ ] `kalshi_private_key.txt` saved in project root
- [ ] `.env` created with `KALSHI_KEY_ID` and `KALSHI_PRIVATE_KEY_PATH`
- [ ] `.gitignore` includes `.env`, `kalshi_private_key.*`, `data/`
- [ ] `uv init` run, dependencies installed
- [ ] `kalshi_client.py` created and verified (test GET request works)
- [ ] `data_collection.py` run in discovery mode, series selected
- [ ] `data_collection.py` run in full mode, `markets.csv` and `features.csv` verified
- [ ] Candlestick response format verified, `price_from_candle()` updated if needed
- [ ] `track_a.py` run, predictions and coefficients inspected
- [ ] `track_b.py` run, `mode=SYNTHETIC` confirmed
- [ ] `backtest.py` run, alpha sweep results inspected
- [ ] `visualize.py` run, plots reviewed
- [ ] Sanity checks pass (α near 1.0, Brier < 0.25, features make sense)
