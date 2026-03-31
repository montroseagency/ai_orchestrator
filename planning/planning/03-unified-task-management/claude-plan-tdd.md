# TDD Plan: Unified Task Management UI (Split 03)

**Testing framework:** Vitest + `@testing-library/react`
**Test location:** `client/app/dashboard/agent/marketing/management/tasks/__tests__/`
**Mock pattern:** `vi.mock('@/lib/hooks/...')`, `vi.mock('next/navigation', ...)`
**Run command:** `cd client && npx vitest run`

All tests are written **before** implementing the corresponding module.

---

## Context / What We're Building

No tests for this section (prose context only).

---

## File Structure

No tests for this section. Verify file structure by running `ls client/components/management/tasks/` after scaffolding.

---

## Data Layer

### clientPalette.ts

Write tests first in `clientPalette.test.ts`:
- Test: `getClientColor` returns the same color for the same clientId every time (deterministic)
- Test: `getClientColor` returns different colors for different clientIds (distribution)
- Test: `getClientColor` returns the default gray `#9CA3AF` when called with `null`
- Test: `getClientColor` returns the default gray `#9CA3AF` when called with `undefined`
- Test: `getClientColor` returns the default gray `#9CA3AF` when called with empty string
- Test: All returned values are valid hex color strings (match `/#[0-9A-Fa-f]{6}/`)

### useTaskFilters.ts

Write tests first in `useTaskFilters.test.ts`:
- Test: Parses `clients` comma-separated param into string array
- Test: Parses `categories` comma-separated param into string array
- Test: Parses single `status` param into correct `GlobalTaskStatus` value
- Test: Parses `priority` param correctly
- Test: Parses debounced `q` param as string
- Test: Returns empty arrays / undefined for missing params (not null or error)
- Test: `updateClients([...ids])` calls `router.push` with comma-joined `clients` param
- Test: `updateSearch(text)` updates `q` param
- Test: Invalid/unrecognized `status` value falls back gracefully (does not throw)
- Test: Invalid/unrecognized `priority` value falls back gracefully

---

## View Toggle

Write tests first in `ViewToggle.test.tsx`:
- Test: Renders both List and Kanban buttons
- Test: Active button has `bg-accent` class applied to the correct segment based on current view
- Test: Clicking List button calls `onViewChange('list')`
- Test: Clicking Kanban button calls `onViewChange('kanban')`
- Test: Both buttons render their Lucide icons

---

## Kanban View

### TaskCard.tsx

Write tests first in `TaskCard.test.tsx`:
- Test: Renders task title (truncated to 2 lines with `line-clamp-2`)
- Test: Renders `ClientBadge` with correct `clientId` and `clientName`
- Test: Renders category badge with category name
- Test: Renders priority dot with correct color class (red for high, amber for medium, blue for low)
- Test: Renders due date with `CalendarDays` icon
- Test: Applies `text-status-error` class to due date when `is_overdue` is true
- Test: Renders `RefreshCw` icon when `is_recurring` is true
- Test: Does NOT render recurrence icon when `is_recurring` is false
- Test: Clicking the card (not on drag handle) calls `onEdit(task)`
- Test: Clicking the drag handle does NOT call `onEdit`
- Test: Card has `cursor-pointer` class
- Test: Drag handle has `cursor-grab` class

### KanbanColumn.tsx

Write tests first in `KanbanColumn.test.tsx`:
- Test: Renders column label in uppercase
- Test: Renders task count badge showing correct number
- Test: Renders all provided `TaskCard` children
- Test: Renders an empty-state message when tasks array is empty (column still visible, not collapsed)
- Test: Column has a minimum height when empty (rendered area is non-zero)

### TasksKanbanView.tsx

Write tests first in `TasksKanbanView.test.tsx`:
- Test: Renders exactly 4 columns: To-Do, In Progress, In Review, Done
- Test: Tasks are distributed to correct columns based on their `status` field
- Test: `onTaskEdit` callback is passed through to cards
- Test: `onStatusChange` is called with correct `{ id, status }` when simulating a column drop (mock `@dnd-kit/core` — test the `onDragEnd` handler logic directly, not the drag DOM event)
- Test: `useCompleteGlobalTask` is called (not `useUpdateGlobalTask`) when status changes to `done`
- Test: `useUpdateGlobalTask` is called (not `useCompleteGlobalTask`) when status changes to `in_review`
- Test: Toast "Task sent for review" appears after successful in_review mutation
- Test: Toast "Failed to move task — change reverted" appears after failed mutation

---

## List View

### TasksListView.tsx

Write tests first in `TasksListView.test.tsx`:
- Test: Renders table with all 8 column headers: Title, Client, Category, Status, Priority, Due Date, Scheduled, Actions
- Test: Each row renders task title, client badge, category badge, status
- Test: Clicking a column header once sorts ascending; clicking again sorts descending
- Test: Row click opens TaskModal with the correct task pre-populated
- Test: Checking the header checkbox selects all visible rows
- Test: Unchecking the header checkbox deselects all rows
- Test: `BulkActionBar` is visible when at least one row is selected
- Test: `BulkActionBar` is not visible when no rows are selected
- Test: Inline status dropdown change calls `useUpdateGlobalTask` with correct `{ id, status }`
- Test: On mobile viewport (`< sm`), table is hidden and card layout is rendered instead
- Test: Card layout on mobile shows title, client badge, status badge per task

### BulkActionBar.tsx

Write tests first in `BulkActionBar.test.tsx`:
- Test: Shows "N tasks selected" with correct count
- Test: "Change status" triggers update call for each selected ID when no bulk endpoint
- Test: Partial failure — failed items remain selected, successful items deselected
- Test: Error toast shown for each failed update
- Test: "Delete" button shows confirmation dialog before proceeding
- Test: Confirmed delete calls delete hook for each selected ID

---

## Task Creation / Edit Modal

### RecurrenceBuilder.tsx

Write tests first in `RecurrenceBuilder.test.tsx`:
- Test: Renders frequency selector with all 6 options: Daily, Weekly, Biweekly, Monthly, Yearly, Custom
- Test: Day-of-week checkboxes are hidden when frequency is Daily or Monthly or Yearly
- Test: Day-of-week checkboxes are visible when frequency is Weekly
- Test: Day-of-week checkboxes are visible when frequency is Custom
- Test: Interval field renders with correct unit label (e.g., "days" for Daily, "weeks" for Weekly)
- Test: End condition radio group shows "Never", "After N occurrences", "On date"
- Test: Number input appears when "After N occurrences" is selected
- Test: Date picker appears when "On date" is selected
- Test: Neither extra input appears when "Never" is selected
- Test: All value changes call the provided `onChange` callbacks with correct updated values

### TaskModal.tsx

Write tests first in `TaskModal.test.tsx`:
- Test: Renders all section headings in create mode (Basic Info, Assignment, Scheduling, Recurrence)
- Test: All required fields are present: title input, priority toggle, client select, category select, due date input
- Test: Recurrence section is hidden by default
- Test: Toggling the recurrence switch shows `RecurrenceBuilder`
- Test: In edit mode, all fields are pre-populated with existing task values
- Test: Title field is required — Save button is disabled or shows validation error when empty
- Test: Save in create mode calls `useCreateGlobalTask` with exactly the user-editable field payload (no id, no created_at)
- Test: Save in edit mode calls `useUpdateGlobalTask` with correct id and changed fields
- Test: Cancel calls `onClose` without mutation
- Test: "Save & Schedule" shows toast "Calendar scheduling coming soon" and also saves the task
- Test: Modal closes (`onClose` called) after successful save
- Test: Modal stays open on save failure, shows error feedback

---

## Client Color System

### ClientBadge.tsx

Write tests first in `ClientBadge.test.tsx`:
- Test: Renders client name as text
- Test: Applies background-color style derived from `getClientColor(clientId)`
- Test: Renders "Unassigned" when `clientId` is null/undefined
- Test: Applies gray color styling when rendering "Unassigned"
- Test: Has `rounded-full` and `text-xs` classes
- Test: Renders an `×` remove button when `onRemove` prop is provided
- Test: `×` button click calls `onRemove` callback

---

## Filter Bar

### TaskFilterBar.tsx

Write tests first in `TaskFilterBar.test.tsx`:
- Test: Renders client, category, status, and priority dropdowns
- Test: Renders search input
- Test: Selected clients appear as `ClientBadge` chips
- Test: Clicking `×` on a chip removes that client from the filter
- Test: Changing status dropdown calls `updateStatus` from `useTaskFilters`
- Test: Typing in search input calls `updateSearch` after debounce
- Test: "All Clients" state — no chips visible, dropdown shows placeholder
- Test: Selecting a client from dropdown adds it as a chip
- Test: Multiple client chips are all visible simultaneously

---

## Notification Flow (In Review)

No additional tests beyond those in `TasksKanbanView.test.tsx` (covered: toast on success, no toast on error). No separate notification unit test needed — notification dispatch is backend-managed.

---

## Page Composition

Write tests first in `page.test.tsx`:
- Test: Page renders heading "Tasks"
- Test: `ViewToggle` is present in the header
- Test: Default view is Kanban (or matches localStorage value)
- Test: Clicking the List toggle renders `TasksListView` (not Kanban)
- Test: Clicking the Kanban toggle renders `TasksKanbanView` (not List)
- Test: Switching views does NOT reset the filter state (URL params preserved)
- Test: `TaskFilterBar` is rendered above the view
- Test: "+ New Task" button is visible
- Test: Clicking "+ New Task" opens `TaskModal` in create mode (no pre-populated task)
- Test: `TaskModal` renders at the page level, not inside the Kanban or List component (verify it's outside both)
- Test: `useGlobalTasks` is called once with the parsed filter object from `useTaskFilters`

---

## Testing Strategy (Summary)

No extra tests — the individual sections above cover all components.

**Pre-flight checklist before each implementation section:**
1. Write the tests listed above for that section
2. Run `npx vitest run` — all new tests should fail (red)
3. Implement the component/hook
4. Run `npx vitest run` — all tests should pass (green)
5. Refactor if needed; keep tests green

---

## Implementation Order (with TDD sequence)

The implementation order from the plan maps to this test-first sequence:

1. `clientPalette.ts` → write `clientPalette.test.ts` first
2. `ViewToggle.tsx` → write `ViewToggle.test.tsx` first
3. `useTaskFilters.ts` → write `useTaskFilters.test.ts` first
4. `TaskFilterBar.tsx` → write `TaskFilterBar.test.tsx` first (mock useTaskFilters + useClients + useTaskCategories)
5. `TaskCard.tsx` + `TaskCardOverlay.tsx` → write `TaskCard.test.tsx` first
6. `KanbanColumn.tsx` + `TasksKanbanView.tsx` → write `KanbanColumn.test.tsx` + `TasksKanbanView.test.tsx` first
7. `TasksListView.tsx` + `BulkActionBar.tsx` → write `TasksListView.test.tsx` + `BulkActionBar.test.tsx` first
8. `RecurrenceBuilder.tsx` → write `RecurrenceBuilder.test.tsx` first
9. `TaskModal.tsx` → write `TaskModal.test.tsx` first
10. `page.tsx` → write `page.test.tsx` first
11. `ClientBadge.tsx` → write `ClientBadge.test.tsx` first (can be done alongside step 1)
