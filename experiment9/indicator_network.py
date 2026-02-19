"""
experiment9/indicator_network.py

Refine the domain-level lead-lag finding to indicator-level granularity.
Instead of "inflation → monetary_policy", identify which specific indicators
lead which (CPI → Fed Funds vs PCE → Fed Funds vs PPI → Fed Funds).

This tests whether the lead-lag structure is consistent with the Fed's
stated policy framework (PCE is the Fed's preferred inflation measure).

No API calls required. Uses cached Granger results from experiment1.
"""

import os
import json
import numpy as np
import pandas as pd
from scipy import stats
from collections import defaultdict

from experiment1.propagation_network import INDICATOR_MAP, INDICATOR_DOMAIN

DATA_DIR = "data/exp9"


def load_granger_results(path: str = "data/exp1/granger_significant.csv") -> pd.DataFrame:
    """Load significant Granger pairs from experiment 1."""
    df = pd.read_csv(path)
    return df


def classify_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add indicator-level classification to Granger results.

    Maps each ticker's series prefix to a specific economic indicator
    (CPI, PCE, PPI, Fed Funds, Jobless Claims, etc.).
    """
    df = df.copy()

    def get_indicator(ticker):
        prefix = ticker.split("-")[0] if "-" in ticker else ticker
        if prefix in INDICATOR_MAP:
            return INDICATOR_MAP[prefix]
        for key, ind in INDICATOR_MAP.items():
            if prefix.startswith(key):
                return ind
        return "other"

    df["leader_indicator"] = df["leader_ticker"].apply(get_indicator)
    df["follower_indicator"] = df["follower_ticker"].apply(get_indicator)
    df["leader_indicator_domain"] = df["leader_indicator"].map(INDICATOR_DOMAIN).fillna("other")
    df["follower_indicator_domain"] = df["follower_indicator"].map(INDICATOR_DOMAIN).fillna("other")

    return df


def build_indicator_network(df: pd.DataFrame) -> dict:
    """Build directed graph at indicator level.

    Aggregates Granger pairs by (leader_indicator, follower_indicator),
    computing median lag, pair count, and significance statistics.
    """
    # Filter to known indicators (exclude "other")
    df = df[(df["leader_indicator"] != "other") & (df["follower_indicator"] != "other")].copy()

    # Only cross-indicator pairs
    df = df[df["leader_indicator"] != df["follower_indicator"]].copy()

    edges = {}
    for _, row in df.iterrows():
        key = (row["leader_indicator"], row["follower_indicator"])
        if key not in edges:
            edges[key] = {"lags": [], "f_stats": [], "p_values": [], "pairs": []}
        edges[key]["lags"].append(row["best_lag"])
        edges[key]["f_stats"].append(row["f_stat"])
        edges[key]["p_values"].append(row["p_value"])
        edges[key]["pairs"].append(f"{row['leader_ticker']} -> {row['follower_ticker']}")

    graph = []
    for (src, dst), data in edges.items():
        lags = np.array(data["lags"])
        graph.append({
            "source": src,
            "target": dst,
            "source_domain": INDICATOR_DOMAIN.get(src, "other"),
            "target_domain": INDICATOR_DOMAIN.get(dst, "other"),
            "n_pairs": len(data["lags"]),
            "median_lag": float(np.median(lags)),
            "mean_lag": float(np.mean(lags)),
            "std_lag": float(np.std(lags)) if len(lags) > 1 else 0,
            "min_lag": int(np.min(lags)),
            "max_lag": int(np.max(lags)),
            "mean_f_stat": float(np.mean(data["f_stats"])),
            "sample_pairs": data["pairs"][:5],
        })

    graph.sort(key=lambda x: x["n_pairs"], reverse=True)
    return graph


def analyze_inflation_to_fed(df: pd.DataFrame) -> dict:
    """Specifically analyze which inflation indicator leads Fed Funds.

    Tests: CPI → Fed vs PCE → Fed vs PPI → Fed
    """
    inflation_indicators = ["CPI", "PCE", "PPI"]
    fed_indicators = ["Fed Funds", "Fed Funds Rate"]

    results = {}

    for infl in inflation_indicators:
        for fed in fed_indicators:
            # Inflation → Fed
            forward = df[(df["leader_indicator"] == infl) & (df["follower_indicator"] == fed)]
            # Fed → Inflation
            reverse = df[(df["leader_indicator"] == fed) & (df["follower_indicator"] == infl)]

            if len(forward) > 0 or len(reverse) > 0:
                key = f"{infl}_to_{fed}"
                results[key] = {
                    "forward_pairs": len(forward),
                    "forward_median_lag": float(forward["best_lag"].median()) if len(forward) > 0 else None,
                    "forward_lags": forward["best_lag"].tolist() if len(forward) > 0 else [],
                    "reverse_pairs": len(reverse),
                    "reverse_median_lag": float(reverse["best_lag"].median()) if len(reverse) > 0 else None,
                    "asymmetry": len(forward) - len(reverse),
                    "is_asymmetric": len(forward) > len(reverse),
                }

    # Compare CPI vs PCE: which leads Fed more strongly?
    cpi_to_fed = sum(1 for k, v in results.items() if k.startswith("CPI") and v["forward_pairs"] > 0)
    pce_to_fed = sum(1 for k, v in results.items() if k.startswith("PCE") and v["forward_pairs"] > 0)

    cpi_pairs = sum(v["forward_pairs"] for k, v in results.items() if k.startswith("CPI"))
    pce_pairs = sum(v["forward_pairs"] for k, v in results.items() if k.startswith("PCE"))
    ppi_pairs = sum(v["forward_pairs"] for k, v in results.items() if k.startswith("PPI"))

    results["comparison"] = {
        "cpi_to_fed_pairs": cpi_pairs,
        "pce_to_fed_pairs": pce_pairs,
        "ppi_to_fed_pairs": ppi_pairs,
        "dominant_inflation_indicator": (
            "CPI" if cpi_pairs > pce_pairs and cpi_pairs > ppi_pairs
            else "PCE" if pce_pairs > cpi_pairs and pce_pairs > ppi_pairs
            else "PPI" if ppi_pairs > cpi_pairs and ppi_pairs > pce_pairs
            else "tie"
        ),
        "interpretation": (
            "CPI is the dominant market-implied inflation signal for monetary policy"
            if cpi_pairs > pce_pairs
            else "PCE (Fed's preferred measure) dominates, consistent with Fed communication"
            if pce_pairs > cpi_pairs
            else "No clear dominant inflation indicator"
        ),
    }

    return results


def analyze_bidirectional_pairs(df: pd.DataFrame) -> dict:
    """Identify bidirectional indicator pairs (co-movement vs causation)."""
    # Build pair keys
    forward_pairs = set()
    reverse_pairs = set()

    for _, row in df.iterrows():
        key = (row["leader_indicator"], row["follower_indicator"])
        forward_pairs.add(key)

    bidirectional = set()
    unidirectional = set()

    for pair in forward_pairs:
        reverse = (pair[1], pair[0])
        if reverse in forward_pairs:
            bidirectional.add(tuple(sorted(pair)))
        else:
            unidirectional.add(pair)

    return {
        "n_forward_edges": len(forward_pairs),
        "n_bidirectional_pairs": len(bidirectional),
        "n_unidirectional_edges": len(unidirectional),
        "bidirectional_pairs": [list(p) for p in sorted(bidirectional)],
        "unidirectional_edges": [list(p) for p in sorted(unidirectional)],
    }


def compute_indicator_centrality(graph: list[dict]) -> dict:
    """Compute influence and receptivity scores for each indicator.

    Influence = weighted out-degree (number of markets this indicator leads)
    Receptivity = weighted in-degree (number of markets that lead this indicator)
    """
    influence = defaultdict(int)
    receptivity = defaultdict(int)

    for edge in graph:
        influence[edge["source"]] += edge["n_pairs"]
        receptivity[edge["target"]] += edge["n_pairs"]

    all_indicators = set(influence.keys()) | set(receptivity.keys())

    centrality = {}
    for ind in sorted(all_indicators):
        infl = influence.get(ind, 0)
        recep = receptivity.get(ind, 0)
        total = infl + recep
        centrality[ind] = {
            "influence": infl,
            "receptivity": recep,
            "total_connections": total,
            "influence_ratio": infl / total if total > 0 else 0,
            "domain": INDICATOR_DOMAIN.get(ind, "other"),
        }

    return centrality


def test_lag_asymmetry(df: pd.DataFrame) -> dict:
    """Test whether cross-domain lags show significant directional asymmetry.

    Uses Mann-Whitney U test on lag distributions for each indicator pair direction.
    """
    results = {}

    # Key pairs to test
    test_pairs = [
        ("CPI", "Fed Funds"),
        ("PCE", "Fed Funds"),
        ("Jobless Claims", "CPI"),
        ("GDP", "CPI"),
        ("CPI", "Jobless Claims"),
    ]

    for indicator_a, indicator_b in test_pairs:
        ab = df[(df["leader_indicator"] == indicator_a) &
                (df["follower_indicator"] == indicator_b)]["best_lag"]
        ba = df[(df["leader_indicator"] == indicator_b) &
                (df["follower_indicator"] == indicator_a)]["best_lag"]

        if len(ab) >= 3 and len(ba) >= 3:
            stat, p = stats.mannwhitneyu(ab, ba, alternative="two-sided")
            results[f"{indicator_a}_vs_{indicator_b}"] = {
                "ab_median_lag": float(ab.median()),
                "ba_median_lag": float(ba.median()),
                "ab_n": len(ab),
                "ba_n": len(ba),
                "mann_whitney_p": float(p),
                "significant": p < 0.05,
                "faster_direction": (
                    f"{indicator_a} → {indicator_b}"
                    if ab.median() < ba.median()
                    else f"{indicator_b} → {indicator_a}"
                ),
            }
        elif len(ab) > 0 or len(ba) > 0:
            results[f"{indicator_a}_vs_{indicator_b}"] = {
                "ab_n": len(ab),
                "ba_n": len(ba),
                "note": "insufficient_pairs_for_test",
            }

    return results


def plot_indicator_network(
    graph: list[dict],
    centrality: dict,
    output_dir: str = "data/exp9/plots",
):
    """Plot the indicator-level information network."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    os.makedirs(output_dir, exist_ok=True)

    # Heatmap of pair counts
    indicators = sorted(set(
        [e["source"] for e in graph] + [e["target"] for e in graph]
    ))

    matrix = pd.DataFrame(0, index=indicators, columns=indicators, dtype=float)
    for edge in graph:
        matrix.loc[edge["source"], edge["target"]] = edge["n_pairs"]

    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    # Heatmap
    im = axes[0].imshow(matrix.values, cmap="YlOrRd", aspect="auto")
    axes[0].set_xticks(range(len(indicators)))
    axes[0].set_yticks(range(len(indicators)))
    axes[0].set_xticklabels(indicators, rotation=45, ha="right", fontsize=8)
    axes[0].set_yticklabels(indicators, fontsize=8)
    axes[0].set_xlabel("Follower")
    axes[0].set_ylabel("Leader")
    axes[0].set_title("Granger-Causal Pair Counts\n(Leader → Follower)")
    plt.colorbar(im, ax=axes[0], fraction=0.046)

    # Add text annotations
    for i in range(len(indicators)):
        for j in range(len(indicators)):
            val = int(matrix.values[i, j])
            if val > 0:
                axes[0].text(j, i, str(val), ha="center", va="center",
                           fontsize=7, color="white" if val > matrix.values.max() / 2 else "black")

    # Centrality bar chart
    inds = sorted(centrality.keys(), key=lambda x: centrality[x]["influence_ratio"], reverse=True)
    influence_vals = [centrality[i]["influence"] for i in inds]
    receptivity_vals = [centrality[i]["receptivity"] for i in inds]

    x = np.arange(len(inds))
    width = 0.35
    axes[1].bar(x - width / 2, influence_vals, width, label="Influence (out-degree)",
               color="steelblue", alpha=0.7)
    axes[1].bar(x + width / 2, receptivity_vals, width, label="Receptivity (in-degree)",
               color="coral", alpha=0.7)
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(inds, rotation=45, ha="right", fontsize=8)
    axes[1].set_ylabel("Number of Granger-Causal Pairs")
    axes[1].set_title("Indicator Centrality")
    axes[1].legend()
    axes[1].grid(True, alpha=0.3, axis="y")

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "indicator_network.png"), dpi=150)
    plt.close()
    print(f"  Saved {output_dir}/indicator_network.png")
