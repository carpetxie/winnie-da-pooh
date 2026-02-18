"""
experiment5/embeddings.py

Generate sentence embeddings for market descriptions.
Uses sentence-transformers with BAAI/bge-base-en-v1.5 (768-dim, strong on financial text).
"""

import os
import json
import numpy as np
import pandas as pd
from tqdm import tqdm

DATA_DIR = "data/exp5"
DEFAULT_MODEL = "BAAI/bge-base-en-v1.5"


def load_or_generate_embeddings(
    texts: list[str],
    model_name: str = DEFAULT_MODEL,
    cache_path: str = None,
    batch_size: int = 256,
) -> np.ndarray:
    """
    Generate sentence embeddings, or load from cache.

    Args:
        texts: List of text strings to embed
        model_name: Sentence-transformer model name
        cache_path: Path to save/load .npy file
        batch_size: Batch size for encoding

    Returns:
        np.ndarray of shape (len(texts), embedding_dim)
    """
    if cache_path is None:
        cache_path = os.path.join(DATA_DIR, "embeddings.npy")

    metadata_path = cache_path.replace(".npy", "_metadata.json")

    # Check cache
    if os.path.exists(cache_path) and os.path.exists(metadata_path):
        with open(metadata_path) as f:
            meta = json.load(f)
        if meta.get("n_texts") == len(texts) and meta.get("model") == model_name:
            print(f"Loading cached embeddings from {cache_path}")
            return np.load(cache_path)
        print(f"Cache mismatch (cached {meta.get('n_texts')} vs {len(texts)} texts), regenerating...")

    print(f"Generating embeddings with {model_name}...")
    print(f"  {len(texts)} texts, batch_size={batch_size}")

    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(model_name)
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=True,
        normalize_embeddings=True,
    )
    embeddings = np.array(embeddings, dtype=np.float32)

    # Save cache
    os.makedirs(os.path.dirname(cache_path) or ".", exist_ok=True)
    np.save(cache_path, embeddings)

    metadata = {
        "model": model_name,
        "n_texts": len(texts),
        "embedding_dim": embeddings.shape[1],
        "dtype": str(embeddings.dtype),
    }
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"  Embeddings shape: {embeddings.shape}")
    print(f"  Saved to {cache_path}")

    return embeddings


def compute_cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two vectors."""
    dot = np.dot(a, b)
    norm = np.linalg.norm(a) * np.linalg.norm(b)
    return float(dot / norm) if norm > 0 else 0.0


def pairwise_cosine_similarity(embeddings: np.ndarray) -> np.ndarray:
    """
    Compute pairwise cosine similarity matrix.
    Assumes embeddings are L2-normalized (dot product = cosine similarity).

    Args:
        embeddings: (N, D) array of L2-normalized embeddings

    Returns:
        (N, N) similarity matrix
    """
    return embeddings @ embeddings.T


def main():
    """Generate embeddings from cached market data."""
    markets_path = os.path.join(DATA_DIR, "markets.csv")
    if not os.path.exists(markets_path):
        print(f"Error: {markets_path} not found. Run data_collection.py first.")
        return

    df = pd.read_csv(markets_path)
    texts = df["text_for_embedding"].tolist()

    embeddings = load_or_generate_embeddings(texts)
    print(f"Done. Shape: {embeddings.shape}")


if __name__ == "__main__":
    main()
