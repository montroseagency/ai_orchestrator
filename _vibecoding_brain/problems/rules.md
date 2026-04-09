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

## RULE-7: [BACKEND] URL Registration Uniqueness

**Why:** Duplicate path registrations cause Django to resolve first-match, shadowing later views. Two views registered at `admin/agents/` made all POST/PATCH/DELETE to the second view return 404. Only caught at code review.

**How to apply:** Before finalizing any URL registration:
1. Run `grep -n "path(" server/api/urls.py | grep "your-route-path"` and verify it appears exactly once
2. Check both direct `path()` calls and included routers for conflicts
3. Run `python manage.py check` to validate syntax
4. If changing an existing path, review git diff for shadowed registrations

See `_vibecoding_brain/problems/rule-7-url-uniqueness.md` for full detail.

---

## RULE-8: [BACKEND + FRONTEND] DRF Serializer update() Must Handle Related Model Fields Explicitly

**Why:** `PATCH /admin/agents/` with `first_name`/`last_name` silently ignored those fields. `setattr(agent_instance, 'first_name', value)` does nothing because those fields belong to the related `User` model, not `Agent`. No error was raised.

**How to apply:** Identify which fields in `Meta.fields` belong to related models. For each, explicitly fetch the related instance, apply changes, and call `.save()` on it separately. Test with partial PATCH requests that include only related-model fields to confirm persistence.

See `_vibecoding_brain/problems/rule-8-drf-related-fields.md` for full detail.

---

## RULE-9: [BACKEND] Assignment Guard Pattern for Delete Operations

**Why:** `DELETE /admin/agents/{id}/` always succeeded even when the agent had active client assignments, risking data orphaning. The assignment-check pattern existed in `client_assignment_views.py` but wasn't applied to the new delete view.

**How to apply:** Before allowing deletion of any assignable entity, check both `ClientTeamAssignment` (is_active=True) and direct Client FK fields (`marketing_agent`, `website_agent`). Return HTTP 400 with descriptive error if either exists. Follow the existing guard pattern in `client_assignment_views.py`.

See `_vibecoding_brain/problems/rule-9-assignment-guards.md` for full detail.

---

## RULE-10: [FULLSTACK] FK-to-M2M Migration Must Update All Frontend References

**Why:** Changing `specialization` (FK, string) to `specializations` (M2M, array) on the backend without updating the frontend type caused silent data loss — multi-specialization agents couldn't round-trip through the edit form. Contract verification happened after implementation.

**How to apply:** Treat FK→M2M (or any field shape change) as a breaking API contract change. Update simultaneously: model, serializer, `client/lib/types.ts`, all consuming components, and `client/lib/api.ts`. Grep for the old field name across the entire codebase before shipping. Use contract-reviewer to verify URL/field-name/auth alignment between frontend and backend.

See `_vibecoding_brain/problems/rule-10-fk-m2m-migration.md` for full detail.

---

## RULE-11: [FRONTEND] Destructive Actions Must Be Enforced in UI, Not Just Warned

**Why:** A delete dialog showed a warning about active client assignments but the button stayed enabled. Users could still delete, making the safety guard purely informational. Form state logic was incomplete.

**How to apply:** For any destructive action with preconditions: disable the button (`disabled={hasCondition}`), show an inline block message explaining why, and guard at the mutation call site. Warning text alone is not sufficient — enforcement must be in the DOM. Test that `disabled` attribute is present when preconditions aren't met.

See `_vibecoding_brain/problems/rule-11-destructive-action-safety.md` for full detail.

---
