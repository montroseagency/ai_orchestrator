<!-- PROJECT_CONFIG
runtime: typescript-npm
test_command: npm test
END_PROJECT_CONFIG -->

<!-- SECTION_MANIFEST
section-01-test-utils
section-02-shared-utils
section-03-dayschedule-refactor
section-04-data-hook
section-05-scheduling-engine
section-06-calendar-header
section-07-backlog-pane
section-08-grid-structure
section-09-day-column
section-10-time-block-card
section-11-portal-page
section-12-status-bar
END_MANIFEST -->

# Implementation Sections Index — Interactive Scheduling Engine

## Overview

12 sections implementing the full scheduling engine at `client/components/portal/calendar/` plus a refactored `DaySchedule.tsx` and the portal page entry point. The implementation is additive — existing `CommandCenter` and `DaySchedule` are not broken.

---

## Dependency Graph

| Section | Depends On | Blocks | Parallelizable |
|---------|------------|--------|----------------|
| section-01-test-utils | — | 04, 06, 07, 08, 09, 10, 12 | Yes |
| section-02-shared-utils | — | 03, 04, 08, 09, 10 | Yes |
| section-03-dayschedule-refactor | 02 | — | Yes (after 02) |
| section-04-data-hook | 01, 02 | 05, 06, 07, 08, 10, 12 | Yes (after 01+02) |
| section-05-scheduling-engine | 04, 06, 07, 08, 09, 10 | 11 | No (final root) |
| section-06-calendar-header | 04 | 05 | Yes (after 04) |
| section-07-backlog-pane | 01, 04 | 05 | Yes (after 04) |
| section-08-grid-structure | 01, 02, 04 | 05, 09 | Yes (after 04) |
| section-09-day-column | 01, 02, 08, 10 | 05 | After 08+10 |
| section-10-time-block-card | 01, 02, 04 | 05, 09 | Yes (after 04) |
| section-11-portal-page | 05 | — | After 05 |
| section-12-status-bar | 01, 04 | — | Yes (after 04) |

---

## Execution Order (Batches)

**Batch 1** — No dependencies (parallel):
- `section-01-test-utils`
- `section-02-shared-utils`

**Batch 2** — After Batch 1 (parallel):
- `section-03-dayschedule-refactor` (needs 02)
- `section-04-data-hook` (needs 01, 02)

**Batch 3** — After Batch 2 (parallel):
- `section-06-calendar-header` (needs 04)
- `section-07-backlog-pane` (needs 01, 04)
- `section-08-grid-structure` (needs 01, 02, 04)
- `section-10-time-block-card` (needs 01, 02, 04)
- `section-12-status-bar` (needs 01, 04)

**Batch 4** — After Batch 3 (after 08 + 10):
- `section-09-day-column` (needs 01, 02, 08, 10)

**Batch 5** — After Batch 4 (all prior sections complete):
- `section-05-scheduling-engine` (needs 04, 06, 07, 08, 09, 10)

**Batch 6** — After Batch 5:
- `section-11-portal-page` (needs 05)

---

## Section Summaries

### section-01-test-utils
Testing infrastructure for the scheduling feature. Creates `client/test-utils/scheduling.tsx` with `createMockTimeBlock()`, `createMockGlobalTask()`, `mockUseSchedulingEngine()`, and `renderWithQuery()` helpers. Written as pure TypeScript factories with no React dependencies beyond the test wrapper. These utilities are prerequisites for all component and hook tests.

### section-02-shared-utils
Pure utility functions in `client/components/portal/calendar/utils/`. Three files:
- `timeUtils.ts` — time parsing, pixel conversion, snap-to-slot, event positioning, hour formatting, week day generation, pointer-Y-to-timeslot conversion
- `collisionUtils.ts` — overlap group detection and side-by-side CSS layout computation for overlapping blocks
- `calendarCollision.ts` — custom `@dnd-kit` collision detection (pointerWithin with closestCenter fallback)

All functions are pure with no React dependencies. Write unit tests alongside.

### section-03-dayschedule-refactor
Add optional `hourHeight`, `startHour`, `endHour`, `snapMinutes` props to the existing `client/components/agent/scheduling/DaySchedule.tsx`. All props have backward-compatible defaults matching the current hard-coded constants (`50`, `0`, `24`, `60`). Internal calculations switch from constants to destructured props. Extract `timeToMinutes`/`minutesToTime` into `timeUtils.ts` (already done in section-02); update imports. CommandCenter passes no new props — zero behavior change verified by tests.

### section-04-data-hook
The data layer at `client/lib/hooks/useSchedulingEngine.ts`. Wraps all `schedulingApi.*` calls in React Query with:
- Two query calls for `timeBlocks` (date range) and `getGlobalTasks` (today + overdue)
- Seven mutations: `scheduleTask`, `moveBlock`, `moveBlockToDay`, `resizeBlock`, `unscheduleBlock`, `completeTask`, `dropToAllDay`
- Full optimistic update pattern for each mutation (cancel → snapshot → apply → onError rollback → onSettled invalidate)
- WebSocket subscription (`useEffect`) for `time_block_*` and `global_task_updated` events → `queryClient.invalidateQueries`
- State: `selectedDate`, `setSelectedDate`, `viewMode`, `setViewMode`, `weekDays`

### section-05-scheduling-engine
The root component at `client/components/portal/calendar/SchedulingEngine.tsx`. Owns `<DndContext>` with custom collision detection, PointerSensor (distance:8) + KeyboardSensor, and 30-min snap modifier. Handles all four drag lifecycle events:
- `onDragStart` — sets `activeId`/`activeData`, records `dragStartY` for resize
- `onDragOver` — cross-column override for week view visual feedback
- `onDragEnd` — routes to correct mutation via `active.data.current.type` routing (backlog-task/move/resize)
- `onDragCancel` — full state reset
Composes `<CalendarHeader>`, `<BacklogPane>`, `<CalendarGrid>`, `<StatusBar>` inside the `<DndContext>`. Also holds `<DragOverlay>` for drag previews.

### section-06-calendar-header
`client/components/portal/calendar/CalendarHeader.tsx`. Top bar with:
- Day/Week segmented toggle (localStorage key `scheduler_view_mode`)
- `◀ ▶` nav buttons (advance by 1 day or 7 days)
- `📅` date picker (`<input type="date">`)
- Date display string (single date for Day view, "Mon X – Fri Y" for Week view)
- URL query param `?date=` sync via `useSearchParams` and `useRouter`

### section-07-backlog-pane
`client/components/portal/calendar/BacklogPane.tsx` + `BacklogTaskItem.tsx`. Left panel (~250px, collapsible to 40px icon strip). Day view shows "Today's Tasks" + "Overdue" sections with count badge. Week view shows Mon–Fri accordion. Search bar filters across all visible sections. `BacklogTaskItem` uses `useDraggable` from `@dnd-kit` with `touch-action: none` only on the grip handle (⠿). Task items show priority border color, client badge, and checkbox. Tasks sorted: priority desc → due_date asc → title asc.

### section-08-grid-structure
Three components:
- `client/components/portal/calendar/CalendarGrid.tsx` — thin router: renders `<DayGrid>` or `<WeekGrid>` based on `viewMode`, passes layout constants as props
- `client/components/portal/calendar/TimeGutter.tsx` — left column of hour labels from `startHour` to `endHour`, positioned with `minutesToPx`, formatted with `formatHour`
- `client/components/portal/calendar/AllDayHeader.tsx` — fixed-height drop zone row; renders all-day task bars; `useDroppable` per day column; "Show N more" popover for >3 tasks; accent-tint highlight on drag-over

### section-09-day-column
Three components:
- `client/components/portal/calendar/DayColumn.tsx` — single day's grid. `position: relative` container at correct height. Single `useDroppable` for entire column. Renders grid lines + `<TimeBlockCard>` instances with side-by-side layout applied. Current time red line indicator.
- `client/components/portal/calendar/DayGrid.tsx` — TimeGutter + one DayColumn in flex row, inside `overflow-y: auto`. Auto-scrolls to current time on mount.
- `client/components/portal/calendar/WeekGrid.tsx` — TimeGutter + five DayColumns. Shared scroll container. Column header click fires `onDaySelect`.

### section-10-time-block-card
`client/components/portal/calendar/TimeBlockCard.tsx`. Absolutely-positioned card with:
- Position from `getEventStyle`, size from collision layout props
- Client color left border + background at 10% opacity
- Two `useDraggable` instances: move handle (whole card) + resize handle (bottom 6px div with `stopPropagation`)
- Active states: `opacity:0.5 + dashed border` during move; accent border during resize
- Click on card body opens `TimeBlockEditor` modal (existing component, unchanged)

### section-11-portal-page
`client/app/dashboard/agent/[type]/management/calendar/page.tsx` — replaces the current placeholder. Reads `type` from route params and `?date=` from search params. Renders `<SchedulingEngine agentType={type} initialDate={date} />`. No data fetching at the page level.

### section-12-status-bar
`client/components/portal/calendar/StatusBar.tsx`. Footer strip displaying:
- "N tasks scheduled" — `timeBlocks.length` for selected date
- "N unscheduled" — `todayTasks.length + overdueTasks.length`
- "Xh Ym blocked" — sum of `block.duration_minutes` across all blocks

All computed client-side from hook data via `useMemo`. No API calls.
