"""DikaAI Trace System

Records full audit trail for every request:
  user_input → intent → memory → context → model → tools → verification → response

Helps debug why the AI gave a specific answer.
"""
import time
import json
import uuid
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
import threading


@dataclass
class TraceEvent:
    """A single event in the trace."""
    step: str              # intent, memory, context, model, tool, verify, response
    input_data: Any = None
    output_data: Any = None
    duration_ms: float = 0
    metadata: Dict = field(default_factory=dict)
    timestamp: float = 0.0

    def to_dict(self) -> Dict:
        return {
            'step': self.step,
            'input': str(self.input_data)[:500] if self.input_data else None,
            'output': str(self.output_data)[:500] if self.output_data else None,
            'duration_ms': round(self.duration_ms, 2),
            'metadata': self.metadata,
            'timestamp': self.timestamp,
        }


@dataclass
class Trace:
    """Full trace for a single request."""
    trace_id: str
    user_input: str
    events: List[TraceEvent] = field(default_factory=list)
    final_response: str = ""
    route: str = ""
    success: bool = True
    total_duration_ms: float = 0
    started_at: float = 0.0
    completed_at: float = 0.0
    metadata: Dict = field(default_factory=dict)

    def add_event(self, step: str, input_data=None, output_data=None,
                  duration_ms: float = 0, **metadata) -> TraceEvent:
        event = TraceEvent(
            step=step,
            input_data=input_data,
            output_data=output_data,
            duration_ms=duration_ms,
            metadata=metadata,
            timestamp=time.time(),
        )
        self.events.append(event)
        return event

    def complete(self, response: str, route: str = "", success: bool = True):
        self.final_response = response
        self.route = route
        self.success = success
        self.completed_at = time.time()
        self.total_duration_ms = (self.completed_at - self.started_at) * 1000

    def to_dict(self) -> Dict:
        return {
            'trace_id': self.trace_id,
            'user_input': self.user_input[:200],
            'events': [e.to_dict() for e in self.events],
            'final_response': self.final_response[:500],
            'route': self.route,
            'success': self.success,
            'total_duration_ms': round(self.total_duration_ms, 2),
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'event_count': len(self.events),
            'metadata': self.metadata,
        }

    def summary(self) -> str:
        """Human-readable trace summary."""
        lines = [f"Trace {self.trace_id[:8]}: {self.user_input[:50]}"]
        for e in self.events:
            lines.append(f"  [{e.step}] {e.duration_ms:.1f}ms")
        lines.append(f"  → Route: {self.route} | {'✅' if self.success else '❌'} | {self.total_duration_ms:.1f}ms total")
        return '\n'.join(lines)


class TraceSystem:
    """Records and manages traces for debugging."""

    def __init__(self, data_dir: str = None, max_traces: int = 500):
        self._traces: List[Trace] = []
        self._max_traces = max_traces
        self._lock = threading.Lock()
        self._data_dir = Path(data_dir) if data_dir else Path("data/traces")
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._load()

    def _load(self):
        """Load recent traces from disk."""
        path = self._data_dir / "recent_traces.json"
        if path.exists():
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                for d in data[-self._max_traces:]:
                    trace = Trace(
                        trace_id=d.get('trace_id', ''),
                        user_input=d.get('user_input', ''),
                        final_response=d.get('final_response', ''),
                        route=d.get('route', ''),
                        success=d.get('success', True),
                        total_duration_ms=d.get('total_duration_ms', 0),
                        started_at=d.get('started_at', 0),
                        completed_at=d.get('completed_at', 0),
                        metadata=d.get('metadata', {}),
                    )
                    self._traces.append(trace)
            except Exception:
                pass

    def _save(self):
        """Save traces to disk."""
        path = self._data_dir / "recent_traces.json"
        try:
            data = [t.to_dict() for t in self._traces[-self._max_traces:]]
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def start_trace(self, user_input: str, **metadata) -> Trace:
        """Start a new trace."""
        trace = Trace(
            trace_id=str(uuid.uuid4()),
            user_input=user_input,
            started_at=time.time(),
            metadata=metadata,
        )
        return trace

    def save_trace(self, trace: Trace):
        """Save completed trace."""
        with self._lock:
            self._traces.append(trace)
            if len(self._traces) > self._max_traces:
                self._traces = self._traces[-self._max_traces:]
            self._save()

    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """Get a specific trace by ID."""
        for t in self._traces:
            if t.trace_id == trace_id:
                return t
        return None

    def get_recent(self, limit: int = 20) -> List[Trace]:
        """Get recent traces."""
        return self._traces[-limit:]

    def get_failures(self, limit: int = 20) -> List[Trace]:
        """Get failed traces."""
        return [t for t in self._traces if not t.success][-limit:]

    def get_slowest(self, limit: int = 10) -> List[Trace]:
        """Get slowest traces."""
        return sorted(self._traces, key=lambda t: t.total_duration_ms, reverse=True)[:limit]

    def search(self, query: str, limit: int = 10) -> List[Trace]:
        """Search traces by query."""
        query_lower = query.lower()
        return [t for t in self._traces if query_lower in t.user_input.lower()][-limit:]

    def get_stats(self) -> Dict:
        if not self._traces:
            return {'total': 0, 'success_rate': '0%', 'avg_duration_ms': 0}

        total = len(self._traces)
        successful = sum(1 for t in self._traces if t.success)
        avg_duration = sum(t.total_duration_ms for t in self._traces) / total

        return {
            'total': total,
            'successful': successful,
            'failed': total - successful,
            'success_rate': f'{successful/total*100:.0f}%',
            'avg_duration_ms': round(avg_duration, 1),
            'slowest_ms': round(max(t.total_duration_ms for t in self._traces), 1) if self._traces else 0,
        }
