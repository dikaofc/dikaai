"""DikaAI Context Quality Engine

Scores and filters context for relevance, freshness, deduplication, and importance.
Ensures only the most useful context is sent to the model.
"""
import time
import re
from typing import List, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class ContextChunk:
    """A piece of context with quality metadata."""
    content: str
    source: str = "unknown"        # user, memory, rag, project, tool
    timestamp: float = 0.0
    relevance: float = 0.0         # 0-1 how relevant to current query
    freshness: float = 0.0         # 0-1 how recent
    authority: float = 0.5         # 0-1 how trustworthy the source
    importance: float = 0.5        # 0-1 how important the content
    dedup_hash: str = ""           # for deduplication
    tokens: int = 0
    metadata: Dict = field(default_factory=dict)

    def quality_score(self) -> float:
        """Combined quality score (0-1)."""
        return (
            self.relevance * 0.35 +
            self.freshness * 0.15 +
            self.authority * 0.20 +
            self.importance * 0.30
        )


class ContextQualityEngine:
    """Evaluates, scores, filters, and deduplicates context chunks."""

    def __init__(self, max_tokens: int = 4000):
        self.max_tokens = max_tokens
        self._seen_hashes = set()

    def score_chunks(self, chunks: List[ContextChunk], query: str) -> List[ContextChunk]:
        """Score and rank context chunks for a given query."""
        query_lower = query.lower()
        query_words = set(query_lower.split())

        for chunk in chunks:
            # Relevance: keyword overlap + semantic hints
            chunk.relevance = self._score_relevance(chunk, query_lower, query_words)

            # Freshness: newer = better (exponential decay)
            chunk.freshness = self._score_freshness(chunk.timestamp)

            # Dedup hash
            chunk.dedup_hash = self._hash_content(chunk.content)

        # Deduplicate
        chunks = self._deduplicate(chunks)

        # Sort by quality score (best first)
        chunks.sort(key=lambda c: c.quality_score(), reverse=True)

        # Fit within token budget
        return self._fit_budget(chunks)

    def _score_relevance(self, chunk: ContextChunk, query_lower: str, query_words: set) -> float:
        """Score relevance based on keyword overlap and content analysis."""
        content_lower = chunk.content.lower()
        content_words = set(content_lower.split())

        if not query_words:
            return 0.3

        # Direct keyword overlap
        overlap = len(query_words & content_words)
        keyword_score = min(overlap / max(len(query_words), 1), 1.0)

        # Exact phrase match bonus
        phrase_bonus = 0.2 if query_lower in content_lower else 0.0

        # Content length penalty (very short = less useful)
        length_factor = min(len(chunk.content) / 100, 1.0)

        # Source authority bonus
        source_bonus = {
            'tool': 0.15,      # Tool output = ground truth
            'user': 0.10,      # User input = direct
            'project': 0.10,   # Project files = relevant
            'rag': 0.05,       # RAG = might be relevant
            'memory': 0.05,    # Memory = might be stale
        }.get(chunk.source, 0.0)

        return min(keyword_score * 0.6 + phrase_bonus + length_factor * 0.1 + source_bonus + 0.1, 1.0)

    def _score_freshness(self, timestamp: float) -> float:
        """Score freshness based on age (exponential decay)."""
        if timestamp <= 0:
            return 0.3  # Unknown age = medium
        age_seconds = time.time() - timestamp
        if age_seconds < 60:
            return 1.0        # < 1 min
        elif age_seconds < 3600:
            return 0.8        # < 1 hour
        elif age_seconds < 86400:
            return 0.6        # < 1 day
        elif age_seconds < 604800:
            return 0.4        # < 1 week
        else:
            return 0.2        # older

    def _hash_content(self, content: str) -> str:
        """Simple content hash for deduplication."""
        # Normalize: lowercase, strip whitespace, collapse spaces
        normalized = re.sub(r'\s+', ' ', content.lower().strip())
        return str(hash(normalized))

    def _deduplicate(self, chunks: List[ContextChunk]) -> List[ContextChunk]:
        """Remove duplicate chunks, keep the one with higher quality."""
        seen = {}
        for chunk in chunks:
            h = chunk.dedup_hash
            if h not in seen:
                seen[h] = chunk
            else:
                # Keep the one with higher quality score
                if chunk.quality_score() > seen[h].quality_score():
                    seen[h] = chunk
        return list(seen.values())

    def _fit_budget(self, chunks: List[ContextChunk]) -> List[ContextChunk]:
        """Select chunks that fit within token budget."""
        result = []
        total_tokens = 0

        for chunk in chunks:
            chunk_tokens = len(chunk.content.split())  # rough estimate
            if total_tokens + chunk_tokens <= self.max_tokens:
                result.append(chunk)
                total_tokens += chunk_tokens
            else:
                # Try to fit a truncated version
                remaining = self.max_tokens - total_tokens
                if remaining > 20:
                    words = chunk.content.split()[:remaining]
                    truncated = ContextChunk(
                        content=' '.join(words) + '...',
                        source=chunk.source,
                        timestamp=chunk.timestamp,
                        relevance=chunk.relevance,
                        freshness=chunk.freshness,
                        authority=chunk.authority,
                        importance=chunk.importance,
                        tokens=remaining,
                    )
                    result.append(truncated)
                break

        return result

    def build_optimized_context(self, chunks: List[ContextChunk], query: str,
                                 max_tokens: int = None) -> str:
        """Build optimized context string from chunks."""
        if max_tokens:
            self.max_tokens = max_tokens

        scored = self.score_chunks(chunks, query)
        return '\n\n'.join(c.content for c in scored)

    def get_stats(self) -> Dict:
        return {
            'max_tokens': self.max_tokens,
            'seen_hashes': len(self._seen_hashes),
        }
