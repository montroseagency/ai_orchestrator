# Context Package Template

> Reference for the orchestrator. Assemble this package from RAG results + file reads BEFORE spawning any agents. Embed the completed package in each agent's prompt, sliced by domain (see Agent-Specific Slicing table below).

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

## Prevention Rules
{Matching rules from _vibecoding_brain/problems/rules.md, filtered by domain tag:}
{Copy the full rule text for each matching rule}

## Architecture Rules
1. No fetch() directly — use typed functions in client/lib/api.ts
2. No inline styles — use Tailwind classes or CSS custom properties from globals.css
3. Server components by default — only add 'use client' when you need interactivity
4. Backend uses DRF. New endpoints go in server/api/views/ + registered in server/api/urls.py
5. JWT auth via client/lib/auth-context.tsx. Never bypass.
6. Shared types in client/lib/types.ts and client/lib/websiteTypes.ts
7. React Query for server state (@tanstack/react-query). No Redux.
8. Animations — Framer Motion only. Duration tokens: fast=150ms, default=200ms, slow=300ms
```

---

## Agent-Specific Slicing

When embedding the context package in an agent's prompt, include only the sections relevant to that agent:

| Agent | RAG Results | Source Files (MODIFY) | Source Files (READ) | Prevention Rules | Architecture Rules | Design System |
|-------|------------|----------------------|--------------------|-----------------|--------------------|---------------|
| **Planner** | All results | Paths only (no contents) | Paths only | All matching | Yes | No |
| **Creative Brain** | Frontend results | None | Reference files for UI context | [FRONTEND], [DESIGN] | Yes | Yes (full design_system.md) |
| **impl-backend** | Backend results | Backend files (full) | Related backend files | [BACKEND], [FULLSTACK] | Yes | No |
| **impl-frontend** | Frontend results | Frontend files (full) | Related frontend files | [FRONTEND], [FULLSTACK] | Yes | Yes (compressed key tokens) |
| **code-reviewer** | All results | All modified files (full) | None | [FULLSTACK] rules | Yes | No |
| **ui-tester** | None | Impl output files (full) | design_brief.md | [FRONTEND] | Yes | Yes (compressed) |
| **backend-tester** | None | Impl output files (full) | plan.md | [BACKEND] | Yes | No |

---

## RAG Query Protocol

The orchestrator runs these queries to build the context package:

### Phase A — Broad Discovery (always run)
1. `search_multi` with 2-3 queries:
   - Raw task description
   - "existing implementation of {feature area}"
   - Related component/endpoint names (if identifiable from task)
2. `search_past_sessions` with task description

### Phase B — Symbol Lookup (if task names specific code)
3. `search_symbol` for each named function/class/component in the task
4. `get_file` for any file paths mentioned in the task

### Phase C — Contract Discovery (FULLSTACK tasks only)
5. `search_codebase` with "API endpoint for {feature}"
6. `search_symbol` for the relevant API method name in `api.ts`

### Fallback (if RAG MCP unresponsive >30s)
- `Glob` patterns based on task keywords
- `Grep` for symbol names in likely directories
- Direct `Read` of files from `context/project_index.md`

### Results Processing
- Filter: discard results below 25% relevance
- Deduplicate: same file+chunk appearing in multiple queries → keep highest score
- Sort: relevance descending
- Expand: for files to MODIFY, read the FULL file (not just the RAG chunk)
- Cap: max 5 RAG snippets per section to keep context manageable
