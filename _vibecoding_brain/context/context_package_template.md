# Context Package Template

> Reference for the orchestrator. Assemble this package from RAG results + file reads BEFORE spawning any agents. Embed the completed package in each agent's prompt as **dynamic content** (after the cache boundary — see Prompt Assembly Order below), sliced by domain.

---

## Prompt Assembly Order (CACHE-FRIENDLY — STRICT)

Claude's prefix cache fires when the leading content of a prompt is identical across spawns within a 5-minute window. To take advantage of this, **every agent prompt is assembled in this exact order**:

```
─── STATIC (cacheable) ──────────────────────────────
1. Agent identity & instructions  (from agents/{agent}.md)
2. Architecture rules             (from CLAUDE.md Architecture Rules section)
3. Domain-filtered prevention     (from problems/rules.md, filtered by [FRONTEND]/[BACKEND]/...)
4. Injected skill text            (ONLY skills/contract_review.md for contract-reviewer — all other fake skills retired; agents invoke real plugins via Skill tool at runtime)
─── <!-- CACHE BOUNDARY --> ─────────────────────────
─── DYNAMIC (per-task) ──────────────────────────────
5. Task description
6. Context Package                (RAG results + source files + design tokens — this template)
7. Files to MODIFY                (full contents)
8. Completion instruction         ("mark your task completed when done")
```

**Never interleave dynamic content into the static prefix.** Putting the task description above the architecture rules breaks the cache key and forces a full re-read on every spawn.

The `<!-- CACHE BOUNDARY -->` marker is a comment for orchestrator sanity checks — it has no effect on Claude, it just documents where the static/dynamic split is.

---

## Template

```markdown
# Context Package
> Task: {task description from user}
> Session: {session_id}
> Complexity: {TRIVIAL|SIMPLE|MEDIUM|COMPLEX} | Domain: {FRONTEND|BACKEND|FULLSTACK} | Risk: {LOW|MEDIUM|HIGH}

## RAG Results

### Relevant Code
{Top 5 results from search_codebase / search_multi — each entry:}
**{file_path}** (relevance: {score}%)
\`\`\`{lang}
{code snippet from RAG result}
\`\`\`

### Symbol References
{Results from search_symbol — each entry:}
**{symbol_name}** in `{file_path}` line {line_number}
\`\`\`{lang}
{symbol definition snippet}
\`\`\`

### Past Sessions
{Results from search_past_sessions, if any:}
- **{session_id}**: {outcome} — {summary}
  Files touched: {file_list}

{If no past sessions match: "No similar past sessions found."}

## Design Tokens
> FRONTEND / FULLSTACK / DESIGN tasks only. One-line pointer — agents call the `ui-ux-pro-max` and `frontend-design` plugins at runtime for task-specific design guidance.
>
> "Read `context/design_system.md` for the brand non-negotiables (taste floor). For everything else — component composition, spacing choices, motion choreography, chart recommendations, a11y tactics — call `Skill({skill: 'ui-ux-pro-max:ui-ux-pro-max'})` and `Skill({skill: 'frontend-design:frontend-design'})` yourself. On conflict, `design_system.md` wins."

## Source Files

### Files to MODIFY
{For each file the agent will edit — include FULL content:}
#### {relative/path/to/file.ext}
\`\`\`{lang}
{full file contents — never summarize}
\`\`\`

### Files to READ (reference only)
{For each file the agent needs for context but won't edit:}
#### {relative/path/to/file.ext}
\`\`\`{lang}
{full file contents or relevant excerpt}
\`\`\`

### Imported Dependencies
> Pulled from the dependency-graph walk (CLAUDE.md Step 5 Phase B substep 4.5). For each MODIFY target, its direct imports (max 10 total, skipping node_modules / stdlib / external packages).
#### {relative/path/to/imported.tsx}
\`\`\`{lang}
{full file contents}
\`\`\`

## Backend API Contract
> FULLSTACK frontend implementer only. Copied verbatim from `impl-backend`'s summary. This is the source of truth for frontend types and API calls.
{The `## API Contract` block from impl-backend's summary output}
```

---

## Agent-Specific Slicing

When embedding the context package in an agent's prompt, include only the sections relevant to that agent:

| Agent | RAG Results | Source Files (MODIFY) | Source Files (READ) | Imported Deps | Design Tokens | Backend API Contract |
|-------|-------------|----------------------|--------------------|----|---------------|----------------------|
| **architect** | All results | Paths only (no contents) | Paths only | — | Pointer line only — plugin-sourced at runtime | — |
| **implementer** | All results | Full contents | Full contents | Full contents | Pointer line (if frontend task) — plugin-sourced at runtime | — |
| **impl-backend** | Backend results | Backend files (full) | Related backend files | Full contents | — | — |
| **impl-frontend** | Frontend results | Frontend files (full) | Related frontend files | Full contents | Pointer line — plugin-sourced at runtime | **Full block** (source of truth) |
| **contract-reviewer** | — | `api.ts`, `types.ts`, new/modified `urls.py` + views + serializers | — | — | — | **Full block** (source of truth) |

**Prevention rules** are handled separately — they sit inside the static prefix (step 4 above), domain-filtered per agent. Do not re-embed them inside the Context Package.

**Architecture rules** are handled separately — they sit inside the static prefix (step 3 above). Do not re-embed them inside the Context Package.

---

## RAG Query Protocol

The orchestrator runs these queries to build the context package:

### Phase A — Broad Discovery (always run)
1. `search_multi` with 2-3 queries:
   - Raw task description
   - "existing implementation of {feature area}"
   - Related component/endpoint names (if identifiable from task)
2. `search_past_sessions` with task description
3. **FRONTEND / FULLSTACK / DESIGN tasks only:** no design-token RAG query needed anymore. The `## Design Tokens` slice of the Context Package is a single pointer line that tells the agent to call `ui-ux-pro-max` and `frontend-design` plugins via the `Skill` tool and to check `context/design_system.md` for the non-negotiable taste floor. Do NOT RAG-inject design tokens into the prompt.

### Phase B — Symbol Lookup (if task names specific code)
4. `search_symbol` for each named function/class/component in the task
4.5. **Dependency graph walk:** after identifying a MODIFY target file, pull its direct imports:
   - **Preferred (when available):** call `get_file_imports` MCP tool → Read each returned path.
   - **Interim fallback:** `Grep` the target file for `^(import|from) .* ['"](\.\.?/[^'"]+)['"]` (TS/JS) or `^from (\.\.?\w+) import` (Python). Resolve relative paths against the target's directory. `Read` each resolved file.
   - Cap at 10 imported files total. Skip `node_modules`, stdlib, and external packages.
   - Add them to the Context Package under `### Imported Dependencies`.
5. `get_file` for any file paths mentioned in the task

### Phase C — Contract Discovery (FULLSTACK tasks only)
6. `search_codebase` with "API endpoint for {feature}"
7. `search_symbol` for the relevant API method name in `api.ts`

### Fallback (if RAG MCP unresponsive >30s)
- `Glob` patterns based on task keywords
- `Grep` for symbol names in likely directories
- Direct `Read` of files from `context/project_index.md`

### Results Processing
- Filter: discard results below 25% relevance
- Deduplicate: same file+chunk in multiple queries → keep highest score
- Sort: relevance descending
- Expand: for files to MODIFY, read the FULL file (not just the RAG chunk)
- Cap: max 5 RAG snippets per section to keep context manageable
