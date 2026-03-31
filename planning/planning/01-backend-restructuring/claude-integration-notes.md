# Integration Notes: Opus Review Feedback

## Integrated (Critical)

### Issue #1: `recurring_source` FK not addressed — INTEGRATING
Both `AgentTimeBlock` (line 49) and `AgentGlobalTask` (line 139) have `recurring_source` FKs to `RecurringTaskTemplate`. These must be dropped before or simultaneously with removing the `RecurringTaskTemplate` model in Migration D, or Django will refuse to apply the migration. Adding explicit cleanup of these FKs to Section 4 (Migration D).

### Issue #2: Department value mismatch — INTEGRATING
Confirmed: `Agent.department` uses `'marketing'` / `'website'`, but the plan's `TaskCategory.department` uses `'marketing'` / `'developer'`. Changing `TaskCategory.department` choices to `marketing` / `website` / `both` to match the actual Agent model values. This is a straightforward fix in Section 1.

### Issue #3: `command_center` and `cross_client_tasks` views not updated — INTEGRATING
Confirmed these function-based views exist and use the old CharField, old serializer name, and GenericFK-based `ScheduledTaskLink`. Adding a new section or expanding Section 7 to cover updates to these views. The `_serialize_global_task` helper also hardcodes empty client data (Issue #15) — fixing both together.

### Issue #4: `ScheduledTaskLink` unique constraint not updated — INTEGRATING
Confirmed `unique_together = ['content_type', 'object_id', 'agent']`. When GenericFK fields are removed, this must become `unique_together = ['task', 'agent']`. Adding to Section 3.

### Issue #5: `ScheduledTaskLink.task` field name collision — INTEGRATING
The existing `task = GenericForeignKey(...)` attribute conflicts with the new FK name. Renaming the new FK to `linked_task` during transition, then renaming to `task` in the cleanup migration (D). OR, removing the GFK and adding the FK in the same migration since the database is fresh. Going with the latter approach — in Migration A, remove GFK fields and add the new `task` FK simultaneously. This is safe since we're on a fresh database.

## Integrated (Significant)

### Issue #7: `IsAdmin` and admin users without `agent_profile` — INTEGRATING
Admin users won't have `agent_profile`, so the `/complete/` action (which an admin uses to approve reviewed tasks) must not call `_get_agent(request)`. Adding a note to Section 7 that the `complete` action should check `request.user.role` and handle admin callers without assuming an agent profile.

### Issue #8: JIT race condition — INTEGRATING
Adding a `unique_together` constraint on `(recurrence_parent, recurrence_instance_number)` to prevent duplicate instance creation. Also noting `select_for_update()` in the complete action. Adding to Section 5.

### Issue #13: Celery Beat schedule location — INTEGRATING
Fixing Section 8: the actual location is `server/server/settings.py` line 326, not `server/config/celery.py`. Also noting Issue #14: there's a second `CELERY_BEAT_SCHEDULE` in `server/settings.py` line 5 that needs cleanup.

### Issue #15: `_serialize_global_task` hardcodes empty client data — INTEGRATING
Covered as part of Issue #3 — updating the helper to use the new `client` FK.

## Not Integrating

### Issue #6: Old index on `(agent, task_category)` — NOT INTEGRATING
Django automatically drops indexes when the field is removed in a migration. This is standard Django behavior and doesn't need explicit handling.

### Issue #9: `MarketingTask` and `ProjectTask` templates not migrated — NOT INTEGRATING
The plan already limits conversion to `target_type='global'` templates. The spec's goal is to unify around `AgentGlobalTask`. MarketingTask/ProjectTask are separate models being deprecated across later splits. Their recurring templates are intentionally not carried forward. This is acceptable data loss per the spec's scope.

### Issue #10: `apply_to_all_clients` and `day_of_month` — NOT INTEGRATING
`day_of_month` is implicitly handled by `dtstart` in dateutil.rrule (the day-of-month from scheduled_date). `apply_to_all_clients` is a batch operation that doesn't map cleanly to single-task recurrence — if needed, it can be re-implemented as a bulk creation utility in a later split. The plan's approach is correct.

### Issue #11: 24 frontend files importing scheduling types — NOT INTEGRATING
The spec explicitly lists frontend UI components as out of scope (Split 03). Sections 9-10 update only the type definitions and API wrappers. Downstream component updates are Split 03's responsibility. The type changes will cause compile errors, which is expected and intentional — they serve as a checklist for Split 03.

### Issue #12: `TASK_CATEGORY_LABELS` and `TASK_CATEGORY_COLORS` constants — NOT INTEGRATING
Same reasoning as Issue #11. These are UI-facing constants that will be replaced with dynamic data from the API in Split 03.

### Issue #14: Two `CELERY_BEAT_SCHEDULE` definitions — PARTIALLY INTEGRATING
Noting both locations in Section 8 so the implementer checks both. The `server/settings.py` one appears to be a legacy/duplicate.

### Issue #16: `order` field / drag-and-drop with `in_review` — NOT INTEGRATING
This is a frontend UI concern (Split 03). The backend simply adds a new status choice; how the UI presents it is out of scope.
