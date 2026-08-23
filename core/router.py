"""DikaAI Router - Classifies user intent and routes to appropriate handler.

Routes:
- CHAT: Simple conversation, questions, greetings
- CODE: Writing, reading, editing, debugging code
- REASON: Complex reasoning, architecture, debugging logic
- SEARCH: Looking up information, finding files, docs
- TOOL: Running commands, git operations
"""

import re
from enum import Enum


class TaskType(Enum):
    CHAT = "chat"
    CODE = "code"
    REASON = "reason"
    SEARCH = "search"
    TOOL = "tool"
    UNKNOWN = "unknown"


class TaskPriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3


class Route:
    def __init__(self, task_type: TaskType, priority: TaskPriority = TaskPriority.NORMAL,
                 language: str = None, action: str = None, context: dict = None):
        self.task_type = task_type
        self.priority = priority
        self.language = language
        self.action = action
        self.context = context or {}

    def __repr__(self):
        return f"Route({self.task_type.value}, lang={self.language}, action={self.action})"


# ============================================================
# Intent Patterns
# ============================================================

CODE_PATTERNS = [
    # File operations
    r'\b(buka|open|read|lihat|tampilkan|show|display)\s+(file|kode|code|source)',
    r'\b(ubah|edit|modify|update|ganti|replace|fix|perbaiki|repair)\s+(file|kode|code)',
    r'\b(buat|create|write|tulis|generate|build|tambah|add)\s+(file|kode|code|script|function|class|module)',
    r'\b(hapus|delete|remove)\s+(file|baris|line|code)',

    # Code actions
    r'\b(run|jalankan|execute|eksekusi)\s+(code|kode|script|program|file)',
    r'\b(test|uji|coba|try)\s+(code|kode|program|file)',
    r'\b(deploy|publish|push|release)',
    r'\b(refactor|rewrite|restructure|clean|optimi[sz]e)',

    # Error fixing
    r'\b(error|bug|fix|perbaiki|repair|debug|traceback|exception|crash)',
    r'\b(mengapa|kenapa|why)\s+.*\s+(error|bug|crash|fail|gagal)',

    # Code generation
    r'\b(buatkan|make|create|write|tulis|generate|code|kode)\b.*\b(function|class|script|program|app|api|endpoint|module|component)',
    r'\b(how to|gimana cara|cara)\s+(write|create|make|build|implement)',

    # Programming languages
    r'\b(python|javascript|typescript|golang|rust|java|kotlin|c\+\+|cpp|shell|bash|sql|html|css|react|vue|svelte|nextjs|fastapi|flask|django|express|spring)',
]

REASON_PATTERNS = [
    r'\b(kenapa|why|explain|jelaskan|analys[ei]|evaluat[ei]|compar[ei]|perbandingan|architecture|arsitektur|design|desain|strategi|strategy)',
    r'\b(best practice|praktik terbaik|approach|pendekatan|solution|solusi|recommendation|rekomendasi|saran|suggest)',
    r'\b(pros? and cons|kelebihan.?kekurangan|trade.?off|alternatif|alternative|option|pilihan)',
    r'\b(bagaimana|how|gimana)\s+(seharusnya|should|better|lebih baik|optimal|efisien)',
    r'\b(masalah|problem|issue|challenge|kompleks|complex|difficult|sulit)',
]

SEARCH_PATTERNS = [
    r'\b(cari|find|search|look|google|searching|gogling|mencari)',
    r'\b(dimana|where|lokasi|location|posisi|position)',
    r'\b(documentation|docs|dokumentasi|reference|referensi|tutorial|panduan|guide)',
    r'\b(library|pustaka|package|paket|dependency|dependensi)',
]

TOOL_PATTERNS = [
    r'\b(git\s+(push|pull|commit|diff|status|log|branch|merge|rebase|stash|checkout|clone))',
    r'\b(install|pasang|setup|konfigurasi|config|setting)',
    r'\b(docker|kubernetes|nginx|apache|mysql|postgres|redis|mongodb)',
    r'\b(pip|npm|yarn|pnpm|cargo|go get|brew|apt|pkg)',
    r'\b(ls|cd|mkdir|cp|mv|cat|grep|find|awk|sed|curl|wget)',
]


class Router:
    """Routes user messages to appropriate task handlers."""

    def __init__(self):
        self._compiled = {
            TaskType.CODE: [re.compile(p, re.IGNORECASE) for p in CODE_PATTERNS],
            TaskType.REASON: [re.compile(p, re.IGNORECASE) for p in REASON_PATTERNS],
            TaskType.SEARCH: [re.compile(p, re.IGNORECASE) for p in SEARCH_PATTERNS],
            TaskType.TOOL: [re.compile(p, re.IGNORECASE) for p in TOOL_PATTERNS],
        }

    def route(self, message: str) -> Route:
        """Classify message and return route."""
        text = message.strip()

        # Check each category, highest confidence wins
        scores = {t: 0 for t in TaskType if t not in (TaskType.UNKNOWN, TaskType.CHAT)}

        for task_type, patterns in self._compiled.items():
            for pattern in patterns:
                if pattern.search(text):
                    scores[task_type] += 1

        # Detect language
        language = self._detect_language(text)

        # Detect action
        action = self._detect_action(text)

        # Get highest scoring category
        max_score = max(scores.values())

        if max_score == 0:
            # Default to CHAT
            return Route(TaskType.CHAT, language=language, action='chat')

        best_type = max(scores, key=scores.get)

        # Priority
        priority = TaskPriority.NORMAL
        if any(w in text.lower() for w in ['urgent', 'segera', 'important', 'penting']):
            priority = TaskPriority.HIGH
        if any(w in text.lower() for w in ['error', 'bug', 'crash', 'broken', 'rusak']):
            priority = TaskPriority.HIGH

        return Route(best_type, priority=priority, language=language,
                     action=action, context={'scores': scores})

    def _detect_language(self, text: str) -> str:
        """Detect programming language from text."""
        text_lower = text.lower()
        lang_map = {
            'python': ['python', 'py', 'django', 'flask', 'fastapi', 'numpy', 'pandas'],
            'javascript': ['javascript', 'js', 'node', 'react', 'vue', 'express', 'nextjs', 'next.js'],
            'typescript': ['typescript', 'ts', 'next.js', 'nest'],
            'go': ['golang', 'go '],
            'rust': ['rust', 'cargo'],
            'java': ['java ', 'spring', 'maven', 'gradle'],
            'kotlin': ['kotlin', 'android studio'],
            'shell': ['bash', 'shell', 'sh ', 'zsh', 'termux'],
            'c': [' c ', 'clang', 'gcc'],
            'cpp': ['c++', 'cpp', 'cmake'],
            'sql': ['sql', 'mysql', 'postgres', 'sqlite', 'database'],
            'html': ['html', 'css', 'web'],
        }
        for lang, keywords in lang_map.items():
            if any(kw in text_lower for kw in keywords):
                return lang
        return None

    def _detect_action(self, text: str) -> str:
        """Detect specific action from text."""
        text_lower = text.lower()
        action_map = {
            'create': ['buat', 'create', 'write', 'tulis', 'generate', 'tambah'],
            'read': ['baca', 'read', 'open', 'buka', 'lihat', 'show', 'tampilkan'],
            'edit': ['ubah', 'edit', 'modify', 'update', 'ganti', 'replace', 'fix'],
            'delete': ['hapus', 'delete', 'remove'],
            'run': ['run', 'jalankan', 'execute', 'eksekusi'],
            'test': ['test', 'uji', 'coba'],
            'debug': ['debug', 'traceback', 'error', 'bug'],
            'refactor': ['refactor', 'rewrite', 'restructure', 'clean', 'optimi'],
            'search': ['cari', 'find', 'search', 'look'],
            'explain': ['jelaskan', 'explain', 'kenapa', 'why', 'apa itu'],
        }
        for action, keywords in action_map.items():
            if any(kw in text_lower for kw in keywords):
                return action
        return 'chat'
