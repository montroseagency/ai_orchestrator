# Section 02: Notification Types

## Overview

Add three new notification type choices that support the task approval workflow. These types must be registered in two places: the Django `Notification` model (for persistence) and the Node.js notification-realtime service enum (for WebSocket delivery and TypeScript type safety). This section has no dependencies and can be implemented in parallel with `section-01-backend-migrations`.

**Sections that depend on this one:** `section-05-approval-queue-api`, `section-11-agent-resubmission`

---

## Files to Modify

| File | Change |
|---|---|
| `server/api/models/notifications.py` | Add 3 new tuples to `NOTIFICATION_TYPES` |
| `server/api/services/notification_service.py` | Add 3 new helper static methods to `NotificationService` |
| `services/notification-realtime/src/types/index.ts` | Add 3 new entries to `NotificationType` enum |

---

## Tests First

Tests live in `server/api/tests/` (Django pytest) and should be written before implementation.

### Backend Tests (pytest-django)

```python
# server/api/tests/test_notification_types.py

def test_notification_types_includes_task_review_submitted():
    """NOTIFICATION_TYPES must contain the 'task_review_submitted' choice."""

def test_notification_types_includes_task_approved():
    """NOTIFICATION_TYPES must contain the 'task_approved' choice."""

def test_notification_types_includes_task_rejected():
    """NOTIFICATION_TYPES must contain the 'task_rejected' choice."""

def test_notify_task_review_submitted_creates_notification_for_admin(db):
    """Calling notify_task_review_submitted(task) must call create_notification
    for each admin user with notification_type='task_review_submitted'."""

def test_notify_task_approved_creates_notification_for_agent(db):
    """Calling notify_task_approved(task, admin_name) must call create_notification
    for the task's agent user with notification_type='task_approved'."""

def test_notify_task_rejected_creates_notification_for_agent(db):
    """Calling notify_task_rejected(task, admin_name, feedback) must call
    create_notification for the task's agent user with notification_type='task_rejected'
    and include the feedback text in the message."""
```

The tests should mock `NotificationService.create_notification` (or `publish_notification_event`) to avoid needing a live RabbitMQ connection. Verify that:

- The correct `notification_type` string is passed.
- The correct `user` is targeted (admin users for `task_review_submitted`; the task's `agent.user` for `task_approved` and `task_rejected`).
- The notification `message` for rejection includes the `feedback` argument.

---

## Implementation

### 1. Django — `server/api/models/notifications.py`

The `NOTIFICATION_TYPES` list currently ends with `('general', 'General')`. Add the three new tuples inside the `# Task notifications` block (or as a new `# Task approval notifications` sub-section comment) before the general tuple. The string values must match exactly what the helper functions and Node.js enum use.

```python
# Add within the NOTIFICATION_TYPES list:
('task_review_submitted', 'Task Submitted for Review'),
('task_approved', 'Task Approved'),
('task_rejected', 'Task Rejected'),
```

No migration is needed — `NOTIFICATION_TYPES` is a Python-level choices list on a `CharField(max_length=30)`. The three new type strings fit within the existing `max_length=30` constraint (longest is `task_review_submitted` at 22 characters).

### 2. Django — `server/api/services/notification_service.py`

Add three new static methods to the existing `NotificationService` class. Follow the exact same pattern as existing methods like `notify_content_approved` and `notify_content_rejected`.

```python
@staticmethod
def notify_task_review_submitted(task):
    """Send notification to all admin users when an agent submits a task for review.

    Args:
        task: AgentGlobalTask instance. Uses task.title and task.agent.user.get_full_name()
              (or email) to build the message. Link points to /dashboard/admin/approvals.
    """

@staticmethod
def notify_task_approved(task, approved_by_name: str):
    """Send notification to the task's agent when their task is approved.

    Args:
        task: AgentGlobalTask instance. The recipient is task.agent.user.
        approved_by_name: Display name of the admin who approved (for the message body).
        Link points to /dashboard/agent/tasks or equivalent.
    """

@staticmethod
def notify_task_rejected(task, rejected_by_name: str, feedback: str):
    """Send notification to the task's agent when their task is rejected.

    Args:
        task: AgentGlobalTask instance. The recipient is task.agent.user.
        rejected_by_name: Display name of the admin who rejected.
        feedback: The rejection feedback text. Must be included in the message body.
        Link points to /dashboard/agent/tasks or equivalent.
    """
```

Key implementation notes:
- `notify_task_review_submitted` queries `User.objects.filter(role='admin')` and calls `create_notification` for each, mirroring `notify_content_submitted`.
- `notify_task_approved` and `notify_task_rejected` target `task.agent.user` (a single user), mirroring `notify_content_approved`.
- The `notification_type` argument passed to `create_notification` must be the exact string: `'task_review_submitted'`, `'task_approved'`, or `'task_rejected'`.
- The `link` for agent-facing notifications should be `/dashboard/agent/tasks` (adjust if a more specific URL exists in the agent task routes).

### 3. Node.js — `services/notification-realtime/src/types/index.ts`

The `NotificationType` enum currently has task-related entries at the top (`TASK_ASSIGNED`, `TASK_COMPLETED`, `TASK_OVERDUE`) followed by payment, social, content, etc. Add the three new approval-workflow entries to the task block:

```typescript
// Add within the // Task notifications block:
TASK_REVIEW_SUBMITTED = 'task_review_submitted',
TASK_APPROVED = 'task_approved',
TASK_REJECTED = 'task_rejected',
```

The string values (`'task_review_submitted'`, `'task_approved'`, `'task_rejected'`) must exactly match the Django `NOTIFICATION_TYPES` choices added above. The Node.js event consumer already handles arbitrary notification types by passing the `type` field through — adding to the enum is sufficient to achieve TypeScript type safety; no other Node.js files need to change.

---

## Acceptance Criteria

- [ ] `NOTIFICATION_TYPES` in `server/api/models/notifications.py` includes all three new tuples.
- [ ] `NotificationService` in `server/api/services/notification_service.py` has all three new static methods.
- [ ] `NotificationType` enum in `services/notification-realtime/src/types/index.ts` has all three new entries with matching string values.
- [ ] All three backend tests pass (with RabbitMQ mocked).
- [ ] TypeScript compiles without errors in the notification-realtime service (`tsc --noEmit` or equivalent).
