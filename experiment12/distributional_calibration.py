"""
experiment12/distributional_calibration.py

Compute CRPS (Continuous Ranked Probability Score) on Kalshi implied distributions
reconstructed from multi-strike prediction markets.

CRPS measures the quality of a full probabilistic forecast against a realized
scalar outcome. Lower CRPS = better calibrated distribution. CRPS generalizes
MAE to distributional forecasts: for a point mass, CRPS = MAE.

Provides benchmark comparisons against uniform, historical empirical, and
point-forecast distributions.

Uses cached candle data from experiment2 and CDF reconstruction logic from
experiment7.
"""

import os
import json
import csv
import io
import urllib.request
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from typing import Optional

CANDLE_DIR = "data/exp2/raw/candles"


# ---------------------------------------------------------------------------
# Core CRPS computation
# ---------------------------------------------------------------------------


def compute_crps(
    cdf_strikes: list[float],
    cdf_values: list[float],
    realized_value: float,
    tail_extension: float = 1.0,
) -> float:
    """Compute CRPS for a Kalshi implied distribution vs a realized value.

    CRPS = integral of [F(x) - H(x - realized)]^2 dx

    where F(x) is the standard CDF (P(X <= x)) and H is the Heaviside step
    function (H(z) = 1 if z >= 0, else 0).

    Parameters
    ----------
    cdf_strikes : list[float]
        Sorted strike thresholds (ascending).
    cdf_values : list[float]
        Survival function values P(X > strike) at each strike.
        Must be same length as cdf_strikes.
    realized_value : float
        The actual observed outcome.
    tail_extension : float
        How far beyond min/max strikes to extend the integration domain.
        CDF is assumed flat (0 below min, 1 above max) in the tails.

    Returns
    -------
    float
        CRPS score (lower is better, 0 = perfect).
    """
    if len(cdf_strikes) != len(cdf_values):
        raise ValueError("cdf_strikes and cdf_values must have the same length")
    if len(cdf_strikes) < 2:
        raise ValueError("Need at least 2 strike points to compute CRPS")

    # Convert survival P(X > x) to standard CDF F(x) = P(X <= x) = 1 - survival
    strikes = np.array(cdf_strikes, dtype=float)
    f_values = 1.0 - np.array(cdf_values, dtype=float)

    # Clip CDF to [0, 1] for robustness against slight arbitrage violations
    f_values = np.clip(f_values, 0.0, 1.0)

    # Define integration domain
    x_min = strikes[0] - tail_extension
    x_max = strikes[-1] + tail_extension

    # Build piecewise linear CDF function:
    #   F(x) = 0          for x < strikes[0]
    #   F(x) = interp     for strikes[0] <= x <= strikes[-1]
    #   F(x) = 1          for x > strikes[-1]
    # (This is consistent with flat tail assumptions.)

    def cdf_at(x: float) -> float:
        if x < strikes[0]:
            return 0.0
        if x > strikes[-1]:
            return 1.0
        return float(np.interp(x, strikes, f_values))

    # CRPS = integral of [F(x) - H(x - y)]^2 dx
    # Split into two regions:
    #   x < y:  H = 0, integrand = F(x)^2
    #   x >= y: H = 1, integrand = (F(x) - 1)^2 = (1 - F(x))^2

    # Build breakpoints for piecewise integration
    breakpoints = sorted(set([x_min] + strikes.tolist() + [realized_value, x_max]))
    breakpoints = [b for b in breakpoints if x_min <= b <= x_max]
    breakpoints = sorted(set(breakpoints))

    crps = 0.0

    for i in range(len(breakpoints) - 1):
        a = breakpoints[i]
        b = breakpoints[i + 1]
        if b <= a:
            continue

        fa = cdf_at(a)
        fb = cdf_at(b)
        width = b - a

        # Within this segment, F(x) is linear: F(x) = fa + (fb - fa) * (x - a) / (b - a)
        # We need integral of g(x)^2 dx over [a, b], where g(x) is either F(x) or F(x)-1.

        if b <= realized_value:
            # Entire segment below realized: integrand = F(x)^2
            crps += _integrate_squared_linear(fa, fb, width)
        elif a >= realized_value:
            # Entire segment above realized: integrand = (F(x) - 1)^2
            crps += _integrate_squared_linear(fa - 1.0, fb - 1.0, width)
        else:
            # Segment straddles realized_value: split at realized_value
            t = (realized_value - a) / width  # fraction of interval below realized
            f_mid = fa + (fb - fa) * t
            w_left = realized_value - a
            w_right = b - realized_value

            crps += _integrate_squared_linear(fa, f_mid, w_left)
            crps += _integrate_squared_linear(f_mid - 1.0, fb - 1.0, w_right)

    return float(crps)


def _integrate_squared_linear(y0: float, y1: float, width: float) -> float:
    """Integrate [y0 + (y1 - y0) * t]^2 * width dt from t=0 to t=1.

    For a linear function f(t) = y0 + (y1 - y0)*t on [0, 1],
    integral of f(t)^2 dt = (y0^2 + y0*y1 + y1^2) / 3.
    Multiply by width to convert from unit interval to actual interval.
    """
    if width <= 0:
        return 0.0
    return width * (y0**2 + y0 * y1 + y1**2) / 3.0


# ---------------------------------------------------------------------------
# Benchmark CRPS: uniform distribution
# ---------------------------------------------------------------------------


def compute_uniform_crps(
    min_val: float,
    max_val: float,
    realized_value: float,
) -> float:
    """Compute CRPS for a uniform distribution U(min_val, max_val).

    Uses numerical integration via the same piecewise approach as compute_crps,
    treating F(x) = (x - min_val) / (max_val - min_val) for x in [min, max].

    Parameters
    ----------
    min_val : float
        Lower bound of the uniform distribution.
    max_val : float
        Upper bound of the uniform distribution.
    realized_value : float
        The actual observed outcome.

    Returns
    -------
    float
        CRPS score.
    """
    if max_val <= min_val:
        raise ValueError("max_val must be greater than min_val")

    span = max_val - min_val
    y = realized_value

    # Closed-form CRPS for Uniform(a, b):
    #   If y < a: CRPS = (a - y) + span/3
    #   If y > b: CRPS = (y - b) + span/3
    #   If a <= y <= b:
    #     t = (y - a) / span
    #     CRPS = span * (t^2 + (1-t)^2 - 1) / 3  +  ... actually integrate directly

    # More reliable: build a synthetic CDF and use compute_crps logic.
    # Uniform CDF: F(x) = 0 for x < a, (x-a)/(b-a) for a <= x <= b, 1 for x > b.
    # Survival S(x) = 1 - F(x).

    n_points = 50
    strikes = np.linspace(min_val, max_val, n_points).tolist()
    survival_values = [1.0 - (s - min_val) / span for s in strikes]

    return compute_crps(strikes, survival_values, realized_value, tail_extension=0.0)


# ---------------------------------------------------------------------------
# Benchmark CRPS: historical empirical distribution
# ---------------------------------------------------------------------------


def compute_historical_crps(
    past_values: list[float],
    realized_value: float,
) -> float:
    """Compute CRPS for an empirical CDF built from historical observations.

    The empirical CDF is a step function: F(x) = (# of past_values <= x) / n.
    CRPS is computed by piecewise integration over each step.

    Parameters
    ----------
    past_values : list[float]
        Historical observations used to build the empirical distribution.
    realized_value : float
        The actual observed outcome.

    Returns
    -------
    float
        CRPS score.

    Raises
    ------
    ValueError
        If past_values is empty.
    """
    if not past_values:
        raise ValueError("past_values must be non-empty")

    sorted_vals = np.sort(past_values)
    n = len(sorted_vals)

    # Build step function breakpoints: at each observed value, CDF jumps by 1/n.
    # Between observations, CDF is flat.
    # CRPS = integral [F(x) - H(x - y)]^2 dx

    y = realized_value

    # Integration domain: extend slightly beyond data range
    margin = 0.1 * (sorted_vals[-1] - sorted_vals[0]) if n > 1 else 1.0
    x_min = min(sorted_vals[0], y) - margin
    x_max = max(sorted_vals[-1], y) + margin

    # Build all breakpoints
    breakpoints = sorted(set([x_min] + sorted_vals.tolist() + [y, x_max]))

    crps = 0.0

    for i in range(len(breakpoints) - 1):
        a = breakpoints[i]
        b = breakpoints[i + 1]
        if b <= a:
            continue

        # Empirical CDF is constant between breakpoints:
        # F(x) = (# of sorted_vals <= a) / n for x in (a, b]
        # Use value at midpoint for the step function level
        f_val = np.searchsorted(sorted_vals, a, side="right") / n
        width = b - a

        if b <= y:
            # Below realized: integrand = F(x)^2
            crps += width * f_val**2
        elif a >= y:
            # Above realized: integrand = (F(x) - 1)^2
            crps += width * (f_val - 1.0) ** 2
        else:
            # Straddles realized_value
            w_left = y - a
            w_right = b - y
            crps += w_left * f_val**2
            crps += w_right * (f_val - 1.0) ** 2

    return float(crps)


# ---------------------------------------------------------------------------
# Benchmark CRPS: point forecast (degenerate distribution)
# ---------------------------------------------------------------------------


def compute_point_crps(
    point_forecast: float,
    realized_value: float,
) -> float:
    """Compute CRPS for a degenerate (point mass) distribution.

    For a point mass at `point_forecast`, the CDF is a Heaviside step.
    CRPS reduces to the absolute error: |forecast - realized|.

    Parameters
    ----------
    point_forecast : float
        The point forecast value.
    realized_value : float
        The actual observed outcome.

    Returns
    -------
    float
        CRPS = |point_forecast - realized_value|.
    """
    return abs(point_forecast - realized_value)


# ---------------------------------------------------------------------------
# CDF extraction from candle data
# ---------------------------------------------------------------------------


def extract_event_cdf_at_time(
    event_markets_df: pd.DataFrame,
    target_time_utc: datetime,
    candle_dir: str = CANDLE_DIR,
) -> Optional[dict]:
    """Extract the implied CDF for an event at a specific timestamp.

    Loads hourly candle data for each market in the event, finds the candle
    closest to `target_time_utc`, and assembles the survival function.

    Parameters
    ----------
    event_markets_df : pd.DataFrame
        Markets belonging to one event. Must have columns:
        ticker, floor_strike, strike_type.
    target_time_utc : datetime
        The target UTC timestamp to extract the CDF at.
    candle_dir : str
        Directory containing candle JSON files ({TICKER}_60.json).

    Returns
    -------
    dict or None
        Dictionary with keys:
        - 'strikes': list of float thresholds (ascending)
        - 'cdf_values': list of float survival probabilities P(X > strike)
        - 'timestamp': actual timestamp used (closest available)
        Returns None if insufficient data (< 2 strikes with prices).
    """
    if target_time_utc.tzinfo is None:
        target_time_utc = target_time_utc.replace(tzinfo=timezone.utc)

    target_ts = target_time_utc.timestamp()

    cdf_points = []

    for _, row in event_markets_df.iterrows():
        ticker = row["ticker"]
        strike = float(row["floor_strike"])

        candle_path = os.path.join(candle_dir, f"{ticker}_60.json")
        if not os.path.exists(candle_path):
            continue

        try:
            with open(candle_path) as f:
                candles = json.load(f)
        except (json.JSONDecodeError, IOError):
            continue

        if not candles:
            continue

        # Find candle closest to target timestamp
        best_candle = None
        best_dist = float("inf")

        for c in candles:
            ts = c.get("end_period_ts")
            if ts is None:
                continue
            dist = abs(ts - target_ts)
            if dist < best_dist:
                best_dist = dist
                best_candle = c

        if best_candle is None:
            continue

        # Extract close price (market price = P(X > strike))
        price_obj = best_candle.get("price", {})
        close_price = price_obj.get("close_dollars")
        if close_price is None:
            continue

        try:
            price = float(close_price)
        except (ValueError, TypeError):
            continue

        actual_ts = best_candle.get("end_period_ts", target_ts)
        cdf_points.append((strike, price, actual_ts))

    if len(cdf_points) < 2:
        return None

    # Sort by strike (ascending)
    cdf_points.sort(key=lambda x: x[0])

    strikes = [p[0] for p in cdf_points]
    cdf_values = [p[1] for p in cdf_points]

    # Use the median actual timestamp as the representative timestamp
    actual_timestamps = [p[2] for p in cdf_points]
    median_ts = sorted(actual_timestamps)[len(actual_timestamps) // 2]
    timestamp = datetime.fromtimestamp(median_ts, tz=timezone.utc)

    return {
        "strikes": strikes,
        "cdf_values": cdf_values,
        "timestamp": timestamp,
    }


# ---------------------------------------------------------------------------
# FRED data fetching: CPI, Jobless Claims, GDP
# ---------------------------------------------------------------------------


def _fetch_fred_csv(
    series_id: str,
    start_date: str,
    end_date: str,
) -> pd.Series:
    """Fetch a FRED series as CSV and return a pandas Series.

    Parameters
    ----------
    series_id : str
        FRED series identifier (e.g., 'CPIAUCSL', 'ICSA').
    start_date : str
        Start date in YYYY-MM-DD format.
    end_date : str
        End date in YYYY-MM-DD format.

    Returns
    -------
    pd.Series
        Series with DatetimeIndex and float values.

    Raises
    ------
    ValueError
        If no data is returned.
    """
    url = (
        f"https://fred.stlouisfed.org/graph/fredgraph.csv"
        f"?id={series_id}"
        f"&cosd={start_date}"
        f"&coed={end_date}"
    )

    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        text = resp.read().decode("utf-8")

    reader = csv.DictReader(io.StringIO(text))
    data = {}
    for row in reader:
        # FRED uses "observation_date" as the date column (same fix as experiment8)
        date_str = row.get("observation_date", row.get("DATE", ""))
        val_str = row.get(series_id, ".")
        if val_str and val_str.strip() and val_str.strip() != ".":
            try:
                data[pd.Timestamp(date_str)] = float(val_str.strip())
            except (ValueError, TypeError):
                pass

    if not data:
        raise ValueError(f"No data returned for FRED series {series_id}")

    return pd.Series(data, name=series_id).sort_index()


def fetch_historical_cpi_from_fred(
    start_date: str = "2023-01-01",
    end_date: str = "2026-02-01",
) -> list[float]:
    """Fetch monthly CPI and compute month-over-month percentage changes.

    Uses FRED series CPIAUCSL (Consumer Price Index for All Urban Consumers).

    Parameters
    ----------
    start_date : str
        Start date in YYYY-MM-DD format.
    end_date : str
        End date in YYYY-MM-DD format.

    Returns
    -------
    list[float]
        Month-over-month CPI percentage changes. Each value represents
        the percent change from the previous month (e.g., 0.3 means +0.3%).
    """
    cpi_levels = _fetch_fred_csv("CPIAUCSL", start_date, end_date)
    pct_changes = cpi_levels.pct_change().dropna() * 100.0
    return pct_changes.tolist()


def fetch_historical_jobless_claims(
    start_date: str = "2023-01-01",
    end_date: str = "2026-02-01",
) -> list[float]:
    """Fetch weekly initial jobless claims from FRED.

    Uses FRED series ICSA (Initial Claims, Seasonally Adjusted).

    Parameters
    ----------
    start_date : str
        Start date in YYYY-MM-DD format.
    end_date : str
        End date in YYYY-MM-DD format.

    Returns
    -------
    list[float]
        Weekly initial jobless claims values (in thousands).
    """
    claims = _fetch_fred_csv("ICSA", start_date, end_date)
    return claims.tolist()


def fetch_historical_gdp(
    start_date: str = "2020-01-01",
    end_date: str = "2026-02-01",
) -> list[float]:
    """Fetch quarterly real GDP growth rate from FRED.

    Uses FRED series A191RL1Q225SBEA (Real GDP percent change, annualized).

    Parameters
    ----------
    start_date : str
        Start date in YYYY-MM-DD format.
    end_date : str
        End date in YYYY-MM-DD format.

    Returns
    -------
    list[float]
        Quarterly real GDP growth rate values (annualized percent change).
    """
    gdp = _fetch_fred_csv("A191RL1Q225SBEA", start_date, end_date)
    return gdp.tolist()
