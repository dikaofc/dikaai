"""
DikaAI RAG - Knowledge retrieval via vector search.

Components:
    Retriever  - Searches knowledge base and provides context to LLM
    VectorDB   - Simple in-memory vector database
    embed_text - Pure Python text embeddings (TF-sign hashing)
"""

from dikaai.rag.retriever import Retriever
from dikaai.rag.vector_db import VectorDB
from dikaai.rag.embeddings import embed_text, cosine_similarity
from dikaai.rag.reranker import Reranker

__all__ = [
    'Retriever',
    'VectorDB',
    'embed_text',
    'cosine_similarity',
    'Reranker',
]
