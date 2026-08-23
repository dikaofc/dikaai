"""DikaAI Embeddings - Simple text embeddings (pure Python, no numpy).

Uses character/word frequency hashing for fast embeddings.
Not as good as transformer embeddings, but works offline with zero deps.
"""

import math
import hashlib
import re
from collections import Counter


def _hash_token(token: str, dim: int) -> int:
    """Hash a token to an index."""
    h = hashlib.md5(token.encode()).hexdigest()
    return int(h, 16) % dim


def _hash_token_sign(token: str) -> float:
    """Get +1 or -1 for a token (consistent sign)."""
    h = hashlib.md5(token.encode()).hexdigest()
    return 1.0 if int(h[:8], 16) % 2 == 0 else -1.0


def embed_text(text: str, dim: int = 128) -> list:
    """Create a simple embedding vector for text.

    Uses TF-sign hashing: for each word, hash to a dimension
    and add/subtract based on consistent sign. Then normalize.
    """
    # Tokenize
    tokens = re.findall(r'\b\w+\b', text.lower())
    if not tokens:
        return [0.0] * dim

    # Count word frequencies
    counts = Counter(tokens)

    # Build embedding
    vec = [0.0] * dim
    for token, count in counts.items():
        idx = _hash_token(token, dim)
        sign = _hash_token_sign(token)
        vec[idx] += sign * math.log1p(count)

    # L2 normalize
    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 0:
        vec = [v / norm for v in vec]

    return vec


def cosine_similarity(a: list, b: list) -> float:
    """Compute cosine similarity between two vectors."""
    if len(a) != len(b):
        return 0.0
    dot = sum(ai * bi for ai, bi in zip(a, b))
    norm_a = math.sqrt(sum(ai * ai for ai in a))
    norm_b = math.sqrt(sum(bi * bi for bi in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def embed_chunks(text: str, chunk_size: int = 500, overlap: int = 50, dim: int = 128) -> list:
    """Split text into chunks and embed each."""
    words = text.split()
    chunks = []

    for i in range(0, len(words), chunk_size - overlap):
        chunk_words = words[i:i + chunk_size]
        chunk_text = ' '.join(chunk_words)
        embedding = embed_text(chunk_text, dim)
        chunks.append({
            'text': chunk_text,
            'embedding': embedding,
            'start': i,
            'end': min(i + chunk_size, len(words)),
        })

    return chunks
