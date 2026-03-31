# Gemini Review

**Model:** gemini-2.5-flash
**Generated:** 2026-03-29T03:27:11.761833

---

This implementation plan is comprehensive and well-structured, covering significant ground from UI components to data flow, testing, and implementation order. It addresses several common pitfalls explicitly, such as optimistic updates and DnD-Kit usage. Overall, this is a strong foundation.

My review identifies potential footguns, missing considerations, and areas for improvement, broken down by section.

---

## Overall Assessment & Key Recommendations

1.  **Bulk Operations API:** The most significant recurring concern is the plan to execute bulk operations (status change, delete) by calling individual task update/delete endpoints in a loop. This is a major performance and reliability footgun. **Strongly recommend creating dedicated bulk API endpoints** for these operations.
2.  **Scalability & Pagination:** The plan implies fetching all tasks client-side for filtering and sorting. This will become a significant performance bottleneck for even moderately large datasets. **Urgent consideration for implementing server-side pagination** for `useGlobalTasks` and potentially client-side virtualization for Kanban columns.
3.  **Client-Side Filtering of All Tasks:** Explicitly stated as a fallback for multi-client filtering, this decision should be reconsidered. Fetching "all tasks" and then filtering client-side for multi-select clients is a critical performance and scalability issue.
4.  **Security & Input Validation:** While touched upon, robust frontend and backend input validation, rich text sanitization, and careful definition of editable fields are paramount.
5.  **Accessibility (A11y):** DnD interactions and color contrast require explicit A11y considerations and testing.

---

## Detailed Review

### 1. Context
*   **No specific issues.** Clear scope and problem definition.

### 2. What We're Building
*   **Potential Footgun / Missing Consideration (Notifications):** "Triggers an admin notification... only after the API call succeeds." While frontend's role is clear, what is the *backend's* guarantee on notification delivery? If the notification service fails after the task status update, is there a retry mechanism or alert?
    *   **Actionable:** Verify with the backend team on notification delivery guarantees, potential retries, and failure modes post-API success.
*   **Performance / Architectural Problem (Bulk Operations):** "Supports bulk operations (bulk status change, bulk delete) in the List view." The plan later implies these use individual `useUpdateGlobalTask()` / `useDeleteGlobalTask()` calls.
    *   **Actionable:** As highlighted in key recommendations, **investigate or create dedicated bulk API endpoints.** Sending N individual requests for N selected tasks is inefficient, slow, and less atomic. What's the plan for partial failures (some succeed, some fail)?

### 3. File Structure
*   **No specific issues.** Logical and clean structure.

### 4. Data Layer

#### Types
*   **Potential Footgun (Type Changes):** "verify it includes `'yearly'` and `'custom'`; add them if missing." Modifying shared type definitions like `RecurrenceFrequency` could have unintended side effects on other parts of the platform that rely on this type.
    *   **Actionable:** Confirm the impact of `RecurrenceFrequency` changes on other features. If 'custom' or 'yearly' are added, ensure existing code handles them gracefully, or that existing code *won't* encounter them if not supported.

#### Hooks
*   **Performance / Architectural Problem (Bulk Operations):** `useCreateGlobalTask()`, `useUpdateGlobalTask()`, `useDeleteGlobalTask()` are likely designed for single operations. Using them in a loop for bulk operations (as implied for List View) leads to N API calls, which is inefficient, prone to partial failures, and increases server load.
    *   **Actionable:** Reiterate the need for bulk API endpoints. If not feasible for this split, clearly document the performance implications and define a robust frontend error handling strategy for partial success/failure (e.g., which tasks remain selected if they failed to update/delete).
*   **Unclear Requirement (Done Status):** `useCompleteGlobalTask()` is mentioned, but `useUpdateGlobalTask()` is also used for status changes (including `done`).
    *   **Actionable:** Clarify the specific use cases for `useCompleteGlobalTask` versus `useUpdateGlobalTask` when a task transitions to 'done'. Is `useCompleteGlobalTask` specifically for recurring tasks to trigger the next instance, and `useUpdateGlobalTask` for non-recurring tasks or general status changes?
*   **Security Vulnerability (Clients Hook):** "If none exists, create `useClients()` in `client/lib/hooks/useClients.ts` that fetches `GET /api/clients/`." This assumes the API endpoint correctly filters clients based on the agent's authorization. Fetching `/api/clients/` globally could expose clients an agent shouldn't see.
    *   **Actionable:** Confirm that the backend `/api/clients/` endpoint correctly enforces access control for the current agent. It should only return clients the agent is authorized to view.

#### Filter State
*   **Unclear Requirement (Status Filter):** "status: single `GlobalTaskStatus` value." This implies a single-select dropdown, which is acceptable but might be unexpected if users want to filter for "To-Do OR In Progress." The List View later clarifies it is single-select.
    *   **Actionable:** This is a design decision. No direct issue, but confirm with design if filtering by *multiple* statuses is ever desired.
*   **Edge Case (Invalid URL Params):** What happens if malformed or invalid URL parameters are present (e.g., non-existent client ID, invalid status string)?
    *   **Actionable:** Define error handling for malformed/invalid URL query parameters in `useTaskFilters()`. It should gracefully fallback to defaults or sensible values rather than crashing or displaying corrupted data.
*   **Performance (Router Push):** Using `router.push` on every filter change can be chatty. While `q` is debounced, multi-selects (clients, categories) could trigger many pushes in quick succession.
    *   **Actionable:** Consider debouncing or batching `router.push` calls for other filter changes, especially for multi-selects, to optimize router interactions.

### 5. View Toggle
*   **No specific issues.**

### 6. Kanban View

#### Drag-and-Drop Architecture
*   **Edge Case (Combined DnD):** "If the task moved to a different column... If the task stayed in the same column but changed position..." The logic needs to account for both: moving to a new column *and* changing position within that new column.
    *   **Actionable:** Refine `onDragEnd` logic to handle simultaneous status (column) and intra-column order changes correctly in a single update call or transaction if the backend supports it.
*   **Missing Consideration (DnD Error Feedback):** "Apply optimistic local state reordering immediately on drop, reverting on mutation error."
    *   **Actionable:** Add explicit user feedback (e.g., a toast notification) when a DnD mutation fails and the optimistic update is reverted, explaining why the task moved back.
*   **Accessibility (DnD):** While `cursor-grab` is present, DnD interactions need to be accessible for keyboard users and screen readers.
    *   **Actionable:** Add accessibility considerations for DnD, including `aria-label`s for drag handles, keyboard support for moving tasks, and screen reader announcements for drag events and status changes.

#### TaskCard
*   **Edge Case (Drag Handle vs. Card Click):** "Card click (not on drag handle) → opens `TaskModal` in edit mode." How is the "not on drag handle" part robustly implemented?
    *   **Actionable:** Ensure the card's click event handler correctly ignores clicks that originate from the drag handle element (e.g., by checking `event.target` or using `stopPropagation` carefully).

### 7. List View

#### Sortable Columns
*   **Performance / Architectural Problem (Client-Side Sorting):** "Sort state is local (not in URL) — it applies client-side on the fetched data array." If `useGlobalTasks(filters)` fetches *all* tasks, client-side sorting on large datasets is a significant performance bottleneck. This also means no pagination is currently supported.
    *   **Actionable:** This is a critical scalability issue. **Implement server-side pagination and sorting** for the List view if task counts are expected to exceed a few hundred. If pagination is not feasible for this split, document this limitation prominently and monitor task counts.

#### Bulk Selection
*   **Performance / Reliability / Architectural Problem (Bulk Operations):** Calls `useUpdateGlobalTask()` or `useDeleteGlobalTask()` for *each* selected ID. This is the same critical issue as discussed earlier.
    *   **Actionable:** **Strongly recommend creating dedicated bulk API endpoints for status changes and deletions.** If not done, provide clear error reporting for partial failures (e.g., "3 of 5 tasks deleted successfully, 2 failed due to X").

#### Mobile Card View
*   **No specific issues.**

### 8. Task Creation / Edit Modal

#### Form State
*   **Security Vulnerability (Editable Fields):** "All fields in a single `formState` object... form state shape mirrors the fields of `AgentGlobalTask` that are user-editable." If not carefully managed, this could allow users to submit changes to read-only or system-managed fields (e.g., `id`, `created_at`, `owner_id`).
    *   **Actionable:** Explicitly define *only* the user-editable fields in the form state. Ensure the payload sent to `useCreateGlobalTask()`/`useUpdateGlobalTask()` includes only these fields and doesn't implicitly allow modifying others. Backend validation is crucial here too.

#### Sections
*   **Security Vulnerability (Rich Text Editor):** "Description: rich text editor." If rich text allows HTML, it must be properly sanitized to prevent Cross-Site Scripting (XSS) vulnerabilities.
    *   **Actionable:** Ensure the rich text editor library (or custom logic) performs robust sanitization on user input before saving to the database. This is a critical backend concern, but frontend must also be aware and configure the editor appropriately.
*   **Missing Consideration (Input Limits):** What are the maximum lengths for title and description?
    *   **Actionable:** Specify maximum lengths for text inputs and implement frontend validation (matching backend limits) for better UX.
*   **Unclear Requirement (Timezone Handling):** "Due date: `<input type="date">` / Scheduled date: `<input type="date">` / Time range: ...`<input type="time">`". How are timezones handled for these dates and times? Are they stored in UTC, local time, or specific to a client? This is critical for scheduling.
    *   **Actionable:** Clarify the timezone strategy for all date/time fields. Backend should typically store in UTC, with frontend converting based on user/client timezone preferences for display and input.
*   **Unclear Requirement (`Save & Schedule`):** "For this split, the "Save & Schedule" button saves the task and shows a toast 'Calendar scheduling coming soon'."
    *   **Actionable:** Confirm that "Save & Schedule" *only* performs the save operation, and does not attempt any other scheduling-related logic for this split beyond showing a toast.

### 9. RecurrenceBuilder
*   **Architectural Problem (Extraction Impact):** "Extracted from `RecurringTaskManager.tsx` and extended... The existing `RecurringTaskManager` already has most of this UI — we extract it into `RecurrenceBuilder`." If `RecurringTaskManager` is still used elsewhere, simply extracting its UI might break it.
    *   **Actionable:** Clarify the fate of `RecurringTaskManager`. Is it deprecated/removed? Or is it being refactored to *use* `RecurrenceBuilder` internally? Ensure its extraction doesn't create silent regressions elsewhere.
*   **Unclear Requirement (Custom Frequency):** "Frequency selector (Daily / Weekly / Biweekly / Monthly / Yearly / Custom) ... Day-of-week checkboxes (Mon–Sun) — shown for Weekly and Custom frequencies." What exactly does "Custom" frequency mean? Is it a combination of existing fields, or something more flexible like a CRON string?
    *   **Actionable:** Clearly define the scope and parameters for "custom" recurrence frequency. Provide specific examples of what patterns it supports.

### 10. Client Color System
*   **Accessibility (Color Contrast):** "ClientBadge.tsx accepts `clientId` and `clientName`, calls `getClientColor(clientId)`, and applies the badge style: `backgroundColor: ${color}20`, `color`, `border: 1px solid ${color}40`." The light background with `text-xs` might have poor contrast depending on the specific color.
    *   **Actionable:** Verify color contrast ratios for the text within `ClientBadge` against its background to ensure WCAG AA or AAA compliance.
*   **Edge Case (Missing Client ID):** `getClientColor(clientId: string)` expects a string. What if `clientId` is `null` or `undefined` (e.g., for unassigned tasks)?
    *   **Actionable:** Handle `null`/`undefined` `clientId` gracefully in `ClientBadge.tsx` and `getClientColor` (e.g., return a default gray, or render a different "unassigned" style badge).

### 11. Filter Bar
*   **Performance (Router Push):** Same as `Filter State` section. Multiple filter changes could lead to many `router.push` calls.
    *   **Actionable:** Reiterate debouncing/batching router pushes for filter changes.
*   **Edge Case (Many Chips):** What happens if a user selects a very large number of client chips?
    *   **Actionable:** Consider UI scalability for a large number of selected filter chips (e.g., wrapping, horizontal scroll, or a count indicator with a modal for details).

### 12. Notification Flow (In Review)
*   **Missing Consideration (Error Feedback):** "Show a toast: 'Task sent for review' to confirm to the agent." This assumes `useUpdateGlobalTask()` always succeeds.
    *   **Actionable:** Ensure the "Task sent for review" toast only appears on API success. A different, informative error toast should be shown if `useUpdateGlobalTask()` fails.

### 13. Page Composition
*   **Performance / Architectural Problem (Scalability):** "Shared state between Kanban and List... fetched once by `useGlobalTasks(filters)` at the page level. Switching views does not re-fetch." This is good for view switching, but if `useGlobalTasks` fetches *all* tasks (without pagination), this remains a critical performance bottleneck for large datasets (as discussed under List View/Sortable Columns).
    *   **Actionable:** Re-emphasize the need for pagination and/or server-side filtering for `useGlobalTasks` if task volume is large. Client-side filtering/sorting of potentially thousands of tasks is unacceptable for scalability. Consider virtualization for Kanban columns if tasks per column grow large.

### 14. Testing Strategy
*   **Missing Consideration (Accessibility Tests):** No explicit mention of testing accessibility for DnD interactions or color contrast.
    *   **Actionable:** Add accessibility tests, particularly for keyboard navigation and screen reader announcements for DnD, and automated color contrast checks if possible.
*   **Missing Consideration (Error State Tests):** The test cases focus on happy paths.
    *   **Actionable:** Include tests for error scenarios: API failures (create, update, delete), DnD mutation errors, invalid form submissions, and malformed URL parameters.

### 15. Implementation Order
*   **No specific issues.** Logical and incremental.

### 16. Edge Cases & Decisions
*   **Footgun / Performance / Architectural Problem (Filter Bar Multi-Select Client):** "if not, fetch all tasks and filter client-side for the multi-client case (with a comment noting the limitation)." This is a **major footgun and critical scalability issue**. Filtering "all tasks" client-side is an anti-pattern for production applications with potentially large datasets.
    *   **Actionable:** This decision **must be changed**. If the backend `useGlobalTasks` hook (or underlying API) does not support multi-client filtering, then a backend change is required. If a backend change is out of scope for *this* split, then multi-client filtering should be deferred or implemented with a warning that it will only work for small datasets until backend support is added. This should *not* be a client-side filtering fallback of all tasks.
*   **Optimistic updates:** "For drag-and-drop, apply the status/order change to local state immediately... then revert on error. For modal saves, don't apply optimistically — wait for API success." This is a solid, well-reasoned decision.

---

## Additional Considerations

1.  **Authentication and Authorization:** Assume existing platform handles this, but all new API calls (create, edit, delete, status change) must be properly authorized for the agent role. Can any agent modify any task, or only tasks they are assigned to/own?
2.  **Rate Limiting:** Is the backend API protected by rate limiting? Frequent updates (e.g., from DnD optimistic updates if errors occur, or rapid filter changes) could be abused.
3.  **Error Boundaries:** Consider adding React Error Boundaries strategically to catch UI rendering errors within components and prevent the entire application from crashing.
4.  **Loading States & Skeletons:** Beyond optimistic updates, ensure clear loading states (spinners, skeletons) for initial data fetch and re-fetches to improve user experience.
5.  **Design System Consistency:** Ensure all new components (buttons, inputs, selects, modals, badges) adhere strictly to the existing Montrroase design system.
6.  **Forms Library:** For the `TaskModal`, if form validation and state management become complex, consider a library like React Hook Form or Formik for robustness and reduced boilerplate, especially with recurrence logic.

By addressing these points, the plan will be significantly more robust, scalable, and secure.
