"""
backtest/backtest.py

Phase 4: Combine Track A + Track B predictions via weighted log-odds ensemble.
Sweep alpha from 0 to 1, evaluate with Brier Score and Log Loss.

Run with:  uv run python -m backtest.backtest
"""

import os
import pandas as pd
import numpy as np
from sklearn.metrics import brier_score_loss, log_loss

PROCESSED_DIR = "data/processed"
EVAL_DIR = "data/evaluation"


def load_predictions() -> pd.DataFrame:
    """
    PURPOSE: Load Track A and Track B predictions and merge them on ticker.

    HOW IT WORKS:
    Reads both CSVs and joins on ['ticker', 'y_true']. This ensures
    we only evaluate markets that have predictions from both tracks.

    CALLED BY: main()
    RETURNS: DataFrame with columns: ticker, P_stat, L_stat, L_news, mode, y_true
    """
    a = pd.read_csv(os.path.join(PROCESSED_DIR, "track_a_predictions.csv"))
    b = pd.read_csv(os.path.join(PROCESSED_DIR, "track_b_predictions.csv"))

    merged = a.merge(b[["ticker", "L_news", "mode"]], on="ticker")

    print(f"Loaded {len(merged)} markets with predictions from both tracks.")
    print(f"Track B mode: {merged['mode'].iloc[0]}")

    return merged


def sweep_alpha(data: pd.DataFrame) -> pd.DataFrame:
    """
    PURPOSE: Test every alpha value from 0.0 to 1.0 (step 0.05) and compute
    Brier Score and Log Loss for each.

    HOW IT WORKS:
    For each alpha:
      1. Compute L_final = alpha * L_stat + (1 - alpha) * L_news
      2. Convert to probability: P_final = sigmoid(L_final) = 1 / (1 + exp(-L_final))
      3. Compute Brier Score: mean((P_final - y_true)²)
      4. Compute Log Loss: -mean(y·log(P) + (1-y)·log(1-P))

    WHY BRIER SCORE AS PRIMARY METRIC:
    Brier Score directly measures calibration — how close your predicted
    probabilities are to the actual outcomes. A well-calibrated model that says
    "70% chance" should be right ~70% of the time. This matters more for
    trading than raw accuracy, because position sizing depends on calibration.

    CALLED BY: main()
    RETURNS: DataFrame with columns: alpha, brier, log_loss, n_markets
    """
    alphas = np.arange(0, 1.05, 0.05)
    results = []

    for a in alphas:
        L_final = a * data["L_stat"] + (1 - a) * data["L_news"]
        P_final = 1 / (1 + np.exp(-L_final))
        # Clip for log_loss stability
        P_final = np.clip(P_final, 1e-6, 1 - 1e-6)

        results.append({
            "alpha": round(a, 2),
            "brier": brier_score_loss(data["y_true"], P_final),
            "log_loss": log_loss(data["y_true"], P_final),
            "n_markets": len(data),
        })

    return pd.DataFrame(results)


def main():
    os.makedirs(EVAL_DIR, exist_ok=True)

    data = load_predictions()
    results = sweep_alpha(data)
    results.to_csv(os.path.join(EVAL_DIR, "alpha_sweep.csv"), index=False)

    # Find best alpha
    best_idx = results["brier"].idxmin()
    best_alpha = results.loc[best_idx, "alpha"]
    best_brier = results.loc[best_idx, "brier"]

    print(f"\n── Alpha Sweep Results ──")
    print(results.to_string(index=False))
    print(f"\nBest alpha: {best_alpha:.2f}")
    print(f"Best Brier: {best_brier:.4f}")
    print(f"Baseline (random guess): 0.2500")

    # Save predictions at best alpha
    L_final = best_alpha * data["L_stat"] + (1 - best_alpha) * data["L_news"]
    P_final = 1 / (1 + np.exp(-L_final))

    best_preds = pd.DataFrame({
        "ticker": data["ticker"],
        "y_true": data["y_true"],
        "P_final": np.clip(P_final, 1e-6, 1 - 1e-6),
        "alpha": best_alpha,
        "track_b_mode": data["mode"],
    })
    best_preds.to_csv(os.path.join(EVAL_DIR, "best_predictions.csv"), index=False)

    print(f"\n✅ Phase 4 complete.")
    print(f"   {os.path.join(EVAL_DIR, 'alpha_sweep.csv')}")
    print(f"   {os.path.join(EVAL_DIR, 'best_predictions.csv')}")


if __name__ == "__main__":
    main()
