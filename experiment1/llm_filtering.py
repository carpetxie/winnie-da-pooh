"""
experiment1/llm_filtering.py

Use Grok API to assess economic plausibility of statistically
significant lead-lag pairs. Filters spurious correlations.
"""

import os
import re
import json
import time
import requests
import pandas as pd

DATA_DIR = "data/exp1"


def build_plausibility_prompt(
    leader_title: str,
    leader_domain: str,
    follower_title: str,
    follower_domain: str,
    lag_hours: int,
) -> str:
    """Build the prompt for LLM plausibility assessment."""
    return f"""You are assessing whether a statistical lead-lag relationship between two Kalshi prediction markets represents a genuine economic connection or a spurious correlation.

Market A (leader, {leader_domain}): "{leader_title}"
Market B (follower, {follower_domain}): "{follower_title}"

Statistical finding: Price movements in Market A predict price movements in Market B with a lag of {lag_hours} hours (Granger causality test, significant after Bonferroni correction).

Questions:
1. Is there a plausible economic transmission mechanism by which information reflected in Market A would predict Market B?
2. Rate the plausibility on a scale of 1-5:
   1 = No plausible connection (likely spurious)
   2 = Very weak / stretch
   3 = Possible but uncertain
   4 = Plausible economic mechanism exists
   5 = Strong, well-known economic connection

Respond with exactly:
SCORE: X/5
EXPLANATION: [2-3 sentences explaining your reasoning]"""


def parse_plausibility_score(response_text: str) -> int:
    """Parse the plausibility score from LLM response.

    Handles formats: "SCORE: 4/5", "Score: 4", "4/5", etc.
    Returns score 1-5 or 0 if parsing fails.
    """
    # Try "SCORE: X/5" or "Score: X/5"
    match = re.search(r"[Ss]core:\s*(\d)/5", response_text)
    if match:
        return int(match.group(1))

    # Try "X/5" anywhere
    match = re.search(r"(\d)/5", response_text)
    if match:
        return int(match.group(1))

    # Try "score: X" without /5
    match = re.search(r"[Ss]core:\s*(\d)", response_text)
    if match:
        return int(match.group(1))

    return 0


def assess_pair_plausibility(
    leader_title: str,
    leader_domain: str,
    follower_title: str,
    follower_domain: str,
    lag_hours: int,
    grok_api_key: str,
) -> dict:
    """Call Grok API to rate plausibility of a lead-lag pair.

    Returns dict with plausibility_score, explanation, raw_response.
    """
    prompt = build_plausibility_prompt(
        leader_title, leader_domain, follower_title, follower_domain, lag_hours
    )

    try:
        response = requests.post(
            "https://api.x.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {grok_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "grok-3-mini-fast",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an economics and financial markets analyst. Be precise and concise.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 200,
                "temperature": 0.2,
            },
            timeout=30,
        )
        response.raise_for_status()
        raw = response.json()["choices"][0]["message"]["content"]
        score = parse_plausibility_score(raw)

        # Extract explanation
        explanation = raw
        exp_match = re.search(r"EXPLANATION:\s*(.*)", raw, re.DOTALL)
        if exp_match:
            explanation = exp_match.group(1).strip()

        return {
            "plausibility_score": score,
            "explanation": explanation,
            "raw_response": raw,
        }

    except Exception as e:
        return {
            "plausibility_score": 0,
            "explanation": f"API error: {e}",
            "raw_response": "",
        }


def run_llm_filtering(
    significant_pairs: pd.DataFrame,
    grok_api_key: str,
    min_score: int = 4,
) -> pd.DataFrame:
    """Run LLM filtering on all significant Granger pairs.

    Args:
        significant_pairs: DataFrame with leader/follower info
        grok_api_key: xAI API key
        min_score: Minimum plausibility score to keep (1-5)

    Returns:
        DataFrame filtered to score >= min_score
    """
    cache_path = os.path.join(DATA_DIR, "llm_assessments.json")

    # Load cache if exists
    cached = {}
    if os.path.exists(cache_path):
        with open(cache_path) as f:
            cached_list = json.load(f)
        for item in cached_list:
            key = f"{item['leader_ticker']}|{item['follower_ticker']}"
            cached[key] = item
        print(f"  Loaded {len(cached)} cached LLM assessments")

    assessments = []
    new_assessments = 0

    for _, row in significant_pairs.iterrows():
        key = f"{row['leader_ticker']}|{row['follower_ticker']}"

        if key in cached:
            assessments.append(cached[key])
            continue

        result = assess_pair_plausibility(
            leader_title=row["leader_title"],
            leader_domain=row["leader_domain"],
            follower_title=row["follower_title"],
            follower_domain=row["follower_domain"],
            lag_hours=int(row["best_lag"]),
            grok_api_key=grok_api_key,
        )

        assessment = {
            "leader_ticker": row["leader_ticker"],
            "follower_ticker": row["follower_ticker"],
            "leader_domain": row["leader_domain"],
            "follower_domain": row["follower_domain"],
            "best_lag": int(row["best_lag"]),
            **result,
        }
        assessments.append(assessment)
        new_assessments += 1

        # Rate limit
        time.sleep(0.5)

        # Periodic save
        if new_assessments % 10 == 0:
            os.makedirs(DATA_DIR, exist_ok=True)
            with open(cache_path, "w") as f:
                json.dump(assessments, f, indent=2)

    # Final save
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(cache_path, "w") as f:
        json.dump(assessments, f, indent=2)
    print(f"  {new_assessments} new LLM assessments, {len(assessments)} total")

    # Merge scores back into the pairs DataFrame
    score_map = {
        f"{a['leader_ticker']}|{a['follower_ticker']}": a
        for a in assessments
    }

    significant_pairs = significant_pairs.copy()
    significant_pairs["plausibility_score"] = significant_pairs.apply(
        lambda r: score_map.get(f"{r['leader_ticker']}|{r['follower_ticker']}", {}).get("plausibility_score", 0),
        axis=1,
    )
    significant_pairs["llm_explanation"] = significant_pairs.apply(
        lambda r: score_map.get(f"{r['leader_ticker']}|{r['follower_ticker']}", {}).get("explanation", ""),
        axis=1,
    )
    significant_pairs["llm_approved"] = significant_pairs["plausibility_score"] >= min_score

    n_approved = significant_pairs["llm_approved"].sum()
    print(f"  LLM approved: {n_approved}/{len(significant_pairs)} pairs (score >= {min_score})")

    return significant_pairs
