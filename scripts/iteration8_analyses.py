"""
Iteration 8 analyses:
1. Formal overconcentration test: sign test + pooled bootstrap + per-series bootstrap
2. std(PIT) vs CRPS/MAE Spearman correlation
3. KXFRM monitoring alert window identification (which events trigger alerts)
"""
import os
import sys
import json
import numpy as np
from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

OUTPUT_DIR = "data/iteration8"
os.makedirs(OUTPUT_DIR, exist_ok=True)

IDEAL_STD = 1.0 / (12**0.5)  # ≈ 0.289

# ============================================================
# LOAD ALL PIT VALUES
# ============================================================
print("=" * 70)
print("LOADING PIT VALUES FOR ALL SERIES")
print("=" * 70)

# Source 1: iteration6_results.json (7 new series with pit_values arrays)
with open("data/iteration6/iteration6_results.json") as f:
    iter6 = json.load(f)

# Source 2: exp13/unified_results.json (KXCPI, KXJOBLESSCLAIMS)
with open("data/exp13/unified_results.json") as f:
    exp13 = json.load(f)

# Source 3: iteration7_results.json (GDP, FED summary stats only)
with open("data/iteration7/iteration7_results.json") as f:
    iter7 = json.load(f)

pit_by_series = {}

# 7 new series from iteration6
for series_key, pit_data in iter6["pit_results"].items():
    if series_key.startswith("ORIG_"):
        continue
    if "pit_values" in pit_data and pit_data["pit_values"]:
        pit_by_series[series_key] = np.array(pit_data["pit_values"])
        print(f"  {series_key}: n={len(pit_data['pit_values'])} PIT values loaded")

# KXCPI and JC from exp13
for series_key, pit_data in exp13["pit_diagnostics"].items():
    if "pit_values" in pit_data and pit_data["pit_values"]:
        canonical = {"KXCPI": "CPI_new", "KXJOBLESSCLAIMS": "JC"}.get(series_key, series_key)
        pit_by_series[canonical] = np.array(pit_data["pit_values"])
        print(f"  {canonical} (from {series_key}): n={len(pit_data['pit_values'])} PIT values loaded")

# GDP and FED: need to recompute from candle data
# Using the same method as iteration7_analyses.py
print("\n--- Recomputing GDP and FED PIT values ---")

import pandas as pd

orig_df = pd.read_csv("data/expanded_analysis/expanded_crps_per_event.csv")
exp2_candles_dir = "data/exp2/raw/candles"

def compute_pit_for_series(events_df, candles_dir):
    """Compute PIT values from candle data."""
    import glob as glob_module
    pit_values = []

    for _, row in events_df.iterrows():
        event_ticker = row["event_ticker"]
        realized = row["realized"]

        event_candle_files = glob_module.glob(os.path.join(candles_dir, f"{event_ticker}*_60.json"))
        if not event_candle_files:
            continue

        tickers_and_strikes = []
        candles_by_ticker = {}

        for candle_file in event_candle_files:
            basename = os.path.basename(candle_file).replace("_60.json", "")
            parts = basename.split("-")
            strike = None
            for p in parts:
                if p.startswith("T") or p.startswith("B"):
                    try:
                        strike = float(p[1:])
                        break
                    except ValueError:
                        continue
            if strike is None:
                continue

            with open(candle_file) as f:
                candles = json.load(f)
            if not candles:
                continue

            tickers_and_strikes.append((basename, strike))
            candles_by_ticker[basename] = candles

        if len(tickers_and_strikes) < 2:
            continue

        tickers_and_strikes.sort(key=lambda x: x[1])

        price_series = {}
        for ticker, strike in tickers_and_strikes:
            candles = candles_by_ticker[ticker]
            prices = {}
            for c in candles:
                ts = c.get("end_period_ts") or c.get("period_start")
                if not ts:
                    continue
                close_price = None
                yes_price = c.get("yes_price", {})
                if isinstance(yes_price, dict) and yes_price.get("close") is not None:
                    close_price = yes_price["close"]
                if close_price is None:
                    price_obj = c.get("price", {})
                    if isinstance(price_obj, dict) and price_obj.get("close") is not None:
                        close_price = price_obj["close"]
                if close_price is None:
                    yes_bid = c.get("yes_bid", {})
                    yes_ask = c.get("yes_ask", {})
                    bid_close = yes_bid.get("close") if isinstance(yes_bid, dict) else None
                    ask_close = yes_ask.get("close") if isinstance(yes_ask, dict) else None
                    if bid_close is not None and ask_close is not None:
                        close_price = (float(bid_close) + float(ask_close)) / 2.0
                    elif bid_close is not None:
                        close_price = float(bid_close)
                    elif ask_close is not None:
                        close_price = float(ask_close)
                if close_price is not None:
                    try:
                        prices[ts] = float(close_price) / 100.0
                    except (ValueError, TypeError):
                        continue
            if prices:
                price_series[ticker] = prices

        if len(price_series) < 2:
            continue

        all_ts = set()
        for ps in price_series.values():
            all_ts.update(ps.keys())

        snapshots = []
        for ts in sorted(all_ts):
            cdf_points = []
            for ticker, strike in tickers_and_strikes:
                if ticker in price_series and ts in price_series[ticker]:
                    cdf_points.append((strike, price_series[ticker][ts]))
            if len(cdf_points) >= 2:
                cdf_points.sort(key=lambda x: x[0])
                snapshots.append({
                    "strikes": [p[0] for p in cdf_points],
                    "cdf_values": [p[1] for p in cdf_points],
                })

        if len(snapshots) < 2:
            continue

        mid_snap = snapshots[len(snapshots) // 2]
        strikes = mid_snap["strikes"]
        cdf_vals = mid_snap["cdf_values"]

        survival = np.interp(realized, strikes, cdf_vals)
        pit = 1.0 - survival
        pit_values.append(float(pit))
        print(f"    {event_ticker}: PIT={pit:.3f}")

    return pit_values

gdp_events_df = orig_df[orig_df["canonical_series"] == "GDP"]
fed_events_df = orig_df[orig_df["canonical_series"] == "FED"]

print(f"\nGDP events: {len(gdp_events_df)}")
gdp_pits = compute_pit_for_series(gdp_events_df, exp2_candles_dir)
if gdp_pits:
    pit_by_series["GDP"] = np.array(gdp_pits)
    print(f"  GDP: {len(gdp_pits)} PIT values computed")

print(f"\nFED events: {len(fed_events_df)}")
fed_pits = compute_pit_for_series(fed_events_df, exp2_candles_dir)
if fed_pits:
    pit_by_series["FED"] = np.array(fed_pits)
    print(f"  FED: {len(fed_pits)} PIT values computed")

# Also compute old CPI PIT (19 events with CPI- prefix)
print(f"\nOld CPI events:")
old_cpi_events = orig_df[(orig_df["canonical_series"] == "CPI") &
                          (orig_df["event_ticker"].str.startswith("CPI-"))]
old_cpi_pits = compute_pit_for_series(old_cpi_events, exp2_candles_dir)
if old_cpi_pits:
    # Merge with KXCPI PIT values for full CPI n=33
    kxcpi_pits = list(pit_by_series.get("CPI_new", []))
    full_cpi_pits = old_cpi_pits + kxcpi_pits
    pit_by_series["CPI"] = np.array(full_cpi_pits)
    print(f"  Full CPI: {len(full_cpi_pits)} PIT values (old={len(old_cpi_pits)}, new={len(kxcpi_pits)})")

# Summary
print("\n" + "=" * 70)
print("PIT VALUES SUMMARY")
print("=" * 70)
total_pits = 0
for series, pits in sorted(pit_by_series.items()):
    if series == "CPI_new":
        continue  # Skip, using merged CPI
    print(f"  {series:15s}: n={len(pits):3d}, mean={pits.mean():.3f}, std={pits.std():.3f}")
    total_pits += len(pits)
print(f"\n  Total PIT values: {total_pits}")


# ============================================================
# PART 1: FORMAL OVERCONCENTRATION TEST
# ============================================================
print("\n" + "=" * 70)
print("PART 1: FORMAL OVERCONCENTRATION TEST")
print("=" * 70)

# --- 1a: Sign test ---
# All 11 series have std(PIT) < 0.289
# Using the values from iteration7_results.json
std_pit_values = {
    "GDP": 0.266,
    "JC": 0.248,
    "KXCPIYOY": 0.228,
    "KXADP": 0.227,
    "KXU3": 0.245,
    "KXCPICORE": 0.219,
    "KXFRM": 0.227,
    "CPI": 0.259,
    "KXISMPMI": 0.136,
    "KXPCECORE": 0.212,
    "FED": 0.226,
}

n_below = sum(1 for v in std_pit_values.values() if v < IDEAL_STD)
n_total = len(std_pit_values)
p_sign = 0.5 ** n_total  # Exact binomial probability

print(f"\n1a. SIGN TEST:")
print(f"  {n_below}/{n_total} series have std(PIT) < {IDEAL_STD:.3f}")
print(f"  Binomial p = 0.5^{n_total} = {p_sign:.6f}")
print(f"  Interpretation: The probability that all {n_total} series would show")
print(f"  overconcentration by chance is {p_sign:.4f} — highly significant.")

# --- 1b: Pooled bootstrap ---
# Concatenate all available PIT values
all_pits_list = []
for series, pits in pit_by_series.items():
    if series == "CPI_new":
        continue
    all_pits_list.extend(pits.tolist())

all_pits = np.array(all_pits_list)
pooled_std = np.std(all_pits)
pooled_n = len(all_pits)

print(f"\n1b. POOLED BOOTSTRAP:")
print(f"  Total PIT values: {pooled_n}")
print(f"  Pooled std(PIT) = {pooled_std:.4f}")

# Bootstrap CI on std
rng = np.random.default_rng(42)
try:
    boot_result = stats.bootstrap(
        (all_pits,),
        np.std,
        n_resamples=10000,
        method='BCa',
        random_state=rng,
    )
    ci_lo, ci_hi = boot_result.confidence_interval
    print(f"  95% BCa CI: [{ci_lo:.4f}, {ci_hi:.4f}]")
    print(f"  CI excludes {IDEAL_STD:.3f}? {'YES ✅' if ci_hi < IDEAL_STD else 'NO ❌'}")
    pooled_bootstrap_ci = (float(ci_lo), float(ci_hi))
except Exception as e:
    print(f"  BCa failed ({e}), trying percentile...")
    boot_stds = []
    for _ in range(10000):
        idx = rng.integers(0, pooled_n, pooled_n)
        boot_stds.append(np.std(all_pits[idx]))
    boot_stds = np.array(boot_stds)
    ci_lo, ci_hi = np.percentile(boot_stds, [2.5, 97.5])
    print(f"  95% Percentile CI: [{ci_lo:.4f}, {ci_hi:.4f}]")
    print(f"  CI excludes {IDEAL_STD:.3f}? {'YES ✅' if ci_hi < IDEAL_STD else 'NO ❌'}")
    pooled_bootstrap_ci = (float(ci_lo), float(ci_hi))

# --- 1c: Per-series bootstrap (for series with n >= 10) ---
print(f"\n1c. PER-SERIES BOOTSTRAP (n ≥ 10):")
per_series_bootstrap = {}
for series, pits in sorted(pit_by_series.items()):
    if series == "CPI_new":
        continue
    n = len(pits)
    if n < 10:
        per_series_bootstrap[series] = {
            "n": n,
            "std_pit": float(np.std(pits)),
            "note": f"n={n} too small for reliable bootstrap"
        }
        continue

    try:
        boot = stats.bootstrap(
            (pits,),
            np.std,
            n_resamples=10000,
            method='BCa',
            random_state=np.random.default_rng(42),
        )
        ci_lo, ci_hi = boot.confidence_interval
    except Exception:
        boot_stds = []
        rng2 = np.random.default_rng(42)
        for _ in range(10000):
            idx = rng2.integers(0, n, n)
            boot_stds.append(np.std(pits[idx]))
        ci_lo, ci_hi = np.percentile(boot_stds, [2.5, 97.5])

    excludes = ci_hi < IDEAL_STD
    per_series_bootstrap[series] = {
        "n": n,
        "std_pit": float(np.std(pits)),
        "ci_lo": float(ci_lo),
        "ci_hi": float(ci_hi),
        "excludes_0289": excludes,
    }
    marker = "✅" if excludes else "❌"
    print(f"  {series:15s}: n={n:3d}, std={np.std(pits):.3f}, CI [{ci_lo:.3f}, {ci_hi:.3f}] {marker}")

# Count how many per-series CIs exclude 0.289
n_excludes = sum(1 for v in per_series_bootstrap.values() if v.get("excludes_0289", False))
n_testable = sum(1 for v in per_series_bootstrap.values() if "ci_lo" in v)
print(f"\n  {n_excludes}/{n_testable} series with n≥10 have CI excluding 0.289")


# ============================================================
# PART 2: STD(PIT) VS CRPS/MAE SPEARMAN CORRELATION
# ============================================================
print("\n" + "=" * 70)
print("PART 2: STD(PIT) VS CRPS/MAE SPEARMAN CORRELATION")
print("=" * 70)

# Data from the paper's executive summary table
series_data = [
    ("GDP",       0.266, 0.48),
    ("JC",        0.248, 0.60),
    ("KXCPIYOY",  0.228, 0.67),
    ("KXADP",     0.227, 0.71),
    ("KXU3",      0.245, 0.75),
    ("KXCPICORE", 0.219, 0.82),
    ("KXFRM",     0.227, 0.85),
    ("CPI",       0.259, 0.86),
    ("KXISMPMI",  0.136, 0.97),
    ("KXPCECORE", 0.212, 1.22),
    ("FED",       0.226, 1.48),
]

std_pits = np.array([x[1] for x in series_data])
ratios = np.array([x[2] for x in series_data])

rho, p_val = stats.spearmanr(std_pits, ratios)
print(f"\n  Spearman ρ = {rho:.3f}, p = {p_val:.3f}")
print(f"  Interpretation: {'Significant' if p_val < 0.05 else 'Not significant'} correlation")

# Also Pearson for comparison
r_pearson, p_pearson = stats.pearsonr(std_pits, ratios)
print(f"  Pearson r = {r_pearson:.3f}, p = {p_pearson:.3f}")

if abs(rho) < 0.3:
    interp = "Weak/no correlation — overconcentration and CRPS/MAE are largely independent calibration dimensions."
elif rho < -0.3:
    interp = "Negative correlation — more overconcentrated series tend to have LOWER CRPS/MAE (better distributions). This suggests overconcentration is compensated by better location accuracy."
else:
    interp = "Positive correlation — more overconcentrated series have higher CRPS/MAE. Overconcentration may partly explain distributional failure."

print(f"  {interp}")


# ============================================================
# PART 3: KXFRM MONITORING ALERT WINDOW IDENTIFICATION
# ============================================================
print("\n" + "=" * 70)
print("PART 3: KXFRM MONITORING ALERT WINDOW IDENTIFICATION")
print("=" * 70)

# Load KXFRM per-event data
with open("data/new_series/expanded_series_results.json") as f:
    expanded = json.load(f)

kxfrm_events = sorted(expanded.get("KXFRM", []), key=lambda x: x.get("event_ticker", ""))
print(f"\nKXFRM events: {len(kxfrm_events)}")

# Compute rolling 8-event CRPS/MAE
WINDOW_SIZE = 8
rolling_ratios = []

for i in range(len(kxfrm_events) - WINDOW_SIZE + 1):
    window = kxfrm_events[i:i + WINDOW_SIZE]
    crps_vals = [e["kalshi_crps"] for e in window if e.get("kalshi_crps")]
    mae_vals = [e["mae_interior"] for e in window if e.get("mae_interior") and e["mae_interior"] > 0]

    if len(crps_vals) == WINDOW_SIZE and len(mae_vals) == WINDOW_SIZE:
        ratio = np.mean(crps_vals) / np.mean(mae_vals)
        rolling_ratios.append({
            "window_idx": i,
            "start_event": window[0]["event_ticker"],
            "end_event": window[-1]["event_ticker"],
            "ratio": ratio,
            "above_1": ratio > 1.0,
            "events": [e["event_ticker"] for e in window],
        })

print(f"\nTotal rolling windows: {len(rolling_ratios)}")
print(f"Windows with ratio > 1.0: {sum(1 for r in rolling_ratios if r['above_1'])}")

# Identify 3-consecutive alert windows
alert_windows = []
alert_event_tickers = set()
for i in range(len(rolling_ratios) - 2):
    if (rolling_ratios[i]["above_1"] and
        rolling_ratios[i+1]["above_1"] and
        rolling_ratios[i+2]["above_1"]):
        alert_windows.append({
            "start_window": i,
            "end_window": i + 2,
            "start_event": rolling_ratios[i]["start_event"],
            "end_event": rolling_ratios[i+2]["end_event"],
            "ratios": [rolling_ratios[i]["ratio"], rolling_ratios[i+1]["ratio"], rolling_ratios[i+2]["ratio"]],
        })
        for j in range(i, i+3):
            for evt in rolling_ratios[j]["events"]:
                alert_event_tickers.add(evt)

print(f"\n3-consecutive alert clusters: {len(alert_windows)}")
if alert_windows:
    # Find the overall date range of alerts
    first_alert = alert_windows[0]
    last_alert = alert_windows[-1]
    print(f"\nAlert range:")
    print(f"  First alert window: {first_alert['start_event']} to {first_alert['end_event']}")
    print(f"  Last alert window: {last_alert['start_event']} to {last_alert['end_event']}")

    print(f"\nAll alert windows:")
    for i, aw in enumerate(alert_windows):
        print(f"  Alert {i+1}: windows {aw['start_window']}-{aw['end_window']}")
        print(f"    Events: {aw['start_event']} to {aw['end_event']}")
        print(f"    Ratios: {[f'{r:.2f}' for r in aw['ratios']]}")

    # Identify unique events involved in alert periods
    print(f"\nUnique events involved in alert periods: {len(alert_event_tickers)}")
    for evt in sorted(alert_event_tickers):
        print(f"    {evt}")

    # Check if alerts cluster in time
    # Extract date info from tickers (e.g., KXFRM-25FEB06)
    alert_dates = sorted(alert_event_tickers)
    non_alert_events = [e["event_ticker"] for e in kxfrm_events if e["event_ticker"] not in alert_event_tickers]

    print(f"\nNon-alert events: {len(non_alert_events)}")

    # Compute per-event ratios for alert vs non-alert
    alert_ratios = []
    non_alert_ratios = []
    for e in kxfrm_events:
        crps = e.get("kalshi_crps", 0)
        mae = e.get("mae_interior", 0)
        if mae and mae > 0:
            r = crps / mae
            if e["event_ticker"] in alert_event_tickers:
                alert_ratios.append(r)
            else:
                non_alert_ratios.append(r)

    print(f"\nAlert period events: n={len(alert_ratios)}, mean ratio={np.mean(alert_ratios):.2f}, median={np.median(alert_ratios):.2f}")
    print(f"Non-alert events: n={len(non_alert_ratios)}, mean ratio={np.mean(non_alert_ratios):.2f}, median={np.median(non_alert_ratios):.2f}")

# Also print per-event KXFRM ratios to see which events are problematic
print(f"\nAll KXFRM per-event ratios:")
for e in kxfrm_events:
    crps = e.get("kalshi_crps", 0)
    mae = e.get("mae_interior", 0)
    if mae and mae > 0:
        r = crps / mae
        alert_marker = " ⚠️" if e["event_ticker"] in alert_event_tickers else ""
        print(f"  {e['event_ticker']:25s}: CRPS/MAE={r:.2f}{alert_marker}")


# ============================================================
# PART 4: MONTE CARLO STRIKE-COUNT vs OVERCONCENTRATION
# ============================================================
print("\n" + "=" * 70)
print("PART 4: CONNECTING STRIKE-COUNT MONTE CARLO TO OVERCONCENTRATION")
print("=" * 70)

# The paper already reports that the Monte Carlo simulation shows
# strike count effects ≤2%. We just need to compute the observed
# overconcentration gap for comparison.

for series, std_val in sorted(std_pit_values.items(), key=lambda x: x[1]):
    gap_pct = (IDEAL_STD - std_val) / IDEAL_STD * 100
    print(f"  {series:15s}: std={std_val:.3f}, gap from ideal = {gap_pct:.1f}%")

min_gap = min((IDEAL_STD - v) / IDEAL_STD * 100 for v in std_pit_values.values())
max_gap = max((IDEAL_STD - v) / IDEAL_STD * 100 for v in std_pit_values.values())
print(f"\n  Overconcentration gap range: {min_gap:.1f}% to {max_gap:.1f}%")
print(f"  Monte Carlo strike-count effect: ≤2%")
print(f"  Conclusion: Observed gaps ({min_gap:.0f}-{max_gap:.0f}%) far exceed mechanical effect (≤2%)")


# ============================================================
# SAVE RESULTS
# ============================================================
print("\n" + "=" * 70)
print("SAVING RESULTS")
print("=" * 70)

results = {
    "overconcentration_test": {
        "sign_test": {
            "n_below": n_below,
            "n_total": n_total,
            "p_value": p_sign,
        },
        "pooled_bootstrap": {
            "n_pits": pooled_n,
            "pooled_std": float(pooled_std),
            "ci_lo": pooled_bootstrap_ci[0],
            "ci_hi": pooled_bootstrap_ci[1],
            "excludes_0289": pooled_bootstrap_ci[1] < IDEAL_STD,
        },
        "per_series_bootstrap": per_series_bootstrap,
    },
    "std_pit_vs_crps_mae": {
        "spearman_rho": float(rho),
        "spearman_p": float(p_val),
        "pearson_r": float(r_pearson),
        "pearson_p": float(p_pearson),
        "interpretation": interp,
    },
    "kxfrm_monitoring": {
        "n_events": len(kxfrm_events),
        "n_windows": len(rolling_ratios),
        "n_above_1": sum(1 for r in rolling_ratios if r["above_1"]),
        "n_3consec_alerts": len(alert_windows),
        "alert_windows": alert_windows,
        "alert_event_tickers": sorted(alert_event_tickers),
    },
    "overconcentration_gaps": {
        series: {
            "std_pit": std_val,
            "gap_pct": float((IDEAL_STD - std_val) / IDEAL_STD * 100),
        }
        for series, std_val in std_pit_values.items()
    },
}

output_path = os.path.join(OUTPUT_DIR, "iteration8_results.json")
with open(output_path, "w") as f:
    json.dump(results, f, indent=2, default=str)

print(f"\nResults saved to {output_path}")
print("\nDONE.")
