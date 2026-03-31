# Implementation Plan: Split 01 — Backend Task Model & API Restructuring

## Context

The Montrose platform is a Django + Next.js application that manages marketing and website development agents working across multiple clients. The current scheduling system uses multiple task models (`AgentGlobalTask`, `MarketingTask`, `ProjectTask`) with a separate `RecurringTaskTemplate` model for generating recurring tasks via Celery Beat.

This split restructures the backend to create a unified task model with client tagging, admin-configurable categories, JIT recurring task generation, and an approval workflow. It is the foundation for 5 subsequent splits covering portal navigation, task management UI, scheduling engine, dashboard KPIs, and admin reporting.

**Key files in the existing codebase:**
- Models: `server/api/models/agent_scheduling.py`
- Serializers: `server/api/serializers/agent_scheduling.py`
- Views: `server/api/views/agent/scheduling_views.py`
- Celery tasks: `server/api/tasks/scheduling_tasks.py`
- URL routing: `server/api/urls.py`
- Frontend types: `client/lib/types/scheduling.ts`
- Frontend API: `client/lib/api/scheduling.ts`

**Key constraints:**
- Database is fresh/development — no production data migration risk
- All changes ship in a single deploy — no backward compatibility period needed
- `dateutil` is available for recurrence computation
- The `IsAnyAgent` permission class exists but there is no `IsAdmin` class yet

---

## Section 1: TaskCategory Model & Seed Data

### What to Build

A new `TaskCategory` Django model in `server/api/models/agent_scheduling.py` that replaces the existing hardcoded `TASK_CATEGORY_CHOICES` list. This model allows admins to CRUD categories through an API, and agents to see department-filtered lists.

### Model Design

Fields: `id` (UUID PK), `name` (CharField, unique, max 100), `slug` (SlugField, auto-generated, unique), `color` (CharField, hex, default `#2563EB`), `icon` (CharField, optional, Lucide icon name), `department` (CharField choices: marketing/website/both — matches `Agent.DEPARTMENT_CHOICES` values), `requires_review` (BooleanField, default False), `is_active` (BooleanField, default True), `sort_order` (IntegerField, default 0), `created_by` (FK to User, nullable SET_NULL), timestamps.

The `requires_review` field is a key interview-driven addition: when True, tasks in this category cannot go directly to `done` — they auto-redirect to `in_review` status, triggering the admin approval workflow.

Ordering by `sort_order, name`. Index on `(is_active, department)` for the agent-facing filtered list query.

The slug should be auto-generated from name on save via `django.utils.text.slugify`, but only on creation (not on update, to prevent URL breakage).

### Seed Data

A data migration creates 11 default categories. Key categories with `requires_review=True`: Copywriting, QA Review. These are the categories where admin sign-off is expected before work is considered complete. The full seed list with colors, departments, and review flags is defined in `claude-spec.md` section 1.

### Existing Code Impact

The existing `TASK_CATEGORY_CHOICES` list at the top of `agent_scheduling.py` will be removed in a later migration (after the old CharField is dropped from AgentGlobalTask). Until then, both coexist.

---

## Section 2: AgentGlobalTask Model Changes

### What to Build

Extend `AgentGlobalTask` with three groups of new fields: client tagging, category FK, and recurrence fields. Also extend the status choices to include `in_review`.

### Client Tagging

Add a nullable FK to the `Client` model with `related_name='global_tasks'` and `on_delete=SET_NULL`. This replaces the existing page-level client filtering with per-task metadata. The `Client` model lives in `server/api/models/clients.py`.

### Category FK

Add `task_category_ref` as a nullable FK to the new `TaskCategory` model. This replaces the existing `task_category` CharField. The old CharField must persist through migration but is removed in the cleanup migration.

Naming it `task_category_ref` (not `task_category`) avoids collision with the existing CharField during the transition.

### Recurrence Fields

These fields directly replace the separate `RecurringTaskTemplate` model:

- `is_recurring` (BooleanField, default False) — the discriminator
- `recurrence_frequency` (CharField, nullable, choices: daily/weekly/biweekly/monthly/yearly/custom)
- `recurrence_days` (JSONField, nullable) — ISO weekday numbers for weekly patterns
- `recurrence_interval` (IntegerField, nullable, default 1) — "every N units"
- `recurrence_end_type` (CharField, nullable, choices: never/count/date)
- `recurrence_end_count` (IntegerField, nullable)
- `recurrence_end_date` (DateField, nullable)
- `recurrence_parent` (self FK, nullable, SET_NULL) — links instances to their template/first occurrence
- `recurrence_instance_number` (IntegerField, nullable) — which occurrence this is

### Status Extension

Change the `TaskStatus` TextChoices to include `IN_REVIEW = 'in_review', 'In Review'` between `IN_PROGRESS` and `DONE`.

### New Indexes

Add indexes on: `(agent, client)`, `(task_category_ref, status)`, `(recurrence_parent,)`, `(client, scheduled_date)`. The last one supports Split 06's client reporting queries.

---

## Section 3: ScheduledTaskLink Simplification

### What to Build

Replace the `GenericForeignKey` pattern on `ScheduledTaskLink` with a direct FK to `AgentGlobalTask`.

### Current State

`ScheduledTaskLink` currently uses `content_type` + `object_id` + `content_object` (GenericFK) to link time blocks to any task type. Now that we're unifying around `AgentGlobalTask`, this indirection is unnecessary.

### Migration Approach

Since the database is fresh, the GenericFK removal and new FK addition can happen in a single migration step:

1. Remove the GenericFK fields (`content_type`, `object_id`) and the `GenericForeignKey` attribute
2. Add a new `task` FK field (nullable) to ScheduledTaskLink pointing to AgentGlobalTask
3. Data migration: for existing links, populate `task` from the old `object_id` data (if any rows exist)
4. Update `unique_together` from `['content_type', 'object_id', 'agent']` to `['task', 'agent']`

This avoids the attribute name collision between the old `task = GenericForeignKey(...)` and the new `task` FK, since both are handled in the same migration.

Any links to non-AgentGlobalTask types (MarketingTask, ProjectTask) can be dropped — they'll be recreated through the new unified model.

---

## Section 4: Django Migrations

### Strategy

Four sequential migrations, all shipping in one deploy:

**Migration A — Schema additions:** Add all new fields to AgentGlobalTask (all nullable). Create the TaskCategory model. Replace ScheduledTaskLink's GenericFK fields with a direct `task` FK to AgentGlobalTask (remove `content_type`, `object_id`, `GenericForeignKey` attribute; add `task` FK; update `unique_together` to `['task', 'agent']`).

**Migration B — Data population:** Create seed TaskCategory records. Map existing `task_category` CharField values to the new `task_category_ref` FK. Convert active RecurringTaskTemplate records into AgentGlobalTask records with `is_recurring=True`. Populate ScheduledTaskLink's new `task` FK from any existing data.

The category mapping from old CharField values to new slugs is documented in `claude-spec.md` section 4. Key mappings: `'admin'→'administrative-ops'`, `'creative'→'design'`, `'coding'→'development'`, `'review'→'qa-review'`.

For RecurringTaskTemplate conversion: only convert `target_type='global'` and `is_active=True` templates. Map `recurrence_type` to the new frequency choices. Use `effective_until` for end date. Calculate initial `scheduled_date` using dateutil. Note: templates with `target_type='marketing_task'` or `'project_task'` are intentionally not migrated — those models are deprecated in later splits.

**Migration C — Constraint enforcement:** Add the new indexes (including `unique_together` on `(recurrence_parent, recurrence_instance_number)` to prevent duplicate JIT instances). No NOT NULL constraints needed (all new fields are nullable by design).

**Migration D — Cleanup:** Drop `recurring_source` FK from both `AgentGlobalTask` and `AgentTimeBlock` (these point to the soon-to-be-deleted `RecurringTaskTemplate`). Remove `RecurringTaskTemplate` model. Remove old `task_category` CharField from AgentGlobalTask. Remove `TASK_CATEGORY_CHOICES` constant.

All migrations must use `apps.get_model()` (never direct imports) and provide reverse functions.

---

## Section 5: JIT Recurring Task Generation

### What to Build

A service function that generates the next recurring task instance when a task is completed. This replaces the Celery Beat periodic generator.

### Trigger Point

The JIT function is called from the new `/complete/` endpoint on `AgentGlobalTaskViewSet`. It fires only when a task's status actually reaches `done` (not `in_review`).

### Next Date Calculation

Use `dateutil.rrule` to compute the next occurrence date:

1. Map `recurrence_frequency` to rrule frequency constants (daily→DAILY, weekly→WEEKLY, biweekly→WEEKLY with interval=2, monthly→MONTHLY, yearly→YEARLY)
2. Map `recurrence_days` (ISO weekday numbers) to rrule weekday constants
3. Create an rrule with the frequency, interval, optional weekday filter, and `dtstart=task.scheduled_date`
4. Call `rule.after(task.scheduled_date)` to get the next date
5. Check end conditions: if `end_type='date'` and next_date exceeds it, return None. If `end_type='count'` and instance_number has reached the count, return None.

### Instance Creation

Create a new `AgentGlobalTask` copying: agent, title, description, priority, client, task_category_ref, all recurrence fields. Set: `status='todo'`, `scheduled_date=calculated_next_date`, `recurrence_parent=original_parent_or_self`, `recurrence_instance_number=previous+1`.

### Race Condition Prevention

Use `select_for_update()` on the task in the `/complete/` action to prevent duplicate JIT instances from concurrent requests (e.g., double-click). Additionally, the `unique_together` constraint on `(recurrence_parent, recurrence_instance_number)` (added in Migration C) serves as a database-level safety net.

### Review-Required Interception

When a task in a `requires_review` category is set to `done`:
- If current status is NOT `in_review` → override to `in_review` (agent completing → auto-redirect)
- If current status IS `in_review` → allow `done` (admin approving the reviewed task)
- JIT generation fires only in the second case (actual completion)

This is implemented in the serializer's `validate_status` method and in the `complete` action.

---

## Section 6: API Layer — Serializers

### What to Build

Separate read and write serializers for `AgentGlobalTask`, a serializer for `TaskCategory`, and the `IsAdmin` permission class.

### Read/Write Serializer Split

Following DRF best practices from the research findings, use separate serializers:

- **AgentGlobalTaskReadSerializer:** Includes nested `task_category_detail` (full TaskCategory object), computed `client_name`, `is_overdue`, `time_block_title`. Used for GET requests.
- **AgentGlobalTaskWriteSerializer:** Accepts `task_category_ref` as a PK (UUID), `client` as a PK (UUID). Includes `validate_status` for review-required interception and `validate` for recurrence field consistency. Used for POST/PATCH.

The ViewSet's `get_serializer_class()` method selects based on action.

### TaskCategorySerializer

Standard ModelSerializer with all fields. `slug` is read-only (auto-generated). Used for both read and write since the shape is simple.

### IsAdmin Permission

New permission class in the permissions file (wherever `IsAnyAgent` lives). Checks `request.user.is_authenticated` and `request.user.role == 'admin'`.

### QuerySet Optimization

The ViewSet's `get_queryset()` must use `select_related('client', 'task_category_ref', 'time_block')` to avoid N+1 queries on the nested serializer fields.

---

## Section 7: API Layer — ViewSets & Routing

### What to Build

Modify `AgentGlobalTaskViewSet`, create `TaskCategoryViewSet`, remove `RecurringTaskTemplateViewSet`, and update URL routing.

### AgentGlobalTaskViewSet Changes

1. **Serializer selection:** Override `get_serializer_class()` to return read vs write serializer based on action
2. **New filters:** Add `client`, `task_category_id` (renamed from `task_category`), `is_recurring` to the existing filter set
3. **New action:** `@action(detail=True, methods=['post'], url_path='complete')` — marks task done, handles review interception, triggers JIT generation. Returns both the completed task and the new instance (if created). **Important:** The `complete` action must handle admin callers (who approve reviewed tasks) without assuming an `agent_profile` exists — check `request.user.role` and skip agent-specific lookups for admin users.
4. **QuerySet:** Add `select_related` for performance

### Function-Based View Updates

The `command_center` and `cross_client_tasks` function-based views (lines 285-458 of scheduling_views.py) must be updated:

1. **`_serialize_global_task` helper:** Currently hardcodes `'client_name': ''` and `'client_id': None`. Update to read from `task.client.name` / `task.client_id` (with null checks). Also update `task.task_category` references to use `task.task_category_ref`.
2. **`command_center`:** Update serializer references from old `AgentGlobalTaskSerializer` to the new read serializer. Update any `task_category` CharField references.
3. **`cross_client_tasks`:** Same updates. Additionally, `ScheduledTaskLink` queries using the GenericFK pattern (`link.task`) must be updated to use the new direct `task` FK (`link.task` as a real FK, which happens to keep the same attribute name after Migration A).
4. **Serializer usage:** These views can use `AgentGlobalTaskReadSerializer` for consistency, or continue with the `_serialize_global_task` helper (updated).

### TaskCategoryViewSet

Two separate ViewSets or one with conditional permissions:

- **Agent-facing** (registered at `/agent/schedule/task-categories/`): List-only, filtered by agent's department. Permission: `IsAuthenticated, IsAnyAgent`. Override `get_queryset()` to filter by `is_active=True` and the agent's department (look up via `request.user.agent_profile.department`).
- **Admin-facing** (registered at `/admin/task-categories/`): Full CRUD. Permission: `IsAuthenticated, IsAdmin`. Shows all categories including inactive.

### RecurringTaskTemplate Removal

Remove `RecurringTaskTemplateViewSet` from views. Remove its router registration from `urls.py`. Remove the `RecurringTaskTemplateSerializer`.

### URL Registration

In `server/api/urls.py`, the router already registers scheduling ViewSets. Add the new task-categories routes and remove the recurring-tasks route.

---

## Section 8: Celery Task Cleanup

### What to Build

Remove the periodic recurring task generator and its Celery Beat schedule.

### Remove

- The `generate_recurring_tasks()` function in `server/api/tasks/scheduling_tasks.py`
- Its `_should_generate_on_date()` helper (only used by this function)
- Its Celery Beat schedule entry in `server/server/settings.py` (line 326+, look for `generate-recurring-tasks` around line 383)
- Also check `server/settings.py` (line 5) which has a second `CELERY_BEAT_SCHEDULE` definition — clean up both locations

### Keep

- `generate_recurring_time_blocks()` — this generates `AgentTimeBlock` from `AgentRecurringBlock` templates, which is a separate system unrelated to task recurrence

---

## Section 9: Frontend Type Updates

### What to Build

Update TypeScript types in `client/lib/types/scheduling.ts` to match the new API shape.

### Changes

1. **GlobalTaskStatus:** Add `'in_review'` to the union type
2. **TaskCategoryItem:** New interface replacing the old `TaskCategory` string union. Fields: id, name, slug, color, icon, department, requires_review, is_active, sort_order.
3. **AgentGlobalTask:** Add fields: `client`, `client_name`, `task_category_ref`, `task_category_detail` (nested TaskCategoryItem), all recurrence fields, `is_overdue`
4. **CreateGlobalTaskRequest / UpdateGlobalTaskRequest:** Add the new writable fields
5. **Remove:** `RecurringTaskTemplate` interface, old `TaskCategory` union type, `CreateRecurringTaskRequest` / `UpdateRecurringTaskRequest`

### Backward Compatibility

Since this is a clean break (per interview), simply replace the types. No type aliases or deprecated exports needed.

---

## Section 10: Frontend API Updates

### What to Build

Update `client/lib/api/scheduling.ts` to add new endpoints, modify existing ones, and remove deprecated ones.

### New Methods

- `getTaskCategories(department?: string)` — GET `/agent/schedule/task-categories/` with optional department filter
- `createTaskCategory(data)` — POST `/admin/task-categories/`
- `updateTaskCategory(id, data)` — PATCH `/admin/task-categories/{id}/`
- `deleteTaskCategory(id)` — DELETE `/admin/task-categories/{id}/`
- `completeGlobalTask(id)` — POST `/agent/schedule/global-tasks/{id}/complete/` — returns `{ task, next_task }`

### Modified Methods

- `getGlobalTasks()` — add params: `client`, `task_category_id`, `is_recurring`
- `createGlobalTask()` — add fields: `client`, `task_category_ref`, recurrence fields
- `updateGlobalTask()` — same new fields

### Removed Methods

- `getRecurringTasks()`, `createRecurringTask()`, `updateRecurringTask()`, `deleteRecurringTask()` — all replaced by recurrence fields on global tasks

### React Query Hooks

If the codebase uses React Query hooks wrapping these API methods, update them too. Add `useTaskCategories()` hook. Update `useGlobalTasks()` to accept new filter params.

---

## Implementation Order

The sections above should be implemented in this order:

1. **Section 1** (TaskCategory model) — no dependencies
2. **Section 2** (AgentGlobalTask changes) — depends on TaskCategory existing
3. **Section 3** (ScheduledTaskLink) — depends on unified model
4. **Section 4** (Migrations) — codifies sections 1-3 into migration files
5. **Section 6** (Serializers + permissions) — depends on models
6. **Section 5** (JIT generation service) — depends on model + serializer patterns
7. **Section 7** (ViewSets + routing) — depends on serializers + JIT service
8. **Section 8** (Celery cleanup) — can be done after JIT is in place
9. **Section 9** (Frontend types) — depends on finalized API shape
10. **Section 10** (Frontend API) — depends on types

Sections 1-3 can be done together as a single "models" pass. Sections 9-10 can be done together as a single "frontend" pass.

---

## Risk Areas

1. **Migration ordering:** Migration D (cleanup) must run after B (data) and C (indexes). Django should handle this via dependency chains, but verify with `python manage.py showmigrations`.

2. **Review interception edge case:** If a task's category is changed from a non-review to a review category while in `in_progress` status, the next status transition should still be intercepted. The `validate_status` check on the serializer handles this because it reads the current `task_category_ref` at validation time.

3. **JIT date calculation:** `dateutil.rrule` with `count=2` and `dtstart=scheduled_date` will return the start date as the first occurrence. `rule.after(scheduled_date)` correctly skips it. Edge case: if `scheduled_date` is null, the JIT function should use `completed_at` date as the base.

4. **GenericFK removal:** Any code that creates `ScheduledTaskLink` using `content_type` and `object_id` must be updated to use the new direct `task` FK. Search for all usages of `ScheduledTaskLink` across the codebase.

5. **Department filtering:** The agent's department comes from `request.user.agent_profile.department`. Values are `'marketing'` and `'website'` (from `Agent.DEPARTMENT_CHOICES`). The `TaskCategory.department` choices must use these same values (`marketing`/`website`/`both`), not `developer`.

6. **`recurring_source` FK cleanup:** Both `AgentGlobalTask` and `AgentTimeBlock` have `recurring_source` FKs pointing to `RecurringTaskTemplate`. These must be dropped in Migration D *before* (or simultaneously with) deleting the `RecurringTaskTemplate` model, or Django will refuse the migration.

7. **Admin users on agent endpoints:** Admin users do not have an `agent_profile`. The `/complete/` action (used by admins to approve reviewed tasks) must not call `_get_agent(request)` unconditionally. Check `request.user.role` first.
