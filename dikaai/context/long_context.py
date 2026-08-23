"""
DikaAI 1M Context Manager - Smart context assembly for up to 1M tokens.

Architecture:
    User Query
        ↓
    Intent Detection
        ↓
    Retrieval (hybrid: semantic + keyword)
        ↓
    Compression (if needed)
        ↓
    Reranking (relevance scoring)
        ↓
    Context Budget Allocation
        ↓
    Final Context (up to 1M tokens available, ~2K used per prediction)
"""

import re
import time
from dataclasses import dataclass
from typing import Optional

from dikaai.memory.hierarchical import HierarchicalMemory
from dikaai.context.compressor import ContextCompressor, CompressedContext


@dataclass
class ContextBudget:
    """Dynamic token budget allocation."""
    total: int = 4000
    current_message: int = 200
    recent_turns: int = 800
    topic_memory: int = 400
    long_term: int = 400
    project: int = 400
    summary: int = 300
    archive: int = 200
    reserve: int = 300  # For model reasoning

    def used(self) -> int:
        return (self.current_message + self.recent_turns + self.topic_memory +
                self.long_term + self.project + self.summary + self.archive)

    def available(self) -> int:
        return self.total - self.used() - self.reserve


class LongContextManager:
    """Manages up to 1M tokens of context with smart retrieval and compression.

    Key insight: 1M context capacity ≠ model processes 1M tokens.
    The manager stores 1M tokens, retrieves relevant subsets, compresses,
    and delivers ~2-4K tokens to the model per prediction.
    """

    def __init__(self, data_dir: str = None):
        self.memory = HierarchicalMemory(data_dir)
        self.compressor = ContextCompressor()
        self.budget = ContextBudget()

        # Context history (for compression)
        self._turn_buffer = []
        self._buffer_limit = 50  # Compress every 50 turns

        # Retrieval cache
        self._retrieval_cache = {}
        self._cache_ttl = 60  # seconds

    # ================================================================
    # Core API
    # ================================================================

    def process_message(self, message: str, topic: str = "") -> dict:
        """Process incoming message - update all memory levels.

        Args:
            message: User's message
            topic: Current topic (if known)

        Returns:
            dict with intent, topic, context
        """
        # 1. Detect intent
        intent = self._detect_intent(message)

        # 2. Detect topic
        if not topic:
            topic = self._detect_topic(message)

        # 3. Add to L0-L1
        self.memory.add_turn('user', message, topic)

        # 4. Update topic memory
        if topic:
            self.memory.update_topic(topic)

        # 5. Buffer for compression
        self._turn_buffer.append({'role': 'user', 'content': message, 'topic': topic})

        # 6. Auto-compress if buffer full
        if len(self._turn_buffer) >= self._buffer_limit:
            self._auto_compress()

        return {
            'intent': intent,
            'topic': topic,
            'memory_stats': self.memory.get_stats(),
        }

    def process_response(self, response: str, topic: str = ""):
        """Process assistant response - update memory."""
        self.memory.add_turn('assistant', response, topic)
        self._turn_buffer.append({'role': 'assistant', 'content': response, 'topic': topic})

    def build_context(self, query: str = "", max_tokens: int = 4000) -> str:
        """Build optimal context for the model.

        This is the core method - it assembles context from all memory levels,
        retrieves relevant information, compresses if needed, and returns
        a context string within the token budget.

        Args:
            query: Current user query (for retrieval)
            max_tokens: Maximum tokens for context

        Returns:
            Context string ready for model input
        """
        self.budget = ContextBudget(total=max_tokens)
        parts = []

        # L0: Current message (always first, ~200 tokens)
        if self.memory.current_message:
            parts.append(f"USER: {self.memory.current_message}")

        # L1: Recent turns (~800 tokens)
        recent = self.memory.get_recent_context(max_tokens=self.budget.recent_turns)
        if recent:
            parts.append(recent)

        # L3: Topic memory (~400 tokens)
        topic_ctx = self.memory.get_topic_context(max_tokens=self.budget.topic_memory)
        if topic_ctx:
            parts.append(topic_ctx)

        # L4: Long-term memory - retrieve relevant (~400 tokens)
        lt_ctx = self.memory.get_long_term_context(query, max_tokens=self.budget.long_term)
        if lt_ctx:
            parts.append(lt_ctx)

        # L5: Project knowledge - if coding task (~400 tokens)
        if self._is_coding_task(query):
            proj_ctx = self.memory.get_project_context(max_tokens=self.budget.project)
            if proj_ctx:
                parts.append(proj_ctx)

        # L2: Summary - if budget allows (~300 tokens)
        used = sum(len(p.split()) for p in parts)
        if used < self.budget.total * 0.5:
            summary_ctx = self.memory.get_summary_context(max_tokens=self.budget.summary)
            if summary_ctx:
                parts.append(summary_ctx)

        # L6: Archive - only if specifically relevant (~200 tokens)
        if self._needs_archive(query):
            archive_results = self.memory.search_archive(query, top_k=2)
            if archive_results:
                archive_lines = ["ARCHIVED:"]
                for entry in archive_results:
                    archive_lines.append(f"  [{entry['topic']}] {entry['summary'][:80]}")
                parts.append('\n'.join(archive_lines))

        # Compression: if total exceeds budget, compress
        context = '\n\n'.join(parts)
        total_tokens = len(context.split())

        if total_tokens > self.budget.total:
            context = self._compress_context(context, self.budget.total)

        return context

    # ================================================================
    # Intent Detection
    # ================================================================

    def _detect_intent(self, message: str) -> dict:
        """Detect user intent from message."""
        text = message.lower()

        # Reference resolution
        reference_words = ['lanjut', 'terus', 'nah', 'yang tadi', 'sebelumnya', 'tadi']
        if any(w in text for w in reference_words):
            return {'type': 'reference', 'resolved': True, 'context': self._resolve_reference(message)}

        # Question
        if '?' in text or any(w in text for w in ['gimana', 'kenapa', 'apa', 'how', 'why', 'what']):
            return {'type': 'question', 'resolved': False}

        # Command
        if any(w in text for w in ['fix', 'edit', 'write', 'create', 'run', 'install', 'git']):
            return {'type': 'command', 'resolved': False}

        # Information
        if any(w in text for w in ['adalah', 'merupakan', 'is a', '定义']):
            return {'type': 'information', 'resolved': False}

        return {'type': 'general', 'resolved': False}

    def _resolve_reference(self, message: str) -> str:
        """Resolve vague references to previous context."""
        # Get last topic
        if self.memory.current_topic:
            return f"Lanjutkan topik: {self.memory.current_topic}"

        # Get last assistant message
        if self.memory.recent_turns:
            last = self.memory.recent_turns[-1]
            if last['role'] == 'assistant':
                return f" Lanjutkan: {last['content'][:100]}"

        return message

    # ================================================================
    # Topic Detection
    # ================================================================

    def _detect_topic(self, message: str) -> str:
        """Detect topic from message."""
        text = message.lower()

        topic_keywords = {
            'coding': ['code', 'kode', 'python', 'javascript', 'error', 'bug', 'fix',
                       'function', 'class', 'run', 'test', 'edit', 'write', 'create'],
            'context': ['context', 'memory', 'topic', 'conversation', 'percakapan'],
            'architecture': ['arsitektur', 'architecture', 'design', 'system', 'sistem'],
            'tools': ['git', 'terminal', 'install', 'docker', 'npm', 'pip'],
            'rag': ['rag', 'retrieval', 'vector', 'embedding', 'search'],
            'training': ['training', 'model', 'dataset', 'epoch', 'loss'],
            'api': ['api', 'endpoint', 'rest', 'server', 'deploy'],
            'database': ['database', 'sql', 'redis', 'sqlite', 'query'],
        }

        scores = {}
        for topic, keywords in topic_keywords.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                scores[topic] = score

        if scores:
            return max(scores, key=scores.get)

        # Inherit from current topic
        if self.memory.current_topic:
            return self.memory.current_topic

        return 'general'

    # ================================================================
    # Compression
    # ================================================================

    def _auto_compress(self):
        """Auto-compress buffered turns."""
        if not self._turn_buffer:
            return

        compressed = self.compressor.compress(self._turn_buffer)

        # Store in long-term memory
        for fact in compressed.facts:
            self.memory.add_long_term(fact, topic=compressed.topics[0] if compressed.topics else '',
                                     importance=0.7)

        for decision in compressed.decisions:
            self.memory.add_long_term(f"Decision: {decision}",
                                     topic=compressed.topics[0] if compressed.topics else '',
                                     importance=0.9)

        # Archive if significant
        if compressed.decisions or len(self._turn_buffer) > 30:
            self.memory.archive_conversation(
                summary=compressed.summary,
                topic=compressed.topics[0] if compressed.topics else 'general',
                key_facts=compressed.facts[:10],
            )

        # Clear buffer
        self._turn_buffer = []

    def _compress_context(self, context: str, max_tokens: int) -> str:
        """Compress context to fit within token budget."""
        lines = context.split('\n\n')
        result = []
        total = 0

        for part in lines:
            tokens = len(part.split())
            if total + tokens <= max_tokens:
                result.append(part)
                total += tokens
            else:
                # Truncate this part
                remaining = max_tokens - total
                if remaining > 20:
                    words = part.split()[:remaining]
                    result.append(' '.join(words) + '...')
                break

        return '\n\n'.join(result)

    # ================================================================
    # Helpers
    # ================================================================

    def _is_coding_task(self, query: str) -> bool:
        """Check if query is a coding task."""
        coding_words = ['code', 'file', 'function', 'class', 'error', 'fix',
                        'edit', 'read', 'write', 'bug', 'test', 'import', 'def']
        return any(w in (query or '').lower() for w in coding_words)

    def _needs_archive(self, query: str) -> bool:
        """Check if query needs archive retrieval."""
        archive_words = ['before', 'earlier', 'previously', 'last time', 'remember',
                        'sebelumnya', 'tadi', 'kemarin', 'yang lalu']
        return any(w in (query or '').lower() for w in archive_words)

    # ================================================================
    # Stats
    # ================================================================

    def get_stats(self) -> dict:
        """Get comprehensive stats."""
        memory_stats = self.memory.get_stats()
        return {
            **memory_stats,
            'buffer_size': len(self._turn_buffer),
            'budget_used': self.budget.used() if self.budget else 0,
            'budget_total': self.budget.total if self.budget else 0,
        }

    def get_memory_summary(self) -> str:
        """Get human-readable memory summary."""
        stats = self.get_stats()
        lines = [
            "=== DikaAI 1M Context Memory ===",
            f"L1 Recent turns    : {stats['recent_turns']}",
            f"L2 Summary turns   : {stats['summary_turns']}",
            f"L3 Topics          : {stats['topics']}",
            f"L4 Long-term       : {stats['long_term_entries']} entries",
            f"L5 Project files   : {stats['project_files']}",
            f"L6 Archive entries : {stats['archive_entries']}",
            f"Total tokens stored: {stats['total_tokens_stored']:,}",
            f"Tokens compressed  : {stats['total_tokens_compressed']:,}",
            f"Compression ratio  : {stats['compression_ratio']:.1%}",
            f"Buffer             : {stats['buffer_size']}/{self._buffer_limit}",
        ]
        return '\n'.join(lines)
