I have enough context now. Let me generate the section content.

# Section 5: JIT Recurring Task Generation

## Overview

This section implements a Just-In-Time (JIT) service that generates the next recurring task instance when a task is completed, replacing the old Celery Beat periodic generator (removed in Section 8). The service lives in a new file at `server/api/services/recurrence.py` and is called from the `/complete/` action on `AgentGlobalTaskViewSet` (Section 7).

## Dependencies

- **Section 2 (AgentGlobalTask model changes):** Requires the recurrence fields (`is_recurring`, `recurrence_frequency`, `recurrence_days`, `recurrence_interval`, `recurrence_end_type`, `recurrence_end_count`, `recurrence_end_date`, `recurrence_parent`, `recurrence_instance_number`) and the `IN_REVIEW` status choice to exist on `AgentGlobalTask`.
- **Section 1 (TaskCategory model):** Requires `TaskCategory.requires_review` for review-required interception logic.
- **Section 4 (Migrations):** All schema changes must be applied. The `unique_together` constraint on `(recurrence_parent, recurrence_instance_number)` from Migration C is the database-level safety net for race conditions.
- **Section 6 (Serializers):** The `validate_status` method on `AgentGlobalTaskWriteSerializer` implements the review-required interception. This section defines the service logic that the serializer and viewset call into.

## Library Dependency

`dateutil` (python-dateutil) must be available. It is used for `dateutil.rrule` to compute next occurrence dates.

---

## Tests

All tests go in `server/api/tests/test_recurrence.py`. Write tests before implementation.

### Next Date Calculation Tests

```python
# server/api/tests/test_recurrence.py
from django.test import TestCase
from datetime import date
from api.services.recurrence import calculate_next_date

class CalculateNextDateTests(TestCase):
    """Tests for the calculate_next_date utility function."""

    # Test: Daily frequency returns the next day after scheduled_date
    def test_daily_returns_next_day(self): ...

    # Test: Weekly frequency with recurrence_days=[0,2] (Mon, Wed) returns the
    # next Monday or Wednesday after the current scheduled_date
    def test_weekly_with_days_returns_next_matching_day(self): ...

    # Test: Biweekly frequency returns a date 2 weeks later
    def test_biweekly_returns_two_weeks_later(self): ...

    # Test: Monthly frequency preserves day-of-month from scheduled_date
    def test_monthly_preserves_day_of_month(self): ...

    # Test: Custom frequency with interval=3 and weekly returns 3 weeks later
    def test_custom_interval_weekly(self): ...

    # Test: End type 'date' — returns None when next date exceeds end_date
    def test_end_type_date_returns_none_past_end(self): ...

    # Test: End type 'count' — returns None when instance_number reaches end_count
    def test_end_type_count_returns_none_at_limit(self): ...

    # Test: End type 'never' — always returns a next date
    def test_end_type_never_always_returns(self): ...

    # Test: Null scheduled_date falls back to current date as dtstart
    def test_null_scheduled_date_uses_today(self): ...
```

### Instance Creation Tests

```python
from django.test import TestCase
from api.services.recurrence import generate_next_instance

class GenerateNextInstanceTests(TestCase):
    """Tests for the generate_next_instance service function."""

    def setUp(self):
        """Create an Agent, TaskCategory, and a recurring AgentGlobalTask."""
        ...

    # Test: Completing a recurring task creates a new task with status='todo'
    def test_creates_new_task_with_todo_status(self): ...

    # Test: New instance copies title, description, priority, client, category
    def test_copies_fields_from_parent(self): ...

    # Test: New instance has correct recurrence_parent (original parent or self)
    def test_sets_recurrence_parent(self): ...

    # Test: New instance has recurrence_instance_number = previous + 1
    def test_increments_instance_number(self): ...

    # Test: New instance has correct scheduled_date from date calculation
    def test_sets_calculated_scheduled_date(self): ...

    # Test: Completing a non-recurring task does NOT create a new instance
    def test_non_recurring_returns_none(self): ...
```

### Review-Required Interception Tests

```python
class ReviewInterceptionTests(TestCase):
    """Tests for the review-required status interception logic."""

    def setUp(self):
        """Create a TaskCategory with requires_review=True and a task using it."""
        ...

    # Test: Task in requires_review category — agent setting to 'done' from
    # 'in_progress' gets redirected to 'in_review'
    def test_review_category_redirects_to_in_review(self): ...

    # Test: Task in requires_review category — setting to 'done' from 'in_review'
    # allows completion (admin approving)
    def test_review_category_allows_done_from_in_review(self): ...

    # Test: Task in non-review category — setting to 'done' works directly
    def test_non_review_category_allows_done(self): ...

    # Test: JIT generation fires only on actual 'done' (not on 'in_review' redirect)
    def test_jit_only_fires_on_actual_done(self): ...
```

### Race Condition Tests

```python
from django.db import IntegrityError

class RaceConditionTests(TestCase):
    """Tests for race condition prevention in JIT generation."""

    # Test: unique_together (recurrence_parent, recurrence_instance_number) constraint
    # prevents duplicate instances at the database level
    def test_unique_constraint_prevents_duplicate_instances(self): ...

    # Test: Calling generate_next_instance twice with the same task does not
    # create two instances (second call returns None or raises)
    def test_duplicate_call_handled_gracefully(self): ...
```

---

## Implementation Details

### File: `server/api/services/__init__.py`

Create an empty `__init__.py` to make `services` a Python package.

### File: `server/api/services/recurrence.py`

This file contains two public functions and one helper.

#### Function 1: `calculate_next_date(task) -> date | None`

Computes the next occurrence date for a recurring task using `dateutil.rrule`.

**Algorithm:**

1. Determine `dtstart`: use `task.scheduled_date` if set, otherwise `date.today()`.
2. Map `task.recurrence_frequency` to an rrule frequency constant:
   - `'daily'` maps to `rrule.DAILY`
   - `'weekly'` maps to `rrule.WEEKLY`
   - `'biweekly'` maps to `rrule.WEEKLY` with interval forced to 2
   - `'monthly'` maps to `rrule.MONTHLY`
   - `'yearly'` maps to `rrule.YEARLY`
   - `'custom'` maps to `rrule.WEEKLY` (uses `recurrence_interval` for the interval)
3. Determine the interval: for `'biweekly'` use 2, otherwise use `task.recurrence_interval or 1`.
4. Map `task.recurrence_days` (ISO weekday numbers like `[0, 2]` for Mon/Wed) to `dateutil.rrule` weekday constants (`MO`, `TU`, `WE`, etc.). Only applied when `recurrence_days` is a non-empty list and frequency is weekly/biweekly/custom.
5. Build the `rrule` object with `freq`, `interval`, `dtstart`, and optional `byweekday`.
6. Call `rule.after(dtstart)` to get the next date strictly after the current scheduled date.
7. Check end conditions:
   - If `task.recurrence_end_type == 'date'` and `next_date > task.recurrence_end_date`, return `None`.
   - If `task.recurrence_end_type == 'count'` and `(task.recurrence_instance_number or 0) >= task.recurrence_end_count`, return `None`.
   - If `task.recurrence_end_type == 'never'` or `None`, return the next date.
8. Return the computed `next_date` as a `date` object (convert from `datetime` if needed via `.date()`).

**Important edge case:** `rrule.after(dt)` returns a `datetime`, not a `date`. Always call `.date()` on the result.

#### Function 2: `generate_next_instance(task) -> AgentGlobalTask | None`

Creates the next recurring task instance after a task reaches `done` status.

**Algorithm:**

1. If `task.is_recurring` is `False`, return `None` immediately.
2. Call `calculate_next_date(task)`. If it returns `None` (end condition met), return `None`.
3. Determine `parent`: if `task.recurrence_parent` is set, use it; otherwise use `task` itself (this task is the original template).
4. Determine `next_instance_number`: `(task.recurrence_instance_number or 0) + 1`.
5. Create a new `AgentGlobalTask` with these field copies from `task`:
   - `agent`, `title`, `description`, `priority`, `estimated_minutes`
   - `client` (FK), `task_category_ref` (FK)
   - All recurrence config fields: `is_recurring`, `recurrence_frequency`, `recurrence_days`, `recurrence_interval`, `recurrence_end_type`, `recurrence_end_count`, `recurrence_end_date`
6. Set on the new instance:
   - `status = 'todo'`
   - `scheduled_date = calculated_next_date`
   - `recurrence_parent = parent`
   - `recurrence_instance_number = next_instance_number`
7. Wrap the creation in a try/except for `IntegrityError` (the `unique_together` constraint on `(recurrence_parent, recurrence_instance_number)` catches race conditions). If `IntegrityError` is raised, return `None`.
8. Return the newly created task instance.

#### Function 3: `should_intercept_for_review(task, new_status) -> bool`

A helper that determines whether a status transition to `done` should be intercepted and redirected to `in_review`.

**Logic:**

1. If `new_status != 'done'`, return `False`.
2. If `task.task_category_ref` is `None` or `task.task_category_ref.requires_review` is `False`, return `False`.
3. If `task.status == 'in_review'`, return `False` (admin is approving, allow completion).
4. Return `True` (agent tried to set done on a review-required category while not yet reviewed).

This function is used by both the `AgentGlobalTaskWriteSerializer.validate_status()` method (Section 6) and the `complete` viewset action (Section 7).

### Race Condition Prevention Strategy

The `/complete/` viewset action (Section 7) must wrap its call to `generate_next_instance` inside a transaction with `select_for_update()`:

```python
from django.db import transaction

with transaction.atomic():
    task = AgentGlobalTask.objects.select_for_update().get(pk=task_id)
    # ... set status to done, save ...
    new_instance = generate_next_instance(task)
```

The `select_for_update()` call locks the row, preventing a second concurrent request from reading the same task state. The `unique_together` constraint on `(recurrence_parent, recurrence_instance_number)` is the secondary safety net in case the lock is somehow bypassed.

### Integration Points

The service functions are consumed by two other sections:

1. **Section 6 (Serializers):** `AgentGlobalTaskWriteSerializer.validate_status()` calls `should_intercept_for_review(task, new_status)` to decide whether to override `done` to `in_review`.

2. **Section 7 (ViewSets):** The `AgentGlobalTaskViewSet.complete()` action calls `generate_next_instance(task)` after setting the task to `done`. It returns both the completed task and the new instance (if any) in the response payload. The action also handles admin users (who approve reviewed tasks) by checking `request.user.role` before attempting agent-specific lookups.

### Weekday Mapping Reference

The `recurrence_days` field stores ISO weekday numbers where 0=Monday through 6=Sunday. The `dateutil.rrule` weekday constants map as follows:

| ISO Number | Day | rrule Constant |
|-----------|-----|---------------|
| 0 | Monday | `MO` |
| 1 | Tuesday | `TU` |
| 2 | Wednesday | `WE` |
| 3 | Thursday | `TH` |
| 4 | Friday | `FR` |
| 5 | Saturday | `SA` |
| 6 | Sunday | `SU` |

Build a lookup list like `WEEKDAY_MAP = [MO, TU, WE, TH, FR, SA, SU]` and index into it with the ISO numbers from `recurrence_days`.

### File Summary

| File | Action |
|------|--------|
| `server/api/services/__init__.py` | Create (empty) |
| `server/api/services/recurrence.py` | Create (3 functions: `calculate_next_date`, `generate_next_instance`, `should_intercept_for_review`) |
| `server/api/tests/test_recurrence.py` | Create (test classes: `CalculateNextDateTests`, `GenerateNextInstanceTests`, `ReviewInterceptionTests`, `RaceConditionTests`) |