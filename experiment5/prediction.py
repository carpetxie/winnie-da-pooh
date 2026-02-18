"""
experiment5/prediction.py

k-Nearest-Neighbor prediction using embedding similarity.
Compares text-only predictor vs market price vs random baseline.
"""

import os
import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss
from scipy.spatial.distance import cdist

DATA_DIR = "data/exp5"


def knn_predict(
    train_embeddings: np.ndarray,
    train_outcomes: np.ndarray,
    test_embeddings: np.ndarray,
    k: int = 10,
) -> np.ndarray:
    """
    Predict outcomes using weighted k-NN in embedding space.

    Weight = cosine similarity (embeddings should be L2-normalized).

    Args:
        train_embeddings: (N_train, D)
        train_outcomes: (N_train,) binary outcomes
        test_embeddings: (N_test, D)
        k: Number of neighbors

    Returns:
        (N_test,) predicted probabilities
    """
    # Cosine similarity: for normalized vectors, sim = dot product
    # Use cdist for distance, convert to similarity
    similarities = test_embeddings @ train_embeddings.T  # (N_test, N_train)

    predictions = np.zeros(len(test_embeddings))

    for i in range(len(test_embeddings)):
        # Find k nearest neighbors
        sim_row = similarities[i]
        top_k_indices = np.argsort(sim_row)[-k:]  # Highest similarity
        top_k_sims = sim_row[top_k_indices]
        top_k_outcomes = train_outcomes[top_k_indices]

        # Weighted average (weight = similarity, clipped to avoid negatives)
        weights = np.clip(top_k_sims, 0.0, None)
        weight_sum = weights.sum()

        if weight_sum > 0:
            predictions[i] = np.average(top_k_outcomes, weights=weights)
        else:
            # Fallback: unweighted average
            predictions[i] = top_k_outcomes.mean()

    return predictions


def compute_brier_score(predictions: np.ndarray, actuals: np.ndarray) -> float:
    """Brier score (lower is better). Range [0, 1]."""
    return float(brier_score_loss(actuals, predictions))


def baseline_random(train_outcomes: np.ndarray, n_test: int) -> np.ndarray:
    """Random baseline: predict the training set base rate for everything."""
    base_rate = train_outcomes.mean()
    return np.full(n_test, base_rate)


def baseline_market_price(df_test: pd.DataFrame) -> np.ndarray:
    """Market price baseline: use last_price_dollars as probability."""
    prices = df_test["last_price_dollars"].values.astype(float)
    # Clip to [0.01, 0.99] to avoid extreme log-loss
    return np.clip(prices, 0.01, 0.99)


def evaluate_all_baselines(
    df: pd.DataFrame,
    embeddings: np.ndarray,
    k_values: list[int] = None,
) -> pd.DataFrame:
    """
    Evaluate k-NN predictor against baselines on test set.

    Returns:
        DataFrame with model, k, brier_score, n_samples
    """
    if k_values is None:
        k_values = [5, 10, 20]

    train_mask = df["split"] == "train"
    test_mask = df["split"] == "test"

    train_embeddings = embeddings[train_mask.values]
    test_embeddings = embeddings[test_mask.values]
    train_outcomes = df.loc[train_mask, "result_binary"].values.astype(float)
    test_outcomes = df.loc[test_mask, "result_binary"].values.astype(float)

    results = []

    # Random baseline
    random_preds = baseline_random(train_outcomes, test_mask.sum())
    random_brier = compute_brier_score(random_preds, test_outcomes)
    results.append({
        "model": "random_baseline",
        "k": None,
        "brier_score": round(random_brier, 6),
        "n_samples": len(test_outcomes),
    })
    print(f"Random baseline Brier: {random_brier:.4f}")

    # Market price baseline
    market_preds = baseline_market_price(df[test_mask])
    # Filter out zeros (markets with no price data)
    valid_price = market_preds > 0.01
    if valid_price.sum() > 0:
        market_brier = compute_brier_score(market_preds[valid_price], test_outcomes[valid_price])
        results.append({
            "model": "market_price",
            "k": None,
            "brier_score": round(market_brier, 6),
            "n_samples": int(valid_price.sum()),
        })
        print(f"Market price Brier: {market_brier:.4f} (n={valid_price.sum()})")

    # k-NN predictions
    for k in k_values:
        preds = knn_predict(train_embeddings, train_outcomes, test_embeddings, k=k)
        brier = compute_brier_score(preds, test_outcomes)
        results.append({
            "model": f"knn_k{k}",
            "k": k,
            "brier_score": round(brier, 6),
            "n_samples": len(test_outcomes),
        })
        print(f"k-NN (k={k}) Brier: {brier:.4f}")

    return pd.DataFrame(results)


def stratified_evaluation(
    df: pd.DataFrame,
    embeddings: np.ndarray,
    k: int = 10,
) -> pd.DataFrame:
    """
    Evaluate k-NN prediction stratified by market volume (thin vs thick).

    Returns:
        DataFrame with volume_bucket, model, brier_score, n_samples
    """
    train_mask = df["split"] == "train"
    test_mask = df["split"] == "test"

    train_embeddings = embeddings[train_mask.values]
    test_embeddings = embeddings[test_mask.values]
    train_outcomes = df.loc[train_mask, "result_binary"].values.astype(float)

    df_test = df[test_mask].copy()
    test_outcomes = df_test["result_binary"].values.astype(float)

    # k-NN predictions for all test
    knn_preds = knn_predict(train_embeddings, train_outcomes, test_embeddings, k=k)
    market_preds = baseline_market_price(df_test)
    random_preds = baseline_random(train_outcomes, len(df_test))

    # Volume buckets
    buckets = {
        "thin (vol < 50)": df_test["volume"] < 50,
        "medium (50-500)": (df_test["volume"] >= 50) & (df_test["volume"] < 500),
        "thick (vol >= 500)": df_test["volume"] >= 500,
    }

    results = []
    for bucket_name, bucket_mask in buckets.items():
        n = bucket_mask.sum()
        if n < 5:
            continue

        bucket_outcomes = test_outcomes[bucket_mask.values]

        # k-NN
        knn_brier = compute_brier_score(knn_preds[bucket_mask.values], bucket_outcomes)
        results.append({"volume_bucket": bucket_name, "model": f"knn_k{k}", "brier_score": round(knn_brier, 6), "n_samples": n})

        # Market price (only where price > 0)
        mp = market_preds[bucket_mask.values]
        valid = mp > 0.01
        if valid.sum() > 0:
            mp_brier = compute_brier_score(mp[valid], bucket_outcomes[valid])
            results.append({"volume_bucket": bucket_name, "model": "market_price", "brier_score": round(mp_brier, 6), "n_samples": int(valid.sum())})

        # Random
        rand_brier = compute_brier_score(random_preds[bucket_mask.values], bucket_outcomes)
        results.append({"volume_bucket": bucket_name, "model": "random", "brier_score": round(rand_brier, 6), "n_samples": n})

    return pd.DataFrame(results)


def save_predictions(
    df: pd.DataFrame,
    embeddings: np.ndarray,
    k: int = 10,
) -> pd.DataFrame:
    """Save per-market predictions for analysis."""
    train_mask = df["split"] == "train"
    test_mask = df["split"] == "test"

    train_embeddings = embeddings[train_mask.values]
    test_embeddings = embeddings[test_mask.values]
    train_outcomes = df.loc[train_mask, "result_binary"].values.astype(float)

    preds = knn_predict(train_embeddings, train_outcomes, test_embeddings, k=k)

    df_test = df[test_mask].copy()
    df_test["knn_prediction"] = preds
    df_test["market_price_prediction"] = baseline_market_price(df_test)
    df_test["random_prediction"] = baseline_random(train_outcomes, len(df_test))

    output_path = os.path.join(DATA_DIR, "predictions.csv")
    df_test.to_csv(output_path, index=False)
    print(f"Saved predictions to {output_path}")

    return df_test


def main():
    """Run prediction evaluation."""
    markets_path = os.path.join(DATA_DIR, "markets.csv")
    embeddings_path = os.path.join(DATA_DIR, "embeddings.npy")

    if not os.path.exists(markets_path) or not os.path.exists(embeddings_path):
        print("Error: Run data_collection.py and embeddings.py first.")
        return

    df = pd.read_csv(markets_path)
    embeddings = np.load(embeddings_path)

    print("=" * 60)
    print("OVERALL EVALUATION")
    print("=" * 60)
    results = evaluate_all_baselines(df, embeddings)
    results.to_csv(os.path.join(DATA_DIR, "evaluation_results.csv"), index=False)
    print(f"\n{results.to_string()}")

    print("\n" + "=" * 60)
    print("STRATIFIED BY VOLUME")
    print("=" * 60)
    strat = stratified_evaluation(df, embeddings)
    strat.to_csv(os.path.join(DATA_DIR, "stratified_results.csv"), index=False)
    print(f"\n{strat.to_string()}")

    # Save per-market predictions
    save_predictions(df, embeddings)


if __name__ == "__main__":
    main()
