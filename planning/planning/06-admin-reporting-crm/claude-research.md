# Research: Admin Reporting & Client CRM Hub

## Part 1: Codebase Research

### 1. Admin Dashboard Structure

**Location**: `client/app/dashboard/admin/`

Pages follow the Next.js App Router pattern with nested directories: `/admin/{section}/{subsection}/page.tsx`.

**Navigation Sidebar** (`client/components/dashboard/sidebar.tsx`):
- Admin nav groups: `main`, `business`, `team`, `company`, `platform`
- Uses `NavGroup` / `NavItem` components with optional `subItems` for expandable sections
- Current groups (relevant ones):
  ```
  main:     Overview
  business: Clients, Quotes & Invoices, Pricing, Analytics (with subItems)
  team:     Team → Agents, Performance
  platform: Courses, Website Config (with subItems), Messages
  ```
- New "Approvals" nav item should be added to the `business` group
- New "Settings → Categories" can go under a new `settings` group or under `platform`

**Key pattern**: To add nav items, edit the `adminNavGroups` config in `sidebar.tsx` with `{ href, label, icon }` and optional `subItems`.

---

### 2. Agent Client Pages

**Marketing Agent Client List** (`client/app/dashboard/agent/marketing/clients/page.tsx`):
- Fetches via `ApiService.get('/agents/my-clients/')`
- Shows stats cards: Total, My Clients, Available, Assigned to Others
- Filter tabs: `all`, `my`, `available`, `assigned`
- For marketing agents: fetches posts (`/marketing-posts/?client={id}`) and subscriptions
- Displays: total_posts, pending_review_posts, scheduled_posts, marketing plan name/status

**Marketing Agent Client Detail** (`client/app/dashboard/agent/marketing/clients/[id]/page.tsx`):
- Uses React Query: `useQuery` with `api.getClient(clientId)` + `api.getMarketingPosts({ client: clientId })`
- Layout: Contact info sidebar + stats grid
- Stats: Total Posts, In Production, Pending Review, Published
- Recent Posts section with status badges
- Quick Actions: All Posts, Ideas, Analytics, Messages

**Developer Agent Client List** (`client/app/dashboard/agent/developer/clients/page.tsx`):
- Same base structure, but no marketing-specific stats
- Shows: client classification, agent assignments, availability

**Enhancement needed**: Both detail pages need upgrading to the 4-tab CRM hub (Overview, Tasks, Marketing Plan, Time & Capacity).

---

### 3. Scheduling & Task API

**API wrapper**: `client/lib/api/scheduling.ts`

**Key methods:**
```typescript
// Time Blocks
getTimeBlocks(params?: { date?, start?, end?, block_type? }): Promise<AgentTimeBlock[]>
// client FK on AgentTimeBlock: client: string | null, client_name: string

// Global Tasks
getGlobalTasks(filters?: GlobalTaskFilters): Promise<AgentGlobalTask[]>
// GlobalTaskFilters includes: status, priority, client, category, search, due_date

// Cross-Client Tasks
getCrossClientTasks(filters?: CrossClientTaskFilters): Promise<CrossClientTasksResponse>

// Categories
getTaskCategories(department?): Promise<TaskCategoryItem[]>
```

**React hooks** (`client/lib/hooks/useScheduling.ts`):
- `useTimeBlocks(params)`, `useGlobalTasks(filters)`, `useTaskCategories(department)`
- All invalidate `SCHEDULE_KEYS` on mutation success

**Key types** (from `client/lib/types.ts` + `client/lib/types/scheduling.ts`):
```typescript
interface AgentTimeBlock {
  id: string
  agent: string
  date: string          // "YYYY-MM-DD"
  start_time: string
  end_time: string
  block_type: 'deep_work' | ...
  client: string | null
  client_name: string
  duration_minutes: number
}

interface AgentGlobalTask {
  id: string
  title: string
  status: 'todo' | 'in_progress' | 'in_review' | 'done'
  priority: 'low' | 'medium' | 'high'
  task_category_ref: string | null
  // client FK should be available per spec dependencies (Split 01)
}
```

---

### 4. Notification-Realtime Service

**Architecture**: Node.js/Express + Socket.IO + MongoDB + RabbitMQ

**Key components**:
- `services/notification-realtime/notificationRoutes.ts` — HTTP `/api/notifications` endpoints
- `services/notification-realtime/notificationSocket.ts` — WebSocket real-time delivery
- `services/notification-realtime/eventConsumer.ts` — RabbitMQ event consumer

**Notification MongoDB schema**:
```typescript
interface INotificationDocument {
  userId: string
  title: string
  message: string
  type: NotificationType    // enum of ~20+ types
  read: boolean
  link?: string
  metadata?: Record<string, any>
  createdAt: Date
}
```

**Existing notification types** (Django `server/api/models/notifications.py`):
- Task: `task_assigned`, `task_completed`, `task_overdue`
- Content: `content_submitted`, `content_approved`, `content_rejected`
- No `task_review_submitted`, `task_approved`, `task_rejected` yet — these need adding

**Pattern to follow**: Backend sends event to RabbitMQ → `eventConsumer.ts` picks it up → creates MongoDB notification → pushes via Socket.IO to connected clients.

---

### 5. Existing Task Management UI (Split 03 — reusable components)

**Location**: `client/app/dashboard/agent/marketing/management/tasks/`

**Reusable components for the Tasks tab:**
- `ViewToggle.tsx` — List/Kanban toggle (state in localStorage + URL param `?view=kanban`)
- `TaskFilterBar.tsx` — Status, category, priority, search, client filter (URL param state)
- `TasksKanbanView.tsx` — Columns by status (TODO, IN PROGRESS, IN REVIEW, DONE)
- `TasksListView.tsx` — Table with bulk selection + `BulkActionBar`
- `TaskCard.tsx`, `KanbanColumn.tsx`, `ClientBadge.tsx`
- `useTaskFilters()` hook — manages all filter state via URL params

**Client Tasks tab pattern**: Import these components and pass `client={clientId}` as a filter to `useTaskFilters()` / `useGlobalTasks()` to scope tasks to the selected client.

---

### 6. Testing Setup

**Framework**: **Vitest** (not Jest)

**Config** (`client/vitest.config.ts`):
```typescript
defineConfig({
  plugins: [react()],
  test: { environment: 'jsdom', setupFiles: ['./vitest.setup.ts'], globals: true }
})
```

**Setup file**: `client/vitest.setup.ts` — imports `@testing-library/jest-dom`

**Test utilities** (`client/test-utils/scheduling.tsx`):
- `createMockTimeBlock(overrides?)` — returns valid `AgentTimeBlock`
- `createMockGlobalTask(overrides?)` — returns valid `AgentGlobalTask`
- `mockUseSchedulingEngine(overrides?)` — mock hook return value
- `renderWithQuery(ui, options?)` — wraps in `QueryClientProvider`

**Patterns**:
- `@tanstack/react-query` with fresh `QueryClient` per test
- Component tests in `__tests__/` directories
- Files: `*.test.tsx` or `*.test.ts`

---

### 7. Django Backend — Task Models & Categories

**Task status choices** (from `server/api/models/marketing_tasks.py`):
```python
class Status(TextChoices):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"      # Note: currently "review" not "in_review"
    DONE = "done"
```
The spec uses `in_review` — need to verify if this was updated in Split 01 backend migration.

**Global task model** (`AgentGlobalTaskViewSet` in `server/api/agent/scheduling_views.py`):
- Unified task view with helper: `_serialize_client_task(task, agent) -> Dict`
- Filters: status, priority, client, category, search, due_date
- Custom action: `complete/`

**Category choices** (marketing_tasks.py):
```python
MARKETING_CATEGORY_CHOICES = [
    ("creative", "Creative"), ("analytical", "Analytical"),
    ("admin", "Admin"), ("strategy", "Strategy"),
    ("content_creation", "Content Creation"),
    ("communication", "Communication"), ("research", "Research"),
]
```
The spec references a `TaskCategory` model (dynamic, from Split 01) — likely a database model replacing this tuple.

**Notification model** (`server/api/models/notifications.py`):
- Fields: id (UUID), user (FK), title, message, notification_type, read, created_at
- ~23 notification type choices — new approval types need adding

**Admin assignment views** (`server/api/admin/client_assignment_views.py`):
- Existing pattern for admin-only POST actions on clients

---

### 8. Navigation Summary

To add new admin pages:
1. Edit `adminNavGroups` in `client/components/dashboard/sidebar.tsx`
2. Add routes under `client/app/dashboard/admin/`
3. Follow the existing `admin/clients/` pattern for page structure

---

## Part 2: Web Research

### PDF Export

**Recommended approach for this project**: `django-weasyprint` for HTML-template-based PDFs (client reports with tables + static charts).

**Why WeasyPrint over alternatives:**
- Pure Python, no external daemon
- Supports HTML/CSS templates — matches Django's template system
- `django-weasyprint` integrates cleanly with DRF
- Actively maintained (2.x series, switched to pydyf renderer in v53+)

**Implementation pattern:**
```python
# pip install django-weasyprint
from django_weasyprint import WeasyTemplateResponseMixin

class ClientReportPDFView(WeasyTemplateResponseMixin, DetailView):
    template_name = "reports/client_report_pdf.html"
    pdf_attachment = True

    def get_pdf_filename(self):
        return f"report-{self.object.pk}.pdf"
```

**Charts in PDFs**: WeasyPrint cannot execute JavaScript. Charts must be:
- Pre-rendered as SVG on the server
- Or embedded as static PNG images

**Recommendation for this project**: Since chart data is already available server-side (time block aggregations), render charts as inline SVG in the HTML template using a simple Python SVG generator or matplotlib in `Agg` (non-GUI) mode. This avoids Playwright complexity.

**CSV export**: No library needed — Django's `HttpResponse` with `content_type='text/csv'` + Python's built-in `csv` module is sufficient.

**Always offload PDF generation to Celery** — never block a request thread for PDF rendering.

---

### Recharts Advanced Patterns

**TypeScript**: No separate `@types/recharts` needed in Recharts 2.x. Built-in types.

**Bar chart pattern (weekly breakdown):**
```tsx
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"

<ResponsiveContainer width="100%" height={320}>
  <BarChart data={weeklyData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
    <XAxis dataKey="week_start" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }} />
    <YAxis tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }} />
    <Tooltip content={<CustomTooltip />} />
    <Bar dataKey="hours" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
  </BarChart>
</ResponsiveContainer>
```

**Donut chart pattern (category breakdown):**
```tsx
import { PieChart, Pie, Cell, ResponsiveContainer, Sector } from "recharts"

// Use activeShape with renderActiveShape for interactive donut
// Use innerRadius={70} outerRadius={100} for donut proportions
// COLORS: map from task category to a fixed palette
```

**Key rules:**
- Always use `ResponsiveContainer` — never hardcode pixel width
- Wrap with `React.memo` in dashboards with many charts
- Memoize data arrays with `useMemo` to prevent remounts
- Bar + Donut cannot be combined in a single `ComposedChart` — render as separate components in a grid

---

### Django Approval Workflow

**Status machine**: `django-fsm` is archived (Oct 2025). Options:
- `viewflow.fsm` v3 (active, new API)
- Hand-rolled state validation (simpler for a 4-state machine)

**Recommendation for this project**: Given the simple 4-state machine (`todo → in_progress → in_review → done`), hand-rolling is cleaner than adding a new dependency:

```python
VALID_TRANSITIONS = {
    'in_review': ['done', 'in_progress'],   # admin can approve or reject
    'todo': ['in_progress'],
    'in_progress': ['in_review', 'done'],
}

def transition_task_status(task, new_status, actor):
    if new_status not in VALID_TRANSITIONS.get(task.status, []):
        raise ValueError(f"Cannot transition from {task.status} to {new_status}")
    task.status = new_status
    task.save()
```

**DRF approval endpoints pattern:**
```python
@action(detail=True, methods=["post"], permission_classes=[IsAdminUser])
def approve(self, request, pk=None):
    task = self.get_object()
    with transaction.atomic():
        task.status = 'done'
        task.save()
    # trigger notification
    return Response(TaskSerializer(task).data)

@action(detail=True, methods=["post"], permission_classes=[IsAdminUser])
def reject(self, request, pk=None):
    feedback = request.data.get('feedback', '')
    if not feedback:
        return Response({'feedback': 'Required'}, status=400)
    task = self.get_object()
    with transaction.atomic():
        task.status = 'in_progress'
        task.feedback = feedback  # new field
        task.save()
    return Response(TaskSerializer(task).data)
```

**Notifications**: Use Django signals → thin handler → Celery task → RabbitMQ → notification-realtime service. Keep signal handlers under 1ms.

**Approval queue endpoint:**
```python
@action(detail=False, methods=["get"], permission_classes=[IsAdminUser])
def approval_queue(self, request):
    tasks = Task.objects.filter(status='in_review').select_related('client', 'agent')
    return Response(TaskSerializer(tasks, many=True).data)
```

---

### dnd-kit Drag-and-Drop Sorting

**Package** (`@dnd-kit/sortable`) is already installed in `client/package.json`.

**Core pattern for category reordering:**
```tsx
import { DndContext, closestCenter, PointerSensor, useSensor, useSensors } from "@dnd-kit/core"
import { SortableContext, arrayMove, verticalListSortingStrategy, useSortable } from "@dnd-kit/sortable"
import { CSS } from "@dnd-kit/utilities"

// useSortable hook in each item:
const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: item.id })
const style = { transform: CSS.Transform.toString(transform), transition, opacity: isDragging ? 0.4 : 1 }

// PointerSensor with activationConstraint prevents accidental drags on click:
useSensor(PointerSensor, { activationConstraint: { distance: 8 } })
```

**Persisting to backend — bulk PATCH (one request):**
```typescript
// Single PATCH with ordered IDs array — much better than N individual requests
await fetch('/api/categories/reorder/', {
  method: 'PATCH',
  body: JSON.stringify({ ordered_ids: items.map(i => i.id) })
})
```

**Django side:**
```python
@action(detail=False, methods=["patch"], permission_classes=[IsAdminUser])
def reorder(self, request):
    ordered_ids = request.data.get("ordered_ids", [])
    with transaction.atomic():
        for index, cat_id in enumerate(ordered_ids):
            TaskCategory.objects.filter(id=cat_id).update(sort_order=index)
    return Response({"status": "ok"})
```

**Accessibility**: dnd-kit has keyboard navigation built-in — `KeyboardSensor` with `sortableKeyboardCoordinates` enables arrow key drag. Customize `announcements` prop for screen reader messages.

---

## Key Decisions from Research

1. **PDF format**: Use `django-weasyprint` with Celery task, charts as inline SVG. CSV is built-in Python.
2. **Charts**: Recharts (already installed) — separate `BarChart` + `PieChart` components in a grid layout.
3. **Approval state machine**: Hand-rolled validation (4-state machine too simple for a library).
4. **Notification pattern**: Signals → Celery → RabbitMQ → notification-realtime service (existing pipeline).
5. **Category drag-and-drop**: `@dnd-kit/sortable` (already installed) with bulk PATCH `ordered_ids[]`.
6. **Testing**: Vitest + `renderWithQuery` from `test-utils/scheduling.tsx`. New mock factories needed for client report data.
