"""DikaAI Validator - Checks response quality before sending.

Checks: correctness, relevance, safety, format, repetition, topic drift.
"""

import re
from core.context import ConversationState, TOPIC_KEYWORDS


class ValidationResult:
    def __init__(self):
        self.passed = True
        self.checks = {}
        self.issues = []
        self.should_regenerate = False
        self.regenerate_reason = ""

    def fail(self, check: str, reason: str):
        self.checks[check] = False
        self.issues.append(f"{check}: {reason}")
        self.passed = False
        self.should_regenerate = True
        self.regenerate_reason = reason

    def pass_check(self, check: str):
        self.checks[check] = True

    def to_dict(self):
        return {
            'passed': self.passed,
            'checks': self.checks,
            'issues': self.issues,
            'should_regenerate': self.should_regenerate,
            'reason': self.regenerate_reason,
        }


class Validator:
    """Validates AI responses before sending to user."""

    def __init__(self):
        self.min_response_length = 3
        self.max_response_length = 5000
        self.max_repetition_ratio = 0.4

    def validate(self, response: str, user_message: str,
                 state: ConversationState = None, context: dict = None) -> ValidationResult:
        """Run all validation checks."""
        result = ValidationResult()

        # 1. Basic checks
        self._check_length(response, result)

        # 2. Relevance check
        self._check_relevance(response, user_message, result)

        # 3. Topic consistency
        if state:
            self._check_topic(response, state, result)

        # 4. Repetition check
        self._check_repetition(response, result)

        # 5. Safety check
        self._check_safety(response, result)

        # 6. Format check
        self._check_format(response, user_message, result)

        # 7. Code validity (if code response)
        if self._contains_code(response):
            self._check_code(response, result)

        return result

    def _check_length(self, response: str, result: ValidationResult):
        """Check response length."""
        if len(response) < self.min_response_length:
            result.fail('length', 'Response too short')
            return
        if len(response) > self.max_response_length:
            result.fail('length', 'Response too long')
            return
        result.pass_check('length')

    def _check_relevance(self, response: str, user_message: str, result: ValidationResult):
        """Check if response is relevant to user message."""
        user_words = set(user_message.lower().split())
        response_words = set(response.lower().split())

        # Check for unrelated topics
        if len(user_words) > 3:
            overlap = len(user_words & response_words)
            # Very low overlap might mean off-topic
            if overlap == 0 and len(response) > 100:
                result.fail('relevance', 'Response may be off-topic')
                return
        result.pass_check('relevance')

    def _check_topic(self, response: str, state: ConversationState, result: ValidationResult):
        """Check topic consistency."""
        if not state.current_topic:
            result.pass_check('topic')
            return

        topic_keywords = TOPIC_KEYWORDS.get(state.current_topic, [])
        if not topic_keywords:
            result.pass_check('topic')
            return

        response_lower = response.lower()

        # Check for topic drift
        for other_topic, keywords in TOPIC_KEYWORDS.items():
            if other_topic != state.current_topic:
                drift = sum(1 for kw in keywords if kw in response_lower)
                if drift >= 3:
                    result.fail('topic', f'Topic drift to {other_topic}')
                    return

        result.pass_check('topic')

    def _check_repetition(self, response: str, result: ValidationResult):
        """Check for excessive repetition."""
        words = response.split()
        if len(words) < 5:
            result.pass_check('repetition')
            return

        # Check word repetition
        unique_ratio = len(set(words)) / len(words)
        if unique_ratio < (1 - self.max_repetition_ratio):
            result.fail('repetition', f'Too repetitive ({unique_ratio:.0%} unique)')
            return

        # Check phrase repetition
        phrases = []
        for i in range(len(words) - 2):
            phrase = ' '.join(words[i:i+3])
            phrases.append(phrase)

        if phrases:
            phrase_ratio = len(set(phrases)) / len(phrases)
            if phrase_ratio < 0.5:
                result.fail('repetition', 'Phrase repetition detected')
                return

        result.pass_check('repetition')

    def _check_safety(self, response: str, result: ValidationResult):
        """Check for unsafe content."""
        unsafe_patterns = [
            r'rm\s+-rf\s+/',
            r'mkfs',
            r'dd\s+if=',
            r'curl.*\|\s*sh',
            r'wget.*\|\s*bash',
            r'eval\s*\(',
            r'exec\s*\(',
            r'__import__',
            r'os\.system',
            r'subprocess\.call.*shell=True',
        ]

        for pattern in unsafe_patterns:
            if re.search(pattern, response):
                result.fail('safety', f'Unsafe pattern detected: {pattern[:30]}')
                return

        result.pass_check('safety')

    def _check_format(self, response: str, user_message: str, result: ValidationResult):
        """Check response format."""
        # Check for unclosed code blocks
        code_blocks = response.count('```')
        if code_blocks % 2 != 0:
            result.fail('format', 'Unclosed code block')
            return

        # Check for unclosed brackets
        opens = sum(1 for c in response if c in '([{')
        closes = sum(1 for c in response if c in ')]}')
        if opens > closes + 3:
            result.fail('format', 'Too many unclosed brackets')
            return

        result.pass_check('format')

    def _contains_code(self, response: str) -> bool:
        """Check if response contains code."""
        return '```' in response or ('def ' in response) or ('function ' in response)

    def _check_code(self, response: str, result: ValidationResult):
        """Check code validity."""
        # Extract code blocks
        code_blocks = re.findall(r'```[\w]*\n(.*?)```', response, re.DOTALL)

        for code in code_blocks:
            # Check Python syntax
            if 'def ' in code or 'import ' in code:
                try:
                    compile(code, '<string>', 'exec')
                except SyntaxError as e:
                    result.fail('code_syntax', f'Syntax error: {e.msg}')
                    return

        result.pass_check('code_syntax')
