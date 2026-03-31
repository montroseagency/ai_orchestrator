# Integration Notes: Gemini Review Feedback

## What I'm Integrating

### 1. Timezone strategy — INTEGRATING
**Why:** Gemini correctly identifies this as a footgun. The existing codebase uses wall-clock "HH:MM:SS" strings throughout with no timezone conversion. I'll add an explicit statement that this continues: all times are treated as wall-clock local times, and no timezone conversion is performed. The backend stores and returns times as-is. This is consistent with the existing codebase and avoids introducing a timezone library for this split.

**Change:** Add a "Timezone Strategy" note to Section 2 (Shared Utilities) documenting this decision explicitly.

### 2. `onDragOver` local state clarification — INTEGRATING
**Why:** The plan was ambiguous about how temporary visual state during cross-column drags is managed. Gemini is right that mixing `useState` with React Query for the same data is a footgun. I'll clarify: the temporary reorder state lives as a shallow `useState` override in `SchedulingEngine`, is reset in *both* `onDragEnd` and `onDragCancel`, and `DayColumn` receives a merged `displayBlocks` prop that combines query data + override.

**Change:** Clarify in Section 4 and Section 10.

### 3. Implementation order fix for collision utils — INTEGRATING
**Why:** The original plan listed "collision side-by-side layout" as step 13, but Section 7 and 8 already reference `getOverlapGroups` and `getSideBySideLayout`. The collision utilities must be in Section 2 (Shared Utilities). This is a clear sequencing error.

**Change:** Move collision logic into Section 2 where it belongs, remove it as a separate late step.

### 4. `+N more` indicator detail — INTEGRATING
**Why:** The plan mentioned "+N more" without explaining the interaction. Gemini correctly flags this as a footgun for layout shifts.

**Change:** Specify that clicking "+N more" opens a popover/modal (not an in-place expand) to avoid layout shifts.

### 5. Single `useDroppable` per column instead of per-slot — INTEGRATING
**Why:** 160 droppable DOM nodes in week view is a legitimate performance concern. The alternative — one droppable per column, with Y-coordinate math in `onDragEnd` — is cleaner and avoids rendering 160 nodes.

**Change:** Update Section 8 to use a single `useDroppable` per `DayColumn`, calculate `hour`/`minute` from `event.clientY` and column's `getBoundingClientRect().top` in `onDragEnd`.

### 6. Backlog sort order — INTEGRATING
**Why:** Obvious gap. Default sort: priority desc (high first), then `due_date` asc (soonest first), then title asc.

**Change:** Add sort order to Section 6.

### 7. AllDayHeader expand behavior — INTEGRATING
**Why:** In-place expand causes layout shift. Popover is cleaner.

**Change:** Update Section 7 to specify "Show N more" opens a popover, not in-place expand.

### 8. `onDragCancel` handler — INTEGRATING
**Why:** Gemini correctly points out that cancelled drags must reset visual state. This was missing from the plan.

**Change:** Add `onDragCancel` to Section 4 and Section 10.

---

## What I'm NOT Integrating

### Timezone library (date-fns-tz / luxon)
**Why not:** The existing codebase uses raw "HH:MM:SS" strings throughout — `DaySchedule.tsx`, `CommandCenter.tsx`, all API responses. Introducing a timezone library for this split creates an inconsistency (the new calendar uses timezone-aware conversions but the rest doesn't). Timezone support is a cross-cutting concern requiring backend changes as well. Explicitly documenting "wall-clock, no TZ conversion" is the right call for now.

### Server-side search for backlog
**Why not:** Premature optimization. The backlog shows tasks for a single day — typically < 20–30 items. Client-side filtering is fast enough. Implement server-side search if pagination is added later.

### Granular WebSocket invalidation (per-date keys)
**Why not:** Adds meaningful complexity (requires backend to include affected dates in WS messages) for a marginal gain. Broad `SCHEDULE_KEYS.timeBlocks.all` invalidation with 30s staleTime is acceptable. Note the limitation in the plan.

### E2E tests (Playwright/Cypress)
**Why not:** Out of scope for the implementation plan. The project doesn't currently have an E2E testing setup. Worth a future dedicated split.

### Backend-persisted user preferences
**Why not:** Out of scope. `localStorage` is appropriate for view mode and collapse state at this scale.

### Authorization bypass security note
**Why not:** The Django backend already validates the authenticated user's agent type on every API request — this is an existing pattern throughout the codebase. The `agentType` URL param is used for routing, not authorization. No change needed.

### Concurrent edit conflict resolution
**Why not:** Out of scope. Documenting "last-write-wins" as the strategy is sufficient.

### `DaySchedule` prop validation edge cases
**Why not:** The prop refactor adds backward-compatible optional props with safe defaults. Input validation for edge cases (startHour > endHour, hourHeight = 0) is an implementation detail for the implementer to handle. The plan doesn't need to prescribe defensive coding style.
