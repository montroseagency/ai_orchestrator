Now I have all the context I need. Let me produce the section content.

# Section 02: AgentGlobalTask Model Changes

## Overview

This section extends the existing `AgentGlobalTask` model in `server/api/models/agent_scheduling.py` with three groups of new fields: **client tagging**, **category FK** (to the new `TaskCategory` model), and **recurrence fields** (replacing the separate `RecurringTaskTemplate` model). It also extends the status choices to include `in_review`.

**Depends on:** section-01-taskcategory-model (the `TaskCategory` model must exist before the FK can be defined)

**Blocks:** section-03-scheduledtasklink, section-04-migrations

## File to Modify

`/home/ubuntu/Montrroase_website/server/api/models/agent_scheduling.py`

## Current State

The `AgentGlobalTask` model (line 80) currently has:
- `Status` TextChoices with `TODO`, `IN_PROGRESS`, `DONE`
- `TASK_CATEGORY_CHOICES` list of hardcoded string tuples (lines 92-109)
- `task_category` CharField using those choices (line 125)
- `recurring_source` FK to `RecurringTaskTemplate` (line 139)
- No client FK (tasks are not tagged to clients)
- No recurrence fields on the model itself

The `Client` model lives in `server/api/models/clients.py` and uses a standard auto-incrementing PK (not UUID).

---

## Tests First

Create or add to `server/api/tests.py` (or a `tests/` package). These tests validate the model changes in isolation.

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

### Implementation Notes for Tests

All tests should use `django.test.TestCase`. A `setUp` method should create the required `Agent` (and its associated `User`) and optionally a `Client` and `TaskCategory` fixture. The recurrence validation test ("requires recurrence_frequency when is_recurring=True") is a **serializer-level** concern, not a model-level constraint -- the model allows all null combinations. The test here should simply confirm the fields accept null values without error.

---

## Implementation Details

### 1. Extend Status Choices

Add `IN_REVIEW` to the `Status` TextChoices class on `AgentGlobalTask`, positioned between `IN_PROGRESS` and `DONE`:

```python
class Status(models.TextChoices):
    TODO = 'todo', 'To Do'
    IN_PROGRESS = 'in_progress', 'In Progress'
    IN_REVIEW = 'in_review', 'In Review'
    DONE = 'done', 'Done'
```

This new status is used by the review-required workflow: tasks in categories with `requires_review=True` auto-redirect to `in_review` instead of `done` when an agent completes them. An admin then approves them to `done`. The status transition logic itself lives in the serializer (section-06), not the model.

### 2. Add Client FK

Add a nullable FK to the `Client` model. This replaces page-level client filtering with per-task metadata.

```python
client = models.ForeignKey(
    'Client', on_delete=models.SET_NULL, null=True, blank=True,
    related_name='global_tasks'
)
```

The `Client` model is in `server/api/models/clients.py`. Using a string reference (`'Client'`) avoids circular imports since both models are in the same app.

### 3. Add Category FK

Add `task_category_ref` as a nullable FK to `TaskCategory`. The name `task_category_ref` (not `task_category`) is intentional to avoid collision with the existing `task_category` CharField during the transition period. The old CharField is removed in Migration D (section-04).

```python
task_category_ref = models.ForeignKey(
    'TaskCategory', on_delete=models.SET_NULL, null=True, blank=True,
    related_name='tasks'
)
```

### 4. Add Recurrence Fields

These fields embed recurrence configuration directly on the task, replacing the separate `RecurringTaskTemplate` model:

```python
is_recurring = models.BooleanField(default=False)

recurrence_frequency = models.CharField(
    max_length=20, null=True, blank=True,
    choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('biweekly', 'Biweekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
        ('custom', 'Custom'),
    ]
)

recurrence_days = models.JSONField(
    null=True, blank=True,
    help_text='ISO weekday numbers for weekly patterns, e.g. [0,2,4] for Mon/Wed/Fri'
)

recurrence_interval = models.IntegerField(
    null=True, blank=True, default=1,
    help_text='Every N units of frequency'
)

recurrence_end_type = models.CharField(
    max_length=10, null=True, blank=True,
    choices=[
        ('never', 'Never'),
        ('count', 'After N occurrences'),
        ('date', 'Until date'),
    ]
)

recurrence_end_count = models.IntegerField(null=True, blank=True)
recurrence_end_date = models.DateField(null=True, blank=True)

recurrence_parent = models.ForeignKey(
    'self', on_delete=models.SET_NULL, null=True, blank=True,
    related_name='recurrence_instances'
)

recurrence_instance_number = models.IntegerField(null=True, blank=True)
```

All recurrence fields are nullable. When `is_recurring=False` (the default), all recurrence fields should be null. Validation of consistency (e.g., requiring `recurrence_frequency` when `is_recurring=True`) is handled at the serializer level (section-06), not the model level.

The `recurrence_parent` self-FK links generated instances back to the original template task. The `recurrence_instance_number` tracks which occurrence a generated task represents. Together with a `unique_together` constraint added in Migration C (section-04), these prevent duplicate JIT-generated instances.

### 5. Add New Indexes

Update the `Meta.indexes` list to add indexes that support the new query patterns:

```python
class Meta:
    ordering = ['order', '-created_at']
    indexes = [
        models.Index(fields=['agent', 'status']),
        models.Index(fields=['agent', 'scheduled_date']),
        models.Index(fields=['agent', 'task_category']),  # existing, removed in Migration D
        models.Index(fields=['agent', 'client']),
        models.Index(fields=['task_category_ref', 'status']),
        models.Index(fields=['recurrence_parent']),
        models.Index(fields=['client', 'scheduled_date']),
    ]
```

The `(agent, client)` index supports filtering an agent's tasks by client. The `(task_category_ref, status)` index supports category-based dashboards. The `(recurrence_parent,)` index supports looking up all instances of a recurring series. The `(client, scheduled_date)` index supports client reporting queries in a later split.

Note: The existing `(agent, task_category)` index references the old CharField and will be removed when that field is dropped in Migration D. Both can coexist until then.

### 6. Keep Existing Fields

The following existing fields must remain unchanged during this section:

- `TASK_CATEGORY_CHOICES` list (lines 92-109) -- removed in Migration D
- `task_category` CharField (line 125) -- removed in Migration D  
- `recurring_source` FK to `RecurringTaskTemplate` (line 139) -- removed in Migration D

These fields coexist with the new fields during the transition. The cleanup happens in section-04 (Migration D).

---

## Summary of Changes to `AgentGlobalTask`

| Change | Type | Details |
|--------|------|---------|
| `Status.IN_REVIEW` | Modified enum | New choice between IN_PROGRESS and DONE |
| `client` | New FK | Nullable FK to Client, SET_NULL |
| `task_category_ref` | New FK | Nullable FK to TaskCategory, SET_NULL |
| `is_recurring` | New BooleanField | Default False |
| `recurrence_frequency` | New CharField | Nullable, 6 choices |
| `recurrence_days` | New JSONField | Nullable, stores weekday array |
| `recurrence_interval` | New IntegerField | Nullable, default 1 |
| `recurrence_end_type` | New CharField | Nullable, 3 choices |
| `recurrence_end_count` | New IntegerField | Nullable |
| `recurrence_end_date` | New DateField | Nullable |
| `recurrence_parent` | New self-FK | Nullable, SET_NULL |
| `recurrence_instance_number` | New IntegerField | Nullable |
| 4 new indexes | Meta.indexes | See list above |

No fields are removed in this section. No migrations are generated in this section (that is section-04). This section is purely about defining the model fields in Python code.