# Section 09: DayColumn, DayGrid, WeekGrid

## Overview

This section builds the three grid components that make up the scrollable calendar body. `DayColumn` is a single day's hourly grid: it renders background lines, positions time blocks absolutely, and serves as a drop target. `DayGrid` wraps one `DayColumn` with a `TimeGutter` for the Day view. `WeekGrid` wraps five `DayColumn` instances side-by-side for the Week view.

**Batch:** Batch 4 (runs after section-08-grid-structure and section-10-time-block-card are complete)

---

## Dependencies

| Section | What it provides |
|---------|-----------------|
| section-01-test-utils | `createMockTimeBlock`, `createMockGlobalTask`, `renderWithQuery`, `mockUseSchedulingEngine` |
| section-02-shared-utils | `minutesToPx`, `getEventStyle`, `getOverlapGroups`, `getSideBySideLayout`, `clientYToTimeSlot` |
| section-08-grid-structure | `TimeGutter` component (already built), layout constant prop shapes |
| section-10-time-block-card | `TimeBlockCard` component (already built) |

Do not re-implement anything from those sections. Import from their output paths.

---

## Files to Create

| File | Purpose |
|------|---------|
| `client/components/portal/calendar/DayColumn.tsx` | Single-day grid with droppable zone, grid lines, time blocks, current-time indicator |
| `client/components/portal/calendar/DayGrid.tsx` | Day view: TimeGutter + DayColumn inside scrollable container |
| `client/components/portal/calendar/WeekGrid.tsx` | Week view: TimeGutter + five DayColumns, column headers with click handlers |
| `client/components/portal/calendar/__tests__/DayColumn.test.tsx` | DayColumn unit + integration tests |
| `client/components/portal/calendar/__tests__/DayGrid.test.tsx` | DayGrid tests |
| `client/components/portal/calendar/__tests__/WeekGrid.test.tsx` | WeekGrid tests |

---

## Tests First

Write the tests below **before** implementing the components. All component tests mock `@dnd-kit/core` (stub `useDroppable` to return `{ isOver: false, setNodeRef: vi.fn() }`) and mock `TimeBlockCard` as a simple `<div data-testid="time-block-card" />`.

### DayColumn Tests (`DayColumn.test.tsx`)

```typescript
describe('DayColumn', () => {
  it('renders a container with correct pixel height: (endHour - startHour) * hourHeight')
  // e.g. (22 - 6) * 60 = 960px

  it('renders one grid line div per hour from startHour to endHour')
  // 16 hour marks for 6AM–10PM

  it('renders half-hour tick marks (lower opacity) between each hour mark')

  it('renders current time indicator at correct top offset (mock new Date())')
  // If now = 8:30am with startHour=6, hourHeight=60: top = 2.5 * 60 = 150px

  it('does NOT render current time indicator when current time is outside startHour–endHour range')

  it('calls useDroppable with id "column-{date}" and data { type: "day-column", date }')

  it('renders a TimeBlockCard for each time block in displayBlocks')

  it('passes side-by-side layout (left%, width%) props to each TimeBlockCard')
  // Verify that getOverlapGroups + getSideBySideLayout are applied before rendering

  it('adds isOver highlight class when draggable is over the column')
  // mock useDroppable to return isOver: true, check for bg-accent-light/20 or similar
})
```

### DayGrid Tests (`DayGrid.test.tsx`)

```typescript
describe('DayGrid', () => {
  it('renders TimeGutter alongside DayColumn in a flex row')

  it('wraps content in an overflow-y: auto scrollable container')

  it('calls scrollTo on mount to scroll to current time position')
  // Use vi.spyOn(element, 'scrollTo') — check it is called with a non-zero top value
  // when current time is within startHour..endHour
})
```

### WeekGrid Tests (`WeekGrid.test.tsx`)

```typescript
describe('WeekGrid', () => {
  it('renders exactly 5 DayColumn instances (Mon–Fri)')

  it('renders column headers with formatted day labels (e.g. "Mon 23", "Tue 24")')

  it('clicking a column header calls onDaySelect with that column\'s date')

  it('all 5 columns share a single overflow-y: auto scroll container')

  it('renders TimeGutter once (not once per column)')
})
```

---

## Implementation Details

### Layout Constants

These components receive layout constants as props (not hard-coded). The values used by the portal calendar are:

| Prop | Value | Description |
|------|-------|-------------|
| `hourHeight` | `60` | Pixels per hour |
| `startHour` | `6` | First visible hour (6 AM) |
| `endHour` | `22` | Last visible hour (10 PM) |
| `snapMinutes` | `30` | Drag snap resolution |

All three components accept and forward these constants.

---

### DayColumn

**File:** `client/components/portal/calendar/DayColumn.tsx`

**Props:**
```typescript
interface DayColumnProps {
  date: string                    // ISO date "YYYY-MM-DD"
  displayBlocks: AgentTimeBlock[] // pre-filtered blocks for this date
  hourHeight: number
  startHour: number
  endHour: number
  snapMinutes: number
  activeId: string | null         // from SchedulingEngine — for card ghost state
}
```

**Structure:**
- Outer wrapper: `position: relative`, `height: (endHour - startHour) * hourHeight` px
- Drop zone: single `useDroppable({ id: 'column-{date}', data: { type: 'day-column', date } })` — the `setNodeRef` is applied to the outer wrapper. The entire column is one drop target; the exact time slot is resolved by `SchedulingEngine.onDragEnd` using `clientYToTimeSlot`.
- `isOver` highlight: when `useDroppable` returns `isOver: true`, apply a subtle background tint (`bg-accent-light/20` or similar design token).

**Background grid lines:**
- For each hour from `startHour` to `endHour`, render a full-width `<div>` at `top: minutesToPx((hour - startHour) * 60, hourHeight)` — this is the hour mark line.
- For each half-hour mark, render a shorter or lower-opacity `<div>` at `top: minutesToPx((hour - startHour) * 60 + 30, hourHeight)`.
- Grid lines are `position: absolute`, `pointer-events: none`, `z-index: 0`.

**Current time indicator:**
- Compute `nowMinutes = currentHour * 60 + currentMinute` from `new Date()`.
- Only render if `nowMinutes >= startHour * 60 && nowMinutes < endHour * 60`.
- `position: absolute`, `top: minutesToPx(nowMinutes - startHour * 60, hourHeight)`, full width, 2px red line (`bg-red-500`), `z-index: 10`, `pointer-events: none`.
- Add a small red circle at the left edge of the indicator line.

**Time block rendering:**
- Before rendering, call `getOverlapGroups(displayBlocks)` then `getSideBySideLayout(group)` for each group.
- Merge the resulting `{left, width}` map entries across all groups into a single lookup by `block.id`.
- For each block, render `<TimeBlockCard>` with:
  - `style` from `getEventStyle(block.start_time, block.end_time, startHour, hourHeight)`
  - `layoutLeft` and `layoutWidth` from the side-by-side layout map
  - `activeId` forwarded as-is
  - `position: absolute`, `z-index: 1`
- Blocks in the `hidden` array from `getSideBySideLayout` (when a group has >3) are not rendered inline. Instead, the third column slot renders a `+N more` indicator badge that opens a popover listing the hidden blocks. (The popover contents can be a simple `<ul>` of block titles for now.)

---

### DayGrid

**File:** `client/components/portal/calendar/DayGrid.tsx`

**Props:**
```typescript
interface DayGridProps {
  date: string
  timeBlocks: AgentTimeBlock[]
  hourHeight: number
  startHour: number
  endHour: number
  snapMinutes: number
  activeId: string | null
}
```

**Structure:**
- Outer: `overflow-y: auto`, `flex: 1`, has a `ref` for scroll management
- Inner flex row: `<TimeGutter>` (fixed ~48px width) + `<DayColumn>` (flex: 1)
- On mount (`useEffect`): compute `scrollTop` for the current time (or 8 AM as a reasonable default when current time is outside range) and call `scrollContainerRef.current.scrollTo({ top: scrollTop, behavior: 'instant' })`.

---

### WeekGrid

**File:** `client/components/portal/calendar/WeekGrid.tsx`

**Props:**
```typescript
interface WeekGridProps {
  weekDays: string[]              // 5 ISO date strings, Mon–Fri
  timeBlocksByDate: Record<string, AgentTimeBlock[]>  // keyed by ISO date
  hourHeight: number
  startHour: number
  endHour: number
  snapMinutes: number
  activeId: string | null
  onDaySelect: (date: string) => void  // fires when a column header is clicked
}
```

**Structure:**
- Outer: `overflow-y: auto`, `flex: 1`, single shared scroll container for all columns
- Column headers row (sticky or fixed above the scroll area): one header per day showing the day abbreviation + date number, e.g. "Mon 23". Clicking fires `onDaySelect(date)`.
- Inner flex row: `<TimeGutter>` (once) + five `<DayColumn>` instances, each `flex: 1`.
- All five columns and the `TimeGutter` are inside the same scroll container so they scroll together.
- On mount: same current-time scroll behavior as `DayGrid`.

**Column header formatting:** Given ISO date "2026-03-23", display "Mon 23". Use `new Date(date)` with `toLocaleDateString('en-US', { weekday: 'short', day: 'numeric' })` or equivalent.

---

## Integration Notes

**`clientYToTimeSlot` usage:** `DayColumn` does not call this function itself. It exposes a `ref` (via `useDroppable`'s `setNodeRef`) so that `SchedulingEngine.onDragEnd` can call `columnRef.current.getBoundingClientRect().top` and pass it to `clientYToTimeSlot`. This keeps the time-slot resolution logic in one place (the DnD handler) rather than distributed across columns.

**`crossColumnOverride` from SchedulingEngine:** When `SchedulingEngine` detects a cross-column drag in `onDragOver`, it overrides the `displayBlocks` prop for the source and target `DayColumn` to give visual feedback. `DayColumn` is unaware of this — it simply renders whatever `displayBlocks` it receives. This means `DayColumn` is a pure renderer with no internal block-state management.

**Scroll synchronization in WeekGrid:** The `TimeGutter` labels are inside the same scrollable flex container as the columns, so they scroll together naturally. No JavaScript scroll-sync needed.

---

## Edge Cases

- **Block extends past `endHour`:** `getEventStyle` will return a `height` that extends past the column's bottom. Clip visually using `overflow: hidden` on the column container. The `end_time` stored in the block is not modified.
- **Block starts before `startHour`:** Similarly, `getEventStyle` may return a negative `top`. The column's `overflow: hidden` clips it. No error is thrown.
- **Empty column:** Grid lines and current time indicator still render. `useDroppable` is still active so tasks can be dropped.
- **Today vs. other days:** The current time indicator should only appear in today's `DayColumn`. Check `date === new Date().toISOString().slice(0, 10)` before rendering it.
- **`nowMinutes` outside `[startHour*60, endHour*60)`:** Do not render the indicator. Avoids the indicator appearing at the top or bottom of the grid for early-morning or late-night times.
- **Groups with exactly 3 blocks:** All three get equal-width columns, no `+N more` needed. The `+N more` indicator only appears when a group has 4 or more.
