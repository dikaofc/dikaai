"""DikaAI Coding Memory - Learns from past coding experiences."""

import json
import hashlib
import time
from pathlib import Path


class CodingMemory:
    def __init__(self, path: str = None):
        self.path = Path(path or 'data/memory/coding_memory.json')
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.experiences = self._load()

    def _load(self):
        if self.path.exists():
            try:
                with open(self.path) as f: return json.load(f)
            except: return []
        return []

    def _save(self):
        self.experiences.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        self.experiences = self.experiences[:500]
        with open(self.path, 'w') as f: json.dump(self.experiences, f, indent=2, ensure_ascii=False)

    def save_experience(self, task: str, success: bool, error: str = "", fixes: list = None, context: dict = None):
        if not error and not fixes: return
        sig = hashlib.md5(error[:100].encode()).hexdigest()[:12]
        for exp in self.experiences:
            if exp.get('sig') == sig:
                exp['use_count'] = exp.get('use_count', 0) + 1
                if success: exp['confidence'] = min(1.0, exp['confidence'] + 0.2)
                self._save()
                return
        self.experiences.append({
            'task': task[:200], 'success': success, 'error': error[:500],
            'fixes': (fixes or [])[:5], 'sig': sig, 'confidence': 1.0 if success else 0.3,
            'use_count': 0, 'timestamp': time.time(),
        })
        self._save()

    def find_solution(self, error: str):
        for exp in self.experiences:
            if exp['error'] and exp['error'][:50] in error[:100]:
                exp['use_count'] += 1; self._save()
                return exp
        return None

    def get_context(self, task: str, language: str = None) -> str:
        relevant = []
        for exp in self.experiences:
            score = (2 if language and exp.get('language') == language else 0) + (1 if exp['success'] else 0)
            if score > 0: relevant.append((score, exp))
        relevant.sort(key=lambda x: x[0], reverse=True)
        if not relevant: return ""
        lines = ["Past experiences:"]
        for _, exp in relevant[:3]:
            status = "✅" if exp['success'] else "❌"
            lines.append(f"  {status} {exp['task'][:60]}")
        return '\n'.join(lines)

    def get_stats(self):
        total = len(self.experiences)
        successful = sum(1 for e in self.experiences if e.get('success'))
        return {'total': total, 'successful': successful, 'rate': f'{successful/max(total,1)*100:.0f}%'}
