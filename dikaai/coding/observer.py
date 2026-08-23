"""DikaAI Observer - Tracks execution output, errors, performance.

Logs: tool calls, errors, retries, latency, tokens.
"""

import time
from collections import defaultdict


class Observation:
    """Single observation entry."""
    def __init__(self, event_type: str, data: dict = None):
        self.type = event_type
        self.data = data or {}
        self.timestamp = time.time()

    def to_dict(self):
        return {
            'type': self.type,
            'data': self.data,
            'time': self.timestamp,
        }


class Observer:
    """Observes and logs all DikaAI activity."""

    def __init__(self):
        self.observations = []
        self.tool_calls = defaultdict(int)
        self.errors = defaultdict(int)
        self.latencies = []
        self.total_tokens = 0
        self.start_time = time.time()

    def log_tool_call(self, tool: str, success: bool, latency: float = 0):
        """Log a tool call."""
        self.tool_calls[tool] += 1
        self.latencies.append(latency)
        self.observations.append(Observation('tool_call', {
            'tool': tool, 'success': success, 'latency': latency
        }))

    def log_error(self, error_type: str, message: str):
        """Log an error."""
        self.errors[error_type] += 1
        self.observations.append(Observation('error', {
            'type': error_type, 'message': message[:200]
        }))

    def log_retry(self, attempt: int, reason: str):
        """Log a retry attempt."""
        self.observations.append(Observation('retry', {
            'attempt': attempt, 'reason': reason[:100]
        }))

    def log_generation(self, tokens: int, latency: float):
        """Log model generation."""
        self.total_tokens += tokens
        self.latencies.append(latency)
        self.observations.append(Observation('generation', {
            'tokens': tokens, 'latency': latency
        }))

    def log_validation(self, passed: bool, issues: list):
        """Log validation result."""
        self.observations.append(Observation('validation', {
            'passed': passed, 'issues': issues[:5]
        }))

    def get_stats(self) -> dict:
        """Get observation statistics."""
        uptime = time.time() - self.start_time
        avg_latency = sum(self.latencies) / max(len(self.latencies), 1)

        return {
            'uptime': f'{uptime/3600:.1f}h',
            'total_observations': len(self.observations),
            'tool_calls': dict(self.tool_calls),
            'errors': dict(self.errors),
            'avg_latency': f'{avg_latency:.2f}s',
            'total_tokens': self.total_tokens,
            'tokens_per_hour': f'{self.total_tokens/max(uptime/3600, 0.01):.0f}',
        }

    def get_recent(self, n: int = 10) -> list:
        """Get recent observations."""
        return [obs.to_dict() for obs in self.observations[-n:]]

    def get_error_summary(self) -> str:
        """Get human-readable error summary."""
        if not self.errors:
            return "No errors"
        lines = ["Errors:"]
        for etype, count in sorted(self.errors.items(), key=lambda x: -x[1]):
            lines.append(f"  {etype}: {count}")
        return '\n'.join(lines)
