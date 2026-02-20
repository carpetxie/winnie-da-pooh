"""
experiment6/microstructure.py

Extract and analyze market microstructure signals from cached hourly candles:
- Bid-ask spread (disagreement measure)
- Open interest dynamics (conviction/informed trading)
- OHLC intraday range (information arrival)
- Per-candle volume (activity clustering)

No API calls required. Uses cached data from experiment2.
"""

import os
import json
import glob
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from tqdm import tqdm

CANDLE_DIR = "data/exp2/raw/candles"
DATA_DIR = "data/exp6"


def load_all_candles(candle_dir: str = CANDLE_DIR) -> dict[str, list[dict]]:
    """Load all cached hourly candle files.

    Returns:
        {ticker: [candle_dicts]} for all available tickers.
    """
    files = sorted(glob.glob(os.path.join(candle_dir, "*_60.json")))
    all_candles = {}
    for f in files:
        basename = os.path.basename(f)
        ticker = basename.replace("_60.json", "")
        with open(f) as fh:
            candles = json.load(fh)
        if candles:
            all_candles[ticker] = candles
    return all_candles


def extract_microstructure(candles: list[dict]) -> pd.DataFrame:
    """Extract microstructure features from a list of candle dicts.

    Returns DataFrame indexed by timestamp with columns:
        mid_price, bid, ask, spread, spread_pct, open_interest, volume,
        price_high, price_low, price_open, price_close, intraday_range
    """
    rows = []
    for c in candles:
        ts = c.get("end_period_ts")
        if ts is None:
            continue

        price_obj = c.get("price", {})
        yes_bid = c.get("yes_bid", {})
        yes_ask = c.get("yes_ask", {})

        p_close = _safe_float(price_obj.get("close_dollars"))
        p_high = _safe_float(price_obj.get("high_dollars"))
        p_low = _safe_float(price_obj.get("low_dollars"))
        p_open = _safe_float(price_obj.get("open_dollars"))

        bid_close = _safe_float(yes_bid.get("close_dollars"))
        ask_close = _safe_float(yes_ask.get("close_dollars"))

        oi = _safe_float(c.get("open_interest"))
        vol = _safe_float(c.get("volume"))

        spread = None
        spread_pct = None
        mid_price = p_close

        if bid_close is not None and ask_close is not None:
            spread = ask_close - bid_close
            if mid_price is not None and mid_price > 0.01:
                spread_pct = spread / mid_price
            elif bid_close + ask_close > 0:
                spread_pct = spread / ((bid_close + ask_close) / 2)

        intraday_range = None
        if p_high is not None and p_low is not None:
            intraday_range = p_high - p_low

        rows.append({
            "timestamp": pd.Timestamp.fromtimestamp(ts, tz=timezone.utc),
            "mid_price": mid_price,
            "bid": bid_close,
            "ask": ask_close,
            "spread": spread,
            "spread_pct": spread_pct,
            "open_interest": oi,
            "volume": vol,
            "price_high": p_high,
            "price_low": p_low,
            "price_open": p_open,
            "price_close": p_close,
            "intraday_range": intraday_range,
        })

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df = df.sort_values("timestamp").set_index("timestamp")
    return df


def build_microstructure_panel(
    all_candles: dict[str, list[dict]],
    markets_df: pd.DataFrame | None = None,
) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    """Build microstructure DataFrames for all tickers.

    Returns:
        (ticker_dfs, summary_df) where:
        - ticker_dfs: {ticker: microstructure DataFrame}
        - summary_df: one row per ticker with aggregated stats
    """
    ticker_dfs = {}
    summaries = []

    domain_lookup = {}
    if markets_df is not None:
        domain_lookup = dict(zip(markets_df["ticker"], markets_df["domain"]))

    for ticker, candles in tqdm(all_candles.items(), desc="Extracting microstructure"):
        df = extract_microstructure(candles)
        if df.empty or len(df) < 3:
            continue
        ticker_dfs[ticker] = df

        valid_spread = df["spread"].dropna()
        valid_oi = df["open_interest"].dropna()
        valid_vol = df["volume"].dropna()
        valid_range = df["intraday_range"].dropna()

        summaries.append({
            "ticker": ticker,
            "domain": domain_lookup.get(ticker, "unknown"),
            "n_candles": len(df),
            "mean_spread": valid_spread.mean() if len(valid_spread) > 0 else None,
            "median_spread": valid_spread.median() if len(valid_spread) > 0 else None,
            "mean_spread_pct": df["spread_pct"].dropna().mean() if df["spread_pct"].notna().any() else None,
            "mean_oi": valid_oi.mean() if len(valid_oi) > 0 else None,
            "max_oi": valid_oi.max() if len(valid_oi) > 0 else None,
            "oi_growth": (valid_oi.iloc[-1] - valid_oi.iloc[0]) if len(valid_oi) >= 2 else None,
            "mean_volume": valid_vol.mean() if len(valid_vol) > 0 else None,
            "total_volume": valid_vol.sum() if len(valid_vol) > 0 else None,
            "mean_range": valid_range.mean() if len(valid_range) > 0 else None,
            "max_range": valid_range.max() if len(valid_range) > 0 else None,
        })

    summary_df = pd.DataFrame(summaries)
    return ticker_dfs, summary_df


def analyze_spread_as_uncertainty(
    ticker_dfs: dict[str, pd.DataFrame],
    markets_df: pd.DataFrame,
) -> dict:
    """Analyze bid-ask spread as a market-level uncertainty/disagreement measure.

    Tests:
    1. Do wider spreads predict worse calibration?
    2. How does spread evolve over market lifetime?
    3. Spread correlation with KUI.
    """
    from scipy import stats

    domain_lookup = dict(zip(markets_df["ticker"], markets_df["domain"]))
    result_lookup = dict(zip(markets_df["ticker"], markets_df["result"]))

    # Per-market: average spread vs calibration error
    records = []
    for ticker, df in ticker_dfs.items():
        if ticker not in result_lookup:
            continue

        valid_spread = df["spread"].dropna()
        if len(valid_spread) < 5:
            continue

        result = 1 if result_lookup[ticker] == "yes" else 0
        mid_life_idx = len(df) // 2
        mid_price = df["mid_price"].iloc[mid_life_idx]
        if mid_price is None or np.isnan(mid_price):
            continue

        brier = (mid_price - result) ** 2

        records.append({
            "ticker": ticker,
            "domain": domain_lookup.get(ticker, "unknown"),
            "mean_spread": float(valid_spread.mean()),
            "median_spread": float(valid_spread.median()),
            "mid_price": float(mid_price),
            "result": result,
            "brier": float(brier),
        })

    if len(records) < 10:
        return {"error": "insufficient_data", "n_markets": len(records)}

    records_df = pd.DataFrame(records)

    # Split by spread terciles
    try:
        records_df["spread_tercile"] = pd.qcut(
            records_df["mean_spread"], q=3, labels=["narrow", "medium", "wide"],
            duplicates="drop",
        )
    except ValueError:
        records_df["spread_tercile"] = pd.cut(
            records_df["mean_spread"],
            bins=[-np.inf, records_df["mean_spread"].median(), np.inf],
            labels=["narrow", "wide"],
        )

    # Brier by spread tercile
    tercile_stats = {}
    for t in records_df["spread_tercile"].dropna().unique():
        subset = records_df[records_df["spread_tercile"] == t]
        tercile_stats[str(t)] = {
            "mean_brier": float(subset["brier"].mean()),
            "median_brier": float(subset["brier"].median()),
            "mean_spread": float(subset["mean_spread"].mean()),
            "n": len(subset),
        }

    # Correlation: spread vs brier
    r, p = stats.spearmanr(records_df["mean_spread"], records_df["brier"])

    return {
        "n_markets": len(records_df),
        "spread_tercile_calibration": tercile_stats,
        "spread_brier_correlation": {
            "spearman_r": float(r),
            "p_value": float(p),
            "significant": p < 0.05,
        },
        "overall_stats": {
            "mean_spread": float(records_df["mean_spread"].mean()),
            "mean_brier": float(records_df["brier"].mean()),
        },
    }


def analyze_oi_dynamics(
    ticker_dfs: dict[str, pd.DataFrame],
    markets_df: pd.DataFrame,
) -> dict:
    """Analyze open interest as a conviction/informed trading signal.

    Tests:
    1. Does OI growth predict correct outcomes? (informed trading)
    2. Do markets with higher peak OI have better calibration?
    3. OI growth rate before vs after mid-life.
    """
    from scipy import stats

    result_lookup = dict(zip(markets_df["ticker"], markets_df["result"]))
    domain_lookup = dict(zip(markets_df["ticker"], markets_df["domain"]))

    records = []
    for ticker, df in ticker_dfs.items():
        if ticker not in result_lookup:
            continue

        valid_oi = df["open_interest"].dropna()
        if len(valid_oi) < 10:
            continue

        result = 1 if result_lookup[ticker] == "yes" else 0
        mid_idx = len(df) // 2
        mid_price = df["mid_price"].iloc[mid_idx]
        if mid_price is None or np.isnan(mid_price):
            continue

        # OI growth: first half vs second half
        first_half_oi = valid_oi.iloc[: len(valid_oi) // 2]
        second_half_oi = valid_oi.iloc[len(valid_oi) // 2 :]

        oi_growth_total = float(valid_oi.iloc[-1] - valid_oi.iloc[0])
        oi_growth_first = float(first_half_oi.iloc[-1] - first_half_oi.iloc[0]) if len(first_half_oi) >= 2 else 0
        oi_growth_second = float(second_half_oi.iloc[-1] - second_half_oi.iloc[0]) if len(second_half_oi) >= 2 else 0

        brier = (mid_price - result) ** 2

        # Did price move toward the correct answer after mid-life?
        final_price = df["mid_price"].dropna().iloc[-1] if df["mid_price"].dropna().shape[0] > 0 else mid_price
        price_move_correct = abs(final_price - result) < abs(mid_price - result)

        records.append({
            "ticker": ticker,
            "domain": domain_lookup.get(ticker, "unknown"),
            "result": result,
            "mid_price": float(mid_price),
            "brier": float(brier),
            "peak_oi": float(valid_oi.max()),
            "mean_oi": float(valid_oi.mean()),
            "oi_growth_total": oi_growth_total,
            "oi_growth_first_half": oi_growth_first,
            "oi_growth_second_half": oi_growth_second,
            "oi_acceleration": oi_growth_second - oi_growth_first,
            "price_move_correct": price_move_correct,
        })

    if len(records) < 10:
        return {"error": "insufficient_data", "n_markets": len(records)}

    records_df = pd.DataFrame(records)

    # Test 1: OI growth vs calibration
    r_oi_brier, p_oi_brier = stats.spearmanr(records_df["peak_oi"], records_df["brier"])

    # Test 2: OI acceleration (late-life OI surge) vs correct price convergence
    accel_pos = records_df[records_df["oi_acceleration"] > 0]
    accel_neg = records_df[records_df["oi_acceleration"] <= 0]

    convergence_test = None
    if len(accel_pos) >= 5 and len(accel_neg) >= 5:
        # Markets with accelerating OI vs decelerating: do they converge to truth more?
        rate_accel = accel_pos["price_move_correct"].mean()
        rate_decel = accel_neg["price_move_correct"].mean()
        # Fisher exact test
        table = np.array([
            [accel_pos["price_move_correct"].sum(), (~accel_pos["price_move_correct"]).sum()],
            [accel_neg["price_move_correct"].sum(), (~accel_neg["price_move_correct"]).sum()],
        ])
        _, fisher_p = stats.fisher_exact(table)
        convergence_test = {
            "oi_accelerating_convergence_rate": float(rate_accel),
            "oi_decelerating_convergence_rate": float(rate_decel),
            "n_accelerating": len(accel_pos),
            "n_decelerating": len(accel_neg),
            "fisher_exact_p": float(fisher_p),
            "significant": fisher_p < 0.05,
        }

    # Test 3: Peak OI terciles vs brier
    try:
        records_df["oi_tercile"] = pd.qcut(
            records_df["peak_oi"], q=3, labels=["low", "medium", "high"],
            duplicates="drop",
        )
    except ValueError:
        records_df["oi_tercile"] = pd.cut(
            records_df["peak_oi"],
            bins=[-np.inf, records_df["peak_oi"].median(), np.inf],
            labels=["low", "high"],
        )

    oi_tercile_stats = {}
    for t in records_df["oi_tercile"].dropna().unique():
        subset = records_df[records_df["oi_tercile"] == t]
        oi_tercile_stats[str(t)] = {
            "mean_brier": float(subset["brier"].mean()),
            "mean_peak_oi": float(subset["peak_oi"].mean()),
            "n": len(subset),
        }

    return {
        "n_markets": len(records_df),
        "peak_oi_brier_correlation": {
            "spearman_r": float(r_oi_brier),
            "p_value": float(p_oi_brier),
            "significant": p_oi_brier < 0.05,
        },
        "oi_tercile_calibration": oi_tercile_stats,
        "oi_convergence_test": convergence_test,
        "overall_stats": {
            "mean_peak_oi": float(records_df["peak_oi"].mean()),
            "median_peak_oi": float(records_df["peak_oi"].median()),
            "mean_oi_acceleration": float(records_df["oi_acceleration"].mean()),
        },
    }


def analyze_event_microstructure(
    ticker_dfs: dict[str, pd.DataFrame],
    markets_df: pd.DataFrame,
    events: pd.DataFrame,
    window_hours: int = 48,
) -> dict:
    """Analyze microstructure around economic events.

    For each event:
    1. Track spread changes (pre vs post)
    2. Track OI changes (pre vs post)
    3. Track range changes (pre vs post)
    """
    from scipy import stats

    domain_lookup = dict(zip(markets_df["ticker"], markets_df["domain"]))

    pre_spreads = []
    post_spreads = []
    pre_ranges = []
    post_ranges = []
    pre_oi_changes = []
    post_oi_changes = []
    event_records = []

    for _, event in events.iterrows():
        event_ts = pd.Timestamp(event["date"], tz=timezone.utc)
        event_type = event.get("event_type", "unknown")
        event_date_str = str(event["date"])[:10]

        # Collect microstructure from all active markets around this event
        for ticker, df in ticker_dfs.items():
            domain = domain_lookup.get(ticker, "unknown")
            if domain in ("crypto", "politics", "unknown"):
                continue

            # Window
            pre_mask = (df.index >= event_ts - pd.Timedelta(hours=window_hours)) & (df.index < event_ts)
            post_mask = (df.index >= event_ts) & (df.index < event_ts + pd.Timedelta(hours=window_hours))

            pre = df.loc[pre_mask]
            post = df.loc[post_mask]

            if len(pre) < 3 or len(post) < 3:
                continue

            pre_s = pre["spread"].dropna()
            post_s = post["spread"].dropna()
            pre_r = pre["intraday_range"].dropna()
            post_r = post["intraday_range"].dropna()

            if len(pre_s) > 0 and len(post_s) > 0:
                pre_spreads.append(pre_s.mean())
                post_spreads.append(post_s.mean())

            if len(pre_r) > 0 and len(post_r) > 0:
                pre_ranges.append(pre_r.mean())
                post_ranges.append(post_r.mean())

            # Record per-pair data for event-level clustering
            if len(pre_s) > 0 and len(post_s) > 0 and len(pre_r) > 0 and len(post_r) > 0:
                event_records.append({
                    "event_date": event_date_str,
                    "ticker": ticker,
                    "pre_spread": pre_s.mean(),
                    "post_spread": post_s.mean(),
                    "pre_range": pre_r.mean(),
                    "post_range": post_r.mean(),
                })

    results = {
        "n_event_market_pairs": len(pre_spreads),
    }

    # --- Naive (pair-level) tests ---
    if len(pre_spreads) >= 10:
        spread_stat, spread_p = stats.wilcoxon(
            np.array(pre_spreads) - np.array(post_spreads),
            alternative="two-sided",
        )
        results["spread_change"] = {
            "pre_mean": float(np.mean(pre_spreads)),
            "post_mean": float(np.mean(post_spreads)),
            "change_pct": float((np.mean(post_spreads) - np.mean(pre_spreads)) / np.mean(pre_spreads) * 100),
            "wilcoxon_p": float(spread_p),
            "significant": spread_p < 0.05,
            "direction": "wider_after" if np.mean(post_spreads) > np.mean(pre_spreads) else "narrower_after",
            "note": "Naive: treats each event-market pair as independent",
        }

    if len(pre_ranges) >= 10:
        range_stat, range_p = stats.wilcoxon(
            np.array(pre_ranges) - np.array(post_ranges),
            alternative="two-sided",
        )
        results["range_change"] = {
            "pre_mean": float(np.mean(pre_ranges)),
            "post_mean": float(np.mean(post_ranges)),
            "change_pct": float((np.mean(post_ranges) - np.mean(pre_ranges)) / np.mean(pre_ranges) * 100) if np.mean(pre_ranges) > 0 else 0,
            "wilcoxon_p": float(range_p),
            "significant": range_p < 0.05,
            "direction": "wider_after" if np.mean(post_ranges) > np.mean(pre_ranges) else "narrower_after",
            "note": "Naive: treats each event-market pair as independent",
        }

    # --- Event-level clustered tests ---
    # Collapse to event-level means: one observation per event date
    if len(event_records) >= 10:
        rec_df = pd.DataFrame(event_records)
        event_level = rec_df.groupby("event_date").agg(
            pre_spread_mean=("pre_spread", "mean"),
            post_spread_mean=("post_spread", "mean"),
            pre_range_mean=("pre_range", "mean"),
            post_range_mean=("post_range", "mean"),
            n_markets=("ticker", "count"),
        ).reset_index()

        n_events = len(event_level)
        results["n_independent_events"] = n_events

        if n_events >= 10:
            spread_diffs = event_level["pre_spread_mean"].values - event_level["post_spread_mean"].values
            cl_spread_stat, cl_spread_p = stats.wilcoxon(spread_diffs, alternative="two-sided")
            results["spread_change_clustered"] = {
                "n_events": n_events,
                "pre_mean": float(event_level["pre_spread_mean"].mean()),
                "post_mean": float(event_level["post_spread_mean"].mean()),
                "change_pct": float(
                    (event_level["post_spread_mean"].mean() - event_level["pre_spread_mean"].mean())
                    / event_level["pre_spread_mean"].mean() * 100
                ),
                "wilcoxon_p": float(cl_spread_p),
                "significant": cl_spread_p < 0.05,
                "direction": "wider_after" if event_level["post_spread_mean"].mean() > event_level["pre_spread_mean"].mean() else "narrower_after",
                "note": "Event-level clustering: one observation per event date",
            }

            range_diffs = event_level["pre_range_mean"].values - event_level["post_range_mean"].values
            cl_range_stat, cl_range_p = stats.wilcoxon(range_diffs, alternative="two-sided")
            results["range_change_clustered"] = {
                "n_events": n_events,
                "pre_mean": float(event_level["pre_range_mean"].mean()),
                "post_mean": float(event_level["post_range_mean"].mean()),
                "change_pct": float(
                    (event_level["post_range_mean"].mean() - event_level["pre_range_mean"].mean())
                    / event_level["pre_range_mean"].mean() * 100
                ) if event_level["pre_range_mean"].mean() > 0 else 0,
                "wilcoxon_p": float(cl_range_p),
                "significant": cl_range_p < 0.05,
                "direction": "wider_after" if event_level["post_range_mean"].mean() > event_level["pre_range_mean"].mean() else "narrower_after",
                "note": "Event-level clustering: one observation per event date",
            }

    return results


def analyze_spread_vs_kui(
    ticker_dfs: dict[str, pd.DataFrame],
    markets_df: pd.DataFrame,
    kui_path: str = "data/exp2/kui_daily.csv",
) -> dict:
    """Compare aggregate bid-ask spread to KUI as competing uncertainty measures.

    Builds a daily aggregate spread index and correlates with KUI.
    """
    from scipy import stats

    if not os.path.exists(kui_path):
        return {"error": "kui_daily.csv not found"}

    kui = pd.read_csv(kui_path, parse_dates=["date"], index_col="date")
    domain_lookup = dict(zip(markets_df["ticker"], markets_df["domain"]))

    # Build daily spread index: average spread across all active markets per day
    daily_records = {}
    for ticker, df in ticker_dfs.items():
        domain = domain_lookup.get(ticker, "unknown")
        if domain in ("crypto", "politics", "unknown"):
            continue

        for ts, row in df.iterrows():
            day = ts.normalize().tz_localize(None)
            if row["spread"] is not None and not np.isnan(row["spread"]):
                if day not in daily_records:
                    daily_records[day] = []
                daily_records[day].append(row["spread"])

    if not daily_records:
        return {"error": "no_spread_data"}

    daily_spread = pd.Series(
        {d: np.mean(spreads) for d, spreads in daily_records.items()},
        name="daily_spread",
    ).sort_index()

    daily_count = pd.Series(
        {d: len(spreads) for d, spreads in daily_records.items()},
        name="n_markets",
    ).sort_index()

    # Align with KUI
    combined = pd.DataFrame({
        "spread": daily_spread,
        "n_markets": daily_count,
        "KUI": kui["KUI"],
    }).dropna()

    if len(combined) < 20:
        return {"error": "insufficient_overlap", "n_days": len(combined)}

    r_pearson, p_pearson = stats.pearsonr(combined["spread"], combined["KUI"])
    r_spearman, p_spearman = stats.spearmanr(combined["spread"], combined["KUI"])

    return {
        "n_days": len(combined),
        "pearson_r": float(r_pearson),
        "pearson_p": float(p_pearson),
        "spearman_r": float(r_spearman),
        "spearman_p": float(p_spearman),
        "spread_mean": float(combined["spread"].mean()),
        "spread_std": float(combined["spread"].std()),
        "kui_mean": float(combined["KUI"].mean()),
        "mean_active_markets": float(combined["n_markets"].mean()),
    }


def plot_microstructure(
    ticker_dfs: dict[str, pd.DataFrame],
    summary_df: pd.DataFrame,
    output_dir: str = "data/exp6/plots",
):
    """Generate microstructure visualization plots."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    os.makedirs(output_dir, exist_ok=True)

    # 1. Spread distribution by domain
    econ_domains = {"inflation", "monetary_policy", "labor_market", "fiscal_policy"}
    econ_summary = summary_df[summary_df["domain"].isin(econ_domains)].copy()

    if len(econ_summary) > 0:
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))

        # Spread by domain
        for domain in sorted(econ_domains):
            subset = econ_summary[econ_summary["domain"] == domain]
            if len(subset) > 0:
                axes[0].hist(subset["mean_spread"].dropna(), bins=20, alpha=0.5, label=domain)
        axes[0].set_xlabel("Mean Bid-Ask Spread ($)")
        axes[0].set_ylabel("Count")
        axes[0].set_title("Spread Distribution by Domain")
        axes[0].legend(fontsize=8)

        # OI by domain
        for domain in sorted(econ_domains):
            subset = econ_summary[econ_summary["domain"] == domain]
            if len(subset) > 0:
                vals = subset["max_oi"].dropna()
                if len(vals) > 0:
                    axes[1].hist(np.log10(vals.clip(lower=1)), bins=20, alpha=0.5, label=domain)
        axes[1].set_xlabel("log10(Peak Open Interest)")
        axes[1].set_ylabel("Count")
        axes[1].set_title("Open Interest by Domain")
        axes[1].legend(fontsize=8)

        # Range by domain
        for domain in sorted(econ_domains):
            subset = econ_summary[econ_summary["domain"] == domain]
            if len(subset) > 0:
                axes[2].hist(subset["mean_range"].dropna(), bins=20, alpha=0.5, label=domain)
        axes[2].set_xlabel("Mean Intraday Range ($)")
        axes[2].set_ylabel("Count")
        axes[2].set_title("Intraday Price Range by Domain")
        axes[2].legend(fontsize=8)

        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "microstructure_by_domain.png"), dpi=150)
        plt.close()

    # 2. Spread vs Brier scatter (if we have the data)
    print(f"  Saved plots to {output_dir}/")


def _safe_float(val) -> float | None:
    if val is None:
        return None
    try:
        f = float(val)
        return f if not np.isnan(f) else None
    except (ValueError, TypeError):
        return None
