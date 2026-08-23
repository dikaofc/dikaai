"""
DikaAI Benchmark History - Track scores over time.

Saves each benchmark run with:
    - timestamp
    - version
    - scores per category
    - overall score/grade
    - model step at time of test
    - context size tested

Enables:
    - Score progression charts
    - Regression detection
    - Version comparison
"""

import json
import time
from pathlib import Path
from dataclasses import dataclass, field, asdict


@dataclass
class BenchmarkRun:
    """A single benchmark run record."""
    timestamp: float = 0.0
    version: str = "3.0.0"
    model_step: int = 0
    overall_score: float = 0.0
    grade: str = "F"
    pass_rate: float = 0.0
    total_tasks: int = 0
    passed_tasks: int = 0
    category_scores: dict = field(default_factory=dict)
    difficulty_scores: dict = field(default_factory=dict)
    quality_metrics: dict = field(default_factory=dict)
    timing: dict = field(default_factory=dict)
    notes: str = ""

    def to_dict(self):
        return {
            'timestamp': self.timestamp,
            'datetime': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.timestamp)),
            'version': self.version,
            'model_step': self.model_step,
            'overall_score': self.overall_score,
            'grade': self.grade,
            'pass_rate': self.pass_rate,
            'total_tasks': self.total_tasks,
            'passed_tasks': self.passed_tasks,
            'category_scores': self.category_scores,
            'difficulty_scores': self.difficulty_scores,
            'quality_metrics': self.quality_metrics,
            'timing': self.timing,
            'notes': self.notes,
        }


class BenchmarkHistory:
    """Tracks benchmark scores over time."""

    def __init__(self, data_dir: str = None):
        self.data_dir = Path(data_dir or 'data/benchmarks')
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = self.data_dir / 'benchmark_history.json'
        self.runs = self._load()

    def record(self, report: dict, model_step: int = 0,
               version: str = "3.0.0", notes: str = "") -> BenchmarkRun:
        """Record a benchmark run from a report.

        Args:
            report: Report dict from Evaluator.evaluate()
            model_step: Current model training step
            version: DikaAI version
            notes: Optional notes about this run

        Returns:
            BenchmarkRun that was saved
        """
        score_data = report.get('score', {})
        summary = report.get('summary', {})

        run = BenchmarkRun(
            timestamp=time.time(),
            version=version,
            model_step=model_step,
            overall_score=score_data.get('score', 0),
            grade=score_data.get('grade', 'F'),
            pass_rate=summary.get('pass_rate', 0),
            total_tasks=summary.get('total_tasks', 0),
            passed_tasks=summary.get('passed', 0),
            category_scores=report.get('by_category', {}),
            difficulty_scores=report.get('by_difficulty', {}),
            quality_metrics=report.get('quality', {}),
            timing=report.get('timing', {}),
            notes=notes,
        )

        self.runs.append(run)
        self._save()
        return run

    def get_latest(self) -> BenchmarkRun:
        """Get the most recent benchmark run."""
        return self.runs[-1] if self.runs else None

    def get_best(self) -> BenchmarkRun:
        """Get the best benchmark run by score."""
        if not self.runs:
            return None
        return max(self.runs, key=lambda r: r.overall_score)

    def get_progression(self, last_n: int = None) -> list:
        """Get score progression over time."""
        runs = self.runs[-last_n:] if last_n else self.runs
        return [
            {
                'timestamp': r.timestamp,
                'datetime': time.strftime('%Y-%m-%d %H:%M', time.localtime(r.timestamp)),
                'score': r.overall_score,
                'grade': r.grade,
                'pass_rate': r.pass_rate,
                'model_step': r.model_step,
                'version': r.version,
            }
            for r in runs
        ]

    def get_category_trend(self, category: str) -> list:
        """Get trend for a specific category."""
        return [
            {
                'timestamp': r.timestamp,
                'score': r.category_scores.get(category, {}).get('rate', 0),
                'passed': r.category_scores.get(category, {}).get('passed', 0),
                'total': r.category_scores.get(category, {}).get('total', 0),
            }
            for r in self.runs
            if category in r.category_scores
        ]

    def detect_regression(self, threshold: float = 0.1) -> dict:
        """Check if latest run regressed from previous.

        Args:
            threshold: Minimum drop to consider regression

        Returns:
            dict with regressed, current_score, previous_score, drop
        """
        if len(self.runs) < 2:
            return {'regressed': False}

        current = self.runs[-1]
        previous = self.runs[-2]
        drop = previous.overall_score - current.overall_score

        return {
            'regressed': drop > threshold * 100,
            'current_score': current.overall_score,
            'previous_score': previous.overall_score,
            'drop': drop,
            'current_grade': current.grade,
            'previous_grade': previous.grade,
        }

    def get_summary(self) -> dict:
        """Get overall history summary."""
        if not self.runs:
            return {'total_runs': 0}

        scores = [r.overall_score for r in self.runs]
        return {
            'total_runs': len(self.runs),
            'first_run': time.strftime('%Y-%m-%d', time.localtime(self.runs[0].timestamp)),
            'last_run': time.strftime('%Y-%m-%d', time.localtime(self.runs[-1].timestamp)),
            'best_score': max(scores),
            'worst_score': min(scores),
            'avg_score': sum(scores) / len(scores),
            'latest_score': scores[-1],
            'latest_grade': self.runs[-1].grade,
            'improvement': scores[-1] - scores[0] if len(scores) > 1 else 0,
        }

    def print_history(self):
        """Pretty-print benchmark history."""
        print(f"\n{'='*60}")
        print(f"  DikaAI Benchmark History")
        print(f"{'='*60}")

        if not self.runs:
            print("  No benchmark runs recorded yet.")
            print(f"{'='*60}")
            return

        summary = self.get_summary()
        print(f"\n  📊 Summary")
        print(f"  {'─'*40}")
        print(f"  Total runs   : {summary['total_runs']}")
        print(f"  First run    : {summary['first_run']}")
        print(f"  Last run     : {summary['last_run']}")
        print(f"  Best score   : {summary['best_score']:.0f}")
        print(f"  Avg score    : {summary['avg_score']:.0f}")
        print(f"  Latest       : {summary['latest_score']:.0f} ({summary['latest_grade']})")
        print(f"  Improvement  : {summary['improvement']:+.0f}")

        # Score chart (ASCII)
        print(f"\n  📈 Score Progression")
        print(f"  {'─'*40}")
        max_score = max(r.overall_score for r in self.runs) or 100
        for r in self.runs[-10:]:  # Last 10 runs
            dt = time.strftime('%m/%d %H:%M', time.localtime(r.timestamp))
            bar_len = int(r.overall_score / max_score * 30)
            bar = '█' * bar_len + '░' * (30 - bar_len)
            grade_color = {'A': '92', 'B': '93', 'C': '94', 'D': '95', 'F': '91'}
            color = grade_color.get(r.grade, '0')
            print(f"  {dt} {bar} \033[{color}m{r.overall_score:5.0f} ({r.grade})\033[0m")

        # Regression check
        regression = self.detect_regression()
        if regression['regressed']:
            print(f"\n  ⚠️  REGRESSION DETECTED!")
            print(f"  Previous: {regression['previous_score']:.0f} ({regression['previous_grade']})")
            print(f"  Current:  {regression['current_score']:.0f} ({regression['current_grade']})")
            print(f"  Drop:     {regression['drop']:.0f} points")

        print(f"\n{'='*60}")

    def _save(self):
        data = [r.to_dict() for r in self.runs]
        with open(self.history_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _load(self) -> list:
        if not self.history_file.exists():
            return []
        try:
            with open(self.history_file) as f:
                data = json.load(f)
            return [BenchmarkRun(**d) for d in data]
        except Exception:
            return []
