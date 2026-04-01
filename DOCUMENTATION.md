# Vibe Coding Team — Complete Documentation

> A production-grade multi-agent AI orchestration system that takes a single natural-language prompt and routes it through a specialized team of AI agents to produce high-quality, production-ready code.

---

## Table of Contents

1. [What Is This?](#1-what-is-this)
2. [How to Use It](#2-how-to-use-it)
3. [High-Level Architecture](#3-high-level-architecture)
4. [The Pipeline — Step by Step](#4-the-pipeline--step-by-step)
5. [The Agent Team](#5-the-agent-team)
   - [Conductor](#51-conductor)
   - [Planner](#52-planner)
   - [Creative Brain](#53-creative-brain)
   - [Implementer](#54-implementer)
   - [UI/UX Tester](#55-uiux-tester)
   - [Backend Tester](#56-backend-tester)
6. [Native Agent Teams — How It Works](#6-native-agent-teams--how-it-works)
7. [Skills — Injectable Capabilities](#7-skills--injectable-capabilities)
8. [The Brain Directory](#8-the-brain-directory--_vibecoding_brain)
9. [Session Artifacts](#9-session-artifacts)
10. [Quality Systems (Built Into Prompts)](#10-quality-systems-built-into-prompts)
11. [RAG — Codebase Search + Cross-Session Memory](#11-rag--codebase-search--cross-session-memory)
12. [MCP Servers — Tools Available to Agents](#12-mcp-servers--tools-available-to-agents)
13. [Antigravity IDE Integration](#13-antigravity-ide-integration)
14. [The Sentinel — Real-Time Quality Watcher](#14-the-sentinel--real-time-quality-watcher)
15. [Configuration Reference](#15-configuration-reference)
16. [Directory Structure](#16-directory-structure)
17. [Key Source Files](#17-key-source-files)
18. [Testing](#18-testing)
19. [The Design Standard](#19-the-design-standard)

---

## 1. What Is This?

**Vibe Coding Team** is a multi-agent AI system that uses **Claude Code's native Agent Teams**. You give it a task in plain English — e.g., `"Add a dark mode toggle to the dashboard"` — and it orchestrates a team of specialized Claude subagents that plan, design, implement, and test the code automatically, then writes the resulting files to disk.

The system is purpose-built for a specific codebase: **Montrroase** (a marketing agency SaaS built on Next.js 15 + Django 4). Every agent knows the project's architecture rules, design system, and tech stack. It is not a generic code generator — it generates code that is architecturally consistent with an existing system.

**Key capabilities:**
- Classifies tasks by domain (frontend, backend, fullstack, etc.) and selects the minimal agent team needed
- Decomposes complex tasks into atomic steps before any code is written
- Generates complete, production-quality code with no placeholders or TODOs
- Adversarially tests its own output and auto-retries on failure
- Self-healing validation (runs linting/type-checking and fixes errors before testing)
- Learns from past sessions via a RAG (Retrieval-Augmented Generation) memory system
- Generates a human-readable walkthrough of every change made

**Execution model:**
- Uses your **Claude Code subscription** (Pro/Max) — no API key needed
- Launches a single `claude --print` session as the conductor
- The conductor spawns specialized subagents via Claude Code's native **Agent tool**
- Subagents communicate fluidly within the same environment — no subprocess overhead per agent
- Agents can read, write, and edit files directly using Claude Code's built-in tools

---

## 2. How to Use It

### Setup

```bash
# 1. Install Claude Code CLI
npm install -g @anthropic-ai/claude-code
claude login

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. (Optional) Copy and configure environment
cp .env.example .env
```

### Run a Task

```bash
# General usage
python vibe.py "Your task description here"

# Dry-run: see what would change without writing files
python vibe.py "Redesign the sidebar nav" --dry-run

# Help
python vibe.py --help
```

### Configuration (Optional)

All settings have sensible defaults. Override in `.env` if needed:

```bash
# Model: sonnet (default) | opus | haiku
VIBE_CLAUDE_CLI_MODEL=opus

# Effort: low | medium | high (default) | max
VIBE_CLAUDE_CLI_EFFORT=max
```

---

## 3. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Prompt                              │
└─────────────────────────────────┬───────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────┐
│  Python Launcher (thin wrapper — ~200 lines)                    │
│  • Parses CLI args                                              │
│  • Builds --agents JSON from system prompt files                │
│  • Optional: RAG pre-hook (inject historical context)           │
│  • Launches ONE claude --print session                          │
│  • Streams real-time progress as JSON to stdout                 │
│  • Optional: RAG post-hook (index session)                      │
└─────────────────────────────────┬───────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────┐
│  CONDUCTOR (Claude Code native session)                         │
│  Orchestrates the full pipeline using Agent tool:               │
│                                                                 │
│  Step 1: Classify task → select team                            │
│  Step 2: Read project context (AGENTS.md, project files)        │
│  Step 3: Spawn planner ──→ plan.md                              │
│  Step 4: Spawn creative_brain ──→ design_brief.md (if frontend) │
│  Step 5: Spawn implementer ──→ writes files to disk directly    │
│  Step 5.5: Self-heal (run validation via Bash, fix errors)      │
│  Step 6: Spawn tester(s) ──→ PASS/FAIL verdict                 │
│       ┌── FAIL? ──→ retry with fix instructions (max 8 iter) ──┘│
│       ↓ PASS                                                    │
│  Step 7: Write walkthrough.md                                   │
│  Step 8: Write reflection.md                                    │
│  Step 9: Output final JSON summary                              │
└─────────────────────────────────────────────────────────────────┘
```

### Why Native Agent Teams?

Previous versions used Python to orchestrate agents via subprocess calls or API invocations. This had significant limitations:

| Old Approach | Native Agent Teams |
|---|---|
| Each agent = separate subprocess | All agents run within one Claude session |
| Async "email-style" messages | Fluid real-time communication via Agent tool |
| Python manages retry loops | Conductor prompt drives retries natively |
| Context lost in 200-word summaries | Shared optimized internal context |
| 1028 lines of Python orchestration | ~200 lines (thin launcher only) |
| Subprocess spin-up latency per agent | Zero spin-up — agents spawn instantly |
| Required API key OR subscription | Subscription only — simpler setup |

---

## 4. The Pipeline — Step by Step

### Step 1: Classification (Conductor)

The Conductor classifies the task and selects the minimal team:

| Tag | Trigger | Agents Activated |
|-----|---------|-----------------|
| `FRONTEND` | UI component, page, styling, animation | Planner + Creative Brain + Implementer + UI/UX Tester |
| `BACKEND` | API endpoint, model, serializer, URL | Planner + Implementer + Backend Tester |
| `FULLSTACK` | Both frontend + backend changes | Full team (both testers run concurrently) |
| `TRIVIAL` | Typo fix, rename, tiny CSS tweak | Implementer + Tester (skip planning) |
| `DESIGN` | Design-heavy UI overhaul | Creative Brain + Planner + Implementer + UI/UX Tester |
| `DATABASE` | Migration, model change | Planner + Implementer + Backend Tester |
| `REFACTOR` | Code quality, restructure | Planner + Implementer + Backend Tester |

If the task is genuinely ambiguous, the Conductor asks ONE clarifying question before proceeding.

### Step 2: Context Gathering

The Conductor uses its own Read tool to load:
- `_vibecoding_brain/context/AGENTS.md` — architecture rules (always)
- `_vibecoding_brain/context/project_index.md` — file directory
- Specific source files from `Montrroase_website/` that the implementer will need

### Step 3: Planning

The Conductor spawns the `planner` subagent with the task, classification, AGENTS.md content, and relevant file paths. The planner returns `plan.md` with atomic steps, file lists, acceptance criteria, and risk flags. The Conductor writes it to the session directory.

### Step 4: Design (Frontend Only)

The Conductor spawns the `creative_brain` subagent with the task, plan, and design system reference. The creative brain returns `design_brief.md` with precise visual/interaction specs. The Conductor writes it to the session directory.

### Step 5: Implementation

The Conductor spawns the `implementer` subagent with the task, plan, design brief (if frontend), and actual file contents. **The implementer writes files directly to disk** using Claude Code's Write and Edit tools — no JSON blob intermediary. It returns a summary of what was written.

### Step 5.5: Self-Healing Validation

After implementation, the Conductor runs validation commands via its own Bash tool:
- Frontend: `npx tsc --noEmit`, `npx eslint <files>`
- Backend: `python3 -m py_compile <file>`, `python3 -m ruff check <file>`

If validation fails, the Conductor re-spawns the implementer with the error output. Max 2 self-healing rounds before proceeding to testing. This does not count as a test iteration.

### Step 6: Testing (Adversarial Quality Gate)

The Conductor spawns the appropriate tester(s):
- **Frontend/Design:** `ui_ux_tester`
- **Backend/Database/Refactor:** `backend_tester`
- **Fullstack:** Both testers **concurrently** (via parallel Agent tool calls)

Testers return PASS or FAIL with specific fix instructions.

On FAIL, the Conductor:
1. Extracts fix instructions from the test report
2. Injects a reflection prompt before retrying: "What specifically failed? What is ONE concrete change? Are you repeating the same approach?"
3. Re-spawns the implementer with fix instructions
4. Max 8 total iterations before forced stop

**Stuck detection:** If the same core issue appears in 3 consecutive iterations, the Conductor stops and marks status as `stuck`.

### Step 7: Walkthrough

The Conductor writes `walkthrough.md` — a user-facing summary of what was built, why, and what changed.

### Step 8: Reflection

The Conductor writes `reflection.md` — a post-pipeline analysis of what went well, what the tester caught, and suggestions for improvement.

### Step 9: Final Output

The Conductor outputs a structured JSON summary with session_id, status, files written, iterations, verdict, and quality self-assessment. The Python launcher parses this and displays a Rich summary.

---

## 5. The Agent Team

### 5.1 Conductor

**File:** `_vibecoding_brain/agents/conductor_team.md`
**Runs as:** The main Claude Code session (with `--agents` flag)

The master orchestrator. It has full access to Claude Code tools (Read, Write, Edit, Bash, Glob, Grep) plus the ability to spawn subagents. It never writes implementation code itself — it orchestrates.

**Responsibilities:**
- Classify the task (domain tags)
- Select the minimal agent team needed
- Read project context files and pass them to subagents
- Coordinate the full pipeline (plan → design → implement → validate → test → walkthrough)
- Run self-healing validation (linting/type-checking) via Bash
- Detect when the pipeline is stuck (same error 3+ times)
- Inject reflection prompts on retries
- Write session artifacts (plan.md, review.md, walkthrough.md, reflection.md)
- Produce the final JSON summary

---

### 5.2 Planner

**File:** `_vibecoding_brain/agents/planner.md`
**Spawned by:** Conductor via Agent tool

The task decomposition specialist. **Never writes code.**

**Principles:**
- Every step must be atomic (doable in isolation)
- Every file the Implementer needs must be explicitly listed
- No assumptions about file contents — flag unknown files as READ first
- Pattern compliance — all steps follow AGENTS.md rules
- Minimal footprint — resist scope creep
- Risk flags are named prominently (breaking changes, migrations)

---

### 5.3 Creative Brain

**File:** `_vibecoding_brain/agents/creative_brain.md`
**Spawned by:** Conductor via Agent tool
**Activated:** Frontend and design tasks only

The design and UX specialist. **Never writes code.**

**Phase 0 (internal reasoning before any output):**
1. User intent — who is using this and what do they need?
2. Component inventory — reuse > compose > create new
3. State inventory — must cover all 8 UI states (loading, fetching, success, empty first-use, empty no-results, error, optimistic, real-time)
4. Primary interaction flow (max 3 steps)
5. Data density decision (table vs. cards vs. charts vs. KPI strip)

**The Anti-AI-Slop Rules:** 12 banned patterns are explicitly listed (purple gradients, emoji headers, Lucide icons, etc.). The Creative Brain has a self-check checklist it must pass before submitting.

---

### 5.4 Implementer

**File:** `_vibecoding_brain/agents/implementer.md`
**Spawned by:** Conductor via Agent tool

The code generation specialist. **Writes files directly to disk** using Claude Code's Write and Edit tools.

**Key difference from traditional agents:** The implementer is a real Claude Code subagent with file system access. It reads existing files, writes new ones, and edits in place — no JSON intermediary, no Python-level file application step. This means:
- Immediate disk writes (no serialization delay)
- Can read surrounding code for context mid-implementation
- Natural incremental editing instead of full-file replacement

**Frontend rules enforced:**
1. TypeScript strictly — type all props, state, API responses
2. `'use client'` only when needed
3. React Query for all data fetching
4. Framer Motion for animations
5. Design system classes only
6. Phosphor icons (not Lucide)
7. Error + loading states on every data-fetching component
8. Empty states on every list/table
9. Mobile responsive layouts
10. No hardcoded colors

**Backend rules enforced:**
1. DRF ViewSets — prefer `ModelViewSet`
2. Scope ALL queries by user/role
3. Serializers validate all write operations
4. Register every endpoint in urls.py
5. Include migration file content if model changes
6. Complex logic in services layer
7. Async operations as Celery tasks
8. No raw SQL — Django ORM only
9. Python type hints on all functions
10. Docstrings on all public functions/classes

---

### 5.5 UI/UX Tester

**File:** `_vibecoding_brain/agents/ui_ux_tester.md`
**Spawned by:** Conductor via Agent tool
**Skills injected:** `web_accessibility.md` (always) + `playwright_testing.md` (if server URL set)

The adversarial frontend quality gate. Does not rewrite code — reports issues.

**Immediate FAIL signals:**
- Purple/indigo gradient backgrounds
- Emojis as UI elements
- Uniform `rounded-2xl` on everything
- Cards nested 3+ levels deep
- Lucide icons (Phosphor only)
- Rainbow icon colors
- Glassmorphism on regular surfaces
- Dark sidebar (must be `gray-50`)
- Font weight 700+ in non-heading UI
- Raw Tailwind color classes instead of Montrose tokens
- Solid colored modal headers
- Pure white page background
- Animations exceeding 300ms
- Missing `aria-label` on icon-only buttons
- Missing `useReducedMotion()` on animated components

---

### 5.6 Backend Tester

**File:** `_vibecoding_brain/agents/backend_tester.md`
**Spawned by:** Conductor via Agent tool
**Skills injected:** `code_review.md` (always)

The adversarial backend quality gate.

**Review areas:**
- Logic correctness (matches acceptance criteria)
- Security (query scoping, no unguarded endpoints)
- Django/DRF patterns (ViewSets, serializer validation, URL registration)
- Data integrity (migrations, ORM queries)
- Type hints and docstrings
- Services layer usage
- Celery task patterns

---

## 6. Native Agent Teams — How It Works

The system uses Claude Code's **experimental Agent Teams** feature (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`).

### The Launch Sequence

1. **Python builds `--agents` JSON** from the system prompt markdown files in `_vibecoding_brain/agents/`. Each agent gets a name, description, and system prompt.

2. **Python spawns ONE `claude --print` subprocess** with:
   - `--system-prompt` = conductor_team.md content
   - `--agents` = the JSON of all available subagents
   - `--output-format stream-json` = for real-time progress streaming
   - `--dangerously-skip-permissions` = agents can write files without prompts
   - `--add-dir` = project root directory

3. **The Conductor session starts** with access to its own tools (Read, Write, Edit, Bash) and the ability to spawn any of the defined subagents via the Agent tool.

4. **Subagents are spawned on demand.** The Conductor calls the Agent tool to launch each specialist. Each subagent runs with its own system prompt and has access to Claude Code's built-in tools.

5. **Communication is fluid.** Subagents return results to the Conductor. The Conductor reads files, checks results, and decides next steps — all within the same session context.

6. **Progress streams in real time.** The Python launcher reads `stream-json` events and displays Rich-formatted progress: agent spawns, file writes, tool calls, errors.

### Why This Is Better Than Subprocess-Per-Agent

| Subprocess approach | Native Agent Teams |
|---|---|
| Each agent = `subprocess.run(["claude", "--print", ...])` | Each agent = `Agent` tool call within one session |
| ~3-5 second spin-up per agent | Instant spawn (same process) |
| Context passed as compressed text strings | Context shared efficiently within the session |
| No mid-task communication | Agents can be re-spawned with new context at any point |
| Python must parse JSON outputs and route them | Conductor handles all routing natively |

---

## 7. Skills — Injectable Capabilities

Skills are Markdown files in `_vibecoding_brain/agents/skills/` that are baked into subagent system prompts when the `--agents` JSON is built.

### `web_accessibility.md`
**Injected into:** UI/UX Tester (always)
**Purpose:** Full WCAG 2.1 AA compliance checklist — color contrast, keyboard navigation, focus management, screen reader requirements, reduced-motion requirements.

### `code_review.md`
**Injected into:** Backend Tester (always)
**Purpose:** Code review patterns specific to the Python/Django/DRF stack — security, query optimization, serializer completeness, error handling.

### `playwright_testing.md`
**Injected into:** UI/UX Tester (optional — only if `VIBE_PLAYWRIGHT_SERVER_URL` is set)
**Purpose:** E2E testing instructions using Playwright against a running dev server.

---

## 8. The Brain Directory (`_vibecoding_brain/`)

```
_vibecoding_brain/
│
├── AGENTS.md                    # Project constitution — loaded by conductor
│
├── agents/                      # System prompts for each agent role
│   ├── conductor_team.md        # Conductor instructions + full pipeline
│   ├── planner.md               # Planner format + planning principles
│   ├── creative_brain.md        # Design thinking + brief format + anti-slop rules
│   ├── implementer.md           # Code generation rules (frontend + backend)
│   ├── ui_ux_tester.md          # Frontend review checklist + verdict format
│   ├── backend_tester.md        # Backend review checklist + verdict format
│   └── skills/
│       ├── web_accessibility.md # WCAG 2.1 AA checklist
│       ├── code_review.md       # Backend code review patterns
│       └── playwright_testing.md # E2E testing skill (optional)
│
├── context/                     # Reference documents
│   ├── AGENTS.md                # Full project constitution
│   ├── project_index.md         # Every key file with one-line description
│   ├── design_system.md         # Complete design tokens, colors, typography
│   └── tech_stack.md            # Stack decisions, dependencies, patterns
│
├── workflows/                   # Slash command handlers
│   ├── vibe_code.md
│   └── review_only.md
│
└── sessions/                    # Auto-generated — one directory per task
    └── <session-id>/
        ├── plan.md
        ├── design_brief.md
        ├── review.md
        ├── walkthrough.md
        ├── reflection.md
        └── implementation_log.md
```

### `AGENTS.md` — The Project Constitution

Read by the Conductor at the start of every pipeline. Defines:
- Project identity: Montrroase — marketing agency management SaaS
- Stack: Next.js 15 (App Router, React 19, TailwindCSS v4) + Django 4 + Celery + PostgreSQL + Redis + WebSockets
- Key directories and their purposes
- 8 architecture rules that must NEVER be violated
- Design system summary
- Index of context documents

---

## 9. Session Artifacts

Every task generates a session directory at `_vibecoding_brain/sessions/<session-id>/`.

**Session ID format:** `<kebab-case-task-slug>` (e.g., `add-dark-mode-toggle`)

All artifacts are written by the Conductor during pipeline execution:

| Artifact | Written by | Purpose |
|----------|-----------|---------|
| `plan.md` | Conductor (from planner output) | Task decomposition, file lists, acceptance criteria |
| `design_brief.md` | Conductor (from creative brain output) | Visual/interaction specs (frontend only) |
| `review.md` | Conductor (from tester output) | Test verdict, issues found, positive observations |
| `walkthrough.md` | Conductor | User-facing summary of all changes |
| `reflection.md` | Conductor | Post-pipeline analysis and improvement suggestions |
| `implementation_log.md` | Conductor | Log of files written and what each does |

---

## 10. Quality Systems (Built Into Prompts)

Quality enforcement that was previously in separate Python modules is now built directly into the Conductor's system prompt:

### Self-Healing Validation
After implementation, the Conductor runs linting and type-checking via Bash. Errors are fed back to the implementer for fixing. Max 2 self-healing rounds before proceeding to testing.

### Stuck Detection
The Conductor tracks fix instructions across iterations. If the same core issue appears 3 consecutive times, it stops the retry loop and marks the task as `stuck` rather than wasting more iterations.

### Reflection
On every retry, the implementer receives a structured reflection prompt: What failed? What is ONE concrete fix? Are you repeating the same approach?

### Quality Self-Assessment
The Conductor includes a `quality_assessment` in its final JSON output with scores for correctness, completeness, and code quality. The Conductor has full visibility into the entire pipeline and is well-positioned to self-assess.

---

## 11. RAG — Codebase Search + Cross-Session Memory

**Location:** `src/rag_mcp/`
**Database:** ChromaDB (vector database, persisted at `src/rag_mcp/chroma_db/`)
**Embeddings:** `nomic-ai/nomic-embed-text-v1.5` via sentence-transformers

The RAG system has two components:

### Codebase Search (MCP Server)

An MCP server (`server.py`) that gives Claude Code agents semantic search over the codebase. Runs as a stdio process connected to Claude Code at startup.

**Tools exposed:**
- `search_codebase` — Semantic search with relevance threshold (≥25%) + MMR deduplication
- `search_multi` — Batch 2-5 queries in one call, merged and deduplicated
- `search_symbol` — Exact function/class name lookup
- `get_file` — Read a specific file with line numbers
- `list_indexed_files` — Browse what's in the index
- `rag_status` — Chunk count, last indexed time, model info

**Indexing:** Run `python src/rag_mcp/indexer.py` (incremental) or `python src/rag_mcp/indexer.py --full` (rebuild). AST-aware chunking for Python, regex-aware for TS/JS.

### Session Memory (Python hooks)

Cross-session learning via `session_memory.py`. Runs as optional pre/post hooks in the Python launcher:

**Pre-hook (before pipeline):** Queries similar past sessions from a `sessions` collection and injects a brief historical context snippet into the prompt.

**Post-hook (after pipeline):** Indexes the completed session for future retrieval.

### Collections

| Collection | Managed by | Contains |
|-----------|------------|---------|
| `codebase` | MCP server (`server.py`) | Indexed source code chunks for semantic search |
| `sessions` | Python hooks (`session_memory.py`) | Past task prompts + outcomes + summaries |

### Session Memory Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `VIBE_ENABLE_HISTORICAL_CONTEXT` | `true` | Enable/disable session memory hooks |
| `VIBE_MAX_SIMILAR_SESSIONS` | `5` | Max past sessions to retrieve |
| `VIBE_MIN_RELEVANCE_THRESHOLD` | `0.50` | Min cosine similarity score |

---

## 12. MCP Servers — Tools Available to Agents

All agents in the team session have access to MCP tools defined in `.mcp.json`. These are started automatically when Claude Code launches.

### `codebase-rag` — Semantic Codebase Search

**Server:** `src/rag_mcp/server.py`
**Target:** `Montrroase_website/` codebase

| Tool | Purpose |
|------|---------|
| `search_codebase` | Semantic search — "how does JWT auth work", "billing webhook handler" |
| `search_multi` | Batch 2-5 queries in one call, merged + deduplicated |
| `search_symbol` | Exact function/class name lookup — faster than semantic for known names |
| `get_file` | Read a specific file by relative path with line numbers |
| `list_indexed_files` | Browse all indexed files, optionally filtered by directory |
| `rag_status` | Index health: chunk count, last indexed time, model info |

### `ide-tools` — IDE Intelligence

**Server:** `src/ide_mcp_server.py`

| Tool | Purpose |
|------|---------|
| `get_git_diff` | Uncommitted changes — understand what was recently modified |
| `find_references` | Find all usages of a symbol across the project (via `git grep`) |
| `run_ide_linter` | Run ruff (Python) or eslint (TS/JS) and get structured lint output |

### `sequential-thinking` — Extended Reasoning

**Server:** `@anthropic-ai/mcp-sequential-thinking` (npx)

Provides structured multi-step reasoning for complex decisions. Used by the Conductor for task classification edge cases, stuck detection analysis, and architectural decisions.

---

## 13. Antigravity IDE Integration

The system integrates with the **Antigravity IDE Agent** for a seamless development experience:

- **Context injection:** When invoked from the IDE (`/vibe <prompt>`), Antigravity injects cursor position, active file, and terminal errors via the `--ide-state` JSON flag
- **IDE MCP Server:** Exposes git diff, symbol references, and native IDE linting to all agents
- **Sentinel warnings:** AI-slop pattern violations appear as real-time squiggly warnings in the IDE

The IDE layer acts as a context sensory system — Claude Code handles execution, Antigravity handles presentation and developer experience.

---

## 14. The Sentinel — Real-Time Quality Watcher

**File:** `src/sentinel.py`
**Dependency:** `watchdog>=4.0.0`

A passive background daemon that monitors all file writes to `Montrroase_website/` in real time. If any modification introduces banned AI-slop patterns, it instantly emits IDE-compatible warnings:

```
Montrroase_website/client/app/page.tsx:42: warning: [Sentinel] Lucide icons detected. Use Phosphor icons.
```

**Patterns detected:**
- Purple-to-blue gradients
- Uniform `rounded-2xl`
- Lucide icon imports
- Font weight 700+ in product UI
- Pure white page backgrounds
- Raw Tailwind color classes

**Integration with team_runner:** The Sentinel is auto-started as a background process when the agent team launches. After the pipeline completes, any warnings are collected and included in the result under `sentinel_warnings`.

**Manual usage:** `python src/sentinel.py`

---

## 15. Configuration Reference

All configuration via environment variables. Copy `.env.example` to `.env` and set values.

### Claude CLI

| Variable | Default | Description |
|----------|---------|-------------|
| `VIBE_CLAUDE_CLI_PATH` | `claude` | Path to Claude CLI binary |
| `VIBE_CLAUDE_CLI_MODEL` | `sonnet` | Model: `sonnet` / `opus` / `haiku` |
| `VIBE_CLAUDE_CLI_EFFORT` | `high` | Effort: `low` / `medium` / `high` / `max` |
| `VIBE_PLAYWRIGHT_SERVER_URL` | `""` | Dev server URL — enables Playwright skill |

### Execution Limits

| Variable | Default | Description |
|----------|---------|-------------|
| `VIBE_MAX_RETRIES` | `3` | Max implementer retries per tester FAIL |
| `VIBE_MAX_ITERATIONS` | `8` | Max total pipeline iterations |

### Session Memory (Optional)

| Variable | Default | Description |
|----------|---------|-------------|
| `VIBE_ENABLE_HISTORICAL_CONTEXT` | `true` | Enable session memory hooks |
| `VIBE_MAX_SIMILAR_SESSIONS` | `5` | Max past sessions retrieved |
| `VIBE_MIN_RELEVANCE_THRESHOLD` | `0.50` | Min similarity score |

---

## 16. Directory Structure

```
agentic_workflow/
│
├── vibe.py                          # Main entry point
├── requirements.txt                 # Python deps (stdlib only; optional deps noted)
├── .env.example                     # Environment variable template
├── .gitignore
│
├── .mcp.json                        # MCP server definitions for Claude Code
├── ANTIGRAVITY_INTEGRATION.md       # IDE integration documentation
│
├── src/                             # Python execution engine (thin launcher)
│   ├── __init__.py
│   ├── team_runner.py               # Core: builds agents, launches Claude session,
│   │                                #   streams output, sentinel, session memory (~400 lines)
│   ├── config.py                    # Configuration, env var loading (~55 lines)
│   ├── sentinel.py                  # Background AI-slop watcher (watchdog)
│   ├── ide_mcp_server.py            # MCP server: git diff, references, linting
│   │
│   └── rag_mcp/                     # RAG: codebase search + session memory
│       ├── server.py                # MCP server for semantic codebase search
│       ├── indexer.py               # AST-aware code chunking + embedding
│       ├── session_memory.py        # Cross-session learning (index/search past tasks)
│       ├── budget.py                # Token budget enforcement
│       ├── test_rag.py              # Test suite for the MCP server
│       └── requirements.txt         # Dependencies: mcp, chromadb, sentence-transformers
│
├── _vibecoding_brain/               # Agent knowledge base
│   ├── AGENTS.md                    # Project constitution
│   ├── agents/                      # System prompts (loaded into --agents JSON)
│   │   ├── conductor_team.md        # Conductor: full pipeline orchestration
│   │   ├── planner.md               # Task decomposition
│   │   ├── creative_brain.md        # Design thinking + anti-AI-slop
│   │   ├── implementer.md           # Code generation rules
│   │   ├── ui_ux_tester.md          # Frontend quality checklist
│   │   ├── backend_tester.md        # Backend quality checklist
│   │   └── skills/
│   │       ├── web_accessibility.md
│   │       ├── code_review.md
│   │       └── playwright_testing.md
│   ├── context/                     # Reference documents
│   │   ├── AGENTS.md
│   │   ├── project_index.md
│   │   ├── design_system.md
│   │   └── tech_stack.md
│   ├── workflows/
│   │   ├── vibe_code.md
│   │   └── review_only.md
│   └── sessions/                    # Auto-generated session artifacts
│
├── tests/                           # Test suite
│   └── test_integration.py          # Config validation, result parsing
│
├── utils/
│   └── math_helper.py
│
├── planning/                        # Planning artifacts
│   ├── ads-manager-plan.md
│   ├── command_centre_plan.md
│   ├── repomap.txt
│   └── CLAUDE.md
│
└── audits/                          # Audit reports
    ├── architecture_audit
    ├── components_audit.md
    └── url_audit.md
```

---

## 17. Key Source Files

| File | Lines | Purpose |
|------|-------|---------|
| `src/team_runner.py` | ~400 | Core engine — builds agents JSON, launches Claude session, sentinel, session memory hooks |
| `src/config.py` | ~55 | Configuration — env var loading, defaults, CLI path validation |
| `src/sentinel.py` | ~107 | Background AI-slop watcher — monitors file writes for banned patterns |
| `src/ide_mcp_server.py` | ~163 | IDE MCP server — git diff, find references, run linter |
| `src/rag_mcp/server.py` | ~500 | Codebase RAG MCP server — semantic search with 6 tools |
| `src/rag_mcp/indexer.py` | ~544 | Codebase indexer — AST-aware chunking + embedding |
| `src/rag_mcp/session_memory.py` | ~170 | Session memory — index/search past task outcomes |
| `_vibecoding_brain/agents/conductor_team.md` | ~150 | Conductor prompt — full pipeline orchestration with quality systems |
| `_vibecoding_brain/agents/creative_brain.md` | ~508 | Creative Brain — design thinking + anti-AI-slop rules |
| `_vibecoding_brain/agents/implementer.md` | ~80 | Implementer — code generation rules, direct file writing |
| `_vibecoding_brain/agents/ui_ux_tester.md` | ~200 | UI/UX Tester — 100+ specific quality checks |
| `_vibecoding_brain/context/design_system.md` | ~500 | Complete design system reference |

---

## 18. Testing

```bash
# Run the launcher test suite
pytest tests/ -v

# Run specific test files
pytest tests/test_integration.py -v

# Run MCP server tests (requires chromadb + sentence-transformers)
python src/rag_mcp/test_rag.py
```

**Test coverage:**
- `tests/test_integration.py` — Config validation, CliTeamRunner result parsing
- `src/rag_mcp/test_rag.py` — MCP server search tools, indexer, embedding quality

---

## 19. The Design Standard

The system embeds a specific design philosophy that all generated UI must follow. This is encoded into both the Creative Brain's system prompt and the UI/UX Tester's checklist.

### Core Philosophy

1. **Subtraction over addition** — before adding any element, ask "what happens if we remove this?" If the interface works without it, it shouldn't exist.
2. **Systems over decisions** — colors generated algorithmically from a palette. Spacing from a 4px grid. Animation from named tokens. Correct choices should be automatic.
3. **Opinion over safety** — the generic aesthetic of AI UIs comes from statistical averaging. Premium software takes positions and commits to them.

### The 12 AI-Slop Patterns (Hard-Banned)

| Pattern | Why It's Banned |
|---------|----------------|
| Purple-to-blue gradients | Overused in AI-generated templates; signals "generic" |
| Emoji section headers | Decorative noise, not information |
| Uniform `rounded-2xl` on everything | Graduated radius signals craftsmanship |
| Cards nested 3+ levels | Visual complexity without hierarchy |
| Lucide icons | Ubiquitous in AI templates; use Phosphor |
| Rainbow icon colors | Color should communicate meaning, not decorate |
| Glassmorphism on regular surfaces | Reserve for command palette/modals only |
| Dark sidebar (`bg-slate-900`) | Sidebar should be `gray-50`, barely distinguishable from content |
| Font weight 700+ in UI | Weight 600 max in product UI; 700 for page headings only |
| Raw Tailwind colors (`bg-zinc-100`) | Use custom Montrroase tokens |
| Solid colored modal headers | Modal title on same white bg as modal body |
| Pure white (`#ffffff`) page background | Page canvas = `gray-50` (#FAFAF8) |

### Key Design Decisions

- **Page background:** `gray-50` (#FAFAF8) — never pure white
- **Cards:** white (#FFFFFF) on `gray-50` creates depth without shadows
- **Accent color:** `#6366F1` — under 10% of screen area
- **Default body text:** 14px (not 16px)
- **Font weights:** 400/500/600 only in product UI
- **All numbers/data:** `tabular-nums` for alignment
- **Border-radius:** 4px buttons → 6px list items → 8px cards → 12px modals (graduated)
- **Spacing:** 4px base grid
- **Animations:** Hover=100ms, press=150ms, dropdown=150ms, modal=200ms — never exceed 300ms
- **Icons:** Phosphor at 16px/20px/24px — `currentColor`
- **Shadows:** Only for floating elements — cards use border, not shadow

---

*Generated: 2026-04-01*
