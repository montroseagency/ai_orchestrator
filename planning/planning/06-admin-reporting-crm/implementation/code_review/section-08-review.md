# Code Review — Section 08: ClientDetailHub Frontend Component

**Reviewer:** Senior Code Review
**Date:** 2026-03-30
**Branch:** section-08 diff
**Scope:** `ClientDetailHub`, all four tab components, `ExportReportModal`, two custom hooks, shared CRM types, and the accompanying test suite.

---

## Summary

The overall implementation is solid. The component architecture is well-decomposed, the XSS mitigation for markdown rendering is thoughtful, and the test suite covers the main happy paths with appropriate mocking strategies. There are no critical security vulnerabilities, but there are several correctness bugs and architectural gaps that should be addressed before shipping.

**Finding counts:**
- CRITICAL: 2
- MAJOR: 6
- MINOR: 7
- NITPICK: 5

---

## 1. Correctness and Completeness

### [CRITICAL] `OverviewTab` — `today` and `defaultStart` are recomputed on every render

**File:** `client/components/portal/crm/tabs/OverviewTab.tsx`, lines ~1231–1234

```tsx
// Inside the component body — recomputed every render
const today = format(new Date(), 'yyyy-MM-dd')
const defaultStart = format(subDays(new Date(), 90), 'yyyy-MM-dd')
const { data: report } = useClientReport(clientId, defaultStart, today)
```

`today` and `defaultStart` are plain `const` variables computed at the top of the function body. On every parent-triggered re-render (e.g., tab switch back to Overview) these values are recomputed. Because the computed strings feed directly into `useClientReport`'s `queryKey`, a new query will be keyed on the exact ISO string — this is fine if the date hasn't changed, but across a midnight boundary the key changes mid-session, causing a refetch and a brief flash of stale data. More critically, `new Date()` is called twice (once for `today`, once inside `subDays`) producing two `Date` instances. If `OverviewTab` is ever wrapped in a `React.memo` comparison or the parent passes stable props, the query key inconsistency can cause subtle cache-miss loops.

**Fix:** Stabilise both values with `useMemo` (or compute them once outside the component as constants if they truly never need to update during a session). At minimum, capture a single `new Date()` instance:

```tsx
const { startDate, endDate } = useMemo(() => {
  const now = new Date()
  return {
    startDate: format(subDays(now, 90), 'yyyy-MM-dd'),
    endDate: format(now, 'yyyy-MM-dd'),
  }
}, []) // empty deps — intentionally fixed at mount time
```

---

### [CRITICAL] `ExportReportModal` — URL parameters are not encoded

**File:** `client/components/portal/crm/export/ExportReportModal.tsx`, lines ~952–954

```tsx
const url = `/agent/clients/${clientId}/report/export/?format=${format}&start_date=${startDate}&end_date=${endDate}`
window.location.href = url
```

`clientId`, `startDate`, and `endDate` are interpolated directly into the URL without `encodeURIComponent`. While `startDate`/`endDate` are controlled date strings that are safe in practice, `clientId` could theoretically contain characters that break the URL (particularly if client IDs ever come from UUIDs with special chars or from a query parameter). More importantly, this pattern sets a dangerous precedent. Additionally, `format` here shadows the imported `format` function from `date-fns` — while it works because the local `useState` shadows the import in this file, it is confusing and a latent bug if the import is ever used elsewhere in this file.

**Fix:**
1. Rename the state variable: `const [exportFormat, setExportFormat] = useState<'csv' | 'pdf'>('csv')`
2. Encode parameters: use `encodeURIComponent` for each interpolated value, or use `URLSearchParams`.

```tsx
const params = new URLSearchParams({ format: exportFormat, start_date: startDate, end_date: endDate })
const url = `/agent/clients/${encodeURIComponent(clientId)}/report/export/?${params}`
```

---

### [MAJOR] `ClientDetailHub` — stale client data when `clientProp` changes identity

**File:** `client/components/portal/crm/ClientDetailHub.tsx`, lines ~123–133

```tsx
const { data: fetchedClient } = useQuery<ClientInfo>({
  queryKey: ['client', clientId],
  queryFn: () => api.getClient(clientId),
  enabled: !!clientId && !clientProp,
  staleTime: 300_000,
})

const client = clientProp
  ? { id: clientId, ...clientProp }
  : fetchedClient
```

The `enabled` flag is `!clientProp`. If a parent component starts passing `clientProp` and later stops (e.g., navigating from a list where client data is in-cache to a direct deep-link), the query will never fire because `clientProp` was truthy at mount time and React Query's `enabled` does not retroactively re-enable a disabled query unless the component remounts. The merged `client` object would be `undefined` on the second render, causing the header to display `—` even though the fetch key has data in the cache.

**Fix:** Remove the `!clientProp` guard from `enabled` and instead let TanStack Query serve the cached result instantly when the key is warm. The `clientProp` fallback pattern on line 130 is fine for the initial render, but the query should always be enabled so stale background data can be refreshed.

---

### [MAJOR] `TasksTab` — `storageKey` changes when `agentType` prop changes at runtime

**File:** `client/components/portal/crm/tabs/TasksTab.tsx`, lines ~1359–1367

```tsx
const storageKey = `tasks-view-${agentType}`

const [view, setView] = useState<'kanban' | 'list'>(() => {
  if (typeof window !== 'undefined') {
    const saved = localStorage.getItem(storageKey)
    ...
  }
  return 'kanban'
})
```

The `useState` initialiser only runs once at mount. If `agentType` ever changes (e.g., the parent re-renders with a different value due to routing or context), the `storageKey` variable updates but the `useState` value remains locked to the original localStorage key. This is a silent stale-read bug. The `handleViewChange` function will also write to the new key while reads still come from the old key on the next mount.

**Fix:** Either accept this as intentional (document it) and use `useEffect` to sync on `agentType` change, or use a `useRef` to capture the key at mount:

```tsx
const storageKeyRef = useRef(`tasks-view-${agentType}`)
```

---

### [MAJOR] `TimeCapacityTab` — `DATE_RANGE_OPTIONS` array is recreated on every render

**File:** `client/components/portal/crm/tabs/TimeCapacityTab.tsx`, lines ~1492–1497

```tsx
// Inside the component body
const DATE_RANGE_OPTIONS: { id: DateRange; label: string }[] = [
  { id: 'last-30d', label: 'Last 30d' },
  ...
]
```

This constant array is defined inside the component, causing a new array reference on every render. This will needlessly invalidate any `useMemo`/`useCallback` dependencies downstream and can cause unnecessary re-renders of the button group if it is ever extracted. It should be defined as a module-level constant (alongside `CHART_COLORS` which is correctly placed at module level).

---

### [MAJOR] `MarketingPlanTab` — `isBlock` code-detection heuristic is incorrect

**File:** `client/components/portal/crm/tabs/MarketingPlanTab.tsx`, lines ~1125–1134

```tsx
const isBlock = !!(props as { node?: { type?: string } }).node
if (match && isBlock) {
```

The `isBlock` check tests whether a `node` prop exists on the rendered element. In `react-markdown` v9+/v10, the `node` prop is always passed to custom components (it represents the AST node), so `isBlock` will be `true` for both inline and block code elements. The correct way to differentiate block code from inline code is to check whether the parent node's type is `element` and its tag is `pre`, or — more simply — whether the `className` contains a language identifier (which only block fences receive from remark-gfm). The existing `match && isBlock` condition accidentally works when there is a language tag, but will fail silently for fenced blocks without a language tag, rendering them as `<code>` instead of the `CodeBlock` component.

**Fix:** Use the well-known `inline` prop convention from react-markdown v8 (if that API is available), or detect block code via the parent node type:

```tsx
const isInline = !(props as any).node?.position || (props as any).node?.type === 'inlineCode'
if (!isInline && match) { /* use CodeBlock */ }
```

Alternatively, wrap the `code` renderer to check `node.tagName !== 'code'` vs the parent being `pre`.

---

### [MAJOR] `OverviewTab` — activity list sliced redundantly

**File:** `client/components/portal/crm/tabs/OverviewTab.tsx`, lines ~1237–1244 and ~1311

The API call already requests `&limit=10`:
```tsx
queryFn: () => api.request<AgentGlobalTask[]>(
  `/agent/tasks/?client=${clientId}&ordering=-updated_at&limit=10`
),
```

Then at render time it is sliced again:
```tsx
{activityTasks.slice(0, 10).map(...)}
```

This is harmless but inconsistent — it implies distrust of the API's pagination, which is fine as a safety net but should be a named constant rather than a magic `10` repeated in two places. At worst, if the API changes the default limit this silently mismatches.

---

### [MAJOR] `ClientDetailHub` — missing `isError` / error boundary handling

**File:** `client/components/portal/crm/ClientDetailHub.tsx`

None of the four tabs or the hub itself surface a UI error state for failed queries. TanStack Query's `isError` and `error` fields are available from all hooks but unused. A user whose network drops or whose session expires will see the loading skeleton indefinitely (if the query is still loading) or a blank panel (once the query settles to an error state). Given this is an admin/agent-facing CRM hub, missing error feedback is a significant UX gap.

**Fix:** At minimum, check `isError` in `useClientReport`, `useClientMarketingPlan`, and the activity query, and render an `<alert>` or `<InlineError>` component (both available in `client/components/ui/`).

---

## 2. Security

### [MINOR] `MarketingPlanTab` — sanitize schema disallows `img` but permits `a[href]` with arbitrary protocols

**File:** `client/components/portal/crm/tabs/MarketingPlanTab.tsx`, lines ~1079–1082

```tsx
const sanitizeSchema = {
  ...defaultSchema,
  tagNames: (defaultSchema.tagNames ?? []).filter((tag) => tag !== 'img'),
}
```

The custom schema correctly strips `<img>` elements. However, `rehype-sanitize`'s `defaultSchema` permits `<a href>` with any protocol including `javascript:` in some versions (the protocol check was tightened only in later releases). Strategy notes are agent-authored content, but if the platform ever allows clients to edit their own strategy notes, a `javascript:` href would survive sanitisation in older rehype-sanitize versions.

**Recommendation:** Explicitly add a protocol allowlist for `a[href]`:

```ts
const sanitizeSchema = {
  ...defaultSchema,
  tagNames: (defaultSchema.tagNames ?? []).filter((tag) => tag !== 'img'),
  attributes: {
    ...defaultSchema.attributes,
    a: [['href', /^https?:/]],
  },
}
```

This is belt-and-suspenders given the current trust model, but prudent.

---

### [MINOR] `ExportReportModal` — download via `window.location.href` bypasses CSRF

**File:** `client/components/portal/crm/export/ExportReportModal.tsx`, line ~952

Using `window.location.href` triggers a GET request which will include session cookies but no CSRF token header. If the Django export endpoint requires a CSRF token (standard in Django for non-safe methods), this will work only because the endpoint is a GET. The concern is that this endpoint effectively performs an authenticated data export without CSRF protection. If the endpoint is ever changed to POST (e.g., for large reports that exceed URL limits), this pattern will silently break.

**Recommendation:** Document that the export endpoint is intentionally GET-only and add a backend comment to enforce this. Alternatively, use `<a href={url} download>` rendered via a hidden ref and `.click()` to be explicit about intent.

---

### [MINOR] `useClientReport` — query parameters are not encoded

**File:** `client/components/portal/crm/hooks/useClientReport.ts`, line ~1054

```tsx
queryFn: () =>
  api.request<ClientReportResponse>(
    `/agent/clients/${clientId}/report/?start_date=${startDate}&end_date=${endDate}`
  ),
```

Same issue as `ExportReportModal` — `clientId` is interpolated without `encodeURIComponent`. Same pattern appears in `useClientMarketingPlan`.

---

## 3. React / TypeScript Best Practices

### [MINOR] `ClientDetailHub` — tab switching unmounts/remounts all tab components

**File:** `client/components/portal/crm/ClientDetailHub.tsx`, lines ~1181–1193

```tsx
{activeTab === 'overview' && <OverviewTab ... />}
{activeTab === 'tasks' && <TasksTab ... />}
{activeTab === 'marketing-plan' && <MarketingPlanTab ... />}
{activeTab === 'time-capacity' && <TimeCapacityTab ... />}
```

Every tab switch fully unmounts the inactive tabs. `TasksTab` stores `view`, `selectedIds`, and `editingTask` in local state. All of this state is lost when the user switches away and back. For the `TimeCapacityTab`, the selected `dateRange` and `customStart`/`customEnd` are also lost. This is particularly jarring if a user sets a custom date range, switches tabs to check a task, and returns to find the date picker reset.

**Fix:** Use `display: none` / CSS `hidden` to keep tabs mounted, or lift the per-tab UI state up to `ClientDetailHub` so it survives re-mounts. The project already has `tabs.tsx` in `client/components/ui/` — check whether it handles this.

---

### [MINOR] `TasksTab` — `selectedIds` state is declared but never passed to `TasksKanbanView`

**File:** `client/components/portal/crm/tabs/TasksTab.tsx`, lines ~1371 and ~1406

```tsx
const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
...
<TasksKanbanView tasks={tasks} onTaskEdit={handleTaskEdit} />
// selectedIds not passed ↑
```

`selectedIds` and `setSelectedIds` are declared but only `TasksListView` receives them. `TasksKanbanView` does not receive selection state, which is likely intentional if kanban doesn't support multi-select, but then the state declaration should be conditional or documented. If kanban does need selection in a future iteration, the state should be passed now.

---

### [MINOR] `TimeCapacityTab` — `today` is recomputed twice

**File:** `client/components/portal/crm/tabs/TimeCapacityTab.tsx`, lines ~1483–1485

```tsx
const [dateRange, setDateRange] = useState<DateRange>('last-90d')
const today = format(new Date(), 'yyyy-MM-dd')
const [customStart, setCustomStart] = useState(format(subDays(new Date(), 90), 'yyyy-MM-dd'))
const [customEnd, setCustomEnd] = useState(today)
```

`today` is computed on every render. While the `useState` initialisers only run once, `today` itself is recalculated on each render pass and fed to `deriveRange` which calls `format(new Date(), ...)` again internally. Three separate `new Date()` calls exist across this component. At minimum, `today` should be a module constant or a `useMemo` with `[]` deps.

---

### [MINOR] `MarketingPlanTab` — unsafe `as` cast on `props`

**File:** `client/components/portal/crm/tabs/MarketingPlanTab.tsx`, line ~1125

```tsx
const isBlock = !!(props as { node?: { type?: string } }).node
```

Casting `props` inline with `as` to access a duck-typed `node` property is fragile. It bypasses TypeScript's component prop types and will silently return `undefined` if react-markdown's API changes. The `ReactMarkdown` component's `code` renderer component type from `@types/mdast` / `react-markdown` provides proper typing for the `node` property. Use the correct type import.

---

### [MINOR] `OverviewTab` — `ClientInfo` interface is duplicated

**File:** `client/components/portal/crm/tabs/OverviewTab.tsx` (defines `ClientInfo`) and `client/components/portal/crm/ClientDetailHub.tsx` (defines its own `ClientInfo`)

Both files define a local `ClientInfo` interface with slightly different shapes (OverviewTab adds `email`, `phone`, `created_at`). Since `client/lib/types/crm.ts` was added in this diff, `ClientInfo` should be centralised there and imported in both files. This will become a maintenance issue when the client object shape changes.

---

### [NITPICK] `ClientDetailHub` — `client` prop type is inconsistently defined

**File:** `client/components/portal/crm/ClientDetailHub.tsx`, lines ~109–110

```tsx
client?: { name: string; company: string; status: string }
```

The prop omits `id`, but the merged value on line 131 adds it:
```tsx
const client = clientProp ? { id: clientId, ...clientProp } : fetchedClient
```

This is fine functionally, but the merged type `{ id: string; name: string; company: string; status: string }` is not reflected in the prop type. A TypeScript reader has to trace the merge to understand the runtime shape. Consider defining a `ClientBasicInfo` type in `crm.ts` and using it consistently.

---

### [NITPICK] `ExportReportModal` — `format` state variable shadows `date-fns` import name

**File:** `client/components/portal/crm/export/ExportReportModal.tsx`

There is no `date-fns` import in `ExportReportModal.tsx`, so the shadow is currently benign. However, the variable name `format` conflicts with the ubiquitous `date-fns/format` import that is used everywhere else in this feature. If a future maintainer needs to add date formatting to this file, they will encounter a confusing collision. Rename to `exportFormat`.

---

### [NITPICK] `TimeCapacityTab` — `PieChart` used but described as "donut"

**File:** `client/components/portal/crm/tabs/TimeCapacityTab.tsx`, lines ~1591–1613

The comment says "Category donut chart" and `innerRadius={35}` is set on `<Pie>`, which is correct for a donut. The chart title in the UI is "Hours by Category". The test ID is `pie-chart`. The naming is inconsistent across comment, code and test. This is a nitpick but choose one name and use it consistently.

---

### [NITPICK] `TimeCapacityTab` — custom date inputs lack `aria-label`

**File:** `client/components/portal/crm/tabs/TimeCapacityTab.tsx`, lines ~1537–1549

```tsx
<input type="date" value={customStart} onChange={...} ... />
<span>→</span>
<input type="date" value={customEnd} onChange={...} ... />
```

Neither date input has an `aria-label` or `<label>` association. Screen readers will announce these as unlabelled inputs.

---

### [NITPICK] Test file — `beforeEach` is imported but unused in `ClientDetailHub.test.tsx`

**File:** `client/components/portal/crm/__tests__/ClientDetailHub.test.tsx`, line ~204

```tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
```

`beforeEach` is imported but no `beforeEach` block is defined anywhere in the file. The `render` import from `@testing-library/react` is also unused — `renderWithQuery` is used instead. Clean up unused imports.

---

## 4. Performance

### [MINOR] `OverviewTab` — two independent queries trigger two loading spinners merged into one

**File:** `client/components/portal/crm/tabs/OverviewTab.tsx`, lines ~1246–1260

```tsx
const isLoading = reportLoading || activityLoading

if (isLoading) {
  return <Skeleton ... />
}
```

The combined `isLoading` guard means the full skeleton is shown until both `useClientReport` and the activity query have resolved. If one is fast (cached) and one is slow, the user sees the skeleton for longer than necessary. Consider rendering the stat cards as soon as `report` is available and showing a smaller inline skeleton for the activity feed independently.

---

## 5. Test Quality and Coverage Gaps

### [MAJOR] No test for `ClientDetailHub` with `clientProp` absent (fetch path)

**File:** `client/components/portal/crm/__tests__/ClientDetailHub.test.tsx`

All tests pass `client={clientProp}`, meaning the `useQuery` fetch path (`enabled: !!clientId && !clientProp`) is never exercised. The test for the fetched-client display path is missing entirely. Given the `enabled` flag bug identified above, this gap means the bug would not be caught by the test suite.

**Recommendation:** Add a test that renders `<ClientDetailHub clientId="client-1" agentType="marketing" />` (no `client` prop), waits for the mocked `api.getClient` to resolve, and asserts that the header shows "Acme Corp".

---

### [MAJOR] No test for error states in any tab

None of `OverviewTab.test.tsx`, `TimeCapacityTab.test.tsx`, or `MarketingPlanTab.test.tsx` test the `isError` state. Since error UI is not implemented (see finding above), this gap is doubly concerning — the error path is neither implemented nor tested.

---

### [MAJOR] `TasksTab` test — test description and assertion are contradictory

**File:** `client/components/portal/crm/__tests__/TasksTab.test.tsx`, lines ~729–733

```tsx
it('agentType="developer" — same task list without "Project Milestones"... false', async () => {
  ...
  expect(screen.getByText('Project Milestones')).toBeInTheDocument()
})
```

The test description says `without "Project Milestones"... false` but the assertion is `getByText('Project Milestones').toBeInTheDocument()` — i.e., it asserts the section IS present. The test name is deeply misleading. This test would pass for the wrong reasons if the conditional was accidentally inverted. Rename the test to clearly state: `agentType="developer" renders "Project Milestones" section`.

---

### [MINOR] `ExportReportModal` tests — no test for `open={false}` (modal hidden)

**File:** `client/components/portal/crm/__tests__/ExportReportModal.test.tsx`

All tests pass `open: true`. There is no test confirming that the modal is not rendered (or not visible) when `open={false}`. Given that `Modal` from the shared UI library controls open/close, this is low risk, but coverage is incomplete.

---

### [MINOR] `MarketingPlanTab` XSS test — assertion only checks for absent `<script>` element, not for script execution

**File:** `client/components/portal/crm/__tests__/MarketingPlanTab.test.tsx`, lines ~484–497

```tsx
expect(container.querySelector('script')).toBeNull()
```

Checking that no `<script>` tag appears in the DOM is necessary but not sufficient. The test does not verify that `onerror`, `onload`, or other event-handler XSS vectors (e.g., `<img onerror="...">`) are stripped. Given that `img` is already blocked by the sanitize schema, this is largely moot, but an `on*` attribute test would give higher confidence.

---

### [MINOR] `TimeCapacityTab` — date-range button tests rely on call-count ordering

**File:** `client/components/portal/crm/__tests__/TimeCapacityTab.test.tsx`, lines ~820–836

```tsx
const calls = vi.mocked(mockUseReport).mock.calls
const lastCall = calls[calls.length - 1]
expect(lastCall[0]).toBe('client-1')
expect(lastCall[1]).not.toBe(calls[0][1])
```

This test relies on `mockUseReport` being called at least twice (initial render + after click) and that the last call has a different `startDate` than the first. This is fragile: if React batches renders differently, or if TanStack Query's `useQuery` triggers extra calls in future versions, the index arithmetic breaks. Prefer a direct assertion on the expected date string value rather than "different from first call":

```tsx
const expectedStart = format(subDays(new Date(), 30), 'yyyy-MM-dd')
expect(lastCall[1]).toBe(expectedStart)
```

---

## 6. Miscellaneous

### [MINOR] `package.json` — `react-markdown` and `rehype-sanitize` not shown as production dependencies

The diff shows entries in `package-lock.json` but the corresponding `package.json` changes are not visible in this diff. Confirm that both `react-markdown` and `rehype-sanitize` were added to `dependencies` (not `devDependencies`) in `package.json`, since they are used in production render paths.

---

### [NITPICK] `crm.ts` — `ReportTaskItem.status` typed as `string`, not a union

**File:** `client/lib/types/crm.ts`, line ~1703

```ts
export interface ReportTaskItem {
  status: string
```

All other status fields in the codebase use a `GlobalTaskStatus` union type (from `lib/types/scheduling`). Using `string` here breaks autocompletion and type safety for any code that branches on task status values from report data.

---

## Overall Verdict

Ship-blocking issues (CRITICAL) are limited to two concrete bugs:
1. URL parameters not encoded in `ExportReportModal` (and `useClientReport`/`useClientMarketingPlan` hooks), with the added variable-name shadow for `format`.
2. Unstable date computation in `OverviewTab` that can cause silent query-key churn.

The MAJOR findings around error handling, stale state on tab switch, and the misleading test description should be addressed in the same PR. The remaining MINOR and NITPICK items can be handled in a follow-up.
