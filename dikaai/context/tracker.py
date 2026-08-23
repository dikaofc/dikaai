"""DikaAI Context Tracker - Topic tracking, anti-drift, hierarchical context."""

import re
import time
from collections import defaultdict


class ConversationState:
    """Tracks conversation state."""
    def __init__(self):
        self.current_topic = ""
        self.subtopic = ""
        self.goal = ""
        self.entities = []
        self.decisions = []
        self.recent_turns = []
        self.turn_count = 0

    def update(self, message: str, response: str = ""):
        self.turn_count += 1
        self.recent_turns.append({'role': 'user', 'content': message, 'time': time.time()})
        if response:
            self.recent_turns.append({'role': 'assistant', 'content': response, 'time': time.time()})
        if len(self.recent_turns) > 20:
            self.recent_turns = self.recent_turns[-20:]

    def set_topic(self, topic: str, subtopic: str = ""):
        self.current_topic = topic
        if subtopic:
            self.subtopic = subtopic

    def add_entity(self, entity: str):
        if entity not in self.entities:
            self.entities.append(entity)
            if len(self.entities) > 10:
                self.entities = self.entities[-10:]

    def to_dict(self):
        return {
            'topic': self.current_topic, 'subtopic': self.subtopic,
            'goal': self.goal, 'entities': self.entities[-5:],
            'turns': self.turn_count,
        }

    def to_context_string(self):
        lines = []
        if self.current_topic: lines.append(f"TOPIC: {self.current_topic}")
        if self.subtopic: lines.append(f"SUBTOPIC: {self.subtopic}")
        if self.entities: lines.append(f"ENTITIES: {', '.join(self.entities[-5:])}")
        return '\n'.join(lines)


TOPIC_KEYWORDS = {
    'coding': ['code', 'kode', 'python', 'javascript', 'error', 'bug', 'fix', 'function', 'class', 'run', 'test'],
    'context': ['context', 'memory', 'topic', 'conversation', 'percakapan'],
    'architecture': ['arsitektur', 'architecture', 'design', 'system', 'sistem'],
    'tools': ['git', 'terminal', 'install', 'docker', 'npm', 'pip'],
    'rag': ['rag', 'retrieval', 'vector', 'embedding', 'search'],
    'training': ['training', 'model', 'dataset', 'epoch', 'loss', 'fine-tune'],
}

REFERENCE_WORDS = ['lanjut', 'terus', 'nah', 'gimana', 'yang tadi', 'sebelumnya', 'tadi', 'yg tadi']


class IntentResolver:
    def is_reference(self, message: str) -> bool:
        return any(ref in message.lower() for ref in REFERENCE_WORDS)

    def resolve(self, message: str, state: ConversationState) -> dict:
        last = ""
        for turn in reversed(state.recent_turns):
            if turn['role'] == 'assistant':
                last = turn['content'][:100]
                break
        if any(w in message.lower() for w in ['lanjut', 'terus', 'yg tadi', 'yang tadi']):
            return {'resolved': True, 'intent': 'continue', 'context': f'Lanjutkan {state.current_topic}'}
        if any(w in message.lower() for w in ['gimana', 'nah gimana']):
            return {'resolved': True, 'intent': 'ask_progress', 'context': f'Progress {state.current_topic}'}
        return {'resolved': False, 'intent': 'general', 'context': message}


class TopicTracker:
    def detect(self, message: str, state: ConversationState = None) -> dict:
        text = message.lower()
        scores = {}
        for topic, kws in TOPIC_KEYWORDS.items():
            score = sum(1 for kw in kws if kw in text)
            if score > 0: scores[topic] = score
        if not scores:
            if state and state.current_topic:
                return {'topic': state.current_topic, 'confidence': 0.5, 'is_new': False}
            return {'topic': 'general', 'confidence': 0.3, 'is_new': False}
        best = max(scores, key=scores.get)
        is_new = not (state and state.current_topic == best)
        return {'topic': best, 'confidence': min(1.0, scores[best] / 3.0), 'is_new': is_new}


class ContextManager:
    """Full context management pipeline."""
    def __init__(self):
        self.state = ConversationState()
        self.topic_tracker = TopicTracker()
        self.intent_resolver = IntentResolver()

    def process_message(self, message: str) -> dict:
        if self.intent_resolver.is_reference(message):
            intent = self.intent_resolver.resolve(message, self.state)
        else:
            intent = {'resolved': False, 'intent': 'general', 'context': message}
        topic = self.topic_tracker.detect(message, self.state)
        if topic['is_new'] or topic['confidence'] > 0.5:
            self.state.set_topic(topic['topic'])
        self.state.add_entity(topic['topic'])
        return {'intent': intent, 'topic': topic, 'state': self.state}

    def update_after_response(self, message: str, response: str):
        self.state.update(message, response)

    def build_context(self, message: str, memory: str = "", project: str = "") -> str:
        parts = [f"USER: {message}"]
        if self.state.to_context_string():
            parts.append(f"STATE:\n{self.state.to_context_string()}")
        if memory:
            parts.append(f"MEMORY:\n{memory[:500]}")
        if project:
            parts.append(f"PROJECT:\n{project[:500]}")
        return '\n\n'.join(parts)
