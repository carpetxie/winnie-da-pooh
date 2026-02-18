"""
Unit tests for Experiment 5 modules.
Tests use synthetic data — no API calls or model downloads.

Run: uv run python -m pytest experiment5/tests/test_unit.py -v
"""

import os
import json
import tempfile
import numpy as np
import pandas as pd
import pytest


# ── data_collection tests ──────────────────────────────────────────

class TestDataCollection:
    def test_extract_domain_economics(self):
        from experiment5.data_collection import extract_domain
        assert extract_domain("KXCPI-26JAN-T3.5") == "economics"
        assert extract_domain("KXNFP-26FEB") == "economics"
        assert extract_domain("KXFED-26MAR") == "economics"
        assert extract_domain("KXJOBLESSCLAIMS-26FEB05") == "economics"

    def test_extract_domain_crypto(self):
        from experiment5.data_collection import extract_domain
        assert extract_domain("KXBTC15M-26FEB07") == "crypto"
        assert extract_domain("KXETH15M-26FEB07") == "crypto"
        assert extract_domain("KXSOL15M-26FEB07") == "crypto"

    def test_extract_domain_sports(self):
        from experiment5.data_collection import extract_domain
        assert extract_domain("KXNCAAMBGAME-26FEB07") == "basketball"
        assert extract_domain("KXNHLPTS-26FEB03") == "hockey"
        assert extract_domain("KXATPMATCH-26FEB06") == "tennis"

    def test_extract_domain_esports(self):
        from experiment5.data_collection import extract_domain
        assert extract_domain("KXMVESPORTSMULTIGAMEEXTENDED-S2026") == "esports"

    def test_extract_domain_unknown(self):
        from experiment5.data_collection import extract_domain
        assert extract_domain("KXUNKNOWN-26FEB") == "other"

    def test_extract_text_title_only(self):
        from experiment5.data_collection import extract_text
        row = {"title": "BTC price up?", "rules_primary": ""}
        assert extract_text(row) == "BTC price up?"

    def test_extract_text_with_rules(self):
        from experiment5.data_collection import extract_text
        row = {"title": "BTC price up?", "rules_primary": "If BTC goes up..."}
        assert extract_text(row) == "BTC price up? | If BTC goes up..."

    def test_extract_result_binary(self):
        from experiment5.data_collection import extract_result_binary
        assert extract_result_binary({"result": "yes"}) == 1
        assert extract_result_binary({"result": "no"}) == 0
        assert extract_result_binary({"result": "scalar"}) == -1

    def test_prepare_dataset_filters_scalars(self):
        from experiment5.data_collection import prepare_dataset
        markets = [
            {"ticker": "KXCPI-A", "event_ticker": "EV1", "title": "CPI above 3%",
             "rules_primary": "", "result": "yes", "volume": 100,
             "settlement_ts": "2026-01-01T00:00:00Z", "last_price_dollars": 0.65,
             "open_time": "2025-12-01T00:00:00Z", "close_time": "2026-01-01T00:00:00Z"},
            {"ticker": "KXCPI-B", "event_ticker": "EV2", "title": "CPI above 4%",
             "rules_primary": "", "result": "scalar", "volume": 50,
             "settlement_ts": "2026-01-02T00:00:00Z", "last_price_dollars": 0.30,
             "open_time": "2025-12-01T00:00:00Z", "close_time": "2026-01-02T00:00:00Z"},
            {"ticker": "KXNFP-A", "event_ticker": "EV3", "title": "NFP above 200K",
             "rules_primary": "", "result": "no", "volume": 200,
             "settlement_ts": "2026-01-03T00:00:00Z", "last_price_dollars": 0.40,
             "open_time": "2025-12-01T00:00:00Z", "close_time": "2026-01-03T00:00:00Z"},
        ]
        df = prepare_dataset(markets)
        assert len(df) == 2  # scalar market filtered out
        assert set(df["result_binary"]) == {0, 1}

    def test_prepare_dataset_temporal_split(self):
        from experiment5.data_collection import prepare_dataset
        markets = []
        for i in range(10):
            markets.append({
                "ticker": f"KXTEST-{i}", "event_ticker": f"EV{i}",
                "title": f"Test market {i}", "rules_primary": "",
                "result": "yes" if i % 2 == 0 else "no",
                "volume": 100, "last_price_dollars": 0.5,
                "settlement_ts": f"2026-01-{i+1:02d}T00:00:00Z",
                "open_time": f"2025-12-{i+1:02d}T00:00:00Z",
                "close_time": f"2026-01-{i+1:02d}T00:00:00Z",
            })
        df = prepare_dataset(markets)
        assert (df["split"] == "train").sum() == 8
        assert (df["split"] == "test").sum() == 2


# ── embeddings tests ───────────────────────────────────────────────

class TestEmbeddings:
    def test_cosine_similarity(self):
        from experiment5.embeddings import compute_cosine_similarity
        a = np.array([1.0, 0.0, 0.0])
        b = np.array([1.0, 0.0, 0.0])
        assert abs(compute_cosine_similarity(a, b) - 1.0) < 1e-6

    def test_cosine_similarity_orthogonal(self):
        from experiment5.embeddings import compute_cosine_similarity
        a = np.array([1.0, 0.0])
        b = np.array([0.0, 1.0])
        assert abs(compute_cosine_similarity(a, b)) < 1e-6

    def test_pairwise_similarity_shape(self):
        from experiment5.embeddings import pairwise_cosine_similarity
        emb = np.random.randn(5, 10).astype(np.float32)
        emb = emb / np.linalg.norm(emb, axis=1, keepdims=True)
        sim = pairwise_cosine_similarity(emb)
        assert sim.shape == (5, 5)
        # Diagonal should be ~1.0
        np.testing.assert_allclose(np.diag(sim), 1.0, atol=1e-5)


# ── clustering tests ───────────────────────────────────────────────

class TestClustering:
    def _make_clustered_data(self, n_per_cluster=50, n_clusters=3):
        """Generate synthetic clustered data."""
        rng = np.random.RandomState(42)
        coords = []
        outcomes = []
        domains = []
        domain_names = ["economics", "crypto", "sports"]

        for i in range(n_clusters):
            center = rng.randn(2) * 10
            pts = center + rng.randn(n_per_cluster, 2) * 0.5
            coords.append(pts)
            # Each cluster has biased outcomes
            outcome_prob = 0.2 + i * 0.3  # 0.2, 0.5, 0.8
            outcomes.extend(rng.binomial(1, outcome_prob, n_per_cluster))
            domains.extend([domain_names[i]] * n_per_cluster)

        coords = np.vstack(coords)
        return coords, np.array(outcomes), domains

    def test_run_clustering_finds_clusters(self):
        from experiment5.clustering import run_clustering
        coords, _, _ = self._make_clustered_data()
        labels = run_clustering(coords, min_cluster_size=10, min_samples=5)
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        assert n_clusters >= 2, f"Expected at least 2 clusters, got {n_clusters}"

    def test_compute_cluster_stats(self):
        from experiment5.clustering import compute_cluster_stats
        coords, outcomes, domains = self._make_clustered_data()

        df = pd.DataFrame({
            "result_binary": outcomes,
            "domain": domains,
            "volume": np.random.randint(0, 1000, len(outcomes)),
            "title": [f"Market {i}" for i in range(len(outcomes))],
        })
        labels = np.array([0] * 50 + [1] * 50 + [2] * 50)

        stats = compute_cluster_stats(df, labels)
        assert len(stats) == 3
        assert "yes_rate" in stats.columns
        assert "domain_count" in stats.columns

    def test_permutation_test(self):
        from experiment5.clustering import permutation_test_cluster_outcomes
        rng = np.random.RandomState(42)

        # Create dataset where cluster 0 has biased outcomes (90% YES)
        # but overall dataset is 50/50. Cluster must be SUBSET of data.
        cluster_outcomes = [1] * 45 + [0] * 5  # 50 points, 90% YES
        other_outcomes = [0] * 45 + [1] * 5    # 50 points, 10% YES
        df = pd.DataFrame({
            "result_binary": np.array(cluster_outcomes + other_outcomes),
            "domain": ["test"] * 100,
        })
        labels = np.array([0] * 50 + [-1] * 50)  # Cluster 0 = first 50, rest = noise

        results = permutation_test_cluster_outcomes(df, labels, n_permutations=500)
        assert len(results) == 1
        # A 90% YES rate cluster in a 50% base rate dataset should be significant
        assert results.iloc[0]["p_value"] < 0.05

    def test_dimensionality_reduction_pca(self):
        from experiment5.clustering import run_dimensionality_reduction
        embeddings = np.random.randn(50, 100).astype(np.float32)

        with tempfile.TemporaryDirectory() as tmpdir:
            import experiment5.clustering as mod
            old_dir = mod.DATA_DIR
            mod.DATA_DIR = tmpdir

            coords = run_dimensionality_reduction(embeddings, method="pca")
            assert coords.shape == (50, 2)

            mod.DATA_DIR = old_dir


# ── prediction tests ───────────────────────────────────────────────

class TestPrediction:
    def test_knn_predict_perfect(self):
        """k-NN on identical embeddings should return correct outcomes."""
        from experiment5.prediction import knn_predict
        # Two clusters: first 5 = YES, last 5 = NO
        train_emb = np.eye(10, dtype=np.float32)
        train_outcomes = np.array([1, 1, 1, 1, 1, 0, 0, 0, 0, 0], dtype=float)

        # Test points close to first cluster
        test_emb = np.zeros((2, 10), dtype=np.float32)
        test_emb[0, 0] = 1.0  # Close to first YES
        test_emb[1, 9] = 1.0  # Close to last NO

        preds = knn_predict(train_emb, train_outcomes, test_emb, k=3)
        assert preds[0] > 0.5  # Should predict YES
        assert preds[1] < 0.5  # Should predict NO

    def test_brier_score_perfect(self):
        from experiment5.prediction import compute_brier_score
        preds = np.array([1.0, 0.0, 1.0])
        actuals = np.array([1, 0, 1])
        assert compute_brier_score(preds, actuals) == 0.0

    def test_brier_score_worst(self):
        from experiment5.prediction import compute_brier_score
        preds = np.array([0.0, 1.0])
        actuals = np.array([1, 0])
        assert abs(compute_brier_score(preds, actuals) - 1.0) < 1e-6

    def test_baseline_random(self):
        from experiment5.prediction import baseline_random
        train_outcomes = np.array([1, 1, 0, 0, 1], dtype=float)
        preds = baseline_random(train_outcomes, 3)
        assert len(preds) == 3
        assert all(abs(p - 0.6) < 1e-6 for p in preds)

    def test_evaluate_all_baselines(self):
        from experiment5.prediction import evaluate_all_baselines

        n = 100
        rng = np.random.RandomState(42)
        df = pd.DataFrame({
            "result_binary": rng.binomial(1, 0.5, n),
            "last_price_dollars": rng.uniform(0.1, 0.9, n),
            "volume": rng.randint(0, 1000, n),
            "split": ["train"] * 80 + ["test"] * 20,
        })
        embeddings = rng.randn(n, 32).astype(np.float32)
        embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

        results = evaluate_all_baselines(df, embeddings, k_values=[3, 5])
        assert len(results) >= 3  # random, market_price, at least one knn
        assert all(0 <= r <= 1 for r in results["brier_score"])


# ── cross_domain tests ─────────────────────────────────────────────

class TestCrossDomain:
    def test_find_cross_domain_clusters(self):
        from experiment5.cross_domain import find_cross_domain_clusters

        cluster_stats = pd.DataFrame({
            "cluster_id": [0, 1, 2],
            "size": [50, 30, 20],
            "domain_count": [3, 1, 2],
            "domains": ['{"econ": 20, "crypto": 15, "sports": 15}', '{"sports": 30}', '{"econ": 10, "crypto": 10}'],
        })

        result = find_cross_domain_clusters(cluster_stats)
        assert len(result) == 2  # Clusters 0 and 2

    def test_validate_cross_domain_empty(self):
        from experiment5.cross_domain import validate_cross_domain_correlations

        df = pd.DataFrame({
            "result_binary": [1, 0, 1, 0],
            "domain": ["econ", "econ", "econ", "econ"],
        })
        labels = np.array([0, 0, 0, 0])

        result = validate_cross_domain_correlations(df, labels, n_permutations=10)
        assert len(result) == 0  # Single domain, no cross-domain clusters


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
