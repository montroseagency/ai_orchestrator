# Montrroase Problem Prevention Rules
> Read by the orchestrator at Step 2 (Gather Context) to avoid repeating past mistakes.
> Rules are appended by the Problem Tracker agent after confirmed fixes.
> Format: RULE-{number}: [DOMAIN] Title

---

<!-- Rules will be appended below this line -->

## RULE-1: [FRONTEND] All UI Colors Use CSS Custom Properties, Never Raw Tailwind or Hex

**Why:** Phase 4 testing found color token violations in CommandCenter.tsx and reports/page.tsx—hover states, icon maps, Recharts SVG attributes all using raw Tailwind classes (`text-red-500`) or hardcoded hex values (`#FF6B6B`). This breaks theming and design system consistency.

**How to apply:** On any frontend file change: grep for `text-*`, `bg-*`, `fill="*"`, `stroke="*"` and verify they use Montrroase tokens (`--color-status-*`, `--color-accent`, `--color-border`, etc.) instead. This applies to both Tailwind class attributes AND SVG fill/stroke in charts. Check `CommandCenter.tsx` and any Recharts integrations especially.

---

## RULE-2: [FRONTEND] Tab-Like Selectors Must Implement Full ARIA Tab Semantics

**Why:** Developer agent portal report type selector was missing tab pattern semantics—no `role="tablist"`, `role="tab"`, `aria-selected`, `aria-controls`, or `aria-labelledby`—making it inaccessible to screen readers.

**How to apply:** Any tab, pill, or segmented button selector pattern must have: `role="tablist"` on container, `role="tab"` + `aria-selected` + `aria-controls` on buttons, and `role="tabpanel"` + `aria-labelledby` on content sections. Check file changes touching selectors or filters.

---

## RULE-3: [BACKEND + FRONTEND] API Method Names Must Match Registered URL Paths Exactly

**Why:** `getDeveloperProjectOverview()` called `/agent/developer/projects/overview/` but the registered route was `/agent/developer/project-overview/`—silent mismatch causing 404s.

**How to apply:** After implementing new backend endpoints, cross-reference: extract the exact URL path from `server/api/urls.py` registration and verify every API method call in `client/lib/api.ts` uses that path. Consider adding a comment above the method showing the exact endpoint path.

---

## RULE-4: [FRONTEND] Backend Response Keys Must Match Frontend Type Definitions Exactly

**Why:** Backend serializer returned `project_id`/`project_name` while frontend types expected `id`/`name`; backend sent `pending_quotes` but frontend expected `quotes_pending`. Mismatches cause undefined values at runtime.

**How to apply:** After writing a new backend endpoint, extract actual response keys from the serializer's `fields` list and cross-verify them against `client/lib/types.ts` type definitions. If keys differ, update one to match. Add an inline comment above the API method showing the expected response shape to prevent key-name drift.

---

## RULE-5: [FRONTEND] Document Response Structure Differences for Multi-Agent Branches

**Why:** CommandCenter KPI strip read from wrong object path (`stats.active_projects` vs `data.developer_stats.active_projects_count`) because the response structure differed by agent type but wasn't documented.

**How to apply:** When a component branches on `agentType` (or similar), add an inline code comment above each branch showing which keys come from which part of the response object. Example: `// For developer agents: activeProjectsCount from data.developer_stats`

---

## RULE-6: [BACKEND] Defensive No-ops Must Raise Deprecation Warnings, Not Silently Fail

**Why:** `DeveloperDomainReportView` SSL warnings feature used `getattr(dc, 'ssl_expiry_date', None)` for a field that doesn't exist on the model, silently returning empty instead of surfacing the gap.

**How to apply:** When querying a field that may not exist on a model, add a comment explaining why (backwards compatibility, conditional fields, etc.). If the field will never exist, raise a deprecation warning or TODO comment instead of silently returning None—this surfaces permanent no-ops so they can be cleaned up or the feature can be completed.

---
