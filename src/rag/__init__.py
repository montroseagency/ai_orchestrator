"""
RAG (Retrieval-Augmented Generation) module for self-improving agent architecture.

Provides:
- ChromaDB-based vector storage for sessions, patterns, and lessons
- MCP server with tools for indexing and searching
- Session indexing with pre-computed summaries
- Lesson extraction from successful retries
- Token-optimized retrieval with hierarchical loading
"""

from .server import RagServer, get_rag_client, EmbeddingFunction
from .session_indexer import SessionIndexer
from .lesson_extractor import LessonExtractor, PatternDetector
from .retriever import ProgressiveRetriever, get_retriever, DetailLevel
from .deduplicator import SemanticDeduplicator, get_deduplicator
from .budget import BudgetEnforcer, get_budget_enforcer, TOKEN_BUDGETS

__all__ = [
    # Server
    "RagServer",
    "get_rag_client",
    "EmbeddingFunction",
    # Session indexing
    "SessionIndexer",
    # Lesson extraction
    "LessonExtractor",
    "PatternDetector",
    # Progressive retrieval
    "ProgressiveRetriever",
    "get_retriever",
    "DetailLevel",
    # Deduplication
    "SemanticDeduplicator",
    "get_deduplicator",
    # Budget enforcement
    "BudgetEnforcer",
    "get_budget_enforcer",
    "TOKEN_BUDGETS",
]
