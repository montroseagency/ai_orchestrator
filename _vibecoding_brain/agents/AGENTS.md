# AGENTS.md — Montrroase Agent Registry

> Read by the orchestrator before spawning any agents. Single source of truth for who does what.

---

## Available Agents

### 1. Architect (`architect`)
- **File:** `agents/architect.md`
- **Role:** Combined technical planner + UX/visual designer. Produces a single `architect_brief.md` with a Technical Plan section and a Design Brief section. Replaces the old planner → creative-brain handoff. Never writes code.
- **When to use:** **COMPLEX tasks only.** SIMPLE and MEDIUM tasks skip the architect entirely — the implementer handles its own planning via Chain-of-Thought.
- **Input requires:** Task description, Context Package (architect slice), Design Tokens (RAG-retrieved).
- **Output:** `sessions/{session_id}/architect_brief.md`

### 2. Implementer (`implementer`)
- **File:** `agents/implementer.md`
- **Role:** General-purpose production code writer for SIMPLE tasks and single-domain MEDIUM+ tasks. Does its own Chain-of-Thought planning when no architect brief is present.
- **When to use:** SIMPLE tasks (any domain) and single-domain MEDIUM+ tasks (FRONTEND-only or BACKEND-only). For FULLSTACK MEDIUM+, use the specialized split implementers below.
- **Input requires:** Task description, Context Package, optional `architect_brief.md`.
- **Tool rules:** `Edit`/`MultiEdit` for existing files only; `Write` only for new files. `Write` on an existing path is rejected by the quality gate.
- **Note:** No MCP access. Uses Glob/Grep.

### 2a. Backend Implementer (`impl-backend`)
- **File:** `agents/impl_backend.md`
- **Role:** Backend-only code writer. Only touches `server/`. Runs **first** in FULLSTACK pipelines and emits a mandatory `## API Contract` block as the canonical source of truth for the frontend implementer.
- **When to use:** FULLSTACK MEDIUM+ tasks. Runs **before** `impl-frontend` (sequential, not parallel).
- **Input requires:** Task description, Context Package (backend slice), optional `architect_brief.md`.
- **Output contract:** Summary MUST contain a `## API Contract` block listing URL, method, permission class, pagination, request payload, response payload, `source=` remaps, and role-branched responses for every endpoint.

### 2b. Frontend Implementer (`impl-frontend`)
- **File:** `agents/impl_frontend.md`
- **Role:** Frontend-only code writer. Only touches `client/`. Runs **after** `impl-backend`, consuming the backend's `## API Contract` block as the source of truth for types and API methods. No guessing.
- **When to use:** FULLSTACK MEDIUM+ tasks. Runs **after** `impl-backend` finishes.
- **Input requires:** Task description, Context Package (frontend slice + Design Tokens), the backend's `## API Contract` block, optional `architect_brief.md`.

### 3. Contract Reviewer (`contract-reviewer`)
- **File:** `agents/contract_reviewer.md`
- **Role:** Surgical four-check gate verifying that frontend and backend can talk to each other. Checks URLs, HTTP methods, payload key mapping, auth headers — **nothing else**. Does NOT review code quality, design, security, or N+1 queries.
- **When to use:** FULLSTACK MEDIUM+ tasks, after `impl-frontend` finishes, before the deterministic quality gate runs.
- **Input requires:** `impl-backend`'s `## API Contract` block, `client/lib/api.ts`, `client/lib/types.ts`, the new/modified Django `urls.py` + views + serializers. Nothing else.
- **Verdict:** PASS (zero mismatches) or FAIL (any mismatch = runtime error = critical).
- **On FAIL:** Specifies which implementer to fix (default: frontend adapts to backend) and sends fix instructions via `SendMessage`.

### 4. Problem Tracker (`problem-tracker`)
- **File:** `agents/problem_tracker.md`
- **Role:** Post-fix observer. Creates problem records and writes preventive rules to `problems/rules.md` so the same mistakes don't recur.
- **When to use:** After successful `fix:` tasks ONLY.
- **Output:** Appends rule to `problems/rules.md`, creates record in `problems/active/`.

---

## Retired Agents

These agents have been removed from the pipeline. Do not spawn them.

- `planner` — merged into `architect`.
- `creative-brain` — merged into `architect`.
- `ui-tester` — replaced by deterministic quality gate (`tsc`, `eslint`) + human visual review.
- `backend-tester` — replaced by deterministic quality gate (`ruff check`, `ruff format --check`).
- `code-reviewer` — renamed and narrowed to `contract-reviewer` (URLs / methods / payload keys / auth only).

---

## Model Selection

Set the `model` parameter when spawning each agent based on task complexity:

| Agent | SIMPLE | MEDIUM | COMPLEX |
|---|---|---|---|
| architect | — | — | opus |
| implementer | haiku | sonnet | opus |
| impl-frontend | — | sonnet | opus |
| impl-backend | — | sonnet | opus |
| contract-reviewer | — | sonnet | opus |
| problem-tracker | haiku | haiku | sonnet |

Default to **sonnet** if unsure. Use **haiku** for fast auxiliary work. Use **opus** only for COMPLEX planning or implementation.

**Note:** `impl-frontend`, `impl-backend`, and `contract-reviewer` are only used for FULLSTACK MEDIUM+ tasks. For SIMPLE or single-domain tasks, use the general `implementer`.

---

## Plugin Runtime Invocation

> **Replaces the old "Skill Injection" pattern.** We no longer bulk-inject `.md` skill files into agent prompts. Instead, each agent invokes real Claude Code plugins via the `Skill` tool itself, at runtime, against the specific task. Plugins own their knowledge (and update with the plugin) — no duplication in `agents/skills/`.

The following fake-skill files are **retired** (deleted from `agents/skills/`): `code_review.md`, `frontend_design.md`, `ui_ux_pro_max.md`, `web_design_guidelines.md`, `web_accessibility.md`.
The only surviving text-injected skill is `skills/contract_review.md` — it's project-specific (Montrroase's snake_case/camelCase 4-check protocol) and has no plugin equivalent.

### Plugin Invocation Table

| Agent | Invokes at runtime (via `Skill` tool) | When |
|---|---|---|
| **architect** | `ui-ux-pro-max` | Start of Design Brief phase (FRONTEND / FULLSTACK / DESIGN). Backend-only tasks skip this. |
| **implementer** | `frontend-design` → `ui-ux-pro-max` (if FRONTEND/FULLSTACK/DESIGN), then `simplify` | Design plugins first, before any code; `simplify` last, before the summary. |
| **impl-frontend** | `frontend-design` → `ui-ux-pro-max`, then `simplify` | Always. |
| **impl-backend** | `simplify` | Last step, before emitting the `## API Contract` block. |
| **contract-reviewer** | — (receives text-injected `skills/contract_review.md` only) | Already at FULLSTACK MEDIUM+. |
| **problem-tracker** | — | None. |

Orchestrator-invoked (not agent-invoked):

| Plugin | When |
|---|---|
| `chrome-devtools-mcp:a11y-debugging` | After Step 8.5 checkpoint, before Step 9 visual review. FRONTEND/FULLSTACK only, conditional on dev server being up. See CLAUDE.md Step 8.6. |

### Tool access

Agents must spawn with the `Skill` tool available. If spawned as `subagent_type: general-purpose`, no change needed (all tools). If using a restricted tool list, include `Skill` explicitly.

---

## Context Index

Read these files when needed for context:

| File | Purpose |
|---|---|
| `context/montrroase_guide.md` | Business domain, user roles, features, data flows, infrastructure |
| `context/design_system.md` | Full design tokens — **RAG source only; never bulk-injected** |
| `context/tech_stack.md` | Detailed stack decisions, testing, deployment |
| `context/project_index.md` | Every key file with one-line description |
| `context/modal_guide.md` | Modal building patterns and rules |
| `context/context_package_template.md` | Context Package slicing, prompt-cache ordering, RAG protocol |
| `problems/rules.md` | Learned prevention rules (domain-filtered per agent) |

---

## Agent Spawning Checklist

Before spawning any agent, the orchestrator must:

1. Read the agent's `.md` file from `agents/`
2. Append `skills/contract_review.md` in the static prefix **only** for `contract-reviewer`. No other skill-file injection. All other agents call plugins via `Skill` themselves — see Plugin Invocation Table.
3. Assemble the prompt in the strict **static → dynamic** order (see CLAUDE.md Step 6)
4. Embed full contents of files the agent needs to read/modify (never summarize code) — as **dynamic** content, after the cache boundary
5. Include domain-tag-filtered prevention rules from `problems/rules.md` — as **semi-static** content
6. Include architecture rules from CLAUDE.md — **static**
7. Instruct the agent to mark its task as completed when done
8. Verify the agent has the `Skill` tool available (spawn as `general-purpose` or include `Skill` in the tool list). Remind the agent to use `Glob`/`Grep` for file discovery (NO MCP access).
9. Enforce tool rules: implementers must `Edit`/`MultiEdit` existing files; `Write` only for new files
