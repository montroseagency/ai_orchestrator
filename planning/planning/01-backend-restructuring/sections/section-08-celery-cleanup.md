Good -- the secondary `server/settings.py` file does not contain the `generate-recurring-tasks` entry, so no changes needed there. Now I have all the context needed.

# Section 8: Celery Task Cleanup

## Overview

This section removes the periodic Celery Beat task `generate_recurring_tasks()` and its helper `_should_generate_on_date()` from the codebase. Recurring task generation is now handled by the JIT (just-in-time) approach implemented in Section 5, which creates the next task instance when the current one is completed. The related helper `generate_tasks_from_template()` is also removed since it is only called by the deleted task.

The `generate_recurring_time_blocks()` task and its helper `generate_blocks_from_recurring()` must be preserved -- they handle `AgentRecurringBlock` to `AgentTimeBlock` generation, which is a completely separate system.

## Dependencies

- **Section 4 (Migrations):** Migration D removes the `RecurringTaskTemplate` model that the deleted code imports. This section can run in parallel with Section 5 after Section 4 is complete.
- **Section 5 (JIT Recurrence):** The JIT service replaces the functionality being removed here. Both can be implemented in parallel since there is no code-level dependency between them.

## Files to Modify

1. `/home/ubuntu/Montrroase_website/server/api/tasks/scheduling_tasks.py` -- remove functions
2. `/home/ubuntu/Montrroase_website/server/server/settings.py` -- remove Beat schedule entry

## Tests (Write First)

Tests belong in `/home/ubuntu/Montrroase_website/server/api/tests.py` (or a new `tests/` package if one is created by earlier sections). These tests verify the cleanup was done correctly.

```python
# server/api/tests/test_celery_cleanup.py

from django.test import TestCase


class CeleryTaskCleanupTest(TestCase):
    """Verify that the old periodic recurring task generator has been removed
    while the unrelated recurring time block generator remains intact."""

    def test_generate_recurring_tasks_function_removed(self):
        """The generate_recurring_tasks Celery task must not exist in scheduling_tasks."""
        from api.tasks import scheduling_tasks
        self.assertFalse(
            hasattr(scheduling_tasks, 'generate_recurring_tasks'),
            "generate_recurring_tasks should have been removed from scheduling_tasks"
        )

    def test_should_generate_on_date_helper_removed(self):
        """The _should_generate_on_date helper (only used by the removed task) must not exist."""
        from api.tasks import scheduling_tasks
        self.assertFalse(
            hasattr(scheduling_tasks, '_should_generate_on_date'),
            "_should_generate_on_date should have been removed from scheduling_tasks"
        )

    def test_generate_tasks_from_template_helper_removed(self):
        """The generate_tasks_from_template helper (only called by the removed task) must not exist."""
        from api.tasks import scheduling_tasks
        self.assertFalse(
            hasattr(scheduling_tasks, 'generate_tasks_from_template'),
            "generate_tasks_from_template should have been removed from scheduling_tasks"
        )

    def test_celery_beat_schedule_no_recurring_tasks_entry(self):
        """CELERY_BEAT_SCHEDULE must not contain the 'generate-recurring-tasks' entry."""
        from django.conf import settings
        self.assertNotIn(
            'generate-recurring-tasks',
            settings.CELERY_BEAT_SCHEDULE,
            "The 'generate-recurring-tasks' Beat schedule entry should have been removed"
        )

    def test_generate_recurring_time_blocks_still_exists(self):
        """generate_recurring_time_blocks must be preserved (separate system)."""
        from api.tasks import scheduling_tasks
        self.assertTrue(
            hasattr(scheduling_tasks, 'generate_recurring_time_blocks'),
            "generate_recurring_time_blocks must NOT be removed -- it is unrelated to task recurrence"
        )

    def test_generate_recurring_time_blocks_beat_entry_preserved(self):
        """The Beat schedule for time block generation must remain."""
        from django.conf import settings
        self.assertIn(
            'generate-recurring-time-blocks',
            settings.CELERY_BEAT_SCHEDULE,
            "The 'generate-recurring-time-blocks' Beat entry must be preserved"
        )

    def test_generate_blocks_from_recurring_helper_preserved(self):
        """The generate_blocks_from_recurring helper (used by time block generation) must remain."""
        from api.tasks import scheduling_tasks
        self.assertTrue(
            hasattr(scheduling_tasks, 'generate_blocks_from_recurring'),
            "generate_blocks_from_recurring must NOT be removed"
        )
```

## Implementation Details

### Step 1: Remove functions from `scheduling_tasks.py`

File: `/home/ubuntu/Montrroase_website/server/api/tasks/scheduling_tasks.py`

Remove the following three functions entirely:

1. **`generate_tasks_from_template(template, target_date)`** (lines 38-126) -- Helper that creates `AgentGlobalTask`, `MarketingTask`, or `ProjectTask` records from a `RecurringTaskTemplate`. Only called by `generate_recurring_tasks()`.

2. **`_should_generate_on_date(template, target_date)`** (lines 129-143) -- Helper that checks whether a template's recurrence pattern matches a given date (daily, weekly, biweekly, monthly logic). Only called by `generate_recurring_tasks()`.

3. **`generate_recurring_tasks()`** (lines 186-220) -- The `@shared_task` Celery task itself. Queries active `RecurringTaskTemplate` records and calls the two helpers above.

**Keep these functions untouched:**

- `generate_blocks_from_recurring(recurring_block, target_date)` (lines 12-35) -- Generates `AgentTimeBlock` from `AgentRecurringBlock` templates. Unrelated system.
- `generate_recurring_time_blocks()` (lines 146-183) -- The `@shared_task` that drives time block generation. Must remain.

After cleanup, the file should contain only: the module docstring, imports (`celery.shared_task`, `django.utils.timezone`, `datetime.timedelta`, `datetime.date`, `logging`), the logger, `generate_blocks_from_recurring()`, and `generate_recurring_time_blocks()`. Remove any imports that become unused after the deletion (none are expected -- all current imports are also used by the kept functions).

### Step 2: Remove Beat schedule entry from `settings.py`

File: `/home/ubuntu/Montrroase_website/server/server/settings.py`

Remove lines 383-386 (the `'generate-recurring-tasks'` entry) from the `CELERY_BEAT_SCHEDULE` dictionary:

```python
    # REMOVE this entire entry:
    'generate-recurring-tasks': {
        'task': 'api.tasks.scheduling_tasks.generate_recurring_tasks',
        'schedule': crontab(hour=0, minute=10),
    },
```

The adjacent `'generate-recurring-time-blocks'` entry (lines 378-381) must remain.

### Step 3: Verify no other references exist

There is a secondary file `/home/ubuntu/Montrroase_website/server/settings.py` (at the repo root of `server/`) that contains a partial `CELERY_BEAT_SCHEDULE`. This file does **not** contain a `generate-recurring-tasks` entry, so no changes are needed there.

Search the codebase for any other references to the removed functions to ensure nothing else calls them:

- Search for `generate_recurring_tasks` across all Python files
- Search for `generate_tasks_from_template` across all Python files  
- Search for `_should_generate_on_date` across all Python files

If any imports or references are found outside `scheduling_tasks.py` (e.g., in `__init__.py` re-exports, test files, or management commands), remove those references as well.

## Final State

After this section is complete:

- `/home/ubuntu/Montrroase_website/server/api/tasks/scheduling_tasks.py` contains only `generate_blocks_from_recurring()` and `generate_recurring_time_blocks()` (plus imports and logger)
- `/home/ubuntu/Montrroase_website/server/server/settings.py` `CELERY_BEAT_SCHEDULE` has 12 entries (down from 13), with `generate-recurring-time-blocks` still present
- No references to `generate_recurring_tasks`, `generate_tasks_from_template`, or `_should_generate_on_date` exist anywhere in the codebase
- All tests in the test class above pass