"""DikaAI Short-term Memory - Conversation history."""


class ConversationMemory:
    """Stores recent conversation turns."""
    def __init__(self, limit: int = 20):
        self.limit = limit
        self.messages = []

    def add(self, role: str, content: str):
        self.messages.append({'role': role, 'content': content, 'time': __import__('time').time()})
        if len(self.messages) > self.limit:
            self.messages = self.messages[-self.limit:]

    def get_context(self, max_tokens: int = 500) -> str:
        lines = []
        total = 0
        for msg in reversed(self.messages):
            line = f"{msg['role']}: {msg['content'][:200]}"
            total += len(line.split())
            if total > max_tokens: break
            lines.insert(0, line)
        return '\n'.join(lines)

    def get_last(self, n: int = 5):
        return self.messages[-n:]

    def clear(self):
        self.messages = []
