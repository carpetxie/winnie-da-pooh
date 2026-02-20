"""
experiment11/favorite_longshot.py

Favorite-Longshot Bias × Microstructure Analysis.

Tests whether the favorite-longshot bias (Whelan, CEPR 2024) disappears
in high-OI, tight-spread markets. Extends the published finding with
microstructure data that Whelan didn't have access to.

Key hypothesis: more liquidity → more informed traders → bias elimination.
"""

import os
import json
import glob
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from scipy import stats
from collections import defaultdict

CANDLE_DIR = "data/exp2/raw/candles"
TARGETED_MARKETS = "data/exp2/raw/targeted_markets.json"


def load_settled_markets() -> pd.DataFrame:
    """Load all settled markets with outcomes.

    Returns DataFrame with: ticker, result (yes/no), last_price (implied prob),
    open_interest, volume, open_time, close_time, etc.
    """
    with open(TARGETED_MARKETS) as f:
        markets = json.load(f)

    records = []
    for m in markets:
        if m.get("status") != "finalized" or m.get("result") not in ("yes", "no"):
            continue

        last_price = m.get("last_price")
        if last_price is None:
            continue

        # Implied probability from last price (cents → probability)
        implied_prob = last_price / 100.0
        realized = 1.0 if m["result"] == "yes" else 0.0

        records.append({
            "ticker": m["ticker"],
            "event_ticker": m.get("event_ticker", ""),
            "title": m.get("title", ""),
            "result": m["result"],
            "implied_prob": implied_prob,
            "realized": realized,
            "last_price": last_price,
            "open_interest": int(m.get("open_interest", 0)),
            "volume": int(m.get("volume", 0)),
            "yes_bid": int(m.get("yes_bid", 0)),
            "yes_ask": int(m.get("yes_ask", 0)),
            "open_time": m.get("open_time"),
            "close_time": m.get("close_time"),
            "settlement_ts": m.get("settlement_ts"),
        })

    df = pd.DataFrame(records)

    # Compute derived fields
    df["spread"] = (df["yes_ask"] - df["yes_bid"]) / 100.0  # in dollars
    df["spread"] = df["spread"].clip(lower=0)

    # Time to expiration
    df["open_dt"] = pd.to_datetime(df["open_time"], errors="coerce")
    df["close_dt"] = pd.to_datetime(df["close_time"], errors="coerce")
    df["lifetime_hours"] = (df["close_dt"] - df["open_dt"]).dt.total_seconds() / 3600

    return df


def load_microstructure_from_candles() -> pd.DataFrame:
    """Load per-ticker microstructure summaries from hourly candles.

    Returns DataFrame indexed by ticker with:
    mean_spread, mean_oi, peak_oi, mean_volume, total_volume, n_candles
    """
    files = sorted(glob.glob(os.path.join(CANDLE_DIR, "*_60.json")))

    records = []
    for f in files:
        ticker = os.path.basename(f).replace("_60.json", "")

        with open(f) as fh:
            candles = json.load(fh)

        if not candles:
            continue

        spreads = []
        ois = []
        volumes = []

        for c in candles:
            bid = c.get("yes_bid", {})
            ask = c.get("yes_ask", {})
            try:
                bid_close = float(bid.get("close_dollars", 0) or 0)
                ask_close = float(ask.get("close_dollars", 0) or 0)
                spread = max(0, ask_close - bid_close)
                spreads.append(spread)
            except (ValueError, TypeError):
                pass

            oi = c.get("open_interest", 0)
            if oi is not None:
                ois.append(int(oi))

            vol = c.get("volume", 0)
            if vol is not None:
                volumes.append(int(vol))

        if spreads:
            records.append({
                "ticker": ticker,
                "mean_spread": np.mean(spreads),
                "median_spread": np.median(spreads),
                "mean_oi": np.mean(ois) if ois else 0,
                "peak_oi": max(ois) if ois else 0,
                "mean_volume": np.mean(volumes) if volumes else 0,
                "total_volume": sum(volumes) if volumes else 0,
                "n_candles": len(candles),
            })

    return pd.DataFrame(records).set_index("ticker")


def compute_calibration_curve(
    df: pd.DataFrame,
    n_bins: int = 10,
    min_bin_count: int = 5,
) -> pd.DataFrame:
    """Compute calibration curve: bin by implied probability, compute actual frequency.

    Returns DataFrame with: bin_center, mean_implied, mean_realized, n, bias
    where bias = mean_implied - mean_realized (positive = overpriced).
    """
    df = df.copy()

    # Create probability bins
    bins = np.linspace(0, 1, n_bins + 1)
    df["prob_bin"] = pd.cut(df["implied_prob"], bins=bins, labels=False, include_lowest=True)

    calibration = []
    for bin_idx in range(n_bins):
        bin_data = df[df["prob_bin"] == bin_idx]
        if len(bin_data) < min_bin_count:
            continue

        bin_center = (bins[bin_idx] + bins[bin_idx + 1]) / 2
        mean_implied = bin_data["implied_prob"].mean()
        mean_realized = bin_data["realized"].mean()

        calibration.append({
            "bin_center": bin_center,
            "mean_implied": mean_implied,
            "mean_realized": mean_realized,
            "n": len(bin_data),
            "bias": mean_implied - mean_realized,
        })

    return pd.DataFrame(calibration)


def analyze_favorite_longshot_bias(df: pd.DataFrame) -> dict:
    """Test for favorite-longshot bias overall.

    Favorite-longshot bias: longshots (low probability events) are overpriced
    (implied prob > actual frequency), favorites (high probability events)
    are underpriced (implied prob < actual frequency).
    """
    cal = compute_calibration_curve(df, n_bins=10)

    if len(cal) < 4:
        return {"error": "insufficient_bins", "n_bins": len(cal)}

    # Split into longshots (p < 0.3) and favorites (p > 0.7)
    longshots = df[df["implied_prob"] < 0.30]
    favorites = df[df["implied_prob"] > 0.70]
    midrange = df[(df["implied_prob"] >= 0.30) & (df["implied_prob"] <= 0.70)]

    result = {
        "overall_calibration": cal.to_dict("records"),
        "n_total": len(df),
    }

    # Longshot bias test: are longshots overpriced?
    if len(longshots) >= 10:
        longshot_implied = longshots["implied_prob"].mean()
        longshot_actual = longshots["realized"].mean()
        longshot_bias = longshot_implied - longshot_actual
        # Binomial test: is actual frequency significantly below implied?
        n = len(longshots)
        k = int(longshots["realized"].sum())
        binom_p = stats.binomtest(k, n, longshot_implied, alternative="less").pvalue
        result["longshot"] = {
            "mean_implied": float(longshot_implied),
            "mean_actual": float(longshot_actual),
            "bias": float(longshot_bias),
            "n": len(longshots),
            "binomial_p": float(binom_p),
            "overpriced": longshot_bias > 0 and binom_p < 0.05,
        }

    # Favorite bias test: are favorites underpriced?
    if len(favorites) >= 10:
        fav_implied = favorites["implied_prob"].mean()
        fav_actual = favorites["realized"].mean()
        fav_bias = fav_implied - fav_actual
        n = len(favorites)
        k = int(favorites["realized"].sum())
        binom_p = stats.binomtest(k, n, fav_implied, alternative="greater").pvalue
        result["favorite"] = {
            "mean_implied": float(fav_implied),
            "mean_actual": float(fav_actual),
            "bias": float(fav_bias),
            "n": len(favorites),
            "binomial_p": float(binom_p),
            "underpriced": fav_bias < 0 and binom_p < 0.05,
        }

    # Overall Brier score
    brier = np.mean((df["implied_prob"] - df["realized"]) ** 2)
    result["overall_brier"] = float(brier)

    return result


def analyze_bias_by_microstructure(
    df: pd.DataFrame,
    micro: pd.DataFrame,
) -> dict:
    """Test whether favorite-longshot bias disappears with better microstructure.

    Splits markets into terciles by OI, spread, and volume.
    Tests calibration in each tercile.

    Key hypothesis: high-OI / tight-spread markets should show less bias.
    """
    # Merge microstructure data
    merged = df.copy()
    if "ticker" in merged.columns:
        merged = merged.set_index("ticker").join(micro, how="inner").reset_index()
    else:
        merged = merged.join(micro, how="inner").reset_index()

    if len(merged) < 30:
        return {"error": "insufficient_merged_data", "n": len(merged)}

    results = {}

    # Analyze by OI tercile
    for metric, label in [
        ("peak_oi", "open_interest"),
        ("mean_spread", "spread"),
        ("total_volume", "volume"),
    ]:
        if metric not in merged.columns or merged[metric].isna().all():
            continue

        # Remove zeros for cleaner terciles
        valid = merged[merged[metric] > 0].copy()
        if len(valid) < 30:
            continue

        try:
            valid["tercile"] = pd.qcut(valid[metric], q=3, labels=["low", "medium", "high"])
        except ValueError:
            continue

        tercile_results = {}
        for tercile in ["low", "medium", "high"]:
            t_data = valid[valid["tercile"] == tercile]
            if len(t_data) < 10:
                continue

            cal = compute_calibration_curve(t_data, n_bins=5, min_bin_count=3)

            # Compute bias for longshots in this tercile
            longshots = t_data[t_data["implied_prob"] < 0.30]
            longshot_bias = None
            if len(longshots) >= 5:
                longshot_bias = float(longshots["implied_prob"].mean() - longshots["realized"].mean())

            favorites = t_data[t_data["implied_prob"] > 0.70]
            favorite_bias = None
            if len(favorites) >= 5:
                favorite_bias = float(favorites["implied_prob"].mean() - favorites["realized"].mean())

            brier = float(np.mean((t_data["implied_prob"] - t_data["realized"]) ** 2))

            tercile_results[tercile] = {
                "n": len(t_data),
                "brier": brier,
                "mean_metric": float(t_data[metric].mean()),
                "longshot_bias": longshot_bias,
                "favorite_bias": favorite_bias,
                "calibration": cal.to_dict("records") if len(cal) > 0 else [],
            }

        # Statistical test: does bias differ between low and high OI?
        comparison = {}
        low = valid[valid["tercile"] == "low"]
        high = valid[valid["tercile"] == "high"]
        if len(low) >= 20 and len(high) >= 20:
            # Compare squared calibration error
            low_errors = (low["implied_prob"] - low["realized"]) ** 2
            high_errors = (high["implied_prob"] - high["realized"]) ** 2
            stat, p = stats.mannwhitneyu(low_errors, high_errors, alternative="greater")
            comparison = {
                "low_brier": float(low_errors.mean()),
                "high_brier": float(high_errors.mean()),
                "mann_whitney_U": float(stat),
                "p_value": float(p),
                "significant": p < 0.05,
                "direction": "high_better" if low_errors.mean() > high_errors.mean() else "low_better",
            }

        results[label] = {
            "terciles": tercile_results,
            "comparison": comparison,
            "n_total": len(valid),
        }

    return results


def analyze_bias_by_time_to_expiration(df: pd.DataFrame) -> dict:
    """Test whether bias decreases as markets approach expiration.

    Closer to expiration → more information → less bias?
    """
    df = df.copy()
    df = df[df["lifetime_hours"].notna() & (df["lifetime_hours"] > 0)]

    if len(df) < 30:
        return {"error": "insufficient_data"}

    try:
        df["time_tercile"] = pd.qcut(
            df["lifetime_hours"].rank(method="first"), q=3, labels=["short", "medium", "long"]
        )
    except ValueError:
        return {"error": "cannot_create_terciles"}

    results = {}
    for tercile in ["short", "medium", "long"]:
        t_data = df[df["time_tercile"] == tercile]
        if len(t_data) < 10:
            continue

        brier = float(np.mean((t_data["implied_prob"] - t_data["realized"]) ** 2))

        longshots = t_data[t_data["implied_prob"] < 0.30]
        longshot_bias = None
        if len(longshots) >= 5:
            longshot_bias = float(longshots["implied_prob"].mean() - longshots["realized"].mean())

        results[tercile] = {
            "n": len(t_data),
            "brier": brier,
            "mean_lifetime_hours": float(t_data["lifetime_hours"].mean()),
            "longshot_bias": longshot_bias,
        }

    return results


def analyze_bias_by_domain(df: pd.DataFrame) -> dict:
    """Break down favorite-longshot bias by market domain.

    Some domains may have more informed traders than others.
    """
    from experiment1.data_collection import extract_fine_domain

    df = df.copy()
    df["domain"] = df["ticker"].apply(extract_fine_domain)

    results = {}
    for domain in df["domain"].unique():
        d_data = df[df["domain"] == domain]
        if len(d_data) < 20:
            continue

        brier = float(np.mean((d_data["implied_prob"] - d_data["realized"]) ** 2))

        longshots = d_data[d_data["implied_prob"] < 0.30]
        longshot_bias = None
        if len(longshots) >= 5:
            longshot_bias = float(longshots["implied_prob"].mean() - longshots["realized"].mean())

        favorites = d_data[d_data["implied_prob"] > 0.70]
        favorite_bias = None
        if len(favorites) >= 5:
            favorite_bias = float(favorites["implied_prob"].mean() - favorites["realized"].mean())

        results[domain] = {
            "n": len(d_data),
            "brier": brier,
            "longshot_bias": longshot_bias,
            "favorite_bias": favorite_bias,
            "mean_oi": float(d_data["open_interest"].mean()),
            "mean_volume": float(d_data["volume"].mean()),
        }

    return results


def plot_favorite_longshot(
    df: pd.DataFrame,
    micro_results: dict,
    output_dir: str,
):
    """Plot calibration curves overall and by microstructure tercile."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    os.makedirs(output_dir, exist_ok=True)

    # Panel 1: Overall calibration curve
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    # Overall calibration
    ax = axes[0]
    cal = compute_calibration_curve(df, n_bins=10, min_bin_count=3)
    if len(cal) > 0:
        ax.plot(cal["mean_implied"], cal["mean_realized"], "bo-", markersize=8, label="Markets")
        ax.plot([0, 1], [0, 1], "k--", alpha=0.5, label="Perfect calibration")
        # Show bias as shaded region
        ax.fill_between(cal["mean_implied"], cal["mean_realized"], cal["mean_implied"],
                        alpha=0.2, color="red", label="Bias")
        ax.set_xlabel("Implied Probability")
        ax.set_ylabel("Actual Frequency")
        ax.set_title(f"Overall Calibration (n={len(df)})")
        ax.legend()
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.grid(True, alpha=0.3)

    # Panel 2: Calibration by OI tercile
    ax = axes[1]
    if "open_interest" in micro_results:
        colors = {"low": "red", "medium": "orange", "high": "green"}
        for tercile in ["low", "medium", "high"]:
            t_data = micro_results["open_interest"]["terciles"].get(tercile, {})
            cal_data = t_data.get("calibration", [])
            if cal_data:
                cal_df = pd.DataFrame(cal_data)
                ax.plot(cal_df["mean_implied"], cal_df["mean_realized"],
                       "o-", color=colors[tercile], markersize=6,
                       label=f"{tercile} OI (n={t_data['n']})")
        ax.plot([0, 1], [0, 1], "k--", alpha=0.5)
        ax.set_xlabel("Implied Probability")
        ax.set_ylabel("Actual Frequency")
        ax.set_title("Calibration by Open Interest")
        ax.legend()
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.grid(True, alpha=0.3)

    # Panel 3: Calibration by spread tercile
    ax = axes[2]
    if "spread" in micro_results:
        colors = {"low": "green", "medium": "orange", "high": "red"}
        for tercile in ["low", "medium", "high"]:
            t_data = micro_results["spread"]["terciles"].get(tercile, {})
            cal_data = t_data.get("calibration", [])
            if cal_data:
                cal_df = pd.DataFrame(cal_data)
                ax.plot(cal_df["mean_implied"], cal_df["mean_realized"],
                       "o-", color=colors[tercile], markersize=6,
                       label=f"{tercile} spread (n={t_data['n']})")
        ax.plot([0, 1], [0, 1], "k--", alpha=0.5)
        ax.set_xlabel("Implied Probability")
        ax.set_ylabel("Actual Frequency")
        ax.set_title("Calibration by Bid-Ask Spread")
        ax.legend()
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "favorite_longshot_calibration.png"), dpi=150)
    plt.close()
    print(f"  Saved {output_dir}/favorite_longshot_calibration.png")

    # Bias magnitude plot
    _plot_bias_by_tercile(micro_results, output_dir)


def _plot_bias_by_tercile(micro_results: dict, output_dir: str):
    """Bar chart of longshot bias magnitude by microstructure tercile."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    for i, (metric, label) in enumerate([
        ("open_interest", "Open Interest"),
        ("spread", "Bid-Ask Spread"),
        ("volume", "Trading Volume"),
    ]):
        ax = axes[i]
        if metric not in micro_results:
            continue

        terciles = micro_results[metric]["terciles"]
        labels = []
        biases = []
        for t in ["low", "medium", "high"]:
            if t in terciles and terciles[t].get("longshot_bias") is not None:
                labels.append(t)
                biases.append(terciles[t]["longshot_bias"])

        if biases:
            colors = ["#e74c3c" if b > 0 else "#2ecc71" for b in biases]
            ax.bar(labels, biases, color=colors, edgecolor="black")
            ax.axhline(0, color="black", linewidth=0.5)
            ax.set_ylabel("Longshot Bias (positive = overpriced)")
            ax.set_title(f"Bias by {label}")
            ax.grid(True, alpha=0.3, axis="y")

    plt.suptitle("Favorite-Longshot Bias × Microstructure", fontweight="bold")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "bias_by_microstructure.png"), dpi=150)
    plt.close()
    print(f"  Saved {output_dir}/bias_by_microstructure.png")
