"""DikaAI Context Management System.

Solves: "panjang context tapi makin goblok"

Architecture:
  Message → Intent Resolver → Topic Tracker → Memory Retriever
  → Context Builder (L0-L5) → LLM → Response Validator → Send/Regenerate
"""

import re
import time
import json
from collections import defaultdict
from pathlib import Path
from core.config import DATA_DIR, MEMORY


# ============================================================
# Conversation State
# ============================================================

class ConversationState:
    """Tracks everything about the current conversation."""

    def __init__(self):
        self.current_topic = ""
        self.subtopic = ""
        self.goal = ""
        self.entities = []
        self.decisions = []
        self.unresolved = []
        self.recent_turns = []
        self.summary = ""
        self.last_user_intent = ""
        self.status = "active"
        self.turn_count = 0
        self.last_anchor_time = time.time()
        self.anchor_interval = 10  # Save anchor every N turns

    def update(self, user_message: str, assistant_response: str = ""):
        """Update state with new turn."""
        self.turn_count += 1
        self.recent_turns.append({
            'role': 'user',
            'content': user_message,
            'time': time.time(),
        })
        if assistant_response:
            self.recent_turns.append({
                'role': 'assistant',
                'content': assistant_response,
                'time': time.time(),
            })

        # Keep only last 10 turns
        if len(self.recent_turns) > 20:
            self.recent_turns = self.recent_turns[-20:]

    def set_topic(self, topic: str, subtopic: str = ""):
        if topic != self.current_topic:
            # Topic changed - archive old topic
            if self.current_topic:
                self._archive_topic()
            self.current_topic = topic
            self.subtopic = subtopic
        elif subtopic:
            self.subtopic = subtopic

    def set_goal(self, goal: str):
        self.goal = goal

    def add_entity(self, entity: str):
        if entity not in self.entities:
            self.entities.append(entity)
            if len(self.entities) > 10:
                self.entities = self.entities[-10:]

    def add_decision(self, decision: str):
        if decision not in self.decisions:
            self.decisions.append(decision)
            if len(self.decisions) > 20:
                self.decisions = self.decisions[-20:]

    def add_unresolved(self, question: str):
        if question not in self.unresolved:
            self.unresolved.append(question)

    def resolve_unresolved(self, question: str):
        if question in self.unresolved:
            self.unresolved.remove(question)

    def _archive_topic(self):
        """Archive current topic before switching."""
        if self.current_topic:
            archive = f"Topic: {self.current_topic}"
            if self.subtopic:
                archive += f" / {self.subtopic}"
            if self.decisions:
                archive += f"\nDecisions: {'; '.join(self.decisions[-3:])}"
            self.summary += f"\n{archive}"

    def get_state(self) -> dict:
        return {
            'current_topic': self.current_topic,
            'subtopic': self.subtopic,
            'goal': self.goal,
            'entities': self.entities,
            'decisions': self.decisions[-5:],
            'unresolved': self.unresolved,
            'recent_turns': self.recent_turns[-6:],
            'summary': self.summary[:500],
            'turn_count': self.turn_count,
            'status': self.status,
        }

    def to_context_string(self) -> str:
        """Convert state to context string for LLM."""
        lines = []
        if self.current_topic:
            lines.append(f"TOPIC: {self.current_topic}")
        if self.subtopic:
            lines.append(f"SUBTOPIC: {self.subtopic}")
        if self.goal:
            lines.append(f"GOAL: {self.goal}")
        if self.entities:
            lines.append(f"ENTITIES: {', '.join(self.entities[-5:])}")
        if self.decisions:
            lines.append(f"DECISIONS: {'; '.join(self.decisions[-3:])}")
        if self.unresolved:
            lines.append(f"UNRESOLVED: {'; '.join(self.unresolved[-3:])}")
        if self.summary:
            lines.append(f"SUMMARY:\n{self.summary[:300]}")
        return '\n'.join(lines)


# ============================================================
# Topic Tracker
# ============================================================

# Topic keywords for classification
TOPIC_KEYWORDS = {
    'dikaai': ['dikaai', 'dika ai', 'dika'],
    'coding': ['code', 'kode', 'coding', 'program', 'python', 'javascript',
               'function', 'class', 'error', 'bug', 'fix', 'debug', 'run'],
    'architecture': ['arsitektur', 'architecture', 'design', 'desain',
                     'structure', 'struktur', 'system', 'sistem'],
    'context': ['context', 'konteks', 'memory', 'memori', 'topic', 'topik',
                'conversation', 'percakapan'],
    'training': ['training', 'model', 'fine-tune', 'dataset', 'learning',
                 'belajar', 'epoch', 'loss'],
    'telegram': ['telegram', 'bot', 'chat', 'reply', 'auto-reply'],
    'database': ['database', 'db', 'sqlite', 'redis', 'sql', 'data'],
    'web': ['web', 'scrape', 'api', 'http', 'rest', 'vercel', 'deploy'],
    'tools': ['tool', 'terminal', 'git', 'filesystem', 'command'],
    'rag': ['rag', 'retrieval', 'vector', 'embedding', 'search'],
    'benchmark': ['benchmark', 'eval', 'score', 'metric', 'test'],
}

# Reference words that need context resolution
REFERENCE_WORDS = [
    'lanjut', 'terus', 'nah', 'gimana', 'kalo', 'kalau',
    'yang tadi', 'sebelumnya', 'tadi', 'itu', 'ini',
    'nah gimana', 'terus gimana', 'lanjut dong',
    'yg tadi', 'yg sebelumnya',
]


class TopicTracker:
    """Tracks conversation topics and detects topic changes."""

    def __init__(self):
        self.topic_history = []

    def detect_topic(self, message: str, state: ConversationState = None) -> dict:
        """Detect topic from message."""
        text_lower = message.lower()
        scores = {}

        for topic, keywords in TOPIC_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[topic] = score

        if not scores:
            # Inherit topic from state
            if state and state.current_topic:
                return {
                    'topic': state.current_topic,
                    'subtopic': state.subtopic,
                    'confidence': 0.5,
                    'is_new_topic': False,
                }
            return {
                'topic': 'general',
                'subtopic': '',
                'confidence': 0.3,
                'is_new_topic': False,
            }

        best_topic = max(scores, key=scores.get)
        confidence = min(1.0, scores[best_topic] / 3.0)

        # Detect subtopic
        subtopic = self._detect_subtopic(text_lower, best_topic)

        # Is this a new topic?
        is_new = True
        if state and state.current_topic == best_topic:
            is_new = False
        elif state and best_topic in state.current_topic.lower():
            is_new = False

        return {
            'topic': best_topic,
            'subtopic': subtopic,
            'confidence': confidence,
            'is_new_topic': is_new,
        }

    def _detect_subtopic(self, text: str, topic: str) -> str:
        """Detect subtopic within a main topic."""
        subtopic_map = {
            'coding': {
                'python': ['python', 'py', 'django', 'flask', 'fastapi'],
                'javascript': ['javascript', 'js', 'node', 'react', 'vue'],
                'debugging': ['error', 'bug', 'fix', 'debug', 'traceback'],
                'creation': ['buat', 'create', 'write', 'tulis', 'generate'],
                'refactoring': ['refactor', 'rewrite', 'optimi', 'clean'],
            },
            'context': {
                'topic_tracking': ['topic', 'topik', 'track'],
                'memory': ['memory', 'memori', 'remember'],
                'compression': ['compress', 'compress', 'summary', 'ringkas'],
                'validation': ['valid', 'check', 'cek', 'drift'],
            },
            'architecture': {
                'system_design': ['system', 'sistem', 'design', 'desain'],
                'data_flow': ['flow', 'pipeline', 'pipeline'],
                'modules': ['module', 'modul', 'component', 'komponen'],
            },
        }

        subs = subtopic_map.get(topic, {})
        for subtopic, keywords in subs.items():
            if any(kw in text for kw in keywords):
                return subtopic
        return ""


# ============================================================
# Intent Resolver
# ============================================================

class IntentResolver:
    """Resolves vague references like 'lanjut yang tadi', 'nah gimana'."""

    def is_reference(self, message: str) -> bool:
        """Check if message is a vague reference."""
        text_lower = message.lower().strip()
        return any(ref in text_lower for ref in REFERENCE_WORDS)

    def resolve(self, message: str, state: ConversationState) -> dict:
        """Resolve vague reference to specific intent."""
        text_lower = message.lower().strip()

        # Get last assistant message for context
        last_assistant = ""
        for turn in reversed(state.recent_turns):
            if turn['role'] == 'assistant':
                last_assistant = turn['content'][:200]
                break

        # Resolve based on reference type
        if any(w in text_lower for w in ['lanjut', 'terus', 'yg tadi', 'yang tadi']):
            return {
                'resolved': True,
                'intent': f'continue_topic',
                'context': f'Lanjutkan pembahasan tentang {state.current_topic}',
                'reference_to': last_assistant[:100] if last_assistant else '',
            }

        if any(w in text_lower for w in ['gimana', 'nah gimana', 'terus gimana']):
            return {
                'resolved': True,
                'intent': 'ask_progress',
                'context': f'Tanya perkembangan tentang {state.current_topic}/{state.subtopic}',
                'reference_to': last_assistant[:100] if last_assistant else '',
            }

        if any(w in text_lower for w in ['tadi', 'sebelumnya']):
            return {
                'resolved': True,
                'intent': 'recall_previous',
                'context': f'Recall pembahasan sebelumnya tentang {state.current_topic}',
                'reference_to': last_assistant[:100] if last_assistant else '',
            }

        # Unresolved - use general context
        return {
            'resolved': False,
            'intent': 'general',
            'context': message,
            'reference_to': '',
        }


# ============================================================
# Context Builder (Hierarchical L0-L5)
# ============================================================

class ContextBuilder:
    """Builds optimized context using hierarchical levels."""

    def __init__(self, max_tokens: int = 2000):
        self.max_tokens = max_tokens

    def build(self, message: str, state: ConversationState,
              memory_context: str = "", project_context: str = "") -> str:
        """Build hierarchical context (L0-L5)."""
        parts = []
        token_budget = self.max_tokens

        # L0: Current message (always include)
        parts.append(f"USER: {message}")
        token_budget -= len(message.split())

        # L1: Recent conversation (last 3 turns)
        recent = self._get_recent_context(state, max_tokens=token_budget // 3)
        if recent:
            parts.append(f"RECENT:\n{recent}")
            token_budget -= len(recent.split())

        # L2: Topic state
        topic_ctx = state.to_context_string()
        if topic_ctx:
            parts.append(f"STATE:\n{topic_ctx}")
            token_budget -= len(topic_ctx.split())

        # L3: Relevant memory
        if memory_context and token_budget > 50:
            mem = memory_context[:token_budget // 3]
            parts.append(f"MEMORY:\n{mem}")
            token_budget -= len(mem.split())

        # L4: Project knowledge
        if project_context and token_budget > 50:
            proj = project_context[:token_budget // 4]
            parts.append(f"PROJECT:\n{proj}")
            token_budget -= len(proj.split())

        # L5: Summary (only if relevant)
        if state.summary and token_budget > 100:
            summary = state.summary[:token_budget // 2]
            parts.append(f"ARCHIVE:\n{summary}")

        return '\n\n'.join(parts)

    def _get_recent_context(self, state: ConversationState, max_tokens: int = 300) -> str:
        """Get recent conversation turns."""
        lines = []
        total = 0
        for turn in reversed(state.recent_turns[-6:]):
            line = f"{turn['role'].upper()}: {turn['content'][:200]}"
            words = len(line.split())
            if total + words > max_tokens:
                break
            lines.insert(0, line)
            total += words
        return '\n'.join(lines)


# ============================================================
# Response Validator
# ============================================================

class ResponseValidator:
    """Checks if response is on-topic and relevant."""

    def validate(self, response: str, message: str, state: ConversationState) -> dict:
        """Validate response against topic and intent."""
        result = {
            'same_topic': True,
            'answers_question': True,
            'introduces_unrelated': False,
            'confidence': 1.0,
            'should_regenerate': False,
        }

        if not response or not state.current_topic:
            return result

        response_lower = response.lower()

        # Check topic consistency
        topic_keywords = TOPIC_KEYWORDS.get(state.current_topic, [])
        if topic_keywords:
            topic_relevance = sum(1 for kw in topic_keywords if kw in response_lower)
            if topic_relevance == 0 and len(response) > 50:
                # Response might be off-topic
                result['same_topic'] = False
                result['confidence'] -= 0.3

        # Check for topic drift
        for other_topic, keywords in TOPIC_KEYWORDS.items():
            if other_topic != state.current_topic:
                drift_score = sum(1 for kw in keywords if kw in response_lower)
                if drift_score >= 3:
                    result['introduces_unrelated'] = True
                    result['confidence'] -= 0.2

        # Check if response is too generic
        generic_phrases = ['maaf', 'sorry', 'tidak mengerti', 'bisa dijelaskan',
                          'tidak paham', 'error', 'terjadi kesalahan']
        if any(phrase in response_lower for phrase in generic_phrases):
            result['confidence'] -= 0.1

        # Should regenerate?
        if result['confidence'] < 0.5 or not result['same_topic']:
            result['should_regenerate'] = True

        return result

    def should_save_anchor(self, state: ConversationState) -> bool:
        """Check if we should save a conversation anchor."""
        return (state.turn_count - (state.turn_count % state.anchor_interval)) > 0 and \
               state.turn_count % state.anchor_interval == 0


# ============================================================
# Main Context Manager
# ============================================================

class ContextManager:
    """Full context management pipeline."""

    def __init__(self):
        self.state = ConversationState()
        self.topic_tracker = TopicTracker()
        self.intent_resolver = IntentResolver()
        self.context_builder = ContextBuilder()
        self.validator = ResponseValidator()

    def process_message(self, message: str) -> dict:
        """Process incoming message through full pipeline."""
        # 1. Resolve intent
        if self.intent_resolver.is_reference(message):
            intent = self.intent_resolver.resolve(message, self.state)
        else:
            intent = {'resolved': False, 'intent': 'general', 'context': message}

        # 2. Detect topic
        topic_info = self.topic_tracker.detect_topic(message, self.state)

        # 3. Update state
        if topic_info['is_new_topic'] or topic_info['confidence'] > 0.5:
            self.state.set_topic(topic_info['topic'], topic_info['subtopic'])

        self.state.last_user_intent = intent['intent']
        self.state.add_entity(topic_info['topic'])

        # 4. Check for decisions/keywords
        self._extract_decisions(message)

        return {
            'intent': intent,
            'topic': topic_info,
            'state': self.state,
        }

    def build_context(self, message: str, memory_context: str = "",
                      project_context: str = "") -> str:
        """Build optimized context for LLM."""
        return self.context_builder.build(
            message, self.state, memory_context, project_context
        )

    def validate_response(self, response: str, message: str) -> dict:
        """Validate response before sending."""
        return self.validator.validate(response, message, self.state)

    def update_after_response(self, message: str, response: str):
        """Update state after sending response."""
        self.state.update(message, response)

    def _extract_decisions(self, message: str):
        """Extract decisions from message."""
        decision_patterns = [
            r'(gunakan|pakai|pake|apply|implement|terapkan)\s+(.+)',
            r'(bikin|buat|create|build|develop)\s+(.+)',
            r'(decide|putuskan|pilih|choose|select)\s+(.+)',
        ]
        for pattern in decision_patterns:
            match = re.search(pattern, message.lower())
            if match:
                self.state.add_decision(match.group(0)[:100])
