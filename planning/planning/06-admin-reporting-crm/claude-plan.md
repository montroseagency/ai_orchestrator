# Implementation Plan: Admin Reporting & Client CRM Hub

## Context and Goals

The Montrroase platform has agents (marketing and developer) managing clients. Currently the agent client detail pages are shallow — they show basic contact info and a task count. This split transforms those pages into full CRM hubs that surface the work done for each client: tasks, time invested, marketing strategy, and exportable reports.

Simultaneously, the admin side gains an approval queue for reviewing agent-submitted tasks (those marked `in_review`), a category management page for administering the `TaskCategory` model, and three new notification types to support the review workflow.

This split integrates with established models (`AgentGlobalTask`, `MarketingPlan`, `TaskCategory`, `AgentTimeBlock`) and reuses the existing `PDFService`, task UI components from Split 03, and the notification-realtime service.

---

## High-Level Architecture

The work divides into six areas, roughly in dependency order:

1. **Backend migrations** — two small migrations adding fields to existing models
2. **New backend API endpoints** — client report aggregation, approval actions, category CRUD/reorder, marketing plan read/write
3. **Notification type additions** — Django model + Node.js service enum
4. **Shared `ClientDetailHub` frontend component** — 4-tab layout used by both agent types
5. **Admin pages** — approvals queue and category management
6. **Export functionality** — CSV download + PDF using extended PDFService

---

## Section 1: Backend Migrations

### What and Why

Three schema changes are needed before any API work can proceed.

**Migration 1 — `review_feedback` on `AgentGlobalTask`:**
The approval reject action must store the admin's feedback so the agent can read it. A simple `TextField` with `blank=True, default=''` is sufficient. It is cleared (reset to empty string) when the agent re-submits the task for review. No new model; no history tracking is needed for this scope.

**Migration 2 — `strategy_notes` on `MarketingPlan`:**
The `MarketingPlan` model already exists as a `OneToOneField(Client)` with structured related models (`ContentPillar`, `AudiencePersona`). The Marketing Plan tab also needs to show a free-form strategy document written by admins in markdown. Adding `strategy_notes = TextField(blank=True, default='')` to `MarketingPlan` is the minimal, non-breaking change.

**Migration 3 — Database index on `AgentTimeBlock(client, date)`:**
The client report aggregation filters time blocks by `client=clientId` and `date__range`. Without an index on `(client, date)`, every report request requires a full table scan on time blocks. This migration adds `Index(fields=['client', 'date'])` to `AgentTimeBlock`.

### What to Build

1. Migration file: add `review_feedback = models.TextField(blank=True, default='')` to `AgentGlobalTask`
2. Migration file: add `strategy_notes = models.TextField(blank=True, default='')` to `MarketingPlan`
3. Migration file: add `Index(fields=['client', 'date'])` to `AgentTimeBlock`
4. Update `AgentGlobalTaskSerializer` to include `review_feedback` (read field for agents)
5. Update `MarketingPlanSerializer` to include `strategy_notes`

No data migrations are needed. Existing rows get empty string defaults.

---

## Section 2: Client Report API

### What and Why

Agents need a backend endpoint that aggregates time block and task data for a specific client over a date range. This is the data source for the Time & Capacity tab and the report export. Building it as a dedicated read endpoint (rather than assembling on the frontend) keeps the aggregation logic centralized and queryable.

All aggregations use `AgentTimeBlock` filtered by `client=clientId` and the requested date range. Task counts use `AgentGlobalTask` filtered by `client=clientId` (no date range filter on tasks — show totals). The client must be assigned to the requesting agent (authorization check).

### Endpoint Contract

```
GET /agent/clients/{id}/report/
Query params: start_date (YYYY-MM-DD), end_date (YYYY-MM-DD)
Default range: last 90 days from today
Auth: IsAuthenticated, agent must be assigned to this client
```

Response shape:

```python
@dataclass
class ClientReportData:
    client: ClientSummary          # id, name, company
    period: PeriodRange            # start, end
    summary: ReportSummary         # total_tasks, completed_tasks, in_progress_tasks,
                                   # total_hours, days_worked, unique_categories[]
    category_breakdown: list       # [{category, hours, task_count}]
    weekly_breakdown: list         # [{week_start, hours, tasks_completed}]
    monthly_summary: list          # [{month, days, hours, tasks_completed}]
    tasks: list                    # [{id, title, status, category, hours_spent, completed_at}]
```

**Aggregation logic:**
- `days_worked`: `AgentTimeBlock.objects.filter(client=id, date__range=...).dates('date', 'day').count()`
- `total_hours`: sum of `duration_minutes` / 60
- `weekly_breakdown`: annotate with `TruncWeek('date')`, aggregate `Sum('duration_minutes')`
- `category_breakdown`: join time blocks → tasks → `task_category_ref`, group by category
- `monthly_summary`: annotate with `TruncMonth('date')`, aggregate sum + count completed tasks

The `tasks` list in the response is filtered to tasks with `created_at` or `completed_at` within the date range (not all tasks for the client). Capped at 200 records for the JSON endpoint; the export endpoints return the full dataset. Tasks are fetched with `select_related('task_category_ref')` to avoid N+1 queries.

**Date range defaults:** If neither `start_date` nor `end_date` is provided, default to last 90 days. If only `end_date` is provided, `start_date` defaults to 90 days before. If only `start_date` is provided, `end_date` defaults to today.

Use the new `(client, date)` index on `AgentTimeBlock` (Migration 3) plus the existing `(agent, client)` index on `AgentGlobalTask`.

### Where It Lives

New file: `server/api/agent/client_report_views.py`
Registered in `server/api/urls.py` under the `agent/` prefix.

---

## Section 3: Marketing Plan API

### What and Why

The Marketing Plan tab needs to fetch the client's `MarketingPlan` including `strategy_notes`, `pillars` (ContentPillar), and `audiences` (AudiencePersona). Admins need a write endpoint to update `strategy_notes`.

### Endpoints

```
GET /agent/clients/{id}/marketing-plan/
Auth: IsAuthenticated (agent assigned to client)
Returns: { strategy_notes, pillars[], audiences[], updated_at }

POST /admin/clients/{id}/marketing-plan/
Auth: IsAdminUser
Body: { strategy_notes: string }
Creates MarketingPlan if none exists (get_or_create), sets strategy_notes
```

### Serializers

`MarketingPlanDetailSerializer` — nested serializer including:
- `strategy_notes`, `updated_at` from `MarketingPlan`
- `pillars` via `ContentPillarSerializer` (nested, read-only from agent perspective)
- `audiences` via `AudiencePersonaSerializer` (nested, read-only)

The admin write endpoint validates that `strategy_notes` is a string and creates the `MarketingPlan` instance if one doesn't exist for that client.

---

## Section 4: Admin Approval Queue API

### What and Why

Admins need to see all `AgentGlobalTask` records with `status='in_review'` and take approve/reject actions. Each action updates the task status and triggers a notification to the agent.

### Endpoints

```
GET /admin/approvals/
Auth: IsAdminUser
Returns: AgentGlobalTask list filtered by status='in_review', ordered by updated_at ASC
Includes: agent.name, client.name, client.company, task.description, task.review_feedback

POST /admin/approvals/{task_id}/approve/
Auth: IsAdminUser
Sets: status='done', review_feedback=''
Triggers: task_approved notification to task.agent.user

POST /admin/approvals/{task_id}/reject/
Auth: IsAdminUser
Body: { feedback: string } (validated — required, non-empty)
Sets: status='in_progress', review_feedback=feedback
Triggers: task_rejected notification to task.agent.user
```

### Status Transition Logic

Rather than a state machine library (overkill for a 4-state machine), use inline validation in the view:

```python
def approve_task(task_id, admin_user):
    """Approve a task in review. Raises ValueError if task is not in_review."""

def reject_task(task_id, admin_user, feedback: str):
    """Reject a task in review with required feedback. Raises ValueError if feedback empty."""
```

Both functions use `AgentGlobalTask.objects.select_for_update().get(id=task_id)` inside `transaction.atomic()` and verify that the task's `status` is still `in_review` before proceeding. This prevents race conditions when two admins act on the same task simultaneously. If the task is no longer `in_review`, the function raises a `ValueError` which the view converts to HTTP 409 Conflict. Notification dispatch happens after the transaction commits (via Celery task or direct Django signal).

### Where It Lives

New file: `server/api/admin/approval_views.py`
Registered in `server/api/urls.py` under `admin/` prefix with `IsAdminUser` permission.

---

## Section 5: Notification Types

### What and Why

Three new notification types support the approval workflow. They must exist in both the Django model (for persistence to the Django DB notification store) and in the Node.js notification-realtime service (for WebSocket delivery).

### Django Changes

Add to `NOTIFICATION_TYPES` in `server/api/models/notifications.py`:
```
('task_review_submitted', 'Task Submitted for Review')
('task_approved', 'Task Approved')
('task_rejected', 'Task Rejected')
```

Notification helper functions (in `server/api/services/notification_service.py` or equivalent):
```python
def notify_task_review_submitted(task):
    """Send notification to admin users when agent submits task for review."""

def notify_task_approved(task, approved_by_name: str):
    """Send notification to task's agent when their task is approved."""

def notify_task_rejected(task, rejected_by_name: str, feedback: str):
    """Send notification to task's agent when their task is rejected."""
```

Each helper creates a Django `Notification` record and dispatches an event to RabbitMQ for the notification-realtime service to pick up and push via WebSocket.

### Node.js Changes

Add the three new type strings to the `NotificationType` enum in the notification-realtime service. The event consumer already handles arbitrary notification types — adding to the enum is sufficient for TypeScript type safety.

---

## Section 6: Category Management API

### What and Why

The admin category settings page needs full CRUD for `TaskCategory` plus a bulk reorder endpoint. The model already has `sort_order` and `is_active` fields. Deletion must be soft (toggle `is_active`) because existing tasks reference categories by FK and hard deleting would break them.

### Endpoints

```
GET  /admin/categories/                     # List all (include inactive)
POST /admin/categories/                     # Create new
PATCH /admin/categories/{id}/              # Update (name, color, icon, department, is_active)
DELETE /admin/categories/{id}/             # Soft delete: sets is_active=False
PATCH /admin/categories/reorder/           # Body: { ordered_ids: string[] }
                                           # Updates sort_order for each ID in order
```

All require `IsAdminUser`. The reorder endpoint uses a single `transaction.atomic()` to update all sort orders in one round-trip.

`TaskCategoryAdminSerializer` exposes: `id`, `name`, `slug`, `color`, `icon`, `department`, `sort_order`, `is_active`.

**Agent-facing category filtering:** The existing agent-facing category endpoint (used by task creation forms and filters) must filter `is_active=True` by default. Deactivated categories are hidden from agents but remain in the database and are not removed from existing task references. The admin endpoint returns all categories including inactive ones.

### Where It Lives

New viewset: `server/api/admin/category_views.py`
Custom router action `reorder` on the viewset.

---

## Section 7: Export API

### What and Why

From the Time & Capacity tab, agents can export a client report as CSV or PDF for a given date range. Both formats use the same `/agent/clients/{id}/report/export/` endpoint, differentiated by `?format=csv|pdf`.

### CSV Format

```
Task Title, Status, Category, Client, Date, Hours Spent, Agent
"Nike Q2 Brief", "Done", "Copywriting", "Nike", "2026-03-15", "2.5", "Agent Smith"
```

Generated using Python's built-in `csv` module via `StreamingHttpResponse` for large datasets. No third-party library needed.

### PDF Format

Extends the existing `PDFService` in `server/api/services/pdf_service.py`:

```python
def generate_client_report_pdf(report_data: dict, client, period: dict) -> bytes:
    """Generate branded PDF client report.

    Uses the same WeasyPrint + Montrose branding setup as generate_quote_pdf().
    Template: server/api/templates/reports/client_report_pdf.html
    Includes: header with logo, summary stats, monthly table, task list.
    Charts: inline SVG bar chart for weekly hours (no JS required).
    Uses the same django_url_fetcher as quote PDFs to restrict resource loading
    to Django-resolved URLs only (SSRF mitigation).
    Returns PDF as bytes.
    """
```

The HTML template uses the same brand colors and company info as the quote PDF template. Charts are rendered as inline SVG `<path>` elements calculated from the report data in the Django template context — this avoids any JavaScript dependency since WeasyPrint cannot execute JS. Content fields (`strategy_notes`, task descriptions) are **not** rendered in the PDF template — only structured data fields are used. This prevents SSRF via externally-referenced URLs in markdown content.

PDF generation is synchronous (no Celery task needed for this scope — reports are small). If generation exceeds 3 seconds in practice, move to async in a future split.

### Endpoint

```
GET /agent/clients/{id}/report/export/
Params: start_date, end_date, format=csv|pdf
Auth: IsAuthenticated, agent assigned to client
Returns: file download with appropriate Content-Disposition header
```

---

## Section 8: ClientDetailHub Frontend Component

### What and Why

Both the marketing agent and developer agent client detail pages need the same 4-tab CRM hub. Rather than duplicating the UI, a single `ClientDetailHub` component is built with an `agentType` prop that controls which data sources appear in the Tasks tab.

### Component Structure

```
client/components/portal/crm/
  ClientDetailHub.tsx          # 4-tab container, fetches client data
  tabs/
    OverviewTab.tsx            # Stats + recent activity feed
    TasksTab.tsx               # List/Kanban with ViewToggle, reuses management/tasks components
    MarketingPlanTab.tsx       # strategy_notes markdown + pillars + audiences
    TimeCapacityTab.tsx        # Charts, date range picker, export button
  hooks/
    useClientReport.ts         # React Query hook for /agent/clients/{id}/report/
    useClientMarketingPlan.ts  # React Query hook for /agent/clients/{id}/marketing-plan/
  export/
    ExportReportModal.tsx      # Date range + format selector modal
```

### ClientDetailHub Layout

The component wraps the existing agent client detail pages. It receives `clientId` and `agentType` as props and renders:

1. **Header section**: Back link, client name, status badge, package name, assigned agent
2. **Tab bar**: Four tabs styled per design spec (`border-b-2 border-accent` for active)
3. **Tab content pane**: Renders the appropriate tab component

Tab state is managed locally in `ClientDetailHub` (no URL param needed — the tabs are secondary navigation within the page).

### OverviewTab

Displays:
- Client info card (name, company, plan/package, status badge, contact info)
- Quick stats row using existing `stat-card.tsx`: Total Tasks, Completed, In Progress, Days Worked, Total Hours
- Recent activity feed: ordered list of the last 10 task status changes for this client, showing task title, old status → new status, and relative time

Data: `useClientReport` (for stats) + `useGlobalTasks({ client: id, ordering: '-updated_at', limit: 10 })` (for activity).

### TasksTab

For marketing clients: renders `TasksListView` / `TasksKanbanView` with `ViewToggle` and `TaskFilterBar`, pre-filtered to `client=clientId`. The filter bar `ClientFilter` multi-select is hidden since we're already scoped to one client.

For developer clients: same list/kanban for `AgentGlobalTask` filtered by `client=clientId`. A "Project Milestones" section is deferred to a future split when the website project task API is formally specified — a placeholder accordion with "Coming soon" message occupies that area for now.

Both variants show full task history (all statuses, no date filter by default).

### MarketingPlanTab

Renders the response from `useClientMarketingPlan`:
- If `strategy_notes` is non-empty: render as markdown using `react-markdown` with `rehype-sanitize` plugin. This sanitizes HTML output and prevents XSS. Raw HTML is explicitly disallowed. Code blocks use `prism-react-renderer` for syntax highlighting.
- ContentPillar cards in a 2-column grid: name with color badge, description, target_percentage
- AudiencePersona cards in a 2-column grid: name, description
- "Last updated: {date}" footer
- If `strategy_notes` is empty: show `EmptyState` component with message "No marketing plan has been set for this client yet."

For agents: completely read-only. No edit button.

### TimeCapacityTab

Contains:
1. **Date range selector** — segmented button group (Last 30d / Last 90d / Last 6m / Custom). Custom opens a date picker. On change, refetches `useClientReport` with new params.
2. **Stats row** — Days Worked, Total Hours, Unique Categories (from report summary)
3. **Two-column chart section:**
   - Left: `WeeklyBarChart` — wraps Recharts `BarChart` with `data={report.weekly_breakdown}`, `dataKey="hours"`, CSS variable theming
   - Right: `CategoryDonutChart` — wraps Recharts `PieChart` with `data={report.category_breakdown}`, `dataKey="hours"`, active shape pattern
4. **Monthly Summary Table** — columns: Month, Days, Hours, Tasks Completed
5. **Export Report button** — opens `ExportReportModal`

`ExportReportModal` shows the current date range, a format picker (CSV / PDF), and a Download button. On confirm, it redirects to the export endpoint URL which triggers a file download.

---

## Section 9: Admin Approvals Page

### What and Why

Admins need a single view to review all tasks awaiting approval. The review action (approve/reject with feedback) should be quick — a slide-out panel avoids a full page navigation.

### Page: `/dashboard/admin/approvals/page.tsx`

Fetches `GET /admin/approvals/` on mount, polling every 60 seconds or on Socket.IO `task_review_submitted` event.

Renders a table (using the existing `DataTable.tsx` component from `client/components/ui/`) with columns:
- Agent (avatar + name)
- Task title (clickable, opens review panel)
- Client (company name)
- Submitted (relative time, e.g. "2h ago")
- Action (view eye icon button)

When a row is clicked, a `Drawer` (from `client/components/ui/drawer.tsx`) slides in from the right with:

```
Title: Review: {task.title}
Subtitle: Agent: {agent.name} · Client: {client.company} · Category: {category}
Submitted: {relative time}
─────────────────────────
Task Description:
{task.description}
─────────────────────────
Feedback (required for rejection):
<textarea />
─────────────────────────
[✓ Approve]   [✗ Reject & Return]
```

**Approve action**: calls `POST /admin/approvals/{task_id}/approve/`, shows success toast, removes task from table.

**Reject action**: validates feedback is non-empty before calling `POST /admin/approvals/{task_id}/reject/`, shows success toast, removes task from table. Shows inline error if feedback empty.

**Navigation badge**: The "Approvals" nav item in the sidebar shows a count badge (number of pending tasks). This is fetched on sidebar mount and refreshed via Socket.IO.

---

## Section 10: Admin Category Management Page

### What and Why

Admins need to manage the `TaskCategory` records that agents see when creating tasks. The page provides full CRUD with drag-and-drop reordering.

### Page: `/dashboard/admin/settings/categories/page.tsx`

**Layout:**
- Page header with "Add Category" button (opens `Modal`)
- Sortable list of category rows

**Each category row:**
- `GripVertical` drag handle icon (from lucide-react)
- Color swatch circle (shows `category.color`)
- Category name
- Department badge
- Active/inactive toggle (calls `PATCH /admin/categories/{id}/` with `{ is_active: !current }`)
- Edit button (opens edit modal)
- Delete button (calls `DELETE /admin/categories/{id}/` — soft delete; shows `confirmation-modal.tsx` first)
- Preview badge showing how the category appears in task views

**Drag-and-drop:**
- Wraps list in `DndContext` + `SortableContext` from `@dnd-kit/sortable`
- Each row uses `useSortable` hook
- `onDragEnd` calls `arrayMove` to update local order, then dispatches `PATCH /admin/categories/reorder/` with `{ ordered_ids: [...] }`
- Optimistic update: local state updates immediately
- On API error: show error toast AND call `queryClient.invalidateQueries(['admin-categories'])` to refetch the authoritative order from the server. This reconciles the frontend state without requiring a manual page refresh.

**Add/Edit Modal (`Modal` component from `client/components/ui/modal.tsx`):**
- Name field (text input, required)
- Color picker (hex color input with preview swatch)
- Icon selector (dropdown of lucide icon names)
- Department dropdown (choices from backend: marketing, developer, admin, all)
- Preview badge rendered in real-time from current form values

### Sidebar Update

Add to `adminNavGroups` in `client/components/dashboard/sidebar.tsx`:
- Under `business` group: `{ href: '/dashboard/admin/approvals', label: 'Approvals', icon: CheckCircle2 }`
- New `settings` group: `{ label: 'Settings', items: [{ href: '/dashboard/admin/settings/categories', label: 'Categories', icon: Tag }] }`

---

## Section 11: Agent Re-submission Workflow

### What and Why

The approval workflow is incomplete without the agent's side. When an admin rejects a task, the agent sees the feedback and needs a way to re-submit the corrected task for review. Without this, `review_feedback` is informational-only with no actionable path.

### Backend

```
POST /agent/tasks/{task_id}/resubmit/
Auth: IsAuthenticated, requesting agent must own this task
Validates: task.status must be 'in_progress' (agent can only re-submit after rejection)
Sets: status='in_review', review_feedback='' (clears prior feedback)
Triggers: task_review_submitted notification to admin users
```

This endpoint lives on the `AgentGlobalTaskViewSet` as a custom `@action`. It follows the same pattern as the existing `complete/` action on that viewset.

### Frontend

In the agent's task detail view (or wherever the task card renders for `in_progress` tasks):
- When `review_feedback` is non-empty (i.e., the task was previously rejected), show a highlighted rejection feedback panel: "Returned: {review_feedback}"
- Show a "Re-submit for Review" button that calls `POST /agent/tasks/{task_id}/resubmit/`
- On success, update the task's cached status to `in_review` and hide the feedback panel

This is a small addition to the existing task card/modal UI, not a new page.

---

## Section 12: Agent Client Page Integration (was 11)

### What and Why

The existing marketing and developer agent client detail pages need to be updated to render `ClientDetailHub` instead of their current simple layouts.

### Marketing Agent

`client/app/dashboard/agent/marketing/clients/[id]/page.tsx`:
- Keep the existing React Query data fetching pattern (`useQuery` for client + posts)
- Replace the current JSX body with `<ClientDetailHub clientId={params.id} agentType="marketing" />`
- The existing quick action buttons (All Posts, Ideas, etc.) can remain above the tab bar or be removed — discuss with user if needed (plan assumes they are preserved in the Overview tab's client info card)

### Developer Agent

`client/app/dashboard/agent/developer/clients/[id]/page.tsx` (create if not exists):
- Same pattern: fetch client, render `<ClientDetailHub clientId={params.id} agentType="developer" />`

---

## Section 13: Tests

### Backend Tests

For each new view:
- Approval queue: test `GET` returns only `in_review` tasks; test approve sets status to `done`; test reject requires feedback and sets status to `in_progress`; test concurrent approve raises 409; test non-admin gets 403
- Agent re-submission: test `resubmit/` transitions `in_progress → in_review` and clears `review_feedback`; test `in_review` task cannot be re-submitted
- Client report: test aggregation math with known fixture data; test date range filtering; test unauthorized client returns 403
- Category reorder: test bulk sort_order update in single transaction; test ordering is correct
- Marketing plan: test get returns pillars + audiences + strategy_notes; test admin write creates plan if none exists

### Frontend Tests

New test files using Vitest + `renderWithQuery` from `test-utils/scheduling.tsx`:
- `ClientDetailHub.test.tsx`: tab switching, correct component rendered per tab
- `TimeCapacityTab.test.tsx`: date range selector triggers refetch; charts render with data
- `ApprovalsPage.test.tsx`: table renders tasks; approve action closes drawer and removes row; reject requires feedback
- `CategoryManagement.test.tsx`: drag end dispatches reorder API call; add modal opens; delete shows confirmation

New mock factories needed:
- `createMockClientReport(overrides?)` — returns full `ClientReportResponse`
- `createMockMarketingPlan(overrides?)` — returns plan with pillars and audiences
- `createMockApprovalTask(overrides?)` — returns `AgentGlobalTask` with `status='in_review'`
- `createMockTaskCategory(overrides?)` — returns `TaskCategoryItem`

---

## Implementation Order

Dependencies flow in this order:

1. **Backend migrations** (no deps)
2. **Notification type additions** (no deps)
3. **Client report API** (requires migration 1 for `review_feedback` to be in serializer)
4. **Marketing plan API** (requires migration 2)
5. **Approval queue API** (requires migration 1, notification types)
6. **Category management API** (no deps)
7. **Export API** (requires client report API)
8. **`ClientDetailHub` component + hooks** (requires client report API and marketing plan API to be defined)
9. **OverviewTab, TasksTab, MarketingPlanTab, TimeCapacityTab** (requires hub)
10. **ExportReportModal** (requires TimeCapacityTab)
11. **Admin approvals page** (requires approval API)
12. **Admin category page** (requires category API)
13. **Agent page integration** (requires hub component)
14. **Sidebar updates** (can be done anytime after pages exist)

---

## Key Technical Decisions

| Decision | Choice | Reason |
|---|---|---|
| PDF library | Extend existing `PDFService` (WeasyPrint) | Already installed, branded templates exist |
| State machine | Inline validation only | 4-state machine is too simple to justify a library |
| `django-fsm` | Not used | Archived Oct 2025; `viewflow.fsm` v3 would be overkill |
| Category deletion | Soft-delete only (`is_active=False`) | Live task data references categories by FK |
| Drag-and-drop | `@dnd-kit/sortable` | Already in `package.json`; bulk PATCH for persistence |
| Charts | Recharts (`BarChart` + `PieChart` separately) | Already installed; Bar+Pie cannot share a container |
| Marketing Plan tab | Add `strategy_notes` + show existing structured data | `MarketingPlan` model already exists with pillars/audiences |
| Developer tasks | Global tasks + project milestones | Developer agents work with both types |
| Time data | Time blocks only | Accurate real tracking; matches spec |
| PDF charts | Inline SVG (no JS) | WeasyPrint cannot execute JavaScript |
