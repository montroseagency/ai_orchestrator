# Section 02 — View Chrome

## Overview

This section implements the UI chrome components that sit above the task view area on the Tasks page. These are the controls the agent uses to switch between Kanban and List views and to filter the task list. Both components are purely presentational/interaction layers — they do not fetch tasks themselves.

**Depends on:** section-01-data-foundation (provides `useTaskFilters`, `ClientBadge`, `useClients`, `useTaskCategories`)
**Blocks:** section-06-page-composition
**Parallelizable with:** section-03, section-04, section-05

---

## Files to Create

```
client/components/management/tasks/ViewToggle.tsx
client/components/management/tasks/TaskFilterBar.tsx
```

---

## Tests First

Write all tests before implementing. Run `cd client && npx vitest run` to confirm they are **red** before starting implementation.

### Test file: `client/app/dashboard/agent/marketing/management/tasks/__tests__/ViewToggle.test.tsx`

Test cases:
- Renders both a "List" button and a "Kanban" button
- The active button has the `bg-accent` class applied based on the `currentView` prop
- Clicking the List button calls `onViewChange('list')`
- Clicking the Kanban button calls `onViewChange('kanban')`
- Both buttons render their Lucide icons (`LayoutList` for list, `Columns3` for kanban)

**Mock requirements:** None — this component has no external dependencies.

**Stub signature to test against:**

```typescript
// client/components/management/tasks/ViewToggle.tsx
interface ViewToggleProps {
  currentView: 'kanban' | 'list';
  onViewChange: (view: 'kanban' | 'list') => void;
}
export function ViewToggle({ currentView, onViewChange }: ViewToggleProps): JSX.Element
```

---

### Test file: `client/app/dashboard/agent/marketing/management/tasks/__tests__/TaskFilterBar.test.tsx`

Test cases:
- Renders a client dropdown or multi-select control
- Renders a category dropdown
- Renders a status dropdown
- Renders a priority dropdown
- Renders a search text input
- Selected clients appear as `ClientBadge` chip components in the filter bar
- Clicking the `×` on a client chip removes that client from the active filter (calls the appropriate `useTaskFilters` update function)
- Changing the status dropdown calls `updateStatus` from `useTaskFilters`
- Typing in the search input calls `updateSearch` after the debounce period (300ms — use `vi.useFakeTimers` and `vi.advanceTimersByTime`)
- When no clients are selected, no chips are visible and the client dropdown shows its placeholder
- Selecting a client from the dropdown adds it as a chip

**Mock requirements:**

```typescript
vi.mock('@/lib/hooks/useTaskFilters', () => ({
  useTaskFilters: () => ({
    filters: { clients: [], categories: [], status: undefined, priority: undefined, q: '' },
    updateClients: vi.fn(),
    updateCategories: vi.fn(),
    updateStatus: vi.fn(),
    updatePriority: vi.fn(),
    updateSearch: vi.fn(),
  }),
}));

vi.mock('@/lib/hooks/useClients', () => ({
  useClients: () => ({ data: [{ id: '1', name: 'Acme Corp' }], isLoading: false }),
}));

vi.mock('@/lib/hooks/useScheduling', () => ({
  useTaskCategories: () => ({ data: [{ id: 'cat-1', name: 'Design', color: '#6366f1' }], isLoading: false }),
}));
```

**Stub signature to test against:**

```typescript
// client/components/management/tasks/TaskFilterBar.tsx
export function TaskFilterBar(): JSX.Element
```

---

## Implementation Details

### ViewToggle.tsx

A small segmented control with exactly two buttons. It does not manage its own state — it receives `currentView` as a prop and fires `onViewChange` on click. The parent (page.tsx) owns the view state and persists it to both URL params and localStorage.

**Visual spec:**
- Container: `rounded-lg border border-border flex` (no gap — buttons are flush)
- Active button: `bg-accent text-white rounded-md`
- Inactive button: `bg-surface text-secondary`
- Both buttons: `flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium transition-colors`
- Icons: `LayoutList` (list) and `Columns3` (kanban) — both from `lucide-react`, size 16

**Behavior:** On click, call `onViewChange` with the clicked view value. The parent handles localStorage write and URL param update via `useTaskFilters`.

---

### TaskFilterBar.tsx

A horizontal flex row of filter controls. Reads current values from `useTaskFilters()` and dispatches updates on every change. Does not own filter state — the hook owns it via URL params.

**Layout:** `flex flex-wrap gap-2 items-center p-3 bg-surface-subtle rounded-lg border border-border-subtle`

**Controls (left to right):**

1. **Client multi-select:** A `<select multiple>` or a custom dropdown populated from `useClients()`. Selected clients render as `ClientBadge` chips inline in the bar. Each chip has an `×` button that calls `updateClients(currentClients.filter(id => id !== removedId))`. Selecting a client from the dropdown appends it to the current selection.

2. **Category select:** A plain `<select>` populated from `useTaskCategories()`. On change, calls `updateCategories([value])` (single-select for now). Renders a color preview dot next to each option label.

3. **Status select:** A plain `<select>` with options: All / To-Do / In Progress / In Review / Done. Values: `''` / `'todo'` / `'in_progress'` / `'in_review'` / `'done'`. On change, calls `updateStatus(value || undefined)`.

4. **Priority select:** A plain `<select>` with options: All / Low / Medium / High. Values: `''` / `'low'` / `'medium'` / `'high'`. On change, calls `updatePriority(value || undefined)`.

5. **Search input:** `<input type="text" placeholder="Search tasks...">`. Uses a local `useState` for the displayed value and `useDebounce` (300ms) before calling `updateSearch`. Import or create a minimal `useDebounce` hook — check `client/lib/hooks/` first; if one exists, use it.

**Client chip area:** Render selected client chips immediately after the client dropdown (or inline with it). Each chip is a `ClientBadge` with `onRemove` prop wired to remove that client ID from the filter.

**Loading states:** While `useClients()` or `useTaskCategories()` is loading, disable the respective dropdown and show a placeholder "Loading…".

---

## Background Context

### Why URL params for filter state

Filters are stored in URL query params (not component state or a store) so:
- The page is shareable via URL
- Filters survive browser refresh and back/forward navigation
- `useGlobalTasks(filters)` at the page level receives the same parsed filter object on every render without extra synchronization

The `useTaskFilters()` hook from section-01 handles all parsing and updating. `TaskFilterBar` and `ViewToggle` simply consume it.

### View preference persistence

`ViewToggle` fires `onViewChange` and the **parent page** is responsible for:
1. Updating the `view` URL param via `useTaskFilters`
2. Writing the value to `localStorage` key `command-centre-task-view`

`ViewToggle` itself is stateless — this keeps it easily testable and free of side effects.

### Client multi-select limitation

If the `useGlobalTasks` hook (from `useScheduling.ts`) only supports a single `client` filter param, the filter bar UI should still render chips for all selected clients, but pass only the most recently selected client ID to the hook. Add a `// TODO: backend multi-client filtering not yet supported` comment at the call site. Do not filter client-side.

### Debounce for search

The search input must debounce URL updates at 300ms to avoid hammering the router on every keystroke. A local `inputValue` state tracks the displayed text immediately; the debounced value is what gets written to the URL (and thus passed to `useGlobalTasks`).

---

## Dependency Checklist

Before implementing, confirm the following are available (from section-01):

- [ ] `useTaskFilters()` hook exists at `client/lib/hooks/useTaskFilters.ts` and exports `filters`, `updateClients`, `updateCategories`, `updateStatus`, `updatePriority`, `updateSearch`
- [ ] `ClientBadge` component exists at `client/components/management/tasks/ClientBadge.tsx` and accepts `clientId`, `clientName`, and optional `onRemove` props
- [ ] `useClients()` hook exists at `client/lib/hooks/useClients.ts`
- [ ] `useTaskCategories()` is available from `client/lib/hooks/useScheduling.ts`

If any of these are missing, complete section-01 first before starting this section.
