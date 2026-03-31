# Unified Task Management UI — Combined Specification

## Overview

Replace the existing separate Kanban/List task pages with a single unified Tasks page at `/management/tasks/` inside the Command Centre portal. The page provides a seamless Kanban ↔ List toggle, client tagging with color-coded badges, dynamic category picker, recurrence rule builder, and a 4-column approval workflow (To-Do → In Progress → In Review → Done) with notification triggers on `in_review` transition.

---

## Dependencies

- **Split 01 (Backend Restructuring):** `AgentGlobalTask` type with `client`, `task_category_ref`, recurrence fields, and `in_review` status must be available. Backend handles JIT next-instance creation on task completion.
- **Split 02 (Portal Navigation):** Command Centre portal shell at `client/app/dashboard/agent/marketing/management/` with `ManagementSidebar` already routing to `/tasks/`.

---

## Route & File Location

```
client/app/dashboard/agent/marketing/management/tasks/page.tsx
```

The Management portal `layout.tsx` and `ManagementSidebar` already handle the shell, breadcrumbs, and navigation. The tasks page renders inside the content area.

---

## Core Features

### 1. View Toggle (Kanban / List)

- Segmented control in the page header top-right
- Icons: `LayoutList` (list) and `Columns3` (kanban) from Lucide
- Active segment: `bg-accent text-white`; inactive: `bg-surface text-secondary`
- State persisted in `localStorage` key `command-centre-task-view`
- Switching views preserves all active filters

### 2. Filter Bar

Rendered below the page header, above the view content:

```
[All Clients ▾] [All Categories ▾] [All Statuses ▾] [All Priorities ▾] [Search...]
```

- **Client filter:** Multi-select dropdown from clients API. Renders selected clients as color-coded chips. "All Clients" default.
- **Category filter:** Multi-select from `useTaskCategories()`.
- **Status filter:** Single-select (All / To-Do / In Progress / In Review / Done).
- **Priority filter:** Single-select (All / High / Medium / Low).
- **Search:** Debounced text search on task title.
- **Persistence:** All filter state reflected in URL query params (via `useRouter` / `useSearchParams`). Page is shareable and survives refresh.

### 3. Kanban View

Four columns corresponding to `GlobalTaskStatus`:

| Column | Status value | Notes |
|--------|-------------|-------|
| To-Do | `todo` | Default for new tasks |
| In Progress | `in_progress` | Active work |
| In Review | `in_review` | Triggers admin notification on drop |
| Done | `done` | Backend creates next instance if recurring |

**Drag-and-drop:**
- Library: `@dnd-kit/core` + `@dnd-kit/sortable` (existing in codebase)
- Cards are sortable **within** a column (reorder by `order` field) and **between** columns (status change)
- Implementation: `SortableContext` per column with `verticalListSortingStrategy`, wrapped in a root `DndContext`
- `DragOverlay` renders a ghost card during drag
- Cross-column detection: check `overId` against column droppable IDs in `onDragEnd`
- Status change: `useUpdateGlobalTask()` PATCH after drop, with optimistic UI update
- `in_review` transition: notification triggered only **after** API success (not optimistically)
- `done` transition: backend auto-creates next recurring instance; frontend invalidates `globalTasks` query

**Card layout:**
```
┌─────────────────────────────────┐
│ ⠿  [Client Badge] [Cat Badge]   │
│ Task title (truncated, 2 lines) │
│ ● Priority  📅 Due date         │
│ 🔄 (if recurring)               │
└─────────────────────────────────┘
```
- `bg-surface rounded-lg border border-border shadow-sm p-3`
- Hover: `translateY(-4px)` transition (`hover-lift` or equivalent)
- Drag state: `shadow-lg opacity-90`
- Priority dot: red (high), amber (medium), blue (low)
- Due date: red text if `is_overdue`
- Drag handle: grip icon (`GripVertical`) in top-left

### 4. List View

Sortable table:

| # | Title | Client | Category | Status | Priority | Due Date | Scheduled | Actions |
|---|-------|--------|----------|--------|----------|----------|-----------|---------|

- **Sortable columns:** Click header to sort asc/desc (local sort on fetched data)
- **Row click:** Opens task edit modal
- **Inline status dropdown:** Per-row status select (calls `useUpdateGlobalTask`)
- **Bulk selection:** Checkbox column (select all + per-row). Bulk toolbar appears when ≥1 selected: bulk status change, bulk delete
- **Mobile:** Collapses to card view (similar to `CrossClientTaskList` mobile layout)

### 5. Client Tagging

- Client selector is a **controlled vocabulary** dropdown linked to the clients API (`/api/clients/` or equivalent — discover hook during implementation)
- No free-text entry for clients
- Client badge color: **deterministic palette assignment** — hash `client.id` (string) to an index in a fixed 12-color palette. Same client always gets same color across sessions.
- Badge style: `rounded-full px-2 py-0.5 text-xs font-medium`, `backgroundColor: ${color}20`, `color: color`, `border: 1px solid ${color}40`

**Color palette (12 colors):**
```typescript
const CLIENT_PALETTE = [
  '#2563EB', '#7C3AED', '#DB2777', '#DC2626',
  '#EA580C', '#CA8A04', '#16A34A', '#0891B2',
  '#4F46E5', '#9333EA', '#E11D48', '#0D9488',
];
```

### 6. Task Creation / Edit Modal

Modal sections:

**1. Basic Info**
- Title (required, text input)
- Description (rich text editor — locate existing editor in codebase)
- Priority selector (Low / Medium / High toggle buttons)

**2. Assignment**
- Client selector (controlled vocabulary dropdown)
- Category selector (from `useTaskCategories()`, renders category badge preview)

**3. Scheduling**
- Date picker (single date, or range if multi-day task)
- Optional time range: start time + end time

**4. Recurrence** (toggle to reveal — based on `RecurringTaskManager` pattern)
- Frequency: Daily | Weekly | Biweekly | Monthly | Yearly | Custom
- For Weekly/Custom: day-of-week checkboxes Mon–Sun
- Interval: "Every N [days/weeks/months/years]"
- End condition: Never | After N occurrences | On date (date picker)

**5. Actions**
- Save (PATCH or POST)
- Save & Schedule (POST + navigate to calendar — Split 04 integration point, stub for now)
- Cancel

### 7. Approval Workflow Notification

Flow when task moves to `in_review`:
1. `onDragEnd` or inline status change triggers `useUpdateGlobalTask().mutate({ id, status: 'in_review' })`
2. On mutation `onSuccess`: backend has already triggered the notification via `notification-realtime` service
3. Frontend does **not** call a separate notification endpoint — the Django signal/handler on status change handles it
4. Frontend invalidates query to refresh task list

---

## Existing Code to Reuse / Refactor

| Existing File | What to Reuse |
|--------------|---------------|
| `client/app/dashboard/agent/developer/tasks/page.tsx` | View toggle pattern, Kanban layout structure, card component |
| `client/components/agent/scheduling/CrossClientTaskList.tsx` | List view table columns, filter logic, mobile card layout |
| `client/components/agent/scheduling/TaskCategoryBadge.tsx` | Badge color pattern (replicate for client badges) |
| `client/components/agent/scheduling/RecurringTaskManager.tsx` | Recurrence rule builder UI — extract into modal section |
| `client/components/agent/scheduling/DaySchedule.tsx` | @dnd-kit drag pattern reference |
| `client/components/ui/modal.tsx` | Modal shell for create/edit |
| `client/components/ui/SectionHeader.tsx` | Page header with icon + action |
| `client/components/ui/badge.tsx` | Status badges |

---

## API Contracts

### Hooks Used
```typescript
useGlobalTasks(filters: GlobalTaskFilters)  // GET /agent/schedule/global-tasks/
useCreateGlobalTask()                        // POST /agent/schedule/global-tasks/
useUpdateGlobalTask()                        // PATCH /agent/schedule/global-tasks/{id}/
useDeleteGlobalTask()                        // DELETE /agent/schedule/global-tasks/{id}/
useCompleteGlobalTask()                      // POST /agent/schedule/global-tasks/{id}/complete/
useTaskCategories(department?: string)       // GET /agent/schedule/task-categories/
// useClients() — find or build during implementation
```

### Filter Shape
```typescript
interface GlobalTaskFilters {
  status?: GlobalTaskStatus;
  priority?: TaskPriority;
  client?: string;           // client ID
  category_id?: string;
  search?: string;
  page?: number;
}
```

---

## URL Query Param Schema

```
/management/tasks/?view=kanban&client=abc123&category=cat456&status=in_progress&priority=high&q=search+term
```

- `view`: `kanban` | `list` (also in localStorage)
- `client`: comma-separated client IDs for multi-select
- `category`: comma-separated category IDs
- `status`: single status value
- `priority`: single priority value
- `q`: search string

---

## Design Specs (Summary)

- **View toggle:** `rounded-lg border border-border` segmented control; active `bg-accent text-white`
- **Kanban card:** `bg-surface rounded-lg border border-border shadow-sm p-3`; hover lift
- **Column header:** `text-label font-medium uppercase tracking-wider`
- **Filter bar:** `flex gap-2 items-center p-3 bg-surface-subtle rounded-lg border border-border-subtle`
- **Client/category badges:** `rounded-full px-2 py-0.5 text-xs font-medium` with dynamic hex colors
- **Priority dots:** `w-2 h-2 rounded-full` — `bg-red-500` (high), `bg-amber-500` (medium), `bg-blue-500` (low)

---

## Out of Scope

- Calendar drag scheduling (Split 04)
- Admin approval queue UI (Split 06)
- Client CRM detail page (Split 06)
- Dashboard KPIs (Split 05)

---

## Acceptance Criteria

1. Single Tasks page at `/management/tasks/` with Kanban ↔ List toggle
2. Switching views preserves all active filters
3. Kanban has 4 columns: To-Do, In Progress, In Review, Done
4. Drag-and-drop between Kanban columns updates task status via API
5. Cards sortable within a column (order field updated)
6. Moving to "In Review" triggers admin notification after API success
7. List view: sortable table with all task metadata, inline status change
8. Bulk selection in list view (bulk status change, bulk delete)
9. Filter bar: client, category, status, priority, search — all persisted in URL
10. Client filter uses controlled vocabulary (no free-text)
11. Color-coded client badges (deterministic palette) and category badges throughout
12. Task creation/edit modal: all fields including client selector, category, date, recurrence
13. Recurrence rule builder: daily/weekly/biweekly/monthly/yearly/custom with day-of-week and end conditions
14. Completing a recurring task triggers next-instance creation (server-side, frontend just invalidates query)
15. View preference persists in localStorage
16. Responsive: Kanban scrolls horizontally on mobile, List collapses to card view
