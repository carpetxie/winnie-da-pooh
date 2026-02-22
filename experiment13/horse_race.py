"""
experiment13/horse_race.py

CPI Forecasting Horse Race: compare Kalshi implied distributions against
professional forecasters (SPF) and market-based measures (TIPS breakevens).

Benchmarks:
1. SPF (Survey of Professional Forecasters) - quarterly from Philadelphia Fed
2. TIPS breakeven rates - daily from FRED (T10YIE)
3. Historical FRED CPI distribution - already in exp12
"""

import os
import numpy as np
import pandas as pd
from typing import Optional
from scipy import stats

from experiment12.distributional_calibration import (
    compute_point_crps,
    _fetch_fred_csv,
    fetch_historical_cpi_from_fred,
)


# Realized MoM CPI values by event ticker, extracted from Kalshi settlements.
# Used for the random-walk benchmark (last month's realized → this month's forecast).
# Source: BLS CPI-U All Items, seasonally adjusted, month-over-month % change.
REALIZED_MOM_CPI = {
    "KXCPI-24NOV": 0.3,    # Nov 2024: realized 0.3%
    "KXCPI-24DEC": 0.4,    # Dec 2024: realized 0.4%
    "KXCPI-25JAN": 0.5,    # Jan 2025: realized 0.5%
    "KXCPI-25FEB": 0.2,    # Feb 2025: realized 0.2%
    "KXCPI-25MAR": -0.1,   # Mar 2025: realized -0.1%
    "KXCPI-25APR": 0.2,    # Apr 2025: realized 0.2%
    "KXCPI-25MAY": 0.1,    # May 2025: realized 0.1%
    "KXCPI-25JUN": 0.3,    # Jun 2025: realized 0.3%
    "KXCPI-25JUL": 0.2,    # Jul 2025: realized 0.2%
    "KXCPI-25AUG": 0.4,    # Aug 2025: realized 0.4%
    "KXCPI-25SEP": 0.3,    # Sep 2025: realized 0.3%
    "KXCPI-25OCT": 0.2,    # Oct 2025: realized 0.2%
    "KXCPI-25NOV": 0.2,    # Nov 2025: realized 0.2%
    "KXCPI-25DEC": 0.3,    # Dec 2025: realized 0.3%
}

# Ordered list for random walk: previous month's realized value
_TICKER_ORDER = [
    "KXCPI-24NOV", "KXCPI-24DEC", "KXCPI-25JAN", "KXCPI-25FEB",
    "KXCPI-25MAR", "KXCPI-25APR", "KXCPI-25MAY", "KXCPI-25JUN",
    "KXCPI-25JUL", "KXCPI-25AUG", "KXCPI-25SEP", "KXCPI-25OCT",
    "KXCPI-25NOV", "KXCPI-25DEC",
]


# CPI release dates and realized MoM % changes for our event window.
# These are matched from Kalshi event settlements (expiration_value field).
# Release dates from BLS calendar.
CPI_RELEASE_CALENDAR = {
    # event_ticker: (release_date, target_month_label)
    "KXCPI-24NOV": ("2024-12-11", "Nov 2024"),
    "KXCPI-24DEC": ("2025-01-15", "Dec 2024"),
    "KXCPI-25JAN": ("2025-02-12", "Jan 2025"),
    "KXCPI-25FEB": ("2025-03-12", "Feb 2025"),
    "KXCPI-25MAR": ("2025-04-10", "Mar 2025"),
    "KXCPI-25APR": ("2025-05-13", "Apr 2025"),
    "KXCPI-25MAY": ("2025-06-11", "May 2025"),
    "KXCPI-25JUN": ("2025-07-11", "Jun 2025"),
    "KXCPI-25JUL": ("2025-08-12", "Jul 2025"),
    "KXCPI-25AUG": ("2025-09-10", "Aug 2025"),
    "KXCPI-25SEP": ("2025-10-14", "Sep 2025"),
    "KXCPI-25OCT": ("2025-11-12", "Oct 2025"),
    "KXCPI-25NOV": ("2025-12-10", "Nov 2025"),
    "KXCPI-25DEC": ("2026-01-13", "Dec 2025"),
}

# SPF quarterly CPI forecasts (annual Q4/Q4 % change).
# Source: Philadelphia Fed SPF median responses.
# SPF forecasts annual CPI levels, not MoM. We convert using:
#   Annual forecast -> implied quarterly MoM ~ (annual_rate / 12)
# This is a rough approximation; SPF doesn't directly forecast MoM CPI.
# We note this limitation explicitly.
SPF_ANNUAL_CPI_FORECASTS = {
    # survey_quarter: annual CPI % change forecast (Q4/Q4)
    "2024Q4": 2.4,   # Q4 2024 SPF: 2.4% annual CPI
    "2025Q1": 2.5,   # Q1 2025 SPF: 2.5% annual CPI
    "2025Q2": 2.8,   # Q2 2025 SPF (tariff uncertainty)
    "2025Q3": 2.6,   # Q3 2025 SPF
    "2025Q4": 2.4,   # Q4 2025 SPF
}


def _event_to_quarter(event_ticker: str) -> str:
    """Map event ticker to the most recent SPF survey quarter.

    KXCPI-25MAR -> release Apr 2025 -> most recent SPF is 2025Q1.
    """
    cal = CPI_RELEASE_CALENDAR.get(event_ticker)
    if not cal:
        return ""
    release_date = pd.Timestamp(cal[0])
    year = release_date.year
    month = release_date.month

    # SPF releases: mid-Feb (Q1), mid-May (Q2), mid-Aug (Q3), mid-Nov (Q4)
    if month <= 2:
        return f"{year - 1}Q4"
    elif month <= 5:
        return f"{year}Q1"
    elif month <= 8:
        return f"{year}Q2"
    elif month <= 11:
        return f"{year}Q3"
    else:
        return f"{year}Q4"


def get_spf_mom_forecast(event_ticker: str) -> Optional[float]:
    """Get SPF-implied MoM CPI forecast for a given event.

    SPF forecasts annual CPI (Q4/Q4). We convert to monthly:
        MoM ≈ annual_rate / 12

    This is an approximation. SPF does not directly forecast MoM CPI.
    We document this limitation in the results.
    """
    quarter = _event_to_quarter(event_ticker)
    annual = SPF_ANNUAL_CPI_FORECASTS.get(quarter)
    if annual is None:
        return None
    return annual / 12.0


def fetch_tips_monthly_forecast(
    start_date: str = "2024-09-01",
    end_date: str = "2026-02-01",
) -> pd.Series:
    """Fetch TIPS 10Y breakeven and convert to monthly CPI forecast.

    Monthly CPI ≈ ((1 + T10YIE/100)^(1/12) - 1) * 100
    """
    tips = _fetch_fred_csv("T10YIE", start_date, end_date)
    if tips is None or len(tips) == 0:
        return pd.Series(dtype=float)
    # Convert annual breakeven to monthly
    monthly = ((1 + tips / 100) ** (1 / 12) - 1) * 100
    return monthly


def get_tips_forecast_for_event(
    tips_monthly: pd.Series,
    event_ticker: str,
    lookback_days: int = 5,
) -> Optional[float]:
    """Get TIPS-implied MoM CPI forecast: average of lookback_days before release."""
    cal = CPI_RELEASE_CALENDAR.get(event_ticker)
    if not cal or len(tips_monthly) == 0:
        return None

    release_date = pd.Timestamp(cal[0])
    # Average of lookback_days before release
    window_start = release_date - pd.Timedelta(days=lookback_days + 5)  # buffer for weekends
    window_end = release_date - pd.Timedelta(days=1)

    window = tips_monthly[
        (tips_monthly.index >= window_start) & (tips_monthly.index <= window_end)
    ]
    if len(window) == 0:
        return None
    return float(window.tail(lookback_days).mean())


def get_random_walk_forecast(event_ticker: str) -> Optional[float]:
    """Random walk benchmark: last month's realized CPI as this month's forecast.

    This is the standard naive benchmark in forecasting literature.
    """
    try:
        idx = _TICKER_ORDER.index(event_ticker)
    except ValueError:
        return None
    if idx == 0:
        # For the first event, use Nov 2024 CPI MoM (0.3%) from BLS data
        return 0.3
    prev_ticker = _TICKER_ORDER[idx - 1]
    return REALIZED_MOM_CPI.get(prev_ticker)


def get_trailing_mean_forecast(event_ticker: str, window: int = 12) -> Optional[float]:
    """Trailing mean benchmark: average of last `window` months' realized CPI.

    Uses FRED historical CPI data to compute the trailing mean.
    """
    try:
        idx = _TICKER_ORDER.index(event_ticker)
    except ValueError:
        return None

    # Collect all realized values before this event
    realized_before = []
    # Use Nov 2024 and earlier from REALIZED_MOM_CPI
    # For simplicity, use the available realized values in our window
    for i in range(max(0, idx - window), idx):
        val = REALIZED_MOM_CPI.get(_TICKER_ORDER[i])
        if val is not None:
            realized_before.append(val)

    # If we don't have enough from our window, we can't compute
    # For the earliest events, supplement with a hardcoded trailing mean
    # from BLS data: 2024 average MoM CPI was approximately 0.25%
    if len(realized_before) == 0:
        return 0.25  # 2024 average MoM CPI
    return float(np.mean(realized_before))


def run_cpi_horse_race(
    cpi_events: pd.DataFrame,
) -> dict:
    """Run the CPI forecasting horse race.

    For each CPI event, compare:
    1. Kalshi implied mean (point forecast) MAE
    2. SPF-implied MoM forecast MAE
    3. TIPS-implied MoM forecast MAE

    This is an apples-to-apples POINT forecast comparison.
    The distributional CRPS comparison is separate (Kalshi vs historical CDF).

    Args:
        cpi_events: DataFrame with columns: event_ticker, realized, implied_mean, kalshi_crps

    Returns:
        dict with per-event results and statistical tests
    """
    print("\n  Fetching TIPS breakeven data from FRED...")
    tips_monthly = fetch_tips_monthly_forecast()
    print(f"  TIPS data: {len(tips_monthly)} daily observations")

    results = []

    for _, event in cpi_events.iterrows():
        event_ticker = event["event_ticker"]
        realized = event["realized"]
        kalshi_mean = event.get("implied_mean")

        row = {
            "event_ticker": event_ticker,
            "realized": realized,
            "kalshi_implied_mean": kalshi_mean,
            "kalshi_point_mae": abs(kalshi_mean - realized) if kalshi_mean is not None else None,
            "kalshi_crps": event.get("kalshi_crps"),
        }

        # SPF forecast
        spf_forecast = get_spf_mom_forecast(event_ticker)
        if spf_forecast is not None:
            row["spf_forecast"] = spf_forecast
            row["spf_mae"] = abs(spf_forecast - realized)

        # TIPS forecast
        tips_forecast = get_tips_forecast_for_event(tips_monthly, event_ticker)
        if tips_forecast is not None:
            row["tips_forecast"] = tips_forecast
            row["tips_mae"] = abs(tips_forecast - realized)

        # Naive benchmarks
        rw_forecast = get_random_walk_forecast(event_ticker)
        if rw_forecast is not None:
            row["random_walk_forecast"] = rw_forecast
            row["random_walk_mae"] = abs(rw_forecast - realized)

        trail_forecast = get_trailing_mean_forecast(event_ticker)
        if trail_forecast is not None:
            row["trailing_mean_forecast"] = trail_forecast
            row["trailing_mean_mae"] = abs(trail_forecast - realized)

        results.append(row)

    results_df = pd.DataFrame(results)

    # --- Statistical tests: point forecast comparisons ---
    test_results = {}

    def _paired_effect_size(a, b):
        """Compute Cohen's d for paired samples."""
        diff = a - b
        d_mean = diff.mean()
        d_std = diff.std(ddof=1)
        if d_std == 0:
            return float("inf") if d_mean != 0 else 0.0
        return float(d_mean / d_std)

    # Kalshi implied mean MAE vs SPF MAE (apples-to-apples point forecasts)
    valid = results_df.dropna(subset=["kalshi_point_mae", "spf_mae"])
    if len(valid) >= 5:
        stat, p = stats.wilcoxon(
            valid["kalshi_point_mae"], valid["spf_mae"],
            alternative="less",
        )
        test_results["kalshi_point_vs_spf"] = {
            "n": len(valid),
            "kalshi_mean_mae": float(valid["kalshi_point_mae"].mean()),
            "spf_mean_mae": float(valid["spf_mae"].mean()),
            "cohen_d": _paired_effect_size(valid["kalshi_point_mae"].values, valid["spf_mae"].values),
            "wilcoxon_p": float(p),
            "significant": p < 0.05,
            "note": "Apples-to-apples: Kalshi implied mean MAE vs SPF annual-to-monthly MAE",
        }

    # Kalshi implied mean MAE vs TIPS MAE
    valid = results_df.dropna(subset=["kalshi_point_mae", "tips_mae"])
    if len(valid) >= 5:
        stat, p = stats.wilcoxon(
            valid["kalshi_point_mae"], valid["tips_mae"],
            alternative="less",
        )
        test_results["kalshi_point_vs_tips"] = {
            "n": len(valid),
            "kalshi_mean_mae": float(valid["kalshi_point_mae"].mean()),
            "tips_mean_mae": float(valid["tips_mae"].mean()),
            "cohen_d": _paired_effect_size(valid["kalshi_point_mae"].values, valid["tips_mae"].values),
            "wilcoxon_p": float(p),
            "significant": p < 0.05,
            "note": "Apples-to-apples: Kalshi implied mean MAE vs TIPS monthly-implied MAE",
        }

    # SPF vs TIPS (for context)
    valid = results_df.dropna(subset=["spf_mae", "tips_mae"])
    if len(valid) >= 5:
        stat, p = stats.wilcoxon(
            valid["spf_mae"], valid["tips_mae"],
            alternative="two-sided",
        )
        test_results["spf_vs_tips"] = {
            "n": len(valid),
            "spf_mean_mae": float(valid["spf_mae"].mean()),
            "tips_mean_mae": float(valid["tips_mae"].mean()),
            "wilcoxon_p": float(p),
            "significant": p < 0.05,
        }

    # Kalshi vs naive benchmarks
    for naive_col, naive_label in [
        ("random_walk_mae", "random_walk"),
        ("trailing_mean_mae", "trailing_mean"),
    ]:
        valid = results_df.dropna(subset=["kalshi_point_mae", naive_col])
        if len(valid) >= 5:
            stat, p = stats.wilcoxon(
                valid["kalshi_point_mae"], valid[naive_col],
                alternative="less",
            )
            test_results[f"kalshi_vs_{naive_label}"] = {
                "n": len(valid),
                "kalshi_mean_mae": float(valid["kalshi_point_mae"].mean()),
                f"{naive_label}_mean_mae": float(valid[naive_col].mean()),
                "cohen_d": _paired_effect_size(valid["kalshi_point_mae"].values, valid[naive_col].values),
                "wilcoxon_p": float(p),
                "significant": p < 0.05,
                "note": f"Kalshi implied mean vs {naive_label.replace('_', ' ')} forecast",
            }

    # --- Bonferroni correction across horse race benchmarks ---
    benchmark_tests = [
        "kalshi_point_vs_spf", "kalshi_point_vs_tips",
        "kalshi_vs_random_walk", "kalshi_vs_trailing_mean",
    ]
    raw_pvals = {k: test_results[k]["wilcoxon_p"] for k in benchmark_tests if k in test_results and "wilcoxon_p" in test_results[k]}
    n_benchmarks = len(raw_pvals)
    if n_benchmarks > 0:
        for k, raw_p in raw_pvals.items():
            adj_p = min(raw_p * n_benchmarks, 1.0)
            test_results[k]["wilcoxon_p_bonferroni"] = float(adj_p)
            test_results[k]["n_benchmarks_corrected"] = n_benchmarks
            test_results[k]["significant_bonferroni"] = adj_p < 0.05

    return {
        "per_event": results_df.to_dict("records"),
        "n_events": len(results_df),
        "statistical_tests": test_results,
        "methodology_notes": {
            "spf_conversion": (
                "SPF forecasts annual CPI (Q4/Q4 %). Converted to MoM via "
                "annual_rate / 12. This is an approximation; SPF does not "
                "directly forecast monthly CPI changes."
            ),
            "tips_conversion": (
                "TIPS 10Y breakeven converted to monthly via "
                "((1 + annual/100)^(1/12) - 1) * 100. Uses 5-day average "
                "before CPI release. Includes risk premium and term structure effects."
            ),
            "crps_vs_mae": (
                "For a well-calibrated distribution, CRPS is typically lower than MAE "
                "(the sharpness reward means a good distribution outperforms a point mass). "
                "However, CRPS > MAE is possible and indicates distributional miscalibration. "
                "Comparing Kalshi CRPS to point forecast MAE conflates distributional "
                "advantage with forecasting accuracy. This horse race compares "
                "point-vs-point (MAE vs MAE) for an honest comparison."
            ),
            "naive_benchmarks": (
                "Random walk: last month's realized MoM CPI as this month's forecast. "
                "Trailing mean: average of available prior months' realized CPI. "
                "These are standard naive benchmarks in the forecasting literature."
            ),
            "sample_size": (
                f"n={len(results_df)} CPI events. Low statistical power; "
                "effect sizes are more informative than p-values."
            ),
        },
    }
