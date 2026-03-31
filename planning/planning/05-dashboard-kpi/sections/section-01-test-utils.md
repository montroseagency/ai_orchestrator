# section-01-test-utils

## Overview

This section establishes the data layer configuration and test utilities that all subsequent dashboard component sections depend on. It covers two concrete changes:

1. Update `useCommandCenter` in `client/lib/hooks/useScheduling.ts` to use `staleTime: 55_000` (was `30_000`).
2. Extend `client/test-utils/scheduling.tsx` with a `makeMockCommandCenterData()` factory function used by all component test suites.

All new tests live in `client/test-utils/scheduling.test.tsx`.

---

## Dependencies

None — this section has no upstream dependencies and must be completed before sections 02–05.

---

## Files to Modify

| File | Change |
|------|--------|
| `client/lib/hooks/useScheduling.ts` | Update `staleTime` in `useCommandCenter` from `30_000` to `55_000` |
| `client/test-utils/scheduling.tsx` | Add `makeMockCommandCenterData()` export; add `CommandCenterData`, `CommandCenterStats` to imports |
| `client/test-utils/scheduling.test.tsx` | Add `useCommandCenter` config tests; add `makeMockCommandCenterData` tests |

---

## Tests First

### `useCommandCenter` query config (in `client/test-utils/scheduling.test.tsx`)

These two tests verify the query options on the live hook via `renderHook`. They require `vi.mock('@/lib/api/scheduling', ...)` to resolve `schedulingApi.getCommandCenter` without a real server.

```typescript
describe('useCommandCenter query config', () => {
  it('has staleTime of 55_000')
  // Render the hook inside a QueryClientProvider, wait for isSuccess,
  // then inspect queryCache.findAll(['scheduling', 'command-center'])[0].options.staleTime === 55_000

  it('has refetchInterval of 60_000')
  // Same pattern; assert options.refetchInterval === 60_000
})
```

### `makeMockCommandCenterData` (in `client/test-utils/scheduling.test.tsx`)

```typescript
describe('makeMockCommandCenterData', () => {
  it('returns a complete CommandCenterData object')
  // date, time_blocks, todays_global_tasks, todays_client_tasks, stats all present

  it('stats contains all four required KPI fields')
  // total_active_tasks, completed_today, hours_blocked_today, active_clients

  it('includes a default time_block from createMockTimeBlock')
  // time_blocks has length 1; first element has start_time property

  it('includes a default global task from createMockGlobalTask')
  // todays_global_tasks has length 1; first element has status property

  it('applies top-level overrides')
  // Pass { date: '2026-04-01', time_blocks: [] }; assert date and empty array

  it('applies stats overrides')
  // Pass { stats: { total_active_tasks: 10, ... } }; assert 10

  it('returns independent objects on separate calls')
  // Mutate result a; assert result b.date unchanged
})
```

---

## Implementation Details

### 1. Update `staleTime` in `useCommandCenter`

**File:** `client/lib/hooks/useScheduling.ts` — the `useCommandCenter` function near line 279.

Change `staleTime: 30_000` to `staleTime: 55_000`. Everything else in the function stays the same.

**Why 55_000?** React Query's default `staleTime: 0` marks data stale immediately, which means both the `refetchInterval` timer and a `refetchOnWindowFocus` event can fire within milliseconds of each other when the user switches tabs, causing two identical network requests. Setting `staleTime` to just under the polling interval (55s < 60s) ensures a focus event finds the data "fresh" and skips the duplicate refetch, while the interval still fires on schedule.

The hook after the change:

```typescript
export function useCommandCenter() {
  return useQuery<CommandCenterData>({
    queryKey: SCHEDULE_KEYS.commandCenter,
    queryFn: () => schedulingApi.getCommandCenter(),
    staleTime: 55_000,
    refetchInterval: 60_000,
  });
}
```

### 2. Extend `client/test-utils/scheduling.tsx`

**Add to imports** at the top:

```typescript
import type {
  AgentTimeBlock,
  AgentGlobalTask,
  CommandCenterData,
  CommandCenterStats,
} from '@/lib/types/scheduling'
```

**Add `makeMockCommandCenterData` function** (insert before `renderWithQuery`):

```typescript
/**
 * Builds a complete CommandCenterData mock for page-level and integration tests.
 * Uses createMockTimeBlock() and createMockGlobalTask() internally.
 * Pass overrides to replace any top-level field.
 */
export function makeMockCommandCenterData(
  overrides?: Partial<CommandCenterData>
): CommandCenterData {
  const defaultStats: CommandCenterStats = {
    total_active_tasks: 5,
    completed_today: 2,
    hours_blocked_today: 4,
    active_clients: 3,
  }

  return {
    date: '2026-03-29',
    weekly_plan: null,
    time_blocks: [createMockTimeBlock()],
    todays_global_tasks: [createMockGlobalTask()],
    todays_client_tasks: [],
    overdue_tasks: [],
    upcoming_deadlines: [],
    stats: defaultStats,
    ...overrides,
  }
}
```

The function relies on the already-existing `createMockTimeBlock()` and `createMockGlobalTask()` in the same file — no new dependencies.

### 3. Extend `client/test-utils/scheduling.test.tsx`

**Add to imports** at the top:

```typescript
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
```

**Add a module-level mock** before the describe blocks:

```typescript
vi.mock('@/lib/api/scheduling', () => ({
  schedulingApi: {
    getCommandCenter: vi.fn().mockResolvedValue({
      // minimal valid CommandCenterData
      date: '2026-03-29',
      weekly_plan: null,
      time_blocks: [],
      todays_global_tasks: [],
      todays_client_tasks: [],
      overdue_tasks: [],
      upcoming_deadlines: [],
      stats: { total_active_tasks: 0, completed_today: 0, hours_blocked_today: 0, active_clients: 0 },
    }),
  },
}))
```

**Add the two describe blocks** (config tests + makeMockCommandCenterData tests) as detailed in the Tests section above.

---

## Relevant Types (for reference)

`CommandCenterData` (from `client/lib/types/scheduling.ts`):

```typescript
interface CommandCenterData {
  date: string;
  weekly_plan: WeeklyPlan | null;
  time_blocks: AgentTimeBlock[];
  todays_global_tasks: AgentGlobalTask[];
  todays_client_tasks: CrossClientTask[];
  overdue_tasks: CrossClientTask[];
  upcoming_deadlines: CrossClientTask[];
  stats: CommandCenterStats;
}

interface CommandCenterStats {
  total_active_tasks: number;
  completed_today: number;
  hours_blocked_today: number;
  active_clients: number;
}
```

---

## Acceptance Criteria

- [ ] `useCommandCenter` has `staleTime: 55_000` and `refetchInterval: 60_000`
- [ ] `makeMockCommandCenterData()` is exported from `client/test-utils/scheduling.tsx`
- [ ] `makeMockCommandCenterData()` accepts `Partial<CommandCenterData>` overrides
- [ ] `makeMockCommandCenterData()` returns objects with all required `CommandCenterData` fields populated
- [ ] Config tests pass: `has staleTime of 55_000` and `has refetchInterval of 60_000`
- [ ] All `makeMockCommandCenterData` tests pass
- [ ] No existing tests broken

---

## Implementation Status

**COMPLETE.** All changes have been applied and all new tests pass (27 tests added, 341 total, 1 pre-existing failure in an unrelated file).
