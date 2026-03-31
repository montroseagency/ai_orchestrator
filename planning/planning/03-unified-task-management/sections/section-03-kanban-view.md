# Section 03 — Kanban View

## Overview

This section builds the drag-and-drop Kanban board for the Tasks page. It is parallelizable with sections 02, 04, and 05 — but requires **section-01-data-foundation** to be complete first (provides `ClientBadge`, `clientPalette`, and shared types).

**Output files (all new, none modify existing files):**

```
client/components/management/tasks/TaskCard.tsx
client/components/management/tasks/TaskCardOverlay.tsx
client/components/management/tasks/KanbanColumn.tsx
client/components/management/tasks/TasksKanbanView.tsx
client/app/dashboard/agent/marketing/management/tasks/__tests__/TaskCard.test.tsx
client/app/dashboard/agent/marketing/management/tasks/__tests__/KanbanColumn.test.tsx
client/app/dashboard/agent/marketing/management/tasks/__tests__/TasksKanbanView.test.tsx
```

**Run tests:** `cd client && npx vitest run`

---

## Dependencies

- **section-01-data-foundation** must be complete. You will import:
  - `ClientBadge` from `@/components/management/tasks/ClientBadge`
  - `getClientColor` from `@/components/management/tasks/clientPalette`
  - Types: `AgentGlobalTask`, `GlobalTaskStatus` from `@/lib/types/scheduling`
- **Hooks** (already exist in `client/lib/hooks/useScheduling.ts`):
  - `useUpdateGlobalTask()` — for status transitions to `todo`, `in_progress`, `in_review`, and for order changes
  - `useCompleteGlobalTask()` — **exclusively** for transitions to `done`
- **@dnd-kit** packages already installed: `@dnd-kit/core`, `@dnd-kit/sortable`, `@dnd-kit/utilities`
- **Toast notifications:** `sonner` (already installed) — import `toast` from `sonner`
- **Icons:** `lucide-react` — `GripVertical`, `CalendarDays`, `RefreshCw`

---

## Step 1 — Write Tests First (TDD)

Write all three test files before implementing any component. Run `npx vitest run` and confirm they **fail** (red) before proceeding to implementation.

### `TaskCard.test.tsx`

Location: `client/app/dashboard/agent/marketing/management/tasks/__tests__/TaskCard.test.tsx`

Mock `@/components/management/tasks/ClientBadge` as a simple passthrough. Do not mock `@dnd-kit/sortable` — instead render `TaskCard` outside of any `SortableContext` by mocking `useSortable` to return stub values (transform: null, listeners: {}, attributes: {}, setNodeRef: () => {}, isDragging: false).

Test cases:

- Renders task title (truncated to 2 lines with `line-clamp-2` class)
- Renders `ClientBadge` with correct `clientId` and `clientName` props
- Renders category badge showing category name
- Renders priority dot with `bg-red-500` for high priority
- Renders priority dot with `bg-amber-500` for medium priority
- Renders priority dot with `bg-blue-500` for low priority
- Renders due date string alongside a `CalendarDays` icon
- Applies `text-status-error` class to the due date element when `is_overdue` is `true`
- Renders `RefreshCw` icon when `is_recurring` is `true`
- Does NOT render `RefreshCw` icon when `is_recurring` is `false`
- Clicking the card body (not drag handle) calls `onEdit(task)`
- Clicking the drag handle element does NOT call `onEdit`
- Card root element has `cursor-pointer` class
- Drag handle element has `cursor-grab` class

### `KanbanColumn.test.tsx`

Location: `client/app/dashboard/agent/marketing/management/tasks/__tests__/KanbanColumn.test.tsx`

Mock `@dnd-kit/sortable` (`SortableContext`) as a passthrough wrapper. Pass `TaskCard` children as render-prop or children array.

Test cases:

- Renders the column label text in uppercase
- Renders a task count badge showing the correct number (e.g. "(4)")
- Renders all provided task card children
- Renders an empty-state message (e.g. "No tasks here") when the tasks array is empty
- The rendered column area is non-zero height when empty (column remains visible, not collapsed)

### `TasksKanbanView.test.tsx`

Location: `client/app/dashboard/agent/marketing/management/tasks/__tests__/TasksKanbanView.test.tsx`

Mock `@dnd-kit/core` (`DndContext`, `DragOverlay`, `closestCenter`) as passthrough wrappers. Mock `useUpdateGlobalTask` and `useCompleteGlobalTask` from `@/lib/hooks/useScheduling` to return `{ mutate: vi.fn() }`. Mock `toast` from `sonner`.

To test `onDragEnd` logic without triggering real DOM drag events, extract the handler and call it directly in tests (or expose it via a test-id data attribute on the `DndContext`'s `onDragEnd` prop — the simplest approach is to export a `handleDragEnd` function separately and test it in unit tests).

Test cases:

- Renders exactly 4 columns labeled "To-Do", "In Progress", "In Review", "Done"
- Tasks are distributed to the correct column based on their `status` field
- `onTaskEdit` callback is passed through to task cards and fires when a card is clicked
- When `handleDragEnd` is called with a cross-column drop to `in_progress`: `useUpdateGlobalTask().mutate` is called with `{ id, status: 'in_progress' }`
- When `handleDragEnd` is called with a cross-column drop to `in_review`: `useUpdateGlobalTask().mutate` is called with `{ id, status: 'in_review' }` (NOT `useCompleteGlobalTask`)
- When `handleDragEnd` is called with a cross-column drop to `done`: `useCompleteGlobalTask().mutate` is called (NOT `useUpdateGlobalTask`)
- After successful `in_review` mutation (`onSuccess`): `toast` is called with the string `"Task sent for review"`
- After a failed mutation (`onError`): `toast` is called with `"Failed to move task — change reverted"` and the optimistic state is reverted
- The `"Task sent for review"` toast is NOT shown on mutation error

---

## Step 2 — Implement `TaskCard.tsx`

**File:** `client/components/management/tasks/TaskCard.tsx`

This is a display + interaction component. It uses `useSortable` from `@dnd-kit/sortable` for both the drag handle and the sortable positioning.

### Props interface

```typescript
interface TaskCardProps {
  task: AgentGlobalTask;
  onEdit: (task: AgentGlobalTask) => void;
}
```

### Key implementation notes

- Call `useSortable({ id: task.id })` at the top of the component. Destructure `attributes`, `listeners`, `setNodeRef`, `transform`, `transition`, `isDragging`.
- Apply `setNodeRef`, `style` (with transform/transition from dnd-kit), and `attributes` to the card's root `<div>`.
- Apply `...listeners` **only** to the drag handle element (the `GripVertical` icon wrapper), NOT to the card root. This ensures card clicks reach `onClick` while the drag handle initiates drag.
- Card root `onClick` handler: call `onEdit(task)`. The drag handle's `onClick` should call `e.stopPropagation()`.
- Apply `isDragging` style: when `isDragging` is true, apply `opacity-50` to the card (the `DragOverlay` shows the full-opacity ghost).

### Card layout (Tailwind classes)

```
Root div: bg-surface rounded-lg border border-border shadow-sm p-3 cursor-pointer
          transition-transform duration-150 hover:-translate-y-1
          (when isDragging: opacity-50)
```

Internal layout:

1. Top row: drag handle (`cursor-grab`) on the left, recurrence icon (`RefreshCw`, size 14) on the right — shown only when `task.is_recurring`
2. Client badge: `<ClientBadge clientId={task.client} clientName={task.client_name} />`
3. Category badge: small chip using `task.category_color` (or fallback) — style: `bg-[{color}20] text-[{color}] border border-[{color}40] rounded-full px-2 py-0.5 text-xs font-medium`
4. Title: `<p className="text-sm font-medium line-clamp-2">{task.title}</p>`
5. Bottom row:
   - Priority dot: `<span className="w-2 h-2 rounded-full inline-block" />` — `bg-red-500` (high), `bg-amber-500` (medium), `bg-blue-500` (low)
   - Due date: `<CalendarDays size={12} />` + formatted date string — apply `text-status-error` when `task.is_overdue`

---

## Step 3 — Implement `TaskCardOverlay.tsx`

**File:** `client/components/management/tasks/TaskCardOverlay.tsx`

This is the ghost card rendered inside `DragOverlay` during a drag operation. It receives the dragged task as a prop and renders a visual copy of `TaskCard` without the `useSortable` hook (static display only).

### Props interface

```typescript
interface TaskCardOverlayProps {
  task: AgentGlobalTask;
}
```

Render the same visual layout as `TaskCard` but without `useSortable`, `onClick`, or `onEdit`. Apply `shadow-lg opacity-90` to the root div. This component is intentionally minimal — it just needs to look like the card being dragged.

---

## Step 4 — Implement `KanbanColumn.tsx`

**File:** `client/components/management/tasks/KanbanColumn.tsx`

Each column is a droppable area that also provides a `SortableContext` for its tasks.

### Props interface

```typescript
interface KanbanColumnProps {
  status: GlobalTaskStatus;
  label: string;           // "To-Do", "In Progress", "In Review", "Done"
  tasks: AgentGlobalTask[];
  onTaskEdit: (task: AgentGlobalTask) => void;
}
```

### Key implementation notes

- Use `useDroppable({ id: status })` from `@dnd-kit/core` to make the column a drop target. The column's `id` as a droppable is its `status` string (e.g. `"todo"`). Apply `setNodeRef` to the column's task list container `<div>`.
- Wrap the task list in `<SortableContext items={tasks.map(t => t.id)} strategy={verticalListSortingStrategy}>` from `@dnd-kit/sortable`.
- Render each task as `<TaskCard key={task.id} task={task} onEdit={onTaskEdit} />`.
- When `tasks.length === 0`, render an empty-state `<div>` with text "No tasks here" and a minimum height (`min-h-[120px]`) so the column remains a valid drop target.

### Column layout

```
Outer div: flex flex-col min-w-[260px] max-w-[320px] flex-1
Header: flex items-center justify-between mb-3
  Label: text-xs font-medium uppercase tracking-wider text-secondary
  Count badge: text-xs bg-surface-subtle rounded-full px-2 py-0.5 text-secondary
Task list container (setNodeRef here): flex flex-col gap-2 min-h-[120px]
```

The column has a subtle left border accent (e.g. `border-l-2`) whose color varies by status:
- `todo`: `border-l-border`
- `in_progress`: `border-l-blue-400`
- `in_review`: `border-l-amber-400`
- `done`: `border-l-green-400`

---

## Step 5 — Implement `TasksKanbanView.tsx`

**File:** `client/components/management/tasks/TasksKanbanView.tsx`

This is the DnD root. It owns `DndContext`, distributes tasks to columns, manages `activeTask` state for `DragOverlay`, and handles all drag-end mutation logic.

### Props interface

```typescript
interface TasksKanbanViewProps {
  tasks: AgentGlobalTask[];
  onTaskEdit: (task: AgentGlobalTask) => void;
}
```

### Column definitions (constant, defined at module level)

```typescript
const COLUMNS: { status: GlobalTaskStatus; label: string }[] = [
  { status: 'todo',        label: 'To-Do' },
  { status: 'in_progress', label: 'In Progress' },
  { status: 'in_review',   label: 'In Review' },
  { status: 'done',        label: 'Done' },
];
```

### State

```typescript
const [activeTask, setActiveTask] = useState<AgentGlobalTask | null>(null);
const [optimisticTasks, setOptimisticTasks] = useState<AgentGlobalTask[]>(tasks);
```

Keep `optimisticTasks` in sync with the incoming `tasks` prop via `useEffect` (update when `tasks` reference changes). All rendering uses `optimisticTasks`.

### Mutation hooks

```typescript
const { mutate: updateTask } = useUpdateGlobalTask();
const { mutate: completeTask } = useCompleteGlobalTask();
```

### `handleDragEnd` logic

This is the most critical part of this section. The handler receives a `DragEndEvent` from dnd-kit.

```typescript
function handleDragEnd(event: DragEndEvent): void {
  // 1. Clear activeTask (hides DragOverlay)
  // 2. If no `over`, bail out
  // 3. Determine the target column status:
  //    - If `over.id` is a column status string (one of the COLUMNS statuses), that's the target
  //    - If `over.id` is a task ID, find which column that task belongs to
  // 4. Get the active task's current status
  // 5. If status changed (cross-column drop):
  //    a. Apply optimistic update: setOptimisticTasks(...) with new status for this task
  //    b. If newStatus === 'done':
  //         completeTask({ id: activeId }, {
  //           onError: () => { revertOptimisticUpdate(); toast.error("Failed to move task — change reverted"); }
  //         })
  //    c. Else if newStatus === 'in_review':
  //         updateTask({ id: activeId, status: 'in_review' }, {
  //           onSuccess: () => toast.success("Task sent for review"),
  //           onError: () => { revertOptimisticUpdate(); toast.error("Failed to move task — change reverted"); }
  //         })
  //    d. Else:
  //         updateTask({ id: activeId, status: newStatus }, {
  //           onError: () => { revertOptimisticUpdate(); toast.error("Failed to move task — change reverted"); }
  //         })
  // 6. If same column but different position (intra-column reorder):
  //    a. Calculate new order using arrayMove from @dnd-kit/sortable
  //    b. Apply optimistic reorder
  //    c. updateTask({ id: activeId, order: newOrder }, {
  //         onError: () => { revertOptimisticUpdate(); toast.error("Failed to move task — change reverted"); }
  //       })
}
```

The `revertOptimisticUpdate` function restores `optimisticTasks` to the snapshot taken before the drag began. Take the snapshot in `onDragStart`.

### JSX structure

```tsx
<DndContext
  collisionDetection={closestCenter}
  onDragStart={handleDragStart}
  onDragEnd={handleDragEnd}
>
  <div className="flex gap-4 overflow-x-auto pb-4">
    {COLUMNS.map(col => (
      <KanbanColumn
        key={col.status}
        status={col.status}
        label={col.label}
        tasks={optimisticTasks.filter(t => t.status === col.status)}
        onTaskEdit={onTaskEdit}
      />
    ))}
  </div>
  <DragOverlay>
    {activeTask ? <TaskCardOverlay task={activeTask} /> : null}
  </DragOverlay>
</DndContext>
```

---

## Step 6 — Verify Tests Pass

After implementing all four components, run:

```bash
cd client && npx vitest run
```

All tests written in Step 1 should now be **green**. If any are red:

- `TaskCard` tests failing: check that `useSortable` mock matches the structure your component destructures
- `KanbanColumn` tests failing: ensure `useDroppable` mock is set up and the empty-state `min-h-[120px]` div is rendered when `tasks.length === 0`
- `TasksKanbanView` tests failing: confirm `handleDragEnd` is testable in isolation (either exported separately or tested by calling it via the mocked `DndContext`'s `onDragEnd` prop)

---

## Important Edge Cases

**Empty columns must remain drop targets.** `KanbanColumn` always renders the `setNodeRef` container with `min-h-[120px]`, even when `tasks` is empty. A column with no tasks should still accept drops.

**`useCompleteGlobalTask` vs `useUpdateGlobalTask`.** Never call `useUpdateGlobalTask` with `status: 'done'` — always use `useCompleteGlobalTask` for the `done` transition. This is what triggers backend JIT next-instance creation for recurring tasks. Conversely, never call `useCompleteGlobalTask` for any other status transition.

**`in_review` notification.** No frontend notification API call is needed. The Django backend fires a signal on `in_review` status that routes through the `notification-realtime` service to the admin. The frontend only needs to call `useUpdateGlobalTask({ id, status: 'in_review' })` and show the `"Task sent for review"` toast on `onSuccess`.

**Optimistic revert snapshot.** Take the snapshot of `optimisticTasks` at `onDragStart`, not at `onDragEnd`. Store it in a `ref` (not state) to avoid re-renders.

**`listeners` on drag handle only.** Spreading `...listeners` on the card root would intercept click events on the whole card. Apply `...listeners` only to the `GripVertical` wrapper. The card root gets `onClick` for edit. The drag handle wrapper calls `e.stopPropagation()` on click.

**Do not modify `RecurringTaskManager.tsx`.** The existing component continues to serve other pages. `TasksKanbanView` uses `useCompleteGlobalTask` directly — no need to touch the scheduling manager.
