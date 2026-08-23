"""DikaAI Chat - Conversation interface.

Usage:
  chat = DikaAIChat(workspace="/path/to/project")
  response = chat.send("fix error in main.py")
"""

import time
from dikaai.engine import Engine


class DikaAIChat:
    """Chat interface for DikaAI."""

    def __init__(self, workspace: str = None, model=None, tokenizer=None):
        self.engine = Engine(workspace)
        self.model = model
        self.tokenizer = tokenizer
        self.history = []

    def send(self, message: str) -> dict:
        """Send a message and get response."""
        result = self.engine.process(message, self.model, self.tokenizer)
        self.history.append({
            'user': message,
            'assistant': result['response'],
            'route': result['route'],
            'time': result['time'],
            'timestamp': time.time(),
        })
        return result

    def get_history(self, limit: int = 10) -> list:
        return self.history[-limit:]

    def clear(self):
        self.history = []
        self.engine.context.state = __import__('dikaai.context.tracker', fromlist=['ConversationState']).ConversationState()

    def stats(self):
        return self.engine.get_stats()
