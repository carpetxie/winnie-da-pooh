"""
experiment1/propagation_network.py

Build and visualize the information propagation network from Granger
causality results. Shows how fast information flows between economics
sub-domains in Kalshi prediction markets.
"""

import os
import json
import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

DATA_DIR = "data/exp1"


def build_domain_graph(sig_df: pd.DataFrame) -> dict:
    """Aggregate Granger pairs into domain-level directed graph.

    Returns dict with nodes and edges suitable for visualization.
    """
    # Aggregate by (leader_domain, follower_domain)
    edges = {}
    for _, row in sig_df.iterrows():
        key = (row["leader_domain"], row["follower_domain"])
        if key not in edges:
            edges[key] = {"lags": [], "f_stats": [], "p_values": [], "pairs": []}
        edges[key]["lags"].append(row["best_lag"])
        edges[key]["f_stats"].append(row["f_stat"])
        edges[key]["p_values"].append(row["p_value"])
        edges[key]["pairs"].append(f"{row['leader_ticker']} -> {row['follower_ticker']}")

    # Compute aggregate stats
    graph_edges = []
    for (src, dst), data in edges.items():
        lags = np.array(data["lags"])
        graph_edges.append({
            "source": src,
            "target": dst,
            "n_pairs": len(data["lags"]),
            "median_lag_hours": float(np.median(lags)),
            "mean_lag_hours": float(np.mean(lags)),
            "min_lag_hours": float(np.min(lags)),
            "max_lag_hours": float(np.max(lags)),
            "lag_std": float(np.std(lags)),
            "mean_f_stat": float(np.mean(data["f_stats"])),
            "min_p_value": float(np.min(data["p_values"])),
        })

    # Compute node stats
    all_domains = set()
    for e in graph_edges:
        all_domains.add(e["source"])
        all_domains.add(e["target"])

    nodes = []
    for domain in sorted(all_domains):
        n_as_leader = sum(1 for e in graph_edges if e["source"] == domain)
        n_as_follower = sum(1 for e in graph_edges if e["target"] == domain)
        n_markets = len(sig_df[
            (sig_df["leader_domain"] == domain) | (sig_df["follower_domain"] == domain)
        ]["leader_ticker"].unique())

        # Influence score: sum of (n_pairs / median_lag) for outgoing edges
        # Higher = more pairs that propagate faster
        influence = sum(
            e["n_pairs"] / max(e["median_lag_hours"], 1)
            for e in graph_edges if e["source"] == domain
        )
        # Receptivity score: same for incoming
        receptivity = sum(
            e["n_pairs"] / max(e["median_lag_hours"], 1)
            for e in graph_edges if e["target"] == domain
        )

        nodes.append({
            "domain": domain,
            "n_outgoing": n_as_leader,
            "n_incoming": n_as_follower,
            "n_markets": n_markets,
            "influence_score": round(influence, 2),
            "receptivity_score": round(receptivity, 2),
            "net_influence": round(influence - receptivity, 2),
        })

    return {"nodes": nodes, "edges": graph_edges}


def compute_lag_distributions(sig_df: pd.DataFrame) -> dict:
    """Compute lag histograms per domain pair for asymmetry analysis."""
    results = {}

    pairs = sig_df.groupby(["leader_domain", "follower_domain"])
    for (src, dst), group in pairs:
        lags = group["best_lag"].values
        hist, bin_edges = np.histogram(lags, bins=range(0, 26))

        results[f"{src} -> {dst}"] = {
            "n_pairs": len(lags),
            "histogram": hist.tolist(),
            "bin_edges": bin_edges.tolist(),
            "median": float(np.median(lags)),
            "mean": float(np.mean(lags)),
            "mode": int(bin_edges[np.argmax(hist)]),
        }

    # Check asymmetry (A→B vs B→A)
    asymmetry = []
    seen = set()
    for key in results:
        src, dst = key.split(" -> ")
        reverse = f"{dst} -> {src}"
        pair_key = tuple(sorted([src, dst]))
        if pair_key in seen:
            continue
        seen.add(pair_key)

        if reverse in results:
            fwd = results[key]
            rev = results[reverse]

            # Mann-Whitney U test: is the lag distribution significantly different?
            fwd_lags = sig_df[
                (sig_df["leader_domain"] == src) & (sig_df["follower_domain"] == dst)
            ]["best_lag"].values
            rev_lags = sig_df[
                (sig_df["leader_domain"] == dst) & (sig_df["follower_domain"] == src)
            ]["best_lag"].values

            if len(fwd_lags) >= 5 and len(rev_lags) >= 5:
                u_stat, u_p = scipy_stats.mannwhitneyu(fwd_lags, rev_lags, alternative="two-sided")
            else:
                u_stat, u_p = np.nan, np.nan

            asymmetry.append({
                "forward": key,
                "reverse": reverse,
                "forward_median_lag": fwd["median"],
                "reverse_median_lag": rev["median"],
                "forward_n": fwd["n_pairs"],
                "reverse_n": rev["n_pairs"],
                "faster_direction": key if fwd["median"] < rev["median"] else reverse,
                "lag_ratio": fwd["median"] / max(rev["median"], 0.1),
                "mann_whitney_U": float(u_stat) if np.isfinite(u_stat) else None,
                "mann_whitney_p": float(u_p) if np.isfinite(u_p) else None,
                "asymmetry_significant": bool(u_p < 0.05) if np.isfinite(u_p) else False,
            })

    return {"distributions": results, "asymmetry": asymmetry}


def merge_event_propagation(
    graph: dict,
    event_study_path: str = "data/exp2/event_study_results.csv",
    shock_prop_path: str = "data/exp2/shock_propagation.csv",
) -> dict:
    """Enrich graph with exp2 event-level propagation data."""
    graph = graph.copy()

    # Load event study
    if os.path.exists(event_study_path):
        events = pd.read_csv(event_study_path)
        event_summary = {
            "n_events": len(events),
            "events_with_epu_leadlag": int(events["lead_lag_vs_epu"].notna().sum()),
            "mean_leadlag_vs_epu_days": float(events["lead_lag_vs_epu"].mean()) if events["lead_lag_vs_epu"].notna().any() else None,
            "kalshi_leads_epu_pct": float((events["lead_lag_vs_epu"] < 0).mean()) if events["lead_lag_vs_epu"].notna().any() else None,
            "by_event_type": {},
        }
        for etype in events["event_type"].unique():
            subset = events[events["event_type"] == etype]
            ll = subset["lead_lag_vs_epu"].dropna()
            if len(ll) > 0:
                event_summary["by_event_type"][etype] = {
                    "mean_leadlag_days": float(ll.mean()),
                    "n_events": len(ll),
                }
        graph["event_study"] = event_summary

    # Load shock propagation
    if os.path.exists(shock_prop_path):
        prop = pd.read_csv(shock_prop_path)
        if not prop.empty:
            prop_summary = []
            for _, row in prop.iterrows():
                prop_summary.append({
                    "from_domain": row.get("source_domain", ""),
                    "to_domain": row.get("target_domain", ""),
                    "delay_days": float(row.get("propagation_delay", 0)),
                    "event_type": row.get("event_type", ""),
                })
            graph["shock_propagation"] = prop_summary

    return graph


def visualize_network(graph: dict, output_dir: str = "data/exp1/plots"):
    """Visualize the propagation network."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    os.makedirs(output_dir, exist_ok=True)

    edges = graph["edges"]
    nodes = graph["nodes"]

    # Layout: manual positioning for 4 economics domains
    domain_positions = {
        "inflation": (0, 1),
        "monetary_policy": (1, 1),
        "labor": (0, 0),
        "macro": (1, 0),
    }

    fig, ax = plt.subplots(figsize=(12, 10))

    # Draw edges
    for edge in edges:
        src = edge["source"]
        dst = edge["target"]
        if src not in domain_positions or dst not in domain_positions:
            continue

        x0, y0 = domain_positions[src]
        x1, y1 = domain_positions[dst]

        # Offset for bidirectional edges
        dx, dy = x1 - x0, y1 - y0
        offset = 0.03
        perp_x, perp_y = -dy * offset, dx * offset

        width = max(1, edge["n_pairs"] / 30)
        color = "blue" if edge["median_lag_hours"] <= 6 else ("orange" if edge["median_lag_hours"] <= 12 else "red")

        ax.annotate(
            "",
            xy=(x1 + perp_x, y1 + perp_y),
            xytext=(x0 + perp_x, y0 + perp_y),
            arrowprops=dict(
                arrowstyle="->",
                color=color,
                lw=width,
                connectionstyle="arc3,rad=0.1",
            ),
        )

        # Label: median lag + count
        mx = (x0 + x1) / 2 + perp_x * 3
        my = (y0 + y1) / 2 + perp_y * 3
        ax.text(mx, my, f"{edge['median_lag_hours']:.0f}h\n(n={edge['n_pairs']})",
                fontsize=8, ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.8))

    # Draw nodes
    for node in nodes:
        if node["domain"] not in domain_positions:
            continue
        x, y = domain_positions[node["domain"]]
        size = max(800, node["n_markets"] * 5)
        ax.scatter(x, y, s=size, c="lightblue", edgecolors="black", zorder=5, linewidths=2)
        ax.text(x, y, f"{node['domain']}\n({node['n_markets']} mkts)",
                ha="center", va="center", fontsize=10, fontweight="bold", zorder=6)

    # Legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], color="blue", lw=2, label="Fast (<6h)"),
        Line2D([0], [0], color="orange", lw=2, label="Medium (6-12h)"),
        Line2D([0], [0], color="red", lw=2, label="Slow (>12h)"),
    ]
    ax.legend(handles=legend_elements, loc="upper right", title="Propagation Speed")

    ax.set_xlim(-0.3, 1.3)
    ax.set_ylim(-0.3, 1.3)
    ax.set_title("Information Propagation Network\nKalshi Economics Sub-Domains (Hourly Granger Causality)", fontsize=14)
    ax.set_aspect("equal")
    ax.axis("off")

    plt.tight_layout()
    path = os.path.join(output_dir, "propagation_network.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved {path}")

    # Also plot lag distributions
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    axes = axes.flatten()

    for i, edge in enumerate(sorted(edges, key=lambda e: -e["n_pairs"])):
        if i >= 6:
            break
        ax = axes[i]
        # Reconstruct lag distribution from the significant pairs
        sig_df = pd.read_csv(os.path.join(DATA_DIR, "granger_significant.csv"))
        mask = (sig_df["leader_domain"] == edge["source"]) & (sig_df["follower_domain"] == edge["target"])
        lags = sig_df[mask]["best_lag"].values
        ax.hist(lags, bins=range(0, 26), color="steelblue", edgecolor="black", alpha=0.7)
        ax.axvline(edge["median_lag_hours"], color="red", linestyle="--", label=f"median={edge['median_lag_hours']:.0f}h")
        ax.set_title(f"{edge['source']} → {edge['target']}\n(n={edge['n_pairs']})", fontsize=10)
        ax.set_xlabel("Lag (hours)")
        ax.set_ylabel("Count")
        ax.legend(fontsize=8)

    plt.suptitle("Lag Distributions by Domain Pair", fontsize=14)
    plt.tight_layout()
    path = os.path.join(output_dir, "lag_distributions.png")
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  Saved {path}")


def run_propagation_analysis():
    """Main entry point for propagation network analysis."""
    print("\n" + "=" * 70)
    print("PROPAGATION NETWORK ANALYSIS")
    print("=" * 70)

    sig_df = pd.read_csv(os.path.join(DATA_DIR, "granger_significant.csv"))
    print(f"  Loaded {len(sig_df)} significant Granger pairs")

    # Build graph
    graph = build_domain_graph(sig_df)
    print(f"  Network: {len(graph['nodes'])} nodes, {len(graph['edges'])} directed edges")

    for edge in sorted(graph["edges"], key=lambda e: -e["n_pairs"]):
        print(f"    {edge['source']} → {edge['target']}: "
              f"median={edge['median_lag_hours']:.0f}h, n={edge['n_pairs']}, "
              f"F={edge['mean_f_stat']:.1f}")

    # Node centrality
    print(f"\n  Domain influence scores (higher = faster propagation to more markets):")
    for node in sorted(graph["nodes"], key=lambda n: -n["influence_score"]):
        print(f"    {node['domain']}: influence={node['influence_score']:.1f}, "
              f"receptivity={node['receptivity_score']:.1f}, "
              f"net={node['net_influence']:+.1f}")

    # Lag distributions + asymmetry
    lag_info = compute_lag_distributions(sig_df)
    print(f"\n  Asymmetry analysis (Mann-Whitney U test for directional difference):")
    for a in lag_info["asymmetry"]:
        sig_str = f"p={a['mann_whitney_p']:.4f}" if a["mann_whitney_p"] is not None else "N/A"
        star = " *" if a.get("asymmetry_significant") else ""
        print(f"    {a['forward']}: {a['forward_median_lag']:.0f}h (n={a['forward_n']}) vs "
              f"{a['reverse']}: {a['reverse_median_lag']:.0f}h (n={a['reverse_n']}) → "
              f"faster: {a['faster_direction']} ({sig_str}){star}")

    # Merge event study data
    graph = merge_event_propagation(graph)

    if "event_study" in graph:
        es = graph["event_study"]
        print(f"\n  Event study overlay:")
        print(f"    Kalshi leads EPU in {es.get('kalshi_leads_epu_pct', 0):.0%} of events")
        for etype, info in es.get("by_event_type", {}).items():
            print(f"    {etype}: mean lead-lag = {info['mean_leadlag_days']:.1f} days (n={info['n_events']})")

    # Save
    output = {**graph, "lag_distributions": lag_info}
    with open(os.path.join(DATA_DIR, "propagation_network.json"), "w") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\n  Saved propagation_network.json")

    # Visualize
    visualize_network(graph)

    return output
