# TDD Plan: Agent Dashboard KPI

**Testing stack**: Vitest v4.1.2, @testing-library/react, @testing-library/jest-dom, jsdom
**Test utilities**: `client/test-utils/scheduling.tsx` — `createMockTimeBlock()`, `createMockGlobalTask()`, `renderWithQuery()`
**Mock pattern**: `vi.mock('@/lib/hooks/useScheduling', ...)` to mock React Query hooks
**Fake timers**: `vi.useFakeTimers()` / `vi.advanceTimersByTime()` for interval tests

---

## File Structure (Tests Mirror Components)

```
client/components/agent/dashboard/__tests__/
  CurrentTaskKpi.test.tsx
  DashboardTaskList.test.tsx
  ReadOnlySchedule.test.tsx
  DashboardStatsRow.test.tsx
```

---

## Data Layer

### Stale Time Configuration (in `useScheduling.ts`)
- Test: `useCommandCenter` hook has `staleTime: 55_000` set (verify query config object)
- Test: `useCommandCenter` hook retains `refetchInterval: 60_000`

---

## CurrentTaskKpi

### Active Block Detection
- Test: given a time block spanning the current time (e.g., 9:00–10:00, now=9:30), renders the block's `title`
- Test: given a time block spanning current time, renders client badge with `block.client_name`
- Test: given a time block spanning current time, renders category badge with `BLOCK_TYPE_LABELS[block.block_type]`
- Test: given multiple time blocks, renders the one whose range contains `now` — not a block in the past or future
- Test: given overlapping blocks, renders the block with the latest `start_time`

### Progress Calculation
- Test: block starts at 0min, ends at 60min, now=30min → progress bar has `transform: scaleX(0.5)`
- Test: block starts at 0min, ends at 60min, now=0min → progress bar has `transform: scaleX(0)`
- Test: block starts at 0min, ends at 60min, now=60min → progress bar has `transform: scaleX(1)` (clamped to 100%)
- Test: progress does not go below 0 or above 100

### Time Remaining Display
- Test: 30 minutes remaining → renders "30 min remaining"
- Test: < 1 minute remaining → renders "Ending soon" (not "0 min remaining")
- Test: `floor()` is applied — 29.9 minutes remaining renders "29 min remaining"

### Empty States
- Test: no time blocks for today → renders "No tasks scheduled for today" text
- Test: no time blocks for today → renders link to portal
- Test: `now` falls between two blocks (gap) → renders "Free until" with next block's start time
- Test: `now` falls between two blocks → renders next block's title
- Test: `now` is after all blocks (day ended) → renders no active task message with portal link

### 60-Second Timer
- Test: advancing fake timers by 60s triggers `setNow` → component re-renders with updated progress
- Test: `setInterval` is cleared on unmount (no memory leak)

### Deep-link Button
- Test: "Open in Portal →" button has correct `href` containing `date={block.date}` and `block={block.id}`

### Accessibility
- Test: progress bar element has `role="progressbar"`
- Test: progress bar has `aria-valuenow`, `aria-valuemin={0}`, `aria-valuemax={100}`

---

## DashboardStatsRow

### Rendering
- Test: renders `stats.total_active_tasks` value
- Test: renders `stats.completed_today` value
- Test: renders `stats.hours_blocked_today` value
- Test: renders `stats.active_clients` value
- Test: renders label "Active Tasks" (or equivalent mapped label)
- Test: renders label "Done Today"
- Test: renders label "Hours Blocked"
- Test: renders label "Active Clients"

### Edge Cases
- Test: zero values render as "0" (not blank or undefined)

---

## DashboardTaskList

### Data Merge and Rendering
- Test: renders all `todays_global_tasks` titles
- Test: renders all `todays_client_tasks` titles
- Test: tasks from both sources appear in a single list (not separate sections by source)

### Sort Order
- Test: `in_progress` task appears before `todo` task in rendered output
- Test: `todo` task appears before `done` task in rendered output
- Test: within the same status group, task with earlier `start_time` appears first
- Test: within the same status group, tasks without `start_time` appear after tasks with `start_time`
- Test: tasks without `start_time` are ordered by `order` field

### Done Task Styling
- Test: tasks with `status === 'done'` have `line-through` styling class

### Checkboxes (Global Tasks Only)
- Test: `AgentGlobalTask` items render with a checkbox element
- Test: `CrossClientTask` items render without a checkbox element
- Test: checkbox for a `todo` task is unchecked
- Test: checkbox for a `done` task is checked

### Optimistic Update
- Test: clicking a checkbox immediately renders the task as done (before mutation resolves)
- Test: clicking a checkbox calls `useUpdateGlobalTask` mutation with `{ status: 'done' }`
- Test: if the mutation fails, the task reverts to its original status
- Test: on mutation error, a toast error is shown

### Rollback
- Test: on mutation failure, `setQueryData` is called with the snapshot from `onMutate`

### Footer Link
- Test: "View All in Portal →" link has correct `href` containing `/management/tasks/`

### Empty State
- Test: when both `todays_global_tasks` and `todays_client_tasks` are empty, renders empty state text

---

## ReadOnlySchedule

### Block Rendering
- Test: given a time block, renders the block's `title` in the DOM
- Test: given a time block, renders the block's `client_name`
- Test: a block starting at 9:00 (540 min), with `startHour=8` and `hourHeight=50`, has `top: 50px` (1 hour × 50px)
- Test: a 60-minute block has `height: 50px` (1 hour × 50px)
- Test: a block's left border color matches `BLOCK_TYPE_COLORS[block.block_type]`

### Hour Grid
- Test: hour labels "8 AM" through "8 PM" render when `startHour=8`, `endHour=20`
- Test: `formatHour(8)` → "8 AM" label renders in grid

### Active Block Highlight
- Test: the block whose range contains `now` has a highlight class (e.g., `ring-accent`)
- Test: a block in the past does not have a highlight class

### NowIndicator
- Test: `NowIndicator` is present in the DOM
- Test: NowIndicator's `top` style matches expected position for current time within `[startHour, endHour]`
- Test: NowIndicator is not rendered when `now` is before `startHour`
- Test: NowIndicator is not rendered when `now` is after `endHour`
- Test: advancing fake timers by 60s updates NowIndicator position

### No Interactivity
- Test: time block elements do not have `onClick` handlers
- Test: time block elements are not focusable (no `tabIndex` or `role="button"`)

### Auto-Scroll on Mount
- Test: `scrollTop` on the container is set to a non-zero value on mount when `now` is within visible range

### Footer Link
- Test: "Edit Schedule in Portal →" link has correct `href` containing `/management/calendar/`

---

## AgentDashboardPage (Integration)

### Loading State
- Test: when `isLoading` is true, renders a skeleton (not the dashboard content)

### Error State
- Test: when `isError` is true, renders an error state with a retry button

### Loaded State
- Test: when data is loaded, renders `CurrentTaskKpi` section
- Test: when data is loaded, renders `DashboardStatsRow` section
- Test: when data is loaded, renders `DashboardTaskList` section
- Test: when data is loaded, renders `ReadOnlySchedule` section

### Layout
- Test: on mobile (narrow viewport), sections are stacked vertically
- Test: `CurrentTaskKpi` is the first element in document order

---

## Test Utilities to Create

For the `__tests__` directory, create a local helper:

```typescript
// Test helper signatures (not implementations):

function advanceTimerAndRerender(renderResult, ms: number): void
  // Advances fake timers and flushes React updates

function makeMockCommandCenterData(overrides?): CommandCenterData
  // Builds a full CommandCenterData mock for page-level tests
  // Uses createMockTimeBlock() and createMockGlobalTask() internally
```
