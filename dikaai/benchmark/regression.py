"""DikaAI Regression Benchmark

Compares benchmark scores across versions to detect regressions.
Every code change should be checked against the baseline.
"""
import time
import json
from typing import List, Dict, Optional
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class BenchmarkResult:
    """A single benchmark run result."""
    version: str
    timestamp: float
    scores: Dict[str, float]      # category -> score (0-100)
    overall_score: float
    grade: str
    total_tasks: int
    passed_tasks: int
    details: Dict = field(default_factory=dict)
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            'version': self.version,
            'timestamp': self.timestamp,
            'scores': self.scores,
            'overall_score': self.overall_score,
            'grade': self.grade,
            'total_tasks': self.total_tasks,
            'passed_tasks': self.passed_tasks,
            'details': self.details,
            'metadata': self.metadata,
        }


class RegressionBenchmark:
    """Tracks and compares benchmark scores across versions."""

    def __init__(self, data_dir: str = None):
        self._results: List[BenchmarkResult] = []
        self._data_dir = Path(data_dir) if data_dir else Path("data/benchmarks")
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._load()

    def _load(self):
        path = self._data_dir / "benchmark_history.json"
        if path.exists():
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                for d in data:
                    result = BenchmarkResult(
                        version=d.get('version', 'unknown'),
                        timestamp=d.get('timestamp', 0),
                        scores=d.get('scores', {}),
                        overall_score=d.get('overall_score', 0),
                        grade=d.get('grade', 'F'),
                        total_tasks=d.get('total_tasks', 0),
                        passed_tasks=d.get('passed_tasks', 0),
                        details=d.get('details', {}),
                        metadata=d.get('metadata', {}),
                    )
                    self._results.append(result)
            except Exception:
                pass

    def _save(self):
        path = self._data_dir / "benchmark_history.json"
        try:
            data = [r.to_dict() for r in self._results[-50:]]
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def record(self, version: str, scores: Dict[str, float], overall_score: float,
               total_tasks: int, passed_tasks: int, details: Dict = None,
               **metadata) -> BenchmarkResult:
        """Record a benchmark result."""
        grade = self._score_to_grade(overall_score)
        result = BenchmarkResult(
            version=version,
            timestamp=time.time(),
            scores=scores,
            overall_score=overall_score,
            grade=grade,
            total_tasks=total_tasks,
            passed_tasks=passed_tasks,
            details=details or {},
            metadata=metadata,
        )
        self._results.append(result)
        self._save()
        return result

    def compare(self, v1: str = None, v2: str = None) -> Dict:
        """Compare two versions (latest two if not specified)."""
        if len(self._results) < 2:
            return {'error': 'Need at least 2 benchmark results to compare'}

        if v1 and v2:
            r1 = next((r for r in self._results if r.version == v1), None)
            r2 = next((r for r in self._results if r.version == v2), None)
        else:
            r1 = self._results[-2]
            r2 = self._results[-1]

        if not r1 or not r2:
            return {'error': 'Version not found'}

        # Compare category scores
        categories = set(list(r1.scores.keys()) + list(r2.scores.keys()))
        changes = {}
        regressions = []
        improvements = []

        for cat in categories:
            old_score = r1.scores.get(cat, 0)
            new_score = r2.scores.get(cat, 0)
            diff = new_score - old_score
            changes[cat] = {
                'old': old_score,
                'new': new_score,
                'diff': round(diff, 1),
                'status': '✅ improved' if diff > 0 else ('❌ regressed' if diff < 0 else '➡️ unchanged'),
            }
            if diff < -2:
                regressions.append(cat)
            elif diff > 2:
                improvements.append(cat)

        overall_diff = r2.overall_score - r1.overall_score

        return {
            'v1': {'version': r1.version, 'score': r1.overall_score, 'grade': r1.grade},
            'v2': {'version': r2.version, 'score': r2.overall_score, 'grade': r2.grade},
            'overall_diff': round(overall_diff, 1),
            'overall_status': '✅ improved' if overall_diff > 0 else ('❌ regressed' if overall_diff < 0 else '➡️ unchanged'),
            'categories': changes,
            'regressions': regressions,
            'improvements': improvements,
            'safe_to_deploy': len(regressions) == 0,
        }

    def check_regression(self, threshold: float = -2.0) -> Dict:
        """Check if latest result has any regressions vs previous."""
        if len(self._results) < 2:
            return {'regression': False, 'message': 'Not enough data'}

        comparison = self.compare()
        regressions = comparison.get('regressions', [])

        return {
            'regression': len(regressions) > 0,
            'regressed_categories': regressions,
            'safe_to_deploy': comparison.get('safe_to_deploy', True),
            'message': f"Regressions in: {', '.join(regressions)}" if regressions else "No regressions detected",
        }

    def get_history(self, limit: int = 20) -> List[Dict]:
        """Get benchmark history."""
        return [r.to_dict() for r in self._results[-limit:]]

    def get_best(self) -> Optional[BenchmarkResult]:
        """Get the best result."""
        if not self._results:
            return None
        return max(self._results, key=lambda r: r.overall_score)

    def get_latest(self) -> Optional[BenchmarkResult]:
        """Get the latest result."""
        return self._results[-1] if self._results else None

    def get_score_trend(self) -> List[Dict]:
        """Get score trend over time."""
        return [{
            'version': r.version,
            'score': r.overall_score,
            'grade': r.grade,
            'timestamp': r.timestamp,
        } for r in self._results]

    def _score_to_grade(self, score: float) -> str:
        if score >= 95: return 'A+'
        if score >= 90: return 'A'
        if score >= 80: return 'B'
        if score >= 70: return 'C'
        if score >= 60: return 'D'
        return 'F'

    def get_stats(self) -> Dict:
        if not self._results:
            return {'total_runs': 0}
        scores = [r.overall_score for r in self._results]
        return {
            'total_runs': len(self._results),
            'best_score': max(scores),
            'worst_score': min(scores),
            'avg_score': round(sum(scores) / len(scores), 1),
            'latest_score': scores[-1],
            'versions': [r.version for r in self._results],
        }
