# Montrroase Agent Team Orchestrator

A self-orchestrating agent team system for building the Montrroase marketing agency SaaS. No Python wrapper, no CLI flags, no environment variables — just Claude Code reading `.md` files and following instructions.

## How It Works

```
cd ai_orchestrator
claude "build: Add a dark mode toggle to the dashboard"
```

Claude reads `CLAUDE.md` on startup, which contains the full orchestration pipeline. The pipeline is **gated** — only messages prefixed with `build:`, `task:`, or `fix:` trigger agent orchestration. All other messages get a normal assistant response.

When triggered, the orchestrator analyzes the task's complexity, domain, and risk, then **adaptively selects** which agents to spawn, what models they run on, and which skills to inject. The RAG MCP server provides semantic codebase search and cross-session memory.

There is no Python orchestration layer. Claude Code **is** the orchestrator.

---

## Architecture

```
ai_orchestrator/
├── CLAUDE.md                          # Master orchestration file (the "brain")
├── DOCUMENTATION.md                   # This file
├── .mcp.json                          # MCP server configuration
├── .claude/settings.local.json        # Claude Code permissions
│
├── _vibecoding_brain/
│   ├── AGENTS.md                      # Project constitution (stack, rules)
│   ├── agents/                        # Agent system prompts
│   │   ├── planner.md                 #   Task decomposition specialist
│   │   ├── creative_brain.md          #   UI/UX design specialist
│   │   ├── implementer.md             #   Code writer
│   │   ├── ui_ux_tester.md            #   Frontend quality gate
│   │   ├── backend_tester.md          #   Backend quality gate
│   │   ├── problem_tracker.md         #   Bug tracking + preventive rules
│   │   └── skills/                    #   Modular skill files (injected at runtime)
│   │       ├── web_accessibility.md   #     WCAG 2.1 AA checklist
│   │       ├── playwright_testing.md  #     E2E browser testing via CDP
│   │       ├── code_review.md         #     Django/DRF anti-patterns + security
│   │       ├── frontend_design.md     #     Montrroase component patterns + AI-slop rules
│   │       ├── ui_ux_pro_max.md       #     50+ styles, 161 palettes, 57 font pairings, 99 UX guidelines
│   │       └── web_design_guidelines.md #   Modern SaaS design standards
│   ├── context/                       # Reference documents
│   │   ├── design_system.md           #   Full design tokens, component patterns
│   │   ├── tech_stack.md              #   Stack decisions, testing, deployment
│   │   └── project_index.md           #   Key files with one-line descriptions
│   ├── problems/                      # Problem prevention system
│   │   ├── rules.md                   #   Learned rules from past bugs (append-only)
│   │   └── active/                    #   In-progress problem tracking
│   └── sessions/                      # Session artifacts (auto-created per task)
│       └── {session_id}/
│           ├── plan.md
│           ├── design_brief.md
│           ├── review.md
│           ├── walkthrough.md
│           └── reflection.md
│
├── src/rag_mcp/                       # RAG MCP Server
│   ├── server.py                      #   8 MCP tools (search + session memory)
│   ├── indexer.py                     #   Codebase indexer (AST-aware chunking)
│   ├── test_rag.py                    #   Tests
│   ├── requirements.txt               #   chromadb, sentence-transformers, mcp
│   ├── chroma_db/                     #   Persistent vector store
│   ├── index_manifest.json            #   File mtime tracking for incremental index
│   └── last_indexed.txt               #   Timestamp of last index run
│
└── Montrroase_website/                # The actual project being built
    ├── client/                        #   Next.js 15 frontend
    └── server/                        #   Django 4 backend
```

---

## Pipeline Gate

The orchestration pipeline only runs when the user's message starts with a prefix:

| Prefix | Purpose | Example |
|---|---|---|
| `build:` | New feature or component | `build: Add a dark mode toggle` |
| `task:` | General pipeline task | `task: refactor the auth middleware` |
| `fix:` | Bug fix or correction | `fix: the sidebar collapses on mobile` |

Messages without a prefix get a normal assistant response (no agents, no session artifacts).

---

## Smart Orchestration

The orchestrator analyzes every gated task across three dimensions before deciding what to do:

### Task Analysis

**Complexity:**
| Level | Criteria | Examples |
|---|---|---|
| TRIVIAL | Single-line or config change | Typo fix, env var change, rename a variable |
| SIMPLE | Single-domain, < 3 files | Add a field to a serializer, new badge component |
| MEDIUM | Multi-file, moderate logic | New page with API endpoint, form with validation |
| COMPLEX | Multi-domain, architectural impact | New module with backend + frontend + real-time |

**Domain:** FRONTEND / BACKEND / FULLSTACK / DESIGN / DATABASE

**Risk:** LOW (isolated) / MEDIUM (new endpoint, model changes) / HIGH (migrations, auth changes, breaking API)

### Adaptive Execution

| Complexity | Strategy | Agents | Artifacts |
|---|---|---|---|
| TRIVIAL | Claude handles directly | None | None |
| SIMPLE | Single specialist + optional tester | 1-2 | Brief walkthrough |
| MEDIUM | Planner → Implementer → Tester(s) | 2-4 | Full |
| COMPLEX | Full team with all relevant agents | 3-5 | Full |

The orchestrator decides which agents are needed — a backend-only task doesn't get Creative Brain, a design-only task doesn't get Backend Tester.

### Model Selection

Each agent runs on a model selected by the orchestrator based on task complexity:

| Agent | SIMPLE | MEDIUM | COMPLEX |
|---|---|---|---|
| planner | sonnet | sonnet | opus |
| creative_brain | sonnet | sonnet | opus |
| implementer | haiku | sonnet | opus |
| ui_ux_tester | haiku | sonnet | sonnet |
| backend_tester | haiku | sonnet | sonnet |
| problem_tracker | haiku | haiku | sonnet |

---

## The Agents

### Planner
**File:** `_vibecoding_brain/agents/planner.md`

Decomposes tasks into structured `plan.md` with acceptance criteria, file lists (MODIFY/CREATE/READ/SKIP), phased task breakdown, risk flags, and constraints. Never writes code. Skipped for TRIVIAL and SIMPLE tasks.

### Creative Brain
**File:** `_vibecoding_brain/agents/creative_brain.md`

Design and UX specialist. Activated only for frontend-visible tasks at MEDIUM+ complexity. Produces `design_brief.md` with component architecture, complete state coverage table, visual specs using Montrroase design tokens, animation specs (Framer Motion), interaction design, and exact UX copy for every user-facing string.

**Skills injected:** `frontend_design.md`, `ui_ux_pro_max.md`, `web_design_guidelines.md`

### Implementer
**File:** `_vibecoding_brain/agents/implementer.md`

Writes production code directly to disk. Follows strict rules:
- **Frontend:** TypeScript, `'use client'` sparingly, React Query, Framer Motion, Phosphor icons, design system compliance
- **Backend:** DRF ViewSets, scoped queries, serializer validation, migrations, services layer, Celery tasks

**Skills injected:** `frontend_design.md` (on frontend tasks)

### UI/UX Tester
**File:** `_vibecoding_brain/agents/ui_ux_tester.md`

Adversarial frontend quality gate. Checks 10+ categories: AI-slop detection, surface hierarchy, brand color discipline, modal quality, animation timing, typography discipline, design system compliance, spacing, TypeScript safety, architecture, accessibility, interaction quality.

**Skills injected:** `web_accessibility.md`, `playwright_testing.md` (when dev server available), `web_design_guidelines.md`

### Backend Tester
**File:** `_vibecoding_brain/agents/backend_tester.md`

Adversarial backend quality gate. Checks correctness, architecture compliance, security, performance, and data integrity.

**Skills injected:** `code_review.md`

### Problem Tracker
**File:** `_vibecoding_brain/agents/problem_tracker.md`

Activated on `fix:` tasks after the fix passes testing. Tracks the problem, root cause, and fix, then writes a preventive rule to `_vibecoding_brain/problems/rules.md` so the same mistake is never repeated. Future sessions read these rules during context gathering.

---

## Skills System

Skills are modular `.md` files in `_vibecoding_brain/agents/skills/` that are injected into agent prompts at runtime by the orchestrator. This keeps agent prompts focused on their core logic while skills remain reusable across agents.

### Available Skills

| Skill | Description | Injected Into |
|---|---|---|
| `web_accessibility.md` | WCAG 2.1 AA: contrast, ARIA, keyboard nav, focus management, forms, reduced motion | ui_ux_tester |
| `playwright_testing.md` | E2E browser testing via CDP: render checks, keyboard nav, mobile viewport, state coverage, screen reader tree | ui_ux_tester |
| `code_review.md` | Django/DRF anti-patterns, N+1 query detection, security checklist, migration safety, Celery rules | backend_tester |
| `frontend_design.md` | Montrroase component patterns, 12 anti-AI-slop rules, surface hierarchy, border-radius scale, typography, spacing | creative_brain, implementer |
| `ui_ux_pro_max.md` | 50+ design styles, 161 color palettes, 57 font pairings, 161 product types, 99 UX guidelines | creative_brain |
| `web_design_guidelines.md` | Modern SaaS design standards (Linear/Vercel aesthetic): information density, progressive disclosure, responsive design, micro-interactions | creative_brain, ui_ux_tester |

### Injection Conditions

| Skill | When Injected |
|---|---|
| `web_accessibility.md` | FRONTEND / FULLSTACK / DESIGN tasks |
| `playwright_testing.md` | Only when dev server URL is available |
| `code_review.md` | BACKEND / FULLSTACK / DATABASE / REFACTOR tasks |
| `frontend_design.md` | FRONTEND / FULLSTACK / DESIGN tasks |
| `ui_ux_pro_max.md` | FRONTEND / FULLSTACK / DESIGN tasks |
| `web_design_guidelines.md` | FRONTEND / FULLSTACK / DESIGN tasks |

### Injection Format
Skills are appended to the agent prompt separated by `---`:
```
[agent prompt content]

---

[skill file contents]
```

---

## Problem Prevention System

The Problem Tracker agent learns from bugs and writes rules to prevent recurrence.

### How It Works
1. User reports a bug with `fix:` prefix
2. The orchestrator fixes the bug through the normal pipeline
3. After the fix passes testing, the Problem Tracker agent is spawned
4. It records the root cause and writes a preventive rule to `_vibecoding_brain/problems/rules.md`
5. Future sessions read these rules during context gathering (Step 4) and pass matching rules to planner and implementer

### Rule Format
```markdown
### RULE-{number}: [DOMAIN] {title}
- **Trigger:** what conditions cause this problem
- **Prevention:** what to check/do to avoid it
- **Files:** relevant file paths
- **Date:** YYYY-MM-DD
```

### Rule Categories
- `[FRONTEND]` — React, Next.js, Tailwind, component patterns
- `[BACKEND]` — Django, DRF, database, API patterns
- `[FULLSTACK]` — Integration issues spanning both layers
- `[INFRA]` — Docker, deployment, environment issues
- `[DESIGN]` — UI/UX, design system violations

---

## The Pipeline Steps

When a gated message triggers the pipeline:

### Step 1 — Analyze & Decide
Assess complexity (TRIVIAL/SIMPLE/MEDIUM/COMPLEX), domain, and risk. Select execution strategy, agents, and models.

### Step 2 — Select Execution Strategy
Choose the right approach based on complexity. TRIVIAL = handle directly. SIMPLE = single agent. MEDIUM/COMPLEX = full pipeline.

### Step 3 — Select Models
Set the `model` parameter for each agent based on complexity (haiku/sonnet/opus).

### Step 4 — Gather Context
- Read AGENTS.md and project_index.md
- Read problem prevention rules from `_vibecoding_brain/problems/rules.md`
- Semantic discovery via MCP tools (`search_codebase`, `search_symbol`, `search_multi`)
- Session memory via `search_past_sessions`
- Read actual source files that will be modified

### Step 5 — Plan (MEDIUM/COMPLEX only)
Planner agent decomposes the task. Output: `plan.md`

### Step 6 — Design Brief (frontend-visible, MEDIUM+ only)
Creative Brain agent produces visual specs. Output: `design_brief.md`

### Step 7 — Implement
Implementer agent (or orchestrator directly for TRIVIAL) writes code to disk.

### Step 7.5 — Self-Healing Validation
Lint/type checks on changed files. Max 2 fix rounds.

### Step 7.75 — Quality Gate Check
Banned AI-slop pattern scan on modified files. Violations trigger re-implementation.

### Step 8 — Test Loop (max 8 iterations)
Tester agent(s) review. FAIL triggers implementer re-spawn with fix instructions. Stuck detection after 3 identical failures.

### Step 9 — Problem Tracking (fix: tasks only)
Problem Tracker agent writes preventive rule after successful fix.

### Step 10 — Wrap Up
Write walkthrough, reflection (MEDIUM+), index session, output JSON summary.

---

## RAG MCP Server

**File:** `src/rag_mcp/server.py`
**Config:** `.mcp.json` (started automatically by Claude Code)

### Codebase Search (6 tools)

| Tool | Purpose |
|---|---|
| `search_codebase` | Semantic search — natural language queries, returns ranked code chunks with relevance % |
| `search_multi` | Batch 2-5 queries in one call, merged and deduplicated |
| `search_symbol` | Exact function/class name lookup in indexed code |
| `get_file` | Read a file with line numbers |
| `list_indexed_files` | Browse what's indexed, optionally filtered by directory |
| `rag_status` | Chunk count, last indexed time, model info |

**How it works:**
- **Embedding model:** `nomic-ai/nomic-embed-text-v1.5` (8192 token context)
- **Vector store:** ChromaDB with cosine distance
- **Chunking:** AST-aware for Python, regex-aware for TypeScript/JavaScript. 80-line target chunks with 15-line overlap.
- **Quality controls:** 25% minimum relevance threshold, max 2 chunks per file per query (MMR deduplication)

### Session Memory (2 tools)

| Tool | Purpose |
|---|---|
| `search_past_sessions` | Find similar past tasks — returns session outcomes, summaries, files touched |
| `index_session` | Store a completed session for future retrieval |

**How it works:**
- Separate `sessions` ChromaDB collection
- 50% minimum relevance threshold (stricter than codebase search)
- Token budget enforcement (300 tokens max) with sentence-aware truncation
- Called at Step 4 (search) and Step 10 (index) of the pipeline

### Indexing the Codebase

```bash
cd ai_orchestrator

# Incremental update (only re-indexes changed files)
python src/rag_mcp/indexer.py

# Full reindex (deletes and rebuilds everything)
python src/rag_mcp/indexer.py --full
```

**Indexed file types:** `.py`, `.ts`, `.tsx`, `.js`, `.jsx`, `.css`, `.md`, `.json`, `.yaml`, `.yml`, `.toml`, `.conf`, `.cfg`, `.ini`, `.html`
**Indexed roots:** `Montrroase_website/` (project code + docs + config) + orchestrator context docs (prefixed `_orchestrator/`)
**Excluded directories:** `node_modules`, `.git`, `dist`, `build`, `.next`, `__pycache__`, `migrations`, `.venv`, `chroma_db`, `monitoring`, `rabbitmq`, `coverage`, `.pytest_cache`, `staticfiles`, `sessions`

---

## MCP Servers

Configured in `.mcp.json`, started automatically when Claude Code launches:

| Server | Purpose |
|---|---|
| `codebase-rag` | Semantic search + session memory (8 tools) |
| `sequential-thinking` | Complex multi-step reasoning for classification edge cases, stuck analysis, architectural decisions |

---

## Key Design Decisions

### Why no Python wrapper?
Claude Code already has the Agent tool for spawning sub-agents, reads CLAUDE.md automatically, and connects to MCP servers. The Python layer (`vibe.py`, `team_runner.py`) was a bootloader — it built JSON agent definitions and launched the CLI. Claude can do this itself by reading `.md` files and following the pipeline instructions in CLAUDE.md.

### Why separate skill files instead of baking them into agents?
Skills are now modular `.md` files in `_vibecoding_brain/agents/skills/`. The orchestrator reads and injects them at runtime based on the task's domain. This makes skills reusable across agents (e.g., `frontend_design.md` goes to both creative_brain and implementer) and keeps agent prompts focused on their core review/implementation logic.

### Why adaptive orchestration instead of fixed pipelines?
The original system mapped each classification to a fixed agent sequence. Now the orchestrator assesses complexity, domain, and risk, then decides what to run. A typo fix doesn't need a planner. A backend endpoint doesn't need a design brief. This eliminates unnecessary agent spawns and makes the system faster for simple tasks while keeping the full pipeline available for complex work.

### Why a Problem Tracker agent?
Bugs that get fixed but not documented tend to recur. The Problem Tracker writes preventive rules after each `fix:` task, creating a growing knowledge base of project-specific anti-patterns. Future sessions read these rules during context gathering, so the implementer and planner know what to avoid before writing code.

### Why session memory in the RAG server?
Session memory was previously handled by Python hooks (`session_memory.py`, `budget.py`) in `team_runner.py`. Now it's exposed as MCP tools (`search_past_sessions`, `index_session`) in the same RAG server. Claude calls them directly at Steps 4 and 10 of the pipeline.

### What replaced the Sentinel?
The Sentinel was a `watchdog`-based file watcher that flagged AI-slop patterns in real-time. Now these patterns are checked at Step 7.75 (Quality Gate Check) in the pipeline. This is better — Claude can both detect AND fix violations, whereas the Sentinel could only log them.

---

## Context Documents

| File | Purpose | When to read |
|---|---|---|
| `_vibecoding_brain/AGENTS.md` | Project constitution — stack, architecture rules, design system summary | Every task (Step 4) |
| `_vibecoding_brain/context/montrroase_guide.md` | Business domain, user roles, features, data flows, infrastructure | Every task (Step 4) |
| `_vibecoding_brain/context/design_system.md` | Full design tokens, component patterns, animation guide | Frontend tasks (Step 6) |
| `_vibecoding_brain/context/tech_stack.md` | Detailed stack decisions, testing, deployment | When needed |
| `_vibecoding_brain/context/project_index.md` | Every key file with one-line description | Every task (Step 4) |
| `_vibecoding_brain/problems/rules.md` | Learned preventive rules from past bugs | Every task (Step 4) |

---

## Session Artifacts

Each task produces artifacts in `_vibecoding_brain/sessions/{session_id}/`:

| File | Source | Content |
|---|---|---|
| `plan.md` | Planner | Task decomposition, file lists, acceptance criteria |
| `design_brief.md` | Creative Brain | Visual specs, state coverage, animations, UX copy |
| `review.md` | Tester | Quality review with verdict and fix instructions |
| `walkthrough.md` | Orchestrator | What was built, files changed, decisions made |
| `reflection.md` | Orchestrator | What went well/poorly, suggestions for improvement |

**Artifact generation is conditional:**
- TRIVIAL: no artifacts
- SIMPLE: walkthrough only
- MEDIUM/COMPLEX: all artifacts

---

## Pipeline Rules

- **Pipeline gate:** Only `build:`, `task:`, `fix:` prefixes trigger the pipeline. Everything else is a normal response.
- **Context compression:** Between agents, outputs are compressed to <200 words. Exception: implementer and tester always receive full file contents.
- **Skill injection:** Skills from `_vibecoding_brain/agents/skills/` are appended to agent prompts based on the skill injection table in CLAUDE.md.
- **Model selection:** Agents run on haiku (simple/fast), sonnet (default), or opus (complex) based on task complexity.
- **Problem prevention:** Rules from past fixes are read during context gathering and passed to planner + implementer.
- **Retry reflection:** On retry N > 1, the implementer gets a reflection prompt asking what specifically failed and whether the same approach is being repeated.
- **Parallel execution:** FULLSTACK testing spawns both ui_ux_tester and backend_tester concurrently.
- **Stuck detection:** Same issue 3 times in a row = stop with status `stuck`.
- **Max iterations:** 8 test-fix cycles before `fail_max_retries`.
- **Self-healing:** Max 2 lint-fix rounds before testing (does not count as test iterations).
