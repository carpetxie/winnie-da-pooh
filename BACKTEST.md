# BACKTEST.md: Kalshi RLM Backtesting Guide

## Table of Contents
1. [Overview & Strategy](#1-overview--strategy)
2. [API Setup](#2-api-setup)
3. [Project Setup](#3-project-setup)
4. [File 1: kalshi_client.py](#4-file-1-kalshi_clientpy)
5. [File 2: data_collection.py](#5-file-2-data_collectionpy)
6. [File 3: track_a.py](#6-file-3-track_apy)
7. [File 4: track_b.py](#7-file-4-track_bpy)
8. [File 5: backtest.py](#8-file-5-backtestpy)
9. [File 6: visualize.py](#9-file-6-visualizepy)
10. [File 7: run.py](#10-file-7-runpy)

---

## 1. Overview & Strategy

### System Architecture

Two-track prediction system combined via weighted log-odds ensemble:

**Track A: Universal Calibration**
- Corrects structural biases in market prices using metadata
- Features: price, volatility, time-to-close
- Model: Logistic Regression on diverse markets

**Track B: Recursive Language Model** (synthetic for now)
- Analyzes news to generate independent predictions
- Will be implemented in Stage 2

**Synthesis:**
```
L_final = α·L_stat + (1-α)·L_news
P_final = sigmoid(L_final)
```

Sweep α from 0.0 to 1.0, optimize via Brier Score.

**(Universal Calibration):**
- **Insight**: Market prices are informative but biased (overconfidence, time decay, volatility effects)
- **Strategy**: Train calibration model on N=3000 diverse markets
- **Advantage**: Every market is a training example (no overlap needed)

### Features at Market Midpoint

```
midpoint = (open_time + close_time) / 2
```

| Feature | Calculation | Meaning |
|---------|-------------|---------|
| `feature_price` | Price at midpoint from candlesticks | Market's baseline prediction |
| `feature_volatility` | Std dev of prices 7 days before midpoint | Uncertainty |
| `feature_days_remaining` | Days from midpoint to close | Time until resolution |

**Target**: `y_true` (0 or 1, did market resolve YES?)

**Model learns**: "When price=0.70, volatility=0.15, days=10 → true probability is 0.62"

### Data Strategy

1. Fetch ALL settled markets from past 12 months
2. Sort by series frequency (prioritize weekly)
3. Sample N=3000 markets
4. Temporal split: 80% train (earliest), 20% test (most recent)

### Output Compatibility

Track A outputs `track_a_predictions.csv`:
- `ticker`, `P_stat`, `L_stat`, `y_true`

This matches the original schema, so Track B and synthesis require no changes.

---

## 2. API Setup

### Kalshi Credentials

1. Create account: https://kalshi.com
2. Get API keys: Account Settings → Profile Settings → "Create New API Key"
   - **Key ID**: UUID (e.g., `a952bcbe-ec3b-4b5b-b8f9-11dae589608c`)
   - **Private Key**: RSA key in PEM format, downloaded as `.txt` file

3. Save credentials:
```bash
cd ~/Desktop/winnie
echo "KALSHI_API_KEY_ID=your_key_id_here" > .env
echo "KALSHI_API_SECRET_PATH=/path/to/your/private_key.txt" >> .env
```

### Authentication

Kalshi uses **RSA-PSS with SHA256** signing:

**Headers required:**
- `KALSHI-ACCESS-KEY`: Your Key ID
- `KALSHI-ACCESS-TIMESTAMP`: Current time in milliseconds since epoch
- `KALSHI-ACCESS-SIGNATURE`: Base64-encoded RSA-PSS signature of `{timestamp}{HTTP_METHOD}{path}`

**Important**: Strip query params when signing. Sign `/markets`, not `/markets?limit=10`.

### API Endpoints

**Base URL**: `https://api.elections.kalshi.com/trade-api/v2`

**Key endpoints:**

```
GET /markets
  - Params: status, series_ticker, min_settled_ts, limit, cursor
  - Returns: {markets: [...], cursor: "..."}

GET /series
  - Returns: {series: [...]}

GET /series/{series_ticker}/markets/{ticker}/candlesticks
  - **REQUIRED** params: start_ts, end_ts, period_interval
  - period_interval: 1 (1min), 60 (1hr), or 1440 (1day)
  - Returns: {candlesticks: [{end_period_ts, price: {close, close_dollars, ...}, ...}]}
```

**Rate limit**: 100 requests/minute

### Critical: Candlestick Endpoint Structure

❌ **WRONG**:
```
GET /markets/{ticker}/candlesticks  # Returns 404
```

✅ **CORRECT**:
```
GET /series/{series_ticker}/markets/{ticker}/candlesticks?start_ts={ts}&end_ts={ts}&period_interval=1440
```

**Response structure:**
```json
{
  "candlesticks": [
    {
      "end_period_ts": 1769749200,
      "price": {
        "close": 15,
        "close_dollars": "0.1500",
        "open": 10,
        "high": 20,
        "low": 5
      },
      "volume": 100
    }
  ]
}
```

Extract price as: `candlestick['price']['close_dollars']` (already 0.0-1.0 scale)

---

## 3. Project Setup

```bash
cd ~/Desktop/winnie

# Initialize UV environment
uv venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
uv add pandas numpy scikit-learn matplotlib requests cryptography python-dotenv

# Create directory structure
mkdir -p backtest data/{raw,processed,models,evaluation}

# Create .gitignore
cat > .gitignore << 'EOF'
.env
*.txt  # Exclude RSA private key files
__pycache__/
*.pyc
.venv/
data/
.DS_Store
EOF
```

---

## 4. File 1: kalshi_client.py

**Purpose**: Handles Kalshi API authentication and requests.

**Key functions:**
- `_sign()`: RSA-PSS signature generation
- `get()`: Single HTTP GET with signed headers
- `get_all_pages()`: Cursor-based pagination

### Complete Code

```python
"""
backtest/kalshi_client.py

Handles Kalshi API authentication (RSA-PSS signing) and HTTP requests.
"""

import os
import time
import base64
from datetime import datetime
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
import requests as http_lib
from dotenv import load_dotenv

load_dotenv()


class KalshiClient:
    """
    Kalshi API client with RSA-PSS authentication.

    Usage:
        client = KalshiClient()
        markets = client.get("/markets", params={"series_ticker": "KXJOBLESSCLAIMS", "status": "settled"})
    """

    BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"

    def __init__(self):
        self.key_id = os.getenv("KALSHI_API_KEY_ID")
        key_path = os.getenv("KALSHI_API_SECRET_PATH")

        if not self.key_id or not key_path:
            raise ValueError("Set KALSHI_API_KEY_ID and KALSHI_API_SECRET_PATH in .env")

        with open(key_path, "rb") as f:
            self.private_key = serialization.load_pem_private_key(
                f.read(), password=None, backend=default_backend()
            )

    def _sign(self, timestamp_ms: int, method: str, path: str) -> str:
        """Generate RSA-PSS signature for request."""
        message = f"{timestamp_ms}{method}{path}"
        signature = self.private_key.sign(
            message.encode("utf-8"),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )
        return base64.b64encode(signature).decode("utf-8")

    def _headers(self, method: str, path: str) -> dict:
        """Build signed headers for Kalshi API request."""
        # Strip query params for signing
        path_for_signing = path.split("?")[0]
        timestamp_ms = int(datetime.now().timestamp() * 1000)
        signature = self._sign(timestamp_ms, method, path_for_signing)

        return {
            "KALSHI-ACCESS-KEY": self.key_id,
            "KALSHI-ACCESS-TIMESTAMP": str(timestamp_ms),
            "KALSHI-ACCESS-SIGNATURE": signature,
        }

    def get(self, path: str, params: dict = None) -> dict:
        """Execute GET request with signed headers."""
        url = f"{self.BASE_URL}{path}"
        headers = self._headers("GET", path)
        r = http_lib.get(url, headers=headers, params=params)
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
        Fetch all pages via cursor-based pagination.

        Args:
            path: API endpoint
            params: Query parameters
            result_key: JSON key containing results ("markets", "series", "candlesticks")
            page_limit: Items per page (max 1000)
            delay: Sleep between requests (0.7s ≈ 85 req/min)

        Returns:
            Flat list of all results across pages
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

### Verification

```bash
uv run python -c "
from backtest.kalshi_client import KalshiClient
c = KalshiClient()
resp = c.get('/markets', {'limit': 1})
print(f'✓ Authentication works. Sample ticker: {resp[\"markets\"][0][\"ticker\"]}')
"
```

---

## 5. File 2: data_collection.py

**Purpose**: Fetch N=3000 random settled markets, compute features at midpoint, save to CSV.

**Key changes from original:**
1. Fetch ALL settled markets (not specific series)
2. Sort by frequency, sample 3000
3. Use correct candlestick endpoint: `/series/{series_ticker}/markets/{ticker}/candlesticks`
4. Calculate `feature_price` (price at midpoint), `feature_volatility` (7-day std dev), `feature_days_remaining`
5. Output: `universal_features.csv` (not `features.csv`)

### Complete Code

```python
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
```

### Verification

```bash
uv run python -m backtest.data_collection
```

**Expected output:**
- `data/raw/all_settled_markets.json` (cached)
- `data/raw/candles_*.json` (one per market)
- `data/processed/universal_features.csv`

**Check:**
- CSV has ~3000 rows
- `feature_price` column has values in [0, 1]
- `feature_volatility` column has values >= 0
- `split` column has "train" and "test"

---

## 6. File 3: track_a.py

**Purpose**: Train Universal Calibration model on `universal_features.csv`.

**Key changes:**
1. Load `universal_features.csv` (not `features.csv` + `markets.csv`)
2. Features: `[feature_price, feature_volatility, feature_days_remaining]`
3. Model: Standard Logistic Regression (L2, not L1 Lasso)
4. Output: Same schema (`track_a_predictions.csv`)

### Complete Code

```python
"""
backtest/track_a.py

Phase 2: Universal Calibration Model Training

Trains a logistic regression model to calibrate market prices using metadata.

Run with: uv run python -m backtest.track_a
"""

import os
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV

PROCESSED_DIR = "data/processed"
MODELS_DIR = "data/models"


def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load universal_features.csv and split by 'split' column.

    Returns:
        (train_df, test_df)
    """
    df = pd.read_csv(
        os.path.join(PROCESSED_DIR, "universal_features.csv"),
        parse_dates=['open_time', 'close_time', 'midpoint']
    )

    train_df = df[df['split'] == 'train'].copy()
    test_df = df[df['split'] == 'test'].copy()

    print(f"Loaded data: {len(train_df)} train, {len(test_df)} test")

    return train_df, test_df


def train_model(X_train: np.ndarray, y_train: np.ndarray) -> LogisticRegression:
    """
    Train Universal Calibration model.

    Uses LogisticRegression with L2 penalty (not L1 Lasso).
    Optional: Wrap with CalibratedClassifierCV for extra calibration.

    Args:
        X_train: Feature matrix [feature_price, feature_volatility, feature_days_remaining]
        y_train: Binary outcomes (0 or 1)

    Returns:
        Fitted model
    """
    # Option 1: Standard Logistic Regression
    model = LogisticRegression(
        penalty='l2',
        C=1.0,  # Regularization strength (lower = more regularization)
        max_iter=1000,
        random_state=42
    )

    # Option 2: Calibrated Classifier (uncomment to use)
    # base_model = LogisticRegression(penalty='l2', C=1.0, max_iter=1000, random_state=42)
    # model = CalibratedClassifierCV(base_model, cv=5, method='sigmoid')

    model.fit(X_train, y_train)

    print(f"✓ Model trained")
    if hasattr(model, 'coef_'):
        print(f"  Coefficients: {model.coef_[0]}")
        print(f"  Intercept: {model.intercept_[0]}")

    return model


def predict(model: LogisticRegression, X_test: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Generate calibrated probabilities and log-odds.

    Returns:
        (P_stat, L_stat)
    """
    P_stat = model.predict_proba(X_test)[:, 1]
    P_stat = np.clip(P_stat, 1e-6, 1 - 1e-6)
    L_stat = np.log(P_stat / (1 - P_stat))

    return P_stat, L_stat


def main():
    os.makedirs(MODELS_DIR, exist_ok=True)

    # Load
    train_df, test_df = load_data()

    # Drop rows with missing features
    feature_cols = ['feature_price', 'feature_volatility', 'feature_days_remaining']
    train_df = train_df.dropna(subset=feature_cols)
    test_df = test_df.dropna(subset=feature_cols)

    X_train = train_df[feature_cols].values
    y_train = train_df['y_true'].values
    X_test = test_df[feature_cols].values
    y_test = test_df['y_true'].values
    test_tickers = test_df['ticker'].values

    print(f"After dropping NaN: {len(train_df)} train, {len(test_df)} test")

    # Train
    print("\nTraining Universal Calibration Model...")
    model = train_model(X_train, y_train)

    # Predict
    P_stat, L_stat = predict(model, X_test)

    # Save predictions
    results = pd.DataFrame({
        'ticker': test_tickers,
        'P_stat': P_stat,
        'L_stat': L_stat,
        'y_true': y_test,
    })
    results.to_csv(os.path.join(PROCESSED_DIR, "track_a_predictions.csv"), index=False)

    # Save model coefficients
    if hasattr(model, 'coef_'):
        coefs = pd.DataFrame({
            'feature': feature_cols,
            'coefficient': model.coef_[0],
        })
        coefs.to_csv(os.path.join(MODELS_DIR, "track_a_coefficients.csv"), index=False)

    print(f"\n✅ Track A complete")
    print(f"   {len(results)} test predictions saved")
    print(f"   Mean P_stat: {P_stat.mean():.3f}")
    print(f"   Mean y_true: {y_test.mean():.3f}")


if __name__ == "__main__":
    main()
```

### Verification

```bash
uv run python -m backtest.track_a
```

**Expected:**
- `data/processed/track_a_predictions.csv` (same schema as before)
- `data/models/track_a_coefficients.csv` (3 rows: price, volatility, days_remaining)

**Check:**
- P_stat values are in [0, 1]
- L_stat values are real numbers
- Coefficients make sense (e.g., positive for feature_price)

---

## 7. File 4: track_b.py

**No changes needed.** Uses same synthetic approach as before.

(Refer to existing file)

---

## 8. File 5: backtest.py

**No changes needed.** Synthesis logic remains identical.

(Refer to existing file)

---

## 9. File 6: visualize.py

**No changes needed.** Plotting logic remains identical.

(Refer to existing file)

---

## 10. File 7: run.py

**No changes needed.** Orchestration remains identical.

(Refer to existing file)

---

## Summary

### What Changed

1. **Track A strategy**: Correlation Matrix → Universal Calibration
2. **Data collection**: Specific series → N=3000 random markets
3. **Features**: Cross-market prices → (price, volatility, days_remaining) at midpoint
4. **Candlestick endpoint**: Corrected to `/series/{series_ticker}/markets/{ticker}/candlesticks`
5. **Model**: Lasso (L1) → Standard Logistic Regression (L2)

### What Stayed the Same

- Track B (synthetic)
- Synthesis (alpha sweep)
- Visualization
- Output schemas

### Next Steps

1. Run `uv run python -m backtest.data_collection` (~10-15 min)
2. Run `uv run python -m backtest.track_a`
3. Run `uv run python -m backtest.track_b`
4. Run `uv run python -m backtest.backtest`
5. Run `uv run python -m backtest.visualize`
Or run all at once: `uv run python run.py`
