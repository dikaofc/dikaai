"""
DikaAI Benchmark - Evaluate DikaAI coding capability.

Usage:
    from dikaai.benchmark import BenchmarkRunner, Evaluator

    runner = BenchmarkRunner()
    results = runner.run(category='python', max_tasks=5)
    report = runner.report(results)
    evaluator = Evaluator()
    evaluator.print_report(report)
"""

from dikaai.benchmark.runner import BenchmarkRunner
from dikaai.benchmark.evaluator import Evaluator
from dikaai.benchmark.tasks import get_tasks, get_categories, ALL_TASKS
from dikaai.benchmark.needle_haystack import NeedleHaystackBenchmark

__all__ = [
    'BenchmarkRunner',
    'Evaluator',
    'get_tasks',
    'get_categories',
    'ALL_TASKS',
    'NeedleHaystackBenchmark',
]
