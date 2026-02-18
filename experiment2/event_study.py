"""
experiment2/event_study.py

Event study analysis: identify major economic events and measure whether
the KUI domain sub-indices detect uncertainty changes before EPU/VIX.
"""

import numpy as np
import pandas as pd


def get_economic_events() -> pd.DataFrame:
    """Return a curated list of major US economic events (2025-2026).

    Each event has:
        - date: event date
        - type: event category (CPI, NFP, FOMC, GDP, tariff, etc.)
        - description: brief description
        - surprise: whether the outcome was a significant surprise
        - relevant_domain: which KUI domain sub-index is most relevant
    """
    events = [
        # CPI Releases (typically 8:30 AM ET on release day)
        {"date": "2025-03-12", "type": "CPI", "description": "February 2025 CPI",
         "surprise": True, "relevant_domain": "inflation"},
        {"date": "2025-04-10", "type": "CPI", "description": "March 2025 CPI",
         "surprise": False, "relevant_domain": "inflation"},
        {"date": "2025-05-13", "type": "CPI", "description": "April 2025 CPI",
         "surprise": True, "relevant_domain": "inflation"},
        {"date": "2025-06-11", "type": "CPI", "description": "May 2025 CPI",
         "surprise": False, "relevant_domain": "inflation"},
        {"date": "2025-07-10", "type": "CPI", "description": "June 2025 CPI",
         "surprise": False, "relevant_domain": "inflation"},
        {"date": "2025-08-12", "type": "CPI", "description": "July 2025 CPI",
         "surprise": False, "relevant_domain": "inflation"},
        {"date": "2025-09-10", "type": "CPI", "description": "August 2025 CPI",
         "surprise": True, "relevant_domain": "inflation"},
        {"date": "2025-10-10", "type": "CPI", "description": "September 2025 CPI",
         "surprise": False, "relevant_domain": "inflation"},
        {"date": "2025-11-12", "type": "CPI", "description": "October 2025 CPI",
         "surprise": False, "relevant_domain": "inflation"},
        {"date": "2025-12-10", "type": "CPI", "description": "November 2025 CPI",
         "surprise": True, "relevant_domain": "inflation"},
        {"date": "2026-01-15", "type": "CPI", "description": "December 2025 CPI",
         "surprise": False, "relevant_domain": "inflation"},

        # FOMC Meetings (decision date)
        {"date": "2025-03-19", "type": "FOMC", "description": "March 2025 FOMC",
         "surprise": False, "relevant_domain": "monetary_policy"},
        {"date": "2025-05-07", "type": "FOMC", "description": "May 2025 FOMC",
         "surprise": False, "relevant_domain": "monetary_policy"},
        {"date": "2025-06-18", "type": "FOMC", "description": "June 2025 FOMC",
         "surprise": True, "relevant_domain": "monetary_policy"},
        {"date": "2025-07-30", "type": "FOMC", "description": "July 2025 FOMC",
         "surprise": False, "relevant_domain": "monetary_policy"},
        {"date": "2025-09-17", "type": "FOMC", "description": "September 2025 FOMC",
         "surprise": True, "relevant_domain": "monetary_policy"},
        {"date": "2025-11-05", "type": "FOMC", "description": "November 2025 FOMC",
         "surprise": False, "relevant_domain": "monetary_policy"},
        {"date": "2025-12-17", "type": "FOMC", "description": "December 2025 FOMC",
         "surprise": True, "relevant_domain": "monetary_policy"},
        {"date": "2026-01-29", "type": "FOMC", "description": "January 2026 FOMC",
         "surprise": False, "relevant_domain": "monetary_policy"},

        # NFP (Nonfarm Payrolls, first Friday of month)
        {"date": "2025-03-07", "type": "NFP", "description": "February 2025 NFP",
         "surprise": True, "relevant_domain": "labor_market"},
        {"date": "2025-04-04", "type": "NFP", "description": "March 2025 NFP",
         "surprise": False, "relevant_domain": "labor_market"},
        {"date": "2025-05-02", "type": "NFP", "description": "April 2025 NFP",
         "surprise": False, "relevant_domain": "labor_market"},
        {"date": "2025-06-06", "type": "NFP", "description": "May 2025 NFP",
         "surprise": True, "relevant_domain": "labor_market"},
        {"date": "2025-07-03", "type": "NFP", "description": "June 2025 NFP",
         "surprise": False, "relevant_domain": "labor_market"},
        {"date": "2025-08-01", "type": "NFP", "description": "July 2025 NFP",
         "surprise": False, "relevant_domain": "labor_market"},

        # GDP Releases (quarterly)
        {"date": "2025-03-27", "type": "GDP", "description": "Q4 2024 GDP (third estimate)",
         "surprise": False, "relevant_domain": "fiscal_policy"},
        {"date": "2025-06-26", "type": "GDP", "description": "Q1 2025 GDP (third estimate)",
         "surprise": True, "relevant_domain": "fiscal_policy"},
        {"date": "2025-09-25", "type": "GDP", "description": "Q2 2025 GDP (third estimate)",
         "surprise": False, "relevant_domain": "fiscal_policy"},
        {"date": "2025-12-23", "type": "GDP", "description": "Q3 2025 GDP (third estimate)",
         "surprise": False, "relevant_domain": "fiscal_policy"},

        # Tariff / Geopolitical Events
        {"date": "2025-04-02", "type": "tariff", "description": "Trump Liberation Day tariffs",
         "surprise": True, "relevant_domain": "geopolitics"},
        {"date": "2025-04-09", "type": "tariff", "description": "90-day tariff pause",
         "surprise": True, "relevant_domain": "geopolitics"},
    ]

    df = pd.DataFrame(events)
    df["date"] = pd.to_datetime(df["date"])
    return df


def extract_event_window(
    series: pd.Series,
    event_date: pd.Timestamp,
    window_days: int = 7,
) -> pd.Series:
    """Extract a [-window_days, +window_days] window around an event.

    Args:
        series: Time series with DatetimeIndex
        event_date: Center date
        window_days: Days before and after event

    Returns:
        Series clipped to the event window, with index as day offsets
    """
    start = event_date - pd.Timedelta(days=window_days)
    end = event_date + pd.Timedelta(days=window_days)

    window = series[(series.index >= start) & (series.index <= end)].copy()

    if window.empty:
        return pd.Series(dtype=float)

    # Convert index to day offsets from event
    window.index = (window.index - event_date).days

    return window


def detect_first_significant_move(
    window: pd.Series,
    pre_event_end: int = -1,
    threshold_std: float = 2.0,
) -> int | None:
    """Detect the first significant move in a time series window.

    "Significant" = value exceeds pre-event mean +/- threshold_std * pre-event_std.

    Args:
        window: Series indexed by day offsets (negative = before event, 0 = event day)
        pre_event_end: Last day to include in pre-event baseline (default: day -1)
        threshold_std: Number of standard deviations for significance

    Returns:
        Day offset of first significant move, or None
    """
    # Pre-event baseline: days before pre_event_end
    pre_event = window[window.index <= pre_event_end]

    if len(pre_event) < 3:
        return None

    baseline_mean = pre_event.mean()
    baseline_std = pre_event.std()

    if baseline_std == 0 or np.isnan(baseline_std):
        return None

    upper = baseline_mean + threshold_std * baseline_std
    lower = baseline_mean - threshold_std * baseline_std

    # Look for first breach (starting from pre_event_end)
    post_baseline = window[window.index > pre_event_end].sort_index()

    for day_offset, value in post_baseline.items():
        if value > upper or value < lower:
            return int(day_offset)

    return None


def compute_event_lead_lag(
    kalshi_window: pd.Series,
    traditional_window: pd.Series,
    threshold_std: float = 1.5,
) -> dict:
    """Compute lead-lag between Kalshi and traditional indicator around an event.

    Args:
        kalshi_window: KUI domain sub-index in event window
        traditional_window: EPU or VIX in event window

    Returns:
        Dict with kalshi_first_move, traditional_first_move, lead_lag_days
        Negative lead_lag = Kalshi leads (moves first)
    """
    kalshi_move = detect_first_significant_move(kalshi_window, threshold_std=threshold_std)
    traditional_move = detect_first_significant_move(traditional_window, threshold_std=threshold_std)

    result = {
        "kalshi_first_move_day": kalshi_move,
        "traditional_first_move_day": traditional_move,
        "lead_lag_days": None,
    }

    if kalshi_move is not None and traditional_move is not None:
        result["lead_lag_days"] = kalshi_move - traditional_move

    return result


def run_event_study(
    kui_domain_indices: dict,
    epu: pd.Series,
    vix: pd.Series,
    events: pd.DataFrame = None,
    window_days: int = 7,
) -> pd.DataFrame:
    """Run the full event study analysis.

    For each economic event:
    1. Extract event windows from relevant KUI sub-index and EPU/VIX
    2. Detect first significant moves
    3. Compute lead-lag

    Returns:
        DataFrame with event details and lead-lag results
    """
    if events is None:
        events = get_economic_events()

    results = []

    for _, event in events.iterrows():
        event_date = event["date"]
        domain = event["relevant_domain"]
        event_type = event["type"]

        # Get relevant KUI domain sub-index
        kui_series = kui_domain_indices.get(domain)
        if kui_series is None or kui_series.dropna().empty:
            continue

        # Extract windows
        kui_window = extract_event_window(kui_series, event_date, window_days)
        epu_window = extract_event_window(epu, event_date, window_days)
        vix_window = extract_event_window(vix, event_date, window_days)

        # Lead-lag vs EPU
        epu_ll = compute_event_lead_lag(kui_window, epu_window)
        vix_ll = compute_event_lead_lag(kui_window, vix_window)

        results.append({
            "event_date": event_date.strftime("%Y-%m-%d"),
            "event_type": event_type,
            "description": event["description"],
            "surprise": event["surprise"],
            "relevant_domain": domain,
            "kui_window_size": len(kui_window),
            "kui_first_move_vs_epu": epu_ll["kalshi_first_move_day"],
            "epu_first_move": epu_ll["traditional_first_move_day"],
            "lead_lag_vs_epu": epu_ll["lead_lag_days"],
            "kui_first_move_vs_vix": vix_ll["kalshi_first_move_day"],
            "vix_first_move": vix_ll["traditional_first_move_day"],
            "lead_lag_vs_vix": vix_ll["lead_lag_days"],
        })

    return pd.DataFrame(results)


def summarize_event_study(results: pd.DataFrame) -> dict:
    """Summarize event study results.

    Returns:
        Dict with aggregate statistics
    """
    if results.empty:
        return {"n_events": 0}

    # Lead-lag vs EPU
    ll_epu = results["lead_lag_vs_epu"].dropna()
    ll_vix = results["lead_lag_vs_vix"].dropna()

    # Surprise events only
    surprise_mask = results["surprise"] == True
    ll_epu_surprise = results.loc[surprise_mask, "lead_lag_vs_epu"].dropna()
    ll_vix_surprise = results.loc[surprise_mask, "lead_lag_vs_vix"].dropna()

    summary = {
        "n_events": len(results),
        "n_with_epu_leadlag": len(ll_epu),
        "n_with_vix_leadlag": len(ll_vix),
        # EPU lead-lag
        "mean_lead_lag_vs_epu": round(ll_epu.mean(), 2) if len(ll_epu) > 0 else None,
        "median_lead_lag_vs_epu": round(ll_epu.median(), 2) if len(ll_epu) > 0 else None,
        "pct_kalshi_leads_epu": round((ll_epu < 0).mean(), 3) if len(ll_epu) > 0 else None,
        # VIX lead-lag
        "mean_lead_lag_vs_vix": round(ll_vix.mean(), 2) if len(ll_vix) > 0 else None,
        "median_lead_lag_vs_vix": round(ll_vix.median(), 2) if len(ll_vix) > 0 else None,
        "pct_kalshi_leads_vix": round((ll_vix < 0).mean(), 3) if len(ll_vix) > 0 else None,
        # Surprise events
        "n_surprise_events": int(surprise_mask.sum()),
        "mean_lead_lag_surprise_epu": round(ll_epu_surprise.mean(), 2) if len(ll_epu_surprise) > 0 else None,
        "mean_lead_lag_surprise_vix": round(ll_vix_surprise.mean(), 2) if len(ll_vix_surprise) > 0 else None,
    }

    # By event type
    for event_type in results["event_type"].unique():
        type_ll = results.loc[results["event_type"] == event_type, "lead_lag_vs_epu"].dropna()
        if len(type_ll) > 0:
            summary[f"mean_lead_lag_{event_type}_vs_epu"] = round(type_ll.mean(), 2)

    return summary
