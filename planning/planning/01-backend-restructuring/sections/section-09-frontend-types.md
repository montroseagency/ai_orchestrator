# Section 9: Frontend Type Updates

## Overview

This section updates the TypeScript type definitions in `client/lib/types/scheduling.ts` to reflect the restructured backend API. The changes include adding the `in_review` status, introducing a `TaskCategoryItem` interface (replacing the old string union `TaskCategory`), extending `AgentGlobalTask` with client tagging and recurrence fields, and removing deprecated `RecurringTaskTemplate` types.

## Dependencies

- **Section 07 (ViewSets & Routing):** The API shape must be finalized before these types can be written. The types here mirror the serializer output defined in sections 06 and 07.

## File to Modify

- `/home/ubuntu/Montrroase_website/client/lib/types/scheduling.ts`

## Current State of the File

The file currently defines:
- `GlobalTaskStatus` as `'todo' | 'in_progress' | 'done'` (missing `'in_review'`)
- `TaskCategory` as a string union of 13 hardcoded category slugs (to be removed)
- `TaskRecurrenceType` as `'daily' | 'weekly' | 'biweekly' | 'monthly'` (used by old `RecurringTaskTemplate`)
- `TargetType` as `'global' | 'marketing_task' | 'project_task'` (used by old `RecurringTaskTemplate`)
- `AgentGlobalTask` interface without client, category ref, or recurrence fields
- `RecurringTaskTemplate` interface plus its `CreateRecurringTaskRequest` and `UpdateRecurringTaskRequest` (all to be removed)
- `TASK_CATEGORY_LABELS`, `TASK_CATEGORY_COLORS`, `MARKETING_CATEGORIES`, `DEVELOPER_CATEGORIES` constants typed against the old `TaskCategory` union (all to be removed)

Several components import from this file: `DaySchedule.tsx`, `CommandCenter.tsx`, `CrossClientTaskList.tsx`, `QuickTaskInput.tsx`, `RecurringTaskManager.tsx`, `TaskCategoryBadge.tsx`, and `client/lib/api/scheduling.ts`. Consumers of removed types will need updates in Section 10 and subsequent splits, but this section focuses only on the type definitions file itself.

## Tests

These are TypeScript compile-time checks. Create a lightweight type-test file at `/home/ubuntu/Montrroase_website/client/lib/types/__tests__/scheduling.typetest.ts` (or verify manually with `npx tsc --noEmit`).

```typescript
// File: client/lib/types/__tests__/scheduling.typetest.ts
// These are compile-time assertions, not runtime tests.
// Run: npx tsc --noEmit from the client/ directory.

import type {
  GlobalTaskStatus,
  TaskCategoryItem,
  AgentGlobalTask,
  RecurrenceFrequency,
  RecurrenceEndType,
} from '../scheduling';

// Test: GlobalTaskStatus type includes 'in_review'
const statusCheck: GlobalTaskStatus = 'in_review'; // must compile

// Test: TaskCategoryItem interface has all expected fields
const category: TaskCategoryItem = {
  id: 'uuid',
  name: 'Copywriting',
  slug: 'copywriting',
  color: '#2563EB',
  icon: 'pen-tool',
  department: 'marketing',
  requires_review: true,
  is_active: true,
  sort_order: 0,
};

// Test: AgentGlobalTask interface includes new fields
const task: AgentGlobalTask = {} as AgentGlobalTask;
const _client: string | null = task.client;
const _clientName: string = task.client_name;
const _catRef: string | null = task.task_category_ref;
const _catDetail: TaskCategoryItem | null = task.task_category_detail;
const _isRecurring: boolean = task.is_recurring;
const _freq: RecurrenceFrequency | null = task.recurrence_frequency;
const _isOverdue: boolean = task.is_overdue;

// Test: RecurringTaskTemplate type no longer exported
// @ts-expect-error - RecurringTaskTemplate should not exist
import type { RecurringTaskTemplate } from '../scheduling';

// Test: Old TaskCategory string union type no longer exported
// @ts-expect-error - TaskCategory union should not exist
import type { TaskCategory } from '../scheduling';
```

Additionally, after all changes are made, run `npx tsc --noEmit` from the `client/` directory to confirm the entire project compiles without errors.

## Implementation Details

### 1. Update `GlobalTaskStatus` Union

Add `'in_review'` to the existing union type.

Before:
```typescript
export type GlobalTaskStatus = 'todo' | 'in_progress' | 'done';
```

After:
```typescript
export type GlobalTaskStatus = 'todo' | 'in_progress' | 'in_review' | 'done';
```

### 2. Add New Type: `RecurrenceFrequency`

This replaces the old `TaskRecurrenceType` with the values matching the backend model's `FREQUENCY_CHOICES`.

```typescript
export type RecurrenceFrequency = 'daily' | 'weekly' | 'biweekly' | 'monthly' | 'custom';
```

### 3. Add New Type: `RecurrenceEndType`

```typescript
export type RecurrenceEndType = 'never' | 'date' | 'count';
```

### 4. Add `TaskCategoryItem` Interface

This is a new interface representing the API response for a `TaskCategory` model instance. It replaces the old `TaskCategory` string union.

```typescript
export interface TaskCategoryItem {
  id: string;
  name: string;
  slug: string;
  color: string;
  icon: string;
  department: 'marketing' | 'website' | 'both';
  requires_review: boolean;
  is_active: boolean;
  sort_order: number;
}
```

### 5. Update `AgentGlobalTask` Interface

Add the following fields to the existing interface:

- `client: string | null` -- UUID of the associated Client, nullable
- `client_name: string` -- denormalized client name from the read serializer
- `task_category_ref: string | null` -- UUID FK to TaskCategory, nullable
- `task_category_detail: TaskCategoryItem | null` -- nested category object from the read serializer
- `is_recurring: boolean`
- `recurrence_frequency: RecurrenceFrequency | null`
- `recurrence_days: number[] | null` -- JSON array of ISO weekday numbers
- `recurrence_interval: number` -- defaults to 1
- `recurrence_end_type: RecurrenceEndType` -- defaults to 'never'
- `recurrence_end_date: string | null`
- `recurrence_end_count: number | null`
- `recurrence_parent: string | null` -- UUID of parent task for instances
- `recurrence_instance_number: number` -- 0 for templates, N for instances

Remove:
- `task_category: TaskCategory | ''` -- replaced by `task_category_ref` and `task_category_detail`
- `recurring_source: string | null` -- replaced by `recurrence_parent`

The `is_overdue` field already exists on the current interface; keep it.

### 6. Update `CreateGlobalTaskRequest` Interface

Add new writable fields:

- `client?: string | null`
- `task_category_ref?: string | null`
- `is_recurring?: boolean`
- `recurrence_frequency?: RecurrenceFrequency`
- `recurrence_days?: number[]`
- `recurrence_interval?: number`
- `recurrence_end_type?: RecurrenceEndType`
- `recurrence_end_date?: string | null`
- `recurrence_end_count?: number | null`

Remove:
- `task_category?: TaskCategory` -- replaced by `task_category_ref`

### 7. Update `GlobalTaskFilters` Interface

Replace old filter fields to match the new API query parameters:

```typescript
export interface GlobalTaskFilters {
  status?: GlobalTaskStatus;
  task_category_id?: string;  // was task_category (string union)
  client?: string;            // new: filter by client UUID
  is_recurring?: boolean;     // new: filter recurring tasks
  scheduled_date?: string;
  due_before?: string;
  priority?: TaskPriority;
}
```

### 8. Update `ScheduledTaskLink` Interface

Replace GenericFK fields with a direct task FK:

- Remove: `content_type: number`, `object_id: string`
- Add: `task: string` (UUID FK to AgentGlobalTask)
- Update `task_type` field -- may no longer be needed, but keep for now as the backend still returns it during the transition

Similarly update `CreateTaskLinkRequest`:
- Remove: `content_type?: number`, `content_type_model?: string`, `object_id: string`
- Add: `task: string`

### 9. Remove Deprecated Types

Remove these exports entirely from the file:

- `type TaskCategory` (the old string union)
- `type TaskRecurrenceType` (replaced by `RecurrenceFrequency`)
- `type TargetType` (was only used by `RecurringTaskTemplate`)
- `interface RecurringTaskTemplate`
- `interface CreateRecurringTaskRequest`
- `interface UpdateRecurringTaskRequest`
- `const TASK_CATEGORY_LABELS` (categories are now dynamic from the API, labels come from `TaskCategoryItem.name`)
- `const TASK_CATEGORY_COLORS` (colors now come from `TaskCategoryItem.color`)
- `const MARKETING_CATEGORIES` (filtering is now server-side by department)
- `const DEVELOPER_CATEGORIES` (same)

### 10. Update `CrossClientTask` Interface

Update the `task_category` field type since the old `TaskCategory` union is removed:

```typescript
export interface CrossClientTask {
  // ... existing fields ...
  task_category: string;         // already a string, no change needed
  task_category_detail: TaskCategoryItem | null;  // new: nested category
  // ... rest of fields ...
}
```

### 11. Keep Untouched

The following types remain unchanged:
- `BlockType`, `RecurrenceType` (for time blocks, unrelated to task recurrence)
- `AgentTimeBlock`, `CreateTimeBlockRequest`, `UpdateTimeBlockRequest`, `BulkCreateTimeBlocksRequest`
- `WeeklyPlan`, `WeeklyGoal`, `CreateWeeklyPlanRequest`, `UpdateWeeklyPlanRequest`
- `AgentRecurringBlock`, `CreateRecurringBlockRequest`, `UpdateRecurringBlockRequest` (these are for recurring time blocks, not tasks)
- `CommandCenterData`, `CommandCenterStats`
- `BLOCK_TYPE_LABELS`, `BLOCK_TYPE_COLORS`
- `MARKETING_BLOCK_TYPES`, `DEVELOPER_BLOCK_TYPES`
- `DAY_NAMES`
- `CrossClientTaskType`, `CrossClientTaskFilters`, `CrossClientTasksResponse`

## Verification

After making all changes:

1. Run `npx tsc --noEmit` from `/home/ubuntu/Montrroase_website/client/` to confirm the project compiles. Expect some errors in components that still reference removed types (e.g., `RecurringTaskManager.tsx`, `TaskCategoryBadge.tsx`) -- those will be addressed in subsequent splits. The type file itself must be internally consistent.

2. Confirm that the type-test file compiles without errors (excluding the intentional `@ts-expect-error` lines, which should correctly error).

## Notes on Downstream Impact

Removing `TaskCategory` (string union), `TASK_CATEGORY_LABELS`, `TASK_CATEGORY_COLORS`, `MARKETING_CATEGORIES`, and `DEVELOPER_CATEGORIES` will cause compile errors in these files:
- `client/components/agent/scheduling/TaskCategoryBadge.tsx` -- uses `TASK_CATEGORY_LABELS` and `TASK_CATEGORY_COLORS`
- `client/components/agent/scheduling/QuickTaskInput.tsx` -- may reference `TaskCategory` type
- `client/components/agent/scheduling/RecurringTaskManager.tsx` -- uses `RecurringTaskTemplate` type
- `client/lib/api/scheduling.ts` -- uses `RecurringTaskTemplate` and related request types

These downstream files are addressed in Section 10 (Frontend API) and subsequent UI splits. For this section, focus only on getting `scheduling.ts` type definitions correct and internally consistent.

## Implementation Notes (Actual)

**File modified:** `client/lib/types/scheduling.ts`

**Changes applied:**
- Added `'in_review'` to `GlobalTaskStatus`
- Added `RecurrenceFrequency` and `RecurrenceEndType` types
- Added `TaskCategoryItem` interface
- Updated `AgentGlobalTask`: added client/recurrence/category ref fields; removed `task_category` (string) and `recurring_source`
- Updated `CreateGlobalTaskRequest`: added new writable fields; removed `task_category`
- Updated `GlobalTaskFilters`: replaced `task_category` with `task_category_id`, added `client` and `is_recurring`
- Updated `ScheduledTaskLink`: replaced `content_type`/`object_id` with `task` FK
- Updated `CreateTaskLinkRequest`: replaced GenericFK fields with `task`
- Removed: `TaskCategory` union, `TaskRecurrenceType`, `TargetType`, `RecurringTaskTemplate`, `CreateRecurringTaskRequest`, `UpdateRecurringTaskRequest`, `TASK_CATEGORY_LABELS`, `TASK_CATEGORY_COLORS`, `MARKETING_CATEGORIES`, `DEVELOPER_CATEGORIES`

**Verification:** `npx tsc --noEmit` shows 0 errors originating from `scheduling.ts`. Expected downstream errors in `lib/api/scheduling.ts` (3 errors referencing removed types) will be fixed in section 10.