"""
experiment1/trading_simulation.py

Signal-triggered trading simulation comparing LLM-filtered
vs unfiltered vs random portfolios.
"""

import numpy as np
import pandas as pd


def temporal_split_prices(
    hourly_prices: dict[str, pd.Series],
    train_frac: float = 0.75,
) -> tuple[dict[str, pd.Series], dict[str, pd.Series]]:
    """Split hourly price series into train and test by timestamp.

    For each ticker, the first train_frac% of observations go to train,
    the rest to test.

    Returns:
        (train_prices, test_prices)
    """
    train = {}
    test = {}

    for ticker, series in hourly_prices.items():
        n = len(series)
        split_idx = int(n * train_frac)
        if split_idx < 10 or n - split_idx < 10:
            continue
        train[ticker] = series.iloc[:split_idx]
        test[ticker] = series.iloc[split_idx:]

    return train, test


def simulate_signal_triggered_trades(
    leader_series: pd.Series,
    follower_series: pd.Series,
    signal_threshold: float = 0.05,
    hold_hours: int = 24,
) -> list[dict]:
    """Execute signal-triggered trading on a single pair.

    Protocol:
    1. When leader price moves by > signal_threshold (absolute change),
       predict follower moves in same direction.
    2. Hold until follower moves by > signal_threshold/2, or timeout.
    3. Record trade outcome.

    Returns list of trade dicts.
    """
    # Align on common timestamps
    combined = pd.concat(
        [leader_series.rename("leader"), follower_series.rename("follower")],
        axis=1,
    ).dropna()

    if len(combined) < 5:
        return []

    trades = []
    leader_vals = combined["leader"].values
    follower_vals = combined["follower"].values
    timestamps = combined.index

    i = 1
    while i < len(combined):
        leader_change = leader_vals[i] - leader_vals[i - 1]

        if abs(leader_change) > signal_threshold:
            # Signal triggered — enter position
            entry_time = timestamps[i]
            entry_price = follower_vals[i]
            direction = 1.0 if leader_change > 0 else -1.0

            # Hold until exit condition
            exit_idx = None
            for j in range(i + 1, min(i + hold_hours + 1, len(combined))):
                follower_change = follower_vals[j] - entry_price
                if abs(follower_change) > signal_threshold / 2:
                    exit_idx = j
                    break

            if exit_idx is None:
                exit_idx = min(i + hold_hours, len(combined) - 1)

            exit_price = follower_vals[exit_idx]
            pnl = direction * (exit_price - entry_price)

            trades.append({
                "entry_time": str(entry_time),
                "exit_time": str(timestamps[exit_idx]),
                "leader_signal": float(leader_change),
                "direction": float(direction),
                "entry_price": float(entry_price),
                "exit_price": float(exit_price),
                "pnl": float(pnl),
                "hold_hours": exit_idx - i,
            })

            # Skip past this trade
            i = exit_idx + 1
        else:
            i += 1

    return trades


def compute_portfolio_metrics(trades: list[dict]) -> dict:
    """Compute summary metrics for a set of trades."""
    if not trades:
        return {
            "n_trades": 0,
            "total_pnl": 0.0,
            "mean_pnl": 0.0,
            "sharpe_ratio": 0.0,
            "win_rate": 0.0,
            "avg_hold_hours": 0.0,
        }

    pnls = [t["pnl"] for t in trades]
    n_trades = len(pnls)
    total_pnl = sum(pnls)
    mean_pnl = total_pnl / n_trades
    std_pnl = np.std(pnls) if n_trades > 1 else 1.0
    sharpe = (mean_pnl / std_pnl) * np.sqrt(252) if std_pnl > 0 else 0.0
    win_rate = sum(1 for p in pnls if p > 0) / n_trades
    avg_hold = np.mean([t["hold_hours"] for t in trades])

    return {
        "n_trades": n_trades,
        "total_pnl": round(total_pnl, 6),
        "mean_pnl": round(mean_pnl, 6),
        "sharpe_ratio": round(sharpe, 4),
        "win_rate": round(win_rate, 4),
        "avg_hold_hours": round(avg_hold, 2),
    }


def run_portfolio_simulation(
    test_prices: dict[str, pd.Series],
    all_significant: pd.DataFrame,
    llm_filtered: pd.DataFrame,
    signal_threshold: float = 0.05,
    hold_hours: int = 24,
) -> dict:
    """Run the three-portfolio comparison.

    Portfolio A: All Granger-significant pairs (no LLM filtering)
    Portfolio B: LLM-filtered pairs only
    Portfolio C: Random pairs (same count as B, random entry times)
    """
    rng = np.random.RandomState(42)

    def _simulate_portfolio(pairs_df: pd.DataFrame) -> tuple[list[dict], dict]:
        all_trades = []
        for _, row in pairs_df.iterrows():
            leader = row["leader_ticker"]
            follower = row["follower_ticker"]
            if leader not in test_prices or follower not in test_prices:
                continue
            trades = simulate_signal_triggered_trades(
                test_prices[leader],
                test_prices[follower],
                signal_threshold=signal_threshold,
                hold_hours=hold_hours,
            )
            for t in trades:
                t["leader_ticker"] = leader
                t["follower_ticker"] = follower
            all_trades.extend(trades)
        metrics = compute_portfolio_metrics(all_trades)
        return all_trades, metrics

    # Portfolio A: All significant pairs
    print("  Simulating Portfolio A (all Granger-significant)...")
    trades_a, metrics_a = _simulate_portfolio(all_significant)

    # Portfolio B: LLM-filtered pairs
    approved = llm_filtered[llm_filtered.get("llm_approved", False)] if "llm_approved" in llm_filtered.columns else llm_filtered
    print("  Simulating Portfolio B (LLM-filtered)...")
    trades_b, metrics_b = _simulate_portfolio(approved)

    # Portfolio C: Random control (same number of trades as B)
    print("  Simulating Portfolio C (random control)...")
    available_tickers = list(test_prices.keys())
    n_random_pairs = len(approved) if not approved.empty else 10
    random_pairs = []
    for _ in range(n_random_pairs):
        if len(available_tickers) < 2:
            break
        idxs = rng.choice(len(available_tickers), size=2, replace=False)
        random_pairs.append({
            "leader_ticker": available_tickers[idxs[0]],
            "follower_ticker": available_tickers[idxs[1]],
        })
    random_df = pd.DataFrame(random_pairs)
    trades_c, metrics_c = _simulate_portfolio(random_df)

    results = {
        "portfolio_a_all_granger": {"metrics": metrics_a, "n_pairs": len(all_significant)},
        "portfolio_b_llm_filtered": {"metrics": metrics_b, "n_pairs": len(approved)},
        "portfolio_c_random": {"metrics": metrics_c, "n_pairs": len(random_df)},
    }

    # Print summary
    print("\n  --- Portfolio Comparison ---")
    for name, data in results.items():
        m = data["metrics"]
        print(f"  {name}: {m['n_trades']} trades, PnL={m['total_pnl']:.4f}, "
              f"Sharpe={m['sharpe_ratio']:.2f}, WinRate={m['win_rate']:.1%}")

    return results
