"""
experiment1/granger_pipeline.py

Run pairwise Granger causality tests on all concurrent market pairs
and apply Bonferroni correction for multiple comparisons.

Methodology notes:
- Series are differenced (returns) before Granger testing to ensure stationarity.
  Raw price levels are non-stationary and produce spurious Granger results.
- ADF test is used as a sanity check; if differenced series is still non-stationary,
  the pair is skipped.
- F-stat overflow guards are in experiment2/validation.py.
"""

import os
import numpy as np
import pandas as pd
from tqdm import tqdm
from statsmodels.tsa.stattools import adfuller

from experiment2.validation import granger_causality_test

DATA_DIR = "data/exp1"


def _ensure_stationary(series: pd.Series, max_diffs: int = 2) -> pd.Series | None:
    """Difference series until stationary (ADF p < 0.05). Returns None if can't achieve it."""
    s = series.dropna()
    for _ in range(max_diffs + 1):
        if len(s) < 30:
            return None
        try:
            adf_p = adfuller(s, maxlag=min(12, len(s) // 3), autolag="AIC")[1]
        except Exception:
            return None
        if adf_p < 0.05:
            return s
        s = s.diff().dropna()
    return None


def run_pairwise_granger(
    hourly_prices: dict[str, pd.Series],
    pairs: list[tuple[str, str]],
    market_df: pd.DataFrame,
    max_lag: int = 24,
    min_overlap: int = 48,
) -> pd.DataFrame:
    """Run Granger causality test for each pair in BOTH directions.

    For each pair (A, B):
      - Test A -> B (does A's past improve prediction of B?)
      - Test B -> A (does B's past improve prediction of A?)

    Args:
        hourly_prices: {ticker: pd.Series} with hourly prices
        pairs: List of (ticker_A, ticker_B) tuples
        market_df: Market metadata for domain lookup
        max_lag: Maximum lag in hours to test
        min_overlap: Minimum overlapping observations

    Returns:
        DataFrame with leader_ticker, follower_ticker, best_lag, f_stat, p_value, etc.
    """
    # Build domain lookup
    domain_lookup = dict(zip(market_df["ticker"], market_df["domain"]))
    title_lookup = dict(zip(market_df["ticker"], market_df["title"]))

    results = []
    skipped = 0

    for ticker_a, ticker_b in tqdm(pairs, desc="Granger tests"):
        if ticker_a not in hourly_prices or ticker_b not in hourly_prices:
            skipped += 1
            continue

        series_a = hourly_prices[ticker_a]
        series_b = hourly_prices[ticker_b]

        # Align on common timestamps
        combined = pd.concat([series_a.rename("a"), series_b.rename("b")], axis=1).dropna()
        if len(combined) < min_overlap:
            skipped += 1
            continue

        # Difference to ensure stationarity (critical for valid Granger causality)
        a_stat = _ensure_stationary(combined["a"])
        b_stat = _ensure_stationary(combined["b"])
        if a_stat is None or b_stat is None:
            skipped += 1
            continue

        # Re-align after differencing (may have lost first row)
        stat_combined = pd.concat([a_stat.rename("a"), b_stat.rename("b")], axis=1).dropna()
        if len(stat_combined) < min_overlap:
            skipped += 1
            continue

        # Test A -> B
        result_ab = granger_causality_test(stat_combined["a"], stat_combined["b"], max_lag=max_lag)
        if result_ab["best_lag"] is not None:
            results.append({
                "leader_ticker": ticker_a,
                "follower_ticker": ticker_b,
                "leader_domain": domain_lookup.get(ticker_a, "unknown"),
                "follower_domain": domain_lookup.get(ticker_b, "unknown"),
                "leader_title": title_lookup.get(ticker_a, ""),
                "follower_title": title_lookup.get(ticker_b, ""),
                "best_lag": result_ab["best_lag"],
                "f_stat": result_ab["f_stat"],
                "p_value": result_ab["p_value"],
                "n_obs": result_ab["n_obs"],
            })

        # Test B -> A
        result_ba = granger_causality_test(stat_combined["b"], stat_combined["a"], max_lag=max_lag)
        if result_ba["best_lag"] is not None:
            results.append({
                "leader_ticker": ticker_b,
                "follower_ticker": ticker_a,
                "leader_domain": domain_lookup.get(ticker_b, "unknown"),
                "follower_domain": domain_lookup.get(ticker_a, "unknown"),
                "leader_title": title_lookup.get(ticker_b, ""),
                "follower_title": title_lookup.get(ticker_a, ""),
                "best_lag": result_ba["best_lag"],
                "f_stat": result_ba["f_stat"],
                "p_value": result_ba["p_value"],
                "n_obs": result_ba["n_obs"],
            })

    print(f"  Completed {len(results)} directional tests (skipped {skipped} pairs)")
    return pd.DataFrame(results)


def apply_bonferroni_correction(
    results: pd.DataFrame,
    alpha: float = 0.01,
) -> pd.DataFrame:
    """Apply Bonferroni correction for multiple comparisons.

    Args:
        results: Granger test results with p_value column
        alpha: Significance level after correction

    Returns:
        DataFrame filtered to significant pairs only
    """
    if results.empty:
        return results

    n_tests = len(results)
    results = results.copy()
    results["n_tests"] = n_tests
    results["adjusted_p"] = (results["p_value"] * n_tests).clip(upper=1.0)
    results["significant"] = results["adjusted_p"] < alpha

    significant = results[results["significant"]].copy()
    significant = significant.sort_values("adjusted_p")

    print(f"  Bonferroni correction: {len(significant)}/{n_tests} pairs significant at α={alpha}")
    return significant


def run_granger_stage(
    hourly_prices: dict[str, pd.Series],
    pairs: list[tuple[str, str]],
    market_df: pd.DataFrame,
    max_lag: int = 24,
    alpha: float = 0.01,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Full Stage 1 pipeline: Granger + Bonferroni.

    Returns:
        (all_results, significant_results)
    """
    all_results = run_pairwise_granger(hourly_prices, pairs, market_df, max_lag=max_lag)

    # Save all results
    os.makedirs(DATA_DIR, exist_ok=True)
    all_path = os.path.join(DATA_DIR, "granger_results.csv")
    all_results.to_csv(all_path, index=False)
    print(f"  Saved all results to {all_path}")

    # Apply Bonferroni
    significant = apply_bonferroni_correction(all_results, alpha=alpha)
    sig_path = os.path.join(DATA_DIR, "granger_significant.csv")
    significant.to_csv(sig_path, index=False)
    print(f"  Saved significant pairs to {sig_path}")

    return all_results, significant
