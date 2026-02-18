"""
experiment2/run.py

Main orchestrator for Experiment 2: Kalshi-Derived Real-Time Uncertainty Index.

Usage:
    uv run python -m experiment2.run                    # Full run
    uv run python -m experiment2.run --quick-test       # Quick test (50 markets)
    uv run python -m experiment2.run --skip-fetch       # Use cached data
    uv run python -m experiment2.run --skip-candles     # Use cached candle data
"""

import os
import json
import argparse
import numpy as np
import pandas as pd
from datetime import datetime

DATA_DIR = "data/exp2"


def phase1_data_collection(quick_test: bool = False, max_markets: int = None):
    """Phase 1: Fetch and prepare all data."""
    print("\n" + "=" * 70)
    print("PHASE 1: DATA COLLECTION")
    print("=" * 70)

    from experiment2.data_collection import main as dc_main
    return dc_main(quick_test=quick_test, max_markets=max_markets)


def phase2_index_construction(df: pd.DataFrame, daily_prices: dict):
    """Phase 2: Build KUI and domain sub-indices."""
    print("\n" + "=" * 70)
    print("PHASE 2: INDEX CONSTRUCTION")
    print("=" * 70)

    from experiment2.index_construction import build_kui_dataset

    kui_data = build_kui_dataset(daily_prices, df)

    # Print summary
    kui = kui_data["kui_normalized"]
    valid_kui = kui.dropna()
    print(f"\n  KUI time series: {len(valid_kui)} days with data")
    if not valid_kui.empty:
        print(f"  KUI range: [{valid_kui.min():.1f}, {valid_kui.max():.1f}]")
        print(f"  KUI mean: {valid_kui.mean():.1f}")

    print(f"\n  Domain sub-indices:")
    for domain, series in sorted(kui_data["domain_indices"].items()):
        n_valid = series.dropna().shape[0]
        print(f"    {domain}: {n_valid} days")

    # Save
    kui_df = pd.DataFrame({"KUI": kui_data["kui_normalized"]})
    for domain, series in kui_data["domain_indices"].items():
        kui_df[f"KUI_{domain}"] = series

    kui_df.to_csv(os.path.join(DATA_DIR, "kui_daily.csv"))

    if not kui_data["bv_df"].empty:
        kui_data["bv_df"].to_csv(os.path.join(DATA_DIR, "belief_volatility.csv"))

    if not kui_data["n_active_df"].empty:
        kui_data["n_active_df"].to_csv(os.path.join(DATA_DIR, "active_markets.csv"))

    return kui_data


def phase3_validation(
    kui_data: dict,
    epu: pd.Series,
    vix: pd.Series,
    sp500: pd.Series,
):
    """Phase 3: Validate KUI against EPU and VIX."""
    print("\n" + "=" * 70)
    print("PHASE 3: VALIDATION")
    print("=" * 70)

    from experiment2.validation import (
        compute_correlations,
        run_granger_tests,
        incremental_r2_test,
        compute_realized_volatility,
    )

    kui = kui_data["kui_normalized"]

    # Correlations
    print("\n--- Correlation Analysis ---")
    corr_results = compute_correlations(kui, epu, vix)
    print(corr_results.to_string())
    corr_results.to_csv(os.path.join(DATA_DIR, "correlations.csv"), index=False)

    # Granger causality
    print("\n--- Granger Causality Tests ---")
    granger_results = run_granger_tests(kui, epu, vix, max_lag=5)
    print(granger_results.to_string())
    granger_results.to_csv(os.path.join(DATA_DIR, "granger_causality.csv"), index=False)

    # Incremental R²
    print("\n--- Incremental R² Test ---")
    r2_result = {"error": "insufficient data"}
    if not sp500.empty:
        realized_vol = compute_realized_volatility(sp500)
        r2_result = incremental_r2_test(realized_vol, vix, epu, kui)
        print(f"  R² (VIX + EPU): {r2_result.get('r2_base', 'N/A')}")
        print(f"  R² (VIX + EPU + KUI): {r2_result.get('r2_full', 'N/A')}")
        print(f"  Delta R²: {r2_result.get('delta_r2', 'N/A')}")
        print(f"  F-stat: {r2_result.get('f_stat', 'N/A')}")
        print(f"  P-value: {r2_result.get('p_value', 'N/A')}")

    with open(os.path.join(DATA_DIR, "incremental_r2.json"), "w") as f:
        json.dump(r2_result, f, indent=2, default=str)

    # Regime-conditional analysis
    print("\n--- Regime-Conditional Analysis ---")
    from experiment2.validation import (
        detect_shock_regime,
        regime_conditional_granger,
        regime_conditional_incremental_r2,
    )

    regime = detect_shock_regime(kui)
    n_shock = int(regime.sum())
    n_normal = int((~regime).sum())
    print(f"  Shock days: {n_shock}, Normal days: {n_normal}")

    regime_granger = regime_conditional_granger(kui, epu, regime, max_lag=5)
    print(f"\n  Granger (shock regime): {regime_granger['shock_result']}")
    print(f"  Granger (normal regime): {regime_granger['normal_result']}")

    regime_r2 = {}
    if not sp500.empty:
        from experiment2.validation import compute_realized_volatility as crv
        realized_vol_r = crv(sp500)
        regime_r2 = regime_conditional_incremental_r2(
            realized_vol_r, vix, epu, kui, regime
        )
        print(f"\n  Regime-conditional R²: {regime_r2}")

    regime_results = {
        "n_shock_days": n_shock,
        "n_normal_days": n_normal,
        "granger": regime_granger,
        "incremental_r2": regime_r2,
    }
    with open(os.path.join(DATA_DIR, "regime_conditional_results.json"), "w") as f:
        json.dump(regime_results, f, indent=2, default=str)

    return corr_results, granger_results, r2_result


def phase4_event_study(
    kui_data: dict,
    epu: pd.Series,
    vix: pd.Series,
):
    """Phase 4: Event study analysis."""
    print("\n" + "=" * 70)
    print("PHASE 4: EVENT STUDY")
    print("=" * 70)

    from experiment2.event_study import (
        get_economic_events,
        run_event_study,
        summarize_event_study,
        compute_shock_propagation,
    )

    events = get_economic_events()
    print(f"  {len(events)} economic events defined")

    event_results = run_event_study(
        kui_data["domain_indices"], epu, vix, events
    )

    if not event_results.empty:
        print(f"\n  Events with lead-lag data: {event_results['lead_lag_vs_epu'].notna().sum()}")
        event_results.to_csv(os.path.join(DATA_DIR, "event_study_results.csv"), index=False)

        summary = summarize_event_study(event_results)
        print(f"\n  Event Study Summary:")
        for k, v in summary.items():
            print(f"    {k}: {v}")

        with open(os.path.join(DATA_DIR, "event_study_summary.json"), "w") as f:
            json.dump(summary, f, indent=2, default=str)
    else:
        print("  No event study results (insufficient data overlap)")
        summary = {}

    # Shock propagation analysis
    print("\n--- Shock Propagation Analysis ---")
    propagation = compute_shock_propagation(kui_data["domain_indices"], events)
    if not propagation.empty:
        propagation.to_csv(os.path.join(DATA_DIR, "shock_propagation.csv"), index=False)
        print(f"  {len(propagation)} cross-domain propagation observations")

        # Summary by domain pair
        if len(propagation) > 0:
            avg_delay = propagation.groupby(["primary_domain", "secondary_domain"])["propagation_delay_days"].mean()
            print("\n  Average propagation delay (days):")
            for (primary, secondary), delay in avg_delay.items():
                print(f"    {primary} -> {secondary}: {delay:.1f} days")
    else:
        print("  No shock propagation data (insufficient surprise events or domains)")

    return event_results, summary


def phase5_visualization(
    kui_data: dict,
    epu: pd.Series,
    vix: pd.Series,
    corr_results: pd.DataFrame,
    event_results: pd.DataFrame,
):
    """Phase 5: Generate all plots."""
    print("\n" + "=" * 70)
    print("PHASE 5: VISUALIZATION")
    print("=" * 70)

    from experiment2.visualize import generate_all_plots

    generate_all_plots(kui_data, epu, vix, corr_results, event_results)


def generate_results_summary(
    kui_data: dict,
    df_markets: pd.DataFrame,
    corr_results: pd.DataFrame,
    granger_results: pd.DataFrame,
    r2_result: dict,
    event_results: pd.DataFrame,
    event_summary: dict,
):
    """Generate results_summary.md."""
    print("\n" + "=" * 70)
    print("GENERATING RESULTS SUMMARY")
    print("=" * 70)

    kui = kui_data["kui_normalized"]
    valid_kui = kui.dropna()

    # Domain coverage
    domain_lines = []
    for domain, series in sorted(kui_data["domain_indices"].items()):
        n = series.dropna().shape[0]
        domain_lines.append(f"| {domain} | {n} days |")

    # Correlation summary
    corr_lines = ""
    if corr_results is not None and not corr_results.empty:
        corr_lines = corr_results.to_string()

    # Granger summary
    granger_lines = ""
    if granger_results is not None and not granger_results.empty:
        granger_lines = granger_results.to_string()

    # Event study summary
    event_lines = ""
    if event_summary:
        for k, v in event_summary.items():
            event_lines += f"- **{k}**: {v}\n"

    # Success metrics assessment
    kui_epu_corr = np.nan
    kui_leads_epu = False
    delta_r2 = r2_result.get("delta_r2", np.nan)
    n_domains = len(kui_data["domain_indices"])

    if corr_results is not None and not corr_results.empty:
        kui_epu_row = corr_results[
            (corr_results["pair"] == "KUI-EPU") & (corr_results["method"] == "pearson")
        ]
        if not kui_epu_row.empty:
            kui_epu_corr = kui_epu_row.iloc[0]["correlation"]

    if granger_results is not None and not granger_results.empty:
        kui_leads_row = granger_results[granger_results["test"] == "KUI -> EPU"]
        if not kui_leads_row.empty:
            kui_leads_epu = kui_leads_row.iloc[0].get("significant", False)

    summary = f"""# Experiment 2: Results Summary
## Kalshi-Derived Real-Time Uncertainty Index (KUI)

**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

---

## Dataset
- **Total KUI-relevant markets:** {len(df_markets)}
- **Markets with candle data:** {len(kui_data.get('prices_df', pd.DataFrame()).columns)}
- **KUI time series length:** {len(valid_kui)} days
- **Domain sub-indices:** {n_domains}

### Domain Coverage
| Domain | Days with Data |
|--------|---------------|
{chr(10).join(domain_lines)}

---

## KUI Index Statistics
- **Mean:** {valid_kui.mean():.1f} (target: 100)
- **Std:** {valid_kui.std():.1f} (target: 15)
- **Min:** {valid_kui.min():.1f}
- **Max:** {valid_kui.max():.1f}
- **Date range:** {valid_kui.index.min().strftime('%Y-%m-%d') if not valid_kui.empty else 'N/A'} to {valid_kui.index.max().strftime('%Y-%m-%d') if not valid_kui.empty else 'N/A'}

---

## Validation Results

### Correlation Analysis
```
{corr_lines}
```

### Granger Causality
```
{granger_lines}
```

### Incremental R² (Realized Vol ~ VIX + EPU + KUI)
- **R² (VIX + EPU):** {r2_result.get('r2_base', 'N/A')}
- **R² (VIX + EPU + KUI):** {r2_result.get('r2_full', 'N/A')}
- **Delta R²:** {r2_result.get('delta_r2', 'N/A')}
- **F-stat:** {r2_result.get('f_stat', 'N/A')}
- **P-value:** {r2_result.get('p_value', 'N/A')}

---

## Event Study Results
{event_lines}

---

## Success Metrics Assessment
| Metric | Threshold | Result | Status |
|--------|-----------|--------|--------|
| KUI-EPU correlation | 0.3-0.7 | {kui_epu_corr:.3f} if not np.isnan(kui_epu_corr) else 'N/A' | {'PASS' if not np.isnan(kui_epu_corr) and 0.3 <= abs(kui_epu_corr) <= 0.7 else 'CHECK'} |
| KUI leads EPU (Granger) | p < 0.05 | {'Yes' if kui_leads_epu else 'No'} | {'PASS' if kui_leads_epu else 'FAIL'} |
| Incremental R² | > 0.02 | {delta_r2 if not np.isnan(delta_r2) else 'N/A'} | {'PASS' if not np.isnan(delta_r2) and delta_r2 > 0.02 else 'CHECK'} |
| Domain decomposition | >= 3 domains | {n_domains} domains | {'PASS' if n_domains >= 3 else 'PARTIAL'} |

---

## Deliverables
- [x] KUI time series (data/exp2/kui_daily.csv)
- [x] Domain sub-indices (data/exp2/kui_daily.csv)
- [x] Correlation analysis (data/exp2/correlations.csv)
- [x] Granger causality (data/exp2/granger_causality.csv)
- [x] Event study (data/exp2/event_study_results.csv)
- [x] Visualizations (data/exp2/plots/)

## Plots
- KUI time series + domain decomposition
- KUI vs EPU/VIX overlay
- Raw belief volatility by domain
- Active markets per domain
- Correlation heatmap
- Event study windows
- Lead-lag distribution
"""

    output_path = os.path.join(DATA_DIR, "results_summary.md")
    with open(output_path, "w") as f:
        f.write(summary)
    print(f"Saved results summary to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Experiment 2: Kalshi Uncertainty Index")
    parser.add_argument("--quick-test", action="store_true", help="Run on small subset")
    parser.add_argument("--max-markets", type=int, default=None, help="Max markets to fetch")
    parser.add_argument("--skip-fetch", action="store_true", help="Use cached market data")
    parser.add_argument("--skip-candles", action="store_true", help="Use cached candle data")
    parser.add_argument("--skip-events", action="store_true", help="Skip event study")
    args = parser.parse_args()

    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "plots"), exist_ok=True)

    start_time = datetime.now()
    print(f"Experiment 2 started at {start_time.strftime('%H:%M:%S')}")

    if args.quick_test:
        args.max_markets = args.max_markets or 500

    # Phase 1: Data collection
    markets_path = os.path.join(DATA_DIR, "markets.csv")
    candles_path = os.path.join(DATA_DIR, "daily_prices_by_ticker.json")

    if args.skip_fetch and os.path.exists(markets_path) and os.path.exists(candles_path):
        print(f"\nLoading cached data...")
        df = pd.read_csv(markets_path)
        df["open_time"] = pd.to_datetime(df["open_time"], format="ISO8601", errors="coerce")
        df["close_time"] = pd.to_datetime(df["close_time"], format="ISO8601", errors="coerce")

        with open(candles_path) as f:
            daily_prices = json.load(f)

        vix_path = os.path.join(DATA_DIR, "vix_daily.csv")
        epu_path = os.path.join(DATA_DIR, "epu_daily.csv")
        sp500_path = os.path.join(DATA_DIR, "sp500_daily.csv")

        vix_df = pd.read_csv(vix_path) if os.path.exists(vix_path) else pd.DataFrame(columns=["date", "value"])
        epu_df = pd.read_csv(epu_path) if os.path.exists(epu_path) else pd.DataFrame(columns=["date", "value"])
        sp500_df = pd.read_csv(sp500_path) if os.path.exists(sp500_path) else pd.DataFrame(columns=["date", "value"])
    else:
        df, daily_prices, vix_df, epu_df, sp500_df = phase1_data_collection(
            quick_test=args.quick_test,
            max_markets=args.max_markets,
        )

    # Convert external data to Series with DatetimeIndex
    def to_series(ext_df, name):
        if ext_df.empty:
            return pd.Series(dtype=float, name=name)
        ext_df = ext_df.copy()
        ext_df["date"] = pd.to_datetime(ext_df["date"])
        ext_df["value"] = pd.to_numeric(ext_df["value"], errors="coerce")
        ext_df = ext_df.dropna()
        s = ext_df.set_index("date")["value"]
        s.name = name
        return s

    vix = to_series(vix_df, "VIX")
    epu = to_series(epu_df, "EPU")
    sp500 = to_series(sp500_df, "SP500")

    # Phase 2: Index construction
    kui_data = phase2_index_construction(df, daily_prices)

    # Phase 3: Validation
    corr_results, granger_results, r2_result = phase3_validation(
        kui_data, epu, vix, sp500
    )

    # Phase 4: Event study
    event_results = pd.DataFrame()
    event_summary = {}
    if not args.skip_events:
        event_results, event_summary = phase4_event_study(
            kui_data, epu, vix
        )

    # Phase 5: Visualization
    phase5_visualization(kui_data, epu, vix, corr_results, event_results)

    # Results summary
    generate_results_summary(
        kui_data, df, corr_results, granger_results,
        r2_result, event_results, event_summary,
    )

    elapsed = datetime.now() - start_time
    print(f"\n{'=' * 70}")
    print(f"EXPERIMENT 2 COMPLETE ({elapsed.total_seconds():.0f}s)")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
