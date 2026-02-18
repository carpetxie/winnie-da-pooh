#!/usr/bin/env python3
"""
Fetch ALL settled Kalshi markets and run the full Experiment 5 pipeline.

Usage:
    uv run python -m experiment5.fetch_all                  # Fetch all + run pipeline
    uv run python -m experiment5.fetch_all --fetch-only      # Just fetch data
    uv run python -m experiment5.fetch_all --max-pages 10    # Limit to 10 pages (~10K markets)
    uv run python -m experiment5.fetch_all --run-only        # Skip fetch, run pipeline on cached data
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime, timedelta, timezone
from collections import Counter
from tqdm import tqdm

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

DATA_DIR = "data/exp5"
CACHE_PATH = os.path.join(DATA_DIR, "all_settled_markets.json")


def fetch_all_markets(max_pages: int = None):
    """Fetch all settled markets with progress bar."""
    from kalshi.client import KalshiClient

    if os.path.exists(CACHE_PATH):
        print(f"Cache exists at {CACHE_PATH}")
        with open(CACHE_PATH) as f:
            data = json.load(f)
        print(f"  {len(data)} markets cached. Delete file to re-fetch.")
        return data

    client = KalshiClient()
    twelve_months_ago = int((datetime.now(timezone.utc) - timedelta(days=365)).timestamp())
    two_days_ago = int((datetime.now(timezone.utc) - timedelta(days=2)).timestamp())

    all_markets = []
    cursor = None
    page_num = 0

    desc = "Fetching markets"
    if max_pages:
        desc += f" (max {max_pages} pages)"
        pbar = tqdm(total=max_pages * 1000, desc=desc, unit=" mkts")
    else:
        pbar = tqdm(desc=desc, unit=" mkts")

    while True:
        params = {
            "status": "settled",
            "min_settled_ts": twelve_months_ago,
            "max_settled_ts": two_days_ago,
            "limit": 1000,
        }
        if cursor:
            params["cursor"] = cursor

        resp = client.get("/markets", params=params)
        items = resp.get("markets", [])

        if not items:
            break

        all_markets.extend(items)
        page_num += 1
        pbar.update(len(items))
        pbar.set_postfix({"pages": page_num})

        cursor = resp.get("cursor", "")
        if not cursor:
            break

        if max_pages and page_num >= max_pages:
            break

        time.sleep(0.7)

    pbar.close()
    print(f"\nFetched {len(all_markets)} markets in {page_num} pages")

    # Save
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(CACHE_PATH, "w") as f:
        json.dump(all_markets, f, default=str)
    print(f"Saved to {CACHE_PATH}")

    # Domain summary
    prefixes = Counter()
    for m in all_markets:
        prefix = m["ticker"].split("-")[0]
        prefixes[prefix] += 1
    print(f"\nTop 20 domains:")
    for prefix, count in prefixes.most_common(20):
        print(f"  {prefix}: {count}")

    return all_markets


def run_pipeline():
    """Run the full experiment pipeline on cached data."""
    from experiment5.data_collection import prepare_dataset
    from experiment5.embeddings import load_or_generate_embeddings
    from experiment5.clustering import (
        run_dimensionality_reduction, run_clustering,
        compute_cluster_stats, permutation_test_cluster_outcomes,
        compute_silhouette,
    )
    from experiment5.prediction import (
        evaluate_all_baselines, stratified_evaluation, save_predictions,
    )
    from experiment5.cross_domain import (
        validate_cross_domain_correlations, generate_discoveries,
    )
    from experiment5.visualize import generate_all_plots
    from experiment5.run import generate_results_summary
    from dotenv import load_dotenv
    import numpy as np
    import pandas as pd

    load_dotenv()

    # Phase 1: Prepare data
    print("\n" + "=" * 60)
    print("PHASE 1: DATA PREPARATION")
    print("=" * 60)
    with open(CACHE_PATH) as f:
        markets = json.load(f)
    df = prepare_dataset(markets)
    df.to_csv(os.path.join(DATA_DIR, "markets.csv"), index=False)

    # Phase 2: Embeddings
    print("\n" + "=" * 60)
    print("PHASE 2: EMBEDDINGS")
    print("=" * 60)
    texts = df["text_for_embedding"].tolist()
    embeddings = load_or_generate_embeddings(texts)

    # Phase 3: Clustering
    print("\n" + "=" * 60)
    print("PHASE 3: CLUSTERING")
    print("=" * 60)
    coords = run_dimensionality_reduction(embeddings, method="tsne")
    min_cluster_size = max(10, len(df) // 100)
    labels = run_clustering(coords, min_cluster_size=min_cluster_size)
    cluster_stats = compute_cluster_stats(df, labels)
    cluster_stats.to_csv(os.path.join(DATA_DIR, "clusters.csv"), index=False)

    perm = permutation_test_cluster_outcomes(df, labels)
    n_sig = perm["significant"].sum()
    print(f"Permutation test: {n_sig}/{len(perm)} significant")
    sil = compute_silhouette(embeddings, labels)
    print(f"Silhouette: {sil:.3f}")

    # Phase 4: Prediction
    print("\n" + "=" * 60)
    print("PHASE 4: PREDICTION")
    print("=" * 60)
    eval_results = evaluate_all_baselines(df, embeddings, k_values=[5, 10, 20])
    eval_results.to_csv(os.path.join(DATA_DIR, "evaluation_results.csv"), index=False)
    strat = stratified_evaluation(df, embeddings, k=10)
    strat.to_csv(os.path.join(DATA_DIR, "stratified_results.csv"), index=False)
    predictions = save_predictions(df, embeddings, k=10)

    # Phase 5: Cross-domain
    print("\n" + "=" * 60)
    print("PHASE 5: CROSS-DOMAIN DISCOVERY")
    print("=" * 60)
    grok_api_key = os.getenv("GROK_API_KEY")
    validation = validate_cross_domain_correlations(df, labels)
    if not validation.empty:
        validation.to_csv(os.path.join(DATA_DIR, "cross_domain_validation.csv"), index=False)
    discoveries = generate_discoveries(df, labels, cluster_stats, grok_api_key, top_n=5)
    with open(os.path.join(DATA_DIR, "cross_domain_discoveries.json"), "w") as f:
        json.dump(discoveries, f, indent=2)

    # Phase 6: Visualization
    print("\n" + "=" * 60)
    print("PHASE 6: VISUALIZATION")
    print("=" * 60)
    generate_all_plots(df, coords, labels, eval_results, predictions, strat)

    # Results summary
    generate_results_summary(df, eval_results, strat, cluster_stats, discoveries, labels)

    print("\n" + "=" * 60)
    print("DONE!")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Experiment 5: Full fetch + pipeline")
    parser.add_argument("--fetch-only", action="store_true", help="Only fetch data, don't run pipeline")
    parser.add_argument("--run-only", action="store_true", help="Only run pipeline on cached data")
    parser.add_argument("--max-pages", type=int, default=20, help="Max API pages to fetch (1000 mkts/page, default 20 = ~20K markets)")
    args = parser.parse_args()

    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "plots"), exist_ok=True)

    if not args.run_only:
        fetch_all_markets(max_pages=args.max_pages)

    if args.fetch_only:
        return

    if not os.path.exists(CACHE_PATH):
        print(f"No cached data at {CACHE_PATH}. Run without --run-only first.")
        return

    run_pipeline()


if __name__ == "__main__":
    main()
