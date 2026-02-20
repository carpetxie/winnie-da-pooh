"""
experiment10/shock_propagation.py

Cross-Event Shock Propagation Heatmap.

When a CPI surprise drops, track how the shock ripples through
Fed Funds -> Jobless Claims -> GDP markets hour-by-hour.

Uses existing hourly candle data from experiment2 + economic event
calendar from experiment2/event_study.py.
"""

import os
import json
import glob
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta
from scipy import stats
from collections import defaultdict

CANDLE_DIR = "data/exp2/raw/candles"

# Map event types to their "origin domain" for shock source identification
EVENT_DOMAIN_MAP = {
    "CPI": "inflation",
    "FOMC": "monetary_policy",
    "NFP": "labor",
    "GDP": "macro",
    "tariff": "macro",
}

# Map ticker prefixes to domains (same as experiment1)
DOMAIN_MAP = {
    "KXCPI": "inflation", "KXPCE": "inflation", "KXPPI": "inflation",
    "KXFED": "monetary_policy", "KXFFR": "monetary_policy",
    "KXNFP": "labor", "KXJOBLESSCLAIMS": "labor", "KXUNEMPLOYMENT": "labor",
    "KXGDP": "macro", "KXRETAILSALES": "macro", "KXISM": "macro",
    "KXRECESSION": "macro",
}

ECON_DOMAINS = ["inflation", "monetary_policy", "labor", "macro"]


def _ticker_to_domain(ticker: str) -> str:
    prefix = ticker.split("-")[0] if "-" in ticker else ticker
    if prefix in DOMAIN_MAP:
        return DOMAIN_MAP[prefix]
    for key, domain in DOMAIN_MAP.items():
        if prefix.startswith(key):
            return domain
    return "other"


def load_hourly_series(candle_dir: str = CANDLE_DIR) -> dict[str, pd.DataFrame]:
    """Load all hourly candle files into per-ticker DataFrames.

    Returns:
        {ticker: DataFrame with columns [close, volume, oi, spread, range]}
        indexed by UTC datetime.
    """
    files = sorted(glob.glob(os.path.join(candle_dir, "*_60.json")))
    ticker_series = {}

    for f in files:
        ticker = os.path.basename(f).replace("_60.json", "")
        domain = _ticker_to_domain(ticker)
        if domain == "other":
            continue

        with open(f) as fh:
            candles = json.load(fh)

        rows = []
        for c in candles:
            ts = c.get("end_period_ts")
            price = c.get("price", {})
            close = price.get("close_dollars")
            if ts is None or close is None:
                continue
            try:
                dt = datetime.fromtimestamp(ts, tz=timezone.utc)
                close_f = float(close)
                vol = int(c.get("volume", 0))
                oi = int(c.get("open_interest", 0))

                bid = c.get("yes_bid", {})
                ask = c.get("yes_ask", {})
                bid_close = float(bid.get("close_dollars", 0) or 0)
                ask_close = float(ask.get("close_dollars", 0) or 0)
                spread = ask_close - bid_close if ask_close > bid_close else 0

                high = float(price.get("high_dollars", close) or close)
                low = float(price.get("low_dollars", close) or close)
                rng = high - low

                rows.append({
                    "datetime": dt,
                    "close": close_f,
                    "volume": vol,
                    "oi": oi,
                    "spread": spread,
                    "range": rng,
                })
            except (ValueError, TypeError):
                continue

        if len(rows) >= 10:
            df = pd.DataFrame(rows).set_index("datetime").sort_index()
            # Remove exact duplicates
            df = df[~df.index.duplicated(keep="first")]
            ticker_series[ticker] = df

    return ticker_series


def compute_event_responses(
    ticker_series: dict[str, pd.DataFrame],
    events: pd.DataFrame,
    pre_hours: int = 24,
    post_hours: int = 48,
) -> pd.DataFrame:
    """For each event, compute hourly price response in every active market.

    Returns DataFrame with columns:
        event_date, event_type, event_surprise, ticker, domain,
        hour_offset (-pre_hours to +post_hours),
        abs_return (absolute price change from event hour),
        cum_return (cumulative return from event hour),
        volume_ratio (volume / pre-event avg volume),
        spread_change (spread - pre-event avg spread)
    """
    records = []

    for _, event in events.iterrows():
        event_date = pd.Timestamp(event["date"]).tz_localize("US/Eastern")
        # Economic events typically release at 8:30 AM ET
        if event["type"] in ("CPI", "NFP", "GDP"):
            event_time = event_date.replace(hour=8, minute=30)
        elif event["type"] == "FOMC":
            event_time = event_date.replace(hour=14, minute=0)
        else:
            event_time = event_date.replace(hour=12, minute=0)

        event_utc = event_time.tz_convert("UTC")
        origin_domain = EVENT_DOMAIN_MAP.get(event["type"], "other")

        for ticker, df in ticker_series.items():
            domain = _ticker_to_domain(ticker)
            if domain == "other":
                continue

            # Find the candle closest to event time
            window_start = event_utc - timedelta(hours=pre_hours)
            window_end = event_utc + timedelta(hours=post_hours)

            mask = (df.index >= window_start) & (df.index <= window_end)
            window = df[mask]

            if len(window) < 5:
                continue

            # Find the anchor price (closest candle to event time)
            time_diffs = abs(window.index - event_utc)
            anchor_idx = time_diffs.argmin()
            anchor_price = window["close"].iloc[anchor_idx]

            if anchor_price == 0:
                continue

            # Pre-event baseline stats
            pre_mask = window.index < event_utc
            pre_data = window[pre_mask]
            pre_vol_mean = pre_data["volume"].mean() if len(pre_data) > 0 else 1
            pre_spread_mean = pre_data["spread"].mean() if len(pre_data) > 0 else 0

            for i, (ts, row) in enumerate(window.iterrows()):
                hour_offset = (ts - event_utc).total_seconds() / 3600
                # Round to nearest integer hour
                hour_offset_int = round(hour_offset)

                abs_return = abs(row["close"] - anchor_price)
                cum_return = row["close"] - anchor_price
                vol_ratio = row["volume"] / max(pre_vol_mean, 1)
                spread_change = row["spread"] - pre_spread_mean

                records.append({
                    "event_date": event["date"],
                    "event_type": event["type"],
                    "event_surprise": event["surprise"],
                    "origin_domain": origin_domain,
                    "ticker": ticker,
                    "domain": domain,
                    "hour_offset": hour_offset_int,
                    "abs_return": abs_return,
                    "cum_return": cum_return,
                    "volume_ratio": vol_ratio,
                    "spread_change": spread_change,
                })

    return pd.DataFrame(records)


def build_propagation_heatmap(
    responses: pd.DataFrame,
    metric: str = "abs_return",
) -> dict:
    """Build the cross-domain shock propagation heatmap.

    For each (event_type, responding_domain) pair, compute the
    average response at each hour offset. This shows how fast
    each domain reacts to each type of event.

    Uses a GLOBAL pre-event baseline (all domains combined) to avoid the
    bias where origin domains have inflated thresholds due to anticipation
    trading. First significant response is detected via cumulative abnormal
    returns (CAR) exceeding the 95th percentile of pre-event CAR values.

    Returns:
        {
            "heatmaps": {event_type: {domain: {hour: avg_response}}},
            "first_significant_response": {event_type: {domain: hour}},
            "propagation_speeds": [{source, target, ...}],
        }
    """
    heatmaps = {}
    first_response = {}
    propagation_speeds = []

    for event_type in responses["event_type"].unique():
        evt_data = responses[responses["event_type"] == event_type]
        origin_domain = EVENT_DOMAIN_MAP.get(event_type, "other")

        heatmaps[event_type] = {}
        first_response[event_type] = {}

        # --- Global pre-event baseline across ALL domains ---
        all_pre = evt_data[evt_data["hour_offset"] < 0]
        if len(all_pre) < 5:
            continue
        global_hourly = all_pre.groupby("hour_offset")[metric].mean()
        global_baseline = float(global_hourly.mean())

        # Build null distribution of CAR from pre-event hours to set threshold.
        # For each starting hour h_start in [-24, -1], compute CAR over a
        # short window (same length we'll scan post-event, up to 6 hours)
        # using the global baseline.
        pre_hours_sorted = sorted(global_hourly.index)
        null_car_values = []
        scan_len = 6  # hours to accumulate
        for start_idx in range(len(pre_hours_sorted)):
            car = 0.0
            for j in range(start_idx, min(start_idx + scan_len, len(pre_hours_sorted))):
                car += max(float(global_hourly.iloc[j]) - global_baseline, 0.0)
                null_car_values.append(car)

        if len(null_car_values) < 3:
            continue
        global_threshold = float(np.percentile(null_car_values, 95))
        # Ensure threshold is positive to avoid trivial triggers
        if global_threshold <= 0:
            global_threshold = global_baseline * 0.5 if global_baseline > 0 else 1e-9

        # --- Per-domain: compute heatmap and CAR-based first response ---
        for domain in ECON_DOMAINS:
            dom_data = evt_data[evt_data["domain"] == domain]
            if len(dom_data) == 0:
                continue

            # Average response by hour offset
            hourly = dom_data.groupby("hour_offset")[metric].mean()
            heatmaps[event_type][domain] = {
                int(h): float(v) for h, v in hourly.items()
            }

            # Post-event CAR detection with global baseline & threshold
            post_event = hourly[hourly.index >= 0].sort_index()
            if len(post_event) == 0:
                continue

            car = 0.0
            first_sig_hour = None
            for hour, value in post_event.items():
                car += max(float(value) - global_baseline, 0.0)
                if car > global_threshold:
                    first_sig_hour = int(hour)
                    break

            if first_sig_hour is not None:
                first_response[event_type][domain] = first_sig_hour

        # Validate: warn if origin responds after cross-domains
        origin_hour = first_response.get(event_type, {}).get(origin_domain)
        cross_hours = {
            d: h for d, h in first_response.get(event_type, {}).items()
            if d != origin_domain
        }
        if origin_hour is not None and cross_hours:
            min_cross = min(cross_hours.values())
            if origin_hour > min_cross:
                earliest_cross = [d for d, h in cross_hours.items() if h == min_cross]
                print(
                    f"  WARNING [{event_type}]: origin domain '{origin_domain}' "
                    f"responds at h={origin_hour}, but {earliest_cross} respond "
                    f"at h={min_cross}. Possible residual threshold bias."
                )

        # Compute propagation speed: origin → each other domain
        if origin_domain in first_response.get(event_type, {}):
            origin_lag = first_response[event_type][origin_domain]
            for target_domain, target_lag in first_response[event_type].items():
                if target_domain != origin_domain:
                    propagation_speeds.append({
                        "event_type": event_type,
                        "source": origin_domain,
                        "target": target_domain,
                        "source_lag_hours": origin_lag,
                        "target_lag_hours": target_lag,
                        "propagation_delay": target_lag - origin_lag,
                    })

    return {
        "heatmaps": heatmaps,
        "first_significant_response": first_response,
        "propagation_speeds": propagation_speeds,
    }


def compute_response_ratio_ordering(responses: pd.DataFrame) -> dict:
    """Compute normalized response ratio per domain for each event type.

    For each (event_type, domain), the ratio is:
        mean(abs_return for h in [0, 6]) / mean(abs_return for h in [-24, -1])

    Higher ratio means the domain reacts more strongly relative to its
    own pre-event activity. This gives a simple, interpretable ordering
    of which domain responds most to each event type.

    Returns:
        {event_type: {domain: ratio}}
    """
    result = {}

    for event_type in responses["event_type"].unique():
        evt_data = responses[responses["event_type"] == event_type]
        result[event_type] = {}

        for domain in ECON_DOMAINS:
            dom_data = evt_data[evt_data["domain"] == domain]
            if len(dom_data) == 0:
                continue

            post = dom_data[
                (dom_data["hour_offset"] >= 0) & (dom_data["hour_offset"] <= 6)
            ]["abs_return"]
            pre = dom_data[
                (dom_data["hour_offset"] >= -24) & (dom_data["hour_offset"] <= -1)
            ]["abs_return"]

            if len(pre) == 0 or pre.mean() == 0:
                continue

            ratio = float(post.mean() / pre.mean())
            result[event_type][domain] = ratio

    return result


def test_response_ordering(responses: pd.DataFrame) -> dict:
    """Test whether the origin domain responds more strongly than cross-domains.

    For each event type, compares the origin domain's hourly abs_returns
    (hours 0-6) against each cross-domain's hourly abs_returns (hours 0-6)
    using the Mann-Whitney U test.

    Returns:
        {event_type: {
            "origin_domain": str,
            "origin_mean": float,
            "cross_tests": {domain: {U, p_value, cross_mean, significant}},
        }}
    """
    result = {}

    for event_type in responses["event_type"].unique():
        evt_data = responses[responses["event_type"] == event_type]
        origin_domain = EVENT_DOMAIN_MAP.get(event_type, "other")

        post = evt_data[
            (evt_data["hour_offset"] >= 0) & (evt_data["hour_offset"] <= 6)
        ]

        origin_returns = post[post["domain"] == origin_domain]["abs_return"]
        if len(origin_returns) < 5:
            continue

        cross_tests = {}
        for domain in ECON_DOMAINS:
            if domain == origin_domain:
                continue

            cross_returns = post[post["domain"] == domain]["abs_return"]
            if len(cross_returns) < 5:
                continue

            stat, p = stats.mannwhitneyu(
                origin_returns, cross_returns, alternative="greater"
            )
            cross_tests[domain] = {
                "U": float(stat),
                "p_value": float(p),
                "cross_mean": float(cross_returns.mean()),
                "significant": p < 0.05,
            }

        result[event_type] = {
            "origin_domain": origin_domain,
            "origin_mean": float(origin_returns.mean()),
            "cross_tests": cross_tests,
        }

    return result


def analyze_surprise_vs_nonsurprise(responses: pd.DataFrame) -> dict:
    """Compare shock propagation speed for surprise vs non-surprise events.

    Tests whether surprise events cause faster/stronger cross-domain responses.
    """
    results = {}

    for domain in ECON_DOMAINS:
        dom_data = responses[responses["domain"] == domain]
        if len(dom_data) < 20:
            continue

        # Post-event absolute returns (hours 0-12)
        post = dom_data[(dom_data["hour_offset"] >= 0) & (dom_data["hour_offset"] <= 12)]

        surprise = post[post["event_surprise"] == True]["abs_return"]
        nonsurprise = post[post["event_surprise"] == False]["abs_return"]

        if len(surprise) < 10 or len(nonsurprise) < 10:
            continue

        stat, p = stats.mannwhitneyu(surprise, nonsurprise, alternative="greater")

        results[domain] = {
            "surprise_mean": float(surprise.mean()),
            "nonsurprise_mean": float(nonsurprise.mean()),
            "ratio": float(surprise.mean() / nonsurprise.mean()) if nonsurprise.mean() > 0 else None,
            "mann_whitney_U": float(stat),
            "p_value": float(p),
            "significant": p < 0.05,
            "n_surprise": len(surprise),
            "n_nonsurprise": len(nonsurprise),
        }

    return results


def analyze_cross_domain_contagion(responses: pd.DataFrame) -> dict:
    """For each event, measure how much non-origin domains move.

    Computes a "contagion score": the ratio of cross-domain response
    magnitude to origin-domain response magnitude.
    """
    contagion_scores = []

    for (event_date, event_type), group in responses.groupby(["event_date", "event_type"]):
        origin_domain = EVENT_DOMAIN_MAP.get(event_type, "other")

        # Post-event window (hours 1-12)
        post = group[(group["hour_offset"] >= 1) & (group["hour_offset"] <= 12)]

        origin_response = post[post["domain"] == origin_domain]["abs_return"].mean()
        cross_responses = post[post["domain"] != origin_domain]

        if pd.isna(origin_response) or origin_response == 0 or len(cross_responses) == 0:
            continue

        for domain in cross_responses["domain"].unique():
            cross_mean = cross_responses[cross_responses["domain"] == domain]["abs_return"].mean()
            if pd.isna(cross_mean):
                continue

            contagion_scores.append({
                "event_date": str(event_date),
                "event_type": event_type,
                "event_surprise": group["event_surprise"].iloc[0],
                "origin_domain": origin_domain,
                "target_domain": domain,
                "origin_response": float(origin_response),
                "cross_response": float(cross_mean),
                "contagion_ratio": float(cross_mean / origin_response),
            })

    if not contagion_scores:
        return {"error": "no_contagion_data"}

    df = pd.DataFrame(contagion_scores)

    # Summary by event_type -> target_domain
    summary = {}
    for event_type in df["event_type"].unique():
        evt = df[df["event_type"] == event_type]
        summary[event_type] = {}
        for target in evt["target_domain"].unique():
            tgt = evt[evt["target_domain"] == target]
            summary[event_type][target] = {
                "mean_contagion_ratio": float(tgt["contagion_ratio"].mean()),
                "median_contagion_ratio": float(tgt["contagion_ratio"].median()),
                "n_events": len(tgt),
            }

    # Test: surprise events have higher contagion
    surprise = df[df["event_surprise"] == True]["contagion_ratio"]
    nonsurprise = df[df["event_surprise"] == False]["contagion_ratio"]

    surprise_test = {}
    if len(surprise) >= 5 and len(nonsurprise) >= 5:
        stat, p = stats.mannwhitneyu(surprise, nonsurprise, alternative="greater")
        surprise_test = {
            "surprise_mean_contagion": float(surprise.mean()),
            "nonsurprise_mean_contagion": float(nonsurprise.mean()),
            "mann_whitney_p": float(p),
            "significant": p < 0.05,
        }

    return {
        "contagion_summary": summary,
        "surprise_contagion_test": surprise_test,
        "n_total_pairs": len(df),
        "raw_scores": contagion_scores,
    }


def build_temporal_cascade_matrix(responses: pd.DataFrame) -> dict:
    """Build the hour-by-hour response matrix for visualization.

    For each event type, creates a matrix:
        rows = domains (inflation, monetary_policy, labor, macro)
        cols = hour offsets (-6 to +24)
        values = normalized average absolute return

    This is the data behind the propagation heatmap figure.
    """
    matrices = {}

    for event_type in responses["event_type"].unique():
        evt = responses[responses["event_type"] == event_type]

        # Focus on -6 to +24 hours
        evt = evt[(evt["hour_offset"] >= -6) & (evt["hour_offset"] <= 24)]

        matrix = {}
        for domain in ECON_DOMAINS:
            dom = evt[evt["domain"] == domain]
            if len(dom) == 0:
                continue

            hourly = dom.groupby("hour_offset")["abs_return"].mean()

            # Normalize by pre-event mean
            pre = hourly[hourly.index < 0]
            baseline = pre.mean() if len(pre) > 0 else 0

            if baseline > 0:
                normalized = {int(h): float(v / baseline) for h, v in hourly.items()}
            else:
                normalized = {int(h): float(v) for h, v in hourly.items()}

            matrix[domain] = normalized

        if matrix:
            matrices[event_type] = matrix

    return matrices


def plot_propagation_heatmap(
    matrices: dict,
    first_response: dict,
    output_dir: str,
):
    """Plot the shock propagation heatmap for each event type."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors

    os.makedirs(output_dir, exist_ok=True)

    event_types = sorted(matrices.keys())
    n_types = len(event_types)

    if n_types == 0:
        return

    fig, axes = plt.subplots(n_types, 1, figsize=(16, 4 * n_types), squeeze=False)

    for i, event_type in enumerate(event_types):
        ax = axes[i, 0]
        matrix = matrices[event_type]

        # Build the heatmap array
        domains = [d for d in ECON_DOMAINS if d in matrix]
        hours = sorted(set(h for d in domains for h in matrix[d].keys()))

        if not domains or not hours:
            continue

        data = np.full((len(domains), len(hours)), np.nan)
        for di, domain in enumerate(domains):
            for hi, hour in enumerate(hours):
                if hour in matrix[domain]:
                    data[di, hi] = matrix[domain][hour]

        # Plot
        im = ax.imshow(
            data, aspect="auto", cmap="YlOrRd",
            interpolation="nearest",
            vmin=0.5, vmax=3.0,
        )

        ax.set_yticks(range(len(domains)))
        ax.set_yticklabels(domains)

        # Show every 3rd hour label
        tick_positions = list(range(0, len(hours), 3))
        ax.set_xticks(tick_positions)
        ax.set_xticklabels([hours[j] for j in tick_positions])
        ax.set_xlabel("Hours relative to event")

        # Mark event time
        if 0 in hours:
            event_idx = hours.index(0)
            ax.axvline(event_idx, color="white", linewidth=2, linestyle="--")

        # Mark first significant response
        fr = first_response.get(event_type, {})
        for di, domain in enumerate(domains):
            if domain in fr:
                hour = fr[domain]
                if hour in hours:
                    hi = hours.index(hour)
                    ax.plot(hi, di, "w*", markersize=12, markeredgecolor="black")

        origin = EVENT_DOMAIN_MAP.get(event_type, "?")
        ax.set_title(
            f"{event_type} Events → Cross-Domain Response "
            f"(origin: {origin}, * = first significant response)"
        )

        plt.colorbar(im, ax=ax, label="Normalized response (1.0 = pre-event baseline)")

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "shock_propagation_heatmap.png"), dpi=150)
    plt.close()
    print(f"  Saved {output_dir}/shock_propagation_heatmap.png")

    # Also plot the cascade timeline
    _plot_cascade_timeline(matrices, first_response, output_dir)


def _plot_cascade_timeline(matrices, first_response, output_dir):
    """Plot a timeline showing when each domain first responds to each event type."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(12, 6))

    colors = {
        "inflation": "#e74c3c",
        "monetary_policy": "#3498db",
        "labor": "#2ecc71",
        "macro": "#f39c12",
    }

    y_positions = {"CPI": 4, "FOMC": 3, "NFP": 2, "GDP": 1}

    for event_type, fr in first_response.items():
        if event_type not in y_positions:
            continue
        y = y_positions[event_type]

        for domain, hour in fr.items():
            ax.barh(
                y, width=1, left=hour,
                color=colors.get(domain, "gray"),
                edgecolor="black", linewidth=0.5,
                height=0.6, alpha=0.8,
            )
            ax.text(hour + 0.5, y, f"{domain[:4]}\n{hour}h",
                    ha="center", va="center", fontsize=7, fontweight="bold")

    ax.set_yticks(list(y_positions.values()))
    ax.set_yticklabels(list(y_positions.keys()))
    ax.set_xlabel("Hours after event")
    ax.set_title("Shock Propagation Timeline: First Significant Response by Domain")
    ax.axvline(0, color="red", linewidth=2, linestyle="--", label="Event time")
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "cascade_timeline.png"), dpi=150)
    plt.close()
    print(f"  Saved {output_dir}/cascade_timeline.png")
