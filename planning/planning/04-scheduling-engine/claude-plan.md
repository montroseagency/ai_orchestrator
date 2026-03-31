# Implementation Plan: Interactive Scheduling Engine

## What We're Building

A purpose-built interactive scheduling calendar at the Management Portal route (`/management/calendar/`). The interface presents a split-view layout: a task backlog pane on the left and an hourly calendar grid on the right. Agents drag tasks from the backlog onto time slots to schedule them, resize time blocks, and move blocks between slots or days. The feature covers both Day and Week views, includes an All-Day header for time-agnostic tasks, and synchronizes with the server via optimistic React Query mutations and the existing WebSocket realtime service.

This calendar is **additive** — it coexists with the existing CommandCenter at `/schedule`. The old CommandCenter is not modified except for a minor refactor to DaySchedule that makes its layout props configurable.

---

## Context and Existing Codebase

The project is a Next.js + TypeScript frontend with a Django backend. The relevant layer for this feature is entirely in `client/`.

**What already exists and will be used:**
- `AgentTimeBlock`, `AgentGlobalTask`, `ScheduledTaskLink` types in `client/lib/types/scheduling.ts` — fully defined, no changes needed
- `schedulingApi.*` in `client/lib/api/scheduling.ts` — all required methods exist: `getTimeBlocks`, `createTimeBlock`, `updateTimeBlock`, `deleteTimeBlock`, `getGlobalTasks`, `updateGlobalTask`
- `@dnd-kit/core`, `@dnd-kit/sortable`, `@dnd-kit/utilities` — already installed
- `SCHEDULE_KEYS` query key object — hierarchical structure ready for targeted invalidation
- Design tokens in `globals.css` — `--color-accent-light`, `--color-border`, `--color-surface-subtle`, `--transition-fast`, `--shadow-lg`, etc.
- The calendar portal route placeholder at `client/app/dashboard/agent/{type}/management/calendar/page.tsx`

**What needs to change:**
- `DaySchedule.tsx` — add optional layout props with backward-compatible defaults (no behavior change for existing users)
- The calendar portal route placeholder — replace with the new `SchedulingEngine` component
- New component directory: `client/components/portal/calendar/`
- New hook: `client/lib/hooks/useSchedulingEngine.ts`

---

## Section 1: DaySchedule Refactor (Configurable Layout Props)

The existing `DaySchedule.tsx` uses hard-coded constants `HOUR_HEIGHT = 50`, `START_HOUR = 0`, `END_HOUR = 24`. The new portal calendar needs `HOUR_HEIGHT = 60`, `START_HOUR = 6`, `END_HOUR = 22`. Rather than forking the component, we add optional props with backward-compatible defaults.

**New props added to DaySchedule:**

```typescript
interface DayScheduleProps {
  // existing props...
  hourHeight?: number      // px per hour — default: 50
  startHour?: number       // first hour shown — default: 0
  endHour?: number         // last hour shown — default: 24
  snapMinutes?: number     // drag snap resolution — default: 60
}
```

All internal calculations that reference `HOUR_HEIGHT`, `START_HOUR`, `END_HOUR` switch to reading from the destructured props. Utility functions `timeToMinutes` and `minutesToTime` are extracted to `client/components/portal/calendar/utils/timeUtils.ts` so both DaySchedule and the new calendar can share them without circular imports.

**CommandCenter impact:** Zero. It passes no props, gets the same behavior as before. No changes needed to `CommandCenter.tsx`.

---

## Section 2: Shared Utilities

Before building any calendar components, extract reusable logic into `client/components/portal/calendar/utils/`.

**Timezone Strategy:** All times in this feature are treated as wall-clock local times. No timezone conversion is performed — `start_time`/`end_time` strings ("HH:MM:SS") are stored and returned by the backend as-is, matching the convention used throughout the existing codebase. Timezone support is explicitly out of scope for this split.

**`timeUtils.ts`** — Pure functions, no React dependencies:
- `timeToMinutes(time: string): number` — parses "HH:MM:SS" or "HH:MM" to total minutes
- `minutesToTime(minutes: number): string` — converts total minutes to "HH:MM"
- `snapToSlot(minutes: number, snapMinutes: number): number` — rounds to nearest snap increment
- `minutesToPx(minutes: number, hourHeight: number): number` — converts minutes offset to CSS pixels
- `pxToMinutes(px: number, hourHeight: number): number` — inverse of above
- `getEventStyle(startTime, endTime, startHour, hourHeight)` — returns `{top, height}` in px for absolutely-positioned blocks
- `formatHour(hour: number): string` — "6 AM", "12 PM", "2 PM"
- `isoDateToWeekDays(isoDate: string): string[]` — returns Mon-Fri date strings for the week containing isoDate
- `clientYToTimeSlot(clientY, columnTop, startHour, hourHeight, snapMinutes)` — converts a pointer Y coordinate (from `getBoundingClientRect`) to `{hour, minute}` snapped to `snapMinutes`; used in `onDragEnd` to determine drop target from pointer position

**`collisionUtils.ts`** — Overlap detection and side-by-side layout:
- `getOverlapGroups(blocks: AgentTimeBlock[]): AgentTimeBlock[][]` — groups blocks whose time ranges overlap; returns arrays of groups
- `getSideBySideLayout(group: AgentTimeBlock[]): Map<string, {left: string, width: string}>` — computes CSS left% and width% for each block in an overlap group. For groups of more than 3 blocks: first 2 blocks get standard columns, remaining blocks are designated "hidden" (not rendered inline); the third slot renders a "+N more" indicator that opens a popover. Returns a `{hidden: string[]}` marker for these blocks.

**`calendarCollision.ts`** — Custom collision detection algorithm:
- `calendarCollisionDetection(args)` — returns `pointerWithin(args)` if non-empty, else falls back to `closestCenter(args)`

---

## Section 3: Data Hook — `useSchedulingEngine`

All data fetching, mutations, and cache management for the scheduling engine live in one hook at `client/lib/hooks/useSchedulingEngine.ts`. Components consume this hook rather than calling React Query directly.

**What the hook manages:**

*Queries:*
- `timeBlocks` — fetches `AgentTimeBlock[]` for the selected date range (day: single date; week: Mon–Fri)
- `globalTasks` — fetches `AgentGlobalTask[]` in two filtered calls:
  - Today's tasks: `scheduled_date = selectedDate, time_block = null`
  - Overdue tasks: `scheduled_date < today, time_block = null` (plus tasks with no scheduled_date)
- Both queries use `staleTime: 30_000` and `refetchInterval: 60_000`

*Mutations (all with concurrent optimistic update pattern):*
- `scheduleTask(task, slot)` — creates time block + links task; optimistic add to timeBlocks cache
- `moveBlock(blockId, newSlot)` — updates block start/end; optimistic reposition in cache
- `moveBlockToDay(blockId, newDate, newSlot)` — cross-day move; updates date + times
- `resizeBlock(blockId, newEndTime)` — updates end_time; optimistic resize in cache
- `unscheduleBlock(blockId)` — removes time assignment; optimistic remove from blocks, add back to tasks
- `completeTask(taskId)` — marks task complete; removes from backlog
- `dropToAllDay(taskId, date)` — sets scheduled_date, clears time_block and start/end times

**Optimistic update pattern** (all mutations follow this structure):
- `mutationKey: ['timeBlocks']` or `['globalTasks']` for scoped isMutating check
- `onMutate`: cancel in-flight queries, snapshot current cache, apply optimistic state, return snapshot
- `onError`: restore snapshot, show `toast.error()`
- `onSettled`: check `queryClient.isMutating({ mutationKey }) === 1` before invalidating (defers until last concurrent mutation settles)

**WebSocket integration:**
- Subscribe to the existing realtime socket in a `useEffect` inside the hook
- Listen for `time_block_updated`, `time_block_created`, `time_block_deleted`, `global_task_updated` events
- On event: `queryClient.invalidateQueries({ queryKey: SCHEDULE_KEYS.timeBlocks.all })`
- Unsubscribe on unmount

**Hook returns:**
- `timeBlocks: AgentTimeBlock[]`
- `todayTasks: AgentGlobalTask[]`
- `overdueTasks: AgentGlobalTask[]`
- `isLoading: boolean`
- All mutation functions listed above
- `selectedDate: string`, `setSelectedDate(date: string)`
- `viewMode: 'day' | 'week'`, `setViewMode`
- `weekDays: string[]` — Mon–Fri ISO dates for current week

---

## Section 4: SchedulingEngine (Root Component)

`SchedulingEngine.tsx` is the top-level component rendered by the portal calendar page. It owns the `<DndContext>` that wraps everything, handles drag lifecycle events, and composes the layout.

**Responsibilities:**
- Holds `activeId` / `activeData` state for the currently dragged item
- Configures `<DndContext>` with:
  - Custom `calendarCollisionDetection`
  - `sensors` with `PointerSensor` (distance: 8 activation constraint) + `KeyboardSensor`
  - `createSnapModifier(30)` for 30-minute snap (at 60px/hr → 30px/slot)
- `onDragStart`: sets `activeId` and `activeData` to show `<DragOverlay>` preview
- `onDragOver`: for week view, detects cross-column movement and triggers optimistic re-parent in local state
- `onDragEnd`: routes to the correct mutation based on `active.data.current.type`:
  - `backlog-task` dropped on column (use pointer Y → `clientYToTimeSlot` to determine slot): call `scheduleTask`
  - `backlog-task` dropped on `allday` zone: call `dropToAllDay`
  - `move-{id}` dropped on column: call `moveBlock` or `moveBlockToDay` (Y coordinate → time slot)
  - `move-{id}` dropped on backlog: call `unscheduleBlock`
  - `resize-{id}`: `delta.y` → `deltaMinutes` (snapped to 15min) → `resizeBlock`
  - Clear the `crossColumnOverride` state
- `onDragCancel`: clear `activeId`, `activeData`, and `crossColumnOverride` state (ensures cancelled drags fully reset visual state)
- Renders `<DragOverlay>` with a non-draggable preview of the active item
- Composes: `<CalendarHeader>` + `<div class="split-view">` containing `<BacklogPane>` and `<CalendarGrid>` + `<StatusBar>`

---

## Section 5: CalendarHeader and Navigation

`CalendarHeader.tsx` — the top bar of the calendar.

**Elements:**
- Title: "Calendar"
- Day/Week segmented control: clicking toggles `viewMode` in the hook, persists to `localStorage` key `scheduler_view_mode`
- `◀ ▶` nav arrows: call `setSelectedDate` advancing by 1 day (Day view) or 7 days (Week view)
- `📅` date picker: `<input type="date">` or headless UI equivalent; calls `setSelectedDate` on change
- Date display: "March 28, 2026" (Day) or "Mar 24 – 28, 2026" (Week)

The selected date is reflected in the URL query param `?date=2026-03-28` for shareable links. On load, the page reads this param to initialize `selectedDate`.

---

## Section 6: BacklogPane

`BacklogPane.tsx` — the left panel (~250px, collapsible).

**Day View:**
- `<BacklogSection title="Today's Tasks" tasks={todayTasks} />`
- `<BacklogSection title="Overdue" tasks={overdueTasks} />` (conditional — hidden if empty)
- Count badge at top: "N unscheduled" (sum of both sections)

**Week View — Accordion:**
- One `<BacklogSection>` per day (Mon–Fri), each collapsible
- `expandedDay` state tracks which section is open
- When `activeColumnDate` prop changes (user clicked a day column), set `expandedDay` to that date and scroll that section into view

**Search bar:**
- `<input type="search">` at the top
- Client-side filter on `task.title` (case-insensitive includes)
- Filters across all visible sections simultaneously

**Collapse toggle:**
- `◀` button on the right edge of the pane
- Collapses to ~40px icon strip; `▶` button expands it back
- Collapse state in `localStorage` key `scheduler_backlog_collapsed`

**Backlog sort order:** Within each section, tasks are sorted: priority desc (high → medium → low), then `due_date` asc (soonest first, nulls last), then `title` asc. Computed client-side via `useMemo`.

**`BacklogTaskItem.tsx`:**
- Uses `useDraggable({ id: task.id, data: { type: 'backlog-task', task } })`
- `touch-action: none` only on the grip handle element (⠿ icon), not the whole card
- Left border color indicates priority: high=`border-red-500`, medium=`border-amber-400`, low=`border-gray-300`
- Client/category badge: small colored dot + `task_category_detail.name` or `client_name`
- Checkbox: calls `completeTask(task.id)` on change; task fades out on completion

---

## Section 7: CalendarGrid, TimeGutter, AllDayHeader

`CalendarGrid.tsx` — thin router: renders `<DayGrid>` or `<WeekGrid>` based on `viewMode`. Passes layout constants down as props.

**Layout constants passed as props:**
- `hourHeight = 60`
- `startHour = 6`
- `endHour = 22`
- `snapMinutes = 30`

`TimeGutter.tsx` — the left column of hour labels:
- Renders one label per hour from `startHour` to `endHour`
- Each label positioned at `top: minutesToPx((hour - startHour) * 60, hourHeight)`
- Label text: `formatHour(hour)` — "6 AM", "7 AM", ..., "10 PM"
- Width: ~48px, right-aligned text

`AllDayHeader.tsx` — fixed-height row between the column headers and the scrollable grid:
- One `useDroppable({ id: 'allday-{date}', data: { type: 'allday', date } })` per day column
- Renders all-day tasks as horizontal bars with client color left border
- Minimum height: 48px (always a valid drop target even when empty)
- "Show N more" collapsed state if > 3 tasks — click opens a popover (not in-place expand) listing the remaining tasks; avoids layout shifts in the main calendar
- Highlight (`bg-accent-light/30`) when a draggable is over this area

---

## Section 8: DayColumn and Time Block Positioning

`DayColumn.tsx` — a single day's hourly grid. Used in both `DayGrid` (one column) and `WeekGrid` (five columns).

**Structure:**
- `position: relative` container, height = `(endHour - startHour) * hourHeight`
- Background grid lines rendered as absolutely-positioned `<div>` elements at each hour and half-hour mark
- Drop zone: **single `useDroppable` for the entire column** — `id: 'column-{date}'`, `data: { type: 'day-column', date }`. The exact time slot is calculated in `onDragEnd` using `clientYToTimeSlot(event.clientY, columnRef.getBoundingClientRect().top, startHour, hourHeight, snapMinutes)`. This avoids rendering ~32 droppable DOM nodes per column (160 total in week view) and is the recommended pattern for high-density grids.
- Time blocks rendered as `<TimeBlockCard>` positioned absolutely using `getEventStyle()`
- Current time indicator: `position: absolute`, `top: minutesToPx(nowMinutes - startHour*60, hourHeight)`, a red line

**Overlap handling:** Before rendering, `getOverlapGroups(timeBlocks)` is called and `getSideBySideLayout()` provides `{left, width}` CSS values per block. These are passed as props to each `<TimeBlockCard>`.

`DayGrid.tsx` — wraps `TimeGutter` and one `DayColumn` in a flex row, within a `overflow-y: auto` scrollable container. Auto-scrolls to current time on mount.

`WeekGrid.tsx` — wraps `TimeGutter` and five `DayColumn` components (Mon–Fri) in a flex row. All columns share the same scroll container. Clicking a column header fires `onDaySelect(date)` which bubbles up to set `activeColumnDate` in `BacklogPane`.

---

## Section 9: TimeBlockCard

`TimeBlockCard.tsx` — the rendered time block inside the grid.

**Visual design:**
- `position: absolute` (top/height from `getEventStyle`, left/width from collision layout)
- `rounded-lg p-2 text-sm border-l-4` where border color = `block.color` (client/category color)
- Background: block color at 10% opacity
- Title: `font-medium text-text` (truncated to available height)
- Client/category: `text-xs text-secondary`
- Resize cursor hint: bottom 6px of the card shows `cursor-ns-resize` on hover

**Two draggables inside one card:**
1. Move handle: `useDraggable({ id: 'move-{block.id}', data: { type: 'move', blockId, block } })` — applied to the whole card except the resize handle zone
2. Resize handle: `useDraggable({ id: 'resize-{block.id}', data: { type: 'resize', blockId, originalEndTime } })` — applied to a `position: absolute; bottom: 0; height: 6px; width: 100%` div. Has `onPointerDown: (e) => e.stopPropagation()` to prevent the parent move drag from starting.

**Active state:** When this card is being moved (`activeId === 'move-{block.id}'`), renders with `opacity: 0.5` and `border: 2px dashed` to show the "ghost in place" while DragOverlay shows the preview.

**Resize active state:** Border turns accent color during resize (tracked by `activeId === 'resize-{block.id}'`).

**Click to edit:** Clicking the card body (not drag or resize handles) opens `<TimeBlockEditor>` modal with the block pre-populated. `TimeBlockEditor` is kept as-is from the existing codebase.

---

## Section 10: Drag-and-Drop Event Handler Logic

All drag events are handled in `SchedulingEngine.tsx`. The logic is:

**`onDragStart({ active })`:**
- Set `activeId = active.id`
- Set `activeData = active.data.current`
- For resize handles: record `dragStartY = event.clientY` and `originalEndMinutes` from the block

**`onDragOver({ active, over })`** (week view cross-column only):
- If `active.data.current.type === 'move'` and the target column's date differs from the active block's date
- Set `crossColumnOverride: { blockId, targetDate }` in a separate `useState` inside `SchedulingEngine`
- `DayColumn` receives a merged `displayBlocks` prop: query data for that date, with the override block inserted (and removed from the source column's display list)
- This gives visual feedback without touching the React Query cache — the real mutation fires in `onDragEnd`
- Both `onDragEnd` and `onDragCancel` reset `crossColumnOverride` to `null`

**`onDragEnd({ active, over, delta })`:**
- Clear `activeId`, `activeData`
- If `!over`: no-op (cancel, spring back)
- Route based on `active.data.current.type`:

  *`backlog-task`*:
  - over `time-slot` → `scheduleTask(task, { date: over.data.current.date, hour: over.data.current.hour, minute: over.data.current.minute })`
  - over `allday` → `dropToAllDay(task.id, over.data.current.date)`

  *`move`* (existing block):
  - over `time-slot` on same date → `moveBlock(blockId, newSlot)`
  - over `time-slot` on different date → `moveBlockToDay(blockId, newDate, newSlot)`
  - over backlog zone → `unscheduleBlock(blockId)`

  *`resize`*:
  - Compute `deltaPx = delta.y`; `deltaMinutes = pxToMinutes(deltaPx, hourHeight)` (snapped to 15min)
  - `newEndMinutes = originalEndMinutes + deltaMinutes`; minimum = `startMinutes + 15`
  - `resizeBlock(blockId, minutesToTime(newEndMinutes))`

---

## Section 11: Portal Calendar Page

`client/app/dashboard/agent/[type]/management/calendar/page.tsx` replaces the current placeholder.

The page is a standard Next.js page component. It:
- Reads `type` from route params to determine agent type (marketing/developer)
- Reads `?date=` query param to initialize `selectedDate`
- Renders `<SchedulingEngine agentType={type} initialDate={date} />`
- The page itself has no data fetching — all data ownership is in `useSchedulingEngine`

The route works for both `marketing` and `developer` agent types. The `agentType` prop is passed down to API calls that require it (e.g., filtering task categories by department).

---

## Section 12: StatusBar

`StatusBar.tsx` — the bottom summary strip:

```
3 tasks scheduled · 2 unscheduled · 5.5h blocked
```

All values computed client-side from the data already in the hook:
- "N tasks scheduled" = `timeBlocks.length` for the selected date
- "N unscheduled" = `todayTasks.length + overdueTasks.length`
- "Xh Ym blocked" = sum of all block durations (from `block.duration_minutes`)

No additional API call. Rendered as a `<footer>` below the split view.

---

## Error States and Edge Cases

**Empty states:**
- Empty backlog: "No tasks scheduled for this day" with a subtle illustration or icon
- Empty grid: Grid lines still render; user can still drop tasks onto empty slots
- No time blocks: Grid renders normally with just the current time indicator

**API errors:**
- All mutations roll back optimistically on error via the snapshot in `onError`
- `toast.error()` with the API error message
- Failed drop: task snaps back to backlog with the spring animation from DragOverlay

**Loading states:**
- Initial load: grid and backlog show skeleton loaders (matching the dimensions of real content)
- Mutation in-progress: the affected block shows a subtle pulse animation

**Edge cases:**
- Drag to a slot before `startHour` (6 AM) or after `endHour` (10 PM): `restrictToParentElement` modifier on grid prevents this; if it somehow happens, snap to `startHour` / `endHour`
- Block extending past `endHour` (e.g., 9:30 PM block with 60min): render it but clip to `endHour` visually; `end_time` stores the real value
- Overlapping blocks beyond 3: third+ blocks get a "+N more" indicator

---

## Testing Plan (Overview)

Testing uses the existing Vitest 4.1.2 + React Testing Library setup (`client/vitest.config.ts`).

**Unit tests** (pure utilities — no mocks needed):
- `timeUtils.ts`: all exported functions, including edge cases (midnight wrap, DST ignorance)
- `collisionUtils.ts`: overlap detection with 2, 3, and 0 overlapping blocks

**Component tests** (mock React Query + mock @dnd-kit):
- `BacklogTaskItem`: renders with priority colors, calls `completeTask` on checkbox change
- `TimeBlockCard`: renders with correct positioning props, shows resize cursor zone
- `AllDayHeader`: renders all-day tasks, highlights on drag-over
- `StatusBar`: computes correct counts from mock data

**Integration tests** (mock API calls, real React Query):
- `useSchedulingEngine` hook: verify `scheduleTask` calls `createTimeBlock` and `updateGlobalTask` with correct args, verify optimistic cache update, verify rollback on error
- Drop flow: render `SchedulingEngine` with mock data, simulate a drag from backlog to grid, verify API calls and cache state

**TDD approach:** Write utility function tests first, then hook integration tests, then component tests. The utility tests can be written immediately as pure functions with known inputs/outputs.

---

## Implementation Order

The sections above are numbered to suggest implementation sequence:

1. Extract shared utilities (`timeUtils`, `collisionUtils`, `calendarCollision`) — tested before anything else
2. DaySchedule prop refactor — tiny change, verify CommandCenter still works
3. `useSchedulingEngine` hook — data layer, all mutations, WebSocket subscription
4. `SchedulingEngine` root + `CalendarHeader` — layout shell, navigation
5. `BacklogPane` + `BacklogTaskItem` — draggable task list
6. `TimeGutter` + `AllDayHeader` — non-interactive grid structure
7. `DayColumn` + `DayGrid` — single-day grid with drop zones and time block rendering
8. `TimeBlockCard` — move + resize handles
9. `WeekGrid` — multi-column layout reusing DayColumn
10. `BacklogPane` week accordion + cross-day DnD wiring
11. Portal page wrapper + URL param handling
12. `StatusBar`
13. Collision side-by-side layout
14. WebSocket event subscription (wired in `useSchedulingEngine`)
