"""
backtest/visualize.py

Produces diagnostic plots from backtest results.

Run with:  uv run python -m backtest.visualize
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.calibration import calibration_curve

EVAL_DIR = "data/evaluation"


def plot_brier_vs_alpha():
    """
    PURPOSE: Visualize how the ensemble Brier Score changes as we shift
    weight between Track A (α=1) and Track B (α=0).

    HOW IT WORKS:
    Reads alpha_sweep.csv, plots Brier Score on y-axis vs alpha on x-axis.
    Marks the optimal alpha with a red dot and dashed line.
    Draws a horizontal line at 0.25 (random-guessing baseline).

    HOW TO READ THIS PLOT:
    - The lowest point on the curve is the best alpha.
    - If the curve is flat: both tracks are similarly (un)informative.
    - If the curve is U-shaped with minimum in the middle: both tracks
      contribute unique information. (Unlikely with synthetic Track B.)
    - If the minimum is at α=1.0: Track A alone is best.

    CALLED BY: main()
    """
    results = pd.read_csv(os.path.join(EVAL_DIR, "alpha_sweep.csv"))

    best_idx = results["brier"].idxmin()
    best_alpha = results.loc[best_idx, "alpha"]
    best_brier = results.loc[best_idx, "brier"]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(results["alpha"], results["brier"], "o-", linewidth=2, markersize=5)
    ax.axvline(best_alpha, color="red", linestyle="--", alpha=0.7,
               label=f"Best α = {best_alpha:.2f}")
    ax.scatter([best_alpha], [best_brier], color="red", s=150, zorder=5)
    ax.axhline(0.25, color="gray", linestyle=":", alpha=0.5,
               label="Random baseline (0.25)")

    ax.set_xlabel("α  (1.0 = Track A only, 0.0 = Track B only)")
    ax.set_ylabel("Brier Score (lower = better)")
    ax.set_title("Ensemble Performance: Brier Score vs. Alpha")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()

    path = os.path.join(EVAL_DIR, "brier_vs_alpha.png")
    fig.savefig(path, dpi=150)
    print(f"Saved {path}")
    plt.close(fig)


def plot_calibration():
    """
    PURPOSE: Check whether the model's predicted probabilities match
    observed frequencies.

    HOW IT WORKS:
    Reads best_predictions.csv (predictions at optimal alpha).
    Bins predictions into ~10 groups by predicted probability.
    For each bin, computes the actual fraction of YES outcomes.
    Plots predicted vs. observed. A perfectly calibrated model
    lies on the diagonal.

    HOW TO READ THIS PLOT:
    - Points above the diagonal: model is under-confident
      (predicts 30% but outcome happens 50% of the time)
    - Points below the diagonal: model is over-confident
      (predicts 80% but outcome only happens 60% of the time)
    - Points on the diagonal: perfect calibration

    NOTE: With few test samples (<30), this plot will be very noisy.
    Don't over-interpret individual points.

    CALLED BY: main()
    """
    preds = pd.read_csv(os.path.join(EVAL_DIR, "best_predictions.csv"))

    n_bins = min(10, len(preds) // 2)  # Need at least 2 samples per bin
    if n_bins < 3:
        print("⚠️  Too few samples for a meaningful calibration curve. Skipping.")
        return

    prob_true, prob_pred = calibration_curve(
        preds["y_true"], preds["P_final"], n_bins=n_bins, strategy="uniform"
    )

    fig, ax = plt.subplots(figsize=(8, 8))
    ax.plot([0, 1], [0, 1], "k--", alpha=0.5, label="Perfect calibration")
    ax.plot(prob_pred, prob_true, "o-", linewidth=2, markersize=8, label="Model")

    ax.set_xlabel("Predicted probability")
    ax.set_ylabel("Observed frequency")
    ax.set_title(f"Calibration Curve (α = {preds['alpha'].iloc[0]:.2f})")
    ax.legend()
    ax.grid(alpha=0.3)
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.05, 1.05)
    fig.tight_layout()

    path = os.path.join(EVAL_DIR, "calibration.png")
    fig.savefig(path, dpi=150)
    print(f"Saved {path}")
    plt.close(fig)


def main():
    plot_brier_vs_alpha()
    plot_calibration()
    print("\n✅ Visualizations complete.")


if __name__ == "__main__":
    main()
