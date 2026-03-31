# Section 04 — Data Hook: `useSchedulingEngine`

## Overview

This section implements the data layer for the interactive scheduling calendar. All server communication, caching, optimistic updates, and WebSocket subscription are contained in a single hook at `client/lib/hooks/useSchedulingEngine.ts`. Calendar components do not call React Query or the API directly — they consume this hook exclusively.

**Position in the implementation order:** Batch 2 (parallel with `section-03-dayschedule-refactor`). Depends on:
- `section-01-test-utils` — provides `createMockTimeBlock`, `createMockGlobalTask`, `renderWithQuery` used in tests
- `section-02-shared-utils` — provides `isoDateToWeekDays` used inside the hook to compute `weekDays`

This section is a prerequisite for sections 05, 06, 07, 08, 10, and 12.

---

## Files To Create

| File | Action |
|------|--------|
| `client/lib/hooks/useSchedulingEngine.ts` | Create new |
| `client/lib/hooks/useSchedulingEngine.test.ts` | Create new (tests alongside hook) |

No existing files are modified by this section.

---

## Background and Codebase Context

### Existing API Layer

All API methods needed already exist in `client/lib/api/scheduling.ts` as `schedulingApi.*`:

- `schedulingApi.getTimeBlocks(params?)` — accepts `{ date?, start?, end?, block_type? }`, returns `AgentTimeBlock[]`
- `schedulingApi.createTimeBlock(data)` — returns `AgentTimeBlock`
- `schedulingApi.updateTimeBlock(id, data)` — PATCH, returns `AgentTimeBlock`
- `schedulingApi.deleteTimeBlock(id)` — returns void
- `schedulingApi.getGlobalTasks(filters?)` — accepts `GlobalTaskFilters`, returns `AgentGlobalTask[]`
- `schedulingApi.updateGlobalTask(id, data)` — PATCH, returns `AgentGlobalTask`
- `schedulingApi.completeGlobalTask(id)` — returns `CompleteGlobalTaskResponse`

### Existing Types

From `client/lib/types/scheduling.ts`:

```typescript
interface AgentTimeBlock {
  id: string;
  date: string;          // YYYY-MM-DD
  start_time: string;    // HH:MM:SS
  end_time: string;      // HH:MM:SS
  title: string;
  color: string;
  client: string | null;
  client_name: string;
  duration_minutes: number;
  is_completed: boolean;
  // ...more fields
}

interface AgentGlobalTask {
  id: string;
  title: string;
  priority: TaskPriority;           // 'low' | 'medium' | 'high'
  due_date: string | null;
  scheduled_date: string | null;
  time_block: string | null;        // FK to TimeBlock id
  start_time: string | null;
  end_time: string | null;
  is_overdue: boolean;
  // ...more fields
}

interface GlobalTaskFilters {
  scheduled_date?: string;
  due_before?: string;
  priority?: TaskPriority;
  // ...more fields
  // NOTE: time_block filter does not exist in this interface —
  // filter unscheduled tasks by checking time_block === null client-side
}
```

### Existing Query Keys

Import from `client/lib/hooks/useScheduling.ts` (the existing hook file):

```typescript
import { SCHEDULE_KEYS } from '@/lib/hooks/useScheduling';

SCHEDULE_KEYS.timeBlocks.all       // ['scheduling', 'time-blocks']
SCHEDULE_KEYS.timeBlocks.list(p)   // ['scheduling', 'time-blocks', 'list', p]
SCHEDULE_KEYS.globalTasks.all      // ['scheduling', 'global-tasks']
SCHEDULE_KEYS.globalTasks.list(f)  // ['scheduling', 'global-tasks', 'list', f]
```

### WebSocket Pattern

Use `useSocket` from `client/lib/socket-context.tsx` (not `client/lib/hooks/useSocket.ts`). The socket-context version is the shared context provider already mounted in the app tree.

```typescript
import { useSocket } from '@/lib/socket-context';

const { on, off } = useSocket();
```

### Shared Utility

Import `isoDateToWeekDays` from the section-02 utility (must be completed first):

```typescript
import { isoDateToWeekDays } from '@/components/portal/calendar/utils/timeUtils';
```

---

## Time Slot Type

Define a local `TimeSlot` type at the top of the hook file for use by mutations:

```typescript
interface TimeSlot {
  date: string;    // YYYY-MM-DD
  hour: number;
  minute: number;
}
```

---

## Hook Signature

```typescript
// client/lib/hooks/useSchedulingEngine.ts
'use client';

export function useSchedulingEngine(agentType?: string, initialDate?: string) {
  // Returns:
  // timeBlocks: AgentTimeBlock[]
  // todayTasks: AgentGlobalTask[]
  // overdueTasks: AgentGlobalTask[]
  // isLoading: boolean
  // selectedDate: string
  // setSelectedDate: (date: string) => void
  // viewMode: 'day' | 'week'
  // setViewMode: (mode: 'day' | 'week') => void
  // weekDays: string[]           -- Mon–Fri ISO dates for the week containing selectedDate
  // scheduleTask: (task: AgentGlobalTask, slot: TimeSlot) => void
  // moveBlock: (blockId: string, newSlot: TimeSlot) => void
  // moveBlockToDay: (blockId: string, newDate: string, newSlot: TimeSlot) => void
  // resizeBlock: (blockId: string, newEndTime: string) => void
  // unscheduleBlock: (blockId: string) => void
  // completeTask: (taskId: string) => void
  // dropToAllDay: (taskId: string, date: string) => void
}
```

---

## Queries

### Time Blocks Query

Fetches blocks for the selected date range. Day view: single `date` param. Week view: `start`/`end` params (Monday–Friday).

```typescript
// Day view
schedulingApi.getTimeBlocks({ date: selectedDate })

// Week view
schedulingApi.getTimeBlocks({ start: weekDays[0], end: weekDays[4] })
```

Config: `staleTime: 30_000`, `refetchInterval: 60_000`.

Query key includes the current params object so that changing `selectedDate` or `viewMode` automatically triggers a re-fetch.

### Global Tasks Queries

Two separate `useQuery` calls, both with `staleTime: 30_000` and `refetchInterval: 60_000`:

**Today's tasks** — tasks assigned to the selected date but not yet placed in a time block. Fetch with `schedulingApi.getGlobalTasks({ scheduled_date: selectedDate })`, then filter the result client-side: keep only tasks where `task.time_block === null`.

**Overdue tasks** — tasks past due or with no scheduled date, not placed in a time block. Fetch with `schedulingApi.getGlobalTasks({ due_before: today })`, then filter client-side: keep tasks where `task.time_block === null`. `today` is the current date as `YYYY-MM-DD` (compute once outside the query function with `new Date().toISOString().slice(0, 10)`).

Expose the filtered results as `todayTasks` and `overdueTasks`. The raw query data is not exported.

---

## Mutations

All seven mutations follow the same optimistic update pattern:

```
onMutate  → cancelQueries → snapshot → apply optimistic state → return snapshot
onError   → restore snapshot + toast.error(message)
onSettled → if queryClient.isMutating({ mutationKey }) === 1, invalidate affected queries
```

The `isMutating` check defers cache invalidation until the last concurrent mutation of that type has settled, preventing flicker when mutations overlap.

Use `toast` from `react-hot-toast` (already in the project) for error notifications.

### `scheduleTask(task, slot)`

Creates a new time block and links the task to it.

- `mutationKey: ['timeBlocks']`
- API calls (sequential in `mutationFn`):
  1. `schedulingApi.createTimeBlock({ date: slot.date, start_time, end_time, title: task.title, client: task.client, block_type: 'deep_work', color: task.task_category_detail?.color ?? '#6366f1' })`
     - `start_time` = `minutesToTime(slot.hour * 60 + slot.minute)` + ':00'
     - `end_time` = start + 60 minutes (default 1-hour block)
  2. `schedulingApi.updateGlobalTask(task.id, { time_block: newBlock.id, scheduled_date: slot.date })`
- Optimistic `onMutate`: add a temporary block (with a generated temp id) to `SCHEDULE_KEYS.timeBlocks.list(...)` cache; remove the task from `todayTasks`/`overdueTasks` cache.
- `onError`: restore both snapshots.
- `onSettled`: invalidate `SCHEDULE_KEYS.timeBlocks.all` and `SCHEDULE_KEYS.globalTasks.all`.

### `moveBlock(blockId, newSlot)`

Repositions an existing block within the same day.

- `mutationKey: ['timeBlocks']`
- `mutationFn`: `schedulingApi.updateTimeBlock(blockId, { start_time, end_time })`
  - Preserve original duration: `duration = original.duration_minutes`; `end_time = minutesToTime(newStartMinutes + duration)`
- Optimistic `onMutate`: update the block's `start_time` and `end_time` in cache.
- `onSettled`: invalidate `SCHEDULE_KEYS.timeBlocks.all`.

### `moveBlockToDay(blockId, newDate, newSlot)`

Cross-day block move.

- `mutationKey: ['timeBlocks']`
- `mutationFn`: `schedulingApi.updateTimeBlock(blockId, { date: newDate, start_time, end_time })`
- Optimistic `onMutate`: remove block from source date's cache entry, add to target date's cache entry with updated date/times.
- `onSettled`: invalidate `SCHEDULE_KEYS.timeBlocks.all`.

### `resizeBlock(blockId, newEndTime)`

Updates only the end time of a block.

- `mutationKey: ['timeBlocks']`
- `mutationFn`: `schedulingApi.updateTimeBlock(blockId, { end_time: newEndTime })`
- Minimum duration enforced in `SchedulingEngine` before calling this mutation (15 minutes). The hook does not re-enforce it.
- Optimistic `onMutate`: update `end_time` (and `duration_minutes`) in cache.
- `onSettled`: invalidate `SCHEDULE_KEYS.timeBlocks.all`.

### `unscheduleBlock(blockId)`

Removes the time block assignment from a task, returning it to the backlog.

- `mutationKey: ['timeBlocks']`
- `mutationFn` (sequential):
  1. Fetch the linked task id from cache (the block's associated global task)
  2. `schedulingApi.deleteTimeBlock(blockId)`
  3. `schedulingApi.updateGlobalTask(taskId, { time_block: null, scheduled_date: null, start_time: null, end_time: null })`
- Optimistic `onMutate`: remove block from cache; add the task back to `todayTasks` cache.
- `onSettled`: invalidate both `SCHEDULE_KEYS.timeBlocks.all` and `SCHEDULE_KEYS.globalTasks.all`.

### `completeTask(taskId)`

Marks a task as completed and removes it from the backlog.

- `mutationKey: ['globalTasks']`
- `mutationFn`: `schedulingApi.completeGlobalTask(taskId)`
- Optimistic `onMutate`: remove task from `todayTasks` and `overdueTasks` in cache.
- `onSettled`: invalidate `SCHEDULE_KEYS.globalTasks.all`.

### `dropToAllDay(taskId, date)`

Assigns a task to a date as an all-day item (no specific time block).

- `mutationKey: ['globalTasks']`
- `mutationFn`: `schedulingApi.updateGlobalTask(taskId, { scheduled_date: date, time_block: null, start_time: null, end_time: null })`
- Optimistic `onMutate`: remove from backlog sections in cache; the task will appear in `AllDayHeader` after invalidation.
- `onSettled`: invalidate `SCHEDULE_KEYS.globalTasks.all`.

---

## WebSocket Subscription

Inside the hook, add a `useEffect` that subscribes to realtime events using the `useSocket` context:

```typescript
useEffect(() => {
  const handleTimeBlockEvent = () => {
    queryClient.invalidateQueries({ queryKey: SCHEDULE_KEYS.timeBlocks.all });
  };
  const handleTaskEvent = () => {
    queryClient.invalidateQueries({ queryKey: SCHEDULE_KEYS.globalTasks.all });
  };

  on('time_block_updated', handleTimeBlockEvent);
  on('time_block_created', handleTimeBlockEvent);
  on('time_block_deleted', handleTimeBlockEvent);
  on('global_task_updated', handleTaskEvent);

  return () => {
    off('time_block_updated', handleTimeBlockEvent);
    off('time_block_created', handleTimeBlockEvent);
    off('time_block_deleted', handleTimeBlockEvent);
    off('global_task_updated', handleTaskEvent);
  };
}, [on, off, queryClient]);
```

---

## State Management

```typescript
const today = new Date().toISOString().slice(0, 10);
const [selectedDate, setSelectedDate] = useState(initialDate ?? today);
const [viewMode, setViewMode] = useState<'day' | 'week'>('day');

// Derived — recomputed when selectedDate changes
const weekDays = useMemo(() => isoDateToWeekDays(selectedDate), [selectedDate]);
```

`isLoading` is `true` when either the time blocks query or the global tasks queries are in their initial loading state (`timeBlocksQuery.isLoading || todayTasksQuery.isLoading || overdueTasksQuery.isLoading`).

---

## Tests

File: `client/lib/hooks/useSchedulingEngine.test.ts`

Use `renderHook` from `@testing-library/react` with a `QueryClientProvider` wrapper. Mock all API calls with `vi.mock('@/lib/api/scheduling', ...)`. Mock the socket context with `vi.mock('@/lib/socket-context', ...)`.

Use `createMockTimeBlock` and `createMockGlobalTask` from `client/test-utils/scheduling.tsx` (section-01).

### Query Tests

```typescript
// Stub signatures — implement with vi.fn() returns:

it('fetches getTimeBlocks with selected date on mount')
// verify schedulingApi.getTimeBlocks called with { date: today }

it('fetches getGlobalTasks with scheduled_date filter for today tasks')
// verify schedulingApi.getGlobalTasks called with { scheduled_date: today }

it('fetches getGlobalTasks with due_before filter for overdue tasks')
// verify schedulingApi.getGlobalTasks called with { due_before: today }

it('filters todayTasks to only tasks where time_block === null')
// mock returns tasks with mixed time_block values; expect only null ones in result

it('setSelectedDate triggers re-fetch of timeBlocks for new date')
// call result.current.setSelectedDate('2026-03-30'); verify new query fired

it('setViewMode week triggers fetch with start/end params instead of date')
// call result.current.setViewMode('week'); verify getTimeBlocks called with { start, end }
```

### Mutation Tests

```typescript
it('scheduleTask calls createTimeBlock with correct date, start_time, end_time, title, client')
// Verify args derived from task + slot

it('scheduleTask calls updateGlobalTask with time_block: newBlock.id after block creation')
// Verify sequential call order

it('scheduleTask optimistically adds block to cache before API resolves')
// Use delayed mock; check cache state before resolution

it('scheduleTask rolls back optimistic update when createTimeBlock rejects')
// Mock rejection; verify cache restored

it('moveBlock calls updateTimeBlock with new start_time and end_time, preserving duration')

it('moveBlock optimistically updates cache position before API resolves')

it('resizeBlock calls updateTimeBlock with new end_time only')
// Verify only end_time in patch body

it('unscheduleBlock calls deleteTimeBlock and updateGlobalTask with null fields')

it('completeTask calls schedulingApi.completeGlobalTask and removes task from todayTasks cache')

it('dropToAllDay calls updateGlobalTask with scheduled_date and null time_block/start_time/end_time')
```

### WebSocket Test

```typescript
it('invalidates timeBlocks queries when time_block_updated socket event fires')
// Trigger the mocked socket on() callback; verify queryClient.invalidateQueries called
// with SCHEDULE_KEYS.timeBlocks.all
```

---

## Implementation Notes

- The hook is a `'use client'` module (add the directive at the top of the file).
- `minutesToTime` is imported from `client/components/portal/calendar/utils/timeUtils.ts` (section-02). Do not redefine it.
- Do not add a `time_block` filter to `GlobalTaskFilters` — that type is shared and the filter isn't supported by the backend. Filter client-side after fetching.
- The `agentType` parameter is accepted by the hook signature but is not used in this section. It is passed down for future use by category filtering. Leave it as an unused parameter for now.
- Temp ids for optimistic blocks: use `crypto.randomUUID()` or `'temp-' + Date.now()`.
- The `onMutate` snapshot should capture both the time blocks cache and the global tasks cache where applicable, so `onError` can restore both in a single callback.
