"""
RAG MCP Server — Vector-based memory for cross-session learning.

Collections:
- codebase: Source code search (existing pattern)
- sessions: Past task prompts + outcomes
- patterns: Error/solution patterns
- lessons: Specific learnings from successful fixes

MCP Tools:
- search_codebase: Search indexed code
- index_session: Store a completed session
- search_sessions: Find similar past tasks
- get_session: Get full session details
- record_lesson: Store a lesson/pattern
- search_lessons: Search lessons by topic
- rag_status: Get system status
"""

import os
import json
import hashlib
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
import chromadb
from chromadb.config import Settings

# Use ollama for local embeddings (nomic-embed-text)
# Falls back to sentence-transformers if ollama unavailable
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False


class EmbeddingFunction:
    """Embedding function using Ollama nomic-embed-text or sentence-transformers fallback."""

    def __init__(self, model_name: str = "nomic-embed-text"):
        self.model_name = model_name
        self._fallback_model = None

    def __call__(self, input: list[str]) -> list[list[float]]:
        """Generate embeddings for input texts."""
        if OLLAMA_AVAILABLE:
            try:
                embeddings = []
                for text in input:
                    response = ollama.embeddings(model=self.model_name, prompt=text)
                    embeddings.append(response["embedding"])
                return embeddings
            except Exception:
                pass

        # Fallback to sentence-transformers
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            if self._fallback_model is None:
                self._fallback_model = SentenceTransformer("all-MiniLM-L6-v2")
            return self._fallback_model.encode(input).tolist()

        raise RuntimeError("No embedding model available. Install ollama or sentence-transformers.")


class RagServer:
    """
    RAG Server with ChromaDB for self-improving agent memory.

    Provides vector search across sessions, patterns, and lessons
    to enable cross-session learning and pattern recognition.
    """

    # Collection configurations
    COLLECTIONS = {
        "codebase": {
            "metadata": {"hnsw:space": "cosine"},
            "description": "Indexed source code for semantic search",
        },
        "sessions": {
            "metadata": {"hnsw:space": "cosine"},
            "description": "Past task prompts, outcomes, and summaries",
        },
        "patterns": {
            "metadata": {"hnsw:space": "cosine"},
            "description": "Error/solution patterns extracted from reviews",
        },
        "lessons": {
            "metadata": {"hnsw:space": "cosine"},
            "description": "Specific learnings from successful fixes",
        },
    }

    def __init__(self, persist_directory: Optional[Path] = None):
        """
        Initialize the RAG server.

        Args:
            persist_directory: Where to store ChromaDB data.
                             Defaults to src/rag/chroma_db/
        """
        if persist_directory is None:
            persist_directory = Path(__file__).parent / "chroma_db"

        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB with persistence
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(anonymized_telemetry=False),
        )

        # Initialize embedding function
        self.embed_fn = EmbeddingFunction()

        # Cache for query results
        self._cache: dict[str, tuple[float, Any]] = {}
        self._cache_ttl = 300  # 5 minutes

        # Initialize collections
        self._collections: dict[str, chromadb.Collection] = {}
        self._init_collections()

    def _init_collections(self):
        """Initialize or get existing collections."""
        for name, config in self.COLLECTIONS.items():
            self._collections[name] = self.client.get_or_create_collection(
                name=name,
                metadata=config["metadata"],
            )

    def _get_collection(self, name: str) -> chromadb.Collection:
        """Get a collection by name."""
        if name not in self._collections:
            raise ValueError(f"Unknown collection: {name}")
        return self._collections[name]

    def _cache_key(self, query: str, collection: str, n: int) -> str:
        """Generate a cache key for a query."""
        return hashlib.md5(f"{query}:{collection}:{n}".encode()).hexdigest()

    def _check_cache(self, key: str) -> Optional[Any]:
        """Check cache for a query result."""
        if key in self._cache:
            timestamp, result = self._cache[key]
            if time.time() - timestamp < self._cache_ttl:
                return result
            del self._cache[key]
        return None

    def _set_cache(self, key: str, result: Any):
        """Cache a query result."""
        self._cache[key] = (time.time(), result)

    # ═══════════════════════════════════════════════════════════════
    # MCP Tools: Session Management
    # ═══════════════════════════════════════════════════════════════

    def index_session(
        self,
        session_id: str,
        prompt: str,
        outcome: str,
        summary: str,
        files_touched: list[str],
        review_issues: list[str],
        retry_count: int = 0,
        full_plan_path: Optional[str] = None,
        full_review_path: Optional[str] = None,
    ) -> dict:
        """
        Index a completed session into ChromaDB.

        Args:
            session_id: Unique session identifier
            prompt: Original user prompt
            outcome: "pass" or "fail"
            summary: Pre-computed summary (150 tokens max)
            files_touched: List of file paths modified
            review_issues: Categorized issues from review
            retry_count: Number of review retries
            full_plan_path: Path to full plan.md for detail loading
            full_review_path: Path to full review.md

        Returns:
            Status dict with success/error info
        """
        try:
            collection = self._get_collection("sessions")

            # Build embedding text from prompt + summary
            embed_text = f"{prompt}\n\n{summary}"

            # Metadata for filtering and retrieval
            metadata = {
                "session_id": session_id,
                "prompt": prompt[:500],  # Truncate for storage
                "outcome": outcome,
                "retry_count": retry_count,
                "files_touched": ",".join(files_touched[:20]),  # Limit files
                "review_issues": ",".join(review_issues[:10]),
                "summary": summary,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            if full_plan_path:
                metadata["full_plan_path"] = full_plan_path
            if full_review_path:
                metadata["full_review_path"] = full_review_path

            # Upsert (update if exists, insert if not)
            collection.upsert(
                ids=[session_id],
                documents=[embed_text],
                metadatas=[metadata],
            )

            return {"status": "ok", "session_id": session_id}

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def search_sessions(
        self,
        query: str,
        n: int = 5,
        min_relevance: float = 0.5,
        outcome_filter: Optional[str] = None,
    ) -> list[dict]:
        """
        Find similar past sessions.

        Args:
            query: Search query (task description)
            n: Maximum results to return
            min_relevance: Minimum relevance score (0-1)
            outcome_filter: "pass" or "fail" to filter by outcome

        Returns:
            List of matching sessions with metadata and relevance scores
        """
        # Check cache
        cache_key = self._cache_key(query, "sessions", n)
        cached = self._check_cache(cache_key)
        if cached is not None:
            return cached

        try:
            collection = self._get_collection("sessions")

            # Build where clause if filtering
            where = None
            if outcome_filter:
                where = {"outcome": outcome_filter}

            results = collection.query(
                query_texts=[query],
                n_results=n,
                where=where,
                include=["metadatas", "distances"],
            )

            # Convert to list of dicts with relevance scores
            sessions = []
            if results["metadatas"] and results["metadatas"][0]:
                for i, metadata in enumerate(results["metadatas"][0]):
                    # ChromaDB returns distances, convert to similarity
                    distance = results["distances"][0][i] if results["distances"] else 0
                    relevance = 1 - (distance / 2)  # Cosine distance to similarity

                    if relevance >= min_relevance:
                        sessions.append({
                            **metadata,
                            "relevance": relevance,
                            "files": metadata.get("files_touched", "").split(","),
                            "issues": metadata.get("review_issues", "").split(","),
                        })

            # Cache results
            self._set_cache(cache_key, sessions)

            return sessions

        except Exception as e:
            return []

    def get_session(self, session_id: str) -> Optional[dict]:
        """
        Get full details of a specific session.

        Args:
            session_id: The session ID to retrieve

        Returns:
            Session dict with all metadata, or None if not found
        """
        try:
            collection = self._get_collection("sessions")
            result = collection.get(ids=[session_id], include=["metadatas", "documents"])

            if result["metadatas"] and result["metadatas"][0]:
                metadata = result["metadatas"][0]

                # Load full artifacts if paths available
                full_data = dict(metadata)

                plan_path = metadata.get("full_plan_path")
                if plan_path and Path(plan_path).exists():
                    full_data["full_plan"] = Path(plan_path).read_text(encoding="utf-8")

                review_path = metadata.get("full_review_path")
                if review_path and Path(review_path).exists():
                    full_data["full_review"] = Path(review_path).read_text(encoding="utf-8")

                return full_data

            return None

        except Exception:
            return None

    # ═══════════════════════════════════════════════════════════════
    # MCP Tools: Lesson Management
    # ═══════════════════════════════════════════════════════════════

    def record_lesson(
        self,
        lesson_id: str,
        issue_type: str,
        fix_that_worked: str,
        context: str,
        source_session: Optional[str] = None,
    ) -> dict:
        """
        Record a lesson/pattern learned from a successful fix.

        Args:
            lesson_id: Unique identifier for the lesson
            issue_type: Categorized issue type (e.g., "typescript_any_type")
            fix_that_worked: Description of the fix
            context: Additional context about when this applies
            source_session: Session ID where this was learned

        Returns:
            Status dict
        """
        try:
            collection = self._get_collection("lessons")

            # Build embedding from issue + fix
            embed_text = f"{issue_type}: {fix_that_worked}\n\nContext: {context}"

            metadata = {
                "lesson_id": lesson_id,
                "issue_type": issue_type,
                "fix": fix_that_worked[:1000],  # Truncate
                "context": context[:500],
                "source_session": source_session or "",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "occurrences": 1,
            }

            collection.upsert(
                ids=[lesson_id],
                documents=[embed_text],
                metadatas=[metadata],
            )

            return {"status": "ok", "lesson_id": lesson_id}

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def search_lessons(
        self,
        query: str,
        n: int = 5,
        issue_type_filter: Optional[str] = None,
    ) -> list[dict]:
        """
        Search for relevant lessons.

        Args:
            query: Search query (error description, issue type)
            n: Maximum results
            issue_type_filter: Filter by specific issue type

        Returns:
            List of matching lessons with relevance scores
        """
        cache_key = self._cache_key(query, "lessons", n)
        cached = self._check_cache(cache_key)
        if cached is not None:
            return cached

        try:
            collection = self._get_collection("lessons")

            where = None
            if issue_type_filter:
                where = {"issue_type": issue_type_filter}

            results = collection.query(
                query_texts=[query],
                n_results=n,
                where=where,
                include=["metadatas", "distances"],
            )

            lessons = []
            if results["metadatas"] and results["metadatas"][0]:
                for i, metadata in enumerate(results["metadatas"][0]):
                    distance = results["distances"][0][i] if results["distances"] else 0
                    relevance = 1 - (distance / 2)

                    lessons.append({
                        **metadata,
                        "relevance": relevance,
                    })

            self._set_cache(cache_key, lessons)
            return lessons

        except Exception:
            return []

    # ═══════════════════════════════════════════════════════════════
    # MCP Tools: Pattern Management
    # ═══════════════════════════════════════════════════════════════

    def record_pattern(
        self,
        pattern_id: str,
        error_type: str,
        solution: str,
        frequency: int = 1,
    ) -> dict:
        """Record an error/solution pattern."""
        try:
            collection = self._get_collection("patterns")

            embed_text = f"Error: {error_type}\nSolution: {solution}"

            metadata = {
                "pattern_id": pattern_id,
                "error_type": error_type,
                "solution": solution[:1000],
                "frequency": frequency,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            collection.upsert(
                ids=[pattern_id],
                documents=[embed_text],
                metadatas=[metadata],
            )

            return {"status": "ok", "pattern_id": pattern_id}

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def search_patterns(
        self,
        query: str,
        n: int = 5,
    ) -> list[dict]:
        """Search for error/solution patterns."""
        cache_key = self._cache_key(query, "patterns", n)
        cached = self._check_cache(cache_key)
        if cached is not None:
            return cached

        try:
            collection = self._get_collection("patterns")

            results = collection.query(
                query_texts=[query],
                n_results=n,
                include=["metadatas", "distances"],
            )

            patterns = []
            if results["metadatas"] and results["metadatas"][0]:
                for i, metadata in enumerate(results["metadatas"][0]):
                    distance = results["distances"][0][i] if results["distances"] else 0
                    relevance = 1 - (distance / 2)

                    patterns.append({
                        **metadata,
                        "relevance": relevance,
                    })

            self._set_cache(cache_key, patterns)
            return patterns

        except Exception:
            return []

    # ═══════════════════════════════════════════════════════════════
    # MCP Tools: Status and Utilities
    # ═══════════════════════════════════════════════════════════════

    def rag_status(self) -> dict:
        """
        Get status of the RAG system.

        Returns:
            Dict with collection counts and system info
        """
        status = {
            "status": "ok",
            "persist_directory": str(self.persist_directory),
            "collections": {},
            "cache_size": len(self._cache),
        }

        for name in self.COLLECTIONS:
            try:
                collection = self._get_collection(name)
                count = collection.count()
                status["collections"][name] = {
                    "count": count,
                    "description": self.COLLECTIONS[name]["description"],
                }
            except Exception as e:
                status["collections"][name] = {"error": str(e)}

        return status

    def clear_cache(self):
        """Clear the query cache."""
        self._cache.clear()


# ═══════════════════════════════════════════════════════════════
# Client convenience function
# ═══════════════════════════════════════════════════════════════

_rag_instance: Optional[RagServer] = None


def get_rag_client(persist_directory: Optional[Path] = None) -> RagServer:
    """
    Get or create a singleton RAG client instance.

    Args:
        persist_directory: Override default persist directory

    Returns:
        RagServer instance
    """
    global _rag_instance

    if _rag_instance is None:
        _rag_instance = RagServer(persist_directory)

    return _rag_instance
