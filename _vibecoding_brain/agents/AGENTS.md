# AGENTS.md — Montrroase Agent Registry

> Read by the orchestrator before spawning any agents. This is the single source of truth for who does what.

---

## Available Agents

### 1. Planner (`planner`)
- **File:** `agents/planner.md`
- **Role:** Decomposition specialist. Turns task descriptions into structured `plan.md` with file lists, acceptance criteria, task breakdown, and risk flags. Never writes code.
- **When to use:** MEDIUM and COMPLEX tasks. Skip for TRIVIAL and SIMPLE.
- **Output:** `sessions/{session_id}/plan.md`

### 2. Creative Brain (`creative-brain`)
- **File:** `agents/creative_brain.md`
- **Role:** UI/UX design specialist. Produces `design_brief.md` with visual specs, state coverage, animation specs, UX copy, and accessibility notes. Contains the full Montrroase design standard and anti-AI-slop rules.
- **When to use:** Frontend-visible tasks at MEDIUM+ complexity. Skip for backend-only or SIMPLE tasks.
- **Input requires:** plan.md + `context/design_system.md`
- **Output:** `sessions/{session_id}/design_brief.md`

### 3. Implementer (`implementer`)
- **File:** `agents/implementer.md`
- **Role:** Production code writer. Follows plan + design brief precisely. Writes files directly to disk using Write/Edit tools.
- **When to use:** SIMPLE and above (for TRIVIAL, the orchestrator handles it directly).
- **Input requires:** plan.md (if exists) + design_brief.md (if exists) + full content of files to modify + architecture rules
- **Note:** Does NOT have MCP access. Uses Glob/Grep for file discovery.
- **For parallel work:** Spawn separate implementers with distinct names (`impl-backend`, `impl-frontend`)

### 4. UI/UX Tester (`ui-tester`)
- **File:** `agents/ui_ux_tester.md`
- **Role:** Adversarial quality gate for frontend. Checks AI-slop patterns, surface hierarchy, brand color discipline, modal quality, animation timing, typography, design system compliance, accessibility, and interaction quality.
- **When to use:** FRONTEND or FULLSTACK domain tasks. Skip for backend-only.
- **Verdict:** PASS (zero critical issues) or FAIL (one+ critical issues). Produces fix instructions on FAIL.

### 5. Backend Tester (`backend-tester`)
- **File:** `agents/backend_tester.md`
- **Role:** Adversarial quality gate for backend. Checks correctness, architecture compliance, security, performance (N+1 queries), and data integrity.
- **When to use:** BACKEND or FULLSTACK domain tasks. Skip for frontend-only.
- **Verdict:** PASS or FAIL. Security issues are ALWAYS critical.

### 6. Problem Tracker (`problem-tracker`)
- **File:** `agents/problem_tracker.md`
- **Role:** Post-fix observer. Creates problem records and writes preventive rules to `problems/rules.md` so the same mistakes don't recur.
- **When to use:** After successful `fix:` tasks ONLY.
- **Output:** Appends rule to `problems/rules.md`, creates record in `problems/active/`

---

## Model Selection

Set the `model` parameter when spawning each agent based on task complexity:

| Agent | SIMPLE | MEDIUM | COMPLEX |
|---|---|---|---|
| planner | sonnet | sonnet | opus |
| creative-brain | sonnet | sonnet | opus |
| implementer | haiku | sonnet | opus |
| ui-tester | haiku | sonnet | sonnet |
| backend-tester | haiku | sonnet | sonnet |
| problem-tracker | haiku | haiku | sonnet |

Default to **sonnet** if unsure. Use **haiku** for fast auxiliary work. Use **opus** only for complex planning or implementation.

---

## Skill Injection

Read skill files from `agents/skills/` and append to the agent's prompt separated by `---`.

| Skill File | Inject Into | When |
|---|---|---|
| `skills/web_accessibility.md` | ui-tester | FRONTEND / FULLSTACK / DESIGN |
| `skills/playwright_testing.md` | ui-tester | Only when dev server URL is available |
| `skills/code_review.md` | backend-tester | BACKEND / FULLSTACK / DATABASE |
| `skills/frontend_design.md` | creative-brain, implementer | FRONTEND / FULLSTACK / DESIGN |
| `skills/ui_ux_pro_max.md` | creative-brain | FRONTEND / FULLSTACK / DESIGN |
| `skills/web_design_guidelines.md` | creative-brain, ui-tester | FRONTEND / FULLSTACK / DESIGN |

**Injection format:**
```
[agent prompt content from agents/{agent}.md]

---

[skill file contents from agents/skills/{skill}.md]
```

---

## Context Index

Read these files when needed for context:

| File | Purpose |
|---|---|
| `context/montrroase_guide.md` | Business domain, user roles, features, data flows, infrastructure |
| `context/design_system.md` | Full design tokens, component patterns, animation guide |
| `context/tech_stack.md` | Detailed stack decisions, testing, deployment |
| `context/project_index.md` | Every key file with one-line description |
| `context/modal_guide.md` | Modal building patterns and rules |
| `problems/rules.md` | Learned prevention rules from past bugs |

---

## Agent Spawning Checklist

Before spawning any agent, the orchestrator must:

1. Read the agent's `.md` file from `agents/`
2. Read and append any required skill files (see Skill Injection table)
3. Embed full contents of files the agent needs to read/modify (never summarize code)
4. Include matching problem prevention rules from `problems/rules.md`
5. Include architecture rules from CLAUDE.md
6. Instruct the agent to mark its task as completed when done
7. Remind the agent: use Glob/Grep for file discovery (NO MCP access)
