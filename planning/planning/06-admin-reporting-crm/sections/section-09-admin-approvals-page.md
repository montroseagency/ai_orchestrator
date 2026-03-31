# Section 09: Admin Approvals Page [IMPLEMENTED]

## Implementation Notes

**Status:** Complete — 10/10 tests passing

**Files created:**
- `client/app/dashboard/admin/approvals/page.tsx`
- `client/app/dashboard/admin/approvals/__tests__/ApprovalsPage.test.tsx`

**Files modified:**
- `client/components/dashboard/sidebar.tsx` — added Approvals nav item with badge, Settings group with Categories, useSocket for badge refresh

**Deviations from plan:**
- `columns` and action handlers wrapped in `useMemo`/`useCallback` to prevent unnecessary re-renders
- Added `submittingRef` to prevent concurrent approve/reject clicks
- Null guard on `updated_at` in both column render and drawer

---

## Overview

Build the admin approvals queue page at `client/app/dashboard/admin/approvals/page.tsx`. Admins see all tasks currently awaiting review (`status='in_review'`), can click a row to open a slide-out review panel, and approve or reject each task directly from that panel. The page stays up-to-date via 60-second polling and a Socket.IO event listener. The admin sidebar gains an "Approvals" nav item with a live pending-count badge.

**Dependency:** This section requires `section-05-approval-queue-api` to be complete. The three backend endpoints must exist before the frontend can be built:
- `GET /admin/approvals/` — list of in-review tasks
- `POST /admin/approvals/{task_id}/approve/`
- `POST /admin/approvals/{task_id}/reject/`

---

## Files to Create / Modify

| Action | Path |
|--------|------|
| Create | `client/app/dashboard/admin/approvals/page.tsx` |
| Create | `client/app/dashboard/admin/approvals/__tests__/ApprovalsPage.test.tsx` |
| Modify | `client/components/dashboard/sidebar.tsx` |

---

## Tests First

Test file: `client/app/dashboard/admin/approvals/__tests__/ApprovalsPage.test.tsx`

Use `renderWithQuery` from `client/test-utils/scheduling.tsx`. Mock `ApiService` and `useSocket` from `@/lib/socket-context`. Use `createMockApprovalTask` (factory defined in section-13 but stub it locally for this section — see below).

### Local mock factory stub

```typescript
// At top of test file — temporary until section-13 adds it to test-utils
function createMockApprovalTask(overrides?: Partial<any>) {
  return {
    id: 'task-1',
    title: 'Test Task',
    description: 'Task description',
    status: 'in_review',
    review_feedback: '',
    agent: { id: 'agent-1', name: 'Agent Smith' },
    client: { id: 'client-1', name: 'Nike', company: 'Nike Inc.' },
    task_category_detail: { name: 'Copywriting', color: '#6366F1' },
    updated_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2h ago
    ...overrides,
  };
}
```

### Test cases

```typescript
describe('ApprovalsPage', () => {
  it('fetches and renders table of in_review tasks on mount')
  // Mock GET /admin/approvals/ returning [createMockApprovalTask()]
  // Assert: table row with agent name "Agent Smith" is visible

  it('table shows Agent, Task, Client, Submitted columns')
  // Assert column headers are present

  it('clicking a row opens the review Drawer')
  // Click row → Drawer becomes visible (check for task title in drawer)

  it('Drawer shows task title, agent, client, description')
  // With drawer open, assert task title, agent name, client company, description text

  it('"Approve" button calls approve endpoint and removes row from table on success')
  // Mock POST /admin/approvals/task-1/approve/ → 200
  // Click Approve → row disappears from table, success toast fires

  it('"Reject" button is disabled when feedback textarea is empty')
  // Open drawer → Reject button has disabled attribute when textarea is empty

  it('"Reject" button calls reject endpoint with feedback and removes row on success')
  // Type feedback text → click Reject
  // Mock POST /admin/approvals/task-1/reject/ → 200
  // Row disappears from table, success toast fires

  it('shows error toast on approve/reject API failure')
  // Mock POST → 500 → error toast appears, row stays in table

  it('shows empty state when no pending approvals exist')
  // Mock GET /admin/approvals/ → []
  // Assert EmptyState component is rendered

  it('nav badge shows count of pending approvals')
  // With 3 mock tasks, badge shows "3"
})
```

---

## Implementation

### Page: `client/app/dashboard/admin/approvals/page.tsx`

```typescript
'use client';
// Imports: useState, useEffect, useCallback, useRef from 'react'
// ApiService from '@/lib/api'
// DataTable, Column from '@/components/ui/DataTable'
// Drawer from '@/components/ui/drawer'
// Button from '@/components/ui/button'
// Textarea from '@/components/ui/textarea'
// EmptyState from '@/components/ui/empty-state'
// Spinner from '@/components/ui/spinner'
// Badge from '@/components/ui/badge'
// { toast } from 'sonner'
// { useSocket } from '@/lib/socket-context'
// { Eye, CheckCircle2, XCircle } from 'lucide-react'
// formatDistanceToNow from 'date-fns'
```

#### Types

Define these inline in the page file (or in a co-located `types.ts`):

```typescript
interface ApprovalAgent {
  id: string;
  name: string;
}

interface ApprovalClient {
  id: string;
  name: string;
  company: string;
}

interface ApprovalTask {
  id: string;
  title: string;
  description: string;
  status: string;
  review_feedback: string;
  agent: ApprovalAgent;
  client: ApprovalClient;
  task_category_detail: { name: string; color: string } | null;
  updated_at: string;
}
```

#### State

```typescript
const [tasks, setTasks] = useState<ApprovalTask[]>([]);
const [isLoading, setIsLoading] = useState(true);
const [selectedTask, setSelectedTask] = useState<ApprovalTask | null>(null);
const [drawerOpen, setDrawerOpen] = useState(false);
const [feedback, setFeedback] = useState('');
const [isSubmitting, setIsSubmitting] = useState(false);
const [feedbackError, setFeedbackError] = useState('');
```

#### Data fetching

```typescript
const fetchApprovals = useCallback(async () => {
  /** Fetch GET /admin/approvals/ and update tasks state. */
}, []);
```

- Call `fetchApprovals()` in a `useEffect` on mount.
- Set up a 60-second polling interval with `setInterval` — clear it on unmount.
- Listen to Socket.IO `task_review_submitted` event via `useSocket` from `@/lib/socket-context`. On event: call `fetchApprovals()` to refresh. Register in `useEffect` with cleanup.

Pattern for socket listener (matches existing `useSchedulingEngine.ts` pattern):

```typescript
const { on, off } = useSocket();

useEffect(() => {
  const handler = () => { fetchApprovals(); };
  on('task_review_submitted', handler);
  return () => { off('task_review_submitted', handler); };
}, [on, off, fetchApprovals]);
```

#### DataTable columns

```typescript
const columns: Column<ApprovalTask>[] = [
  {
    key: 'agent',
    header: 'Agent',
    render: (row) => (
      // Avatar (use first letter of agent.name as fallback) + agent.name text
    ),
  },
  {
    key: 'title',
    header: 'Task',
    render: (row) => <span className="font-medium">{row.title}</span>,
  },
  {
    key: 'client',
    header: 'Client',
    render: (row) => row.client.company,
  },
  {
    key: 'updated_at',
    header: 'Submitted',
    render: (row) => formatDistanceToNow(new Date(row.updated_at), { addSuffix: true }),
  },
  {
    key: 'actions',
    header: '',
    render: (row) => (
      <Button variant="ghost" size="sm" onClick={() => openDrawer(row)}>
        <Eye className="w-4 h-4" />
      </Button>
    ),
  },
];
```

Pass `onRowClick={(row) => openDrawer(row)}` to `DataTable` as well (whole row is clickable).

Empty state config:

```typescript
emptyState={{
  title: 'No pending approvals',
  description: 'All tasks have been reviewed.',
  icon: <CheckCircle2 className="w-10 h-10 text-green-500" />,
}}
```

#### Drawer: review panel

Open with `openDrawer(task)` which sets `selectedTask`, clears `feedback` and `feedbackError`, sets `drawerOpen = true`.

Use `<Drawer isOpen={drawerOpen} onClose={closeDrawer} side="right" size="lg">`.

Drawer inner layout (prose, not full JSX):

1. **Header** — "Review: {selectedTask.title}" as `<h2>`, subtitle line showing "Agent: {agent.name} · Client: {client.company} · {category name if present}" as small muted text. Submitted time as another small line.
2. **Divider** (`<hr className="my-4" />`).
3. **Task Description** — label "Task Description" in semibold, then `<p>` with `selectedTask.description`.
4. **Divider**.
5. **Feedback** — label "Feedback (required for rejection)" in semibold. `<Textarea>` bound to `feedback` state. If `feedbackError` is non-empty, show inline error text below the textarea in red.
6. **Divider**.
7. **Action buttons row** — two buttons, full-width stacked on mobile or side-by-side:
   - `<Button onClick={handleApprove} disabled={isSubmitting}>Approve</Button>` — green / primary style
   - `<Button onClick={handleReject} disabled={isSubmitting || !feedback.trim()} variant="destructive">Reject & Return</Button>`

#### Action handlers

```typescript
async function handleApprove() {
  /**
   * POST /admin/approvals/{selectedTask.id}/approve/
   * On success: toast.success('Task approved'), removeTask(selectedTask.id), closeDrawer()
   * On error: toast.error('Failed to approve task')
   */
}

async function handleReject() {
  /**
   * Validate: if feedback.trim() is empty, set feedbackError and return early.
   * POST /admin/approvals/{selectedTask.id}/reject/ with body { feedback }
   * On success: toast.success('Task returned to agent'), removeTask(selectedTask.id), closeDrawer()
   * On error: toast.error('Failed to reject task')
   */
}

function removeTask(taskId: string) {
  setTasks(prev => prev.filter(t => t.id !== taskId));
}
```

Both handlers set `isSubmitting = true` at start and `isSubmitting = false` in a `finally` block.

#### API calls

Use `ApiService.post()` for approve and reject. Use `ApiService.get('/admin/approvals/')` for the fetch. The `ApiService` singleton handles auth headers automatically.

#### Pending count badge

Export a `usePendingApprovalsCount` hook (or inline it in the page) that returns `tasks.length`. The sidebar badge is handled in the sidebar section below.

---

### Sidebar update: `client/components/dashboard/sidebar.tsx`

The `adminNavGroups` object currently has `business`, `team`, `company`, `platform`, and `bottom` groups. Two changes are needed:

**1. Add Approvals to the `business` group:**

Add after the Analytics item in `adminNavGroups.business`:

```typescript
{
  href: '/dashboard/admin/approvals',
  label: 'Approvals',
  icon: <CheckCircle2 className="w-5 h-5" />,
  badge: pendingApprovalsCount > 0 ? String(pendingApprovalsCount) : undefined,
},
```

The `pendingApprovalsCount` is fetched in the sidebar via a lightweight `useEffect` that calls `GET /admin/approvals/` on mount and listens to `task_review_submitted` and `task_approved` / `task_rejected` Socket.IO events to refresh the count. This mirrors how `messageBadge` (total unread messages) is already handled in the sidebar for the Messages nav item.

**2. Add a new `settings` group** (render it between `platform` and `bottom`):

```typescript
settings: [
  {
    href: '/dashboard/admin/settings/categories',
    label: 'Categories',
    icon: <Tag className="w-5 h-5" />,
  },
],
```

Add `Tag` to the lucide-react imports at the top of the file.

In the JSX section where nav groups are rendered (around line 386+), add a render block for the new `settings` group alongside the existing ones.

---

## Key Technical Notes

### Using existing components correctly

- **`DataTable`** (`client/components/ui/DataTable.tsx`): Accepts `columns: Column<T>[]`, `data: T[]`, `isLoading`, `emptyState`, `onRowClick`, `getRowKey`. The `render` function on a `Column` receives `(row: T, index: number)`. The generic constraint is `T extends Record<string, unknown>` — `ApprovalTask` satisfies this.

- **`Drawer`** (`client/components/ui/drawer.tsx`): Props are `isOpen`, `onClose`, `children`, `side` (default `'right'`), `size` (`'sm'|'md'|'lg'|'xl'`; use `'lg'` for the review panel), `className`. The drawer handles ESC key and body scroll locking internally — do not duplicate this logic.

- **`Textarea`** (`client/components/ui/textarea.tsx`): Standard controlled textarea. Bind to `feedback` state.

- **`toast`** from `sonner`: Call `toast.success('...')` and `toast.error('...')`. Do not import from any other toast library.

- **`useSocket`** from `@/lib/socket-context` (not from `@/lib/hooks/useSocket`): The socket context provides the shared connection. The `on` / `off` helpers register and deregister event handlers.

### Polling interval

```typescript
useEffect(() => {
  const interval = setInterval(fetchApprovals, 60_000);
  return () => clearInterval(interval);
}, [fetchApprovals]);
```

### Race condition on approve/reject

If two admins have the page open simultaneously and one approves a task, the other's page will either:
- Get a 409 response (task no longer `in_review`) — show `toast.error('This task has already been reviewed.')` for 409 specifically, and close the drawer.
- Or receive the real-time `task_review_submitted` / next poll and see the task removed.

Handle HTTP 409 explicitly in both `handleApprove` and `handleReject`.

### `formatDistanceToNow`

`date-fns` is available in the project. Import: `import { formatDistanceToNow } from 'date-fns'`. Use `{ addSuffix: true }` for "2 hours ago" style.

---

## Acceptance Criteria

1. Page renders at `/dashboard/admin/approvals` without errors.
2. On mount, fetches `GET /admin/approvals/` and displays tasks in a `DataTable`.
3. Polling refreshes the table every 60 seconds.
4. Socket.IO `task_review_submitted` event triggers an immediate refresh.
5. Clicking a row (or the eye icon button) opens the `Drawer`.
6. Drawer displays: task title, agent name, client company, category, submitted time, task description, feedback textarea, Approve button, Reject button.
7. Reject button is disabled while the feedback textarea is empty.
8. Successful approve: success toast, drawer closes, task row removed from table.
9. Successful reject: success toast, drawer closes, task row removed from table.
10. API failure: error toast shown, drawer remains open, row stays in table.
11. Empty state rendered when no tasks are pending.
12. Admin sidebar shows "Approvals" link with a badge indicating pending count (hidden when 0).
13. All 10 test cases pass.
