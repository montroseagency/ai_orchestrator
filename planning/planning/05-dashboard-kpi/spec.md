# Spec: Main Dashboard Redesign & Current Task KPI

## Summary

Redesign the main agent dashboard as a read-only operational overview with a "Current Task" KPI widget as the primary focal point. The dashboard shows today's schedule, task summary, and analytics in read-only format with progressive interactivity (checkboxes for quick task completion). The KPI widget uses chronological sync to display the active time-blocked task with a progress bar and deep-link to the Command Centre portal.

## Dependencies

- **Split 04 (Scheduling Engine):** Calendar data feeds the KPI widget and schedule view
- **Split 01 (Backend):** Task API with updated status fields

## Goals

1. **Read-only overview:** Dashboard answers "What is the state of my day?" — no task creation, no schedule editing
2. **Current Task KPI:** Large, prominent widget showing the active time-blocked task with progress visualization
3. **Progressive interactivity:** Simple checkboxes to mark tasks done without leaving the dashboard
4. **Read-only schedule mirror:** Shows today's calendar from the scheduling engine (view-only)
5. **Gateway to portal:** Every actionable element deep-links to the relevant Command Centre page

## Existing Code to Refactor

### Components to Evolve
- `client/components/agent/scheduling/CommandCenter.tsx` — Current interactive hub. Refactor into read-only dashboard.
- `client/components/agent/scheduling/DaySchedule.tsx` — Rendered read-only on dashboard (no DnD).
- `client/components/agent/scheduling/MobileAgendaView.tsx` — Keep for mobile, make read-only.

### API to Use
- `schedulingApi.getCommandCenterData()` — Already returns `CommandCenterData` with stats, time_blocks, tasks
- `schedulingApi.getTimeBlocks()` — For current task detection
- `schedulingApi.updateGlobalTask()` — For checkbox completion only

### Existing Types
- `CommandCenterData` — Has `stats`, `todays_global_tasks`, `todays_client_tasks`, `time_blocks`
- `CommandCenterStats` — `total_tasks`, `completed_today`, `hours_blocked`, `active_clients`

## Detailed Requirements

### Dashboard Layout

```
┌──────────────────────────────────────────────────────────────────┐
│                    CURRENT TASK KPI                              │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  📋 Design Review — Nike Campaign Assets                   │  │
│  │  Client: Nike  ·  Category: Design  ·  9:00 – 10:30 AM    │  │
│  │  ████████████████████░░░░░░░  67% · 30min remaining       │  │
│  │                                        [Open in Portal →]  │  │
│  └────────────────────────────────────────────────────────────┘  │
├──────────────────────────────────────────────────────────────────┤
│  Stats:  12 Tasks  ·  5 Done  ·  6.5h Blocked  ·  4 Clients    │
├─────────────────────────────┬────────────────────────────────────┤
│  TODAY'S TASKS              │  TODAY'S SCHEDULE (read-only)      │
│  ☑ Write Nike copy     Done │  8:00  SEO Audit - Adidas         │
│  ☐ Review Adidas brief  IP  │  9:00  Design Review - Nike  ←NOW │
│  ☐ Update client deck   TD  │  10:30 (free)                     │
│  ☐ Send weekly report   TD  │  11:00 Client Call - Puma         │
│  ...                        │  12:00 Lunch                      │
│  [View All in Portal →]     │  13:00 Copywriting - Nike         │
│                             │  ...                              │
│                             │  [Edit Schedule in Portal →]      │
└─────────────────────────────┴────────────────────────────────────┘
```

### Current Task KPI Widget

This is the PRIMARY focal point of the dashboard.

**Chronological Sync Logic:**
1. Fetch today's time blocks from API
2. Find the block where `now >= start_time AND now < end_time`
3. Display that block's task info
4. Calculate progress: `(now - start_time) / (end_time - start_time) * 100`
5. Update every 60 seconds (setInterval or requestAnimationFrame)

**Display Elements:**
- Task title (large, `text-xl font-semibold font-display`)
- Client badge (color-coded)
- Category badge
- Time range (`start_time – end_time` in 12h format)
- Progress bar (animated, uses accent color)
- Time remaining text ("N min remaining")
- Deep-link button: "Open in Portal →" → navigates to `/management/calendar/` with task focused

**Empty States:**
- No current task: "No active task right now. Your next task is [Title] at [Time]." + link to portal
- No tasks today: "No tasks scheduled for today. [Open Command Centre →]"
- Between tasks: "Free until [next_task_time]. Next: [next_task_title]"

**Visual Design:**
- Card: `bg-surface rounded-2xl border border-border shadow-surface p-6`
- Progress bar: `h-3 rounded-full bg-surface-muted` container, `bg-accent rounded-full` fill with `transition-all 1s ease`
- Accent glow on active: `ring-2 ring-accent/20`
- Larger than other dashboard cards — spans full width

### Stats Row

4 KPI stat cards (refactor existing `StatCard`):
- **Total Active Tasks** — count of non-done tasks
- **Completed Today** — tasks marked done today
- **Hours Blocked** — sum of today's time block durations
- **Active Clients** — count of unique clients in today's tasks

Read-only, no interactions. Data from `CommandCenterData.stats`.

### Today's Tasks (Left Panel)

- List of all tasks scheduled for today (global + client tasks)
- Each row: checkbox + title + client badge + status badge
- **Progressive interactivity:** Clicking checkbox → calls `updateGlobalTask({ status: 'done' })` → updates immediately
- If recurring, JIT generation triggers automatically via API
- Grouped by status: In Progress first, then To-Do, then Done (greyed out)
- "View All in Portal →" link at bottom

### Today's Schedule (Right Panel)

- Read-only vertical timeline mirroring the scheduling engine's hourly grid
- Shows time blocks with title + client color
- Current time indicator (red line)
- Highlight current block with accent border
- No DnD, no editing — purely visual
- "Edit Schedule in Portal →" link at bottom

### Auto-Refresh

- Dashboard data refreshes every 60 seconds
- KPI progress bar updates every 60 seconds
- React Query with `refetchInterval: 60000`
- When task is checked off, optimistic update + refetch

## Design Specifications

### KPI Widget
- Background: `var(--color-surface)` with `var(--shadow-lg)`
- Border: `2px solid var(--color-accent-light)`
- Title: Poppins 600, `text-xl`
- Time: Inter 400, `text-sm text-secondary`
- Progress bar: `h-3 rounded-full`, accent fill with smooth transition
- Button: `bg-accent text-white rounded-lg px-4 py-2 text-sm font-medium`

### Stats Row
- Cards: `bg-surface rounded-xl border border-border p-4`
- Value: Poppins 700, `text-2xl`
- Label: Inter 400, `text-xs text-muted uppercase tracking-wider`

### Task List
- Checkbox: `w-5 h-5 rounded border-2 border-border checked:bg-accent checked:border-accent`
- Done tasks: `line-through text-muted`
- Status badges: `rounded-full px-2 py-0.5 text-xs`

### Schedule Timeline
- Time label: `text-xs text-muted font-mono`
- Block: `rounded-lg p-2 border-l-4` (left border = client color)
- Current indicator: `border-t-2 border-red-500`

## Out of Scope

- Schedule editing (that's the portal/Split 04)
- Task creation (that's the portal/Split 03)
- Admin dashboard (Split 06)
- Analytics charts (future enhancement)

## Acceptance Criteria

1. Dashboard is read-only — no task creation, no schedule editing possible
2. Current Task KPI shows the active time-blocked task with real-time progress bar
3. Progress bar updates automatically (60s interval)
4. KPI shows correct empty state when no task is active
5. Deep-link from KPI opens the task in Command Centre portal
6. Stats row shows accurate counts from API
7. Task checkboxes work — marking done updates API and refreshes UI
8. Recurring task completion triggers JIT generation
9. Read-only schedule shows today's time blocks accurately
10. Current time indicator visible on schedule
11. "View All in Portal" and "Edit Schedule" links navigate correctly
12. Dashboard auto-refreshes every 60 seconds
13. Mobile responsive: stacks vertically, KPI still prominent
14. Uses existing design tokens — consistent with rest of platform
