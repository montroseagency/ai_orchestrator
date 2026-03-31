# Backend Restructuring — Usage Guide

Generated after completing all 10 sections of `01-backend-restructuring`.

## What Was Built

The agent scheduling backend has been fully restructured away from the old
`RecurringTaskTemplate` / generic-FK model toward a unified `AgentGlobalTask`
with inline recurrence fields and a direct `ScheduledTaskLink.task` FK.

---

## Key Model Changes

| Before | After |
|--------|-------|
| `RecurringTaskTemplate` model | Removed — recurrence lives on `AgentGlobalTask` |
| `ScheduledTaskLink` with GenericFK (`content_type` / `object_id`) | Direct FK `task → AgentGlobalTask` |
| `AgentGlobalTask.task_category` (string slug) | `task_category_ref → TaskCategory` FK + `task_category_detail` nested read |
| Celery periodic task generator | Removed — replaced by JIT recurrence service |

---

## Backend

### Migrations (sections 01–04)
Migrations `0070`–`0073` are applied in order. Run:
```bash
python manage.py migrate
```

### JIT Recurrence Service (section 05)
`server/api/services/recurrence.py`
- `generate_next_instance(task)` — called inside `complete` action to create the next recurring instance
- `should_intercept_for_review(task, target_status)` — redirects tasks that `requires_review` to `in_review` instead of `done`

### Serializers (section 06)
`server/api/serializers/scheduling_serializers.py`
- `AgentGlobalTaskReadSerializer` — nested `task_category_detail`, `client_name`
- `AgentGlobalTaskWriteSerializer` — accepts `task_category_ref` (string UUID), all recurrence fields
- `TaskCategorySerializer` — full category detail
- `IsAdmin` permission — `request.user.role == 'admin'`

### Viewsets & URLs (section 07)
`server/api/views/agent/scheduling_views.py`
- `AgentGlobalTaskViewSet.complete` — marks done, JIT creates next instance, returns `{ ...task, next_task }`
- `AgentTaskCategoryViewSet` — read-only, filtered by department, `/agent/schedule/task-categories/`
- `AdminTaskCategoryViewSet` — full CRUD with soft-delete, `/admin/task-categories/`
- `ScheduledTaskLinkViewSet` — now uses direct `task` FK

### Celery Cleanup (section 08)
- `generate_recurring_tasks` periodic task removed from `CELERY_BEAT_SCHEDULE`
- `RecurringTaskTemplate`-dependent Celery tasks removed

---

## Frontend

### Types (section 09)
`client/lib/types/scheduling.ts`
- `TaskCategoryItem` replaces old `TaskCategory` union
- `AgentGlobalTask` gains `task_category_ref`, `task_category_detail`, inline recurrence fields
- `ScheduledTaskLink` uses `task: string` instead of `content_type`/`object_id`
- `GlobalTaskFilters` gains `task_category_id`, `client`, `is_recurring`
- Removed: `TASK_CATEGORY_LABELS`, `TASK_CATEGORY_COLORS`, `MARKETING_CATEGORIES`, `DEVELOPER_CATEGORIES`

### API Layer (section 10)
`client/lib/api/scheduling.ts`
- `completeGlobalTask(id)` → `POST /agent/schedule/global-tasks/{id}/complete/`
- `getTaskCategories(dept?)`, `createTaskCategory()`, `updateTaskCategory()`, `deleteTaskCategory()`
- Removed: all `RecurringTaskTemplate` methods

`client/lib/hooks/useScheduling.ts`
- `useCompleteGlobalTask()`, `useTaskCategories()`, `useCreateTaskCategory()`, `useUpdateTaskCategory()`, `useDeleteTaskCategory()`
- Removed: `useRecurringTasks`, `useCreateRecurringTask`, `useUpdateRecurringTask`, `useDeleteRecurringTask`, `useGenerateRecurringTaskNow`

---

## Pending / Future Work

- `RecurringTaskManager.tsx` is stubbed (`return null`) — needs a full UI rewrite to expose recurrence fields on `AgentGlobalTask`
- `CrossClientTask.task_category` is still a plain string; consider migrating to a nested object if category color is needed there

---

## Commits

| Section | Hash | Description |
|---------|------|-------------|
| 01 | `134399180` | TaskCategory model |
| 02 | `eeec4976c` | AgentGlobalTask model |
| 03 | `e700fd896` | ScheduledTaskLink FK |
| 04 | `94b0e5f06` | Migrations 0070–0073 |
| 05 | `20786ba98` | JIT recurrence service |
| 06 | `7c56af222` | Serializers + IsAdmin |
| 07 | `f96e4af6c` | Viewsets & routing |
| 08 | `559e1e980` | Celery cleanup |
| 09 | `4adacf46f` | Frontend types |
| 10 | `00d6b425c` | Frontend API layer |
