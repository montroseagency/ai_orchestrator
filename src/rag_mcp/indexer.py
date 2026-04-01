#!/usr/bin/env python3
"""
Codebase indexer for RAG MCP server.

Modes:
  python indexer.py              -- incremental: only re-indexes changed/new files
  python indexer.py --full       -- wipes index and rebuilds from scratch

Design:
  - AST-aware chunking for Python (splits on function/class boundaries, includes
    decorators and inter-block lines so nothing is dropped)
  - Regex-aware chunking for TS/TSX/JS (splits on export/declaration boundaries,
    contiguous coverage via next-declaration-start heuristic)
  - Contextual embedding headers: file path + symbol names prepended before
    encoding so embeddings capture file identity; clean code stored in the DB
  - Symbol names stored in metadata for exact-match search_symbol queries
  - ChromaDB collection uses cosine distance for accurate relevance percentages
"""

import ast
import bisect
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Generator

import chromadb
from sentence_transformers import SentenceTransformer

# ── Config ────────────────────────────────────────────────────────────────────
PROJECT_ROOT   = Path(__file__).parent.parent.parent.resolve() / "Montrroase_website"
DB_PATH        = Path(__file__).parent / "chroma_db"
MANIFEST_PATH  = Path(__file__).parent / "index_manifest.json"
COLLECTION     = "codebase"
MODEL_NAME     = "nomic-ai/nomic-embed-text-v1.5"
# nomic-embed requires task prefixes for optimal quality:
#   documents → "search_document: <text>"
#   queries   → "search_query: <text>"
EMBED_DOC_PREFIX   = "search_document: "
EMBED_QUERY_PREFIX = "search_query: "
CHUNK_SIZE     = 80   # target lines per chunk (line span, not text lines)
CHUNK_OVERLAP  = 15   # overlap for line-based fallback on large blocks
BATCH_SIZE     = 8

INCLUDE_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx", ".css"}

EXCLUDE_DIRS = {
    "node_modules", ".git", "dist", "build", ".next", "__pycache__",
    "migrations", ".venv", "venv", "env", "chroma_db",
    "monitoring", "rabbitmq", "coverage", ".pytest_cache", "staticfiles",
}

EXCLUDE_FILES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    ".package-lock.json", "next-env.d.ts",
}

EXT_LANG = {
    ".py": "python", ".ts": "typescript", ".tsx": "tsx",
    ".js": "javascript", ".jsx": "jsx", ".css": "css",
}

# Matches top-level exports in TS/TSX/JS files
TS_SYMBOL_RE = re.compile(
    r'^export\s+'
    r'(?:default\s+)?'
    r'(?:async\s+)?'
    r'(?:'
    r'(?:function\*?|class)\s+(\w+)'
    r'|(?:const|let|var)\s+(\w+)'
    r'|(?:type|interface|enum)\s+(\w+)'
    r')',
    re.MULTILINE,
)

# Also catches non-exported top-level functions/classes
TS_NOEXPORT_RE = re.compile(
    r'^(?:async\s+)?(?:function\*?|class)\s+(\w+)',
    re.MULTILINE,
)


# ── File discovery ─────────────────────────────────────────────────────────────

def should_skip(rel: Path) -> bool:
    for part in rel.parts:
        if part in EXCLUDE_DIRS:
            return True
    if rel.name in EXCLUDE_FILES:
        return True
    try:
        if (PROJECT_ROOT / rel).stat().st_size > 500_000:
            return True
    except Exception:
        return True
    return False


def iter_source_files() -> Generator[Path, None, None]:
    for ext in INCLUDE_EXTENSIONS:
        for path in sorted(PROJECT_ROOT.rglob(f"*{ext}")):
            rel = path.relative_to(PROJECT_ROOT)
            if not should_skip(rel):
                yield path


# ── Manifest (tracks file mtimes for incremental updates) ─────────────────────

def load_manifest() -> dict[str, float]:
    if MANIFEST_PATH.exists():
        try:
            return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_manifest(manifest: dict[str, float]) -> None:
    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )


# ── Symbol extraction ──────────────────────────────────────────────────────────

def extract_python_blocks(lines: list[str]) -> list[tuple[int, int, str]]:
    """
    Parse Python source and return (start_0idx, end_0idx, name) for every
    top-level function, async function, and class definition.

    The start_0idx includes the first decorator line (if any), ensuring
    decorators are never separated from their function.
    Returns [] if the file fails to parse or contains no top-level defs.
    """
    try:
        tree = ast.parse("\n".join(lines))
    except SyntaxError:
        return []

    blocks = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            # Start at the first decorator line so @decorator stays with its def
            if node.decorator_list:
                start_0 = node.decorator_list[0].lineno - 1
            else:
                start_0 = node.lineno - 1
            blocks.append((start_0, node.end_lineno - 1, node.name))

    return sorted(blocks)


def extract_ts_blocks(lines: list[str]) -> list[tuple[int, int, str]]:
    """
    Regex-based extraction of top-level export/declaration boundaries for
    TS/TSX/JS. Uses next-declaration start as the end of the current one,
    so blocks are contiguous and cover every line with no gaps.
    Returns [] if no declarations are found.
    """
    content = "\n".join(lines)

    # Build line-start offset table for O(log n) char→line lookup
    line_starts = [0]
    for line in lines:
        line_starts.append(line_starts[-1] + len(line) + 1)

    def char_to_line(pos: int) -> int:
        return bisect.bisect_right(line_starts, pos) - 1

    # Merge both patterns and sort by position
    matches = sorted(
        list(TS_SYMBOL_RE.finditer(content)) + list(TS_NOEXPORT_RE.finditer(content)),
        key=lambda m: m.start(),
    )

    # Deduplicate matches that start on the same line (e.g. export + noexport both match)
    seen_lines: set[int] = set()
    unique = []
    for m in matches:
        ln = char_to_line(m.start())
        if ln not in seen_lines:
            seen_lines.add(ln)
            unique.append(m)
    matches = unique

    if not matches:
        return []

    blocks = []
    for i, m in enumerate(matches):
        name = next((g for g in m.groups() if g), "unknown")
        start = char_to_line(m.start())
        # Each block ends just before the next one starts (contiguous, no gaps)
        end = char_to_line(matches[i + 1].start()) - 1 if i + 1 < len(matches) else len(lines) - 1
        end = max(start, end)
        blocks.append((start, end, name))

    return blocks


# ── Chunk helpers ──────────────────────────────────────────────────────────────

def _make_chunk(
    text: str,
    rel_path: str,
    start_0: int,
    end_0: int,
    language: str,
    chunk_idx: int,
    symbols: list[str],
) -> dict:
    return {
        "content":     text,
        "file_path":   rel_path,
        "start_line":  start_0 + 1,
        "end_line":    end_0 + 1,
        "language":    language,
        "chunk_index": chunk_idx,
        "symbols":     ", ".join(symbols[:10]),
    }


def line_chunk(
    lines: list[str],
    rel_path: str,
    language: str,
    line_offset: int = 0,
    start_chunk_idx: int = 0,
    symbols: list[str] | None = None,
) -> list[dict]:
    """
    Sliding-window line chunker with overlap.
    Used as fallback for unsupported languages and for oversized individual blocks.
    Chunks intentionally overlap by CHUNK_OVERLAP lines for better retrieval context.
    """
    chunks = []
    chunk_idx = start_chunk_idx
    i = 0
    while i < len(lines):
        end = min(i + CHUNK_SIZE, len(lines))
        text = "\n".join(lines[i:end])
        if text.strip():
            chunks.append(_make_chunk(
                text, rel_path,
                line_offset + i, line_offset + end - 1,
                language, chunk_idx, symbols or [],
            ))
            chunk_idx += 1
        i += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def smart_chunk(lines: list[str], rel_path: str, language: str) -> list[dict]:
    """
    Chunk by semantic boundaries (functions/classes) with full line coverage:

    Python:
      - Uses ast for exact function/class/decorator line ranges
      - Groups adjacent small blocks into one chunk (up to CHUNK_SIZE line span)
      - Gap lines between blocks (blank lines, module-level code) are included
        in the chunk that covers them — nothing is dropped
      - Oversized individual blocks are split by line_chunk

    TS/TSX/JS:
      - Uses regex to find export/declaration boundaries
      - Blocks are contiguous (each ends where the next begins) so no gaps

    Both: falls back to line_chunk for unsupported languages or parse failures.
    """
    if language == "python":
        blocks = extract_python_blocks(lines)
    elif language in ("typescript", "tsx", "javascript", "jsx"):
        blocks = extract_ts_blocks(lines)
    else:
        blocks = []

    if not blocks:
        return line_chunk(lines, rel_path, language)

    chunks: list[dict] = []
    chunk_idx = 0

    # Preamble: everything before the first declaration (imports, module-level code)
    preamble_end = blocks[0][0] - 1
    if preamble_end >= 0:
        preamble_text = "\n".join(lines[: preamble_end + 1])
        if preamble_text.strip():
            chunks.append(_make_chunk(
                preamble_text, rel_path,
                0, preamble_end, language, chunk_idx, ["(preamble)"],
            ))
            chunk_idx += 1

    # ── Range-based grouping with full coverage ────────────────────────────────
    # `prev_end` tracks the last line already covered by a chunk (0-indexed).
    # `unit_start = prev_end + 1` is the first uncovered line before each block.
    # By setting group_start (or the line_chunk offset) to unit_start instead of
    # the block's own start, we pull in any gap lines (blank lines, section
    # comments, module-level assignments) that appear between blocks and would
    # otherwise be dropped when groups are split across chunks.
    prev_end      = preamble_end   # -1 if no preamble, else index of last preamble line
    group_start   = -1
    group_end     = -1
    group_symbols: list[str] = []

    def flush_group() -> None:
        nonlocal chunk_idx, group_start, group_end, group_symbols
        if group_start >= 0:
            text = "\n".join(lines[group_start: group_end + 1])
            if text.strip():
                chunks.append(_make_chunk(
                    text, rel_path,
                    group_start, group_end,
                    language, chunk_idx, group_symbols,
                ))
                chunk_idx += 1
        group_start, group_end, group_symbols = -1, -1, []

    for start, end, name in blocks:
        block_span  = end - start + 1
        unit_start  = prev_end + 1   # first line not yet in any chunk

        if block_span > CHUNK_SIZE:
            # Oversized single block: flush pending group, then split the entire
            # unit (leading gap + block) via line_chunk so nothing is dropped.
            flush_group()
            sub = line_chunk(
                lines[unit_start: end + 1], rel_path, language,
                line_offset=unit_start,
                start_chunk_idx=chunk_idx,
                symbols=[name],
            )
            chunks.extend(sub)
            chunk_idx += len(sub)
            prev_end = end

        elif group_start == -1:
            # Start a new group from the first uncovered line (covers leading gap)
            group_start   = unit_start
            group_end     = end
            group_symbols = [name]
            prev_end      = end

        elif end - group_start + 1 <= CHUNK_SIZE:
            # Adding this block keeps total span within CHUNK_SIZE.
            # Gap lines between group_end and start are auto-included by
            # lines[group_start:group_end+1] when we flush.
            group_end = end
            group_symbols.append(name)
            prev_end  = end

        else:
            # Would exceed CHUNK_SIZE — flush, then start new group from unit_start
            # so the gap between the old group and this block goes into the new chunk.
            flush_group()
            group_start   = unit_start
            group_end     = end
            group_symbols = [name]
            prev_end      = end

    flush_group()

    # Tail: any remaining lines after the last block (e.g. `if __name__ == "__main__":`,
    # trailing module-level comments). prev_end tracks exactly where we stopped.
    file_end = len(lines) - 1
    if prev_end < file_end:
        tail_text = "\n".join(lines[prev_end + 1: file_end + 1])
        if tail_text.strip():
            chunks.append(_make_chunk(
                tail_text, rel_path,
                prev_end + 1, file_end,
                language, chunk_idx, ["(tail)"],
            ))

    return chunks


# ── Contextual embedding header ────────────────────────────────────────────────

def build_embed_text(chunk: dict) -> str:
    """
    Build the text to embed for a code chunk.

    Combines two techniques:
    1. nomic task prefix ("search_document: ") — tells the model this is a
       document being indexed, not a query, activating the right embedding mode.
    2. Contextual header — file path + symbol names prepended so the embedding
       vector reflects file identity, not just code semantics.

    Neither the prefix nor the header is stored in ChromaDB — only the clean
    code goes into the document field.

    Example:
        search_document: # [python] server/api/views/auth_views.py lines 45-125 | login_view
        def login_view(request): ...
    """
    symbols_part = f" | {chunk['symbols']}" if chunk.get("symbols") else ""
    header = (
        f"# [{chunk['language']}] {chunk['file_path']} "
        f"lines {chunk['start_line']}-{chunk['end_line']}{symbols_part}"
    )
    return f"{EMBED_DOC_PREFIX}{header}\n{chunk['content']}"


# ── Index helpers ──────────────────────────────────────────────────────────────

def delete_file_chunks(collection, rel_path: str) -> None:
    try:
        existing = collection.get(where={"file_path": {"$eq": rel_path}})
        if existing["ids"]:
            collection.delete(ids=existing["ids"])
    except Exception:
        pass


def embed_and_store(collection, model, chunks: list[dict]) -> None:
    """
    Embed chunks using contextual headers for better retrieval quality,
    but store only clean code (no headers) in ChromaDB documents.
    """
    for batch_start in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[batch_start: batch_start + BATCH_SIZE]

        # Contextual header + code → better embedding
        embed_texts = [build_embed_text(c) for c in batch]
        embeddings  = model.encode(embed_texts, show_progress_bar=False).tolist()

        # Clean code → what Claude actually reads
        collection.upsert(
            ids        = [f"{c['file_path']}::{c['chunk_index']}" for c in batch],
            documents  = [c["content"] for c in batch],
            embeddings = embeddings,
            metadatas  = [{
                "file_path":   c["file_path"],
                "start_line":  c["start_line"],
                "end_line":    c["end_line"],
                "language":    c["language"],
                "chunk_index": c["chunk_index"],
                "symbols":     c.get("symbols", ""),
            } for c in batch],
        )


# ── Public chunk_file entry point ─────────────────────────────────────────────

def chunk_file(path: Path) -> list[dict]:
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        print(f"  [skip] {path.name}: {e}")
        return []

    if not content.strip():
        return []

    rel_path = str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")
    language = EXT_LANG.get(path.suffix, "")
    lines    = content.split("\n")

    return smart_chunk(lines, rel_path, language)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    full_reindex = "--full" in sys.argv

    print(f"Project root : {PROJECT_ROOT}")
    print(f"DB path      : {DB_PATH}")
    print(f"Mode         : {'FULL re-index' if full_reindex else 'incremental'}\n")

    print("Loading embedding model...")
    model = SentenceTransformer(MODEL_NAME, trust_remote_code=True)
    model.max_seq_length = 8192   # unlock full context window
    print("Model ready.\n")

    DB_PATH.mkdir(exist_ok=True)
    client = chromadb.PersistentClient(path=str(DB_PATH))

    if full_reindex:
        try:
            client.delete_collection(COLLECTION)
            print("Cleared existing index.\n")
        except Exception:
            pass
        manifest: dict[str, float] = {}
        collection = client.create_collection(
            COLLECTION,
            metadata={"hnsw:space": "cosine"},   # accurate relevance percentages
        )
    else:
        manifest   = load_manifest()
        collection = client.get_or_create_collection(
            COLLECTION,
            metadata={"hnsw:space": "cosine"},
        )

    current_files: dict[str, float] = {}
    for file_path in iter_source_files():
        rel = str(file_path.relative_to(PROJECT_ROOT)).replace("\\", "/")
        current_files[rel] = file_path.stat().st_mtime

    changed = [p for p, mt in current_files.items() if mt != manifest.get(p)]
    deleted = [p for p in manifest if p not in current_files]

    if not full_reindex and not changed and not deleted:
        print("Index is up to date. Nothing to do.")
        print(f"  {collection.count():,} chunks across {len(current_files)} files.")
        return

    print(f"Changed / new : {len(changed)} files")
    print(f"Deleted       : {len(deleted)} files\n")

    for rel_path in deleted:
        delete_file_chunks(collection, rel_path)
        del manifest[rel_path]
        print(f"  [removed] {rel_path}")

    total_new_chunks = 0
    for i, rel_path in enumerate(sorted(changed), 1):
        abs_path = PROJECT_ROOT / rel_path
        chunks   = chunk_file(abs_path)

        if not full_reindex:
            delete_file_chunks(collection, rel_path)

        if chunks:
            embed_and_store(collection, model, chunks)
            total_new_chunks += len(chunks)
            manifest[rel_path] = current_files[rel_path]
            label = "({} chunk{})".format(len(chunks), "s" if len(chunks) > 1 else "")
            print(f"  [{i:3d}/{len(changed)}] {rel_path} {label}")
        else:
            print(f"  [empty]   {rel_path}")

    save_manifest(manifest)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    (Path(__file__).parent / "last_indexed.txt").write_text(ts, encoding="utf-8")

    print(f"\nDone at {ts}")
    print(f"  +{total_new_chunks} new chunks  |  {collection.count():,} total in index")


if __name__ == "__main__":
    main()
