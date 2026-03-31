# Code Review: Section 09 — Admin Approvals Page

**Files reviewed:**
- `client/app/dashboard/admin/approvals/page.tsx`
- `client/app/dashboard/admin/approvals/__tests__/ApprovalsPage.test.tsx`
- `client/components/dashboard/sidebar.tsx` (badge + nav additions)

---

## CRITICAL

### C-1: Sidebar makes a full list fetch just to get a count — no auth guard on the interval
**File:** `sidebar.tsx` lines 535–555

The sidebar calls `/admin/approvals/` on mount (and on every socket event) to count items. This endpoint returns full task objects purely to count them. There is no polling interval cleanup tied to role change — if `user.role` becomes non-admin mid-session (e.g., token refresh returns different role), the effect has already registered socket handlers that reference the stale `fetchCount` closure and will keep firing. The `useEffect` dependency array is `[user?.role, on, off]` which does guard the initial registration, but socket `on/off` reference equality is not guaranteed stable across re-renders depending on the socket context implementation — confirm `on` and `off` are memoized in `socket-context`, otherwise this effect fires on every render and accumulates duplicate socket listeners.

**Fix:** Add a `/admin/approvals/count/` endpoint that returns `{ count: number }`, and confirm `on`/`off` are wrapped in `useCallback` in `socket-context`.

---

### C-2: No server-side role enforcement visible in diff — page is client-only guarded
**File:** `page.tsx`

The page has no route-level auth check (no `redirect` in a Server Component, no middleware guard shown). If Next.js middleware does not protect `/dashboard/admin/*`, a non-admin user who knows the URL can load the page and the API will be the only gate. This is acceptable only if the Django endpoint enforces `IsAdminUser` — that is not visible in this diff and must be confirmed.

**Action required:** Verify `AdminApprovalViewSet` (or equivalent) has `permission_classes = [IsAdminUser]` and that Next.js middleware blocks the route for non-admin roles.

---

## MAJOR

### M-1: Stale `selectedTask` closure in `handleApprove` / `handleReject`
**File:** `page.tsx` lines 301–347

Both handlers capture `selectedTask` from the closure at call time. If a socket event fires `fetchApprovals()` between the user opening the drawer and clicking Approve, `tasks` is refreshed but `selectedTask` is not updated (it's a separate state reference). This means the user could approve a stale snapshot of the task — the task ID remains correct so the API call itself is safe, but any optimistic UI based on `selectedTask` data could reflect outdated info. More concretely: if the task was already reviewed by another admin and removed from the list via `fetchApprovals`, `selectedTask` still holds the old object and the user sees the drawer with stale data.

**Fix:** After `fetchApprovals()` completes, add a reconciliation step: if `selectedTask` is set and the refreshed list no longer contains its ID, close the drawer automatically. Example:

```ts
const refreshedTask = data.find(t => t.id === selectedTask?.id);
if (selectedTask && !refreshedTask) {
  closeDrawer();
  toast.info('This task was already reviewed.');
}
```

---

### M-2: Double-click / concurrent submit not fully blocked
**File:** `page.tsx` lines 301–347

`isSubmitting` is set to `true` at the start of `handleApprove`/`handleReject` and cleared in `finally`. The Approve and Reject buttons are both disabled while `isSubmitting` is true, which is correct. However, both `handleApprove` and `handleReject` are plain `async function` declarations — they are recreated every render. If the user clicks Approve and then Reject before the first `await` resolves, two concurrent inflight requests can exist because the `isSubmitting` guard depends on React having flushed the state update (it may not have in the same event-loop tick).

**Fix:** Wrap handlers in `useCallback` with `isSubmitting` in the dependency list and add an early return guard that checks a `ref` rather than state:

```ts
const isSubmittingRef = useRef(false);
// at top of each handler:
if (isSubmittingRef.current) return;
isSubmittingRef.current = true;
// in finally: isSubmittingRef.current = false;
```

---

### M-3: `columns` array recreated on every render
**File:** `page.tsx` lines 349–395

The `columns` array is defined inside the component body without `useMemo`. Each render produces a new array with new inline `render` functions. If `DataTable` uses `React.memo` or does shallow-equality checks on `columns` to avoid re-renders, this defeats that optimization and will cause the entire table to re-render on every keystroke in the feedback `Textarea`.

**Fix:** Wrap in `useMemo`:

```ts
const columns = useMemo<Column<ApprovalTask>[]>(() => [...], []);
```

Since none of the render functions close over component state (they call `openDrawer` which is also not memoized), also wrap `openDrawer` in `useCallback`.

---

### M-4: `updated_at` date parsing can throw silently
**File:** `page.tsx` lines 376–379, 438–439

`formatDistanceToNow(new Date(row.updated_at), ...)` will render `"Invalid date"` if the server returns a malformed or null `updated_at`. There is no guard. In the table this shows as garbled text; inside the drawer it also calls `new Date(selectedTask.updated_at)` with no try/catch.

**Fix:** Add a utility wrapper:

```ts
function safeFormatDistance(dateStr: string) {
  const d = new Date(dateStr);
  return isNaN(d.getTime()) ? '—' : formatDistanceToNow(d, { addSuffix: true });
}
```

---

## MINOR

### m-1: `task_category_detail.color` is fetched but never rendered
**File:** `page.tsx` lines 229, 435

The type includes `color: string` on `task_category_detail` and the mock factory populates it, but the page never uses the color anywhere (no colored dot, no badge styling). Either render it as a colored badge or remove it from the type and mock to avoid confusion about intent.

---

### m-2: Approval badge in sidebar does not cap at a display maximum
**File:** `sidebar.tsx` line 564

`messageBadge` caps at `'9+'` for large unread counts. `approvalsBadge` does not — it renders the raw count as a string. With many pending approvals (e.g., 127) the badge may overflow its container depending on the `NavItem` badge rendering.

**Fix:** Apply the same cap: `pendingApprovalsCount > 99 ? '99+' : String(pendingApprovalsCount)`.

---

### m-3: Polling interval does not back off on repeated failures
**File:** `page.tsx` lines 273–276

The 60-second interval calls `fetchApprovals` unconditionally. If the server is down, it will hammer the endpoint every 60 seconds with no exponential backoff or failure counter. Minor for a low-traffic admin page but worth noting.

---

### m-4: `feedbackError` uses raw inline `<p>` instead of `<InlineError>`
**File:** `page.tsx` line 467

`InlineError` is imported (line 212) and used for `fetchError`, but `feedbackError` renders a raw `<p className="text-xs text-red-600 mt-1">`. Inconsistent — use `<InlineError>` for both.

---

### m-5: `navGroups` cast to `adminNavGroups` type
**File:** `sidebar.tsx` line 447

`(navGroups as typeof adminNavGroups).settings` — this cast is needed because the `navGroups` type is not statically inferred to include `settings`. This will silently break if the agent/client branch also tries to access `.settings`. Use a discriminated type or explicitly type `adminNavGroups` so the compiler catches misuse without a cast.

---

## NITPICK

### n-1: `& Record<string, unknown>` on `ApprovalTask` type is overly permissive
**File:** `page.tsx` line 239

The intersection with `Record<string, unknown>` exists to satisfy some indexing pattern but is not explained. It weakens TypeScript's type safety for the entire `ApprovalTask` type. Remove it unless a specific DataTable prop requires it, and update `DataTable`'s generic constraint instead.

---

### n-2: Test uses `fireEvent` where `userEvent` is more appropriate
**File:** `ApprovalsPage.test.tsx` lines 112, 142, 147, 165

`fireEvent.change` and `fireEvent.click` bypass browser event simulation that `@testing-library/user-event`'s `userEvent` provides (focus, blur, keyboard events). For the textarea change test in particular, `userEvent.type` would more accurately simulate real user input and catch potential issues with `onChange` handlers that depend on focus state.

---

### n-3: Test for "row still visible after error" checks by text, not by task count
**File:** `ApprovalsPage.test.tsx` lines 168–170

The assertion `expect(screen.getByText('Agent Smith')).toBeInTheDocument()` proves the text exists but not that the full row is present in the table. A more robust assertion would query the table row directly.

---

### n-4: No test for the 409 (already reviewed) conflict path
**File:** `ApprovalsPage.test.tsx`

The 409-conflict branch in `handleApprove` and `handleReject` (which shows an error toast and removes the row) has no test coverage.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 2 |
| MAJOR    | 4 |
| MINOR    | 5 |
| NITPICK  | 4 |

The most urgent items are **C-2** (confirm backend enforces admin-only access on all approval endpoints) and **M-1** (stale drawer state when a concurrent review occurs). The sidebar double-fetch pattern (**C-1**) is a performance and correctness risk that warrants a dedicated count endpoint.
