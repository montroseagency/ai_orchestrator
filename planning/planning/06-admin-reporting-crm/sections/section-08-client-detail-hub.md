# Section 08 — ClientDetailHub Frontend Component [IMPLEMENTED]

## Implementation Notes

**Status:** Complete — 42/42 tests passing

**Actual files created:**
- `client/lib/types/crm.ts` — CRM type definitions
- `client/components/portal/crm/ClientDetailHub.tsx`
- `client/components/portal/crm/tabs/OverviewTab.tsx`
- `client/components/portal/crm/tabs/TasksTab.tsx`
- `client/components/portal/crm/tabs/MarketingPlanTab.tsx`
- `client/components/portal/crm/tabs/TimeCapacityTab.tsx`
- `client/components/portal/crm/hooks/useClientReport.ts`
- `client/components/portal/crm/hooks/useClientMarketingPlan.ts`
- `client/components/portal/crm/export/ExportReportModal.tsx`
- `client/components/portal/crm/__tests__/` (6 test files + factories.ts)

**Modified files:**
- `client/components/management/tasks/TaskFilterBar.tsx` — added `showClientFilter?: boolean` prop
- `client/package.json` — added `react-markdown` + `rehype-sanitize`

**Deviations from plan:**
- `date-picker.tsx` was empty; used native `<input type="date">` in TimeCapacityTab instead
- Modal prop is `isOpen` not `open` (matches existing Modal component API)
- `rehypeSanitize` configured with custom schema stripping `img` tags to prevent external URL tracking
- Mock factories moved to `__tests__/factories.ts` (not inline in test files) to prevent vitest module registry pollution
- Error UI (`InlineError`) added to OverviewTab, MarketingPlanTab, TimeCapacityTab on query failure (added during code review)

---

## Overview

This section builds the shared `ClientDetailHub` component tree used by both the marketing agent and developer agent client detail pages. It is a 4-tab CRM hub backed by two new React Query hooks and includes a modal for report exports.

**Dependencies (must be complete before starting this section):**
- `section-03-client-report-api` — `GET /agent/clients/{id}/report/` endpoint must exist
- `section-04-marketing-plan-api` — `GET /agent/clients/{id}/marketing-plan/` endpoint must exist

**Blocks:**
- `section-12-agent-page-integration` — wires `ClientDetailHub` into the existing pages

---

## New Files to Create

```
client/components/portal/crm/
  ClientDetailHub.tsx
  tabs/
    OverviewTab.tsx
    TasksTab.tsx
    MarketingPlanTab.tsx
    TimeCapacityTab.tsx
  hooks/
    useClientReport.ts
    useClientMarketingPlan.ts
  export/
    ExportReportModal.tsx
client/components/portal/crm/__tests__/
  ClientDetailHub.test.tsx
  OverviewTab.test.tsx
  TasksTab.test.tsx
  MarketingPlanTab.test.tsx
  TimeCapacityTab.test.tsx
  ExportReportModal.test.tsx
```

---

## New Types to Add

Add to `client/lib/types/scheduling.ts` (or a new `client/lib/types/crm.ts`):

```typescript
export interface ClientReportSummary {
  total_tasks: number
  completed_tasks: number
  in_progress_tasks: number
  total_hours: number
  days_worked: number
  unique_categories: string[]
}

export interface CategoryBreakdownItem {
  category: string
  hours: number
  task_count: number
}

export interface WeeklyBreakdownItem {
  week_start: string   // YYYY-MM-DD
  hours: number
  tasks_completed: number
}

export interface MonthlySummaryItem {
  month: string        // YYYY-MM
  days: number
  hours: number
  tasks_completed: number
}

export interface ReportTaskItem {
  id: string
  title: string
  status: string
  category: string
  hours_spent: number
  completed_at: string | null
}

export interface ClientReportResponse {
  client: { id: string; name: string; company: string }
  period: { start: string; end: string }
  summary: ClientReportSummary
  category_breakdown: CategoryBreakdownItem[]
  weekly_breakdown: WeeklyBreakdownItem[]
  monthly_summary: MonthlySummaryItem[]
  tasks: ReportTaskItem[]
}

export interface ContentPillar {
  id: string
  name: string
  description: string
  color: string
  target_percentage: number
}

export interface AudiencePersona {
  id: string
  name: string
  description: string
}

export interface MarketingPlanDetailResponse {
  strategy_notes: string
  pillars: ContentPillar[]
  audiences: AudiencePersona[]
  updated_at: string | null
}
```

---

## Tests First

Write all test files before writing production code. Use `renderWithQuery` from `client/test-utils/scheduling.tsx`. Mock API calls with `vi.mock('@/lib/api')` or `msw`. The `createMockClientReport` and `createMockMarketingPlan` factories are defined here (and later consolidated in section-13).

### Mock Factories (define in test files, to be promoted in section-13)

```typescript
// Place these at the top of each test file that needs them.
// They will be consolidated into client/test-utils/ in section-13.

function createMockClientReport(overrides?: Partial<ClientReportResponse>): ClientReportResponse {
  /** Returns a complete ClientReportResponse for testing. */
}

function createMockMarketingPlan(overrides?: Partial<MarketingPlanDetailResponse>): MarketingPlanDetailResponse {
  /** Returns a plan with one pillar, one audience, and non-empty strategy_notes. */
}
```

### `ClientDetailHub.test.tsx`

```typescript
// Test: renders 4 tabs labelled "Overview", "Tasks", "Marketing Plan", "Time & Capacity"
// Test: "Overview" tab is active by default (has active styling)
// Test: clicking "Tasks" tab renders TasksTab, not OverviewTab
// Test: clicking "Marketing Plan" tab renders MarketingPlanTab
// Test: clicking "Time & Capacity" tab renders TimeCapacityTab
// Test: passes agentType='marketing' prop down to TasksTab
// Test: passes agentType='developer' prop down to TasksTab
```

### `OverviewTab.test.tsx`

```typescript
// Test: renders client name, company, status badge
// Test: renders 5 stat cards: Total Tasks, Completed, In Progress, Days Worked, Total Hours
// Test: stat values come from useClientReport summary
// Test: renders recent activity feed with up to 10 items
// Test: each activity item shows task title and relative time
// Test: shows skeleton while data is loading
// Test: shows empty-state component when no tasks exist
```

### `TasksTab.test.tsx`

```typescript
// Test: renders ViewToggle (list/kanban) button group
// Test: renders TaskFilterBar with ClientFilter hidden
// Test: agentType='marketing' — tasks list is filtered by clientId
// Test: agentType='developer' — same task list plus a "Project Milestones" section
// Test: "Project Milestones" section shows "Coming soon" placeholder text
// Test: switching view toggle persists selection to localStorage
```

### `MarketingPlanTab.test.tsx`

```typescript
// Test: renders markdown from strategy_notes when non-empty
// Test: renders ContentPillar cards (name, description, color badge, target_percentage)
// Test: renders AudiencePersona cards (name, description)
// Test: shows "Last updated: {date}" footer
// Test: shows EmptyState when strategy_notes is empty string and no pillars/audiences
// Test: <script> tag inside strategy_notes is NOT rendered in the DOM (XSS protection)
// Test: raw <img> tags referencing external URLs are stripped by rehype-sanitize
```

### `TimeCapacityTab.test.tsx`

```typescript
// Test: "Last 90d" button is active (highlighted) by default
// Test: clicking "Last 30d" calls useClientReport with updated date params
// Test: clicking "Last 6m" calls useClientReport with updated date params
// Test: WeeklyBarChart renders when weekly_breakdown is non-empty
// Test: CategoryDonutChart renders when category_breakdown is non-empty
// Test: monthly summary table renders one row per month entry
// Test: "Export Report" button opens ExportReportModal
// Test: shows loading skeleton while report is fetching
```

### `ExportReportModal.test.tsx`

```typescript
// Test: renders the current date range (start and end dates)
// Test: CSV and PDF radio/button options are both present
// Test: CSV is selected by default
// Test: clicking "Download" navigates to /agent/clients/{id}/report/export/?format=csv&start_date=...&end_date=...
// Test: clicking "Download" with PDF selected uses format=pdf in URL
// Test: clicking Cancel closes the modal without navigating
```

---

## Implementation

### Hooks

#### `client/components/portal/crm/hooks/useClientReport.ts`

React Query hook. Query key: `['client-report', clientId, startDate, endDate]`. Fetches `GET /agent/clients/{id}/report/?start_date={startDate}&end_date={endDate}`. Returns `{ data: ClientReportResponse | undefined, isLoading, error }`.

```typescript
export function useClientReport(
  clientId: string,
  startDate: string,
  endDate: string
): UseQueryResult<ClientReportResponse>
```

Call `api.request(...)` (the existing API client at `client/lib/api`). Enable only when `clientId` is truthy.

#### `client/components/portal/crm/hooks/useClientMarketingPlan.ts`

```typescript
export function useClientMarketingPlan(
  clientId: string
): UseQueryResult<MarketingPlanDetailResponse>
```

Query key: `['client-marketing-plan', clientId]`. Fetches `GET /agent/clients/{id}/marketing-plan/`. Enable only when `clientId` is truthy.

---

### `ClientDetailHub.tsx`

Props:
```typescript
interface ClientDetailHubProps {
  clientId: string
  agentType: 'marketing' | 'developer'
}
```

State: `activeTab: 'overview' | 'tasks' | 'marketing-plan' | 'time-capacity'` — managed locally with `useState`, default `'overview'`.

Structure:
- Header section: back button (`ArrowLeft` icon, calls `router.back()`), client name, status badge, client company
- Tab bar: four `<button>` elements, active tab styled with `border-b-2 border-accent text-primary`, inactive with `text-secondary hover:text-primary`
- Tab content area: conditionally renders the active tab component

The component does **not** fetch client info itself — it receives `clientId` and each tab fetches what it needs. However, it does accept an optional `client` prop if the parent has already fetched the client object (to avoid double-fetching):

```typescript
interface ClientDetailHubProps {
  clientId: string
  agentType: 'marketing' | 'developer'
  client?: { name: string; company: string; status: string }
}
```

If `client` is not passed, `ClientDetailHub` fetches it via `useQuery(['client', clientId], () => api.getClient(clientId))`.

---

### `OverviewTab.tsx`

Props: `{ clientId: string; client: ClientInfo }`

Data sources:
1. `useClientReport(clientId, defaultStart, defaultEnd)` — for `summary` stats (use last-90-days range as default)
2. `useQuery(['client-tasks-activity', clientId], ...)` — fetches `GET /agent/tasks/?client={id}&ordering=-updated_at&limit=10`

Layout:
- Client info card (`Surface`): name, company, email/phone if available, status badge, "Client since" date
- Stats row using `stat-card.tsx` from `client/components/common/stat-card.tsx`: Total Tasks, Completed Tasks, In Progress, Days Worked, Total Hours
- Recent activity feed: ordered list, each item shows task title, a status chip, and relative time (`"2h ago"` format — use `date-fns/formatDistanceToNow` or a simple inline helper)

Show `Skeleton` from `client/components/ui/skeleton.tsx` while either query is loading.

---

### `TasksTab.tsx`

Props: `{ clientId: string; agentType: 'marketing' | 'developer' }`

For both agent types:
- `ViewToggle` — list/kanban switcher, state in `localStorage` key `'tasks-view-{agentType}'`
- Task list or kanban, pre-filtered via `?client={clientId}` param, showing all statuses
- `TaskFilterBar` rendered with `showClientFilter={false}` — the client is already fixed

The management task list and kanban components that already exist under `client/app/dashboard/agent/marketing/management/tasks/` should be **imported and reused** rather than recreated. Check `client/components/management/` for any reusable task list components.

For `agentType='developer'`:
- Render the same task list/kanban above
- Below it, render a `Surface` with a heading "Project Milestones" and an `EmptyState` component with title "Coming soon" and description "Project milestone tracking will be available in a future update."

---

### `MarketingPlanTab.tsx`

Props: `{ clientId: string }`

Data: `useClientMarketingPlan(clientId)`

Install required packages if not present (check `client/package.json`):
- `react-markdown`
- `rehype-sanitize`

Note: `prism-react-renderer` is already installed (per CLAUDE.md).

Layout:
- If `strategy_notes` is non-empty: render with `<ReactMarkdown rehypePlugins={[rehypeSanitize]}>`. Code blocks use `prism-react-renderer` via a custom `components.code` prop on `ReactMarkdown`.
- ContentPillar cards in a `grid grid-cols-1 md:grid-cols-2 gap-4`: each card shows the pillar name with a small color badge (circle with `background: pillar.color`), description text, and `target_percentage` as a percentage string.
- AudiencePersona cards in a `grid grid-cols-1 md:grid-cols-2 gap-4`: each card shows name and description.
- Footer: `"Last updated: {formattedDate}"` using `updated_at` from the API response.
- If the plan response has empty `strategy_notes` **and** zero pillars **and** zero audiences: show `EmptyState` with title "No marketing plan yet" and description "No marketing plan has been set for this client yet."

For agents this tab is **entirely read-only** — no edit buttons.

---

### `TimeCapacityTab.tsx`

Props: `{ clientId: string }`

Local state:
- `dateRange: 'last-30d' | 'last-90d' | 'last-6m' | 'custom'` — default `'last-90d'`
- `customStart: string`, `customEnd: string` — only used when `dateRange === 'custom'`
- `showExportModal: boolean`

Derive `startDate` and `endDate` from `dateRange`:
- `'last-30d'`: today minus 30 days
- `'last-90d'`: today minus 90 days
- `'last-6m'`: today minus 6 months
- `'custom'`: use `customStart` / `customEnd`

Calls `useClientReport(clientId, startDate, endDate)`.

Layout top to bottom:
1. Segmented button group for date range: "Last 30d" / "Last 90d" / "Last 6m" / "Custom". Active button: `bg-accent text-white`. "Custom" opens two `DatePicker` inputs (from `client/components/ui/date-picker.tsx`).
2. Stats row (3 items): Days Worked, Total Hours, Unique Categories — values from `report.summary`.
3. Two-column chart area (stacks to single column on mobile):
   - Left: `WeeklyBarChart` — wraps Recharts `BarChart`, `data={report.weekly_breakdown}`, `dataKey="hours"`, x-axis `dataKey="week_start"`. CSS variable colors: `fill="var(--color-accent)"`.
   - Right: `CategoryDonutChart` — wraps Recharts `PieChart` with a `Pie` component, `data={report.category_breakdown}`, `dataKey="hours"`, `nameKey="category"`.
4. Monthly Summary Table — use HTML `<table>` or the existing `client/components/ui/table.tsx`. Columns: Month, Days, Hours, Tasks Completed. Rows from `report.monthly_summary`.
5. "Export Report" button (`Button` variant `outline`) — sets `showExportModal = true`.

Show `Skeleton` while `isLoading` is true.

---

### `ExportReportModal.tsx`

Props:
```typescript
interface ExportReportModalProps {
  open: boolean
  onClose: () => void
  clientId: string
  startDate: string
  endDate: string
}
```

Uses `Modal` from `client/components/ui/modal.tsx`.

Content:
- Display-only date range: "Report period: {startDate} → {endDate}"
- Format picker: two radio-style buttons or a `<select>`: "CSV" and "PDF". State: `format: 'csv' | 'pdf'`, default `'csv'`.
- "Download" button: constructs the URL `/agent/clients/{clientId}/report/export/?format={format}&start_date={startDate}&end_date={endDate}` and navigates to it via `window.location.href = url` (triggers a file download, not a React navigation). Then calls `onClose()`.
- "Cancel" button: calls `onClose()`.

---

## Package Requirements

Check `client/package.json` before installing. The following may need to be added:

```
react-markdown
rehype-sanitize
```

All other dependencies (`recharts`, `@tanstack/react-query`, `framer-motion`, `lucide-react`) are confirmed present per project setup.

---

## Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Tab state | Local `useState` | No URL param needed — tabs are secondary nav within a page |
| Client data | Optional prop + fallback query | Avoids double-fetching when parent already has client data |
| Markdown rendering | `react-markdown` + `rehype-sanitize` | Prevents XSS; raw HTML disallowed |
| Code blocks in markdown | `prism-react-renderer` (already installed) | Consistent with codebase |
| Charts | Recharts `BarChart` + `PieChart` separately | Bar and Pie cannot share a Recharts container; both already installed |
| Export | `window.location.href` redirect | Triggers native browser file download; no React routing needed |
| Developer milestones | `EmptyState` placeholder | Website project milestone API is out of scope for this split |
| Task list reuse | Import from existing management components | Avoids duplicating task list/kanban logic |

---

## Dependency Notes

- `stat-card.tsx` is at `client/components/common/stat-card.tsx`
- `Surface`, `Button`, `Badge`, `Modal`, `Skeleton`, `EmptyState`, `DatePicker` are all confirmed in `client/components/ui/`
- `api.getClient(id)` and `api.request(path)` are the fetch helpers from `client/lib/api`
- `renderWithQuery` test helper is in `client/test-utils/scheduling.tsx`
- `AgentGlobalTask`, `TaskCategoryItem` types are in `client/lib/types/scheduling.ts`
- The new `ClientReportResponse`, `MarketingPlanDetailResponse` types should be added to `client/lib/types/scheduling.ts` or a new `client/lib/types/crm.ts`
