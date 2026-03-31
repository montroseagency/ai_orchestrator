# Section 07: BacklogPane

## Overview

This section builds the left-side task panel for the scheduling calendar. It consists of two files:

- `client/components/portal/calendar/BacklogPane.tsx` — the collapsible container pane
- `client/components/portal/calendar/BacklogTaskItem.tsx` — the individual draggable task card

The `BacklogPane` is ~250px wide and collapses to a ~40px icon strip. It shows unscheduled tasks grouped by day (Day view) or as a Mon–Fri accordion (Week view). A search bar filters tasks across all visible sections simultaneously.

**Dependencies required before starting:**
- `section-01-test-utils` must be complete (provides `createMockGlobalTask`, `renderWithQuery`, `mockUseSchedulingEngine`)
- `section-04-data-hook` must be complete (provides `useSchedulingEngine` hook with `todayTasks`, `overdueTasks`, `completeTask`, `viewMode`, `weekDays`)

---

## Files to Create

```
client/components/portal/calendar/BacklogPane.tsx
client/components/portal/calendar/BacklogTaskItem.tsx
client/components/portal/calendar/BacklogPane.test.tsx
client/components/portal/calendar/BacklogTaskItem.test.tsx
```

---

## Tests First

Write tests in `BacklogPane.test.tsx` and `BacklogTaskItem.test.tsx` before implementing. Use the test utilities from `section-01-test-utils`.

### BacklogPane tests (`BacklogPane.test.tsx`)

Mock `useSchedulingEngine` using the `mockUseSchedulingEngine` helper. Wrap renders with `renderWithQuery`.

```typescript
// Stub mock for @dnd-kit/core — provide useDraggable returning { attributes: {}, listeners: {}, setNodeRef: () => {}, isDragging: false }
// The BacklogTaskItem drag behavior is tested separately; BacklogPane tests focus on layout and logic

describe('BacklogPane — Day view', () => {
  it('renders "Today\'s Tasks" section with tasks from todayTasks')
  it('renders "Overdue" section only when overdueTasks.length > 0')
  it('does NOT render "Overdue" section when overdueTasks is empty')
  it('count badge shows correct total (todayTasks.length + overdueTasks.length)')
  it('search input filters displayed tasks by title — case-insensitive match')
  it('search hides non-matching tasks')
  it('search filters across both Today and Overdue sections simultaneously')
})

describe('BacklogPane — Week view accordion', () => {
  it('renders one section per weekday (Mon–Fri) when viewMode is "week"')
  it('activeColumnDate prop change expands the matching day section')
  it('only one accordion section is expanded at a time')
})

describe('BacklogPane — Collapse toggle', () => {
  it('collapse button hides the task list and shows ▶ to re-expand')
  it('expanding from collapsed state restores the task list')
  it('collapse state persists to localStorage key "scheduler_backlog_collapsed"')
  it('reads initial collapsed state from localStorage on mount')
})
```

### BacklogTaskItem tests (`BacklogTaskItem.test.tsx`)

```typescript
describe('BacklogTaskItem', () => {
  it('renders the task title')
  it('renders a client/category badge with task_category_detail.name or client_name')
  it('high priority task has border-red-500 class on left border')
  it('medium priority task has border-amber-400 class on left border')
  it('low priority task has border-gray-300 class on left border')
  it('checkbox click calls completeTask with the task id')
  it('task fades out (opacity class) after checkbox is clicked')
  it('grip handle (⠿ icon) has touch-action: none; card body does not')
})

describe('BacklogTaskItem — sort order', () => {
  // These tests exercise the sort logic by passing an array to BacklogSection
  // and asserting DOM order
  it('sorts high priority before medium before low')
  it('within same priority, sorts by due_date ascending (soonest first)')
  it('tasks with null due_date appear last within their priority group')
  it('within same priority and due_date, sorts alphabetically by title')
})
```

---

## Implementation Details

### `BacklogTaskItem.tsx`

This component renders a single draggable task card. Key points:

**Drag setup:**
```typescript
const { attributes, listeners, setNodeRef, isDragging } = useDraggable({
  id: task.id,
  data: { type: 'backlog-task', task },
})
```

Apply `setNodeRef` and drag `attributes` to the outer card div. Apply `listeners` **only to the grip handle element** (the ⠿ icon), not to the whole card. This is important — applying `touch-action: none` only to the grip avoids blocking scroll on mobile.

**Priority border colors:**
- `priority === 'high'` → `border-l-4 border-red-500`
- `priority === 'medium'` → `border-l-4 border-amber-400`
- `priority === 'low'` (or default) → `border-l-4 border-gray-300`

**Checkbox behaviour:** When the checkbox is toggled, call `completeTask(task.id)`. Apply a CSS transition to reduce opacity (`opacity-50`) immediately (optimistic visual) — the item will be removed from the list once the mutation settles and the cache updates.

**Client/category badge:** Render `task.task_category_detail?.name ?? task.client_name` in a small pill alongside a colored dot. Use `task.color` if available for the dot, otherwise fall back to a neutral gray.

**Active/dragging state:** When `isDragging` is true, render the card with reduced opacity (`opacity-50`) so it appears as a ghost while the `<DragOverlay>` preview follows the cursor.

**Signature stub:**
```typescript
interface BacklogTaskItemProps {
  task: AgentGlobalTask
  completeTask: (taskId: string) => void
}

export function BacklogTaskItem({ task, completeTask }: BacklogTaskItemProps): JSX.Element
```

---

### `BacklogPane.tsx`

**Internal sort function** — apply via `useMemo` before passing tasks to section components:

```typescript
function sortTasks(tasks: AgentGlobalTask[]): AgentGlobalTask[] {
  // Sort by: priority desc (high=0, medium=1, low=2), then due_date asc (nulls last), then title asc
}
```

Priority weight map: `{ high: 0, medium: 1, low: 2 }`.

**Search filtering** — keep a `searchQuery` state string. Filter each task list with:
```typescript
task.title.toLowerCase().includes(searchQuery.toLowerCase())
```
Apply filtering after sorting, in the same `useMemo` block.

**Collapse state:**
```typescript
const [isCollapsed, setIsCollapsed] = useState<boolean>(() => {
  // Read from localStorage key 'scheduler_backlog_collapsed' on init
  return localStorage.getItem('scheduler_backlog_collapsed') === 'true'
})
```
On toggle, update both the state and `localStorage.setItem('scheduler_backlog_collapsed', String(!isCollapsed))`.

When collapsed, render only the ~40px strip with a `▶` expand button and nothing else. When expanded, render the full pane content.

**Day view structure:**

```
<aside class="backlog-pane [collapsed or expanded]">
  <header>
    <span>{total} unscheduled</span>    ← count badge
    <input type="search" ... />         ← search bar
    <button onClick={collapse}>◀</button>
  </header>
  <BacklogSection title="Today's Tasks" tasks={filteredToday} completeTask={completeTask} />
  {filteredOverdue.length > 0 && (
    <BacklogSection title="Overdue" tasks={filteredOverdue} completeTask={completeTask} />
  )}
</aside>
```

**Week view accordion:**

Keep `expandedDay: string | null` state (initialized to `null` or the first weekday).

```typescript
useEffect(() => {
  if (activeColumnDate) {
    setExpandedDay(activeColumnDate)
    // scroll the matching section into view
  }
}, [activeColumnDate])
```

Render one `<BacklogSection>` per day in `weekDays` (Mon–Fri ISO strings). Each section receives `isExpanded={expandedDay === date}` and an `onToggle={() => setExpandedDay(expandedDay === date ? null : date)}` prop.

**`BacklogSection` inner component** (can be defined in the same file or as a separate non-exported component):

```typescript
interface BacklogSectionProps {
  title: string
  tasks: AgentGlobalTask[]
  completeTask: (id: string) => void
  isExpanded?: boolean      // for accordion mode
  onToggle?: () => void     // for accordion mode
}
```

Renders a titled list of `<BacklogTaskItem>` components. In accordion mode, shows a chevron in the header and animates open/close.

**`BacklogPane` prop signature:**

```typescript
interface BacklogPaneProps {
  todayTasks: AgentGlobalTask[]
  overdueTasks: AgentGlobalTask[]
  completeTask: (taskId: string) => void
  viewMode: 'day' | 'week'
  weekDays: string[]                   // Mon–Fri ISO date strings
  activeColumnDate?: string | null     // set by SchedulingEngine when a grid column is clicked
}

export function BacklogPane(props: BacklogPaneProps): JSX.Element
```

**Note on data access:** `BacklogPane` receives all task data as props from `SchedulingEngine`, which reads from `useSchedulingEngine`. `BacklogPane` does **not** call `useSchedulingEngine` directly. This keeps it easily testable without needing the full hook context.

---

## Visual Design

Follow the `Ui-Ux-Pro-Max` design language from the existing portal components.

- Pane background: `var(--color-surface-subtle)` with a right border `var(--color-border)`
- Section headers: `text-xs font-semibold text-secondary uppercase tracking-wide`
- Task cards: `rounded-md bg-surface p-2 mb-1.5 shadow-sm` with the priority left border
- Search input: borderless style inside the pane header, placeholder "Search tasks…"
- Count badge: small pill `bg-accent-light/20 text-accent text-xs font-medium px-2 py-0.5 rounded-full`
- Grip handle: `text-gray-400 hover:text-gray-600 cursor-grab active:cursor-grabbing`
- Collapse animation: `transition-all duration-200 var(--transition-fast)`
- Collapsed state width: `w-10` (40px); expanded: `w-[250px]`

---

## Empty State

When both `todayTasks` and `overdueTasks` are empty (after filtering), render:

```
<div class="empty-backlog">
  <CalendarIcon class="w-8 h-8 text-secondary/40" />
  <p>No unscheduled tasks</p>
</div>
```

Do not show empty section headers — hide them entirely when their filtered task list is empty.

---

## Dependency Notes

- `useDraggable` from `@dnd-kit/core` — already installed
- `AgentGlobalTask` type from `client/lib/types/scheduling.ts` — use as-is, no changes needed
- `completeTask` mutation function comes from the parent (`SchedulingEngine` via `useSchedulingEngine`) — `BacklogPane` does not call the hook directly
- The `useDroppable` droppable zone for "drop block back to backlog" is set up in `SchedulingEngine`, **not** in `BacklogPane` — `SchedulingEngine` wraps the pane in a droppable; `BacklogPane` itself does not need to register a drop target

---

## Acceptance Criteria

Before marking this section complete:

1. All tests in `BacklogPane.test.tsx` and `BacklogTaskItem.test.tsx` pass
2. Day view renders Today + Overdue sections with correct counts
3. Week view accordion renders Mon–Fri; `activeColumnDate` opens the correct section
4. Search filters tasks case-insensitively across all visible sections
5. Sort order is correct: priority desc → due_date asc (nulls last) → title asc
6. Collapse toggle works and persists to localStorage
7. Priority border colors match spec (red/amber/gray)
8. Checkbox calls `completeTask` and gives immediate visual feedback
9. Drag listeners are on the grip handle only; `touch-action: none` does not block card-level scroll
10. No TypeScript errors (`npm run type-check` passes in `client/`)
