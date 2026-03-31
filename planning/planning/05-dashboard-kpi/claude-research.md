# Research: Main Dashboard KPI Redesign

## 1. Codebase Findings

### 1.1 Components to Refactor

#### CommandCenter.tsx (`client/components/agent/scheduling/CommandCenter.tsx`)
- **732 lines** — the current interactive hub
- Props: `{ agentType: 'marketing' | 'website' }`
- Uses `useCommandCenter()`, `useUpdateGlobalTask()`, `useUpdateTimeBlock()`, `useCreateTaskLink()`, `useTimeBlocks()`, `useGlobalTasks()` hooks
- DnD via `@dnd-kit/core` (DndContext, useDraggable, useDroppable) — must be removed for read-only
- Real-time 60s `setInterval` already exists for "Now" indicator and next item calculation
- Passes `externalDnd=true` to DaySchedule to share DnD context — no longer needed
- Inline StatCard component with Surface variant styling (not using common/stat-card.tsx)
- Sub-components rendered: AgendaSummary, DraggableTaskItem, CollapsibleSection, QuickTaskInput, DaySchedule, MobileAgendaView, FocusTimer, ScheduleCalendar, TaskCategoryBadge

#### DaySchedule.tsx (`client/components/agent/scheduling/DaySchedule.tsx`)
- **544 lines** — 24h timeline with hourly grid
- Props: `{ date, agentType, externalDnd?, hourHeight=50, startHour=0, endHour=24, snapMinutes=60 }`
- Absolute positioning formula: `top = ((startMin - startHour * 60) / 60) * hourHeight`
- Height formula: `height = ((endMin - startMin) / 60) * hourHeight`
- Contains `NowIndicator` component (red line, updates every 60s) — keep for read-only
- DraggableBlock and TimedTaskBlock are drop targets — remove for read-only
- Click-to-edit opens TimeBlockEditor modal — remove for read-only
- For read-only: keep hour grid, NowIndicator, block rendering; remove DnD and click handlers

#### MobileAgendaView.tsx (`client/components/agent/scheduling/MobileAgendaView.tsx`)
- **185 lines** — mobile period-based list view
- Props: `{ date, timeBlocks: AgentTimeBlock[], timedTasks: AgentGlobalTask[], clientTasks: CrossClientTask[] }`
- 4 periods: Early Morning (12-6am), Morning (6am-12pm), Afternoon (12-5pm), Evening (5pm-12am)
- No drag-and-drop already — already effectively read-only

### 1.2 Existing Stat Card (`client/components/common/stat-card.tsx`)
- Props: `{ value, label, icon?, trend?: { value, isPositive } }`
- Styling: `bg-white rounded-xl shadow-card border-neutral-100`
- CommandCenter uses its **own inline StatCard** with Surface variant styling
- For KPI dashboard: can use the common StatCard or the inline variant — inline is more consistent with the existing dashboard styling

### 1.3 API Layer (`client/lib/api/scheduling.ts`, 228 lines)

```typescript
schedulingApi.getCommandCenter()     // GET /agent/schedule/command-center/
schedulingApi.getTimeBlocks(params)  // GET /agent/schedule/time-blocks/?date=...
schedulingApi.updateGlobalTask(id, data) // PATCH /agent/schedule/global-tasks/{id}/
```

### 1.4 React Query Hooks (`client/lib/hooks/useScheduling.ts`, 297 lines)

```typescript
// Already configured with 60s polling:
useCommandCenter()   // staleTime: 30s, refetchInterval: 60s
useTimeBlocks()      // staleTime: 30s
useGlobalTasks()     // staleTime: 30s

// Mutation (used for checkbox completion):
useUpdateGlobalTask()  // invalidates: globalTasks + commandCenter
useCompleteGlobalTask() // invalidates: globalTasks + commandCenter
```

**Note:** `refetchInterval: 60_000` already exists on `useCommandCenter`. The new dashboard just needs to consume it read-only.

### 1.5 Complete Type Definitions (`client/lib/types/scheduling.ts`, 364 lines)

**Key types:**
```typescript
interface AgentTimeBlock {
  id: string;
  date: string;                 // YYYY-MM-DD
  start_time: string;           // HH:MM:SS
  end_time: string;             // HH:MM:SS
  block_type: BlockType;        // 'deep_work' | 'reactive' | 'creative' | ...
  title: string;
  color: string;
  client: string | null;
  client_name: string;
  is_completed: boolean;
  duration_minutes: number;
}

interface AgentGlobalTask {
  id: string;
  title: string;
  status: 'todo' | 'in_progress' | 'in_review' | 'done';
  priority: 'low' | 'medium' | 'high';
  client: string | null;
  client_name: string;
  task_category_detail: TaskCategoryItem | null;
  scheduled_date: string | null;
  start_time: string | null;    // null = unscheduled
  end_time: string | null;
  is_recurring: boolean;
  recurrence_parent: string | null;
  is_overdue: boolean;
  completed_at: string | null;
}

interface CommandCenterData {
  date: string;
  time_blocks: AgentTimeBlock[];
  todays_global_tasks: AgentGlobalTask[];
  todays_client_tasks: CrossClientTask[];
  overdue_tasks: CrossClientTask[];
  stats: CommandCenterStats;
}

interface CommandCenterStats {
  total_active_tasks: number;
  completed_today: number;
  hours_blocked_today: number;
  active_clients: number;
}
```

### 1.6 Design Tokens (`client/app/globals.css`)

```css
/* Colors */
--color-accent: #2563EB;
--color-accent-light: #DBEAFE;
--color-surface: #FFFFFF;
--color-surface-subtle: #FAFAFA;
--color-surface-muted: #F4F4F5;
--color-border: #E4E4E7;
--color-text: #18181B;
--color-text-secondary: #52525B;
--color-text-muted: #A1A1AA;

/* Shadows */
--shadow-surface: 0 2px 8px rgba(0,0,0,0.06);
--shadow-lg: 0 4px 16px rgba(0,0,0,0.08);

/* Transitions */
--transition-fast: 150ms;
--transition-default: 200ms;
--transition-slow: 300ms;
```

Block type colors already defined in `BLOCK_TYPE_COLORS` constant (13 colors for deep_work, reactive, creative, etc.)

### 1.7 Time Utilities (`client/components/portal/calendar/utils/timeUtils.ts`)

```typescript
timeToMinutes("07:30") → 450       // "HH:MM:SS" or "HH:MM"
minutesToTime(450) → "07:30"
formatHour(7) → "7 AM", formatHour(19) → "7 PM"
getEventStyle(startTime, endTime, startHour, hourHeight) → { top, height }
```

These utilities are already available for KPI progress calculation and time display.

### 1.8 Testing Setup

- **Test runner:** Vitest v4.1.2
- **DOM:** jsdom
- **Libraries:** @testing-library/react v16.3.2, @testing-library/jest-dom v6.9.1, @testing-library/user-event v14.6.1
- **Config:** `client/vitest.config.ts` with `globals: true`, `@` alias
- **Test utilities:** `client/test-utils/scheduling.tsx`
  - `createMockTimeBlock(overrides?)` — creates a mock AgentTimeBlock
  - `createMockGlobalTask(overrides?)` — creates a mock AgentGlobalTask
  - `renderWithQuery(ui)` — renders with QueryClientProvider wrapper
- **Existing tests:** `client/components/agent/scheduling/__tests__/DaySchedule.test.tsx` (110 lines)
  - Patterns: `vi.mock('@/lib/hooks/useScheduling', ...)` for hook mocking
  - Uses `renderWithQuery()`, `vi.useFakeTimers()` for time-based tests

### 1.9 Dashboard Page Integration

- Developer dashboard: `client/app/dashboard/agent/developer/schedule/page.tsx` just renders `<CommandCenter agentType="website" />`
- Marketing: Similar pattern expected for marketing agent
- New KPI dashboard would replace or sit above `CommandCenter` in the route hierarchy

### 1.10 Real-time Pattern Already in Code

```typescript
// CommandCenter.tsx — existing 60s interval pattern
useEffect(() => {
  const id = setInterval(() => setNow(new Date()), 60_000);
  return () => clearInterval(id);
}, []);
```

For the KPI widget progress bar, a similar `useEffect + setInterval` (or `useState(new Date())` refreshed every 60s) computes the current task's progress:
```
progress = (now - startTime) / (endTime - startTime) * 100
```

---

## 2. Web Research Findings

### 2.1 React Query Polling for 60s Dashboards

**Best pattern (TanStack Query v5):**
```typescript
const { data, isFetching } = useQuery({
  queryKey: ['dashboard', 'command-center'],
  queryFn: apiFetchCommandCenter,
  staleTime: 55_000,              // slightly less than interval prevents double-fetch on focus
  refetchInterval: 60_000,        // 60s polling
  refetchIntervalInBackground: false,  // pauses when tab hidden (free CPU saving)
  refetchOnWindowFocus: true,     // catches up when user returns
  gcTime: 5 * 60 * 1000,         // keep in cache 5 min after unmount
});
```

**Key insight**: `staleTime` and `refetchInterval` are orthogonal. Without `staleTime: 55_000`, every tab focus triggers an extra refetch (in addition to the interval). Setting `staleTime` just below the interval prevents the double-fetch.

**Tab hidden behavior**: `refetchIntervalInBackground: false` (the default) automatically pauses polling when the tab is hidden via the Page Visibility API. No extra code needed.

**Show subtle refresh indicator** (not blocking skeleton):
```tsx
if (isLoading) return <DashboardSkeleton />;
// isFetching shows subtle spinner during background refetch
return <div>{isFetching && <RefreshIndicator />}<Dashboard data={data} /></div>;
```

### 2.2 KPI Progress Bar Animation

**Rule**: For a progress bar whose value comes from server data (KPI widget showing task progress), use CSS `transition` on `transform: scaleX()`. This is GPU-composited (better perf than `width`), handles discrete value jumps from polling, and needs zero JS animation code.

```tsx
// For current task progress bar (value updates every 60s from server):
<div style={{ width: '100%', height: 12, background: 'var(--color-surface-muted)', borderRadius: 6 }}>
  <div
    style={{
      height: '100%',
      background: 'var(--color-accent)',
      borderRadius: 6,
      transform: `scaleX(${progress / 100})`,
      transformOrigin: 'left',
      transition: 'transform 800ms cubic-bezier(0.4, 0, 0.2, 1)',
    }}
  />
</div>
```

**For time-elapsed bars** (if showing countdown to next refresh): Use `requestAnimationFrame` in a custom hook — never `setInterval` for animation (imprecise, no frame sync, throttled in background).

**Don't combine** `requestAnimationFrame` updates with CSS transitions on the same property (compound interpolation artifacts).

### 2.3 Optimistic Checkbox Updates (TanStack Query v5)

**Two patterns — choose based on query structure:**

**Pattern A: Variables-based** (simpler, recommended for isolated checkboxes)
```tsx
const { mutate, isPending, variables } = useMutation({
  mutationFn: (status: GlobalTaskStatus) => api.updateGlobalTask(task.id, { status }),
  onError: () => toast.error('Failed to update task. Change reverted.'),
  onSettled: () => queryClient.invalidateQueries({ queryKey: ['scheduling', 'command-center'] }),
});
const isChecked = isPending ? (variables === 'done') : (task.status === 'done');
```
- Rollback is automatic (no explicit code): when `isPending` → false, `variables` resets, UI shows server value
- Use when each task renders its own checkbox with its own optimistic state

**Pattern B: Cache onMutate** (for shared list queries)
```tsx
onMutate: async ({ id, status }) => {
  await queryClient.cancelQueries({ queryKey: ['scheduling', 'command-center'] });
  const previous = queryClient.getQueryData(['scheduling', 'command-center']);
  queryClient.setQueryData(['scheduling', 'command-center'], (old) => ({
    ...old,
    todays_global_tasks: old.todays_global_tasks.map(t =>
      t.id === id ? { ...t, status } : t
    )
  }));
  return { previous };
},
onError: (err, vars, context) => {
  queryClient.setQueryData(['scheduling', 'command-center'], context.previous);
  toast.error('Failed to update. Reverted.');
},
onSettled: () => queryClient.invalidateQueries({ queryKey: ['scheduling', 'command-center'] }),
```

**Race condition guard** (rapid checkbox toggling):
```typescript
onSettled: () => {
  if (queryClient.isMutating({ mutationKey: ['toggle-task'] }) === 1) {
    queryClient.invalidateQueries({ queryKey: ['scheduling', 'command-center'] });
  }
},
```

**Recommendation for this project**: Since tasks are rendered from the shared `CommandCenterData` query, use **Pattern B (cache onMutate)** to update `todays_global_tasks` optimistically within the existing `command-center` cache entry. Add `mutationKey: ['toggle-task']` and the `isMutating()` guard.

---

## 3. Architecture Decisions from Research

### For Current Task KPI Progress Calculation

The `AgentTimeBlock` type has `start_time: "HH:MM:SS"` and `end_time: "HH:MM:SS"`. Use `timeToMinutes()` from `timeUtils.ts`:

```typescript
function getCurrentTaskProgress(block: AgentTimeBlock, now: Date): number {
  const nowMinutes = now.getHours() * 60 + now.getMinutes();
  const startMinutes = timeToMinutes(block.start_time);
  const endMinutes = timeToMinutes(block.end_time);
  return Math.min(100, Math.max(0,
    ((nowMinutes - startMinutes) / (endMinutes - startMinutes)) * 100
  ));
}
```

Local `now` state updated every 60s drives this — already the pattern in CommandCenter.

### For Read-Only DaySchedule

DaySchedule can be used in read-only mode by:
1. Not passing `externalDnd` (so no DnD wrapping)
2. Removing or ignoring the click handlers on blocks
3. Keeping the `NowIndicator` — it's pure display

A simpler approach: create a new `ReadOnlySchedule` component that renders the same grid/blocks without any DnD code. This keeps the existing DaySchedule untouched for the portal.

### For the Dashboard Page Route

The dashboard should be a new page (or refactored main route) that:
1. Imports `CommandCenterData` via `useCommandCenter()`
2. Renders the new KPI widget, stats row, task list, and read-only schedule
3. Provides deep-link navigation via `router.push('/management/calendar')`

---

## 4. Testing Approach

Use Vitest + @testing-library/react (existing setup). Key test areas:

1. **CurrentTaskKpi** — test chronological sync logic:
   - Given time blocks, renders correct "active" block for current time
   - Shows "No active task" empty state when no block active
   - Shows "Free until X" state between tasks
   - Progress calculation is correct (0%, 50%, 100% cases)
   - Timer fires and updates progress

2. **Task checkbox** — test optimistic update:
   - Renders unchecked → check → shows done state optimistically
   - On mutation error, reverts to original state

3. **Stats row** — test data mapping:
   - Renders correct values from `CommandCenterStats`

4. **ReadOnlySchedule** — test rendering:
   - Blocks render at correct positions
   - Current time indicator visible
   - No click handlers active

Mock utilities: `createMockTimeBlock()`, `createMockGlobalTask()`, `renderWithQuery()` are all available in `client/test-utils/scheduling.tsx`.
