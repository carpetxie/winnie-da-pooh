"""
experiment5/cross_domain.py

Identify cross-domain clusters and generate LLM explanations
for why semantically similar markets from different domains
have correlated outcomes.
"""

import os
import json
import numpy as np
import pandas as pd
import requests

DATA_DIR = "data/exp5"


def find_cross_domain_clusters(cluster_stats: pd.DataFrame, min_domains: int = 2) -> pd.DataFrame:
    """
    Find clusters that span multiple market domains.

    Args:
        cluster_stats: Output of clustering.compute_cluster_stats()
        min_domains: Minimum number of domains to qualify

    Returns:
        Filtered DataFrame of cross-domain clusters
    """
    cross_domain = cluster_stats[cluster_stats["domain_count"] >= min_domains].copy()
    cross_domain = cross_domain.sort_values("domain_count", ascending=False)
    print(f"Found {len(cross_domain)} cross-domain clusters (spanning {min_domains}+ domains)")
    return cross_domain


def explain_cluster_with_llm(
    cluster_markets: pd.DataFrame,
    grok_api_key: str,
    max_examples: int = 10,
) -> str:
    """
    Use Grok API to explain why markets in a cross-domain cluster are related.

    Args:
        cluster_markets: DataFrame of markets in this cluster
        grok_api_key: xAI API key
        max_examples: Maximum number of example markets to include in prompt

    Returns:
        LLM-generated explanation string
    """
    # Build market description list
    examples = cluster_markets.head(max_examples)
    market_list = []
    for _, row in examples.iterrows():
        market_list.append(f"- [{row['domain']}] {row['title']}")

    market_text = "\n".join(market_list)

    domains = cluster_markets["domain"].unique().tolist()
    yes_rate = cluster_markets["result_binary"].mean()

    prompt = f"""These prediction markets from different domains were found to be semantically similar based on their descriptions. They cluster together in embedding space.

Domains represented: {', '.join(domains)}
Outcome rate (YES): {yes_rate:.1%}
Number of markets: {len(cluster_markets)}

Example markets in this cluster:
{market_text}

In 2-3 sentences, explain:
1. What economic or thematic connection links these markets across domains?
2. Why might their outcomes be correlated?
3. Is this a meaningful economic relationship or a superficial linguistic similarity?"""

    try:
        response = requests.post(
            "https://api.x.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {grok_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "grok-3-mini-fast",
                "messages": [
                    {"role": "system", "content": "You are an economics and prediction markets analyst. Be concise and specific."},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 300,
                "temperature": 0.3,
            },
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"LLM explanation failed: {e}"


def validate_cross_domain_correlations(
    df: pd.DataFrame,
    cluster_labels: np.ndarray,
    n_permutations: int = 500,
) -> pd.DataFrame:
    """
    For cross-domain clusters, test whether outcome correlation across domains
    is significantly different from chance.

    Returns:
        DataFrame with cluster_id, cross_domain_correlation, p_value
    """
    rng = np.random.RandomState(42)
    df = df.copy()
    df["cluster"] = cluster_labels

    results = []
    for cluster_id in sorted(df["cluster"].unique()):
        if cluster_id == -1:
            continue

        cluster_df = df[df["cluster"] == cluster_id]
        domains = cluster_df["domain"].unique()

        if len(domains) < 2:
            continue

        # Actual: outcome consistency across all domains in cluster
        actual_consistency = abs(cluster_df["result_binary"].mean() - 0.5) * 2

        # Null: randomly sample same number of markets from same domains
        null_consistencies = []
        for _ in range(n_permutations):
            random_sample = df.sample(n=len(cluster_df), random_state=rng.randint(0, 1_000_000))
            null_consistency = abs(random_sample["result_binary"].mean() - 0.5) * 2
            null_consistencies.append(null_consistency)

        p_value = (np.array(null_consistencies) >= actual_consistency).mean()

        results.append({
            "cluster_id": cluster_id,
            "n_markets": len(cluster_df),
            "n_domains": len(domains),
            "domains": ", ".join(sorted(domains)),
            "yes_rate": round(cluster_df["result_binary"].mean(), 3),
            "cross_domain_consistency": round(actual_consistency, 3),
            "p_value": round(p_value, 4),
            "significant": p_value < 0.05,
        })

    return pd.DataFrame(results)


def generate_discoveries(
    df: pd.DataFrame,
    cluster_labels: np.ndarray,
    cluster_stats: pd.DataFrame,
    grok_api_key: str = None,
    top_n: int = 5,
) -> list[dict]:
    """
    Generate cross-domain discovery reports with LLM explanations.

    Returns:
        List of discovery dicts with cluster info + LLM explanation
    """
    df = df.copy()
    df["cluster"] = cluster_labels

    cross_domain = find_cross_domain_clusters(cluster_stats)

    if cross_domain.empty:
        print("No cross-domain clusters found.")
        return []

    # Take top N by domain count, then by size
    top_clusters = cross_domain.sort_values(
        ["domain_count", "size"], ascending=[False, False]
    ).head(top_n)

    discoveries = []
    for _, row in top_clusters.iterrows():
        cluster_id = row["cluster_id"]
        cluster_markets = df[df["cluster"] == cluster_id]

        discovery = {
            "cluster_id": int(cluster_id),
            "size": int(row["size"]),
            "domains": json.loads(row["domains"]),
            "yes_rate": float(row["yes_rate"]),
            "outcome_consistency": float(row["outcome_consistency"]),
            "sample_titles": json.loads(row["sample_titles"]),
        }

        # LLM explanation if API key available
        if grok_api_key:
            print(f"  Generating LLM explanation for cluster {cluster_id}...")
            explanation = explain_cluster_with_llm(cluster_markets, grok_api_key)
            discovery["llm_explanation"] = explanation
        else:
            discovery["llm_explanation"] = "(No API key provided)"

        discoveries.append(discovery)

    return discoveries


def main():
    """Run cross-domain discovery."""
    from dotenv import load_dotenv
    load_dotenv()

    grok_api_key = os.getenv("GROK_API_KEY")

    markets_path = os.path.join(DATA_DIR, "markets.csv")
    clusters_path = os.path.join(DATA_DIR, "clusters.csv")

    if not os.path.exists(markets_path) or not os.path.exists(clusters_path):
        print("Error: Run data_collection.py, embeddings.py, and clustering.py first.")
        return

    df = pd.read_csv(markets_path)
    cluster_stats = pd.read_csv(clusters_path)

    # Load cluster labels from the markets file or recompute
    embeddings = np.load(os.path.join(DATA_DIR, "embeddings.npy"))
    coords = np.load(os.path.join(DATA_DIR, "tsne_2d.npy"))

    from experiment5.clustering import run_clustering
    labels = run_clustering(coords)

    # Validate cross-domain correlations
    print("\n" + "=" * 60)
    print("CROSS-DOMAIN VALIDATION")
    print("=" * 60)
    validation = validate_cross_domain_correlations(df, labels)
    if not validation.empty:
        n_sig = validation["significant"].sum()
        print(f"{n_sig}/{len(validation)} cross-domain clusters have significant outcome correlation")
        print(validation.to_string())

    # Generate discoveries
    print("\n" + "=" * 60)
    print("CROSS-DOMAIN DISCOVERIES")
    print("=" * 60)
    discoveries = generate_discoveries(df, labels, cluster_stats, grok_api_key)

    output_path = os.path.join(DATA_DIR, "cross_domain_discoveries.json")
    with open(output_path, "w") as f:
        json.dump(discoveries, f, indent=2)
    print(f"\nSaved {len(discoveries)} discoveries to {output_path}")


if __name__ == "__main__":
    main()
