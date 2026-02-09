"""
backtest/track_b.py

Phase 3: Generate Track B (RLM) predictions.

⚠️  CURRENTLY SYNTHETIC. All outputs are tagged mode=SYNTHETIC.
    Replace with real LLM-based predictions in Stage 2.

Run with:  uv run python -m backtest.track_b
"""

import os
import pandas as pd
import numpy as np

PROCESSED_DIR = "data/processed"


def synthetic_log_odds(y_true: np.ndarray, noise_std: float = 1.0, seed: int = 42) -> np.ndarray:
    """
    PURPOSE: Generate synthetic (fake) log-odds predictions that are correlated
    with the true outcome but noisy.

    HOW IT WORKS:
    - If the true outcome is YES (1): base log-odds = +1.0
    - If the true outcome is NO  (0): base log-odds = -1.0
    - Add Gaussian noise ~ N(0, noise_std²)

    This produces predictions that are "somewhat informative" — they lean in the
    right direction ~73% of the time (since P(noise > 1) ≈ 16%, so directional
    accuracy ≈ 84% before noise, degraded by overlap).

    WHY THIS APPROACH: We need predictions that behave like a real but imperfect
    RLM. Pure random would be useless (all noise). Perfect predictions would be
    unrealistically good. This heuristic sits in between.

    ⚠️  IMPORTANT: This function uses y_true (the ground truth) as input.
    This means the synthetic predictions are "cheating" — they have access to
    the answer. This is intentional for pipeline validation only. When you
    interpret backtest results with synthetic Track B, remember that any
    apparent Track B performance is artificial.

    CALLED BY: main()
    RETURNS: numpy array of log-odds values.
    """
    rng = np.random.default_rng(seed)
    base = 2.0 * y_true - 1.0  # Maps: 0 → -1.0, 1 → +1.0
    return base + rng.normal(0, noise_std, size=len(y_true))


def main():
    # Read Track A predictions to get the test set tickers and ground truth
    track_a = pd.read_csv(os.path.join(PROCESSED_DIR, "track_a_predictions.csv"))

    L_news = synthetic_log_odds(track_a["y_true"].values)

    results = pd.DataFrame({
        "ticker": track_a["ticker"],
        "L_news": L_news,
        "mode": "SYNTHETIC",
        "y_true": track_a["y_true"],
    })
    results.to_csv(os.path.join(PROCESSED_DIR, "track_b_predictions.csv"), index=False)

    print(f"⚠️  Track B (SYNTHETIC): {len(results)} predictions saved.")
    print(f"   Mode: SYNTHETIC — these are NOT real LLM predictions.")


if __name__ == "__main__":
    main()
