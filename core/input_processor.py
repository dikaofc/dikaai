"""DikaAI Input Processor - Analyzes incoming messages.

Extracts: language, intent, entities, ambiguity level, complexity.
"""

import re
from enum import Enum


class Language(Enum):
    INDONESIAN = "id"
    ENGLISH = "en"
    MIXED = "mixed"
    CODE = "code"
    UNKNOWN = "unknown"


class Intent(Enum):
    QUESTION = "question"
    REQUEST = "request"
    DEBUG = "debug"
    EXPLAIN = "explain"
    CREATE = "create"
    MODIFY = "modify"
    CONTINUE = "continue"
    COMPARE = "compare"
    SUMMARIZE = "summarize"
    EXECUTE = "execute"
    SEARCH = "search"
    LEARN = "learn"
    REVIEW = "review"
    CHAT = "chat"
    UNKNOWN = "unknown"


class Complexity(Enum):
    TRIVIAL = 0   # "2+2"
    SIMPLE = 1    # "apa itu git"
    MODERATE = 2  # "buat function python"
    COMPLEX = 3   # "refactor project ini"
    VERY_COMPLEX = 4  # "redesign architecture"


# Indonesian signal words
ID_WORDS = {
    'yang', 'dan', 'ini', 'itu', 'untuk', 'dengan', 'tidak', 'ada',
    'bisa', 'saya', 'kamu', 'dia', 'akan', 'sudah', 'belum', 'lagi',
    'mau', 'halo', 'hai', 'apa', 'siapa', 'kenapa', 'gimana', 'kapan',
    'dimana', 'sih', 'dong', 'nih', 'deh', 'lah', 'kok', 'aja',
    'banget', 'mantap', 'bikin', 'buat', 'cari', 'jalankan', 'fix',
    'error', 'bug', 'test', 'run', 'install', 'deploy', 'push',
}

EN_WORDS = {
    'the', 'is', 'are', 'was', 'were', 'have', 'has', 'had',
    'will', 'would', 'could', 'should', 'can', 'may', 'might',
    'what', 'why', 'how', 'when', 'where', 'who', 'which',
    'this', 'that', 'these', 'those', 'my', 'your', 'his', 'her',
    'make', 'create', 'write', 'fix', 'debug', 'run', 'test',
    'find', 'search', 'explain', 'show', 'tell', 'help',
}

INTENT_PATTERNS = {
    Intent.QUESTION: [r'\?$', r'\b(apa|what|why|how|gimana|kenapa|dimana|kapan|siapa)\b'],
    Intent.DEBUG: [r'\b(error|bug|fix|traceback|exception|crash|gagal|rusak)\b'],
    Intent.EXPLAIN: [r'\b(jelaskan|explain|apa itu|what is|gimana cara|how to)\b'],
    Intent.CREATE: [r'\b(buat|create|write|tulis|generate|build|tambah|add)\b'],
    Intent.MODIFY: [r'\b(ubah|edit|modify|update|ganti|replace|fix|perbaiki)\b'],
    Intent.CONTINUE: [r'\b(lanjut|terus|nah|gimana|yang tadi|sebelumnya)\b'],
    Intent.COMPARE: [r'\b(bandingkan|compare|vs|versus|mana yang lebih)\b'],
    Intent.SUMMARIZE: [r'\b(ringkas|summarize|summary|rekap|recap)\b'],
    Intent.EXECUTE: [r'\b(jalankan|run|execute|eksekusi)\b'],
    Intent.SEARCH: [r'\b(cari|find|search|look|google)\b'],
    Intent.REVIEW: [r'\b(review|audit|check|cek|evaluasi|evaluate)\b'],
}


class InputProcessor:
    """Processes incoming user messages."""

    def process(self, message: str) -> dict:
        """Full analysis of user message."""
        return {
            'original': message,
            'language': self._detect_language(message),
            'intent': self._detect_intent(message),
            'complexity': self._assess_complexity(message),
            'entities': self._extract_entities(message),
            'is_ambigious': self._check_ambiguity(message),
            'is_code': self._is_code(message),
            'word_count': len(message.split()),
            'char_count': len(message),
        }

    def _detect_language(self, text: str) -> str:
        """Detect language (id/en/mixed/code)."""
        words = set(text.lower().split())
        id_score = len(words & ID_WORDS)
        en_score = len(words & EN_WORDS)

        # Check for code patterns
        code_patterns = [r'def\s+\w+', r'function\s+\w+', r'class\s+\w+',
                        r'import\s+\w+', r'const\s+\w+', r'let\s+\w+']
        if any(re.search(p, text) for p in code_patterns):
            return Language.CODE.value

        if id_score > 2 and en_score > 2:
            return Language.MIXED.value
        elif id_score > en_score:
            return Language.INDONESIAN.value
        elif en_score > id_score:
            return Language.ENGLISH.value
        return Language.UNKNOWN.value

    def _detect_intent(self, text: str) -> str:
        """Detect user intent."""
        text_lower = text.lower()
        scores = {}

        for intent, patterns in INTENT_PATTERNS.items():
            score = sum(1 for p in patterns if re.search(p, text_lower))
            if score > 0:
                scores[intent] = score

        if not scores:
            return Intent.CHAT.value

        return max(scores, key=scores.get).value

    def _assess_complexity(self, text: str) -> str:
        """Assess task complexity."""
        words = text.split()
        word_count = len(words)

        # Trivial: very short
        if word_count <= 3:
            return Complexity.TRIVIAL.value

        # Simple: single question
        if word_count <= 8 and '?' in text:
            return Complexity.SIMPLE.value

        # Complex indicators
        complex_indicators = [
            r'\b(refactor|redesign|restructure|optimi[sz]e)\b',
            r'\b(project|repo|codebase|architecture)\b',
            r'\b(multiple|semua|all|every|each)\b',
            r'\b(and then|lalu|setelah itu|kemudian)\b',
        ]
        complex_score = sum(1 for p in complex_indicators if re.search(p, text.lower()))

        if complex_score >= 3 or word_count > 30:
            return Complexity.VERY_COMPLEX.value
        elif complex_score >= 2 or word_count > 15:
            return Complexity.COMPLEX.value
        elif word_count > 8:
            return Complexity.MODERATE.value

        return Complexity.SIMPLE.value

    def _extract_entities(self, text: str) -> list:
        """Extract named entities (files, languages, tools)."""
        entities = []

        # File references
        file_pattern = r'[\w/\\.-]+\.\w{1,5}'
        for match in re.finditer(file_pattern, text):
            entities.append({'type': 'file', 'value': match.group()})

        # Programming languages
        lang_pattern = r'\b(python|javascript|typescript|golang|go|rust|java|kotlin|c\+\+|cpp|shell|bash|sql|html|css|react|vue|svelte|django|flask|fastapi|node|express|nextjs|next\.js)\b'
        for match in re.finditer(lang_pattern, text, re.IGNORECASE):
            entities.append({'type': 'language', 'value': match.group().lower()})

        # Tools
        tool_pattern = r'\b(git|docker|npm|pip|cargo|brew|apt|npm|yarn|pnpm|nginx|apache|redis|mysql|postgres|sqlite|mongodb)\b'
        for match in re.finditer(tool_pattern, text, re.IGNORECASE):
            entities.append({'type': 'tool', 'value': match.group().lower()})

        return entities

    def _check_ambiguity(self, text: str) -> bool:
        """Check if message is ambiguous."""
        ambiguous_patterns = [
            r'^(itu|ini|yang|yg)\s*$',  # Just reference words
            r'^(ok|oke|ya|iy|nah)\s*$',  # Just acknowledgments
            r'^(hmm|hm|hmm|uh|um)\s*$',  # Just sounds
            r'\.\.\.$',  # Trailing dots
        ]
        return any(re.search(p, text.lower().strip()) for p in ambiguous_patterns)

    def _is_code(self, text: str) -> bool:
        """Check if message contains code."""
        code_patterns = [
            r'def\s+\w+\s*\(',
            r'function\s+\w+\s*\(',
            r'class\s+\w+',
            r'import\s+',
            r'const\s+\w+\s*=',
            r'let\s+\w+\s*=',
            r'var\s+\w+\s*=',
            r'return\s+',
            r'if\s*\(',
            r'for\s*\(',
            r'while\s*\(',
            r'\{\s*$',
            r'\}\s*$',
        ]
        return sum(1 for p in code_patterns if re.search(p, text)) >= 2
