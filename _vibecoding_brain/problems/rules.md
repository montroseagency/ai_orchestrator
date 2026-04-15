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

## RULE-12: [BACKEND] Verify `related_name` Before Using Count() on Reverse Relations

**Why:** Two analytics endpoints 500'd because `Count("teamannouncementread")` and `Count("pollvote", distinct=True)` referenced guessed auto-names for reverse relations. The actual `related_name` values were `"read_by"` and `"votes"`. Django raised `FieldError` at query time, not at import, so it escaped static checks.

**How to apply:** Before writing `Count("...")` / `Sum("...")` / `Prefetch("...")` over a reverse relation, open the child model and read the FK's `related_name`. If missing, use `<modelname>_set`. Never guess. If the query is part of a new endpoint, hit it once in a shell or unit test before shipping — `FieldError` only fires on execution.

---

## RULE-13: [BACKEND] Date Arithmetic With Stored Birthdays Must Handle Feb 29

**Why:** `HomeSidebarViewSet._get_celebrations` crashed with `ValueError: day is out of range for month` because `date.replace(year=today.year)` fails on Feb 29 in non-leap years. The 500 only reproduced in non-leap years, making it a latent bug for any agent whose birthday or work-anniversary falls on the 29th.

**How to apply:** When shifting a stored date to the current year for anniversary/birthday logic, wrap `date.replace(year=…)` in try/except `ValueError` and fall back to `day=28`. Do this for every `Agent.birthday` / `Agent.work_anniversary` / any `DateField` used in "same day this year" comparisons. Add a test with a Feb-29 fixture.

---

## RULE-14: [FRONTEND] DRF-Paginated Endpoints Return an Envelope — Unwrap `.results` at the Call Site

**Why:** `/api/admin/approvals/` uses `LimitOffsetPagination` so it returns `{count, next, previous, results}`. The frontend typed it as `ApprovalTask[]` and passed the envelope to `DataTable`, which crashed on `[...data]`. The type annotation was a wish, not a check — TypeScript trusted the generic and missed it at compile time.

**How to apply:** When calling a paginated DRF endpoint from `api.ts`: type the response as `Paginated<T> | T[]` (or the specific envelope), unwrap `.results` at the call site, and pass the inner array to components. Never annotate a paginated response as a bare array. When wiring a new list endpoint, check the backend view for `pagination_class` / `paginator.get_paginated_response` before writing the frontend type.

---

## RULE-15: [BACKEND] Pair Post-Save Signals That Maintain Invariants With Backfill Data Migrations

**Why:** `auto_assign_marketing_agent_to_company` signal in Phase 1 created `ClientTeamAssignment` rows only on new Agent saves. Pre-existing marketing agents had no assignment row, causing permission 403s on company endpoints. The signal enforced an invariant but skipped backfilling historical data.

**How to apply:** When adding a post-save signal that creates or updates a related row to maintain an invariant, immediately add a data migration (`makemigrations --empty --name backfill_...`) that applies the same logic to all pre-existing rows. Use `get_or_create()` for idempotency and `apps.get_model()` for historical safety. Test the migration on production-like data volume. If the dependent model (like `Client`) is created by the signal, ensure the migration handles its absence.

---

## RULE-16: [DESIGN] Pure White on #FAFAFA Is Not Layering — Tint the Canvas

**Why:** The Marketing Management Command Centre shipped with `body { background: #FAFAFA }` and cards at `#FFFFFF`. Those two values are ~1.5% apart in lightness — the human eye reads them as the same color. Result: cards had no visible edge against the page, the dashboard looked like a blank Google Doc ("hospital white"), and the entire UI was rejected as unfit for a top-tier SaaS. The tokens were technically correct but blank-by-default, and implementers had no explicit rule to prevent this.

**How to apply:** Page canvas is `--color-canvas` (`#F5F7FA`) — a slate-tinted off-white, **never** pure `#FFFFFF` and **never** `#FAFAFA`. Cards use `--color-surface` (pure `#FFFFFF`) AND must carry both `1px solid --color-border` AND `var(--shadow-card)`. This is the **Contrast Rule** (`design_system.md` §0): every surface must be distinguishable from its parent by ≥4% lightness delta or by a border+shadow combo. Before submitting any frontend change, grep the diff for `bg-white` on page shells and for any `#FAFAFA` / `#FFFFFF` used as `body` or page background — reject if found. Run the Blank-Page Smell Test from `skills/frontend_design.md` during Chain-of-Thought planning.

---

## RULE-17: [DESIGN] Every Interactive Element Must Define Hover + Focus-Visible + Pressed

**Why:** Command Centre buttons and clickable rows had no visible hover feedback because the implementer left them as `<Link>`s with only default styles. "Minimalist" was used as justification, but missing a hover state is broken UX, not minimalism — users can't tell what's clickable. A dashboard without interactive feedback feels dead.

**How to apply:** For every `<button>`, `<a>`, `<Link>`, form control, clickable card, and interactive row, the code must define four states: (1) default, (2) hover — `background-color` shift, never cursor-only, (3) `focus-visible` — 2px accent ring with 2px offset via `box-shadow: var(--shadow-focus)`, (4) pressed/active — either darker bg or `transform: scale(0.98)`. Grep the diff for interactive elements missing `hover:` or `focus-visible:` classes. A "minimalist" button still animates on hover — "minimalist" describes color and density, not deadness.

---

## RULE-18: [DESIGN] Stat Tiles Need Left Rail, Icon Square, and Tabular Nums — Never "Nude Stats"

**Why:** The `StatTile` component rendered as "label + number in body font on pure white" with nothing else. No left status rail, no icon, no delta indicator, no `tabular-nums`. The number jittered when data refreshed (variable-width digits), had no visual anchor, and the tile read as a sentence fragment instead of a KPI card. This is the "nude stat" anti-pattern.

**How to apply:** Every stat tile must have (a) a 3px left status rail in `--color-accent`, `--color-success`, `--color-warning`, or `--color-error`, (b) an icon rendered inside a 32px `--color-accent-subtle` square with `--radius-sm`, (c) `font-variant-numeric: tabular-nums lining-nums` on the value (non-negotiable — prevents digit jitter on refresh), (d) a delta badge where a comparison is meaningful. Before shipping any dashboard/overview page, run the StatTile recipe from `design_system.md` §9.1 against each KPI.

---

## RULE-19: [DESIGN] Badges Must Use Tinted Bg + Inset Ring, Not Flat Solid Color

**Why:** Flat solid-color badges (`bg-green-500 text-white`) read as stickers — bolted on, not integrated. They break the 60-30-10 color discipline because the solid saturation competes with primary CTAs for attention. Quality SaaS (Linear, Stripe, Notion) uses the tinted-ring variant: subtle background tint + 1px inset ring + darker text. Restraint beats saturation.

**How to apply:** Every badge uses the pattern `background: var(--color-success-bg); color: var(--color-success); box-shadow: inset 0 0 0 1px var(--color-success-border);` (and equivalents for warning/error/info). Radius is `--radius-xs` (4px). Font is 12px/500. See `design_system.md` §9.4. Grep the diff for `bg-green-`, `bg-red-`, `bg-yellow-` on badge elements — reject and rewrite.

---
