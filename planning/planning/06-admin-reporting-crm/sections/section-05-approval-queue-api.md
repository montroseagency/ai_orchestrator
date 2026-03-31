# Section 05: Admin Approval Queue API

## Overview

This section implements the backend API that allows admins to list all tasks pending review, approve them (setting status to `done`), or reject them (setting status back to `in_progress` with stored feedback). It also adds the three notification types needed by this workflow to both the Django model and the Node.js realtime service.

**Dependencies:**
- `section-01-backend-migrations` must be complete — the `review_feedback` field on `AgentGlobalTask` must exist before this section is implemented.
- `section-02-notification-types` must be complete — the three new notification type strings must be registered before the helper functions can be tested.

**Blocks:** `section-09-admin-approvals-page` (frontend approval page depends on these endpoints).

---

## Files to Create / Modify

| Action | Path |
|--------|------|
| **Created** | `server/api/views/admin/approval_views.py` (actual path — not `server/api/admin/`) |
| **Modified** | `server/api/models/notifications.py` — added 3 notification type tuples (done in section-02) |
| **Modified** | `server/api/services/notification_service.py` — added 3 helper methods (done in section-02) |
| **Modified** | `services/notification-realtime/src/types/index.ts` — added 3 entries (done in section-02) |
| **Modified** | `server/api/urls.py` — registered 3 approval endpoints under `admin/` prefix |
| **Modified** | `server/api/tests.py` — added `ApprovalQueueAPITests` (14 tests) and `NotificationTypesApprovalTests` (6 tests) |

---

## Part A: Notification Types

### Background

The `Notification` model at `server/api/models/notifications.py` stores notifications via a `notification_type` CharField constrained to a `NOTIFICATION_TYPES` list of tuples. Three new types are needed for the approval workflow. They must be added here before any notification helper that references them can be tested.

The Node.js service at `services/notification-realtime/src/types/index.ts` exports a `NotificationType` enum. The event consumer already handles arbitrary type strings at runtime; adding entries to this enum is purely for TypeScript type safety.

### Django — `server/api/models/notifications.py`

In the `NOTIFICATION_TYPES` list, add the following three tuples in the `# Task notifications` group (or in a new `# Task review notifications` group):

```python
('task_review_submitted', 'Task Submitted for Review'),
('task_approved', 'Task Approved'),
('task_rejected', 'Task Rejected'),
```

The `notification_type` field has `max_length=30`; all three new strings are within that limit.

### Node.js — `services/notification-realtime/src/types/index.ts`

In the `NotificationType` enum, add three entries in the `// Task notifications` group:

```typescript
TASK_REVIEW_SUBMITTED = 'task_review_submitted',
TASK_APPROVED = 'task_approved',
TASK_REJECTED = 'task_rejected',
```

### Notification Helper Functions — `server/api/services/notification_service.py`

Add three static methods to the existing `NotificationService` class. Follow the same pattern as the existing `notify_content_submitted`, `notify_content_approved`, and `notify_content_rejected` methods.

```python
@staticmethod
def notify_task_review_submitted(task):
    """Send notification to all admin users when an agent submits a task for review.

    Fetches all users with role='admin' and calls create_notification for each.
    Notification type: 'task_review_submitted'.
    Link: '/dashboard/admin/approvals'
    Message includes: task.title, task.agent.user.get_full_name() or username.
    """

@staticmethod
def notify_task_approved(task, approved_by_name: str):
    """Send notification to the task's agent user when their task is approved.

    Recipient: task.agent.user
    Notification type: 'task_approved'.
    Link: '/dashboard/agent/tasks' (or equivalent agent task list route)
    Message includes: task.title, approved_by_name.
    """

@staticmethod
def notify_task_rejected(task, rejected_by_name: str, feedback: str):
    """Send notification to the task's agent user when their task is rejected.

    Recipient: task.agent.user
    Notification type: 'task_rejected'.
    Link: '/dashboard/agent/tasks'
    Message includes: task.title, rejected_by_name, feedback (truncated to 100 chars).
    """
```

Each helper calls `NotificationService.create_notification(...)` which publishes to RabbitMQ via `publish_notification_event`. No direct database writes happen in these helpers — persistence is handled by the notification-realtime Node.js service consuming the RabbitMQ event.

---

## Part B: Approval Queue Views

### Background

Admins need to list all `AgentGlobalTask` records with `status='in_review'` and take approve or reject actions. The key safety requirement is that two admins acting on the same task simultaneously must not corrupt state. This is solved with `select_for_update()` inside `transaction.atomic()` — the database row is locked for the duration of the status update, and the view returns HTTP 409 if the task has already left `in_review` status by the time the lock is acquired.

`IsAdminUser` permission class already exists in `server/api/views/admin/invoice_views.py` (and duplicated across other admin view files). Copy the same pattern: check `request.user.is_authenticated and request.user.role == 'admin'`.

### New File: `server/api/admin/approval_views.py`

This file needs the following structure:

```python
# server/api/admin/approval_views.py

import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import permissions
from django.db import transaction

from ..models.agent_scheduling import AgentGlobalTask
from ..serializers import AgentGlobalTaskReadSerializer  # or a dedicated ApprovalTaskSerializer
from ..services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class IsAdminUser(permissions.BasePermission):
    """Allow access only to users with role='admin'."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'


def approve_task(task_id, admin_user):
    """Approve a task in review. Raises ValueError if task is not in_review.

    Uses select_for_update() inside transaction.atomic() to prevent race conditions.
    Sets: status='done', review_feedback=''
    Dispatches: task_approved notification to task.agent.user (after transaction commits).
    Returns the updated task instance.
    """


def reject_task(task_id, admin_user, feedback: str):
    """Reject a task in review with required feedback. Raises ValueError if task is not
    in_review or if feedback is empty/blank.

    Uses select_for_update() inside transaction.atomic() to prevent race conditions.
    Sets: status='in_progress', review_feedback=feedback
    Dispatches: task_rejected notification to task.agent.user (after transaction commits).
    Returns the updated task instance.
    """


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def list_approvals(request):
    """GET /admin/approvals/

    Returns all AgentGlobalTask records with status='in_review', ordered by updated_at ASC.
    Uses select_related('agent__user', 'client', 'task_category_ref') to avoid N+1 queries.
    Serializes with AgentGlobalTaskReadSerializer (or ApprovalTaskSerializer).
    """


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def approve_task_view(request, task_id):
    """POST /admin/approvals/{task_id}/approve/

    Calls approve_task(). On ValueError (task not in_review) returns 409.
    On task not found returns 404. On success returns 200 with updated task data.
    """


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def reject_task_view(request, task_id):
    """POST /admin/approvals/{task_id}/reject/

    Body: { feedback: string } — required, non-empty.
    Validates feedback before calling reject_task().
    On missing/blank feedback returns 400 with error message.
    On ValueError (task not in_review) returns 409.
    On task not found returns 404. On success returns 200 with updated task data.
    """
```

#### Implementation Notes for `approve_task` and `reject_task`

Both functions follow this structure:

```python
with transaction.atomic():
    try:
        task = AgentGlobalTask.objects.select_for_update().get(id=task_id)
    except AgentGlobalTask.DoesNotExist:
        raise  # let the view catch and return 404

    if task.status != AgentGlobalTask.Status.IN_REVIEW:
        raise ValueError(f"Task {task_id} is not in_review (current: {task.status})")

    # ... mutate fields ...
    task.save(update_fields=[...])

# Notifications happen OUTSIDE the transaction (after commit)
NotificationService.notify_task_approved(task, admin_user.get_full_name() or admin_user.username)
```

Dispatching notifications outside the `with transaction.atomic():` block ensures the row is committed to the database before RabbitMQ receives the event, preventing a race where the frontend tries to fetch the updated task before the DB write lands.

#### Serializer Consideration

The list endpoint needs `agent.user.first_name + last_name`, `client.name`, `client.company`, `task.description`, and `task.review_feedback`. The existing `AgentGlobalTaskReadSerializer` (at `server/api/serializers/`) may not include nested agent/client names. Either:

1. Annotate the queryset with `agent_name` and `client_company` using `values()` or annotations, and return a plain dict response, **or**
2. Create a minimal `ApprovalTaskSerializer` in the same file that uses `SerializerMethodField` for the nested names.

Option 2 is cleaner. The serializer only needs to be used by this file, so defining it locally is acceptable.

```python
class ApprovalTaskSerializer(serializers.ModelSerializer):
    """Read serializer for the admin approval queue. Includes nested agent and client info."""
    agent_name = serializers.SerializerMethodField()
    client_name = serializers.SerializerMethodField()
    client_company = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()

    class Meta:
        model = AgentGlobalTask
        fields = [
            'id', 'title', 'description', 'status', 'priority',
            'review_feedback', 'updated_at', 'created_at',
            'agent_name', 'client_name', 'client_company', 'category_name',
        ]

    def get_agent_name(self, obj): ...
    def get_client_name(self, obj): ...
    def get_client_company(self, obj): ...
    def get_category_name(self, obj): ...
```

### URL Registration — `server/api/urls.py`

Register the three approval endpoints under the `admin/` URL prefix. The pattern follows how other admin function-based views are registered in this file (e.g., `admin_bank_settings`, `get_pending_verifications`, `approve_payment_verification`):

```python
from .admin.approval_views import list_approvals, approve_task_view, reject_task_view

# In urlpatterns:
path('admin/approvals/', list_approvals, name='admin-approvals-list'),
path('admin/approvals/<uuid:task_id>/approve/', approve_task_view, name='admin-approvals-approve'),
path('admin/approvals/<uuid:task_id>/reject/', reject_task_view, name='admin-approvals-reject'),
```

Note: `AgentGlobalTask.id` is a `UUIDField`, so use `<uuid:task_id>` in the URL pattern, not `<int:task_id>`.

---

## Tests

Test file: `server/api/tests.py` (extend the existing file, or create a new class block).

Use `APITestCase` from `rest_framework.test`. Create helper methods in `setUp` to build an admin user (`role='admin'`), an agent user with an `Agent` profile, and a `Client`. Create `AgentGlobalTask` instances in test methods as needed.

### Test Stubs

```python
class ApprovalQueueAPITests(APITestCase):

    def setUp(self):
        """Create admin user, agent user with Agent profile, client, and a sample in_review task."""

    def test_list_returns_only_in_review_tasks(self):
        """GET /admin/approvals/ returns only tasks with status='in_review'.
        Tasks with status='todo', 'in_progress', 'done' must NOT appear."""

    def test_list_ordered_by_updated_at_asc(self):
        """GET /admin/approvals/ tasks are ordered oldest-first (updated_at ASC)."""

    def test_list_includes_agent_client_names(self):
        """Response includes agent_name, client_name, client_company fields."""

    def test_list_returns_403_for_non_admin(self):
        """GET /admin/approvals/ returns 403 when called by an agent or client user."""

    def test_approve_sets_status_done_clears_feedback(self):
        """POST /admin/approvals/{id}/approve/ sets status='done' and review_feedback=''."""

    def test_approve_returns_404_for_nonexistent_task(self):
        """POST /admin/approvals/{nonexistent_id}/approve/ returns 404."""

    def test_approve_returns_409_when_task_not_in_review(self):
        """POST approve on a task with status='done' (already processed) returns 409."""

    def test_approve_returns_403_for_non_admin(self):
        """POST /admin/approvals/{id}/approve/ returns 403 for non-admin users."""

    def test_reject_sets_status_in_progress_stores_feedback(self):
        """POST /admin/approvals/{id}/reject/ with feedback sets status='in_progress'
        and saves feedback to review_feedback field."""

    def test_reject_returns_400_when_feedback_empty(self):
        """POST reject with empty string or missing feedback field returns 400."""

    def test_reject_returns_409_when_task_not_in_review(self):
        """POST reject on a task with status='in_progress' (already rejected) returns 409."""

    def test_reject_returns_403_for_non_admin(self):
        """POST /admin/approvals/{id}/reject/ returns 403 for non-admin users."""

    def test_approve_dispatches_notification(self):
        """Approve action calls NotificationService.notify_task_approved.
        Mock NotificationService.create_notification (or the underlying
        publish_notification_event) and assert it is called once with the
        correct notification_type='task_approved'."""

    def test_reject_dispatches_notification(self):
        """Reject action calls NotificationService.notify_task_rejected.
        Assert called with notification_type='task_rejected'."""
```

### Test for Notification Types

Add these as a separate class or inline:

```python
class NotificationTypesTests(TestCase):

    def test_notification_types_includes_task_review_submitted(self):
        """NOTIFICATION_TYPES list contains ('task_review_submitted', ...) tuple."""

    def test_notification_types_includes_task_approved(self):
        """NOTIFICATION_TYPES list contains ('task_approved', ...) tuple."""

    def test_notification_types_includes_task_rejected(self):
        """NOTIFICATION_TYPES list contains ('task_rejected', ...) tuple."""

    def test_notify_task_review_submitted_creates_notification_for_admins(self):
        """notify_task_review_submitted(task) calls create_notification for each
        admin user. Use unittest.mock.patch on publish_notification_event."""

    def test_notify_task_approved_creates_notification_for_agent(self):
        """notify_task_approved(task, 'Admin Name') calls create_notification for
        task.agent.user with type='task_approved'."""

    def test_notify_task_rejected_creates_notification_for_agent(self):
        """notify_task_rejected(task, 'Admin Name', 'feedback text') calls
        create_notification for task.agent.user with type='task_rejected'."""
```

---

## Implementation Notes (Actual)

- **File location:** Views landed at `server/api/views/admin/approval_views.py` (existing views directory), not the planned `server/api/admin/` path. Import in urls.py: `from .views.admin.approval_views import ...`
- **Race condition fix:** `select_for_update(of=('self',)).select_related('agent__user', 'client')` — the `of=('self',)` is required to avoid PostgreSQL `FOR UPDATE cannot be applied to nullable outer join` error when combining with `select_related`.
- **Blank feedback validation:** Only at view layer in `reject_task_view`. `reject_task()` service function only raises `ValueError` for state conflicts, keeping semantics clean.
- **Pagination:** `LimitOffsetPagination` added to `list_approvals`. List tests access `response.data['results']`.
- **Tests:** 20 total (14 `ApprovalQueueAPITests` + 6 `NotificationTypesApprovalTests`). All pass.
