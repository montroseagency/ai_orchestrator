#!/usr/bin/env python3
"""
Comprehensive test suite for the RAG MCP indexer and server logic.
Run: PYTHONUTF8=1 python test_rag.py
"""

import sys
import textwrap
import traceback
from pathlib import Path

# ── Bootstrap ─────────────────────────────────────────────────────────────────
RAG_DIR      = Path(__file__).parent
PROJECT_ROOT = RAG_DIR.parent.parent
sys.path.insert(0, str(RAG_DIR))

# Inline the constants so tests are self-contained
CHUNK_SIZE = 80

PASS = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"
WARN = "\033[93m!\033[0m"

results: list[tuple[str, bool, str]] = []   # (name, passed, detail)


def test(name: str, cond: bool, detail: str = ""):
    icon = PASS if cond else FAIL
    print(f"  {icon} {name}" + (f"  [{detail}]" if detail else ""))
    results.append((name, cond, detail))


def section(title: str):
    print(f"\n{'─'*60}")
    print(f"  {title}")
    print(f"{'─'*60}")


# ── Import indexer ─────────────────────────────────────────────────────────────
section("Importing indexer module")
try:
    from indexer import (
        extract_python_blocks,
        extract_ts_blocks,
        smart_chunk,
        line_chunk,
        build_embed_text,
        chunk_file,
        _make_chunk,
    )
    test("indexer imports successfully", True)
except Exception as e:
    test("indexer imports successfully", False, str(e))
    print(f"\n  FATAL: Cannot import indexer. Aborting.\n  {e}")
    sys.exit(1)


# ══════════════════════════════════════════════════════════════════════════════
# 1. extract_python_blocks
# ══════════════════════════════════════════════════════════════════════════════
section("1. extract_python_blocks")

py_simple = textwrap.dedent("""\
    import os

    MY_CONST = 42

    def foo(x):
        return x + 1

    class Bar:
        def method(self):
            pass

    def baz():
        pass
""")

blocks = extract_python_blocks(py_simple.split("\n"))
names  = [b[2] for b in blocks]
test("detects 3 top-level definitions", len(blocks) == 3, str(names))
test("foo is first",  names[0] == "foo")
test("Bar is second", names[1] == "Bar")
test("baz is third",  names[2] == "baz")
test("blocks are sorted by line", all(blocks[i][0] < blocks[i+1][0] for i in range(len(blocks)-1)))

# Decorator handling
py_decorated = textwrap.dedent("""\
    from functools import wraps

    def decorator(fn):
        @wraps(fn)
        def inner(*a, **kw):
            return fn(*a, **kw)
        return inner

    @decorator
    @decorator
    def my_view():
        pass
""")

blocks_dec = extract_python_blocks(py_decorated.split("\n"))
names_dec  = [b[2] for b in blocks_dec]
test("detects decorator + inner function", len(blocks_dec) == 2, str(names_dec))

if blocks_dec:
    my_view = next((b for b in blocks_dec if b[2] == "my_view"), None)
    if my_view:
        # my_view should start at the first @decorator line, not at `def my_view`
        lines_d = py_decorated.split("\n")
        start_content = lines_d[my_view[0]].strip()
        test("my_view block starts at @decorator line", start_content.startswith("@"), start_content)
    else:
        test("my_view block starts at @decorator line", False, "my_view not found in blocks")

# Syntax error falls back gracefully
py_broken = "def foo(:\n    pass\n"
blocks_broken = extract_python_blocks(py_broken.split("\n"))
test("returns [] on SyntaxError", blocks_broken == [])

# Empty file
blocks_empty = extract_python_blocks([""])
test("returns [] for empty file", blocks_empty == [])

# File with only imports (no functions/classes)
py_imports_only = "import os\nimport sys\nX = 5\n"
blocks_imports = extract_python_blocks(py_imports_only.split("\n"))
test("returns [] for imports-only file", blocks_imports == [])


# ══════════════════════════════════════════════════════════════════════════════
# 2. extract_ts_blocks
# ══════════════════════════════════════════════════════════════════════════════
section("2. extract_ts_blocks")

ts_simple = textwrap.dedent("""\
    import React from 'react'
    import { useState } from 'react'

    export const MyComponent = () => {
      const [count, setCount] = useState(0)
      return <div>{count}</div>
    }

    export function helperFn(x: number): number {
      return x * 2
    }

    export type MyType = {
      id: number
      name: string
    }

    export interface MyInterface {
      run(): void
    }
""")

ts_blocks = extract_ts_blocks(ts_simple.split("\n"))
ts_names  = [b[2] for b in ts_blocks]
test("detects TS exports", len(ts_blocks) >= 4, str(ts_names))
test("MyComponent detected", "MyComponent" in ts_names)
test("helperFn detected",    "helperFn"    in ts_names)
test("MyType detected",      "MyType"      in ts_names)
test("MyInterface detected", "MyInterface" in ts_names)

# TS: blocks should be contiguous (no gaps)
if ts_blocks:
    ts_lines = ts_simple.split("\n")
    # Every line from first block to last block should be covered
    first_block_start = ts_blocks[0][0]
    last_block_end    = ts_blocks[-1][1]
    all_covered = set()
    for s, e, _ in ts_blocks:
        all_covered.update(range(s, e + 1))
    expected_range = set(range(first_block_start, last_block_end + 1))
    uncovered = expected_range - all_covered
    test("no lines dropped between TS blocks", len(uncovered) == 0, f"uncovered: {uncovered}")

# Non-exported functions
ts_noexport = textwrap.dedent("""\
    function helper() {
      return 1
    }

    export function main() {
      return helper()
    }
""")
ts_ne = extract_ts_blocks(ts_noexport.split("\n"))
ne_names = [b[2] for b in ts_ne]
test("detects non-exported functions too", "helper" in ne_names, str(ne_names))

# Empty file
ts_empty = extract_ts_blocks([""])
test("returns [] for empty TS file", ts_empty == [])


# ══════════════════════════════════════════════════════════════════════════════
# 3. smart_chunk — line coverage
# ══════════════════════════════════════════════════════════════════════════════
section("3. smart_chunk — no lines dropped")

def check_coverage(source: str, language: str, label: str):
    lines  = source.split("\n")
    chunks = smart_chunk(lines, f"test/{label}", language)
    if not chunks:
        test(f"{label}: produces chunks", False, "no chunks returned")
        return

    # Coverage: every meaningful line should appear in at least one chunk
    covered_lines: set[int] = set()
    for c in chunks:
        s = c["start_line"] - 1   # back to 0-indexed
        e = c["end_line"]   - 1
        covered_lines.update(range(s, e + 1))

    total_lines = len(lines)
    dropped     = set(range(total_lines)) - covered_lines
    # Trailing blank lines at the very end of the file are OK to omit
    meaningful_dropped = {ln for ln in dropped if ln < total_lines and lines[ln].strip()}

    test(f"{label}: no meaningful lines dropped",
         len(meaningful_dropped) == 0,
         f"dropped lines: {sorted(meaningful_dropped)[:10]}")

    # Duplicate line ranges: only flag if NOT caused by intentional line_chunk overlap.
    # line_chunk is used for large blocks and always overlaps by CHUNK_OVERLAP lines,
    # so duplicates there are expected. We only flag duplicates in AST-chunked sections.
    duplicate_lines: set[int] = set()
    seen: set[int] = set()
    for c in chunks:
        # Skip chunks from line_chunk fallback (identified by (preamble)/(tail) absence
        # and consecutive chunk indices over the same range — use a simpler heuristic:
        # if symbols contain only one entry and the chunk spans nearly CHUNK_SIZE, it's
        # probably a line_chunk sub-chunk of a large block. Allow overlap there.
        syms = c.get("symbols", "")
        is_line_chunk_sub = (syms.count(",") == 0 and syms not in ("(preamble)", "(tail)", ""))
        # Simpler: just skip duplicate check for line_chunk sub-chunks within large blocks
        s = c["start_line"] - 1
        e = c["end_line"]   - 1
        span = e - s + 1
        if span >= 60 and not is_line_chunk_sub:
            # likely a large-block line_chunk — allow overlap
            continue
        for ln in range(s, e + 1):
            if ln in seen:
                duplicate_lines.add(ln)
            seen.add(ln)

    test(f"{label}: no unexpected duplicate ranges",
         len(duplicate_lines) == 0,
         f"duplicated: {sorted(duplicate_lines)[:10]}")
    test(f"{label}: chunk symbols populated",
         all(c.get("symbols", "") != "" for c in chunks),
         f"empty symbols in {sum(1 for c in chunks if not c.get('symbols',''))}/{len(chunks)} chunks")

check_coverage(py_simple,    "python", "py_simple")
check_coverage(py_decorated, "python", "py_decorated")
check_coverage(ts_simple,    "tsx",    "ts_simple")
check_coverage(ts_noexport,  "javascript", "ts_noexport")

# Large python file (forces line-based fallback inside large blocks)
py_large = textwrap.dedent("""\
    import os

    class BigClass:
""") + "\n".join(f"    def method_{i}(self): return {i}" for i in range(200))
# py_large_class: BigClass is one block > CHUNK_SIZE → line_chunk with intentional
# CHUNK_OVERLAP is used. Duplicate line ranges in that case are expected and correct.
lines_large = py_large.split("\n")
chunks_large = smart_chunk(lines_large, "test/py_large_class", "python")
covered_large: set[int] = set()
for c in chunks_large: covered_large.update(range(c["start_line"]-1, c["end_line"]))
ml_dropped = {ln for ln in range(len(lines_large)) if ln not in covered_large and lines_large[ln].strip()}
test("py_large_class: no meaningful lines dropped", len(ml_dropped)==0, f"dropped: {sorted(ml_dropped)[:5]}")
test("py_large_class: produces multiple chunks from line_chunk", len(chunks_large) > 1, f"{len(chunks_large)} chunks")


# ══════════════════════════════════════════════════════════════════════════════
# 4. build_embed_text
# ══════════════════════════════════════════════════════════════════════════════
section("4. build_embed_text")

sample_chunk = {
    "content":     "def login(request):\n    pass",
    "file_path":   "server/api/views/auth_views.py",
    "start_line":  45,
    "end_line":    60,
    "language":    "python",
    "chunk_index": 3,
    "symbols":     "login, logout",
}
embed_text = build_embed_text(sample_chunk)
test("header contains file path",   "server/api/views/auth_views.py" in embed_text)
test("header contains language",    "[python]"  in embed_text)
test("header contains line range",  "45-60"     in embed_text)
test("header contains symbols",     "login"     in embed_text)
test("code appears after header",   "def login" in embed_text)
test("header is first line",        "# [" in embed_text.split("\n")[0])

no_symbol_chunk = {**sample_chunk, "symbols": ""}
embed_no_sym = build_embed_text(no_symbol_chunk)
test("no symbol separator when symbols is empty", " | " not in embed_no_sym.split("\n")[0])


# ══════════════════════════════════════════════════════════════════════════════
# 5. chunk_file on real project files
# ══════════════════════════════════════════════════════════════════════════════
section("5. chunk_file on real project files")

real_files = [
    PROJECT_ROOT / "server/api/views/auth_views.py",
    PROJECT_ROOT / "server/api/models.py",
    PROJECT_ROOT / "client/lib/auth-context.tsx",
    PROJECT_ROOT / "client/lib/api.ts",
    PROJECT_ROOT / "services/realtime/src/services/SocketService.js",
]

for fp in real_files:
    if not fp.exists():
        print(f"  {WARN} Skipping missing: {fp.name}")
        continue
    try:
        chunks = chunk_file(fp)
        lines  = fp.read_text(encoding="utf-8", errors="replace").split("\n")
        label  = fp.name

        test(f"{label}: produces chunks", len(chunks) > 0, f"{len(chunks)} chunks")

        # Coverage check
        covered: set[int] = set()
        for c in chunks:
            covered.update(range(c["start_line"] - 1, c["end_line"]))
        meaningful_dropped = {
            ln for ln in range(len(lines))
            if ln not in covered and ln < len(lines) and lines[ln].strip()
        }
        test(f"{label}: no meaningful lines dropped",
             len(meaningful_dropped) == 0,
             f"dropped: {len(meaningful_dropped)}" if meaningful_dropped else "")

        # Chunk size sanity
        max_chunk = max(c["end_line"] - c["start_line"] + 1 for c in chunks)
        test(f"{label}: max chunk ≤ {CHUNK_SIZE*2} lines",
             max_chunk <= CHUNK_SIZE * 2,
             f"max={max_chunk}")

        # Symbol coverage
        chunks_with_sym = sum(1 for c in chunks if c.get("symbols"))
        pct = chunks_with_sym / len(chunks) * 100
        test(f"{label}: >50% chunks have symbols",
             pct > 50,
             f"{pct:.0f}% ({chunks_with_sym}/{len(chunks)})")

    except Exception as e:
        test(f"{fp.name}: no exception", False, str(e))
        traceback.print_exc()


# ══════════════════════════════════════════════════════════════════════════════
# 6. ChromaDB connectivity and search quality
# ══════════════════════════════════════════════════════════════════════════════
section("6. ChromaDB connectivity + search quality")

try:
    import chromadb
    from sentence_transformers import SentenceTransformer

    DB_PATH    = RAG_DIR / "chroma_db"
    COLLECTION = "codebase"

    client = chromadb.PersistentClient(path=str(DB_PATH))

    # Check collection exists
    try:
        col   = client.get_collection(COLLECTION)
        count = col.count()
        test("ChromaDB collection exists", True, f"{count:,} chunks")
    except Exception as e:
        test("ChromaDB collection exists", False, str(e))
        raise

    # Spot-check: symbol metadata present in some chunks
    sample = col.get(limit=50, include=["metadatas"])
    metas  = sample["metadatas"]
    with_symbols    = sum(1 for m in metas if m.get("symbols"))
    test("symbol metadata present in sampled chunks",
         with_symbols > 0,
         f"{with_symbols}/{len(metas)} have symbols")

    # Spot-check: distance metric
    # Check if the collection was created with cosine space
    col_metadata = col.metadata or {}
    space = col_metadata.get("hnsw:space", "l2")
    test("collection uses cosine distance",
         space == "cosine",
         f"actual: {space} — run indexer --full after applying cosine fix")

    # Semantic search test
    emb_model = SentenceTransformer("nomic-ai/nomic-embed-text-v1.5", trust_remote_code=True)
    emb_model.max_seq_length = 8192
    queries = [
        ("JWT authentication login",        "auth"),
        ("WebSocket realtime socket",       "socket"),
        ("Celery background task",          "celery"),
        ("PayPal billing payment invoice",   "billing"), # paypal_billing_views.py
    ]
    for q_text, expected_keyword in queries:
        try:
            emb = emb_model.encode(["search_query: " + q_text]).tolist()
            res = col.query(
                query_embeddings=emb,
                n_results=5,
                include=["metadatas", "distances"],
            )
            top_paths = [m["file_path"] for m in res["metadatas"][0]]
            top_dist  = res["distances"][0][0] if res["distances"][0] else 999
            # At least one result should mention the expected keyword
            keyword_found = any(expected_keyword.lower() in p.lower() for p in top_paths)
            test(f'search "{q_text}" → keyword in top-5',
                 keyword_found,
                 f"top: {top_paths[0] if top_paths else 'none'}  dist={top_dist:.3f}")
        except Exception as e:
            test(f'search "{q_text}"', False, str(e))

    # Symbol search test — uses where_document (correct ChromaDB API for text search)
    symbol_tests = [
        ("login",        "auth"),
        ("Notification", "notification"),
    ]
    for sym, keyword in symbol_tests:
        try:
            sym_res = col.get(
                where_document={"$contains": sym},
                include=["metadatas"],
                limit=5,
            )
            paths = [m["file_path"] for m in sym_res["metadatas"]]
            found_any = len(paths) > 0
            keyword_match = any(keyword.lower() in p.lower() for p in paths)
            test(f'symbol search "{sym}" → results found',  found_any, f"paths: {paths[:2]}")
            test(f'symbol search "{sym}" → relevant file', keyword_match, f"paths: {paths[:2]}")
        except Exception as e:
            test(f'symbol search "{sym}"', False, str(e))

except ImportError as e:
    test("chromadb/sentence_transformers available", False, str(e))
except Exception as e:
    test("ChromaDB tests", False, str(e))
    traceback.print_exc()


# ══════════════════════════════════════════════════════════════════════════════
# 7. _apply_threshold_and_mmr logic (inline test)
# ══════════════════════════════════════════════════════════════════════════════
section("7. _apply_threshold_and_mmr logic")

MIN_RELEVANCE = 0.25   # matches updated server.py constant
MAX_PER_FILE  = 2

def apply_threshold_and_mmr_inline(results: dict, n_results: int):
    docs      = results["documents"][0]
    metas     = results["metadatas"][0]
    distances = results["distances"][0]
    file_counts: dict = {}
    output = []
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

def make_fake(docs, paths, dists):
    return {
        "documents": [docs],
        "metadatas": [[{"file_path": p, "start_line": 1, "end_line": 10, "language": "py", "symbols": ""} for p in paths]],
        "distances":  [dists],
    }

# With cosine distance: dist=0.8 → relevance=20% → below 25% threshold
r = apply_threshold_and_mmr_inline(
    make_fake(["a", "b"], ["f1.py", "f2.py"], [0.8, 0.5]), 10)
test("filters out low-relevance chunks (dist=0.8 → 20%, threshold=25%)", len(r) == 1)
test("keeps high-relevance chunks (dist=0.5 → 50%)", len(r) == 1 and abs(r[0][2] - 50.0) < 0.01)

# MMR: 3 chunks from same file → only 2 kept
r2 = apply_threshold_and_mmr_inline(
    make_fake(["a","b","c"], ["same.py","same.py","same.py"], [0.1, 0.2, 0.3]), 10)
test("MMR limits chunks per file to 2", len(r2) == 2)

# n_results cap
r3 = apply_threshold_and_mmr_inline(
    make_fake(["a","b","c","d"], ["f1.py","f2.py","f3.py","f4.py"], [0.1,0.2,0.3,0.4]), 2)
test("respects n_results cap", len(r3) == 2)


def pytest_approx(val, rel=0.01):
    """Trivial approx check used inline."""
    return val   # just return value; test uses == comparison above


# ══════════════════════════════════════════════════════════════════════════════
# Summary
# ══════════════════════════════════════════════════════════════════════════════
section("SUMMARY")
passed = sum(1 for _, ok, _ in results if ok)
total  = len(results)
failed = [(n, d) for n, ok, d in results if not ok]

print(f"\n  {passed}/{total} tests passed")
if failed:
    print(f"\n  FAILURES:")
    for name, detail in failed:
        print(f"    {FAIL} {name}" + (f"  [{detail}]" if detail else ""))
print()
sys.exit(0 if not failed else 1)
