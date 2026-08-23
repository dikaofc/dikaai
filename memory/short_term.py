"""DikaAI Short-Term Memory - Conversation context."""

import json
import time
from pathlib import Path
from core.config import MEMORY


class ShortTermMemory:
    """Keeps recent conversation context (sliding window)."""

    def __init__(self, limit: int = None):
        self.limit = limit or MEMORY['short_term_limit']
        self.messages = []

    def add(self, role: str, content: str, metadata: dict = None):
        """Add a message to memory."""
        self.messages.append({
            'role': role,
            'content': content,
            'timestamp': time.time(),
            'metadata': metadata or {},
        })
        # Trim to limit
        if len(self.messages) > self.limit:
            self.messages = self.messages[-self.limit:]

    def get_context(self, max_tokens: int = 500) -> str:
        """Get conversation context as formatted string."""
        lines = []
        total = 0
        for msg in reversed(self.messages):
            line = f"{msg['role']}: {msg['content']}"
            total += len(line.split())
            if total > max_tokens:
                break
            lines.insert(0, line)
        return '\n'.join(lines)

    def get_last(self, n: int = 5) -> list:
        """Get last N messages."""
        return self.messages[-n:]

    def clear(self):
        """Clear all memory."""
        self.messages = []

    def to_dict(self) -> list:
        return self.messages

    def from_dict(self, data: list):
        self.messages = data


class ProjectMemory:
    """Remembers project structure and conventions."""

    def __init__(self, project_path: str = None):
        self.project_path = project_path
        self.structure = {}
        self.conventions = []
        self.dependencies = []
        self.architecture = ""

    def analyze_project(self, path: str = None) -> dict:
        """Analyze project structure."""
        from tools.filesystem import FilesystemTools
        fs = FilesystemTools(path or self.project_path)

        result = fs.list_dir(path or self.project_path, max_depth=3)
        if result.get('success'):
            self.structure = {
                'files': [i['name'] for i in result['items'] if i['type'] == 'file'],
                'dirs': [i['name'] for i in result['items'] if i['type'] == 'dir'],
            }

        # Detect language
        exts = set()
        for f in self.structure.get('files', []):
            ext = Path(f).suffix
            if ext:
                exts.add(ext)

        lang_map = {
            '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
            '.go': 'go', '.rs': 'rust', '.java': 'java', '.kt': 'kotlin',
            '.c': 'c', '.cpp': 'cpp', '.sh': 'shell',
        }
        self.languages = [lang_map[e] for e in exts if e in lang_map]

        return self.structure

    def add_convention(self, convention: str):
        self.conventions.append(convention)
        if len(self.conventions) > 20:
            self.conventions = self.conventions[-20:]

    def to_dict(self):
        return {
            'structure': self.structure,
            'conventions': self.conventions,
            'languages': getattr(self, 'languages', []),
        }


class ConversationContext:
    """Manages full conversation context for the orchestrator."""

    def __init__(self):
        self.short_term = ShortTermMemory()
        self.project = ProjectMemory()
        self.current_task = None
        self.current_file = None
        self.last_error = None
        self.session_start = time.time()

    def add_user_message(self, content: str):
        self.short_term.add('user', content)

    def add_assistant_message(self, content: str, metadata: dict = None):
        self.short_term.add('assistant', content, metadata)

    def get_full_context(self) -> dict:
        """Get complete context for response generation."""
        return {
            'conversation': self.short_term.get_context(),
            'project': self.project.to_dict(),
            'current_task': self.current_task,
            'current_file': self.current_file,
            'last_error': self.last_error,
            'session_time': time.time() - self.session_start,
        }

    def set_task(self, task: str):
        self.current_task = task

    def set_file(self, file_path: str):
        self.current_file = file_path

    def set_error(self, error: str):
        self.last_error = error
