# Integration Notes: Gemini Review Feedback

## Integrating

### 1. Timezone strategy (low risk, good to clarify)
Adding a note that time calculations assume the agent's local timezone. The existing `DaySchedule` and `CommandCenter` use the same approach (`new Date()` vs HH:MM strings) without timezone handling — so this is a known, accepted constraint. Documenting it prevents future confusion.

### 2. Block overlap/gap behavior (missing spec case)
The chronological sync spec didn't cover overlapping blocks or sub-minute gaps. Adding: overlapping blocks → pick the one with the latest `start_time` (most recently started); gaps of any size → "free until" state. This is deterministic.

### 3. Secondary sort order for tasks without `start_time` (missing spec detail)
Good catch. Adding: tasks without `start_time` sort by `order` field (already on `AgentGlobalTask`), then by `id` as stable tiebreaker.

### 4. "N min remaining" rounding (missing spec detail)
Adding: floor to nearest minute, show "Ending soon" when < 1 minute remains.

### 5. Progress bar ARIA attributes (accessibility)
Adding explicit `role="progressbar"`, `aria-valuenow`, `aria-valuemin`, `aria-valuemax` attributes to plan.

### 6. React.memo for child components (performance)
Adding note that stateless display children (`DashboardStatsRow`, `ReadOnlySchedule`, `CurrentTaskKpi`) should be wrapped in `React.memo` to prevent unnecessary re-renders on the 60s polling cycle.

### 7. Exact deep-link URLs for footer links (completeness)
The KPI widget deep-link is specified but the footer links are vague. Adding exact URL patterns for "View All in Portal →" and "Edit Schedule in Portal →".

---

## Not Integrating

### Backend API load concern
The `useCommandCenter()` endpoint already exists and is already polled at 60s by the existing `CommandCenter` component. This is not a *new* load on the backend — the new dashboard just adds one more consumer of an existing, already-polled endpoint. The suggestion to investigate payload size would be valid for a new endpoint, but not here.

### WebSockets/SSE alternative
Out of scope. The spec is explicit: 60s polling. Real-time WebSocket infrastructure would require backend changes and is far beyond this dashboard's requirements.

### i18n
The platform codebase uses hardcoded English strings throughout. There's no i18n infrastructure. Noting this is not something we can action at the component level.

### Observability / feature flagging
Valid enterprise concerns but out of scope for this feature plan. These are platform-level infrastructure concerns.

### Cross-device optimistic update race conditions
Addressed by `onSettled` invalidation which syncs to server state after every mutation. The backend is the source of truth. The optimistic update only affects the instant between click and server response — any stale state from another device is corrected on the next poll or mutation.

### Context API / state management for child props
Single dashboard page with 4 children and a flat data structure. Prop drilling is appropriate here and matches existing patterns in the codebase. Introducing Context or Recoil for a single page would be premature.

### Routing ambiguity
The plan's "exact path depends on route structure" guidance is intentional — the implementer should follow the existing convention in the codebase. Adding a concrete note to follow the marketing agent route directory pattern.

### Deep-link parameter validation in portal
Valid concern but out of scope for this plan — it's a Split 04 responsibility. Added as a noted dependency.
