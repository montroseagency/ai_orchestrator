<!-- PROJECT_CONFIG
runtime: python-pip
test_command: python manage.py test api
END_PROJECT_CONFIG -->

<!-- SECTION_MANIFEST
section-01-taskcategory-model
section-02-agentglobaltask-model
section-03-scheduledtasklink
section-04-migrations
section-05-jit-recurrence
section-06-serializers
section-07-viewsets-routing
section-08-celery-cleanup
section-09-frontend-types
section-10-frontend-api
END_MANIFEST -->

# Implementation Sections Index

## Dependency Graph

| Section | Depends On | Blocks | Parallelizable |
|---------|------------|--------|----------------|
| section-01-taskcategory-model | - | 02, 04 | Yes |
| section-02-agentglobaltask-model | 01 | 03, 04 | No |
| section-03-scheduledtasklink | 02 | 04 | No |
| section-04-migrations | 01, 02, 03 | 05, 06, 07, 08 | No |
| section-05-jit-recurrence | 04, 06 | 07 | No |
| section-06-serializers | 04 | 05, 07 | No |
| section-07-viewsets-routing | 05, 06 | - | No |
| section-08-celery-cleanup | 04 | - | Yes (after 04) |
| section-09-frontend-types | 07 | 10 | Yes (after 07) |
| section-10-frontend-api | 09 | - | No |

## Execution Order

1. **Batch 1:** section-01-taskcategory-model (no dependencies)
2. **Batch 2:** section-02-agentglobaltask-model (after 01)
3. **Batch 3:** section-03-scheduledtasklink (after 02)
4. **Batch 4:** section-04-migrations (after 01, 02, 03)
5. **Batch 5:** section-06-serializers (after 04) — note: 06 before 05 per plan's implementation order
6. **Batch 6:** section-05-jit-recurrence, section-08-celery-cleanup (parallel after 04/06)
7. **Batch 7:** section-07-viewsets-routing (after 05, 06)
8. **Batch 8:** section-09-frontend-types (after 07)
9. **Batch 9:** section-10-frontend-api (after 09)

## Section Summaries

### section-01-taskcategory-model
New `TaskCategory` Django model with UUID PK, admin-configurable fields (name, slug, color, icon, department, requires_review), and seed data migration for 11 default categories.

### section-02-agentglobaltask-model
Extend `AgentGlobalTask` with client FK, category FK (`task_category_ref`), recurrence fields (is_recurring, frequency, days, interval, end conditions, parent/instance tracking), and `in_review` status.

### section-03-scheduledtasklink
Replace `ScheduledTaskLink`'s GenericForeignKey pattern with a direct FK to `AgentGlobalTask`. Update unique_together constraint.

### section-04-migrations
Four sequential migrations: A (schema additions), B (data population/seed), C (constraint enforcement/indexes), D (cleanup of old fields and RecurringTaskTemplate model).

### section-05-jit-recurrence
JIT recurring task generation service using `dateutil.rrule` for next date calculation. Handles review-required interception and race condition prevention with `select_for_update()`.

### section-06-serializers
Read/write serializer split for `AgentGlobalTask`, `TaskCategorySerializer`, `IsAdmin` permission class, and QuerySet optimization with `select_related`.

### section-07-viewsets-routing
Modified `AgentGlobalTaskViewSet` with `/complete/` action, new `TaskCategoryViewSet` (agent + admin), function-based view updates, URL routing changes, and `RecurringTaskTemplateViewSet` removal.

### section-08-celery-cleanup
Remove `generate_recurring_tasks()` Celery task and its Beat schedule entry. Keep `generate_recurring_time_blocks()` (unrelated system).

### section-09-frontend-types
Update TypeScript types in `scheduling.ts`: add `in_review` status, `TaskCategoryItem` interface, new fields on `AgentGlobalTask`, remove deprecated `RecurringTaskTemplate` types.

### section-10-frontend-api
Update `schedulingApi` with new category CRUD methods, `completeGlobalTask()`, updated filter params, and removal of deprecated recurring task methods.
