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
| **TRIVIAL** | Any | Handle it yourself. No agents. No artifacts. No git checkpoint. |
| **SIMPLE** | Single domain | 1 `implementer` → quality gate. No architect, no contract review, no AI tester. Brief walkthrough. |
| **SIMPLE** | FULLSTACK | 1 `implementer` → quality gate. Brief walkthrough. |
| **MEDIUM** | FRONTEND | 1 `implementer` (does its own Chain-of-Thought planning) → quality gate. Full artifacts. |
| **MEDIUM** | BACKEND | 1 `implementer` (does its own CoT planning) → quality gate. Full artifacts. |
| **MEDIUM** | FULLSTACK | `impl-backend` → `impl-frontend` → `contract-reviewer` → quality gate. **Sequential.** Full artifacts. See Sequential Execution below. |
| **COMPLEX** | Any | `architect` → (impl-backend → impl-frontend → contract-reviewer for FULLSTACK, else single implementer) → quality gate. All agents use opus. Full artifacts + reflection. |

**FULLSTACK Sequential Execution (MEDIUM+):**
```
[Orchestrator: RAG Context Assembly + dependency-graph walk]
              ↓
[Pre-pipeline git checkpoint]
              ↓
[architect] → architect_brief.md      (COMPLEX only; MEDIUM skips this)
              ↓
[impl-backend]  — emits "## API Contract" block (source of truth)
              ↓
[impl-frontend] — derives types/api.ts from the API Contract block verbatim
              ↓
[contract-reviewer] — 4 checks only: URLs, methods, payload keys, auth
              ↓
[Quality Gate: tsc / eslint / ruff + banned-pattern scan]
              ↓
[Post-quality-gate git checkpoint]
              ↓
[Wrap Up — hand off to human for visual review]
```

**Why sequential, not parallel:** Running backend and frontend in parallel forces the frontend to guess the API contract. With sequential execution, `impl-backend` finalizes the contract first and hands it to `impl-frontend` as a single source of truth — no guessing, no drift.

**Refer to `AGENTS.md`** for which agents to spawn, what model to use, and which skills to inject.

### Step 3.5 — Pre-pipeline Git Checkpoint (SIMPLE and above)

Before spawning any agent, commit the current working tree as a safety net.

**IMPORTANT: The `ai_orchestrator/` directory and `Montrroase_website/` are SEPARATE git repositories.** `Montrroase_website/` is gitignored by the orchestrator repo. All git checkpoints and commits for pipeline work MUST be run inside `Montrroase_website/`:

```bash
cd Montrroase_website
git status --porcelain  # sanity check — warn the user if there is unfamiliar uncommitted work not authored by the pipeline
git add . && git commit -m "chore: pre-agent checkpoint [{session_id}]" --allow-empty
```

**Rules:**
- **Always `cd Montrroase_website` before any git operation** — running git at the orchestrator root will not see project file changes.
- Never push, never force, never amend. Ever.
- If this commit fails (e.g., pre-commit hook rejects), log and continue — never abort the pipeline on a checkpoint failure.
- If `git status` shows unfamiliar uncommitted changes that the user did not mention, pause and confirm with the user before committing their in-progress work.
- Rollback for the entire pipeline: `git reset --hard HEAD~2` (undoes both pre and post checkpoints, returning to the exact state before the pipeline ran).

### Step 4 — Create Team & Tasks (SIMPLE and above)

1. `TeamCreate` with descriptive `team_name` (kebab-case, e.g. `fix-auth-modal`)
2. `TaskCreate` for each piece of work
3. `TaskUpdate` with `addBlockedBy` for sequential work
4. `TaskUpdate` with `owner` matching agent `name`

### Step 5 — RAG Context Assembly

**IMPORTANT:** MCP tools are only available to you (the orchestrator). Team agents do NOT have MCP access. You MUST run all searches before spawning agents, then package results into a **Context Package** embedded in each agent's prompt. See `_vibecoding_brain/context/context_package_template.md` for the full template, prompt-caching order, and agent-specific slicing rules.

**Phase A — Broad Discovery (always run):**
1. `search_multi` with 2-3 queries: raw task description, "existing implementation of {feature}", related component/endpoint names
2. `search_past_sessions` with the task description for similar prior work
3. **FRONTEND / FULLSTACK tasks only:** `search_codebase` with `"design tokens for {UI element in task}"` (e.g., "design tokens for button hover state"). Top 5 hits form the `## Design Tokens` Context Package slice. **Do not bulk-inject `design_system.md`** — targeted RAG slices only.

**Phase B — Symbol Lookup (if task names specific code):**
4. `search_symbol` for each named function/class/component mentioned in the task
5. **Dependency-graph walk (after identifying each MODIFY target):**
   - **Preferred:** call `get_file_imports` MCP tool → `get_file` for each returned path.
   - **Interim fallback (until `get_file_imports` ships):** `Grep` the target file for `^(import|from) .* ['"](\.\.?/[^'"]+)['"]` (TS/JS) or `^from (\.\.?\w+) import` (Python). Resolve relative paths against the target's directory. `Read` each resolved file.
   - Cap at 10 imported files total. Skip `node_modules`, stdlib, and external packages.
   - Embed them in the Context Package under `### Imported Dependencies`.
6. `get_file` for any file paths mentioned in the task

**Phase C — Contract Discovery (FULLSTACK tasks only):**
7. `search_codebase` with "API endpoint for {feature}" to find related backend endpoints
8. `search_symbol` for the relevant API method name in `api.ts`

**Phase D — Build Context Package:**
9. Filter RAG results: discard below 25% relevance, deduplicate, sort by score, cap at 5 per section
10. Read FULL contents of files that will be MODIFIED (not just RAG chunks)
11. Filter `rules.md` by domain tag — pass only matching rules to each agent (goes in the static prefix, not the Context Package)
12. Assemble the Context Package using the template, sliced per agent (see template for slicing table)

**Fallback (if RAG MCP unresponsive >30s):**
- `Glob` patterns based on task keywords
- `Grep` for symbol names in likely directories (`client/lib/`, `server/api/views/`, `server/api/urls.py`)
- Direct `Read` of files referenced in `context/project_index.md`

### Step 6 — Spawn Agents

Read the agent's `.md` file from `_vibecoding_brain/agents/` before spawning. **Assemble every agent's prompt in this exact STATIC → DYNAMIC order** so Claude's prefix cache fires across spawns within the 5-minute window:

```
─── STATIC (cacheable prefix — identical across spawns) ───
1. Agent identity & instructions   (from agents/{agent}.md)
2. Injected skills                 (from agents/skills/*.md — see AGENTS.md Skill Injection table)
3. Architecture rules              (the "Architecture Rules" section above, verbatim)
4. Domain-filtered prevention rules (from problems/rules.md, filtered by [FRONTEND]/[BACKEND]/[FULLSTACK]/[DATABASE]/[DESIGN])
─── <!-- CACHE BOUNDARY --> ───
─── DYNAMIC (per-task) ───
5. Task description
6. Context Package                 (RAG results + Design Tokens + Source Files + Imported Dependencies + Backend API Contract)
7. Completion instruction          ("Mark your task as completed via TaskUpdate when done.")
```

**Never interleave dynamic content into the static prefix.** Putting the task description or file contents above the architecture rules breaks the cache key and forces a cold read on every spawn. The `<!-- CACHE BOUNDARY -->` marker is a documentation comment — no runtime effect, but it helps you visually verify the split while assembling prompts.

**Embedding format for files in agent prompts** (inside the Context Package, dynamic section):
```
## File: path/to/file.tsx
\`\`\`tsx
[full file contents]
\`\`\`
```

**Sequential execution rules:**
- **FULLSTACK MEDIUM+:** spawn `impl-backend` → wait for its summary → extract the `## API Contract` block → spawn `impl-frontend` with the Contract block embedded in its Context Package → wait → spawn `contract-reviewer`. Never parallel.
- **Single-domain MEDIUM+:** spawn the single `implementer` and wait.
- **COMPLEX FULLSTACK:** prepend an `architect` spawn before `impl-backend`; `impl-backend` receives `architect_brief.md` and the Context Package.

**Implementer selection:**
- SIMPLE or single-domain MEDIUM+: use `implementer` (general-purpose).
- FULLSTACK MEDIUM+: use `impl-backend` → `impl-frontend` (sequential specializations).

### Step 7 — Contract Review Gate (FULLSTACK MEDIUM+ only)

After `impl-frontend` finishes, spawn the **contract-reviewer** agent. Skip for single-domain tasks.

The contract-reviewer receives:
- `impl-backend`'s `## API Contract` block (source of truth)
- `client/lib/api.ts` and `client/lib/types.ts` (full contents)
- The new/modified Django `urls.py`, views, and serializers (full contents)
- Injected skill: `contract_review.md`

It checks exactly four things: URLs, HTTP methods, payload key mapping, auth headers. Nothing else. Single PASS/FAIL verdict.

If FAIL: send the fix instructions to the relevant implementer via `SendMessage`. Default: the frontend adapts to the backend.

### Step 8 — Deterministic Quality Gate (max 8 iterations)

This is the **sole** quality gate. There are no LLM testers in the pipeline. After implementation (and contract review if applicable), run:

```bash
# Frontend — only if client/ files changed
cd Montrroase_website/client
npx tsc --noEmit 2>&1 | head -80
npx eslint <changed-files> 2>&1 | head -80

# Backend — only if server/ files changed
cd Montrroase_website/server
python3 -m ruff check <changed-files> 2>&1 | head -80
python3 -m ruff format --check <changed-files> 2>&1 | head -40
```

**Banned-pattern scan** — grep modified frontend files for AI-slop tells and contrast failures that tsc/eslint won't catch. Full red-line list lives in `_vibecoding_brain/context/design_system.md` §12 and `_vibecoding_brain/agents/skills/frontend_design.md`. Minimum scan:
- `bg-gradient-to` / `from-purple` / `to-blue` / `from-indigo` — AI-slop gradients
- `rounded-2xl` — must use graduated radius (4/6/8/12px)
- `import ... from 'lucide-react'` — Phosphor only
- `font-bold` / `font-\[700\]` / `font-black` in body — max weight 600 unless page `<h1>`
- Raw Tailwind neutrals: `bg-zinc-*`, `bg-slate-*`, `bg-gray-*`, `text-indigo-*` — must use CSS custom properties from `globals.css`
- Emojis used as UI elements (labels, bullets, status)
- **Hospital-white canvas:** `bg-white` or `background:\s*#FFFFFF` or `background:\s*#FAFAFA` on `body`, page shells, or layout wrappers — canvas must be `var(--color-canvas)` (`#F5F7FA`). Violates the Contrast Rule (`design_system.md` §0).
- **Nude cards:** any element with `.card-surface` / `card` semantics missing either `border` or `shadow` — grep for cards that lack `box-shadow` + `border` combo. A card must have both.
- **Dead interactives:** `<button>` / `<Link>` / `<a>` / `role="button"` elements with no `hover:` OR no `focus-visible:` class. Grep each interactive for both.
- **Nude stats:** `StatTile` / `.kpi-item` / stat-card usage missing `tabular-nums` OR missing a status rail class (`status-rail-*`).
- **Solid-color badges:** `bg-green-`, `bg-red-`, `bg-yellow-`, `bg-blue-` on `.badge-*` or badge elements — must use tinted-ring variant via `badge-success/warning/error/info` classes.
- **Pure-black shadows:** `box-shadow: 0 \d+px \d+px rgba(0,\s*0,\s*0` — use slate-tinted `rgba(16, 24, 40, …)`.
- **Arbitrary motion durations:** `duration-\[\d+ms\]` / `transition-duration:\s*\d+ms` with values not matching the token scale (80/120/180/220/160/280). Use named tokens.
- `backdrop-filter:\s*blur` on anything that isn't a modal/drawer overlay or the command palette.

**Write-on-existing-file scan** — if the implementer's tool-call log shows a `Write` call on a path that existed pre-pipeline, that is a tool-rule violation. Send it back.

**On any failure:** send the exact compiler/linter output + the violating file paths to the implementer via `SendMessage` with the Reflection-on-Retry prompt. The implementer edits, you re-run the gate. Max 8 iterations. If the same error persists 3 consecutive iterations, mark `stuck` and stop.

### Step 8.5 — Post-quality-gate Git Checkpoint

Once the quality gate passes, commit the known-good snapshot **inside `Montrroase_website/`**:

```bash
cd Montrroase_website
git add . && git commit -m "chore: post-agent checkpoint [{session_id}]"
```

This is the point of no return for the pipeline. If the human reviewer later rejects the work, `git reset --hard HEAD~1` restores the pre-pipeline state while keeping the post-commit as a reference for what was produced. Full pipeline rollback: `git reset --hard HEAD~2`.

Never push, never force, never amend. **Always run git operations inside `Montrroase_website/`, not at the orchestrator root.**

### Step 9 — Human Visual Review (FRONTEND / FULLSTACK only)

There is no AI UI tester. After the quality gate and checkpoint, report to the user:

> Quality gate passed. Ready for your visual review.

List the files touched and the dev-server URL (if available). The human owns the visual-correctness verdict. If the user rejects, collect their feedback and feed it back to the implementer as a new iteration.

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
Between agents, compress summaries to <200 words. **Exceptions:** implementers and `contract-reviewer` MUST receive full file contents (via the Context Package), and `impl-frontend` MUST receive `impl-backend`'s full `## API Contract` block verbatim.

### Reflection on Retry (N > 1)
> "Attempt {N}/8. Before retrying: 1) What specifically failed? 2) What is ONE concrete change to fix it? 3) Are you repeating the same approach? If yes, try fundamentally different. Fix EXACTLY these issues — do not refactor."

### Context Docs (in `_vibecoding_brain/context/`)
- `design_system.md` — Full design tokens. **RAG source only — never bulk-inject. Use targeted `search_codebase` queries to pull task-relevant snippets.**
- `tech_stack.md` — Stack decisions, testing, deployment
- `project_index.md` — Key files with descriptions
- `montrroase_guide.md` — Business domain, user roles, features, data flows
- `modal_guide.md` — Modal building patterns (read when task involves modals)
- `context_package_template.md` — Template for assembling Context Packages + prompt-cache ordering + RAG query protocol + agent slicing table
