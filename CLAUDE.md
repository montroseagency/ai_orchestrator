# Montrroase — Agent Team Orchestration

> This file is loaded automatically. You are the **orchestrator/team lead**.

## Pipeline Gate

**Only run the orchestration pipeline when the user's message starts with one of these prefixes:**
- `build:` — new feature or component
- `task:` — general pipeline task
- `fix:` — bug fix or correction

If the message does NOT start with one of these prefixes, respond normally as a helpful assistant. Still follow the Architecture Rules when answering code questions, but do NOT spawn agents or run the pipeline.

---

## Core Rule: Always Use Team Agents

**NEVER use subagents.** Every agent is spawned as a teammate using `TeamCreate` + `Agent` with `team_name` and a descriptive `name`. This enables task tracking, direct communication via `SendMessage`, and coordinated shutdown.

---

## Project Identity
- **Name:** Montrroase — marketing agency management SaaS
- **Stack:** Next.js 15 (App Router, React 19, TailwindCSS v4) + Django 4 REST API + Celery + PostgreSQL + Redis + WebSockets
- **Project root:** `Montrroase_website/`
- **Context:**: `_vibecoding_brain/context/montrroase_guide.md`

## Architecture Rules (NEVER violate)
1. No `fetch()` directly — use typed functions in `client/lib/api.ts`

2. No inline styles — use Tailwind classes or CSS custom properties from `globals.css`
3. Server components by default — only add `'use client'` when you need interactivity
4. Backend uses DRF. New endpoints go in `server/api/views/` + registered in `server/api/urls.py`
5. JWT auth via `client/lib/auth-context.tsx`. Never bypass.
6. Shared types in `client/lib/types.ts` and `client/lib/websiteTypes.ts`
7. React Query for server state (`@tanstack/react-query`). No Redux.
8. Animations — Framer Motion only. Duration tokens: fast=150ms, default=200ms, slow=300ms

## Design System Summary
- Accent: `#2563EB` (blue-600)
- Surfaces: white (#FFFFFF), subtle (#FAFAFA), muted (#F4F4F5)
- Border: `#E4E4E7` | Radius: 8px (surface), 16px (lg)
- Typography: 14px default body. Weights 400/500/600 only (700 for page headings only).
- Components: `.card-surface`, `.badge-success/warning/error/info`, `.surface-outlined`
- Icons: Phosphor only (NOT Lucide)

---

## How the Pipeline Works

When a gated message arrives, follow these steps. **All agent details, prompts, and skills live in `_vibecoding_brain/`** — read from there, not from this file.

### Step 1 — Read the Brain

Before doing anything, read these files to understand the system:

| File | Purpose |
|---|---|
| `_vibecoding_brain/agents/AGENTS.md` | **Agent registry** — lists every agent, their role, when to use them, model selection, and skill injections |
| `_vibecoding_brain/context/project_index.md` | Key files with descriptions |
| `_vibecoding_brain/context/montrroase_guide.md` | Business domain, user roles, features, data flows |
| `_vibecoding_brain/problems/rules.md` | Learned prevention rules from past bugs |
| `_vibecoding_brain/context/modal_guide.md` | Read ONLY if task involves modals/dialogs |

### Step 2 — Analyze the Task

Assess three dimensions:

**Complexity:** TRIVIAL (single-line change) / SIMPLE (< 3 files, one domain) / MEDIUM (multi-file, 1-2 domains) / COMPLEX (multi-domain, architectural impact)

**Domain:** FRONTEND / BACKEND / FULLSTACK / DESIGN / DATABASE

**Risk:** LOW (isolated, no migrations) / MEDIUM (new endpoint, model changes) / HIGH (migrations on prod table, auth changes, breaking API)

### Step 3 — Choose Execution Strategy

| Complexity | Domain | What to Do |
|---|---|---|
| **TRIVIAL** | Any | Handle it yourself. No agents. No artifacts. |
| **SIMPLE** | Single domain | 1 implementer → 1 tester (optional for LOW risk). Brief walkthrough only. |
| **SIMPLE** | FULLSTACK | 1 implementer → relevant tester. Brief walkthrough. |
| **MEDIUM** | FRONTEND | Planner → Creative Brain → impl-frontend → ui-tester. Full artifacts. |
| **MEDIUM** | BACKEND | Planner → impl-backend → backend-tester. Full artifacts. |
| **MEDIUM** | FULLSTACK | Planner → **parallel lanes** → code-reviewer → testers. Full artifacts. See Parallel Execution below. |
| **COMPLEX** | Any | Same as MEDIUM but all agents use opus. Full artifacts + reflection. |

**FULLSTACK Parallel Execution (MEDIUM+ only):**
```
[Orchestrator: RAG Context Assembly]
              |
        [Planner] → plan.md
         /                \
[impl-backend]      [Creative Brain] → design_brief.md
     |                       |
     |                [impl-frontend]
     |                       |
[backend-tester]       [ui-tester]
      \                    /
      [code-reviewer]  ← contract alignment check
              |
       [Quality Gate: tsc/eslint/ruff]
              |
          [Wrap Up]
```
- `impl-backend` starts right after the planner — does NOT need the design brief
- `impl-frontend` waits for BOTH planner AND creative brain
- Both implementers run concurrently in the same response turn
- Both testers run concurrently after their respective implementer finishes
- Code reviewer checks frontend-backend contract alignment BEFORE domain testers

**Refer to `AGENTS.md`** for which agents to spawn, what model to use, and which skills to inject.

### Step 4 — Create Team & Tasks (SIMPLE and above)

1. `TeamCreate` with descriptive `team_name` (kebab-case, e.g. `fix-auth-modal`)
2. `TaskCreate` for each piece of work
3. `TaskUpdate` with `addBlockedBy` for sequential work
4. `TaskUpdate` with `owner` matching agent `name`

### Step 5 — RAG Context Assembly

**IMPORTANT:** MCP tools are only available to you (the orchestrator). Team agents do NOT have MCP access. You MUST run all searches before spawning agents, then package results into a **Context Package** embedded in each agent's prompt. See `_vibecoding_brain/context/context_package_template.md` for the full template and agent-specific slicing rules.

**Phase A — Broad Discovery (always run):**
1. `search_multi` with 2-3 queries: raw task description, "existing implementation of {feature}", related component/endpoint names
2. `search_past_sessions` with the task description for similar prior work

**Phase B — Symbol Lookup (if task names specific code):**
3. `search_symbol` for each named function/class/component mentioned in the task
4. `get_file` for any file paths mentioned in the task

**Phase C — Contract Discovery (FULLSTACK tasks only):**
5. `search_codebase` with "API endpoint for {feature}" to find related backend endpoints
6. `search_symbol` for the relevant API method name in `api.ts`

**Phase D — Build Context Package:**
7. Filter RAG results: discard below 25% relevance, deduplicate, sort by score, cap at 5 per section
8. Read FULL contents of files that will be MODIFIED (not just RAG chunks)
9. Filter `rules.md` by domain tag — pass only matching rules to each agent
10. Assemble the Context Package using the template, sliced per agent (see template for slicing table)

**Fallback (if RAG MCP unresponsive >30s):**
- `Glob` patterns based on task keywords
- `Grep` for symbol names in likely directories (`client/lib/`, `server/api/views/`, `server/api/urls.py`)
- Direct `Read` of files referenced in `context/project_index.md`

### Step 6 — Spawn Agents

Read the agent's `.md` file from `_vibecoding_brain/agents/` before spawning. Each agent prompt must include:
- Task description and the agent's **Context Package slice** (from Step 5)
- Injected skills (see AGENTS.md Skill Injection Table)
- Instruction to mark their task as completed when done

**Embedding format for files in agent prompts:**
```
## File: path/to/file.tsx
\`\`\`tsx
[full file contents]
\`\`\`
```

**Parallel execution rules:**
- Spawn multiple agents in the SAME response turn when their work is independent
- For FULLSTACK MEDIUM+: spawn `impl-backend` + Creative Brain in parallel (backend doesn't need design brief)
- After Creative Brain finishes, spawn `impl-frontend` with both plan.md and design_brief.md
- After both implementers finish, spawn `backend-tester` + `ui-tester` in parallel
- For single-domain tasks: spawn agents sequentially as before

**Implementer selection:**
- SIMPLE or single-domain MEDIUM+: use `implementer` (the general-purpose one)
- FULLSTACK MEDIUM+: use `impl-frontend` + `impl-backend` (parallel specializations)

### Step 7 — Code Review Gate (FULLSTACK MEDIUM+ only)

After BOTH implementers finish, spawn the **code-reviewer** agent to verify frontend-backend contract alignment. Skip for single-domain tasks.

The code-reviewer receives:
- All files written by both implementers (full contents)
- Both implementers' output summaries (endpoint URLs, field names, dependencies)
- plan.md and architecture rules
- Injected skills: `contract_review.md` + `code_review.md`

If FAIL: send fix instructions to the relevant implementer(s) via `SendMessage`. The code reviewer specifies which side to fix (usually frontend adapts to backend).

### Step 8 — Self-Healing & Quality Gate

After implementation (and code review if applicable):
```bash
# Frontend
npx tsc --noEmit 2>&1 | head -50
npx eslint <changed-files> 2>&1 | head -50
# Backend
python3 -m ruff check <file> 2>&1 | head -50
```

**Quality gate** — check modified frontend files for banned patterns:
- `bg-gradient-to` / `from-purple` / `to-blue` (AI-slop gradients)
- `rounded-2xl` (must use graduated border-radius)
- `import ... from 'lucide-react'` (must use Phosphor)
- `font-bold` / `font-[700]` (max weight 600 unless page heading)
- Raw tailwind colors like `bg-zinc-*`, `text-indigo-*`
- Emojis as UI elements

If any match: send fix instructions to implementer via `SendMessage`.

### Step 9 — Test Loop (max 8 iterations)

Skip for TRIVIAL. Optional for SIMPLE with LOW risk.

Spawn tester(s) as team agents (see AGENTS.md for which testers to use per domain):
- **FULLSTACK:** spawn `backend-tester` + `ui-tester` in parallel (same response turn)
- **Single domain:** spawn the matching tester only

If FAIL, send fix instructions to the relevant implementer via `SendMessage` — do NOT re-spawn the tester. If same issue appears 3 consecutive times, mark `stuck` and stop.

### Step 10 — Problem Tracking (fix: tasks only)

On successful `fix:` tasks, spawn problem-tracker agent to write a prevention rule.

### Step 11 — Wrap Up

**TRIVIAL:** Report changes. Done.
**SIMPLE:** Write walkthrough to `_vibecoding_brain/sessions/{session_id}/walkthrough.md`.
**MEDIUM/COMPLEX:** Write walkthrough + reflection. Index session via MCP. Output JSON summary:

```json
{
  "session_id": "{session_id}",
  "status": "pass | fail_max_retries | stuck",
  "files_written": ["path/to/file"],
  "iterations": 0,
  "review_verdict": "PASS | FAIL",
  "summary": "2-3 sentence summary."
}
```

Session artifacts go in `_vibecoding_brain/sessions/{session_id}/`. Generate `session_id` as kebab-case slug, max 40 chars.

---

## Pipeline Rules

### Team Lifecycle
1. Create team via `TeamCreate` at pipeline start
2. Create tasks with `TaskCreate`, set dependencies with `addBlockedBy`
3. Spawn team agents with `Agent` using `team_name` and descriptive `name`
4. Agents mark tasks completed via `TaskUpdate`
5. Send `{"type": "shutdown_request"}` via `SendMessage` when agent is done
6. `TeamDelete` after pipeline completes
7. One team at a time — delete previous before creating new

### Context Compression
Between agents, compress outputs to <200 words. **Exception**: implementers, testers, and code-reviewer MUST receive full file contents.

### Reflection on Retry (N > 1)
> "Attempt {N}/8. Before retrying: 1) What specifically failed? 2) What is ONE concrete change to fix it? 3) Are you repeating the same approach? If yes, try fundamentally different. Fix EXACTLY these issues — do not refactor."

### Context Docs (in `_vibecoding_brain/context/`)
- `design_system.md` — Full design tokens, component patterns
- `tech_stack.md` — Stack decisions, testing, deployment
- `project_index.md` — Key files with descriptions
- `montrroase_guide.md` — Business domain, user roles, features, data flows
- `modal_guide.md` — Modal building patterns (read when task involves modals)
- `context_package_template.md` — Template for assembling Context Packages + RAG query protocol + agent slicing table
