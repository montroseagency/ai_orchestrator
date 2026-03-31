# Section 08: Grid Structure — CalendarGrid, TimeGutter, AllDayHeader

## Overview

This section creates three components that form the structural shell of the calendar grid area. `CalendarGrid` is a thin routing component that delegates to `DayGrid` or `WeekGrid` based on the current view mode. `TimeGutter` renders the column of hour labels on the left edge of the grid. `AllDayHeader` is the fixed-height drop zone row that sits between the column headers and the scrollable hourly grid, accepting tasks that have a scheduled date but no specific time.

These components are in **Batch 3** of the execution order — they can be implemented in parallel with `section-06-calendar-header`, `section-07-backlog-pane`, `section-10-time-block-card`, and `section-12-status-bar` once `section-04-data-hook` (and its prerequisites `section-01-test-utils` + `section-02-shared-utils`) are complete.

`section-09-day-column` depends on this section — do not start it until this section passes all tests.

---

## Dependencies

- **section-01-test-utils** — provides `createMockTimeBlock`, `createMockGlobalTask`, `renderWithQuery`
- **section-02-shared-utils** — provides `minutesToPx`, `formatHour` from `timeUtils.ts`; `useDroppable` wrapping pattern established by `calendarCollision.ts`
- **section-04-data-hook** — provides `useSchedulingEngine` return shape, which dictates the prop interfaces consumed here

Do not copy implementation from those sections. Import from their established file paths.

---

## Files to Create

```
client/components/portal/calendar/CalendarGrid.tsx
client/components/portal/calendar/TimeGutter.tsx
client/components/portal/calendar/AllDayHeader.tsx
```

Tests sit alongside their components:

```
client/components/portal/calendar/CalendarGrid.test.tsx
client/components/portal/calendar/TimeGutter.test.tsx
client/components/portal/calendar/AllDayHeader.test.tsx
```

---

## Layout Constants

These constants are defined once in `CalendarGrid` and passed as props to all child components. They are not re-declared in children.

| Constant | Value | Description |
|---|---|---|
| `hourHeight` | `60` | Pixels per hour |
| `startHour` | `6` | First hour shown (6 AM) |
| `endHour` | `22` | Last hour shown (10 PM, exclusive) |
| `snapMinutes` | `30` | Drag snap resolution in minutes |

---

## Tests (Write These First)

### CalendarGrid

```typescript
// client/components/portal/calendar/CalendarGrid.test.tsx
```

- **renders DayGrid when viewMode is 'day'** — mount `<CalendarGrid>` with `viewMode="day"`. Assert `DayGrid` is rendered. Assert `WeekGrid` is not rendered.
- **renders WeekGrid when viewMode is 'week'** — mount with `viewMode="week"`. Assert `WeekGrid` is rendered. Assert `DayGrid` is not rendered.
- **passes layout constants to child grid** — confirm `hourHeight={60}`, `startHour={6}`, `endHour={22}`, `snapMinutes={30}` reach the child via props.

Mock `DayGrid` and `WeekGrid` as stubs returning identifiable `data-testid` divs so this test does not depend on their internal implementation.

### TimeGutter

```typescript
// client/components/portal/calendar/TimeGutter.test.tsx
```

- **renders hour labels from startHour to endHour - 1** — with `startHour=6, endHour=22, hourHeight=60`, the component renders exactly 16 labels (hours 6–21 inclusive).
- **labels use formatHour output** — label text is "6 AM", "7 AM", ..., "10 AM", "12 PM", "1 PM", ..., "9 PM". Not "6:00" or "06:00".
- **labels are positioned at correct top values** — for hour `h`, the rendered element's inline `top` style is `minutesToPx((h - startHour) * 60, hourHeight)` pixels. Check at least hour 6 (`top: 0px`) and hour 7 (`top: 60px`) and a midrange label.
- **renders nothing outside startHour–endHour range** — hour 0 ("12 AM") and hour 23 ("11 PM") are not present when `startHour=6, endHour=22`.

### AllDayHeader

```typescript
// client/components/portal/calendar/AllDayHeader.test.tsx
```

- **renders minimum 48px height even when no all-day tasks** — assert the container has `minHeight: 48` (or a class that sets it). This ensures a valid drop target is always present.
- **renders all-day tasks as horizontal bars** — pass `allDayTasks` containing two tasks with `start_time: null` and `scheduled_date: selectedDate`. Assert both are rendered as bars inside the header.
- **shows "Show N more" button when more than 3 tasks present** — pass 5 tasks. Assert only 3 bars rendered and a button with text "Show 2 more" is visible. The button text should reflect the hidden count.
- **clicking "Show N more" opens a popover** — simulate click on "Show 2 more". Assert a popover/overlay element appears listing the remaining 2 tasks. Assert the existing 3 bars are still in the DOM (no in-place expand — the main layout must not shift).
- **drop zone highlights when a draggable is over it** — mock `useDroppable` to return `isOver: true` for the drop zone. Assert the element receives the accent-tint highlight class or inline style (e.g. a `bg-accent-light/30` class or equivalent CSS variable).
- **drop zone does NOT highlight when isOver is false** — mock `useDroppable` to return `isOver: false`. Assert the highlight class/style is absent.
- **renders one drop zone per day column in week view** — pass `dates={["2026-03-23", "2026-03-24", "2026-03-25", "2026-03-26", "2026-03-27"]}`. Assert `useDroppable` is called with `id: 'allday-2026-03-23'`, ..., `'allday-2026-03-27'` — one per date.
- **useDroppable called with correct data shape** — assert each droppable is registered with `data: { type: 'allday', date }` where `date` matches the column date.

---

## Implementation Details

### CalendarGrid.tsx

`CalendarGrid` is a thin conditional router. It does not contain any business logic, layout calculation, or data fetching.

**Props interface:**

```typescript
interface CalendarGridProps {
  viewMode: 'day' | 'week'
  selectedDate: string         // ISO date string, e.g. "2026-03-28"
  weekDays: string[]           // Mon–Fri ISO dates for the current week
  timeBlocks: AgentTimeBlock[]
  allDayTasks: AgentGlobalTask[]
  onDaySelect: (date: string) => void
  crossColumnOverride: { blockId: string; targetDate: string } | null
}
```

**Behavior:** Defines the layout constants (`hourHeight`, `startHour`, `endHour`, `snapMinutes`) and passes them as props alongside the data props to whichever child grid is rendered. The component itself is a single conditional render — no state, no effects.

**Rendered output structure (conceptual):**

```
<div className="calendar-grid-container">
  {viewMode === 'day'
    ? <DayGrid ... hourHeight={60} startHour={6} endHour={22} snapMinutes={30} />
    : <WeekGrid ... hourHeight={60} startHour={6} endHour={22} snapMinutes={30} />
  }
</div>
```

`DayGrid` and `WeekGrid` are implemented in `section-09-day-column`. Stub-import them for now — `CalendarGrid` just needs to reference and forward props.

---

### TimeGutter.tsx

`TimeGutter` renders the vertical strip of hour labels on the left edge of the hourly grid. It has no interactivity — it is purely presentational.

**Props interface:**

```typescript
interface TimeGutterProps {
  startHour: number    // e.g. 6
  endHour: number      // e.g. 22 (exclusive — last label is endHour - 1)
  hourHeight: number   // px per hour, e.g. 60
}
```

**Layout:**
- The gutter is `position: relative`, width ~48px, right-aligned text.
- The total height of the gutter matches the grid height: `(endHour - startHour) * hourHeight` pixels.
- Each label is `position: absolute`, `top: minutesToPx((hour - startHour) * 60, hourHeight)`.
- Label text: `formatHour(hour)` — imported from `client/components/portal/calendar/utils/timeUtils.ts`.
- Render labels for `hour` in `[startHour, startHour+1, ..., endHour-1]`. Do not render a label at `endHour` itself (the grid ends there).

**Visual guidance:**
- Font size: `text-xs`.
- Color: secondary/muted text (use design token `--color-text-secondary` or Tailwind `text-secondary`).
- Each label should be offset slightly so the baseline of the text aligns with the corresponding grid line (typically `-0.5em` or `-8px` translateY, depending on the grid line approach).

---

### AllDayHeader.tsx

`AllDayHeader` sits between the date column headers and the scrollable hourly grid. It serves as a persistent drop target for tasks that should be scheduled for a day but without a specific time.

**Props interface:**

```typescript
interface AllDayHeaderProps {
  dates: string[]                // one entry per visible day column
  allDayTasks: AgentGlobalTask[] // tasks with start_time = null for visible dates
  selectedDate: string
}
```

**Drop zone registration:**
- For each entry in `dates`, call `useDroppable({ id: \`allday-\${date}\`, data: { type: 'allday', date } })`.
- Because `useDroppable` must be called unconditionally, the per-column drop zones should be handled inside a child component `AllDayCell` that wraps one column's drop zone:

```typescript
// internal sub-component
function AllDayCell({ date, tasks }: { date: string; tasks: AgentGlobalTask[] }) {
  const { setNodeRef, isOver } = useDroppable({
    id: `allday-${date}`,
    data: { type: 'allday', date },
  })
  // ...render tasks and apply isOver highlight
}
```

**Task bar rendering:**
- Each all-day task renders as a horizontal bar spanning the full column width.
- Left border uses the task's client/category color.
- Text: `task.title`, truncated with `text-ellipsis overflow-hidden whitespace-nowrap`.
- If there are more than 3 tasks for a column, render 3 bars and a "Show N more" button.

**"Show N more" popover behavior:**
- Clicking the button opens a floating popover (not an inline expand). Use a `useState` toggle + absolutely positioned popover div, or a headless UI Popover. The popover lists the remaining tasks by title.
- The popover must not cause layout shifts in the surrounding calendar. Keep it `position: absolute` or `position: fixed`, not `position: relative` in the document flow.

**Highlight on drag-over:**
- When `isOver` is `true` for a cell, apply a background tint: the CSS variable `--color-accent-light` at 30% opacity, e.g. Tailwind class `bg-accent-light/30` if defined, or inline style `backgroundColor: 'color-mix(in srgb, var(--color-accent-light) 30%, transparent)'`.
- When `isOver` is `false`, no background tint.

**Minimum height:**
- The header must be at least 48px tall even when there are no all-day tasks. This ensures the drop zone is always large enough to receive a dragged item. Use `minHeight: 48` (CSS) or equivalent Tailwind.

---

## Integration Notes

- `AllDayHeader` receives `allDayTasks` filtered by the parent (`SchedulingEngine` or `CalendarGrid`). Tasks qualify as all-day when `task.start_time === null && task.scheduled_date === date`. The filtering logic lives upstream — `AllDayHeader` just renders what it receives.
- `TimeGutter` and `AllDayHeader` are not connected to each other. They are siblings laid out by `DayGrid`/`WeekGrid` (section-09).
- The `dates` prop on `AllDayHeader` is either a single-element array (Day view) or a five-element array for Mon–Fri (Week view). `CalendarGrid` supplies this from `selectedDate` (day) or `weekDays` (week).
- No mutations fire from `AllDayHeader` directly. The `useDroppable` registration makes the zone detectable by `onDragEnd` in `SchedulingEngine`. The mutation call (`dropToAllDay`) is routed from there.

---

## Acceptance Criteria

- [ ] All TimeGutter tests pass: correct label count, correct top positions, correct text via `formatHour`
- [ ] All AllDayHeader tests pass: minimum height, task bar rendering, "Show N more" popover (no layout shift), drag-over highlight, correct droppable IDs and data shapes
- [ ] All CalendarGrid tests pass: correct child rendered for each viewMode, layout constants forwarded
- [ ] `CalendarGrid` does not break if `DayGrid`/`WeekGrid` are stubs (they are implemented in section-09)
- [ ] No TypeScript errors in the three new files
- [ ] `minutesToPx` and `formatHour` are imported from `client/components/portal/calendar/utils/timeUtils.ts` — not re-implemented
