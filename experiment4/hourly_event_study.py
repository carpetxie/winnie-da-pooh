"""
experiment4/hourly_event_study.py

Hourly-resolution event study: measures how quickly Kalshi markets absorb
economic information compared to EPU/VIX at daily resolution.

Uses cached hourly candle data (725 files in data/exp2/raw/candles/).
"""

import os
import json
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from scipy import stats as scipy_stats


def load_hourly_prices_from_candles(
    candle_dir: str = "data/exp2/raw/candles",
    markets_path: str = "data/exp2/markets.csv",
) -> dict[str, pd.Series]:
    """Load all cached hourly candle files into {ticker: pd.Series} format.

    Returns dict mapping ticker -> hourly price Series with DatetimeIndex.
    Only includes tickers that have a valid domain assignment.
    """
    from experiment2.data_collection import extract_candle_price

    df = pd.read_csv(markets_path)
    valid_tickers = set(df["ticker"].tolist())

    hourly_prices = {}
    files = [f for f in os.listdir(candle_dir) if f.endswith("_60.json")]

    for fname in files:
        ticker = fname.replace("_60.json", "")
        if ticker not in valid_tickers:
            continue

        path = os.path.join(candle_dir, fname)
        with open(path) as f:
            candles = json.load(f)

        timestamps = []
        prices = []
        for c in candles:
            ts = c.get("end_period_ts", 0)
            price = extract_candle_price(c)
            if not np.isnan(price) and ts > 0:
                timestamps.append(datetime.fromtimestamp(ts, tz=timezone.utc))
                prices.append(price)

        if len(timestamps) >= 3:
            series = pd.Series(prices, index=pd.DatetimeIndex(timestamps), name=ticker)
            series = series.sort_index()
            # Remove duplicates
            series = series[~series.index.duplicated(keep="last")]
            hourly_prices[ticker] = series

    return hourly_prices


def compute_hourly_kui_domain(
    hourly_prices: dict[str, pd.Series],
    markets_df: pd.DataFrame,
) -> dict[str, pd.Series]:
    """Compute hourly belief volatility per domain.

    For each domain, computes the mean absolute percentage change
    across active markets at each hour.

    Returns dict mapping domain -> hourly BV Series.
    """
    ticker_to_domain = dict(zip(markets_df["ticker"], markets_df["domain"]))

    # Group tickers by domain
    domain_tickers: dict[str, list[str]] = {}
    for ticker, series in hourly_prices.items():
        domain = ticker_to_domain.get(ticker)
        if domain and domain not in ("excluded", "crypto", "politics"):
            domain_tickers.setdefault(domain, []).append(ticker)

    domain_bv = {}
    for domain, tickers in domain_tickers.items():
        if len(tickers) < 2:
            continue

        # Build hourly price matrix for this domain
        price_data = {}
        for t in tickers:
            price_data[t] = hourly_prices[t]

        prices_df = pd.DataFrame(price_data)

        # Compute percentage returns
        clipped = prices_df.clip(lower=0.02, upper=0.98)
        returns = (prices_df.diff() / clipped.shift(1)).abs()

        # Mean absolute pct change across active markets
        n_active = returns.notna().sum(axis=1)
        bv = returns.mean(axis=1)
        bv[n_active < 2] = np.nan

        # Drop NaN
        bv = bv.dropna()
        if len(bv) > 0:
            domain_bv[domain] = bv

    return domain_bv


def compute_hourly_event_windows(
    hourly_bv: dict[str, pd.Series],
    events: pd.DataFrame,
    window_hours: int = 72,
) -> list[dict]:
    """For each event, extract [-window_hours, +window_hours] windows.

    Returns list of dicts with event metadata and hourly window data.
    """
    results = []

    for _, event in events.iterrows():
        event_date = pd.Timestamp(event["date"], tz="UTC")
        domain = event["relevant_domain"]

        bv_series = hourly_bv.get(domain)
        if bv_series is None or bv_series.empty:
            continue

        # Ensure timezone-aware
        if bv_series.index.tz is None:
            bv_series = bv_series.tz_localize("UTC")

        start = event_date - pd.Timedelta(hours=window_hours)
        end = event_date + pd.Timedelta(hours=window_hours)

        window = bv_series[(bv_series.index >= start) & (bv_series.index <= end)]

        if len(window) < 6:  # Need minimum data
            continue

        # Convert to hour offsets
        hour_offsets = (window.index - event_date).total_seconds() / 3600
        window_offset = pd.Series(window.values, index=hour_offsets)

        results.append({
            "event_date": event["date"],
            "event_type": event["type"],
            "description": event["description"],
            "surprise": event["surprise"],
            "domain": domain,
            "window": window_offset,
            "n_hours": len(window),
        })

    return results


def detect_first_significant_move_hourly(
    window: pd.Series,
    pre_event_hours: int = 24,
    threshold_std: float = 2.0,
) -> float | None:
    """Detect first significant move in hourly window.

    Args:
        window: Series indexed by hour offsets (negative = before event)
        pre_event_hours: Hours before event to use as baseline
        threshold_std: Number of stds for significance

    Returns:
        Hour offset of first significant move, or None.
    """
    # Pre-event baseline
    pre_event = window[(window.index >= -pre_event_hours) & (window.index < 0)]

    if len(pre_event) < 3:
        return None

    baseline_mean = pre_event.mean()
    baseline_std = pre_event.std()

    if baseline_std == 0 or np.isnan(baseline_std):
        return None

    upper = baseline_mean + threshold_std * baseline_std

    # Look for first breach starting from hour 0
    post_event = window[window.index >= 0].sort_index()

    for hour_offset, value in post_event.items():
        if value > upper:
            return float(hour_offset)

    return None


def run_hourly_event_study(
    hourly_bv: dict[str, pd.Series],
    epu_daily: pd.Series,
    vix_daily: pd.Series,
    events: pd.DataFrame,
) -> pd.DataFrame:
    """Main hourly event study.

    For each event:
    1. Detect hourly Kalshi reaction time
    2. Detect daily EPU/VIX reaction time (converted to hours)
    3. Compute lead-lag in hours
    """
    from experiment2.event_study import extract_event_window, detect_first_significant_move

    windows = compute_hourly_event_windows(hourly_bv, events, window_hours=72)

    results = []
    for w in windows:
        # Hourly Kalshi reaction
        kalshi_hour = detect_first_significant_move_hourly(w["window"])

        # Daily EPU reaction (in days, converted to hours)
        event_ts = pd.Timestamp(w["event_date"])
        epu_window = extract_event_window(epu_daily, event_ts, window_days=7)
        epu_day = detect_first_significant_move(epu_window, threshold_std=1.5)
        epu_hours = epu_day * 24 if epu_day is not None else None

        # Daily VIX reaction
        vix_window = extract_event_window(vix_daily, event_ts, window_days=7)
        vix_day = detect_first_significant_move(vix_window, threshold_std=1.5)
        vix_hours = vix_day * 24 if vix_day is not None else None

        # Lead-lag (negative = Kalshi leads)
        ll_epu = None
        if kalshi_hour is not None and epu_hours is not None:
            ll_epu = kalshi_hour - epu_hours

        ll_vix = None
        if kalshi_hour is not None and vix_hours is not None:
            ll_vix = kalshi_hour - vix_hours

        # Window stats
        pre_event = w["window"][(w["window"].index >= -24) & (w["window"].index < 0)]
        post_event = w["window"][(w["window"].index >= 0) & (w["window"].index <= 24)]
        pre_mean = pre_event.mean() if len(pre_event) > 0 else np.nan
        post_mean = post_event.mean() if len(post_event) > 0 else np.nan
        spike_ratio = post_mean / pre_mean if pre_mean > 0 else np.nan

        results.append({
            "event_date": w["event_date"],
            "event_type": w["event_type"],
            "description": w["description"],
            "surprise": w["surprise"],
            "domain": w["domain"],
            "n_hours_in_window": w["n_hours"],
            "kalshi_reaction_hours": kalshi_hour,
            "epu_reaction_hours": epu_hours,
            "vix_reaction_hours": vix_hours,
            "lead_lag_vs_epu_hours": ll_epu,
            "lead_lag_vs_vix_hours": ll_vix,
            "pre_event_bv_mean": round(pre_mean, 6) if not np.isnan(pre_mean) else None,
            "post_event_bv_mean": round(post_mean, 6) if not np.isnan(post_mean) else None,
            "spike_ratio": round(spike_ratio, 2) if not np.isnan(spike_ratio) else None,
        })

    return pd.DataFrame(results)


def test_information_speed_significance(results: pd.DataFrame) -> dict:
    """Statistical tests for the information speed hypothesis.

    Tests whether Kalshi consistently reacts before EPU/VIX.
    """
    output = {}

    # Filter to events with both Kalshi and EPU reaction times
    ll_epu = results["lead_lag_vs_epu_hours"].dropna()
    ll_vix = results["lead_lag_vs_vix_hours"].dropna()

    # Sign test vs EPU: does Kalshi lead more than 50% of the time?
    if len(ll_epu) >= 3:
        n_leads = (ll_epu < 0).sum()
        n_total = len(ll_epu)
        # Binomial test: P(X >= n_leads) under H0: p=0.5
        sign_p = scipy_stats.binom_test(n_leads, n_total, 0.5) if hasattr(scipy_stats, 'binom_test') else scipy_stats.binomtest(n_leads, n_total, 0.5).pvalue
        output["epu_sign_test"] = {
            "n_kalshi_leads": int(n_leads),
            "n_total": int(n_total),
            "pct_kalshi_leads": round(n_leads / n_total, 3),
            "p_value": round(float(sign_p), 4),
            "significant": float(sign_p) < 0.05,
        }

        # Wilcoxon signed-rank test
        if len(ll_epu) >= 5:
            try:
                w_stat, w_p = scipy_stats.wilcoxon(ll_epu, alternative="less")
                output["epu_wilcoxon"] = {
                    "w_statistic": float(w_stat),
                    "p_value": round(float(w_p), 4),
                    "significant": float(w_p) < 0.05,
                    "median_lead_lag_hours": round(float(ll_epu.median()), 1),
                    "mean_lead_lag_hours": round(float(ll_epu.mean()), 1),
                }
            except ValueError:
                output["epu_wilcoxon"] = {"error": "insufficient_variation"}

    # Same for VIX
    if len(ll_vix) >= 3:
        n_leads = (ll_vix < 0).sum()
        n_total = len(ll_vix)
        sign_p = scipy_stats.binomtest(n_leads, n_total, 0.5).pvalue
        output["vix_sign_test"] = {
            "n_kalshi_leads": int(n_leads),
            "n_total": int(n_total),
            "pct_kalshi_leads": round(n_leads / n_total, 3),
            "p_value": round(float(sign_p), 4),
            "significant": float(sign_p) < 0.05,
        }

    # By event type
    output["by_event_type"] = {}
    for event_type in results["event_type"].unique():
        type_ll = results.loc[results["event_type"] == event_type, "lead_lag_vs_epu_hours"].dropna()
        if len(type_ll) > 0:
            output["by_event_type"][event_type] = {
                "n": int(len(type_ll)),
                "mean_lead_lag_hours": round(float(type_ll.mean()), 1),
                "median_lead_lag_hours": round(float(type_ll.median()), 1),
                "pct_kalshi_leads": round(float((type_ll < 0).mean()), 3),
            }

    # Surprise vs non-surprise
    for label, mask in [("surprise", results["surprise"] == True), ("non_surprise", results["surprise"] == False)]:
        ll = results.loc[mask, "lead_lag_vs_epu_hours"].dropna()
        if len(ll) > 0:
            output[label] = {
                "n": int(len(ll)),
                "mean_lead_lag_hours": round(float(ll.mean()), 1),
                "median_lead_lag_hours": round(float(ll.median()), 1),
                "pct_kalshi_leads": round(float((ll < 0).mean()), 3),
            }

    return output


def plot_event_windows(
    windows: list[dict],
    results: pd.DataFrame,
    output_dir: str = "data/exp4/plots",
):
    """Plot hourly KUI response around key events."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    os.makedirs(output_dir, exist_ok=True)

    # Select up to 4 surprise events with good data
    surprise_windows = [w for w in windows if w["surprise"] and w["n_hours"] >= 12]

    if not surprise_windows:
        print("  No surprise events with sufficient hourly data for plotting")
        return

    n_plots = min(4, len(surprise_windows))
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()

    for i in range(4):
        ax = axes[i]
        if i < n_plots:
            w = surprise_windows[i]
            window = w["window"]

            # Plot hourly BV
            ax.plot(window.index, window.values, "b-", alpha=0.7, linewidth=1.5, label="Kalshi hourly BV")
            ax.axvline(x=0, color="red", linestyle="--", alpha=0.8, label="Event time")

            # Pre-event baseline
            pre = window[(window.index >= -24) & (window.index < 0)]
            if len(pre) > 0:
                ax.axhline(y=pre.mean(), color="gray", linestyle=":", alpha=0.5, label=f"Pre-event mean")
                ax.axhline(
                    y=pre.mean() + 2 * pre.std(), color="orange", linestyle=":",
                    alpha=0.5, label="2σ threshold"
                )

            # Mark Kalshi reaction
            result_row = results[results["event_date"] == w["event_date"]]
            if not result_row.empty:
                kalshi_h = result_row.iloc[0]["kalshi_reaction_hours"]
                if kalshi_h is not None and not np.isnan(kalshi_h):
                    ax.axvline(x=kalshi_h, color="green", linestyle="-.", alpha=0.7)
                    ax.annotate(f"Kalshi: +{kalshi_h:.0f}h", (kalshi_h, ax.get_ylim()[1] * 0.9),
                               color="green", fontsize=9)

            ax.set_title(f"{w['description']}\n({w['domain']})", fontsize=10)
            ax.set_xlabel("Hours from event")
            ax.set_ylabel("Belief Volatility")
            ax.legend(fontsize=8)
            ax.grid(True, alpha=0.3)
        else:
            ax.set_visible(False)

    plt.suptitle("Hourly Kalshi Response to Economic Events", fontsize=14, y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "hourly_event_windows.png"), dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved {output_dir}/hourly_event_windows.png")

    # Summary bar chart: reaction speed by event type
    type_reactions = results.groupby("event_type")["kalshi_reaction_hours"].agg(["mean", "count"])
    type_reactions = type_reactions.dropna(subset=["mean"])

    if not type_reactions.empty:
        fig, ax = plt.subplots(figsize=(10, 5))
        colors = {"CPI": "#E74C3C", "FOMC": "#3498DB", "NFP": "#2ECC71", "GDP": "#F39C12", "tariff": "#9B59B6"}
        bars = ax.bar(
            type_reactions.index,
            type_reactions["mean"],
            color=[colors.get(t, "gray") for t in type_reactions.index],
            alpha=0.8,
        )
        for bar, (_, row) in zip(bars, type_reactions.iterrows()):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                    f"n={int(row['count'])}", ha="center", fontsize=10)

        ax.set_ylabel("Mean Reaction Time (hours)")
        ax.set_title("Kalshi Market Reaction Speed by Event Type")
        ax.grid(True, alpha=0.3, axis="y")
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "reaction_speed_by_type.png"), dpi=150)
        plt.close()
        print(f"  Saved {output_dir}/reaction_speed_by_type.png")
