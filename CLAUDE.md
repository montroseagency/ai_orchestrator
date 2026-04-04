# Montrroase — Agent Team Orchestration

> This file is loaded automatically. The orchestration pipeline is **gated** — see below.

## Pipeline Gate

**Only run the orchestration pipeline when the user's message starts with one of these prefixes:**
- `build:` — new feature or component
- `task:` — general pipeline task
- `fix:` — bug fix or correction

If the message does NOT start with one of these prefixes, respond normally as a helpful assistant. Still follow the Architecture Rules and Design System when answering code questions, but do NOT spawn agents, create session artifacts, or run the pipeline.

**Examples:**
- `build: Add a dark mode toggle` → run pipeline
- `fix: the sidebar collapses on mobile` → run pipeline
- `task: refactor the auth middleware` → run pipeline
- `how does the auth flow work?` → answer normally, no pipeline
- `what files handle billing?` → answer normally, no pipeline

---

## Project Identity
- **Name:** Montrroase — marketing agency management SaaS
- **Stack:** Next.js 15 (App Router, React 19, TailwindCSS v4) + Django 4 REST API + Celery + PostgreSQL + Redis + WebSockets
- **Project root:** `Montrroase_website/`
- **Client:** `Montrroase_website/client/` — Next.js app
- **Server:** `Montrroase_website/server/` — Django, all API in `server/api/`

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

## Smart Orchestration

When a gated message arrives (`build:`, `task:`, `fix:`), follow this adaptive pipeline. You — the orchestrator — decide **what to run** based on the task. No fixed pipelines.

### Step 1 — Analyze & Decide

Assess three dimensions:

**Complexity:**
| Level | Criteria | Examples |
|---|---|---|
| TRIVIAL | Single-line or config change. No logic. | Typo fix, env var change, rename a variable, update a string |
| SIMPLE | Single-domain, < 3 files, clear scope | Add a field to a serializer, new badge component, simple endpoint |
| MEDIUM | Multi-file, one or two domains, moderate logic | New page with API endpoint, form with validation, feature flag |
| COMPLEX | Multi-domain, architectural impact, many files | New module with backend + frontend + real-time, major refactor |

**Domain:** FRONTEND / BACKEND / FULLSTACK / DESIGN / DATABASE

**Risk:**
| Level | Criteria |
|---|---|
| LOW | No migrations, no auth changes, isolated component |
| MEDIUM | New endpoint, model changes, shared component modification |
| HIGH | Migration on production table, auth/permission changes, breaking API changes |

### Step 2 — Select Execution Strategy

Based on your analysis, choose the right approach:

| Complexity | What to Do | Agents | Session Artifacts |
|---|---|---|---|
| **TRIVIAL** | Handle it yourself directly. No agents needed. Make the change, run lint, done. | None | None |
| **SIMPLE** | Launch the single most appropriate specialist agent. Add a tester only if risk > LOW. | 1-2 agents | Brief walkthrough only |
| **MEDIUM** | Planner → Implementer → Tester(s). Add Creative Brain only if frontend-visible. | 2-4 agents | Full artifacts |
| **COMPLEX** | Full team: Planner → Creative Brain (if frontend) → Implementer → All relevant testers. | 3-5 agents | Full artifacts |

**You decide which agents are needed.** Don't launch agents that won't add value. A backend-only task doesn't need Creative Brain. A design-only task doesn't need Backend Tester.

### Step 3 — Select Models

Set the `model` parameter when spawning each Agent based on task complexity:

| Agent | SIMPLE | MEDIUM | COMPLEX |
|---|---|---|---|
| planner | sonnet | sonnet | opus |
| creative_brain | sonnet | sonnet | opus |
| implementer | haiku | sonnet | opus |
| ui_ux_tester | haiku | sonnet | sonnet |
| backend_tester | haiku | sonnet | sonnet |
| problem_tracker | haiku | haiku | sonnet |

Default to **sonnet** if unsure. Use **haiku** for fast auxiliary work. Use **opus** only for complex planning or implementation.

### Step 4 — Gather Context

**a) Always read:**
- `_vibecoding_brain/context/AGENTS.md` (if it exists)
- `_vibecoding_brain/context/project_index.md` (if it exists)
- `_vibecoding_brain/context/montrroase_guide.md` (if it exists)
- `_vibecoding_brain/context/modal_guide.md` (if task involves modals, dialogs, or popups)

**b) Problem rules** — Read `_vibecoding_brain/problems/rules.md` if it exists. Check if any rules match the current task's domain or files. Pass matching rules to planner and implementer.

**c) Semantic discovery** — use MCP tools to find relevant code:
- `search_codebase` with a natural language query derived from the task
- `search_symbol` if the task mentions a specific function, class, or component
- `search_multi` with 2-3 related queries for multi-area tasks

**d) Session memory** — call `search_past_sessions` with the task description. Include top 3 results as historical context if relevant.

**e) Read source files** — Read the actual files that will be MODIFIED. Embed their full content when passing to subagents.

**Prefer MCP search over blind Glob/Grep** — semantic search finds conceptually related code.

### Step 5 — Plan (skip for TRIVIAL and SIMPLE)

Read `_vibecoding_brain/agents/planner.md`. Spawn an Agent with that prompt plus:
- Task description, complexity, domain
- Full content of AGENTS.md
- Relevant file paths from project index
- Any matching problem prevention rules

Write the returned plan to: `_vibecoding_brain/sessions/{session_id}/plan.md`

### Step 6 — Design Brief (only if frontend-visible AND complexity >= MEDIUM)

Read `_vibecoding_brain/agents/creative_brain.md`. Spawn an Agent with that prompt plus:
- Task description
- Full `plan.md` content
- Contents of `_vibecoding_brain/context/design_system.md`
- Injected skills (see Skill Injection Table)

Write to: `_vibecoding_brain/sessions/{session_id}/design_brief.md`

### Step 7 — Implement

For **TRIVIAL**: Make the change yourself directly. No implementer agent needed.

For **SIMPLE and above**: Read `_vibecoding_brain/agents/implementer.md`. Spawn an Agent with:
- Task description
- Full `plan.md` content (if exists)
- Full `design_brief.md` content (if exists)
- **Actual file contents** of every file listed under "Files to MODIFY/READ"
- Architecture rules from this file
- Injected skills (see Skill Injection Table)
- Any matching problem prevention rules

The implementer writes files directly to disk using Write/Edit tools.

### Step 7.5 — Self-Healing Validation

After implementation, validate changed files:
```bash
# Frontend
npx tsc --noEmit 2>&1 | head -50
npx eslint <changed-files> 2>&1 | head -50
# Backend
python3 -m ruff check <file> 2>&1 | head -50
```

If errors: re-spawn implementer with fix instructions. Max 2 self-healing rounds before testing.

### Step 7.75 — Quality Gate Check

Check all modified `.tsx/.ts/.jsx/.js/.css` files for these banned patterns:
- `bg-gradient-to` or `from-purple` or `to-blue` — ban AI-slop gradients
- `rounded-2xl` — must use graduated border-radius
- `import ... from 'lucide-react'` — must use Phosphor icons
- `font-bold` or `font-[700]` — max weight 600 in product UI unless page heading
- Raw tailwind classes like `bg-zinc-*`, `text-indigo-*` — use Montrroase tokens
- Emojis used as UI elements (emoji inside JSX tags)

If any match: re-spawn implementer with specific fix instructions before testing.

### Step 8 — Test Loop (max 8 iterations)

**Skip for TRIVIAL.** For SIMPLE with risk LOW, testing is optional (use your judgment).

Choose tester(s) based on domain:
- **Frontend-visible:** Read `_vibecoding_brain/agents/ui_ux_tester.md`, spawn Agent with injected skills
- **Backend:** Read `_vibecoding_brain/agents/backend_tester.md`, spawn Agent with injected skills
- **FULLSTACK:** Spawn **both** testers concurrently — FAIL if either fails

Give testers: plan + design_brief (if applicable) + full content of every written file.

**If FAIL:** Extract fix instructions, increment iteration counter (N).
- If N < 8: re-spawn implementer with fix instructions (see Reflection on Retry)
- If N >= 8: stop, mark status as `fail_max_retries`

**If PASS:** Proceed to wrap-up.

**Stuck detection:** If same core issue appears 3 consecutive times, STOP. Mark status `stuck`.

### Step 9 — Problem Tracking (fix: tasks only)

On `fix:` prefixed tasks that PASS testing:

Read `_vibecoding_brain/agents/problem_tracker.md`. Spawn an Agent (model: haiku) with:
- Original problem description
- Files involved in the fix
- Summary of what was changed
- Tester's verdict

The problem tracker writes a preventive rule to `_vibecoding_brain/problems/rules.md`.

### Step 10 — Wrap Up

**TRIVIAL:** Report what was changed. No artifacts. No session indexing.

**SIMPLE:** Write a brief walkthrough to `_vibecoding_brain/sessions/{session_id}/walkthrough.md`. Index the session.

**MEDIUM / COMPLEX:**
1. Write `_vibecoding_brain/sessions/{session_id}/walkthrough.md`:
   - What was built and why
   - Every file changed with a one-line description
   - Architectural decisions made
   - Follow-up items out of scope

2. Write `_vibecoding_brain/sessions/{session_id}/reflection.md`:
   - What went well
   - What went poorly (if retries, why)
   - What the tester caught that the implementer missed
   - One concrete suggestion for improving agent prompts

3. Call `index_session` MCP tool with:
   - session_id, original prompt, outcome (pass/fail/stuck), summary, files_touched list, iterations count

4. Output this JSON block:
```json
{
  "session_id": "{session_id}",
  "status": "pass | fail_max_retries | stuck",
  "files_written": ["path/to/file1.tsx"],
  "iterations": N,
  "review_verdict": "PASS | FAIL",
  "summary": "2-3 sentence summary.",
  "quality_assessment": {
    "correctness": 0.0,
    "completeness": 0.0,
    "code_quality": 0.0,
    "notes": "Brief self-assessment"
  }
}
```

---

## Skill Injection

When spawning agents, read the relevant skill files from `_vibecoding_brain/agents/skills/` and append their content to the agent's prompt.

### Skill Injection Table

| Skill File | Injected Into | When |
|---|---|---|
| `web_accessibility.md` | ui_ux_tester | FRONTEND / FULLSTACK / DESIGN |
| `playwright_testing.md` | ui_ux_tester | Only when dev server URL is available |
| `code_review.md` | backend_tester | BACKEND / FULLSTACK / DATABASE / REFACTOR |
| `frontend_design.md` | creative_brain, implementer | FRONTEND / FULLSTACK / DESIGN |
| `ui_ux_pro_max.md` | creative_brain | FRONTEND / FULLSTACK / DESIGN |
| `web_design_guidelines.md` | creative_brain, ui_ux_tester | FRONTEND / FULLSTACK / DESIGN |

### Injection Format
Read the skill `.md` file and append it to the agent prompt separated by `---`:
```
[agent prompt content]

---

[skill file contents]
```

---

## Pipeline Rules

### Context Compression
Between agents, compress outputs to <200 words. **Exception**: implementer and tester MUST receive full file contents — never summarize code.

### Embedding Files in Subagent Prompts
```
## File: path/to/file.tsx
\`\`\`tsx
[file contents]
\`\`\`
```

### Reflection on Retry
Before re-spawning implementer on retry N > 1:
> "Attempt {N}/8. Before retrying: 1) What specifically failed? 2) What is ONE concrete change that would fix it? 3) Are you repeating the same approach? If yes, try a fundamentally different approach. The reviewer found these issues: {fix_instructions}. Fix EXACTLY these — do not refactor or change anything not flagged."

### Parallel Execution
When pipeline allows concurrent work (FULLSTACK testing), spawn multiple subagents in the same response turn.

### Session Artifacts
All artifacts go in `_vibecoding_brain/sessions/{session_id}/`:
- `plan.md`, `design_brief.md`, `review.md`, `walkthrough.md`, `reflection.md`

Generate `session_id` as a kebab-case slug, max 40 chars (e.g. `add-dark-mode-toggle`).

### Context Docs (read when needed)
- `_vibecoding_brain/context/design_system.md` — Full design tokens, component patterns
- `_vibecoding_brain/context/tech_stack.md` — Stack decisions, testing, deployment
- `_vibecoding_brain/context/project_index.md` — Key files with descriptions
- `_vibecoding_brain/context/montrroase_guide.md` — Business domain, user roles, features, data flows, infrastructure

### Problem Prevention Rules
- `_vibecoding_brain/problems/rules.md` — Learned rules from past bugs. Read during context gathering.
- Rules are written by the Problem Tracker agent after confirmed fixes.
- If `rules.md` exceeds 100 rules, use `search_codebase` against it rather than reading the whole file.
