"""
DikaAI Reasoning Engine - Handles complex analysis and explanation tasks.

Reasoning types:
    explanation  - "apa itu X?"
    comparison   - "X vs Y"
    analysis     - "kenapa X terjadi?"
    planning     - "gimana cara X?"
    debugging    - "kenapa error ini?"
    architecture - "gimana design systemnya?"
"""

import re
import time
from dataclasses import dataclass, field


@dataclass
class ReasoningChain:
    """A chain of reasoning steps."""
    question: str
    steps: list = field(default_factory=list)
    conclusion: str = ""
    confidence: float = 0.0
    sources: list = field(default_factory=list)

    def to_text(self) -> str:
        lines = [f"QUESTION: {self.question}"]
        for i, step in enumerate(self.steps, 1):
            lines.append(f"  Step {i}: {step}")
        if self.conclusion:
            lines.append(f"CONCLUSION: {self.conclusion}")
        return '\n'.join(lines)


class ReasoningEngine:
    """Handles complex reasoning tasks."""

    def __init__(self):
        self.patterns = {
            'explanation': [
                r'apa itu (.+)',
                r'jelaskan (.+)',
                r'what is (.+)',
                r'explain (.+)',
                r'meaning of (.+)',
            ],
            'comparison': [
                r'(.+) vs (.+)',
                r'(.+) atau (.+)',
                r'(.+) or (.+)',
                r'perbandingan (.+)',
                r'compare (.+)',
            ],
            'analysis': [
                r'kenapa (.+)',
                r'mengapa (.+)',
                r'why (.+)',
                r'cause of (.+)',
                r'alasan (.+)',
            ],
            'planning': [
                r'gimana cara (.+)',
                r'bagaimana (.+)',
                r'how to (.+)',
                r'how can (.+)',
                r'cara (.+)',
            ],
            'debugging': [
                r'error (.+)',
                r'bug (.+)',
                r'fix (.+)',
                r'kesalahan (.+)',
                r'troubleshoot (.+)',
            ],
        }

    def classify(self, message: str) -> str:
        """Classify the reasoning type."""
        text = message.lower()
        for rtype, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    return rtype
        return 'general'

    def reason(self, question: str, context: str = "",
               memory_context: str = "", project_context: str = "") -> ReasoningChain:
        """Perform reasoning on a question.

        Args:
            question: The question to reason about
            context: Conversation context
            memory_context: Relevant memory
            project_context: Project knowledge

        Returns:
            ReasoningChain with steps and conclusion
        """
        chain = ReasoningChain(question=question)
        rtype = self.classify(question)

        # Build reasoning steps based on type
        if rtype == 'explanation':
            chain.steps = self._explain(question, context, memory_context)
        elif rtype == 'comparison':
            chain.steps = self._compare(question, context)
        elif rtype == 'analysis':
            chain.steps = self._analyze(question, context, memory_context)
        elif rtype == 'planning':
            chain.steps = self._plan(question, context, project_context)
        elif rtype == 'debugging':
            chain.steps = self._debug(question, context, memory_context)
        else:
            chain.steps = self._general(question, context)

        # Synthesize conclusion
        chain.conclusion = self._synthesize(chain.steps, question)
        chain.confidence = min(1.0, len(chain.steps) * 0.2)

        return chain

    def _explain(self, question: str, context: str, memory: str) -> list:
        steps = []
        # Extract subject
        subject = self._extract_subject(question)
        if subject:
            steps.append(f"Identifying concept: {subject}")
            if memory and subject.lower() in memory.lower():
                steps.append(f"Found relevant information in memory")
            steps.append(f"Analyzing definition and properties")
            steps.append(f"Considering related concepts")
        return steps

    def _compare(self, question: str, context: str) -> list:
        items = self._extract_comparison_items(question)
        steps = [f"Identifying items to compare: {', '.join(items)}"]
        for item in items:
            steps.append(f"Analyzing {item}: characteristics, pros, cons")
        steps.append("Finding similarities and differences")
        steps.append("Determining use cases for each")
        return steps

    def _analyze(self, question: str, context: str, memory: str) -> list:
        subject = self._extract_subject(question)
        steps = [
            f"Identifying cause of: {subject or question}",
            "Examining contributing factors",
            "Tracing root cause",
            "Evaluating impact",
        ]
        if memory:
            steps.append("Checking past experiences for similar issues")
        return steps

    def _plan(self, question: str, context: str, project: str) -> list:
        steps = [
            "Understanding the goal",
            "Identifying required resources",
            "Breaking into actionable steps",
            "Ordering by dependency",
            "Estimating complexity",
        ]
        if project:
            steps.append("Checking existing project structure")
        return steps

    def _debug(self, question: str, context: str, memory: str) -> list:
        steps = [
            "Reading error message",
            "Identifying error type",
            "Locating source of error",
        ]
        if memory:
            steps.append("Checking memory for similar past errors")
        steps.extend([
            "Formulating fix hypothesis",
            "Applying fix",
            "Verifying fix works",
        ])
        return steps

    def _general(self, question: str, context: str) -> list:
        return [
            "Understanding the question",
            "Gathering relevant information",
            "Analyzing available data",
            "Formulating response",
        ]

    def _extract_subject(self, question: str) -> str:
        for pattern in [r'apa itu (.+?)[?.]', r'jelaskan (.+?)[?.]',
                       r'explain (.+?)[?.]', r'what is (.+?)[?.]']:
            match = re.search(pattern, question, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return question

    def _extract_comparison_items(self, question: str) -> list:
        for pattern in [r'(.+?)\s+vs\s+(.+?)[?.]', r'(.+?)\s+atau\s+(.+?)[?.]',
                       r'compare\s+(.+?)(?:\s+and\s+|\s*,\s*)(.+?)[?.]']:
            match = re.search(pattern, question, re.IGNORECASE)
            if match:
                return [match.group(1).strip(), match.group(2).strip()]
        return [question]

    def _synthesize(self, steps: list, question: str) -> str:
        if not steps:
            return "Insufficient information to conclude."
        return f"Based on {len(steps)} analysis steps, here is the reasoning about: {question[:80]}"
