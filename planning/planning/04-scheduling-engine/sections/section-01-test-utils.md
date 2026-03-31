# Section 01 — Test Utilities

## Overview

This section creates the shared testing infrastructure for the entire scheduling engine feature. Nothing in the scheduling feature can be tested without these utilities, so this is a Batch 1 task — it runs in parallel with `section-02-shared-utils` and has no dependencies of its own.

The deliverable is a single file: `client/test-utils/scheduling.tsx`.

---

## What to Build

**File:** `client/test-utils/scheduling.tsx`

This file exports four things:

1. `createMockTimeBlock(overrides?)` — factory for `AgentTimeBlock` test fixtures
2. `createMockGlobalTask(overrides?)` — factory for `AgentGlobalTask` test fixtures
3. `mockUseSchedulingEngine(overrides?)` — returns a complete mock of the `useSchedulingEngine` hook return value
4. `renderWithQuery(ui)` — renders a React component wrapped in a fresh `QueryClientProvider`

These four exports are used by every subsequent section that involves components or hooks. Writing them first prevents test brittleness: when the `AgentTimeBlock` or `AgentGlobalTask` types change, you only fix the factory in one place.

---

## Background: Relevant Types

The factories must produce values that satisfy these interfaces (from `client/lib/types/scheduling.ts`):

**`AgentTimeBlock`** required fields:
- `id: string`
- `agent: string`
- `date: string` — `"YYYY-MM-DD"`
- `start_time: string` — `"HH:MM:SS"`
- `end_time: string` — `"HH:MM:SS"`
- `block_type: BlockType`
- `title: string`
- `color: string`
- `client: string | null`
- `client_name: string`
- `notes: string`
- `recurring_source: string | null`
- `is_completed: boolean`
- `duration_minutes: number`
- `created_at: string`
- `updated_at: string`

**`AgentGlobalTask`** required fields:
- `id: string`
- `agent: string`
- `title: string`
- `description: string`
- `status: GlobalTaskStatus`
- `priority: TaskPriority`
- `client: string | null`
- `client_name: string`
- `task_category_ref: string | null`
- `task_category_detail: TaskCategoryItem | null`
- `due_date: string | null`
- `scheduled_date: string | null`
- `time_block: string | null`
- `time_block_title: string`
- `estimated_minutes: number | null`
- `start_time: string | null`
- `end_time: string | null`
- `order: number`
- `is_recurring: boolean`
- `recurrence_frequency: RecurrenceFrequency | null`
- `recurrence_days: number[] | null`
- `recurrence_interval: number`
- `recurrence_end_type: RecurrenceEndType`
- `recurrence_end_date: string | null`
- `recurrence_end_count: number | null`
- `recurrence_parent: string | null`
- `recurrence_instance_number: number`
- `is_overdue: boolean`
- `completed_at: string | null`
- `created_at: string`
- `updated_at: string`

---

## Implementation

### Imports

```typescript
import React from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { vi } from 'vitest'
import type {
  AgentTimeBlock,
  AgentGlobalTask,
} from '@/lib/types/scheduling'
```

### `createMockTimeBlock(overrides?)`

```typescript
/** Returns a valid AgentTimeBlock. Pass overrides to customise specific fields. */
export function createMockTimeBlock(
  overrides?: Partial<AgentTimeBlock>
): AgentTimeBlock
```

Default values should be fully valid and representative:
- `id`: `"block-1"`
- `agent`: `"agent-1"`
- `date`: `"2026-03-25"`
- `start_time`: `"09:00:00"`
- `end_time`: `"10:00:00"`
- `block_type`: `"deep_work"`
- `title`: `"Test Block"`
- `color`: `"#6366F1"`
- `client`: `null`
- `client_name`: `""`
- `notes`: `""`
- `recurring_source`: `null`
- `is_completed`: `false`
- `duration_minutes`: `60`
- `created_at`: `"2026-03-25T09:00:00Z"`
- `updated_at`: `"2026-03-25T09:00:00Z"`

Spread `overrides` at the end so callers can change any field.

### `createMockGlobalTask(overrides?)`

```typescript
/** Returns a valid AgentGlobalTask. Pass overrides to customise specific fields. */
export function createMockGlobalTask(
  overrides?: Partial<AgentGlobalTask>
): AgentGlobalTask
```

Default values:
- `id`: `"task-1"`
- `agent`: `"agent-1"`
- `title`: `"Test Task"`
- `description`: `""`
- `status`: `"todo"`
- `priority`: `"medium"`
- `client`: `null`
- `client_name`: `""`
- `task_category_ref`: `null`
- `task_category_detail`: `null`
- `due_date`: `null`
- `scheduled_date`: `null`
- `time_block`: `null`
- `time_block_title`: `""`
- `estimated_minutes`: `null`
- `start_time`: `null`
- `end_time`: `null`
- `order`: `0`
- `is_recurring`: `false`
- `recurrence_frequency`: `null`
- `recurrence_days`: `null`
- `recurrence_interval`: `1`
- `recurrence_end_type`: `"never"`
- `recurrence_end_date`: `null`
- `recurrence_end_count`: `null`
- `recurrence_parent`: `null`
- `recurrence_instance_number`: `0`
- `is_overdue`: `false`
- `completed_at`: `null`
- `created_at`: `"2026-03-25T09:00:00Z"`
- `updated_at`: `"2026-03-25T09:00:00Z"`

### `mockUseSchedulingEngine(overrides?)`

```typescript
/**
 * Returns a vi.fn()-backed mock of the useSchedulingEngine hook return value.
 * Suitable for passing as the return value of vi.mock('@/lib/hooks/useSchedulingEngine').
 */
export function mockUseSchedulingEngine(
  overrides?: Partial<ReturnType<typeof import('@/lib/hooks/useSchedulingEngine').useSchedulingEngine>>
): ReturnType<typeof import('@/lib/hooks/useSchedulingEngine').useSchedulingEngine>
```

The return object provides stub values for every field the hook exposes:
- `timeBlocks`: `[]`
- `todayTasks`: `[]`
- `overdueTasks`: `[]`
- `isLoading`: `false`
- `selectedDate`: `"2026-03-25"`
- `setSelectedDate`: `vi.fn()`
- `viewMode`: `"day"`
- `setViewMode`: `vi.fn()`
- `weekDays`: `["2026-03-23", "2026-03-24", "2026-03-25", "2026-03-26", "2026-03-27"]`
- `scheduleTask`: `vi.fn()`
- `moveBlock`: `vi.fn()`
- `moveBlockToDay`: `vi.fn()`
- `resizeBlock`: `vi.fn()`
- `unscheduleBlock`: `vi.fn()`
- `completeTask`: `vi.fn()`
- `dropToAllDay`: `vi.fn()`

Spread `overrides` at the end.

> Note: The `useSchedulingEngine` hook does not exist yet (it is built in `section-04-data-hook`). The type import in `mockUseSchedulingEngine` will resolve once section-04 is complete. Until then, you can type the overrides parameter as `Record<string, unknown>` and cast the return value as needed, or simply inline the return type as a plain object type literal matching the list above.

### `renderWithQuery(ui, options?)`

```typescript
/**
 * Renders ui inside a fresh QueryClientProvider so React Query hooks work in tests.
 * Each call creates a brand-new QueryClient to prevent cache leaking between tests.
 */
export function renderWithQuery(
  ui: React.ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
): ReturnType<typeof render>
```

Create a new `QueryClient` with `defaultOptions.queries.retry: false` (so failed queries don't retry during tests and cause timeouts). Wrap `ui` in `<QueryClientProvider client={queryClient}>`. Return the result of `render(wrappedUi, options)`.

---

## Tests

Write a test file at `client/test-utils/scheduling.test.ts` to verify the factories and helpers behave correctly. These tests require no mocks — they are pure factory verification.

```typescript
// client/test-utils/scheduling.test.ts
import { describe, it, expect } from 'vitest'
import {
  createMockTimeBlock,
  createMockGlobalTask,
  mockUseSchedulingEngine,
} from './scheduling'
```

**Factory shape tests:**

- `createMockTimeBlock()` returns an object with `id`, `start_time`, `end_time`, `duration_minutes`
- `createMockTimeBlock({ id: 'custom-id' })` returns object where `id === 'custom-id'` and all other fields remain at defaults
- `createMockTimeBlock({ duration_minutes: 90 })` returns `duration_minutes === 90`
- `createMockGlobalTask()` returns an object with `id`, `title`, `priority`, `status`
- `createMockGlobalTask({ priority: 'high' })` returns `priority === 'high'`
- `createMockGlobalTask({ due_date: '2026-04-01' })` returns `due_date === '2026-04-01'`
- `mockUseSchedulingEngine()` returns object containing `scheduleTask` that is a function (vi.fn)
- `mockUseSchedulingEngine({ isLoading: true })` returns `isLoading === true`
- `mockUseSchedulingEngine()` returns `timeBlocks` as an empty array by default
- Two separate `createMockTimeBlock()` calls return independent objects (no shared reference)

**`renderWithQuery` test** (needs `@testing-library/react`):

- Renders a component that calls `useQuery` without throwing — confirms `QueryClientProvider` is present
- Each call to `renderWithQuery` uses a fresh `QueryClient` (verify by checking the client instance differs between two calls — or simply ensure no cache contamination by rendering a component that reads from the cache)

---

## File Location

```
client/
  test-utils/
    scheduling.tsx       ← create this (the main deliverable)
    scheduling.test.tsx  ← created (renamed to .tsx for JSX support)
```

The `client/test-utils/` directory did not exist — created.

---

## Dependencies

This section has no dependencies on other sections. It can be implemented immediately.

---

## Checklist

- [x] Create `client/test-utils/` directory
- [x] Implement `createMockTimeBlock` with correct `AgentTimeBlock` defaults
- [x] Implement `createMockGlobalTask` with correct `AgentGlobalTask` defaults
- [x] Implement `mockUseSchedulingEngine` with all hook return fields stubbed as `vi.fn()`
- [x] Implement `renderWithQuery` with fresh `QueryClient` per call and `retry: false`
- [x] Write `scheduling.test.tsx` (12 tests) covering all factory and helper behaviours
- [x] All tests pass: 12/12 passing

## Deviations from Plan

- Test file named `scheduling.test.tsx` (not `.ts`) to support JSX syntax in renderWithQuery tests.
- `mockUseSchedulingEngine` return type defined as local `SchedulingEngineMock` interface (inline object type) since `useSchedulingEngine` hook does not exist yet (built in section-04). Type will be tightened once hook is implemented.
