# Combined Spec: Interactive Scheduling Engine

## Overview

Build a split-view interactive scheduling calendar at the Management Portal route `/management/calendar/`. The interface has a task backlog pane on the left and an hourly calendar grid on the right. Tasks drag from the backlog onto the timeline with ghosting, snap-to-slot, default duration assignment, and resize handles. Supports Day and Week views with full drag-and-drop. Includes an All-Day header, side-by-side collision resolution, and bi-directional sync via the existing WebSocket realtime service.

This is a **new portal-only feature** that coexists with the existing `/schedule` route (CommandCenter). The old CommandCenter is not replaced.

---

## Dependencies

- **Split 01 (Backend Restructuring):** Task API with scheduling fields — AgentGlobalTask, AgentTimeBlock, ScheduledTaskLink all exist and are ready
- **Split 02 (Portal Navigation):** Portal route at `/management/calendar/` — placeholder page exists, ready to replace

---

## Architecture Decisions (from research + interview)

### Coexistence with Old Schedule
The new portal calendar lives at `/dashboard/agent/{type}/management/calendar/`. The old CommandCenter at `/dashboard/agent/{type}/schedule/` continues to operate unchanged. No shared state between them beyond both reading from the same API.

### DaySchedule Refactor to Configurable Props
The existing `DaySchedule.tsx` is refactored to accept layout configuration via optional props with backward-compatible defaults:
- `hourHeight?: number` (default: 50) — pixel height per hour
- `startHour?: number` (default: 0) — first hour shown
- `endHour?: number` (default: 24) — last hour shown
- `snapMinutes?: number` (default: 60) — snap resolution

The new portal calendar passes: `hourHeight=60`, `startHour=6`, `endHour=22`, `snapMinutes=30`.
CommandCenter passes nothing — unchanged behavior.

### HOUR_HEIGHT in Portal Calendar: 60px
At 60px/hr, 1px = 1 minute. This simplifies all pixel-to-time math in the new components.

### Backlog Filter (Two Sections)
The backlog pane shows two groups:
1. **Today's Tasks:** `scheduled_date = selected_date AND time_block = null`
2. **Overdue:** `scheduled_date < today AND time_block = null` OR `scheduled_date = null AND no time_block`

In week view, the backlog shows all 5 days grouped by date in a collapsible accordion. Clicking a day column auto-expands that day's group and collapses others.

### Multi-Day Tasks
No date range fields needed. "Multi-day" tasks use `estimated_minutes` to span their duration across a single scheduled date. If a task genuinely needs to recur across multiple days, it uses the existing recurrence mechanism. This keeps the data model unchanged.

### Collision Resolution: Side-by-Side
When a block is dropped onto an occupied time slot, both blocks render in parallel columns within that slot (like Google Calendar). Visual width is split proportionally. This is not a block — the drop always succeeds. No displacement/auto-slide for this split.

### Realtime Sync: WebSocket
Calendar mutations broadcast via the existing `services/realtime/` service. Multi-tab sync: if another tab moves a block, the current view receives the update and refreshes the cache. Implemented via the existing `SocketContext` / realtime subscription hooks.

### Optimistic Updates
All calendar mutations use the TkDodo concurrent optimistic update pattern:
- `onMutate`: `cancelQueries` → `setQueryData` (optimistic) → return snapshot
- `onError`: rollback to snapshot + `toast.error()`
- `onSettled`: `isMutating({ mutationKey }) === 1` check → `invalidateQueries`

---

## Layout

```
┌─────────────────────────────────────────────────────────────────┐
│ Calendar                                   [Day] [Week] ◀ ▶ 📅 │
├──────────────────┬──────────────────────────────────────────────┤
│ BACKLOG          │ ALL-DAY HEADER                               │
│ 🔍 Search tasks  │ ─────────────────────────────────────────── │
│ ─────────────    │                                              │
│ Today's Tasks    │ 8:00  ┌──────────────────────────┐         │
│ □ Task A     ⠿  │       │  Design Review - Nike     │         │
│ □ Task B     ⠿  │       │  🎨 Design                │↕ resize│
│ □ Task C     ⠿  │ 9:00  └──────────────────────────┘         │
│                  │ 10:00 ┌────────┐┌────────┐  ← side-by-side │
│ ── Overdue ──    │       │ Task D ││ Task E │                  │
│ □ Task D     ⠿  │ 11:00 └────────┘└────────┘                 │
│                  │                                              │
│                  │ 12:00 ░░░░░ LUNCH ░░░░░                    │
├──────────────────┴──────────────────────────────────────────────┤
│ 3 tasks scheduled · 2 unscheduled · 5.5h blocked               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Detailed Requirements

### Backlog Pane (Left, ~250px wide, collapsible)

**Day View:**
- Section 1: "Today's Tasks" — `scheduled_date = selected_date AND time_block = null`
- Section 2: "Overdue" — `scheduled_date < today AND time_block = null`, plus undated tasks
- Count badge: "N unscheduled" at top
- Search bar (client-side filter of task titles)

**Week View — Accordion Hybrid:**
- Groups: Mon / Tue / Wed / Thu / Fri (one collapsible section per day)
- Each section shows that day's unscheduled tasks
- Clicking a day column in the calendar auto-expands that day's group and collapses others (with smooth animation)
- Search bar filters across all days

**Each task item:**
- Checkbox (quick complete — calls `schedulingApi.completeGlobalTask()`)
- Title (truncated, max 2 lines)
- Client badge (color dot + name from `task_category_detail` or `client_name`)
- Priority indicator (left border color: high=red, medium=amber, low=gray)
- Grip handle (⠿) as drag affordance
- `useDraggable({ id: task.id, data: { type: 'backlog-task', task } })`

### Hourly Grid (Right)

**Layout constants (new portal only):**
- `HOUR_HEIGHT = 60px` (1px = 1min)
- `START_HOUR = 6` (6 AM)
- `END_HOUR = 22` (10 PM)
- `SNAP_MINUTES = 30` (snap-to-slot: 30min default, 15min for resize)
- `SLOT_HEIGHT_PX = 30` (30min slot = 30px)

**Grid rendering:**
- Hour labels: `text-xs text-muted font-mono`, left-aligned in gutter column
- Grid lines at each hour: `border-b border-border-subtle`
- Half-hour tick marks: dashed, lower opacity
- Drop zones: `useDroppable({ id: 'slot-{date}-{hour}-{30|00}', data: { type: 'time-slot', date, hour, minute } })`
- Drop zone highlight on hover: `bg-accent-light/30`

**Current time indicator:**
- Horizontal `border-t-2 border-red-500` line with red dot on the left
- Auto-scrolls into view on mount (centered in viewport)
- Updates position every minute

### @dnd-kit Configuration

```typescript
const sensors = useSensors(
  useSensor(PointerSensor, { activationConstraint: { distance: 8 } }),
  useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
);

// Collision detection: pointerWithin primary, closestCenter fallback
function calendarCollisionDetection(args) {
  const ptr = pointerWithin(args);
  return ptr.length > 0 ? ptr : closestCenter(args);
}

// Snap modifier for 30min grid (30px slots at 60px/hr)
const snap30Min = createSnapModifier(30);
```

`<DndContext sensors={sensors} collisionDetection={calendarCollisionDetection} modifiers={[snap30Min]}>`

### Drag Interaction (Backlog → Grid)

1. **Grab:** `PointerSensor` activates after 8px movement. Element elevates (`shadow-lg`, slight scale)
2. **Drag:** Ghost clone in `<DragOverlay>` at 0.85 opacity. Original slot shows dotted outline
3. **Over grid:** Target slot highlights `bg-accent-light/30`. Ghost preview shows where block will land
4. **Drop:** Snaps to 30min slot. Default duration: 60 minutes.
   - Optimistic update: new block appears immediately in grid
   - API calls (in parallel): `createTimeBlock()` + `updateGlobalTask({ time_block: newBlockId })`
   - Task disappears from backlog
5. **Cancel (drop outside):** Task returns to backlog with spring animation (200ms)

### Resize Handles

- Each time block has two draggables: `move-{id}` (whole block) and `resize-{id}` (bottom 6px handle)
- Handle appearance: resize cursor on hover (`cursor-ns-resize`), bottom 6px of block
- Drag down: expand duration (snaps to 15min increments, minimum 15min)
- Drag up: contract duration (minimum 15min)
- On release: `updateTimeBlock({ end_time: newEndTime })` with optimistic update
- Visual: block border turns accent color during resize

### Move Existing Blocks

- Time blocks on the grid are also draggable (same `move-{id}` draggable)
- Drop on new slot: `updateTimeBlock({ start_time, end_time })` — optimistic update
- Drop on backlog: `updateTimeBlock({ time_block: null })` + `updateGlobalTask({ time_block: null })` — unschedules the task
- Collision: if slot is occupied, side-by-side layout (both blocks split width)

### Collision Resolution: Side-by-Side

When N blocks overlap a time range:
- Each block renders with `width: 100% / N`, positioned with `left: (index * 100/N)%`
- Detection: before rendering, group all blocks whose time ranges overlap
- Each group of M overlapping blocks gets equal column widths
- Maximum N: 3 (beyond 3, blocks stack in a "hidden" group with a "+N more" indicator)

### All-Day Header

- Sits between the date header and the hourly grid
- Fixed height, minimum 40px, expands for content
- Tasks with `start_time = null AND scheduled_date = selected_date` appear here
- Droppable area for backlog tasks: `useDroppable({ id: 'allday-{date}', data: { type: 'allday', date } })`
- Drop handler: `updateGlobalTask({ scheduled_date, time_block: null, start_time: null })`
- Tasks render as horizontal bars with client color + title
- "Show N more" if > 3 all-day tasks

### Week View

```
┌──────────────┬──────────┬──────────┬──────────┬──────────┬──────────┐
│ BACKLOG      │ Mon 24   │ Tue 25   │ Wed 26   │ Thu 27   │ Fri 28   │
│ [accordion]  │ ALL-DAY  │ ALL-DAY  │ ALL-DAY  │          │          │
│              │──────────│──────────│──────────│──────────│──────────│
│ ▸ Mon (2)    │ 8:00 ██  │ 8:00    │ 8:00 ██  │         │ 8:00 ██  │
│ ▾ Tue (1)    │ 9:00 ██  │ 9:00 ██  │          │ 9:00 ██ │          │
│   □ Task A   │ 10:00    │ 10:00 ██ │ 10:00 ██ │         │          │
│ ▸ Wed (0)    │ ...      │ ...      │ ...      │ ...      │ ...      │
└──────────────┴──────────┴──────────┴──────────┴──────────┴──────────┘
```

- 5 day columns (Mon–Fri). Weekend toggle (Sat/Sun) in header settings.
- Each column is a `useDroppable` container with per-slot dropzones
- `onDragOver`: optimistically re-parent event when crossing columns
- `<DragOverlay>` prevents visual flicker during cross-column moves
- Clicking a day column header: selects that column, expands its backlog accordion section
- Cross-day drop: `updateTimeBlock({ date: targetDate, start_time, end_time })`

### Day/Week Toggle

- Segmented control in header: "Day" | "Week"
- State persists in `localStorage` key: `scheduler_view_mode`
- Day view defaults to today; Week view defaults to current Mon–Fri week
- `◀ ▶` arrows move by 1 day (Day view) or 1 week (Week view)
- `📅` opens a date picker (headless UI or native `<input type="date">`) to jump to date
- URL reflects selected date: `?date=2026-03-28` — shareable links

### Bi-Directional Sync

**React Query layer:**
- All mutations use concurrent optimistic update pattern (TkDodo)
- Cache invalidation targets: `SCHEDULE_KEYS.timeBlocks.all`, `SCHEDULE_KEYS.globalTasks.all`
- `staleTime: 30_000`, `refetchInterval: 60_000`

**WebSocket layer:**
- Subscribe to existing `realtime` channel for `time_block_updated`, `global_task_updated` events
- On receive: call `queryClient.invalidateQueries()` to trigger re-fetch
- Integration point: `useEffect` subscribes via existing `SocketContext` hook

### Status Bar (Bottom)

```
3 tasks scheduled · 2 unscheduled · 5.5h blocked
```
- Computed from local query data (no extra API call)
- Updates reactively as blocks are added/moved

---

## Component Architecture

```
client/app/dashboard/agent/{type}/management/calendar/
└── page.tsx                         ← New portal calendar page

client/components/portal/calendar/
├── SchedulingEngine.tsx             ← Root DndContext wrapper, view toggle, date nav
├── BacklogPane.tsx                  ← Left panel, task sections/accordion
├── BacklogTaskItem.tsx              ← Individual draggable task
├── CalendarGrid.tsx                 ← Right panel, routes to DayGrid or WeekGrid
├── DayGrid.tsx                      ← Single-day hourly grid
├── WeekGrid.tsx                     ← 5-column week grid (reuses DayGrid columns)
├── DayColumn.tsx                    ← Single day column (used in both DayGrid/WeekGrid)
├── TimeGutter.tsx                   ← Hour labels on left
├── AllDayHeader.tsx                 ← All-day drop area
├── TimeBlockCard.tsx                ← Rendered time block (draggable + resize)
├── CalendarHeader.tsx               ← Day/Week toggle, nav arrows, date picker
├── StatusBar.tsx                    ← Bottom summary stats
└── utils/
    ├── timeUtils.ts                 ← timeToMinutes, minutesToTime, snapToSlot, etc.
    ├── collisionUtils.ts            ← Overlap detection, side-by-side layout math
    └── calendarCollision.ts        ← pointerWithin + closestCenter composite

client/lib/hooks/
└── useSchedulingEngine.ts           ← Aggregated data + mutations for the calendar
    (wraps getTimeBlocks + getGlobalTasks + all mutations + optimistic update logic)
```

**DaySchedule.tsx refactor:**
- Add optional configurable props (hourHeight, startHour, endHour, snapMinutes) with backward-compatible defaults
- No behavior changes to existing CommandCenter usage

---

## API Calls Summary

| User Action | API Call(s) |
|---|---|
| Drop backlog task → time slot | `createTimeBlock()` + `updateGlobalTask({ time_block })` |
| Drop backlog task → all-day header | `updateGlobalTask({ scheduled_date, time_block: null, start_time: null })` |
| Move existing block to new slot | `updateTimeBlock({ start_time, end_time })` |
| Move block to different day (week view) | `updateTimeBlock({ date, start_time, end_time })` |
| Drag block to backlog | `updateTimeBlock({ time_block: null })` + `updateGlobalTask({ time_block: null })` |
| Resize block | `updateTimeBlock({ end_time })` |
| Quick-complete task in backlog | `schedulingApi.completeGlobalTask(id)` |
| Delete time block | `deleteTimeBlock(id)` + `updateGlobalTask({ time_block: null })` |

---

## Out of Scope

- Task creation modal (Split 03)
- Dashboard KPI widget (Split 05)
- Admin views (Split 06)
- Offline support
- Displacement collision (auto-slide) — side-by-side only for this split
- Timezone conversion
- Weekend columns (toggle only, no custom logic)
