# Complete Specification: Agent Dashboard KPI

## What We're Building

A new read-only agent dashboard home page (new route, separate from the existing CommandCenter) that serves as the operational overview for agents. The primary focal point is a "Current Task" KPI widget that shows the active time-blocked task in real time. The dashboard is intentionally read-only — it answers "What is the state of my day?" and deep-links to the Command Centre portal for any action.

## Routing

- **New route**: `/dashboard/agent/{agentType}/` or a shared `/dashboard/agent/` home
- **Not replacing**: CommandCenter stays at its existing route (e.g., `/agent/developer/schedule/` or `/agent/marketing/management/calendar/`)
- The dashboard page takes `agentType: 'marketing' | 'website'` to differentiate API calls
- Deep-links use absolute paths like `/dashboard/agent/marketing/management/calendar/?date={date}&block={id}`

## Architecture

### Data Source
Single React Query call via `useCommandCenter()` which fetches `CommandCenterData`:
- `stats: CommandCenterStats` — 4 KPI metrics
- `time_blocks: AgentTimeBlock[]` — for KPI widget and schedule panel
- `todays_global_tasks: AgentGlobalTask[]` — for task list
- `todays_client_tasks: CrossClientTask[]` — for task list

**Polling**: `refetchInterval: 60_000`, `staleTime: 55_000` (prevents double-fetch on tab focus), `refetchIntervalInBackground: false` (pauses when tab hidden).

### New Components
1. `AgentDashboardPage` — the new page component
2. `CurrentTaskKpi` — KPI widget (primary focal point)
3. `DashboardStatsRow` — 4 stat cards
4. `DashboardTaskList` — merged task list with checkboxes
5. `ReadOnlySchedule` — lightweight read-only timeline

### Reused/Untouched
- `DaySchedule.tsx` — **not modified**, remains interactive for the portal
- `useCommandCenter()` hook — already has 60s polling, just consume it
- `timeUtils.ts` utilities — `timeToMinutes()`, `formatHour()` for progress calculation
- `BLOCK_TYPE_LABELS`, `BLOCK_TYPE_COLORS` constants — for KPI widget display

---

## Component Specifications

### 1. AgentDashboardPage

**Route file**: `client/app/dashboard/agent/[agentType]/page.tsx` (or specific marketing/website variants)

**Layout** (stacked vertically):
```
┌─────────────────────────────────────────────────────┐
│  CurrentTaskKpi (full width)                        │
├─────────────────────────────────────────────────────┤
│  DashboardStatsRow (4 cards, full width)            │
├────────────────────────┬────────────────────────────┤
│  DashboardTaskList     │  ReadOnlySchedule           │
│  (left, ~40%)          │  (right, ~60%)              │
└────────────────────────┴────────────────────────────┘
```

Mobile: stacks vertically. CurrentTaskKpi remains prominent at top.

**Data flow**: Calls `useCommandCenter()` once, passes slices to each child component.

---

### 2. CurrentTaskKpi

**Purpose**: Primary focal point. Shows the active time block with progress.

**Chronological sync logic**:
1. `useCommandCenter()` returns `time_blocks: AgentTimeBlock[]` for today
2. Local `now` state = `new Date()`, updated every 60s via `setInterval`
3. Active block = `time_blocks.find(b => timeToMinutes(b.start_time) <= nowMinutes && nowMinutes < timeToMinutes(b.end_time))`
4. Progress = `(nowMinutes - startMinutes) / (endMinutes - startMinutes) * 100` (clamped 0–100)
5. Time remaining = `endMinutes - nowMinutes` minutes

**Display elements** (when active block found):
- Task title: block's `title` field — `text-xl font-semibold` (Poppins)
- Client badge: `block.client_name` — color from `BLOCK_TYPE_COLORS[block.block_type]`
- Category badge: `BLOCK_TYPE_LABELS[block.block_type]` (e.g., "Deep Work")
- Time range: `startTime – endTime` in 12h format using `formatHour()` or custom formatter
- Progress bar: CSS `transition: transform 800ms cubic-bezier(0.4, 0, 0.2, 1)` on `scaleX(progress/100)` with `transformOrigin: left` — GPU-composited, smooth
- Time remaining: "N min remaining" text
- Deep-link button: "Open in Portal →" → `/dashboard/agent/{agentType}/management/calendar/?date={block.date}&block={block.id}`

**Visual design**:
- Card: `bg-surface rounded-2xl border-2 border-accent/20 shadow-lg p-6`
- Active state ring: `ring-2 ring-accent/20`
- Progress bar container: `h-3 rounded-full bg-surface-muted`
- Progress fill: `h-3 rounded-full bg-accent` with CSS transition on `scaleX`
- Button: `bg-accent text-white rounded-lg px-4 py-2 text-sm font-medium`
- Full width — spans across the dashboard

**Empty states**:
- No active block right now, but next block exists:
  ```
  "No active task right now. Next: [title] at [startTime]."
  + "Open Command Centre →" link
  ```
- Between blocks (free time):
  ```
  "Free until [nextBlock.start_time]. Next: [nextBlock.title]"
  ```
- No blocks at all today:
  ```
  "No tasks scheduled for today."
  + "Open Command Centre →" link
  ```

**Empty state detection logic**:
- If no active block: find the next upcoming block (`start_time > nowMinutes`) — if found, show "free until" state
- If no upcoming block: show "no tasks scheduled" state

---

### 3. DashboardStatsRow

**Data**: `CommandCenterStats` from `CommandCenterData.stats`

**4 cards**:
| Metric | Field | Description |
|--------|-------|-------------|
| Total Active Tasks | `stats.total_active_tasks` | Non-done tasks |
| Completed Today | `stats.completed_today` | Done today |
| Hours Blocked | `stats.hours_blocked_today` | Sum of today's block durations |
| Active Clients | `stats.active_clients` | Unique clients in today's tasks |

**Design**:
- Grid: `grid grid-cols-2 lg:grid-cols-4 gap-4`
- Card: `bg-surface rounded-xl border border-border p-4`
- Value: `text-2xl font-bold` (Poppins 700)
- Label: `text-xs text-muted uppercase tracking-wider` (Inter 400)
- No interactions — pure display

---

### 4. DashboardTaskList

**Data**: Merged list of `todays_global_tasks: AgentGlobalTask[]` + `todays_client_tasks: CrossClientTask[]`

**Merge + sort logic**:
1. Merge both arrays into a unified display type (map to common fields: `id`, `title`, `status`, `client_name`, `start_time`)
2. Sort by: status order (in_progress → todo/in_review → done), then `start_time` ascending within each group
3. Group display: "In Progress" section first, "To-Do" section, "Done" section (greyed)

**Task row**:
- Checkbox + title + client badge + status badge
- Checkbox: `w-5 h-5 rounded border-2 border-border checked:bg-accent checked:border-accent`
- Done tasks: `line-through text-muted opacity-60`
- Status badges: `rounded-full px-2 py-0.5 text-xs` with status-specific colors

**Checkbox behavior** (optimistic update):
- Uses `useUpdateGlobalTask()` mutation with cache-based `onMutate` (Pattern B from research)
- `onMutate`: snapshot cache, update `todays_global_tasks` in cache optimistically
- `onError`: rollback to snapshot + `toast.error()`
- `onSettled`: `invalidateQueries(['scheduling', 'command-center'])` guarded by `isMutating()` check
- Only global tasks (`AgentGlobalTask`) are checkable — cross-client tasks are display-only (no checkbox)
- Recurring tasks: just PATCH `status: 'done'`; backend handles JIT generation automatically

**Footer**: "View All in Portal →" link to `/dashboard/agent/{agentType}/management/tasks/`

**Empty state**: "No tasks scheduled for today. Open Command Centre →"

---

### 5. ReadOnlySchedule

**Purpose**: Lightweight, new component — does NOT modify `DaySchedule.tsx`.

**What it renders**:
- Hourly grid from `startHour` to `endHour` (defaults: 8am–8pm for readability)
- Time label column: `text-xs text-muted font-mono`, e.g. "8 AM", "9 AM"
- Time blocks (from `time_blocks` prop): positioned using same formula as DaySchedule:
  - `top = ((startMin - startHour * 60) / 60) * hourHeight`
  - `height = ((endMin - startMin) / 60) * hourHeight`
- Block styling: `rounded-lg p-2 border-l-4` — left border color = `BLOCK_TYPE_COLORS[block.block_type]`
- Block content: title + client badge
- Current time indicator (`NowIndicator`): `border-t-2 border-red-500` absolute line, updates every 60s
- Active block highlight: `ring-2 ring-accent/20` on the currently active block
- No click handlers, no DnD — purely visual

**Props**:
```typescript
interface ReadOnlyScheduleProps {
  timeBlocks: AgentTimeBlock[];
  date: string;
  startHour?: number;  // default 8
  endHour?: number;    // default 20
  hourHeight?: number; // default 50
}
```

**Footer**: "Edit Schedule in Portal →" link to `/dashboard/agent/{agentType}/management/calendar/`

---

## Auto-Refresh Architecture

- `useCommandCenter()` already has `refetchInterval: 60_000` — add `staleTime: 55_000`
- Local `now` state in `CurrentTaskKpi` updated every 60s via `setInterval` for progress bar
- Optimistic task completion: instantly reflects in UI, syncs on `onSettled`
- When task checked off: `invalidateQueries(['scheduling', 'command-center'])` refreshes all panels

---

## File Structure

```
client/app/dashboard/agent/
  [agentType]/                       # new route (or marketing/ + developer/)
    page.tsx                         # AgentDashboardPage

client/components/agent/dashboard/   # new directory
  CurrentTaskKpi.tsx
  DashboardStatsRow.tsx
  DashboardTaskList.tsx
  ReadOnlySchedule.tsx
  index.ts                           # barrel export

client/components/agent/dashboard/__tests__/
  CurrentTaskKpi.test.tsx
  DashboardTaskList.test.tsx
  ReadOnlySchedule.test.tsx
  DashboardStatsRow.test.tsx
```

---

## Key Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Routing | New route, CommandCenter unchanged | Non-destructive; portal stays interactive |
| Current task source | `AgentTimeBlock` (not `AgentGlobalTask`) | Blocks have definitive time ranges |
| KPI category | `BLOCK_TYPE_LABELS[block_type]` | Already available, consistent with portal |
| Deep-link format | `?date={date}&block={id}` | Allows calendar page to focus specific block |
| Task list scope | Merged global + client tasks | Full picture of today's work |
| Cross-client task checkboxes | Display-only (no checkbox) | CrossClientTask has no simple status patch via this flow |
| Recurring task completion | Just PATCH done | Backend handles JIT |
| Schedule component | New `ReadOnlySchedule` | Keeps DaySchedule untouched for portal |
| Progress bar animation | CSS `transition: transform scaleX()` | GPU-composited, zero JS animation code |
| Optimistic updates | Cache-based `onMutate` (Pattern B) | Tasks are in shared `commandCenter` cache entry |

---

## Out of Scope

- Schedule editing (portal)
- Task creation (portal)
- Admin dashboard
- Analytics charts
- Modifying DaySchedule.tsx or CommandCenter.tsx
