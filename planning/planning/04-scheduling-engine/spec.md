# Spec: Interactive Scheduling Engine

## Summary

Build a split-view scheduling interface with an unscheduled backlog pane and an hourly calendar grid. Tasks drag from the backlog and drop onto the timeline with visual ghosting, snap-to-slot, default duration assignment, and resize handles. Support both Day and Week views with full drag-and-drop. Include an "All-Day" header for multi-day tasks and bi-directional API sync.

## Dependencies

- **Split 01 (Backend Restructuring):** Task API with scheduling fields
- **Split 02 (Portal Navigation):** Portal route at `/management/calendar/`

## Goals

1. **Split-view layout:** Left pane = unscheduled daily task backlog, Right pane = hourly calendar grid
2. **Drag-and-drop:** Tasks drag from backlog → grid with ghosting, snap, default 60min blocks
3. **Resize handles:** Expand/contract time blocks by dragging edges
4. **All-Day header:** Multi-day and time-agnostic tasks sit above the hourly grid
5. **Week view:** Full cross-day DnD — drag tasks across Monday-Friday
6. **Day/Week toggle:** Seamless switch preserving context
7. **Bi-directional sync:** Calendar changes → API → main dashboard reads updated data

## Existing Code to Refactor

### Components to Evolve
- `client/components/agent/scheduling/DaySchedule.tsx` — Already has @dnd-kit hourly grid. Refactor into split-view with backlog pane.
- `client/components/agent/scheduling/CommandCenter.tsx` — Currently wraps DaySchedule. Portal calendar page will replace this as the scheduling container.
- `client/components/agent/scheduling/WeeklyPlanView.tsx` — Weekly planning. Replace with interactive Week View calendar.
- `client/components/agent/scheduling/TimeBlockEditor.tsx` — Time block CRUD modal. Keep and enhance.

### Libraries Already Available
- `@dnd-kit/core`, `@dnd-kit/sortable`, `@dnd-kit/utilities` — Already in use

### Types to Use
- `AgentTimeBlock` — existing, includes date, start_time, end_time, client, is_completed
- `AgentGlobalTask` — with new fields from Split 01
- `ScheduledTaskLink` — links tasks to time blocks

### API to Use
- `schedulingApi.getTimeBlocks()` — GET time blocks for date range
- `schedulingApi.createTimeBlock()` — POST new block (on drop)
- `schedulingApi.updateTimeBlock()` — PATCH (on resize/move)
- `schedulingApi.deleteTimeBlock()` — DELETE
- `schedulingApi.getGlobalTasks()` — GET unscheduled tasks (scheduled_date=X, time_block=null)
- `schedulingApi.updateGlobalTask()` — PATCH to set time_block reference

## Detailed Requirements

### Split-View Layout

```
┌─────────────────────────────────────────────────────────────────┐
│ Calendar                                   [Day] [Week] ◀ ▶ 📅 │
├──────────────────┬──────────────────────────────────────────────┤
│ BACKLOG          │ ALL-DAY HEADER                               │
│ ─────────────    │ ┌─────────────────────────────────────────┐  │
│ □ Task A     ⠿  │ │ Multi-day task spanning Mon-Wed         │  │
│ □ Task B     ⠿  │ └─────────────────────────────────────────┘  │
│ □ Task C     ⠿  │ ────────────────────────────────────────────  │
│                  │ 8:00  ┌──────────────────────────┐          │
│ ── Overdue ──    │       │  Design Review - Nike     │          │
│ □ Task D     ⠿  │       │  🎨 Design                │          │
│                  │ 9:00  └──────────────────────────┘          │
│                  │       ┌──────────────────────────┐          │
│                  │       │  Copywriting - Adidas     │ ↕ resize│
│                  │ 10:00 └──────────────────────────┘          │
│                  │                                              │
│                  │ 11:00  (empty - drop zone highlighted)      │
│                  │                                              │
│                  │ 12:00  ░░░░░░░░ LUNCH ░░░░░░░░             │
│                  │                                              │
│                  │ 13:00                                        │
│                  │ ...                                          │
├──────────────────┴──────────────────────────────────────────────┤
│ 3 tasks scheduled · 2 unscheduled · 5.5h blocked               │
└─────────────────────────────────────────────────────────────────┘
```

### Backlog Pane (Left)

- Width: ~250px, collapsible
- Shows tasks for selected date that have NO time_block assigned
- Each task item shows:
  - Checkbox (quick complete)
  - Title (truncated)
  - Client badge (color dot + name)
  - Priority indicator
  - Grip handle (⠿) for drag affordance
- Sections: "Today's Tasks" / "Overdue" (grouped)
- Tasks are `useDraggable()` from @dnd-kit
- Count badge at top: "N unscheduled"

### Hourly Grid (Right)

- Time range: 6:00 AM – 10:00 PM (configurable)
- Slot height: 60px per hour (30min granularity for snapping)
- Each empty slot is a `useDroppable()` zone
- Existing time blocks rendered as positioned cards within the grid
- Grid lines: `border-b border-border-subtle` at each hour
- Current time indicator: horizontal red line with dot, auto-scrolls into view

### All-Day Header

- Sits between the date header and the hourly grid
- Contains tasks that are:
  - Multi-day tasks (span > 1 day)
  - Day-specific but time-agnostic (no start/end time)
- Droppable area for tasks from backlog
- Tasks render as horizontal bars (like Google Calendar all-day events)
- Expandable: "Show N more" if > 3 all-day tasks

### Drag-and-Drop Interaction

1. **Grab:** User clicks grip handle on backlog task → element elevates with `shadow-lg`
2. **Drag:** Task follows cursor with slight opacity (0.85). Original position shows dotted outline.
3. **Over grid:** Target time slot highlights with `bg-accent-light` tint. Ghost preview shows where task will land.
4. **Drop:** Task snaps into the time slot. Default duration: 60 minutes (configurable).
   - API calls:
     a. `createTimeBlock()` with date, start_time, calculated end_time, title, client from task
     b. `updateGlobalTask()` to set `time_block` reference
   - Task disappears from backlog
5. **Cancel:** Drop outside valid zone → task returns to backlog (spring animation)

### Resize Handles

- Bottom edge of each time block shows resize cursor on hover (`cursor-ns-resize`)
- Click and drag down → expands duration (snaps to 15min increments)
- Click and drag up → contracts duration (minimum 15min)
- On release → `updateTimeBlock()` with new end_time
- Visual feedback: block border turns accent color during resize

### Move Existing Blocks

- Time blocks already on the grid are also draggable
- Drag to new time slot → `updateTimeBlock()` with new start/end
- Drag to backlog → removes time assignment (unschedules)
- Collision detection: if dropped on occupied slot, show warning toast

### Week View

```
┌──────────────────────────────────────────────────────────────────────┐
│ Calendar                                      [Day] [Week] ◀ ▶ 📅   │
├──────────┬──────────┬──────────┬──────────┬──────────┬──────────────┤
│ BACKLOG  │ Mon 24   │ Tue 25   │ Wed 26   │ Thu 27   │ Fri 28       │
├──────────┼──────────┼──────────┼──────────┼──────────┼──────────────┤
│ □ Task A │ ALL-DAY  │ ALL-DAY  │ ALL-DAY  │          │              │
│ □ Task B │──────────│──────────│──────────│──────────│──────────────│
│          │ 8:00 ██  │ 8:00    │ 8:00 ██  │ 8:00    │ 8:00 ██      │
│          │ 9:00 ██  │ 9:00 ██  │ 9:00    │ 9:00 ██  │ 9:00         │
│          │ 10:00    │ 10:00 ██ │ 10:00 ██ │ 10:00   │ 10:00        │
│          │ ...      │ ...      │ ...      │ ...      │ ...          │
└──────────┴──────────┴──────────┴──────────┴──────────┴──────────────┘
```

- Backlog pane persists on left (shows tasks for entire week or selected day)
- 5 day columns (Mon-Fri), optionally Sat-Sun
- Drag from backlog → any day's time slot
- Drag between days (cross-day move) → updates date + time
- Narrower blocks due to space — show title + client color only
- Click block → opens detail popover/modal

### Day/Week Toggle

- Segmented control in header: "Day" / "Week"
- State persists in localStorage
- Day view defaults to today, Week view defaults to current week
- Navigation arrows (◀ ▶) move by day or week respectively
- Date picker (📅) for jump-to-date

### Bi-Directional Sync

- All calendar mutations → API call → React Query cache invalidation
- Main dashboard's read-only schedule view reads from the same API
- Optimistic updates for smooth UX (revert on API error)
- WebSocket or polling for multi-tab sync (via existing realtime service)

### Multi-Day Task Logic

Task spans Mon-Wed:
1. Appears in backlog for Mon, Tue, Wed
2. Agent drags onto Mon at 2PM for 2 hours
3. Task marked as "partially scheduled" — still appears in Tue/Wed backlog
4. Agent drags onto Tue at 10AM — now partially scheduled for 2 of 3 days
5. When all days have time blocks OR task marked complete → fully scheduled

## Design Specifications

### Backlog Pane
- Background: `var(--color-surface-subtle)`
- Border right: `1px solid var(--color-border)`
- Task items: `bg-surface rounded-lg p-2 mb-1 border border-border-subtle`
- Grip handle: `text-muted hover:text-secondary` (6-dot grid icon)

### Grid
- Hour labels: `text-xs text-muted font-mono` left-aligned
- Grid lines: `border-b border-border-subtle`
- Current time: `border-t-2 border-red-500` with red dot
- Drop zone highlight: `bg-accent-light/30` (blue tint at 30% opacity)

### Time Blocks
- `rounded-lg p-2 text-sm border-l-4` (left border = client color)
- Background: client color at 10% opacity
- Title: `font-medium text-text`
- Client/category: `text-xs text-secondary`
- Resize handle zone: bottom 6px of block

### Transitions
- Drag: `transition-shadow var(--transition-fast)`
- Drop snap: spring animation (200ms)
- View toggle: `var(--transition-default)` crossfade

## Out of Scope

- Task creation modal (Split 03 — tasks come from backlog)
- Dashboard KPI widget (Split 05)
- Admin views (Split 06)
- Offline support

## Acceptance Criteria

1. Split-view layout with collapsible backlog pane and hourly grid
2. Drag task from backlog → grid creates time block via API
3. Ghost preview shows during drag-over on grid
4. Default 60min duration on drop, snapped to 30min grid
5. Resize handles expand/contract blocks (15min increments)
6. All-day header displays multi-day and time-agnostic tasks
7. Week view shows 5-day grid with full DnD
8. Cross-day drag in week view updates date and time
9. Day/Week toggle preserves context, persists in localStorage
10. Navigation arrows and date picker work correctly
11. Current time indicator visible and auto-scrolled
12. Bi-directional API sync — changes reflect on main dashboard
13. Optimistic updates for smooth UX
14. Collision detection warns when dropping on occupied slots
15. Multi-day tasks show in backlog for each relevant day
