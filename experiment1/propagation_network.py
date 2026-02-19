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

# Indicator-level classification: more granular than domain
INDICATOR_MAP = {
    "KXCPI": "CPI", "CPI": "CPI",
    "KXPCE": "PCE",
    "KXPPI": "PPI",
    "KXFED": "Fed Funds", "FED": "Fed Funds",
    "KXFFR": "Fed Funds Rate",
    "KXNFP": "Nonfarm Payrolls",
    "KXJOBLESSCLAIMS": "Jobless Claims",
    "KXUNEMPLOYMENT": "Unemployment",
    "KXGDP": "GDP", "GDP": "GDP",
    "KXRETAILSALES": "Retail Sales",
    "KXISM": "ISM",
    "KXRECESSION": "Recession",
    "KXDEBTCEILING": "Debt Ceiling",
    "KXSHUTDOWN": "Shutdown",
}

INDICATOR_DOMAIN = {
    "CPI": "inflation", "PCE": "inflation", "PPI": "inflation",
    "Fed Funds": "monetary_policy", "Fed Funds Rate": "monetary_policy",
    "Nonfarm Payrolls": "labor", "Jobless Claims": "labor", "Unemployment": "labor",
    "GDP": "macro", "Retail Sales": "macro", "ISM": "macro", "Recession": "macro",
    "Debt Ceiling": "fiscal", "Shutdown": "fiscal",
}


def _extract_indicator(ticker: str) -> str:
    """Map ticker to specific economic indicator."""
    prefix = ticker.split("-")[0] if "-" in ticker else ticker
    if prefix in INDICATOR_MAP:
        return INDICATOR_MAP[prefix]
    for key, ind in INDICATOR_MAP.items():
        if prefix.startswith(key):
            return ind
    return "other"


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


def build_indicator_graph(sig_df: pd.DataFrame, min_pairs: int = 5) -> dict:
    """Build indicator-level directed graph (more granular than domain-level).

    Each node is a specific economic indicator (CPI, Fed Funds, Jobless Claims, GDP, etc.)
    instead of a broad domain (inflation, monetary_policy, labor, macro).

    Args:
        sig_df: Significant Granger pairs with leader_ticker, follower_ticker columns.
        min_pairs: Minimum number of significant pairs for an edge to appear.
    """
    # Classify each ticker to indicator
    df = sig_df.copy()
    df["leader_indicator"] = df["leader_ticker"].apply(_extract_indicator)
    df["follower_indicator"] = df["follower_ticker"].apply(_extract_indicator)

    # Drop "other" indicators
    df = df[(df["leader_indicator"] != "other") & (df["follower_indicator"] != "other")]
    # Drop self-indicator edges
    df = df[df["leader_indicator"] != df["follower_indicator"]]

    # Aggregate by (leader_indicator, follower_indicator)
    edges = {}
    for _, row in df.iterrows():
        key = (row["leader_indicator"], row["follower_indicator"])
        if key not in edges:
            edges[key] = {"lags": [], "f_stats": [], "p_values": []}
        edges[key]["lags"].append(row["best_lag"])
        edges[key]["f_stats"].append(row["f_stat"])
        edges[key]["p_values"].append(row["p_value"])

    graph_edges = []
    for (src, dst), data in edges.items():
        if len(data["lags"]) < min_pairs:
            continue
        lags = np.array(data["lags"])
        graph_edges.append({
            "source": src,
            "target": dst,
            "n_pairs": len(data["lags"]),
            "median_lag_hours": float(np.median(lags)),
            "mean_lag_hours": float(np.mean(lags)),
            "lag_std": float(np.std(lags)),
            "mean_f_stat": float(np.mean(data["f_stats"])),
            "min_p_value": float(np.min(data["p_values"])),
        })

    # Nodes
    all_indicators = set()
    for e in graph_edges:
        all_indicators.add(e["source"])
        all_indicators.add(e["target"])

    nodes = []
    for ind in sorted(all_indicators):
        n_markets = len(df[
            (df["leader_indicator"] == ind) | (df["follower_indicator"] == ind)
        ]["leader_ticker"].unique())

        influence = sum(
            e["n_pairs"] / max(e["median_lag_hours"], 1)
            for e in graph_edges if e["source"] == ind
        )
        receptivity = sum(
            e["n_pairs"] / max(e["median_lag_hours"], 1)
            for e in graph_edges if e["target"] == ind
        )

        nodes.append({
            "domain": ind,
            "parent_domain": INDICATOR_DOMAIN.get(ind, "other"),
            "n_outgoing": sum(1 for e in graph_edges if e["source"] == ind),
            "n_incoming": sum(1 for e in graph_edges if e["target"] == ind),
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


def visualize_network(graph: dict, output_dir: str = "data/exp1/plots",
                      indicator_graph: dict = None):
    """Visualize the propagation network as polished static PNG + interactive HTML."""
    os.makedirs(output_dir, exist_ok=True)

    edges = graph["edges"]
    nodes = graph["nodes"]

    _plot_static_network(nodes, edges, output_dir, suffix="", title_extra="Domain-Level")
    _plot_lag_distributions(edges, output_dir)
    _build_interactive_html(nodes, edges, graph, output_dir, suffix="")

    # Indicator-level graph (more nodes)
    if indicator_graph and indicator_graph["nodes"]:
        _plot_static_network(
            indicator_graph["nodes"], indicator_graph["edges"], output_dir,
            suffix="_indicators", title_extra="Indicator-Level",
        )
        _build_interactive_html(
            indicator_graph["nodes"], indicator_graph["edges"], graph, output_dir,
            suffix="_indicators",
        )


def _plot_static_network(nodes: list, edges: list, output_dir: str,
                         suffix: str = "", title_extra: str = ""):
    """Polished static matplotlib network plot."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    import matplotlib.patheffects as pe

    # Color by parent domain (or domain name for domain-level graph)
    DOMAIN_COLORS = {
        "inflation": "#E74C3C", "CPI": "#E74C3C", "PCE": "#C0392B", "PPI": "#E67E22",
        "monetary_policy": "#3498DB", "Fed Funds": "#3498DB", "Fed Funds Rate": "#2980B9",
        "labor": "#2ECC71", "Jobless Claims": "#2ECC71", "Nonfarm Payrolls": "#27AE60", "Unemployment": "#1ABC9C",
        "macro": "#F39C12", "GDP": "#F39C12", "Retail Sales": "#D4AC0D", "ISM": "#E67E22", "Recession": "#D35400",
        "fiscal": "#9B59B6", "Debt Ceiling": "#9B59B6", "Shutdown": "#8E44AD",
    }

    # Dynamic layout based on node count
    n_nodes = len(nodes)
    domain_names = [n["domain"] for n in nodes]

    # Diamond layout for the 4 standard domains; circular for everything else
    standard_positions = {
        "inflation": (0.5, 1.0), "monetary_policy": (1.0, 0.5),
        "labor": (0.0, 0.5), "macro": (0.5, 0.0),
    }
    if n_nodes <= 4 and all(d in standard_positions for d in domain_names):
        domain_positions = {d: standard_positions[d] for d in domain_names}
    else:
        import math
        domain_positions = {}
        for i, name in enumerate(sorted(domain_names)):
            angle = 2 * math.pi * i / n_nodes - math.pi / 2
            domain_positions[name] = (0.5 + 0.42 * math.cos(angle), 0.5 + 0.42 * math.sin(angle))

    DOMAIN_LABELS = {
        "inflation": "Inflation\n(CPI, PCE, PPI)",
        "monetary_policy": "Monetary Policy\n(Fed Funds, FOMC)",
        "labor": "Labor\n(NFP, Jobless Claims)",
        "macro": "Macro\n(GDP, Retail Sales, ISM)",
    }

    fig, ax = plt.subplots(figsize=(14, 11))
    fig.patch.set_facecolor("#FAFAFA")
    ax.set_facecolor("#FAFAFA")

    # Draw edges first (behind nodes)
    for edge in sorted(edges, key=lambda e: e["n_pairs"]):
        src = edge["source"]
        dst = edge["target"]
        if src not in domain_positions or dst not in domain_positions:
            continue

        x0, y0 = domain_positions[src]
        x1, y1 = domain_positions[dst]

        # Offset for bidirectional edges
        dx, dy = x1 - x0, y1 - y0
        length = (dx**2 + dy**2) ** 0.5
        if length < 0.001:
            continue
        offset = 0.025
        perp_x, perp_y = -dy / length * offset, dx / length * offset

        # Arrow width proportional to n_pairs
        max_pairs = max(e["n_pairs"] for e in edges)
        width = 1.0 + edge["n_pairs"] / max(max_pairs / 5, 1)
        lag = edge["median_lag_hours"]

        # Color by speed
        if lag <= 4:
            color = "#2980B9"
        elif lag <= 7:
            color = "#E67E22"
        else:
            color = "#C0392B"

        # Shorten arrows proportional to layout
        shrink = 0.06 if n_nodes <= 4 else 0.08
        ax0 = x0 + perp_x + dx * shrink
        ay0 = y0 + perp_y + dy * shrink
        ax1 = x1 + perp_x - dx * shrink
        ay1 = y1 + perp_y - dy * shrink

        ax.annotate(
            "",
            xy=(ax1, ay1),
            xytext=(ax0, ay0),
            arrowprops=dict(
                arrowstyle="->,head_length=0.4,head_width=0.25",
                color=color,
                lw=width,
                connectionstyle="arc3,rad=0.15",
                alpha=0.85,
            ),
        )

        # Edge label
        mx = (x0 + x1) / 2 + perp_x * 4.5
        my = (y0 + y1) / 2 + perp_y * 4.5
        label = f"{lag:.0f}h  (n={edge['n_pairs']})"
        fontsize = 9 if n_nodes <= 5 else 7
        ax.text(
            mx, my, label,
            fontsize=fontsize, ha="center", va="center", fontweight="bold",
            color=color,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor=color, alpha=0.9, linewidth=0.8),
        )

    # Draw nodes
    for node in nodes:
        domain = node["domain"]
        if domain not in domain_positions:
            continue
        x, y = domain_positions[domain]
        color = DOMAIN_COLORS.get(domain, DOMAIN_COLORS.get(node.get("parent_domain", ""), "#95A5A6"))
        size = 1200 + node["n_markets"] * 8 if n_nodes <= 5 else 800 + node["n_markets"] * 5

        ax.scatter(x, y, s=size, c=color, edgecolors="white", zorder=5, linewidths=3, alpha=0.9)

        # Node label
        label = DOMAIN_LABELS.get(domain, domain)
        node_fontsize = 11 if n_nodes <= 5 else 9
        txt = ax.text(
            x, y + 0.002, label,
            ha="center", va="center", fontsize=node_fontsize, fontweight="bold", color="white", zorder=6,
        )
        txt.set_path_effects([pe.withStroke(linewidth=2, foreground="black")])

        # Sub-label
        net = node.get("net_influence", 0)
        arrow = "+" if net > 0 else ""
        sub = f"{node['n_markets']} mkts | net: {arrow}{net:.1f}"
        sub_fontsize = 8 if n_nodes <= 5 else 7
        ax.text(
            x, y - 0.07, sub,
            ha="center", va="center", fontsize=sub_fontsize, color="#555",
            bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.8, edgecolor="#CCC"),
            zorder=6,
        )

    # Legend
    legend_elements = [
        Line2D([0], [0], color="#2980B9", lw=3, label="Fast (< 5h)"),
        Line2D([0], [0], color="#E67E22", lw=3, label="Medium (5-7h)"),
        Line2D([0], [0], color="#C0392B", lw=3, label="Slow (> 7h)"),
    ]
    ax.legend(
        handles=legend_elements, loc="lower right", title="Propagation Speed",
        fontsize=10, title_fontsize=11, framealpha=0.95, edgecolor="#CCC",
    )

    ax.set_xlim(-0.15, 1.15)
    ax.set_ylim(-0.15, 1.15)
    title_label = title_extra + " " if title_extra else ""
    ax.set_title(
        f"Information Propagation Network ({title_label}View)\n"
        "Kalshi Economics  |  Hourly Granger Causality (ADF-stationary, Bonferroni p<0.01)",
        fontsize=14, fontweight="bold", pad=20,
    )
    ax.set_aspect("equal")
    ax.axis("off")

    plt.tight_layout()
    path = os.path.join(output_dir, f"propagation_network{suffix}.png")
    plt.savefig(path, dpi=200, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print(f"  Saved {path}")


def _plot_lag_distributions(edges: list, output_dir: str):
    """Lag distribution histograms per domain pair."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    sig_df = pd.read_csv(os.path.join(DATA_DIR, "granger_significant.csv"))

    sorted_edges = sorted(edges, key=lambda e: -e["n_pairs"])[:6]
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    axes = axes.flatten()

    for i, edge in enumerate(sorted_edges):
        ax = axes[i]
        mask = (sig_df["leader_domain"] == edge["source"]) & (sig_df["follower_domain"] == edge["target"])
        lags = sig_df[mask]["best_lag"].values
        ax.hist(lags, bins=range(0, 26), color="steelblue", edgecolor="white", alpha=0.8)
        ax.axvline(edge["median_lag_hours"], color="red", linestyle="--", lw=2,
                    label=f"median = {edge['median_lag_hours']:.0f}h")
        ax.set_title(f"{edge['source']}  ->  {edge['target']}  (n={edge['n_pairs']})", fontsize=11, fontweight="bold")
        ax.set_xlabel("Lag (hours)")
        ax.set_ylabel("Count")
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.2)

    # Hide unused subplots
    for j in range(len(sorted_edges), 6):
        axes[j].set_visible(False)

    plt.suptitle("Lag Distributions by Domain Pair", fontsize=14, fontweight="bold")
    plt.tight_layout()
    path = os.path.join(output_dir, "lag_distributions.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved {path}")


def _build_interactive_html(nodes: list, edges: list, graph: dict, output_dir: str,
                            suffix: str = ""):
    """Build a self-contained interactive HTML network visualization using D3.js."""

    # Prepare data for the template
    node_data = []
    DOMAIN_COLORS = {
        "inflation": "#E74C3C", "CPI": "#E74C3C", "PCE": "#C0392B", "PPI": "#E67E22",
        "monetary_policy": "#3498DB", "Fed Funds": "#3498DB", "Fed Funds Rate": "#2980B9",
        "labor": "#2ECC71", "Jobless Claims": "#2ECC71", "Nonfarm Payrolls": "#27AE60", "Unemployment": "#1ABC9C",
        "macro": "#F39C12", "GDP": "#F39C12", "Retail Sales": "#D4AC0D", "ISM": "#E67E22", "Recession": "#D35400",
        "fiscal": "#9B59B6", "Debt Ceiling": "#9B59B6", "Shutdown": "#8E44AD",
    }

    for node in nodes:
        d = node["domain"]
        parent = node.get("parent_domain", d)
        node_data.append({
            "id": d,
            "label": d.replace("_", " ").title(),
            "parent": parent,
            "markets": node["n_markets"],
            "influence": node.get("influence_score", 0),
            "receptivity": node.get("receptivity_score", 0),
            "net": node.get("net_influence", 0),
            "color": DOMAIN_COLORS.get(d, DOMAIN_COLORS.get(parent, "#95A5A6")),
        })

    edge_data = []
    for edge in edges:
        lag = edge["median_lag_hours"]
        if lag <= 4:
            color = "#2980B9"
        elif lag <= 7:
            color = "#E67E22"
        else:
            color = "#C0392B"
        edge_data.append({
            "source": edge["source"],
            "target": edge["target"],
            "lag": lag,
            "n_pairs": edge["n_pairs"],
            "f_stat": round(edge["mean_f_stat"], 1),
            "color": color,
        })

    # Event study overlay
    event_info = ""
    if "event_study" in graph:
        es = graph["event_study"]
        event_items = []
        for etype, info in es.get("by_event_type", {}).items():
            sign = "+" if info["mean_leadlag_days"] > 0 else ""
            event_items.append(f'<li><b>{etype}</b>: {sign}{info["mean_leadlag_days"]:.1f} days vs EPU (n={info["n_events"]})</li>')
        if event_items:
            event_info = "<ul>" + "".join(event_items) + "</ul>"

    nodes_json = json.dumps(node_data)
    edges_json = json.dumps(edge_data)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Kalshi Information Propagation Network</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #1a1a2e; color: #eee; }}
  #header {{ padding: 20px 30px 10px; text-align: center; }}
  #header h1 {{ font-size: 22px; color: #fff; margin-bottom: 4px; }}
  #header p {{ font-size: 13px; color: #888; }}
  #container {{ display: flex; height: calc(100vh - 80px); }}
  #graph {{ flex: 1; position: relative; }}
  svg {{ width: 100%; height: 100%; }}
  #sidebar {{ width: 320px; background: #16213e; padding: 20px; overflow-y: auto; border-left: 1px solid #333; }}
  #sidebar h2 {{ font-size: 16px; margin-bottom: 12px; color: #fff; border-bottom: 1px solid #444; padding-bottom: 8px; }}
  #sidebar h3 {{ font-size: 13px; margin: 14px 0 6px; color: #aaa; text-transform: uppercase; letter-spacing: 1px; }}
  .stat {{ display: flex; justify-content: space-between; padding: 4px 0; font-size: 13px; }}
  .stat-label {{ color: #888; }}
  .stat-value {{ color: #fff; font-weight: 600; }}
  .edge-card {{ background: #1a1a2e; border-radius: 6px; padding: 10px; margin-bottom: 8px; border-left: 3px solid; }}
  .edge-card .title {{ font-weight: 600; font-size: 13px; margin-bottom: 4px; }}
  .edge-card .detail {{ font-size: 11px; color: #999; }}
  .legend {{ margin-top: 16px; }}
  .legend-item {{ display: flex; align-items: center; gap: 8px; margin-bottom: 6px; font-size: 12px; }}
  .legend-dot {{ width: 12px; height: 12px; border-radius: 50%; }}
  .legend-line {{ width: 24px; height: 3px; border-radius: 2px; }}
  #tooltip {{ position: absolute; background: rgba(22,33,62,0.95); border: 1px solid #444; border-radius: 6px; padding: 10px 14px; font-size: 12px; pointer-events: none; opacity: 0; transition: opacity 0.15s; max-width: 250px; }}
  #tooltip .tt-title {{ font-weight: 700; font-size: 14px; margin-bottom: 4px; }}
  #tooltip .tt-row {{ display: flex; justify-content: space-between; gap: 16px; padding: 1px 0; }}
  #event-info {{ font-size: 12px; color: #aaa; margin-top: 8px; }}
  #event-info ul {{ padding-left: 16px; }}
  #event-info li {{ margin-bottom: 3px; }}
  marker {{ overflow: visible; }}
</style>
</head>
<body>
<div id="header">
  <h1>Information Propagation Network</h1>
  <p>Kalshi Economics Sub-Domains &middot; Hourly Granger Causality (ADF-stationary, Bonferroni p&lt;0.01) &middot; Drag nodes to rearrange</p>
</div>
<div id="container">
  <div id="graph">
    <svg></svg>
    <div id="tooltip"></div>
  </div>
  <div id="sidebar">
    <h2>Network Summary</h2>
    <div class="stat"><span class="stat-label">Significant pairs</span><span class="stat-value">446</span></div>
    <div class="stat"><span class="stat-label">Domains</span><span class="stat-value">4</span></div>
    <div class="stat"><span class="stat-label">Directed edges</span><span class="stat-value">6</span></div>

    <h3>Edges (by pair count)</h3>
    <div id="edge-cards"></div>

    <h3>Speed Legend</h3>
    <div class="legend">
      <div class="legend-item"><div class="legend-line" style="background:#2980B9"></div> Fast (&lt; 5h)</div>
      <div class="legend-item"><div class="legend-line" style="background:#E67E22"></div> Medium (5-7h)</div>
      <div class="legend-item"><div class="legend-line" style="background:#C0392B"></div> Slow (&gt; 7h)</div>
    </div>

    <h3>Event Study Overlay</h3>
    <div id="event-info">Kalshi lead-lag vs EPU (daily):{event_info if event_info else '<p style="color:#666">No event data</p>'}</div>
  </div>
</div>

<script>
const nodes = {nodes_json};
const edges = {edges_json};

const svg = document.querySelector('svg');
const width = svg.parentElement.clientWidth;
const height = svg.parentElement.clientHeight;
svg.setAttribute('viewBox', `0 0 ${{width}} ${{height}}`);

// Build edge cards
const cardsEl = document.getElementById('edge-cards');
edges.sort((a,b) => b.n_pairs - a.n_pairs).forEach(e => {{
  const card = document.createElement('div');
  card.className = 'edge-card';
  card.style.borderColor = e.color;
  card.innerHTML = `<div class="title" style="color:${{e.color}}">${{e.source.replace('_',' ')}} &rarr; ${{e.target.replace('_',' ')}}</div>
    <div class="detail">${{e.lag}}h median lag &middot; ${{e.n_pairs}} pairs &middot; F=${{e.f_stat}}</div>`;
  cardsEl.appendChild(card);
}});

// Position nodes: diamond for 4, circular for more
const cx = width / 2, cy = height / 2, spread = Math.min(width, height) * 0.32;
const fixedPositions = {{
  'inflation':       {{ x: cx,          y: cy - spread }},
  'monetary_policy': {{ x: cx + spread, y: cy }},
  'labor':           {{ x: cx - spread, y: cy }},
  'macro':           {{ x: cx,          y: cy + spread }},
}};
if (nodes.length <= 4) {{
  nodes.forEach(n => {{ n.x = fixedPositions[n.id]?.x || cx; n.y = fixedPositions[n.id]?.y || cy; }});
}} else {{
  // Circular layout
  const sorted = [...nodes].sort((a,b) => a.id.localeCompare(b.id));
  sorted.forEach((n, i) => {{
    const angle = (2 * Math.PI * i / nodes.length) - Math.PI / 2;
    n.x = cx + spread * 1.1 * Math.cos(angle);
    n.y = cy + spread * 1.1 * Math.sin(angle);
  }});
}}

// Arrowhead markers
const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
edges.forEach((e, i) => {{
  const marker = document.createElementNS('http://www.w3.org/2000/svg', 'marker');
  marker.setAttribute('id', `arrow-${{i}}`);
  marker.setAttribute('viewBox', '0 0 10 10');
  marker.setAttribute('refX', '10'); marker.setAttribute('refY', '5');
  marker.setAttribute('markerWidth', '8'); marker.setAttribute('markerHeight', '8');
  marker.setAttribute('orient', 'auto-start-reverse');
  const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
  path.setAttribute('d', 'M 0 0 L 10 5 L 0 10 z');
  path.setAttribute('fill', e.color);
  marker.appendChild(path);
  defs.appendChild(marker);
}});
svg.appendChild(defs);

// Draw edges as curved paths
const edgeGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
svg.appendChild(edgeGroup);

const edgeEls = edges.map((e, i) => {{
  const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
  path.setAttribute('stroke', e.color);
  path.setAttribute('stroke-width', Math.max(2, e.n_pairs / 20));
  path.setAttribute('fill', 'none');
  path.setAttribute('opacity', '0.7');
  path.setAttribute('marker-end', `url(#arrow-${{i}})`);
  edgeGroup.appendChild(path);
  return path;
}});

// Edge labels
const labelGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
svg.appendChild(labelGroup);

const edgeLabelEls = edges.map(e => {{
  const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
  text.setAttribute('font-size', '12');
  text.setAttribute('font-weight', 'bold');
  text.setAttribute('fill', e.color);
  text.setAttribute('text-anchor', 'middle');
  text.setAttribute('dy', '-6');
  text.textContent = `${{e.lag}}h (n=${{e.n_pairs}})`;
  labelGroup.appendChild(text);
  return text;
}});

// Draw nodes
const nodeGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
svg.appendChild(nodeGroup);

const nodeRadius = n => 30 + n.markets * 0.3;

const nodeEls = nodes.map(n => {{
  const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
  g.style.cursor = 'grab';

  // Glow
  const glow = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
  glow.setAttribute('r', nodeRadius(n) + 8);
  glow.setAttribute('fill', n.color);
  glow.setAttribute('opacity', '0.15');
  g.appendChild(glow);

  // Main circle
  const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
  circle.setAttribute('r', nodeRadius(n));
  circle.setAttribute('fill', n.color);
  circle.setAttribute('stroke', '#fff');
  circle.setAttribute('stroke-width', '3');
  g.appendChild(circle);

  // Label
  const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
  text.setAttribute('text-anchor', 'middle');
  text.setAttribute('fill', '#fff');
  text.setAttribute('font-weight', 'bold');
  text.setAttribute('font-size', '13');
  text.setAttribute('dy', '-4');
  text.textContent = n.label;
  text.style.pointerEvents = 'none';
  g.appendChild(text);

  // Sub-label
  const sub = document.createElementNS('http://www.w3.org/2000/svg', 'text');
  sub.setAttribute('text-anchor', 'middle');
  sub.setAttribute('fill', 'rgba(255,255,255,0.7)');
  sub.setAttribute('font-size', '10');
  sub.setAttribute('dy', '12');
  sub.textContent = `${{n.markets}} mkts`;
  sub.style.pointerEvents = 'none';
  g.appendChild(sub);

  nodeGroup.appendChild(g);
  return {{ g, circle, glow, node: n }};
}});

// Tooltip
const tooltip = document.getElementById('tooltip');

nodeEls.forEach(el => {{
  el.g.addEventListener('mouseenter', ev => {{
    const n = el.node;
    const sign = n.net > 0 ? '+' : '';
    tooltip.innerHTML = `<div class="tt-title" style="color:${{n.color}}">${{n.label}}</div>
      <div class="tt-row"><span>Markets</span><span>${{n.markets}}</span></div>
      <div class="tt-row"><span>Influence</span><span>${{n.influence.toFixed(1)}}</span></div>
      <div class="tt-row"><span>Receptivity</span><span>${{n.receptivity.toFixed(1)}}</span></div>
      <div class="tt-row"><span>Net influence</span><span>${{sign}}${{n.net.toFixed(1)}}</span></div>`;
    tooltip.style.opacity = 1;
  }});
  el.g.addEventListener('mousemove', ev => {{
    tooltip.style.left = (ev.clientX - svg.parentElement.getBoundingClientRect().left + 15) + 'px';
    tooltip.style.top = (ev.clientY - svg.parentElement.getBoundingClientRect().top - 10) + 'px';
  }});
  el.g.addEventListener('mouseleave', () => {{ tooltip.style.opacity = 0; }});
}});

// Drag behavior
let dragNode = null, dragOffset = {{x:0, y:0}};
nodeEls.forEach(el => {{
  el.g.addEventListener('mousedown', ev => {{
    dragNode = el.node;
    dragOffset.x = ev.clientX - el.node.x;
    dragOffset.y = ev.clientY - el.node.y;
    el.g.style.cursor = 'grabbing';
    ev.preventDefault();
  }});
}});
document.addEventListener('mousemove', ev => {{
  if (!dragNode) return;
  dragNode.x = ev.clientX - dragOffset.x;
  dragNode.y = ev.clientY - dragOffset.y;
  updatePositions();
}});
document.addEventListener('mouseup', () => {{
  if (dragNode) {{
    nodeEls.find(el => el.node === dragNode).g.style.cursor = 'grab';
    dragNode = null;
  }}
}});

function updatePositions() {{
  const nodeMap = {{}};
  nodes.forEach(n => nodeMap[n.id] = n);

  // Update node positions
  nodeEls.forEach(el => {{
    el.g.setAttribute('transform', `translate(${{el.node.x}}, ${{el.node.y}})`);
  }});

  // Update edge curves
  edges.forEach((e, i) => {{
    const s = nodeMap[e.source], t = nodeMap[e.target];
    const dx = t.x - s.x, dy = t.y - s.y;
    const len = Math.sqrt(dx*dx + dy*dy);
    const nx = -dy/len, ny = dx/len;
    const off = 25;  // curve offset for bidirectional
    const r = 40;    // shorten to not overlap node circles

    const sx = s.x + dx/len * r + nx * off;
    const sy = s.y + dy/len * r + ny * off;
    const tx = t.x - dx/len * r + nx * off;
    const ty = t.y - dy/len * r + ny * off;
    const mx = (s.x + t.x) / 2 + nx * off * 2.5;
    const my = (s.y + t.y) / 2 + ny * off * 2.5;

    edgeEls[i].setAttribute('d', `M ${{sx}} ${{sy}} Q ${{mx}} ${{my}} ${{tx}} ${{ty}}`);

    // Label at midpoint of curve
    const lx = (sx + 2*mx + tx) / 4;
    const ly = (sy + 2*my + ty) / 4;
    edgeLabelEls[i].setAttribute('x', lx);
    edgeLabelEls[i].setAttribute('y', ly);
  }});
}}

updatePositions();
</script>
</body>
</html>"""

    path = os.path.join(output_dir, f"propagation_network{suffix}.html")
    with open(path, "w") as f:
        f.write(html)
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

    # Indicator-level graph (more nodes)
    ind_graph = build_indicator_graph(sig_df, min_pairs=3)
    print(f"\n  Indicator-level network: {len(ind_graph['nodes'])} nodes, {len(ind_graph['edges'])} directed edges")
    for edge in sorted(ind_graph["edges"], key=lambda e: -e["n_pairs"]):
        print(f"    {edge['source']} -> {edge['target']}: "
              f"median={edge['median_lag_hours']:.0f}h, n={edge['n_pairs']}, "
              f"F={edge['mean_f_stat']:.1f}")

    # Merge event study data
    graph = merge_event_propagation(graph)

    if "event_study" in graph:
        es = graph["event_study"]
        print(f"\n  Event study overlay:")
        print(f"    Kalshi leads EPU in {es.get('kalshi_leads_epu_pct', 0):.0%} of events")
        for etype, info in es.get("by_event_type", {}).items():
            print(f"    {etype}: mean lead-lag = {info['mean_leadlag_days']:.1f} days (n={info['n_events']})")

    # Shock-regime propagation analysis
    print("\n  --- Shock-Regime Propagation Analysis ---")
    shock_analysis = analyze_shock_regime_propagation(sig_df)
    if shock_analysis:
        for key, val in shock_analysis.items():
            if isinstance(val, dict) and "median_lag" in val:
                print(f"    {key}: median_lag={val['median_lag']}h, n={val['n_pairs']}")

    # Save
    output = {
        **graph,
        "lag_distributions": lag_info,
        "indicator_graph": ind_graph,
        "shock_regime_analysis": shock_analysis,
    }
    with open(os.path.join(DATA_DIR, "propagation_network.json"), "w") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\n  Saved propagation_network.json")

    # Visualize
    visualize_network(graph, indicator_graph=ind_graph)

    return output


def analyze_shock_regime_propagation(sig_df: pd.DataFrame) -> dict:
    """Analyze whether information propagation speeds change during shock periods.

    Splits Granger pairs by whether they overlap with known economic shock events
    (surprise CPI, surprise FOMC, tariff shocks) and compares median lags.

    Returns dict with shock vs calm comparison per domain pair.
    """
    from experiment2.event_study import get_economic_events

    events = get_economic_events()
    surprise_events = events[events["surprise"] == True]

    if surprise_events.empty or sig_df.empty:
        return {"note": "insufficient_data"}

    # Define shock windows: +/- 3 days around each surprise event
    shock_windows = []
    for _, event in surprise_events.iterrows():
        event_date = pd.Timestamp(event["date"])
        shock_windows.append((event_date - pd.Timedelta(days=3), event_date + pd.Timedelta(days=3)))

    # For each Granger pair, determine if the pair's markets overlapped with any shock window
    # We use the leader/follower tickers' open/close times from the markets CSV
    markets_path = os.path.join(DATA_DIR, "markets.csv")
    if not os.path.exists(markets_path):
        # Fall back: split by lag magnitude (proxy for volatility regime)
        return _analyze_by_lag_percentile(sig_df)

    markets_df = pd.read_csv(markets_path)
    markets_df["open_time"] = pd.to_datetime(markets_df["open_time"], format="ISO8601", errors="coerce")
    markets_df["close_time"] = pd.to_datetime(markets_df["close_time"], format="ISO8601", errors="coerce")

    ticker_times = {}
    for _, row in markets_df.iterrows():
        if pd.notna(row["open_time"]) and pd.notna(row["close_time"]):
            ticker_times[row["ticker"]] = (
                row["open_time"].tz_localize(None) if row["open_time"].tzinfo else row["open_time"],
                row["close_time"].tz_localize(None) if row["close_time"].tzinfo else row["close_time"],
            )

    # Classify each pair as shock-period or calm-period
    shock_pairs = []
    calm_pairs = []

    for _, row in sig_df.iterrows():
        leader_times = ticker_times.get(row["leader_ticker"])
        follower_times = ticker_times.get(row["follower_ticker"])

        if leader_times is None or follower_times is None:
            calm_pairs.append(row)
            continue

        # Overlap period of the two markets
        overlap_start = max(leader_times[0], follower_times[0])
        overlap_end = min(leader_times[1], follower_times[1])

        # Check if overlap intersects any shock window
        is_shock = False
        for shock_start, shock_end in shock_windows:
            shock_start = shock_start.tz_localize(None) if shock_start.tzinfo else shock_start
            shock_end = shock_end.tz_localize(None) if shock_end.tzinfo else shock_end
            if overlap_start <= shock_end and overlap_end >= shock_start:
                is_shock = True
                break

        if is_shock:
            shock_pairs.append(row)
        else:
            calm_pairs.append(row)

    shock_df = pd.DataFrame(shock_pairs) if shock_pairs else pd.DataFrame()
    calm_df = pd.DataFrame(calm_pairs) if calm_pairs else pd.DataFrame()

    result = {
        "n_shock_pairs": len(shock_df),
        "n_calm_pairs": len(calm_df),
        "n_surprise_events": len(surprise_events),
    }

    # Compare lags for key domain pairs
    for src, dst in [("inflation", "monetary_policy"), ("monetary_policy", "inflation"),
                     ("macro", "inflation"), ("inflation", "macro"),
                     ("labor", "inflation"), ("inflation", "labor")]:
        key = f"{src}_to_{dst}"

        shock_lags = shock_df[
            (shock_df["leader_domain"] == src) & (shock_df["follower_domain"] == dst)
        ]["best_lag"] if not shock_df.empty else pd.Series(dtype=float)

        calm_lags = calm_df[
            (calm_df["leader_domain"] == src) & (calm_df["follower_domain"] == dst)
        ]["best_lag"] if not calm_df.empty else pd.Series(dtype=float)

        entry = {
            "n_shock": len(shock_lags),
            "n_calm": len(calm_lags),
        }

        if len(shock_lags) >= 3:
            entry["shock_median_lag"] = float(shock_lags.median())
            entry["shock_mean_lag"] = float(shock_lags.mean())
        if len(calm_lags) >= 3:
            entry["calm_median_lag"] = float(calm_lags.median())
            entry["calm_mean_lag"] = float(calm_lags.mean())

        # Mann-Whitney U test if enough samples
        if len(shock_lags) >= 5 and len(calm_lags) >= 5:
            u_stat, u_p = scipy_stats.mannwhitneyu(shock_lags, calm_lags, alternative="two-sided")
            entry["mann_whitney_U"] = float(u_stat)
            entry["mann_whitney_p"] = float(u_p)
            entry["significant"] = u_p < 0.05

        result[key] = entry

    # Overall comparison
    if len(shock_df) >= 10 and len(calm_df) >= 10:
        result["overall"] = {
            "shock_median_lag": float(shock_df["best_lag"].median()),
            "calm_median_lag": float(calm_df["best_lag"].median()),
            "shock_mean_lag": float(shock_df["best_lag"].mean()),
            "calm_mean_lag": float(calm_df["best_lag"].mean()),
        }
        u_stat, u_p = scipy_stats.mannwhitneyu(
            shock_df["best_lag"], calm_df["best_lag"], alternative="two-sided"
        )
        result["overall"]["mann_whitney_U"] = float(u_stat)
        result["overall"]["mann_whitney_p"] = float(u_p)
        result["overall"]["significant"] = u_p < 0.05

    return result


def _analyze_by_lag_percentile(sig_df: pd.DataFrame) -> dict:
    """Fallback: split pairs by F-stat magnitude (proxy for signal strength)."""
    median_f = sig_df["f_stat"].median()
    strong = sig_df[sig_df["f_stat"] >= median_f]
    weak = sig_df[sig_df["f_stat"] < median_f]
    return {
        "note": "fallback_f_stat_split",
        "strong_signal_median_lag": float(strong["best_lag"].median()),
        "weak_signal_median_lag": float(weak["best_lag"].median()),
        "n_strong": len(strong),
        "n_weak": len(weak),
    }
