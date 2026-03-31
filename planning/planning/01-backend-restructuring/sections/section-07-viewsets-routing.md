# Section 7: ViewSets and Routing

## Overview

This section modifies `AgentGlobalTaskViewSet` to add new filters, a `/complete/` action, and serializer switching. It creates a new `TaskCategoryViewSet` (with separate agent and admin endpoints), updates the function-based views (`command_center`, `cross_client_tasks`) to work with the new model fields and direct FK on `ScheduledTaskLink`, removes `RecurringTaskTemplateViewSet`, and updates URL routing in `server/api/urls.py`.

## Dependencies

- **Section 04 (Migrations):** Database schema must be applied (new fields on `AgentGlobalTask`, `TaskCategory` model, `ScheduledTaskLink` direct FK)
- **Section 05 (JIT Recurrence):** The `generate_next_recurring_instance` service function must exist for the `/complete/` action to call
- **Section 06 (Serializers):** `AgentGlobalTaskReadSerializer`, `AgentGlobalTaskWriteSerializer`, `TaskCategorySerializer`, and the `IsAdmin` permission class must be defined

## Files to Modify

- `/home/ubuntu/Montrroase_website/server/api/views/agent/scheduling_views.py` -- primary file; modify viewsets, helpers, FBVs
- `/home/ubuntu/Montrroase_website/server/api/urls.py` -- update imports and router registrations

## Tests

All tests go in `/home/ubuntu/Montrroase_website/server/api/tests/test_viewsets_routing.py` (or in the existing `tests.py` if a tests package has not been created yet). Use DRF's `APIClient` for authenticated requests. Each test class should create fixture data in `setUp`.

### AgentGlobalTaskViewSet Tests

```python
class AgentGlobalTaskViewSetTests(APITestCase):
    """Tests for the modified AgentGlobalTaskViewSet."""

    # Test: GET /agent/schedule/global-tasks/ returns list with new fields
    #   - Create a user+agent, create a task with client and task_category_ref
    #   - Assert response includes task_category_detail nested object and client_name

    # Test: GET with ?client={id} filters by client
    #   - Create tasks for two different clients, filter by one, assert only matching returned

    # Test: GET with ?task_category_id={id} filters by category
    #   - Create tasks with different categories, filter, assert correct results

    # Test: GET with ?is_recurring=true filters recurring tasks
    #   - Create one recurring and one non-recurring task, filter, assert only recurring returned

    # Test: POST /agent/schedule/global-tasks/ creates task with new fields
    #   - Post with client UUID, task_category_ref UUID, assert created correctly

    # Test: POST /agent/schedule/global-tasks/{id}/complete/ marks task done
    #   - Create a task with status in_progress, POST to complete, assert status becomes done

    # Test: POST /complete/ on recurring task returns both completed and new instance
    #   - Create a recurring task, complete it, assert response contains task and next_task

    # Test: POST /complete/ on requires_review category redirects to in_review
    #   - Create task in a requires_review category with status in_progress
    #   - POST to complete, assert status becomes in_review (not done)

    # Test: POST /complete/ by admin user (no agent_profile) works for reviewed tasks
    #   - Create admin user (role='admin'), create task with status in_review
    #   - POST to complete as admin, assert status becomes done

    # Test: ViewSet uses read serializer for GET, write serializer for POST/PATCH
    #   - Inspect response shapes: GET should include nested objects, POST should accept UUIDs

    # Test: QuerySet uses select_related for performance (no N+1)
    #   - Use assertNumQueries to verify select_related is effective
```

### TaskCategoryViewSet Tests

```python
class TaskCategoryViewSetTests(APITestCase):
    """Tests for agent-facing and admin-facing TaskCategory endpoints."""

    # Test: GET /agent/schedule/task-categories/ returns active categories filtered by agent department
    #   - Create marketing and website categories, log in as marketing agent
    #   - Assert only marketing + both categories returned, not website-only

    # Test: Marketing agent sees marketing + both categories
    # Test: Website agent sees website + both categories

    # Test: POST /admin/task-categories/ creates category (admin only)
    #   - Log in as admin, POST category data, assert 201

    # Test: PATCH /admin/task-categories/{id}/ updates category (admin only)
    # Test: DELETE /admin/task-categories/{id}/ soft-deletes (sets is_active=False)
    #   - Note: implement DELETE as soft-delete by overriding destroy()

    # Test: Non-admin users get 403 on admin endpoints
    #   - Log in as agent, attempt POST to admin endpoint, assert 403
```

### Function-Based View Tests

```python
class FunctionBasedViewTests(APITestCase):
    """Tests for command_center and cross_client_tasks after updates."""

    # Test: command_center returns tasks with correct client data (not hardcoded empty)
    #   - Create a global task with a client FK set
    #   - Call command_center, verify the task's client_name and client_id are populated

    # Test: command_center uses updated serializer/helper with new fields
    #   - Verify task_category comes from task_category_ref, not old CharField

    # Test: cross_client_tasks works with direct FK ScheduledTaskLink (not GenericFK)
    #   - Create a ScheduledTaskLink with the new direct task FK
    #   - Call cross_client_tasks, verify linked tasks appear correctly

    # Test: cross_client_tasks returns tasks with task_category_ref data
```

### Routing Tests

```python
class RoutingTests(APITestCase):
    """Tests that URL routes resolve correctly."""

    # Test: /agent/schedule/task-categories/ resolves
    # Test: /admin/task-categories/ resolves
    # Test: /agent/schedule/recurring-tasks/ no longer resolves (removed)
    # Test: /agent/schedule/global-tasks/{id}/complete/ resolves
```

## Implementation Details

### 1. AgentGlobalTaskViewSet Modifications

**File:** `/home/ubuntu/Montrroase_website/server/api/views/agent/scheduling_views.py`

The existing `AgentGlobalTaskViewSet` (line 173) needs four changes:

**a) Serializer selection** -- Override `get_serializer_class()`:

```python
def get_serializer_class(self):
    """Return read serializer for safe methods, write serializer for mutations."""
    if self.action in ('list', 'retrieve'):
        return AgentGlobalTaskReadSerializer
    return AgentGlobalTaskWriteSerializer
```

**b) New query filters** -- Add `client`, `task_category_id`, and `is_recurring` filters to `get_queryset()`. The existing filters (`status`, `task_category` CharField, `scheduled_date`, `due_before`, `priority`) remain. Add:

- `client` query param: `qs = qs.filter(client_id=client_param)`
- `task_category_id` query param: `qs = qs.filter(task_category_ref_id=task_category_id_param)`
- `is_recurring` query param: `qs = qs.filter(is_recurring=is_recurring_param == 'true')`
- Remove or keep the old `task_category` CharField filter for backward compat (it can be removed since old field is dropped in migration D)

**c) QuerySet optimization** -- Add `select_related('client', 'task_category_ref', 'time_block')` to the base queryset in `get_queryset()`.

**d) The `/complete/` action** -- Add a new custom action:

```python
@action(detail=True, methods=['post'], url_path='complete')
def complete(self, request, pk=None):
    """Mark a task as done, handling review interception and JIT recurrence."""
    # ...
```

Key logic in the `complete` action:

1. Retrieve the task. If the caller is an agent (`request.user.role == 'agent'`), use `select_for_update()` to prevent race conditions. If the caller is an admin, also use `select_for_update()` but do not look up `agent_profile`.
2. Check if the task's category has `requires_review=True`:
   - If yes, and current status is NOT `in_review`: set status to `in_review`, save, return. Do NOT trigger JIT.
   - If yes, and current status IS `in_review`: this is an admin approval. Set status to `done`.
   - If no: set status to `done`.
3. Set `completed_at = timezone.now()`.
4. If the task `is_recurring` and status is now `done`, call the JIT service function `generate_next_recurring_instance(task)` (from section 05). Capture the returned new instance (or None).
5. Serialize the completed task with the read serializer. Include `next_task` in the response (serialized new instance, or null).

Important: The `complete` action must handle admin callers who do not have an `agent_profile`. Check `request.user.role` before calling `_get_agent(request)`. For admin users, do not filter the queryset by agent -- instead look up the task directly by PK (with appropriate permission checks).

The permission for the `complete` action should allow both agents and admins. You can achieve this by setting `permission_classes` on the action itself or by making the viewset-level permissions more flexible. One approach: keep `IsAuthenticated` at the viewset level, but override `get_permissions()` to allow `IsAdmin` for the `complete` action alongside `IsAnyAgent`.

### 2. TaskCategoryViewSet (Agent-Facing)

Create a new `TaskCategoryViewSet` in the same file or in a new dedicated file. It provides list-only access for agents, filtered by department:

```python
class AgentTaskCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Agent-facing: list active categories filtered by department."""
    permission_classes = [IsAuthenticated, IsAnyAgent]
    serializer_class = TaskCategorySerializer

    def get_queryset(self):
        agent = _get_agent(self.request)
        return TaskCategory.objects.filter(
            is_active=True
        ).filter(
            Q(department=agent.department) | Q(department='both')
        ).order_by('sort_order', 'name')
```

Register at `agent/schedule/task-categories/` in the router.

### 3. TaskCategoryViewSet (Admin-Facing)

Create a separate `AdminTaskCategoryViewSet` for full CRUD:

```python
class AdminTaskCategoryViewSet(viewsets.ModelViewSet):
    """Admin-facing: full CRUD for task categories."""
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = TaskCategorySerializer
    queryset = TaskCategory.objects.all().order_by('sort_order', 'name')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_destroy(self, instance):
        """Soft-delete: set is_active=False instead of removing."""
        instance.is_active = False
        instance.save(update_fields=['is_active'])
```

Register at `admin/task-categories/` in the router.

Note: `perform_destroy` implements soft-delete. The DELETE endpoint returns 204 but the record persists with `is_active=False`.

### 4. Function-Based View Updates

**`_serialize_global_task` helper (line 111):**

Update the function to read client data from the new FK instead of hardcoding empty values:

- Change `'client_name': ''` to `'client_name': task.client.company if task.client else ''`
- Change `'client_id': None` to `'client_id': str(task.client_id) if task.client_id else None`
- Change `'task_category': task.task_category or ''` to `'task_category': task.task_category_ref.name if task.task_category_ref else ''`

**`command_center` view (line 285):**

- Update the import/reference from `AgentGlobalTaskSerializer` to `AgentGlobalTaskReadSerializer` on line 377 where `todays_global_tasks` is serialized
- Add `select_related('client', 'task_category_ref')` to the `AgentGlobalTask` querysets (lines 302 and 336+) for performance
- The `ScheduledTaskLink` queries (line 319) that use `link.task` already work because the migration replaces the GenericFK with a real FK using the same attribute name `task`. Remove the `.select_related('content_type')` call since `content_type` no longer exists; replace with `.select_related('task')` or `.select_related('task__client')`

**`cross_client_tasks` view (line 395):**

- Update category filtering: change `client_qs.filter(task_category=category)` to use the new FK where applicable for global tasks: `global_qs.filter(task_category_ref__slug=category)` or `global_qs.filter(task_category_ref_id=category)` depending on what the frontend sends
- Add `select_related('client', 'task_category_ref')` to the `AgentGlobalTask` queryset
- The grouping by `'category'` key (line 452) should use the updated `task_category` field from the helper, which now reads from `task_category_ref`

### 5. RecurringTaskTemplateViewSet Removal

Remove the entire `RecurringTaskTemplateViewSet` class (lines 264-278 in the current file). Also remove:

- The import of `RecurringTaskTemplate` from `api.models` (line 17)
- The import of `RecurringTaskTemplateSerializer` from `api.serializers.agent_scheduling` (line 26)

### 6. URL Routing Updates

**File:** `/home/ubuntu/Montrroase_website/server/api/urls.py`

**Update the import block (line 159-164):**

Remove `RecurringTaskTemplateViewSet` from the import. Add the new viewsets:

```python
from .views.agent.scheduling_views import (
    AgentTimeBlockViewSet, AgentGlobalTaskViewSet,
    ScheduledTaskLinkViewSet, WeeklyPlanViewSet,
    AgentRecurringBlockViewSet,
    AgentTaskCategoryViewSet, AdminTaskCategoryViewSet,
    command_center, cross_client_tasks,
)
```

**Update router registrations (around line 352-357):**

Remove this line:
```python
router.register(r'agent/schedule/recurring-tasks', RecurringTaskTemplateViewSet, basename='recurring-task-template')
```

Add these lines:
```python
router.register(r'agent/schedule/task-categories', AgentTaskCategoryViewSet, basename='agent-task-category')
router.register(r'admin/task-categories', AdminTaskCategoryViewSet, basename='admin-task-category')
```

### 7. New Imports Needed in scheduling_views.py

Add at the top of the file:

```python
from api.serializers.agent_scheduling import (
    AgentTimeBlockSerializer, AgentTimeBlockBulkSerializer,
    AgentGlobalTaskReadSerializer, AgentGlobalTaskWriteSerializer,
    ScheduledTaskLinkSerializer,
    WeeklyPlanSerializer,
    AgentRecurringBlockSerializer,
    TaskCategorySerializer,
    CrossClientTaskSerializer,
    CommandCenterSerializer,
)
from api.models import TaskCategory
from api.permissions import IsAdmin  # wherever IsAdmin was defined in section 06
from django.db import transaction
from api.services.recurrence import generate_next_recurring_instance  # from section 05
```

Remove imports that are no longer needed:
- `RecurringTaskTemplate` from `api.models`
- `RecurringTaskTemplateSerializer` from the serializer imports
- `ContentType` from `django.contrib.contenttypes.models` (no longer needed since GenericFK is gone)

### 8. ScheduledTaskLinkViewSet Update

The existing `ScheduledTaskLinkViewSet` (line 206) uses `.select_related('content_type')`. Update this to `.select_related('task')` since the `content_type` field no longer exists after migration A replaced the GenericFK with a direct FK.

### 9. Permission Handling on AgentGlobalTaskViewSet

The viewset currently uses `permission_classes = [IsAuthenticated, IsAnyAgent]`. The `/complete/` action must also allow admin users. Two approaches:

**Option A (recommended):** Override `get_permissions()` on the viewset:

```python
def get_permissions(self):
    if self.action == 'complete':
        return [IsAuthenticated()]
    return [IsAuthenticated(), IsAnyAgent()]
```

This makes `complete` accessible to any authenticated user (agent or admin). The action itself checks `request.user.role` to determine behavior.

**Option B:** Create a combined permission class `IsAgentOrAdmin` that allows either role. This is more restrictive but reusable.

### 10. Complete Action Queryset Handling

When an admin calls `/complete/`, there is no `agent_profile`, so the viewset's `get_queryset()` (which calls `_get_agent(request)`) will fail. The `complete` action should override the queryset lookup:

```python
@action(detail=True, methods=['post'], url_path='complete')
def complete(self, request, pk=None):
    with transaction.atomic():
        if request.user.role == 'admin':
            task = AgentGlobalTask.objects.select_for_update().get(pk=pk)
        else:
            agent = _get_agent(request)
            task = AgentGlobalTask.objects.select_for_update().get(pk=pk, agent=agent)
        # ... rest of logic
```

Alternatively, override `get_object()` for this action. The direct lookup shown above is simpler and avoids the `get_queryset` path entirely for the complete action.

## Summary of Changes

| Change | File | Lines (approx.) |
|--------|------|-----------------|
| Modify `AgentGlobalTaskViewSet` (serializer switch, filters, select_related, complete action) | `scheduling_views.py` | 173-201 |
| Create `AgentTaskCategoryViewSet` | `scheduling_views.py` | new class |
| Create `AdminTaskCategoryViewSet` | `scheduling_views.py` | new class |
| Update `_serialize_global_task` | `scheduling_views.py` | 111-128 |
| Update `command_center` | `scheduling_views.py` | 285-388 |
| Update `cross_client_tasks` | `scheduling_views.py` | 395-458 |
| Update `ScheduledTaskLinkViewSet` | `scheduling_views.py` | 206-218 |
| Remove `RecurringTaskTemplateViewSet` | `scheduling_views.py` | 264-278 |
| Update imports | `scheduling_views.py` | 1-29 |
| Update imports and router registrations | `urls.py` | 159-164, 352-357 |

## Implementation Notes (Actual)

**Files modified:**
- `server/api/views/agent/scheduling_views.py` — all viewset/view changes
- `server/api/urls.py` — import + router registration updates
- `server/api/migrations/0070_task_restructure_schema.py` — fixed operation order (AlterUniqueTogether must come after AddField(task))
- `server/api/services/recurrence.py` — fixed datetime/date comparison bug (rrule.after() requires datetime, not date)
- `server/api/signals.py` — fixed NullPointerException when client.user is None

**Deviations from plan:**
- `IsAdmin` was already defined in `scheduling_views.py` — no import needed
- `select_for_update()` cannot be combined with `select_related` on nullable FKs in PostgreSQL; removed `select_related('task_category_ref')` from the locked query in `complete` action
- `get_queryset()` returns `AgentGlobalTask.objects.all()` for the `complete` action to bypass agent filtering (agent check is done in the action directly)
- Migration 0070 had incorrect operation ordering — split the single `AlterUniqueTogether` into two: clear old unique_together first, then set new after AddField

**Tests:** 16 new tests in `server/api/tests.py` (classes `AgentGlobalTaskViewSetSection07Test`, `TaskCategoryViewSetSection07Test`, `RoutingSection07Test`). All pass.