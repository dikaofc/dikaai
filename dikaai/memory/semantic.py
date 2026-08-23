"""
DikaAI Semantic Memory - Facts and knowledge store.

Stores: facts, definitions, relationships, preferences
Enables: knowledge retrieval, fact checking, context enrichment
"""

import json
import time
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class Fact:
    """A stored fact or piece of knowledge."""
    subject: str
    predicate: str
    object: str
    confidence: float = 1.0
    source: str = ""
    timestamp: float = 0.0
    use_count: int = 0
    tags: list = field(default_factory=list)

    def to_text(self) -> str:
        return f"{self.subject} {self.predicate} {self.object}"

    def to_dict(self):
        return {
            'subject': self.subject,
            'predicate': self.predicate,
            'object': self.object,
            'confidence': self.confidence,
            'source': self.source,
            'tags': self.tags[:5],
        }


class SemanticMemory:
    """Facts and knowledge store."""

    def __init__(self, data_dir: str = None):
        self.data_dir = Path(data_dir or 'data/memory')
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.facts = []
        self._load()

    def add_fact(self, subject: str, predicate: str, obj: str,
                 confidence: float = 1.0, source: str = "",
                 tags: list = None) -> Fact:
        """Add a fact to semantic memory."""
        # Check for duplicate
        for fact in self.facts:
            if (fact.subject.lower() == subject.lower() and
                fact.predicate.lower() == predicate.lower()):
                # Update confidence
                fact.confidence = max(fact.confidence, confidence)
                fact.use_count += 1
                self._save()
                return fact

        fact = Fact(
            subject=subject, predicate=predicate, object=obj,
            confidence=confidence, source=source,
            timestamp=time.time(), tags=tags or [],
        )
        self.facts.append(fact)

        if len(self.facts) > 5000:
            self.facts.sort(key=lambda f: (f.confidence, f.use_count), reverse=True)
            self.facts = self.facts[:3000]

        self._save()
        return fact

    def search(self, query: str, top_k: int = 10) -> list:
        """Search facts by query."""
        query_words = set(query.lower().split())
        results = []

        for fact in self.facts:
            fact_text = fact.to_text().lower()
            fact_words = set(fact_text.split())
            overlap = len(query_words & fact_words)

            # Check subject/predicate/object match
            subject_match = 2 if any(w in fact.subject.lower() for w in query_words) else 0
            object_match = 1 if any(w in fact.object.lower() for w in query_words) else 0

            score = overlap + subject_match + object_match + fact.confidence

            if score > 1:
                results.append((score, fact))

        results.sort(key=lambda x: x[0], reverse=True)
        return [fact for _, fact in results[:top_k]]

    def get_by_subject(self, subject: str) -> list:
        """Get all facts about a subject."""
        return [f for f in self.facts if f.subject.lower() == subject.lower()]

    def get_facts_for_topic(self, topic: str, max_tokens: int = 300) -> str:
        """Get facts relevant to a topic as context string."""
        facts = self.search(topic, top_k=10)
        if not facts:
            return ""

        lines = ["KNOWLEDGE:"]
        total = 0
        for fact in facts:
            text = fact.to_text()
            tokens = len(text.split())
            if total + tokens > max_tokens:
                break
            lines.append(f"  • {text}")
            total += tokens

        return '\n'.join(lines)

    def extract_facts_from_text(self, text: str) -> list:
        """Extract facts from text using simple patterns."""
        facts = []
        # Pattern: X is Y
        for match in __import__('re').finditer(
            r'(\w[\w\s]*?)\s+(?:is|adalah|merupakan|ialah)\s+(.+?)[.!]',
            text, __import__('re').IGNORECASE
        ):
            subject = match.group(1).strip()
            obj = match.group(2).strip()
            if len(subject) > 2 and len(obj) > 2:
                facts.append(self.add_fact(subject, 'is', obj, source='auto_extract'))

        return facts

    def get_stats(self) -> dict:
        return {
            'total_facts': len(self.facts),
            'avg_confidence': sum(f.confidence for f in self.facts) / max(len(self.facts), 1),
        }

    def _save(self):
        data = [f.to_dict() for f in self.facts[-1000:]]
        path = self.data_dir / 'semantic_memory.json'
        with open(path, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _load(self):
        path = self.data_dir / 'semantic_memory.json'
        if not path.exists():
            return
        try:
            with open(path) as f:
                data = json.load(f)
            for d in data:
                self.facts.append(Fact(**d))
        except Exception:
            pass
