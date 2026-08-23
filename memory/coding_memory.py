"""DikaAI Coding Memory - Learns from past coding experiences.

Every error → fix → success is recorded. Over time DikaAI builds
a database of programming knowledge from its own experience.
"""

import json
import hashlib
import time
from pathlib import Path
from core.config import MEMORY, DATA_DIR


class CodingMemory:
    """Stores and retrieves coding experiences (error→solution pairs)."""

    def __init__(self, path: str = None):
        self.path = Path(path) if path else DATA_DIR / "codex" / "coding_memory.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.experiences = self._load()

    def _load(self) -> list:
        if self.path.exists():
            try:
                with open(self.path) as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save(self):
        # Keep only the most recent and most useful
        self.experiences.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        self.experiences = self.experiences[:MEMORY['coding_memory_limit']]
        with open(self.path, 'w') as f:
            json.dump(self.experiences, f, indent=2, ensure_ascii=False)

    def save_experience(self, task: str, success: bool, error: str = "",
                        fixes: list = None, context: dict = None):
        """Save a coding experience."""
        if not error and not fixes:
            return

        exp = {
            'task': task[:200],
            'success': success,
            'error': error[:500] if error else '',
            'fixes': (fixes or [])[:5],
            'language': (context or {}).get('language', ''),
            'action': (context or {}).get('action', ''),
            'timestamp': time.time(),
            'confidence': 1.0 if success else 0.3,
            'use_count': 0,
        }

        # Deduplicate by error signature
        sig = hashlib.md5(exp['error'][:100].encode()).hexdigest()[:12]
        exp['sig'] = sig

        # Update if exists
        for i, existing in enumerate(self.experiences):
            if existing.get('sig') == sig:
                self.experiences[i]['use_count'] += 1
                if success:
                    self.experiences[i]['confidence'] = min(1.0,
                        self.experiences[i]['confidence'] + 0.2)
                self._save()
                return

        self.experiences.append(exp)
        self._save()

    def find_solution(self, error: str) -> dict:
        """Find a solution for a given error."""
        if not error:
            return None

        # Exact match first
        for exp in self.experiences:
            if exp['error'] and exp['error'][:50] in error[:100]:
                exp['use_count'] += 1
                self._save()
                return exp

        # Fuzzy match - check error type
        error_type = error.split(':')[0].strip() if ':' in error else error[:30]
        for exp in self.experiences:
            if exp['error'] and error_type[:20] in exp['error'][:50]:
                exp['use_count'] += 1
                self._save()
                return exp

        return None

    def get_context(self, task: str, language: str = None) -> str:
        """Get relevant experiences as context."""
        relevant = []
        for exp in self.experiences:
            score = 0
            if language and exp.get('language') == language:
                score += 2
            if exp['success']:
                score += 1
            if exp.get('use_count', 0) > 0:
                score += 1
            if score > 0:
                relevant.append((score, exp))

        relevant.sort(key=lambda x: x[0], reverse=True)

        lines = ["Past experiences:"]
        for _, exp in relevant[:5]:
            status = "✅" if exp['success'] else "❌"
            lines.append(f"  {status} {exp['task'][:60]}")
            if exp.get('fixes'):
                lines.append(f"     Fix: {exp['fixes'][0][:60]}")

        return '\n'.join(lines) if len(lines) > 1 else ""

    def get_stats(self) -> dict:
        """Get memory statistics."""
        total = len(self.experiences)
        successful = sum(1 for e in self.experiences if e.get('success'))
        return {
            'total': total,
            'successful': successful,
            'success_rate': f'{successful/max(total,1)*100:.0f}%',
            'languages': list(set(e.get('language', '') for e in self.experiences if e.get('language'))),
        }

    def clear(self):
        self.experiences = []
        self._save()


class LongTermMemory:
    """Persistent memory across sessions."""

    def __init__(self):
        self.path = DATA_DIR / "codex" / "long_term.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data = self._load()

    def _load(self) -> dict:
        if self.path.exists():
            try:
                with open(self.path) as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save(self):
        with open(self.path, 'w') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def save(self, key: str, value):
        self.data[key] = value
        self._save()

    def get(self, key: str, default=None):
        return self.data.get(key, default)

    def get_all(self) -> dict:
        return self.data
