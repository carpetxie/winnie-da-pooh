"""
experiment2/validation.py

Validate the Kalshi Uncertainty Index (KUI) against traditional
uncertainty indicators: VIX and Baker-Bloom-Davis EPU Index.

Tests:
1. Correlation analysis (Pearson, Spearman)
2. Granger causality (both directions)
3. Incremental R² (does KUI add predictive power beyond VIX + EPU?)
"""

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats


def align_series(*series_list, min_overlap: int = 20) -> pd.DataFrame:
    """Align multiple time series on common dates, dropping NaN rows.

    Args:
        *series_list: pd.Series objects with DatetimeIndex
        min_overlap: Minimum number of overlapping observations required

    Returns:
        DataFrame with aligned series as columns

    Raises:
        ValueError: If fewer than min_overlap dates overlap
    """
    combined = pd.concat(series_list, axis=1)
    combined = combined.dropna()

    if len(combined) < min_overlap:
        raise ValueError(
            f"Only {len(combined)} overlapping dates (need {min_overlap}). "
            f"Series lengths: {[len(s.dropna()) for s in series_list]}"
        )

    return combined


def compute_correlations(
    kui: pd.Series, epu: pd.Series, vix: pd.Series
) -> pd.DataFrame:
    """Compute pairwise correlations between KUI, EPU, and VIX.

    Returns DataFrame with correlation type, pair, value, and p-value.
    """
    results = []

    pairs = [
        ("KUI", "EPU", kui, epu),
        ("KUI", "VIX", kui, vix),
        ("EPU", "VIX", epu, vix),
    ]

    for name_a, name_b, series_a, series_b in pairs:
        try:
            aligned = align_series(
                series_a.rename(name_a),
                series_b.rename(name_b),
                min_overlap=10,
            )

            # Pearson
            r_pearson, p_pearson = scipy_stats.pearsonr(
                aligned[name_a], aligned[name_b]
            )
            results.append({
                "pair": f"{name_a}-{name_b}",
                "method": "pearson",
                "correlation": round(r_pearson, 4),
                "p_value": round(p_pearson, 6),
                "n_obs": len(aligned),
            })

            # Spearman
            r_spearman, p_spearman = scipy_stats.spearmanr(
                aligned[name_a], aligned[name_b]
            )
            results.append({
                "pair": f"{name_a}-{name_b}",
                "method": "spearman",
                "correlation": round(r_spearman, 4),
                "p_value": round(p_spearman, 6),
                "n_obs": len(aligned),
            })

        except ValueError as e:
            results.append({
                "pair": f"{name_a}-{name_b}",
                "method": "pearson",
                "correlation": np.nan,
                "p_value": np.nan,
                "n_obs": 0,
            })

    return pd.DataFrame(results)


def granger_causality_test(
    x: pd.Series, y: pd.Series, max_lag: int = 5
) -> dict:
    """Test if x Granger-causes y (does x's past improve prediction of y?).

    Uses an F-test comparing:
        Restricted: y(t) = a0 + a1*y(t-1) + ... + ap*y(t-p)
        Unrestricted: y(t) = a0 + a1*y(t-1) + ... + ap*y(t-p) + b1*x(t-1) + ... + bp*x(t-p)

    Args:
        x: Potential "cause" series
        y: Potential "effect" series
        max_lag: Maximum lag to test

    Returns:
        Dict with best_lag, f_stat, p_value, significant
    """
    try:
        aligned = align_series(x.rename("x"), y.rename("y"), min_overlap=max_lag + 20)
    except ValueError:
        return {
            "best_lag": None,
            "f_stat": np.nan,
            "p_value": np.nan,
            "significant": False,
            "n_obs": 0,
        }

    x_vals = aligned["x"].values
    y_vals = aligned["y"].values
    n = len(y_vals)

    best_result = {"best_lag": None, "f_stat": 0, "p_value": 1.0, "significant": False, "n_obs": n}

    for lag in range(1, max_lag + 1):
        if n <= 2 * lag + 2:
            continue

        # Build lagged matrices
        y_target = y_vals[lag:]
        n_obs = len(y_target)

        # Restricted model: y lags only
        X_restricted = np.column_stack([
            y_vals[lag - i - 1: n - i - 1] for i in range(lag)
        ])
        X_restricted = np.column_stack([np.ones(n_obs), X_restricted])

        # Unrestricted model: y lags + x lags
        X_unrestricted = np.column_stack([
            X_restricted,
            *[x_vals[lag - i - 1: n - i - 1] for i in range(lag)]
        ])

        # OLS for both models
        try:
            # Restricted
            beta_r, rss_r, _, _ = np.linalg.lstsq(X_restricted, y_target, rcond=None)
            resid_r = y_target - X_restricted @ beta_r
            rss_r = np.sum(resid_r ** 2)

            # Unrestricted
            beta_u, rss_u, _, _ = np.linalg.lstsq(X_unrestricted, y_target, rcond=None)
            resid_u = y_target - X_unrestricted @ beta_u
            rss_u = np.sum(resid_u ** 2)

            # F-test
            df1 = lag  # Number of added x-lag parameters
            df2 = n_obs - X_unrestricted.shape[1]

            if df2 <= 0 or rss_u <= 0:
                continue

            # Guard against F-stat overflow from near-zero residuals
            # (overfitting when lags ≈ n_obs)
            if rss_u < 1e-12 or rss_r < 1e-12:
                continue
            if rss_r < rss_u:
                # Unrestricted model is worse — no Granger causality
                continue

            f_stat = ((rss_r - rss_u) / df1) / (rss_u / df2)

            # Reject absurd F-stats (numerical artifact)
            if not np.isfinite(f_stat) or f_stat > 1e6:
                continue

            p_value = 1 - scipy_stats.f.cdf(f_stat, df1, df2)

            if p_value < best_result["p_value"]:
                best_result = {
                    "best_lag": lag,
                    "f_stat": round(float(f_stat), 4),
                    "p_value": round(float(p_value), 6),
                    "significant": p_value < 0.05,
                    "n_obs": n_obs,
                }

        except np.linalg.LinAlgError:
            continue

    return best_result


def run_granger_tests(
    kui: pd.Series, epu: pd.Series, vix: pd.Series, max_lag: int = 5
) -> pd.DataFrame:
    """Run Granger causality tests in all relevant directions.

    Tests:
        KUI -> EPU (does KUI lead EPU?)
        KUI -> VIX (does KUI lead VIX?)
        EPU -> KUI (does EPU lead KUI?)
        VIX -> KUI (does VIX lead KUI?)
    """
    tests = [
        ("KUI -> EPU", kui, epu),
        ("KUI -> VIX", kui, vix),
        ("EPU -> KUI", epu, kui),
        ("VIX -> KUI", vix, kui),
        ("EPU -> VIX", epu, vix),
        ("VIX -> EPU", vix, epu),
    ]

    results = []
    for name, x, y in tests:
        result = granger_causality_test(x, y, max_lag=max_lag)
        result["test"] = name
        results.append(result)

    return pd.DataFrame(results)


def incremental_r2_test(
    realized_vol: pd.Series,
    vix: pd.Series,
    epu: pd.Series,
    kui: pd.Series,
    forward_days: int = 5,
) -> dict:
    """Test whether KUI adds incremental predictive power for realized volatility.

    Model:
        RealizedVol(t+forward_days) = b0 + b1*VIX(t) + b2*EPU(t) + b3*KUI(t) + e

    Compares R² of full model vs model without KUI.

    Args:
        realized_vol: Realized volatility of S&P 500 (5-day rolling std of returns)
        vix: VIX daily
        epu: EPU daily
        kui: KUI daily
        forward_days: Days ahead to predict

    Returns:
        Dict with r2_base, r2_full, delta_r2, f_stat, p_value
    """
    try:
        aligned = align_series(
            realized_vol.rename("realized_vol"),
            vix.rename("VIX"),
            epu.rename("EPU"),
            kui.rename("KUI"),
            min_overlap=forward_days + 20,
        )
    except ValueError as e:
        return {
            "r2_base": np.nan,
            "r2_full": np.nan,
            "delta_r2": np.nan,
            "f_stat": np.nan,
            "p_value": np.nan,
            "n_obs": 0,
            "error": str(e),
        }

    # Forward-shift realized_vol
    y = aligned["realized_vol"].shift(-forward_days).dropna()
    X = aligned.loc[y.index, ["VIX", "EPU", "KUI"]]

    # Drop any remaining NaN
    valid = y.notna() & X.notna().all(axis=1)
    y = y[valid].values
    X = X[valid].values
    n = len(y)

    if n < 10:
        return {
            "r2_base": np.nan, "r2_full": np.nan, "delta_r2": np.nan,
            "f_stat": np.nan, "p_value": np.nan, "n_obs": n,
        }

    # Base model: VIX + EPU only
    X_base = np.column_stack([np.ones(n), X[:, 0], X[:, 1]])  # VIX, EPU
    X_full = np.column_stack([np.ones(n), X])  # VIX, EPU, KUI

    # OLS
    beta_base, _, _, _ = np.linalg.lstsq(X_base, y, rcond=None)
    resid_base = y - X_base @ beta_base
    rss_base = np.sum(resid_base ** 2)

    beta_full, _, _, _ = np.linalg.lstsq(X_full, y, rcond=None)
    resid_full = y - X_full @ beta_full
    rss_full = np.sum(resid_full ** 2)

    # Total sum of squares
    tss = np.sum((y - y.mean()) ** 2)

    if tss == 0:
        return {
            "r2_base": np.nan, "r2_full": np.nan, "delta_r2": np.nan,
            "f_stat": np.nan, "p_value": np.nan, "n_obs": n,
        }

    r2_base = 1 - rss_base / tss
    r2_full = 1 - rss_full / tss
    delta_r2 = r2_full - r2_base

    # F-test for adding KUI
    df1 = 1  # One additional parameter (KUI)
    df2 = n - X_full.shape[1]

    if df2 <= 0 or rss_full <= 0:
        return {
            "r2_base": round(r2_base, 6),
            "r2_full": round(r2_full, 6),
            "delta_r2": round(delta_r2, 6),
            "f_stat": np.nan,
            "p_value": np.nan,
            "n_obs": n,
        }

    f_stat = ((rss_base - rss_full) / df1) / (rss_full / df2)
    p_value = 1 - scipy_stats.f.cdf(f_stat, df1, df2)

    return {
        "r2_base": round(float(r2_base), 6),
        "r2_full": round(float(r2_full), 6),
        "delta_r2": round(float(delta_r2), 6),
        "f_stat": round(float(f_stat), 4),
        "p_value": round(float(p_value), 6),
        "n_obs": n,
    }


def detect_shock_regime(
    kui: pd.Series,
    window: int = 20,
    threshold_std: float = 2.0,
) -> pd.Series:
    """Detect shock regimes based on KUI z-score exceeding threshold.

    Computes rolling z-score of KUI over `window` days.
    Returns boolean Series: True = shock regime day.

    Args:
        kui: KUI daily time series
        window: Rolling window in days for baseline stats
        threshold_std: Z-score threshold for shock classification
    """
    rolling_mean = kui.rolling(window, min_periods=max(window // 2, 5)).mean()
    rolling_std = kui.rolling(window, min_periods=max(window // 2, 5)).std()

    # Avoid division by zero
    rolling_std = rolling_std.replace(0, np.nan)

    z_score = (kui - rolling_mean) / rolling_std
    shock = z_score.abs() > threshold_std

    return shock.fillna(False).astype(bool)


def regime_conditional_granger(
    x: pd.Series,
    y: pd.Series,
    regime: pd.Series,
    max_lag: int = 5,
) -> dict:
    """Run Granger causality separately in shock and normal regimes.

    Splits x and y into contiguous blocks where regime is True/False.
    Runs granger_causality_test() on each regime separately.

    Returns dict with shock and normal Granger test results.
    """
    # Align all three series
    try:
        aligned = align_series(
            x.rename("x"), y.rename("y"), regime.rename("regime").astype(float),
            min_overlap=max_lag + 10,
        )
    except ValueError as e:
        return {
            "shock_result": {"error": str(e)},
            "normal_result": {"error": str(e)},
            "n_shock_days": 0,
            "n_normal_days": 0,
        }

    shock_mask = aligned["regime"] > 0.5

    # Shock regime
    shock_x = aligned.loc[shock_mask, "x"]
    shock_y = aligned.loc[shock_mask, "y"]
    n_shock = len(shock_x)

    if n_shock >= max_lag + 10:
        shock_result = granger_causality_test(shock_x, shock_y, max_lag=max_lag)
    else:
        shock_result = {"error": f"Insufficient shock observations ({n_shock})", "n_obs": n_shock}

    # Normal regime
    normal_x = aligned.loc[~shock_mask, "x"]
    normal_y = aligned.loc[~shock_mask, "y"]
    n_normal = len(normal_x)

    if n_normal >= max_lag + 10:
        normal_result = granger_causality_test(normal_x, normal_y, max_lag=max_lag)
    else:
        normal_result = {"error": f"Insufficient normal observations ({n_normal})", "n_obs": n_normal}

    return {
        "shock_result": shock_result,
        "normal_result": normal_result,
        "n_shock_days": n_shock,
        "n_normal_days": n_normal,
    }


def regime_conditional_incremental_r2(
    realized_vol: pd.Series,
    vix: pd.Series,
    epu: pd.Series,
    kui: pd.Series,
    regime: pd.Series,
    forward_days: int = 5,
) -> dict:
    """Run incremental R² test separately for shock and normal regimes.

    Returns dict with separate R² values for each regime.
    """
    # Align all series
    try:
        aligned = align_series(
            realized_vol.rename("realized_vol"),
            vix.rename("VIX"),
            epu.rename("EPU"),
            kui.rename("KUI"),
            regime.rename("regime").astype(float),
            min_overlap=forward_days + 10,
        )
    except ValueError as e:
        return {"error": str(e)}

    shock_mask = aligned["regime"] > 0.5

    results = {}
    for label, mask in [("shock", shock_mask), ("normal", ~shock_mask)]:
        subset = aligned[mask]
        if len(subset) < forward_days + 10:
            results[f"{label}_r2_base"] = np.nan
            results[f"{label}_r2_full"] = np.nan
            results[f"{label}_delta_r2"] = np.nan
            results[f"{label}_p_value"] = np.nan
            results[f"{label}_n_obs"] = len(subset)
            continue

        r2 = incremental_r2_test(
            subset["realized_vol"],
            subset["VIX"],
            subset["EPU"],
            subset["KUI"],
            forward_days=forward_days,
        )
        results[f"{label}_r2_base"] = r2.get("r2_base")
        results[f"{label}_r2_full"] = r2.get("r2_full")
        results[f"{label}_delta_r2"] = r2.get("delta_r2")
        results[f"{label}_p_value"] = r2.get("p_value")
        results[f"{label}_n_obs"] = r2.get("n_obs", len(subset))

    return results


def compute_realized_volatility(
    sp500_prices: pd.Series, window: int = 5
) -> pd.Series:
    """Compute realized volatility from S&P 500 daily prices.

    RealizedVol = rolling std of daily log returns.

    Args:
        sp500_prices: Daily S&P 500 close prices
        window: Rolling window in days

    Returns:
        Series of realized volatility
    """
    log_returns = np.log(sp500_prices / sp500_prices.shift(1))
    realized_vol = log_returns.rolling(window).std() * np.sqrt(252)  # Annualized
    realized_vol.name = "realized_vol"
    return realized_vol
