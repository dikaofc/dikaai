"""
DikaAI Benchmark Runner - Executes benchmark tasks and collects results.

Usage:
    from dikaai.benchmark.runner import BenchmarkRunner
    runner = BenchmarkRunner()
    results = runner.run(category='python', max_tasks=10)
    report = runner.report(results)
"""

import time
import traceback
from dataclasses import dataclass, field
from typing import Optional

from dikaai.benchmark.tasks import BenchmarkTask, get_tasks, get_categories


@dataclass
class TaskResult:
    """Result of a single task execution."""
    task_id: str
    category: str
    difficulty: str
    passed: bool
    response: str = ""
    error: str = ""
    time_taken: float = 0.0
    attempt: int = 1
    metrics: dict = field(default_factory=dict)


class BenchmarkRunner:
    """Runs benchmark tasks through DikaAI engine."""

    def __init__(self, engine=None, workspace: str = None):
        """
        Args:
            engine: DikaAI Engine instance (creates new if None)
            workspace: Working directory for code execution
        """
        self.workspace = workspace
        self._engine = engine

    @property
    def engine(self):
        if self._engine is None:
            from dikaai.engine import Engine
            self._engine = Engine(workspace=self.workspace)
        return self._engine

    def run(self, category: str = None, difficulty: str = None,
            max_tasks: int = None, max_retries: int = 1) -> list:
        """Run benchmark tasks.

        Args:
            category: Filter by category (python, debugging, algorithms, git, tool_use)
            difficulty: Filter by difficulty (easy, medium, hard)
            max_tasks: Maximum number of tasks to run
            max_retries: Number of retries per task

        Returns:
            List of TaskResult objects
        """
        tasks = get_tasks(category, difficulty)
        if max_tasks:
            tasks = tasks[:max_tasks]

        results = []
        total = len(tasks)

        print(f"\n{'='*60}")
        print(f"  DikaAI Benchmark - Running {total} tasks")
        if category:
            print(f"  Category: {category}")
        if difficulty:
            print(f"  Difficulty: {difficulty}")
        print(f"{'='*60}\n")

        for i, task in enumerate(tasks, 1):
            print(f"  [{i}/{total}] {task.id} ({task.category}/{task.difficulty})")

            # Run task with retries
            for attempt in range(1, max_retries + 1):
                result = self._run_task(task, attempt)
                results.append(result)

                if result.passed:
                    print(f"    ✅ PASSED (attempt {attempt}, {result.time_taken:.1f}s)")
                    break
                elif attempt < max_retries:
                    print(f"    🔄 RETRY {attempt}/{max_retries}")
                else:
                    print(f"    ❌ FAILED ({result.time_taken:.1f}s)")
                    if result.error:
                        print(f"       Error: {result.error[:100]}")

        print(f"\n{'='*60}")
        passed = sum(1 for r in results if r.passed)
        print(f"  Results: {passed}/{total} passed ({passed/max(total,1)*100:.0f}%)")
        print(f"{'='*60}\n")

        return results

    def _run_task(self, task: BenchmarkTask, attempt: int = 1) -> TaskResult:
        """Execute a single benchmark task."""
        start = time.time()

        try:
            # Send instruction to engine
            result = self.engine.process(task.instruction)
            response = result.get('response', '')

            # Evaluate
            eval_result = task.evaluate(response, self.engine)

            return TaskResult(
                task_id=task.id,
                category=task.category,
                difficulty=task.difficulty,
                passed=eval_result['passed'],
                response=response,
                time_taken=time.time() - start,
                attempt=attempt,
                metrics=eval_result.get('metrics', {}),
            )

        except Exception as e:
            return TaskResult(
                task_id=task.id,
                category=task.category,
                difficulty=task.difficulty,
                passed=False,
                error=str(e),
                time_taken=time.time() - start,
                attempt=attempt,
            )

    def report(self, results: list) -> dict:
        """Generate evaluation report from results."""
        from dikaai.benchmark.evaluator import Evaluator
        evaluator = Evaluator()
        return evaluator.evaluate(results)
