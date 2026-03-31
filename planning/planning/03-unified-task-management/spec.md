# Spec: Unified Task Management UI

## Summary

Merge the Kanban board and List view into a single unified Tasks page inside the Command Centre portal. Replace page-level client filtering with task-level client tagging using controlled vocabulary. Add task creation/edit modal with admin-configurable category picker and recurrence rule builder. Implement approval workflow columns (To-Do → In Progress → In Review → Done) with notification triggers.

## Dependencies

- **Split 01 (Backend Restructuring):** API must support client tagging, dynamic categories, recurrence fields, `in_review` status
- **Split 02 (Portal Navigation):** Portal shell with route at `/management/tasks/`

## Goals

1. **Unified view toggle:** Single Tasks page with seamless Kanban ↔ List switch, same dataset and filters preserved across views
2. **Client tagging:** Controlled vocabulary selector (linked to Clients database), color-coded badges, horizontal filter bar
3. **Category picker:** Fetches admin-configured categories from API, visual badges
4. **Recurrence rule builder:** Toggle in task modal reveals frequency/interval/end-condition UI
5. **Approval workflow:** Kanban columns include "In Review"; moving a task there triggers admin notification

## Existing Code to Refactor

### Components to Evolve
- `client/app/dashboard/agent/developer/tasks/page.tsx` — Has Kanban with filters. Refactor into shared component.
- `client/components/agent/scheduling/CrossClientTaskList.tsx` — Cross-client task display. Incorporate into unified list view.
- `client/components/agent/scheduling/TaskCategoryBadge.tsx` — Category visualization. Update for dynamic categories.
- `client/components/agent/scheduling/RecurringTaskManager.tsx` — Recurrence UI. Extract rule builder into task modal.

### Types to Use (from Split 01)
- `AgentGlobalTask` (with new client, category, recurrence fields)
- `TaskCategoryItem` (dynamic categories from API)
- `GlobalTaskStatus` (with `in_review`)

### API Hooks to Use
- `useGlobalTasks()` — with new filter params (client, category_id)
- `useUpdateGlobalTask()` — for status changes including `in_review`
- New: `useTaskCategories()` — fetch dynamic categories

## Detailed Requirements

### Unified Tasks Page Layout

```
┌──────────────────────────────────────────────────────────────┐
│ Tasks                                    [List] [Kanban] ⚙  │
├──────────────────────────────────────────────────────────────┤
│ Filter Bar: [All Clients ▾] [All Categories ▾] [Status ▾]   │
│             [Priority ▾] [Search...                      🔍] │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  (Kanban View OR List View based on toggle)                  │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│                               [+ New Task]                   │
└──────────────────────────────────────────────────────────────┘
```

### View Toggle

- Position: Top-right of page header
- Style: Segmented control / toggle button group
- Options: List icon + Kanban icon
- State persists in localStorage (`command-centre-task-view`)
- Switching views preserves all active filters

### Kanban View

4 columns:
1. **To-Do** — New tasks, backlog
2. **In Progress** — Active work
3. **In Review** — Awaiting admin approval (triggers notification on drop)
4. **Done** — Completed/approved tasks

Each card shows:
- Task title (truncated)
- Client badge (color-coded)
- Category badge
- Priority indicator (colored dot: red/amber/blue)
- Due date (red if overdue)
- Recurrence icon (🔄) if recurring
- Drag handle (grip dots)

Drag-and-drop between columns using @dnd-kit:
- Moving to "In Review" → API call to update status + trigger notification
- Moving to "Done" → API call; if recurring, JIT creates next instance

### List View

Table columns:
| Title | Client | Category | Status | Priority | Due Date | Scheduled | Actions |

- Sortable columns (click header)
- Row click → opens task detail/edit modal
- Inline status dropdown per row
- Bulk selection checkbox column
- Color-coded client and category badges inline

### Client Tag Filter Bar

- Horizontal bar below page header
- Dropdown selector linked to agent's assigned clients (from `/api/clients/` endpoint)
- Selected client shows as colored chip/badge
- Multiple client selection supported
- "All Clients" default shows everything
- Client badges use distinct colors (auto-assigned from a palette or from client record)

### Task Creation/Edit Modal

Sections:
1. **Basic Info:** Title, Description (rich text), Priority selector
2. **Assignment:** Client selector (dropdown from Clients DB — controlled vocabulary, no free-text), Category selector (from admin-configured list)
3. **Scheduling:** Date picker (single day, date range, or multi-select days), Optional time range (start/end)
4. **Recurrence** (toggle to reveal):
   - Frequency: Daily, Weekly, Biweekly, Monthly, Yearly, Custom
   - For Weekly/Custom: Day-of-week checkboxes (Mon-Sun)
   - Interval: "Every N [days/weeks/months]"
   - End condition: Never / After N occurrences / On date (date picker)
5. **Actions:** Save, Save & Schedule (opens calendar), Cancel

### Approval Workflow Notification

When task status changes to `in_review`:
1. Frontend calls `PATCH /agent/schedule/global-tasks/{id}/` with `{ status: 'in_review' }`
2. Backend triggers notification via notification-realtime service
3. Notification payload: `{ type: 'task_review_request', task_id, task_title, agent_name, client_name }`
4. Admin sees notification in their dashboard

## Design Specifications

### View Toggle
- Segmented control: `rounded-lg border border-border`
- Active segment: `bg-accent text-white`
- Inactive segment: `bg-surface text-secondary`
- Icons: `LayoutList` (list), `Columns3` (kanban) from Lucide

### Kanban Cards
- Card: `bg-surface rounded-lg border border-border shadow-sm p-3`
- Hover: `hover-lift` (translateY -4px)
- Drag state: `shadow-lg opacity-90`
- Column header: `text-label font-medium uppercase tracking-wider`

### Client Badges
- `rounded-full px-2 py-0.5 text-xs font-medium`
- Background: client's assigned color at 15% opacity
- Text: client's assigned color at full

### Filter Bar
- `flex gap-2 items-center p-3 bg-surface-subtle rounded-lg border border-border-subtle`
- Dropdowns: `rounded-lg border border-border bg-surface text-sm`

## Out of Scope

- Calendar drag-and-drop scheduling (Split 04)
- Admin approval queue UI (Split 06)
- Client detail CRM page (Split 06)
- Dashboard KPI (Split 05)

## Acceptance Criteria

1. Single Tasks page at `/management/tasks/` with Kanban ↔ List toggle
2. Switching views preserves filters and dataset
3. Kanban has 4 columns: To-Do, In Progress, In Review, Done
4. Drag-and-drop between Kanban columns updates task status via API
5. Moving to "In Review" sends notification to admin
6. List view shows sortable table with all task metadata
7. Client filter bar with controlled vocabulary (no free-text)
8. Color-coded client and category badges throughout
9. Task creation modal with all fields: client selector, category, date, recurrence
10. Recurrence rule builder supports daily/weekly/monthly/yearly/custom with end conditions
11. Task completion of recurring task triggers JIT next-instance creation
12. View preference persists in localStorage
13. Responsive: Kanban scrolls horizontally on mobile, List becomes card view
