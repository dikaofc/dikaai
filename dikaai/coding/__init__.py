"""
DikaAI Coding - Quality control and smart replies.

Components:
    Validator      - Checks response quality (correctness, relevance, safety)
    Observer       - Tracks execution output, errors, performance
    get_smart_reply - Pattern-based Indonesian replies with fallback
"""

from dikaai.coding.validator import Validator, ValidationResult
from dikaai.coding.observer import Observer, Observation
from dikaai.coding.smart_reply import get_smart_reply

__all__ = [
    'Validator',
    'ValidationResult',
    'Observer',
    'Observation',
    'get_smart_reply',
]
