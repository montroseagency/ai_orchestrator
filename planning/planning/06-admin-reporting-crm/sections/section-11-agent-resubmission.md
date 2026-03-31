# Section 11: Agent Re-submission Workflow

## Overview

This section implements the agent's side of the task approval workflow. When an admin rejects a task (section-05), the agent must be able to see the rejection feedback and re-submit the corrected task for review. Without this, `review_feedback` is read-only with no actionable path forward.

This section is purely additive — it adds one new backend action to an existing viewset and small UI additions to the existing task card/modal. No new pages are created.

**Dependencies:**
- **section-01-backend-migrations** must be complete — `review_feedback` field must exist on `AgentGlobalTask` and be included in `AgentGlobalTaskReadSerializer`.
- **section-02-notification-types** must be complete — `task_review_submitted` notification type and `notify_task_review_submitted` helper must exist.

---

## Files to Create

- `server/api/tests/test_agent_resubmission.py` — backend tests (write first)
- `client/components/management/tasks/__tests__/RejectionFeedbackPanel.test.tsx` — frontend tests (write first)
- `client/components/management/tasks/RejectionFeedbackPanel.tsx` — new UI component

## Files to Modify

- `server/api/views/agent/scheduling_views.py` — add `resubmit` action to `AgentGlobalTaskViewSet`
- `server/api/urls.py` — no change needed (router already registers the viewset with all actions)
- `client/lib/types/scheduling.ts` — add `review_feedback` field to `AgentGlobalTask` interface
- `client/lib/hooks/useScheduling.ts` — add `useResubmitTask` mutation hook
- `client/components/management/tasks/TaskModal.tsx` — render `RejectionFeedbackPanel` when task has feedback

---

## Tests First

### Backend Tests (`server/api/tests/test_agent_resubmission.py`)

Write these tests before implementing the `resubmit` action. Use the same `APITestCase`/`pytest-django` pattern as existing tests in `server/api/tests.py`. Create a test agent, task, and client using model factories or direct model creation.

```python
class AgentResubmissionTests(APITestCase):

    def test_resubmit_transitions_in_progress_to_in_review(self):
        """resubmit/ on an in_progress task sets status to in_review."""

    def test_resubmit_clears_review_feedback(self):
        """resubmit/ clears the review_feedback field (sets to empty string)."""

    def test_resubmit_returns_400_if_task_not_in_progress(self):
        """resubmit/ on a task with status other than in_progress returns HTTP 400."""

    def test_resubmit_returns_403_if_agent_does_not_own_task(self):
        """resubmit/ by a different agent returns HTTP 403."""

    def test_resubmit_triggers_task_review_submitted_notification(self):
        """resubmit/ calls notify_task_review_submitted with the task."""
        # Mock NotificationService and assert it was called with the task.
```

### Frontend Tests (`client/components/management/tasks/__tests__/RejectionFeedbackPanel.test.tsx`)

Use the same test pattern as `TaskCard.test.tsx` — import `render`, `screen`, `fireEvent` from `@testing-library/react`. Mock `useResubmitTask` from `@/lib/hooks/useScheduling` and `sonner`.

The `baseTask` in these tests needs `review_feedback` on the type — add it to the import. A rejected task has `status: 'in_progress'` and a non-empty `review_feedback`. A normal in-progress task has `review_feedback: ''`.

```typescript
describe('RejectionFeedbackPanel', () => {

  it('renders when task has review_feedback and status is in_progress', () => {
    // Panel with "Returned:" prefix and the feedback text should be visible.
  });

  it('does NOT render when review_feedback is empty', () => {
    // Component should return null.
  });

  it('does NOT render when status is not in_progress (e.g. in_review)', () => {
    // Even if review_feedback is set, do not show panel once re-submitted.
  });

  it('renders feedback text inside the panel', () => {
    // The exact feedback string from review_feedback should appear.
  });

  it('"Re-submit for Review" button calls resubmit mutation with task id', () => {
    // fireEvent.click the button, assert mutateAsync was called with task.id
  });

  it('on successful resubmit, panel hides (status optimistically changes to in_review)', () => {
    // After mutation resolves, component should no longer be visible.
  });

});
```

**Test for TaskModal integration** — add to the existing `TaskModal.test.tsx` describe block:

```typescript
it('shows RejectionFeedbackPanel when editing a task with non-empty review_feedback and in_progress status', () => {
  // Render TaskModal with a task where status='in_progress' and review_feedback='Please fix the copy'.
  // Assert the panel text "Please fix the copy" is visible.
});

it('does NOT show RejectionFeedbackPanel when review_feedback is empty', () => {
  // Standard editing task (no rejection) should not show the panel.
});
```

---

## Backend Implementation

### `resubmit` Action on `AgentGlobalTaskViewSet`

**File:** `server/api/views/agent/scheduling_views.py`

Add a new `@action` to `AgentGlobalTaskViewSet` following the same structure as the existing `complete` action (line ~232). The action must:

1. Look up the task scoped to the requesting agent (`agent=_get_agent(request)`) to enforce ownership — return 403 if not found.
2. Check `task.status == 'in_progress'` — return 400 if not.
3. Inside `transaction.atomic()` with `select_for_update()`: set `status = 'in_review'` and `review_feedback = ''`.
4. After the transaction: call `notify_task_review_submitted(task)` (from section-02's `NotificationService`).
5. Return `AgentGlobalTaskReadSerializer(task).data` with HTTP 200.

```python
@action(detail=True, methods=['post'], url_path='resubmit')
def resubmit(self, request, pk=None):
    """Re-submit a rejected task for admin review.

    Validates that the requesting agent owns the task and that its
    current status is 'in_progress' (i.e., it was previously rejected).
    Transitions status to 'in_review' and clears review_feedback.
    Dispatches task_review_submitted notification to admin users.

    Returns:
        200 with updated task data on success.
        400 if task status is not 'in_progress'.
        403 if agent does not own the task.
    """
```

**`get_queryset` update:** The existing `get_queryset` already bypasses agent filtering for the `complete` action. Add `resubmit` to the same bypass condition so that `select_for_update` lookups within the action are not accidentally double-filtered:

```python
def get_queryset(self):
    if self.action in ('complete', 'resubmit'):
        return AgentGlobalTask.objects.all()
    ...
```

**`get_permissions` update:** The `complete` action already loosens permissions to `[IsAuthenticated()]`. Add `resubmit` to the same condition so agents (who are not `IsAnyAgent` role in all setups) can call it:

```python
def get_permissions(self):
    if self.action in ('complete', 'resubmit'):
        return [IsAuthenticated()]
    return [IsAuthenticated(), IsAnyAgent()]
```

**Notification call:** Import `NotificationService` from `server/api/services/notification_service.py` (it is already imported in other views). Call `NotificationService.notify_task_review_submitted(task)` after the transaction commits.

---

## Frontend Implementation

### 1. Update `AgentGlobalTask` Type

**File:** `client/lib/types/scheduling.ts`

Add `review_feedback` to the `AgentGlobalTask` interface after the `updated_at` field:

```typescript
export interface AgentGlobalTask {
  // ... existing fields ...
  updated_at: string;
  review_feedback: string;   // empty string when no feedback; non-empty when admin rejected
}
```

Also update any `baseTask` mock objects in existing test files that spread `AgentGlobalTask` — add `review_feedback: ''` to satisfy TypeScript. The test files to check are:
- `client/app/dashboard/agent/marketing/management/tasks/__tests__/TaskCard.test.tsx`
- `client/app/dashboard/agent/marketing/management/tasks/__tests__/TaskModal.test.tsx`
- `client/app/dashboard/agent/marketing/management/tasks/__tests__/KanbanColumn.test.tsx`
- Any other test files that construct `AgentGlobalTask` literals

### 2. Add `useResubmitTask` Hook

**File:** `client/lib/hooks/useScheduling.ts`

Add a new React Query mutation hook following the same pattern as `useCompleteGlobalTask` in that file:

```typescript
export function useResubmitTask() {
  /**
   * Calls POST /agent/tasks/{taskId}/resubmit/.
   * On success, invalidates ['global-tasks'] query cache so the task's
   * status and cleared review_feedback are reflected everywhere.
   */
}
```

The API call should POST to `/agent/tasks/${taskId}/resubmit/` with no body. On success, call `queryClient.invalidateQueries({ queryKey: ['global-tasks'] })`.

### 3. Create `RejectionFeedbackPanel` Component

**File:** `client/components/management/tasks/RejectionFeedbackPanel.tsx`

A small, self-contained component that:
- Accepts `task: AgentGlobalTask` as its only prop.
- Returns `null` if `task.review_feedback` is empty or if `task.status !== 'in_progress'` (don't show if the task is already back in_review).
- Renders a highlighted panel (e.g., amber/warning color using Tailwind) showing:
  - A header: "Returned for Revision" (with an alert icon from `lucide-react`, e.g. `AlertTriangle`)
  - The feedback text: `{task.review_feedback}`
  - A "Re-submit for Review" button (use the existing `Button` component from `client/components/ui/button.tsx`)
- On button click: call `useResubmitTask().mutateAsync(task.id)`. Show a success toast (`sonner`) on resolve and an error toast on reject.

```typescript
interface RejectionFeedbackPanelProps {
  task: AgentGlobalTask;
}

export function RejectionFeedbackPanel({ task }: RejectionFeedbackPanelProps) {
  /**
   * Renders rejection feedback from admin and a re-submission button.
   * Returns null if task has no feedback or is not in 'in_progress' status.
   */
}
```

### 4. Integrate into `TaskModal`

**File:** `client/components/management/tasks/TaskModal.tsx`

When `TaskModal` is opened in edit mode (`task` prop is provided), render `<RejectionFeedbackPanel task={task} />` near the top of the modal content — before the form fields, so the agent sees the feedback prominently before making edits. No other changes to `TaskModal` are required.

Import `RejectionFeedbackPanel` at the top of the file alongside other imports.

---

## Behavior Summary

| Scenario | Expected behavior |
|---|---|
| Agent views a rejected task (status=`in_progress`, `review_feedback` non-empty) | Amber feedback panel shown in task modal with feedback text and "Re-submit" button |
| Agent views a normal in-progress task (`review_feedback` empty) | No panel shown — modal appears as before |
| Task is back `in_review` after re-submit | Panel hidden (status is no longer `in_progress`) |
| Agent clicks "Re-submit for Review" | POST to `/agent/tasks/{id}/resubmit/`, status → `in_review`, feedback cleared, cache invalidated |
| Non-owner agent tries to resubmit | Backend returns 403 |
| Task is not `in_progress` when resubmit POSTed | Backend returns 400 |

---

## Implementation Notes

- The `resubmit` action intentionally does NOT use the Kanban board drag-to-column mechanism — it is a deliberate re-submission, not a status drag. It bypasses any `should_intercept_for_review` check since the task is already being sent to review explicitly.
- Do not clear `review_feedback` on the frontend before the API call succeeds. Only invalidate the query cache on success — this ensures the UI reflects server state.
- The `RejectionFeedbackPanel` is intentionally read-only. The agent edits the task content via the standard `TaskModal` form fields; the panel is informational + action only.
- Reuse `lucide-react` icons already used in `TaskCard.tsx` (`AlertTriangle` or `MessageSquareWarning` for the feedback panel header). Do not add new icon libraries.
