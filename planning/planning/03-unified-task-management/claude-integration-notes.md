# Integration Notes: Gemini Review Feedback

**Review source:** `reviews/iteration-1-gemini.md` (Gemini 2.5 Flash)

---

## Integrating

### 1. Multi-Client Filtering Fallback — CHANGED
**Issue:** Plan said "fetch all tasks and filter client-side" as fallback for multi-client selection. Gemini correctly flagged this as a critical performance anti-pattern.

**Change:** Replace the fallback with a firm scope decision: support single-client filter only for this split. If the backend `GlobalTaskFilters` accepts only a single `client` ID, multi-client filtering is deferred out of scope. The filter bar still supports multi-select UI (chips), but only the first selected client is passed to the API hook when multi-client backend support is absent. This limitation is noted with a code comment. Multi-client backend filtering is scoped to a future backend task.

### 2. Bulk Operations — Strengthened Warning
**Issue:** Plan implied calling individual update/delete hooks in a loop. Gemini flagged N-requests for N tasks as unreliable and slow.

**Change:** Update the bulk operations section to explicitly state: if the backend exposes bulk endpoints (`PATCH /agent/schedule/global-tasks/bulk/`, `DELETE /agent/schedule/global-tasks/bulk/`), use them. If not, the per-item approach is acceptable for the split with a clear error-handling contract: show a toast per failure and keep the selection active for failed items. Add an explicit note in Edge Cases that bulk endpoints are the preferred future path.

### 3. Form State — Explicit Payload Shape
**Issue:** Plan's `formState` was described generically as "fields of AgentGlobalTask that are user-editable", which could allow accidentally including read-only system fields.

**Change:** Add an explicit list of user-editable fields to the modal section. The `useCreateGlobalTask` / `useUpdateGlobalTask` calls construct a typed payload from only those fields, never spreading the full `formState` or task object.

### 4. useCompleteGlobalTask vs useUpdateGlobalTask — Clarified
**Issue:** Plan used both hooks for "done" status without explaining when each applies.

**Change:** Add a clarification: use `useCompleteGlobalTask()` when moving a task to `done` via drag-and-drop or inline status change (this triggers backend JIT next-instance creation for recurring tasks). Use `useUpdateGlobalTask()` for all other status transitions (to-do, in-progress, in-review) and for field edits. The modal Save always uses `useUpdateGlobalTask()` for edits (it handles all fields including status).

### 5. ClientBadge null/undefined clientId — Edge Case Added
**Issue:** `getClientColor(clientId)` could receive null/undefined for unassigned tasks.

**Change:** Update Client Color System section: `getClientColor` should guard against null/undefined clientId and return a default gray (`#9CA3AF`). `ClientBadge` should render "Unassigned" label in that case.

### 6. DnD Error Feedback — Explicit Toast
**Issue:** Plan mentioned reverting optimistic state on error but didn't specify user feedback.

**Change:** Add: on DnD mutation error (revert fires), show a `sonner` toast: "Failed to move task — change reverted."

### 7. In Review Toast — Success-Only
**Issue:** Plan said "show a toast 'Task sent for review'" but didn't specify this only fires on success.

**Change:** Make explicit: toast "Task sent for review" fires in `onSuccess` callback only. On error, toast "Failed to update task status."

### 8. RecurrenceBuilder Extraction — Fate of RecurringTaskManager
**Issue:** Plan didn't clarify whether `RecurringTaskManager` is deprecated or remains in use.

**Change:** Add clarification: `RecurringTaskManager.tsx` is NOT modified or deprecated in this split. `RecurrenceBuilder.tsx` is a new component in `components/management/tasks/`, created by extracting and extending the relevant UI logic. `RecurringTaskManager` continues to serve its existing usage on other pages.

---

## Not Integrating

### Server-Side Pagination
**Why not:** Pagination is a backend API contract change (cursor/page params on `useGlobalTasks`). Scoping it into this frontend split would require backend coordination not planned for Split 03. The existing `useGlobalTasks` hook fetches with a defined staleTime; this is the established pattern across the codebase. Adding a comment noting the scalability concern is sufficient for now.

### Accessibility (DnD Keyboard Support)
**Why not:** Full DnD keyboard accessibility is a significant implementation effort (aria announcements, keyboard drag simulation) beyond the spec's scope. A brief "future work" note will be added, but implementing it fully is out of scope for this split.

### Timezone Handling
**Why not:** The interview confirmed dates are stored as-is (the backend handles UTC). No frontend timezone conversion logic is specified. Adding it would require defining timezone preferences per user/client, which is out of scope. The concern is valid for future work.

### Forms Library (React Hook Form / Formik)
**Why not:** The codebase doesn't use a forms library (confirmed in research). Adding one for a single modal would deviate from existing patterns and introduce a new dependency. `useState` + `setField` is consistent with how other modals in the codebase are implemented.

### Router Push Debouncing
**Why not:** Minor optimization. The search input is already debounced (300ms). For dropdown changes, a single `router.push` per selection is acceptable. This is micro-optimization territory not worth complicating the hook for.

### Rate Limiting
**Why not:** Backend concern, not within frontend plan scope.

### Automated A11y Color Contrast Tests
**Why not:** Out of scope for this split's test suite. The color palette was already chosen with readability in mind (15% opacity bg, full-opacity text). Future design audit can verify WCAG compliance.
