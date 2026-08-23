"""DikaAI Token Budget - Dynamic context budgeting.

128K available → choose 4-12K most relevant + structured state.

Budget allocation:
  system       5K
  task         3K
  recent       8K
  summary      4K
  memory       5K
  RAG          8K
  tool output 10K
  reserve     85K
"""


class TokenBudget:
    """Manages token budget for context building."""

    def __init__(self, total: int = 4000):
        """Initialize with total token budget."""
        self.total = total
        self.allocated = {
            'system': min(500, total // 8),
            'task': min(300, total // 12),
            'recent': min(800, total // 5),
            'summary': min(400, total // 10),
            'memory': min(500, total // 8),
            'rag': min(800, total // 5),
            'tool_output': min(1000, total // 4),
            'reserve': total,  # Calculated after
        }
        self.used = {k: 0 for k in self.allocated}
        self._calc_reserve()

    def _calc_reserve(self):
        """Calculate reserve budget."""
        used_sum = sum(self.used.values())
        alloc_sum = sum(v for k, v in self.allocated.items() if k != 'reserve')
        self.allocated['reserve'] = self.total - alloc_sum

    def use(self, category: str, tokens: int) -> int:
        """Use tokens from a category. Returns actual tokens used."""
        available = self.allocated.get(category, 0) - self.used.get(category, 0)
        actual = min(tokens, max(available, 0))
        self.used[category] = self.used.get(category, 0) + actual
        return actual

    def available(self, category: str = None) -> int:
        """Get available tokens."""
        if category:
            return self.allocated.get(category, 0) - self.used.get(category, 0)
        return self.total - sum(self.used.values())

    def get_allocation(self) -> dict:
        """Get current allocation summary."""
        return {
            cat: {
                'allocated': self.allocated[cat],
                'used': self.used[cat],
                'available': self.allocated[cat] - self.used[cat],
            }
            for cat in self.allocated
        }

    def scale(self, factor: float):
        """Scale all budgets by a factor."""
        for cat in self.allocated:
            self.allocated[cat] = int(self.allocated[cat] * factor)
        self.total = sum(self.allocated.values())
        self._calc_reserve()

    def __repr__(self):
        used = sum(self.used.values())
        return f"TokenBudget({used}/{self.total} used)"
