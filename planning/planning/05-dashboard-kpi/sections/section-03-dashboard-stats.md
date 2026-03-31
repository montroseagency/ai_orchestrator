# Section 03: DashboardStatsRow

## Overview

Implement a single read-only component that renders four stat cards in a responsive grid. Each card displays one metric from the `CommandCenterStats` object returned by the command center API. There are no user interactions — this component is purely display.

**Depends on**: `section-01-test-utils` (for `renderWithQuery` and the `CommandCenterStats` type fixture).

**Blocks**: `section-06-dashboard-page` (which assembles all components into the page).

---

## Files to Create

```
client/components/agent/dashboard/DashboardStatsRow.tsx
client/components/agent/dashboard/__tests__/DashboardStatsRow.test.tsx
```

---

## Tests First

**File**: `client/components/agent/dashboard/__tests__/DashboardStatsRow.test.tsx`

Testing stack: Vitest + @testing-library/react + @testing-library/jest-dom.

The test file imports `renderWithQuery` from `@/test-utils/scheduling` and uses inline mock stats objects (no hook mocking required — `DashboardStatsRow` receives stats as a prop).

### Test cases to implement

**Rendering stat values**

- Renders `stats.total_active_tasks` value in the DOM
- Renders `stats.completed_today` value in the DOM
- Renders `stats.hours_blocked_today` value in the DOM
- Renders `stats.active_clients` value in the DOM

**Rendering stat labels**

- Renders the label `"Active Tasks"` in the DOM
- Renders the label `"Done Today"` in the DOM
- Renders the label `"Hours Blocked"` in the DOM
- Renders the label `"Active Clients"` in the DOM

**Edge case**

- When all stats are `0`, each value renders as `"0"` (not blank, `undefined`, or omitted)

### Test stub

```typescript
import { screen } from '@testing-library/react'
import { renderWithQuery } from '@/test-utils/scheduling'
import { DashboardStatsRow } from '../DashboardStatsRow'
import type { CommandCenterStats } from '@/lib/types/scheduling'

const mockStats: CommandCenterStats = {
  total_active_tasks: 7,
  completed_today: 3,
  hours_blocked_today: 4.5,
  active_clients: 2,
}

describe('DashboardStatsRow', () => {
  it('renders total_active_tasks value', () => { /* ... */ })
  it('renders completed_today value', () => { /* ... */ })
  it('renders hours_blocked_today value', () => { /* ... */ })
  it('renders active_clients value', () => { /* ... */ })

  it('renders "Active Tasks" label', () => { /* ... */ })
  it('renders "Done Today" label', () => { /* ... */ })
  it('renders "Hours Blocked" label', () => { /* ... */ })
  it('renders "Active Clients" label', () => { /* ... */ })

  it('renders zero values as "0" not blank', () => { /* ... */ })
})
```

---

## Implementation

**File**: `client/components/agent/dashboard/DashboardStatsRow.tsx`

### Props interface

```typescript
import type { CommandCenterStats } from '@/lib/types/scheduling'

interface DashboardStatsRowProps {
  stats: CommandCenterStats
}
```

### Field-to-label mapping

The four stats map directly from `CommandCenterStats` — no derived calculations needed:

| `CommandCenterStats` field | Display label   |
|---------------------------|-----------------|
| `total_active_tasks`      | Active Tasks    |
| `completed_today`         | Done Today      |
| `hours_blocked_today`     | Hours Blocked   |
| `active_clients`          | Active Clients  |

### Layout and styling

The row uses a 2-column mobile grid that expands to 4 columns on large screens:

```
grid grid-cols-2 lg:grid-cols-4 gap-4
```

Each individual stat card:
- Container: `bg-surface rounded-xl border border-border p-4`
- Value: `text-2xl font-bold` (render the raw number as a string)
- Label: `text-xs text-muted uppercase tracking-wider`

The value is always rendered as `String(value)` or direct interpolation. Do not use conditional rendering that suppresses `0` (e.g., avoid `{value && <span>...`).

### Component structure stub

```typescript
export const DashboardStatsRow = React.memo(function DashboardStatsRow({ stats }: DashboardStatsRowProps) {
  const cards = [
    { value: stats.total_active_tasks, label: 'Active Tasks' },
    { value: stats.completed_today,    label: 'Done Today' },
    { value: stats.hours_blocked_today, label: 'Hours Blocked' },
    { value: stats.active_clients,     label: 'Active Clients' },
  ]

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map(({ value, label }) => (
        <StatCard key={label} value={value} label={label} />
      ))}
    </div>
  )
})
```

`StatCard` can be an inline sub-component or a named inner function — it does not need to be exported separately.

### React.memo

Wrap `DashboardStatsRow` in `React.memo`. The parent page (`AgentDashboardPage`) re-renders every 60 seconds on refetch; `memo` prevents a cascade re-render here unless `stats` actually changes.

---

## Type Reference

`CommandCenterStats` is defined in `client/lib/types/scheduling.ts`:

```typescript
export interface CommandCenterStats {
  total_active_tasks: number;
  completed_today: number;
  hours_blocked_today: number;
  active_clients: number;
}
```

Import it as: `import type { CommandCenterStats } from '@/lib/types/scheduling'`

---

## Checklist

- [ ] `DashboardStatsRow.tsx` created at `client/components/agent/dashboard/DashboardStatsRow.tsx`
- [ ] Props accept `stats: CommandCenterStats`
- [ ] Four cards rendered in `grid grid-cols-2 lg:grid-cols-4 gap-4` layout
- [ ] Each card: value in `text-2xl font-bold`, label in `text-xs text-muted uppercase tracking-wider`
- [ ] Component wrapped in `React.memo`
- [ ] Zero values render as `"0"` (not blank)
- [ ] All 9 test cases pass (4 values + 4 labels + zero edge case)
- [ ] No hooks, no mutations, no side effects in this component
