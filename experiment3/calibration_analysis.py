"""
experiment3/calibration_analysis.py

Analyze prediction market calibration under different uncertainty regimes.
Uses exp5 market predictions + exp2 KUI uncertainty index.
"""

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import brier_score_loss
from sklearn.calibration import calibration_curve


def load_market_predictions(
    markets_path: str = "data/exp2/markets.csv",
    prices_path: str = "data/exp2/daily_prices_by_ticker.json",
) -> pd.DataFrame:
    """Load economics markets from exp2 with mid-life price as probability forecast.

    Uses price at the midpoint of each market's lifetime as the 'prediction',
    then checks calibration against the actual outcome.
    """
    import json

    df = pd.read_csv(markets_path)

    # Parse timestamps
    df["open_time"] = pd.to_datetime(df["open_time"], format="ISO8601", errors="coerce")
    df["close_time"] = pd.to_datetime(df["close_time"], format="ISO8601", errors="coerce")

    # Convert result to binary
    df["result_binary"] = (df["result"] == "yes").astype(int)

    # Load price data
    with open(prices_path) as f:
        all_prices = json.load(f)

    # For each market, extract mid-life price as the probability forecast
    mid_probs = []
    for _, row in df.iterrows():
        ticker = row["ticker"]
        if ticker not in all_prices or not all_prices[ticker]:
            mid_probs.append(np.nan)
            continue

        prices = all_prices[ticker]
        n = len(prices)
        if n < 3:
            mid_probs.append(np.nan)
            continue

        # Use price at 50% of lifetime as the forecast
        mid_idx = n // 2
        mid_price = prices[mid_idx]
        if isinstance(mid_price, (list, tuple)):
            mid_price = mid_price[1]  # (timestamp, price) format
        mid_probs.append(float(mid_price) / 100.0)

    df["market_prob"] = mid_probs
    df["market_prob"] = df["market_prob"].clip(0.01, 0.99)

    # Filter
    df = df.dropna(subset=["market_prob", "open_time", "close_time"]).reset_index(drop=True)

    return df


def load_kui(kui_path: str = "data/exp2/kui_daily.csv") -> pd.DataFrame:
    """Load KUI daily index."""
    kui = pd.read_csv(kui_path, parse_dates=["date"], index_col="date")
    return kui


def assign_uncertainty_regime(
    markets_df: pd.DataFrame,
    kui_df: pd.DataFrame,
) -> pd.DataFrame:
    """Assign each market an uncertainty regime based on KUI during its trading window.

    Returns DataFrame with added columns: mean_kui, regime_tercile, regime_binary.
    """
    df = markets_df.copy()

    # For each market, compute mean KUI during its open→close window
    mean_kuis = []
    for _, row in df.iterrows():
        open_date = row["open_time"].normalize().tz_localize(None) if row["open_time"].tzinfo else row["open_time"].normalize()
        close_date = row["close_time"].normalize().tz_localize(None) if row["close_time"].tzinfo else row["close_time"].normalize()

        kui_window = kui_df.loc[
            (kui_df.index >= open_date) & (kui_df.index <= close_date), "KUI"
        ]

        if len(kui_window) > 0:
            mean_kuis.append(kui_window.mean())
        else:
            mean_kuis.append(np.nan)

    df["mean_kui"] = mean_kuis

    # Drop markets without KUI coverage
    df = df.dropna(subset=["mean_kui"]).reset_index(drop=True)

    # Tercile split (use qcut for equal-sized bins when values cluster)
    try:
        df["regime_tercile"] = pd.qcut(
            df["mean_kui"], q=3, labels=["low", "medium", "high"], duplicates="drop"
        )
    except ValueError:
        # Fallback: binary split only
        df["regime_tercile"] = pd.cut(
            df["mean_kui"],
            bins=[-np.inf, df["mean_kui"].median(), np.inf],
            labels=["low", "high"],
        )

    # Binary split at median
    median_kui = df["mean_kui"].median()
    df["regime_binary"] = np.where(df["mean_kui"] > median_kui, "high", "low")

    return df


def compute_brier(predictions: np.ndarray, actuals: np.ndarray) -> float:
    """Compute Brier score."""
    return float(brier_score_loss(actuals, predictions))


def compute_ece(predictions: np.ndarray, actuals: np.ndarray, n_bins: int = 10) -> float:
    """Compute Expected Calibration Error."""
    bin_edges = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    total = len(predictions)

    for i in range(n_bins):
        mask = (predictions >= bin_edges[i]) & (predictions < bin_edges[i + 1])
        if mask.sum() == 0:
            continue
        bin_acc = actuals[mask].mean()
        bin_conf = predictions[mask].mean()
        ece += mask.sum() / total * abs(bin_acc - bin_conf)

    return float(ece)


def murphy_decomposition(predictions: np.ndarray, actuals: np.ndarray, n_bins: int = 10) -> dict:
    """Murphy decomposition: Brier = reliability - resolution + uncertainty.

    - Reliability (calibration error): lower is better
    - Resolution: higher means predictions are more informative (better)
    - Uncertainty: base rate variance, independent of forecaster skill

    This separates true calibration quality from base rate effects.
    """
    base_rate = actuals.mean()
    uncertainty = base_rate * (1 - base_rate)

    bin_edges = np.linspace(0, 1, n_bins + 1)
    reliability = 0.0
    resolution = 0.0
    total = len(predictions)

    for i in range(n_bins):
        mask = (predictions >= bin_edges[i]) & (predictions < bin_edges[i + 1])
        n_k = mask.sum()
        if n_k == 0:
            continue
        bin_acc = actuals[mask].mean()
        bin_conf = predictions[mask].mean()
        reliability += n_k / total * (bin_conf - bin_acc) ** 2
        resolution += n_k / total * (bin_acc - base_rate) ** 2

    brier = reliability - resolution + uncertainty
    return {
        "brier": float(brier),
        "reliability": float(reliability),
        "resolution": float(resolution),
        "uncertainty": float(uncertainty),
        "base_rate": float(base_rate),
    }


def compute_regime_calibration(df: pd.DataFrame) -> dict:
    """Compute calibration metrics split by uncertainty regime."""
    results = {}

    # Overall
    overall_murphy = murphy_decomposition(df["market_prob"].values, df["result_binary"].values)
    results["overall"] = {
        "brier": compute_brier(df["market_prob"].values, df["result_binary"].values),
        "ece": compute_ece(df["market_prob"].values, df["result_binary"].values),
        "n_markets": len(df),
        **{f"murphy_{k}": v for k, v in overall_murphy.items()},
    }

    # By tercile
    for regime in ["low", "medium", "high"]:
        subset = df[df["regime_tercile"] == regime]
        if len(subset) < 10:
            continue
        murphy = murphy_decomposition(subset["market_prob"].values, subset["result_binary"].values)
        results[f"tercile_{regime}"] = {
            "brier": compute_brier(subset["market_prob"].values, subset["result_binary"].values),
            "ece": compute_ece(subset["market_prob"].values, subset["result_binary"].values),
            "n_markets": len(subset),
            "mean_kui": float(subset["mean_kui"].mean()),
            **{f"murphy_{k}": v for k, v in murphy.items()},
        }

    # By binary split
    for regime in ["low", "high"]:
        subset = df[df["regime_binary"] == regime]
        if len(subset) < 10:
            continue
        results[f"binary_{regime}"] = {
            "brier": compute_brier(subset["market_prob"].values, subset["result_binary"].values),
            "ece": compute_ece(subset["market_prob"].values, subset["result_binary"].values),
            "n_markets": len(subset),
            "mean_kui": float(subset["mean_kui"].mean()),
        }

    # By volume bucket × regime
    vol_bins = {"thin": (0, 50), "medium": (50, 500), "thick": (500, float("inf"))}
    for vol_name, (lo, hi) in vol_bins.items():
        for regime in ["low", "high"]:
            subset = df[(df["regime_binary"] == regime) & (df["volume"] >= lo) & (df["volume"] < hi)]
            if len(subset) < 10:
                continue
            results[f"vol_{vol_name}_regime_{regime}"] = {
                "brier": compute_brier(subset["market_prob"].values, subset["result_binary"].values),
                "n_markets": len(subset),
            }

    # Statistical test: is high-uncertainty Brier significantly different from low?
    high_df = df[df["regime_binary"] == "high"]
    low_df = df[df["regime_binary"] == "low"]
    if len(high_df) >= 10 and len(low_df) >= 10:
        # Bootstrap test for Brier score difference
        n_boot = 1000
        diffs = []
        reliability_diffs = []
        rng = np.random.default_rng(42)
        for _ in range(n_boot):
            h_idx = rng.choice(len(high_df), len(high_df), replace=True)
            l_idx = rng.choice(len(low_df), len(low_df), replace=True)
            h_brier = compute_brier(
                high_df["market_prob"].values[h_idx], high_df["result_binary"].values[h_idx]
            )
            l_brier = compute_brier(
                low_df["market_prob"].values[l_idx], low_df["result_binary"].values[l_idx]
            )
            diffs.append(h_brier - l_brier)
            # Also bootstrap reliability (pure calibration) difference
            h_murphy = murphy_decomposition(
                high_df["market_prob"].values[h_idx], high_df["result_binary"].values[h_idx]
            )
            l_murphy = murphy_decomposition(
                low_df["market_prob"].values[l_idx], low_df["result_binary"].values[l_idx]
            )
            reliability_diffs.append(h_murphy["reliability"] - l_murphy["reliability"])

        diffs = np.array(diffs)
        reliability_diffs = np.array(reliability_diffs)
        results["statistical_test"] = {
            "test": "bootstrap_brier_difference",
            "mean_diff": float(diffs.mean()),
            "ci_lower": float(np.percentile(diffs, 2.5)),
            "ci_upper": float(np.percentile(diffs, 97.5)),
            "significant": bool(np.percentile(diffs, 2.5) > 0 or np.percentile(diffs, 97.5) < 0),
            "direction": "high_worse" if diffs.mean() > 0 else "low_worse",
        }

        # Base rate control: test if RELIABILITY (not Brier) differs
        # This isolates true calibration from base rate effects
        results["base_rate_control"] = {
            "test": "bootstrap_reliability_difference",
            "high_base_rate": float(high_df["result_binary"].mean()),
            "low_base_rate": float(low_df["result_binary"].mean()),
            "base_rate_difference": float(high_df["result_binary"].mean() - low_df["result_binary"].mean()),
            "reliability_diff_mean": float(reliability_diffs.mean()),
            "reliability_diff_ci_lower": float(np.percentile(reliability_diffs, 2.5)),
            "reliability_diff_ci_upper": float(np.percentile(reliability_diffs, 97.5)),
            "reliability_significant": bool(
                np.percentile(reliability_diffs, 2.5) > 0 or np.percentile(reliability_diffs, 97.5) < 0
            ),
            "interpretation": (
                "If base rates differ but reliability does not, the Brier difference "
                "is driven by base rate composition, not calibration quality."
            ),
        }

    # By domain × regime
    for domain in df["domain"].unique():
        for regime in ["low", "high"]:
            subset = df[(df["domain"] == domain) & (df["regime_binary"] == regime)]
            if len(subset) < 10:
                continue
            results[f"domain_{domain}_regime_{regime}"] = {
                "brier": compute_brier(subset["market_prob"].values, subset["result_binary"].values),
                "n_markets": len(subset),
            }

    return results


def plot_calibration_curves(df: pd.DataFrame, output_dir: str = "data/exp3/plots"):
    """Generate calibration curve plots split by uncertainty regime."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import os

    os.makedirs(output_dir, exist_ok=True)

    # 1. Calibration curves by regime
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    for regime, color in [("low", "blue"), ("medium", "gray"), ("high", "red")]:
        subset = df[df["regime_tercile"] == regime]
        if len(subset) < 20:
            continue
        prob_true, prob_pred = calibration_curve(
            subset["result_binary"], subset["market_prob"], n_bins=8, strategy="uniform"
        )
        axes[0].plot(prob_pred, prob_true, "o-", color=color, label=f"{regime} KUI (n={len(subset)})")

    axes[0].plot([0, 1], [0, 1], "k--", alpha=0.5, label="Perfect")
    axes[0].set_xlabel("Mean Predicted Probability")
    axes[0].set_ylabel("Fraction of Positives")
    axes[0].set_title("Calibration by Uncertainty Regime (Terciles)")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # 2. Brier score bar chart
    regimes = []
    briers = []
    counts = []
    for regime in ["low", "medium", "high"]:
        subset = df[df["regime_tercile"] == regime]
        if len(subset) < 10:
            continue
        regimes.append(f"{regime}\n(n={len(subset)})")
        briers.append(compute_brier(subset["market_prob"].values, subset["result_binary"].values))
        counts.append(len(subset))

    colors = ["blue", "gray", "red"][: len(regimes)]
    axes[1].bar(regimes, briers, color=colors, alpha=0.7)
    axes[1].set_ylabel("Brier Score (lower = better calibrated)")
    axes[1].set_title("Market Calibration by Uncertainty Regime")
    axes[1].grid(True, alpha=0.3, axis="y")

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "calibration_by_regime.png"), dpi=150)
    plt.close()
    print(f"  Saved {output_dir}/calibration_by_regime.png")

    # 3. Domain breakdown
    domains = df["domain"].value_counts()
    domains = domains[domains >= 20].index.tolist()

    if len(domains) >= 2:
        fig, ax = plt.subplots(figsize=(10, 6))
        x = np.arange(len(domains))
        width = 0.35

        low_briers = []
        high_briers = []
        for domain in domains:
            for regime, brier_list in [("low", low_briers), ("high", high_briers)]:
                subset = df[(df["domain"] == domain) & (df["regime_binary"] == regime)]
                if len(subset) >= 10:
                    brier_list.append(compute_brier(subset["market_prob"].values, subset["result_binary"].values))
                else:
                    brier_list.append(0)

        ax.bar(x - width / 2, low_briers, width, label="Low Uncertainty", color="blue", alpha=0.7)
        ax.bar(x + width / 2, high_briers, width, label="High Uncertainty", color="red", alpha=0.7)
        ax.set_xticks(x)
        ax.set_xticklabels(domains)
        ax.set_ylabel("Brier Score")
        ax.set_title("Calibration by Domain and Uncertainty Regime")
        ax.legend()
        ax.grid(True, alpha=0.3, axis="y")

        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "calibration_by_domain.png"), dpi=150)
        plt.close()
        print(f"  Saved {output_dir}/calibration_by_domain.png")


def investigate_fiscal_anomaly(df: pd.DataFrame) -> dict:
    """Deep-dive into the fiscal policy calibration anomaly.

    Fiscal policy shows Brier 0.767 (low uncertainty) vs 0.210 (high uncertainty).
    This function investigates whether the effect is real or a small-n artifact.

    Returns dict with sample sizes, per-market breakdown, sub-type analysis,
    and bootstrap CI.
    """
    fiscal = df[df["domain"] == "fiscal_policy"].copy()
    result = {
        "n_fiscal_total": len(fiscal),
        "domains_in_data": sorted(df["domain"].unique().tolist()),
    }

    if len(fiscal) < 5:
        result["conclusion"] = "insufficient_data"
        return result

    # Split by regime
    low = fiscal[fiscal["regime_binary"] == "low"]
    high = fiscal[fiscal["regime_binary"] == "high"]
    result["n_low"] = len(low)
    result["n_high"] = len(high)

    if len(low) >= 2:
        result["brier_low"] = compute_brier(low["market_prob"].values, low["result_binary"].values)
    if len(high) >= 2:
        result["brier_high"] = compute_brier(high["market_prob"].values, high["result_binary"].values)

    # Per-market Brier scores to detect outliers
    fiscal["per_market_brier"] = (fiscal["market_prob"] - fiscal["result_binary"]) ** 2
    result["per_market_brier_stats"] = {
        "mean": float(fiscal["per_market_brier"].mean()),
        "median": float(fiscal["per_market_brier"].median()),
        "std": float(fiscal["per_market_brier"].std()),
        "max": float(fiscal["per_market_brier"].max()),
        "min": float(fiscal["per_market_brier"].min()),
    }

    # Check which series_tickers/sub-types drive the effect
    if "series_ticker" in fiscal.columns:
        sub_types = fiscal.groupby("series_ticker").agg(
            n=("result_binary", "count"),
            mean_brier=("per_market_brier", "mean"),
            pct_yes=("result_binary", "mean"),
            mean_prob=("market_prob", "mean"),
        ).sort_values("n", ascending=False)
        result["sub_types"] = sub_types.to_dict(orient="index")
    elif "ticker" in fiscal.columns:
        # Extract series prefix from ticker
        fiscal["series_prefix"] = fiscal["ticker"].str.extract(r"^([A-Z]+)")
        sub_types = fiscal.groupby("series_prefix").agg(
            n=("result_binary", "count"),
            mean_brier=("per_market_brier", "mean"),
            pct_yes=("result_binary", "mean"),
            mean_prob=("market_prob", "mean"),
        ).sort_values("n", ascending=False)
        result["sub_types"] = sub_types.to_dict(orient="index")

    # Bootstrap CI for fiscal-specific Brier difference
    if len(low) >= 5 and len(high) >= 5:
        n_boot = 1000
        diffs = []
        rng = np.random.default_rng(42)
        for _ in range(n_boot):
            h_idx = rng.choice(len(high), len(high), replace=True)
            l_idx = rng.choice(len(low), len(low), replace=True)
            h_brier = compute_brier(
                high["market_prob"].values[h_idx], high["result_binary"].values[h_idx]
            )
            l_brier = compute_brier(
                low["market_prob"].values[l_idx], low["result_binary"].values[l_idx]
            )
            diffs.append(h_brier - l_brier)

        diffs = np.array(diffs)
        result["bootstrap"] = {
            "mean_diff": float(diffs.mean()),
            "ci_lower": float(np.percentile(diffs, 2.5)),
            "ci_upper": float(np.percentile(diffs, 97.5)),
            "significant": bool(np.percentile(diffs, 2.5) > 0 or np.percentile(diffs, 97.5) < 0),
        }
    else:
        result["bootstrap"] = {"note": "insufficient_samples_for_bootstrap"}

    # Assess power
    underpowered = result["n_low"] < 15 or result["n_high"] < 15
    result["underpowered"] = underpowered
    if underpowered:
        result["conclusion"] = "underpowered"
    elif result.get("bootstrap", {}).get("significant"):
        result["conclusion"] = "significant_difference"
    else:
        result["conclusion"] = "not_significant"

    return result
