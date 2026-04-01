"""
Session Memory — Cross-session learning via ChromaDB.

Stores completed session outcomes and retrieves similar past tasks
to enrich future prompts with historical context.

Uses the same ChromaDB instance and embedding model as the MCP codebase server,
but manages a separate 'sessions' collection.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import chromadb
from sentence_transformers import SentenceTransformer

from .budget import BudgetEnforcer

# ── Config (shared with MCP server) ──────────────────────────────────────────
DB_PATH = Path(__file__).parent / "chroma_db"
MODEL_NAME = "nomic-ai/nomic-embed-text-v1.5"
EMBED_QUERY_PREFIX = "search_query: "
EMBED_DOC_PREFIX = "search_document: "
COLLECTION = "sessions"

# ── Lazy globals ─────────────────────────────────────────────────────────────
_model: SentenceTransformer | None = None
_chroma_client: chromadb.PersistentClient | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME, trust_remote_code=True)
        _model.max_seq_length = 8192
    return _model


def _get_chroma() -> chromadb.PersistentClient:
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=str(DB_PATH))
    return _chroma_client


def _get_collection():
    return _get_chroma().get_or_create_collection(
        COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )


# ── Public API ───────────────────────────────────────────────────────────────

def index_session(
    session_id: str,
    prompt: str,
    outcome: str,
    summary: str,
    files_touched: list[str],
    iterations: int = 0,
) -> dict:
    """
    Index a completed session for future retrieval.

    Args:
        session_id: Unique session identifier
        prompt: Original user prompt
        outcome: "pass", "fail", or "stuck"
        summary: Brief summary of what happened
        files_touched: List of file paths modified
        iterations: Number of review iterations

    Returns:
        Status dict with session_id and success/error info
    """
    try:
        col = _get_collection()
        embed_text = EMBED_DOC_PREFIX + f"{prompt}\n\n{summary}"
        embedding = _get_model().encode([embed_text]).tolist()

        metadata = {
            "session_id": session_id,
            "prompt": prompt[:500],
            "outcome": outcome,
            "summary": summary[:600],
            "files_touched": ",".join(files_touched[:20]),
            "iterations": iterations,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        col.upsert(
            ids=[session_id],
            embeddings=embedding,
            documents=[embed_text],
            metadatas=[metadata],
        )
        return {"status": "ok", "session_id": session_id}

    except Exception as e:
        return {"status": "error", "error": str(e)}


def search_similar_sessions(
    query: str,
    max_results: int = 5,
    min_relevance: float = 0.50,
) -> list[dict]:
    """
    Find similar past sessions by semantic search.

    Args:
        query: Search query (typically the current task prompt)
        max_results: Maximum sessions to return
        min_relevance: Minimum cosine similarity (0-1) to include

    Returns:
        List of session dicts sorted by relevance, each containing:
        session_id, prompt, outcome, summary, files, relevance
    """
    try:
        col = _get_collection()
        if col.count() == 0:
            return []

        embedding = _get_model().encode([EMBED_QUERY_PREFIX + query]).tolist()

        results = col.query(
            query_embeddings=embedding,
            n_results=min(max_results * 2, col.count()),
            include=["metadatas", "distances"],
        )

        sessions = []
        if results["metadatas"] and results["metadatas"][0]:
            for meta, dist in zip(results["metadatas"][0], results["distances"][0]):
                relevance = 1 - dist  # cosine distance → similarity
                if relevance < min_relevance:
                    continue
                sessions.append({
                    "session_id": meta.get("session_id", ""),
                    "prompt": meta.get("prompt", ""),
                    "outcome": meta.get("outcome", ""),
                    "summary": meta.get("summary", ""),
                    "files": [f for f in meta.get("files_touched", "").split(",") if f],
                    "iterations": meta.get("iterations", 0),
                    "relevance": relevance,
                })
                if len(sessions) >= max_results:
                    break

        return sessions

    except Exception:
        return []


def format_context(sessions: list[dict], budget_tokens: int = 100) -> str:
    """
    Format retrieved sessions as markdown within a token budget.

    Args:
        sessions: List of session dicts from search_similar_sessions()
        budget_tokens: Maximum tokens for the formatted output

    Returns:
        Markdown string with session summaries, truncated to budget
    """
    if not sessions:
        return ""

    parts = []
    for s in sessions:
        outcome = s.get("outcome", "unknown")
        relevance = s.get("relevance", 0)
        summary = s.get("summary", "")
        files = s.get("files", [])

        entry = f"- **{s['session_id']}** ({outcome}, {relevance:.0%} match)"
        if summary:
            entry += f": {summary}"
        if files:
            entry += f"\n  Files: {', '.join(files[:5])}"
        parts.append(entry)

    text = "\n".join(parts)

    enforcer = BudgetEnforcer(budgets={"context": budget_tokens})
    return enforcer.enforce("context", text)
