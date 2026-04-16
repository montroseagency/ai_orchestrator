"""
RAG MCP shared configuration.

All tunables are set for max throughput on a GTX 980 Ti (6 GB VRAM,
compute 5.2, 22 SMs, 336 GB/s bandwidth). TDR registry fix assumed.
Override any value via environment variable.

Environment variables (all optional):
  RAG_DEVICE            - "cuda", "cpu", or "cuda:N"  (default: auto-detect)
  RAG_BATCH_SIZE        - Embedding batch size         (default: 32)
  RAG_CHUNK_SIZE        - Target lines per chunk       (default: 80)
  RAG_CHUNK_OVERLAP     - Overlap lines for fallback   (default: 15)
  RAG_MAX_SEQ_LENGTH    - Model max token length       (default: 2048)
  RAG_MODEL_NAME        - HuggingFace model ID         (default: nomic-ai/nomic-embed-text-v1.5)
  RAG_MIN_RELEVANCE     - Min cosine similarity 0-1    (default: 0.25)
  RAG_MAX_PER_FILE      - MMR: max chunks per file     (default: 2)
  RAG_WORKER_THREADS    - Thread pool size              (default: 2)
  RAG_HALF_PRECISION    - Use float16 on GPU           (default: true)
"""

import os
from pathlib import Path


def _env(key: str, default: str) -> str:
    return os.environ.get(key, default).strip()


def _env_int(key: str, default: int) -> int:
    v = os.environ.get(key)
    return int(v) if v else default


def _env_float(key: str, default: float) -> float:
    v = os.environ.get(key)
    return float(v) if v else default


def _env_bool(key: str, default: bool) -> bool:
    v = os.environ.get(key)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes")


# ── Paths ────────────────────────────────────────────────────────────────────
PROJECT_ROOT      = Path(__file__).parent.parent.parent.resolve() / "Montrroase_website"
ORCHESTRATOR_ROOT = Path(__file__).parent.parent.parent.resolve()
DB_PATH           = Path(__file__).parent / "chroma_db"
MANIFEST_PATH     = Path(__file__).parent / "index_manifest.json"

# ── Model ────────────────────────────────────────────────────────────────────
MODEL_NAME       = _env("RAG_MODEL_NAME", "nomic-ai/nomic-embed-text-v1.5")
EMBED_DOC_PREFIX   = "search_document: "
EMBED_QUERY_PREFIX = "search_query: "

# ── Device & precision ───────────────────────────────────────────────────────
# Auto-detect: use CUDA if available, else CPU.
# GTX 980 Ti (compute 5.2) supports float16 inference fine.
DEVICE         = _env("RAG_DEVICE", "auto")       # "auto" | "cuda" | "cpu" | "cuda:0"
HALF_PRECISION = _env_bool("RAG_HALF_PRECISION", True)

# ── Indexer tunables ─────────────────────────────────────────────────────────
# Benchmarked on 980 Ti fp16, seq=2048 (128 chunks):
#   batch=4:   7 chunks/s,  566 MB peak
#   batch=8:   8 chunks/s,  468 MB peak
#   batch=16:  8 chunks/s,  657 MB peak  <-- best: max throughput, lowest useful VRAM
#   batch=32:  8 chunks/s, 1032 MB peak  (no speed gain, +375 MB wasted)
#   batch=64:  7 chunks/s, 1784 MB peak  (slower due to memory pressure)
# The 980 Ti is compute-bound at batch>=8. batch=16 saturates the SMs
# while keeping peak VRAM under 700 MB, leaving 5.3 GB free.
BATCH_SIZE     = _env_int("RAG_BATCH_SIZE", 16)
CHUNK_SIZE     = _env_int("RAG_CHUNK_SIZE", 80)
CHUNK_OVERLAP  = _env_int("RAG_CHUNK_OVERLAP", 15)

# Max sequence length for the embedding model.
# nomic-embed supports up to 8192, but code chunks (80 lines) rarely exceed
# 1500 tokens. 2048 covers 99%+ of chunks and keeps activations small.
# For the remaining <1% that exceed 2048, SentenceTransformer truncates
# gracefully — the first 2048 tokens still produce a good embedding.
MAX_SEQ_LENGTH = _env_int("RAG_MAX_SEQ_LENGTH", 2048)

# ── Collections ──────────────────────────────────────────────────────────────
COLLECTION         = "codebase"
SESSION_COLLECTION = "sessions"

# ── Search quality ───────────────────────────────────────────────────────────
MIN_RELEVANCE          = _env_float("RAG_MIN_RELEVANCE", 0.25)
MAX_PER_FILE           = _env_int("RAG_MAX_PER_FILE", 2)
SESSION_MIN_RELEVANCE  = 0.50
SESSION_BUDGET_TOKENS  = 300
CHARS_PER_TOKEN_ESTIMATE = 4

# ── Server ───────────────────────────────────────────────────────────────────
WORKER_THREADS = _env_int("RAG_WORKER_THREADS", 2)

# ── File filters (not env-configurable) ──────────────────────────────────────
INCLUDE_EXTENSIONS = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".css",
    ".md", ".json", ".yaml", ".yml", ".toml",
    ".conf", ".cfg", ".ini", ".html",
}

EXCLUDE_DIRS = {
    "node_modules", ".git", "dist", "build", ".next", "__pycache__",
    "migrations", ".venv", "venv", "env", "chroma_db",
    "monitoring", "rabbitmq", "coverage", ".pytest_cache", "staticfiles",
    "sessions",
}

EXCLUDE_FILES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    ".package-lock.json", "next-env.d.ts",
}

EXT_LANG = {
    ".py": "python", ".ts": "typescript", ".tsx": "tsx",
    ".js": "javascript", ".jsx": "jsx", ".css": "css",
    ".md": "markdown", ".json": "json", ".yaml": "yaml", ".yml": "yaml",
    ".toml": "toml", ".conf": "conf", ".cfg": "conf", ".ini": "ini",
    ".html": "html",
}

# ── Orchestrator whitelist ───────────────────────────────────────────────────
ORCHESTRATOR_INCLUDE = [
    "_vibecoding_brain/context",
    "_vibecoding_brain/AGENTS.md",
    "_vibecoding_brain/problems/rules.md",
    "CLAUDE.md",
    "DOCUMENTATION.md",
]


def resolve_device() -> str:
    """Resolve the actual torch device string."""
    if DEVICE != "auto":
        return DEVICE
    try:
        import torch
        return "cuda" if torch.cuda.is_available() else "cpu"
    except ImportError:
        return "cpu"
