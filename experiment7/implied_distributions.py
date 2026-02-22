"""
experiment7/implied_distributions.py

Reconstruct implied probability distributions from Kalshi's multi-strike
market structure (CPI, GDP, Jobless Claims).

Each event (e.g., KXCPI-25DEC) has markets at multiple thresholds.
The price of "CPI > X%" is the market-implied P(CPI > X), giving
points on the CDF. First-differencing across strikes yields the PDF.

Also tests no-arbitrage monotonicity constraints: P(X > a) >= P(X > b)
whenever a < b.

No API calls required. Uses cached data from experiment2.
"""

import os
import json
import glob
import re
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from collections import defaultdict
from tqdm import tqdm

CANDLE_DIR = "data/exp2/raw/candles"
TARGETED_MARKETS_PATH = "data/exp2/raw/targeted_markets.json"
DATA_DIR = "data/exp7"

# Series that have multiple strike levels
STRIKE_SERIES = {"KXCPI", "KXGDP", "KXJOBLESSCLAIMS"}


def load_targeted_markets() -> pd.DataFrame:
    """Load full market metadata including floor_strike and expiration_value."""
    with open(TARGETED_MARKETS_PATH) as f:
        markets = json.load(f)
    df = pd.DataFrame(markets)
    return df


def extract_strike_markets(markets_df: pd.DataFrame) -> pd.DataFrame:
    """Filter to multi-strike markets and parse strike levels.

    Returns DataFrame with columns:
        ticker, event_ticker, series_prefix, floor_strike, strike_type,
        result, title, expiration_value
    """
    # Extract series prefix
    markets_df = markets_df.copy()
    markets_df["series_prefix"] = markets_df["ticker"].str.extract(r"^([A-Z]+)")

    # Filter to strike series
    strike_df = markets_df[markets_df["series_prefix"].isin(STRIKE_SERIES)].copy()

    # Parse floor_strike
    strike_df["floor_strike"] = pd.to_numeric(strike_df["floor_strike"], errors="coerce")

    # Build event_ticker if not present
    if "event_ticker" not in strike_df.columns:
        strike_df["event_ticker"] = strike_df["ticker"].str.extract(r"^([A-Z]+-\w+)")

    # Filter to markets with valid floor_strike
    strike_df = strike_df.dropna(subset=["floor_strike"]).copy()

    return strike_df[["ticker", "event_ticker", "series_prefix", "floor_strike",
                       "strike_type", "result", "title", "expiration_value",
                       "volume", "open_time", "close_time", "settlement_ts"]].copy()


def group_by_event(strike_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Group strike markets by event_ticker.

    Returns {event_ticker: DataFrame sorted by floor_strike}.
    Only includes events with >= 2 distinct strikes.
    """
    events = {}
    for event_ticker, group in strike_df.groupby("event_ticker"):
        # Need at least 2 distinct strikes to form a distribution
        if group["floor_strike"].nunique() >= 2:
            events[event_ticker] = group.sort_values("floor_strike").reset_index(drop=True)
    return events


def load_candle_prices(ticker: str) -> pd.Series | None:
    """Load hourly close prices for a ticker from cached candles."""
    candle_path = os.path.join(CANDLE_DIR, f"{ticker}_60.json")
    if not os.path.exists(candle_path):
        return None

    with open(candle_path) as f:
        candles = json.load(f)

    prices = {}
    for c in candles:
        ts = c.get("end_period_ts")
        price_obj = c.get("price", {})
        close = price_obj.get("close_dollars")
        if ts and close is not None:
            try:
                prices[pd.Timestamp.fromtimestamp(ts, tz=timezone.utc)] = float(close)
            except (ValueError, TypeError):
                pass

    if not prices:
        return None

    return pd.Series(prices, name=ticker).sort_index()


def build_implied_cdf_snapshots(
    event_markets: pd.DataFrame,
) -> list[dict]:
    """Build implied CDF snapshots at each available hour for an event.

    For each hour where price data exists for all strikes,
    construct the CDF: strike -> P(X > strike) = market price.

    Returns list of {timestamp, strikes, cdf_values, is_monotonic, violations}.
    """
    tickers = event_markets["ticker"].tolist()
    strikes = event_markets["floor_strike"].tolist()
    strike_type = event_markets["strike_type"].iloc[0]

    # Load prices for all tickers
    price_series = {}
    for ticker in tickers:
        ps = load_candle_prices(ticker)
        if ps is not None:
            price_series[ticker] = ps

    if len(price_series) < 2:
        return []

    # Find common timestamps
    all_timestamps = set()
    for ps in price_series.values():
        all_timestamps.update(ps.index)

    snapshots = []
    for ts in sorted(all_timestamps):
        cdf_points = []
        for ticker, strike in zip(tickers, strikes):
            if ticker in price_series and ts in price_series[ticker].index:
                price = price_series[ticker].loc[ts]
                cdf_points.append((strike, price))

        if len(cdf_points) < 2:
            continue

        cdf_points.sort(key=lambda x: x[0])
        cdf_strikes = [p[0] for p in cdf_points]
        cdf_values = [p[1] for p in cdf_points]

        # For "greater" type: P(X > strike) should DECREASE as strike increases
        # For "greater_or_equal": same logic
        is_monotonic = True
        violations = []
        for i in range(len(cdf_values) - 1):
            if cdf_values[i] < cdf_values[i + 1]:
                is_monotonic = False
                violations.append({
                    "lower_strike": cdf_strikes[i],
                    "upper_strike": cdf_strikes[i + 1],
                    "lower_price": cdf_values[i],
                    "upper_price": cdf_values[i + 1],
                    "violation_size": cdf_values[i + 1] - cdf_values[i],
                })

        snapshots.append({
            "timestamp": ts,
            "strikes": cdf_strikes,
            "cdf_values": cdf_values,
            "is_monotonic": is_monotonic,
            "n_violations": len(violations),
            "violations": violations,
            "n_strikes": len(cdf_points),
        })

    return snapshots


def compute_implied_pdf(cdf_strikes: list[float], cdf_values: list[float]) -> dict:
    """Convert CDF to PDF via first-differencing.

    For strikes [s1, s2, s3] with CDF values [p1, p2, p3]:
    PDF bin [s1, s2] has probability p1 - p2 (for "greater" type).

    Returns dict with bin_edges, pdf_values, implied_mean, implied_std.
    """
    if len(cdf_strikes) < 2:
        return {}

    bin_edges = cdf_strikes
    pdf_values = []
    for i in range(len(cdf_values) - 1):
        prob = cdf_values[i] - cdf_values[i + 1]
        pdf_values.append(max(0, prob))  # Clip negative (violation) to 0

    # Tail probabilities
    prob_below_min = 1.0 - cdf_values[0]  # P(X <= min_strike)
    prob_above_max = cdf_values[-1]  # P(X > max_strike)

    # Implied mean (midpoint-weighted)
    total_interior = sum(pdf_values)
    if total_interior > 0:
        weighted_sum = 0
        for i, p in enumerate(pdf_values):
            midpoint = (bin_edges[i] + bin_edges[i + 1]) / 2
            weighted_sum += midpoint * p
        implied_mean = weighted_sum / total_interior
    else:
        implied_mean = (bin_edges[0] + bin_edges[-1]) / 2

    # Tail-aware implied mean: E[X] computed from the full piecewise-linear CDF
    # used in CRPS, which assigns tail mass to boundary strikes.
    # Formula: E[X] = strikes[0] + integral of [1 - F(x)] dx from strikes[0] to strikes[-1]
    # where F(x) is the standard CDF (1 - survival), linearly interpolated between strikes.
    tail_aware_mean = compute_tail_aware_mean(cdf_strikes, cdf_values)

    return {
        "bin_edges": bin_edges,
        "pdf_values": pdf_values,
        "prob_below_min_strike": prob_below_min,
        "prob_above_max_strike": prob_above_max,
        "implied_mean": implied_mean,
        "implied_mean_tail_aware": tail_aware_mean,
        "total_interior_probability": total_interior,
    }


def compute_tail_aware_mean(
    cdf_strikes: list[float],
    cdf_values: list[float],
) -> float:
    """Compute E[X] from the same piecewise-linear CDF used in CRPS computation.

    Unlike the interior-only implied mean (which renormalizes over interior
    probability mass), this integrates over the full CDF including implicit
    tail mass at boundary strikes.

    Uses the identity: E[X] = strikes[0] + integral of S(x) dx from strikes[0]
    to strikes[-1], where S(x) = 1 - F(x) is the survival function. This is
    exact for the piecewise-linear CDF that assumes F(x)=0 for x < strikes[0]
    and F(x)=1 for x > strikes[-1].

    Parameters
    ----------
    cdf_strikes : list[float]
        Sorted strike thresholds (ascending).
    cdf_values : list[float]
        Survival function values P(X > strike) at each strike.

    Returns
    -------
    float
        Tail-aware implied mean E[X].
    """
    if len(cdf_strikes) < 2:
        return (cdf_strikes[0] if cdf_strikes else 0.0)

    strikes = np.array(cdf_strikes, dtype=float)
    # Survival values S(x) = P(X > x) = cdf_values (in Kalshi convention)
    survival = np.array(cdf_values, dtype=float)
    survival = np.clip(survival, 0.0, 1.0)

    # E[X] = strikes[0] + integral of S(x) dx from strikes[0] to strikes[-1]
    # S(x) is piecewise linear between strikes, so use trapezoidal integration
    integral = 0.0
    for i in range(len(strikes) - 1):
        width = strikes[i + 1] - strikes[i]
        # Trapezoidal rule: average of S at endpoints × width
        integral += width * (survival[i] + survival[i + 1]) / 2.0

    return float(strikes[0] + integral)


def analyze_no_arbitrage(
    event_groups: dict[str, pd.DataFrame],
) -> dict:
    """Test no-arbitrage monotonicity constraints across all events.

    Returns aggregate statistics on violation frequency, size, and persistence.
    """
    all_violations = []
    total_snapshots = 0
    violating_snapshots = 0
    events_analyzed = 0

    per_event_results = {}

    for event_ticker, event_markets in tqdm(event_groups.items(), desc="No-arbitrage tests"):
        snapshots = build_implied_cdf_snapshots(event_markets)
        if not snapshots:
            continue

        events_analyzed += 1
        n_snap = len(snapshots)
        n_violating = sum(1 for s in snapshots if not s["is_monotonic"])
        total_snapshots += n_snap
        violating_snapshots += n_violating

        violation_sizes = []
        for s in snapshots:
            for v in s["violations"]:
                violation_sizes.append(v["violation_size"])
                all_violations.append({
                    "event_ticker": event_ticker,
                    "timestamp": s["timestamp"],
                    **v,
                })

        per_event_results[event_ticker] = {
            "n_snapshots": n_snap,
            "n_violating": n_violating,
            "violation_rate": n_violating / n_snap if n_snap > 0 else 0,
            "n_strikes": event_markets["floor_strike"].nunique(),
            "series": event_markets["series_prefix"].iloc[0],
            "mean_violation_size": float(np.mean(violation_sizes)) if violation_sizes else 0,
            "max_violation_size": float(np.max(violation_sizes)) if violation_sizes else 0,
        }

    # Do violations mean-revert?
    reversion_results = _test_violation_reversion(all_violations)

    return {
        "events_analyzed": events_analyzed,
        "total_snapshots": total_snapshots,
        "violating_snapshots": violating_snapshots,
        "overall_violation_rate": violating_snapshots / total_snapshots if total_snapshots > 0 else 0,
        "mean_violation_size": float(np.mean([v["violation_size"] for v in all_violations])) if all_violations else 0,
        "total_violations": len(all_violations),
        "per_event": per_event_results,
        "reversion": reversion_results,
    }


def _test_violation_reversion(violations: list[dict]) -> dict:
    """Test whether no-arbitrage violations revert within subsequent hours.

    Group violations by event, check if the violation disappears in the next snapshot.
    """
    if not violations:
        return {"n_violations": 0}

    # Group by event
    by_event = defaultdict(list)
    for v in violations:
        by_event[v["event_ticker"]].append(v)

    reverted = 0
    persisted = 0
    total_checked = 0

    for event, event_violations in by_event.items():
        # Sort by timestamp
        event_violations.sort(key=lambda x: x["timestamp"])

        for i, v in enumerate(event_violations[:-1]):
            next_v = event_violations[i + 1]
            # Check if same strike pair still violating in next snapshot
            if (v["lower_strike"] == next_v["lower_strike"] and
                v["upper_strike"] == next_v["upper_strike"]):
                persisted += 1
            else:
                reverted += 1
            total_checked += 1

    return {
        "n_violations_checked": total_checked,
        "n_reverted": reverted,
        "n_persisted": persisted,
        "reversion_rate": reverted / total_checked if total_checked > 0 else None,
    }


def build_distribution_snapshots(
    event_groups: dict[str, pd.DataFrame],
) -> dict:
    """Build implied PDFs at mid-life for each event and compare to realized outcome.

    Returns per-event distribution accuracy metrics.
    """
    results = {}

    for event_ticker, event_markets in tqdm(event_groups.items(), desc="Building PDFs"):
        snapshots = build_implied_cdf_snapshots(event_markets)
        if not snapshots:
            continue

        # Use mid-life snapshot
        mid_idx = len(snapshots) // 2
        mid_snap = snapshots[mid_idx]

        pdf = compute_implied_pdf(mid_snap["strikes"], mid_snap["cdf_values"])
        if not pdf:
            continue

        # Get realized outcome from expiration_value
        exp_val = event_markets["expiration_value"].iloc[0]
        realized = _parse_expiration_value(exp_val, event_markets["series_prefix"].iloc[0])

        results[event_ticker] = {
            "pdf": pdf,
            "n_strikes": mid_snap["n_strikes"],
            "realized_value": realized,
            "implied_mean": pdf.get("implied_mean"),
            "series": event_markets["series_prefix"].iloc[0],
            "forecast_error": abs(pdf["implied_mean"] - realized) if realized is not None and pdf.get("implied_mean") is not None else None,
        }

    return results


def _parse_expiration_value(val: str, series: str) -> float | None:
    """Parse the expiration_value string into a numeric value."""
    if not val or pd.isna(val):
        return None

    # Remove %, commas, and whitespace
    cleaned = val.replace("%", "").replace(",", "").strip()

    # Handle strings like "Above 3.50%" or "At least 200000"
    cleaned = re.sub(r"^(Above|Below|At least|At most)\s*", "", cleaned, flags=re.IGNORECASE)

    try:
        return float(cleaned)
    except ValueError:
        return None


def plot_implied_distributions(
    distribution_results: dict,
    output_dir: str = "data/exp7/plots",
):
    """Plot implied PDFs for key events."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    os.makedirs(output_dir, exist_ok=True)

    # Plot up to 6 CPI events
    cpi_events = {k: v for k, v in distribution_results.items() if "KXCPI" in k}
    if not cpi_events:
        return

    n_plots = min(6, len(cpi_events))
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    axes = axes.flatten()

    for idx, (event_ticker, data) in enumerate(sorted(cpi_events.items())[:n_plots]):
        ax = axes[idx]
        pdf = data["pdf"]
        edges = pdf["bin_edges"]
        values = pdf["pdf_values"]

        # Plot as bar chart
        mids = [(edges[i] + edges[i + 1]) / 2 for i in range(len(values))]
        widths = [edges[i + 1] - edges[i] for i in range(len(values))]
        ax.bar(mids, values, width=widths, alpha=0.7, color="steelblue", edgecolor="navy")

        # Add tail probabilities
        if pdf["prob_below_min_strike"] > 0.01:
            ax.annotate(f"P(<{edges[0]})={pdf['prob_below_min_strike']:.0%}",
                       xy=(edges[0], 0), fontsize=8, color="red")
        if pdf["prob_above_max_strike"] > 0.01:
            ax.annotate(f"P(>{edges[-1]})={pdf['prob_above_max_strike']:.0%}",
                       xy=(edges[-1], 0), fontsize=8, color="red")

        # Mark realized value
        if data.get("realized_value") is not None:
            ax.axvline(data["realized_value"], color="red", linestyle="--",
                      label=f"Realized: {data['realized_value']}")

        # Mark implied mean
        if pdf.get("implied_mean") is not None:
            ax.axvline(pdf["implied_mean"], color="green", linestyle=":",
                      label=f"Implied mean: {pdf['implied_mean']:.2f}")

        ax.set_title(event_ticker, fontsize=10)
        ax.set_xlabel("Value")
        ax.set_ylabel("Implied Probability")
        ax.legend(fontsize=7)

    # Hide unused axes
    for idx in range(n_plots, len(axes)):
        axes[idx].set_visible(False)

    plt.suptitle("Kalshi Implied Probability Distributions (CPI)", fontsize=14)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "implied_pdfs_cpi.png"), dpi=150)
    plt.close()
    print(f"  Saved {output_dir}/implied_pdfs_cpi.png")

    # Summary: forecast error distribution
    errors = [v["forecast_error"] for v in distribution_results.values()
              if v.get("forecast_error") is not None]
    if errors:
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.hist(errors, bins=15, alpha=0.7, color="steelblue", edgecolor="navy")
        ax.axvline(np.mean(errors), color="red", linestyle="--",
                  label=f"Mean error: {np.mean(errors):.3f}")
        ax.set_xlabel("Absolute Forecast Error (implied mean vs realized)")
        ax.set_ylabel("Count")
        ax.set_title("Implied Distribution Forecast Accuracy")
        ax.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "forecast_errors.png"), dpi=150)
        plt.close()
        print(f"  Saved {output_dir}/forecast_errors.png")
