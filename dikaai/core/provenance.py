"""DikaAI Provenance & Trust System

Tracks the source and trust level of every piece of information:
  - TRUSTED: system, developer, tool output, verified state
  - SEMI-TRUSTED: project docs, database, known sources
  - UNTRUSTED: web pages, logs, uploaded docs, external text

Prevents the model from treating guesses as facts.
"""
import time
from typing import Dict, Optional
from enum import Enum


class TrustLevel(str, Enum):
    TRUSTED = "trusted"
    SEMI_TRUSTED = "semi_trusted"
    UNTRUSTED = "untrusted"


# Default trust levels for different sources
SOURCE_TRUST = {
    # TRUSTED - ground truth
    'tool_output': TrustLevel.TRUSTED,
    'terminal': TrustLevel.TRUSTED,
    'git': TrustLevel.TRUSTED,
    'compiler': TrustLevel.TRUSTED,
    'test_result': TrustLevel.TRUSTED,
    'developer': TrustLevel.TRUSTED,
    'config_file': TrustLevel.TRUSTED,

    # SEMI-TRUSTED - likely correct but not verified
    'project_doc': TrustLevel.SEMI_TRUSTED,
    'readme': TrustLevel.SEMI_TRUSTED,
    'database': TrustLevel.SEMI_TRUSTED,
    'user_input': TrustLevel.SEMI_TRUSTED,
    'memory': TrustLevel.SEMI_TRUSTED,
    'rag': TrustLevel.SEMI_TRUSTED,

    # UNTRUSTED - might be wrong
    'web_page': TrustLevel.UNTRUSTED,
    'log': TrustLevel.UNTRUSTED,
    'uploaded_doc': TrustLevel.UNTRUSTED,
    'external_api': TrustLevel.UNTRUSTED,
    'model_inference': TrustLevel.UNTRUSTED,
    'unknown': TrustLevel.UNTRUSTED,
}


class ProvenanceEntry:
    """Tracks the source and trust of a piece of information."""
    def __init__(self, content: str, source: str, trust_level: TrustLevel = None,
                 confidence: float = 1.0, evidence: str = "",
                 metadata: Dict = None):
        self.content = content
        self.source = source
        self.trust_level = trust_level or SOURCE_TRUST.get(source, TrustLevel.UNTRUSTED)
        self.confidence = confidence
        self.evidence = evidence      # What supports this claim
        self.metadata = metadata or {}
        self.timestamp = time.time()

    def is_trusted(self) -> bool:
        return self.trust_level == TrustLevel.TRUSTED

    def is_actionable(self) -> bool:
        """Can we act on this information?"""
        return self.trust_level in (TrustLevel.TRUSTED, TrustLevel.SEMI_TRUSTED)

    def to_dict(self) -> Dict:
        return {
            'content': self.content[:200],
            'source': self.source,
            'trust_level': self.trust_level.value,
            'confidence': self.confidence,
            'evidence': self.evidence[:200],
            'timestamp': self.timestamp,
            'metadata': self.metadata,
        }


class ProvenanceSystem:
    """Tracks source and trust for all information."""

    def __init__(self):
        self._entries: list = []
        self._claims: Dict[str, list] = {}  # claim -> [ProvenanceEntry]

    def track(self, content: str, source: str, confidence: float = 1.0,
              evidence: str = "", **metadata) -> ProvenanceEntry:
        """Track the provenance of a piece of information."""
        entry = ProvenanceEntry(
            content=content,
            source=source,
            confidence=confidence,
            evidence=evidence,
            metadata=metadata,
        )
        self._entries.append(entry)

        # Index by normalized content
        key = content.lower().strip()[:100]
        if key not in self._claims:
            self._claims[key] = []
        self._claims[key].append(entry)

        return entry

    def check_claim(self, claim: str) -> Dict:
        """Check if a claim has evidence."""
        key = claim.lower().strip()[:100]
        entries = self._claims.get(key, [])

        if not entries:
            return {
                'claim': claim,
                'status': 'unsupported',
                'trust_level': TrustLevel.UNTRUSTED.value,
                'evidence': [],
                'recommendation': 'This claim has no supporting evidence. Verify before acting.',
            }

        best = max(entries, key=lambda e: e.confidence)
        return {
            'claim': claim,
            'status': 'supported' if best.is_actionable() else 'uncertain',
            'trust_level': best.trust_level.value,
            'source': best.source,
            'confidence': best.confidence,
            'evidence': best.evidence,
            'recommendation': self._get_recommendation(best),
        }

    def _get_recommendation(self, entry: ProvenanceEntry) -> str:
        if entry.trust_level == TrustLevel.TRUSTED:
            return "Verified from trusted source. Safe to use."
        elif entry.trust_level == TrustLevel.SEMI_TRUSTED:
            return "From semi-trusted source. Consider verifying."
        else:
            return "From untrusted source. Do NOT treat as fact without verification."

    def filter_by_trust(self, items: list, min_trust: TrustLevel = TrustLevel.SEMI_TRUSTED) -> list:
        """Filter items by minimum trust level."""
        trust_order = {
            TrustLevel.UNTRUSTED: 0,
            TrustLevel.SEMI_TRUSTED: 1,
            TrustLevel.TRUSTED: 2,
        }
        min_val = trust_order.get(min_trust, 0)
        return [item for item in items
                if trust_order.get(item.trust_level, 0) >= min_val]

    def get_untrusted(self) -> list:
        """Get all untrusted entries."""
        return [e for e in self._entries if e.trust_level == TrustLevel.UNTRUSTED]

    def get_stats(self) -> Dict:
        trusted = sum(1 for e in self._entries if e.trust_level == TrustLevel.TRUSTED)
        semi = sum(1 for e in self._entries if e.trust_level == TrustLevel.SEMI_TRUSTED)
        untrusted = sum(1 for e in self._entries if e.trust_level == TrustLevel.UNTRUSTED)
        return {
            'total_entries': len(self._entries),
            'trusted': trusted,
            'semi_trusted': semi,
            'untrusted': untrusted,
            'unique_claims': len(self._claims),
        }
