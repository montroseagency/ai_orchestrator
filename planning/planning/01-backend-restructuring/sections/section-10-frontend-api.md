I have all the context I need. Let me now generate the section content.

# Section 10: Frontend API Updates

## Overview

This section updates the frontend API layer in `client/lib/api/scheduling.ts` and the React Query hooks in `client/lib/hooks/useScheduling.ts` to align with the restructured backend endpoints. New methods are added for task category CRUD and task completion. Existing global task methods gain new filter and field support. Deprecated recurring task template methods are removed entirely.

**Depends on:** Section 9 (Frontend Type Updates) -- the new and updated TypeScript types (`TaskCategoryItem`, `CreateTaskCategoryRequest`, `UpdateTaskCategoryRequest`, updated `GlobalTaskFilters`, updated `CreateGlobalTaskRequest`, `CompleteGlobalTaskResponse`) must exist before this section can compile.

## Files to Modify

- `/home/ubuntu/Montrroase_website/client/lib/api/scheduling.ts` -- main API wrapper
- `/home/ubuntu/Montrroase_website/client/lib/hooks/useScheduling.ts` -- React Query hooks

## Tests

Since this is frontend TypeScript code, validation is done through type-checking (compilation) and verifying the correct endpoints/shapes. The tests below are expressed as verification criteria.

```typescript
// File: client/lib/api/__tests__/scheduling.test.ts (or inline verification)

// Test: getTaskCategories() calls correct endpoint with optional department param
//   - schedulingApi.getTaskCategories() should GET /agent/schedule/task-categories/
//   - schedulingApi.getTaskCategories('marketing') should GET /agent/schedule/task-categories/?department=marketing

// Test: createTaskCategory() POSTs to /admin/task-categories/
//   - schedulingApi.createTaskCategory({ name: 'Test', ... }) should POST /admin/task-categories/

// Test: updateTaskCategory() PATCHes to /admin/task-categories/{id}/
//   - schedulingApi.updateTaskCategory('uuid', { name: 'Updated' }) should PATCH /admin/task-categories/{uuid}/

// Test: deleteTaskCategory() DELETEs /admin/task-categories/{id}/
//   - schedulingApi.deleteTaskCategory('uuid') should DELETE /admin/task-categories/{uuid}/

// Test: completeGlobalTask(id) POSTs to /agent/schedule/global-tasks/{id}/complete/
//   - schedulingApi.completeGlobalTask('uuid') should POST /agent/schedule/global-tasks/{uuid}/complete/
//   - Return type should be CompleteGlobalTaskResponse (contains task and optional next_task)

// Test: getGlobalTasks() accepts client, task_category_id, is_recurring params
//   - schedulingApi.getGlobalTasks({ client: 'uuid', task_category_id: 'uuid', is_recurring: 'true' })
//     should serialize all params into the query string

// Test: createGlobalTask() sends new fields (client, task_category_ref, recurrence fields)
//   - The CreateGlobalTaskRequest type accepted by createGlobalTask must include these fields

// Test: getRecurringTasks/createRecurringTask/updateRecurringTask/deleteRecurringTask/generateRecurringTaskNow
//   no longer exported from schedulingApi

// Test: TypeScript compiles without errors after changes
```

## Implementation Details

### 1. Update Imports in `scheduling.ts`

The import block at the top of `/home/ubuntu/Montrroase_website/client/lib/api/scheduling.ts` must be updated to reflect the type changes from Section 9.

**Remove** from imports:
- `RecurringTaskTemplate`
- `CreateRecurringTaskRequest`
- `UpdateRecurringTaskRequest`

**Add** to imports:
- `TaskCategoryItem`
- `CreateTaskCategoryRequest`
- `UpdateTaskCategoryRequest`
- `CompleteGlobalTaskResponse`

The existing imports for `AgentGlobalTask`, `CreateGlobalTaskRequest`, `UpdateGlobalTaskRequest`, and `GlobalTaskFilters` remain but reference the updated type definitions from Section 9 (which now include new fields like `client`, `task_category_ref`, `task_category_id`, `is_recurring`, and recurrence fields).

### 2. Add Task Category Methods to `schedulingApi`

Add a new section in the `schedulingApi` object between the existing Global Tasks section and the Scheduled Task Links section. These methods target two different URL prefixes: agent-facing (read-only list) and admin-facing (full CRUD).

**`getTaskCategories(department?: string)`**
- Endpoint: `GET /agent/schedule/task-categories/`
- If `department` is provided, append it as a query param: `?department=marketing`
- Returns: `TaskCategoryItem[]`
- Use the existing `buildParams` helper to construct the query string
- Handle the response the same way as other list endpoints: check for array or `results` key

**`createTaskCategory(data: CreateTaskCategoryRequest)`**
- Endpoint: `POST /admin/task-categories/`
- Note the different URL prefix (`/admin/` not `/agent/schedule/`)
- Returns: `TaskCategoryItem`
- Sends JSON body

**`updateTaskCategory(id: string, data: UpdateTaskCategoryRequest)`**
- Endpoint: `PATCH /admin/task-categories/{id}/`
- Returns: `TaskCategoryItem`
- Sends JSON body

**`deleteTaskCategory(id: string)`**
- Endpoint: `DELETE /admin/task-categories/{id}/`
- Returns: `void`

### 3. Add `completeGlobalTask` Method

Add within the Global Tasks section of `schedulingApi`.

**`completeGlobalTask(id: string)`**
- Endpoint: `POST /agent/schedule/global-tasks/{id}/complete/`
- No request body needed
- Returns: `CompleteGlobalTaskResponse` -- this is defined in Section 9 as an object containing `task` (the completed `AgentGlobalTask`) and optionally `next_task` (the newly created recurring instance, if applicable, also an `AgentGlobalTask` or `null`)
- Method: POST with no body (just the action trigger)

### 4. Update Existing Global Task Methods

The method signatures for `getGlobalTasks`, `createGlobalTask`, and `updateGlobalTask` do not need code changes because they already accept the type-parameterized request/filter objects. The expanded fields come from the updated types in Section 9:

- `GlobalTaskFilters` gains: `client?: string`, `task_category_id?: string`, `is_recurring?: string`
- `CreateGlobalTaskRequest` gains: `client?: string`, `task_category_ref?: string`, plus all recurrence fields (`is_recurring`, `recurrence_frequency`, `recurrence_days`, `recurrence_interval`, `recurrence_end_type`, `recurrence_end_count`, `recurrence_end_date`)
- `UpdateGlobalTaskRequest` extends `Partial<CreateGlobalTaskRequest>` so it picks up the new fields automatically

The existing method bodies (`getGlobalTasks`, `createGlobalTask`, `updateGlobalTask`) pass through the data/filters unchanged to `ApiService.request` and `buildParams`, so no code changes are required in the method implementations themselves -- only the type imports matter.

### 5. Remove Recurring Task Template Methods

Remove the entire "Recurring Task Templates" section from `schedulingApi` (currently lines 179-210 in the file). This includes:

- `getRecurringTasks`
- `createRecurringTask`
- `updateRecurringTask`
- `deleteRecurringTask`
- `generateRecurringTaskNow`

These are fully replaced by the recurrence fields on global tasks and the `completeGlobalTask` action.

### 6. Update React Query Hooks in `useScheduling.ts`

File: `/home/ubuntu/Montrroase_website/client/lib/hooks/useScheduling.ts`

**Update imports:**
- Remove: `CreateRecurringTaskRequest`, `UpdateRecurringTaskRequest`
- Add: `TaskCategoryItem`, `CreateTaskCategoryRequest`, `UpdateTaskCategoryRequest`, `CompleteGlobalTaskResponse`

**Add to `SCHEDULE_KEYS`:**
```typescript
taskCategories: {
  all: ['scheduling', 'task-categories'] as const,
  list: (department?: string) => ['scheduling', 'task-categories', 'list', department] as const,
},
```

**Add new hooks:**

`useTaskCategories(department?: string)` -- calls `schedulingApi.getTaskCategories(department)`, returns `TaskCategoryItem[]`, stale time 60 seconds (categories change rarely).

`useCreateTaskCategory()` -- mutation calling `schedulingApi.createTaskCategory(data)`, on success invalidates `SCHEDULE_KEYS.taskCategories.all`.

`useUpdateTaskCategory()` -- mutation calling `schedulingApi.updateTaskCategory(id, data)` with `{ id: string; data: UpdateTaskCategoryRequest }` input shape (matches the existing pattern used by `useUpdateGlobalTask`), on success invalidates `SCHEDULE_KEYS.taskCategories.all`.

`useDeleteTaskCategory()` -- mutation calling `schedulingApi.deleteTaskCategory(id)`, on success invalidates `SCHEDULE_KEYS.taskCategories.all`.

`useCompleteGlobalTask()` -- mutation calling `schedulingApi.completeGlobalTask(id)`, on success invalidates `SCHEDULE_KEYS.globalTasks.all` and `SCHEDULE_KEYS.commandCenter` (completing a task affects both the task list and command center stats).

**Remove hooks:**
- `useRecurringTasks`
- `useCreateRecurringTask`
- `useUpdateRecurringTask`
- `useDeleteRecurringTask`
- `useGenerateRecurringTaskNow`

**Remove from `SCHEDULE_KEYS`:**
- `recurringTasks` key group

### 7. Update Components That Import Removed Hooks/Methods

The following components currently import from `schedulingApi` or `useScheduling` and may reference removed methods. These are noted for awareness but full component refactoring is out of scope for this section (it belongs in later UI splits):

- `/home/ubuntu/Montrroase_website/client/components/agent/scheduling/RecurringTaskManager.tsx` -- uses `useRecurringTasks`, `useCreateRecurringTask`, `useUpdateRecurringTask`, `useDeleteRecurringTask`, `useGenerateRecurringTaskNow`. This component will need a full rewrite in a later split. For now, after removing the hooks, this file will have compilation errors. The implementer should either:
  - (a) Comment out the component body with a TODO note, or
  - (b) Leave it and accept the build error until the UI split addresses it

The other component files (`DaySchedule.tsx`, `CommandCenter.tsx`, `ScheduleCalendar.tsx`) use `schedulingApi` for non-removed methods and should remain unaffected.

## Implementation Checklist

1. [x] Update type imports in `client/lib/api/scheduling.ts` (remove old, add new)
2. [x] Add `getTaskCategories`, `createTaskCategory`, `updateTaskCategory`, `deleteTaskCategory` methods to `schedulingApi`
3. [x] Add `completeGlobalTask` method to `schedulingApi`
4. [x] Remove the five recurring task template methods from `schedulingApi`
5. [x] Update type imports in `client/lib/hooks/useScheduling.ts`
6. [x] Add `taskCategories` to `SCHEDULE_KEYS`
7. [x] Add `useTaskCategories`, `useCreateTaskCategory`, `useUpdateTaskCategory`, `useDeleteTaskCategory` hooks
8. [x] Add `useCompleteGlobalTask` hook
9. [x] Remove `recurringTasks` from `SCHEDULE_KEYS`
10. [x] Remove `useRecurringTasks`, `useCreateRecurringTask`, `useUpdateRecurringTask`, `useDeleteRecurringTask`, `useGenerateRecurringTaskNow` hooks
11. [x] Stub `RecurringTaskManager.tsx` with TODO for future UI rewrite
12. [x] Verify TypeScript compiles without errors (`npx tsc --noEmit` from the `client/` directory)

## Actual Implementation Notes

- **Additional files fixed**: `CrossClientTaskList.tsx`, `DaySchedule.tsx`, `MobileAgendaView.tsx`, `QuickTaskInput.tsx`, `CommandCenter.tsx` all had references to removed constants (`TASK_CATEGORY_COLORS`, `TASK_CATEGORY_LABELS`, `MARKETING_CATEGORIES`, `DEVELOPER_CATEGORIES`) and old types (`TaskCategory`). These were replaced with dynamic `useTaskCategories` hook calls and `task_category_detail?.color` lookups.
- **ScheduledTaskLink FK change**: `CreateTaskLinkRequest` now uses `task: string` instead of `content_type`/`object_id`. Updated all `createTaskLink.mutateAsync` calls in `DaySchedule.tsx` and `CommandCenter.tsx`.
- **TaskCategoryBadge API**: Now accepts `category?: TaskCategoryItem | null` or `categoryName?: string` / `categoryColor?: string`. Components passing string category used `categoryName` prop.
- Commit: `00d6b425c23084d82a6f5c236d86725a7273bce0`