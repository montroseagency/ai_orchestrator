# Spec: Admin Reporting & Client CRM Hub

## Summary

Enhance the Clients Page into a CRM hub with task aggregation by client tag, automated "Days Worked" tracking from time block data, and marketing plan integration. Build an admin approval queue into the existing admin dashboard for reviewing agent-submitted tasks. Add admin-configurable category management settings page. Implement automated client report export.

## Dependencies

- **Split 01 (Backend):** Task model with client tagging, dynamic categories
- **Split 03 (Task Management):** Tasks tagged with clients, approval workflow columns
- **Split 04 (Scheduling Engine):** Time block data for capacity/time tracking
- **Split 05 (Dashboard KPI):** Dashboard structure (for admin overview integration)

## Goals

1. **Client CRM hub:** Agent's Clients Page shows aggregated task history, time investment, and marketing plan per client
2. **Automated time tracking:** "Days Worked" and hours calculated from time block data — no manual timesheets
3. **Admin approval queue:** Admins see pending review tasks, can approve/reject with feedback
4. **Category management:** Admin settings page to CRUD task categories
5. **Client report export:** Generate exportable summaries (tasks, time, milestones) by client and date range

## Existing Code to Integrate

### Admin Dashboard Structure
- Sidebar nav: Overview, Clients, Quotes & Invoices, Pricing, Analytics, Agents, Performance
- Add "Approvals" nav item and "Category Settings" under a new "Settings" group

### Agent Client Pages
- `client/app/dashboard/agent/developer/clients/page.tsx` — Developer client list
- `client/app/dashboard/agent/marketing/clients/page.tsx` — Marketing client list
- `client/app/dashboard/agent/marketing/clients/[id]/page.tsx` — Client detail

### API Endpoints
- Existing client API endpoints
- `schedulingApi.getTimeBlocks()` — for time aggregation
- `schedulingApi.getGlobalTasks()` — for task aggregation by client
- `schedulingApi.getCrossClientTasks()` — cross-client view
- Notification-realtime service — for approval workflow triggers

### Types
- `Client` from `lib/types.ts`
- `AgentGlobalTask` with client FK (from Split 01)
- `AgentTimeBlock` with client FK (existing)

## Detailed Requirements

### Enhanced Client Detail Page (Agent View)

When agent clicks a client in the Command Centre's Clients page:

```
┌──────────────────────────────────────────────────────────────────┐
│ ◀ Back to Clients                                               │
│                                                                  │
│ [Nike]  Active · Marketing Package · Assigned: Agent Smith       │
├──────────────────────────────────────────────────────────────────┤
│ [Overview] [Tasks] [Marketing Plan] [Time & Capacity]            │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  (Tab content here)                                              │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

**Tabs:**

#### Overview Tab
- Client info card (name, company, package, status)
- Quick stats: Total tasks, Completed, In Progress, Days Worked, Total Hours
- Recent activity feed (last 10 task status changes)

#### Tasks Tab
- Filtered task list showing ALL tasks tagged with this client
- Same List/Kanban toggle as Split 03's unified Tasks page
- Filter by status, category, date range
- Shows full task history (not just active)

#### Marketing Plan Tab
- Displays strategic documents, campaign goals, budget constraints, brand guidelines
- Set by administrator
- Read-only for agents (editable by admin)
- Markdown/rich text rendering
- Attachments section for brand assets

#### Time & Capacity Tab
- **Days Worked:** Count of unique dates where time blocks exist for this client
- **Total Hours:** Sum of all time block durations for this client
- **Weekly Breakdown:** Bar chart showing hours per week for last 8 weeks
- **Category Breakdown:** Pie/donut chart showing time split by task category
- **Monthly Summary:** Table with columns: Month, Days, Hours, Tasks Completed
- All data auto-calculated from time block records — no manual entry

### Backend API for Client Reporting

#### New Endpoints

```
GET /agent/clients/{id}/report/
  Query params: ?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
  Returns:
  {
    client: { id, name, company },
    period: { start, end },
    summary: {
      total_tasks: number,
      completed_tasks: number,
      in_progress_tasks: number,
      total_hours: number,
      days_worked: number,
      unique_categories: string[]
    },
    category_breakdown: [
      { category: string, hours: number, task_count: number }
    ],
    weekly_breakdown: [
      { week_start: string, hours: number, tasks_completed: number }
    ],
    tasks: [
      { id, title, status, category, hours_spent, completed_at }
    ]
  }

GET /agent/clients/{id}/marketing-plan/
  Returns: { content: string (markdown), attachments: [], updated_at: string }

POST /admin/clients/{id}/marketing-plan/
  Body: { content: string }
  Admin-only: Update marketing plan content
```

### Admin Approval Queue

New page in admin dashboard: `/dashboard/admin/approvals/`

```
┌──────────────────────────────────────────────────────────────────┐
│ Pending Approvals (7)                                           │
├──────────────────────────────────────────────────────────────────┤
│ Agent       │ Task                    │ Client  │ Submitted │ ⚡ │
│─────────────│─────────────────────────│─────────│───────────│────│
│ Agent Smith │ Nike Q2 Campaign Brief  │ Nike    │ 2h ago    │ 👁 │
│ Agent Jones │ Adidas Social Calendar  │ Adidas  │ 4h ago    │ 👁 │
│ Agent Smith │ Puma SEO Report         │ Puma    │ 1d ago    │ 👁 │
│ ...                                                              │
└──────────────────────────────────────────────────────────────────┘
```

**Clicking a task opens the review panel:**

```
┌──────────────────────────────────────────────────────────────┐
│ Review: Nike Q2 Campaign Brief                               │
│ Agent: Smith · Client: Nike · Category: Copywriting          │
│ Submitted: 2 hours ago                                       │
├──────────────────────────────────────────────────────────────┤
│ Task Description:                                            │
│ [Full task description and any attachments]                  │
│                                                              │
│ Agent Notes:                                                 │
│ "Completed the Q2 brief with updated brand guidelines..."   │
├──────────────────────────────────────────────────────────────┤
│ Feedback (required for rejection):                           │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │                                                          │ │
│ └──────────────────────────────────────────────────────────┘ │
│                                                              │
│ [✓ Approve]                              [✗ Reject & Return] │
└──────────────────────────────────────────────────────────────┘
```

**Approve:** Sets task status to `done`, sends notification to agent
**Reject:** Sets task status to `in_progress`, attaches feedback notes, sends notification to agent with rejection reason

#### Backend API

```
GET /admin/approvals/
  Returns: List of tasks with status='in_review', includes agent name, client name

POST /admin/approvals/{task_id}/approve/
  Sets status='done', triggers agent notification

POST /admin/approvals/{task_id}/reject/
  Body: { feedback: string (required) }
  Sets status='in_progress', attaches feedback, triggers agent notification
```

### Admin Category Management

New settings page: `/dashboard/admin/settings/categories/`

- List all task categories with: name, color, icon, department, sort order, active toggle
- Add new category: modal with name, color picker, icon selector, department dropdown
- Edit category: inline or modal
- Deactivate category: soft delete (toggle)
- Reorder: drag-and-drop sort order
- Preview: shows badge as it would appear in task views

Uses the `TaskCategory` model and admin API from Split 01.

### Automated Client Report Export

In the Client Detail → Time & Capacity tab, add an "Export Report" button.

**Export options:**
- Date range selector (last 30 days, last quarter, custom range)
- Format: PDF or CSV
- Content: Task summary, hours breakdown by category, weekly timeline

**CSV format:**
```
Task Title, Status, Category, Client, Date, Hours Spent, Agent
"Nike Q2 Brief", "Done", "Copywriting", "Nike", "2026-03-15", "2.5", "Agent Smith"
```

**PDF format:** Branded with Montrose logo, summary stats at top, task table, charts

### Notification Payloads

#### Task Submitted for Review (→ Admin)
```json
{
  "type": "task_review_submitted",
  "task_id": "uuid",
  "task_title": "Nike Q2 Campaign Brief",
  "agent_name": "Agent Smith",
  "client_name": "Nike",
  "submitted_at": "2026-03-26T14:30:00Z"
}
```

#### Task Approved (→ Agent)
```json
{
  "type": "task_approved",
  "task_id": "uuid",
  "task_title": "Nike Q2 Campaign Brief",
  "approved_by": "Admin Name"
}
```

#### Task Rejected (→ Agent)
```json
{
  "type": "task_rejected",
  "task_id": "uuid",
  "task_title": "Nike Q2 Campaign Brief",
  "rejected_by": "Admin Name",
  "feedback": "Please update the budget section with Q2 figures"
}
```

## Design Specifications

### Client Detail Tabs
- Tab bar: `border-b border-border`, active tab has `border-b-2 border-accent text-accent`
- Tab content area: `p-6`

### Approval Queue
- Table: `border border-border rounded-xl overflow-hidden`
- Rows: `hover:bg-surface-subtle transition-colors`
- Approve button: `bg-green-600 text-white rounded-lg px-4 py-2`
- Reject button: `bg-red-600 text-white rounded-lg px-4 py-2`
- Feedback textarea: `border border-border rounded-lg p-3 min-h-[100px]`

### Charts (Time & Capacity tab)
- Use recharts or existing charting library
- Bar chart: accent color bars, subtle grid
- Donut chart: category colors, center text with total hours

## Out of Scope

- Real-time chat between admin and agent (future)
- Billing/invoice integration (separate system)
- External client-facing portal (future)
- Multi-agent task assignment (future)

## Acceptance Criteria

1. Client detail page shows 4 tabs: Overview, Tasks, Marketing Plan, Time & Capacity
2. Tasks tab shows all tasks tagged with that client, with List/Kanban toggle
3. Time & Capacity shows auto-calculated Days Worked, Total Hours, breakdowns
4. Marketing Plan tab renders admin-set content (read-only for agents)
5. Admin approval queue at `/admin/approvals/` lists all `in_review` tasks
6. Admin can approve (→ done + notification) or reject (→ in_progress + feedback + notification)
7. Rejection requires feedback text (form validates)
8. Admin category settings page with full CRUD for task categories
9. Export report generates CSV with task/time data for selected date range
10. All notifications sent via notification-realtime service
11. Data aggregation queries are performant (indexed on client + date)
12. Uses existing admin dashboard navigation structure
13. Mobile responsive for all new pages
