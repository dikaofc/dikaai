"""
DikaAI - Intelligent AI Coding Agent & Chat System

Architecture:
  User → Engine → Context → Memory → RAG → Agent → Model → Validator → Response

Quick Start:
    from dikaai import DikaAIChat
    chat = DikaAIChat()
    result = chat.send("fix error in main.py")

    from dikaai import Engine
    engine = Engine()
    result = engine.process("buat function fibonacci")
"""

__version__ = "3.0.0"
__author__ = "DikaAI"

# Core engine
from dikaai.engine import Engine
from dikaai.chat import DikaAIChat

# Model
from dikaai.model.model import DikaModel
from dikaai.model.tokenizer import DikaTokenizer
from dikaai.model.trainer import DikaTrainer

# Context & Memory
from dikaai.context.tracker import ContextManager, ConversationState
from dikaai.memory.short_term import ConversationMemory
from dikaai.memory.coding_memory import CodingMemory

# RAG
from dikaai.rag.retriever import Retriever
from dikaai.rag.vector_db import VectorDB

# Agent
from dikaai.agent.planner import Planner
from dikaai.agent.executor import Executor

# Tools
from dikaai.tools.filesystem import FilesystemTools
from dikaai.tools.terminal import TerminalTools
from dikaai.tools.git_tools import GitTools

# Coding
from dikaai.coding.validator import Validator
from dikaai.coding.observer import Observer
from dikaai.coding.smart_reply import get_smart_reply

# Database
from dikaai.database import DikaDB

__all__ = [
    # Engine
    'Engine',
    'DikaAIChat',
    # Model
    'DikaModel',
    'DikaTokenizer',
    'DikaTrainer',
    # Context & Memory
    'ContextManager',
    'ConversationState',
    'ConversationMemory',
    'CodingMemory',
    # RAG
    'Retriever',
    'VectorDB',
    # Agent
    'Planner',
    'Executor',
    # Tools
    'FilesystemTools',
    'TerminalTools',
    'GitTools',
    # Coding
    'Validator',
    'Observer',
    'get_smart_reply',
    # Database
    'DikaDB',
]
