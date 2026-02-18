"""
experiment5/clustering.py

Discover structure in the embedding space using dimensionality reduction
and density-based clustering. Compute within-cluster outcome statistics.
"""

import os
import json
import numpy as np
import pandas as pd
from sklearn.cluster import HDBSCAN
from sklearn.manifold import TSNE
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from scipy import stats

DATA_DIR = "data/exp5"


def run_dimensionality_reduction(
    embeddings: np.ndarray,
    method: str = "tsne",
    n_components: int = 2,
    random_state: int = 42,
) -> np.ndarray:
    """
    Reduce embedding dimensions for visualization and clustering.

    Args:
        embeddings: (N, D) array
        method: "tsne" or "pca"
        n_components: Output dimensions
        random_state: For reproducibility

    Returns:
        (N, n_components) array of reduced coordinates
    """
    cache_path = os.path.join(DATA_DIR, f"{method}_{n_components}d.npy")
    if os.path.exists(cache_path):
        coords = np.load(cache_path)
        if coords.shape[0] == embeddings.shape[0]:
            print(f"Loading cached {method} coords from {cache_path}")
            return coords

    print(f"Running {method.upper()} ({embeddings.shape[1]}D → {n_components}D)...")

    if method == "tsne":
        # For large datasets, use PCA first to speed up t-SNE
        if embeddings.shape[1] > 50:
            print(f"  Pre-reducing with PCA to 50D...")
            pca = PCA(n_components=50, random_state=random_state)
            embeddings_reduced = pca.fit_transform(embeddings)
        else:
            embeddings_reduced = embeddings

        perplexity = min(30, embeddings.shape[0] - 1)
        tsne = TSNE(
            n_components=n_components,
            perplexity=perplexity,
            random_state=random_state,
            max_iter=1000,
            learning_rate="auto",
            init="pca",
        )
        coords = tsne.fit_transform(embeddings_reduced)
    elif method == "pca":
        pca = PCA(n_components=n_components, random_state=random_state)
        coords = pca.fit_transform(embeddings)
        print(f"  Explained variance: {pca.explained_variance_ratio_.sum():.3f}")
    else:
        raise ValueError(f"Unknown method: {method}")

    np.save(cache_path, coords)
    print(f"  Saved to {cache_path}")
    return coords


def run_clustering(
    coords: np.ndarray,
    min_cluster_size: int = 15,
    min_samples: int = 5,
) -> np.ndarray:
    """
    Run HDBSCAN clustering on reduced coordinates.

    Args:
        coords: (N, D) array (typically 2D from TSNE/PCA)
        min_cluster_size: Minimum cluster size
        min_samples: Core point threshold

    Returns:
        Array of cluster labels (-1 = noise)
    """
    print(f"Running HDBSCAN (min_cluster_size={min_cluster_size})...")

    clusterer = HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
    )
    labels = clusterer.fit_predict(coords)

    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = (labels == -1).sum()
    print(f"  Found {n_clusters} clusters, {n_noise} noise points ({n_noise/len(labels)*100:.1f}%)")

    return labels


def compute_cluster_stats(df: pd.DataFrame, cluster_labels: np.ndarray) -> pd.DataFrame:
    """
    Compute statistics for each cluster.

    Returns DataFrame with columns:
        cluster_id, size, yes_rate, outcome_correlation,
        dominant_domain, domain_count, domains, volume_mean, volume_median
    """
    df = df.copy()
    df["cluster"] = cluster_labels

    cluster_stats = []
    for cluster_id in sorted(df["cluster"].unique()):
        if cluster_id == -1:
            continue  # Skip noise

        mask = df["cluster"] == cluster_id
        cluster_df = df[mask]

        size = len(cluster_df)
        yes_rate = cluster_df["result_binary"].mean()
        domains = cluster_df["domain"].value_counts().to_dict()
        dominant_domain = cluster_df["domain"].mode().iloc[0] if not cluster_df.empty else "unknown"
        domain_count = cluster_df["domain"].nunique()
        volume_mean = cluster_df["volume"].mean()
        volume_median = cluster_df["volume"].median()

        # Outcome correlation: how consistent are outcomes within cluster
        # If all same outcome, correlation = 1. If 50/50, correlation = 0.
        outcome_consistency = abs(yes_rate - 0.5) * 2  # 0 = random, 1 = all same

        # Sample titles for description
        sample_titles = cluster_df["title"].head(5).tolist()

        cluster_stats.append({
            "cluster_id": cluster_id,
            "size": size,
            "yes_rate": round(yes_rate, 3),
            "outcome_consistency": round(outcome_consistency, 3),
            "dominant_domain": dominant_domain,
            "domain_count": domain_count,
            "domains": json.dumps(domains),
            "volume_mean": round(volume_mean, 1),
            "volume_median": round(volume_median, 1),
            "sample_titles": json.dumps(sample_titles),
        })

    return pd.DataFrame(cluster_stats)


def permutation_test_cluster_outcomes(
    df: pd.DataFrame,
    cluster_labels: np.ndarray,
    n_permutations: int = 1000,
    random_state: int = 42,
) -> pd.DataFrame:
    """
    Test whether within-cluster outcome consistency is better than chance.

    For each cluster, computes the actual outcome consistency and compares
    to a null distribution from random label permutations.

    Returns:
        DataFrame with cluster_id, actual_consistency, p_value, significant
    """
    rng = np.random.RandomState(random_state)
    df = df.copy()
    df["cluster"] = cluster_labels
    outcomes = df["result_binary"].values

    results = []
    unique_clusters = [c for c in sorted(df["cluster"].unique()) if c != -1]

    for cluster_id in unique_clusters:
        mask = df["cluster"] == cluster_id
        cluster_outcomes = outcomes[mask]
        actual_consistency = abs(cluster_outcomes.mean() - 0.5) * 2

        # Null distribution: randomly assign same number of points
        null_consistencies = []
        cluster_size = mask.sum()
        for _ in range(n_permutations):
            random_indices = rng.choice(len(outcomes), size=cluster_size, replace=False)
            random_outcomes = outcomes[random_indices]
            null_consistency = abs(random_outcomes.mean() - 0.5) * 2
            null_consistencies.append(null_consistency)

        p_value = (np.array(null_consistencies) >= actual_consistency).mean()

        results.append({
            "cluster_id": cluster_id,
            "actual_consistency": round(actual_consistency, 3),
            "null_mean": round(np.mean(null_consistencies), 3),
            "p_value": round(p_value, 4),
            "significant": p_value < 0.05,
        })

    return pd.DataFrame(results)


def compute_silhouette(embeddings: np.ndarray, labels: np.ndarray) -> float:
    """Compute silhouette score (excluding noise points)."""
    mask = labels != -1
    if mask.sum() < 2 or len(set(labels[mask])) < 2:
        return 0.0
    return float(silhouette_score(embeddings[mask], labels[mask]))


def main():
    """Run clustering pipeline."""
    markets_path = os.path.join(DATA_DIR, "markets.csv")
    embeddings_path = os.path.join(DATA_DIR, "embeddings.npy")

    if not os.path.exists(markets_path) or not os.path.exists(embeddings_path):
        print("Error: Run data_collection.py and embeddings.py first.")
        return

    df = pd.read_csv(markets_path)
    embeddings = np.load(embeddings_path)

    # Dimensionality reduction
    coords = run_dimensionality_reduction(embeddings, method="tsne")

    # Clustering
    labels = run_clustering(coords)
    df["cluster"] = labels

    # Cluster stats
    cluster_stats = compute_cluster_stats(df, labels)
    cluster_stats.to_csv(os.path.join(DATA_DIR, "clusters.csv"), index=False)
    print(f"\nCluster statistics:")
    print(cluster_stats[["cluster_id", "size", "yes_rate", "outcome_consistency", "dominant_domain", "domain_count"]].to_string())

    # Permutation test
    perm_results = permutation_test_cluster_outcomes(df, labels)
    n_sig = perm_results["significant"].sum()
    print(f"\nPermutation test: {n_sig}/{len(perm_results)} clusters have significant outcome consistency")

    # Silhouette score
    sil = compute_silhouette(embeddings, labels)
    print(f"\nSilhouette score: {sil:.3f}")


if __name__ == "__main__":
    main()
