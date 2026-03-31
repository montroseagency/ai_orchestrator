# Implementation Plan: Agent Dashboard KPI

## Context

The Montrroase agency platform currently has an interactive `CommandCenter` component that serves as the agent's scheduling hub. It mixes read-only display with drag-and-drop editing, task creation, and modal interactions. This plan introduces a separate read-only agent dashboard — a new route that gives agents an at-a-glance operational overview of their day without the complexity of the full portal.

The dashboard is not a replacement for the CommandCenter. Both coexist: the dashboard is the landing page ("what's my day?"), and the CommandCenter portal is where agents take action ("edit this block", "create a task"). Every actionable element in the dashboard is a deep-link to the portal.

The primary feature of this dashboard is the **Current Task KPI widget** — a full-width card that shows the currently active time-blocked task, a real-time progress bar, and a deep-link into the portal. This is the focal point of the new page.

---

## What We're Building

Four new React components and one new route page:

1. **`AgentDashboardPage`** — the page component at the new route
2. **`CurrentTaskKpi`** — the primary KPI widget showing the active time block
3. **`DashboardStatsRow`** — four stat cards showing today's metrics
4. **`DashboardTaskList`** — merged task list with optimistic checkboxes
5. **`ReadOnlySchedule`** — lightweight read-only timeline (not a modification of `DaySchedule.tsx`)

**Critically: `DaySchedule.tsx`, `CommandCenter.tsx`, and all existing scheduling hooks and API files are not modified.** The new dashboard only consumes existing APIs.

---

## File Structure

```
client/app/dashboard/agent/
  marketing/
    page.tsx             # existing page — potentially updated to redirect to new dashboard
  [agentType]/           # new shared dashboard route
    page.tsx             # AgentDashboardPage

client/components/agent/dashboard/
  CurrentTaskKpi.tsx
  DashboardStatsRow.tsx
  DashboardTaskList.tsx
  ReadOnlySchedule.tsx
  index.ts               # barrel export

client/components/agent/dashboard/__tests__/
  CurrentTaskKpi.test.tsx
  DashboardTaskList.test.tsx
  ReadOnlySchedule.test.tsx
  DashboardStatsRow.test.tsx
```

---

## Data Layer

### Single Data Fetch

The entire dashboard is powered by one React Query call: `useCommandCenter()`. This hook already exists in `client/lib/hooks/useScheduling.ts` and already has `refetchInterval: 60_000`. The implementation should update its `staleTime` to `55_000` to prevent a double-fetch when the user switches back to the tab (React Query would otherwise fire both an interval refetch and a focus refetch within the same second).

The hook returns `CommandCenterData` which contains:
- `stats: CommandCenterStats` (4 metrics)
- `time_blocks: AgentTimeBlock[]` (used by KPI widget and ReadOnlySchedule)
- `todays_global_tasks: AgentGlobalTask[]` (used by DashboardTaskList)
- `todays_client_tasks: CrossClientTask[]` (used by DashboardTaskList)

`AgentDashboardPage` makes this single call and distributes slices to child components via props. Children are stateless display components with the exception of `DashboardTaskList` which has mutation logic for checkboxes.

### Polling Behavior

The existing `refetchInterval: 60_000` handles all data freshness. Tab-hidden pausing is free because `refetchIntervalInBackground` defaults to `false`. When the user returns to the tab, React Query fires an immediate refetch (`refetchOnWindowFocus: true`). The dashboard shows `isFetching` as a subtle top-bar indicator rather than blocking the UI with a skeleton.

---

## Component Design

### AgentDashboardPage

This is the page-level component. It calls `useCommandCenter()` and handles the three loading states:

- **Initial loading** (`isLoading`): renders a full-page skeleton matching the dashboard layout
- **Error** (`isError`): renders an error state with a retry button
- **Loaded** (`data`): renders the four child components in the layout described below

Layout (desktop):
```
┌──────────────────────────────────────────┐
│  CurrentTaskKpi (full width)             │
├──────────────────────────────────────────┤
│  DashboardStatsRow (4 cards)             │
├────────────────────┬─────────────────────┤
│  DashboardTaskList │  ReadOnlySchedule   │
│  (col, ~40% wide)  │  (col, ~60% wide)   │
└────────────────────┴─────────────────────┘
```

Mobile: all sections stack vertically in the same order. `CurrentTaskKpi` always appears first.

The page also receives `agentType` from route params (or a parent layout) and passes it to children that need to construct deep-link URLs.

---

### CurrentTaskKpi

This is the most complex of the four components. It owns a local `now: Date` state that drives progress calculation.

**Timezone assumption**: All time calculations use the agent's local device clock (`new Date()`). The `AgentTimeBlock` `start_time`/`end_time` strings (`HH:MM:SS`) are assumed to be in the agent's local timezone — consistent with how the existing `CommandCenter` and `DaySchedule` handle times. No UTC conversion is performed. If the backend ever normalizes times to UTC, this will need revisiting.

**Current task detection** runs as a derived value (useMemo or inline computation) every time `now` or `timeBlocks` changes:

1. Convert `now` to minutes-since-midnight
2. Walk `timeBlocks` to find the block where `startMinutes <= nowMinutes < endMinutes` (using `timeToMinutes()` from the existing `timeUtils.ts`)
3. If multiple blocks overlap (e.g., a meeting started before the previous one ended), select the one with the **latest `start_time`** (most recently started takes priority)
4. If found: that's the active block
5. If not found: find the next upcoming block (`startMinutes > nowMinutes`) to populate the "free until" empty state. Gaps of any duration between blocks (even 1 minute) correctly show the "free" state.

The `setInterval` for `now` runs every 60 seconds, matching the polling interval. This means the progress bar re-calculates once per minute, which is appropriate for this scale of precision.

**Progress calculation**:
- `progress = ((nowMinutes - startMinutes) / (endMinutes - startMinutes)) * 100`
- Clamped to 0–100
- Passed to the progress bar as a CSS `transform: scaleX(progress/100)` on the fill element

**Progress bar animation**: CSS `transition: transform 800ms cubic-bezier(0.4, 0, 0.2, 1)` on `scaleX`. The `transformOrigin` is set to `left`. This is GPU-composited (`transform` runs off the main thread), so it doesn't cause layout recalculations. When the value updates every 60 seconds, the browser smoothly interpolates over 800ms. No `requestAnimationFrame` or `setInterval` is needed for the animation itself.

**Display elements** (when active block exists):
- Task title from `block.title` in large, bold font
- Client badge using `block.client_name`
- Category badge using `BLOCK_TYPE_LABELS[block.block_type]` (e.g., "Deep Work")
- Time range in 12-hour format (e.g., "9:00 – 10:30 AM") — can use the existing `formatHour()` utility or a simple custom formatter for the full HH:MM format
- Progress bar with animated fill
- "N min remaining" text below the bar — calculated as `floor(endMinutes - nowMinutes)` minutes. When less than 1 minute remains, display "Ending soon" instead of "0 min remaining"
- "Open in Portal →" button linking to `/dashboard/agent/{agentType}/management/calendar/?date={block.date}&block={block.id}`

**Accessibility**: The progress bar element must have `role="progressbar"`, `aria-valuenow={progress}`, `aria-valuemin={0}`, `aria-valuemax={100}` for screen reader compatibility.

**Empty states** (three cases):
1. Active block exists — render the full widget above
2. Free time (no active block, but a future block exists) — render a simpler card: "Free until {nextBlock.start_time}. Next: {nextBlock.title}" with a portal link
3. No blocks at all for today — render: "No tasks scheduled for today." with a portal link

**Visual design**:
- Full-width card with `border-2` accent border and `ring-2 ring-accent/20` when active
- More prominent shadow (`shadow-lg`) than the stat cards below
- Background: `bg-surface`

---

### DashboardStatsRow

A straightforward row of four read-only metric cards. Each card receives a `value` (number) and `label` (string). No interactions.

**Field mapping from `CommandCenterStats`**:
- `total_active_tasks` → "Active Tasks"
- `completed_today` → "Done Today"
- `hours_blocked_today` → "Hours Blocked"
- `active_clients` → "Active Clients"

These map directly to `CommandCenterStats` fields. No derived calculations needed.

**Layout**: `grid grid-cols-2 lg:grid-cols-4 gap-4`

Each card: `bg-surface rounded-xl border border-border p-4` with value in `text-2xl font-bold` and label in `text-xs text-muted uppercase tracking-wider`.

---

### DashboardTaskList

**Data preparation**: Before rendering, merge `todays_global_tasks` and `todays_client_tasks` into a single unified display list. Both types share a common set of fields for display purposes: `id`, `title`, `status`, `client_name`. The merge produces a typed union that tracks whether each item is a `GlobalTask` (checkable) or `ClientTask` (display-only).

**Sort order**: Status group first (in_progress → todo/in_review → done), then by `start_time` ascending within each group. Tasks without a `start_time` sort to the end of their group, ordered by the `order` field from `AgentGlobalTask` (which represents user-defined priority ordering), then by `id` as a stable tiebreaker.

**Rendering**: Three visual sections ("In Progress", "To Do", "Done") each with a section header. Done tasks are greyed out with `line-through` on the title. Each row shows: checkbox (global tasks only) + title + client badge + status badge.

**Checkbox behavior** uses the existing `useUpdateGlobalTask()` mutation with a cache-based optimistic update (not the simpler variables-based approach, because all tasks share the single `commandCenter` cache entry). The pattern:

1. `onMutate`: cancel in-flight queries for `commandCenter`, snapshot current cache, apply optimistic update to `todays_global_tasks` in the cache
2. `onError`: restore snapshot, show toast error
3. `onSettled`: call `invalidateQueries(['scheduling', 'command-center'])` guarded by an `isMutating()` check to handle rapid toggling without race conditions

Cross-client tasks (`CrossClientTask`) do not have checkboxes — they are display-only with their existing status shown as a badge.

**Footer**: "View All in Portal →" link to `/dashboard/agent/{agentType}/management/tasks/`.

---

### ReadOnlySchedule

A new, self-contained component that renders a vertical hour-by-hour timeline. It uses the same positioning math as `DaySchedule` but without any drag-and-drop, modals, or click handlers.

**Props**: `timeBlocks: AgentTimeBlock[]`, `date: string`, `startHour = 8`, `endHour = 20`, `hourHeight = 50`

**Rendering**:
- A container with relative positioning and `overflow-y: auto` with `max-height: 600px`
- Hour labels column on the left: one label per hour from `startHour` to `endHour`, formatted as "8 AM", "9 AM", etc.
- Grid lines (thin horizontal borders) at each hour boundary
- Time blocks positioned absolutely using:
  - `top = ((startMin - startHour * 60) / 60) * hourHeight`
  - `height = ((endMin - startMin) / 60) * hourHeight`
- Block card: `rounded-lg border-l-4` where the left border color is `BLOCK_TYPE_COLORS[block.block_type]`, background is a lighter tint
- Block content: title and client name in small text
- Active block (same detection logic as `CurrentTaskKpi`) gets an `ring-2 ring-accent/20` highlight

**`NowIndicator`** (inline sub-component): a thin `border-t-2 border-red-500` line positioned absolutely at `top = ((nowMinutes - startHour * 60) / 60) * hourHeight`. Updates every 60s via local `setInterval`. Hidden if `nowMinutes` is outside `[startHour * 60, endHour * 60]`.

On mount, the schedule auto-scrolls to show the current hour (or nearest to it) using a `useEffect` with a ref on the container.

**Footer**: "Edit Schedule in Portal →" link to `/dashboard/agent/{agentType}/management/calendar/?date={date}` where `date` is today's date in `YYYY-MM-DD` format.

---

## Routing

The new page lives at a new route. The exact path depends on whether the project uses a shared `[agentType]` segment or separate marketing/developer route directories. Either way, the page component is the same and receives `agentType` as a prop (from route params or a parent layout).

The implementation should follow the existing marketing agent route directory pattern already established in the codebase (`client/app/dashboard/agent/marketing/`). The page receives `agentType` from its parent layout rather than a dynamic segment.

The page should not replace existing routes. The CommandCenter remains accessible at its current URL for agents who need it.

**Cross-plan dependency**: The "Open in Portal →" deep-link and the "Edit Schedule in Portal →" link both depend on the portal's calendar page (`/management/calendar/`) correctly consuming `?date=` and `?block=` URL parameters to navigate to and highlight the specified block. This is in scope for Split 04. If the portal doesn't yet handle these params, the links should still navigate to the calendar page (graceful degradation — the user arrives at the calendar but without auto-scroll).

---

## Deep-Link URL Construction

All deep-links are constructed at the component level by combining:
- `agentType`: from the page's route param
- `block.date`: `YYYY-MM-DD` string from the block
- `block.id`: UUID string

The calendar page at the target URL (`/management/calendar/?date={date}&block={id}`) is responsible for reading these params and scrolling to or highlighting the referenced block. This plan does not define the calendar page's handling — that's in scope for the portal (Split 04).

---

## Key Design Decisions and Rationale

**Why a new component instead of modifying DaySchedule?**
`DaySchedule.tsx` has 544 lines of drag-and-drop, modal, and edit logic. Adding a `readOnly` prop would scatter conditionals throughout and make future maintenance harder. A dedicated `ReadOnlySchedule` has ~100 lines and zero coupling to DnD libraries.

**Why CSS `scaleX` transition instead of width animation?**
CSS `transform: scaleX()` runs on the GPU compositor thread — it does not trigger layout recalculation. `width` animation causes a layout pass on every frame. For a progress bar that updates every 60s, the difference is minor, but the pattern is architecturally correct and consistent with the project's use of CSS custom properties for transitions.

**Why cache-based optimistic update instead of variables-based?**
All tasks are returned in the single `commandCenter` query cache entry. If we use the simpler variables-based pattern, we can only optimistically update the single task component — but the stats row (which shows `completed_today`) would not update until the next refetch. With cache-based `onMutate`, we can update the full `CommandCenterData` snapshot optimistically, including incrementing `stats.completed_today`.

**Why `staleTime: 55_000` on the command center query?**
React Query's default `staleTime: 0` means any data is immediately stale, so both the `refetchInterval` timer AND a `refetchOnWindowFocus` event can fire within milliseconds of each other, causing two identical network requests. Setting `staleTime` to just under the polling interval (55s < 60s) ensures the focus event finds the data "fresh" and skips the refetch, while the interval still fires on schedule.

**Performance note on re-renders**: All stateless child components (`CurrentTaskKpi`, `DashboardStatsRow`, `ReadOnlySchedule`) should be wrapped in `React.memo`. Since `AgentDashboardPage` re-renders every 60 seconds when the query resolves, `memo` ensures children only re-render when their specific props change — preventing cascade re-renders in components that received the same data.

---

## Testing Strategy Overview

Tests use the existing Vitest + @testing-library/react setup. The test utility functions `createMockTimeBlock()` and `createMockGlobalTask()` in `client/test-utils/scheduling.tsx` provide mock data. `renderWithQuery()` wraps components in a `QueryClientProvider`.

Key test scenarios per component:

**CurrentTaskKpi**:
- Given a time block covering `now`, renders the active block's title, client, category, and progress
- Progress calculation: start=0min, end=60min, now=30min → 50%
- Empty state: no time blocks → renders "no tasks" message
- Empty state: now is between blocks → renders "free until" message
- Progress bar element has correct `transform: scaleX(0.5)` style for 50%
- Timer: advancing fake timers by 60s re-calculates progress

**DashboardTaskList**:
- Renders merged global + client tasks
- Sort order: in_progress tasks appear before todo tasks
- Checkbox click on a global task fires `updateGlobalTask` mutation
- Optimistic update: checking a task immediately renders it as done before server response
- Rollback: if mutation fails, task reverts to original state
- Cross-client tasks render without a checkbox

**ReadOnlySchedule**:
- Renders time blocks at correct vertical positions
- Current time indicator visible and at correct position
- No click handlers on blocks (blocks are not focusable or interactive)
- Auto-scroll fires on mount

**DashboardStatsRow**:
- Renders all four stat values from `CommandCenterStats`
- Label text correct for each stat

---

## Acceptance Criteria Checklist

1. Dashboard is a new route; CommandCenter portal unchanged
2. Current Task KPI shows the active time block with animated progress bar
3. Progress bar updates automatically every 60 seconds
4. KPI shows correct empty state (free/no tasks) when no block is active
5. "Open in Portal →" navigates to calendar with `?date=` and `?block=` params
6. Stats row shows values from `CommandCenterStats`
7. Global task checkboxes apply optimistic update + error rollback
8. Recurring task completion sends single PATCH (backend handles JIT)
9. Read-only schedule shows blocks at correct time positions
10. Current time red-line indicator visible in schedule
11. "View All in Portal" and "Edit Schedule" links navigate correctly
12. Dashboard auto-refreshes every 60 seconds (via existing `useCommandCenter` refetchInterval)
13. Mobile: all sections stack vertically, KPI remains at top
14. Progress bar uses `transform: scaleX()` with CSS transition (GPU-composited)
