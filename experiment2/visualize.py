"""
experiment2/visualize.py

Generate all plots for Experiment 2: Kalshi Uncertainty Index.
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

DATA_DIR = "data/exp2"
PLOTS_DIR = os.path.join(DATA_DIR, "plots")


def setup():
    os.makedirs(PLOTS_DIR, exist_ok=True)
    plt.style.use("seaborn-v0_8-whitegrid")
    plt.rcParams.update({"figure.dpi": 150, "savefig.bbox": "tight"})


def plot_kui_time_series(
    kui: pd.Series,
    domain_indices: dict,
    filename: str = "kui_time_series.png",
):
    """Plot KUI aggregate and domain sub-indices over time."""
    fig, axes = plt.subplots(2, 1, figsize=(14, 10), sharex=True)

    # Top: Aggregate KUI
    ax = axes[0]
    kui_clean = kui.dropna()
    if not kui_clean.empty:
        ax.plot(kui_clean.index, kui_clean.values, "b-", linewidth=1.5, label="KUI (aggregate)")
        ax.axhline(y=100, color="gray", linestyle="--", alpha=0.5)
        ax.set_ylabel("KUI (normalized, mean=100)")
        ax.set_title("Kalshi Uncertainty Index (KUI)")
        ax.legend()

    # Bottom: Domain sub-indices
    ax = axes[1]
    colors = plt.cm.Set2(np.linspace(0, 1, len(domain_indices)))
    for (domain, series), color in zip(sorted(domain_indices.items()), colors):
        clean = series.dropna()
        if len(clean) > 5:
            ax.plot(clean.index, clean.values, color=color, linewidth=1, alpha=0.8,
                    label=domain)

    ax.axhline(y=100, color="gray", linestyle="--", alpha=0.5)
    ax.set_ylabel("Domain Sub-Index (normalized)")
    ax.set_xlabel("Date")
    ax.set_title("KUI Domain Decomposition")
    ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left", fontsize=8)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))

    path = os.path.join(PLOTS_DIR, filename)
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved {path}")


def plot_kui_vs_benchmarks(
    kui: pd.Series,
    epu: pd.Series,
    vix: pd.Series,
    filename: str = "kui_vs_benchmarks.png",
):
    """Overlay KUI with EPU and VIX (all normalized)."""
    fig, ax1 = plt.subplots(figsize=(14, 6))

    # KUI
    kui_clean = kui.dropna()
    if not kui_clean.empty:
        ax1.plot(kui_clean.index, kui_clean.values, "b-", linewidth=1.5, label="KUI", alpha=0.9)

    # EPU
    epu_clean = epu.dropna()
    if not epu_clean.empty:
        ax1.plot(epu_clean.index, epu_clean.values, "r-", linewidth=1, label="EPU", alpha=0.7)

    ax1.set_ylabel("Index Value (normalized)")
    ax1.set_xlabel("Date")
    ax1.set_title("KUI vs EPU vs VIX")

    # VIX on secondary axis
    ax2 = ax1.twinx()
    vix_clean = vix.dropna()
    if not vix_clean.empty:
        ax2.plot(vix_clean.index, vix_clean.values, "g-", linewidth=1, label="VIX", alpha=0.7)
        ax2.set_ylabel("VIX", color="green")

    # Combined legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")

    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))

    path = os.path.join(PLOTS_DIR, filename)
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved {path}")


def plot_correlation_heatmap(
    corr_results: pd.DataFrame,
    filename: str = "correlation_heatmap.png",
):
    """Plot correlation heatmap between KUI, EPU, VIX."""
    # Extract Pearson correlations
    pearson = corr_results[corr_results["method"] == "pearson"]

    if pearson.empty:
        return

    # Build correlation matrix
    labels = ["KUI", "EPU", "VIX"]
    corr_matrix = np.eye(3)

    for _, row in pearson.iterrows():
        pair = row["pair"]
        val = row["correlation"]
        if np.isnan(val):
            continue
        a, b = pair.split("-")
        i, j = labels.index(a), labels.index(b)
        corr_matrix[i, j] = val
        corr_matrix[j, i] = val

    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(corr_matrix, cmap="RdBu_r", vmin=-1, vmax=1)

    ax.set_xticks(range(3))
    ax.set_yticks(range(3))
    ax.set_xticklabels(labels)
    ax.set_yticklabels(labels)

    # Annotate
    for i in range(3):
        for j in range(3):
            ax.text(j, i, f"{corr_matrix[i, j]:.3f}",
                    ha="center", va="center", fontsize=12,
                    color="white" if abs(corr_matrix[i, j]) > 0.5 else "black")

    fig.colorbar(im, label="Pearson Correlation")
    ax.set_title("Correlation: KUI vs EPU vs VIX")

    path = os.path.join(PLOTS_DIR, filename)
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved {path}")


def plot_event_study_windows(
    events_results: pd.DataFrame,
    kui_domain_indices: dict,
    epu: pd.Series,
    vix: pd.Series,
    top_n: int = 6,
    filename: str = "event_study_windows.png",
):
    """Plot event study windows for top N events."""
    from experiment2.event_study import extract_event_window

    # Select top events (prefer surprises)
    surprise_events = events_results[events_results["surprise"] == True]
    if len(surprise_events) >= top_n:
        selected = surprise_events.head(top_n)
    else:
        selected = events_results.head(top_n)

    if selected.empty:
        return

    n_events = min(len(selected), top_n)
    n_cols = min(3, n_events)
    n_rows = (n_events + n_cols - 1) // n_cols

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(5 * n_cols, 4 * n_rows))
    if n_events == 1:
        axes = np.array([axes])
    axes = axes.flatten()

    for idx, (_, event) in enumerate(selected.iterrows()):
        if idx >= len(axes):
            break
        ax = axes[idx]

        event_date = pd.to_datetime(event["event_date"])
        domain = event["relevant_domain"]

        # KUI domain sub-index
        kui_series = kui_domain_indices.get(domain)
        if kui_series is not None:
            kui_win = extract_event_window(kui_series, event_date, window_days=7)
            if not kui_win.empty:
                ax.plot(kui_win.index, kui_win.values, "b-o", markersize=3,
                        label=f"KUI_{domain}", linewidth=1.5)

        # EPU
        epu_win = extract_event_window(epu, event_date, window_days=7)
        if not epu_win.empty:
            ax.plot(epu_win.index, epu_win.values, "r-s", markersize=3,
                    label="EPU", linewidth=1, alpha=0.7)

        ax.axvline(x=0, color="black", linestyle="--", alpha=0.5, label="Event")
        ax.set_title(f"{event['description']}\n{'(Surprise)' if event['surprise'] else ''}",
                     fontsize=9)
        ax.set_xlabel("Days from event")
        ax.legend(fontsize=7)

    # Hide unused axes
    for idx in range(n_events, len(axes)):
        axes[idx].set_visible(False)

    fig.suptitle("Event Study Windows", fontsize=14, y=1.02)
    fig.tight_layout()

    path = os.path.join(PLOTS_DIR, filename)
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved {path}")


def plot_lead_lag_distribution(
    events_results: pd.DataFrame,
    filename: str = "lead_lag_distribution.png",
):
    """Histogram of KUI lead times across all events."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    for ax, col, title in [
        (axes[0], "lead_lag_vs_epu", "KUI Lead-Lag vs EPU"),
        (axes[1], "lead_lag_vs_vix", "KUI Lead-Lag vs VIX"),
    ]:
        ll = events_results[col].dropna()
        if ll.empty:
            ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
            ax.set_title(title)
            continue

        ax.hist(ll, bins=range(int(ll.min()) - 1, int(ll.max()) + 2), color="#3498db",
                edgecolor="white", alpha=0.8)
        ax.axvline(x=0, color="red", linestyle="--", linewidth=2, label="Simultaneous")
        ax.axvline(x=ll.mean(), color="green", linestyle="-", linewidth=1.5,
                   label=f"Mean: {ll.mean():.1f}d")

        pct_leads = (ll < 0).mean() * 100
        ax.set_title(f"{title}\n(KUI leads in {pct_leads:.0f}% of events)")
        ax.set_xlabel("Lead-Lag (days, negative = KUI leads)")
        ax.set_ylabel("Count")
        ax.legend()

    fig.tight_layout()
    path = os.path.join(PLOTS_DIR, filename)
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved {path}")


def plot_active_markets(
    n_active_df: pd.DataFrame,
    filename: str = "active_markets.png",
):
    """Plot number of active markets per domain over time."""
    fig, ax = plt.subplots(figsize=(14, 6))

    colors = plt.cm.Set2(np.linspace(0, 1, len(n_active_df.columns)))
    for (domain, color) in zip(sorted(n_active_df.columns), colors):
        series = n_active_df[domain].dropna()
        if len(series) > 0:
            ax.fill_between(series.index, 0, series.values, alpha=0.3, color=color)
            ax.plot(series.index, series.values, color=color, linewidth=0.5, label=domain)

    ax.set_ylabel("Number of Active Markets")
    ax.set_xlabel("Date")
    ax.set_title("Active Kalshi Markets per Domain")
    ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left", fontsize=8)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))

    path = os.path.join(PLOTS_DIR, filename)
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved {path}")


def plot_belief_volatility_raw(
    bv_df: pd.DataFrame,
    filename: str = "belief_volatility_raw.png",
):
    """Plot raw (unnormalized) belief volatility per domain."""
    fig, ax = plt.subplots(figsize=(14, 6))

    colors = plt.cm.tab10(np.linspace(0, 1, len(bv_df.columns)))
    for (domain, color) in zip(sorted(bv_df.columns), colors):
        series = bv_df[domain].dropna()
        if len(series) > 5:
            # Smooth with 7-day rolling average for readability
            smoothed = series.rolling(7, min_periods=1).mean()
            ax.plot(smoothed.index, smoothed.values, color=color, linewidth=1, label=domain)

    ax.set_ylabel("Belief Volatility (avg |Δprice|)")
    ax.set_xlabel("Date")
    ax.set_title("Raw Belief Volatility by Domain (7-day MA)")
    ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left", fontsize=8)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))

    path = os.path.join(PLOTS_DIR, filename)
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved {path}")


def generate_all_plots(
    kui_data: dict,
    epu: pd.Series,
    vix: pd.Series,
    corr_results: pd.DataFrame = None,
    event_results: pd.DataFrame = None,
):
    """Generate all visualization outputs."""
    setup()
    print("Generating plots...")

    # KUI time series
    plot_kui_time_series(
        kui_data["kui_normalized"],
        kui_data["domain_indices"],
    )

    # KUI vs benchmarks
    plot_kui_vs_benchmarks(
        kui_data["kui_normalized"],
        epu,
        vix,
    )

    # Raw belief volatility
    if not kui_data["bv_df"].empty:
        plot_belief_volatility_raw(kui_data["bv_df"])

    # Active markets
    if not kui_data["n_active_df"].empty:
        plot_active_markets(kui_data["n_active_df"])

    # Correlation heatmap
    if corr_results is not None and not corr_results.empty:
        plot_correlation_heatmap(corr_results)

    # Event study
    if event_results is not None and not event_results.empty:
        plot_event_study_windows(
            event_results,
            kui_data["domain_indices"],
            epu,
            vix,
        )
        plot_lead_lag_distribution(event_results)

    print("All plots generated.")
