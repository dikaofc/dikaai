"""
DikaAI Episodic Memory - Learns from past coding experiences.

Stores: task → plan → code → test → error → fix → result
Enables: pattern recognition, error prevention, solution reuse
"""

import json
import time
import hashlib
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Episode:
    """A single coding experience."""
    task: str
    plan: list = field(default_factory=list)
    code: str = ""
    test_result: str = ""
    error: str = ""
    fix: str = ""
    success: bool = False
    language: str = ""
    tools_used: list = field(default_factory=list)
    timestamp: float = 0.0
    duration: float = 0.0
    confidence: float = 0.5
    use_count: int = 0
    tags: list = field(default_factory=list)

    def to_dict(self):
        return {
            'task': self.task[:200],
            'plan': self.plan[:10],
            'code': self.code[:500],
            'error': self.error[:300],
            'fix': self.fix[:300],
            'success': self.success,
            'language': self.language,
            'tools_used': self.tools_used[:5],
            'confidence': self.confidence,
            'use_count': self.use_count,
            'tags': self.tags[:10],
        }


class EpisodicMemory:
    """Experience-based memory for coding tasks."""

    def __init__(self, data_dir: str = None):
        self.data_dir = Path(data_dir or 'data/memory')
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.episodes = []
        self._load()

    def record_episode(self, task: str, plan: list = None, code: str = "",
                       error: str = "", fix: str = "", success: bool = False,
                       language: str = "", tools_used: list = None,
                       duration: float = 0.0, tags: list = None) -> Episode:
        """Record a coding experience."""
        episode = Episode(
            task=task,
            plan=plan or [],
            code=code[:500],
            error=error[:300],
            fix=fix[:300],
            success=success,
            language=language,
            tools_used=tools_used or [],
            timestamp=time.time(),
            duration=duration,
            confidence=1.0 if success else 0.3,
            tags=tags or [],
        )
        self.episodes.append(episode)

        # Keep under limit
        if len(self.episodes) > 2000:
            # Remove low-confidence, old episodes
            self.episodes.sort(key=lambda e: (e.confidence, e.timestamp), reverse=True)
            self.episodes = self.episodes[:1500]

        self._save()
        return episode

    def find_similar(self, task: str, language: str = None,
                     top_k: int = 5) -> list:
        """Find similar past experiences."""
        task_words = set(task.lower().split())
        results = []

        for ep in self.episodes:
            ep_words = set(ep.task.lower().split())
            overlap = len(task_words & ep_words)
            lang_match = 1 if language and ep.language == language else 0
            success_bonus = 1 if ep.success else 0
            score = overlap + lang_match * 2 + success_bonus + ep.confidence

            if score > 0:
                results.append((score, ep))

        results.sort(key=lambda x: x[0], reverse=True)
        return [ep for _, ep in results[:top_k]]

    def find_error_solution(self, error: str) -> Optional[Episode]:
        """Find past episode that solved a similar error."""
        error_lower = error.lower()[:100]

        for ep in self.episodes:
            if ep.success and ep.error:
                ep_error = ep.error.lower()[:100]
                # Check if errors are similar
                if self._errors_similar(error_lower, ep_error):
                    ep.use_count += 1
                    ep.confidence = min(1.0, ep.confidence + 0.1)
                    self._save()
                    return ep
        return None

    def _errors_similar(self, e1: str, e2: str) -> bool:
        """Check if two errors are similar."""
        # Exact match
        if e1 == e2:
            return True
        # Check error type
        error_types = ['syntaxerror', 'typeerror', 'valueerror', 'nameerror',
                       'importerror', 'modulenotfounderror', 'indexerror',
                       'keyerror', 'attributeerror', 'runtimeerror']
        for et in error_types:
            if et in e1 and et in e2:
                return True
        # Word overlap
        w1 = set(e1.split())
        w2 = set(e2.split())
        overlap = len(w1 & w2)
        return overlap >= 3

    def get_task_stats(self) -> dict:
        """Get statistics about past experiences."""
        total = len(self.episodes)
        successful = sum(1 for e in self.episodes if e.success)
        languages = {}
        for ep in self.episodes:
            lang = ep.language or 'unknown'
            languages[lang] = languages.get(lang, 0) + 1

        return {
            'total_episodes': total,
            'successful': successful,
            'success_rate': f'{successful/max(total,1)*100:.0f}%',
            'languages': languages,
            'avg_confidence': sum(e.confidence for e in self.episodes) / max(total, 1),
        }

    def get_context(self, task: str, language: str = None) -> str:
        """Get relevant experience context for a task."""
        similar = self.find_similar(task, language, top_k=3)
        if not similar:
            return ""

        lines = ["PAST EXPERIENCES:"]
        for ep in similar:
            status = "✅" if ep.success else "❌"
            lines.append(f"  {status} {ep.task[:80]}")
            if ep.fix:
                lines.append(f"     Fix: {ep.fix[:100]}")

        return '\n'.join(lines)

    def _save(self):
        data = [ep.to_dict() for ep in self.episodes[-500:]]
        path = self.data_dir / 'episodic_memory.json'
        with open(path, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _load(self):
        path = self.data_dir / 'episodic_memory.json'
        if not path.exists():
            return
        try:
            with open(path) as f:
                data = json.load(f)
            for d in data:
                self.episodes.append(Episode(**d))
        except Exception:
            pass
