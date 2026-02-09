"""
run.py

Runs all backtest phases in order.
Expects DISCOVERY_MODE = False in data_collection.py (i.e., you've already
done the discovery step and configured your series).

Run with:  uv run python run.py
"""

from backtest import data_collection, track_a, track_b, backtest, visualize


def main():
    print("=" * 60)
    print("PHASE 1: Data Collection")
    print("=" * 60)
    data_collection.main()

    print("\n" + "=" * 60)
    print("PHASE 2: Track A — Lasso Logistic Regression")
    print("=" * 60)
    track_a.main()

    print("\n" + "=" * 60)
    print("PHASE 3: Track B — SYNTHETIC predictions")
    print("=" * 60)
    track_b.main()

    print("\n" + "=" * 60)
    print("PHASE 4: Synthesis & Evaluation")
    print("=" * 60)
    backtest.main()

    print("\n" + "=" * 60)
    print("VISUALIZATION")
    print("=" * 60)
    visualize.main()

    print("\n" + "=" * 60)
    print("BACKTEST COMPLETE")
    print("=" * 60)
    print("Check data/evaluation/ for results.")


if __name__ == "__main__":
    main()
