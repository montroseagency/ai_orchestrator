# Research: Interactive Scheduling Engine

## Part 1: Codebase Analysis

### Existing Scheduling Components

**`client/components/agent/scheduling/DaySchedule.tsx`** (510 lines)
- Hourly timeline grid, 24h (0–24), `HOUR_HEIGHT = 50px`
- Uses `@dnd-kit/core` with `DndContext`, `DragOverlay`, `useDraggable`, `useDroppable`
- Collision detection: `closestCenter`
- Draggable types: `time-block`, `timed-task`, external tasks
- Droppable zones: `hour-{hour}` slots (per-hour, not per-slot)
- Y-axis only transform: `translate3d(0, ${transform.y}px, 0)`
- No modifiers (no snap), no custom sensors configured
- No optimistic updates — waits for API response, then invalidates
- Utilities already defined: `timeToMinutes()`, `minutesToTime()`, `formatHour()`

**`client/components/agent/scheduling/CommandCenter.tsx`** (731 lines)
- Dashboard hub wrapping DaySchedule; currently the scheduling container
- Multiple sections: stats, agenda, calendar, tasks sidebar, focus timer
- `useMemo` for filtering, `useCallback` for handlers
- Mobile: switches to `MobileAgendaView` (period-based grouping)

**`client/components/agent/scheduling/WeeklyPlanView.tsx`** (276 lines)
- Goals management (low/medium/high priority)
- Day themes (Mon-Sun, indexed 0-6)
- Planning/retrospective notes, target hours tracking
- Week calculation: Monday-based (`getMonday()`)
- **Not an interactive calendar** — text/form based weekly planner

**`client/components/agent/scheduling/TimeBlockEditor.tsx`** (216 lines)
- Modal for create/edit time blocks
- Color picker, block type selection with dynamic labels
- Delete with confirmation
- Supports marketing and developer agent types

**`client/app/dashboard/agent/marketing/management/calendar/page.tsx`**
- Currently a placeholder ("coming soon")
- This is the target portal route for the new calendar

### Types (client/lib/types/scheduling.ts — 364 lines)

**`AgentTimeBlock`:**
```typescript
{
  id: string; agent: string; date: string; // YYYY-MM-DD
  start_time: string; end_time: string;    // HH:MM:SS
  block_type: BlockType; title: string; color: string;
  client: string | null; client_name: string;
  notes: string; is_completed: boolean; duration_minutes: number;
  recurring_source: string | null;
  created_at: string; updated_at: string;
}
```

**`AgentGlobalTask`:**
```typescript
{
  id: string; agent: string; title: string; description: string;
  status: GlobalTaskStatus; priority: TaskPriority;
  client: string | null; client_name: string;
  task_category_ref: string | null; task_category_detail: TaskCategoryItem | null;
  due_date: string | null; scheduled_date: string | null;
  time_block: string | null; time_block_title: string;
  estimated_minutes: number | null;
  start_time: string | null; end_time: string | null;  // can be timed or unscheduled
  order: number; is_recurring: boolean; is_overdue: boolean;
  // ...recurrence fields
}
```

**`ScheduledTaskLink`:**
```typescript
{
  id: string; agent: string; task: string;
  scheduled_date: string | null; time_block: string | null;
  order: number; task_title: string; task_status: string;
  task_type: string; client_name: string;
}
```

### API Layer (client/lib/api/scheduling.ts — 227 lines)

All spec-referenced methods exist and are ready to use:
- `getTimeBlocks(params?)` — GET with optional date range filter
- `createTimeBlock(data)` — POST
- `updateTimeBlock(id, data)` — PATCH
- `deleteTimeBlock(id)` — DELETE
- `getGlobalTasks(filters?)` — GET with optional filters (scheduled_date, time_block, etc.)
- `updateGlobalTask(id, data)` — PATCH

Additional useful: `bulkCreateTimeBlocks()`, `getTaskLinks()`, `createTaskLink()`, `updateTaskLink()`

**Error handling:** `ApiService.request()` with try/catch, toast notifications via `toast.error()`
**Cache keys:** `SCHEDULE_KEYS` object with hierarchical structure for targeted invalidation
**Stale times:** time blocks/tasks = 30s, weekly plans = 60s

### Current @dnd-kit Usage

```typescript
// Current sensors: defaults (no custom config)
// Current modifiers: none (no snapping)
// Current collision detection: closestCenter
// Current drag data:
useDraggable({ id: block.id, data: { type: 'time-block', block } })
useDraggable({ id: `task-${task.id}`, data: { type: 'timed-task', task } })
useDroppable({ id: `hour-${hour}`, data: { type: 'hour-slot', hour } })
```

**Gap from spec requirements:**
- Needs snap-to-15min/30min via `createSnapModifier`
- Needs 30min-resolution droppables (not hourly), or pointer-based time calculation
- Needs `PointerSensor` with `distance: 8` activation constraint
- Needs separate resize-handle draggables per block
- Needs cross-column droppables for week view
- Needs backlog pane with its own draggables

### Portal Route Structure

```
/dashboard/agent/{marketing|developer}/management/
├── page.tsx        (overview — 4 nav cards)
├── calendar/       ← TARGET: replace placeholder with new scheduling engine
├── tasks/
├── clients/
└── notes/
```

The calendar route is the new home for this feature; the old CommandCenter scheduling view stays at `/schedule`.

### Design Tokens (globals.css)

All spec-referenced CSS variables exist:
```css
--color-surface-subtle: #FAFAFA
--color-surface: #FFFFFF
--color-border: #E4E4E7
--color-border-subtle: #F4F4F5
--color-accent: #2563EB
--color-accent-light: #DBEAFE
--color-text: #18181B
--color-text-secondary: #52525B
--color-text-muted: #A1A1AA
--transition-fast: 150ms
--transition-default: 200ms
--shadow-lg: 0 4px 16px rgba(0,0,0,0.08)
--radius-surface: 8px
```

### Testing Setup

- **Framework:** Vitest 4.1.2 + React Testing Library
- **Config:** `client/vitest.config.ts`, jsdom environment, globals: true
- **Matchers:** `@testing-library/jest-dom` via `vitest.setup.ts`
- **Current coverage:** Management page stubs only — NO tests exist for any scheduling components
- **Test pattern:** `render()` + `screen.getBy*()` + `vi.mock()`

### Key Architectural Insights

1. **Two-phase scheduling:** Time blocks (fixed slots, calendar-like) vs Global tasks (flexible, can be unscheduled or linked to blocks)
2. **ScheduledTaskLink** bridges external client tasks to date/block — enables cross-client task management
3. **No optimistic updates currently** — all mutations wait for server round-trip
4. **HOUR_HEIGHT = 50px** (current) — spec targets 60px/hr for cleaner math (1px = 1min)
5. **Time stored as `HH:MM:SS` strings** on both frontend and backend

---

## Part 2: @dnd-kit Best Practices

### Sensors Configuration

Use `PointerSensor` with `distance: 8` activation constraint to prevent click handlers from being swallowed by drag intent:

```typescript
const sensors = useSensors(
  useSensor(PointerSensor, {
    activationConstraint: { distance: 8 }
  }),
  useSensor(KeyboardSensor, {
    coordinateGetter: sortableKeyboardCoordinates,
  })
);
```

Apply `touch-action: none` only on the drag handle element (not the entire event card) to prevent browser scroll conflicts.

### Ghost / DragOverlay

- `<DragOverlay>` must remain **always mounted** — only conditionally render its children
- Use a presentational (non-draggable) clone inside `<DragOverlay>`
- Default drop animation: 250ms ease. Customize via `dropAnimation` prop.

```tsx
<DragOverlay dropAnimation={{ duration: 200, easing: 'ease' }}>
  {activeId ? <EventCardPresentation id={activeId} /> : null}
</DragOverlay>
```

### Snap-to-Slot via Modifiers

`createSnapModifier(gridSizePx)` from `@dnd-kit/modifiers`:

```typescript
import { createSnapModifier } from '@dnd-kit/modifiers';

// 60px/hr, 15min slot = 15px
const snap15Min = createSnapModifier(15);
// 30min slot = 30px
const snap30Min = createSnapModifier(30);
```

`gridSizePx` must equal the rendered pixel height of a single time slot. If `HOUR_HEIGHT = 60px`:
- 15min snap → `createSnapModifier(15)`
- 30min snap → `createSnapModifier(30)`

Other useful modifiers: `restrictToVerticalAxis`, `restrictToParentElement`.

### Resize Handles

Treat the resize handle as a **second independent draggable** inside the event:

```tsx
// Inside CalendarEventCard:
const moveHandle = useDraggable({
  id: `move-${id}`,
  data: { type: 'move', eventId: id }
});

const resizeHandle = useDraggable({
  id: `resize-${id}`,
  data: { type: 'resize', eventId: id }
});
```

In `onDragEnd`, check `active.data.current.type` to route to move vs resize handler.
- Move: update `start_time` + `end_time` preserving duration
- Resize: delta Y (`delta.y`) → additional minutes = `delta.y / pixelsPerMinute`

Stop propagation on the resize handle's `onPointerDown` to prevent the parent drag from activating.

### Cross-Column Drag (Week View)

Each day column is a separate `useDroppable`. Use `onDragOver` to optimistically re-parent the event as it crosses columns:

```tsx
function handleDragOver({ active, over }) {
  if (!over) return;
  const sourceDay = active.data.current.date;
  const targetDay = over.data.current.date;
  if (sourceDay !== targetDay) {
    // Optimistically move in local state for visual feedback
  }
}
```

`<DragOverlay>` prevents visual discontinuity when events unmount/remount across columns.

### Collision Detection

For a time grid, compose `pointerWithin` as primary with `closestCenter` as fallback:

```typescript
function calendarCollisionDetection(args) {
  const pointerCollisions = pointerWithin(args);
  if (pointerCollisions.length > 0) return pointerCollisions;
  return closestCenter(args);
}
```

---

## Part 3: Hourly Calendar Grid Implementation

### Pixel-to-Time Mapping

With `HOUR_HEIGHT = 60px` (1px = 1 minute):

```typescript
const HOUR_HEIGHT_PX = 60;     // px per hour
const START_HOUR = 6;          // 6 AM
const SLOT_MINUTES = 30;       // snap resolution
const SLOT_HEIGHT_PX = 30;     // = HOUR_HEIGHT * (30/60)

function minutesToPx(minutes: number): number {
  return minutes * (HOUR_HEIGHT_PX / 60); // = minutes px
}
function pxToMinutes(px: number): number {
  return px; // 1:1 with 60px/hr
}
function snapToSlot(minutes: number): number {
  return Math.round(minutes / SLOT_MINUTES) * SLOT_MINUTES;
}

// Event positioning inside day column
function getEventStyle(startTime: string, endTime: string) {
  const startMin = timeToMinutes(startTime) - START_HOUR * 60;
  const endMin = timeToMinutes(endTime) - START_HOUR * 60;
  return {
    position: 'absolute',
    top: minutesToPx(startMin),
    height: minutesToPx(endMin - startMin),
    left: 0, right: 0,
  };
}
```

### Calendar Layout Architecture

Two-layer approach: background grid (CSS) + event layer (absolutely positioned):

```
[Time gutter] | [Day columns — position: relative]
                   ├── Grid lines (background)   ← position: absolute, inset: 0
                   └── Event blocks (foreground) ← position: absolute, top/height computed
```

### All-Day Header

Separate fixed-height header row above the scrollable grid:

```tsx
<div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
  {/* Fixed header: date names + all-day events */}
  <div style={{ flexShrink: 0 }}>
    <AllDayRow />  {/* separate droppable from timed grid */}
  </div>
  {/* Scrollable time grid */}
  <div style={{ flex: 1, overflow: 'auto' }}>
    <TimeGrid />
  </div>
</div>
```

All-day area needs a minimum height (~40–60px) when empty to remain a valid drop target. Route `onDragEnd` to all-day handler when `over.data.current.type === 'allday'`.

### Auto-Scroll to Current Time

```typescript
useEffect(() => {
  const nowMinutes = (new Date().getHours() - START_HOUR) * 60 + new Date().getMinutes();
  const scrollTop = minutesToPx(nowMinutes) - viewportHeight / 3;
  gridRef.current?.scrollTo({ top: Math.max(0, scrollTop), behavior: 'smooth' });
}, []);
```

---

## Part 4: React Query Optimistic Updates

### Recommended Pattern (Cache-Based)

```typescript
useMutation({
  mutationKey: ['timeBlocks'],  // scope for concurrent mutation check
  mutationFn: (update) => schedulingApi.updateTimeBlock(update.id, update),

  onMutate: async (update) => {
    await queryClient.cancelQueries({ queryKey: SCHEDULE_KEYS.timeBlocks.all });
    const previous = queryClient.getQueryData(SCHEDULE_KEYS.timeBlocks.all);
    queryClient.setQueryData(SCHEDULE_KEYS.timeBlocks.all, (old: AgentTimeBlock[]) =>
      old.map(b => b.id === update.id ? { ...b, ...update } : b)
    );
    return { previous };
  },

  onError: (_err, _vars, context) => {
    queryClient.setQueryData(SCHEDULE_KEYS.timeBlocks.all, context?.previous);
    toast.error('Failed to update schedule');
  },

  onSettled: () => {
    // Only invalidate when this is the LAST concurrent mutation of this type
    if (queryClient.isMutating({ mutationKey: ['timeBlocks'] }) === 1) {
      queryClient.invalidateQueries({ queryKey: SCHEDULE_KEYS.timeBlocks.all });
    }
  },
});
```

### Concurrent Mutation Handling (TkDodo Pattern)

The `isMutating({ mutationKey }) === 1` check in `onSettled` is critical: it defers cache invalidation until the last in-flight mutation of the same type settles. This prevents intermediate refetches from overwriting subsequent optimistic updates during rapid drag-drop sequences.

### Drag-Drop Flow Summary

```
User drops → onDragEnd → mutate({ id, newStartTime, newEndTime })
  → onMutate: cancelQueries → setQueryData (optimistic) → UI updates instantly
  → [network] PATCH /time-blocks/:id
  → onSettled: isMutating check → invalidateQueries → server state syncs
  → onError (if fail): setQueryData(previous) → event snaps back
```

---

## Testing Recommendations

Since there are no existing scheduling component tests, new tests should:

1. **Unit test time utilities** in isolation: `timeToMinutes`, `minutesToTime`, `snapToSlot`, `getEventStyle`
2. **Mock @dnd-kit** for component tests (dnd-kit doesn't work in jsdom without patching)
3. **Mock React Query** with a `QueryClient` wrapper in test utils
4. **Integration tests** for the drop handler: verify `createTimeBlock` and `updateGlobalTask` are called with correct args when a task is dropped on a slot
5. **Snapshot tests** for Backlog pane and TimeBlock card rendering

Pattern:
```typescript
// vitest + RTL
const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
const wrapper = ({ children }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);
render(<SchedulerComponent />, { wrapper });
```

---

## Key Decisions for Implementation

| Decision | Recommendation | Rationale |
|---|---|---|
| HOUR_HEIGHT | 60px (change from current 50px) | 1px = 1 minute, simplifies math |
| Snap resolution | 30min for drop, 15min for resize | Spec default: 30min; resize: 15min |
| Collision detection | `pointerWithin` + `closestCenter` fallback | Most precise for time grid |
| Sensor activation | `distance: 8` | Prevents click→drag conflicts |
| Optimistic updates | Cache-based with isMutating check | Smooth UX for rapid drag sequences |
| Time block positioning | Absolute within position:relative day column | Standard, handles overlaps |
| Resize handle | Separate `useDraggable` on bottom 6px | dnd-kit native pattern |
| Week view cross-drag | `onDragOver` re-parenting + DragOverlay | No visual flicker |
