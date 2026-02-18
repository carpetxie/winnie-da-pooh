"""
experiment5/visualize.py

Generate all plots and tables for Experiment 5.
"""

import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

DATA_DIR = "data/exp5"
PLOTS_DIR = os.path.join(DATA_DIR, "plots")


def setup():
    os.makedirs(PLOTS_DIR, exist_ok=True)
    plt.style.use("seaborn-v0_8-whitegrid")
    plt.rcParams.update({"figure.dpi": 150, "savefig.bbox": "tight"})


def plot_tsne_by_domain(coords: np.ndarray, domains: pd.Series, filename: str = "tsne_by_domain.png"):
    """TSNE scatter plot colored by market domain."""
    fig, ax = plt.subplots(figsize=(12, 8))

    # Get unique domains and assign colors
    unique_domains = sorted(domains.unique())
    cmap = plt.cm.get_cmap("tab20", len(unique_domains))
    domain_to_color = {d: cmap(i) for i, d in enumerate(unique_domains)}

    for domain in unique_domains:
        mask = domains == domain
        ax.scatter(
            coords[mask, 0], coords[mask, 1],
            c=[domain_to_color[domain]],
            label=f"{domain} ({mask.sum()})",
            s=8, alpha=0.6,
        )

    ax.set_xlabel("t-SNE 1")
    ax.set_ylabel("t-SNE 2")
    ax.set_title("Market Embedding Space by Domain")
    ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left", fontsize=8, markerscale=2)

    path = os.path.join(PLOTS_DIR, filename)
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved {path}")


def plot_tsne_by_outcome(coords: np.ndarray, outcomes: pd.Series, filename: str = "tsne_by_outcome.png"):
    """TSNE scatter plot colored by YES/NO outcome."""
    fig, ax = plt.subplots(figsize=(10, 8))

    colors = {0: "#e74c3c", 1: "#2ecc71"}
    labels = {0: "NO", 1: "YES"}

    for outcome in [0, 1]:
        mask = outcomes == outcome
        ax.scatter(
            coords[mask, 0], coords[mask, 1],
            c=colors[outcome],
            label=f"{labels[outcome]} ({mask.sum()})",
            s=8, alpha=0.4,
        )

    ax.set_xlabel("t-SNE 1")
    ax.set_ylabel("t-SNE 2")
    ax.set_title("Market Embedding Space by Outcome")
    ax.legend(fontsize=10, markerscale=3)

    path = os.path.join(PLOTS_DIR, filename)
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved {path}")


def plot_tsne_by_cluster(coords: np.ndarray, labels: np.ndarray, filename: str = "tsne_by_cluster.png"):
    """TSNE scatter plot colored by HDBSCAN cluster."""
    fig, ax = plt.subplots(figsize=(10, 8))

    unique_labels = sorted(set(labels))
    n_clusters = len([l for l in unique_labels if l != -1])
    cmap = plt.cm.get_cmap("tab20", max(n_clusters, 1))

    # Plot noise points first (gray)
    noise_mask = labels == -1
    if noise_mask.any():
        ax.scatter(
            coords[noise_mask, 0], coords[noise_mask, 1],
            c="lightgray", label=f"Noise ({noise_mask.sum()})",
            s=4, alpha=0.3,
        )

    cluster_idx = 0
    for label in unique_labels:
        if label == -1:
            continue
        mask = labels == label
        ax.scatter(
            coords[mask, 0], coords[mask, 1],
            c=[cmap(cluster_idx)],
            label=f"C{label} ({mask.sum()})",
            s=10, alpha=0.6,
        )
        cluster_idx += 1

    ax.set_xlabel("t-SNE 1")
    ax.set_ylabel("t-SNE 2")
    ax.set_title(f"Market Clusters ({n_clusters} clusters)")
    if n_clusters <= 20:
        ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left", fontsize=7, markerscale=2)

    path = os.path.join(PLOTS_DIR, filename)
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved {path}")


def plot_brier_comparison(results: pd.DataFrame, filename: str = "brier_comparison.png"):
    """Bar chart comparing Brier scores across models."""
    fig, ax = plt.subplots(figsize=(8, 5))

    models = results["model"].tolist()
    scores = results["brier_score"].tolist()

    colors = []
    for m in models:
        if "knn" in m:
            colors.append("#3498db")
        elif "market" in m:
            colors.append("#e67e22")
        else:
            colors.append("#95a5a6")

    bars = ax.bar(range(len(models)), scores, color=colors)

    ax.set_xticks(range(len(models)))
    ax.set_xticklabels(models, rotation=30, ha="right", fontsize=9)
    ax.set_ylabel("Brier Score (lower = better)")
    ax.set_title("Prediction Performance Comparison")

    # Add value labels
    for bar, score in zip(bars, scores):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.002,
                f"{score:.4f}", ha="center", va="bottom", fontsize=8)

    path = os.path.join(PLOTS_DIR, filename)
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved {path}")


def plot_calibration_curve(predictions: pd.DataFrame, filename: str = "calibration_curve.png"):
    """Reliability diagram for k-NN predictions."""
    fig, ax = plt.subplots(figsize=(8, 8))

    for col, label, color in [
        ("knn_prediction", "k-NN Embedding", "#3498db"),
        ("market_price_prediction", "Market Price", "#e67e22"),
    ]:
        if col not in predictions.columns:
            continue

        preds = predictions[col].values
        actuals = predictions["result_binary"].values

        # Bin predictions
        n_bins = 10
        bin_edges = np.linspace(0, 1, n_bins + 1)
        bin_centers = []
        bin_accuracies = []
        bin_counts = []

        for i in range(n_bins):
            mask = (preds >= bin_edges[i]) & (preds < bin_edges[i + 1])
            if mask.sum() > 0:
                bin_centers.append((bin_edges[i] + bin_edges[i + 1]) / 2)
                bin_accuracies.append(actuals[mask].mean())
                bin_counts.append(mask.sum())

        ax.plot(bin_centers, bin_accuracies, "o-", label=label, color=color, markersize=6)

    # Perfect calibration line
    ax.plot([0, 1], [0, 1], "k--", alpha=0.5, label="Perfect calibration")

    ax.set_xlabel("Predicted Probability")
    ax.set_ylabel("Actual Frequency")
    ax.set_title("Calibration Curve")
    ax.legend()
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.05, 1.05)

    path = os.path.join(PLOTS_DIR, filename)
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved {path}")


def plot_stratified_brier(strat_results: pd.DataFrame, filename: str = "stratified_brier.png"):
    """Grouped bar chart of Brier scores by volume bucket."""
    fig, ax = plt.subplots(figsize=(10, 6))

    buckets = strat_results["volume_bucket"].unique()
    models = strat_results["model"].unique()
    x = np.arange(len(buckets))
    width = 0.25

    colors = {"knn_k10": "#3498db", "market_price": "#e67e22", "random": "#95a5a6"}

    for i, model in enumerate(models):
        model_data = strat_results[strat_results["model"] == model]
        scores = [model_data[model_data["volume_bucket"] == b]["brier_score"].values[0]
                  if len(model_data[model_data["volume_bucket"] == b]) > 0 else 0
                  for b in buckets]
        ax.bar(x + i * width, scores, width, label=model, color=colors.get(model, "#cccccc"))

    ax.set_xticks(x + width)
    ax.set_xticklabels(buckets, fontsize=9)
    ax.set_ylabel("Brier Score (lower = better)")
    ax.set_title("Performance by Market Volume")
    ax.legend()

    path = os.path.join(PLOTS_DIR, filename)
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved {path}")


def plot_domain_distribution(df: pd.DataFrame, filename: str = "domain_distribution.png"):
    """Bar chart of market counts by domain."""
    fig, ax = plt.subplots(figsize=(10, 5))

    counts = df["domain"].value_counts()
    ax.barh(range(len(counts)), counts.values, color="#3498db")
    ax.set_yticks(range(len(counts)))
    ax.set_yticklabels(counts.index, fontsize=9)
    ax.set_xlabel("Number of Markets")
    ax.set_title("Market Distribution by Domain")

    path = os.path.join(PLOTS_DIR, filename)
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved {path}")


def generate_all_plots(
    df: pd.DataFrame,
    coords: np.ndarray,
    cluster_labels: np.ndarray,
    eval_results: pd.DataFrame = None,
    predictions: pd.DataFrame = None,
    strat_results: pd.DataFrame = None,
):
    """Generate all visualization outputs."""
    setup()

    print("Generating plots...")

    plot_tsne_by_domain(coords, df["domain"])
    plot_tsne_by_outcome(coords, df["result_binary"])
    plot_tsne_by_cluster(coords, cluster_labels)
    plot_domain_distribution(df)

    if eval_results is not None:
        plot_brier_comparison(eval_results)

    if predictions is not None:
        plot_calibration_curve(predictions)

    if strat_results is not None:
        plot_stratified_brier(strat_results)

    print("All plots generated.")


def main():
    """Generate all visualizations from cached data."""
    setup()

    df = pd.read_csv(os.path.join(DATA_DIR, "markets.csv"))
    coords = np.load(os.path.join(DATA_DIR, "tsne_2d.npy"))

    from experiment5.clustering import run_clustering
    labels = run_clustering(coords)

    eval_path = os.path.join(DATA_DIR, "evaluation_results.csv")
    eval_results = pd.read_csv(eval_path) if os.path.exists(eval_path) else None

    pred_path = os.path.join(DATA_DIR, "predictions.csv")
    predictions = pd.read_csv(pred_path) if os.path.exists(pred_path) else None

    strat_path = os.path.join(DATA_DIR, "stratified_results.csv")
    strat_results = pd.read_csv(strat_path) if os.path.exists(strat_path) else None

    generate_all_plots(df, coords, labels, eval_results, predictions, strat_results)


if __name__ == "__main__":
    main()
