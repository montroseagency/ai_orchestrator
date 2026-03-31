Now I have all the context I need. Let me generate the section content.

# Section 6: API Layer -- Serializers

## Overview

This section creates separate read and write serializers for `AgentGlobalTask`, a `TaskCategorySerializer`, and an `IsAdmin` permission class. It also specifies QuerySet optimization with `select_related` to prevent N+1 queries.

**Depends on:** Section 4 (migrations must be applied so the new model fields exist in the database).

**Blocks:** Section 5 (JIT recurrence uses the write serializer's `validate_status` method), Section 7 (ViewSets consume these serializers).

## File Paths

- **Modify:** `/home/ubuntu/Montrroase_website/server/api/serializers/agent_scheduling.py`
- **Modify:** `/home/ubuntu/Montrroase_website/server/api/views/agent/scheduling_views.py` (for the `IsAdmin` permission class, placed alongside `IsAnyAgent`)
- **Create:** `/home/ubuntu/Montrroase_website/server/api/tests/test_serializers.py` (tests)

## Background Context

### Current Serializer State

The existing `AgentGlobalTaskSerializer` in `server/api/serializers/agent_scheduling.py` is a single ModelSerializer used for both reads and writes. It includes:

- `is_overdue` as a `SerializerMethodField`
- `time_block_title` as a nested `CharField(source='time_block.title')`
- Auto-assignment of `agent` from `request.user.agent_profile` on create
- Manual `completed_at` timestamping in `update()`
- Fields reference the old `task_category` CharField and `recurring_source` FK

The file also contains `RecurringTaskTemplateSerializer` which will be removed in Section 7.

### Current Permission State

`IsAnyAgent` lives directly in `scheduling_views.py` (line 32), not in a separate permissions module. It checks `request.user.role == 'agent'` and `hasattr(request.user, 'agent_profile')`.

There are various `IsAdmin`/`IsAdminUser` classes scattered across other view files (e.g., `dashboard_views.py`, `invoice_views.py`, `analytics_views.py`) but none is shared. The scheduling module needs its own `IsAdmin` permission.

### User Model Role Field

The `User` model (in `server/api/models/users.py`) has `role = CharField(choices=[('admin', 'Admin'), ('client', 'Client'), ('agent', 'Agent')])`. The `IsAdmin` permission checks `request.user.role == 'admin'`.

### New Model Fields (from Sections 1-4)

After migrations are applied, `AgentGlobalTask` has these new fields:

- `client` -- nullable FK to `Client`
- `task_category_ref` -- nullable FK to `TaskCategory`
- `is_recurring`, `recurrence_frequency`, `recurrence_days`, `recurrence_interval`, `recurrence_end_type`, `recurrence_end_count`, `recurrence_end_date`, `recurrence_parent`, `recurrence_instance_number`

The `TaskCategory` model has: `id` (UUID), `name`, `slug` (auto-generated, read-only), `color`, `icon`, `department`, `requires_review`, `is_active`, `sort_order`, `created_by`, timestamps.

The status choices now include `IN_REVIEW = 'in_review'`.

---

## Tests (Write First)

Create tests at `/home/ubuntu/Montrroase_website/server/api/tests/test_serializers.py`. These tests verify serializer behavior and the `IsAdmin` permission class.

### Test Structure

```python
"""Tests for Section 6: Serializers and IsAdmin permission."""
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIRequestFactory
from api.models import AgentGlobalTask, TaskCategory, Client, User, Agent


class AgentGlobalTaskReadSerializerTest(TestCase):
    """Tests for the read serializer."""

    def setUp(self):
        """Create user, agent, client, category, and a task for testing."""
        # Create admin user, agent user, client, TaskCategory, and an AgentGlobalTask
        # with client and task_category_ref assigned.
        ...

    def test_includes_nested_task_category_detail(self):
        """Read serializer returns a full nested TaskCategory object under 'task_category_detail'."""
        ...

    def test_includes_computed_client_name(self):
        """Read serializer returns the client's company name as 'client_name'."""
        ...

    def test_includes_is_overdue_computed_field(self):
        """Read serializer computes is_overdue based on due_date and status."""
        ...

    def test_includes_all_recurrence_fields(self):
        """Read serializer includes is_recurring, recurrence_frequency, recurrence_days, etc."""
        ...


class AgentGlobalTaskWriteSerializerTest(TestCase):
    """Tests for the write serializer."""

    def setUp(self):
        """Create user, agent, category, client for validation tests."""
        ...

    def test_accepts_task_category_ref_as_uuid(self):
        """Write serializer accepts task_category_ref as a UUID primary key."""
        ...

    def test_accepts_client_as_uuid(self):
        """Write serializer accepts client as a UUID primary key."""
        ...

    def test_validate_status_intercepts_done_for_review_category(self):
        """When task is in a requires_review category, setting status to 'done'
        from 'in_progress' should redirect to 'in_review'."""
        ...

    def test_validate_status_allows_done_from_in_review(self):
        """When task is in a requires_review category, setting status to 'done'
        from 'in_review' should be allowed (admin approval flow)."""
        ...

    def test_validate_recurrence_consistency(self):
        """When is_recurring=True, recurrence_frequency must be provided."""
        ...

    def test_invalid_uuid_for_category_returns_400(self):
        """A non-existent UUID for task_category_ref returns a validation error."""
        ...

    def test_invalid_uuid_for_client_returns_400(self):
        """A non-existent UUID for client returns a validation error."""
        ...


class TaskCategorySerializerTest(TestCase):
    """Tests for TaskCategorySerializer."""

    def test_serializes_all_fields(self):
        """All model fields are present in serialized output."""
        ...

    def test_slug_is_read_only(self):
        """Providing a slug value in input data does not override auto-generation."""
        ...


class IsAdminPermissionTest(TestCase):
    """Tests for the IsAdmin permission class."""

    def test_admin_user_allowed(self):
        """User with role='admin' passes the permission check."""
        ...

    def test_agent_user_denied(self):
        """User with role='agent' is rejected."""
        ...

    def test_client_user_denied(self):
        """User with role='client' is rejected."""
        ...

    def test_unauthenticated_denied(self):
        """Anonymous user is rejected."""
        ...
```

### Key Test Details

For the `validate_status` interception test: create a task with a `TaskCategory` that has `requires_review=True`. Set the task's current status to `in_progress`. Pass `status='done'` through the write serializer. The serializer should change the validated status to `in_review` instead.

For the recurrence consistency test: pass `is_recurring=True` without `recurrence_frequency` and assert a `ValidationError` is raised.

For the `IsAdmin` permission tests: use DRF's `APIRequestFactory` to create mock requests, set `request.user` to users with different roles, and call `has_permission()` directly.

---

## Implementation Details

### 1. IsAdmin Permission Class

Add the `IsAdmin` class in `/home/ubuntu/Montrroase_website/server/api/views/agent/scheduling_views.py`, directly below the existing `IsAnyAgent` class (line 37). This keeps both scheduling-related permission classes co-located.

```python
class IsAdmin(BasePermission):
    """Permission class that allows only admin users."""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == 'admin'
        )
```

This mirrors the pattern already used in `IsAnyAgent` but checks for `role == 'admin'` instead.

### 2. TaskCategorySerializer

Add to `/home/ubuntu/Montrroase_website/server/api/serializers/agent_scheduling.py`, before the Global Task serializers.

- Standard `ModelSerializer` for the `TaskCategory` model.
- Include all fields: `id`, `name`, `slug`, `color`, `icon`, `department`, `requires_review`, `is_active`, `sort_order`, `created_by`, `created_at`, `updated_at`.
- Mark `slug` as `read_only` (it is auto-generated from `name` on model save).
- Mark `id`, `created_at`, `updated_at` as `read_only`.

### 3. AgentGlobalTaskReadSerializer

Replace the existing `AgentGlobalTaskSerializer` usage for GET responses. Keep the old class temporarily (Section 7 handles the switchover in ViewSets), or rename it.

Fields to include (all read-only in practice since this is the read serializer):

- All existing fields from the current serializer: `id`, `agent`, `title`, `description`, `status`, `priority`, `due_date`, `scheduled_date`, `start_time`, `end_time`, `time_block`, `time_block_title`, `estimated_minutes`, `is_overdue`, `order`, `completed_at`, `created_at`, `updated_at`
- **New fields:**
  - `client` -- FK ID (UUID)
  - `client_name` -- `SerializerMethodField` or `CharField(source='client.company', read_only=True, default='')` to display the client's company name
  - `task_category_ref` -- FK ID (UUID)
  - `task_category_detail` -- nested `TaskCategorySerializer(source='task_category_ref', read_only=True)` providing the full category object
  - All recurrence fields: `is_recurring`, `recurrence_frequency`, `recurrence_days`, `recurrence_interval`, `recurrence_end_type`, `recurrence_end_count`, `recurrence_end_date`, `recurrence_parent`, `recurrence_instance_number`

The `is_overdue` method field should use the same logic as the existing serializer (check `due_date < today` and `status != 'done'`), but also consider `in_review` as not-done.

The `time_block_title` remains as `CharField(source='time_block.title', read_only=True, default='')`.

### 4. AgentGlobalTaskWriteSerializer

Used for POST and PATCH requests. This serializer handles validation and creation/update logic.

Fields (writable):

- `title`, `description`, `status`, `priority`, `due_date`, `scheduled_date`, `start_time`, `end_time`, `time_block`, `estimated_minutes`, `order`
- `client` -- accepts UUID (FK PK)
- `task_category_ref` -- accepts UUID (FK PK)
- All recurrence fields: `is_recurring`, `recurrence_frequency`, `recurrence_days`, `recurrence_interval`, `recurrence_end_type`, `recurrence_end_count`, `recurrence_end_date`, `recurrence_parent`, `recurrence_instance_number`

Read-only fields: `id`, `agent`, `completed_at`, `created_at`, `updated_at`

#### validate_status Method

This is the review-required interception logic, critical for Section 5 (JIT recurrence):

```python
def validate_status(self, value):
    """Intercept 'done' status for tasks in requires_review categories.

    If the task's category has requires_review=True and the current status
    is NOT 'in_review', redirect 'done' to 'in_review' instead.
    If current status IS 'in_review', allow 'done' (admin approval).
    """
    ...
```

The method needs access to the instance (for current status) via `self.instance`. On creation (no instance), no interception is needed. The category is read from `self.instance.task_category_ref`.

#### validate Method (Cross-Field)

```python
def validate(self, attrs):
    """Cross-field validation for recurrence consistency.

    When is_recurring=True, recurrence_frequency must be provided.
    """
    ...
```

Check: if `attrs.get('is_recurring')` is `True` (or, on partial update, if the instance already has `is_recurring=True` and frequency is being cleared), require `recurrence_frequency` to be non-null.

#### create Method

Same pattern as existing serializer -- assign `agent` from `request.user.agent_profile`.

#### update Method

Same `completed_at` timestamping logic as the existing serializer:

- If new status is `done` and old status was not `done`, set `completed_at = now()`
- If new status is not `done`, clear `completed_at = None`
- Also handle `in_review` -- `in_review` should NOT set `completed_at` (task is not yet complete)

### 5. Update Imports

Add `TaskCategory` to the model imports at the top of the serializers file:

```python
from api.models import (
    AgentTimeBlock, AgentGlobalTask, ScheduledTaskLink, WeeklyPlan,
    AgentRecurringBlock, RecurringTaskTemplate,
    MarketingTask, ProjectTask,
    TaskCategory,
)
```

### 6. QuerySet Optimization Note

The ViewSet (implemented in Section 7) must call `select_related('client', 'task_category_ref', 'time_block')` on the queryset to avoid N+1 queries when the read serializer accesses `client.company`, `task_category_ref.*`, and `time_block.title`. This is documented here for context but implemented in Section 7's `get_queryset()`.

### 7. Keep Existing Serializers

Do NOT remove `AgentGlobalTaskSerializer`, `RecurringTaskTemplateSerializer`, `ScheduledTaskLinkSerializer`, or `CrossClientTaskSerializer` in this section. They are still referenced by existing views. Section 7 handles the switchover and removal of deprecated serializers.

The `ScheduledTaskLinkSerializer` will need updates in Section 7 to remove GenericFK fields (`content_type`, `object_id`, `content_type_model`) and use the direct `task` FK instead.

---

## Implementation Checklist

1. Write tests in `/home/ubuntu/Montrroase_website/server/api/tests/test_serializers.py`
2. Add `IsAdmin` permission class to `scheduling_views.py` (below `IsAnyAgent`)
3. Add `TaskCategorySerializer` to `agent_scheduling.py` serializers
4. Add `AgentGlobalTaskReadSerializer` to `agent_scheduling.py` serializers
5. Add `AgentGlobalTaskWriteSerializer` to `agent_scheduling.py` serializers (with `validate_status` and `validate` methods)
6. Update imports in the serializers file to include `TaskCategory`
7. Run tests: `cd /home/ubuntu/Montrroase_website/server && python manage.py test api.tests.test_serializers`