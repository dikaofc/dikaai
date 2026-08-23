"""
DikaAI Context Compressor - Compress long conversations into structured summaries.

Strategy:
    Raw conversation (800K tokens)
        ↓
    Extract: topics, decisions, facts, entities
        ↓
    Compress per-topic
        ↓
    Structured summary (50K tokens)
        ↓
    Hot/Warm/Cold storage
"""

import re
import time
from dataclasses import dataclass, field


@dataclass
class CompressedContext:
    """Compressed version of a conversation segment."""
    topics: list = field(default_factory=list)
    decisions: list = field(default_factory=list)
    facts: list = field(default_factory=list)
    entities: list = field(default_factory=list)
    unresolved: list = field(default_factory=list)
    summary: str = ""
    token_count: int = 0
    original_tokens: int = 0
    compression_ratio: float = 0.0

    def to_text(self) -> str:
        """Convert to text for context injection."""
        parts = []
        if self.summary:
            parts.append(f"SUMMARY: {self.summary}")
        if self.topics:
            parts.append(f"TOPICS: {', '.join(self.topics)}")
        if self.decisions:
            parts.append(f"DECISIONS: {'; '.join(self.decisions[-5:])}")
        if self.facts:
            parts.append(f"FACTS: {'; '.join(self.facts[-10:])}")
        if self.entities:
            parts.append(f"ENTITIES: {', '.join(self.entities[-10:])}")
        if self.unresolved:
            parts.append(f"UNRESOLVED: {'; '.join(self.unresolved[-5:])}")
        return '\n'.join(parts)


class ContextCompressor:
    """Compresses long conversations into structured summaries."""

    def __init__(self):
        # Indonesian stop words for keyword extraction
        self.stop_words = {
            'yang', 'dan', 'ini', 'itu', 'untuk', 'dengan', 'tidak', 'ada',
            'bisa', 'saya', 'kamu', 'dia', 'mereka', 'akan', 'sudah',
            'belum', 'lagi', 'mau', 'halo', 'kabar', 'apa', 'siapa',
            'kenapa', 'gimana', 'kapan', 'dimana', 'sih', 'dong', 'nih',
            'deh', 'lah', 'kok', 'aja', 'banget', 'mantap', 'sip', 'oke',
            'ya', 'yg', 'udah', 'bisa', 'juga', 'kalau', 'kalo', 'jadi',
            'gitu', 'gini', 'kayak', 'seperti', 'itu', 'sama', 'dari',
            'pada', 'dalam', 'atas', 'bawah', 'sini', 'situ', 'sono',
        }

    def compress(self, turns: list, max_tokens: int = 500) -> CompressedContext:
        """Compress a list of conversation turns into structured summary.

        Args:
            turns: List of {'role': str, 'content': str, 'topic': str}
            max_tokens: Target token count for compressed output

        Returns:
            CompressedContext with extracted information
        """
        result = CompressedContext()
        result.original_tokens = sum(len(t.get('content', '').split()) for t in turns)

        if not turns:
            return result

        # 1. Extract topics
        result.topics = self._extract_topics(turns)

        # 2. Extract decisions (sentences with decision keywords)
        result.decisions = self._extract_decisions(turns)

        # 3. Extract key facts (important statements)
        result.facts = self._extract_facts(turns)

        # 4. Extract entities (names, files, concepts)
        result.entities = self._extract_entities(turns)

        # 5. Find unresolved questions
        result.unresolved = self._extract_unresolved(turns)

        # 6. Build summary
        result.summary = self._build_summary(turns, result)

        # Calculate compression
        result.token_count = len(result.to_text().split())
        if result.original_tokens > 0:
            result.compression_ratio = result.token_count / result.original_tokens

        return result

    def _extract_topics(self, turns: list) -> list:
        """Extract main topics from conversation."""
        topic_counts = {}
        for turn in turns:
            topic = turn.get('topic', '')
            if topic:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1
            else:
                # Extract topic from content
                words = set(turn.get('content', '').lower().split())
                words -= self.stop_words
                for word in words:
                    if len(word) > 3:
                        topic_counts[word] = topic_counts.get(word, 0) + 1

        # Return top topics
        sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
        return [topic for topic, count in sorted_topics[:10] if count >= 2]

    def _extract_decisions(self, turns: list) -> list:
        """Extract decisions made in conversation."""
        decision_keywords = [
            'decided', 'agreed', 'chosen', 'selected', 'will use',
            'using', 'going with', 'final', 'settled',
            'memutuskan', 'setuju', 'pilih', 'pakai', 'gunakan',
            'final', 'udah fix', 'udah decided', 'oke gas',
        ]
        decisions = []
        for turn in turns:
            content = turn.get('content', '')
            content_lower = content.lower()
            for kw in decision_keywords:
                if kw in content_lower:
                    # Extract the sentence containing the decision
                    sentences = re.split(r'[.!?\n]', content)
                    for sent in sentences:
                        if kw in sent.lower() and len(sent.strip()) > 10:
                            decisions.append(sent.strip()[:150])
                            break
                    break

        return decisions[-10:]  # Keep last 10

    def _extract_facts(self, turns: list) -> list:
        """Extract key facts from conversation."""
        fact_patterns = [
            r'(?:the|ini|itu)\s+(.+?)\s+(?:is|adalah|merupakan)\s+(.+?)[.!]',
            r'(?:we|kita|kami)\s+(?:need|butuh|harus)\s+(.+?)[.!]',
            r'(?:the|file|function|class)\s+(.+?)\s+(?:was|telah|sudah)\s+(.+?)[.!]',
        ]
        facts = []
        for turn in turns:
            content = turn.get('content', '')
            for pattern in fact_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    fact = ' '.join(match).strip()
                    if len(fact) > 10 and fact not in facts:
                        facts.append(fact[:150])

        return facts[-15:]  # Keep last 15

    def _extract_entities(self, turns: list) -> list:
        """Extract named entities (files, classes, functions, names)."""
        entities = set()

        for turn in turns:
            content = turn.get('content', '')

            # File names
            files = re.findall(r'\b[\w/]+\.(?:py|js|ts|go|rs|java|kt|sh|md)\b', content)
            entities.update(files)

            # Class names (PascalCase)
            classes = re.findall(r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b', content)
            entities.update(classes[:3])

            # Function names
            funcs = re.findall(r'\b(?:def|function|func)\s+(\w+)', content)
            entities.update(funcs[:3])

            # Technical terms
            tech_terms = re.findall(r'\b(?:Python|JavaScript|React|Docker|Git|Redis|SQLite|Vercel|API|REST|GraphQL)\b', content)
            entities.update(tech_terms[:3])

        return list(entities)[:15]

    def _extract_unresolved(self, turns: list) -> list:
        """Extract unresolved questions."""
        question_patterns = [
            r'(?:how|gimana|bagaimana)\s+(?:do|to|can)\s+(.+?)\?',
            r'(?:why|kenapa|kenp)\s+(.+?)\?',
            r'(?:what|apa)\s+(?:is|are|does)\s+(.+?)\?',
            r'\?$',
        ]
        unresolved = []
        for turn in turns:
            if turn.get('role') == 'user':
                content = turn.get('content', '')
                if '?' in content or any(kw in content.lower() for kw in ['gimana', 'kenapa', 'apa itu', 'how', 'why']):
                    # Check if it was answered
                    content_lower = content.lower()
                    if not any(kw in content_lower for kw in ['done', 'selesai', 'fixed', 'olved', 'answered']):
                        unresolved.append(content[:150])

        return unresolved[-5:]

    def _build_summary(self, turns: list, extracted: CompressedContext) -> str:
        """Build a concise summary."""
        parts = []

        if extracted.topics:
            parts.append(f"Discussion about {', '.join(extracted.topics[:3])}")

        if extracted.decisions:
            parts.append(f"Decided: {extracted.decisions[-1][:100]}")

        if extracted.facts:
            parts.append(f"Key facts: {'; '.join(extracted.facts[:3])}")

        if extracted.unresolved:
            parts.append(f"Open questions: {len(extracted.unresolved)}")

        turn_count = len(turns)
        if turn_count > 0:
            parts.append(f"({turn_count} turns)")

        return ' | '.join(parts)
