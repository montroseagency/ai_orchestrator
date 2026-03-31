# Section 04 — List View

## Overview

This section implements the sortable table list view for the Tasks page, along with the bulk action toolbar. It runs **in parallel** with sections 02, 03, and 05 (all after section-01-data-foundation is complete).

**Files to create:**
- `client/components/management/tasks/TasksListView.tsx`
- `client/components/management/tasks/BulkActionBar.tsx`

**Test files to create (write these first):**
- `client/app/dashboard/agent/marketing/management/tasks/__tests__/TasksListView.test.tsx`
- `client/app/dashboard/agent/marketing/management/tasks/__tests__/BulkActionBar.test.tsx`

**Dependencies (must be complete before this section):**
- `section-01-data-foundation` — provides `ClientBadge.tsx`, types from `client/lib/types/scheduling.ts`, and hooks from `client/lib/hooks/useScheduling.ts`

**Blocks:**
- `section-06-page-composition` — the page imports `TasksListView` directly

---

## Background and Context

The Tasks page supports two views: Kanban and List. This section delivers the List view. It is a sortable HTML table rendered on desktop; on mobile it collapses to a stacked card layout. When one or more rows are checked, a `BulkActionBar` appears that provides bulk status change and bulk delete operations.

The List view does **not** use drag-and-drop — that is solely the Kanban view (section-03). The List view uses client-side sort on the already-fetched tasks array. Filters are managed upstream by `useTaskFilters` (section-01) and applied at the page level via `useGlobalTasks(filters)` — the List view receives a pre-filtered `tasks` prop.

Reference file for table and mobile-card patterns: `client/components/agent/scheduling/CrossClientTaskList.tsx`. Do not modify that file — extract patterns only.

---

## Step 0 — Understand the Data Shape

Relevant types from `client/lib/types/scheduling.ts`:

```typescript
// Already exists — do not redefine
type GlobalTaskStatus = 'todo' | 'in_progress' | 'in_review' | 'done';

interface AgentGlobalTask {
  id: string;
  title: string;
  description?: string;
  status: GlobalTaskStatus;
  priority: 'low' | 'medium' | 'high';
  client?: string;         // client ID
  client_name?: string;    // display name
  category_id?: string;
  category_name?: string;
  category_color?: string;
  due_date?: string;       // ISO date string
  scheduled_date?: string;
  start_time?: string;
  end_time?: string;
  is_recurring: boolean;
  is_overdue: boolean;
  // ... other fields
}
```

Relevant hooks from `client/lib/hooks/useScheduling.ts`:
- `useUpdateGlobalTask()` — used for inline status change and bulk status update
- `useDeleteGlobalTask()` — used for bulk delete (per-item)

---

## Step 1 — Write Tests First

Run `cd client && npx vitest run` after writing tests to confirm they all fail (red). Implement, then re-run to make them pass (green).

### `TasksListView.test.tsx`

```typescript
// client/app/dashboard/agent/marketing/management/tasks/__tests__/TasksListView.test.tsx

import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import TasksListView from '@/components/management/tasks/TasksListView';
// Mock useUpdateGlobalTask
vi.mock('@/lib/hooks/useScheduling', () => ({
  useUpdateGlobalTask: () => ({ mutate: vi.fn() }),
}));
```

**Tests to implement:**

- Renders table with all 8 column headers: `Title`, `Client`, `Category`, `Status`, `Priority`, `Due Date`, `Scheduled`, `Actions`
- Each row renders task title, client badge, category badge, status for each task in the provided `tasks` prop
- Clicking a column header once sorts that column ascending; clicking the same header again sorts descending
- Row click (not on checkbox or status dropdown) calls `onTaskEdit(task)` with the correct task
- Checking the header checkbox selects all visible rows
- Unchecking the header checkbox (when all selected) deselects all rows
- `BulkActionBar` is visible when at least one row is selected
- `BulkActionBar` is not visible when no rows are selected
- Inline status dropdown `onChange` calls `useUpdateGlobalTask().mutate` with `{ id, status: newValue }`
- On mobile viewport (`window.innerWidth < 640`), the `<table>` is not rendered and a card layout is rendered instead
- Card layout on mobile shows title, client badge, and status badge for each task

### `BulkActionBar.test.tsx`

```typescript
// client/app/dashboard/agent/marketing/management/tasks/__tests__/BulkActionBar.test.tsx

import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import BulkActionBar from '@/components/management/tasks/BulkActionBar';
vi.mock('@/lib/hooks/useScheduling', () => ({
  useUpdateGlobalTask: () => ({ mutate: vi.fn() }),
  useDeleteGlobalTask: () => ({ mutate: vi.fn() }),
}));
```

**Tests to implement:**

- Shows "N tasks selected" with the correct count matching `selectedIds.size`
- "Change status" dropdown triggers `useUpdateGlobalTask().mutate` for each selected ID with the chosen status
- Partial failure scenario: items whose update failed remain in `selectedIds`; items that succeeded are removed from selection; an error toast is shown for each failure
- "Delete" button renders a confirmation dialog before proceeding (dialog text includes "delete" and the count)
- After confirmation, calls `useDeleteGlobalTask().mutate` for each selected ID

---

## Step 2 — Implement `TasksListView.tsx`

**File:** `client/components/management/tasks/TasksListView.tsx`

### Props interface

```typescript
interface TasksListViewProps {
  tasks: AgentGlobalTask[];
  onTaskEdit: (task: AgentGlobalTask) => void;
  selectedIds: Set<string>;
  onSelectionChange: (ids: Set<string>) => void;
}
```

`selectedIds` and `onSelectionChange` are lifted to the caller (the page) so `BulkActionBar` can be rendered at the same level.

### Sort state

Local `useState` inside `TasksListView`:

```typescript
type SortColumn = 'title' | 'client_name' | 'category_name' | 'status' | 'priority' | 'due_date' | 'scheduled_date';
type SortDirection = 'asc' | 'desc';

interface SortState {
  column: SortColumn;
  direction: SortDirection;
}
```

Default sort: `{ column: 'due_date', direction: 'asc' }`.

Toggling: clicking a header that is already the active sort column flips direction. Clicking a different header sets it as the new column with direction `'asc'`.

### `useSortedTasks` helper

A local helper function (not exported, defined in the same file or in a co-located `utils.ts`):

```typescript
function useSortedTasks(tasks: AgentGlobalTask[], sort: SortState): AgentGlobalTask[]
// Returns a stable-sorted shallow copy of tasks.
// Priority sort order: high > medium > low.
// Status sort order: todo > in_progress > in_review > done.
// Null/undefined values sort last in ascending, first in descending.
```

### Table structure

Standard HTML `<table>` styled with Tailwind following the project's existing table convention:

- `<thead>` with `<th>` per column — each header is a `<button>` showing an up/down arrow icon (Lucide `ArrowUp` / `ArrowDown` / `ArrowUpDown`) indicating current sort direction
- First column `<th>` is the select-all checkbox (`<input type="checkbox">`)
- Last column `<th>` is "Actions" (non-sortable)
- `<tbody>` with one `<tr>` per task

Table row contents:
- Checkbox cell
- Title: text, `cursor-pointer` — clicking calls `onTaskEdit(task)`
- Client: `<ClientBadge clientId={task.client} clientName={task.client_name} />`
- Category: a badge styled with `task.category_color` (same inline-style approach as `ClientBadge`)
- Status: inline `<select>` with all four `GlobalTaskStatus` options; `onChange` calls `useUpdateGlobalTask().mutate({ id: task.id, status: value })`; status value maps to a readable label ("To-Do", "In Progress", "In Review", "Done")
- Priority: text with a colored dot (same dot style as `TaskCard` — red/amber/blue)
- Due date: formatted date string; apply `text-red-500` (or `text-status-error`) when `task.is_overdue`
- Scheduled date: formatted date string or `—` if empty
- Actions: an `Edit` icon button (Lucide `Pencil`) that calls `onTaskEdit(task)`

Table styling:
```
<table className="w-full text-sm">
  <thead className="bg-surface-subtle border-b border-border">
  <tbody className="divide-y divide-border-subtle">
```
Row hover: `hover:bg-surface-subtle transition-colors`.

### Mobile card layout

Wrap the table in `<div className="hidden sm:block">`. Below it, render `<div className="sm:hidden space-y-2">` with one card per task:

Each mobile card:
- `bg-surface rounded-lg border border-border p-3`
- Row 1: task title (bold)
- Row 2: `<ClientBadge>` + category badge side by side
- Row 3: status badge + priority dot

On mobile, tapping the card calls `onTaskEdit(task)`.

Bulk selection is not available on mobile (omit checkboxes from mobile cards for this split).

### Inline status change and notification flow

When the inline status `<select>` is changed to `in_review`:
- Call `useUpdateGlobalTask().mutate({ id, status: 'in_review' })`
- `onSuccess`: show toast "Task sent for review" (the backend notification fires server-side; no separate client call)
- `onError`: show toast "Failed to update task status"

When changed to `done`:
- Use `useUpdateGlobalTask()` in the list view (not `useCompleteGlobalTask`) — the complete hook is reserved for the Kanban drag-to-done path. Add a comment: `// Note: inline status change to 'done' does not trigger JIT next-instance creation. Use Kanban drag-to-done or the modal complete action for recurring tasks.`

---

## Step 3 — Implement `BulkActionBar.tsx`

**File:** `client/components/management/tasks/BulkActionBar.tsx`

### Props interface

```typescript
interface BulkActionBarProps {
  selectedIds: Set<string>;
  onSelectionChange: (ids: Set<string>) => void;
  tasks: AgentGlobalTask[];  // needed to find task objects by id for delete confirmation text
}
```

### Behavior

The bar is only rendered by `TasksListView`'s parent (the page) when `selectedIds.size > 0`. `BulkActionBar` itself does not conditionally hide — the caller controls visibility.

**Status change:**
- Renders a `<select>` with all four status options (labeled: To-Do, In Progress, In Review, Done)
- On selection change, iterates `selectedIds` and calls `useUpdateGlobalTask().mutate({ id, status })` for each
- Each mutation is independent. Track results: on each `onSuccess`, remove that id from `selectedIds`; on each `onError`, keep that id in `selectedIds` and show a toast "Failed to update task [title]"
- Add a `// TODO: replace with bulk endpoint when available (e.g. PATCH /agent/schedule/global-tasks/bulk/)` comment

**Delete:**
- Renders a "Delete" button (Lucide `Trash2` icon + label)
- On click, show a confirmation using the existing `ConfirmationModal` from `client/components/common/confirmation-modal.tsx`. Pass message: `"Delete N selected tasks? This cannot be undone."`
- On confirm, call `useDeleteGlobalTask().mutate({ id })` for each id in `selectedIds`
- Each delete is independent; track partial failures same as status change
- Add same `// TODO: bulk endpoint` comment

**Layout:**
```
fixed bottom-4 left-1/2 -translate-x-1/2
bg-surface border border-border rounded-xl shadow-lg px-4 py-3
flex items-center gap-4
```

Shows: `"{N} tasks selected"` label, status `<select>`, Delete button.

---

## Edge Cases

- **Empty task list:** The table renders normally with an empty `<tbody>` and an empty state row spanning all columns: `<tr><td colSpan={9} className="text-center py-8 text-secondary">No tasks found</td></tr>`. `BulkActionBar` is not shown.
- **Sort stability:** Use a stable sort (JavaScript's `Array.prototype.sort` is stable in V8 ≥ 7). No secondary sort key is required.
- **Select-all checkbox indeterminate state:** When some (not all) rows are checked, set the header checkbox's `indeterminate` property to `true` (via a `ref` on the element). This is a standard HTML checkbox behavior not expressible in JSX props alone.
- **Inline status dropdown propagation:** The status `<select>` sits inside a clickable row. Stop the click event from propagating to the row's `onClick` handler with `e.stopPropagation()` on the select's `onChange`.
- **Bulk status to `in_review`:** Each individual update to `in_review` will trigger a backend notification signal for that task. This is intentional — each affected task gets its admin notification.

---

## Acceptance Criteria

All tests in `TasksListView.test.tsx` and `BulkActionBar.test.tsx` pass.

Manual verification:
1. Table renders with all 8 headers
2. Clicking column headers sorts tasks correctly; arrow icon updates
3. Inline status dropdown updates immediately (optimistic) and shows the correct toast for `in_review`
4. Checking header checkbox selects all; unchecking deselects all
5. `BulkActionBar` appears/disappears correctly
6. Bulk status change updates each selected task; partial failures leave failed items selected
7. Bulk delete shows confirmation dialog; confirmed deletes fire per-item
8. On a narrow viewport, table is hidden and mobile cards appear
