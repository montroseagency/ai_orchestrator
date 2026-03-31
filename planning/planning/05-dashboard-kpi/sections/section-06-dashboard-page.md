# Section 06: AgentDashboardPage — Assembly and Integration

## Overview

This section assembles the four dashboard components from sections 02–05 into a single route page. It also creates the barrel export file and covers the page-level integration tests. This section must be implemented after sections 02–05 are complete.

**Dependencies**: section-02 (`CurrentTaskKpi`), section-03 (`DashboardStatsRow`), section-04 (`DashboardTaskList`), section-05 (`ReadOnlySchedule`).

---

## Implementation Notes (Actual)

- Guard order: `isLoading` → `isError` → `!data` (safety net) → success branch. This order is required because `data` is `undefined` in both loading and error states; checking `isError` before the `!data` guard ensures the error UI renders correctly.
- `AGENT_TYPE = 'marketing'` is a module-level constant (not inside the component).
- `todayStr` is stabilized with `useMemo([], [])` to prevent midnight flip.
- Retry button uses `Button` from `@/components/ui/button` (project design system).
- `isFetching` indicator has `data-testid="fetching-indicator"`, `aria-live="polite"`, and `aria-label` for screen readers.
- Tests use a typed `makeQueryReturn()` helper (Partial<ReturnType<typeof useCommandCenter>>) instead of `as any` casts.
- 13 tests implemented (2 more than planned stubs): added `isFetching` indicator tests and `refetch` call assertion.

## Files Created or Modified

| Path | Action |
|------|--------|
| `client/components/agent/dashboard/index.ts` | Created — barrel export |
| `client/app/dashboard/agent/marketing/page.tsx` | Modified — replaced `AgentMarketingOverviewPage` with `AgentDashboardPage` |
| `client/components/agent/dashboard/__tests__/AgentDashboardPage.test.tsx` | Created — 13 integration tests, all passing |

**Not modified**: `DaySchedule.tsx`, `CommandCenter.tsx`, `useScheduling.ts`, or any other existing file outside the above list.

**Important**: The existing `client/app/dashboard/agent/marketing/page.tsx` currently renders `AgentMarketingOverviewPage` — a marketing-specific overview that is completely separate from the scheduling dashboard. Replace it entirely with `AgentDashboardPage`. The old marketing overview content is superseded by the new dashboard.

---

## Tests First

File: `client/components/agent/dashboard/__tests__/AgentDashboardPage.test.tsx`

Testing stack: Vitest, @testing-library/react, @testing-library/jest-dom. Use `renderWithQuery()` from `client/test-utils/scheduling.tsx` and `makeMockCommandCenterData()` from the same file (added in section-01).

Mock `@/lib/hooks/useScheduling` to control `useCommandCenter()` return values.

### Test stubs

```typescript
// AgentDashboardPage.test.tsx

describe('AgentDashboardPage — loading state', () => {
  it('renders a skeleton when isLoading is true');
  // mock: useCommandCenter returns { isLoading: true, isError: false, data: undefined }
  // assert: skeleton element is present, no CurrentTaskKpi/StatsRow/TaskList/Schedule content
});

describe('AgentDashboardPage — error state', () => {
  it('renders an error state with a retry button when isError is true');
  // mock: useCommandCenter returns { isLoading: false, isError: true, data: undefined }
  // assert: error message present, retry button present
  // assert: no KPI/stats/task/schedule content
});

describe('AgentDashboardPage — loaded state', () => {
  it('renders CurrentTaskKpi section when data is loaded');
  it('renders DashboardStatsRow section when data is loaded');
  it('renders DashboardTaskList section when data is loaded');
  it('renders ReadOnlySchedule section when data is loaded');
  // For each: mock useCommandCenter returns { isLoading: false, isError: false, data: makeMockCommandCenterData() }
  // Assert the respective section's data-testid or known content is in the DOM
});

describe('AgentDashboardPage — layout ordering', () => {
  it('CurrentTaskKpi is the first major section in document order');
  // assert: the KPI container appears before the stats row in the DOM
});

describe('AgentDashboardPage — mobile layout', () => {
  it('all sections are present in the DOM on a narrow viewport');
  // Resize viewport or use CSS class inspection — all four sections must render
  // regardless of viewport (no conditional rendering, layout is CSS-only)
});
```

The `makeMockCommandCenterData()` helper (from section-01) must return a valid `CommandCenterData` object with `stats`, `time_blocks`, `todays_global_tasks`, and `todays_client_tasks`.

---

## Barrel Export

File: `client/components/agent/dashboard/index.ts`

Export all four components from a single entry point:

```typescript
export { CurrentTaskKpi } from './CurrentTaskKpi';
export { DashboardStatsRow } from './DashboardStatsRow';
export { DashboardTaskList } from './DashboardTaskList';
export { ReadOnlySchedule } from './ReadOnlySchedule';
```

---

## AgentDashboardPage Implementation

File: `client/app/dashboard/agent/marketing/page.tsx`

This is a `'use client'` page component. It is the single data-fetching boundary — it calls `useCommandCenter()` once and passes slices of the result to each child.

### agentType

The route is at `/dashboard/agent/marketing/`, so `agentType` is the string `"marketing"`. This is a constant for this file — hardcode it as `const agentType = 'marketing'` inside the component. Children that need it for deep-link URL construction receive it as a prop.

### Three states

**Loading state** (`isLoading === true`):
- Render a skeleton layout that mirrors the real layout (KPI full-width, stats row, two-column bottom). Use the project's `skeleton` component from `client/components/ui/skeleton.tsx`. Do not render any child dashboard components.

**Error state** (`isError === true`):
- Render an error message and a "Retry" button. The button calls `refetch()` from the `useCommandCenter()` return value. Do not render any child dashboard components.
- Use `client/components/ui/alert.tsx` or a simple surface card to display the error.

**Loaded state** (`data` is present):
- Render the four child components in the layout described below.
- Wrap each stateless child (`CurrentTaskKpi`, `DashboardStatsRow`, `ReadOnlySchedule`) in `React.memo` at their definition files (sections 02, 03, 05 — not here). `DashboardTaskList` is not memoized because it manages its own mutation state.

### Layout

Desktop (large screens): two-column bottom half via CSS grid. Mobile: single column. Use Tailwind responsive classes — no JavaScript viewport detection.

```
┌──────────────────────────────────────────┐
│  CurrentTaskKpi (col-span-full)          │
├──────────────────────────────────────────┤
│  DashboardStatsRow (col-span-full)       │
├────────────────────┬─────────────────────┤
│  DashboardTaskList │  ReadOnlySchedule   │
│  (lg:col-span-2/5) │  (lg:col-span-3/5)  │
└────────────────────┴─────────────────────┘
```

Tailwind classes for the outer grid: `grid grid-cols-1 gap-6`. The bottom row is a nested grid: `grid grid-cols-1 lg:grid-cols-5 gap-6`. `DashboardTaskList` takes `lg:col-span-2`, `ReadOnlySchedule` takes `lg:col-span-3`.

### isFetching indicator

When `isFetching === true` (background refetch — not the initial load), show a subtle pulsing indicator at the top of the page. A simple `<div>` with `animate-pulse bg-accent/30 h-0.5 w-full rounded` renders as a thin line that conveys background refresh activity without blocking the UI.

### Props to pass

| Child | Props |
|-------|-------|
| `CurrentTaskKpi` | `timeBlocks={data.time_blocks}` `agentType={agentType}` |
| `DashboardStatsRow` | `stats={data.stats}` |
| `DashboardTaskList` | `globalTasks={data.todays_global_tasks}` `clientTasks={data.todays_client_tasks}` `agentType={agentType}` |
| `ReadOnlySchedule` | `timeBlocks={data.time_blocks}` `date={todayStr}` `agentType={agentType}` |

Where `todayStr` is today's date in `YYYY-MM-DD` format, derived inline:
```typescript
const todayStr = new Date().toISOString().slice(0, 10);
```

### Component signature stub

```typescript
'use client';

import React from 'react';
import { useCommandCenter } from '@/lib/hooks/useScheduling';
import {
  CurrentTaskKpi,
  DashboardStatsRow,
  DashboardTaskList,
  ReadOnlySchedule,
} from '@/components/agent/dashboard';
// ... skeleton, alert imports

export default function AgentDashboardPage() {
  const agentType = 'marketing';
  const todayStr = new Date().toISOString().slice(0, 10);
  const { data, isLoading, isError, isFetching, refetch } = useCommandCenter();

  if (isLoading) { /* return skeleton layout */ }
  if (isError)   { /* return error state with retry button */ }

  return (
    <div className="space-y-6">
      {/* isFetching indicator */}
      {/* CurrentTaskKpi */}
      {/* DashboardStatsRow */}
      {/* two-column bottom: DashboardTaskList + ReadOnlySchedule */}
    </div>
  );
}
```

---

## Background: useCommandCenter Data Shape

The `useCommandCenter()` hook (already defined in `client/lib/hooks/useScheduling.ts`) returns a React Query result wrapping `CommandCenterData`:

```typescript
interface CommandCenterData {
  stats: CommandCenterStats;           // { total_active_tasks, completed_today, hours_blocked_today, active_clients }
  time_blocks: AgentTimeBlock[];       // time blocks for today
  todays_global_tasks: AgentGlobalTask[];
  todays_client_tasks: CrossClientTask[];
}
```

This section does not modify the hook — section-01 already set `staleTime: 55_000` and retained `refetchInterval: 60_000`.

---

## Cross-Plan Deep-Link Graceful Degradation

The "Open in Portal →" and "Edit Schedule in Portal →" links inside `CurrentTaskKpi` and `ReadOnlySchedule` (assembled by this page) link to:
- `/dashboard/agent/marketing/management/calendar/?date={date}&block={id}`
- `/dashboard/agent/marketing/management/tasks/`

The calendar page's handling of `?date=` and `?block=` params is in scope for Split 04. If not yet implemented, the links still navigate to the calendar page — the user arrives without auto-scroll (graceful degradation). No conditional logic is needed in this page for that.

---

## Acceptance Criteria for This Section

1. Barrel export at `client/components/agent/dashboard/index.ts` exports all four components.
2. `client/app/dashboard/agent/marketing/page.tsx` exports `AgentDashboardPage` as the default export (replacing `AgentMarketingOverviewPage`).
3. Loading state renders a skeleton matching the dashboard layout structure (no child component content).
4. Error state renders an error message and functional retry button (calls `refetch()`).
5. Loaded state renders all four child components with the correct props.
6. `CurrentTaskKpi` appears first in DOM order (before stats, task list, schedule).
7. On large screens, `DashboardTaskList` and `ReadOnlySchedule` are side-by-side (`lg:col-span-2` / `lg:col-span-3`).
8. On small screens, all sections stack vertically (single column, no JS viewport detection).
9. Background refetch (`isFetching`) shows a subtle indicator that does not disrupt the loaded content.
10. `agentType = 'marketing'` is a constant within the component; no dynamic param lookup is needed.
11. All integration tests in `AgentDashboardPage.test.tsx` pass.
