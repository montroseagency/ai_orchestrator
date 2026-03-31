# Combined Spec: Admin Reporting & Client CRM Hub

## Overview

This split enhances the agent-facing Clients pages into full CRM hubs, adds an admin approval queue for task review, builds an admin category management page with drag-and-drop reordering, and implements automated client report export (CSV + PDF). It integrates with existing Django models (AgentGlobalTask, MarketingPlan, TaskCategory, AgentTimeBlock) and the notification-realtime service.

---

## Confirmed Backend State (from codebase research)

- `AgentGlobalTask` already has `client = ForeignKey("Client")` and `status='in_review'` ✓
- `TaskCategory` DB model already exists with `sort_order`, `is_active`, `name`, `slug`, `color`, `icon`, `department` ✓
- `MarketingPlan` model already exists as `OneToOneField(Client)` with ContentPillar + AudiencePersona relations ✓
- `PDFService` in `server/api/services/pdf_service.py` uses WeasyPrint with Montrose branding ✓
- No `review_feedback` field on `AgentGlobalTask` — needs migration
- No `strategy_notes` field on `MarketingPlan` — needs migration
- No approval-specific notification types — need adding to both Django model and Node.js service

---

## New Backend Work

### 1. Database Migrations

**Migration A** — `AgentGlobalTask` changes:
```python
review_feedback = models.TextField(blank=True, default='')
# Stores admin rejection reason. Cleared on re-submission.
```

**Migration B** — `MarketingPlan` changes:
```python
strategy_notes = models.TextField(
    blank=True, default='',
    help_text='Admin-written strategy document in markdown format'
)
```

### 2. New API Endpoints

#### Agent-facing endpoints (authenticated, scoped to requesting agent's clients)

```
GET /agent/clients/{id}/report/
  Params: ?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD (default: last 90 days)
  Returns: ClientReportResponse (see type definition below)
  Auth: IsAuthenticated — agent must be assigned to this client

GET /agent/clients/{id}/report/export/
  Params: ?start_date=...&end_date=...&format=csv|pdf
  Returns: File download (text/csv or application/pdf)
  Auth: IsAuthenticated — same auth as above

GET /agent/clients/{id}/marketing-plan/
  Returns: { strategy_notes, pillars[], audiences[], updated_at }
  Auth: IsAuthenticated
```

#### Admin-only endpoints

```
POST /admin/clients/{id}/marketing-plan/
  Body: { strategy_notes: string }
  Auth: IsAdminUser
  Sets marketing_plan.strategy_notes

GET /admin/approvals/
  Returns: AgentGlobalTask[] where status='in_review', ordered by updated_at ASC
  Includes: agent.name, client.name, client.company, task description
  Auth: IsAdminUser

POST /admin/approvals/{task_id}/approve/
  Sets status='done', review_feedback=''
  Sends notification to agent
  Auth: IsAdminUser

POST /admin/approvals/{task_id}/reject/
  Body: { feedback: string } (required, validated)
  Sets status='in_progress', review_feedback=feedback
  Sends notification to agent
  Auth: IsAdminUser

GET /admin/categories/
POST /admin/categories/
PATCH /admin/categories/{id}/
DELETE /admin/categories/{id}/  → soft delete (toggle is_active)
PATCH /admin/categories/reorder/
  Body: { ordered_ids: string[] }
  Bulk updates sort_order for each category
  Auth: IsAdminUser
```

#### ClientReportResponse type

```typescript
interface ClientReportResponse {
  client: { id: string, name: string, company: string }
  period: { start: string, end: string }
  summary: {
    total_tasks: number
    completed_tasks: number
    in_progress_tasks: number
    total_hours: number          // from AgentTimeBlock.duration_minutes sum / 60
    days_worked: number          // distinct AgentTimeBlock.date count
    unique_categories: string[]
  }
  category_breakdown: Array<{ category: string, hours: number, task_count: number }>
  weekly_breakdown: Array<{ week_start: string, hours: number, tasks_completed: number }>
  monthly_summary: Array<{ month: string, days: number, hours: number, tasks_completed: number }>
  tasks: Array<{ id: string, title: string, status: string, category: string, hours_spent: number, completed_at: string | null }>
}
```

### 3. Notification Types (new)

Django `NOTIFICATION_TYPES` additions:
- `task_review_submitted` — sent to admins when agent moves task to in_review
- `task_approved` — sent to agent when admin approves
- `task_rejected` — sent to agent when admin rejects, includes feedback

Node.js `NotificationType` enum additions (same 3 types).

### 4. PDF Service Extension

Add `generate_client_report_pdf(report_data, client, period)` to `PDFService`.
Template: `server/api/templates/reports/client_report_pdf.html`
- Header: Montrose logo + client name + date range
- Summary stats section
- Monthly summary table
- Task list table
- Charts: static SVG bar chart (weekly hours) embedded in template

---

## Frontend Work

### Architecture: Shared ClientDetailHub Component

Both agent types use the same component:
- `client/components/portal/crm/ClientDetailHub.tsx` — 4-tab layout
- Props: `clientId`, `agentType: 'marketing' | 'developer'`
- The `agentType` prop controls which task types appear in the Tasks tab

**Tab structure:**
```
[Overview] [Tasks] [Marketing Plan] [Time & Capacity]
```

### Tab 1: Overview

- Client info card: name, company, package, status badge
- Quick stats row: Total Tasks, Completed, In Progress, Days Worked, Total Hours
- Recent activity feed: last 10 status changes on tasks tagged to this client
- Data sources:
  - Stats from `/agent/clients/{id}/report/` (last 90 days)
  - Activity from `useGlobalTasks({ client: id, ordering: '-updated_at', limit: 10 })`

### Tab 2: Tasks

**Marketing clients:**
- Reuse `TasksListView` + `TasksKanbanView` + `ViewToggle` + `TaskFilterBar` from `client/app/dashboard/agent/marketing/management/tasks/`
- Filter pre-set: `client=clientId`
- Shows full task history (all statuses)

**Developer clients:**
- Same list/kanban view for `AgentGlobalTask` filtered by client
- Additional section: "Project Milestones" showing website project tasks

### Tab 3: Marketing Plan

- Renders `strategy_notes` as markdown (using `prism-react-renderer` or a markdown renderer)
- ContentPillar cards: name, description, target_percentage, color badge
- AudiencePersona cards: name, description
- For agents: read-only
- Admin-editable via a separate admin page (`/dashboard/admin/clients/[id]/marketing-plan/edit`)

### Tab 4: Time & Capacity

- Date range selector: Last 30d / Last 90d / Last 6m / Custom (default: Last 90d)
- **Stats row:** Days Worked, Total Hours, Unique Categories
- **Weekly Bar Chart** (Recharts `BarChart`): hours per week for selected range
- **Category Donut Chart** (Recharts `PieChart`): hours split by task category
- **Monthly Summary Table**: Month | Days | Hours | Tasks Completed
- **Export Report button**: opens modal with date range confirmation + format selector (CSV / PDF)
- Data source: `/agent/clients/{id}/report/?start_date=...&end_date=...`

### New Admin Pages

#### `/dashboard/admin/approvals/`

- Table of `AgentGlobalTask` where `status='in_review'`
- Columns: Agent, Task Title, Client, Submitted (relative time), View button
- Clicking row opens a slide-out `Drawer` (from `client/components/ui/drawer.tsx`):
  - Task title, agent, client, category, submitted time
  - Full task description
  - Agent notes (from task description or a dedicated notes field)
  - Feedback textarea (required for rejection)
  - `[✓ Approve]` (green) and `[✗ Reject & Return]` (red) buttons
  - Feedback field validates: required only when rejecting
- Real-time badge on nav item showing count of pending approvals

#### `/dashboard/admin/settings/categories/`

- List of all `TaskCategory` records with: color swatch, name, department badge, sort order, active toggle
- **Drag-and-drop reorder** using `@dnd-kit/sortable` (`verticalListSortingStrategy`)
- Reorder persists to `PATCH /admin/categories/reorder/` (bulk ordered_ids)
- **Add category**: uses `Modal` component from `client/components/ui/modal.tsx` with form
- **Edit category**: inline edit or modal (same form)
- **Deactivate**: toggle `is_active` (soft delete, not hard)
- **Preview badge**: shows how category will appear in task views
- Navigation: add "Settings" group to admin sidebar with "Categories" item

### Sidebar Updates (`client/components/dashboard/sidebar.tsx`)

```
business group:
  + { href: '/dashboard/admin/approvals', label: 'Approvals', icon: CheckCircle }

[new] settings group:
  + { href: '/dashboard/admin/settings/categories', label: 'Categories', icon: Tag }
```

---

## Component Reuse Map

| Need | Reuse From |
|------|-----------|
| List/Kanban toggle | `management/tasks/ViewToggle.tsx` |
| Task filter bar | `management/tasks/TaskFilterBar.tsx` |
| Kanban view | `management/tasks/TasksKanbanView.tsx` |
| List view | `management/tasks/TasksListView.tsx` |
| Task card | `management/tasks/TaskCard.tsx` |
| Client badge | `management/tasks/ClientBadge.tsx` |
| Drawer panel | `components/ui/drawer.tsx` |
| Modal | `components/ui/modal.tsx` |
| Badge | `components/ui/badge.tsx` |
| Charts | `recharts` (already installed) |
| Drag-and-drop | `@dnd-kit/sortable` (already installed) |
| PDF service | `server/api/services/pdf_service.py` (extend) |

---

## Design Specifications

### ClientDetailHub
- Tab bar: `border-b border-border`, active: `border-b-2 border-accent text-accent`
- Tab content: `p-6`
- Overview stats: same `stat-card.tsx` pattern as Dashboard KPI

### Approval Queue
- Table: `border border-border rounded-xl overflow-hidden`
- Rows: `hover:bg-surface-subtle transition-colors`
- Approve button: `bg-green-600 text-white rounded-lg px-4 py-2`
- Reject button: `bg-red-600 text-white rounded-lg px-4 py-2`
- Feedback textarea: `border border-border rounded-lg p-3 min-h-[100px]`

### Category Manager
- Row: `flex items-center gap-3 p-3 rounded-lg border border-border bg-surface`
- Drag handle: `cursor-grab` grip icon (lucide `GripVertical`)
- Active toggle: existing checkbox or toggle from `components/ui/`

---

## Out of Scope (this split)

- Real-time chat between admin and agent
- Billing/invoice integration
- External client-facing portal
- Multi-agent task assignment
- Developer project task approval (only global tasks in approval queue)

---

## Acceptance Criteria

1. Client detail page shows 4 tabs: Overview, Tasks, Marketing Plan, Time & Capacity
2. Both marketing and developer agents see the 4-tab hub for their respective clients
3. Tasks tab shows all tasks tagged with that client, with List/Kanban toggle
4. Tasks tab for developer clients also shows website project tasks section
5. Time & Capacity shows auto-calculated Days Worked, Total Hours, weekly/category breakdowns
6. Date range picker on Time & Capacity tab (default 90 days)
7. Marketing Plan tab renders strategy_notes as markdown + structured pillars/audiences
8. Marketing Plan content is read-only for agents, editable by admins
9. Admin approval queue at `/admin/approvals/` lists all `in_review` AgentGlobalTasks
10. Admin can approve (→ done + notification) or reject (→ in_progress + feedback + notification)
11. Rejection requires feedback text (form validates before submit)
12. `review_feedback` stored on task, visible to agent in task detail
13. Admin category settings page at `/admin/settings/categories/` with full CRUD
14. Drag-and-drop reordering persists to backend via bulk PATCH
15. Soft-delete only for categories (toggle is_active) — no hard delete
16. Export report generates CSV with task/time data for selected date range
17. Export report generates branded PDF using extended PDFService
18. All 3 new notification types sent via notification-realtime service
19. Performance: client report aggregation queries use existing DB indexes (client + date)
20. Mobile responsive for all new pages
