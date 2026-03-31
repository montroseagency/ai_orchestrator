# Section 12: StatusBar

## Overview

`StatusBar.tsx` is a simple footer strip rendered at the bottom of the `SchedulingEngine` layout. It displays three live summary counts computed from the data already loaded by `useSchedulingEngine` — no additional API calls are made. All values are derived via `useMemo` to avoid recomputing on every render.

**Dependencies:**
- `section-01-test-utils` — `createMockTimeBlock`, `createMockGlobalTask`, `mockUseSchedulingEngine`, `renderWithQuery` helpers required for tests
- `section-04-data-hook` — `useSchedulingEngine` must exist and export `timeBlocks`, `todayTasks`, `overdueTasks`

---

## File to Create

```
client/components/portal/calendar/StatusBar.tsx
```

Test file (co-located):

```
client/components/portal/calendar/StatusBar.test.tsx
```

---

## Tests First

Write these tests before implementing the component. They use the helpers from `section-01-test-utils`.

**File:** `client/components/portal/calendar/StatusBar.test.tsx`

```typescript
// Mock useSchedulingEngine before importing StatusBar
vi.mock('@/lib/hooks/useSchedulingEngine')

describe('StatusBar', () => {
  it('shows correct "N tasks scheduled" count from timeBlocks.length', () => {
    // Arrange: mock hook with 3 time blocks, 0 tasks
    // Assert: renders "3 tasks scheduled"
  })

  it('shows correct "N unscheduled" count from todayTasks + overdueTasks', () => {
    // Arrange: mock hook with 2 todayTasks + 1 overdueTasks = 3 unscheduled
    // Assert: renders "3 unscheduled"
  })

  it('"Xh Ym blocked" correctly sums duration_minutes across all time blocks', () => {
    // Arrange: 2 blocks with duration_minutes = 90 + 60 = 150 min = 2h 30m
    // Assert: renders "2h 30m blocked"
  })

  it('shows "0h 0m blocked" when there are no time blocks', () => {
    // Arrange: mock hook with empty timeBlocks
    // Assert: renders "0h 0m blocked"
  })

  it('values update reactively when mock data changes', () => {
    // Arrange: render with initial data, re-render with updated mock
    // Assert: displayed values reflect the new data
  })
})
```

**Test notes:**
- Use `mockUseSchedulingEngine({ timeBlocks: [...], todayTasks: [...], overdueTasks: [...] })` from `client/test-utils/scheduling.tsx` to set up each scenario
- `createMockTimeBlock({ duration_minutes: 90 })` for building test data
- `renderWithQuery(<StatusBar />)` wrapper ensures React Query context is present even though StatusBar makes no queries itself

---

## Implementation Details

### What it displays

The strip renders a single line in this format:

```
3 tasks scheduled · 2 unscheduled · 2h 30m blocked
```

The three stats are separated by a middle dot (·) character.

### Computed values

| Stat | Source | Formula |
|------|--------|---------|
| N tasks scheduled | `timeBlocks` from hook | `timeBlocks.length` |
| N unscheduled | `todayTasks` + `overdueTasks` from hook | `todayTasks.length + overdueTasks.length` |
| Xh Ym blocked | `timeBlocks` from hook | `sum of block.duration_minutes`, formatted as `Xh Ym` |

All three are computed inside a single `useMemo` that depends on `[timeBlocks, todayTasks, overdueTasks]`.

### Duration formatting

Convert total minutes to `"Xh Ym"`:
- Total minutes = `timeBlocks.reduce((acc, b) => acc + b.duration_minutes, 0)`
- Hours = `Math.floor(total / 60)`
- Minutes = `total % 60`
- Output: `"${hours}h ${minutes}m blocked"`
- When total = 0: `"0h 0m blocked"`

### Component signature

```typescript
// StatusBar.tsx
export default function StatusBar(): JSX.Element
```

The component calls `useSchedulingEngine()` internally — it receives no props. This keeps the caller (`SchedulingEngine.tsx`) clean.

### Rendering

Render as a `<footer>` element. Apply design tokens from `globals.css`:
- Background: `var(--color-surface-subtle)`
- Border top: `1px solid var(--color-border)`
- Text: `text-sm` or `text-xs`, `var(--color-text-secondary)`
- Padding: compact (`px-4 py-2`)
- Layout: single row, stats separated by `·` spans

Example structure (prose, not prescriptive):

```
<footer class="status-bar">
  <span>{scheduledCount} tasks scheduled</span>
  <span aria-hidden="true"> · </span>
  <span>{unscheduledCount} unscheduled</span>
  <span aria-hidden="true"> · </span>
  <span>{blockedLabel}</span>
</footer>
```

The separator spans use `aria-hidden="true"` so screen readers read the three stats as separate phrases.

---

## Context: Where StatusBar Lives

`StatusBar` is rendered as the last child inside `SchedulingEngine.tsx`, below the `.split-view` div that holds `BacklogPane` and `CalendarGrid`:

```
<DndContext ...>
  <CalendarHeader ... />
  <div class="split-view">
    <BacklogPane ... />
    <CalendarGrid ... />
  </div>
  <StatusBar />          {/* ← here */}
</DndContext>
```

It does not participate in drag-and-drop and has no interaction with `@dnd-kit`.

---

## Edge Cases

- **Zero blocks, zero tasks:** All three counts show zero — `"0 tasks scheduled · 0 unscheduled · 0h 0m blocked"`. This is valid and expected for a fresh/empty day.
- **Very long durations:** A day with 16 hours of blocks → `"16h 0m blocked"`. No truncation needed; the format handles any non-negative integer.
- **Plural vs singular:** The plan spec uses "N tasks scheduled" and "N unscheduled" without specifying singular handling. Use consistent pluralization (e.g., always "tasks", always "unscheduled") to avoid complexity — do not add "1 task" vs "2 tasks" logic unless the design spec requests it.

---

## Summary Checklist

- [ ] Create `client/components/portal/calendar/StatusBar.test.tsx` with all 5 tests
- [ ] Create `client/components/portal/calendar/StatusBar.tsx`
- [ ] Component calls `useSchedulingEngine()` and derives all three stats via `useMemo`
- [ ] Duration formatted as `"Xh Ym blocked"`
- [ ] Renders as `<footer>` with design token styles
- [ ] Separator spans are `aria-hidden`
- [ ] All 5 tests pass with `npm test`
