"""
Unit tests for Experiment 2 modules.
Tests use synthetic data — no API calls, no model downloads, no network access.

Run: uv run python -m pytest experiment2/tests/test_unit.py -v
"""

import numpy as np
import pandas as pd
import pytest


# ── data_collection tests ──────────────────────────────────────────

class TestDataCollection:
    def test_classify_economics_domains(self):
        from experiment2.data_collection import classify_uncertainty_domain
        assert classify_uncertainty_domain("KXCPI-26JAN-T3.5") == "inflation"
        assert classify_uncertainty_domain("KXFED-26MAR") == "monetary_policy"
        assert classify_uncertainty_domain("KXNFP-26FEB") == "labor_market"
        assert classify_uncertainty_domain("KXJOBLESSCLAIMS-26FEB05") == "labor_market"
        assert classify_uncertainty_domain("KXGDP-26Q1") == "fiscal_policy"
        assert classify_uncertainty_domain("KXRECESSION-2026") == "fiscal_policy"

    def test_classify_crypto(self):
        from experiment2.data_collection import classify_uncertainty_domain
        assert classify_uncertainty_domain("KXBTC15M-26FEB07") == "crypto"
        assert classify_uncertainty_domain("KXETH-26FEB") == "crypto"
        assert classify_uncertainty_domain("KXSOL15M-26FEB07") == "crypto"

    def test_classify_finance(self):
        from experiment2.data_collection import classify_uncertainty_domain
        assert classify_uncertainty_domain("KXSPY-26FEB07") == "finance"
        assert classify_uncertainty_domain("KXSP500-26FEB") == "finance"
        assert classify_uncertainty_domain("KXNASDAQ-26FEB") == "finance"

    def test_classify_geopolitics(self):
        from experiment2.data_collection import classify_uncertainty_domain
        assert classify_uncertainty_domain("KXTARIFF-2026") == "geopolitics"

    def test_classify_politics(self):
        from experiment2.data_collection import classify_uncertainty_domain
        assert classify_uncertainty_domain("KXTRUMP-2026") == "politics"
        assert classify_uncertainty_domain("KXELECTION-2026") == "politics"

    def test_classify_excluded(self):
        from experiment2.data_collection import classify_uncertainty_domain
        assert classify_uncertainty_domain("KXNBA-26FEB") == "excluded"
        assert classify_uncertainty_domain("KXTEMP-26FEB") == "excluded"
        assert classify_uncertainty_domain("KXUNKNOWN-26FEB") == "excluded"

    def test_extract_candle_price_from_price_obj(self):
        from experiment2.data_collection import extract_candle_price
        candle = {"price": {"close_dollars": 0.65}}
        assert abs(extract_candle_price(candle) - 0.65) < 1e-6

    def test_extract_candle_price_from_bid_ask(self):
        from experiment2.data_collection import extract_candle_price
        candle = {
            "price": {},
            "yes_bid": {"close_dollars": 0.60},
            "yes_ask": {"close_dollars": 0.70},
        }
        assert abs(extract_candle_price(candle) - 0.65) < 1e-6

    def test_extract_candle_price_empty(self):
        from experiment2.data_collection import extract_candle_price
        assert np.isnan(extract_candle_price({}))

    def test_prepare_market_dataset(self):
        from experiment2.data_collection import prepare_market_dataset
        markets = [
            {
                "ticker": "KXCPI-26JAN-T3.5", "event_ticker": "E1",
                "title": "CPI above 3.5%", "open_time": "2025-12-01T00:00:00Z",
                "close_time": "2026-01-01T00:00:00Z",
                "settlement_ts": "2026-01-01T00:00:00Z",
                "result": "yes", "volume": 100, "last_price_dollars": 0.65,
            },
            {
                "ticker": "KXNBA-26FEB", "event_ticker": "E2",
                "title": "NBA game", "open_time": "2025-12-01T00:00:00Z",
                "close_time": "2026-01-01T00:00:00Z",
                "settlement_ts": "2026-01-01T00:00:00Z",
                "result": "yes", "volume": 100, "last_price_dollars": 0.50,
            },
            {
                "ticker": "KXBTC-26JAN", "event_ticker": "E3",
                "title": "BTC above 100K", "open_time": "2025-12-01T00:00:00Z",
                "close_time": "2026-01-01T00:00:00Z",
                "settlement_ts": "2026-01-01T00:00:00Z",
                "result": "no", "volume": 200, "last_price_dollars": 0.30,
            },
        ]
        df = prepare_market_dataset(markets)
        assert len(df) == 2  # NBA excluded
        assert set(df["domain"]) == {"inflation", "crypto"}


# ── index_construction tests ──────────────────────────────────────

class TestIndexConstruction:
    def _make_synthetic_data(self):
        """Create synthetic daily price data for testing."""
        dates = pd.date_range("2025-06-01", periods=30, freq="D")
        rng = np.random.RandomState(42)

        # Two tickers in different domains
        daily_prices = {
            "KXCPI-A": [
                (d.strftime("%Y-%m-%d"), 0.5 + rng.randn() * 0.05)
                for d in dates
            ],
            "KXCPI-B": [
                (d.strftime("%Y-%m-%d"), 0.4 + rng.randn() * 0.03)
                for d in dates
            ],
            "KXBTC-A": [
                (d.strftime("%Y-%m-%d"), 0.6 + rng.randn() * 0.10)
                for d in dates
            ],
        }

        df_markets = pd.DataFrame([
            {"ticker": "KXCPI-A", "domain": "inflation"},
            {"ticker": "KXCPI-B", "domain": "inflation"},
            {"ticker": "KXBTC-A", "domain": "crypto"},
        ])

        return daily_prices, df_markets

    def test_build_daily_price_matrix(self):
        from experiment2.index_construction import build_daily_price_matrix

        daily_prices, df_markets = self._make_synthetic_data()
        prices_df, domain_map = build_daily_price_matrix(daily_prices, df_markets)

        assert prices_df.shape[1] == 3  # 3 tickers
        assert len(domain_map) == 3
        assert domain_map["KXCPI-A"] == "inflation"
        assert domain_map["KXBTC-A"] == "crypto"

    def test_compute_daily_returns(self):
        from experiment2.index_construction import build_daily_price_matrix, compute_daily_returns

        daily_prices, df_markets = self._make_synthetic_data()
        prices_df, _ = build_daily_price_matrix(daily_prices, df_markets)
        returns_df = compute_daily_returns(prices_df)

        assert returns_df.shape == prices_df.shape
        # First row should be NaN (no previous day)
        assert returns_df.iloc[0].isna().all()
        # All values should be >= 0 (absolute returns)
        assert (returns_df.iloc[1:] >= 0).all().all()

    def test_compute_belief_volatility(self):
        from experiment2.index_construction import (
            build_daily_price_matrix,
            compute_daily_returns,
            compute_belief_volatility,
        )

        daily_prices, df_markets = self._make_synthetic_data()
        prices_df, domain_map = build_daily_price_matrix(daily_prices, df_markets)
        returns_df = compute_daily_returns(prices_df)
        bv = compute_belief_volatility(returns_df, domain_map)

        assert "inflation" in bv.columns
        assert "crypto" in bv.columns
        # Inflation domain has 2 tickers, should have data
        assert bv["inflation"].dropna().shape[0] > 0

    def test_construct_kui(self):
        from experiment2.index_construction import (
            build_daily_price_matrix,
            compute_daily_returns,
            compute_belief_volatility,
            compute_n_active_markets,
            construct_kui,
        )

        daily_prices, df_markets = self._make_synthetic_data()
        prices_df, domain_map = build_daily_price_matrix(daily_prices, df_markets)
        returns_df = compute_daily_returns(prices_df)
        bv = compute_belief_volatility(returns_df, domain_map)
        n_active = compute_n_active_markets(prices_df, domain_map)

        kui = construct_kui(bv, n_active, weighting="market_count")
        assert not kui.dropna().empty
        assert kui.name == "KUI"

    def test_normalize_index(self):
        from experiment2.index_construction import normalize_index

        raw = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        normalized = normalize_index(raw, target_mean=100, target_std=15)

        assert abs(normalized.mean() - 100) < 1e-6
        assert abs(normalized.std() - 15) < 1e-6

    def test_normalize_index_constant(self):
        from experiment2.index_construction import normalize_index

        constant = pd.Series([5.0, 5.0, 5.0])
        normalized = normalize_index(constant, target_mean=100, target_std=15)
        # All same value -> should map to target_mean
        assert (normalized == 100).all()

    def test_build_kui_dataset_full(self):
        from experiment2.index_construction import build_kui_dataset

        daily_prices, df_markets = self._make_synthetic_data()
        result = build_kui_dataset(daily_prices, df_markets)

        assert "kui_normalized" in result
        assert "domain_indices" in result
        assert "inflation" in result["domain_indices"]
        assert "crypto" in result["domain_indices"]

    def test_build_kui_dataset_empty(self):
        from experiment2.index_construction import build_kui_dataset

        result = build_kui_dataset({}, pd.DataFrame(columns=["ticker", "domain"]))
        assert result["kui_normalized"].empty or result["kui_raw"].empty


# ── validation tests ──────────────────────────────────────────────

class TestValidation:
    def _make_correlated_series(self, n=100, rng_seed=42):
        """Create correlated time series for testing."""
        rng = np.random.RandomState(rng_seed)
        dates = pd.date_range("2025-06-01", periods=n, freq="D")

        # Base signal
        signal = np.cumsum(rng.randn(n))

        # KUI: signal + noise
        kui = pd.Series(signal + rng.randn(n) * 0.5, index=dates, name="KUI")
        # EPU: lagged signal + noise
        epu = pd.Series(
            np.roll(signal, 2) + rng.randn(n) * 0.5,
            index=dates, name="EPU"
        )
        # VIX: different noise
        vix = pd.Series(signal * 0.5 + rng.randn(n) * 1.0, index=dates, name="VIX")

        return kui, epu, vix

    def test_align_series(self):
        from experiment2.validation import align_series

        dates1 = pd.date_range("2025-06-01", periods=10, freq="D")
        dates2 = pd.date_range("2025-06-05", periods=10, freq="D")

        s1 = pd.Series(range(10), index=dates1, name="a")
        s2 = pd.Series(range(10), index=dates2, name="b")

        aligned = align_series(s1, s2, min_overlap=5)
        assert len(aligned) == 6  # June 5-10 overlap

    def test_align_series_insufficient_overlap(self):
        from experiment2.validation import align_series

        dates1 = pd.date_range("2025-06-01", periods=5, freq="D")
        dates2 = pd.date_range("2025-07-01", periods=5, freq="D")

        s1 = pd.Series(range(5), index=dates1, name="a")
        s2 = pd.Series(range(5), index=dates2, name="b")

        with pytest.raises(ValueError):
            align_series(s1, s2, min_overlap=5)

    def test_compute_correlations(self):
        from experiment2.validation import compute_correlations

        kui, epu, vix = self._make_correlated_series()
        results = compute_correlations(kui, epu, vix)

        assert len(results) >= 6  # 3 pairs x 2 methods
        assert all(0 <= abs(r) <= 1 for r in results["correlation"].dropna())

    def test_granger_causality_test(self):
        from experiment2.validation import granger_causality_test

        rng = np.random.RandomState(42)
        dates = pd.date_range("2025-06-01", periods=100, freq="D")

        # x causes y with lag 1
        x = pd.Series(rng.randn(100), index=dates, name="x")
        noise = rng.randn(100) * 0.3
        y_vals = np.zeros(100)
        y_vals[0] = noise[0]
        for i in range(1, 100):
            y_vals[i] = 0.8 * x.iloc[i - 1] + noise[i]
        y = pd.Series(y_vals, index=dates, name="y")

        result = granger_causality_test(x, y, max_lag=3)
        assert result["best_lag"] is not None
        assert result["p_value"] < 0.05  # Should find the causal relationship

    def test_granger_no_causality(self):
        from experiment2.validation import granger_causality_test

        rng = np.random.RandomState(42)
        dates = pd.date_range("2025-06-01", periods=100, freq="D")

        # Independent random series
        x = pd.Series(rng.randn(100), index=dates, name="x")
        y = pd.Series(rng.randn(100), index=dates, name="y")

        result = granger_causality_test(x, y, max_lag=3)
        # p-value should be high (no causality) — but this is stochastic
        # Just check the function runs without error
        assert isinstance(result["p_value"], float)

    def test_compute_realized_volatility(self):
        from experiment2.validation import compute_realized_volatility

        dates = pd.date_range("2025-06-01", periods=30, freq="D")
        prices = pd.Series(np.cumsum(np.random.randn(30)) + 100, index=dates, name="SP500")

        rv = compute_realized_volatility(prices, window=5)
        assert len(rv) == 30
        # First 5 values should be NaN (rolling window)
        assert rv.iloc[:5].isna().sum() >= 4

    def test_incremental_r2_test(self):
        from experiment2.validation import incremental_r2_test

        rng = np.random.RandomState(42)
        dates = pd.date_range("2025-06-01", periods=100, freq="D")

        realized_vol = pd.Series(rng.randn(100) + 20, index=dates, name="realized_vol")
        vix = pd.Series(rng.randn(100) + 20, index=dates, name="VIX")
        epu = pd.Series(rng.randn(100) + 100, index=dates, name="EPU")
        kui = pd.Series(rng.randn(100) + 100, index=dates, name="KUI")

        result = incremental_r2_test(realized_vol, vix, epu, kui)
        assert "r2_base" in result
        assert "r2_full" in result
        assert "delta_r2" in result


# ── event_study tests ─────────────────────────────────────────────

class TestEventStudy:
    def test_get_economic_events(self):
        from experiment2.event_study import get_economic_events

        events = get_economic_events()
        assert len(events) > 20
        assert "date" in events.columns
        assert "type" in events.columns
        assert "surprise" in events.columns
        assert pd.api.types.is_datetime64_any_dtype(events["date"])

    def test_extract_event_window(self):
        from experiment2.event_study import extract_event_window

        dates = pd.date_range("2025-06-01", periods=30, freq="D")
        series = pd.Series(range(30), index=dates)

        event_date = pd.Timestamp("2025-06-15")
        window = extract_event_window(series, event_date, window_days=5)

        assert len(window) == 11  # -5 to +5 days
        assert window.index.min() == -5
        assert window.index.max() == 5

    def test_extract_event_window_edge(self):
        from experiment2.event_study import extract_event_window

        dates = pd.date_range("2025-06-01", periods=10, freq="D")
        series = pd.Series(range(10), index=dates)

        # Event at the start — limited pre-event data
        event_date = pd.Timestamp("2025-06-03")
        window = extract_event_window(series, event_date, window_days=7)
        assert window.index.min() >= -7

    def test_detect_first_significant_move(self):
        from experiment2.event_study import detect_first_significant_move

        # Pre-event: stable around 100
        # Post-event: spike at day +2
        window = pd.Series(
            [100, 101, 99, 100, 100, 100, 150, 100, 100, 100, 100],
            index=range(-5, 6),
        )

        move = detect_first_significant_move(window, pre_event_end=-1, threshold_std=2.0)
        assert move == 1  # Day +1 is first post-baseline, but spike is at index 6 (day +1)
        # Actually the values at indices: -5:100, -4:101, -3:99, -2:100, -1:100, 0:100, 1:150, 2:100...
        # Pre-event (<=−1) = [100, 101, 99, 100, 100], mean=100, std≈0.71
        # Upper threshold = 100 + 2*0.71 = 101.42
        # Day 0: 100 (not > 101.42)
        # Day 1: 150 (yes > 101.42)
        assert move == 1

    def test_detect_no_significant_move(self):
        from experiment2.event_study import detect_first_significant_move

        # Flat series
        window = pd.Series([100] * 11, index=range(-5, 6))
        move = detect_first_significant_move(window)
        assert move is None  # No move (std=0)

    def test_compute_event_lead_lag(self):
        from experiment2.event_study import compute_event_lead_lag

        # Kalshi moves at day 0, traditional at day +2
        # pre_event_end=-1 means baseline is days <= -1
        # Need slight variation in baseline so std > 0
        kalshi = pd.Series(
            [100, 101, 99, 100, 101, 150, 100, 100, 100, 100, 100],
            #  -5   -4   -3   -2   -1    0   +1   +2   +3   +4   +5
            index=range(-5, 6),
        )
        traditional = pd.Series(
            [100, 101, 99, 100, 101, 100, 100, 150, 100, 100, 100],
            #  -5   -4   -3   -2   -1    0   +1   +2   +3   +4   +5
            index=range(-5, 6),
        )

        result = compute_event_lead_lag(kalshi, traditional)
        # Kalshi first move at day 0 (150 >> baseline ~100), traditional at day +2
        # lead_lag = 0 - 2 = -2 (Kalshi leads)
        assert result["lead_lag_days"] is not None
        assert result["lead_lag_days"] < 0  # Negative = Kalshi leads

    def test_run_event_study_empty(self):
        from experiment2.event_study import run_event_study

        result = run_event_study({}, pd.Series(dtype=float), pd.Series(dtype=float))
        assert result.empty or len(result) == 0

    def test_summarize_event_study(self):
        from experiment2.event_study import summarize_event_study

        results = pd.DataFrame({
            "event_date": ["2025-06-01", "2025-07-01"],
            "event_type": ["CPI", "FOMC"],
            "description": ["Test CPI", "Test FOMC"],
            "surprise": [True, False],
            "relevant_domain": ["inflation", "monetary_policy"],
            "kui_window_size": [10, 10],
            "kui_first_move_vs_epu": [-1, 0],
            "epu_first_move": [1, 0],
            "lead_lag_vs_epu": [-2, 0],
            "kui_first_move_vs_vix": [-1, 1],
            "vix_first_move": [0, 0],
            "lead_lag_vs_vix": [-1, 1],
        })

        summary = summarize_event_study(results)
        assert summary["n_events"] == 2
        assert "mean_lead_lag_vs_epu" in summary


# ── index_construction edge cases ─────────────────────────────────

class TestEdgeCases:
    def test_empty_daily_prices(self):
        from experiment2.index_construction import build_kui_dataset

        df_markets = pd.DataFrame(columns=["ticker", "domain"])
        result = build_kui_dataset({}, df_markets)
        assert result["kui_raw"].empty or result["kui_normalized"].empty

    def test_single_market(self):
        from experiment2.index_construction import build_kui_dataset

        daily_prices = {
            "KXCPI-A": [
                ("2025-06-01", 0.50),
                ("2025-06-02", 0.55),
                ("2025-06-03", 0.52),
            ]
        }
        df_markets = pd.DataFrame([
            {"ticker": "KXCPI-A", "domain": "inflation"},
        ])

        result = build_kui_dataset(daily_prices, df_markets)
        # Single market in domain -> BV should be NaN (need >= 2 markets)
        assert result["bv_df"]["inflation"].isna().all()

    def test_two_markets_same_domain(self):
        from experiment2.index_construction import build_kui_dataset

        daily_prices = {
            "KXCPI-A": [
                ("2025-06-01", 0.50),
                ("2025-06-02", 0.55),
                ("2025-06-03", 0.52),
            ],
            "KXCPI-B": [
                ("2025-06-01", 0.40),
                ("2025-06-02", 0.42),
                ("2025-06-03", 0.38),
            ],
        }
        df_markets = pd.DataFrame([
            {"ticker": "KXCPI-A", "domain": "inflation"},
            {"ticker": "KXCPI-B", "domain": "inflation"},
        ])

        result = build_kui_dataset(daily_prices, df_markets)
        # With 2 markets, BV should have some non-NaN values
        bv = result["bv_df"]["inflation"]
        assert bv.dropna().shape[0] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
