# Implementation Plan: Unified Task Management UI (Split 03)

## Context

The Montrroase platform has a Command Centre portal for agents (located at `client/app/dashboard/agent/marketing/management/`). Currently, task management is scattered across a developer dashboard Kanban page and a separate cross-client scheduling list. This split (Split 03) unifies them into a single Tasks page with full Kanban and List views, client tagging, a category picker, a recurrence rule builder, and an approval workflow with notification triggers.

The portal shell, sidebar, breadcrumbs, and routing already exist from Split 02. This plan focuses entirely on what goes inside `management/tasks/`.

---

## What We're Building

A single page at `/management/tasks/` that:
- Lets agents switch seamlessly between a drag-and-drop Kanban board and a sortable List table
- Filters tasks by client (color-coded, controlled vocabulary), category, status, priority, and search
- Persists all filter state in URL query params (shareable, refresh-safe) and persists view preference in localStorage
- Provides a full-featured create/edit modal with recurrence rule builder
- Enforces a 4-column approval workflow: To-Do → In Progress → In Review → Done
- Triggers an admin notification (via the existing notification-realtime backend service) when a task is moved to "In Review" — only after the API call succeeds
- Supports bulk operations (bulk status change, bulk delete) in the List view

All backend logic — JIT next-instance creation for recurring tasks on completion, notification dispatch on `in_review` transition — is handled server-side. The frontend's job is to make API calls and invalidate queries.

---

## File Structure

```
client/app/dashboard/agent/marketing/management/tasks/
  page.tsx                     # Main Tasks page — entry point, composes all sub-components
  __tests__/
    page.test.tsx              # Integration tests for the page
    TaskCard.test.tsx
    TaskModal.test.tsx
    useTaskFilters.test.ts

client/components/management/tasks/
  TasksKanbanView.tsx          # Kanban board with DnD context and 4 columns
  TasksListView.tsx            # Sortable table list view
  TaskCard.tsx                 # Kanban card component
  TaskCardOverlay.tsx          # DragOverlay ghost card
  KanbanColumn.tsx             # Single column (droppable + sortable context)
  TaskModal.tsx                # Create/edit modal (all sections)
  RecurrenceBuilder.tsx        # Recurrence rule builder (extracted from RecurringTaskManager)
  TaskFilterBar.tsx            # Filter dropdowns + search
  ViewToggle.tsx               # Kanban/List segmented control
  ClientBadge.tsx              # Color-coded client chip
  BulkActionBar.tsx            # Bulk status/delete toolbar (appears when rows selected)
  clientPalette.ts             # Deterministic color assignment logic
```

The existing `client/components/agent/scheduling/` components are reference code — we do not modify them in this split (they may still be used on other pages). We extract patterns from them into the new `client/components/management/tasks/` directory.

---

## Data Layer

### Types

All necessary types already exist in `client/lib/types/scheduling.ts`:
- `AgentGlobalTask` — full task shape including all recurrence fields and `client`/`client_name`
- `GlobalTaskStatus` (`'todo' | 'in_progress' | 'in_review' | 'done'`) — `in_review` is already present
- `TaskCategoryItem` — includes `color` hex field for badge styling
- `RecurrenceFrequency` — verify it includes `'yearly'` and `'custom'`; add them if missing
- `RecurrenceEndType` (`'never' | 'date' | 'count'`)

No type additions should be needed for this split beyond verifying `RecurrenceFrequency` completeness.

### Hooks

All task and category hooks exist in `client/lib/hooks/useScheduling.ts`:
- `useGlobalTasks(filters)` — fetches with 30s staleTime, cached by filter shape
- `useCreateGlobalTask()` — invalidates task list on success
- `useUpdateGlobalTask()` — used for status changes (including drag-and-drop) and field edits
- `useDeleteGlobalTask()` — invalidates task list on success
- `useCompleteGlobalTask()` — marks done; backend creates next recurring instance server-side
- `useTaskCategories(department?)` — returns `TaskCategoryItem[]`

**Clients hook:** During implementation, search `client/lib/hooks/` for any existing clients hook. If none exists, create `useClients()` in `client/lib/hooks/useClients.ts` that fetches `GET /api/clients/` and returns `Client[]` (with at least `id` and `name` fields). This is needed for the client filter bar and modal selector.

### Filter State

Filters live in URL query params, managed via Next.js `useSearchParams` and `useRouter`. The filter bar reads from URL on mount and updates the URL on every change. This means:
- The page is shareable and survives browser refresh
- Navigating away and back restores filters
- The `useGlobalTasks(filters)` hook receives the parsed filter object derived from the URL params

**URL param schema:**
- `view`: `kanban` | `list`
- `clients`: comma-separated client IDs (multi-select)
- `categories`: comma-separated category IDs (multi-select)
- `status`: single `GlobalTaskStatus` value
- `priority`: `low` | `medium` | `high`
- `q`: debounced search string

**View toggle also writes to `localStorage`** (`command-centre-task-view`) as a fallback default for new sessions (URL param takes precedence).

A custom hook `useTaskFilters()` should encapsulate parsing URL params → filter object, and exposing update functions that call `router.push` with updated params. This makes the page component clean and keeps filter logic testable in isolation.

---

## View Toggle

`ViewToggle.tsx` is a small segmented control (two-button group):
- `LayoutList` icon for list; `Columns3` icon for kanban (both from Lucide)
- Active button: `bg-accent text-white rounded-md`; inactive: `bg-surface text-secondary`
- Container: `rounded-lg border border-border flex`
- On click: updates `view` URL param and `localStorage`

---

## Kanban View

### Structure

`TasksKanbanView.tsx` owns the `DndContext` and renders four `KanbanColumn` components side by side. On mobile, the column container scrolls horizontally with `overflow-x-auto`.

The four columns map directly to `GlobalTaskStatus` values: `todo`, `in_progress`, `in_review`, `done`. Their display labels are "To-Do", "In Progress", "In Review", "Done".

### Drag-and-Drop Architecture

The existing codebase uses `@dnd-kit/core` (see `DaySchedule.tsx` and `DndProvider.tsx`). For Kanban with both intra-column reordering and cross-column moving, the standard approach is:

- **Root `DndContext`** with `closestCenter` collision detection, wrapping all four columns
- **Each `KanbanColumn`** wraps its task list in a `SortableContext` with `verticalListSortingStrategy`
- **Each `TaskCard`** uses `useSortable` (from `@dnd-kit/sortable`), which provides both drag handle and sortable positioning
- **`DragOverlay`** renders `TaskCardOverlay` (a styled ghost copy of the dragged card) during the drag operation

The root `DndContext` maintains `activeTask` state (set in `onDragStart`, cleared in `onDragEnd`). The `DragOverlay` displays while `activeTask` is non-null.

**`onDragEnd` logic:**
1. Determine the `over` container — is it a column ID or a task ID within a column?
2. If the task moved to a different column:
   - For `in_review`: call `useUpdateGlobalTask().mutate({ id, status: 'in_review' })`; on `onSuccess`, show toast "Task sent for review"; on `onError`, show toast "Failed to update task status"
   - For `done`: call `useCompleteGlobalTask().mutate({ id })`; on `onSuccess`, invalidate task list (the backend has already created the next recurring instance server-side); for non-recurring tasks moved to `done` via drag, `useCompleteGlobalTask` is still correct — it handles both cases
   - For other columns (`todo`, `in_progress`): call `useUpdateGlobalTask().mutate({ id, status: newColumnStatus })`
3. If the task stayed in the same column but changed position: call `useUpdateGlobalTask().mutate({ id, order: newOrder })`
4. Apply optimistic local state reordering immediately on drop, reverting on mutation error; on revert, show toast "Failed to move task — change reverted"

**useCompleteGlobalTask vs useUpdateGlobalTask:** Use `useCompleteGlobalTask()` exclusively when transitioning a task to `done` (this is what triggers backend JIT next-instance creation for recurring tasks). Use `useUpdateGlobalTask()` for all other status transitions (todo → in_progress, etc.) and for all field edits. The modal Save button always uses `useUpdateGlobalTask()` for edits.

**Why `useSortable` instead of `useDraggable` + `useDroppable`:** The existing `DaySchedule.tsx` uses raw `useDraggable`/`useDroppable` for a time-slot calendar which doesn't need intra-list reordering. Since we need both intra-column sort and cross-column move, `useSortable` + `SortableContext` per column is the correct @dnd-kit pattern. The `DragOverlay` approach is identical.

### TaskCard

Each card displays:
- Drag handle (`GripVertical` icon, top-left, with `cursor-grab`)
- Client badge (color from palette — see Client Color System section)
- Category badge (color from `TaskCategoryItem.color`)
- Task title (2-line clamp, `line-clamp-2`)
- Priority dot (`w-2 h-2 rounded-full` — red/amber/blue for high/medium/low)
- Due date with `CalendarDays` icon — `text-status-error` if `is_overdue`
- Recurrence icon (`RefreshCw` from Lucide) if `is_recurring`

Card style: `bg-surface rounded-lg border border-border shadow-sm p-3 cursor-pointer`
Hover: `transition-transform duration-150 hover:-translate-y-1`
Dragging: `shadow-lg opacity-90`

Card click (not on drag handle) → opens `TaskModal` in edit mode.

### Column Header

`KanbanColumn` renders a header with:
- Column label in `text-xs font-medium uppercase tracking-wider text-secondary`
- Task count badge (e.g. `(4)`)
- A subtle colored left border or top bar to visually distinguish columns (optional, up to implementer)

---

## List View

### Structure

`TasksListView.tsx` renders a table with the columns defined in the spec. The table is built with standard HTML `<table>` elements styled with Tailwind, following the existing `CrossClientTaskList.tsx` pattern.

### Sortable Columns

Clicking a column header toggles asc/desc sort. Sort state is local (not in URL) — it applies client-side on the fetched data array. A `SortState` (column + direction) lives in `useState` within `TasksListView`. The `useSortedTasks(tasks, sortState)` helper function returns a sorted copy.

### Bulk Selection

- A checkbox column is the first column. Checking the header checkbox selects all visible rows.
- `selectedIds: Set<string>` lives in `useState` in `TasksListView`
- When `selectedIds.size > 0`, `BulkActionBar.tsx` appears (fixed bottom bar or above the table) with:
  - "N tasks selected"
  - "Change status" dropdown → if the backend exposes a bulk update endpoint (e.g. `PATCH /agent/schedule/global-tasks/bulk/`), use it; otherwise call `useUpdateGlobalTask()` for each selected ID and track partial failures
  - "Delete" button → if the backend exposes a bulk delete endpoint, use it; otherwise call `useDeleteGlobalTask()` for each selected ID with confirmation dialog

**Bulk operation error handling:** When operating per-item, each mutation runs independently. If any fail, show individual error toasts and keep the failed items in the selection (so the user can retry). Successfully updated items are deselected. A future backend bulk endpoint is the preferred path — add a `// TODO: replace with bulk endpoint` comment in the implementation.

### Inline Status Change

Each row has a `<select>` (or styled dropdown) for status. On change, calls `useUpdateGlobalTask().mutate({ id, status })` immediately — no modal needed.

### Mobile Card View

On screens `< sm breakpoint`, the table is hidden and tasks render as stacked cards (similar to `CrossClientTaskList`'s mobile layout): title, client badge, category badge, status badge, due date in a vertical layout per task.

---

## Task Creation / Edit Modal

`TaskModal.tsx` is a multi-section modal using the existing `Modal`/`ModalHeader`/`ModalContent`/`ModalFooter` components from `client/components/ui/modal.tsx`.

### Props

```typescript
interface TaskModalProps {
  isOpen: boolean;
  onClose: () => void;
  task?: AgentGlobalTask;   // undefined → create mode; defined → edit mode
}
```

### Form State

All fields in a single `formState` object managed by `useState`. A generic setter `setField(key, value)` updates individual fields. The form state contains **only user-editable fields** — explicitly:

```
title, description, priority, client_id, category_id, due_date, scheduled_date,
start_time, end_time, is_recurring, recurrence_frequency, recurrence_interval,
recurrence_days_of_week, recurrence_end_type, recurrence_end_date, recurrence_end_count
```

The API payload passed to `useCreateGlobalTask()` / `useUpdateGlobalTask()` is constructed from these fields only — never spread from a full task object (which would include read-only system fields like `id`, `created_at`, `owner_id`, `is_overdue`).

### Sections

**Basic Info:**
- Title: text input (required)
- Description: rich text editor — locate the existing editor component in the codebase during implementation (search for TipTap, Quill, Slate, or similar); use it here. If no editor is found, fall back to `<textarea>`.
- Priority: three-button toggle group (Low / Medium / High) with colored indicators

**Assignment:**
- Client: `<select>` populated from `useClients()` results (controlled vocabulary — no free text). Shows client name. Stores `client.id`.
- Category: `<select>` populated from `useTaskCategories()`. Renders a preview of the category badge next to each option.

**Scheduling:**
- Due date: `<input type="date">`
- Scheduled date: `<input type="date">` (optional)
- Time range: optional start/end `<input type="time">` fields, revealed by a "Add time" toggle

**Recurrence (toggle section):**
Controlled by `is_recurring` boolean toggle. When toggled on, `RecurrenceBuilder.tsx` appears.

**Actions:**
- Cancel → `onClose()`
- Save → `useCreateGlobalTask()` (create) or `useUpdateGlobalTask()` (edit) → on success, `onClose()` + query invalidation
- Save & Schedule → same as Save, then navigate to calendar (Split 04 stub — for now, just show a toast "Calendar coming soon")

### RecurrenceBuilder

Extracted from `RecurringTaskManager.tsx` and extended. A standalone component that receives recurrence field values as props and emits changes via callbacks. Fields:
- Frequency selector (Daily / Weekly / Biweekly / Monthly / Yearly / Custom)
- Day-of-week checkboxes (Mon–Sun) — shown for Weekly and Custom frequencies
- Interval: "Every [N] [unit]" (number input + unit label derived from frequency)
- End condition: radio group (Never / After N occurrences / On date)
  - "After N": number input
  - "On date": `<input type="date">`

The existing `RecurringTaskManager` already has most of this UI — we extract the relevant logic into the new `RecurrenceBuilder` component and add `yearly` and `custom` frequency options. `RecurringTaskManager.tsx` itself is **not modified or deprecated** in this split; it continues to serve its current usage on other pages. `RecurrenceBuilder` is an independent new component in `components/management/tasks/`.

---

## Client Color System

`clientPalette.ts` exports two things:

1. `CLIENT_PALETTE`: a fixed array of 12 distinct hex color strings
2. `getClientColor(clientId: string): string`: deterministically maps a client ID to a palette color by hashing the ID string to a palette index (e.g., sum of char codes modulo palette length). Same client ID always returns the same color.

`ClientBadge.tsx` accepts `clientId` and `clientName`, calls `getClientColor(clientId)`, and applies the badge style: `backgroundColor: ${color}20`, `color`, `border: 1px solid ${color}40`, `rounded-full px-2 py-0.5 text-xs font-medium`.

`getClientColor` guards against null/undefined `clientId` — it returns `#9CA3AF` (neutral gray) for missing values. `ClientBadge` renders "Unassigned" as the label text when `clientId` is absent.

This is the same color pattern already used by `TaskCategoryBadge` for category colors — just with a palette-derived color instead of a stored hex value.

---

## Filter Bar

`TaskFilterBar.tsx` renders a horizontal flex row of filter controls. It reads current filter values from the URL (via `useTaskFilters()`) and dispatches updates to the URL on change.

Dropdowns for client, category, status, priority each render a `<select>` or custom dropdown. Client and category support multi-select (comma-separated IDs in URL). Status and priority are single-select.

Search input: `<input type="text">` with `useDebounce` (300ms) before updating the `q` URL param.

Selected client chips appear as `ClientBadge` components in the filter bar, with an ×  button to remove them.

Style: `flex flex-wrap gap-2 items-center p-3 bg-surface-subtle rounded-lg border border-border-subtle`

---

## Notification Flow (In Review)

When a task is dragged to the In Review column, or its status is changed to `in_review` via inline dropdown or modal:

1. `useUpdateGlobalTask().mutate({ id, status: 'in_review' })`
2. On `onSuccess` callback: the Django backend has already fired a signal that dispatches a notification through `notification-realtime` to the admin; invalidate `globalTasks` query. No separate notification API call needed.
3. On `onSuccess`: show toast "Task sent for review" to confirm to the agent
4. On `onError`: show toast "Failed to update task status" — do NOT show the success toast

This "after API success, no separate endpoint" approach was confirmed in the interview. The notification service integration is entirely backend-managed.

---

## Page Composition

`management/tasks/page.tsx` is the top-level page component. It:
1. Reads view preference from URL params (falling back to localStorage)
2. Renders `SectionHeader` with title "Tasks" and `ViewToggle` in the action slot
3. Renders `TaskFilterBar`
4. Conditionally renders `TasksKanbanView` or `TasksListView` based on current view
5. Renders a "+ New Task" `Button` (bottom-right or in the header action area) that opens `TaskModal` in create mode
6. `TaskModal` is rendered at the page level (not inside Kanban/List) to avoid z-index issues

Shared state between Kanban and List (filters, task data) flows from the page: both views receive the same `tasks: AgentGlobalTask[]` prop (fetched once by `useGlobalTasks(filters)` at the page level). Switching views does not re-fetch.

---

## Testing Strategy

All tests use Vitest + `@testing-library/react` following the existing pattern in `client/app/dashboard/agent/marketing/management/pages.test.tsx`.

**Mock pattern:**
- `vi.mock('@/lib/hooks/useScheduling', ...)` — return controlled task/category data
- `vi.mock('@/lib/hooks/useClients', ...)` — return controlled client data
- `vi.mock('next/navigation', ...)` — mock `useRouter`, `useSearchParams`, `usePathname`

**Key test cases for each section:**

`page.test.tsx` (integration):
- Renders page heading "Tasks"
- View toggle switches between Kanban and List
- Filter bar dropdowns call useGlobalTasks with updated filters
- "+ New Task" button opens modal
- Switching views preserves filter state

`TaskCard.test.tsx`:
- Renders title, client badge, category badge, priority dot, due date
- Applies overdue styling when `is_overdue`
- Shows recurrence icon when `is_recurring`
- Click triggers onEdit callback

`TaskModal.test.tsx`:
- Renders all sections in create mode
- Renders populated fields in edit mode
- Recurrence builder hidden by default, shown when toggle enabled
- Save calls useCreateGlobalTask with correct payload
- Cancel calls onClose

`useTaskFilters.test.ts`:
- Parses URL params into filter object correctly
- Updates URL params on filter change
- Multi-select clients/categories correctly comma-joined

---

## Implementation Order

Build in this sequence to keep the page functional at each step:

1. `clientPalette.ts` + `ClientBadge.tsx` — standalone, no dependencies
2. `ViewToggle.tsx` — standalone
3. `useTaskFilters.ts` — URL param logic
4. `TaskFilterBar.tsx` — uses useTaskFilters + useClients + useTaskCategories
5. `TaskCard.tsx` + `TaskCardOverlay.tsx` — display only, no DnD yet
6. `KanbanColumn.tsx` + `TasksKanbanView.tsx` — add DnD last within this step
7. `TasksListView.tsx` + `BulkActionBar.tsx`
8. `RecurrenceBuilder.tsx` (extracted from RecurringTaskManager)
9. `TaskModal.tsx`
10. `page.tsx` — compose everything
11. Tests for each component

---

## Edge Cases & Decisions

**Empty columns:** Each Kanban column must remain a valid drop target even with zero tasks. `KanbanColumn` should render a minimum height droppable area with an empty state message ("No tasks here").

**Optimistic updates:** For drag-and-drop, apply the status/order change to local state immediately (so the card visually moves before the API responds), then revert on error. For modal saves, don't apply optimistically — wait for API success.

**`useClients` discovery:** During implementation, check `client/lib/hooks/` and `client/lib/api/` for any existing clients fetching logic. If a `useClients` hook exists, use it. If only an API function exists, wrap it in a React Query `useQuery`. If nothing exists, create a minimal hook that calls `GET /api/clients/` and returns an array.

**Rich text editor:** During implementation, search the codebase for TipTap, Quill, Slate, or similar. Use whatever is already installed. If no editor is found, use a `<textarea>` as fallback and file a note for future enhancement.

**`Save & Schedule`:** The calendar integration is Split 04. For this split, the "Save & Schedule" button saves the task and shows a toast "Calendar scheduling coming soon". The button should still be present in the UI so the modal layout matches the final design.

**Filter bar multi-select client:** If `GlobalTaskFilters` supports a `clients` array, pass it directly to `useGlobalTasks(filters)`. If the API only accepts a single `client` ID, **limit the filter to single-client selection for this split** — the UI still renders chips for any selected client but the hook receives only the most recently selected client ID (with a `// TODO: backend multi-client filtering not yet supported` comment). Do not fetch all tasks and filter client-side — that pattern is explicitly prohibited for scalability reasons. Multi-client server-side filtering is a backend task for a future split.
