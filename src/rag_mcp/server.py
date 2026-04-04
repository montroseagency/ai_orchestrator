#!/usr/bin/env python3
"""
RAG MCP Server — Montrroase codebase semantic search + session memory.

Exposes eight tools to Claude Code:
  search_codebase       — semantic search with relevance threshold + MMR dedup
  search_multi          — batch N queries in one round-trip, merged + deduped
  search_symbol         — exact lookup by function/class name in index metadata
  get_file              — read a specific file with line numbers
  list_indexed_files    — browse what's in the index
  rag_status            — chunk count, last indexed time
  search_past_sessions  — find similar past task sessions for context
  index_session         — store a completed session for future reference

Transport: stdio (Claude Code connects at startup)
"""
from __future__ import annotations

import asyncio
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import chromadb
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool
from sentence_transformers import SentenceTransformer

# Try tiktoken for accurate token counting in session memory budget
try:
    import tiktoken
    _TIKTOKEN_AVAILABLE = True
except ImportError:
    _TIKTOKEN_AVAILABLE = False

# ── Config ────────────────────────────────────────────────────────────────────
PROJECT_ROOT      = Path(__file__).parent.parent.parent.resolve() / "Montrroase_website"
ORCHESTRATOR_ROOT = Path(__file__).parent.parent.parent.resolve()
DB_PATH           = Path(__file__).parent / "chroma_db"
COLLECTION      = "codebase"
SESSION_COLLECTION = "sessions"
MODEL_NAME         = "nomic-ai/nomic-embed-text-v1.5"
EMBED_QUERY_PREFIX = "search_query: "   # nomic task prefix for queries
EMBED_DOC_PREFIX   = "search_document: "  # nomic task prefix for indexing

# Search quality controls
MIN_RELEVANCE   = 0.25   # drop chunks below 25% cosine similarity
MAX_PER_FILE    = 2      # MMR: at most 2 chunks per file per query result

# Session memory controls
SESSION_MIN_RELEVANCE = 0.50  # stricter threshold for session matches
SESSION_BUDGET_TOKENS = 300   # max tokens for formatted session context
CHARS_PER_TOKEN_ESTIMATE = 4  # fallback token estimation

# ── Lazy globals ──────────────────────────────────────────────────────────────
_model: SentenceTransformer | None      = None
_chroma_client: chromadb.PersistentClient | None = None


def model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME, trust_remote_code=True)
        _model.max_seq_length = 8192   # unlock full context window
    return _model


def _chroma() -> chromadb.PersistentClient:
    """Return (cached) ChromaDB client. The client itself is cheap to reuse."""
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=str(DB_PATH))
    return _chroma_client


def collection():
    """
    Always resolve the collection fresh from the client so that a full reindex
    (which deletes and recreates the collection with a new UUID) never leaves
    this server holding a stale reference.

    get_or_create_collection is a lightweight SQLite metadata lookup — safe to
    call on every request.
    """
    return _chroma().get_or_create_collection(
        COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )


def session_collection():
    """Get or create the sessions collection for cross-session memory."""
    return _chroma().get_or_create_collection(
        SESSION_COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )


# ── Token budget helpers ─────────────────────────────────────────────────────

def _count_tokens(text: str) -> int:
    """Count tokens using tiktoken if available, else estimate ~4 chars/token."""
    if not text:
        return 0
    if _TIKTOKEN_AVAILABLE:
        try:
            enc = tiktoken.get_encoding("cl100k_base")
            return len(enc.encode(text))
        except Exception:
            pass
    return len(text) // CHARS_PER_TOKEN_ESTIMATE


def _truncate_to_budget(text: str, budget: int) -> str:
    """Truncate text to fit within token budget, preserving complete sentences."""
    if _count_tokens(text) <= budget:
        return text
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    result = []
    total = 0
    for s in sentences:
        t = _count_tokens(s)
        if total + t > budget:
            break
        result.append(s)
        total += t
    if not result:
        char_limit = budget * CHARS_PER_TOKEN_ESTIMATE
        return text[:char_limit].rsplit(" ", 1)[0] + "..."
    out = " ".join(result)
    if len(result) < len(sentences):
        out += "..."
    return out


# ── MCP server ────────────────────────────────────────────────────────────────
server = Server("codebase-rag")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="search_codebase",
            description=(
                "Semantically search the Montrroase codebase. "
                "Returns ranked code chunks with file paths and line numbers. "
                "Results are filtered by relevance (≥30%) and deduplicated across files. "
                "Use this instead of explore agents to find where features are implemented."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "Natural language query. Examples: "
                            "'how does JWT auth work', "
                            "'stripe billing webhook', "
                            "'websocket notification realtime', "
                            "'dashboard client overview'"
                        ),
                    },
                    "n_results": {
                        "type": "integer",
                        "description": "Number of chunks to return (default 8, max 20)",
                        "default": 8,
                    },
                    "path_filter": {
                        "type": "string",
                        "description": (
                            "Optional: restrict results to a subdirectory. "
                            "E.g. 'server/api', 'client/app/dashboard', 'services/realtime'"
                        ),
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="search_multi",
            description=(
                "Run 2–5 semantic queries in one call and get merged, deduplicated results. "
                "More efficient than calling search_codebase repeatedly for related concepts. "
                "Use when you need code matching any of several related ideas at once."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "queries": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of 2–5 natural language queries",
                        "minItems": 2,
                        "maxItems": 5,
                    },
                    "n_results": {
                        "type": "integer",
                        "description": "Total unique results to return across all queries (default 10, max 20)",
                        "default": 10,
                    },
                    "path_filter": {
                        "type": "string",
                        "description": "Optional: restrict to a subdirectory",
                    },
                },
                "required": ["queries"],
            },
        ),
        Tool(
            name="search_symbol",
            description=(
                "Find chunks by exact function, class, or export name stored in the index. "
                "Faster than semantic search for 'where is function X defined'. "
                "Requires a full reindex (indexer.py --full) after adding this feature."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Exact name of a function, class, or exported symbol, e.g. 'login_view', 'AuthContext'",
                    },
                    "path_filter": {
                        "type": "string",
                        "description": "Optional: restrict to a subdirectory",
                    },
                },
                "required": ["symbol"],
            },
        ),
        Tool(
            name="get_file",
            description=(
                "Read a specific file from the codebase by its relative path. "
                "Returns content with line numbers. Use paths from search_codebase results."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File path relative to project root, e.g. 'server/api/views_new_features.py'",
                    },
                    "start_line": {
                        "type": "integer",
                        "description": "Optional: read from this line (1-indexed)",
                    },
                    "end_line": {
                        "type": "integer",
                        "description": "Optional: read up to this line (inclusive)",
                    },
                },
                "required": ["path"],
            },
        ),
        Tool(
            name="list_indexed_files",
            description="List all source files in the RAG index, optionally filtered by directory.",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "Optional path prefix filter, e.g. 'client/hooks' or 'server'",
                    },
                },
            },
        ),
        Tool(
            name="rag_status",
            description="Show RAG index status: chunk count, last indexed timestamp, model info.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="search_past_sessions",
            description=(
                "Search past task sessions for similar work and lessons learned. "
                "Returns session outcomes, summaries, and files touched. "
                "Use at the start of a task to find relevant historical context."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language description of the current task",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum sessions to return (default 5)",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="index_session",
            description=(
                "Store a completed agent team session for future reference. "
                "Call this at the end of the pipeline (Step 9) to index the session outcome."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Unique session identifier (kebab-case slug)",
                    },
                    "prompt": {
                        "type": "string",
                        "description": "Original user task prompt",
                    },
                    "outcome": {
                        "type": "string",
                        "description": "Session outcome: 'pass', 'fail', or 'stuck'",
                        "enum": ["pass", "fail", "stuck"],
                    },
                    "summary": {
                        "type": "string",
                        "description": "Brief summary of what was implemented",
                    },
                    "files_touched": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of file paths that were created or modified",
                    },
                    "iterations": {
                        "type": "integer",
                        "description": "Number of test-fix iterations",
                        "default": 0,
                    },
                },
                "required": ["session_id", "prompt", "outcome", "summary", "files_touched"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    if name == "search_codebase":
        return await _search(arguments)
    if name == "search_multi":
        return await _search_multi(arguments)
    if name == "search_symbol":
        return await _search_symbol(arguments)
    if name == "get_file":
        return await _get_file(arguments)
    if name == "list_indexed_files":
        return await _list_files(arguments)
    if name == "rag_status":
        return await _status()
    if name == "search_past_sessions":
        return await _search_past_sessions(arguments)
    if name == "index_session":
        return await _index_session(arguments)
    return [TextContent(type="text", text=f"Unknown tool: {name}")]


# ── Shared search helpers ──────────────────────────────────────────────────────

def _run_query(query: str, n: int, path_filter: str) -> dict | str:
    """
    Run a single semantic query against ChromaDB.
    Returns a raw results dict or an error string.
    Fetches up to `n` candidates (caller applies threshold + MMR after).
    """
    col = collection()
    if col.count() == 0:
        return "Index is empty — run `python indexer.py --full` first."

    embedding = model().encode([EMBED_QUERY_PREFIX + query]).tolist()
    where = {"file_path": {"$contains": path_filter}} if path_filter else None

    try:
        return col.query(
            query_embeddings=embedding,
            n_results=min(n, col.count()),
            where=where,
            include=["documents", "metadatas", "distances"],
        )
    except Exception as e:
        return f"Search error: {e}"


def _apply_threshold_and_mmr(
    results: dict,
    n_results: int,
) -> list[tuple[str, dict, float]]:
    """
    Filter raw ChromaDB results:
      1. Drop chunks below MIN_RELEVANCE cosine similarity
      2. MMR dedup: keep at most MAX_PER_FILE chunks per source file
      3. Return up to n_results as [(doc, meta, relevance_pct)]
    """
    docs      = results["documents"][0]
    metas     = results["metadatas"][0]
    distances = results["distances"][0]

    file_counts: dict[str, int] = {}
    output: list[tuple[str, dict, float]] = []

    for doc, meta, dist in zip(docs, metas, distances):
        relevance = (1 - dist) * 100
        if relevance < MIN_RELEVANCE * 100:
            continue
        fp = meta.get("file_path", "")
        if file_counts.get(fp, 0) >= MAX_PER_FILE:
            continue
        file_counts[fp] = file_counts.get(fp, 0) + 1
        output.append((doc, meta, relevance))
        if len(output) >= n_results:
            break

    return output


def _format_results(results: list[tuple[str, dict, float]]) -> str:
    if not results:
        return "No results found above the relevance threshold."

    parts = []
    for i, (doc, meta, relevance) in enumerate(results):
        lang    = meta.get("language", "")
        symbols = meta.get("symbols", "")
        sym_str = f" | `{symbols}`" if symbols else ""
        header  = (
            f"### [{i+1}] `{meta['file_path']}` "
            f"lines {meta['start_line']}–{meta['end_line']} "
            f"({relevance:.0f}% match){sym_str}"
        )
        parts.append(f"{header}\n```{lang}\n{doc}\n```")

    return "\n\n".join(parts)


# ── Tool implementations ───────────────────────────────────────────────────────

async def _search(args: dict) -> list[TextContent]:
    query       = args["query"]
    n_results   = min(int(args.get("n_results", 8)), 20)
    path_filter = args.get("path_filter", "").strip()

    # Fetch 3× candidates so threshold + MMR have enough to work with
    raw = _run_query(query, n_results * 3, path_filter)
    if isinstance(raw, str):
        return [TextContent(type="text", text=raw)]

    filtered = _apply_threshold_and_mmr(raw, n_results)
    return [TextContent(type="text", text=_format_results(filtered))]


async def _search_multi(args: dict) -> list[TextContent]:
    queries     = args.get("queries", [])
    n_results   = min(int(args.get("n_results", 10)), 20)
    path_filter = args.get("path_filter", "").strip()

    if not queries:
        return [TextContent(type="text", text="Provide at least 2 queries.")]

    # Run all queries, keep the best distance score per unique chunk
    best: dict[str, tuple[str, dict, float]] = {}  # chunk_id → (doc, meta, dist)

    for q in queries[:5]:
        raw = _run_query(q, n_results * 2, path_filter)
        if isinstance(raw, str):
            continue  # skip errored queries

        docs      = raw["documents"][0]
        metas     = raw["metadatas"][0]
        distances = raw["distances"][0]

        for doc, meta, dist in zip(docs, metas, distances):
            chunk_id = f"{meta['file_path']}::{meta.get('chunk_index', 0)}"
            if chunk_id not in best or dist < best[chunk_id][2]:
                best[chunk_id] = (doc, meta, dist)

    if not best:
        return [TextContent(type="text", text="No results found.")]

    # Re-sort all candidates by distance and apply threshold + MMR
    ranked = sorted(best.values(), key=lambda x: x[2])
    fake_results = {
        "documents": [[r[0] for r in ranked]],
        "metadatas": [[r[1] for r in ranked]],
        "distances": [[r[2] for r in ranked]],
    }
    filtered = _apply_threshold_and_mmr(fake_results, n_results)

    header = f"**{len(filtered)} results** from {len(queries)} queries\n\n"
    return [TextContent(type="text", text=header + _format_results(filtered))]


async def _search_symbol(args: dict) -> list[TextContent]:
    """
    Find chunks by exact function/class name.

    Uses where_document (searches the code text itself) rather than metadata
    $contains, because ChromaDB's where clause only supports $eq/$ne/$in for
    string metadata — $contains is only valid in where_document.

    This is actually better: it finds both definition and call sites.
    """
    symbol      = args.get("symbol", "").strip()
    path_filter = args.get("path_filter", "").strip()

    if not symbol:
        return [TextContent(type="text", text="Provide a symbol name.")]

    col = collection()
    if col.count() == 0:
        return [TextContent(type="text", text="Index is empty — run `python indexer.py --full` first.")]

    where = {"file_path": {"$contains": path_filter}} if path_filter else None

    try:
        results = col.get(
            where=where,
            where_document={"$contains": symbol},   # search within code text
            include=["documents", "metadatas"],
            limit=10,
        )
    except Exception as e:
        return [TextContent(type="text", text=f"Symbol search error: {e}")]

    docs  = results.get("documents", [])
    metas = results.get("metadatas", [])

    if not docs:
        return [TextContent(type="text", text=f"No indexed chunk found containing `{symbol}`.")]

    parts = []
    for i, (doc, meta) in enumerate(zip(docs, metas)):
        lang    = meta.get("language", "")
        symbols = meta.get("symbols", "")
        sym_str = f" | symbols: `{symbols}`" if symbols else ""
        header  = (
            f"### [{i+1}] `{meta['file_path']}` "
            f"lines {meta['start_line']}–{meta['end_line']}{sym_str}"
        )
        parts.append(f"{header}\n```{lang}\n{doc}\n```")

    return [TextContent(type="text", text=(
        f"**`{symbol}` — found in {len(docs)} chunk(s)**\n\n" + "\n\n".join(parts)
    ))]


async def _get_file(args: dict) -> list[TextContent]:
    path       = args["path"].lstrip("/").replace("\\", "/")
    start_line = args.get("start_line")
    end_line   = args.get("end_line")
    # Multi-root resolution: _orchestrator/ prefix → orchestrator root, else project root
    if path.startswith("_orchestrator/"):
        full_path = ORCHESTRATOR_ROOT / path[len("_orchestrator/"):]
    else:
        full_path = PROJECT_ROOT / path

    if not full_path.exists():
        return [TextContent(type="text", text=f"File not found: `{path}`")]

    try:
        content = full_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return [TextContent(type="text", text=f"Error reading `{path}`: {e}")]

    lines = content.split("\n")
    s = (start_line - 1) if start_line else 0
    e = end_line if end_line else len(lines)
    lines = lines[s:e]

    numbered = "\n".join(f"{s + i + 1:5d} | {line}" for i, line in enumerate(lines))
    ext      = full_path.suffix.lstrip(".")
    header   = f"**`{path}`** ({len(lines)} lines shown)"

    return [TextContent(type="text", text=f"{header}\n```{ext}\n{numbered}\n```")]


async def _list_files(args: dict) -> list[TextContent]:
    directory = args.get("directory", "").strip()
    col       = collection()

    if col.count() == 0:
        return [TextContent(type="text", text="Index is empty — run `python indexer.py --full` first.")]

    all_metas = col.get(include=["metadatas"])["metadatas"]
    paths     = sorted({
        m["file_path"] for m in all_metas
        if not directory or directory in m["file_path"]
    })

    if not paths:
        return [TextContent(type="text", text=f"No indexed files matching `{directory}`.")]

    lines = [f"`{p}`" for p in paths]
    return [TextContent(type="text", text=f"**{len(paths)} files**\n" + "\n".join(lines))]


async def _status() -> list[TextContent]:
    col   = collection()
    count = col.count()

    ts_file    = Path(__file__).parent / "last_indexed.txt"
    last_index = ts_file.read_text().strip() if ts_file.exists() else "Never"

    text = (
        f"**RAG Index Status**\n"
        f"- Chunks indexed : {count:,}\n"
        f"- Last indexed   : {last_index}\n"
        f"- Model          : {MODEL_NAME}\n"
        f"- DB path        : {DB_PATH}\n"
        f"- Project root   : {PROJECT_ROOT}"
    )
    return [TextContent(type="text", text=text)]


# ── Session memory tools ──────────────────────────────────────────────────────

async def _search_past_sessions(args: dict) -> list[TextContent]:
    """Find similar past sessions by semantic search."""
    query       = args["query"]
    max_results = min(int(args.get("max_results", 5)), 10)

    try:
        col = session_collection()
        if col.count() == 0:
            return [TextContent(type="text", text="No past sessions indexed yet.")]

        embedding = model().encode([EMBED_QUERY_PREFIX + query]).tolist()

        results = col.query(
            query_embeddings=embedding,
            n_results=min(max_results * 2, col.count()),
            include=["metadatas", "distances"],
        )

        sessions = []
        if results["metadatas"] and results["metadatas"][0]:
            for meta, dist in zip(results["metadatas"][0], results["distances"][0]):
                relevance = 1 - dist
                if relevance < SESSION_MIN_RELEVANCE:
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

        if not sessions:
            return [TextContent(type="text", text="No similar past sessions found.")]

        parts = []
        for s in sessions:
            entry = f"- **{s['session_id']}** ({s['outcome']}, {s['relevance']:.0%} match)"
            if s["summary"]:
                entry += f": {s['summary']}"
            if s["files"]:
                entry += f"\n  Files: {', '.join(s['files'][:5])}"
            parts.append(entry)

        text = f"**{len(sessions)} similar past sessions:**\n\n" + "\n".join(parts)
        text = _truncate_to_budget(text, SESSION_BUDGET_TOKENS)
        return [TextContent(type="text", text=text)]

    except Exception as e:
        return [TextContent(type="text", text=f"Session search error: {e}")]


async def _index_session(args: dict) -> list[TextContent]:
    """Store a completed session for future retrieval."""
    session_id    = args["session_id"]
    prompt        = args["prompt"]
    outcome       = args["outcome"]
    summary       = args["summary"]
    files_touched = args.get("files_touched", [])
    iterations    = int(args.get("iterations", 0))

    try:
        col = session_collection()
        embed_text = EMBED_DOC_PREFIX + f"{prompt}\n\n{summary}"
        embedding = model().encode([embed_text]).tolist()

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
        return [TextContent(type="text", text=f"Session `{session_id}` indexed ({outcome}, {len(files_touched)} files).")]

    except Exception as e:
        return [TextContent(type="text", text=f"Session index error: {e}")]


# ── Entry point ────────────────────────────────────────────────────────────────

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
