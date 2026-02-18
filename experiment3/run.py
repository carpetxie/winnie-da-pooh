"""
experiment3/run.py

Experiment 3: Do prediction markets become less calibrated during high-uncertainty periods?

Uses existing data from exp5 (market predictions) + exp2 (KUI uncertainty index).
No API calls required.

Usage:
    uv run python -m experiment3.run
"""

import os
import json
from datetime import datetime

DATA_DIR = "data/exp3"


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    start_time = datetime.now()
    print(f"Experiment 3 started at {start_time.strftime('%H:%M:%S')}")

    from experiment3.calibration_analysis import (
        load_market_predictions,
        load_kui,
        assign_uncertainty_regime,
        compute_regime_calibration,
        plot_calibration_curves,
    )

    # Load data
    print("\n" + "=" * 70)
    print("LOADING DATA")
    print("=" * 70)

    markets = load_market_predictions()
    print(f"  Markets with valid predictions: {len(markets)}")
    print(f"  Domains: {markets['domain'].value_counts().to_dict()}")

    kui = load_kui()
    print(f"  KUI: {len(kui)} days ({kui.index.min()} to {kui.index.max()})")

    # Assign regimes
    print("\n" + "=" * 70)
    print("ASSIGNING UNCERTAINTY REGIMES")
    print("=" * 70)

    markets = assign_uncertainty_regime(markets, kui)
    print(f"  Markets with KUI coverage: {len(markets)}")
    print(f"  KUI range: [{markets['mean_kui'].min():.1f}, {markets['mean_kui'].max():.1f}]")
    print(f"  Regime distribution (tercile): {markets['regime_tercile'].value_counts().to_dict()}")
    print(f"  Regime distribution (binary): {markets['regime_binary'].value_counts().to_dict()}")

    # Compute calibration
    print("\n" + "=" * 70)
    print("CALIBRATION ANALYSIS")
    print("=" * 70)

    results = compute_regime_calibration(markets)

    # Print key findings
    print(f"\n  Overall: Brier={results['overall']['brier']:.4f}, ECE={results['overall']['ece']:.4f} (n={results['overall']['n_markets']})")

    for key in ["tercile_low", "tercile_medium", "tercile_high"]:
        if key in results:
            r = results[key]
            print(f"  {key}: Brier={r['brier']:.4f}, ECE={r['ece']:.4f}, KUI={r['mean_kui']:.1f} (n={r['n_markets']})")

    if "statistical_test" in results:
        t = results["statistical_test"]
        print(f"\n  Bootstrap test (high - low Brier):")
        print(f"    Mean diff: {t['mean_diff']:.4f}")
        print(f"    95% CI: [{t['ci_lower']:.4f}, {t['ci_upper']:.4f}]")
        print(f"    Significant: {t['significant']}")
        print(f"    Direction: {t['direction']}")

    # Save results
    with open(os.path.join(DATA_DIR, "calibration_results.json"), "w") as f:
        json.dump(results, f, indent=2, default=str)

    # Plots
    print("\n" + "=" * 70)
    print("GENERATING PLOTS")
    print("=" * 70)

    plot_calibration_curves(markets, os.path.join(DATA_DIR, "plots"))

    # Generate summary
    print("\n" + "=" * 70)
    print("GENERATING RESULTS SUMMARY")
    print("=" * 70)

    generate_summary(markets, results)

    elapsed = datetime.now() - start_time
    print(f"\n{'=' * 70}")
    print(f"EXPERIMENT 3 COMPLETE ({elapsed.total_seconds():.0f}s)")
    print(f"{'=' * 70}")


def generate_summary(markets, results):
    """Generate results_summary.md."""
    t = results.get("statistical_test", {})

    summary = f"""# Experiment 3: Results Summary
## Prediction Market Calibration Under Uncertainty

**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

---

## Dataset
- **Markets analyzed:** {results['overall']['n_markets']}
- **Domain distribution:** {markets['domain'].value_counts().to_dict()}
- **KUI coverage:** {markets['mean_kui'].min():.1f} to {markets['mean_kui'].max():.1f}

---

## Key Finding

**Question:** Do prediction markets become less calibrated during high-uncertainty periods?

### Overall Calibration
- **Brier score:** {results['overall']['brier']:.4f}
- **ECE:** {results['overall']['ece']:.4f}

### By Uncertainty Regime (Terciles)
| Regime | Brier | ECE | Mean KUI | n |
|--------|-------|-----|----------|---|
"""

    for key in ["tercile_low", "tercile_medium", "tercile_high"]:
        if key in results:
            r = results[key]
            regime = key.replace("tercile_", "")
            summary += f"| {regime} | {r['brier']:.4f} | {r['ece']:.4f} | {r['mean_kui']:.1f} | {r['n_markets']} |\n"

    summary += f"""
### Statistical Test
- **Test:** Bootstrap Brier score difference (1000 iterations)
- **Mean diff (high - low):** {t.get('mean_diff', 'N/A')}
- **95% CI:** [{t.get('ci_lower', 'N/A')}, {t.get('ci_upper', 'N/A')}]
- **Significant:** {t.get('significant', 'N/A')}
- **Direction:** {t.get('direction', 'N/A')}

---

## Plots
- Calibration curves by regime (data/exp3/plots/calibration_by_regime.png)
- Domain breakdown (data/exp3/plots/calibration_by_domain.png)

---

## Deliverables
- [x] Calibration results (data/exp3/calibration_results.json)
- [x] Plots (data/exp3/plots/)
- [x] Results summary (data/exp3/results_summary.md)
"""

    output_path = os.path.join(DATA_DIR, "results_summary.md")
    with open(output_path, "w") as f:
        f.write(summary)
    print(f"  Saved to {output_path}")


if __name__ == "__main__":
    main()
