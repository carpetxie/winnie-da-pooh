"""
experiment8/tips_comparison.py

Compare Kalshi CPI market prices to TIPS breakeven inflation rates.

TIPS breakeven = nominal Treasury yield - TIPS yield = bond market's
implied inflation expectation. If Kalshi CPI markets lead TIPS breakevens,
prediction markets contain price discovery information beyond bond markets.

Requires one FRED API fetch for T10YIE (10-year breakeven inflation rate).
"""

import os
import json
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from tqdm import tqdm
from scipy import stats

CANDLE_DIR = "data/exp2/raw/candles"
DATA_DIR = "data/exp8"

# FRED series for TIPS breakeven inflation
TIPS_SERIES = {
    "T10YIE": "10-Year Breakeven Inflation Rate",
    "T5YIE": "5-Year Breakeven Inflation Rate",
}


def fetch_fred_series(series_id: str, start_date: str = "2024-10-01",
                      end_date: str = "2026-02-18") -> pd.Series:
    """Fetch a FRED series as a pandas Series with DatetimeIndex."""
    import urllib.request
    import csv
    import io

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
        # FRED uses "observation_date" as the date column
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


def build_kalshi_cpi_index(candle_dir: str = CANDLE_DIR) -> pd.Series:
    """Build a daily Kalshi CPI expectations index.

    For each day, average the closing prices of all active CPI markets.
    Higher average price → market expects higher CPI.

    We weight by inverse distance from 50% (markets far from 50% carry
    more directional information).
    """
    import glob

    cpi_files = sorted(glob.glob(os.path.join(candle_dir, "KXCPI*_60.json")))

    daily_prices = {}

    for f in cpi_files:
        ticker = os.path.basename(f).replace("_60.json", "")
        with open(f) as fh:
            candles = json.load(fh)

        for c in candles:
            ts = c.get("end_period_ts")
            price_obj = c.get("price", {})
            close = price_obj.get("close_dollars")
            if ts and close is not None:
                try:
                    price = float(close)
                    day = pd.Timestamp.fromtimestamp(ts, tz=timezone.utc).normalize().tz_localize(None)
                    if day not in daily_prices:
                        daily_prices[day] = []
                    daily_prices[day].append(price)
                except (ValueError, TypeError):
                    pass

    if not daily_prices:
        raise ValueError("No CPI candle data found")

    # Daily average CPI market price
    daily_avg = pd.Series(
        {d: np.mean(prices) for d, prices in daily_prices.items()},
        name="kalshi_cpi_index",
    ).sort_index()

    daily_count = pd.Series(
        {d: len(prices) for d, prices in daily_prices.items()},
        name="n_cpi_markets",
    ).sort_index()

    return daily_avg, daily_count


def run_granger_both_directions(
    x: pd.Series, y: pd.Series, max_lag: int = 10,
) -> dict:
    """Run Granger causality in both directions with proper stationarity handling.

    Tests:
    1. x -> y (does x's past improve prediction of y?)
    2. y -> x (does y's past improve prediction of x?)

    Returns dict with both directions and lag selection.
    """
    from experiment2.validation import granger_causality_test
    from experiment1.granger_pipeline import _ensure_stationary

    # Ensure stationarity (difference if needed)
    x_stat = _ensure_stationary(x)
    y_stat = _ensure_stationary(y)

    if x_stat is None or y_stat is None:
        return {
            "error": "could_not_achieve_stationarity",
            "x_stationary": x_stat is not None,
            "y_stationary": y_stat is not None,
        }

    # Align
    combined = pd.concat([x_stat.rename("x"), y_stat.rename("y")], axis=1).dropna()
    if len(combined) < max_lag + 30:
        return {"error": "insufficient_overlap", "n_obs": len(combined)}

    # Test both directions
    xy = granger_causality_test(combined["x"], combined["y"], max_lag=max_lag)
    yx = granger_causality_test(combined["y"], combined["x"], max_lag=max_lag)

    return {
        "x_causes_y": {
            "best_lag": xy["best_lag"],
            "f_stat": float(xy["f_stat"]) if not np.isnan(xy["f_stat"]) else None,
            "p_value": float(xy["p_value"]) if not np.isnan(xy["p_value"]) else None,
            "significant": bool(xy.get("significant", xy["p_value"] < 0.05 if not np.isnan(xy["p_value"]) else False)),
        },
        "y_causes_x": {
            "best_lag": yx["best_lag"],
            "f_stat": float(yx["f_stat"]) if not np.isnan(yx["f_stat"]) else None,
            "p_value": float(yx["p_value"]) if not np.isnan(yx["p_value"]) else None,
            "significant": bool(yx.get("significant", yx["p_value"] < 0.05 if not np.isnan(yx["p_value"]) else False)),
        },
        "n_obs": len(combined),
    }


def compute_lead_lag_correlation(
    x: pd.Series, y: pd.Series, max_lag: int = 20,
) -> dict:
    """Compute cross-correlation at various lags to find optimal lead-lag.

    Positive lag means x leads y. Negative lag means y leads x.
    """
    combined = pd.concat([x.rename("x"), y.rename("y")], axis=1).dropna()
    if len(combined) < 30:
        return {"error": "insufficient_data"}

    x_vals = combined["x"].values
    y_vals = combined["y"].values

    # Standardize
    x_norm = (x_vals - x_vals.mean()) / x_vals.std()
    y_norm = (y_vals - y_vals.mean()) / y_vals.std()

    correlations = {}
    for lag in range(-max_lag, max_lag + 1):
        if lag > 0:
            r, p = stats.pearsonr(x_norm[:-lag], y_norm[lag:])
        elif lag < 0:
            r, p = stats.pearsonr(x_norm[-lag:], y_norm[:lag])
        else:
            r, p = stats.pearsonr(x_norm, y_norm)
        correlations[lag] = {"r": float(r), "p": float(p)}

    # Find peak correlation
    best_lag = max(correlations, key=lambda l: abs(correlations[l]["r"]))

    return {
        "correlations": correlations,
        "best_lag": best_lag,
        "best_r": correlations[best_lag]["r"],
        "best_p": correlations[best_lag]["p"],
        "n_obs": len(combined),
        "interpretation": (
            f"x leads y by {best_lag} days" if best_lag > 0
            else f"y leads x by {-best_lag} days" if best_lag < 0
            else "contemporaneous"
        ),
    }


def plot_tips_comparison(
    kalshi_cpi: pd.Series,
    tips_data: dict[str, pd.Series],
    lead_lag_results: dict,
    output_dir: str = "data/exp8/plots",
):
    """Plot Kalshi CPI index alongside TIPS breakeven rates."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    os.makedirs(output_dir, exist_ok=True)

    fig, axes = plt.subplots(2, 1, figsize=(14, 10))

    # Panel 1: Time series overlay
    ax1 = axes[0]
    ax1_twin = ax1.twinx()

    ax1.plot(kalshi_cpi.index, kalshi_cpi.values, "b-", alpha=0.8, label="Kalshi CPI Index")
    ax1.set_ylabel("Kalshi CPI Index (avg market price)", color="blue")

    for series_id, series in tips_data.items():
        ax1_twin.plot(series.index, series.values, "r-", alpha=0.6,
                     label=f"TIPS {series_id} (%)")
    ax1_twin.set_ylabel("TIPS Breakeven Rate (%)", color="red")

    ax1.set_title("Kalshi CPI Expectations vs TIPS Breakeven Inflation")
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax1_twin.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")

    # Panel 2: Cross-correlation
    ax2 = axes[1]
    for series_id, ll in lead_lag_results.items():
        if "correlations" not in ll:
            continue
        lags = sorted(ll["correlations"].keys(), key=int)
        rs = [ll["correlations"][l]["r"] for l in lags]
        ax2.plot([int(l) for l in lags], rs, "o-", markersize=3, label=series_id)
        ax2.axvline(int(ll["best_lag"]), linestyle="--", alpha=0.5)

    ax2.axhline(0, color="black", alpha=0.3)
    ax2.axvline(0, color="black", alpha=0.3)
    ax2.set_xlabel("Lag (days, positive = Kalshi leads)")
    ax2.set_ylabel("Pearson Correlation")
    ax2.set_title("Cross-Correlation: Kalshi CPI vs TIPS Breakeven")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "tips_comparison.png"), dpi=150)
    plt.close()
    print(f"  Saved {output_dir}/tips_comparison.png")
