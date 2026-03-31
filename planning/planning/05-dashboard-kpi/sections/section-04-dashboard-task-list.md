# Section 04: DashboardTaskList

## Overview

Implement `DashboardTaskList` — a merged, sortable task list that combines `todays_global_tasks` (checkable) and `todays_client_tasks` (display-only) from the command-center data. Global tasks support optimistic checkbox mutations with full cache-based rollback. The component is stateless with respect to data fetching — it receives both task arrays as props from `AgentDashboardPage`.

## Dependencies

- **section-01-test-utils** must be complete before writing tests. The test suite uses `createMockGlobalTask()` and `renderWithQuery()` from `client/test-utils/scheduling.tsx`, and `makeMockCommandCenterData()` which is added in section 01.
- `useUpdateGlobalTask()` already exists in `client/lib/hooks/useScheduling.ts` — do not modify it.
- `SCHEDULE_KEYS.commandCenter` (`['scheduling', 'command-center']`) is defined in `client/lib/hooks/useScheduling.ts` — import it for cache invalidation in mutation callbacks.

## Files to Create

```
client/components/agent/dashboard/DashboardTaskList.tsx
client/components/agent/dashboard/__tests__/DashboardTaskList.test.tsx
```

The `__tests__/` directory is new — create it. The `client/components/agent/dashboard/` directory is also new.

---

## Type Reference

From `client/lib/types/scheduling.ts`:

```typescript
// GlobalTaskStatus = 'todo' | 'in_progress' | 'in_review' | 'done'

interface AgentGlobalTask {
  id: string;
  title: string;
  status: GlobalTaskStatus;
  client_name: string;
  start_time: string | null;   // HH:MM:SS or null
  order: number;               // user-defined priority order
  // ...other fields not needed for display
}

interface CrossClientTask {
  id: string;
  title: string;
  status: string;
  client_name: string;
  // No checkbox — display only
}
```

---

## Component: DashboardTaskList

**File:** `client/components/agent/dashboard/DashboardTaskList.tsx`

### Props

```typescript
interface DashboardTaskListProps {
  globalTasks: AgentGlobalTask[];
  clientTasks: CrossClientTask[];
  agentType: string;  // e.g., 'marketing' — for constructing the portal deep-link
}
```

### Internal Unified List Item Type

Before rendering, merge both arrays into a single typed union:

```typescript
type UnifiedTask =
  | { source: 'global'; task: AgentGlobalTask }
  | { source: 'client'; task: CrossClientTask };
```

Both `AgentGlobalTask` and `CrossClientTask` have `id`, `title`, `status`, and `client_name`. Use these four fields for all display and sorting logic.

### Sort Order

Sort the merged list in this order:

1. **Status group** (ascending): `in_progress` (0) → `todo` / `in_review` (1) → `done` (2)
2. **Within a status group**: tasks with a non-null `start_time` come first, sorted ascending by `start_time` string (lexicographic works for `HH:MM:SS`)
3. **Tasks without `start_time`**: sorted by `order` field (only present on `AgentGlobalTask`; treat `CrossClientTask` `order` as 0) then by `id` as a tiebreaker

`CrossClientTask` has no `start_time` or `order` field — treat both as absent (sorts to the end of their status group, ordered by `id`).

### Rendering Structure

Render three visual sections: **"In Progress"**, **"To Do"**, and **"Done"**. Each section has a small heading label. Sections with zero tasks are hidden (do not render an empty section header).

Each row shows:
- Checkbox (only for `source === 'global'`) — checked when `task.status === 'done'`
- Task title — apply `line-through` and muted colour class when `status === 'done'`
- Client badge — shown when `client_name` is non-empty
- Status badge

"In Review" tasks fall into the "To Do" visual section (they share status group 1).

### Checkbox Mutation (Cache-Based Optimistic Update)

Use `useUpdateGlobalTask()` from `client/lib/hooks/useScheduling.ts`.

The mutation must be configured with cache-based optimistic update logic. The pattern:

**`onMutate`** — before the network request fires:
1. Call `queryClient.cancelQueries({ queryKey: SCHEDULE_KEYS.commandCenter })` to cancel any in-flight refetch
2. Snapshot the current cache: `const snapshot = queryClient.getQueryData<CommandCenterData>(SCHEDULE_KEYS.commandCenter)`
3. Apply the optimistic update to the cache via `queryClient.setQueryData(SCHEDULE_KEYS.commandCenter, ...)` — produce a new `CommandCenterData` where the matching task in `todays_global_tasks` has its `status` set to `'done'` (or toggled back to `'todo'` if already done)
4. Return `{ snapshot }` as the mutation context

**`onError`** — if the mutation fails:
1. Restore the snapshot: `queryClient.setQueryData(SCHEDULE_KEYS.commandCenter, context.snapshot)`
2. Show a toast error via `sonner`'s `toast.error()`

**`onSettled`** — after success or error:
1. Only invalidate if no other mutations for this key are in-flight: `if (!queryClient.isMutating({ mutationKey: ... })) { queryClient.invalidateQueries({ queryKey: SCHEDULE_KEYS.commandCenter }) }`

The `useUpdateGlobalTask()` mutation sends `PATCH /api/scheduling/global-tasks/{id}/` with `{ status: 'done' }` (or the toggled status).

### Empty State

When both `globalTasks` and `clientTasks` are empty arrays, render a simple empty state message (e.g., "No tasks for today.").

### Footer

Render a footer link: `"View All in Portal →"` linking to `/dashboard/agent/{agentType}/management/tasks/`.

### Wrapping

Wrap the component in `React.memo` to prevent unnecessary re-renders when `AgentDashboardPage` re-renders on the polling interval.

---

## Tests: DashboardTaskList

**File:** `client/components/agent/dashboard/__tests__/DashboardTaskList.test.tsx`

**Test setup pattern:**

```typescript
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'
import { screen, fireEvent, waitFor } from '@testing-library/react'
import { renderWithQuery } from '@/test-utils/scheduling'
import { createMockGlobalTask } from '@/test-utils/scheduling'
import { DashboardTaskList } from '../DashboardTaskList'

// Mock the hook module
vi.mock('@/lib/hooks/useScheduling', () => ({
  useUpdateGlobalTask: vi.fn(),
  SCHEDULE_KEYS: { commandCenter: ['scheduling', 'command-center'] },
}))
```

### Test Stubs

**Data merge and rendering:**

```typescript
it('renders all todays_global_tasks titles', () => { /* ... */ })
it('renders all todays_client_tasks titles', () => { /* ... */ })
it('tasks from both sources appear in a single list, not separate source sections', () => { /* ... */ })
```

**Sort order:**

```typescript
it('in_progress task appears before todo task in rendered output', () => { /* ... */ })
it('todo task appears before done task in rendered output', () => { /* ... */ })
it('within the same status group, task with earlier start_time appears first', () => { /* ... */ })
it('within the same status group, tasks without start_time appear after tasks with start_time', () => { /* ... */ })
it('tasks without start_time are ordered by order field', () => { /* ... */ })
```

**Done task styling:**

```typescript
it('tasks with status done have line-through styling class', () => { /* ... */ })
```

**Checkboxes:**

```typescript
it('AgentGlobalTask items render with a checkbox element', () => { /* ... */ })
it('CrossClientTask items render without a checkbox element', () => { /* ... */ })
it('checkbox for a todo task is unchecked', () => { /* ... */ })
it('checkbox for a done task is checked', () => { /* ... */ })
```

**Optimistic update:**

```typescript
it('clicking a checkbox immediately renders the task as done before mutation resolves', () => { /* ... */ })
it('clicking a checkbox calls useUpdateGlobalTask mutation with status done', () => { /* ... */ })
it('if the mutation fails, the task reverts to its original status', () => { /* ... */ })
it('on mutation error, a toast error is shown', () => { /* ... */ })
```

**Rollback:**

```typescript
it('on mutation failure, setQueryData is called with the snapshot from onMutate', () => { /* ... */ })
```

**Footer link:**

```typescript
it('View All in Portal link has correct href containing /management/tasks/', () => { /* ... */ })
```

**Empty state:**

```typescript
it('when both task arrays are empty, renders empty state text', () => { /* ... */ })
```

### Key Test Notes

- For optimistic update tests, configure the `useUpdateGlobalTask` mock to return a mutation object with a `mutateAsync` function that you can control (resolve/reject via a `Promise` you manage in the test).
- The `renderWithQuery` utility creates a fresh `QueryClient` — pre-seed the command center cache via `queryClient.setQueryData(SCHEDULE_KEYS.commandCenter, makeMockCommandCenterData({ ... }))` before rendering.
- For rollback tests, reject the mutateAsync promise after render and assert `queryClient.getQueryData(SCHEDULE_KEYS.commandCenter)` matches the pre-mutation snapshot.
- For toast error tests, mock `sonner`'s `toast.error` via `vi.mock('sonner', () => ({ toast: { error: vi.fn() } }))` and assert it was called after mutation failure.

---

## Acceptance Criteria

1. Global tasks render with a checkbox; cross-client tasks do not.
2. Sort order: `in_progress` → `todo`/`in_review` → `done`; within group by `start_time` then `order` then `id`.
3. Done tasks have `line-through` styling.
4. Checkbox click fires `useUpdateGlobalTask` with the new status.
5. Optimistic update applies immediately to the React Query cache (visible before server responds).
6. On mutation error: cache is restored from snapshot, toast error shown.
7. "View All in Portal →" link href contains `/management/tasks/`.
8. Empty state renders when both task arrays are empty.
9. Component is wrapped in `React.memo`.
