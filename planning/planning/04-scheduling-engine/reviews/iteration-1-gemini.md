# Gemini Review

**Model:** gemini-2.5-flash
**Generated:** 2026-03-28T23:29:29.005977

---

This is an exceptionally detailed and well-structured implementation plan. It clearly outlines the scope, existing context, technical approach, and even a phased implementation order. The use of React Query for server state, optimistic updates, WebSocket integration, and `@dnd-kit` are all excellent choices for building a highly interactive and responsive application.

However, even the best plans have areas for improvement, clarification, or potential pitfalls. Here's my assessment, broken down by category, with specific references to your plan:

---

## Architectural Problems & Missing Considerations

1.  **Critical: Time Zone Management (Sections 2, 3, 5)**
    *   **Problem:** This is the *number one footgun* in any scheduling application. The plan mentions `timeToMinutes`, `minutesToTime`, `selectedDate: string`, and `start_time`/`end_time` for `AgentTimeBlock`. It's unclear how time zones and Daylight Saving Time (DST) are handled.
    *   **Specifics:**
        *   Are `start_time` and `end_time` on `AgentTimeBlock` and `AgentGlobalTask` wall-clock times ("HH:MM") or do they imply a specific time zone? If wall-clock, converting them to backend `datetime` objects (Django `DateTimeField` stores UTC by default) will be error-prone during DST transitions (e.g., 2 AM can appear twice or not at all).
        *   How does `isoDateToWeekDays(isoDate: string)` handle the `isoDate`'s time zone context?
        *   When `setSelectedDate` is called from the date picker (Section 5), the native `<input type="date">` returns a local date. If the internal logic or backend expects UTC, this conversion needs to be explicit and correct. A simple `new Date("YYYY-MM-DD").toISOString().split('T')[0]` might yield the wrong date depending on local timezone offset.
    *   **Actionable:**
        *   **Define a clear time zone strategy:** E.g., all times stored as UTC on the backend, converted to a specific timezone (e.g., agent's local timezone, or a fixed corporate timezone) for display on the frontend.
        *   **Specify data format:** Clearly state whether `start_time`/`end_time` are plain "HH:MM" strings (which implies a date context for meaningful backend storage), or if they are full `ISO 8601` strings with timezone info.
        *   **Utility for conversions:** Introduce a robust date/time library (like `date-fns-tz` or `luxon`) and specific utilities for converting between display time (local/chosen TZ) and backend storage time (UTC).

2.  **Ambiguous: `onDragOver` Local State for Visual Reordering (Sections 4, 10)**
    *   **Problem:** The plan states "optimistically reorder `timeBlocks` in local component state (not query cache — use `useState` override)" during `onDragOver`. Mixing `useState` with `React Query`'s single source of truth for the *same data* (`timeBlocks`) is a significant footgun for consistency.
    *   **Specifics:**
        *   How is this `useState` data merged with or derived from the `useSchedulingEngine`'s `timeBlocks`?
        *   When is this `useState` data reset or discarded? On `onDragEnd` *and* `onDragCancel`? If not, a cancelled drag could leave the UI in a desynced state.
    *   **Actionable:**
        *   **Clarify State Management:** Detail the exact mechanism for this temporary visual state. A safer pattern is to pass `timeBlocks` from `useSchedulingEngine` as a prop, and `DayColumn` (or `WeekGrid`) holds a temporary, shallow copy for visual reordering *only*, which is immediately discarded on `onDragEnd`/`onDragCancel`.
        *   **Explicit reset:** Ensure `onDragCancel` handler is explicitly mentioned for resetting this visual state.

3.  **Scalability: Global Tasks & Backlog (Section 3, 6)**
    *   **Problem:** "fetches `AgentGlobalTask[]` in two filtered calls: Today's tasks... Overdue tasks..." and client-side search. If an agent has hundreds or thousands of overdue tasks, this could lead to:
        *   **Performance:** Slow initial load and slow client-side search/filtering.
        *   **Memory:** High memory consumption on the client.
    *   **Actionable:**
        *   **Consider pagination/infinite scroll:** For `globalTasks`, especially the "Overdue" section, implement pagination or infinite scrolling. The API should support `offset`/`limit` or `page` parameters.
        *   **Server-side search:** For larger backlogs, move search functionality to the backend.

4.  **Targeted WebSocket Invalidation (Section 3)**
    *   **Problem:** `queryClient.invalidateQueries({ queryKey: SCHEDULE_KEYS.timeBlocks.all })` is broad. If a single block changes, invalidating *all* blocks across *all* dates displayed in the week view (Mon-Fri) could lead to unnecessary re-renders and re-fetches, especially if a more granular key is available.
    *   **Actionable:**
        *   **Enhance WebSocket messages:** If possible, modify backend WebSocket messages to include the ID and relevant date(s) of the affected time block (`time_block_updated`, `time_block_created`, `time_block_deleted`).
        *   **Granular invalidation:** Use this information to call `queryClient.invalidateQueries({ queryKey: SCHEDULE_KEYS.timeBlocks.detail(affectedDate) })` or even `SCHEDULE_KEYS.timeBlocks.one(blockId)`.

5.  **Ambiguous: Overlapping Blocks Beyond 3 ("+N more") (Sections 2, 8, 13)**
    *   **Problem:** The plan mentions "Overlapping blocks beyond 3: third+ blocks get a '+N more' indicator". This is a good design pattern but lacks implementation detail.
    *   **Specifics:**
        *   How does `getSideBySideLayout` (Section 2) account for this? Does it calculate `{left, width}` for all blocks, or only up to 3?
        *   How is the "+N more" indicator rendered in `DayColumn.tsx`? Does it appear as a separate "block" or is it an overlay?
        *   What happens when a user clicks "+N more"? Does it expand the column or open a modal? If it expands the column, it will cause layout shifts.
    *   **Actionable:**
        *   **Detail `collisionUtils`:** Update `getSideBySideLayout` to explicitly handle the `+N more` scenario, potentially returning a different structure or capping the number of calculated `{left, width}` values.
        *   **Detail UI for `+N more`:** Specify how this indicator is rendered and what interaction it offers (e.g., modal with list of all overlapping tasks).

6.  **Missing: Weekend Days (Section 8)**
    *   **Problem:** `WeekGrid` only renders five `DayColumn` components (Mon–Fri). It's unclear if this is a business requirement that agents can *only* schedule Mon-Fri, or if weekends are simply not displayed.
    *   **Specifics:** If agents *can* schedule on weekends but they aren't visible, this is a significant data integrity and UX issue.
    *   **Actionable:**
        *   **Clarify business rules:** Explicitly state if scheduling on weekends is allowed/disallowed.
        *   **If disallowed:** Add validation (frontend and backend) to prevent weekend scheduling.
        *   **If allowed but not displayed:** Implement a way to view weekend schedules (e.g., via Day view only, or a toggle for Week view).

---

## Security Vulnerabilities

1.  **Authorization Bypass via `agentType` (Section 11)**
    *   **Problem:** The `agentType` is read from route params (`/dashboard/agent/{type}/management/calendar/`). If API calls (e.g., `getGlobalTasks`) use this `type` parameter to filter results, a malicious user could potentially modify the URL to access tasks or data for an `agentType` they are not authorized for (e.g., changing `/marketing/` to `/developer/`).
    *   **Actionable:**
        *   **Backend re-validation:** Ensure the Django backend *always* validates the `agentType` against the *authenticated user's actual roles/permissions* for *every* API call, not relying on the frontend-provided `agentType`. The frontend parameter should be treated as a preference for filtering, not an authorization token.

---

## Performance Issues

1.  **Many `useDroppable` Instances (Section 8)**
    *   **Problem:** "one `useDroppable` per 30min slot" means a `DayColumn` (16 hours * 2 slots/hr = 32 droppables) would have many droppables. A `WeekGrid` would have 5 * 32 = 160 droppables. While `@dnd-kit` is optimized, this many DOM nodes for drop targets can still introduce overhead, especially on initial render or during drag operations.
    *   **Actionable:**
        *   **Consider a single droppable per column:** An alternative is to make the entire `DayColumn` a single `useDroppable` and then calculate the exact drop `hour`/`minute` based on the `event.clientY` (Y-coordinate) relative to the column's top edge in `onDragEnd`. This reduces DOM overhead.
        *   **Benchmark:** Perform performance testing early, especially for `WeekGrid` with many blocks and droppables.

2.  **Collision Detection Performance (Section 2)**
    *   **Problem:** `getOverlapGroups` and `getSideBySideLayout` will be called whenever `timeBlocks` change. For a very large number of blocks in a single day, these computations (which are O(N log N) or O(N^2) depending on implementation) could become a bottleneck.
    *   **Actionable:**
        *   **Memoization:** Ensure these utilities are called with `useMemo` in `DayColumn.tsx` or `WeekGrid.tsx` to prevent re-calculation on every render if inputs haven't changed.
        *   **Benchmarking:** Profile `collisionUtils.ts` with a large dataset (e.g., 50-100 overlapping blocks in a single day) to identify potential bottlenecks.

---

## Footguns and Edge Cases

1.  **`DaySchedule` Prop Validation (Section 1)**
    *   **Footgun:** What if invalid values are passed to the new optional props? E.g., `startHour` > `endHour`, `snapMinutes` is 0 or negative, `hourHeight` is 0.
    *   **Actionable:** Add input validation or robust error handling within `DaySchedule.tsx` and the shared utilities to prevent division by zero, infinite loops, or illogical layouts.

2.  **`timeUtils.ts` Robustness (Section 2)**
    *   **Footgun:** `timeToMinutes` should handle invalid "HH:MM" strings gracefully (e.g., "25:00", "invalid"). `minutesToTime` should also be robust if minutes exceed 24 hours. `snapToSlot` needs to handle `snapMinutes` being zero or negative.
    *   **Actionable:** Add explicit input validation or error handling for these utility functions.

3.  **`AllDayHeader` Expansion (Section 7)**
    *   **Footgun:** "Show N more" collapsed state. If clicking it expands the `AllDayHeader` section by pushing down the main grid, this will cause layout shifts and affect the scroll position of the main calendar, which can be jarring.
    *   **Actionable:** Consider expanding into a modal or overlay instead, to avoid layout shifts in the main calendar area.

4.  **Click vs. Drag on `TimeBlockCard` (Section 9)**
    *   **Footgun:** "Clicking the card body (not drag or resize handles) opens `<TimeBlockEditor>` modal". Differentiating between a short click (for editing) and the start of a drag can be tricky, especially on touch devices. `PointerSensor`'s `distance: 8` helps, but users might still accidentally drag.
    *   **Actionable:**
        *   **Add a small delay** before a drag is registered, allowing clicks to pass through.
        *   **Consider an explicit edit icon** (e.g., a pencil) instead of relying on the whole card body, or use a right-click/long-press context menu.

5.  **`restrictToParentElement` and Off-Range Blocks (Section 13)**
    *   **Footgun:** "Drag to a slot before `startHour` (6 AM) or after `endHour` (10 PM): `restrictToParentElement` modifier on grid prevents this". What if an existing block (e.g., from a legacy import) *already* starts before `startHour` or ends after `endHour`? `restrictToParentElement` might prevent dragging it *back into* the visible range or modify its position unexpectedly.
    *   **Actionable:** Ensure the rendering logic handles blocks that fall partially outside `startHour`/`endHour` gracefully, even if they can't be dragged there. The `restrictToParentElement` should only apply to new drag operations.

---

## Unclear or Ambiguous Requirements

1.  **Sorting of Backlog Tasks (Section 6)**
    *   **Ambiguity:** How are `todayTasks` and `overdueTasks` sorted within their respective sections in the `BacklogPane`? By priority, due date, title, creation date?
    *   **Actionable:** Specify the default sorting order for backlog tasks for usability.

2.  **API Call Details for `completeTask` (Section 3)**
    *   **Ambiguity:** " `completeTask(taskId)` — marks task complete; removes from backlog". This implies an `updateGlobalTask` call, but the specific payload (`is_complete: true`?) and how `React Query` optimistically updates the `globalTasks` cache (removing the task) are not detailed.
    *   **Actionable:** Briefly describe the expected API payload and the cache update logic for `completeTask`.

---

## Anything Else Worth Adding to the Plan

1.  **Accessibility Testing & Strategy (General, Testing Plan)**
    *   **Recommendation:** While `KeyboardSensor` is mentioned, building a truly accessible interactive drag-and-drop/resize interface is extremely challenging.
    *   **Actionable:**
        *   **Explicit Accessibility Strategy:** Detail how `ARIA` attributes (`aria-grabbed`, `aria-dropeffect`), live regions (`aria-live`), and keyboard interactions will be implemented and tested for screen reader users and those with motor impairments.
        *   **Dedicated A11y Testing:** Add specific steps for manual keyboard navigation, screen reader testing (e.g., VoiceOver, NVDA), and automated accessibility scans (Lighthouse, axe-core) to the testing plan.

2.  **End-to-End (E2E) Testing (Testing Plan)**
    *   **Recommendation:** Given the high interactivity, complex drag-and-drop flows, and optimistic updates, E2E tests are crucial to catch integration issues that unit/component tests might miss.
    *   **Actionable:** Add E2E tests (e.g., Playwright, Cypress) to simulate full user journeys (drag from backlog, resize, move cross-day, complete task), verifying UI state and API calls.

3.  **Conflict Resolution for Concurrent Edits (General)**
    *   **Recommendation:** While optimistic updates + WebSockets provide a great UX for single users, real-time collaboration can lead to conflicts if multiple agents modify the same block simultaneously. The current plan implies a "last-write-wins" approach via WebSocket invalidation.
    *   **Actionable:** Acknowledge this limitation. If conflict resolution (e.g., merging changes, explicit conflict UI) is a future requirement, it's good to note it. Otherwise, state that "last-write-wins" is the chosen strategy.

4.  **User Preferences (Beyond `localStorage`) (Section 5, 6)**
    *   **Recommendation:** `localStorage` is fine for simple preferences like `viewMode` and `backlog_collapsed`. For more complex user preferences (e.g., custom `startHour`/`endHour`, default calendar view settings, specific backlog sorting preferences), a backend-persisted user settings API would be more robust and allow settings to roam across devices.
    *   **Actionable:** Consider if any future preferences might warrant backend storage. For now, `localStorage` is acceptable for the simple cases.

5.  **Small Refinement: Implementation Order (Last Section)**
    *   **Recommendation:** "13. Collision side-by-side layout" is listed quite late. Since `DayColumn` (7) already mentions using `getOverlapGroups` and `getSideBySideLayout`, this functionality needs to be available much earlier.
    *   **Actionable:** Move "13. Collision side-by-side layout" to be integrated with "2. Shared Utilities" or immediately after, definitely before "7. DayColumn".

---

This is a very strong plan. Addressing these points will make it even more robust, performant, and maintainable. Good luck!
