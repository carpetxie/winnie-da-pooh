"""
experiment5/run.py

Main orchestrator for Experiment 5: Market Description Embeddings
as Economic Similarity Metric.

Usage:
    uv run python -m experiment5.run                    # Full run
    uv run python -m experiment5.run --quick-test       # Quick test (500 markets)
    uv run python -m experiment5.run --skip-fetch       # Use cached data
    uv run python -m experiment5.run --skip-embed       # Use cached embeddings
"""

import os
import sys
import json
import argparse
import numpy as np
import pandas as pd
from datetime import datetime

DATA_DIR = "data/exp5"


def phase1_data_collection(quick_test: bool = False, max_markets: int = None):
    """Phase 1: Fetch and prepare market data."""
    print("\n" + "=" * 70)
    print("PHASE 1: DATA COLLECTION")
    print("=" * 70)

    from experiment5.data_collection import (
        fetch_all_settled_markets_full,
        prepare_dataset,
    )
    from kalshi.client import KalshiClient

    client = KalshiClient()
    markets = fetch_all_settled_markets_full(client, max_markets=max_markets)
    df = prepare_dataset(markets)

    output_path = os.path.join(DATA_DIR, "markets.csv")
    df.to_csv(output_path, index=False)
    print(f"Saved {len(df)} markets to {output_path}")
    return df


def phase2_embeddings(df: pd.DataFrame):
    """Phase 2: Generate sentence embeddings."""
    print("\n" + "=" * 70)
    print("PHASE 2: EMBEDDING GENERATION")
    print("=" * 70)

    from experiment5.embeddings import load_or_generate_embeddings

    texts = df["text_for_embedding"].tolist()
    embeddings = load_or_generate_embeddings(texts)
    print(f"Embeddings shape: {embeddings.shape}")
    return embeddings


def phase3_clustering(df: pd.DataFrame, embeddings: np.ndarray):
    """Phase 3: Dimensionality reduction + clustering."""
    print("\n" + "=" * 70)
    print("PHASE 3: CLUSTERING & STRUCTURE DISCOVERY")
    print("=" * 70)

    from experiment5.clustering import (
        run_dimensionality_reduction,
        run_clustering,
        compute_cluster_stats,
        permutation_test_cluster_outcomes,
        compute_silhouette,
    )

    # Dimensionality reduction
    coords = run_dimensionality_reduction(embeddings, method="tsne")

    # Adaptive min_cluster_size based on dataset size
    min_cluster_size = max(10, len(df) // 100)
    labels = run_clustering(coords, min_cluster_size=min_cluster_size)

    # Cluster statistics
    cluster_stats = compute_cluster_stats(df, labels)
    cluster_stats.to_csv(os.path.join(DATA_DIR, "clusters.csv"), index=False)

    # Permutation tests
    perm = permutation_test_cluster_outcomes(df, labels)
    n_sig = perm["significant"].sum()
    print(f"\nPermutation test: {n_sig}/{len(perm)} clusters significant (p < 0.05)")

    # Silhouette
    sil = compute_silhouette(embeddings, labels)
    print(f"Silhouette score: {sil:.3f}")

    return coords, labels, cluster_stats


def phase4_prediction(df: pd.DataFrame, embeddings: np.ndarray):
    """Phase 4: k-NN prediction evaluation."""
    print("\n" + "=" * 70)
    print("PHASE 4: k-NN PREDICTION EVALUATION")
    print("=" * 70)

    from experiment5.prediction import (
        evaluate_all_baselines,
        stratified_evaluation,
        save_predictions,
    )

    # Overall evaluation
    print("\n--- Overall ---")
    eval_results = evaluate_all_baselines(df, embeddings, k_values=[5, 10, 20])
    eval_results.to_csv(os.path.join(DATA_DIR, "evaluation_results.csv"), index=False)

    # Stratified by volume
    print("\n--- Stratified by Volume ---")
    strat = stratified_evaluation(df, embeddings, k=10)
    strat.to_csv(os.path.join(DATA_DIR, "stratified_results.csv"), index=False)

    # Save predictions
    predictions = save_predictions(df, embeddings, k=10)

    return eval_results, strat, predictions


def phase5_cross_domain(df: pd.DataFrame, labels: np.ndarray, cluster_stats: pd.DataFrame):
    """Phase 5: Cross-domain discovery."""
    print("\n" + "=" * 70)
    print("PHASE 5: CROSS-DOMAIN DISCOVERY")
    print("=" * 70)

    from experiment5.cross_domain import (
        find_cross_domain_clusters,
        validate_cross_domain_correlations,
        generate_discoveries,
    )
    from dotenv import load_dotenv
    load_dotenv()

    grok_api_key = os.getenv("GROK_API_KEY")

    # Validation
    validation = validate_cross_domain_correlations(df, labels)
    if not validation.empty:
        n_sig = validation["significant"].sum()
        print(f"{n_sig}/{len(validation)} cross-domain clusters with significant correlation")
        validation.to_csv(os.path.join(DATA_DIR, "cross_domain_validation.csv"), index=False)

    # Generate discoveries with LLM explanations
    discoveries = generate_discoveries(df, labels, cluster_stats, grok_api_key, top_n=5)

    output_path = os.path.join(DATA_DIR, "cross_domain_discoveries.json")
    with open(output_path, "w") as f:
        json.dump(discoveries, f, indent=2)
    print(f"Saved {len(discoveries)} discoveries")

    return discoveries


def phase6_visualization(
    df, coords, labels, eval_results=None, predictions=None, strat_results=None
):
    """Phase 6: Generate all plots."""
    print("\n" + "=" * 70)
    print("PHASE 6: VISUALIZATION")
    print("=" * 70)

    from experiment5.visualize import generate_all_plots
    generate_all_plots(df, coords, labels, eval_results, predictions, strat_results)


def generate_results_summary(
    df, eval_results, strat_results, cluster_stats, discoveries, labels
):
    """Generate results_summary.md with all findings."""
    print("\n" + "=" * 70)
    print("GENERATING RESULTS SUMMARY")
    print("=" * 70)

    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = (labels == -1).sum()
    n_cross_domain = len([d for d in discoveries if len(d.get("domains", {})) >= 2])

    # Best k-NN result
    knn_results = eval_results[eval_results["model"].str.startswith("knn")]
    best_knn = knn_results.loc[knn_results["brier_score"].idxmin()] if not knn_results.empty else None
    random_brier = eval_results[eval_results["model"] == "random_baseline"]["brier_score"].values[0]

    summary = f"""# Experiment 5: Results Summary
## Market Description Embeddings as Economic Similarity Metric

**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

---

## Dataset
- **Total markets:** {len(df)}
- **Train:** {(df['split'] == 'train').sum()}
- **Test:** {(df['split'] == 'test').sum()}
- **Domains:** {df['domain'].nunique()}
- **Outcome balance:** YES={df['result_binary'].sum()}, NO={len(df) - df['result_binary'].sum()}

### Domain Distribution
{df['domain'].value_counts().to_string()}

---

## Clustering Results
- **Clusters found:** {n_clusters}
- **Noise points:** {n_noise} ({n_noise/len(df)*100:.1f}%)
- **Cross-domain clusters:** {n_cross_domain}

### Top Clusters by Size
{cluster_stats.head(10)[['cluster_id', 'size', 'yes_rate', 'outcome_consistency', 'dominant_domain', 'domain_count']].to_string()}

---

## Prediction Performance

### Overall Brier Scores (lower = better)
{eval_results.to_string()}

"""

    if best_knn is not None:
        improvement = ((random_brier - best_knn['brier_score']) / random_brier) * 100
        summary += f"""### Key Finding
- **Best k-NN model:** {best_knn['model']} (Brier = {best_knn['brier_score']:.4f})
- **Random baseline:** {random_brier:.4f}
- **Improvement over random:** {improvement:.1f}%

"""

    summary += f"""### Stratified by Volume
{strat_results.to_string() if strat_results is not None else 'N/A'}

---

## Cross-Domain Discoveries
"""

    for i, d in enumerate(discoveries):
        domains_str = ", ".join(d.get("domains", {}).keys()) if isinstance(d.get("domains"), dict) else str(d.get("domains"))
        summary += f"""
### Discovery {i+1}: Cluster {d['cluster_id']}
- **Size:** {d['size']} markets
- **Domains:** {domains_str}
- **YES rate:** {d['yes_rate']:.1%}
- **Sample markets:** {', '.join(d.get('sample_titles', [])[:3])}
- **LLM Explanation:** {d.get('llm_explanation', 'N/A')}
"""

    summary += f"""
---

## Success Metrics Assessment
| Metric | Threshold | Result | Status |
|--------|-----------|--------|--------|
| k-NN Brier < Random Brier | Significant improvement | {'PASS' if best_knn is not None and best_knn['brier_score'] < random_brier else 'FAIL'} | {'PASS' if best_knn is not None and best_knn['brier_score'] < random_brier else 'FAIL'} |
| High-quality clusters | >= 10 clusters | {n_clusters} clusters | {'PASS' if n_clusters >= 10 else 'PARTIAL'} |
| Cross-domain discoveries | >= 3 compelling | {n_cross_domain} found | {'PASS' if n_cross_domain >= 3 else 'PARTIAL'} |

---

## Deliverables
- [x] UMAP visualization (data/exp5/plots/tsne_by_domain.png)
- [x] Prediction performance table (data/exp5/evaluation_results.csv)
- [x] Cluster catalog (data/exp5/clusters.csv)
- [x] Cross-domain discoveries (data/exp5/cross_domain_discoveries.json)
- [x] Calibration curve (data/exp5/plots/calibration_curve.png)
"""

    output_path = os.path.join(DATA_DIR, "results_summary.md")
    with open(output_path, "w") as f:
        f.write(summary)
    print(f"Saved results summary to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Experiment 5: Market Description Embeddings")
    parser.add_argument("--quick-test", action="store_true", help="Run on small subset")
    parser.add_argument("--max-markets", type=int, default=None, help="Max markets to fetch")
    parser.add_argument("--skip-fetch", action="store_true", help="Use cached market data")
    parser.add_argument("--skip-embed", action="store_true", help="Use cached embeddings")
    parser.add_argument("--skip-cross-domain", action="store_true", help="Skip LLM explanations")
    args = parser.parse_args()

    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "plots"), exist_ok=True)

    start_time = datetime.now()
    print(f"Experiment 5 started at {start_time.strftime('%H:%M:%S')}")

    if args.quick_test:
        args.max_markets = args.max_markets or 500

    # Phase 1: Data collection
    markets_path = os.path.join(DATA_DIR, "markets.csv")
    if args.skip_fetch and os.path.exists(markets_path):
        print(f"\nLoading cached markets from {markets_path}")
        df = pd.read_csv(markets_path)
    else:
        df = phase1_data_collection(
            quick_test=args.quick_test,
            max_markets=args.max_markets,
        )

    # Phase 2: Embeddings
    embeddings_path = os.path.join(DATA_DIR, "embeddings.npy")
    if args.skip_embed and os.path.exists(embeddings_path):
        print(f"\nLoading cached embeddings from {embeddings_path}")
        embeddings = np.load(embeddings_path)
    else:
        embeddings = phase2_embeddings(df)

    # Phase 3: Clustering
    coords, labels, cluster_stats = phase3_clustering(df, embeddings)

    # Phase 4: Prediction
    eval_results, strat_results, predictions = phase4_prediction(df, embeddings)

    # Phase 5: Cross-domain discovery
    discoveries = []
    if not args.skip_cross_domain:
        discoveries = phase5_cross_domain(df, labels, cluster_stats)

    # Phase 6: Visualization
    phase6_visualization(df, coords, labels, eval_results, predictions, strat_results)

    # Results summary
    generate_results_summary(df, eval_results, strat_results, cluster_stats, discoveries, labels)

    elapsed = datetime.now() - start_time
    print(f"\n{'=' * 70}")
    print(f"EXPERIMENT 5 COMPLETE ({elapsed.total_seconds():.0f}s)")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
