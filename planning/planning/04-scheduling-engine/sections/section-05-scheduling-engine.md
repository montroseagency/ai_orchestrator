# Section 05 — SchedulingEngine (Root Component)

## Overview

`SchedulingEngine.tsx` is the root component of the interactive calendar. It owns the `<DndContext>` that wraps the entire scheduling UI, handles all four drag lifecycle events, routes drag outcomes to the correct data mutations, and composes the full layout. This is the last component assembled before the portal page wrapper (`section-11`).

**File to create:** `client/components/portal/calendar/SchedulingEngine.tsx`

---

## Dependencies

This section requires all of the following to be complete before implementation:

- **section-04-data-hook** — `useSchedulingEngine` hook (data, mutations, state)
- **section-06-calendar-header** — `<CalendarHeader>` component
- **section-07-backlog-pane** — `<BacklogPane>` and `<BacklogTaskItem>` components
- **section-08-grid-structure** — `<CalendarGrid>`, `<TimeGutter>`, `<AllDayHeader>`
- **section-09-day-column** — `<DayColumn>`, `<DayGrid>`, `<WeekGrid>`
- **section-10-time-block-card** — `<TimeBlockCard>`
- **section-02-shared-utils** — `clientYToTimeSlot`, `pxToMinutes`, `minutesToTime`, `calendarCollisionDetection`

---

## Tests First

**File:** `client/components/portal/calendar/SchedulingEngine.test.tsx`

Mock all child components as stub divs. Use `vi.mock('@dnd-kit/core', ...)` to expose `onDragStart`, `onDragEnd`, `onDragCancel`, `onDragOver` callbacks through a test harness. Mock `useSchedulingEngine` to return controlled data and spies on each mutation function.

```typescript
// Stub signatures — write full test bodies

describe('SchedulingEngine', () => {
  it('renders CalendarHeader, BacklogPane, CalendarGrid, and StatusBar without crashing')

  it('DndContext is present in the rendered tree')

  it('onDragCancel resets activeId to null')

  it('onDragEnd with no over target does not call any mutation')

  it('onDragEnd with backlog-task active and day-column over calls scheduleTask')

  it('onDragEnd with move-{id} active and day-column over on same date calls moveBlock')

  it('onDragEnd with move-{id} active and day-column over on different date calls moveBlockToDay')

  it('onDragEnd with move-{id} active and backlog zone over calls unscheduleBlock')

  it('onDragEnd with resize-{id} active calls resizeBlock with delta-computed end time')

  it('onDragEnd with backlog-task active and allday zone over calls dropToAllDay')

  it('crossColumnOverride is cleared on onDragEnd')

  it('crossColumnOverride is cleared on onDragCancel')

  it('DragOverlay renders a preview of the active item during drag')
})
```

Run tests with `npm test -- SchedulingEngine` from `client/`.

---

## Implementation

### Component Signature

```typescript
interface SchedulingEngineProps {
  agentType: string
  initialDate?: string  // ISO date string, e.g. "2026-03-28"
}

export function SchedulingEngine({ agentType, initialDate }: SchedulingEngineProps)
```

### Internal State

Three pieces of local state managed inside `SchedulingEngine` (not in the hook):

```typescript
const [activeId, setActiveId] = useState<string | null>(null)
const [activeData, setActiveData] = useState<DragActiveData | null>(null)
const [crossColumnOverride, setCrossColumnOverride] = useState<{
  blockId: string
  targetDate: string
} | null>(null)
```

`dragStartY` for resize operations should be tracked in a `useRef` (not state) to avoid re-renders.

### DndContext Configuration

```typescript
const sensors = useSensors(
  useSensor(PointerSensor, { activationConstraint: { distance: 8 } }),
  useSensor(KeyboardSensor)
)

const snapModifier = createSnapModifier(30)  // 30px = 30 minutes at 60px/hr
```

Pass `sensors`, `snapModifier` (as `modifiers={[snapModifier]}`), and `calendarCollisionDetection` (as `collisionDetection`) to `<DndContext>`.

### `onDragStart`

```typescript
function handleDragStart({ active }: DragStartEvent) {
  setActiveId(active.id as string)
  setActiveData(active.data.current as DragActiveData)
  // For resize type: store dragStartY in the ref
}
```

### `onDragOver`

Only meaningful in week view for cross-column visual feedback. Do not call any mutations here.

```typescript
function handleDragOver({ active, over }: DragOverEvent) {
  if (!over) return
  const isMove = active.data.current?.type === 'move'
  const targetDate = over.data.current?.date
  const activeDate = active.data.current?.block?.date

  if (isMove && targetDate && targetDate !== activeDate) {
    setCrossColumnOverride({ blockId: active.data.current.blockId, targetDate })
  } else {
    setCrossColumnOverride(null)
  }
}
```

### `onDragEnd`

This is the core routing logic. Clear `activeId`/`activeData`/`crossColumnOverride` first, then route.

```typescript
function handleDragEnd({ active, over, delta }: DragEndEvent) {
  setActiveId(null)
  setActiveData(null)
  setCrossColumnOverride(null)

  if (!over) return  // cancelled drag — no mutation

  const type = active.data.current?.type

  if (type === 'backlog-task') {
    if (over.data.current?.type === 'day-column') {
      const slot = clientYToTimeSlot(/* pointer Y, column bounds, layout constants */)
      scheduleTask(active.data.current.task, { date: over.data.current.date, ...slot })
    } else if (over.data.current?.type === 'allday') {
      dropToAllDay(active.data.current.task.id, over.data.current.date)
    }
  }

  if (type === 'move') {
    if (over.data.current?.type === 'day-column') {
      const slot = clientYToTimeSlot(/* pointer Y, column bounds, layout constants */)
      if (over.data.current.date === active.data.current.block.date) {
        moveBlock(active.data.current.blockId, slot)
      } else {
        moveBlockToDay(active.data.current.blockId, over.data.current.date, slot)
      }
    } else if (over.data.current?.type === 'backlog') {
      unscheduleBlock(active.data.current.blockId)
    }
  }

  if (type === 'resize') {
    const deltaPx = delta.y
    const deltaMinutes = pxToMinutes(deltaPx, HOUR_HEIGHT)  // snapped to 15min inside resizeBlock
    const originalEndMinutes = active.data.current.originalEndMinutes
    const newEndMinutes = Math.max(
      active.data.current.startMinutes + 15,
      originalEndMinutes + deltaMinutes
    )
    resizeBlock(active.data.current.blockId, minutesToTime(newEndMinutes))
  }
}
```

Note: `clientYToTimeSlot` needs the column DOM element's bounding rect top. The column component should expose this via a `ref` callback or `data-column-top` attribute on the droppable container; `SchedulingEngine` reads it from `over.rect` which `@dnd-kit` provides on the `over` object.

Actually, `over.rect` from `@dnd-kit` gives the bounding rect of the droppable element directly — use `over.rect.top` as `columnTop` in `clientYToTimeSlot`.

### `onDragCancel`

```typescript
function handleDragCancel() {
  setActiveId(null)
  setActiveData(null)
  setCrossColumnOverride(null)
}
```

### `DragOverlay`

Renders a non-interactive visual preview of the currently dragged item. Use `activeData.type` to decide what to render:

- `backlog-task` → render a `<BacklogTaskItem>` in preview mode (no draggable wiring, `isDragOverlay` prop)
- `move` → render a `<TimeBlockCard>` in preview mode (no draggable wiring, `isDragOverlay` prop)
- `resize` → no overlay needed (resize is inline)

```typescript
<DragOverlay>
  {activeId && activeData?.type === 'backlog-task' && (
    <BacklogTaskItem task={activeData.task} isDragOverlay />
  )}
  {activeId && activeData?.type === 'move' && (
    <TimeBlockCard block={activeData.block} isDragOverlay />
  )}
</DragOverlay>
```

### Layout Structure

```tsx
return (
  <DndContext
    sensors={sensors}
    collisionDetection={calendarCollisionDetection}
    modifiers={[snapModifier]}
    onDragStart={handleDragStart}
    onDragOver={handleDragOver}
    onDragEnd={handleDragEnd}
    onDragCancel={handleDragCancel}
  >
    <div className="scheduling-engine">
      <CalendarHeader
        viewMode={viewMode}
        setViewMode={setViewMode}
        selectedDate={selectedDate}
        setSelectedDate={setSelectedDate}
        weekDays={weekDays}
      />
      <div className="split-view">
        <BacklogPane
          todayTasks={todayTasks}
          overdueTasks={overdueTasks}
          viewMode={viewMode}
          weekDays={weekDays}
          activeColumnDate={activeColumnDate}
          completeTask={completeTask}
        />
        <CalendarGrid
          viewMode={viewMode}
          selectedDate={selectedDate}
          weekDays={weekDays}
          timeBlocks={timeBlocks}
          crossColumnOverride={crossColumnOverride}
          activeId={activeId}
          onDaySelect={setActiveColumnDate}
        />
      </div>
      <StatusBar
        timeBlocks={timeBlocks}
        todayTasks={todayTasks}
        overdueTasks={overdueTasks}
        selectedDate={selectedDate}
      />
    </div>
    <DragOverlay>{/* preview rendering above */}</DragOverlay>
  </DndContext>
)
```

Note: `activeColumnDate` / `setActiveColumnDate` is a small piece of local state in `SchedulingEngine` tracking which day column was most recently clicked (used to sync the week-view `BacklogPane` accordion).

### Layout Constants

Define these as module-level constants in `SchedulingEngine.tsx` (they are passed down to grid components as props):

```typescript
const HOUR_HEIGHT = 60   // px per hour
const START_HOUR = 6     // 6 AM
const END_HOUR = 22      // 10 PM
const SNAP_MINUTES = 30
```

Pass these as props to `<CalendarGrid>` which passes them down to `<DayColumn>`.

### CSS

The component uses a `.scheduling-engine` class. The split view should be a flex row with:
- `BacklogPane` at fixed `~250px` width (collapsible)
- `CalendarGrid` filling remaining space with `flex: 1`
- Full height of the viewport minus header + status bar

Use design tokens from `globals.css` throughout: `--color-surface-subtle` for the grid background, `--color-border` for grid lines, `--color-accent-light` for drop zone highlights, `--shadow-lg` for DragOverlay.

---

## Prop Drilling Map

`crossColumnOverride` must flow from `SchedulingEngine` → `CalendarGrid` → `WeekGrid` → `DayColumn`. Each `DayColumn` checks if `crossColumnOverride.blockId` belongs to its column's date range and adjusts `displayBlocks` accordingly (adds block if it's the target column, removes block if it's the source column). This is purely visual; the actual block data in React Query cache is not touched until `onDragEnd`.

`activeId` must also flow to `DayColumn` → `TimeBlockCard` so cards can apply their active/ghost styling.

---

## Error Boundaries

Wrap `<SchedulingEngine>` internally in a simple React error boundary so a crash in one child component does not break the whole portal. The boundary renders a fallback with a "Reload calendar" button.

---

## Edge Cases

- If `over` is not null but `over.data.current` is undefined (e.g., dropped onto a DOM element with no droppable ID), treat as a cancelled drag — no mutation.
- If `delta.y` for a resize results in a block shorter than 15 minutes, clamp to `startMinutes + 15` before calling `resizeBlock`.
- If the pointer Y lands outside `startHour`–`endHour` bounds (before 6 AM or after 10 PM): `clientYToTimeSlot` should return a clamped value (`{hour: START_HOUR, minute: 0}` or `{hour: END_HOUR - 1, minute: 30}`). `SchedulingEngine` does not need to special-case this — the clamping happens inside the utility function.
- `onDragCancel` must also be called when the keyboard Escape key is pressed mid-drag — `@dnd-kit` fires `onDragCancel` automatically for this; no extra handling needed.
