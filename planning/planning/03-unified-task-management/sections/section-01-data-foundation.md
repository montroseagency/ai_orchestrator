# Section 01: Data Foundation

**Dependencies:** None — this is the base layer. All other sections (02–06) depend on this one.

**Blocks:** section-02-view-chrome, section-03-kanban-view, section-04-list-view, section-05-task-modal, section-06-page-composition

---

## Overview

This section establishes the pure utility layer for the unified task management feature. It has no external React component dependencies and can be built and tested independently. Three deliverables:

1. `clientPalette.ts` — deterministic client-ID → hex color mapping
2. `ClientBadge.tsx` — color-coded client chip React component
3. `useTaskFilters.ts` — URL query-param parsing/updating hook

Once this section is complete, every other section can proceed in parallel.

---

## Existing Types (do not recreate)

All types live in `client/lib/types/scheduling.ts` and are already complete. Key types for this section:

- `GlobalTaskStatus` = `'todo' | 'in_progress' | 'in_review' | 'done'`
- `TaskPriority` = `'low' | 'medium' | 'high'`
- `RecurrenceFrequency` = `'daily' | 'weekly' | 'biweekly' | 'monthly' | 'yearly' | 'custom'` (already includes `yearly` and `custom` — **no changes needed**)
- `RecurrenceEndType` = `'never' | 'date' | 'count'`
- `GlobalTaskFilters` — shape accepted by `useGlobalTasks(filters)`:
  ```typescript
  interface GlobalTaskFilters {
    status?: GlobalTaskStatus;
    task_category_id?: string;
    client?: string;          // single client ID only
    is_recurring?: boolean;
    scheduled_date?: string;
    due_before?: string;
    priority?: TaskPriority;
  }
  ```

**Important:** `GlobalTaskFilters.client` is a single string, not an array. The API does not support multi-client filtering in this split. The filter bar UI allows selecting multiple clients as chips, but only the most recently selected client ID is sent to `useGlobalTasks`. Add a `// TODO: backend multi-client filtering not yet supported` comment at the point where the filter object is constructed.

---

## Existing Hooks (do not recreate)

All live in `client/lib/hooks/useScheduling.ts`:

- `useGlobalTasks(filters?: GlobalTaskFilters)` — 30s staleTime, keyed by filter shape
- `useCreateGlobalTask()` — `mutationFn: (data: CreateGlobalTaskRequest) => ...`
- `useUpdateGlobalTask()` — `mutationFn: ({ id, data }: { id: string; data: UpdateGlobalTaskRequest }) => ...`
- `useDeleteGlobalTask()` — `mutationFn: (id: string) => ...`
- `useCompleteGlobalTask()` — `mutationFn: (id: string) => ...`; triggers backend JIT next-instance creation
- `useTaskCategories(department?: string)` — returns `TaskCategoryItem[]`

**Clients hook:** Check `client/lib/hooks/` for an existing clients hook. There is no `useClients` hook in the current codebase. Create `client/lib/hooks/useClients.ts` as part of this section (see below).

---

## Deliverable 1: `clientPalette.ts`

**File:** `client/components/management/tasks/clientPalette.ts`

### What it does

Exports a fixed palette of 12 distinct hex color strings and a deterministic function that maps any client ID string to one palette entry. The same input always returns the same output (no randomness). Guards against null/undefined/empty inputs by returning a neutral gray.

### Tests first

**File:** `client/components/management/tasks/__tests__/clientPalette.test.ts`

Test cases (write these before implementing):

```
- getClientColor returns the same color for the same clientId on repeated calls
- getClientColor returns different colors for at least two distinct clientIds
  (use IDs with different char-code sums to ensure hash distribution)
- getClientColor(null) returns '#9CA3AF'
- getClientColor(undefined) returns '#9CA3AF'
- getClientColor('') returns '#9CA3AF'
- All returned values match /#[0-9A-Fa-f]{6}/
```

### Implementation stubs

```typescript
// client/components/management/tasks/clientPalette.ts

export const CLIENT_PALETTE: string[] = [
  // 12 visually distinct hex colors
  // e.g. '#6366F1', '#F59E0B', '#10B981', ... (fill in 12 total)
];

/**
 * Deterministically maps a clientId to a palette color.
 * Returns '#9CA3AF' (neutral gray) for null, undefined, or empty string.
 * Algorithm: sum of char codes modulo CLIENT_PALETTE.length
 */
export function getClientColor(clientId: string | null | undefined): string {
  // guard: return gray for falsy inputs
  // hash: sum charCodeAt for each char, mod palette length
  // return CLIENT_PALETTE[index]
}
```

---

## Deliverable 2: `ClientBadge.tsx`

**File:** `client/components/management/tasks/ClientBadge.tsx`

### What it does

Renders a color-coded pill/chip showing a client name. Color is derived from `getClientColor(clientId)`. Shows "Unassigned" (with gray color) when `clientId` is absent. Optionally renders an `×` remove button when an `onRemove` prop is passed (used in the filter bar's chip row).

Badge style:
- `backgroundColor: ${color}20` (10% opacity fill)
- `color: ${color}` (full saturation text)
- `border: 1px solid ${color}40` (25% opacity border)
- Tailwind: `rounded-full px-2 py-0.5 text-xs font-medium`

### Tests first

**File:** `client/components/management/tasks/__tests__/ClientBadge.test.tsx`

Test cases:

```
- Renders clientName as text content
- Applies inline backgroundColor derived from getClientColor(clientId)
- Renders "Unassigned" when clientId is null
- Renders "Unassigned" when clientId is undefined
- Applies gray (#9CA3AF) color styling when rendering "Unassigned"
- Has rounded-full and text-xs classes
- Renders an × remove button when onRemove prop is provided
- Does NOT render × button when onRemove is not provided
- Clicking × calls onRemove callback
```

### Implementation stub

```typescript
// client/components/management/tasks/ClientBadge.tsx

interface ClientBadgeProps {
  clientId?: string | null;
  clientName?: string | null;
  onRemove?: () => void;
}

export function ClientBadge({ clientId, clientName, onRemove }: ClientBadgeProps) {
  // call getClientColor(clientId)
  // render pill with inline style backgroundColor/color/border
  // render "Unassigned" fallback when !clientId
  // conditionally render × button with onRemove callback
}
```

---

## Deliverable 3: `useClients.ts`

**File:** `client/lib/hooks/useClients.ts`

### What it does

Minimal React Query hook that fetches `GET /api/clients/` and returns a `Client[]` array. Used by the filter bar and the task modal's client selector. No existing hook covers this — create it fresh.

### Client type

Define a minimal `Client` interface in this file (or in `client/lib/types/` if you prefer consistency):

```typescript
export interface Client {
  id: string;
  name: string;
}
```

### Implementation stub

```typescript
// client/lib/hooks/useClients.ts
import { useQuery } from '@tanstack/react-query';

export function useClients() {
  return useQuery<Client[]>({
    queryKey: ['clients'],
    queryFn: () => fetch('/api/clients/').then(r => r.json()),
    staleTime: 60_000,
  });
}
```

> Use the existing API client pattern from `client/lib/api/` rather than a raw `fetch` if one already wraps the `/api/clients/` endpoint. Search `client/lib/api/` during implementation to check.

---

## Deliverable 4: `useTaskFilters.ts`

**File:** `client/lib/hooks/useTaskFilters.ts`

### What it does

Encapsulates all URL query-param parsing and updating for the tasks page. Reads from `useSearchParams()` and writes with `useRouter().push()`. Exposes a parsed filter object (ready to pass to `useGlobalTasks`) plus setter functions for each filter dimension.

### URL param schema

| Param | Type | Notes |
|-------|------|-------|
| `view` | `'kanban' \| 'list'` | Used by ViewToggle, not part of GlobalTaskFilters |
| `clients` | comma-separated IDs | Multi-select UI; only the last is passed to API (see note above) |
| `categories` | comma-separated IDs | Multi-select — maps to `task_category_id` (last selected) |
| `status` | `GlobalTaskStatus` | Single value |
| `priority` | `TaskPriority` | Single value |
| `q` | string | Debounced search — not yet wired to API filter; stored in URL for UX |

### Returned shape (from the hook)

```typescript
interface TaskFiltersState {
  // Parsed from URL
  view: 'kanban' | 'list';
  selectedClientIds: string[];      // all selected (for chip display)
  selectedCategoryIds: string[];    // all selected (for chip display)
  status: GlobalTaskStatus | undefined;
  priority: TaskPriority | undefined;
  search: string;

  // The filter object to pass to useGlobalTasks
  apiFilters: GlobalTaskFilters;

  // Setters (each calls router.push with updated params)
  updateView: (view: 'kanban' | 'list') => void;
  updateClients: (ids: string[]) => void;
  updateCategories: (ids: string[]) => void;
  updateStatus: (status: GlobalTaskStatus | undefined) => void;
  updatePriority: (priority: TaskPriority | undefined) => void;
  updateSearch: (q: string) => void;
}
```

`apiFilters` is constructed as:
```typescript
{
  status: parsedStatus,
  task_category_id: selectedCategoryIds[selectedCategoryIds.length - 1],  // last only
  client: selectedClientIds[selectedClientIds.length - 1],                 // last only
  priority: parsedPriority,
  // TODO: backend multi-client filtering not yet supported
}
```

### Tests first

**File:** `client/app/dashboard/agent/marketing/management/tasks/__tests__/useTaskFilters.test.ts`

Test cases:

```
- Parses 'clients' comma-separated param into a string array
- Parses 'categories' comma-separated param into a string array
- Parses single 'status' param into correct GlobalTaskStatus value
- Parses 'priority' param correctly
- Parses 'q' param as a string
- Returns empty arrays / undefined for missing params (not null, not throwing)
- updateClients(['a','b']) calls router.push with 'clients=a%2Cb' (or 'clients=a,b')
- updateSearch('hello') calls router.push with 'q=hello'
- Invalid status value (e.g. 'bogus') falls back gracefully — undefined, no throw
- Invalid priority value falls back gracefully — undefined, no throw
```

### Implementation stub

```typescript
// client/lib/hooks/useTaskFilters.ts
'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import { GlobalTaskFilters, GlobalTaskStatus, TaskPriority } from '@/lib/types/scheduling';

const VALID_STATUSES = new Set<GlobalTaskStatus>(['todo', 'in_progress', 'in_review', 'done']);
const VALID_PRIORITIES = new Set<TaskPriority>(['low', 'medium', 'high']);

export function useTaskFilters() {
  const searchParams = useSearchParams();
  const router = useRouter();

  // Parse each param (with guards for invalid values)
  // Build apiFilters (single client/category — last in array)
  // Return TaskFiltersState

  // Each update function:
  //   1. Reads current params via new URLSearchParams(searchParams.toString())
  //   2. Sets/deletes the relevant key
  //   3. Calls router.push(`?${params.toString()}`, { scroll: false })
}
```

---

## File Creation Checklist

Before writing any implementation code, create the directory structure:

```
client/components/management/tasks/
  clientPalette.ts
  ClientBadge.tsx
  __tests__/
    clientPalette.test.ts
    ClientBadge.test.tsx

client/lib/hooks/
  useClients.ts
  useTaskFilters.ts

client/app/dashboard/agent/marketing/management/tasks/
  __tests__/
    useTaskFilters.test.ts
```

> The `__tests__` directory for `useTaskFilters` goes alongside the page under `tasks/__tests__/` (matching the existing test pattern at `management/__tests__/pages.test.tsx`). The component-level tests go in `client/components/management/tasks/__tests__/`.

---

## TDD Workflow

For each deliverable:

1. Write the tests listed above (they should all **fail**)
2. Run: `cd client && npx vitest run`
3. Implement the module
4. Run again — all tests should **pass**
5. Refactor if needed; keep green

---

## Key Constraints & Decisions

- **No type changes needed.** `RecurrenceFrequency` already includes `'yearly'` and `'custom'`. `GlobalTaskStatus` already includes `'in_review'`.
- **`getClientColor` is pure.** No React, no hooks, no side effects — it's a plain function. This makes it trivially testable.
- **`ClientBadge` uses inline styles** for the color-derived properties (background, text, border) because Tailwind cannot generate dynamic hex-color classes at runtime. Standard Tailwind utility classes (`rounded-full`, `text-xs`, etc.) are used for the structural styling.
- **`useTaskFilters` does not debounce internally.** The debounce for the search input lives in `TaskFilterBar.tsx` (section 02), which calls `updateSearch` after a 300ms delay. `useTaskFilters` simply stores whatever string is passed to `updateSearch`. The existing `useDebounce` hook at `client/lib/hooks/useDebounce.ts` should be used in `TaskFilterBar`.
- **`useClients` uses the `/api/clients/` endpoint.** Check `client/lib/api/` during implementation for an existing clients API function before writing a raw `fetch`. The interface only needs `id` and `name` for this feature.
- **`router.push` uses `{ scroll: false }`.** Filter updates should not scroll the page to the top.
