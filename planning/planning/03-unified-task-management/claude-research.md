# Research Findings: Unified Task Management UI

## Source
Codebase research only (web research skipped by user).

---

## 1. Existing Task Components

### Developer Dashboard Tasks Page
**`client/app/dashboard/agent/developer/tasks/page.tsx`**

Already has a dual-view Kanban/List system with:
- Task filtering by project and priority
- Multi-select with bulk status updates
- Status grouping: Pending, In Progress, Completed
- Task cards: title, description, priority badge, due date, subtask progress, blocked indicator
- Table view with inline actions

This is the primary source for Kanban/list toggle logic and card layout patterns.

### CrossClientTaskList
**`client/components/agent/scheduling/CrossClientTaskList.tsx`**

- Unified cross-client task display
- Filters: status, priority, category, client, date range
- Grouping: by client, category, or status
- Mobile-responsive row layout with collapsible date filter section
- Uses `@tanstack/react-query`

This is the closest existing component to the target unified list view.

### TaskCategoryBadge
**`client/components/agent/scheduling/TaskCategoryBadge.tsx`**

- Inline styles based on category `color` hex field
- `backgroundColor: ${color}20`, `border: 1px solid ${color}40`
- Sizes: `sm` and `md`
- Accepts both category objects and string names

Pattern to replicate for client color badges.

### RecurringTaskManager
**`client/components/agent/scheduling/RecurringTaskManager.tsx`**

- Modal-based create/edit for recurring tasks
- Frequency: daily, weekly, biweekly, monthly
- Interval configuration
- Day selection toggle buttons (Mon-Sun)
- End type: never, date, count
- Delete confirmation modal

The recurrence rule builder already exists here — extract and extend for `yearly` and `custom`.

---

## 2. Portal Shell & Navigation

### Management Portal Location
`client/app/dashboard/agent/marketing/management/` — this is the **Command Centre** portal with:
- `layout.tsx` — `ManagementSidebar` + scrollable content area + breadcrumbs
- `page.tsx` — overview grid with nav cards
- Subdirectories: `tasks/`, `calendar/`, `clients/`, `notes/`

The new unified tasks page goes at `client/app/dashboard/agent/marketing/management/tasks/page.tsx`.

### ManagementSidebar
**`client/components/dashboard/ManagementSidebar.tsx`**

- Collapsible sidebar (localStorage persisted)
- Mobile drawer with hamburger + Escape to close, Tab focus cycling
- Navigation items: Overview, Tasks, Calendar, Clients, Notes
- Active state: left border + light blue background (`.nav-item-active`)

---

## 3. API Hooks

### Core Scheduling Hooks (`client/lib/hooks/useScheduling.ts`)

```typescript
useGlobalTasks(filters?: GlobalTaskFilters)
useCreateGlobalTask()
useUpdateGlobalTask()
useDeleteGlobalTask()
useCompleteGlobalTask()
useTaskCategories(department?: string)
useCreateTaskCategory()
useCrossClientTasks(filters?: CrossClientTaskFilters)
```

Query keys follow `SCHEDULE_KEYS.globalTasks.list(filters)` pattern with 30s staleTime. Mutations auto-invalidate the relevant query family.

### API Endpoints (`client/lib/api/scheduling.ts`)

```
GET  /agent/schedule/global-tasks/        — list with GlobalTaskFilters
POST /agent/schedule/global-tasks/        — create
PATCH /agent/schedule/global-tasks/{id}/  — update (status, fields)
POST /agent/schedule/global-tasks/{id}/complete/ — mark done
GET  /agent/schedule/task-categories/     — list categories
```

---

## 4. Type Definitions (`client/lib/types/scheduling.ts`)

### AgentGlobalTask (full shape)

```typescript
interface AgentGlobalTask {
  id: string;
  agent: string;
  title: string;
  description: string;
  status: GlobalTaskStatus;           // 'todo' | 'in_progress' | 'in_review' | 'done'
  priority: TaskPriority;             // 'low' | 'medium' | 'high'
  client: string | null;
  client_name: string;
  task_category_ref: string | null;
  task_category_detail: TaskCategoryItem | null;
  due_date: string | null;
  scheduled_date: string | null;
  is_recurring: boolean;
  recurrence_frequency: RecurrenceFrequency | null;  // 'daily'|'weekly'|'biweekly'|'monthly'|'yearly'|'custom'
  recurrence_days: number[] | null;
  recurrence_interval: number;
  recurrence_end_type: RecurrenceEndType;            // 'never'|'date'|'count'
  recurrence_end_date: string | null;
  recurrence_end_count: number | null;
  recurrence_parent: string | null;
  is_overdue: boolean;
  created_at: string;
  updated_at: string;
}
```

### TaskCategoryItem

```typescript
interface TaskCategoryItem {
  id: string;
  name: string;
  slug: string;
  color: string;   // Hex — used for dynamic badge styling
  icon: string;
  department: 'marketing' | 'website' | 'both';
  requires_review: boolean;
  is_active: boolean;
  sort_order: number;
}
```

`GlobalTaskStatus` already includes `'in_review'`.

---

## 5. Design Tokens & Styling

### CSS Custom Properties (`client/app/globals.css`)

```css
--color-accent: #2563EB
--color-surface: #FFFFFF
--color-surface-subtle: #FAFAFA
--color-border: #E4E4E7
--color-text: #18181B
--color-text-secondary: #52525B
```

Dynamic badge colors use inline styles: `backgroundColor: ${hex}20`, `color: hex`, `border: 1px solid ${hex}40`.

### Key Reusable UI Components

| Component | Path |
|-----------|------|
| `Surface` | `client/components/ui/Surface.tsx` |
| `Badge` / `StatusBadge` | `client/components/ui/badge.tsx` |
| `SectionHeader` | `client/components/ui/SectionHeader.tsx` |
| `Modal` + sub-components | `client/components/ui/modal.tsx` |
| `Button` | `client/components/ui/button.tsx` |
| `EmptyState` | `client/components/ui/empty-state.tsx` |

---

## 6. Drag-and-Drop (@dnd-kit)

Primary reference: `client/components/agent/scheduling/DaySchedule.tsx`

Pattern:
```typescript
import { DndContext, closestCenter, DragOverlay } from '@dnd-kit/core';
import { useDraggable, useDroppable } from '@dnd-kit/core';
import { CSS } from '@dnd-kit/utilities';

// Draggable card
const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
  id: task.id,
  data: { type: 'task', task, sourceColumn },
});

// Droppable column
const { setNodeRef, isOver } = useDroppable({ id: `column-${status}` });

// Root
<DndContext collisionDetection={closestCenter} onDragStart={...} onDragEnd={...}>
  <DragOverlay>{activeTask && <TaskCardOverlay task={activeTask} />}</DragOverlay>
</DndContext>
```

Use `useDraggable` + `useDroppable` directly (not `SortableContext`) for column-to-column Kanban drag.

---

## 7. Testing Setup

- **Runner:** Vitest + `@testing-library/react`
- **Environment:** jsdom
- **Config:** `client/vitest.config.ts`, setup: `client/vitest.setup.ts`

Mock pattern:
```typescript
vi.mock('@/lib/hooks/useScheduling', () => ({
  useGlobalTasks: vi.fn(() => ({ data: [], isLoading: false })),
  useUpdateGlobalTask: vi.fn(() => ({ mutate: vi.fn() })),
  useTaskCategories: vi.fn(() => ({ data: [] })),
}))
vi.mock('next/navigation', () => ({ useRouter: () => ({ push: vi.fn() }), usePathname: () => '/' }))
```

---

## Key Takeaways

1. **All types ready** — `GlobalTaskStatus` has `in_review`; `AgentGlobalTask` has all recurrence fields.
2. **All hooks exist** — `useGlobalTasks`, `useUpdateGlobalTask`, `useTaskCategories` in `useScheduling.ts`.
3. **DnD pattern established** — follow `DaySchedule.tsx`; `useDraggable`/`useDroppable` for column drag.
4. **Recurrence UI exists** — extract from `RecurringTaskManager`; add `yearly`/`custom`.
5. **Badge color pattern** — `backgroundColor: ${hex}20` / `color: hex` (same for clients and categories).
6. **Portal route** — `client/app/dashboard/agent/marketing/management/tasks/page.tsx`.
7. **View toggle** — localStorage key `command-centre-task-view`.
8. **Testing** — Vitest + RTL, mock hooks via `vi.mock`.
