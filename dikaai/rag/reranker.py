"""
DikaAI Reranker - Rerank retrieved contexts by relevance.

Scores: semantic similarity + topic match + entity match + recency + importance
"""

import re
import time
from dataclasses import dataclass, field


@dataclass
class RankedResult:
    """A ranked retrieval result."""
    text: str
    score: float
    source: str = ""
    metadata: dict = field(default_factory=dict)


class Reranker:
    """Reranks retrieved contexts for optimal relevance."""

    def __init__(self):
        self.topic_weights = {
            'exact_match': 3.0,
            'partial_match': 1.5,
            'related': 0.5,
        }

    def rerank(self, query: str, results: list, topic: str = "",
               entities: list = None, max_results: int = 5) -> list:
        """Rerank results by multi-signal scoring.

        Args:
            query: Original user query
            results: List of text strings or dicts with 'text' key
            topic: Current conversation topic
            entities: Active entities in conversation
            max_results: Maximum results to return

        Returns:
            List of RankedResult sorted by score
        """
        if not results:
            return []

        query_words = set(query.lower().split())
        query_lower = query.lower()
        entities = entities or []

        scored = []
        for item in results:
            if isinstance(item, str):
                text = item
                meta = {}
            else:
                text = item.get('text', '')
                meta = item.get('metadata', {})

            score = self._compute_score(
                query_lower, query_words, text, topic, entities, meta
            )
            scored.append(RankedResult(
                text=text, score=score,
                source=meta.get('source', ''),
                metadata=meta,
            ))

        # Sort by score descending
        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[:max_results]

    def _compute_score(self, query_lower: str, query_words: set,
                       text: str, topic: str, entities: list,
                       metadata: dict) -> float:
        """Compute multi-signal relevance score."""
        text_lower = text.lower()
        text_words = set(text_lower.split())

        score = 0.0

        # 1. Semantic similarity (word overlap)
        overlap = len(query_words & text_words)
        if query_words:
            score += (overlap / len(query_words)) * 2.0

        # 2. Exact phrase match
        if query_lower in text_lower:
            score += 3.0

        # 3. Topic match
        text_topic = metadata.get('topic', '')
        if topic and text_topic:
            if text_topic == topic:
                score += 2.0
            elif topic in text_topic or text_topic in topic:
                score += 1.0

        # 4. Entity match
        for entity in entities:
            if entity.lower() in text_lower:
                score += 1.5

        # 5. Recency (newer is better)
        timestamp = metadata.get('timestamp', 0)
        if timestamp:
            age_hours = (time.time() - timestamp) / 3600
            recency = max(0, 1.0 - age_hours / 168)  # Decays over 1 week
            score += recency * 0.5

        # 6. Importance
        importance = metadata.get('importance', 0.5)
        score += importance * 1.0

        # 7. Length penalty (very short or very long penalized)
        text_len = len(text.split())
        if text_len < 5:
            score *= 0.5
        elif text_len > 500:
            score *= 0.8

        return score

    def rerank_memory(self, query: str, memory_entries: list,
                      topic: str = "", max_results: int = 5) -> list:
        """Rerank memory entries specifically."""
        results = []
        for entry in memory_entries:
            text = entry.content if hasattr(entry, 'content') else str(entry)
            meta = {}
            if hasattr(entry, 'topic'):
                meta['topic'] = entry.topic
            if hasattr(entry, 'timestamp'):
                meta['timestamp'] = entry.timestamp
            if hasattr(entry, 'importance'):
                meta['importance'] = entry.importance
            results.append({'text': text, 'metadata': meta})

        return self.rerank(query, results, topic=topic, max_results=max_results)
