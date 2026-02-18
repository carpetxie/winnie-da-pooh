"""
experiment2/index_construction.py

Construct the Kalshi Uncertainty Index (KUI) from daily candlestick data.

The KUI measures belief volatility — how much prediction market prices
are moving — decomposed by economic domain.
"""

import numpy as np
import pandas as pd
from collections import defaultdict


def build_daily_price_matrix(
    daily_prices: dict, df_markets: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Convert raw candle data into a daily price matrix and a domain map.

    Args:
        daily_prices: Dict mapping ticker -> list of (date_str, price) tuples
        df_markets: Market metadata DataFrame with 'ticker' and 'domain' columns

    Returns:
        Tuple of:
        - prices_df: DataFrame with dates as index, tickers as columns, prices as values
        - domain_map: Series mapping ticker -> domain
    """
    # Build ticker -> domain mapping
    ticker_to_domain = dict(zip(df_markets["ticker"], df_markets["domain"]))

    # Collect all (date, ticker, price) records
    records = []
    for ticker, price_list in daily_prices.items():
        domain = ticker_to_domain.get(ticker, "excluded")
        if domain == "excluded":
            continue
        for date_str, price in price_list:
            records.append({
                "date": pd.to_datetime(date_str),
                "ticker": ticker,
                "price": price,
            })

    if not records:
        empty = pd.DataFrame(columns=["dummy"])
        empty.index.name = "date"
        return empty, pd.Series(dtype=str)

    records_df = pd.DataFrame(records)

    # Pivot to price matrix: rows=dates, columns=tickers
    prices_df = records_df.pivot_table(
        index="date", columns="ticker", values="price", aggfunc="last"
    )
    prices_df = prices_df.sort_index()

    # Domain map for tickers that have price data
    domain_map = pd.Series({
        t: ticker_to_domain.get(t, "excluded")
        for t in prices_df.columns
    })

    return prices_df, domain_map


def compute_daily_returns(prices_df: pd.DataFrame, pct: bool = True) -> pd.DataFrame:
    """Compute daily absolute price changes for each market.

    Args:
        prices_df: Daily price matrix
        pct: If True, use percentage returns (|Δp/p|) instead of absolute (|Δp|).
             Clips prices to [0.02, 0.98] before dividing to avoid division-by-zero
             near prediction market boundaries.

    Returns DataFrame of same shape with |Δp| or |Δp/p|.
    """
    if pct:
        clipped = prices_df.clip(lower=0.02, upper=0.98)
        return (prices_df.diff() / clipped.shift(1)).abs()
    return prices_df.diff().abs()


def compute_belief_volatility(
    returns_df: pd.DataFrame,
    domain_map: pd.Series,
    volume_map: pd.Series = None,
) -> pd.DataFrame:
    """Compute daily belief volatility (BV) per domain.

    BV_domain(t) = weighted mean of |Δp_i(t)| for active markets i in domain.
    If volume_map is provided, weights by log(1 + volume); otherwise equal weight.

    Args:
        returns_df: Daily absolute price changes (from compute_daily_returns)
        domain_map: Series mapping ticker -> domain
        volume_map: Optional Series mapping ticker -> total volume (for weighting)

    Returns:
        DataFrame with dates as index, domains as columns, BV as values
    """
    domains = sorted(domain_map.unique())
    bv_data = {}

    for domain in domains:
        if domain == "excluded":
            continue
        domain_tickers = domain_map[domain_map == domain].index.tolist()
        domain_tickers = [t for t in domain_tickers if t in returns_df.columns]

        if not domain_tickers:
            continue

        domain_returns = returns_df[domain_tickers]
        n_active = domain_returns.notna().sum(axis=1)

        if volume_map is not None:
            # Volume-weighted mean: use log(1+volume) as weight
            weights = np.array([
                np.log1p(volume_map.get(t, 0)) for t in domain_tickers
            ])
            if weights.sum() > 0:
                weights = weights / weights.sum()
                bv = (domain_returns * weights).sum(axis=1) / domain_returns.notna().dot(weights).clip(lower=1e-10)
            else:
                bv = domain_returns.mean(axis=1)
        else:
            bv = domain_returns.mean(axis=1)

        bv[n_active < 2] = np.nan
        bv_data[domain] = bv

    return pd.DataFrame(bv_data)


def compute_cross_market_dispersion(
    returns_df: pd.DataFrame, domain_map: pd.Series
) -> pd.DataFrame:
    """Compute daily cross-market dispersion per domain.

    Dispersion = std(Δp_i(t)) across markets in domain.
    High dispersion = markets disagree on direction.

    Returns:
        DataFrame with dates as index, domains as columns
    """
    domains = sorted(domain_map.unique())
    disp_data = {}

    for domain in domains:
        if domain == "excluded":
            continue
        domain_tickers = domain_map[domain_map == domain].index.tolist()
        domain_tickers = [t for t in domain_tickers if t in returns_df.columns]

        if not domain_tickers:
            continue

        domain_returns = returns_df[domain_tickers]
        n_active = domain_returns.notna().sum(axis=1)
        disp = domain_returns.std(axis=1)
        disp[n_active < 3] = np.nan
        disp_data[domain] = disp

    return pd.DataFrame(disp_data)


def compute_n_active_markets(
    prices_df: pd.DataFrame, domain_map: pd.Series
) -> pd.DataFrame:
    """Count number of active (non-NaN) markets per domain per day."""
    domains = sorted(domain_map.unique())
    counts = {}

    for domain in domains:
        if domain == "excluded":
            continue
        domain_tickers = domain_map[domain_map == domain].index.tolist()
        domain_tickers = [t for t in domain_tickers if t in prices_df.columns]
        if domain_tickers:
            counts[domain] = prices_df[domain_tickers].notna().sum(axis=1)

    return pd.DataFrame(counts)


def construct_kui(
    bv_df: pd.DataFrame,
    n_active_df: pd.DataFrame = None,
    weighting: str = "equal",
) -> pd.Series:
    """Construct the aggregate Kalshi Uncertainty Index.

    Args:
        bv_df: Belief volatility per domain (from compute_belief_volatility)
        n_active_df: Optional number of active markets per domain (for weighting)
        weighting: 'equal', 'market_count', or 'domain_equal'
            - 'equal': simple mean across all domain columns
            - 'market_count': weight domains by active market count
            - 'domain_equal': equal weight per domain (same as 'equal' but
              explicitly handles missing domains by only averaging non-NaN)

    Returns:
        Series with KUI values indexed by date
    """
    if bv_df.empty:
        return pd.Series(dtype=float, name="KUI")

    if weighting == "market_count" and n_active_df is not None:
        weights = n_active_df.reindex(columns=bv_df.columns, fill_value=0)
        total_weight = weights.sum(axis=1)
        total_weight = total_weight.replace(0, np.nan)
        kui = (bv_df * weights).sum(axis=1) / total_weight
    else:
        # Equal weighting across domains (handles NaN gracefully)
        kui = bv_df.mean(axis=1)

    kui.name = "KUI"
    return kui


def normalize_index(series: pd.Series, target_mean: float = 100, target_std: float = 15) -> pd.Series:
    """Normalize a time series to have specified mean and std.

    Following the EPU convention: mean=100, std=15.
    """
    valid = series.dropna()
    if len(valid) < 2:
        return series

    current_mean = valid.mean()
    current_std = valid.std()

    if current_std == 0 or np.isnan(current_std):
        return pd.Series(target_mean, index=series.index, name=series.name)

    normalized = (series - current_mean) / current_std * target_std + target_mean
    normalized.name = series.name
    return normalized


def build_kui_dataset(
    daily_prices: dict,
    df_markets: pd.DataFrame,
) -> dict:
    """Full pipeline: build KUI and all sub-indices from raw data.

    Returns dict with:
        - 'prices_df': Daily price matrix
        - 'returns_df': Daily absolute returns
        - 'bv_df': Belief volatility per domain (raw)
        - 'dispersion_df': Cross-market dispersion per domain
        - 'n_active_df': Active market counts per domain
        - 'kui_raw': Aggregate KUI (raw)
        - 'kui_normalized': KUI normalized to mean=100
        - 'domain_indices': Dict of normalized domain sub-indices
    """
    # Build price matrix
    prices_df, domain_map = build_daily_price_matrix(daily_prices, df_markets)

    if prices_df.empty or len(domain_map) == 0:
        return {
            "prices_df": prices_df,
            "returns_df": pd.DataFrame(),
            "bv_df": pd.DataFrame(),
            "dispersion_df": pd.DataFrame(),
            "n_active_df": pd.DataFrame(),
            "kui_raw": pd.Series(dtype=float),
            "kui_normalized": pd.Series(dtype=float),
            "domain_indices": {},
        }

    # Compute metrics (percentage returns to handle scale differences)
    returns_df = compute_daily_returns(prices_df, pct=True)

    # Build volume map from market metadata if available
    volume_map = None
    if "volume" in df_markets.columns:
        volume_map = df_markets.set_index("ticker")["volume"].dropna()

    bv_df = compute_belief_volatility(returns_df, domain_map, volume_map=volume_map)
    dispersion_df = compute_cross_market_dispersion(returns_df, domain_map)
    n_active_df = compute_n_active_markets(prices_df, domain_map)

    # Construct aggregate KUI with equal domain weighting
    # (prevents high-count domains like crypto from dominating)
    kui_raw = construct_kui(bv_df, n_active_df, weighting="domain_equal")

    # Normalize
    kui_normalized = normalize_index(kui_raw)

    # Domain sub-indices (normalized)
    domain_indices = {}
    for domain in bv_df.columns:
        domain_series = bv_df[domain].copy()
        domain_series.name = f"KUI_{domain}"
        domain_indices[domain] = normalize_index(domain_series)

    return {
        "prices_df": prices_df,
        "returns_df": returns_df,
        "bv_df": bv_df,
        "dispersion_df": dispersion_df,
        "n_active_df": n_active_df,
        "kui_raw": kui_raw,
        "kui_normalized": kui_normalized,
        "domain_indices": domain_indices,
    }
