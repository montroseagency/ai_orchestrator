# Spec: Backend Task Model & API Restructuring

## Summary

Refactor the Django backend to support a unified task system with client tagging as metadata, admin-configurable categories, and recurring tasks as a native property of any task with Just-In-Time generation. This is the foundational split — all other splits depend on its API shape.

## Dependencies

None. This is the foundation.

## Goals

1. **Client tagging as metadata:** Tasks carry a client FK instead of being page-level filtered. Enables cross-client workload views.
2. **Admin-configurable categories:** Replace hardcoded `TaskCategory` enum with a database-backed `TaskCategory` model that admins can CRUD. Categories must be concrete effort types (Design, Copywriting, SEO Optimization, etc.), not vague labels.
3. **Recurring tasks as task property:** Eliminate the separate `RecurringTaskTemplate` model. Add recurrence fields directly to `AgentGlobalTask`. Implement JIT generation — only create the next instance when the current one completes.
4. **Approval workflow status:** Extend task status from `todo|in_progress|done` to `todo|in_progress|in_review|done` to support admin approval workflow.
5. **Backward-compatible migrations:** Existing task data must survive the migration.

## Existing Code to Refactor

### Django Backend (server/)
- **Models to modify:** `AgentGlobalTask`, `RecurringTaskTemplate` (to be merged/deprecated)
- **API endpoints:** `/agent/schedule/global-tasks/`, `/agent/schedule/recurring-tasks/`
- **Serializers:** Corresponding DRF serializers for the above

### Frontend Types (client/lib/types/scheduling.ts)
- `AgentGlobalTask` interface — needs `client`, `client_name`, recurrence fields, `in_review` status
- `GlobalTaskStatus` — add `'in_review'`
- `TaskCategory` — change from union type to dynamic (fetched from API)
- `CreateGlobalTaskRequest` / `UpdateGlobalTaskRequest` — add new fields
- `RecurringTaskTemplate` — deprecate, merge into `AgentGlobalTask`

### Frontend API (client/lib/api/scheduling.ts)
- `schedulingApi` — update task CRUD methods for new fields
- Add `getTaskCategories()`, `createTaskCategory()`, `updateTaskCategory()`, `deleteTaskCategory()` endpoints
- Deprecate `getRecurringTasks()` / `createRecurringTask()` in favor of task recurrence properties

## Detailed Requirements

### New/Modified Django Models

#### TaskCategory (NEW)
```
TaskCategory:
  id: UUID (primary key)
  name: CharField (unique, max 100)
  slug: SlugField (auto-generated)
  color: CharField (hex color, default #2563EB)
  icon: CharField (optional, Lucide icon name)
  department: CharField (choices: marketing, developer, both)
  is_active: BooleanField (default True)
  sort_order: IntegerField (default 0)
  created_by: FK → User (admin who created it)
  created_at: DateTimeField
  updated_at: DateTimeField
```

Default seed categories: Design, Copywriting, SEO Optimization, QA Review, Client Communication, Administrative Ops, Content Creation, Strategy, Research, Development, DevOps

#### AgentGlobalTask (MODIFIED)
New fields to add:
```
  client: FK → Client (nullable, on_delete=SET_NULL)
  task_category_id: FK → TaskCategory (nullable, replaces task_category CharField)

  # Recurrence fields (replaces RecurringTaskTemplate)
  is_recurring: BooleanField (default False)
  recurrence_frequency: CharField (choices: daily, weekly, biweekly, monthly, yearly, custom; nullable)
  recurrence_days: JSONField (nullable, e.g., [1,3] for Mon/Wed for weekly)
  recurrence_interval: IntegerField (nullable, e.g., 3 for "every 3 weeks")
  recurrence_end_type: CharField (choices: never, count, date; nullable)
  recurrence_end_count: IntegerField (nullable)
  recurrence_end_date: DateField (nullable)
  recurrence_parent: FK → self (nullable, tracks which template spawned this instance)
  recurrence_instance_number: IntegerField (nullable, which occurrence this is)
```

Status field change:
```
  status: CharField (choices: todo, in_progress, in_review, done)  # Added in_review
```

#### RecurringTaskTemplate (DEPRECATE)
- Keep the model for backward compatibility during migration
- Add a data migration to convert existing templates into `AgentGlobalTask` records with `is_recurring=True`
- Mark model as deprecated, remove from new code paths

### API Endpoints

#### Task Categories (NEW)
- `GET /agent/schedule/task-categories/` — List active categories (filterable by department)
- `POST /admin/task-categories/` — Create category (admin only)
- `PATCH /admin/task-categories/{id}/` — Update category (admin only)
- `DELETE /admin/task-categories/{id}/` — Soft delete (admin only)

#### AgentGlobalTask (MODIFIED)
- All existing endpoints remain, with new fields in serializer
- `POST /agent/schedule/global-tasks/{id}/complete/` — Mark complete; if recurring, trigger JIT generation of next instance
- New filter params: `?client={id}`, `?task_category_id={id}`, `?is_recurring=true`

### JIT Recurring Task Generation

When a recurring task instance is marked `done`:
1. Read recurrence rules from the completed instance
2. Calculate next occurrence date based on frequency/interval/days
3. Check end conditions (count reached? date passed?)
4. If not ended, create new `AgentGlobalTask` with:
   - Same title, description, priority, client, category
   - New `scheduled_date` = calculated next date
   - `recurrence_parent` = same parent (or self if this was the template)
   - `recurrence_instance_number` = previous + 1
   - `status` = `todo`
5. Return both the completed task and the newly created task in the response

### Frontend Type Updates

```typescript
// New status
export type GlobalTaskStatus = 'todo' | 'in_progress' | 'in_review' | 'done';

// TaskCategory becomes dynamic
export interface TaskCategoryItem {
  id: string;
  name: string;
  slug: string;
  color: string;
  icon: string | null;
  department: 'marketing' | 'developer' | 'both';
  is_active: boolean;
  sort_order: number;
}

// AgentGlobalTask gains new fields
export interface AgentGlobalTask {
  // ... existing fields ...
  client: string | null;        // Client UUID
  client_name: string;          // Denormalized
  task_category_id: string | null;  // FK to TaskCategoryItem
  task_category_detail: TaskCategoryItem | null;  // Nested serializer

  // Recurrence
  is_recurring: boolean;
  recurrence_frequency: 'daily' | 'weekly' | 'biweekly' | 'monthly' | 'yearly' | 'custom' | null;
  recurrence_days: number[] | null;
  recurrence_interval: number | null;
  recurrence_end_type: 'never' | 'count' | 'date' | null;
  recurrence_end_count: number | null;
  recurrence_end_date: string | null;
  recurrence_parent: string | null;
  recurrence_instance_number: number | null;
}
```

## Out of Scope

- Frontend UI components (Split 03)
- Calendar/scheduling changes (Split 04)
- Admin settings page UI (Split 06)
- Notification triggers (Split 03/06)

## Acceptance Criteria

1. `AgentGlobalTask` model has all new fields with migrations applied
2. `TaskCategory` model exists with seed data
3. Existing tasks survive migration with no data loss
4. API endpoints accept and return new fields
5. JIT recurring task generation works on task completion
6. `in_review` status is accepted and queryable
7. Frontend types updated to match new API shape
8. Frontend API wrapper methods updated
9. Existing functionality (create, update, list, filter tasks) continues to work
10. Admin-only endpoints reject non-admin users
