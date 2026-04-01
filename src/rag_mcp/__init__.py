"""
RAG MCP module — Codebase search (MCP server) + cross-session memory.

Components:
- server.py: MCP server for semantic codebase search (runs as stdio process)
- indexer.py: AST-aware code chunking and embedding into ChromaDB
- session_memory.py: Cross-session learning (index/search past task outcomes)
- budget.py: Token budget enforcement for historical context injection
"""
