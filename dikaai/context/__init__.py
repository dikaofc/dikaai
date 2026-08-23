"""
DikaAI Context - Topic tracking, anti-drift, and hierarchical context management.

Components:
    ContextManager    - Full context management pipeline
    ConversationState - Tracks topic, entities, decisions, recent turns
    TopicTracker      - Detects topic changes and maintains focus
    IntentResolver    - Resolves vague references ("lanjut yang tadi")
"""

from dikaai.context.tracker import (
    ContextManager,
    ConversationState,
    TopicTracker,
    IntentResolver,
    TOPIC_KEYWORDS,
    REFERENCE_WORDS,
)
from dikaai.context.compressor import ContextCompressor, CompressedContext
from dikaai.context.long_context import LongContextManager

__all__ = [
    'ContextManager',
    'ConversationState',
    'TopicTracker',
    'IntentResolver',
    'TOPIC_KEYWORDS',
    'REFERENCE_WORDS',
    'ContextCompressor',
    'CompressedContext',
    'LongContextManager',
]
