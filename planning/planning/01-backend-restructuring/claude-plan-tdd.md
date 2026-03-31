# TDD Plan: Split 01 — Backend Task Model & API Restructuring

## Testing Context

- **Framework:** Django TestCase (standard `django.test.TestCase`)
- **Current state:** `server/api/tests.py` exists but is empty — no existing test infrastructure to follow
- **Run command:** `python manage.py test api`
- **Approach:** Since there are no existing patterns, use Django TestCase with `setUp` methods for fixture creation. Use Django's built-in `Client` for API tests. Use `APIClient` from DRF for authenticated requests.

---

## Section 1: TaskCategory Model & Seed Data

### Model Tests

```python
# Test: TaskCategory creates with all required fields and defaults
# Test: TaskCategory.slug auto-generates from name on creation
# Test: TaskCategory.slug does NOT update when name changes (prevents URL breakage)
# Test: TaskCategory.name uniqueness constraint rejects duplicates
# Test: TaskCategory.slug uniqueness constraint rejects duplicates
# Test: TaskCategory.department choices limited to marketing/website/both
# Test: TaskCategory.color defaults to #2563EB
# Test: TaskCategory ordering is by (sort_order, name)
# Test: TaskCategory.__str__ returns name
```

### Seed Data Migration Tests

```python
# Test: After migration, 11 seed categories exist
# Test: Seed categories have correct department assignments
# Test: Copywriting and QA Review categories have requires_review=True
# Test: Seed category slugs are correctly generated
```

### Index Tests

```python
# Test: Query filtering by (is_active, department) uses index (check with EXPLAIN or just verify query works)
```

---

## Section 2: AgentGlobalTask Model Changes

### Client Tagging Tests

```python
# Test: AgentGlobalTask.client is nullable (can create task without client)
# Test: AgentGlobalTask.client FK links to Client model correctly
# Test: Deleting a Client sets task.client to NULL (SET_NULL behavior)
# Test: task.client.name accessible for denormalized display
```

### Category FK Tests

```python
# Test: AgentGlobalTask.task_category_ref is nullable
# Test: AgentGlobalTask.task_category_ref links to TaskCategory correctly
# Test: Deleting a TaskCategory sets task.task_category_ref to NULL
```

### Recurrence Field Tests

```python
# Test: Default is_recurring=False
# Test: Recurring task requires recurrence_frequency when is_recurring=True
# Test: Non-recurring task allows null recurrence fields
# Test: recurrence_days stores and retrieves JSON array correctly (e.g., [1,3])
# Test: recurrence_parent self-FK works (child points to parent)
# Test: recurrence_instance_number tracks occurrence count
```

### Status Extension Tests

```python
# Test: Status choices include 'todo', 'in_progress', 'in_review', 'done'
# Test: Task can be set to 'in_review' status
# Test: Status transitions are not enforced at model level (serializer handles this)
```

---

## Section 3: ScheduledTaskLink Simplification

```python
# Test: ScheduledTaskLink.task is a direct FK to AgentGlobalTask
# Test: ScheduledTaskLink unique_together on (task, agent) prevents duplicate links
# Test: Creating a link with task FK works
# Test: Deleting the AgentGlobalTask cascades to delete the link (or SET_NULL — verify desired behavior)
# Test: GenericFK fields (content_type, object_id) no longer exist on model
```

---

## Section 4: Django Migrations

```python
# Test: All migrations apply cleanly on a fresh database (migrate from zero)
# Test: All migrations have reverse functions (migrate backward)
# Test: After Migration B, seed TaskCategory records exist
# Test: After Migration B, any existing RecurringTaskTemplate records with target_type='global' are converted to AgentGlobalTask with is_recurring=True
# Test: After Migration D, RecurringTaskTemplate model no longer exists in the schema
# Test: After Migration D, old task_category CharField is removed from AgentGlobalTask
# Test: After Migration D, recurring_source FK is removed from AgentGlobalTask and AgentTimeBlock
```

---

## Section 5: JIT Recurring Task Generation

### Next Date Calculation Tests

```python
# Test: Daily frequency returns next day
# Test: Weekly frequency with recurrence_days=[1,3] returns next Monday or Wednesday
# Test: Biweekly frequency returns date 2 weeks later
# Test: Monthly frequency preserves day-of-month from scheduled_date
# Test: Custom frequency with interval=3 and weekly returns 3 weeks later
# Test: End type 'date' — returns None when next date exceeds end_date
# Test: End type 'count' — returns None when instance_number reaches end_count
# Test: End type 'never' — always returns next date
# Test: Null scheduled_date falls back to current date as dtstart
```

### Instance Creation Tests

```python
# Test: Completing a recurring task creates a new task with status='todo'
# Test: New instance copies title, description, priority, client, category from parent
# Test: New instance has correct recurrence_parent (original template or self)
# Test: New instance has recurrence_instance_number = previous + 1
# Test: New instance has correct scheduled_date from calculation
# Test: Completing a non-recurring task does NOT create a new instance
```

### Review-Required Interception Tests

```python
# Test: Task in requires_review category — setting to 'done' from 'in_progress' redirects to 'in_review'
# Test: Task in requires_review category — setting to 'done' from 'in_review' allows completion (admin approving)
# Test: Task in non-review category — setting to 'done' works directly
# Test: JIT generation fires only on actual 'done' (not on 'in_review' redirect)
```

### Race Condition Tests

```python
# Test: Concurrent complete requests don't create duplicate next instances
# Test: unique_together (recurrence_parent, recurrence_instance_number) prevents duplicates at DB level
```

---

## Section 6: API Layer — Serializers

### Read Serializer Tests

```python
# Test: AgentGlobalTaskReadSerializer includes nested task_category_detail object
# Test: AgentGlobalTaskReadSerializer includes computed client_name
# Test: AgentGlobalTaskReadSerializer includes is_overdue computed field
# Test: AgentGlobalTaskReadSerializer includes all recurrence fields
```

### Write Serializer Tests

```python
# Test: AgentGlobalTaskWriteSerializer accepts task_category_ref as UUID
# Test: AgentGlobalTaskWriteSerializer accepts client as UUID
# Test: validate_status rejects invalid status transitions where applicable
# Test: validate_status intercepts 'done' for requires_review categories
# Test: validate checks recurrence field consistency (is_recurring=True requires frequency)
# Test: Invalid UUID for task_category_ref returns 400
# Test: Invalid UUID for client returns 400
```

### TaskCategorySerializer Tests

```python
# Test: Serializes all fields correctly
# Test: slug is read-only (cannot be set via API)
```

### IsAdmin Permission Tests

```python
# Test: Admin user is allowed
# Test: Agent user is denied
# Test: Client user is denied
# Test: Unauthenticated user is denied
```

---

## Section 7: API Layer — ViewSets & Routing

### AgentGlobalTaskViewSet Tests

```python
# Test: GET /agent/schedule/global-tasks/ returns list with new fields
# Test: GET with ?client={id} filters by client
# Test: GET with ?task_category_id={id} filters by category
# Test: GET with ?is_recurring=true filters recurring tasks
# Test: POST /agent/schedule/global-tasks/ creates task with new fields
# Test: POST /agent/schedule/global-tasks/{id}/complete/ marks task done
# Test: POST /complete/ on recurring task returns both completed and new instance
# Test: POST /complete/ on requires_review category redirects to in_review
# Test: POST /complete/ by admin user (no agent_profile) works for reviewed tasks
# Test: ViewSet uses read serializer for GET, write serializer for POST/PATCH
# Test: QuerySet uses select_related for performance (no N+1)
```

### TaskCategoryViewSet Tests

```python
# Test: GET /agent/schedule/task-categories/ returns active categories filtered by agent department
# Test: Marketing agent sees marketing + both categories
# Test: Website agent sees website + both categories
# Test: POST /admin/task-categories/ creates category (admin only)
# Test: PATCH /admin/task-categories/{id}/ updates category (admin only)
# Test: DELETE /admin/task-categories/{id}/ soft-deletes (sets is_active=False)
# Test: Non-admin users get 403 on admin endpoints
```

### Function-Based View Tests

```python
# Test: command_center returns tasks with correct client data (not hardcoded empty)
# Test: command_center uses updated serializer/helper with new fields
# Test: cross_client_tasks works with direct FK ScheduledTaskLink (not GenericFK)
# Test: cross_client_tasks returns tasks with task_category_ref data
```

### Routing Tests

```python
# Test: /agent/schedule/task-categories/ resolves
# Test: /admin/task-categories/ resolves
# Test: /agent/schedule/recurring-tasks/ no longer resolves (removed)
# Test: /agent/schedule/global-tasks/{id}/complete/ resolves
```

---

## Section 8: Celery Task Cleanup

```python
# Test: generate_recurring_tasks function no longer exists in scheduling_tasks.py
# Test: CELERY_BEAT_SCHEDULE no longer contains 'generate-recurring-tasks' entry
# Test: generate_recurring_time_blocks still exists and works (unrelated to task recurrence)
```

---

## Section 9: Frontend Type Updates

```typescript
// Test: GlobalTaskStatus type includes 'in_review'
// Test: TaskCategoryItem interface has all expected fields (id, name, slug, color, icon, department, requires_review, is_active, sort_order)
// Test: AgentGlobalTask interface includes client, client_name, task_category_ref, task_category_detail, recurrence fields
// Test: RecurringTaskTemplate type no longer exported
// Test: Old TaskCategory string union type no longer exported
// Test: TypeScript compiles without errors after changes
```

---

## Section 10: Frontend API Updates

```typescript
// Test: getTaskCategories() calls correct endpoint with optional department param
// Test: createTaskCategory() POSTs to /admin/task-categories/
// Test: completeGlobalTask(id) POSTs to /agent/schedule/global-tasks/{id}/complete/
// Test: getGlobalTasks() accepts client, task_category_id, is_recurring params
// Test: createGlobalTask() sends new fields (client, task_category_ref, recurrence)
// Test: getRecurringTasks/createRecurringTask no longer exported
// Test: TypeScript compiles without errors after changes
```
