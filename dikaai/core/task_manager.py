"""DikaAI Task Manager

Manages coding tasks with:
  - Goal, status, priority, dependencies
  - Progress tracking
  - Artifacts (files, patches, logs, test results)
  - Multi-step task orchestration
"""
import time
import json
import uuid
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "pending"
    PLANNING = "planning"
    EXECUTING = "executing"
    TESTING = "testing"
    DEBUGGING = "debugging"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class Artifact:
    """An artifact produced by a task."""
    name: str
    artifact_type: str  # file, patch, log, test_result, report
    path: str = ""
    content: str = ""
    created_at: float = 0.0
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'type': self.artifact_type,
            'path': self.path,
            'content': self.content[:500] if self.content else '',
            'created_at': self.created_at,
            'metadata': self.metadata,
        }


@dataclass
class Task:
    """A coding task with full tracking."""
    task_id: str
    goal: str
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 5           # 1=highest, 10=lowest
    parent_id: str = ""         # parent task ID
    subtasks: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    steps: List[Dict] = field(default_factory=list)
    current_step: int = 0
    artifacts: List[Artifact] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    result: str = ""
    created_at: float = 0.0
    updated_at: float = 0.0
    completed_at: float = 0.0
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            'task_id': self.task_id,
            'goal': self.goal,
            'status': self.status.value,
            'priority': self.priority,
            'parent_id': self.parent_id,
            'subtasks': self.subtasks,
            'dependencies': self.dependencies,
            'steps': self.steps,
            'current_step': self.current_step,
            'artifacts': [a.to_dict() for a in self.artifacts],
            'errors': self.errors,
            'result': self.result[:500] if self.result else '',
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'completed_at': self.completed_at,
            'progress': f"{len([s for s in self.steps if s.get('done')])}/{max(len(self.steps), 1)}",
            'metadata': self.metadata,
        }


class TaskManager:
    """Manages coding tasks with state tracking."""

    def __init__(self, data_dir: str = None):
        self._tasks: Dict[str, Task] = {}
        self._data_dir = Path(data_dir) if data_dir else Path("data/tasks")
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._load()

    def _load(self):
        path = self._data_dir / "tasks.json"
        if path.exists():
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                for d in data:
                    task = Task(
                        task_id=d.get('task_id', ''),
                        goal=d.get('goal', ''),
                        status=TaskStatus(d.get('status', 'pending')),
                        priority=d.get('priority', 5),
                        parent_id=d.get('parent_id', ''),
                        subtasks=d.get('subtasks', []),
                        dependencies=d.get('dependencies', []),
                        steps=d.get('steps', []),
                        current_step=d.get('current_step', 0),
                        errors=d.get('errors', []),
                        result=d.get('result', ''),
                        created_at=d.get('created_at', 0),
                        updated_at=d.get('updated_at', 0),
                        completed_at=d.get('completed_at', 0),
                        metadata=d.get('metadata', {}),
                    )
                    self._tasks[task.task_id] = task
            except Exception:
                pass

    def _save(self):
        path = self._data_dir / "tasks.json"
        try:
            data = [t.to_dict() for t in self._tasks.values()]
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def create_task(self, goal: str, priority: int = 5, parent_id: str = "",
                    steps: List[str] = None, dependencies: List[str] = None,
                    **metadata) -> Task:
        """Create a new task."""
        now = time.time()
        task = Task(
            task_id=str(uuid.uuid4())[:8],
            goal=goal,
            priority=priority,
            parent_id=parent_id,
            dependencies=dependencies or [],
            created_at=now,
            updated_at=now,
            metadata=metadata,
        )
        if steps:
            task.steps = [{'description': s, 'done': False} for s in steps]

        with self._lock():
            self._tasks[task.task_id] = task
            if parent_id and parent_id in self._tasks:
                self._tasks[parent_id].subtasks.append(task.task_id)
            self._save()

        return task

    def update_task(self, task_id: str, **kwargs) -> Optional[Task]:
        """Update a task."""
        with self._lock():
            task = self._tasks.get(task_id)
            if not task:
                return None
            for k, v in kwargs.items():
                if hasattr(task, k):
                    setattr(task, k, v)
            task.updated_at = time.time()
            self._save()
            return task

    def set_status(self, task_id: str, status: TaskStatus) -> bool:
        """Update task status."""
        with self._lock():
            task = self._tasks.get(task_id)
            if not task:
                return False
            task.status = status
            task.updated_at = time.time()
            if status == TaskStatus.COMPLETED:
                task.completed_at = time.time()
            self._save()
            return True

    def complete_step(self, task_id: str, result: str = "") -> bool:
        """Mark current step as done and advance."""
        with self._lock():
            task = self._tasks.get(task_id)
            if not task or task.current_step >= len(task.steps):
                return False
            task.steps[task.current_step]['done'] = True
            task.steps[task.current_step]['result'] = result
            task.current_step += 1
            task.updated_at = time.time()
            # Auto-complete if all steps done
            if task.current_step >= len(task.steps):
                task.status = TaskStatus.COMPLETED
                task.completed_at = time.time()
            self._save()
            return True

    def add_artifact(self, task_id: str, name: str, artifact_type: str,
                     path: str = "", content: str = "") -> bool:
        """Add an artifact to a task."""
        with self._lock():
            task = self._tasks.get(task_id)
            if not task:
                return False
            task.artifacts.append(Artifact(
                name=name,
                artifact_type=artifact_type,
                path=path,
                content=content,
                created_at=time.time(),
            ))
            task.updated_at = time.time()
            self._save()
            return True

    def add_error(self, task_id: str, error: str) -> bool:
        """Record an error for a task."""
        with self._lock():
            task = self._tasks.get(task_id)
            if not task:
                return False
            task.errors.append(f"[{time.strftime('%H:%M:%S')}] {error}")
            task.updated_at = time.time()
            self._save()
            return True

    def get_task(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)

    def get_active_tasks(self) -> List[Task]:
        active = {TaskStatus.PENDING, TaskStatus.PLANNING, TaskStatus.EXECUTING,
                  TaskStatus.TESTING, TaskStatus.DEBUGGING}
        return [t for t in self._tasks.values() if t.status in active]

    def get_completed_tasks(self) -> List[Task]:
        return [t for t in self._tasks.values() if t.status == TaskStatus.COMPLETED]

    def get_failed_tasks(self) -> List[Task]:
        return [t for t in self._tasks.values() if t.status == TaskStatus.FAILED]

    def get_recent(self, limit: int = 10) -> List[Task]:
        return sorted(self._tasks.values(), key=lambda t: t.updated_at, reverse=True)[:limit]

    def search(self, query: str) -> List[Task]:
        q = query.lower()
        return [t for t in self._tasks.values() if q in t.goal.lower()]

    def get_stats(self) -> Dict:
        total = len(self._tasks)
        by_status = {}
        for t in self._tasks.values():
            by_status[t.status.value] = by_status.get(t.status.value, 0) + 1
        return {
            'total': total,
            'by_status': by_status,
            'active': len(self.get_active_tasks()),
            'completed': len(self.get_completed_tasks()),
            'failed': len(self.get_failed_tasks()),
        }

    def _lock(self):
        """Simple lock context manager."""
        import threading
        return threading.Lock()
