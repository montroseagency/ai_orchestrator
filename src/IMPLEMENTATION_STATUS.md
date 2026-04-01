# Self-Improving Agent Architecture - Implementation Status

## Overview

This document tracks the implementation of the self-improving agent architecture with full coordination for the ai_orchestrator project.

---

## Current Progress

### Completed Files

| File | Status | Description |
|------|--------|-------------|
| `src/rag/__init__.py` | ✅ Done | Module exports and docstring |
| `src/rag/server.py` | ✅ Done | RAG MCP server with ChromaDB, 4 collections, all tools |
| `src/rag/session_indexer.py` | ✅ Done | Session indexing with pre-computed summaries |
| `src/rag/lesson_extractor.py` | ✅ Done | Lesson extraction from successful retries + PatternDetector |
| `src/agents/base.py` | ✅ Fixed | Added missing `Path` import |

### Pending Files

| File | Status | Description |
|------|--------|-------------|
| `src/rag/retriever.py` | ⏳ Pending | Hierarchical retrieval with caching (3 detail levels) |
| `src/rag/deduplicator.py` | ⏳ Pending | Semantic deduplication of lessons |
| `src/rag/budget.py` | ⏳ Pending | Token budget enforcement per agent |
| `src/coordination/__init__.py` | ⏳ Pending | Coordination module init |
| `src/coordination/messages.py` | ⏳ Pending | AgentMessage protocol |
| `src/coordination/router.py` | ⏳ Pending | MessageRouter for inter-agent communication |
| `src/conductor.py` | ⏳ Pending | Add RAG hooks + coordination integration |
| `src/context_builder.py` | ⏳ Pending | Add BudgetedContextBuilder + historical context |
| `src/agents/base.py` | ⏳ Pending | Add outbox, ask(), constrain() methods |
| `src/session.py` | ⏳ Pending | Add on_complete() hook for indexing |
| `src/config.py` | ⏳ Pending | Add all optimization settings |

### Directory Structure Created

```
ai_orchestrator/
├── src/
│   ├── rag/                          # ✅ Created
│   │   ├── __init__.py               # ✅ Done
│   │   ├── server.py                 # ✅ Done
│   │   ├── session_indexer.py        # ✅ Done
│   │   ├── lesson_extractor.py       # ✅ Done
│   │   ├── retriever.py              # ⏳ Pending
│   │   ├── deduplicator.py           # ⏳ Pending
│   │   ├── budget.py                 # ⏳ Pending
│   │   └── chroma_db/                # Auto-created on first run
│   ├── coordination/                 # ✅ Created (empty)
│   │   ├── __init__.py               # ⏳ Pending
│   │   ├── messages.py               # ⏳ Pending
│   │   └── router.py                 # ⏳ Pending
│   └── improvement/                  # ✅ Created (empty)
├── _vibecoding_brain/
│   ├── agents/
│   │   ├── patches/                  # ✅ Created (for auto-generated patches)
│   │   └── profiles/                 # ✅ Created (for agent specialization)
│   ├── patterns/                     # ✅ Created (for error/solution catalogs)
│   └── sessions/                     # ✅ Created (session storage)
```

---

## What's Been Implemented

### 1. RAG Server (`src/rag/server.py`)

**ChromaDB Collections:**
- `codebase` - Source code search
- `sessions` - Past task prompts + outcomes
- `patterns` - Error/solution patterns
- `lessons` - Specific learnings from fixes

**MCP Tools:**
- `index_session()` - Store completed session with metadata
- `search_sessions()` - Find similar past tasks (with caching)
- `get_session()` - Get full session details
- `record_lesson()` - Store a lesson/pattern
- `search_lessons()` - Search lessons by topic
- `record_pattern()` - Store error/solution pattern
- `search_patterns()` - Search patterns
- `rag_status()` - Get system status

**Features:**
- Query caching with 5-minute TTL
- Cosine similarity search
- Embedding via Ollama (nomic-embed-text) or sentence-transformers fallback
- Singleton pattern for client access

### 2. Session Indexer (`src/rag/session_indexer.py`)

**Pre-indexed Summaries:**
- Generates 150-token summary at index time (not query time)
- Uses claude-haiku-4-5 for fast summarization
- Extracts files touched from implementation logs
- Categorizes review issues automatically

**Features:**
- `index_session(session_dir)` - Index a single session
- `backfill_all_sessions()` - Backfill existing sessions
- CLI: `python -m src.rag.session_indexer --backfill`

### 3. Lesson Extractor (`src/rag/lesson_extractor.py`)

**Lesson Extraction:**
- Finds consecutive review attempts (review_attempt_N.md)
- Extracts fix instructions from failed reviews
- Categorizes issues (typescript_any_type, missing_error_handling, etc.)
- Calculates confidence scores

**Pattern Detection:**
- `PatternDetector.find_recurring_patterns()` - Find issues that recur 3+ times
- `PatternDetector.generate_patch_content()` - Generate prompt patches

**Issue Categories:**
- typescript_any_type
- missing_error_handling
- missing_loading_state
- missing_validation
- accessibility
- security
- performance
- import_error
- type_mismatch
- missing_tests

---

## What's Still Needed

### Token Optimization Components

**retriever.py** - Hierarchical retrieval:
```python
class ProgressiveRetriever:
    async def get_context(prompt, detail_level=1):
        # Level 1: Metadata only (5-10 tokens per session)
        # Level 2: Pre-indexed summaries (50-100 tokens per session)
        # Level 3: Full artifacts (only if needed)
```

**deduplicator.py** - Semantic deduplication:
```python
class SemanticDeduplicator:
    async def dedupe_lessons(lessons):
        # Remove lessons >80% similar to already-kept ones
```

**budget.py** - Token budget enforcement:
```python
TOKEN_BUDGETS = {
    "conductor": 100,
    "planner": 300,
    "creative_brain": 200,
    "implementer": 150,
    "reviewer": 100,
}

class BudgetEnforcer:
    def enforce(agent_type, context):
        # Truncate to budget, keeping complete sentences
```

### Agent Coordination

**messages.py** - Message protocol:
```python
@dataclass
class AgentMessage:
    from_agent: str
    to_agent: str
    type: Literal["QUESTION", "CONSTRAINT", "SUGGESTION", ...]
    content: str
    requires_response: bool
    priority: Literal["low", "normal", "high"]
```

**router.py** - Message routing:
```python
class MessageRouter:
    async def route(message: AgentMessage) -> AgentResponse
    async def negotiate(initiator, question, max_rounds=3)
```

### Integration Changes

**conductor.py** additions:
```python
class Conductor:
    def __init__(self):
        self.rag = get_rag_client()
        self.router = MessageRouter(self)

    async def run(self, prompt):
        # Before classification: query similar sessions
        similar = await self.rag.search_sessions(prompt, n=3)
        historical_context = self._format_historical_context(similar)

        # ... run pipeline ...

        # After completion: index this session
        await SessionIndexer().index_session(session.session_dir)
```

**context_builder.py** additions:
```python
class ContextBuilder:
    def for_planner(self, prompt, classification, historical=None):
        base = self._base_planner_context(prompt, classification)
        if historical:
            base += self._format_historical_section(historical)
        return BudgetEnforcer().enforce("planner", base)
```

**base.py** additions:
```python
class BaseAgent:
    def __init__(self):
        self.outbox: list[AgentMessage] = []
        self.can_communicate_with: list[str] = []

    def ask(self, target, question, msg_type="QUESTION"):
        self.outbox.append(AgentMessage(...))

    def constrain(self, target, constraint):
        self.outbox.append(AgentMessage(type="CONSTRAINT", ...))
```

**config.py** additions:
```python
# RAG Integration
ENABLE_HISTORICAL_CONTEXT = True
MAX_SIMILAR_SESSIONS = 5
MIN_RELEVANCE_THRESHOLD = 0.50
SIMILARITY_DEDUPE_THRESHOLD = 0.80

# Token Optimization
ENABLE_PREINDEX_SUMMARIES = True
PREINDEX_SUMMARY_TOKENS = 150
ENABLE_QUERY_CACHE = True
QUERY_CACHE_TTL = 300

# Token budgets per agent
TOKEN_BUDGETS = {
    "conductor": 100,
    "planner": 300,
    "creative_brain": 200,
    "implementer": 150,
    "reviewer": 100,
}

# Learning
LESSON_EXTRACTION_ENABLED = True
PATCH_GENERATION_THRESHOLD = 3
```

---

## Data Flow (Target Architecture)

```
┌─────────────────────────────────────────────────────────────┐
│                     NEW SESSION STARTS                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  1. QUERY SIMILAR SESSIONS                                   │
│     search_sessions("add dark mode toggle")                  │
│     → Returns: 3 similar past sessions with outcomes         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  2. INJECT HISTORICAL CONTEXT (with token budgets)           │
│     Planner receives: "Similar task X took approach Y..."    │
│     Implementer receives: "Common issue: don't use 'any'"    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  3. RUN PIPELINE (with coordination)                         │
│     Conductor → Planner → Creative + Implementer → Reviewer  │
│     Agents can ask(), constrain(), negotiate()               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  4. INDEX COMPLETED SESSION                                  │
│     index_session(session_dir)                               │
│     → Stores: prompt, outcome, files, review issues          │
│     → Pre-computes 150-token summary                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  5. EXTRACT LESSONS (if retry succeeded)                     │
│     record_lesson({issue, fix_that_worked, context})         │
│     → Future sessions can retrieve this lesson               │
└─────────────────────────────────────────────────────────────┘
```

---

## Dependencies to Add

```
# requirements.txt additions
chromadb>=0.4.0
sentence-transformers>=2.2.0  # Fallback embeddings
ollama>=0.1.0                 # Primary embeddings (optional)
```

---

## Verification Steps (When Complete)

1. **Index existing sessions**:
   ```bash
   python -m src.rag.session_indexer --backfill
   ```

2. **Test session search**:
   ```python
   from src.rag import get_rag_client
   rag = get_rag_client()
   results = rag.search_sessions("add user authentication")
   print(results)
   ```

3. **Run a task and verify indexing**:
   ```bash
   python vibe.py "add dark mode toggle"
   # Check: sessions collection should have new entry
   ```

4. **Verify historical context injection**:
   - Run a similar task
   - Check Planner context includes "Historical Context" section

5. **Test lesson extraction**:
   - Run a task that requires retry
   - Verify lesson is recorded after success
   - Run similar task and check lesson appears in context

6. **Test agent coordination**:
   - In a task with design + implementation
   - Implementer should question Creative Brain
   - Check: negotiation happens, answer incorporated




⏺ All 6 improvements implemented and integrated. Here's the final summary:

  What Was Added

  New src/improvement/ Module (5 files)

  ┌───────────────────┬────────────────────────────────────────────────────────────────────────┐
  │       File        │                              What It Does                              │
  ├───────────────────┼────────────────────────────────────────────────────────────────────────┤
  │                   │ Runs tests/lint after implementation, formats errors as fix            │
  │ self_healer.py    │ instructions, auto-sends back to implementer. Supports per-file        │
  │                   │ validation, blocking/non-blocking checks, and configurable validators  │
  │                   │ per domain.                                                            │
  ├───────────────────┼────────────────────────────────────────────────────────────────────────┤
  │                   │ LLM-as-Judge using Haiku to score on 4 dimensions: correctness,        │
  │ quality_scorer.py │ completeness, code quality, architecture. Returns strengths,           │
  │                   │ weaknesses, and actionable improvement suggestions.                    │
  ├───────────────────┼────────────────────────────────────────────────────────────────────────┤
  │                   │ Post-task reflection engine that generates structured learnings: what  │
  │ reflection.py     │ worked, what didn't, prompt improvements, AGENTS.md updates. Saved as  │
  │                   │ reflection.md artifact.                                                │
  ├───────────────────┼────────────────────────────────────────────────────────────────────────┤
  │                   │ Error fingerprinting that detects agents stuck in loops (same error 3+ │
  │ stuck_detector.py │  times). Normalizes errors to match similar-but-not-identical          │
  │                   │ failures. Suggests alternative strategies and escalates.               │
  ├───────────────────┼────────────────────────────────────────────────────────────────────────┤
  │                   │ JSONL-based metrics tracking: tokens, pass rates, retry counts,        │
  │ metrics.py        │ healing effectiveness, time per phase. Auto-generates summary.md       │
  │                   │ dashboard.                                                             │
  └───────────────────┴────────────────────────────────────────────────────────────────────────┘

  Pipeline Integration (conductor.py)

  The pipeline now runs:
  Classification → Planning → Implementation → Self-Healing → Review Loop (with stuck detection)
  → Apply Files → Quality Scoring → RAG Indexing → Reflection → Metrics

  Sources:
  - Self-Improving Coding Agents - Addy Osmani
  - The Code Agent Orchestra - Addy Osmani
  - How we built our multi-agent research system - Anthropic
  - Closing the Agentic Coding Loop with Self-Healing Software - LogicStar
  - Demystifying evals for AI agents - Anthropic
  - Self-Evolving Agents - OpenAI Cookbook



7 new files created:                                                                            
  - _vibecoding_brain/agents/ui_ux_tester.md — frontend-only tester prompt                        
  - _vibecoding_brain/agents/backend_tester.md — backend-only tester prompt                       
  - _vibecoding_brain/agents/skills/web_accessibility.md — WCAG 2.1 AA skill (always on for       
  frontend)                                                                                       
  - _vibecoding_brain/agents/skills/code_review.md — Django/DRF patterns skill (always on for     
  backend)                                                                                        
  - _vibecoding_brain/agents/skills/playwright_testing.md — Playwright skill (set                 
  VIBE_PLAYWRIGHT_SERVER_URL to enable)                                                        
  - src/agents/ui_ux_tester_agent.py — UIUXTesterAgent Python class                               
  - src/agents/backend_tester_agent.py — BackendTesterAgent Python class                       
                                                                                                  
  reviewer.md and reviewer_agent.py deleted.                                                      
                                                                                                  
  How skills are loaded:                                                                          
  - API mode: context_builder.for_ui_ux_tester() returns (context, extra_system) — skills injected
   via BaseAgent.call(extra_system=...)                                                           
  - CLI team mode: team_runner._build_agents_json() bakes skills into each agent's prompt before
  passing to --agents                                                                             
  - Playwright: disabled by default — set VIBE_PLAYWRIGHT_SERVER_URL=http://localhost:3000 in .env
   to activate                                                                                    
                                                                                                  
  Routing:                                                                                     
                                                                                                  
  ┌───────────────────────────────┬─────────────────────┐                                         
  │           Task type           │  Testers that run   │                                         
  ├───────────────────────────────┼─────────────────────┤                                         
  │ FRONTEND / DESIGN             │ UI/UX Tester only   │                                         
  ├───────────────────────────────┼─────────────────────┤                                      
  │ BACKEND / DATABASE / REFACTOR │ Backend Tester only │                                         
  ├───────────────────────────────┼─────────────────────┤                                         
  │ FULLSTACK                     │ Both in parallel    │                                         
  ├───────────────────────────────┼─────────────────────┤                                         
  │ TRIVIAL                       │ Backend Tester only │                                      
  └───────────────────────────────┴─────────────────────┘


  