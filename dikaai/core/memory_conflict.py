"""DikaAI Memory Conflict Resolver

Detects contradictory facts in memory and auto-updates to keep only the latest truth.
Tracks provenance, confidence, and history of all facts.
"""
import time
import json
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import threading


@dataclass
class Fact:
    """A single fact with full metadata."""
    subject: str           # "Python version"
    predicate: str         # "is"
    value: str             # "3.13"
    source: str = "unknown"  # user, tool, rag, inference
    confidence: float = 1.0  # 0-1
    created_at: float = 0.0
    updated_at: float = 0.0
    status: str = "active"  # active, superseded, deleted
    history: List[Dict] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)

    def key(self) -> str:
        """Unique key for this fact (subject + predicate)."""
        return f"{self.subject.lower().strip()}|{self.predicate.lower().strip()}"

    def conflicts_with(self, other: 'Fact') -> bool:
        """Check if two facts conflict (same subject+predicate, different value)."""
        if self.key() != other.key():
            return False
        return self.value.lower().strip() != other.value.lower().strip()

    def is_newer_than(self, other: 'Fact') -> bool:
        return self.updated_at > other.updated_at

    def is_more_confident(self, other: 'Fact') -> bool:
        return self.confidence > other.confidence

    def to_dict(self) -> Dict:
        return {
            'subject': self.subject,
            'predicate': self.predicate,
            'value': self.value,
            'source': self.source,
            'confidence': self.confidence,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'status': self.status,
            'history': self.history[-5:],  # Keep last 5 changes
            'metadata': self.metadata,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> 'Fact':
        return cls(
            subject=d.get('subject', ''),
            predicate=d.get('predicate', 'is'),
            value=d.get('value', ''),
            source=d.get('source', 'unknown'),
            confidence=float(d.get('confidence', 1.0)),
            created_at=float(d.get('created_at', 0)),
            updated_at=float(d.get('updated_at', 0)),
            status=d.get('status', 'active'),
            history=d.get('history', []),
            metadata=d.get('metadata', {}),
        )


class MemoryConflictResolver:
    """Manages facts with automatic conflict detection and resolution."""

    def __init__(self, data_dir: str = None):
        self._facts: Dict[str, Fact] = {}  # key -> Fact
        self._lock = threading.Lock()
        self._data_dir = Path(data_dir) if data_dir else Path("data/memory")
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._load()

    def _load(self):
        """Load facts from disk."""
        path = self._data_dir / "facts.json"
        if path.exists():
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                for d in data:
                    fact = Fact.from_dict(d)
                    if fact.status == 'active':
                        self._facts[fact.key()] = fact
            except Exception:
                pass

    def _save(self):
        """Save facts to disk."""
        path = self._data_dir / "facts.json"
        try:
            data = [f.to_dict() for f in self._facts.values()]
            # Also save superseded facts (last 100)
            superseded = [f.to_dict() for f in self._facts.values() if f.status == 'superseded']
            all_facts = data + superseded[-100:]
            with open(path, 'w') as f:
                json.dump(all_facts, f, indent=2)
        except Exception:
            pass

    def add_fact(self, subject: str, predicate: str, value: str,
                 source: str = "unknown", confidence: float = 1.0,
                 metadata: Dict = None) -> Dict:
        """Add a fact. Returns conflict resolution result.

        Returns:
            {
                'action': 'created' | 'updated' | 'unchanged' | 'conflict_resolved',
                'fact': Fact dict,
                'previous': previous Fact dict (if updated/conflict),
            }
        """
        now = time.time()
        new_fact = Fact(
            subject=subject.strip(),
            predicate=predicate.strip(),
            value=value.strip(),
            source=source,
            confidence=confidence,
            created_at=now,
            updated_at=now,
            status='active',
            metadata=metadata or {},
        )
        key = new_fact.key()

        with self._lock:
            if key not in self._facts:
                # New fact - create it
                self._facts[key] = new_fact
                self._save()
                return {'action': 'created', 'fact': new_fact.to_dict(), 'previous': None}

            existing = self._facts[key]

            # Check if values are the same
            if existing.value.lower().strip() == value.lower().strip():
                # Update metadata but keep status
                existing.updated_at = now
                existing.confidence = max(existing.confidence, confidence)
                self._save()
                return {'action': 'unchanged', 'fact': existing.to_dict(), 'previous': None}

            # CONFLICT detected!
            # Resolution strategy: newer + higher confidence wins
            should_update = (
                new_fact.is_newer_than(existing) or
                (new_fact.is_more_confident(existing) and new_fact.confidence >= 0.8)
            )

            if should_update:
                # Supersede old fact
                existing.status = 'superseded'
                existing.history.append({
                    'value': existing.value,
                    'superseded_at': now,
                    'superseded_by': value,
                    'source': source,
                })

                # Create new active fact
                new_fact.created_at = existing.created_at  # Keep original creation time
                new_fact.history = existing.history.copy()
                self._facts[key] = new_fact
                self._save()
                return {
                    'action': 'conflict_resolved',
                    'fact': new_fact.to_dict(),
                    'previous': existing.to_dict(),
                }
            else:
                # Keep existing (it's newer or higher confidence)
                return {
                    'action': 'unchanged',
                    'fact': existing.to_dict(),
                    'previous': None,
                }

    def get_fact(self, subject: str, predicate: str = "is") -> Optional[Fact]:
        """Get a specific fact."""
        key = f"{subject.lower().strip()}|{predicate.lower().strip()}"
        return self._facts.get(key)

    def get_facts_for_query(self, query: str, limit: int = 10) -> List[Fact]:
        """Find facts relevant to a query."""
        query_lower = query.lower()
        query_words = set(query_lower.split())

        scored = []
        for fact in self._facts.values():
            if fact.status != 'active':
                continue
            # Score by keyword overlap
            fact_words = set(f"{fact.subject} {fact.predicate} {fact.value}".lower().split())
            overlap = len(query_words & fact_words)
            if overlap > 0:
                scored.append((overlap, fact))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [f for _, f in scored[:limit]]

    def get_all_active(self) -> List[Fact]:
        """Get all active facts."""
        return [f for f in self._facts.values() if f.status == 'active']

    def get_conflicts(self) -> List[Dict]:
        """Get all conflicts (superseded facts with history)."""
        conflicts = []
        for fact in self._facts.values():
            if fact.history:
                conflicts.append({
                    'subject': fact.subject,
                    'current_value': fact.value,
                    'previous_values': [h['value'] for h in fact.history],
                    'sources': [h.get('source', '?') for h in fact.history],
                })
        return conflicts

    def delete_fact(self, subject: str, predicate: str = "is") -> bool:
        """Delete a fact."""
        key = f"{subject.lower().strip()}|{predicate.lower().strip()}"
        with self._lock:
            if key in self._facts:
                self._facts[key].status = 'deleted'
                self._save()
                return True
        return False

    def get_stats(self) -> Dict:
        active = [f for f in self._facts.values() if f.status == 'active']
        superseded = [f for f in self._facts.values() if f.status == 'superseded']
        return {
            'total_facts': len(active),
            'superseded': len(superseded),
            'sources': list(set(f.source for f in active)),
        }
