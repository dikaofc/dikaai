"""DikaAI State Manager - Tracks what DikaAI is doing.

Answers: WHERE AM I? WHAT AM I DOING? WHAT HAVE I DONE? WHAT REMAINS?
"""

import time
import json
from pathlib import Path
from core.config import DATA_DIR


class TaskState:
    """Tracks a single task's state."""

    def __init__(self, task: str):
        self.task = task
        self.status = "pending"  # pending / in_progress / testing / done / failed
        self.started_at = time.time()
        self.completed_steps = []
        self.remaining_steps = []
        self.current_step = ""
        self.errors = []
        self.result = ""
        self.retries = 0

    def start(self, step: str = ""):
        self.status = "in_progress"
        self.current_step = step

    def complete_step(self, step: str, result: str = ""):
        self.completed_steps.append({'step': step, 'result': result, 'time': time.time()})
        self.current_step = ""

    def fail(self, error: str):
        self.errors.append({'error': error, 'time': time.time()})
        self.status = "failed"

    def done(self, result: str = ""):
        self.status = "done"
        self.result = result

    def to_dict(self) -> dict:
        return {
            'task': self.task,
            'status': self.status,
            'completed': [s['step'] for s in self.completed_steps],
            'remaining': self.remaining_steps,
            'current': self.current_step,
            'errors': len(self.errors),
            'retries': self.retries,
            'elapsed': f'{time.time() - self.started_at:.1f}s',
        }


class StateManager:
    """Manages all active task states."""

    def __init__(self):
        self.active_tasks = []
        self.completed_tasks = []
        self.current_task = None
        self.session_start = time.time()

    def start_task(self, task: str) -> TaskState:
        """Start tracking a new task."""
        state = TaskState(task)
        self.current_task = state
        self.active_tasks.append(state)
        return state

    def get_current(self) -> dict:
        """Get current task state."""
        if self.current_task:
            return self.current_task.to_dict()
        return {'task': '', 'status': 'idle'}

    def complete_current(self, result: str = ""):
        """Mark current task as done."""
        if self.current_task:
            self.current_task.done(result)
            self.completed_tasks.append(self.current_task)
            self.active_tasks.remove(self.current_task)
            self.current_task = None

    def fail_current(self, error: str):
        """Mark current task as failed."""
        if self.current_task:
            self.current_task.fail(error)

    def get_progress(self) -> str:
        """Get human-readable progress summary."""
        if not self.current_task:
            return "Idle - no active task"

        t = self.current_task
        completed = len(t.completed_steps)
        total = completed + len(t.remaining_steps)
        pct = (completed / max(total, 1)) * 100

        lines = [
            f"Task: {t.task[:60]}",
            f"Status: {t.status}",
            f"Progress: {completed}/{total} steps ({pct:.0f}%)",
        ]

        if t.current_step:
            lines.append(f"Current: {t.current_step}")

        if t.errors:
            lines.append(f"Errors: {len(t.errors)}")

        return '\n'.join(lines)

    def to_dict(self) -> dict:
        return {
            'current': self.get_current(),
            'active_count': len(self.active_tasks),
            'completed_count': len(self.completed_tasks),
            'session_time': f'{(time.time() - self.session_start)/3600:.1f}h',
        }
