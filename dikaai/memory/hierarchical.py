"""
DikaAI Hierarchical Memory - L0-L6 multi-level memory system.

Memory levels:
    L0  Current message
    L1  Recent turns (last N messages)
    L2  Current conversation summary
    L3  Topic summaries (per-topic compressed)
    L4  Long-term memory (cross-conversation)
    L5  Project knowledge (code, docs, architecture)
    L6  Archived conversations (compressed, searchable)

Strategy:
    - L0-L1: Always available (fast access)
    - L2: Compressed from L0-L1 periodically
    - L3: Compressed when topic changes
    - L4: Indexed for retrieval
    - L5: Project index (static until re-indexed)
    - L6: Archive (compressed, rarely accessed)
"""

import time
import json
import hashlib
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MemoryEntry:
    """Single memory entry."""
    content: str
    timestamp: float
    level: int  # 0-6
    topic: str = ""
    summary: str = ""
    tokens: int = 0
    importance: float = 0.5  # 0-1
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        return {
            'content': self.content[:500],
            'timestamp': self.timestamp,
            'level': self.level,
            'topic': self.topic,
            'summary': self.summary,
            'tokens': self.tokens,
            'importance': self.importance,
        }


@dataclass
class TopicMemory:
    """Compressed memory for a single topic."""
    topic: str
    summary: str
    key_facts: list
    decisions: list
    entities: list
    turn_count: int
    first_seen: float
    last_seen: float
    importance: float = 0.5

    def to_dict(self):
        return {
            'topic': self.topic,
            'summary': self.summary,
            'key_facts': self.key_facts[-10:],
            'decisions': self.decisions[-10:],
            'entities': self.entities[-10:],
            'turn_count': self.turn_count,
            'importance': self.importance,
        }


class HierarchicalMemory:
    """Multi-level memory system supporting up to 1M tokens of context."""

    def __init__(self, data_dir: str = None):
        self.data_dir = Path(data_dir or 'data/memory')
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # L0: Current message
        self.current_message = ""

        # L1: Recent turns (ring buffer)
        self.recent_turns = []
        self.recent_limit = 20

        # L2: Conversation summary
        self.conversation_summary = ""
        self.summary_turn_count = 0

        # L3: Topic memories
        self.topic_memories = {}  # topic_name -> TopicMemory
        self.current_topic = ""

        # L4: Long-term memory
        self.long_term = []  # List of MemoryEntry
        self.long_term_limit = 1000

        # L5: Project knowledge
        self.project_index = {}  # file_path -> metadata
        self.project_stats = {'files': 0, 'lines': 0, 'symbols': 0}

        # L6: Archive
        self.archive = []  # Compressed old conversations
        self.archive_limit = 500

        # Stats
        self.total_tokens_stored = 0
        self.total_tokens_compressed = 0
        self.compression_ratio = 0.0

        # Load saved state
        self._load()

    # ================================================================
    # L0-L1: Current & Recent
    # ================================================================

    def add_turn(self, role: str, content: str, topic: str = ""):
        """Add a conversation turn (updates L0 and L1)."""
        import re
        tokens = len(re.findall(r'\b\w+\b', content))

        entry = MemoryEntry(
            content=content,
            timestamp=time.time(),
            level=1,
            topic=topic or self.current_topic,
            tokens=tokens,
        )

        # Update L0
        if role == 'user':
            self.current_message = content

        # Update L1
        self.recent_turns.append({
            'role': role,
            'content': content,
            'timestamp': entry.timestamp,
            'topic': entry.topic,
            'tokens': tokens,
        })

        if len(self.recent_turns) > self.recent_limit:
            self.recent_turns = self.recent_turns[-self.recent_limit:]

        self.total_tokens_stored += tokens

        # Auto-compress if recent turns exceed limit
        if len(self.recent_turns) >= self.recent_limit:
            self._compress_recent()

    def get_recent_context(self, max_tokens: int = 500) -> str:
        """Get recent conversation as text (L0 + L1)."""
        lines = []
        total = 0

        # L0: Current message
        if self.current_message:
            lines.append(f"CURRENT: {self.current_message}")

        # L1: Recent turns (newest first, within token budget)
        for turn in reversed(self.recent_turns):
            tokens = turn.get('tokens', len(turn['content'].split()))
            if total + tokens > max_tokens:
                break
            lines.insert(1, f"{turn['role'].upper()}: {turn['content'][:200]}")
            total += tokens

        return '\n'.join(lines)

    # ================================================================
    # L2: Conversation Summary
    # ================================================================

    def _compress_recent(self):
        """Compress old turns into L2 summary."""
        if len(self.recent_turns) < 10:
            return

        # Take oldest half and compress
        old_turns = self.recent_turns[:len(self.recent_turns) // 2]
        self.recent_turns = self.recent_turns[len(self.recent_turns) // 2:]

        # Build summary
        topics = set()
        key_points = []
        for turn in old_turns:
            topic = turn.get('topic', '')
            if topic:
                topics.add(topic)
            content = turn['content'][:100]
            if len(content) > 20:
                key_points.append(content)

        # Update L2 summary
        summary_parts = []
        if self.conversation_summary:
            summary_parts.append(self.conversation_summary)
        if topics:
            summary_parts.append(f"Topics discussed: {', '.join(topics)}")
        if key_points:
            summary_parts.append(f"Key points: {'; '.join(key_points[:5])}")

        self.conversation_summary = ' | '.join(summary_parts)
        self.summary_turn_count += len(old_turns)

        # Extract topic memories
        for turn in old_turns:
            topic = turn.get('topic', '')
            if topic and topic not in self.topic_memories:
                self.topic_memories[topic] = TopicMemory(
                    topic=topic,
                    summary="",
                    key_facts=[],
                    decisions=[],
                    entities=[],
                    turn_count=0,
                    first_seen=turn['timestamp'],
                    last_seen=turn['timestamp'],
                )
            if topic in self.topic_memories:
                tm = self.topic_memories[topic]
                tm.turn_count += 1
                tm.last_seen = turn['timestamp']
                content = turn['content'][:100]
                if content and content not in tm.key_facts:
                    tm.key_facts.append(content)
                    if len(tm.key_facts) > 20:
                        tm.key_facts = tm.key_facts[-20:]

        self.total_tokens_compressed += sum(t.get('tokens', 0) for t in old_turns)

    def get_summary_context(self, max_tokens: int = 300) -> str:
        """Get L2 conversation summary."""
        if not self.conversation_summary:
            return ""
        lines = [f"CONVERSATION SUMMARY ({self.summary_turn_count} turns compressed):"]
        lines.append(self.conversation_summary[:max_tokens])
        return '\n'.join(lines)

    # ================================================================
    # L3: Topic Memory
    # ================================================================

    def update_topic(self, topic: str, summary: str = "", facts: list = None,
                     decisions: list = None, entities: list = None):
        """Update topic memory (L3)."""
        if topic not in self.topic_memories:
            self.topic_memories[topic] = TopicMemory(
                topic=topic,
                summary=summary,
                key_facts=facts or [],
                decisions=decisions or [],
                entities=entities or [],
                turn_count=0,
                first_seen=time.time(),
                last_seen=time.time(),
            )
        else:
            tm = self.topic_memories[topic]
            if summary:
                tm.summary = summary
            if facts:
                tm.key_facts.extend(facts)
                tm.key_facts = tm.key_facts[-20:]
            if decisions:
                tm.decisions.extend(decisions)
                tm.decisions = tm.decisions[-10:]
            if entities:
                tm.entities.extend(entities)
                tm.entities = tm.entities[-10:]
            tm.last_seen = time.time()

        self.current_topic = topic

    def get_topic_context(self, topic: str = None, max_tokens: int = 300) -> str:
        """Get L3 topic memory."""
        topic = topic or self.current_topic
        if not topic or topic not in self.topic_memories:
            return ""

        tm = self.topic_memories[topic]
        lines = [f"TOPIC: {tm.topic} ({tm.turn_count} turns)"]
        if tm.summary:
            lines.append(f"Summary: {tm.summary[:200]}")
        if tm.key_facts:
            lines.append(f"Facts: {'; '.join(tm.key_facts[-5:])}")
        if tm.decisions:
            lines.append(f"Decisions: {'; '.join(tm.decisions[-3:])}")
        if tm.entities:
            lines.append(f"Entities: {', '.join(tm.entities[-5:])}")

        return '\n'.join(lines)[:max_tokens]

    def get_all_topics(self) -> list:
        """Get all topic names."""
        return list(self.topic_memories.keys())

    # ================================================================
    # L4: Long-term Memory
    # ================================================================

    def add_long_term(self, content: str, topic: str = "", importance: float = 0.5,
                      metadata: dict = None):
        """Add to long-term memory (L4)."""
        import re
        tokens = len(re.findall(r'\b\w+\b', content))

        entry = MemoryEntry(
            content=content,
            timestamp=time.time(),
            level=4,
            topic=topic,
            tokens=tokens,
            importance=importance,
            metadata=metadata or {},
        )
        self.long_term.append(entry)

        # Keep under limit
        if len(self.long_term) > self.long_term_limit:
            # Remove lowest importance entries
            self.long_term.sort(key=lambda e: e.importance, reverse=True)
            self.long_term = self.long_term[:self.long_term_limit]

        self.total_tokens_stored += tokens

    def search_long_term(self, query: str, top_k: int = 5) -> list:
        """Search long-term memory (L4)."""
        query_words = set(query.lower().split())
        results = []

        for entry in self.long_term:
            # Simple word overlap scoring
            entry_words = set(entry.content.lower().split())
            overlap = len(query_words & entry_words)
            topic_match = 1 if entry.topic == self.current_topic else 0
            score = overlap + topic_match * 2 + entry.importance

            if score > 0:
                results.append((score, entry))

        results.sort(key=lambda x: x[0], reverse=True)
        return [entry for _, entry in results[:top_k]]

    def get_long_term_context(self, query: str = "", max_tokens: int = 400) -> str:
        """Get L4 long-term memory relevant to query."""
        if not self.long_term:
            return ""

        entries = self.search_long_term(query, top_k=5) if query else self.long_term[-5:]
        lines = ["LONG-TERM MEMORY:"]
        total = 0
        for entry in entries:
            tokens = entry.tokens
            if total + tokens > max_tokens:
                break
            lines.append(f"  [{entry.topic}] {entry.content[:150]}")
            total += tokens

        return '\n'.join(lines) if len(lines) > 1 else ""

    # ================================================================
    # L5: Project Knowledge
    # ================================================================

    def index_project(self, path: str):
        """Index project files for L5."""
        p = Path(path)
        if not p.exists():
            return

        files = 0
        lines = 0
        symbols = 0

        for ext in ['.py', '.js', '.ts', '.go', '.rs', '.java', '.kt', '.sh', '.md']:
            for file in p.rglob(f'*{ext}'):
                parts = file.parts
                if any(d.startswith('.') or d in ('__pycache__', 'node_modules', 'venv', '.git')
                       for d in parts):
                    continue
                try:
                    content = file.read_text(encoding='utf-8', errors='replace')
                    file_lines = content.count('\n') + 1
                    files += 1
                    lines += file_lines

                    # Count symbols
                    for line in content.split('\n'):
                        stripped = line.strip()
                        if stripped.startswith(('def ', 'class ', 'function ', 'func ', 'fn ')):
                            symbols += 1

                    self.project_index[str(file)] = {
                        'lines': file_lines,
                        'size': len(content),
                        'extension': file.suffix,
                        'modified': file.stat().st_mtime,
                    }
                except Exception:
                    pass

        self.project_stats = {'files': files, 'lines': lines, 'symbols': symbols}

    def search_project(self, query: str, top_k: int = 5) -> list:
        """Search project index (L5)."""
        query_lower = query.lower()
        results = []

        for path, meta in self.project_index.items():
            score = 0
            # Filename match
            if query_lower in Path(path).name.lower():
                score += 5
            # Extension relevance
            if meta['extension'] == '.py' and 'python' in query_lower:
                score += 2

            if score > 0:
                results.append((score, path, meta))

        results.sort(key=lambda x: x[0], reverse=True)
        return [(path, meta) for _, path, meta in results[:top_k]]

    def get_project_context(self, max_tokens: int = 300) -> str:
        """Get L5 project knowledge."""
        if not self.project_index:
            return ""

        lines = [f"PROJECT: {self.project_stats['files']} files, {self.project_stats['lines']} lines, {self.project_stats['symbols']} symbols"]
        # Show key files
        key_files = sorted(self.project_index.items(),
                          key=lambda x: x[1]['lines'], reverse=True)[:5]
        for path, meta in key_files:
            lines.append(f"  {Path(path).name}: {meta['lines']} lines")

        return '\n'.join(lines)[:max_tokens]

    # ================================================================
    # L6: Archive
    # ================================================================

    def archive_conversation(self, summary: str, topic: str, key_facts: list):
        """Archive a completed conversation (L6)."""
        entry = {
            'summary': summary,
            'topic': topic,
            'key_facts': key_facts,
            'timestamp': time.time(),
            'tokens': len(summary.split()) + sum(len(f.split()) for f in key_facts),
        }
        self.archive.append(entry)

        if len(self.archive) > self.archive_limit:
            self.archive = self.archive[-self.archive_limit:]

    def search_archive(self, query: str, top_k: int = 3) -> list:
        """Search archived conversations (L6)."""
        query_words = set(query.lower().split())
        results = []

        for entry in self.archive:
            words = set((entry['summary'] + ' ' + entry['topic']).lower().split())
            overlap = len(query_words & words)
            if overlap > 0:
                results.append((overlap, entry))

        results.sort(key=lambda x: x[0], reverse=True)
        return [entry for _, entry in results[:top_k]]

    # ================================================================
    # Context Assembly (all levels)
    # ================================================================

    def build_context(self, query: str = "", max_tokens: int = 2000) -> str:
        """Build hierarchical context from all memory levels.

        Priority:
            L0 (current message) - always include
            L1 (recent turns) - include if within budget
            L3 (topic memory) - include relevant topics
            L4 (long-term) - retrieve relevant
            L5 (project) - include if coding task
            L2 (summary) - include if budget allows
            L6 (archive) - only if specifically relevant
        """
        parts = []
        total = 0

        # L0: Current message (always first)
        if self.current_message:
            parts.append(f"USER: {self.current_message}")
            total += len(self.current_message.split())

        # L1: Recent turns
        recent = self.get_recent_context(max_tokens=max_tokens // 3)
        if recent:
            parts.append(recent)
            total += len(recent.split())

        # L3: Topic memory
        topic_ctx = self.get_topic_context(max_tokens=max_tokens // 4)
        if topic_ctx:
            parts.append(topic_ctx)
            total += len(topic_ctx.split())

        # L4: Long-term memory
        lt_ctx = self.get_long_term_context(query, max_tokens=max_tokens // 4)
        if lt_ctx:
            parts.append(lt_ctx)
            total += len(lt_ctx.split())

        # L5: Project knowledge (if coding task)
        if any(w in (query or '').lower() for w in
               ['code', 'file', 'function', 'class', 'error', 'fix', 'edit', 'read']):
            proj_ctx = self.get_project_context(max_tokens=max_tokens // 5)
            if proj_ctx:
                parts.append(proj_ctx)
                total += len(proj_ctx.split())

        # L2: Summary (if budget allows)
        if total < max_tokens * 0.6:
            summary_ctx = self.get_summary_context(max_tokens=max_tokens // 5)
            if summary_ctx:
                parts.append(summary_ctx)
                total += len(summary_ctx.split())

        # L6: Archive (only if specifically relevant)
        if any(w in (query or '').lower() for w in ['before', 'earlier', 'previously', 'last time']):
            archive_results = self.search_archive(query, top_k=2)
            if archive_results:
                archive_lines = ["ARCHIVED CONVERSATIONS:"]
                for entry in archive_results:
                    archive_lines.append(f"  [{entry['topic']}] {entry['summary'][:100]}")
                archive_text = '\n'.join(archive_lines)
                parts.append(archive_text)
                total += len(archive_text.split())

        return '\n\n'.join(parts)

    # ================================================================
    # Stats
    # ================================================================

    def get_stats(self) -> dict:
        return {
            'total_tokens_stored': self.total_tokens_stored,
            'total_tokens_compressed': self.total_tokens_compressed,
            'compression_ratio': self.total_tokens_compressed / max(self.total_tokens_stored, 1),
            'recent_turns': len(self.recent_turns),
            'topics': len(self.topic_memories),
            'long_term_entries': len(self.long_term),
            'project_files': len(self.project_index),
            'archive_entries': len(self.archive),
            'summary_turns': self.summary_turn_count,
        }

    # ================================================================
    # Persistence
    # ================================================================

    def _save(self):
        """Save memory state to disk."""
        state = {
            'conversation_summary': self.conversation_summary,
            'summary_turn_count': self.summary_turn_count,
            'topic_memories': {k: v.to_dict() for k, v in self.topic_memories.items()},
            'long_term': [e.to_dict() for e in self.long_term[-100:]],
            'project_stats': self.project_stats,
            'archive': self.archive[-50:],
            'total_tokens_stored': self.total_tokens_stored,
            'total_tokens_compressed': self.total_tokens_compressed,
        }
        path = self.data_dir / 'hierarchical_memory.json'
        with open(path, 'w') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

    def _load(self):
        """Load memory state from disk."""
        path = self.data_dir / 'hierarchical_memory.json'
        if not path.exists():
            return
        try:
            with open(path) as f:
                state = json.load(f)
            self.conversation_summary = state.get('conversation_summary', '')
            self.summary_turn_count = state.get('summary_turn_count', 0)
            self.project_stats = state.get('project_stats', self.project_stats)
            self.archive = state.get('archive', [])
            self.total_tokens_stored = state.get('total_tokens_stored', 0)
            self.total_tokens_compressed = state.get('total_tokens_compressed', 0)

            for topic, data in state.get('topic_memories', {}).items():
                self.topic_memories[topic] = TopicMemory(**data)

            for entry_data in state.get('long_term', []):
                self.long_term.append(MemoryEntry(**entry_data))
        except Exception:
            pass
