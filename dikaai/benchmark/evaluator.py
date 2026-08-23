"""
DikaAI Benchmark Evaluator - Computes metrics from benchmark results.

Metrics:
    pass_rate          - Percentage of tasks passed
    first_attempt_rate - Pass rate on first attempt only
    retry_success_rate - Pass rate after retries
    by_category        - Pass rate per category
    by_difficulty      - Pass rate per difficulty
    avg_time           - Average time per task
    syntax_error_rate  - Rate of syntax errors (code tasks)
    hallucination_rate - Rate of responses with no code (coding tasks)
"""

import time
from collections import defaultdict
from typing import List


class Evaluator:
    """Evaluates benchmark results and produces reports."""

    def evaluate(self, results: list) -> dict:
        """Compute all metrics from task results.

        Args:
            results: List of TaskResult objects

        Returns:
            dict with all metrics
        """
        if not results:
            return self._empty_report()

        total = len(results)
        passed = [r for r in results if r.passed]
        failed = [r for r in results if not r.passed]

        # Basic metrics
        pass_rate = len(passed) / total

        # First attempt (only count first occurrence of each task_id)
        seen = {}
        first_attempt_results = []
        for r in results:
            if r.task_id not in seen:
                seen[r.task_id] = r
                first_attempt_results.append(r)
        first_attempt_passed = sum(1 for r in first_attempt_results if r.passed)
        first_attempt_rate = first_attempt_passed / max(len(first_attempt_results), 1)

        # Retry success (tasks that failed first but passed on retry)
        task_attempts = defaultdict(list)
        for r in results:
            task_attempts[r.task_id].append(r)
        retry_candidates = sum(1 for tid, attempts in task_attempts.items()
                               if len(attempts) > 1 and any(a.passed for a in attempts))
        retry_success_rate = retry_candidates / max(sum(1 for tid, a in task_attempts.items() if len(a) > 1), 1)

        # By category
        by_category = defaultdict(lambda: {'total': 0, 'passed': 0})
        for r in results:
            by_category[r.category]['total'] += 1
            if r.passed:
                by_category[r.category]['passed'] += 1
        category_rates = {}
        for cat, data in by_category.items():
            category_rates[cat] = {
                'total': data['total'],
                'passed': data['passed'],
                'rate': data['passed'] / max(data['total'], 1),
            }

        # By difficulty
        by_difficulty = defaultdict(lambda: {'total': 0, 'passed': 0})
        for r in results:
            by_difficulty[r.difficulty]['total'] += 1
            if r.passed:
                by_difficulty[r.difficulty]['passed'] += 1
        difficulty_rates = {}
        for diff, data in by_difficulty.items():
            difficulty_rates[diff] = {
                'total': data['total'],
                'passed': data['passed'],
                'rate': data['passed'] / max(data['total'], 1),
            }

        # Time metrics
        times = [r.time_taken for r in results]
        avg_time = sum(times) / max(len(times), 1)
        total_time = sum(times)

        # Syntax error rate (code tasks only)
        code_tasks = [r for r in results if r.category in ('python', 'debugging', 'algorithms')]
        syntax_errors = sum(1 for r in code_tasks
                           if r.metrics.get('syntax_valid') == False)
        syntax_error_rate = syntax_errors / max(len(code_tasks), 1)

        # Hallucination rate (coding tasks with no code in response)
        hallucinations = sum(1 for r in code_tasks
                            if r.metrics.get('has_code') == False and not r.passed)
        hallucination_rate = hallucinations / max(len(code_tasks), 1)

        return {
            'summary': {
                'total_tasks': total,
                'passed': len(passed),
                'failed': len(failed),
                'pass_rate': pass_rate,
                'pass_rate_pct': f'{pass_rate * 100:.1f}%',
            },
            'first_attempt': {
                'total': len(first_attempt_results),
                'passed': first_attempt_passed,
                'rate': first_attempt_rate,
                'rate_pct': f'{first_attempt_rate * 100:.1f}%',
            },
            'retry': {
                'candidates': sum(1 for tid, a in task_attempts.items() if len(a) > 1),
                'succeeded': retry_candidates,
                'rate': retry_success_rate,
                'rate_pct': f'{retry_success_rate * 100:.1f}%',
            },
            'by_category': category_rates,
            'by_difficulty': difficulty_rates,
            'timing': {
                'avg_time': f'{avg_time:.1f}s',
                'total_time': f'{total_time:.1f}s',
                'fastest': f'{min(times):.1f}s' if times else '0s',
                'slowest': f'{max(times):.1f}s' if times else '0s',
            },
            'quality': {
                'syntax_error_rate': f'{syntax_error_rate * 100:.1f}%',
                'hallucination_rate': f'{hallucination_rate * 100:.1f}%',
            },
            'score': self._compute_score(pass_rate, first_attempt_rate,
                                          syntax_error_rate, hallucination_rate),
        }

    def _compute_score(self, pass_rate, first_attempt_rate,
                       syntax_error_rate, hallucination_rate) -> dict:
        """Compute overall benchmark score (0-100)."""
        # Weighted score
        score = (
            pass_rate * 50 +           # 50% weight: pass rate
            first_attempt_rate * 30 +   # 30% weight: first attempt
            (1 - syntax_error_rate) * 10 +  # 10% weight: syntax
            (1 - hallucination_rate) * 10   # 10% weight: no hallucination
        ) * 100

        # Grade
        if score >= 90:
            grade = 'A'
        elif score >= 80:
            grade = 'B'
        elif score >= 70:
            grade = 'C'
        elif score >= 60:
            grade = 'D'
        else:
            grade = 'F'

        return {
            'score': round(score, 1),
            'grade': grade,
            'description': self._grade_description(grade),
        }

    def _grade_description(self, grade: str) -> str:
        descriptions = {
            'A': 'Excellent - DikaAI is production-ready',
            'B': 'Good - DikaAI handles most coding tasks well',
            'C': 'Average - DikaAI needs improvement on some tasks',
            'D': 'Below average - DikaAI struggles with many tasks',
            'F': 'Failing - DikaAI needs significant improvement',
        }
        return descriptions.get(grade, 'Unknown')

    def _empty_report(self) -> dict:
        return {
            'summary': {'total_tasks': 0, 'passed': 0, 'failed': 0, 'pass_rate': 0, 'pass_rate_pct': '0.0%'},
            'first_attempt': {'total': 0, 'passed': 0, 'rate': 0, 'rate_pct': '0.0%'},
            'retry': {'candidates': 0, 'succeeded': 0, 'rate': 0, 'rate_pct': '0.0%'},
            'by_category': {},
            'by_difficulty': {},
            'timing': {'avg_time': '0s', 'total_time': '0s', 'fastest': '0s', 'slowest': '0s'},
            'quality': {'syntax_error_rate': '0.0%', 'hallucination_rate': '0.0%'},
            'score': {'score': 0, 'grade': 'F', 'description': 'No tasks run'},
        }

    def print_report(self, report: dict):
        """Pretty-print the benchmark report."""
        s = report['summary']
        fa = report['first_attempt']
        retry = report['retry']
        timing = report['timing']
        quality = report['quality']
        score = report['score']

        print(f"\n{'='*60}")
        print(f"  DikaAI Benchmark Report")
        print(f"{'='*60}")

        print(f"\n  📊 Summary")
        print(f"  {'─'*40}")
        print(f"  Total tasks  : {s['total_tasks']}")
        print(f"  Passed       : {s['passed']}")
        print(f"  Failed       : {s['failed']}")
        print(f"  Pass rate    : {s['pass_rate_pct']}")

        print(f"\n  🎯 First Attempt")
        print(f"  {'─'*40}")
        print(f"  Tasks        : {fa['total']}")
        print(f"  Passed       : {fa['passed']}")
        print(f"  Rate         : {fa['rate_pct']}")

        print(f"\n  🔄 Retry Success")
        print(f"  {'─'*40}")
        print(f"  Candidates   : {retry['candidates']}")
        print(f"  Succeeded    : {retry['succeeded']}")
        print(f"  Rate         : {retry['rate_pct']}")

        print(f"\n  📁 By Category")
        print(f"  {'─'*40}")
        for cat, data in report['by_category'].items():
            bar = '█' * int(data['rate'] * 20) + '░' * (20 - int(data['rate'] * 20))
            print(f"  {cat:15s} {bar} {data['passed']}/{data['total']} ({data['rate']*100:.0f}%)")

        print(f"\n  📈 By Difficulty")
        print(f"  {'─'*40}")
        for diff, data in report['by_difficulty'].items():
            bar = '█' * int(data['rate'] * 20) + '░' * (20 - int(data['rate'] * 20))
            print(f"  {diff:15s} {bar} {data['passed']}/{data['total']} ({data['rate']*100:.0f}%)")

        print(f"\n  ⏱️  Timing")
        print(f"  {'─'*40}")
        print(f"  Average      : {timing['avg_time']}")
        print(f"  Total        : {timing['total_time']}")
        print(f"  Fastest      : {timing['fastest']}")
        print(f"  Slowest      : {timing['slowest']}")

        print(f"\n  🔍 Quality")
        print(f"  {'─'*40}")
        print(f"  Syntax errors    : {quality['syntax_error_rate']}")
        print(f"  Hallucinations   : {quality['hallucination_rate']}")

        print(f"\n  🏆 Score")
        print(f"  {'─'*40}")
        grade_colors = {'A': '92', 'B': '93', 'C': '94', 'D': '95', 'F': '91'}
        color = grade_colors.get(score['grade'], '0')
        print(f"  \033[{color}m  {score['score']}/100  Grade: {score['grade']}\033[0m")
        print(f"  {score['description']}")

        print(f"\n{'='*60}")
