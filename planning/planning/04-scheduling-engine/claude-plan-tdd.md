# TDD Plan: Interactive Scheduling Engine

**Testing stack:** Vitest 4.1.2 + React Testing Library + `@testing-library/jest-dom`
**Config:** `client/vitest.config.ts` — jsdom environment, globals: true
**Pattern:** Test files alongside components — `ComponentName.test.tsx`, or in `utils/__tests__/`
**Mocking:** `vi.mock()` for API calls, `QueryClient` wrapper for React Query, stub out `@dnd-kit/core` for component tests

---

## Section 1: DaySchedule Refactor (Configurable Layout Props)

Write tests BEFORE adding the new props:

- Test: `DaySchedule` renders with no new props → layout unchanged (snapshot or dimension check matching current 50px/0–24h)
- Test: `DaySchedule` with `hourHeight=60, startHour=6, endHour=22` renders only 6AM–10PM hour labels
- Test: `DaySchedule` with custom `hourHeight` positions a time block at the correct pixel offset (e.g., block at 7:00 with 60px/hr → top = 60px from 6AM)
- Test: `CommandCenter` renders without errors after DaySchedule prop refactor (import + render check)

---

## Section 2: Shared Utilities

Write tests BEFORE using utilities anywhere else. These are pure functions — no mocks needed.

**`timeUtils.ts`:**
- Test: `timeToMinutes("06:00")` → 360
- Test: `timeToMinutes("06:00:00")` → 360 (handles "HH:MM:SS" format)
- Test: `timeToMinutes("00:00")` → 0
- Test: `timeToMinutes("23:59")` → 1439
- Test: `minutesToTime(360)` → "06:00"
- Test: `minutesToTime(0)` → "00:00"
- Test: `minutesToTime(1439)` → "23:59"
- Test: `snapToSlot(45, 30)` → 30 (rounds down to nearest 30min)
- Test: `snapToSlot(46, 30)` → 60 (rounds up)
- Test: `snapToSlot(0, 15)` → 0
- Test: `minutesToPx(60, 60)` → 60
- Test: `minutesToPx(30, 60)` → 30
- Test: `pxToMinutes(60, 60)` → 60
- Test: `getEventStyle("06:00", "07:00", 6, 60)` → `{top: 0, height: 60}`
- Test: `getEventStyle("07:30", "08:30", 6, 60)` → `{top: 90, height: 60}`
- Test: `formatHour(0)` → "12 AM"
- Test: `formatHour(6)` → "6 AM"
- Test: `formatHour(12)` → "12 PM"
- Test: `formatHour(22)` → "10 PM"
- Test: `isoDateToWeekDays("2026-03-25")` → ["2026-03-23", "2026-03-24", "2026-03-25", "2026-03-26", "2026-03-27"] (Mon–Fri)
- Test: `clientYToTimeSlot(clientY=60, columnTop=0, startHour=6, hourHeight=60, snapMinutes=30)` → `{hour: 7, minute: 0}`
- Test: `clientYToTimeSlot` snaps to nearest 30min increment

**`collisionUtils.ts`:**
- Test: `getOverlapGroups` with no blocks → empty array
- Test: `getOverlapGroups` with non-overlapping blocks → each in its own group
- Test: `getOverlapGroups` with two overlapping blocks → both in same group
- Test: `getOverlapGroups` with three-way overlap → all three in same group
- Test: `getSideBySideLayout` with 1 block → `{left: "0%", width: "100%"}`
- Test: `getSideBySideLayout` with 2 blocks → each `{left: "0%"/"50%", width: "50%"}`
- Test: `getSideBySideLayout` with 3 blocks → each gets `width: "33.33%"`
- Test: `getSideBySideLayout` with 4 blocks → first 2 get columns, 3rd+ are in `hidden` array
- Test: `getOverlapGroups` edge case — blocks that share only an endpoint (end == start) are NOT considered overlapping

**`calendarCollision.ts`:**
- Test: returns `pointerWithin` result when it is non-empty
- Test: falls back to `closestCenter` result when `pointerWithin` returns empty array

---

## Section 3: Data Hook — `useSchedulingEngine`

Write tests BEFORE wiring up components. Use `renderHook` + `QueryClientProvider` wrapper. Mock API calls with `vi.mock()`.

- Test: `useSchedulingEngine` fetches `getTimeBlocks` with the selected date on mount
- Test: `useSchedulingEngine` fetches `getGlobalTasks` with `scheduled_date + time_block: null` filter for today's tasks
- Test: `useSchedulingEngine` fetches `getGlobalTasks` with overdue filter (separate call)
- Test: `scheduleTask` calls `createTimeBlock` with correct `{date, start_time, end_time, title, client}` derived from task + slot
- Test: `scheduleTask` calls `updateGlobalTask` with `{time_block: newBlockId}` after block creation
- Test: `scheduleTask` optimistically adds block to cache before API resolves
- Test: `scheduleTask` rolls back optimistic update when `createTimeBlock` rejects
- Test: `moveBlock` calls `updateTimeBlock` with new `start_time` and `end_time`
- Test: `moveBlock` optimistically updates cache position before API resolves
- Test: `resizeBlock` calls `updateTimeBlock` with new `end_time`, minimum 15min duration enforced
- Test: `unscheduleBlock` calls `updateTimeBlock` to remove time_block reference + calls `updateGlobalTask`
- Test: `completeTask` calls `schedulingApi.completeGlobalTask` and removes task from `todayTasks`/`overdueTasks`
- Test: `dropToAllDay` calls `updateGlobalTask` with `{scheduled_date, time_block: null, start_time: null, end_time: null}`
- Test: `setSelectedDate` triggers re-fetch of timeBlocks for the new date
- Test: `setViewMode('week')` triggers fetch for 5-day date range
- Test: WebSocket subscription: when a `time_block_updated` event arrives, `queryClient.invalidateQueries` is called

---

## Section 4: SchedulingEngine (Root Component)

Write tests BEFORE connecting child components. Mock all children as stubs.

- Test: renders `<CalendarHeader>`, `<BacklogPane>`, `<CalendarGrid>`, `<StatusBar>` without crashing
- Test: `DndContext` is present in the rendered tree
- Test: `onDragCancel` resets `activeId` to null
- Test: `onDragEnd` with `!over` → no mutation called (cancelled drag)
- Test: `onDragEnd` with `backlog-task` active and `day-column` over → `scheduleTask` called
- Test: `onDragEnd` with `move-{id}` active and `day-column` over → `moveBlock` called
- Test: `onDragEnd` with `resize-{id}` active → `resizeBlock` called with delta-computed end time
- Test: `crossColumnOverride` is cleared on both `onDragEnd` and `onDragCancel`

---

## Section 5: CalendarHeader and Navigation

- Test: renders "Day" and "Week" toggle buttons
- Test: clicking "Week" calls `setViewMode('week')`
- Test: clicking "Week" persists to localStorage key `scheduler_view_mode`
- Test: `◀` button calls `setSelectedDate` with previous day (Day view) or previous week (Week view)
- Test: `▶` button advances date by 1 day or 1 week respectively
- Test: date picker input change calls `setSelectedDate` with the new value
- Test: Day view shows single date label; Week view shows Mon–Fri range label

---

## Section 6: BacklogPane

- Test: renders "Today's Tasks" section with tasks from `todayTasks`
- Test: renders "Overdue" section only when `overdueTasks.length > 0`
- Test: count badge shows correct total (todayTasks + overdueTasks)
- Test: search input filters displayed tasks by title (case-insensitive)
- Test: search shows tasks matching the query; hides non-matching tasks
- Test: week view accordion renders one section per day (Mon–Fri)
- Test: `activeColumnDate` prop change expands the matching day section
- Test: collapse toggle hides task list; shows ▶ to expand

**`BacklogTaskItem.tsx`:**
- Test: renders task title, client badge, priority border color
- Test: high priority → `border-red-500`; medium → `border-amber-400`; low → `border-gray-300`
- Test: checkbox click calls `completeTask(task.id)`
- Test: tasks are sorted: high priority first, then by due_date asc, then title asc

---

## Section 7: CalendarGrid, TimeGutter, AllDayHeader

**`TimeGutter.tsx`:**
- Test: renders hour labels from `startHour` to `endHour - 1`
- Test: labels positioned at correct `top` values using `minutesToPx`
- Test: `formatHour` output used for labels (e.g., "6 AM" not "6:00")

**`AllDayHeader.tsx`:**
- Test: renders all-day tasks as horizontal bars
- Test: tasks with `start_time = null AND scheduled_date = selectedDate` appear in header
- Test: renders minimum 48px height even when no all-day tasks
- Test: if > 3 all-day tasks, shows "Show N more" button
- Test: clicking "Show N more" opens a popover (not in-place expand)
- Test: drop zone highlights with accent tint when a draggable is over it (check `isOver` class)

---

## Section 8: DayColumn and Time Block Positioning

- Test: `DayColumn` renders a container with correct pixel height `(endHour - startHour) * hourHeight`
- Test: grid lines render at each hour mark
- Test: half-hour tick marks are present (lower opacity)
- Test: current time indicator renders at correct `top` offset (mock `new Date()`)
- Test: `useDroppable` called with `id: 'column-{date}'`
- Test: `DayColumn` passes computed `displayBlocks` (with side-by-side layout applied) to `TimeBlockCard` instances
- Test: `WeekGrid` renders 5 day columns (Mon–Fri)
- Test: clicking a day column header fires `onDaySelect` with that column's date
- Test: `DayGrid` auto-scrolls to current time on mount (check `scrollTo` mock called)

---

## Section 9: TimeBlockCard

- Test: renders block title and client/category name
- Test: `position: absolute` with `top` and `height` from `getEventStyle`
- Test: left border color matches `block.color`
- Test: background color is `block.color` at 10% opacity
- Test: when `activeId === 'move-{block.id}'`, card renders with `opacity: 0.5` and dashed border
- Test: when `activeId === 'resize-{block.id}'`, card renders with accent border color
- Test: resize handle div is present at bottom 6px with `cursor-ns-resize`
- Test: `onPointerDown` on resize handle stops propagation (prevents parent drag activation)
- Test: clicking card body (not handle) opens `TimeBlockEditor` modal

---

## Section 10: Drag-and-Drop Event Handler Logic

Integration-level tests for the full drag flow (stub API, use real DndContext):

- Test: drag from backlog + drop on `column-{date}` → `scheduleTask` called with correct time slot (computed from Y coordinate)
- Test: drag from backlog + cancel → `scheduleTask` NOT called; task still in backlog
- Test: drag block to different time on same day → `moveBlock` called with new times
- Test: drag block to different day column → `moveBlockToDay` called with new date + times
- Test: drag block to backlog zone → `unscheduleBlock` called
- Test: resize drag down 30px → `resizeBlock` with end time + 30 minutes
- Test: resize drag up — if result would be < 15min duration, clamped to minimum 15min
- Test: `onDragCancel` fires → `crossColumnOverride` is null, no mutation called

---

## Section 11: Portal Calendar Page

- Test: page renders `<SchedulingEngine>` without crashing
- Test: `?date=2026-03-28` query param initializes `selectedDate` to that date
- Test: missing `?date` param defaults to today's date
- Test: `agentType` from route params is passed to `SchedulingEngine`

---

## Section 12: StatusBar

- Test: shows correct "N tasks scheduled" count from `timeBlocks.length`
- Test: shows correct "N unscheduled" count from `todayTasks.length + overdueTasks.length`
- Test: "Xh Ym blocked" correctly sums `duration_minutes` across all time blocks
- Test: "0h 0m blocked" when no blocks
- Test: values update reactively when mock data changes

---

## Testing Utilities to Create

Before Section 1, create `client/test-utils/scheduling.tsx`:

```typescript
// Test wrapper with QueryClient
// Mock time blocks factory: createMockTimeBlock({ overrides })
// Mock global task factory: createMockGlobalTask({ overrides })
// Mock useSchedulingEngine return value
// renderWithQuery(component) helper
```

These factories prevent test brittleness when types change and make it easy to create test data with specific overlaps, priorities, etc.
