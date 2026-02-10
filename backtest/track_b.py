"""
backtest/track_b.py

Phase 3: Generate Track B (RLM) predictions using Grok.

Implements the Recursive Language Model pipeline:
  1. Root Node — search for headlines relevant to the market
  2. Selection — pick the most informative, non-redundant headlines
  3. Sub-Agents — deep research on each selected headline
  4. Classification — self-consistency voting (k=5) over verbal bins

Run with:  uv run python -m backtest.track_b
"""

import hashlib
import json
import os
import time

import numpy as np
import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

# ── Constants ────────────────────────────────────────────────────────────────

GROK_SEARCH_MODEL = "grok-4-fast-non-reasoning"  # required for web_search tool
GROK_CHAT_MODEL = "grok-3-mini"                  # used for non-search steps
K_CONSISTENCY = 5       # self-consistency classification runs
N_HEADLINES = 50        # headlines to request from root search
CLASSIFY_TEMP = 0.7     # temperature for classification diversity

PROCESSED_DIR = "data/processed"
LLM_CACHE_DIR = "data/raw/llm"

VERBAL_BINS = {
    "STRONG_BUY": 2.0,
    "WEAK_BUY": 0.8,
    "NEUTRAL": 0.0,
    "WEAK_SELL": -0.8,
    "STRONG_SELL": -2.0,
}

GROK_API_KEY = os.environ.get("GROK_API_KEY", "")
GROK_BASE_URL = "https://api.x.ai/v1"


# ── Helpers ──────────────────────────────────────────────────────────────────

def _ticker_hash(ticker: str) -> str:
    """Short deterministic hash of a ticker for cache filenames."""
    return hashlib.sha256(ticker.encode()).hexdigest()[:12]


def _read_cache(path: str) -> str | None:
    """Return cached text if file exists, else None."""
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
        return data.get("text")
    return None


def _write_cache(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump({"text": text}, f)


# ── API wrappers ─────────────────────────────────────────────────────────────

def grok_responses_api(prompt: str) -> str:
    """Call the Grok Responses API with web_search tool enabled."""
    resp = requests.post(
        f"{GROK_BASE_URL}/responses",
        headers={
            "Authorization": f"Bearer {GROK_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": GROK_SEARCH_MODEL,
            "tools": [{"type": "web_search"}],
            "input": prompt,
        },
        timeout=120,
    )
    if not resp.ok:
        raise RuntimeError(f"Responses API {resp.status_code}: {resp.text[:300]}")
    data = resp.json()
    # Extract the text output from the response
    for block in data.get("output", []):
        if block.get("type") == "message":
            for content in block.get("content", []):
                if content.get("type") == "output_text":
                    return content["text"]
    # Fallback: try top-level output_text
    if "output_text" in data:
        return data["output_text"]
    return json.dumps(data.get("output", ""))


def grok_chat_api(messages: list[dict], temperature: float = 0.0) -> str:
    """Call the Grok Chat Completions API (no search)."""
    resp = requests.post(
        f"{GROK_BASE_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {GROK_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": GROK_CHAT_MODEL,
            "messages": messages,
            "temperature": temperature,
        },
        timeout=120,
    )
    if not resp.ok:
        raise RuntimeError(f"Chat API {resp.status_code}: {resp.text[:300]}")
    data = resp.json()
    return data["choices"][0]["message"]["content"]


# ── Pipeline steps ───────────────────────────────────────────────────────────

def step1_search_headlines(title: str, midpoint_date: str, ticker: str) -> str:
    """Root Node: search for top headlines relevant to the market."""
    cache_path = os.path.join(LLM_CACHE_DIR, f"root_{_ticker_hash(ticker)}.json")
    cached = _read_cache(cache_path)
    if cached is not None:
        return cached

    prompt = (
        f"Search for the top {N_HEADLINES} news headlines relevant to: '{title}'. "
        f"Date: {midpoint_date}. "
        f"Return a numbered list: [headline] — [1-sentence description]"
    )
    text = grok_responses_api(prompt)
    _write_cache(cache_path, text)
    return text


def step2_select_headlines(title: str, headlines_text: str, ticker: str) -> list[str]:
    """Selection: pick the most informative, non-redundant headlines."""
    cache_path = os.path.join(LLM_CACHE_DIR, f"select_{_ticker_hash(ticker)}.json")
    cached = _read_cache(cache_path)
    if cached is not None:
        # Parse the cached selection back into individual headlines
        return _parse_selected(cached, headlines_text)

    messages = [
        {
            "role": "system",
            "content": (
                "You are a financial research assistant. "
                "Select all informative and non-redundant headlines."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Market question: '{title}'\n\n"
                f"Headlines:\n{headlines_text}\n\n"
                f"From the numbered headlines above, select ALL that are informative and "
                f"non-redundant for predicting this market. Remove only duplicates or very "
                f"tangential headlines. Return ONLY the selected headline numbers, one per line."
            ),
        },
    ]
    text = grok_chat_api(messages)
    _write_cache(cache_path, text)
    return _parse_selected(text, headlines_text)


def _parse_selected(selection_text: str, headlines_text: str) -> list[str]:
    """Extract selected headlines from the numbered list (no cap on count)."""
    import re
    # Extract numbers from the selection response
    numbers = re.findall(r"\d+", selection_text)
    numbers = [int(n) for n in numbers]

    # Parse the headlines list to extract by number
    headlines_lines = headlines_text.strip().split("\n")
    selected = []
    for num in numbers:
        for line in headlines_lines:
            # Match lines starting with the number
            match = re.match(rf"^\s*{num}[\.\):\s]", line)
            if match:
                selected.append(line.strip())
                break
    # If parsing fails, fall back to all non-empty lines
    if not selected:
        selected = [l.strip() for l in headlines_lines if l.strip()]
    return selected


def step3_subagent_research(
    title: str, headline: str, midpoint_date: str, ticker: str, idx: int
) -> str:
    """Sub-Agent: deep research on a single selected headline."""
    cache_path = os.path.join(
        LLM_CACHE_DIR, f"subagent_{_ticker_hash(ticker)}_{idx}.json"
    )
    cached = _read_cache(cache_path)
    if cached is not None:
        return cached

    prompt = (
        f"Research this topic in depth: '{headline}'. "
        f"Context: predicting '{title}'. Date: {midpoint_date}. "
        f"Summarize key facts, data, and implications."
    )
    text = grok_responses_api(prompt)
    _write_cache(cache_path, text)
    return text


def step4_classify(
    title: str, research_summary: str, ticker: str, run_idx: int
) -> float:
    """Classification: single self-consistency run → log-odds."""
    cache_path = os.path.join(
        LLM_CACHE_DIR, f"classify_{_ticker_hash(ticker)}_{run_idx}.json"
    )
    cached = _read_cache(cache_path)
    if cached is not None:
        return parse_verbal_bin(cached)

    messages = [
        {
            "role": "system",
            "content": (
                "You are a prediction market analyst. "
                "Based on research provided, classify the likelihood that "
                "the market resolves YES."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Market question: '{title}'\n\n"
                f"Research summary:\n{research_summary}\n\n"
                f"Based on the research above, classify the likelihood that "
                f"this market resolves YES into EXACTLY one of these bins:\n"
                f"STRONG_BUY / WEAK_BUY / NEUTRAL / WEAK_SELL / STRONG_SELL\n\n"
                f"STRONG_BUY = very likely YES\n"
                f"WEAK_BUY = somewhat likely YES\n"
                f"NEUTRAL = uncertain / coin flip\n"
                f"WEAK_SELL = somewhat likely NO\n"
                f"STRONG_SELL = very likely NO\n\n"
                f"Respond with ONLY the bin name, nothing else."
            ),
        },
    ]
    text = grok_chat_api(messages, temperature=CLASSIFY_TEMP)
    _write_cache(cache_path, text)
    return parse_verbal_bin(text)


def parse_verbal_bin(text: str) -> float:
    """Map a verbal bin string to log-odds. Default to NEUTRAL on parse failure."""
    text_upper = text.strip().upper().replace(" ", "_")
    for bin_name, value in VERBAL_BINS.items():
        if bin_name in text_upper:
            return value
    return VERBAL_BINS["NEUTRAL"]


# ── Per-market prediction ────────────────────────────────────────────────────

def predict_market(title: str, midpoint_date: str, ticker: str) -> float:
    """Run the full 4-step RLM pipeline for one market. Returns L_news."""
    # Step 1: Search headlines
    headlines_text = step1_search_headlines(title, midpoint_date, ticker)

    # Step 2: Select best headlines
    selected = step2_select_headlines(title, headlines_text, ticker)

    # Step 3: Sub-agent deep research
    summaries = []
    for i, headline in enumerate(selected):
        summary = step3_subagent_research(title, headline, midpoint_date, ticker, i)
        summaries.append(summary)
    research_summary = "\n\n---\n\n".join(summaries)

    # Step 4: Self-consistency classification (k runs)
    log_odds = []
    for run in range(K_CONSISTENCY):
        lo = step4_classify(title, research_summary, ticker, run)
        log_odds.append(lo)

    return float(np.mean(log_odds))


# ── Data loading ─────────────────────────────────────────────────────────────

def load_market_metadata() -> dict[str, dict]:
    """Load market titles and midpoint dates, keyed by ticker."""
    # Load titles from settled markets JSON
    markets_path = "data/raw/settled_markets_6000.json"
    with open(markets_path) as f:
        markets = json.load(f)
    title_map = {m["ticker"]: m.get("title", m["ticker"]) for m in markets}

    # Load midpoint dates from universal features
    features = pd.read_csv(os.path.join(PROCESSED_DIR, "universal_features.csv"))
    midpoint_map = dict(zip(features["ticker"], features["midpoint"]))

    metadata = {}
    for ticker in title_map:
        metadata[ticker] = {
            "title": title_map[ticker],
            "midpoint": midpoint_map.get(ticker, ""),
        }
    # Also add any tickers from features not in markets
    for ticker in midpoint_map:
        if ticker not in metadata:
            metadata[ticker] = {
                "title": ticker,
                "midpoint": midpoint_map[ticker],
            }
    return metadata


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    os.makedirs(LLM_CACHE_DIR, exist_ok=True)

    if not GROK_API_KEY:
        raise RuntimeError("GROK_API_KEY not set in environment / .env")

    track_a = pd.read_csv(os.path.join(PROCESSED_DIR, "track_a_predictions.csv"))
    metadata = load_market_metadata()

    results = []
    total = len(track_a)

    for i, row in track_a.iterrows():
        ticker = row["ticker"]
        y_true = row["y_true"]
        meta = metadata.get(ticker, {"title": ticker, "midpoint": ""})
        title = meta["title"]
        midpoint = meta["midpoint"]

        # Extract just the date portion from the midpoint timestamp
        midpoint_date = str(midpoint).split("T")[0].split(" ")[0] if midpoint else ""

        print(f"[{i+1}/{total}] {ticker[:40]}...")
        try:
            L_news = predict_market(title, midpoint_date, ticker)
        except Exception as e:
            print(f"  ⚠ Error: {e}. Defaulting to NEUTRAL (0.0)")
            L_news = 0.0

        results.append({
            "ticker": ticker,
            "L_news": L_news,
            "mode": "LLM",
            "y_true": y_true,
        })

        # Brief pause to avoid rate limiting
        time.sleep(0.1)

    df = pd.DataFrame(results)
    df.to_csv(os.path.join(PROCESSED_DIR, "track_b_predictions.csv"), index=False)

    print(f"\n✅ Track B (LLM): {len(df)} predictions saved.")
    print(f"   Mode: LLM — real Grok RLM predictions.")
    print(f"   L_news range: [{df['L_news'].min():.2f}, {df['L_news'].max():.2f}]")
    print(f"   L_news mean:  {df['L_news'].mean():.2f}")


if __name__ == "__main__":
    main()
