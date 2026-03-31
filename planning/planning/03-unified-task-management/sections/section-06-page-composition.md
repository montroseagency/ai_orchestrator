# Section 06 — Page Composition

## Overview

This is the final integration section. It composes all components built in sections 01–05 into the top-level Tasks page. The result is a single, fully functional page at `/dashboard/agent/marketing/management/tasks/`.

**Dependencies (must be complete before starting this section):**
- Section 01: `clientPalette.ts`, `ClientBadge.tsx`, `useTaskFilters.ts`
- Section 02: `ViewToggle.tsx`, `TaskFilterBar.tsx`
- Section 03: `TasksKanbanView.tsx`, `TaskCard.tsx`, `TaskCardOverlay.tsx`, `KanbanColumn.tsx`
- Section 04: `TasksListView.tsx`, `BulkActionBar.tsx`
- Section 05: `TaskModal.tsx`, `RecurrenceBuilder.tsx`

---

## Files to Create

| File | Purpose |
|------|---------|
| `client/app/dashboard/agent/marketing/management/tasks/page.tsx` | Top-level page component |
| `client/app/dashboard/agent/marketing/management/tasks/__tests__/page.test.tsx` | Integration tests |

---

## Tests First

Write `page.test.tsx` before implementing `page.tsx`. All tests must fail (red) before implementation begins, then pass (green) after.

**Test file location:** `client/app/dashboard/agent/marketing/management/tasks/__tests__/page.test.tsx`

**Required mocks:**

```typescript
vi.mock('@/lib/hooks/useScheduling', () => ({
  useGlobalTasks: vi.fn(() => ({ data: mockTasks, isLoading: false })),
  useTaskCategories: vi.fn(() => ({ data: mockCategories })),
}))
vi.mock('@/lib/hooks/useClients', () => ({
  useClients: vi.fn(() => ({ data: mockClients })),
}))
vi.mock('next/navigation', () => ({
  useRouter: vi.fn(() => ({ push: mockPush })),
  useSearchParams: vi.fn(() => new URLSearchParams()),
  usePathname: vi.fn(() => '/dashboard/agent/marketing/management/tasks'),
}))
```

**Test cases (write stubs for all of these):**

1. **Renders page heading "Tasks"** — the `SectionHeader` title or an `<h1>` containing "Tasks" must be present in the document
2. **`ViewToggle` is present in the header** — the segmented control buttons for Kanban and List are rendered
3. **Default view is Kanban** — on first render with no URL params and no localStorage value, `TasksKanbanView` is rendered and `TasksListView` is not
4. **Default view respects localStorage** — if `localStorage.getItem('command-centre-task-view')` returns `'list'` and no URL `view` param is set, `TasksListView` is rendered
5. **URL param takes precedence over localStorage** — if localStorage says `'list'` but `?view=kanban` is in the URL, Kanban is rendered
6. **Clicking the List toggle renders `TasksListView`** — after simulating a click on the List button, `TasksListView` appears and `TasksKanbanView` does not
7. **Clicking the Kanban toggle renders `TasksKanbanView`** — after switching to List and then clicking Kanban, `TasksKanbanView` reappears
8. **Switching views does NOT reset the filter state** — set URL params `?status=todo&view=kanban`, switch to list, assert `status=todo` is still present in the URL params passed to `useGlobalTasks`
9. **`TaskFilterBar` is rendered above the view** — both the filter bar and the view component are in the document; the filter bar appears before the view in DOM order
10. **`+ New Task` button is visible** — a button or element with text matching `+ New Task` or `New Task` is in the document
11. **Clicking `+ New Task` opens `TaskModal` in create mode** — after the click, the modal is open (check for modal heading or form) and no `task` prop is passed (modal is in create mode, so no pre-populated title field)
12. **`TaskModal` is rendered at the page level** — the modal is not a child of `TasksKanbanView` or `TasksListView`; verify it is a sibling of the view container in the DOM tree, not nested inside it
13. **`useGlobalTasks` is called once with the parsed filter object** — assert `useGlobalTasks` was called exactly once per render cycle, with the filter object derived from the mocked `useSearchParams` return value

---

## Implementation: `page.tsx`

**File:** `client/app/dashboard/agent/marketing/management/tasks/page.tsx`

This is a Next.js App Router page. It must be a `'use client'` component because it uses hooks (`useSearchParams`, `useRouter`, `useState`, `useEffect`).

### Responsibility

The page component is the single orchestration point. It:

1. Reads the current view preference from URL params, falling back to localStorage
2. Fetches tasks once via `useGlobalTasks(filters)` where `filters` is derived from `useTaskFilters()`
3. Renders the full page layout: heading, view toggle, filter bar, active view, and the task creation modal
4. Controls modal open/close state with a single `useState<boolean>` and a `useState<AgentGlobalTask | undefined>` for the task being edited
5. Passes `tasks` down to both views as a prop — no second fetch occurs inside either view

### Component Signature

```typescript
'use client'

export default function TasksPage() { ... }
```

No props — this is a page component.

### Internal State

```typescript
const [isModalOpen, setIsModalOpen] = useState(false)
const [editingTask, setEditingTask] = useState<AgentGlobalTask | undefined>(undefined)
```

Opening in create mode: `setEditingTask(undefined); setIsModalOpen(true)`
Opening in edit mode: `setEditingTask(task); setIsModalOpen(true)`
Closing: `setIsModalOpen(false)` (the `onClose` prop of `TaskModal`)

### View Preference Logic

```typescript
// Read view from URL params first; fall back to localStorage
const searchParams = useSearchParams()
const urlView = searchParams.get('view') as 'kanban' | 'list' | null
const [view, setView] = useState<'kanban' | 'list'>(() => {
  if (urlView) return urlView
  if (typeof window !== 'undefined') {
    return (localStorage.getItem('command-centre-task-view') as 'kanban' | 'list') ?? 'kanban'
  }
  return 'kanban'
})
```

When `ViewToggle` calls `onViewChange(newView)`:
- Update `view` state
- Write to localStorage: `localStorage.setItem('command-centre-task-view', newView)`
- Push to URL: `router.push(buildUrl({ view: newView }))` — `buildUrl` merges the new param into existing params (do not drop other filter params)

### Filter and Data Fetching

```typescript
const { filters } = useTaskFilters()
const { data: tasks = [], isLoading } = useGlobalTasks(filters)
```

`filters` is the parsed filter object from `useTaskFilters`. `useGlobalTasks` is called once at this level — both `TasksKanbanView` and `TasksListView` receive `tasks` as a prop and do not fetch independently.

### JSX Structure (outline)

```tsx
<div className="flex flex-col gap-4 p-6">
  {/* Header row: title + view toggle + new task button */}
  <div className="flex items-center justify-between">
    <SectionHeader title="Tasks" />
    <div className="flex items-center gap-3">
      <ViewToggle view={view} onViewChange={handleViewChange} />
      <Button onClick={() => { setEditingTask(undefined); setIsModalOpen(true) }}>
        + New Task
      </Button>
    </div>
  </div>

  {/* Filter bar */}
  <TaskFilterBar />

  {/* Active view */}
  {isLoading ? (
    <Spinner />
  ) : view === 'kanban' ? (
    <TasksKanbanView tasks={tasks} onTaskEdit={handleTaskEdit} />
  ) : (
    <TasksListView tasks={tasks} onTaskEdit={handleTaskEdit} />
  )}

  {/* Modal at page level — NOT inside either view */}
  <TaskModal
    isOpen={isModalOpen}
    onClose={() => setIsModalOpen(false)}
    task={editingTask}
  />
</div>
```

Use `SectionHeader` from the existing portal layout primitives (check the management layout for the correct import path). Use `Button` from `client/components/ui/button.tsx`. Use `Spinner` from `client/components/ui/spinner.tsx`.

### `handleTaskEdit`

Passed as `onTaskEdit` to both views:

```typescript
const handleTaskEdit = (task: AgentGlobalTask) => {
  setEditingTask(task)
  setIsModalOpen(true)
}
```

Both `TasksKanbanView` and `TasksListView` call this when a task card or row is clicked (they received it in section 03 and 04 as part of their props).

---

## Imports Checklist

When writing `page.tsx`, verify these import paths resolve:

- `useTaskFilters` → `@/lib/hooks/useTaskFilters` (or wherever section 01 placed it)
- `useGlobalTasks` → `@/lib/hooks/useScheduling`
- `ViewToggle` → `@/components/management/tasks/ViewToggle`
- `TaskFilterBar` → `@/components/management/tasks/TaskFilterBar`
- `TasksKanbanView` → `@/components/management/tasks/TasksKanbanView`
- `TasksListView` → `@/components/management/tasks/TasksListView`
- `TaskModal` → `@/components/management/tasks/TaskModal`
- `Button` → `@/components/ui/button`
- `Spinner` → `@/components/ui/spinner`
- `AgentGlobalTask` → `@/lib/types/scheduling`

---

## Key Constraints

**Modal must be at page level.** Do not render `TaskModal` inside `TasksKanbanView` or `TasksListView`. It must be a sibling of the view container. This prevents z-index stacking context issues where the modal could be clipped by an overflow-hidden ancestor inside the Kanban scroll container.

**Single data fetch.** `useGlobalTasks` is called once in `page.tsx`. The `tasks` array is passed as a prop to the active view. Do not call `useGlobalTasks` inside the view components.

**Filter state is owned by URL.** `page.tsx` does not hold filter state in `useState`. Filter reads come from `useTaskFilters()` which reads URL params. Filter writes go through `useTaskFilters()` update functions which call `router.push`. This ensures view switches do not drop filters.

**`'use client'` directive is required** because the page uses `useSearchParams`, `useRouter`, `useState`, and `useEffect`.

---

## Edge Cases

**Loading state:** While `isLoading` is true, render `<Spinner />` in place of the view. Do not render both the spinner and the view simultaneously.

**Empty task array:** Pass `tasks={[]}` to the active view — each view handles its own empty state internally (Kanban columns show "No tasks here"; the list shows a message or empty table). The page does not need its own empty state UI.

**Modal on view switch:** If the modal is open when the user clicks the view toggle, the modal stays open. View switching only updates the `view` state/URL — it does not touch `isModalOpen` or `editingTask`.

**SSR / hydration:** `useSearchParams` requires `Suspense` in Next.js App Router. Wrap the page export in a `Suspense` boundary if the build produces a "missing Suspense boundary" warning. A simple `<Suspense fallback={<Spinner />}>` around the page content is sufficient.

---

## TDD Sequence

1. Create `__tests__/page.test.tsx` with all 13 test stubs listed above
2. Run `cd client && npx vitest run` — all 13 new tests fail (red)
3. Create `page.tsx` with the full implementation
4. Run `cd client && npx vitest run` — all tests pass (green)
5. Run the full test suite to confirm no regressions across sections 01–05

---

## Definition of Done

- [ ] `page.test.tsx` written with all 13 test cases
- [ ] All 13 tests pass
- [ ] `page.tsx` composes all 5 section outputs
- [ ] `useGlobalTasks` is called exactly once per render
- [ ] `TaskModal` is rendered outside both view components in the DOM
- [ ] View switching preserves URL filter params
- [ ] localStorage fallback for view preference works
- [ ] URL param takes precedence over localStorage for view preference
- [ ] `+ New Task` button opens modal in create mode (no pre-populated task)
- [ ] Card/row clicks open modal in edit mode with correct task pre-populated
- [ ] Full test suite green (`cd client && npx vitest run`)
